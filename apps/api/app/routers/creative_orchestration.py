"""Project-owned creative handoff and explicit human result decisions."""

import hashlib

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_editor
from ..models import MaterialRevision, User
from ..services import capability_memory, creative_execution_files, creative_executions, creative_packages
from ..services.materials import read_bytes_checked
from . import CapabilityInputRoute

router = APIRouter(prefix="/api/v1/content-projects/{project_id}/units/{unit_id}", tags=["creative-orchestration"], route_class=CapabilityInputRoute)


class CreativeInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class PackageInput(CreativeInput):
    source_master_revision_id: int | None = Field(default=None, ge=1)
    source_variant_revision_id: int | None = Field(default=None, ge=1)
    package_schema: str = Field(default="creative.execution.v1", pattern=r"^(creative.execution.v1|director.video.v1)$")
    objective: str = Field(min_length=1, max_length=2000)
    constraints: list[str] = Field(default_factory=list, max_length=50)
    output_contract: dict
    acceptance_criteria: list[str] = Field(default_factory=list, max_length=50)


class PrepareInput(CreativeInput):
    package_id: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=150)
    executor_kind: str = Field(min_length=1, max_length=30)
    executor_key: str = Field(min_length=1, max_length=150)
    executor_version: str = Field(min_length=1, max_length=50)
    retry_of_id: int | None = Field(default=None, ge=1)
    metadata: dict = Field(default_factory=dict, max_length=20)


class ExecutorInput(CreativeInput):
    expected_revision: int = Field(ge=1)
    executor_kind: str | None = Field(default=None, min_length=1, max_length=30)
    executor_key: str | None = Field(default=None, min_length=1, max_length=150)
    executor_version: str | None = Field(default=None, min_length=1, max_length=50)


class TransitionInput(ExecutorInput):
    action: str = Field(min_length=1, max_length=40)
    dispatch_certainty: str | None = Field(default=None, max_length=30)
    safe_reason: str | None = Field(default=None, max_length=100)
    metadata: dict = Field(default_factory=dict, max_length=20)
    checkpoint: dict | None = Field(default=None, max_length=20)
    recovery: dict | None = Field(default=None, max_length=20)
    observation_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    summary: str | None = Field(default=None, max_length=2000)
    resolution: str | None = Field(default=None, max_length=30)


class MaterializeInput(ExecutorInput):
    material_revision_ids: list[int] | None = Field(default=None, max_length=100)


class OutputInput(ExecutorInput):
    role_id: str = Field(min_length=1, max_length=100)
    output_index: int = Field(ge=1, le=20)
    attempt_no: int | None = Field(default=None, ge=1)
    relative_path: str = Field(min_length=1, max_length=500)
    mime_type: str = Field(min_length=1, max_length=100)
    content_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    metadata: dict = Field(default_factory=dict)


class DecisionInput(CreativeInput):
    expected_revision: int = Field(ge=1)
    decision: str = Field(pattern=r"^(accept|reject)$")
    rights: dict = Field(default_factory=dict)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    attach_to_project: bool = False
    reusable_artifact: dict | None = Field(default=None, max_length=10)


class CleanupInput(CreativeInput):
    expected_revision: int = Field(ge=1)
    confirm_temporary_only: bool


class ManualImageInput(CreativeInput):
    source_master_revision_id: int | None = Field(default=None, ge=1)
    source_variant_revision_id: int | None = Field(default=None, ge=1)
    brief: str = Field(min_length=1, max_length=2000)
    style: str = Field(min_length=1, max_length=1000)
    usage: str = Field(min_length=1, max_length=500)
    aspect_ratio: str = Field(min_length=3, max_length=5)
    width: int = Field(ge=256, le=4096)
    height: int = Field(ge=256, le=4096)
    candidate_count: int = Field(ge=1, le=4)
    idempotency_key: str = Field(min_length=1, max_length=150)


