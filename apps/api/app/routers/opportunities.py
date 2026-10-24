"""FE-F5A Content Opportunity APIs."""

import json
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_db as base_get_db
from ..deps import get_current_user, require_editor
from ..models import (
    ContentOpportunity,
    ContentOpportunityAssessmentRevision,
    ContentOpportunitySignal,
    ContentProject,
    CreativeBriefRevision,
    OpportunityProjectConversion,
    ProjectSourceBinding,
    User,
    utcnow,
)
from ..services import opportunities as service
from ..services.project_brief import checksum_brief
from ..services.project_events import record_project_event

router = APIRouter(prefix="/api/v1/content-opportunities", tags=["content-opportunities"])
from .discovery import router as discovery_router

router.include_router(discovery_router)


def get_db(db: Session = Depends(base_get_db)):
    try:
        yield db
    finally:
        # Failed validation must not leave the locking write pending for reuse.
        db.rollback()


class OpportunityIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=300)
    summary: str = ""
    priority: str = "normal"
    relevant_until: datetime | None = None


class OpportunityPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = Field(default=None, min_length=1, max_length=300)
    summary: str | None = None
    priority: str | None = None
    status: str | None = None
    relevant_until: datetime | None = None


class SignalIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    signal_type: str
    source_entity_id: int | None = None
    external_ref: str | None = Field(default=None, max_length=1000)
    label: str = Field(default="", max_length=300)
    annotation: dict = Field(default_factory=dict)
    observed_at: datetime | None = None


class AssessmentIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=0)
    assessment: dict = Field(default_factory=dict)
    analysis_source: str = "manual"
    analysis_provider_key: str | None = None
    analysis_provider_version: str | None = None


class ConversionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_assessment_revision: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=100)
    title: str | None = Field(default=None, min_length=1, max_length=300)
    objective: str | None = None
    selected_signal_ids: list[int] = Field(default_factory=list)
    brief_overrides: dict = Field(default_factory=dict)


def _validate_priority(priority: str) -> None:
    if priority not in {"low", "normal", "high"}:
        raise HTTPException(422, "priority 不受支持")


