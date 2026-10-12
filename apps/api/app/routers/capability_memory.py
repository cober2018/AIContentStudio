"""Explicit Capability Memory management; all writes require an editor."""

import json
from typing import Literal

from fastapi import APIRouter, Depends, Query
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from ..db import get_db
from ..deps import get_current_user, require_editor
from ..models import User
from ..services import capability_memory as service

Kind = Literal["prompt_skill", "recipe", "creative_pattern", "preference", "execution_template", "tool"]
Status = Literal["candidate", "saved", "pinned", "archived", "deprecated"]
Scope = Literal["owner", "persona", "account", "series", "project", "channel", "executor"]
Outcome = Literal["used", "accepted", "rejected", "unknown"]


class SafeCapabilityRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()

        async def safe_handler(request):
            if request.method == "POST":
                chunks, size = [], 0
                async for chunk in request.stream():
                    size += len(chunk)
                    if size > 128 * 1024:
                        return JSONResponse(status_code=422, content={"detail": {"code": "capability_input_bounds"}})
                    chunks.append(chunk)
                # Starlette's body cache lets downstream validation reuse the bounded stream.
                request._body = b"".join(chunks)
                def object_pairs(pairs):
                    result = {}
                    for key, value in pairs:
                        if key in result:
                            raise ValueError("duplicate_json_key")
                        result[key] = value
                    return result
                def constant(_value):
                    raise ValueError("non_finite_json")
                try:
                    json.loads(request._body, object_pairs_hook=object_pairs, parse_constant=constant)
                except (ValueError, UnicodeError, RecursionError):
                    return JSONResponse(status_code=422, content={"detail": {"code": "capability_input_invalid"}})
            try:
                return await handler(request)
            except RequestValidationError:
                # Rejected request values can contain credentials; never echo validation inputs.
                return JSONResponse(status_code=422, content={"detail": {"code": "capability_input_invalid"}})
        return safe_handler


router = APIRouter(prefix="/api/v1/capability-memory", tags=["capability-memory"], route_class=SafeCapabilityRoute)


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ArtifactInput(Input):
    kind: Kind
    name: str = Field(min_length=1, max_length=255)
    content: dict
    args_schema: dict = Field(default_factory=dict)


class CreateInput(ArtifactInput):
    scope_type: Scope = "owner"
    scope: dict = Field(default_factory=dict)


class RevisionInput(Input):
    expected_revision: int = Field(ge=1)
    content: dict
    args_schema: dict = Field(default_factory=dict)


class LifecycleInput(Input):
    expected_revision: int = Field(ge=1)
    status: Status
    scope_type: Scope | None = None
    scope: dict | None = None
    confirm_scope_broadening: bool = False
    name: str | None = Field(default=None, min_length=1, max_length=255)


class UseInput(Input):
    artifact_revision_id: int = Field(ge=1)
    arguments: dict = Field(default_factory=dict)
    project_id: int | None = Field(default=None, ge=1)
    unit_id: int | None = Field(default=None, ge=1)
    execution_id: int | None = Field(default=None, ge=1)


class OutcomeInput(Input):
    outcome: Outcome
    expected_outcome: Outcome


class ExecutionCaptureInput(ArtifactInput):
    execution_id: int = Field(ge=1)


class LearningCaptureInput(ArtifactInput):
    learning_candidate_id: int = Field(ge=1)
    expected_learning_revision: int = Field(ge=1)


class PreferenceEditInput(Input):
    master_revision_id: int = Field(ge=1)
    revision_no: int = Field(ge=2)
    payload_hash: str = Field(pattern="^[0-9a-f]{64}$")
    context_hash: str = Field(pattern="^[0-9a-f]{64}$")
    parent_revision_id: int = Field(ge=1)
    parent_payload_hash: str = Field(pattern="^[0-9a-f]{64}$")
    parent_context_hash: str = Field(pattern="^[0-9a-f]{64}$")


class PreferenceCaptureInput(Input):
    project_id: int = Field(ge=1)
    unit_id: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=255)
    preference: str = Field(min_length=1, max_length=2048)
    edits: list[PreferenceEditInput] = Field(min_length=2, max_length=20)


