"""Pure, bounded manifest construction for Variant-backed Candidates."""

import hashlib
import json
import re

from sqlalchemy.orm import Session

from ..models import (
    ChannelVariantCheckRun,
    ChannelVariantRevision,
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
from .channel_adapters import FIRST_BATCH, executable_adapter_for
from .channel_variant_documents import VariantDocumentError, canonical_payload
from .channel_variants import _check_inputs, projected_variant_checks
from .production_modalities import validate_json_bounds

SECTIONS = ("project", "identity", "brief", "evidence", "source_master", "variant", "target", "content",
            "assets", "evidence_refs", "checks", "render", "production", "citations", "declarations")
_HEX = re.compile(r"^[0-9a-f]{64}$")
_LLM_FIELDS = frozenset({"llm_run_id", "provider", "model", "prompt_version", "purpose", "input_hash",
                         "accepted_output_hash", "status"})


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _object(value: object, section: str, fields: tuple[str, ...]) -> dict:
    if not isinstance(value, dict) or any(value.get(field) is None for field in fields):
        raise ValueError(f"incomplete manifest section: {section}")
    return value


def _id(value: object) -> bool:
    return type(value) is int and value > 0


def _hex(value: object) -> bool:
    return isinstance(value, str) and _HEX.fullmatch(value) is not None


def build_manifest_v5(inputs: dict) -> dict:
    """Freeze explicit, already-authorized snapshots; live DB gates belong to the caller."""
    if not isinstance(inputs, dict) or set(inputs) != set(SECTIONS):
        raise ValueError("incomplete v5 manifest sections")
    project = _object(inputs["project"], "project", ("id", "unit_id", "modality"))
    identity = _object(inputs["identity"], "identity", ("id", "checksum"))
    brief = _object(inputs["brief"], "brief", ("id", "revision_no", "checksum"))
    evidence = _object(inputs["evidence"], "evidence", ("boundary_id", "revision_no", "fact_pack"))
    pack = _object(evidence["fact_pack"], "fact_pack", ("id", "version", "checksum"))
    source = _object(inputs["source_master"], "source_master", ("id", "revision_no", "modality", "payload_schema", "payload_hash", "context_hash"))
    variant = _object(inputs["variant"], "variant", ("id", "variant_key", "revision_no", "source_master_revision_id",
                                                       "identity_snapshot_id", "payload_schema", "payload_hash", "context_hash", "source_kind"))
    target = _object(inputs["target"], "target", ("channel", "content_form", "artifact_kind", "profile", "adapter", "rule_hash"))
    profile = _object(target["profile"], "target.profile", ("id", "key", "version", "hash", "artifact_kind"))
    adapter = _object(target["adapter"], "target.adapter", ("key", "version"))
    render = _object(inputs["render"], "render", ("artifact_kind",))
    production = _object(inputs["production"], "production", ("edit_summary", "created_by"))
    if set(production) - {"workflow", "output", "edit_summary", "created_by", "llm_provenance"}:
        raise ValueError("unsafe production provenance")
    if any(not _id(value) for value in (project["id"], project["unit_id"], identity["id"], brief["id"],
                                            evidence["boundary_id"], pack["id"], source["id"], variant["id"],
                                            variant["source_master_revision_id"], variant["identity_snapshot_id"], profile["id"])):
        raise ValueError("invalid frozen identity or provenance ID")
    if any(type(value) is not int or value <= 0 for value in (brief["revision_no"], evidence["revision_no"], pack["version"], source["revision_no"], variant["revision_no"])):
        raise ValueError("invalid frozen revision")
    if any(not _hex(value) for value in (identity["checksum"], brief["checksum"], pack["checksum"], source["payload_hash"],
                                            source["context_hash"], variant["payload_hash"], variant["context_hash"],
                                            profile["hash"], target["rule_hash"])):
        raise ValueError("invalid frozen checksum")
    contract = FIRST_BATCH.get((target["channel"], target["content_form"]))
    if (contract is None or source["payload_schema"] not in contract.accepted_master_schemas
            or source["modality"] != project["modality"] or variant["payload_schema"] != contract.payload_schema
            or target["artifact_kind"] != profile["artifact_kind"] or target["artifact_kind"] != contract.artifact_kind
            or adapter != {"key": contract.key, "version": contract.version}):
        raise ValueError("variant source, target or adapter mismatch")
    if source["id"] != variant["source_master_revision_id"] or identity["id"] != variant["identity_snapshot_id"]:
        raise ValueError("variant source or identity mismatch")
    if (source.get("channel") != variant.get("source_channel")
            or source.get("content_form") != variant.get("source_content_form")):
        raise ValueError("variant source channel or form mismatch")
    for section in ("assets", "evidence_refs", "checks", "citations", "declarations"):
        if not isinstance(inputs[section], list):
            raise TypeError(f"invalid manifest section: {section}")
    assets, evidence_refs = inputs["assets"], inputs["evidence_refs"]
    for index, ref in enumerate(assets):
        ref = _object(ref, "asset", ("material_revision_id", "content_hash_snapshot", "role", "slot_key", "sort_order", "placement", "rights_snapshot"))
        if not _id(ref["material_revision_id"]) or not _hex(ref["content_hash_snapshot"]) or ref["sort_order"] != index:
            raise ValueError("invalid ordered asset ref")
    for index, ref in enumerate(evidence_refs):
        ref = _object(ref, "evidence_ref", ("fact_pack_item_id", "snapshot_checksum", "role", "sort_order", "content_locator_json"))
        if not _id(ref["fact_pack_item_id"]) or not _hex(ref["snapshot_checksum"]) or ref["sort_order"] != index:
            raise ValueError("invalid ordered evidence ref")
    try:
        canonical = canonical_payload(variant["payload_schema"], inputs["content"], asset_refs=assets, evidence_refs=evidence_refs)
    except VariantDocumentError as exc:
        raise ValueError(f"invalid canonical Variant content: {exc}") from exc
    if canonical != inputs["content"] or _hash(canonical) != variant["payload_hash"]:
        raise ValueError("Variant payload or canonical hash mismatch")
    if inputs["citations"] != canonical["citations"] or inputs["declarations"] != canonical["declarations"]:
        raise ValueError("Variant citations or declarations mismatch")
    if render["artifact_kind"] != target["artifact_kind"]:
        raise ValueError("Variant render target mismatch")
    required_checks = {"variant_schema", "variant_evidence", "variant_rights", "variant_profile", "variant_package"}
    if variant["payload_schema"] == "xiaohongshu.image_note.v1":
        required_checks.add("variant_render")
    checks = inputs["checks"]
    if len(checks) != len(required_checks) or {check.get("kind") for check in checks if isinstance(check, dict)} != required_checks:
        raise ValueError("missing or duplicate Variant checks")
    adapter_hash = _hash(adapter)
    for check in checks:
        _object(check, "check", ("id", "kind", "input_hash", "status", "profile_hash", "adapter_hash", "rule_hash", "report"))
        if (not _id(check["id"]) or not _hex(check["input_hash"]) or check["status"] != "pass"
                or check["profile_hash"] != profile["hash"] or check["adapter_hash"] != adapter_hash
                or check["rule_hash"] != target["rule_hash"]):
            raise ValueError("invalid or unready Variant check")
    if len({check["input_hash"] for check in checks}) != 1:
        raise ValueError("Variant checks have different inputs")
    package = next(check for check in checks if check["kind"] == "variant_package")
    if package["report"].get("projection_hash") != _hash(render) or package["report"].get("coverage") != "projection_only":
        raise ValueError("Variant package projection mismatch")
    receipt = production.get("llm_provenance")
    if receipt is not None and (not isinstance(receipt, dict) or set(receipt) != _LLM_FIELDS or not _id(receipt.get("llm_run_id"))
                                or receipt.get("status") != "succeeded" or receipt.get("accepted_output_hash") != variant["payload_hash"]
                                or not _hex(receipt.get("input_hash"))):
        raise ValueError("invalid or unsafe llm provenance")
    manifest = {"schema_version": 5, **{section: inputs[section] for section in SECTIONS}}
    errors = validate_json_bounds(manifest)
    if errors:
        raise ValueError(f"invalid v5 manifest bounds: {errors}")
    return json.loads(json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False))


