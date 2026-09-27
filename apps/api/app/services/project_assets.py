"""Unified project asset read model over references and verified workflow outputs."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import MaterialRevision, ProjectMaterialReference, ProjectWorkflowOutput


def _asset_json(revision: MaterialRevision, *, source_type: str, reference_id: int | None = None, output: ProjectWorkflowOutput | None = None) -> dict:
    material = revision.material
    return {
        "key": f"reference:{reference_id}" if reference_id is not None else f"workflow:{output.id}",
        "id": reference_id if reference_id is not None else output.id,
        "source_type": source_type,
        "reference_id": reference_id,
        "project_output_id": output.id if output else None,
        "material_id": revision.material_id,
        "material_revision_id": revision.id,
        "revision_no": revision.revision_no,
        "kind": material.kind if material else None,
        "title": material.title if material else None,
        "mime_type": revision.mime_type,
        "content_hash": revision.content_hash,
        "rights_status": revision.rights_status,
        "public_use_allowed": revision.public_use_allowed,
        "model_use_allowed": revision.model_use_allowed,
        "commercial_use_allowed": revision.commercial_use_allowed,
        "attribution_text": revision.attribution_text,
        "project_id": output.project_id if output else None,
        "unit_id": output.unit_id if output else None,
        "run_id": output.run_id if output else None,
        "node_id": output.node_id if output else None,
        "attempt_id": output.attempt_id if output else None,
        "provenance": {
            "source_kind": revision.source_kind,
            "source_url": revision.source_url,
            "source_metadata": revision.source_metadata_json or {},
            "provider_key": revision.provider_key,
            "provider_version": revision.provider_version,
            "created_by": revision.created_by,
            **((output.provenance_json or {}) if output else {}),
        },
    }


def reference_json(db: Session, row: ProjectMaterialReference) -> dict:
    revision = db.get(MaterialRevision, row.material_revision_id)
    return _asset_json(revision, source_type=row.origin, reference_id=row.id)


def shared_assets(db: Session, project_id: int) -> list[dict]:
    refs = db.scalars(select(ProjectMaterialReference).where(ProjectMaterialReference.project_id == project_id, ProjectMaterialReference.status == "active").order_by(ProjectMaterialReference.id.desc()).limit(200)).all()
    outputs = db.scalars(select(ProjectWorkflowOutput).where(ProjectWorkflowOutput.project_id == project_id, ProjectWorkflowOutput.output_kind == "material_revision").order_by(ProjectWorkflowOutput.id.desc()).limit(200)).all()
    items = [reference_json(db, row) for row in refs if db.get(MaterialRevision, row.material_revision_id) is not None]
    for output in outputs:
        revision = db.get(MaterialRevision, output.entity_id)
        if revision is not None:
            items.append(_asset_json(revision, source_type="workflow", output=output))
    return items