class ImportInput(ArtifactInput):
    schema_version: Literal["capability.memory.export.v1"] = Field(alias="schema")


@router.get("", include_in_schema=False)
@router.get("/")
def list_artifacts(status: Status | None = None, kind: Kind | None = None, scope_type: Scope | None = None,
                   q: str = Query("", max_length=500), tag: str = Query("", max_length=100),
                   limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0),
                   db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    data = {"status": status, "kind": kind, "scope_type": scope_type, "q": q, "tag": tag,
        "limit": limit, "offset": offset}
    return service.list_artifacts(db, user, {key: value for key, value in data.items() if value is not None})


@router.get("/discover")
def discover(project_id: int = Query(ge=1), unit_id: int = Query(ge=1),
             execution_id: int | None = Query(default=None, ge=1), kind: Kind | None = None,
             scope_type: Scope | None = None, q: str = Query("", max_length=500), tag: str = Query("", max_length=100),
             limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
             db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    data = {"project_id": project_id, "unit_id": unit_id, "execution_id": execution_id,
        "kind": kind, "scope_type": scope_type, "q": q, "tag": tag, "limit": limit, "offset": offset}
    return service.discover(db, user, {key: value for key, value in data.items() if value is not None})


@router.get("/installed-skills")
def installed_skills(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.installed_skills(db, user)


@router.post("", dependencies=[Depends(require_editor)], status_code=201, include_in_schema=False)
@router.post("/", dependencies=[Depends(require_editor)], status_code=201)
def create_artifact(body: CreateInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.create_artifact(db, user, body.model_dump())


@router.post("/capture-execution", dependencies=[Depends(require_editor)], status_code=201)
def capture_execution(body: ExecutionCaptureInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.capture_execution(db, user, body.model_dump())


@router.post("/capture-learning", dependencies=[Depends(require_editor)], status_code=201)
def capture_learning(body: LearningCaptureInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.capture_learning(db, user, body.model_dump())


@router.get("/preference-edits")
def preference_edits(project_id: int = Query(ge=1), unit_id: int = Query(ge=1),
                     limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0),
                     db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.preference_edits(db, user, {"project_id": project_id, "unit_id": unit_id,
        "limit": limit, "offset": offset})


@router.post("/capture-preference", dependencies=[Depends(require_editor)], status_code=201)
def capture_preference(body: PreferenceCaptureInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.capture_preference(db, user, body.model_dump())


@router.post("/import", dependencies=[Depends(require_editor)], status_code=201)
def import_artifact(body: ImportInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.import_artifact(db, user, body.model_dump(by_alias=True))


@router.get("/uses/{use_id}")
def get_use(use_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.get_use(db, user, use_id)


@router.post("/uses/{use_id}/outcome", dependencies=[Depends(require_editor)])
def record_outcome(use_id: int, body: OutcomeInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.record_outcome(db, user, use_id, body.model_dump())


@router.get("/{artifact_id}")
def get_artifact(artifact_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.get_artifact(db, user, artifact_id)


@router.get("/{artifact_id}/revisions")
def revisions(artifact_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.revisions(db, user, artifact_id)


@router.post("/{artifact_id}/revisions", dependencies=[Depends(require_editor)])
def update_revision(artifact_id: int, body: RevisionInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.update_revision(db, user, artifact_id, body.model_dump())


@router.post("/{artifact_id}/lifecycle", dependencies=[Depends(require_editor)])
def lifecycle(artifact_id: int, body: LifecycleInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.lifecycle(db, user, artifact_id, body.model_dump(exclude_none=True))


@router.post("/{artifact_id}/use", dependencies=[Depends(require_editor)])
def use_artifact(artifact_id: int, body: UseInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.use_artifact(db, user, artifact_id, body.model_dump(exclude_none=True))


@router.get("/{artifact_id}/export")
def export_artifact(artifact_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.export_artifact(db, user, artifact_id)
