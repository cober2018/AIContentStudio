"""Learning candidates, immutable Insights and explicit Content Memory APIs."""

import json
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db as base_get_db
from ..deps import get_current_user, require_editor
from ..models import ContentInsight, ContentMemoryEntry, LearningCandidate, User
from ..services import content_learning as service

router = APIRouter(prefix="/api/v1", tags=["learning"])

Category = Literal["identity", "audience", "channel", "format", "topic", "workflow"]
ScopeType = Literal["owner", "brand", "persona", "account", "series"]
EvidenceType = Literal["published_content", "performance_observation", "insight", "delivery_feedback"]
MemoryType = Literal[
    "historical_viewpoint",
    "audience_learning",
    "channel_experience",
    "editorial_preference",
    "validated_strategy",
    "workflow_learning",
    "topic_learning",
]
Statement = Annotated[str, Field(min_length=1, max_length=10000)]
Limitations = Annotated[list[Annotated[str, Field(min_length=1, max_length=2000)]], Field(max_length=100)]


def get_db(db: Session = Depends(base_get_db)):
    try:
        yield db
    finally:
        # HTTP validation failures must release CAS/row locks and partial writes.
        db.rollback()


class BoundedInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @model_validator(mode="after")
    def bounded_json(self):
        payload = self.model_dump(mode="json")
        if len(json.dumps(payload, ensure_ascii=False, allow_nan=False)) > 50000:
            raise ValueError("请求内容超过 50000 字符")

        def check(value, depth=0):
            if depth > 10:
                raise ValueError("嵌套内容过深")
            if isinstance(value, str) and len(value) > 10000:
                raise ValueError("文本内容过长")
            if isinstance(value, (dict, list)):
                if len(value) > 200:
                    raise ValueError("集合内容过多")
                for child in value.values() if isinstance(value, dict) else value:
                    check(child, depth + 1)

        check(payload)
        return self


class EvidenceRef(BoundedInput):
    evidence_type: EvidenceType
    entity_id: int = Field(gt=0, strict=True)


class InsightInput(BoundedInput):
    insight_type: Literal["identity", "audience", "channel", "format", "topic", "workflow", "general"] = "general"
    statement: Statement
    scope: dict = Field(default_factory=dict)
    cohort: dict = Field(default_factory=dict)
    coverage: dict = Field(default_factory=dict)
    supporting_refs: list[EvidenceRef] = Field(default_factory=list, max_length=100)
    contradicting_refs: list[EvidenceRef] = Field(default_factory=list, max_length=100)
    limitations: Limitations = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    analysis_source: Literal["manual", "rule", "model"] = "manual"
    provider_key: str | None = Field(default=None, max_length=150)
    provider_version: str | None = Field(default=None, max_length=50)
    supersedes_id: int | None = Field(default=None, gt=0, strict=True)


class CandidateInput(BoundedInput):
    category: Category
    title: str = Field(min_length=1, max_length=500)
    proposition: Statement
    rationale: str = Field(default="", max_length=10000)
    scope: dict = Field(default_factory=dict)
    confidence: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    created_from_insight_id: int | None = Field(default=None, gt=0, strict=True)


class RevisionInput(BoundedInput):
    expected_revision: int = Field(ge=1)


class CandidatePatch(RevisionInput):
    category: Category | None = None
    title: str | None = Field(default=None, min_length=1, max_length=500)
    proposition: Statement | None = None
    rationale: str | None = Field(default=None, max_length=10000)
    scope: dict | None = None
    confidence: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)

    @model_validator(mode="after")
    def non_null_fields(self):
        if any(getattr(self, key) is None for key in self.model_fields_set - {"confidence"}):
            raise ValueError("字段不能为 null")
        return self


class EvidenceInput(RevisionInput):
    evidence_type: EvidenceType
    entity_id: int = Field(gt=0, strict=True)
    role: Literal["support", "contradict", "context"]
    note: str | None = Field(default=None, max_length=10000)


class ValidationInput(RevisionInput):
    decision: Literal["accepted", "rejected", "collecting"]
    validation_method: Literal["human", "rule", "experiment", "multi_sample"]
    validation_summary: dict


class PromotionInput(BoundedInput):
    idempotency_key: str = Field(min_length=1, max_length=100)
    scope_type: ScopeType
    scope_id: int | None = Field(default=None, gt=0, strict=True)
    memory_type: MemoryType
    statement: Statement
    applicability: dict = Field(default_factory=dict)
    limitations: Limitations = Field(default_factory=list)


class MemoryInput(PromotionInput):
    source_learning_candidate_id: int = Field(gt=0, strict=True)


class MemoryRevisionInput(RevisionInput):
    statement: Statement
    source_learning_candidate_id: int = Field(gt=0, strict=True)
    applicability: dict = Field(default_factory=dict)
    limitations: Limitations = Field(default_factory=list)


