"""Only proven Draft references become Master references."""

import pytest
from test_candidate_manifest_v2 import env as draft_env  # noqa: F401
from test_f6a_modality_adapters import HEADERS, _render_material, _unit

from app.models import (
    ContentUnit,
    DraftMedia,
    Fact,
    FactPackItem,
    ProjectWorkflowOutput,
    SourceDocument,
    Workflow,
    WorkflowRun,
    WorkflowStep,
    WorkflowStepAttempt,
)


def _source(client, db, draft, tmp_path, *, visible=True, matching_pack=True):
    project, path = _unit(client, db, "text")
    unit = db.get(ContentUnit, int(path.split("/")[6]))
    material = _render_material(db, project, tmp_path, "graphic")
    if not visible:
        from app.models import ProjectMaterialReference

        db.query(ProjectMaterialReference).filter_by(project_id=project, material_revision_id=material.id).one().status = "detached"
    draft.body = "真实事实"
    document = {"schema_version": 1, "blocks": [{"type": "paragraph", "text": draft.body}, {"type": "image", "material_revision_id": material.id, "alt": "配图"}]}
    draft.document_json = document
    db.add(DraftMedia(draft_id=draft.id, material_revision_id=material.id, content_hash=material.content_hash, role="inline", sort_order=0, public_use_allowed=True, placement_json={"after": "intro"}))
    source = SourceDocument(title="源文档", source_type="text", raw_text="事实", parse_status="parsed")
    db.add(source)
    db.flush()
    fact = Fact(source_document_id=source.id, statement="真实事实", status="confirmed")
    db.add(fact)
    db.flush()
    pack = draft.content_job.topic_brief.fact_pack
    item = FactPackItem(fact_pack_id=pack.id, fact_id=fact.id, evidence_kind="fact", snapshot_json={"statement": fact.statement}, snapshot_checksum="s" * 64, public_use_allowed=True)
    db.add(item)
    db.flush()
    draft.structured_json = {**draft.structured_json, "claim_fact_map": [{"text": fact.statement, "fact_ids": [str(fact.id)]}]}
    draft.content_job.fact_pack_snapshot = {"id": pack.id, "version": pack.version, "checksum": pack.checksum} if matching_pack else {"id": pack.id, "version": pack.version, "checksum": "different"}
    db.commit()
    bound = client.post(f"/api/v1/content-projects/{project}/fact-boundary", json={"expected_revision": 1, "fact_pack_id": pack.id}, headers=HEADERS)
    assert bound.status_code == 201, bound.text
    workflow = Workflow(name="真实定义", workflow_key="seed", version=1, checksum="w" * 64, definition_json={})
    db.add(workflow)
    db.flush()
    run = WorkflowRun(workflow_id=workflow.id, workflow_version=workflow.version, definition_checksum=workflow.checksum, content_unit_id=unit.id, identity_snapshot_id=unit.identity_snapshot_id, status="succeeded")
    db.add(run)
    db.flush()
    draft.content_job.workflow_run_id = run.id
    step = WorkflowStep(run_id=run.id, node_id="generate", node_type="AI", plugin_key="builtin.generate", status="succeeded", attempt_no=1, output_json={"draft_id": draft.id}, output_hash="o" * 64)
    db.add(step)
    db.flush()
    attempt = WorkflowStepAttempt(step_id=step.id, run_id=run.id, node_id=step.node_id, attempt_no=1, status="succeeded", output_json=step.output_json, output_hash=step.output_hash, input_hash="i" * 64)
    db.add(attempt)
    db.flush()
    output = ProjectWorkflowOutput(project_id=project, unit_id=unit.id, run_id=run.id, node_id=step.node_id, attempt_id=attempt.id, output_kind="draft", entity_id=draft.id)
    db.add(output)
    db.commit()
    return path, output, material, item, run


