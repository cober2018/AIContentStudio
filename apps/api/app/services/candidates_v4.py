"""Frozen Master projections and a pure, Draft-independent manifest builder."""

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import (
    ContentMasterCheckRun,
    ContentMasterRevision,
    ContentProject,
    ContentUnit,
    CreativeBriefRevision,
    FactPack,
    IdentitySnapshot,
    ProjectFactBoundaryRevision,
    ProjectWorkflowOutput,
    WorkflowRun,
    WorkflowStepAttempt,
)
from .content_harness.channel_registry import resolve_content_form
from .content_masters import _serialize, check_requirements
from .production_modalities import adapter_for, validate_json_bounds

SECTIONS = ("artifact_kind", "channel", "content_form", "project", "identity", "brief", "evidence", "content_master", "content", "assets", "evidence_refs", "checks", "render", "production", "citations", "declarations")


def build_manifest_v4(inputs: dict) -> dict:
    """Build only from explicit snapshots; authorization/live gates belong to callers."""
    required = {"project": ("id", "unit_id", "modality", "channel", "content_form"), "identity": ("id", "checksum"), "brief": ("id", "revision_no", "checksum"), "evidence": ("boundary_id", "revision_no", "fact_pack"), "content_master": ("id", "revision_no", "payload_schema", "payload_hash", "context_hash"), "render": ("status",), "production": ("source_kind",)}
    for section in SECTIONS:
        if section not in inputs or inputs[section] is None:
            raise ValueError(f"missing manifest section: {section}")
    for section, fields in required.items():
        if not isinstance(inputs[section], dict) or any(inputs[section].get(field) is None for field in fields):
            raise ValueError(f"incomplete manifest section: {section}")
    for section in ("assets", "evidence_refs", "checks", "citations", "declarations"):
        if not isinstance(inputs[section], list):
            raise TypeError(f"invalid manifest section: {section}")
    manifest = {"schema_version": 4, **{key: inputs[key] for key in SECTIONS}}
    errors = validate_json_bounds(manifest)
    if errors:
        raise ValueError(f"invalid manifest bounds: {errors}")
    # JSON round-trip prevents later mutations of ORM JSON or caller inputs.
    return json.loads(json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False))


