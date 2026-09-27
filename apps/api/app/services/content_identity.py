"""Versioned content identity, hierarchy authorization and frozen resolution."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import (
    BrandVoiceVersion,
    ContentAccount,
    ContentAccountRevision,
    ContentBrand,
    ContentBrandRevision,
    ContentPersona,
    ContentPersonaRevision,
    ContentSeries,
    ContentSeriesRevision,
    IdentitySnapshot,
    User,
)


class IdentityProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    positioning: str | None = None
    target_audience: list[str] | None = None
    content_domains: list[str] | None = None
    expression_style: dict[str, Any] | None = None
    visual_language: dict[str, Any] | None = None
    long_term_views: list[str] | list[dict[str, Any]] | None = None
    value_propositions: list[str] | None = None
    content_boundaries: list[str] | None = None
    risk_boundaries: list[str] | None = None
    public_fact_policy: dict[str, Any] | None = None
    brand_voice_version_id: int | None = None


REVISION_MODELS = {
    "brand": (ContentBrand, ContentBrandRevision, "brand_id"),
    "persona": (ContentPersona, ContentPersonaRevision, "persona_id"),
    "account": (ContentAccount, ContentAccountRevision, "account_id"),
    "series": (ContentSeries, ContentSeriesRevision, "series_id"),
}


def checksum(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True)
class Hierarchy:
    brand: ContentBrand | None
    persona: ContentPersona
    account: ContentAccount | None
    series: ContentSeries | None

    def members(self) -> tuple[tuple[str, Any], ...]:
        return tuple((name, value) for name, value in (
            ("brand", self.brand), ("persona", self.persona),
            ("account", self.account), ("series", self.series),
        ) if value is not None)


def hierarchy(db: Session, user: User, *, persona_id: int, account_id: int | None = None, series_id: int | None = None, mutable: bool = False) -> Hierarchy:
    persona = db.get(ContentPersona, persona_id)
    if persona is None or persona.owner_user_id != user.id:
        raise HTTPException(404, "内容角色不存在")
    brand = db.get(ContentBrand, persona.brand_id) if persona.brand_id else None
    if persona.brand_id and (brand is None or brand.owner_user_id != user.id):
        raise HTTPException(404, "品牌不存在")
    account = db.get(ContentAccount, account_id) if account_id is not None else None
    if account_id is not None and (account is None or account.persona_id != persona.id):
        raise HTTPException(404, "账号不存在")
    if series_id is not None and account is None:
        raise HTTPException(422, "选择栏目时必须选择所属账号")
    series = db.get(ContentSeries, series_id) if series_id is not None else None
    if series_id is not None and (series is None or series.account_id != account.id):
        raise HTTPException(404, "栏目不存在")
    result = Hierarchy(brand, persona, account, series)
    if mutable and any(value.status == "archived" for _, value in result.members()):
        raise HTTPException(409, "已归档身份只可查看历史")
    return result


def owned_entity(db: Session, user: User, kind: str, entity_id: int, *, mutable: bool = False):
    model = REVISION_MODELS[kind][0]
    entity = db.get(model, entity_id)
    if entity is None:
        raise HTTPException(404, "身份不存在")
    if kind == "brand":
        if entity.owner_user_id != user.id:
            raise HTTPException(404, "身份不存在")
        if mutable and entity.status == "archived":
            raise HTTPException(409, "已归档身份只可查看历史")
    elif kind == "persona":
        hierarchy(db, user, persona_id=entity_id, mutable=mutable)
    elif kind == "account":
        hierarchy(db, user, persona_id=entity.persona_id, account_id=entity_id, mutable=mutable)
    else:
        account = db.get(ContentAccount, entity.account_id)
        if account is None:
            raise HTTPException(404, "身份不存在")
        hierarchy(db, user, persona_id=account.persona_id, account_id=account.id, series_id=entity_id, mutable=mutable)
    return entity


def current_revision(db: Session, kind: str, entity_id: int):
    _, revision_model, foreign_key = REVISION_MODELS[kind]
    return db.scalar(select(revision_model).where(getattr(revision_model, foreign_key) == entity_id).order_by(revision_model.revision_no.desc()).limit(1))


def revisions(db: Session, kind: str, entity_id: int) -> list:
    _, revision_model, foreign_key = REVISION_MODELS[kind]
    return db.scalars(select(revision_model).where(getattr(revision_model, foreign_key) == entity_id).order_by(revision_model.revision_no.desc()).limit(100)).all()


def save_revision(db: Session, user: User, kind: str, entity_id: int, *, expected_revision: int, profile: IdentityProfile):
    owned_entity(db, user, kind, entity_id, mutable=True)
    data = profile.model_dump(exclude_unset=True)
    voice_id = data.get("brand_voice_version_id")
    if voice_id is not None:
        voice = db.get(BrandVoiceVersion, voice_id)
        if voice is None or voice.status != "published":
            raise HTTPException(422, "品牌语气版本不可用于新身份")
    previous = current_revision(db, kind, entity_id)
    current_no = previous.revision_no if previous else 0
    if expected_revision != current_no:
        raise HTTPException(409, "身份版本已更新，请刷新后重试")
    _, revision_model, foreign_key = REVISION_MODELS[kind]
    row = revision_model(**{foreign_key: entity_id}, revision_no=current_no + 1, profile_json=data, checksum=checksum(data), created_by=user.email)
    db.add(row)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "身份版本已更新，请刷新后重试") from exc
    db.refresh(row)
    return row


def effective(db: Session, user: User, *, persona_id: int, account_id: int | None = None, series_id: int | None = None, mutable: bool = False) -> dict:
    selected = hierarchy(db, user, persona_id=persona_id, account_id=account_id, series_id=series_id, mutable=mutable)
    profile: dict[str, Any] = {}
    origins: dict[str, str] = {}
    revision_ids: dict[str, int | None] = {}
    for kind, entity in selected.members():
        revision = current_revision(db, kind, entity.id)
        revision_ids[kind] = revision.id if revision else None
        if revision:
            for key, value in (revision.profile_json or {}).items():
                profile[key] = value
                origins[key] = kind
    voice_id = profile.get("brand_voice_version_id")
    if mutable and voice_id is not None:
        voice = db.get(BrandVoiceVersion, voice_id)
        if voice is None or voice.status != "published":
            raise HTTPException(409, "当前品牌语气版本不可用于新生产")
    return {
        "brand_id": selected.brand.id if selected.brand else None,
        "persona_id": selected.persona.id,
        "account_id": selected.account.id if selected.account else None,
        "series_id": selected.series.id if selected.series else None,
        "revision_ids": revision_ids,
        "brand_voice_version_id": voice_id,
        "effective_profile": profile,
        "field_origins": origins,
    }


def create_snapshot(db: Session, user: User, *, persona_id: int, account_id: int | None = None, series_id: int | None = None) -> IdentitySnapshot:
    resolved = effective(db, user, persona_id=persona_id, account_id=account_id, series_id=series_id, mutable=True)
    revisions = resolved["revision_ids"]
    payload = {**resolved, "owner_user_id": user.id}
    row = IdentitySnapshot(
        owner_user_id=user.id,
        brand_id=resolved["brand_id"], brand_revision_id=revisions.get("brand"),
        persona_id=persona_id, persona_revision_id=revisions.get("persona"),
        account_id=account_id, account_revision_id=revisions.get("account"),
        series_id=series_id, series_revision_id=revisions.get("series"),
        brand_voice_version_id=resolved["brand_voice_version_id"],
        effective_profile_json=resolved["effective_profile"],
        field_origins_json=resolved["field_origins"], checksum=checksum(payload), created_by=user.email,
    )
    db.add(row)
    db.flush()
    return row


def snapshot_json(row: IdentitySnapshot) -> dict:
    return {
        "id": row.id, "owner_user_id": row.owner_user_id,
        "brand_id": row.brand_id, "brand_revision_id": row.brand_revision_id,
        "persona_id": row.persona_id, "persona_revision_id": row.persona_revision_id,
        "account_id": row.account_id, "account_revision_id": row.account_revision_id,
        "series_id": row.series_id, "series_revision_id": row.series_revision_id,
        "brand_voice_version_id": row.brand_voice_version_id,
        "effective_profile": row.effective_profile_json,
        "field_origins": row.field_origins_json,
        "readiness": "ready" if row.effective_profile_json else "incomplete",
        "readiness_reason": None if row.effective_profile_json else "empty_profile",
        "checksum": row.checksum,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }
