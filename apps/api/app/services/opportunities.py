"""FE-F5A opportunity serialization, validation and audit helpers."""

import hashlib
import json
from typing import Literal

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import (
    AuditLog,
    ContentOpportunity,
    ContentOpportunityAssessmentRevision,
    ContentOpportunitySignal,
    ContentProject,
    ContentUnit,
    DataSnapshot,
    DeliveryFeedback,
    DeliveryTarget,
    SourceDocument,
    User,
    utcnow,
)
from . import content_identity

SIGNAL_TYPES = {"source_document", "data_snapshot", "delivery_feedback", "manual", "external_ref"}
TRIAGE_STATUSES = {"new", "watching", "qualified", "dismissed"}
TIME_SENSITIVITY = {"timeless", "low", "medium", "high"}
SIMILARITY_STATES = {"unknown", "none", "possible"}


class IdentityRef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    brand_id: int | None = Field(default=None, gt=0)
    persona_id: int | None = Field(default=None, gt=0)
    account_id: int | None = Field(default=None, gt=0)
    series_id: int | None = Field(default=None, gt=0)


class AssessmentData(BaseModel):
    model_config = ConfigDict(extra="forbid")
    what_happened: str = Field(default="", max_length=5000)
    why_now: str = Field(min_length=1, max_length=5000)
    brand_relevance: str = Field(default="", max_length=5000)
    audience_fit: str = Field(default="", max_length=5000)
    suggested_angle: str | None = Field(default=None, max_length=5000)
    time_sensitivity: Literal["timeless", "low", "medium", "high"] = "timeless"
    recommended_identity_refs: list[IdentityRef] = Field(default_factory=list, max_length=30)
    recommended_modalities: list[Literal["text", "graphic", "video"]] = Field(default_factory=list, max_length=3)
    recommended_channels: list[str] = Field(default_factory=list, max_length=30)
    evidence_signal_ids: list[int] = Field(default_factory=list, max_length=100)
    evidence_summary: list[str] = Field(default_factory=list, max_length=30)
    risk_flags: list[str] = Field(default_factory=list, max_length=30)
    similarity_state: Literal["unknown", "none", "possible"] = "unknown"
    similar_content_refs: list[dict] = Field(default_factory=list, max_length=30)
    confidence: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)


def lock_opportunity(db: Session, opportunity_id: int, user: User) -> ContentOpportunity:
    # A real write lock also serializes revision/conversion races on SQLite.
    db.execute(
        update(ContentOpportunity)
        .where(ContentOpportunity.id == opportunity_id, ContentOpportunity.owner_user_id == user.id)
        .values(updated_at=utcnow())
    )
    row = owned_opportunity(db, opportunity_id, user)
    db.refresh(row)
    return row


def stable_checksum(value: dict) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()


def owned_opportunity(db: Session, opportunity_id: int, user: User, *, mutable: bool = False) -> ContentOpportunity:
    row = db.get(ContentOpportunity, opportunity_id)
    if row is None or row.owner_user_id != user.id:
        raise HTTPException(404, "内容机会不存在")
    if mutable and row.status in {"converted", "archived"}:
        raise HTTPException(409, "已转换或归档的内容机会不可修改")
    return row


def audit(db: Session, *, user: User, event: str, opportunity_id: int, detail: dict | None = None) -> AuditLog:
    row = AuditLog(
        event=event,
        actor=user.email,
        entity_type="content_opportunity",
        entity_id=str(opportunity_id),
        detail_json=detail or {},
    )
    db.add(row)
    return row


def opportunity_json(db: Session, row: ContentOpportunity) -> dict:
    return opportunity_list_json(db, [row])[0]


def opportunity_list_json(db: Session, rows: list[ContentOpportunity]) -> list[dict]:
    if not rows:
        return []
    ids = [row.id for row in rows]
    signals = {}
    for signal in db.scalars(
        select(ContentOpportunitySignal)
        .where(ContentOpportunitySignal.opportunity_id.in_(ids), ContentOpportunitySignal.status == "active")
        .order_by(ContentOpportunitySignal.id)
    ):
        signals.setdefault(signal.opportunity_id, []).append(signal)
    latest_ids = (
        select(ContentOpportunityAssessmentRevision.id)
        .where(ContentOpportunityAssessmentRevision.opportunity_id == ContentOpportunity.id)
        .order_by(ContentOpportunityAssessmentRevision.revision_no.desc())
        .limit(1)
        .correlate(ContentOpportunity)
        .scalar_subquery()
    )
    latest = {
        revision.opportunity_id: revision
        for revision in db.scalars(
            select(ContentOpportunityAssessmentRevision).where(
                ContentOpportunityAssessmentRevision.id.in_(select(latest_ids).where(ContentOpportunity.id.in_(ids)))
            )
        )
    }
    return [_opportunity_summary(row, signals.get(row.id, []), latest.get(row.id)) for row in rows]


def _opportunity_summary(row, signals, latest) -> dict:
    return {
        "id": row.id,
        "title": row.title,
        "summary": row.summary,
        "status": row.status,
        "priority": row.priority,
        "relevant_until": row.relevant_until.isoformat() if row.relevant_until else None,
        "created_by": row.created_by,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        "signal_types": sorted({signal.signal_type for signal in signals}),
        "signal_count": len(signals),
        "latest_assessment": assessment_json(latest) if latest else None,
    }


def signal_json(row: ContentOpportunitySignal) -> dict:
    return {
        "id": row.id,
        "opportunity_id": row.opportunity_id,
        "signal_type": row.signal_type,
        "source_entity_id": row.source_entity_id,
        "external_ref": row.external_ref,
        "label": row.label,
        "annotation": row.annotation_json,
        "source_checksum": row.source_checksum,
        "source_version": row.source_version,
        "observed_at": row.observed_at.isoformat() if row.observed_at else None,
        "status": row.status,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def assessment_json(row: ContentOpportunityAssessmentRevision) -> dict:
    return {
        "id": row.id,
        "opportunity_id": row.opportunity_id,
        "revision_no": row.revision_no,
        "assessment": row.assessment_json,
        "checksum": row.checksum,
        "analysis_source": row.analysis_source,
        "analysis_provider_key": row.analysis_provider_key,
        "analysis_provider_version": row.analysis_provider_version,
        "created_by": row.created_by,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def validate_assessment(db: Session, user: User, assessment: dict) -> None:
    if assessment.get("time_sensitivity") and assessment["time_sensitivity"] not in TIME_SENSITIVITY:
        raise HTTPException(422, "time_sensitivity 不受支持")
    if assessment.get("similarity_state") and assessment["similarity_state"] not in SIMILARITY_STATES:
        raise HTTPException(422, "similarity_state 不受支持")
    confidence = assessment.get("confidence")
    if confidence is not None and (not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1):
        raise HTTPException(422, "confidence 必须在 0 到 1 之间")
    refs = assessment.get("recommended_identity_refs", [])
    if not isinstance(refs, list):
        raise HTTPException(422, "recommended_identity_refs 必须是数组")
    for ref in refs:
        if not isinstance(ref, dict):
            raise HTTPException(422, "身份推荐格式无效")
        if ref.get("persona_id") is not None:
            hierarchy = content_identity.hierarchy(
                db,
                user,
                persona_id=ref["persona_id"],
                account_id=ref.get("account_id"),
                series_id=ref.get("series_id"),
                mutable=True,
            )
            if ref.get("brand_id") is not None and ref["brand_id"] != (hierarchy.brand.id if hierarchy.brand else None):
                raise HTTPException(422, "品牌与角色层级不匹配")
        elif ref.get("brand_id") is not None:
            if ref.get("account_id") or ref.get("series_id"):
                raise HTTPException(422, "账号或栏目推荐必须包含角色")
            content_identity.owned_entity(db, user, "brand", ref["brand_id"], mutable=True)
        else:
            raise HTTPException(422, "身份推荐必须包含品牌或角色")
    from .content_harness.channel_registry import list_channels

    channels = {item["channel"] for item in list_channels(db)}
    if set(assessment.get("recommended_channels", [])) - channels:
        raise HTTPException(422, "推荐渠道未注册")
    for ref in assessment.get("similar_content_refs", []):
        if set(ref) != {"project_id"} or not isinstance(ref["project_id"], int):
            raise HTTPException(422, "历史内容引用必须为 project_id")
        project = db.get(ContentProject, ref["project_id"])
        if project is None or project.owner_user_id != user.id:
            raise HTTPException(404, "历史项目不存在")


def validate_signal_reference(
    db: Session, user: User, signal_type: str, source_entity_id: int | None
) -> tuple[str | None, str | None, str]:
    if signal_type not in SIGNAL_TYPES:
        raise HTTPException(422, "signal_type 不受支持")
    if signal_type == "manual":
        if source_entity_id is not None:
            raise HTTPException(422, "人工观察不能绑定资源 ID")
        return None, None, "人工观察"
    if signal_type == "external_ref":
        if source_entity_id is not None:
            raise HTTPException(422, "外部引用不能绑定资源 ID")
        return None, None, "外部引用"
    if source_entity_id is None:
        raise HTTPException(422, "该 signal_type 必须提供 source_entity_id")
    if signal_type == "source_document":
        source = db.get(SourceDocument, source_entity_id)
        if source is None or source.is_archived:
            raise HTTPException(404, "Source 不存在或已归档")
        return source.sha256, source.as_of, source.title
    if signal_type == "data_snapshot":
        snapshot = db.get(DataSnapshot, source_entity_id)
        if snapshot is None:
            raise HTTPException(404, "DataSnapshot 不存在")
        owner = db.scalar(
            select(ContentProject.owner_user_id)
            .join(ContentUnit, ContentUnit.project_id == ContentProject.id)
            .where(ContentUnit.id == snapshot.unit_id)
        )
        if owner != user.id:
            raise HTTPException(404, "DataSnapshot 不存在")
        return snapshot.checksum, snapshot.source_version, snapshot.source_ref
    feedback = db.get(DeliveryFeedback, source_entity_id)
    if feedback is None:
        raise HTTPException(404, "DeliveryFeedback 不存在")
    target = db.get(DeliveryTarget, feedback.target_id)
    if target is None or target.content_asset_id is None:
        raise HTTPException(404, "DeliveryFeedback 所属交付不存在")
    from .project_authorization import authorize_project_target

    authorize_project_target(db, target, user)
    if target.authorized_by != user.email:
        raise HTTPException(404, "DeliveryFeedback 不存在")
    return (
        stable_checksum({"body": feedback.body, "kind": feedback.kind}),
        feedback.observed_at.isoformat() if feedback.observed_at else None,
        feedback.kind,
    )


def current_assessment(db: Session, opportunity_id: int):
    return db.scalar(
        select(ContentOpportunityAssessmentRevision)
        .where(ContentOpportunityAssessmentRevision.opportunity_id == opportunity_id)
        .order_by(ContentOpportunityAssessmentRevision.revision_no.desc())
        .limit(1)
    )


def save_assessment(
    db: Session,
    user: User,
    opportunity: ContentOpportunity,
    *,
    expected_revision: int,
    assessment: dict,
    analysis_source: str = "manual",
    provider_key: str | None = None,
    provider_version: str | None = None,
):
    opportunity = lock_opportunity(db, opportunity.id, user)
    owned_opportunity(db, opportunity.id, user, mutable=True)
    try:
        assessment = AssessmentData.model_validate(assessment).model_dump()
    except ValidationError as exc:
        raise HTTPException(422, "评估格式无效：" + str(exc)) from exc
    if len(json.dumps(assessment, ensure_ascii=False)) > 50000:
        raise HTTPException(422, "评估内容过长")
    if analysis_source != "manual" or provider_key is not None or provider_version is not None:
        raise HTTPException(422, "人工评估不能冒充自动分析来源")
    validate_assessment(db, user, assessment)
    for signal_id in assessment.get("evidence_signal_ids", []):
        signal = db.get(ContentOpportunitySignal, signal_id)
        if signal is None or signal.opportunity_id != opportunity.id:
            raise HTTPException(422, "评估引用的信号不属于该机会")
        validate_signal_reference(db, user, signal.signal_type, signal.source_entity_id)
    previous = current_assessment(db, opportunity.id)
    current_no = previous.revision_no if previous else 0
    if expected_revision != current_no:
        raise HTTPException(409, "内容机会评估已更新，请刷新后重试")
    row = ContentOpportunityAssessmentRevision(
        opportunity_id=opportunity.id,
        revision_no=current_no + 1,
        parent_revision_id=previous.id if previous else None,
        assessment_json=assessment,
        checksum=stable_checksum(assessment),
        analysis_source=analysis_source,
        analysis_provider_key=provider_key,
        analysis_provider_version=provider_version,
        created_by=user.email,
    )
    db.add(row)
    try:
        db.flush()
        audit(
            db,
            user=user,
            event="content_opportunity.assessment_created",
            opportunity_id=opportunity.id,
            detail={"revision_no": row.revision_no, "checksum": row.checksum},
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "内容机会评估已更新，请刷新后重试") from exc
    db.refresh(row)
    return row