def test_seed_maps_exact_media_evidence_and_document_without_copy(client, draft_env, tmp_path):  # noqa: F811
    db, _, draft = draft_env
    path, output, material, item, _ = _source(client, db, draft, tmp_path)
    response = client.post(f"{path}/from-output", json={"project_output_id": output.id, "idempotency_key": "mapped"}, headers=HEADERS)
    assert response.status_code == 200, response.text
    master = response.json()
    assert master["payload_schema"] == "text.master.v2"
    assert master["payload"]["document"]["schema"] == "studio.text.document.v1"
    assert "markdown" not in master["payload"]
    assert master["payload"]["document"]["blocks"][1]["material_revision_id"] == material.id
    assert master["assets"][0]["material_revision_id"] == material.id
    assert master["assets"][0]["placement"] == {"after": "intro"}
    assert master["evidence"][0]["fact_pack_item_id"] == item.id
    assert master["evidence"][0]["snapshot_checksum"] == item.snapshot_checksum
    assert master["edit_summary"]["unmapped_claims"] == []
    assert master["edit_summary"]["unmapped_media_ids"] == []
    assert master["edit_summary"]["workflow_source"]["draft_content_hash"]


@pytest.mark.parametrize("problem", ["foreign_media", "different_snapshot"])
def test_unproven_seed_refs_produce_incomplete_checks_not_silent_success(client, draft_env, tmp_path, problem):  # noqa: F811
    db, _, draft = draft_env
    path, output, _, _, _ = _source(client, db, draft, tmp_path, visible=problem != "foreign_media", matching_pack=problem != "different_snapshot")
    response = client.post(f"{path}/from-output", json={"project_output_id": output.id, "idempotency_key": "unmapped"}, headers=HEADERS)
    assert response.status_code == 200, response.text
    master = response.json()
    checks = client.post(f"{path}/{master['id']}/checks", headers=HEADERS).json()["items"]
    kind = "rights" if problem == "foreign_media" else "evidence"
    assert next(item for item in checks if item["check_kind"] == kind)["status"] == "incomplete"
    assert master["assets" if problem == "foreign_media" else "evidence"] == []


def test_seed_identical_action_replays_frozen_content_after_draft_changes(client, draft_env, tmp_path):  # noqa: F811
    db, _, draft = draft_env
    path, output, _, _, _ = _source(client, db, draft, tmp_path)
    body = {"project_output_id": output.id, "idempotency_key": "replay"}
    saved = client.post(f"{path}/from-output", json=body, headers=HEADERS).json()
    draft.body = "后来的不同正文"
    db.commit()
    replay = client.post(f"{path}/from-output", json=body, headers=HEADERS)
    assert replay.status_code == 200, replay.text
    assert replay.json()["id"] == saved["id"]
    assert replay.json()["payload"] == saved["payload"]


@pytest.mark.parametrize("problem", ["checksum", "version"])
def test_seed_rejects_unverified_workflow_definition(client, draft_env, tmp_path, problem):  # noqa: F811
    db, _, draft = draft_env
    path, output, _, _, run = _source(client, db, draft, tmp_path)
    if problem == "checksum":
        run.definition_checksum = None
    else:
        run.workflow_version = 99
    db.commit()
    response = client.post(f"{path}/from-output", json={"project_output_id": output.id, "idempotency_key": "invalid"}, headers=HEADERS)
    assert response.status_code == 409, response.text


def test_seeded_master_freezes_exact_attempt_media_and_evidence_provenance(client, draft_env, tmp_path):  # noqa: F811
    from app.models import User
    from app.services.content_masters import _draft_references, save_revision

    db, _, draft = draft_env
    path, output, material, item, run = _source(client, db, draft, tmp_path)
    assets, evidence, _, _ = _draft_references(db, draft, output.project_id)
    # Reconstruct an already-existing v1 seed; new from-output requests use v2.
    master = save_revision(db, project_id=output.project_id, unit_id=output.unit_id, user=db.query(User).filter_by(email=HEADERS["X-Studio-User"]).one(), workflow_seed=True, payload={
        "idempotency_key": "legacy-seed-freeze", "payload_schema": "text.master.v1", "payload": {"title": draft.title, "markdown": draft.body, "document": draft.document_json},
        "asset_refs": assets, "evidence_refs": evidence, "source_kind": "workflow_seed", "origin_workflow_run_id": run.id, "origin_project_output_id": output.id,
        "edit_summary": {"workflow_source": {"draft_id": draft.id, "definition_checksum": run.definition_checksum, "attempt_id": output.attempt_id}},
    })
    replay = client.post(f"{path}/from-output", json={"project_output_id": output.id, "idempotency_key": "legacy-seed-freeze"}, headers=HEADERS)
    assert replay.status_code == 200, replay.text
    assert replay.json()["id"] == master["id"]
    assert replay.json()["payload_schema"] == "text.master.v1"
    checks = client.post(f"{path}/{master['id']}/checks", headers=HEADERS).json()["items"]
    assert all(check["status"] == "pass" for check in checks)
    frozen = client.post(path.replace("master-revisions", "candidates/freeze"), json={"content_master_revision_id": master["id"], "expected_payload_hash": master["payload_hash"]}, headers=HEADERS)
    assert frozen.status_code == 201, frozen.text
    manifest = frozen.json()["manifest"]
    assert manifest["production"]["workflow"]["definition_checksum"] == run.definition_checksum
    assert manifest["production"]["output"]["attempt_id"] == output.attempt_id
    assert manifest["assets"][0]["material_revision_id"] == material.id
    assert manifest["evidence_refs"][0]["fact_pack_item_id"] == item.id
    assert manifest["content"]["document"] == draft.document_json


