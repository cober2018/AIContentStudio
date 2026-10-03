"""Append-only CreativeBrief revisions."""

import hashlib
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import CreativeBriefRevision

BRIEF_FIELDS = (
    "objective", "primary_audience", "core_message", "angle", "required_evidence",
    "content_constraints", "identity_scope", "modality_scope", "channel_scope", "cta", "references",
)


def current_brief(db: Session, project_id: int) -> CreativeBriefRevision | None:
    return db.scalar(select(CreativeBriefRevision).where(CreativeBriefRevision.project_id == project_id).order_by(CreativeBriefRevision.revision_no.desc()).limit(1))


def checksum_brief(payload: dict) -> str:
    canonical = {key: payload.get(key) for key in BRIEF_FIELDS}
    return hashlib.sha256(json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def serialize_brief(row: CreativeBriefRevision) -> dict:
    return {
        "id": row.id,
        "project_id": row.project_id,
        "revision_no": row.revision_no,
        "parent_revision_id": row.parent_revision_id,
        "objective": row.objective,
        "primary_audience": row.primary_audience,
        "core_message": row.core_message,
        "angle": row.angle,
        "required_evidence": row.required_evidence_json,
        "content_constraints": row.content_constraints_json,
        "identity_scope": row.identity_scope_json,
        "modality_scope": row.modality_scope_json,
        "channel_scope": row.channel_scope_json,
        "cta": row.cta,
        "references": row.references_json,
        "checksum": row.checksum,
        "created_by": row.created_by,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }
