"""Project-scoped evidence membership and immutable fact boundaries."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_editor
from ..models import AuditLog, FactPack, FactPackStatus, ProjectFactBoundaryRevision, ProjectSourceBinding, SourceDocument, User, utcnow
from ..services import factpack_service
from ..services.project_events import record_project_event
from ..services.project_evidence import boundary_json, current_boundary, source_binding_json
from .content_projects import mutable_project, owned_project

router = APIRouter(prefix="/api/v1/content-projects", tags=["content-project-evidence"])


class SourceAttachIn(BaseModel):
    source_document_id: int
    note: str | None = None


class BoundaryBindIn(BaseModel):
    fact_pack_id: int
    expected_revision: int = Field(ge=0)


class ExpectedRevisionIn(BaseModel):
    expected_revision: int = Field(ge=0)


@router.get("/{project_id}/sources")
def list_project_sources(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    owned_project(db, project_id, user)
    rows = db.scalars(select(ProjectSourceBinding).where(ProjectSourceBinding.project_id == project_id, ProjectSourceBinding.status == "active").order_by(ProjectSourceBinding.id)).all()
    return [source_binding_json(db, row) for row in rows]


@router.post("/{project_id}/sources", status_code=201)
def attach_project_source(payload: SourceAttachIn, project_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    mutable_project(db, project_id, user)
    source = db.get(SourceDocument, payload.source_document_id)
    if source is None or source.is_archived:
        raise HTTPException(404, "Source 不存在或已归档")
    row = db.scalar(select(ProjectSourceBinding).where(ProjectSourceBinding.project_id == project_id, ProjectSourceBinding.source_document_id == source.id))
    if row is not None and row.status == "active":
        return source_binding_json(db, row)
    if row is None:
        row = ProjectSourceBinding(project_id=project_id, source_document_id=source.id, status="active", note=payload.note, attached_by=user.email)
        db.add(row)
    else:
        row.status = "active"
        row.note = payload.note
        row.attached_by = user.email
        row.attached_at = utcnow()
        row.detached_by = None
        row.detached_at = None
    try:
        db.flush()
        record_project_event(db, project_id=project_id, event_type="source.attached", actor=user.email, entity_type="source_document", entity_id=source.id)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "来源绑定冲突，请刷新后重试") from exc
    return source_binding_json(db, row)


@router.delete("/{project_id}/sources/{source_document_id}", status_code=204)
def detach_project_source(project_id: int, source_document_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    mutable_project(db, project_id, user)
    row = db.scalar(select(ProjectSourceBinding).where(ProjectSourceBinding.project_id == project_id, ProjectSourceBinding.source_document_id == source_document_id))
    if row is None:
        raise HTTPException(404, "项目来源不存在")
    if row.status == "detached":
        return
    row.status = "detached"
    row.detached_by = user.email
    row.detached_at = utcnow()
    record_project_event(db, project_id=project_id, event_type="source.detached", actor=user.email, entity_type="source_document", entity_id=source_document_id)
    db.commit()


@router.get("/{project_id}/fact-boundary")
def get_fact_boundary(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    owned_project(db, project_id, user)
    row = current_boundary(db, project_id)
    return boundary_json(row) if row else None


@router.get("/{project_id}/fact-boundary/revisions")
def list_fact_boundary_revisions(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    owned_project(db, project_id, user)
    rows = db.scalars(select(ProjectFactBoundaryRevision).where(ProjectFactBoundaryRevision.project_id == project_id).order_by(ProjectFactBoundaryRevision.revision_no.desc()).limit(100)).all()
    return [boundary_json(row) for row in rows]


@router.post("/{project_id}/fact-boundary", status_code=201)
def bind_fact_boundary(payload: BoundaryBindIn, project_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    mutable_project(db, project_id, user)
    pack = db.get(FactPack, payload.fact_pack_id)
    if pack is None:
        raise HTTPException(404, "FactPack 不存在")
    if pack.status != FactPackStatus.frozen.value or not pack.checksum:
        raise HTTPException(422, "只可绑定有 checksum 的冻结 FactPack")
    previous = current_boundary(db, project_id)
    current_revision = previous.revision_no if previous else 0
    if payload.expected_revision != current_revision:
        raise HTTPException(409, "事实边界已更新，请刷新后重试")
    row = ProjectFactBoundaryRevision(project_id=project_id, revision_no=current_revision + 1, parent_revision_id=previous.id if previous else None, fact_pack_id=pack.id, fact_pack_version=pack.version, fact_pack_checksum=pack.checksum, created_by=user.email)
    db.add(row)
    try:
        db.flush()
        record_project_event(db, project_id=project_id, event_type="fact_boundary.bound", actor=user.email, entity_type="fact_pack", entity_id=pack.id, payload={"revision_no": row.revision_no, "checksum": pack.checksum})
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "事实边界已更新，请刷新后重试") from exc
    return boundary_json(row)


@router.post("/{project_id}/fact-boundary/clone", status_code=201)
def clone_project_boundary(project_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    mutable_project(db, project_id, user)
    boundary = current_boundary(db, project_id)
    if boundary is None:
        raise HTTPException(409, "项目尚无可克隆的事实边界")
    pack = db.get(FactPack, boundary.fact_pack_id)
    if pack is None or pack.status != FactPackStatus.frozen.value:
        raise HTTPException(409, "当前事实边界不是冻结 FactPack")
    try:
        clone = factpack_service.clone_pack(db, pack, actor=user.email)
        db.add(AuditLog(event="fact_pack.cloned", actor=user.email, entity_type="fact_pack", entity_id=str(clone.id), detail_json={"parent_id": pack.id, "parent_version": pack.version}))
        record_project_event(db, project_id=project_id, event_type="fact_boundary.draft_cloned", actor=user.email, entity_type="fact_pack", entity_id=clone.id, payload={"parent_fact_pack_id": pack.id, "boundary_revision": boundary.revision_no})
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "FactPack 版本冲突，请刷新后重试") from exc
    return {"id": clone.id, "parent_id": clone.parent_id, "version": clone.version, "name": clone.name, "status": clone.status}


@router.post("/{project_id}/fact-boundary/{fact_pack_id}/freeze-and-bind", status_code=201)
def freeze_and_bind_project_boundary(project_id: int, fact_pack_id: int, payload: ExpectedRevisionIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    mutable_project(db, project_id, user)
    previous = current_boundary(db, project_id)
    if previous is None or previous.revision_no != payload.expected_revision:
        raise HTTPException(409, "事实边界已更新，请刷新后重试")
    draft = db.get(FactPack, fact_pack_id)
    if draft is None or draft.parent_id != previous.fact_pack_id or draft.status != FactPackStatus.draft.value:
        raise HTTPException(409, "只能冻结当前事实边界的直接草稿版本")
    try:
        factpack_service.freeze_pack(draft)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    row = ProjectFactBoundaryRevision(project_id=project_id, revision_no=previous.revision_no + 1, parent_revision_id=previous.id, fact_pack_id=draft.id, fact_pack_version=draft.version, fact_pack_checksum=draft.checksum, created_by=user.email)
    db.add(row)
    try:
        db.flush()
        db.add(AuditLog(event="fact_pack.frozen", actor=user.email, entity_type="fact_pack", entity_id=str(draft.id), detail_json={"version": draft.version, "checksum": draft.checksum}))
        record_project_event(db, project_id=project_id, event_type="fact_boundary.frozen_bound", actor=user.email, entity_type="fact_pack", entity_id=draft.id, payload={"revision_no": row.revision_no, "checksum": draft.checksum})
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "事实边界已更新，请刷新后重试") from exc
    return boundary_json(row)