@router.get("/learning/insights")
def insights(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(ContentInsight).where(ContentInsight.owner_user_id == user.id).order_by(ContentInsight.id.desc())
    return service.page(db, stmt, limit, offset)


@router.post("/learning/insights", status_code=201)
def create_insight(payload: InsightInput, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return service.save_insight(db, user, payload.model_dump())


@router.post("/learning/insights/analyze")
def analyze_insight(user: User = Depends(require_editor)):
    return {"status": "capability_unavailable", "reason": "没有已验证的自动分析服务"}


@router.get("/learning/insights/{insight_id}")
def insight_detail(insight_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.document(service.owned(db, ContentInsight, insight_id, user))


@router.get("/learning-candidates")
def candidates(
    status: Literal["collecting", "ready_for_review", "accepted", "rejected", "archived"] | None = None,
    category: Category | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(LearningCandidate).where(LearningCandidate.owner_user_id == user.id)
    if status:
        stmt = stmt.where(LearningCandidate.status == status)
    if category:
        stmt = stmt.where(LearningCandidate.category == category)
    return service.page(
        db, stmt.order_by(LearningCandidate.id.desc()), limit, offset, lambda row: service.candidate_detail(db, row)
    )


@router.post("/learning-candidates", status_code=201)
def create_candidate(payload: CandidateInput, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return service.create_candidate(db, user, payload.model_dump())


@router.get("/learning-candidates/{candidate_id}")
def candidate_detail(candidate_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.candidate_detail(db, service.owned(db, LearningCandidate, candidate_id, user))


@router.patch("/learning-candidates/{candidate_id}")
def patch_candidate(
    candidate_id: int, payload: CandidatePatch, db: Session = Depends(get_db), user: User = Depends(require_editor)
):
    return service.patch_candidate(db, user, candidate_id, payload.model_dump(exclude_unset=True))


@router.post("/learning-candidates/{candidate_id}/evidence", status_code=201)
def add_evidence(
    candidate_id: int, payload: EvidenceInput, db: Session = Depends(get_db), user: User = Depends(require_editor)
):
    return service.add_evidence(db, user, candidate_id, payload.model_dump())


@router.post("/learning-candidates/{candidate_id}/submit-review")
def submit(
    candidate_id: int, payload: RevisionInput, db: Session = Depends(get_db), user: User = Depends(require_editor)
):
    return service.submit(db, user, candidate_id, payload.expected_revision)


@router.post("/learning-candidates/{candidate_id}/validate")
def validate(
    candidate_id: int, payload: ValidationInput, db: Session = Depends(get_db), user: User = Depends(require_editor)
):
    return service.decide(db, user, candidate_id, payload.model_dump())


@router.delete("/learning-candidates/{candidate_id}", status_code=204)
def archive_candidate(
    candidate_id: int,
    expected_revision: int = Query(..., ge=1),
    db: Session = Depends(get_db),
    user: User = Depends(require_editor),
):
    service.archive_candidate(db, user, candidate_id, expected_revision)
    return Response(status_code=204)


@router.post("/learning-candidates/{candidate_id}/promote-to-memory", status_code=201)
def promote(
    candidate_id: int, payload: PromotionInput, db: Session = Depends(get_db), user: User = Depends(require_editor)
):
    return service.promote(db, user, candidate_id, payload.model_dump())


@router.get("/content-memory")
def memories(
    scope_type: ScopeType | None = None,
    scope_id: int | None = Query(None, gt=0),
    include_ancestors: bool = False,
    status: Literal["active", "archived"] | None = "active",
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.list_memory(db, user, limit, offset, scope_type, scope_id, include_ancestors, status)


@router.post("/content-memory", status_code=201)
def create_memory(payload: MemoryInput, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    data = payload.model_dump()
    return service.promote(db, user, data.pop("source_learning_candidate_id"), data)


@router.get("/content-memory/{memory_id}")
def memory_detail(memory_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.memory_detail(db, service.owned(db, ContentMemoryEntry, memory_id, user))


@router.get("/content-memory/{memory_id}/revisions")
def memory_revisions(
    memory_id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service.owned(db, ContentMemoryEntry, memory_id, user)
    return service.page(db, service.memory_revisions(db, memory_id), limit, offset)


@router.post("/content-memory/{memory_id}/revisions", status_code=201)
def revise_memory(
    memory_id: int, payload: MemoryRevisionInput, db: Session = Depends(get_db), user: User = Depends(require_editor)
):
    return service.revise_memory(db, user, memory_id, payload.model_dump())


@router.delete("/content-memory/{memory_id}", status_code=204)
def archive_memory(memory_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    service.archive_memory(db, user, memory_id)
    return Response(status_code=204)
