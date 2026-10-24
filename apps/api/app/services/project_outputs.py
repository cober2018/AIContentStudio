"""Attach verified existing workflow products to the owning project."""

import hashlib

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import (
    ContentMasterRevision,
    ContentProject,
    ContentUnit,
    MaterialRevision,
    ProjectWorkflowOutput,
    WorkflowRun,
    WorkflowStep,
    WorkflowStepAttempt,
    utcnow,
)
from .project_events import record_project_event

OUTPUTS = {
    "media.generate": ("material_revision_id", "material_revision", MaterialRevision),
    "media.chart": ("material_revision_id", "material_revision", MaterialRevision),
    "media.screenshot": ("material_revision_id", "material_revision", MaterialRevision),
    "media.video_clip": ("material_revision_id", "material_revision", MaterialRevision),
}
MEDIA_KINDS = {"media.chart": "chart", "media.screenshot": "screenshot", "media.video_clip": "video"}


def associate_step_output(db: Session, run: WorkflowRun, step: WorkflowStep, attempt_id: int) -> ProjectWorkflowOutput | None:
    if run.content_unit_id is None:
        return None
    master_output = "content_master_revision_id" in (step.output_json or {})
    if master_output:
        field, kind, entity_type = "content_master_revision_id", "content_master_revision", ContentMasterRevision
    elif step.plugin_key in OUTPUTS:
        field, kind, entity_type = OUTPUTS[step.plugin_key]
    else:
        return None
    entity_id = (step.output_json or {}).get(field)
    if type(entity_id) is not int:
        return None
    entity = db.get(entity_type, entity_id)
    if entity is None:
        return None
    if kind == "material_revision":
        expected_kind = step.output_json.get("media_kind") if step.plugin_key == "media.generate" else MEDIA_KINDS[step.plugin_key]
        if step.plugin_key == "media.generate":
            from ..models import ProviderGenerationTask

            task = db.get(ProviderGenerationTask, step.output_json.get("generation_task_id"))
            started = db.get(WorkflowStepAttempt, task.workflow_step_attempt_id) if task else None
            terminal = db.get(WorkflowStepAttempt, attempt_id)
            if (task is None or task.state != "accepted" or task.accepted_material_revision_id != entity.id
                    or task.result_hash != entity.content_hash or started is None
                    or started.run_id != run.id or started.step_id != step.id or started.status != "started"
                    or terminal is None or terminal.status != "succeeded" or terminal.step_id != step.id
                    or terminal.run_id != run.id or terminal.output_json != step.output_json
                    or terminal.output_hash != step.output_hash or terminal.input_hash != started.input_hash
                    or expected_kind not in {"image", "audio", "video"}):
                return None
        if step.output_json.get("generated") is not True or not entity.file_path or not entity.content_hash or not entity.material or entity.material.kind != expected_kind:
            return None
        from .materials import read_bytes_checked

        try:
            content = read_bytes_checked(db, entity)
        except Exception:  # noqa: BLE001 Output association must fail closed.
            return None
        if hashlib.sha256(content).hexdigest() != entity.content_hash:
            return None
    unit = db.get(ContentUnit, run.content_unit_id)
    if unit is None:
        return None
    project = db.get(ContentProject, unit.project_id)
    if project is None:
        return None
    if master_output:
        attempt = db.get(WorkflowStepAttempt, attempt_id)
        latest = db.scalar(select(WorkflowStepAttempt.id).where(WorkflowStepAttempt.step_id == step.id).order_by(WorkflowStepAttempt.id.desc()).limit(1))
        if (
            entity.project_id != project.id or entity.content_unit_id != unit.id
            or entity.origin_workflow_run_id != run.id
            or entity.identity_snapshot_id != run.identity_snapshot_id
            or run.identity_snapshot_id != (None if unit.production_domain == "product" else unit.identity_snapshot_id)
            or step.run_id != run.id or step.status != "succeeded"
            or attempt is None or attempt.id != latest or attempt.status != "succeeded"
            or attempt.run_id != run.id or attempt.step_id != step.id or attempt.node_id != step.node_id
            or attempt.plugin_key != step.plugin_key
            or not step.output_hash or attempt.output_hash != step.output_hash
            or attempt.output_json != step.output_json
        ):
            return None
    existing = db.scalar(select(ProjectWorkflowOutput).where(ProjectWorkflowOutput.attempt_id == attempt_id, ProjectWorkflowOutput.output_kind == kind, ProjectWorkflowOutput.entity_id == entity_id))
    if existing:
        return existing
    lineage = {"plugin_key": step.plugin_key, "workflow_id": run.workflow_id, "definition_checksum": run.definition_checksum}
    if kind == "material_revision":
        lineage.update({"content_hash": entity.content_hash, "source_kind": entity.source_kind, "rights_status": entity.rights_status, "public_use_allowed": entity.public_use_allowed})
    elif master_output:
        lineage.update({"payload_hash": entity.payload_hash, "context_hash": entity.context_hash, "revision_no": entity.revision_no, "identity_snapshot_id": entity.identity_snapshot_id})
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
    db.flush()
    event_type = "content_master.generated" if master_output else "asset.workflow_generated"
    record_project_event(db, project_id=project.id, event_type=event_type, actor=None, entity_type=kind, entity_id=entity_id, payload={"unit_id": unit.id, "run_id": run.id, "node_id": step.node_id, "attempt_id": attempt_id, "project_output_id": output.id})
    return output