def test_v2_seed_and_upgrade_reuse_one_canonical_converter(client, draft_env, tmp_path):  # noqa: F811
    db, _, draft = draft_env
    path, output, material, item, _ = _source(client, db, draft, tmp_path)
    _, other_path = _unit(client, db, "text", suffix="equivalence")
    from app.models import ProjectMaterialReference

    other_project = int(other_path.split("/")[4])
    db.add(ProjectMaterialReference(project_id=other_project, material_revision_id=material.id, origin="system_library", status="active"))
    db.commit()
    assert client.post(f"/api/v1/content-projects/{other_project}/fact-boundary", json={"expected_revision": 1, "fact_pack_id": item.fact_pack_id}, headers=HEADERS).status_code == 201
    from app.services.content_masters import _draft_references

    assets, evidence, _, _ = _draft_references(db, draft, output.project_id)
    legacy = client.post(other_path, json={"idempotency_key": "v1", "payload_schema": "text.master.v1", "payload": {"title": draft.title, "markdown": draft.body, "document": draft.document_json}, "asset_refs": assets, "evidence_refs": evidence}, headers=HEADERS)
    assert legacy.status_code == 200, legacy.text
    preview = client.get(f"{other_path}/{legacy.json()['id']}/text-v2-upgrade-preview", headers=HEADERS)
    assert preview.status_code == 200, preview.text
    seeded = client.post(f"{path}/from-output", json={"project_output_id": output.id, "idempotency_key": "v2-seed"}, headers=HEADERS)
    assert seeded.status_code == 200, seeded.text
    assert seeded.json()["payload"] == preview.json()["payload"]
    assert seeded.json()["edit_summary"]["document_hash"] == preview.json()["document_hash"]
    assert seeded.json()["evidence"][0]["locator"] == preview.json()["evidence_refs"][0]["locator"]


def test_v2_seed_unlocatable_claim_is_not_a_fake_citation(client, draft_env, tmp_path):  # noqa: F811
    db, _, draft = draft_env
    path, output, _, _, _ = _source(client, db, draft, tmp_path)
    draft.body = "没有这条事实的正文"
    db.commit()
    response = client.post(f"{path}/from-output", json={"project_output_id": output.id, "idempotency_key": "unlocatable"}, headers=HEADERS)
    assert response.status_code == 200, response.text
    master = response.json()
    assert master["evidence"] == []
    assert master["payload"]["document"]["citations"] == []
    assert any(w["code"] == "unmapped_evidence_locator" for w in master["edit_summary"]["conversion_warnings"])
    checks = client.post(f"{path}/{master['id']}/checks", headers=HEADERS).json()["items"]
    assert next(c for c in checks if c["check_kind"] == "evidence")["status"] == "incomplete"


def test_new_v2_seed_cannot_bypass_current_v1_upgrade(client, draft_env, tmp_path):  # noqa: F811
    db, _, draft = draft_env
    path, output, _, _, _ = _source(client, db, draft, tmp_path)
    old = client.post(path, json={"idempotency_key": "manual-v1", "payload": {"markdown": "仍然是 v1"}}, headers=HEADERS)
    assert old.status_code == 200, old.text
    response = client.post(f"{path}/from-output", json={"project_output_id": output.id, "idempotency_key": "seed-over-v1", "expected_revision": 1}, headers=HEADERS)
    assert response.status_code == 409, response.text
    assert response.json()["detail"]["code"] == "explicit_master_upgrade_required"
    assert len(client.get(path, headers=HEADERS).json()["items"]) == 1
