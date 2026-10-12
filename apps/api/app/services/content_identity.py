"""Versioned content identity, hierarchy authorization and frozen resolution."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Literal

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError, OperationalError
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
    SystemSetting,
    User,
)
from .studio_creative_catalog import validate_creative_profile


class CreativeProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_: Literal["persona.creative.text.v1", "persona.creative.graphic.v1", "persona.creative.audio.v1", "persona.creative.video.v1"] = Field(alias="schema")
    mode: Literal["auto", "custom", "composed"]
    skill_ref: str = Field(min_length=3, max_length=150)
    style_preset_ref: str = Field(min_length=3, max_length=150)
    quality_profile_ref: str = Field(min_length=3, max_length=150)
    capability: Literal["chat", "image_generation", "video_generation", "tts", "asr"]
    model_binding: dict[str, str] | None = None
    model_chain: list[dict[str, str]] = Field(default_factory=list, max_length=8)
    capability_memory_revision_ids: list[int] = Field(default_factory=list, max_length=8)
    installed_skill_refs: list[str] = Field(default_factory=list, max_length=8)
    parameters: dict[str, Any] = Field(default_factory=dict, max_length=32)
    stage_instruction: str | None = Field(default=None, max_length=4000)
    provenance: dict[str, Any] = Field(default_factory=dict, max_length=8)

    @model_validator(mode="after")
    def validate_contract(self):
        validate_creative_profile(self.model_dump(mode="json", by_alias=True))
        return self


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
    text_creative_profile: CreativeProfile | None = None
    graphic_creative_profile: CreativeProfile | None = None
    audio_creative_profile: CreativeProfile | None = None
    video_creative_profile: CreativeProfile | None = None

    @model_validator(mode="after")
    def validate_creative_modalities(self):
        for modality in ("text", "graphic", "audio", "video"):
            profile = getattr(self, f"{modality}_creative_profile")
            if profile is not None and profile.schema_ != f"persona.creative.{modality}.v1":
                raise ValueError("creative_profile_modality_mismatch")
        return self


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


def _lock_account(db: Session, user: User, account_id: int) -> ContentAccount:
    row = owned_entity(db, user, "account", account_id, mutable=True)
    selected = hierarchy(db, user, persona_id=row.persona_id, account_id=row.id, mutable=True)
    try:
        # Serialize with normal archive UPDATEs, including ancestors, before re-reading authority.
        with db.no_autoflush:
            for model, entity in ((ContentBrand, selected.brand), (ContentPersona, selected.persona), (ContentAccount, row)):
                if entity is not None:
                    db.execute(update(model).where(model.id == entity.id).values(status=model.status).execution_options(synchronize_session=False))
                    db.refresh(entity)
        hierarchy(db, user, persona_id=row.persona_id, account_id=row.id, mutable=True)
    except OperationalError:
        db.rollback()
        raise HTTPException(409, "platform_binding_busy") from None
    except HTTPException:
        db.rollback()
        raise
    return row


def bind_platform_account(db: Session, user: User, account_id: int, *, channel: str, platform_account_id: str) -> ContentAccount:
    if user.role != "admin":
        raise HTTPException(403, "platform_binding_admin_required")
    row = _lock_account(db, user, account_id)
    try:
        if row.platform_channel is not None or row.platform_account_id is not None:
            if (row.platform_channel, row.platform_account_id) != (channel, platform_account_id):
                raise HTTPException(409, "platform_identity_immutable")
        else:
            row.platform_channel = channel
            row.platform_account_id = platform_account_id
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "platform_identity_conflict") from None
    except OperationalError:
        db.rollback()
        raise HTTPException(409, "platform_binding_busy") from None
    except HTTPException:
        db.rollback()
        raise
    db.refresh(row)
    return row


def publisher_connection(db: Session, user: User, account_id: int) -> dict:
    account = owned_entity(db, user, "account", account_id)
    ancestry = hierarchy(db, user, persona_id=account.persona_id, account_id=account.id)
    setting = db.get(SystemSetting, f"wechat.official.account.{account_id}", populate_existing=True)
    config = setting.value if setting else {}
    return {
        "content_account_id": account.id,
        "publisher_key": "publisher.wechat.official", "publisher_version": "1",
        "platform_account_id": account.platform_account_id,
        "revision": config.get("revision", 0), "enabled": config.get("enabled", False),
        "credential_ref": f"AICS_WECHAT_ACCOUNT_{account.id}_APPSECRET",
        "credential_version": config.get("credential_version"),
        "configured": bool(setting), "verified": False, "executable": False,
        "read_only": user.role != "admin" or any(row.status != "active" for _, row in ancestry.members()),
        "unavailable_reason": "official_contract_unresolved",
    }


def save_publisher_connection(db: Session, user: User, account_id: int, *, expected_revision: int, enabled: bool, credential_version: str) -> dict:
    if user.role != "admin":
        raise HTTPException(403, "platform_binding_admin_required")
    account = _lock_account(db, user, account_id)
    try:
        if account.platform_channel != "wechat" or account.platform_account_id is None:
            raise HTTPException(409, "platform_binding_required")
        key = f"wechat.official.account.{account.id}"
        setting = db.get(SystemSetting, key, populate_existing=True)
        revision = setting.value.get("revision", 0) if setting else 0
        if revision != expected_revision:
            raise HTTPException(409, "publisher_connection_conflict")
        if setting is None:
            setting = SystemSetting(key=key)
            db.add(setting)
        setting.value = {
            "revision": revision + 1, "enabled": enabled,
            "credential_ref": f"AICS_WECHAT_ACCOUNT_{account.id}_APPSECRET",
            "credential_version": credential_version,
            "platform_account_id": account.platform_account_id,
        }
        setting.updated_by = user.email
        db.commit()
    except (IntegrityError, OperationalError):
        db.rollback()
        raise HTTPException(409, "publisher_connection_conflict") from None
    except HTTPException:
        db.rollback()
        raise
    return publisher_connection(db, user, account_id)


def revisions(db: Session, kind: str, entity_id: int) -> list:
    _, revision_model, foreign_key = REVISION_MODELS[kind]
    return db.scalars(select(revision_model).where(getattr(revision_model, foreign_key) == entity_id).order_by(revision_model.revision_no.desc()).limit(100)).all()


def save_revision(db: Session, user: User, kind: str, entity_id: int, *, expected_revision: int, profile: IdentityProfile):
    owned_entity(db, user, kind, entity_id, mutable=True)
    data = profile.model_dump(exclude_unset=True, by_alias=True)
    creative_fields = {"text_creative_profile", "graphic_creative_profile", "audio_creative_profile", "video_creative_profile"}
    if kind == "brand" and creative_fields.intersection(data):
        raise HTTPException(422, "brand_creative_profile_forbidden")
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
    creative_keys = {"text_creative_profile", "graphic_creative_profile", "audio_creative_profile", "video_creative_profile"}
    creative_profiles: dict[str, Any] = {}
    creative_origins: dict[str, str] = {}
    revision_ids: dict[str, int | None] = {}
    for kind, entity in selected.members():
        revision = current_revision(db, kind, entity.id)
        revision_ids[kind] = revision.id if revision else None
        if revision:
            for key, value in (revision.profile_json or {}).items():
                if key in creative_keys:
                    if kind != "brand":
                        creative_profiles[key] = value
                        creative_origins[key] = kind
                    continue
                profile[key] = value
                origins[key] = kind
    profile.update(creative_profiles)
    origins.update(creative_origins)
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
        "creative_profile_origins": creative_origins,
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
