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
    document = {"type": "doc", "content": [{"type": "paragraph", "text": "原稿"}]}
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
    assert master["payload"]["document"] == draft.document_json
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
    assert replay.json()["payload"]["markdown"] == saved["payload"]["markdown"]


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
    db, _, draft = draft_env
    path, output, material, item, run = _source(client, db, draft, tmp_path)
    saved = client.post(f"{path}/from-output", json={"project_output_id": output.id, "idempotency_key": "seed-freeze"}, headers=HEADERS)
    assert saved.status_code == 200, saved.text
    master = saved.json()
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
