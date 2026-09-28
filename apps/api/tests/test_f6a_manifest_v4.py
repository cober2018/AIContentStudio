"""A frozen v4 manifest needs no legacy Draft lineage."""

from copy import deepcopy

import pytest
from test_f6a_modality_adapters import HEADERS, _unit

from app.models import ContentMasterRevision, CreativeBriefRevision, IdentitySnapshot, ProjectFactBoundaryRevision
from app.services.candidates import candidate_hash


def _inputs(client, db):
    from app.services.candidates_v4 import load_manifest_v4_inputs

    _, path = _unit(client, db, "text")
    response = client.post(path, json={"idempotency_key": "manifest", "payload": {"title": "手工正文", "markdown": "没有旧稿件的正文", "citations": [{"kind": "author_opinion"}], "declarations": ["独立观点"]}}, headers=HEADERS)
    assert response.status_code == 200, response.text
    master = db.get(ContentMasterRevision, response.json()["id"])
    client.post(f"{path}/{master.id}/checks", headers=HEADERS)
    return master, load_manifest_v4_inputs(db, master)


def test_manual_master_manifest_freezes_actual_context_and_checks(client, db_session):
    from app.services.candidates_v4 import build_manifest_v4

    master, inputs = _inputs(client, db_session)
    manifest = build_manifest_v4(inputs)
    assert manifest["schema_version"] == 4
    assert manifest["artifact_kind"] == "text"
    assert manifest["channel"] == "wechat"
    assert manifest["content_form"] == "article"
    assert manifest["identity"]["checksum"] == db_session.get(IdentitySnapshot, master.identity_snapshot_id).checksum
    assert manifest["brief"]["checksum"] == db_session.get(CreativeBriefRevision, master.creative_brief_revision_id).checksum
    boundary = db_session.get(ProjectFactBoundaryRevision, master.fact_boundary_revision_id)
    assert manifest["evidence"]["fact_pack"] == {"id": boundary.fact_pack_id, "version": boundary.fact_pack_version, "checksum": boundary.fact_pack_checksum}
    assert manifest["content_master"]["payload_hash"] == master.payload_hash
    assert manifest["content"] == master.payload_json
    assert manifest["production"]["workflow"] is None
    assert manifest["production"]["output"] is None
    assert {check["kind"] for check in manifest["checks"]} == {"master_schema", "evidence", "rights", "render"}
    assert all(check["status"] == "pass" and check["input_hash"] for check in manifest["checks"])
    assert manifest["render"]["origin"] == "deterministic"
    assert manifest["citations"] == master.payload_json["citations"]
    assert manifest["declarations"] == master.payload_json["declarations"]
    assert "readiness" not in manifest["identity"]


def test_manifest_hash_is_order_independent_and_inputs_do_not_alias(client, db_session):
    from app.services.candidates_v4 import build_manifest_v4

    _, inputs = _inputs(client, db_session)
    manifest = build_manifest_v4(inputs)
    reordered = {key: inputs[key] for key in reversed(inputs)}
    reordered["content"] = {key: inputs["content"][key] for key in reversed(inputs["content"])}
    assert candidate_hash(manifest) == candidate_hash(build_manifest_v4(reordered))
    inputs["content"]["markdown"] = "调用方后来改变"
    assert manifest["content"]["markdown"] == "没有旧稿件的正文"


@pytest.mark.parametrize("section", ["project", "identity", "brief", "evidence", "content_master", "content", "checks", "render", "production", "assets", "evidence_refs", "citations", "declarations"])
def test_manifest_hash_covers_every_frozen_section(client, db_session, section):
    from app.services.candidates_v4 import build_manifest_v4

    _, inputs = _inputs(client, db_session)
    manifest = build_manifest_v4(inputs)
    changed = deepcopy(manifest)
    if isinstance(changed[section], dict):
        changed[section]["audit_change"] = "changed"
    else:
        changed[section].append({"audit_change": "changed"})
    assert candidate_hash(changed) != candidate_hash(manifest)


def test_builder_rejects_incomplete_snapshot_not_fake_provenance(client, db_session):
    from app.services.candidates_v4 import build_manifest_v4

    _, inputs = _inputs(client, db_session)
    inputs["identity"].pop("checksum")
    with pytest.raises(ValueError, match="identity"):
        build_manifest_v4(inputs)
