"""Draft-only assistance with explicit review and recoverable requests."""
from typing import Any, Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..db import get_db
from ..deps import get_current_user, require_editor
from ..services import form_assistance as service

router = APIRouter(prefix="/api/v1/form-assistance", tags=["form-assistance"])
Surface = Literal["product_creation", "product_brief", "video"]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SourceRef(Input):
    source_id: int = Field(gt=0)
    checksum: str = Field(pattern=r"^[a-f0-9]{64}$")


class MethodRef(Input):
    artifact_id: int = Field(gt=0)
    revision_id: int = Field(gt=0)
    content_hash: str = Field(pattern=r"^[a-f0-9]{64}$")


class Selection(Input):
    field_key: str = Field(max_length=200)
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    text: str = Field(max_length=20000)


class GenerateInput(Input):
    request_key: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_.:-]+$")
    surface: Surface
    mode: Literal["autofill", "polish"] = "autofill"
    project_id: int | None = Field(default=None, gt=0)
    unit_id: int | None = Field(default=None, gt=0)
    context: dict[str, Any] = Field(max_length=200)
    targets: list[str] = Field(min_length=1, max_length=100)
    skipped_keys: list[str] = Field(default_factory=list, max_length=100)
    selection: Selection | None = None
    source_refs: list[SourceRef] = Field(default_factory=list, max_length=30)
    method_refs: list[MethodRef] = Field(default_factory=list, max_length=30)
    production_stages: dict | None = None

    @model_validator(mode="after")
    def validate_stages(self):
        if self.production_stages is not None:
            from ..services.studio_creative_catalog import validate_production_stages

            validate_production_stages(self.production_stages)
        return self


class Decision(Input):
    key: str = Field(max_length=200)
    action: Literal["adopt", "edit", "skip"]
    baseline: Any
    value: Any = None


class DecisionsInput(Input):
    expected_revision: int = Field(gt=0)
    context_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    decisions: list[Decision] = Field(min_length=1, max_length=100)


class Reuse(Input):
    rule: str = Field(min_length=1, max_length=4000)
    name: str = Field(min_length=1, max_length=255)
    scope_type: Literal["owner", "project"]
    category: str | None = Field(default=None, max_length=300)
    style_revision_id: int | None = Field(default=None, gt=0)
    stage: str | None = Field(default=None, max_length=100)


class FeedbackInput(Input):
    expected_revision: int = Field(gt=0)
    request_key: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_.:-]+$")
    context: dict[str, Any] = Field(max_length=200)
    keys: list[str] | None = Field(default=None, max_length=100)
    reason: str = Field(min_length=1, max_length=4000)
    correction_target: Literal["product_fact", "category_method", "presentation_style", "stage_method"] = "presentation_style"
    reuse: Reuse | None = None


@router.get("/fields")
def fields(surface: Surface):
    return service.field_catalog(surface)


@router.get("/styles")
def styles(project_id: int | None = None, db=Depends(get_db), user=Depends(get_current_user)):
    return service.styles(db, user, project_id)


@router.post("")
async def generate(payload: GenerateInput, db=Depends(get_db), user=Depends(require_editor)):
    return await service.generate(db, user, payload.model_dump(mode="json"))


@router.get("")
def sessions(surface: Surface, project_id: int | None = None, unit_id: int | None = None,
             limit: int = Query(20, ge=1, le=100), db=Depends(get_db), user=Depends(get_current_user)):
    return service.list_sessions(db, user, surface, project_id, unit_id, limit)


@router.get("/{session_id}")
def get_session(session_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    return service.read(db, user, session_id)


@router.post("/{session_id}/decisions")
def decisions(session_id: int, payload: DecisionsInput, db=Depends(get_db), user=Depends(require_editor)):
    return service.decide(db, user, session_id, payload.model_dump(mode="json"))


@router.post("/{session_id}/feedback")
async def feedback(session_id: int, payload: FeedbackInput, db=Depends(get_db), user=Depends(require_editor)):
    return await service.feedback(db, user, session_id, payload.model_dump(mode="json"))