@router.post("/manual-chatgpt-images/prepare", dependencies=[Depends(require_editor)], status_code=201)
def prepare_manual_image(project_id: int, unit_id: int, body: ManualImageInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return creative_executions.prepare_manual_image(db, project_id, unit_id, body.model_dump(exclude_none=True), user)


@router.post("/manual-chatgpt-images/{execution_id}/uploads", dependencies=[Depends(require_editor)])
async def upload_manual_image(project_id: int, unit_id: int, execution_id: int,
        file: UploadFile = File(...), expected_revision: int = Form(..., ge=1), output_index: int = Form(..., ge=1, le=4),
        db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        content = await file.read(10 * 1024 * 1024 + 1)
        # PIL 全量解码是重活，放线程池避免阻塞事件循环
        return await run_in_threadpool(
            creative_executions.upload_manual_image, db, project_id, unit_id, execution_id,
            {"expected_revision": expected_revision, "output_index": output_index}, content, file.content_type or "", user)
    finally:
        await file.close()


@router.post("/manual-chatgpt-images/{execution_id}/outputs/{output_id}/accept", dependencies=[Depends(require_editor)])
def accept_manual_image(project_id: int, unit_id: int, execution_id: int, output_id: int, body: DecisionInput,
        db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if body.reusable_artifact is not None:
        raise HTTPException(422, {"code": "manual_image_capture_not_supported"})
    return creative_executions.accept_manual_image(db, project_id, unit_id, execution_id, output_id,
        body.model_dump(exclude_none=True, exclude={"reusable_artifact"}), user)


@router.post("/creative-packages", dependencies=[Depends(require_editor)], status_code=201)
def create_package(project_id: int, unit_id: int, body: PackageInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return creative_packages.create_package(db, project_id=project_id, unit_id=unit_id, user=user, payload=body.model_dump(exclude_none=True))


@router.get("/creative-packages")
def list_packages(project_id: int, unit_id: int, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {"items": creative_packages.list_packages(db, project_id, unit_id, user, limit=limit, offset=offset), "limit": limit, "offset": offset}


@router.get("/creative-packages/{package_id}")
def read_package(project_id: int, unit_id: int, package_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return creative_packages.get_package(db, project_id, unit_id, package_id, user)


@router.post("/creative-executions", dependencies=[Depends(require_editor)], status_code=201)
def prepare_execution(project_id: int, unit_id: int, body: PrepareInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return creative_executions.prepare_execution(db, project_id, unit_id, body.model_dump(exclude_none=True), user)


@router.get("/creative-executions")
def list_executions(project_id: int, unit_id: int, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return creative_executions.list_executions(db, project_id, unit_id, user, limit=limit, offset=offset)


@router.get("/creative-executions/{execution_id}")
def read_execution(project_id: int, unit_id: int, execution_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return creative_executions.get_execution(db, project_id, unit_id, execution_id, user)


@router.post("/creative-executions/{execution_id}/transition", dependencies=[Depends(require_editor)])
def transition(project_id: int, unit_id: int, execution_id: int, body: TransitionInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return creative_executions.transition_execution(db, project_id, unit_id, execution_id, body.model_dump(exclude_none=True), user)


@router.post("/creative-executions/{execution_id}/materialize-inputs", dependencies=[Depends(require_editor)])
def materialize(project_id: int, unit_id: int, execution_id: int, body: MaterializeInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return creative_executions.materialize_inputs(db, project_id, unit_id, execution_id, body.model_dump(exclude_none=True), user)


@router.post("/creative-executions/{execution_id}/outputs", dependencies=[Depends(require_editor)], status_code=201)
def submit_output(project_id: int, unit_id: int, execution_id: int, body: OutputInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return creative_executions.submit_output(db, project_id, unit_id, execution_id, body.model_dump(exclude_none=True), user)


@router.post("/creative-executions/{execution_id}/outputs/{output_id}/decision", dependencies=[Depends(require_editor)])
def decide_output(project_id: int, unit_id: int, execution_id: int, output_id: int, body: DecisionInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    payload = body.model_dump(exclude_none=True, exclude={"reusable_artifact"})
    result = creative_executions.decide_output(db, project_id, unit_id, execution_id, output_id, payload, user)
    if body.reusable_artifact is not None and body.decision == "accept":
        # Capture is a separate transaction so an unsafe method cannot undo accepted material.
        if result["state"] != "accepted":
            result["capability_capture"] = {"status": "deferred", "code": "execution_not_fully_accepted"}
        else:
            try:
                artifact = capability_memory.capture_execution(db, user,
                    {**body.reusable_artifact, "execution_id": execution_id})
                result["capability_capture"] = {"status": "candidate", "artifact_id": artifact["id"]}
            except Exception:  # noqa: BLE001 Do not leak rejected method content or rewrite the successful result.
                db.rollback()
                result["capability_capture"] = {"status": "rejected", "code": "capability_capture_rejected"}
    return result


@router.post("/creative-executions/{execution_id}/outputs/{output_id}/cleanup", dependencies=[Depends(require_editor)])
def cleanup_output(project_id: int, unit_id: int, execution_id: int, output_id: int, body: CleanupInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return creative_executions.cleanup_output(db, project_id, unit_id, execution_id, output_id, body.model_dump(), user)


@router.get("/creative-executions/{execution_id}/outputs/{output_id}/content")
def read_output(project_id: int, unit_id: int, execution_id: int, output_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    execution = creative_executions.get_execution(db, project_id, unit_id, execution_id, user)
    output = next((item for item in execution["outputs"] if item["id"] == output_id), None)
    if output is None:
        raise HTTPException(404, {"code": "creative_output_not_found"})
    if output["state"] == "accepted":
        revision = db.get(MaterialRevision, output["material_revision_id"])
        provenance = revision.source_metadata_json if revision is not None else {}
        expected = {"execution_id": execution_id, "output_id": output_id,
                    "package_id": execution["package_id"], "package_hash": execution["package_hash"],
                    "owner_user_id": user.id, "project_id": project_id, "content_unit_id": unit_id,
                    "output_hash": output["content_hash"]}
        if (revision is None or revision.source_kind != "external_execution"
                or not isinstance(provenance, dict)
                or any(provenance.get(key) != value for key, value in expected.items())):
            raise HTTPException(409, {"code": "creative_output_material_integrity"})
        content = read_bytes_checked(db, revision)
    else:
        content = creative_execution_files.read_file(user.id, execution_id, output["staging_key"])
    if hashlib.sha256(content).hexdigest() != output["content_hash"] or len(content) != output["size_bytes"]:
        raise HTTPException(409, {"code": "creative_output_hash_mismatch"})
    return Response(content, media_type=output["mime_type"], headers={"X-Content-Type-Options": "nosniff", "Content-Disposition": f'attachment; filename="output-{output_id}.bin"'})
