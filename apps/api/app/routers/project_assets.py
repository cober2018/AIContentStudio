"""Project references to existing MaterialRevision rows."""

import hashlib
import logging
import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import require_editor
from ..models import AuditLog, MaterialRevision, ProjectMaterialReference, User, utcnow
from ..services import materials as materials_service
from ..services.project_assets import reference_json
from ..services.project_events import record_project_event
from .content_projects import mutable_project

router = APIRouter(prefix="/api/v1/content-projects", tags=["content-project-assets"])
logger = logging.getLogger(__name__)


class MaterialReferenceIn(BaseModel):
    material_revision_id: int
    note: str | None = None


@router.post("/{project_id}/materials/references", status_code=201)
def attach_material_reference(payload: MaterialReferenceIn, project_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    mutable_project(db, project_id, user)
    revision = db.get(MaterialRevision, payload.material_revision_id)
    if revision is None or revision.material is None or revision.material.status != "active":
        raise HTTPException(404, "素材版本不存在")
    row = db.scalar(select(ProjectMaterialReference).where(ProjectMaterialReference.project_id == project_id, ProjectMaterialReference.material_revision_id == revision.id))
    if row is not None and row.status == "active":
        return reference_json(db, row)
    if row is None:
        row = ProjectMaterialReference(project_id=project_id, material_revision_id=revision.id, origin="system_reference", status="active", note=payload.note, attached_by=user.email)
        db.add(row)
    else:
        row.status = "active"
        row.note = payload.note
        row.detached_by = None
        row.detached_at = None
        row.attached_by = user.email
        row.attached_at = utcnow()
    try:
        db.flush()
        record_project_event(db, project_id=project_id, event_type="asset.attached", actor=user.email, entity_type="material_revision", entity_id=revision.id, payload={"reference_id": row.id, "origin": row.origin})
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "素材引用冲突，请刷新后重试") from exc
    return reference_json(db, row)


@router.delete("/{project_id}/materials/references/{reference_id}", status_code=204)
def detach_material_reference(project_id: int, reference_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    mutable_project(db, project_id, user)
    row = db.get(ProjectMaterialReference, reference_id)
    if row is None or row.project_id != project_id:
        raise HTTPException(404, "项目素材引用不存在")
    if row.status == "detached":
        return
    row.status = "detached"
    row.detached_by = user.email
    row.detached_at = utcnow()
    record_project_event(db, project_id=project_id, event_type="asset.detached", actor=user.email, entity_type="material_revision", entity_id=row.material_revision_id, payload={"reference_id": row.id})
    db.commit()


@router.post("/{project_id}/materials/upload", status_code=201)
async def upload_project_material(project_id: int, file: UploadFile, kind: str = "image", title: str | None = None, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    mutable_project(db, project_id, user)
    content = await file.read()
    mime = materials_service.validate_upload(content, file.content_type)
    extension = (file.filename or "").rsplit(".", 1)[-1].lower()
    suffix = f".{extension}" if re.fullmatch(r"[a-z0-9]{1,5}", extension) else ".bin"
    from ..services import asset_media

    content_hash = hashlib.sha256(content).hexdigest()
    relative_path = Path("material") / content_hash[:2] / f"{content_hash}{suffix}"
    stored_path = asset_media.MEDIA_ROOT / relative_path
    existed_before = stored_path.exists()
    try:
        material = materials_service.create_material(db, kind=kind, title=title or file.filename or "项目素材", created_by=user.email)
        revision = materials_service.create_revision(db, material, content=content, suffix=suffix, declared_mime=mime, source_kind="upload", created_by=user.email)
        row = ProjectMaterialReference(project_id=project_id, material_revision_id=revision.id, origin="project_upload", status="active", attached_by=user.email)
        db.add(row)
        db.flush()
        db.add(AuditLog(event="material.uploaded", actor=user.email, entity_type="material", entity_id=str(material.id), detail_json={"hash": revision.content_hash, "source_kind": "upload"}))
        record_project_event(db, project_id=project_id, event_type="asset.attached", actor=user.email, entity_type="material_revision", entity_id=revision.id, payload={"reference_id": row.id, "origin": "project_upload", "content_hash": revision.content_hash})
        db.commit()
    except Exception:
        db.rollback()
        if not existed_before and stored_path.is_file():
            try:
                db.add(AuditLog(event="material.upload_orphan_candidate", actor=user.email, entity_type="material_bytes", entity_id=content_hash[:50], detail_json={"project_id": project_id, "file_path": str(relative_path), "content_hash": content_hash, "cleanup_rule": "check_committed_revision_references_after_grace_period"}))
                db.commit()
            except Exception:
                db.rollback()
                logger.exception("Could not record failed project upload byte candidate: %s", relative_path)
        raise
    return reference_json(db, row)