@router.get("")
def list_opportunities(
    status: str | None = None,
    priority: str | None = None,
    q: str | None = None,
    signal_type: str | None = None,
    time_sensitivity: str | None = None,
    recommended_only: bool = False,
    actionable_only: bool = False,
    persona_id: int | None = None,
    business_date: date | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = (
        select(ContentOpportunity)
        .where(ContentOpportunity.owner_user_id == user.id)
        .order_by(ContentOpportunity.updated_at.desc(), ContentOpportunity.id.desc())
    )
    if persona_id is not None:
        stmt = stmt.where(ContentOpportunity.persona_id == persona_id)
    if actionable_only:
        from ..services.opportunity_policy import TECH, persona_policy

        if persona_id is None or persona_policy(db, user.id, persona_id) != TECH:
            raise HTTPException(422, "有效建议筛选需要明确选择科技角色")
        stmt = stmt.where(ContentOpportunity.status.in_(["new", "qualified"]),
                          ContentOpportunity.relevant_until > utcnow())
    if business_date is not None:
        stmt = stmt.where(ContentOpportunity.business_date == business_date.isoformat())
    if status:
        if status not in service.TRIAGE_STATUSES | {"archived", "converted"}:
            raise HTTPException(422, "机会状态不受支持")
        stmt = stmt.where(ContentOpportunity.status == status)
    if recommended_only:
        stmt = stmt.where(ContentOpportunity.status.in_(["new", "qualified"]))
    if priority:
        _validate_priority(priority)
        stmt = stmt.where(ContentOpportunity.priority == priority)
    if q:
        stmt = stmt.where(ContentOpportunity.title.ilike(f"%{q}%"))
    if signal_type:
        if signal_type not in service.SIGNAL_TYPES:
            raise HTTPException(422, "信号类型不受支持")
        stmt = stmt.where(
            select(ContentOpportunitySignal.id)
            .where(
                ContentOpportunitySignal.opportunity_id == ContentOpportunity.id,
                ContentOpportunitySignal.signal_type == signal_type,
                ContentOpportunitySignal.status == "active",
            )
            .exists()
        )
    if time_sensitivity:
        if time_sensitivity not in service.TIME_SENSITIVITY:
            raise HTTPException(422, "时间敏感性不受支持")
        latest = (
            select(ContentOpportunityAssessmentRevision.assessment_json["time_sensitivity"].as_string())
            .where(ContentOpportunityAssessmentRevision.opportunity_id == ContentOpportunity.id)
            .order_by(ContentOpportunityAssessmentRevision.revision_no.desc())
            .limit(1)
            .scalar_subquery()
        )
        stmt = stmt.where(latest == time_sensitivity)
    rows = db.scalars(stmt.offset(offset).limit(limit + 1)).all()
    return {
        "items": service.opportunity_list_json(db, rows[:limit]),
        "offset": offset,
        "limit": limit,
        "has_more": len(rows) > limit,
    }


@router.post("", status_code=201)
def create_opportunity(payload: OpportunityIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    _validate_priority(payload.priority)
    row = ContentOpportunity(
        owner_user_id=user.id,
        title=payload.title,
        summary=payload.summary,
        priority=payload.priority,
        relevant_until=payload.relevant_until,
        created_by=user.email,
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    db.add(row)
    db.flush()
    service.audit(db, user=user, event="content_opportunity.created", opportunity_id=row.id)
    db.commit()
    db.refresh(row)
    return service.opportunity_json(db, row)


@router.get("/{opportunity_id}")
def get_opportunity(opportunity_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.opportunity_json(db, service.owned_opportunity(db, opportunity_id, user))


@router.patch("/{opportunity_id}")
def patch_opportunity(
    payload: OpportunityPatch, opportunity_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)
):
    service.lock_opportunity(db, opportunity_id, user)
    row = service.owned_opportunity(db, opportunity_id, user, mutable=True)
    data = payload.model_dump(exclude_unset=True)
    if any(value is None for key, value in data.items() if key != "relevant_until"):
        raise HTTPException(422, "必填字段不能设为 null")
    if "priority" in data:
        _validate_priority(data["priority"])
    if data.get("status") is not None and data["status"] not in service.TRIAGE_STATUSES:
        raise HTTPException(422, "converted/archived 只能由专用操作产生")
    for field, value in data.items():
        setattr(row, field, value)
    service.audit(
        db,
        user=user,
        event="content_opportunity.triaged",
        opportunity_id=row.id,
        detail={"changed_fields": sorted(data), "status": row.status},
    )
    db.commit()
    return service.opportunity_json(db, row)


@router.delete("/{opportunity_id}", status_code=204)
def archive_opportunity(opportunity_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    row = service.lock_opportunity(db, opportunity_id, user)
    if row.status == "archived":
        return
    row.status = "archived"
    row.archived_at = utcnow()
    service.audit(db, user=user, event="content_opportunity.archived", opportunity_id=row.id)
    db.commit()


@router.get("/{opportunity_id}/signals")
def list_signals(opportunity_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service.owned_opportunity(db, opportunity_id, user)
    rows = db.scalars(
        select(ContentOpportunitySignal)
        .where(ContentOpportunitySignal.opportunity_id == opportunity_id)
        .order_by(ContentOpportunitySignal.id.desc())
    ).all()
    return [service.signal_json(row) for row in rows]


@router.post("/{opportunity_id}/signals", status_code=201)
def add_signal(
    payload: SignalIn, opportunity_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)
):
    service.lock_opportunity(db, opportunity_id, user)
    opportunity = service.owned_opportunity(db, opportunity_id, user, mutable=True)
    checksum, version, inferred_label = service.validate_signal_reference(
        db, user, payload.signal_type, payload.source_entity_id
    )
    if len(json.dumps(payload.annotation, ensure_ascii=False)) > 5000:
        raise HTTPException(422, "信号注释过长")
    if payload.signal_type == "external_ref" and not payload.external_ref:
        raise HTTPException(422, "外部引用必须提供 external_ref")
    if payload.signal_type != "external_ref" and payload.external_ref is not None:
        raise HTTPException(422, "该信号不接受 external_ref")
    row = None
    if payload.source_entity_id is not None:
        row = db.scalar(
            select(ContentOpportunitySignal).where(
                ContentOpportunitySignal.opportunity_id == opportunity.id,
                ContentOpportunitySignal.signal_type == payload.signal_type,
                ContentOpportunitySignal.source_entity_id == payload.source_entity_id,
            )
        )
    elif payload.signal_type == "external_ref":
        row = db.scalar(
            select(ContentOpportunitySignal).where(
                ContentOpportunitySignal.opportunity_id == opportunity.id,
                ContentOpportunitySignal.signal_type == payload.signal_type,
                ContentOpportunitySignal.external_ref == payload.external_ref,
            )
        )
    if row is not None:
        row.status = "active"
        row.detached_at = None
    else:
        row = ContentOpportunitySignal(
            opportunity_id=opportunity.id,
            signal_type=payload.signal_type,
            source_entity_id=payload.source_entity_id,
            external_ref=payload.external_ref,
            label=payload.label or inferred_label,
            annotation_json=payload.annotation,
            source_checksum=checksum,
            source_version=version,
            observed_at=payload.observed_at,
            status="active",
            attached_by=user.email,
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return service.signal_json(row)


@router.delete("/{opportunity_id}/signals/{signal_id}", status_code=204)
def detach_signal(
    opportunity_id: int, signal_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)
):
    service.lock_opportunity(db, opportunity_id, user)
    service.owned_opportunity(db, opportunity_id, user, mutable=True)
    row = db.get(ContentOpportunitySignal, signal_id)
    if row is None or row.opportunity_id != opportunity_id:
        raise HTTPException(404, "机会信号不存在")
    row.status = "detached"
    row.detached_at = utcnow()
    db.commit()


@router.get("/{opportunity_id}/assessments")
def list_assessments(opportunity_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service.owned_opportunity(db, opportunity_id, user)
    return [
        service.assessment_json(row)
        for row in db.scalars(
            select(ContentOpportunityAssessmentRevision)
            .where(ContentOpportunityAssessmentRevision.opportunity_id == opportunity_id)
            .order_by(ContentOpportunityAssessmentRevision.revision_no.desc())
        ).all()
    ]


@router.get("/{opportunity_id}/assessments/{revision_id}")
def get_assessment(
    opportunity_id: int, revision_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    service.owned_opportunity(db, opportunity_id, user)
    row = db.get(ContentOpportunityAssessmentRevision, revision_id)
    if row is None or row.opportunity_id != opportunity_id:
        raise HTTPException(404, "评估版本不存在")
    return service.assessment_json(row)


@router.post("/{opportunity_id}/assessments", status_code=201)
def save_assessment(
    payload: AssessmentIn, opportunity_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)
):
    return service.assessment_json(
        service.save_assessment(
            db,
            user,
            service.owned_opportunity(db, opportunity_id, user, mutable=True),
            expected_revision=payload.expected_revision,
            assessment=payload.assessment,
            analysis_source=payload.analysis_source,
            provider_key=payload.analysis_provider_key,
            provider_version=payload.analysis_provider_version,
        )
    )


@router.post("/{opportunity_id}/analyze")
def analyze(opportunity_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    service.owned_opportunity(db, opportunity_id, user, mutable=True)
    return {"status": "capability_unavailable", "capability": "opportunity_analysis"}


@router.get("/{opportunity_id}/conversion")
def get_conversion(opportunity_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service.owned_opportunity(db, opportunity_id, user)
    row = db.scalar(
        select(OpportunityProjectConversion).where(OpportunityProjectConversion.opportunity_id == opportunity_id)
    )
    return (
        {
            "id": row.id,
            "project_id": row.project_id,
            "assessment_revision_id": row.assessment_revision_id,
            "idempotency_key": row.idempotency_key,
        }
        if row
        else None
    )


@router.post("/{opportunity_id}/convert-to-project", status_code=201)
def convert_to_project(
    payload: ConversionIn, opportunity_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)
):
    try:
        return _convert_to_project(payload, opportunity_id, db, user)
    except Exception:
        db.rollback()
        raise


def _convert_to_project(payload: ConversionIn, opportunity_id: int, db: Session, user: User):
    opportunity = service.lock_opportunity(db, opportunity_id, user)
    existing = db.scalar(
        select(OpportunityProjectConversion).where(OpportunityProjectConversion.opportunity_id == opportunity.id)
    )
    if existing:
        db.rollback()
        return {"project_id": existing.project_id, "conversion_id": existing.id, "idempotent": True}
    service.owned_opportunity(db, opportunity_id, user, mutable=True)
    if db.scalar(
        select(OpportunityProjectConversion.id).where(
            OpportunityProjectConversion.idempotency_key == payload.idempotency_key
        )
    ):
        raise HTTPException(409, "转换幂等键已使用")
    if opportunity.status != "qualified":
        raise HTTPException(409, "只有 qualified 内容机会可以转换为项目")
    assessment = service.current_assessment(db, opportunity.id)
    if assessment is None or assessment.revision_no != payload.expected_assessment_revision:
        raise HTTPException(409, "请使用当前内容机会评估版本转换")
    selected = []
    if payload.selected_signal_ids:
        selected = db.scalars(
            select(ContentOpportunitySignal).where(
                ContentOpportunitySignal.opportunity_id == opportunity.id,
                ContentOpportunitySignal.id.in_(payload.selected_signal_ids),
                ContentOpportunitySignal.status == "active",
            )
        ).all()
        if len(selected) != len(set(payload.selected_signal_ids)):
            raise HTTPException(422, "选择的机会信号无效")
        if any(signal.signal_type != "source_document" or signal.source_entity_id is None for signal in selected):
            raise HTTPException(422, "只有 SourceDocument 信号可以绑定到项目来源")
        for signal in selected:
            service.validate_signal_reference(db, user, signal.signal_type, signal.source_entity_id)
    data = assessment.assessment_json
    service.validate_assessment(db, user, data)
    brief_data = {
        "objective": payload.objective or data.get("objective") or opportunity.summary or opportunity.title,
        "primary_audience": data.get("audience_fit"),
        "core_message": data.get("core_message"),
        "angle": data.get("suggested_angle"),
        "required_evidence": data.get("evidence_summary", [])
        + [f"suggested:opportunity_signal:{signal_id}" for signal_id in data.get("evidence_signal_ids", [])],
        "content_constraints": [],
        "identity_scope": data.get("recommended_identity_refs", []),
        "modality_scope": data.get("recommended_modalities", []),
        "channel_scope": data.get("recommended_channels", []),
        "cta": None,
        "references": [{"opportunity_id": opportunity.id, "assessment_revision": assessment.revision_no}],
    }
    from .content_projects import BriefRevisionIn

    try:
        brief_payload = BriefRevisionIn.model_validate(
            {**brief_data, **payload.brief_overrides, "expected_revision": 0}
        )
    except ValueError as exc:
        raise HTTPException(422, "项目简报覆盖无效") from exc
    if set(payload.brief_overrides) - set(brief_data):
        raise HTTPException(422, "简报覆盖字段不受支持")
    brief_data = brief_payload.model_dump(exclude={"expected_revision"})
    try:
        scope = service.AssessmentData.model_validate(
            {
                "why_now": "转换范围校验",
                "recommended_identity_refs": brief_data["identity_scope"],
                "recommended_modalities": brief_data["modality_scope"],
                "recommended_channels": brief_data["channel_scope"],
            }
        ).model_dump()
    except ValueError as exc:
        raise HTTPException(422, "项目简报范围格式无效") from exc
    service.validate_assessment(db, user, scope)
    brief_data["identity_scope"] = [
        {key: value for key, value in ref.items() if value is not None} for ref in scope["recommended_identity_refs"]
    ]
    project = ContentProject(
        owner_user_id=user.id,
        title=payload.title or opportunity.title,
        objective=brief_data["objective"],
        status="draft",
    )
    db.add(project)
    db.flush()
    brief = CreativeBriefRevision(
        project_id=project.id,
        revision_no=1,
        parent_revision_id=None,
        objective=brief_data["objective"],
        primary_audience=brief_data["primary_audience"],
        core_message=brief_data["core_message"],
        angle=brief_data["angle"],
        required_evidence_json=brief_data["required_evidence"],
        content_constraints_json=brief_data["content_constraints"],
        identity_scope_json=brief_data["identity_scope"],
        modality_scope_json=brief_data["modality_scope"],
        channel_scope_json=brief_data["channel_scope"],
        cta=brief_data["cta"],
        references_json=brief_data["references"],
        checksum=checksum_brief(brief_data),
        created_by=user.email,
    )
    db.add(brief)
    for signal in selected:
        db.add(
            ProjectSourceBinding(
                project_id=project.id,
                source_document_id=signal.source_entity_id,
                status="active",
                note=f"来自内容机会 #{opportunity.id}",
                attached_by=user.email,
            )
        )
    conversion = OpportunityProjectConversion(
        opportunity_id=opportunity.id,
        project_id=project.id,
        assessment_revision_id=assessment.id,
        idempotency_key=payload.idempotency_key,
        conversion_snapshot_json={
            "opportunity_id": opportunity.id,
            "title": opportunity.title,
            "assessment_revision": assessment.revision_no,
            "assessment_checksum": assessment.checksum,
            "selected_signal_ids": payload.selected_signal_ids,
            "brief": brief_data,
        },
        created_by=user.email,
    )
    db.add(conversion)
    opportunity.status = "converted"
    db.flush()
    service.audit(
        db,
        user=user,
        event="content_opportunity.converted",
        opportunity_id=opportunity.id,
        detail={"project_id": project.id, "assessment_revision_id": assessment.id},
    )
    record_project_event(
        db,
        project_id=project.id,
        event_type="project.created_from_opportunity",
        actor=user.email,
        entity_type="content_opportunity",
        entity_id=opportunity.id,
        payload={"assessment_revision_id": assessment.id, "conversion_id": conversion.id if conversion.id else None},
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "内容机会转换冲突，请刷新后重试") from exc
    return {
        "project_id": project.id,
        "conversion_id": conversion.id,
        "brief_revision_id": brief.id,
        "idempotent": False,
    }
