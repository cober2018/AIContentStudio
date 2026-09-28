"""Bounded project version aggregation; no ProjectVersion persistence table."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import (
    ContentAsset,
    ContentMasterRevision,
    ContentUnit,
    CreativeBriefRevision,
    DeliveryTarget,
    IdentitySnapshot,
    MaterialRevision,
    ProjectFactBoundaryRevision,
    ProjectMaterialReference,
    ProjectWorkflowOutput,
    Review,
    Workflow,
    WorkflowRun,
)


def _item(kind: str, id: int, version=None, status=None, checksum=None, created_at=None, current=False, unit_id=None, source=None) -> dict:
    item = {"kind": kind, "id": str(id), "version": version, "status": status, "checksum": checksum, "createdAt": created_at.isoformat() if created_at else None, "current": current}
    if unit_id is not None:
        item["unitId"] = unit_id
    if source is not None:
        item["source"] = source
    return item


def project_versions(db: Session, project_id: int) -> dict:
    brief = db.scalars(select(CreativeBriefRevision).where(CreativeBriefRevision.project_id == project_id).order_by(CreativeBriefRevision.revision_no.desc()).limit(100)).all()
    boundary = db.scalars(select(ProjectFactBoundaryRevision).where(ProjectFactBoundaryRevision.project_id == project_id).order_by(ProjectFactBoundaryRevision.revision_no.desc()).limit(100)).all()
    units = db.scalars(select(ContentUnit).where(ContentUnit.project_id == project_id).order_by(ContentUnit.id.desc()).limit(200)).all()
    unit_ids = [unit.id for unit in units]
    runs = db.scalars(select(WorkflowRun).where(WorkflowRun.content_unit_id.in_(unit_ids)).order_by(WorkflowRun.id.desc()).limit(200)).all() if unit_ids else []
    outputs = db.scalars(select(ProjectWorkflowOutput).where(ProjectWorkflowOutput.project_id == project_id).order_by(ProjectWorkflowOutput.id.desc()).limit(200)).all()
    masters = db.scalars(select(ContentMasterRevision).where(ContentMasterRevision.project_id == project_id).order_by(ContentMasterRevision.id.desc()).limit(200)).all()
    current_master_ids = {row.content_unit_id: row.id for row in reversed(masters)}
    candidates = db.scalars(select(ContentAsset).where(ContentAsset.project_id == project_id).order_by(ContentAsset.id.desc()).limit(200)).all()
    candidate_ids = [candidate.id for candidate in candidates]
    approvals = db.scalars(select(Review).where(Review.content_asset_id.in_(candidate_ids)).order_by(Review.id.desc()).limit(200)).all() if candidate_ids else []
    delivery_targets = db.scalars(select(DeliveryTarget).where(DeliveryTarget.content_asset_id.in_(candidate_ids)).order_by(DeliveryTarget.id.desc()).limit(200)).all() if candidate_ids else []
    current_candidate_ids = {candidate.content_unit_id: candidate.id for candidate in reversed(candidates)}
    candidate_unit_ids = {candidate.id: candidate.content_unit_id for candidate in candidates}
    refs = db.scalars(select(ProjectMaterialReference).where(ProjectMaterialReference.project_id == project_id).order_by(ProjectMaterialReference.id.desc()).limit(200)).all()
    workflow_ids = {unit.pinned_workflow_id for unit in units if unit.pinned_workflow_id} | {run.workflow_id for run in runs if run.workflow_id}
    workflows = [db.get(Workflow, workflow_id) for workflow_id in sorted(workflow_ids)]
    snapshot_units: dict[int, set[int]] = {}
    for unit in units:
        if unit.identity_snapshot_id is not None:
            snapshot_units.setdefault(unit.identity_snapshot_id, set()).add(unit.id)
    for run in runs:
        if run.identity_snapshot_id is not None and run.content_unit_id is not None:
            snapshot_units.setdefault(run.identity_snapshot_id, set()).add(run.content_unit_id)
    identity_snapshots = []
    for snapshot_id, related_units in sorted(snapshot_units.items()):
        snapshot = db.get(IdentitySnapshot, snapshot_id)
        if snapshot:
            identity_snapshots.extend(_item("identity_snapshot", snapshot.id, None, "frozen", snapshot.checksum, snapshot.created_at, any(unit.identity_snapshot_id == snapshot.id and unit.status != "archived" for unit in units), unit_id) for unit_id in sorted(related_units))
    identity_states = [_item("identity_state", unit.id, None, "legacy_identity", None, unit.created_at, unit.status != "archived", unit.id) for unit in units if unit.identity_snapshot_id is None]
    materials = []
    for ref in refs:
        revision = db.get(MaterialRevision, ref.material_revision_id)
        if revision:
            materials.append(_item("material_revision", revision.id, revision.revision_no, ref.status, revision.content_hash, revision.created_at, ref.status == "active", source=ref.origin))
    for output in outputs:
        if output.output_kind != "material_revision":
            continue
        revision = db.get(MaterialRevision, output.entity_id)
        if revision:
            materials.append(_item("material_revision", revision.id, revision.revision_no, revision.status, revision.content_hash, revision.created_at, True, output.unit_id, "workflow"))
    return {
        "brief": [_item("creative_brief_revision", row.id, row.revision_no, None, row.checksum, row.created_at, index == 0) for index, row in enumerate(brief)],
        "factBoundary": [_item("project_fact_boundary_revision", row.id, row.revision_no, "frozen", row.fact_pack_checksum, row.created_at, index == 0) for index, row in enumerate(boundary)],
        "contentUnits": [_item("content_unit", row.id, None, row.status, None, row.created_at, row.status != "archived") for row in units],
        "contentMasters": [{**_item("content_master_revision", row.id, row.revision_no, "immutable", row.payload_hash, row.created_at, current_master_ids.get(row.content_unit_id) == row.id, row.content_unit_id, row.source_kind), "payloadSchema": row.payload_schema, "payloadHash": row.payload_hash, "contextHash": row.context_hash, "identitySnapshotId": row.identity_snapshot_id, "briefRevisionId": row.creative_brief_revision_id, "boundaryRevisionId": row.fact_boundary_revision_id, "workflowRunId": row.origin_workflow_run_id, "projectOutputId": row.origin_project_output_id, "parentRevisionId": row.parent_revision_id} for row in masters],
        "identitySnapshots": identity_snapshots,
        "identityStates": identity_states,
        "workflows": [_item("workflow", row.id, row.version, row.status, row.checksum, row.created_at, any(unit.pinned_workflow_id == row.id for unit in units)) for row in workflows if row],
        "runs": [_item("workflow_run", row.id, row.workflow_version, row.status, row.definition_checksum, row.started_at, False, row.content_unit_id) for row in runs],
        "materials": materials,
        "contentOutputs": [_item(output.output_kind, output.entity_id, None, None, None, output.created_at, True, output.unit_id, "workflow") for output in outputs if output.output_kind in {"draft", "candidate", "content_master_revision"}],
        "candidates": [_item("candidate", row.id, (row.candidate_manifest_json or {}).get("schema_version"), row.status, row.candidate_hash, row.created_at, current_candidate_ids.get(row.content_unit_id) == row.id, row.content_unit_id) for row in candidates],
        "approvals": [_item("content_approval", row.id, None, row.decision, row.candidate_hash, row.created_at, current_candidate_ids.get(candidate_unit_ids.get(row.content_asset_id)) == row.content_asset_id, candidate_unit_ids.get(row.content_asset_id)) for row in approvals],
        "deliveryTargets": [_item("delivery_target", row.id, row.authorization_version, row.status, row.approved_candidate_hash, row.requested_at, current_candidate_ids.get(candidate_unit_ids.get(row.content_asset_id)) == row.content_asset_id, candidate_unit_ids.get(row.content_asset_id)) for row in delivery_targets],
    }