def load_manifest_v4_inputs(db: Session, master: ContentMasterRevision, *, require_current: bool = True, frozen_checks: list[dict] | None = None) -> dict:
    project = db.get(ContentProject, master.project_id)
    unit = db.get(ContentUnit, master.content_unit_id)
    identity = db.get(IdentitySnapshot, master.identity_snapshot_id) if master.identity_snapshot_id else None
    brief = db.get(CreativeBriefRevision, master.creative_brief_revision_id) if master.creative_brief_revision_id else None
    boundary = db.get(ProjectFactBoundaryRevision, master.fact_boundary_revision_id) if master.fact_boundary_revision_id else None
    pack = db.get(FactPack, boundary.fact_pack_id) if boundary else None
    if not all((project, unit, identity, brief, boundary, pack)):
        raise ValueError("incomplete frozen Master context")
    if unit.project_id != project.id or identity.owner_user_id != project.owner_user_id or brief.project_id != project.id or boundary.project_id != project.id or pack.checksum != boundary.fact_pack_checksum or pack.version != boundary.fact_pack_version:
        raise ValueError("inconsistent frozen Master context")
    adapter = adapter_for(master.modality, master.payload_schema)
    projection = _serialize(db, master)
    requirements = check_requirements(db, master, require_current=require_current, frozen_checks=frozen_checks if not require_current else None)
    checks = []
    for kind, requirement in requirements.items():
        query = select(ContentMasterCheckRun).where(ContentMasterCheckRun.master_revision_id == master.id, ContentMasterCheckRun.check_kind == kind)
        if not require_current:
            query = query.where(ContentMasterCheckRun.input_hash == requirement["input_hash"])
        check = db.scalar(query.order_by(ContentMasterCheckRun.id.desc()).limit(1))
        if check is None or check.input_hash != requirement["input_hash"] or check.profile_key != requirement["profile_key"] or check.profile_version != requirement["profile_version"]:
            raise ValueError(f"missing or stale Master check: {kind}")
        checks.append({"id": check.id, "kind": kind, "profile_key": check.profile_key, "profile_version": check.profile_version, "input_hash": check.input_hash, "status": check.status, "report": check.report_json})
    workflow, output_snapshot = None, None
    if master.origin_workflow_run_id is not None or master.origin_project_output_id is not None:
        run = db.get(WorkflowRun, master.origin_workflow_run_id) if master.origin_workflow_run_id else None
        output = db.get(ProjectWorkflowOutput, master.origin_project_output_id) if master.origin_project_output_id else None
        attempt = db.get(WorkflowStepAttempt, output.attempt_id) if output and output.attempt_id else None
        if not run or not output or not attempt or not run.definition_checksum or run.workflow_version is None or run.content_unit_id != master.content_unit_id or run.identity_snapshot_id != master.identity_snapshot_id or output.project_id != master.project_id or output.unit_id != master.content_unit_id or output.run_id != run.id or attempt.run_id != run.id or attempt.node_id != output.node_id or attempt.status != "succeeded" or not attempt.output_hash:
            raise ValueError("unverified Master workflow provenance")
        workflow = {"run_id": run.id, "workflow_id": run.workflow_id, "version": run.workflow_version, "definition_checksum": run.definition_checksum}
        output_snapshot = {"id": output.id, "kind": output.output_kind, "entity_id": output.entity_id, "node_id": output.node_id, "attempt_id": attempt.id, "attempt_no": attempt.attempt_no, "input_hash": attempt.input_hash, "output_hash": attempt.output_hash}
    payload = master.payload_json
    structured = payload.get("structured") or {}
    exact_citations = (payload.get("document") or {}).get("citations", []) if master.payload_schema == "text.master.v2" else None
    return {
        "artifact_kind": resolve_content_form(db, master.channel_id, master.content_form).artifact_kind,
        "channel": master.channel_id, "content_form": master.content_form,
        "project": {"id": project.id, "title": project.title, "unit_id": unit.id, "unit_title": unit.title, "modality": master.modality, "channel": master.channel_id, "content_form": master.content_form},
        "identity": {"id": identity.id, "checksum": identity.checksum, "brand_id": identity.brand_id, "brand_revision_id": identity.brand_revision_id, "persona_id": identity.persona_id, "persona_revision_id": identity.persona_revision_id, "account_id": identity.account_id, "account_revision_id": identity.account_revision_id, "series_id": identity.series_id, "series_revision_id": identity.series_revision_id, "brand_voice_version_id": identity.brand_voice_version_id, "effective_profile": identity.effective_profile_json, "field_origins": identity.field_origins_json},
        "brief": {"id": brief.id, "revision_no": brief.revision_no, "checksum": brief.checksum, "snapshot": {"objective": brief.objective, "primary_audience": brief.primary_audience, "core_message": brief.core_message, "angle": brief.angle, "required_evidence": brief.required_evidence_json, "constraints": brief.content_constraints_json, "identity_scope": brief.identity_scope_json, "modality_scope": brief.modality_scope_json, "channel_scope": brief.channel_scope_json, "cta": brief.cta, "references": brief.references_json}},
        "evidence": {"boundary_id": boundary.id, "revision_no": boundary.revision_no, "fact_pack": {"id": boundary.fact_pack_id, "version": boundary.fact_pack_version, "checksum": boundary.fact_pack_checksum}},
        "content_master": {"id": master.id, "revision_no": master.revision_no, "parent_id": master.parent_revision_id, "modality": master.modality, "payload_schema": master.payload_schema, "payload_hash": master.payload_hash, "context_hash": master.context_hash},
        "content": payload, "assets": projection["assets"], "evidence_refs": projection["evidence"], "checks": checks,
        "render": adapter.build_render_snapshot(db, master),
        "production": {"source_kind": master.source_kind, "workflow": workflow, "output": output_snapshot, "edit_summary": master.edit_summary_json, "created_by": master.created_by},
        "citations": exact_citations if exact_citations is not None else (payload.get("citations", structured.get("citations", structured.get("claim_fact_map", []))) or []),
        "declarations": payload.get("declarations", structured.get("declarations", [])) or [],
    }