def load_manifest_v5_inputs(db: Session, row: ChannelVariantRevision) -> dict:
    """Resolve one current Variant into exact, live and frozen candidate inputs."""
    project = db.get(ContentProject, row.project_id)
    unit = db.get(ContentUnit, row.content_unit_id)
    master = db.get(ContentMasterRevision, row.source_master_revision_id)
    identity = db.get(IdentitySnapshot, row.identity_snapshot_id) if row.identity_snapshot_id else None
    if not all((project, unit, master, identity)) or unit.project_id != project.id or project.owner_user_id != identity.owner_user_id:
        raise ValueError("variant project, source or identity unavailable")
    if (master.project_id != project.id or master.content_unit_id != unit.id or master.identity_snapshot_id != identity.id
            or unit.identity_snapshot_id != identity.id or master.payload_hash != row.source_master_payload_hash
            or master.context_hash != row.source_master_context_hash or master.channel_id != row.source_channel_id
            or master.content_form != row.source_content_form):
        raise ValueError("variant source provenance mismatch")
    brief = db.get(CreativeBriefRevision, master.creative_brief_revision_id) if master.creative_brief_revision_id else None
    boundary = db.get(ProjectFactBoundaryRevision, master.fact_boundary_revision_id) if master.fact_boundary_revision_id else None
    pack = db.get(FactPack, boundary.fact_pack_id) if boundary else None
    if (not all((brief, boundary, pack)) or brief.project_id != project.id or boundary.project_id != project.id
            or pack.status != "frozen" or pack.version != boundary.fact_pack_version or pack.checksum != boundary.fact_pack_checksum):
        raise ValueError("variant brief or fact boundary mismatch")
    readiness = projected_variant_checks(db, row)
    if not readiness["ready"]:
        raise ValueError(f"variant not ready: {readiness['drift_reasons'] or readiness['source_gate']['reasons']}")
    input_hash, assets, evidence_refs = _check_inputs(db, row)
    checks = []
    for item in readiness["items"]:
        check = db.get(ChannelVariantCheckRun, item["id"])
        if check is None or check.input_hash != input_hash or not item["is_current"]:
            raise ValueError("variant check changed")
        checks.append({"id": check.id, "kind": check.check_kind, "input_hash": check.input_hash,
                       "status": check.status, "profile_hash": check.profile_hash, "adapter_hash": check.adapter_hash,
                       "rule_hash": check.rule_hash, "report": check.report_json})
    adapter, capability = executable_adapter_for(db, master.payload_schema, row.channel_id, row.content_form)
    if (capability["profile_version_id"] != row.profile_template_version_id or capability["profile_hash"] != row.profile_hash
            or capability["artifact_kind"] != row.artifact_kind):
        raise ValueError("variant target profile changed")
    workflow = output = None
    if master.origin_workflow_run_id is not None or master.origin_project_output_id is not None:
        run = db.get(WorkflowRun, master.origin_workflow_run_id) if master.origin_workflow_run_id else None
        project_output = db.get(ProjectWorkflowOutput, master.origin_project_output_id) if master.origin_project_output_id else None
        attempt = db.get(WorkflowStepAttempt, project_output.attempt_id) if project_output and project_output.attempt_id else None
        if (not run or not project_output or not attempt or not run.definition_checksum or run.workflow_version is None
                or run.content_unit_id != unit.id or run.identity_snapshot_id != identity.id
                or project_output.project_id != project.id or project_output.unit_id != unit.id or project_output.run_id != run.id
                or attempt.run_id != run.id or attempt.node_id != project_output.node_id or attempt.status != "succeeded" or not attempt.output_hash):
            raise ValueError("unverified source Master workflow provenance")
        workflow = {"run_id": run.id, "workflow_id": run.workflow_id, "version": run.workflow_version, "definition_checksum": run.definition_checksum}
        output = {"id": project_output.id, "kind": project_output.output_kind, "entity_id": project_output.entity_id,
                  "node_id": project_output.node_id, "attempt_id": attempt.id, "attempt_no": attempt.attempt_no,
                  "input_hash": attempt.input_hash, "output_hash": attempt.output_hash}
    return {
        "project": {"id": project.id, "title": project.title, "unit_id": unit.id, "unit_title": unit.title, "modality": master.modality},
        "identity": {"id": identity.id, "checksum": identity.checksum, "effective_profile": identity.effective_profile_json,
                     "field_origins": identity.field_origins_json},
        "brief": {"id": brief.id, "revision_no": brief.revision_no, "checksum": brief.checksum,
                  "snapshot": {"objective": brief.objective, "primary_audience": brief.primary_audience,
                               "core_message": brief.core_message, "angle": brief.angle, "constraints": brief.content_constraints_json}},
        "evidence": {"boundary_id": boundary.id, "revision_no": boundary.revision_no,
                     "fact_pack": {"id": pack.id, "version": pack.version, "checksum": pack.checksum}},
        "source_master": {"id": master.id, "revision_no": master.revision_no, "modality": master.modality,
                          "payload_schema": master.payload_schema, "payload_hash": master.payload_hash,
                          "context_hash": master.context_hash, "channel": master.channel_id,
                          "content_form": master.content_form},
        "variant": {"id": row.id, "variant_key": row.variant_key, "revision_no": row.revision_no,
                    "source_master_revision_id": master.id, "identity_snapshot_id": identity.id,
                    "payload_schema": row.payload_schema, "payload_hash": row.payload_hash,
                    "context_hash": row.context_hash, "source_kind": row.source_kind,
                    "source_channel": row.source_channel_id, "source_content_form": row.source_content_form},
        "target": {"channel": row.channel_id, "content_form": row.content_form, "artifact_kind": row.artifact_kind,
                   "profile": {"id": row.profile_template_version_id, "key": row.profile_key,
                               "version": row.profile_version, "hash": row.profile_hash, "artifact_kind": row.artifact_kind},
                   "adapter": {"key": row.adapter_key, "version": row.adapter_version}, "rule_hash": row.rule_hash},
        "content": row.payload_json, "assets": assets, "evidence_refs": evidence_refs, "checks": checks,
        "render": adapter.package_projection(row.payload_json, asset_refs=assets, evidence_refs=evidence_refs),
        "production": {"workflow": workflow, "output": output, "edit_summary": row.edit_summary_json,
                       "created_by": row.created_by, "llm_provenance": row.llm_provenance_json},
        "citations": row.payload_json["citations"], "declarations": row.payload_json["declarations"],
    }
