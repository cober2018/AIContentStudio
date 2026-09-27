"""Project references to global Sources and frozen FactPacks."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ProjectFactBoundaryRevision, ProjectSourceBinding, SourceDocument


def current_boundary(db: Session, project_id: int) -> ProjectFactBoundaryRevision | None:
    return db.scalar(select(ProjectFactBoundaryRevision).where(ProjectFactBoundaryRevision.project_id == project_id).order_by(ProjectFactBoundaryRevision.revision_no.desc()).limit(1))


def source_binding_json(db: Session, row: ProjectSourceBinding) -> dict:
    source = db.get(SourceDocument, row.source_document_id)
    return {"id": row.id, "project_id": row.project_id, "source_document_id": row.source_document_id, "status": row.status, "note": row.note, "title": source.title if source else None, "source_type": source.source_type if source else None, "parse_status": source.parse_status if source else None, "sha256": source.sha256 if source else None, "attached_at": row.attached_at.isoformat() if row.attached_at else None}


def boundary_json(row: ProjectFactBoundaryRevision) -> dict:
    return {"id": row.id, "project_id": row.project_id, "revision_no": row.revision_no, "parent_revision_id": row.parent_revision_id, "fact_pack_id": row.fact_pack_id, "fact_pack_version": row.fact_pack_version, "fact_pack_checksum": row.fact_pack_checksum, "created_by": row.created_by, "created_at": row.created_at.isoformat() if row.created_at else None}
