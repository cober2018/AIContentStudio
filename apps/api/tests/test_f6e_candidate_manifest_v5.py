"""V5 manifests freeze one exact canonical post-adaptation source."""

import hashlib
import json
from copy import deepcopy

import pytest

from app.services.candidates import candidate_hash
from app.services.channel_variant_documents import payload_hash


def _inputs():
    content = {"text": "有来源的原文", "citations": [], "declarations": []}
    adapter_hash = hashlib.sha256(json.dumps({"key": "x.single", "version": "1"}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    render = {"artifact_kind": "text", "text": "有来源的原文"}
    render_hash = hashlib.sha256(json.dumps(render, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {
        "project": {"id": 11, "unit_id": 22, "modality": "text"},
        "identity": {"id": 33, "checksum": "a" * 64},
        "brief": {"id": 44, "revision_no": 1, "checksum": "b" * 64},
        "evidence": {"boundary_id": 55, "revision_no": 1, "fact_pack": {"id": 66, "version": 2, "checksum": "c" * 64}},
        "source_master": {"id": 77, "revision_no": 3, "modality": "text", "payload_schema": "text.master.v2",
                          "payload_hash": "d" * 64, "context_hash": "e" * 64, "channel": None, "content_form": None},
        "variant": {"id": 88, "variant_key": "x.single.primary", "revision_no": 2, "source_master_revision_id": 77,
                    "identity_snapshot_id": 33, "payload_schema": "x.single.v1",
                    "payload_hash": payload_hash("x.single.v1", content), "context_hash": "f" * 64,
                    "source_kind": "deterministic_adapt"},
        "target": {"channel": "x", "content_form": "single", "artifact_kind": "text",
                   "profile": {"id": 99, "key": "x.single", "version": "1", "hash": "1" * 64,
                               "artifact_kind": "text"},
                   "adapter": {"key": "x.single", "version": "1"}, "rule_hash": "2" * 64},
        "content": content,
        "assets": [], "evidence_refs": [],
        "checks": [{"id": index, "kind": kind, "input_hash": "3" * 64, "status": "pass",
                    "profile_hash": "1" * 64, "adapter_hash": adapter_hash, "rule_hash": "2" * 64,
                    "report": {"reasons": [], **({"projection_hash": render_hash, "coverage": "projection_only"} if kind == "variant_package" else {})}}
                   for index, kind in enumerate(("variant_schema", "variant_evidence", "variant_rights", "variant_profile", "variant_package"), 1)],
        "render": render,
        "production": {"workflow": None, "output": None, "edit_summary": {}, "created_by": "editor@studio.local",
                       "llm_provenance": None},
        "citations": [], "declarations": [],
    }


def test_v5_manifest_freezes_exact_variant_target_source_and_checks():
    from app.services.candidates_v5 import build_manifest_v5

    inputs = _inputs()
    manifest = build_manifest_v5(inputs)
    assert manifest["schema_version"] == 5
    assert manifest["variant"]["id"] == 88
    assert manifest["source_master"]["id"] == 77
    assert manifest["identity"]["checksum"] == "a" * 64
    assert manifest["brief"]["checksum"] == "b" * 64
    assert manifest["evidence"]["fact_pack"]["checksum"] == "c" * 64
    assert manifest["target"]["channel"] == "x"
    assert manifest["content"] == inputs["content"]
    assert len(manifest["checks"]) == 5
    assert "draft_id" not in manifest


def test_v5_manifest_hash_is_deterministic_and_inputs_do_not_alias():
    from app.services.candidates_v5 import build_manifest_v5

    inputs = _inputs()
    first = build_manifest_v5(inputs)
    reordered = {key: inputs[key] for key in reversed(inputs)}
    reordered["content"] = {key: inputs["content"][key] for key in reversed(inputs["content"])}
    second = build_manifest_v5(reordered)
    assert candidate_hash(first) == candidate_hash(second)
    inputs["content"]["text"] = "调用方后续修改"
    assert first["content"]["text"] == "有来源的原文"


@pytest.mark.parametrize("section", ["project", "identity", "brief", "evidence", "source_master", "variant", "target", "content", "assets", "evidence_refs", "checks", "render", "production", "citations", "declarations"])
def test_v5_manifest_hash_covers_every_frozen_section(section):
    from app.services.candidates_v5 import build_manifest_v5

    manifest = build_manifest_v5(_inputs())
    changed = deepcopy(manifest)
    if isinstance(changed[section], dict):
        changed[section]["audit_change"] = "changed"
    else:
        changed[section].append({"audit_change": "changed"})
    assert candidate_hash(changed) != candidate_hash(manifest)


@pytest.mark.parametrize("mutation", [
    lambda item: item["identity"].pop("checksum"),
    lambda item: item["variant"].update(source_master_revision_id=999),
    lambda item: item["variant"].update(payload_hash="0" * 64),
    lambda item: item["target"]["profile"].update(artifact_kind="image"),
    lambda item: item["target"].update(content_form="thread"),
    lambda item: item["content"].update(citations=[{"id": "forged"}]),
    lambda item: item["checks"].pop(),
    lambda item: item["render"].update(artifact_kind="image"),
])
def test_v5_builder_rejects_missing_or_conflicting_provenance(mutation):
    from app.services.candidates_v5 import build_manifest_v5

    inputs = _inputs()
    mutation(inputs)
    with pytest.raises((ValueError, TypeError)):
        build_manifest_v5(inputs)


def test_v5_builder_rejects_raw_llm_receipt_and_accepts_safe_projection():
    from app.services.candidates_v5 import build_manifest_v5

    inputs = _inputs()
    receipt = {"llm_run_id": 101, "provider": "openai_compatible", "model": "model-1",
               "prompt_version": "v1", "purpose": "channel_adaptation", "input_hash": "5" * 64,
               "accepted_output_hash": inputs["variant"]["payload_hash"], "status": "succeeded"}
    inputs["production"]["llm_provenance"] = receipt
    assert build_manifest_v5(inputs)["production"]["llm_provenance"] == receipt
    inputs["production"]["llm_provenance"] = {**receipt, "raw_output": "secret"}
    with pytest.raises(ValueError, match="llm"):
        build_manifest_v5(inputs)


def test_v5_builder_rejects_raw_runtime_output_outside_safe_receipt():
    from app.services.candidates_v5 import build_manifest_v5

    inputs = _inputs()
    inputs["production"]["raw_output"] = "provider secret-bearing response"
    with pytest.raises(ValueError, match="production"):
        build_manifest_v5(inputs)
