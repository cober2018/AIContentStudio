"""Pure, bounded manifest construction for Variant-backed Candidates."""

import hashlib
import json
import re

from .channel_adapters import FIRST_BATCH
from .channel_variant_documents import VariantDocumentError, canonical_payload
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
