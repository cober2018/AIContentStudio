"""Attach verified existing workflow products to the owning project."""

import hashlib
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import (
    ContentAsset, ContentJob, ContentProject, ContentUnit, Draft, MaterialRevision,
    ProjectWorkflowOutput, WorkflowRun, WorkflowStep, utcnow,
)

OUTPUTS = {
    "builtin.generate": ("draft_id", "draft", Draft),
    "builtin.generate_cover": ("material_revision_id", "material_revision", MaterialRevision),
    "media.chart": ("material_revision_id", "material_revision", MaterialRevision),
    "media.screenshot": ("material_revision_id", "material_revision", MaterialRevision),
    "media.video_clip": ("material_revision_id", "material_revision", MaterialRevision),
    "builtin.approve": ("asset_id", "candidate", ContentAsset),
}
MEDIA_KINDS = {"builtin.generate_cover": "image", "media.chart": "chart", "media.screenshot": "screenshot", "media.video_clip": "video"}


def associate_step_output(db: Session, run: WorkflowRun, step: WorkflowStep, attempt_id: int) -> ProjectWorkflowOutput | None:
    if run.content_unit_id is None or step.plugin_key not in OUTPUTS:
        return None
    field, kind, entity_type = OUTPUTS[step.plugin_key]
    entity_id = (step.output_json or {}).get(field)
    if not isinstance(entity_id, int):
        return None
    entity = db.get(entity_type, entity_id)
    if entity is None:
        return None
    if kind == "candidate" and not entity.approved_candidate_hash:
        return None
    if kind == "material_revision":
        if step.output_json.get("generated") is not True or not entity.file_path or not entity.content_hash or not entity.material or entity.material.kind != MEDIA_KINDS[step.plugin_key]:
            return None
        from . import asset_media

        path = Path(entity.file_path)
        if not path.is_absolute():
            path = asset_media.MEDIA_ROOT / path
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != entity.content_hash:
            return None
    if kind in {"draft", "candidate"}:
        draft = entity if kind == "draft" else db.get(Draft, entity.draft_id)
        job = db.get(ContentJob, draft.content_job_id) if draft else None
        if job is None or job.workflow_run_id != run.id:
            return None
    unit = db.get(ContentUnit, run.content_unit_id)
    if unit is None:
        return None
    project = db.get(ContentProject, unit.project_id)
    if project is None:
        return None
    existing = db.scalar(select(ProjectWorkflowOutput).where(ProjectWorkflowOutput.attempt_id == attempt_id, ProjectWorkflowOutput.output_kind == kind, ProjectWorkflowOutput.entity_id == entity_id))
    if existing:
        return existing
    lineage = {"plugin_key": step.plugin_key, "workflow_id": run.workflow_id, "definition_checksum": run.definition_checksum}
    if kind == "material_revision":
        lineage.update({"content_hash": entity.content_hash, "source_kind": entity.source_kind, "rights_status": entity.rights_status, "public_use_allowed": entity.public_use_allowed})
    output = ProjectWorkflowOutput(
        project_id=project.id,
        unit_id=unit.id,
        run_id=run.id,
        node_id=step.node_id,
        attempt_id=attempt_id,
        output_kind=kind,
        entity_id=entity_id,
        provenance_json=lineage,
        created_at=utcnow(),
    )
    db.add(output)
    return output
