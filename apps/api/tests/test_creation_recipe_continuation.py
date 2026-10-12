"""Acceptance-gated automatic continuation for Creation Recipe stages."""

import pytest
from test_creation_recipe_stages import _setup

from app.services.stage_contracts import digest


def _two_stage_run(client):
    headers, project_id, unit_id, base = _setup(client)
    definition = {
        "nodes": [
            {
                "id": "outline",
                "kind": "AI",
                "plugin": "stage.master.propose",
                "plugin_version": "1",
                "stage_schema": "stage.master.propose.v1",
                "config": {"instruction": "先生成文章大纲", "candidate_count": 1, "length": "short"},
            },
            {
                "id": "draft",
                "kind": "AI",
                "plugin": "stage.master.propose",
                "plugin_version": "1",
                "stage_schema": "stage.master.propose.v1",
                "config": {"instruction": "根据已接受大纲生成初稿", "candidate_count": 1, "length": "short"},
            },
        ],
        "edges": [{"from": "outline", "to": "draft"}],
        "visual_order": ["outline", "draft"],
    }
    saved = client.post(f"{base}/workflow-override", headers=headers,
                        json={"expected_revision": 0, "definition": definition})
    assert saved.status_code == 201, saved.text
    run = client.post(f"{base}/runs", headers=headers, json={"params": {}})
    assert run.status_code == 201, run.text
    run_id = run.json()["id"]
    preview = client.post(f"{base}/creation-recipe/stages/outline/preview", headers=headers,
                          json={"run_id": run_id}).json()
    execution = client.post(f"{base}/creation-recipe/stages/outline/run", headers=headers, json={
        "run_id": run_id, "expected_resolution_hash": preview["resolution_hash"],
        "invocation_key": "outline-explicit",
    })
    assert execution.status_code == 200, execution.text
    body = execution.json()
    candidate = body["output"]["candidates"][0]
    acceptance = {
        "run_id": run_id, "attempt_id": body["attempt_id"],
        "expected_output_hash": body["receipt"]["output_hash"],
        "expected_resolution_hash": preview["resolution_hash"],
        "expected_context_hash": digest(preview["context"]),
        "candidate_id": candidate["candidate_id"],
        "candidate_hash": digest({key: value for key, value in candidate.items() if key != "candidate_hash"}),
        "expected_revision": 0, "adoption_key": "outline-acceptance",
        "payload": candidate["payload"], "asset_refs": candidate["asset_refs"],
        "evidence_refs": candidate["evidence_refs"], "decision": "accepted", "note": "接受大纲",
    }
    return headers, project_id, unit_id, base, run_id, body, acceptance


def _accept(client, base, headers, acceptance):
    return client.post(f"{base}/creation-recipe/stages/outline/accept-master",
                       headers=headers, json=acceptance)


def test_success_without_acceptance_does_not_release_downstream(client, db_session):
    from app.models import WorkflowStep

    headers, _, _, base, run_id, _, _ = _two_stage_run(client)
    preview = client.post(f"{base}/creation-recipe/stages/draft/preview", headers=headers,
                          json={"run_id": run_id})
    assert preview.status_code == 200, preview.text
    assert preview.json()["ready"] is False
    assert "upstream_acceptance_required" in preview.json()["blockers"]
    assert db_session.query(WorkflowStep).filter_by(run_id=run_id, node_id="draft").one().status == "pending"


def test_acceptance_runs_next_stage_once_and_stops_for_its_review(client, db_session):
    from app.models import LLMRun, WorkflowStep, WorkflowStepAttempt

    headers, _, _, base, run_id, _, acceptance = _two_stage_run(client)
    response = _accept(client, base, headers, acceptance)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["continuation"]["status"] == "waiting_input"
    assert result["continuation"]["node_id"] == "draft"
    draft = db_session.query(WorkflowStep).filter_by(run_id=run_id, node_id="draft").one()
    assert draft.status == "waiting_input"
    draft_attempt = db_session.query(WorkflowStepAttempt).filter_by(run_id=run_id, node_id="draft").one()
    assert draft_attempt.execution_receipt_json["request_mode"] == "automatic"
    assert draft_attempt.execution_receipt_json["prepared_by_server"] is True
    assert draft_attempt.input_snapshot_json["resolved_stage"]["upstream"]["outline"]["output_kind"] == "content_master_revision"
    assert db_session.query(WorkflowStepAttempt).filter_by(run_id=run_id, node_id="draft").count() == 1
    assert db_session.query(LLMRun).count() == 2

    replay = _accept(client, base, headers, acceptance)
    assert replay.status_code == 200, replay.text
    assert replay.json()["master"]["id"] == result["master"]["id"]
    assert replay.json()["continuation"]["status"] == "waiting_input"
    assert replay.json()["continuation"]["attempt_id"] == draft_attempt.id
    assert db_session.query(WorkflowStepAttempt).filter_by(run_id=run_id, node_id="draft").count() == 1
    assert db_session.query(LLMRun).count() == 2


def test_accepted_upstream_projection_contains_exact_entity_and_hash(client, db_session):
    from app.models import WorkflowStep

    headers, _, _, base, run_id, _, acceptance = _two_stage_run(client)
    assert _accept(client, base, headers, acceptance).status_code == 200
    preview = client.post(f"{base}/creation-recipe/stages/draft/preview", headers=headers,
                          json={"run_id": run_id})
    assert preview.status_code == 200, preview.text
    upstream = preview.json()["upstream"]["outline"]
    assert upstream["output_kind"] == "content_master_revision"
    assert upstream["entity_id"] >= 1
    assert upstream["accepted_hash"] == upstream["payload_hash"]
    assert upstream["decision"] == "accepted"
    master = client.get(f"{base}/master-revisions/{upstream['entity_id']}", headers=headers)
    assert master.status_code == 200, master.text
    assert upstream["payload"] == master.json()["payload"]
    assert digest(upstream["payload"]) == upstream["accepted_hash"]
    assert db_session.query(WorkflowStep).filter_by(run_id=run_id, node_id="outline").one().status == "succeeded"


def test_blocked_continuation_remains_visible_on_reload_and_replay(client, db_session):
    from app.models import WorkflowStep

    headers, _, _, base, run_id, _, acceptance = _two_stage_run(client)
    assert _accept(client, base, headers, acceptance).status_code == 200
    draft = db_session.query(WorkflowStep).filter_by(run_id=run_id, node_id="draft").one()
    draft.status, draft.error = "blocked", "accepted_context_changed"
    db_session.commit()
    replay = _accept(client, base, headers, acceptance)
    assert replay.status_code == 200, replay.text
    assert replay.json()["continuation"]["status"] == "blocked"
    recipe = client.get(f"{base}/creation-recipe", headers=headers).json()
    assert "accepted_context_changed" in next(stage for stage in recipe["stages"] if stage["node_id"] == "draft")["blockers"]


def test_continuation_does_not_overwrite_unknown_outcome(client, db_session):
    from app.models import WorkflowRun, WorkflowStep
    from app.services.stage_continuation import _blocked

    _, _, _, _, run_id, _, _ = _two_stage_run(client)
    run = db_session.get(WorkflowRun, run_id)
    step = db_session.query(WorkflowStep).filter_by(run_id=run_id, node_id="draft").one()
    run.status = step.status = "unknown"
    step.error = run.error = "stage_dispatch_unknown"
    db_session.commit()
    result = _blocked(db_session, run, step, "draft", "stage_dispatch_unknown")
    assert result["status"] == "unknown"
    db_session.refresh(run)
    db_session.refresh(step)
    assert step.status == run.status == "unknown"


@pytest.mark.parametrize("field", ["run_id", "node_id", "project_id"])
def test_acceptance_replay_rejects_tampered_output_link(client, db_session, field):
    from app.models import ProjectWorkflowOutput

    headers, _, _, base, _, _, acceptance = _two_stage_run(client)
    accepted = _accept(client, base, headers, acceptance).json()
    output = db_session.get(ProjectWorkflowOutput, accepted["project_output_id"])
    setattr(output, field, "foreign-stage" if field == "node_id" else getattr(output, field) + 100)
    db_session.commit()
    replay = _accept(client, base, headers, acceptance)
    assert replay.status_code == 409, replay.text


def test_preview_blocks_accepted_content_after_brief_drift(client, db_session):
    from app.models import CreativeBriefRevision

    headers, project_id, _, base, run_id, _, acceptance = _two_stage_run(client)
    assert _accept(client, base, headers, acceptance).status_code == 200
    brief = CreativeBriefRevision(project_id=project_id, revision_no=1, objective="新的任务目标",
                                  checksum="e" * 64, created_by="recipe@studio.test")
    db_session.add(brief)
    db_session.commit()
    preview = client.post(f"{base}/creation-recipe/stages/draft/preview", headers=headers, json={"run_id": run_id})
    assert preview.status_code == 200, preview.text
    assert preview.json()["ready"] is False
    assert "accepted_context_changed" in preview.json()["blockers"]


@pytest.mark.parametrize("resource", ["asset", "evidence"])
@pytest.mark.parametrize("restriction", ["model_use_denied", "revoked", "hash_changed"])
def test_preview_never_sends_accepted_content_with_restricted_live_refs(client, db_session, monkeypatch,
                                                                     resource, restriction):
    from app.models import (
        ContentMasterAssetRef,
        ContentMasterEvidenceRef,
        FactPack,
        FactPackItem,
        Material,
        MaterialRevision,
        utcnow,
    )
    from app.services import stage_master_adoptions

    headers, _, _, base, run_id, _, acceptance = _two_stage_run(client)
    accepted = _accept(client, base, headers, acceptance).json()
    master_id = accepted["master"]["id"]
    if resource == "asset":
        material = Material(title="精确素材", status="active")
        db_session.add(material)
        db_session.flush()
        revision = MaterialRevision(material_id=material.id, content_hash="a" * 64, status="accepted",
                                    public_use_allowed=True, model_use_allowed=True)
        db_session.add(revision)
        db_session.flush()
        db_session.add(ContentMasterAssetRef(master_revision_id=master_id, material_revision_id=revision.id,
                                             role="inline", content_hash_snapshot=revision.content_hash))
        if restriction == "model_use_denied":
            revision.model_use_allowed = False
        elif restriction == "revoked":
            revision.status = "revoked"
        else:
            revision.content_hash = "b" * 64
        monkeypatch.setattr(stage_master_adoptions, "read_bytes_checked", lambda *_args: b"isolated bytes")
    else:
        pack = FactPack(name="精确证据", version=1)
        db_session.add(pack)
        db_session.flush()
        item = FactPackItem(fact_pack_id=pack.id, evidence_kind="author_opinion", snapshot_checksum="c" * 64,
                            public_use_allowed=True, model_use_allowed=True)
        db_session.add(item)
        db_session.flush()
        db_session.add(ContentMasterEvidenceRef(master_revision_id=master_id, fact_pack_item_id=item.id,
                                                role="citation", snapshot_checksum=item.snapshot_checksum))
        if restriction == "model_use_denied":
            item.model_use_allowed = False
        elif restriction == "revoked":
            item.public_use_revoked_at = utcnow()
        else:
            item.snapshot_checksum = "d" * 64
    db_session.commit()
    response = client.post(f"{base}/creation-recipe/stages/draft/preview", headers=headers, json={"run_id": run_id})
    assert response.status_code == 200, response.text
    preview = response.json()
    assert preview["ready"] is False
    assert "outline" not in preview["upstream"]
    assert f"stage_{resource}_model_use_blocked" in preview["blockers"]


def test_stage_result_read_restores_original_receipt_and_prompt_without_dispatch(client, db_session, monkeypatch):
    from app.models import ContentMasterRevision, LLMRun
    from app.services import stage_master_proposals

    headers, _, _, base, run_id, execution, _ = _two_stage_run(client)
    count = db_session.query(LLMRun).count()
    monkeypatch.setattr(stage_master_proposals, "_run", lambda *_: pytest.fail("result read dispatched a provider"))
    response = client.get(f"{base}/creation-recipe/stages/outline/result",
                          headers=headers, params={"run_id": run_id, "attempt_id": execution["attempt_id"]})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["output"] == execution["output"] and body["receipt"] == execution["receipt"]
    assert body["resolved_stage"]["prompt_hash"] == execution["receipt"]["prompt_hash"]
    assert body["resolved_stage"]["effective_prompt"]
    assert body["is_current"] is True
    assert db_session.query(LLMRun).count() == count
    assert db_session.query(ContentMasterRevision).count() == 0
    foreign = client.get(f"{base}/creation-recipe/stages/draft/result",
                         headers=headers, params={"run_id": run_id, "attempt_id": execution["attempt_id"]})
    assert foreign.status_code == 404, foreign.text


def test_stage_result_read_is_owner_scoped_and_allows_archived_inspection(client, db_session):
    from app.models import ContentUnit

    headers, _, unit_id, base, run_id, execution, _ = _two_stage_run(client)
    url = f"{base}/creation-recipe/stages/outline/result"
    params = {"run_id": run_id, "attempt_id": execution["attempt_id"]}
    db_session.get(ContentUnit, unit_id).status = "archived"
    db_session.commit()
    historical = client.get(url, headers=headers, params=params)
    assert historical.status_code == 200, historical.text
    assert historical.json()["is_current"] is False
    foreign = client.get(url, headers={"X-User-Email": "foreign@studio.test"}, params=params)
    assert foreign.status_code in {401, 403, 404}, foreign.text


def test_stage_result_recovers_exact_invocation_after_new_run_without_dispatch(client, monkeypatch):
    from app.services import stage_master_proposals

    headers, _, _, base, run_id, execution, _ = _two_stage_run(client)
    new_run = client.post(f"{base}/runs", headers=headers, json={"params": {}})
    assert new_run.status_code == 201, new_run.text
    monkeypatch.setattr(stage_master_proposals, "_run", lambda *_: pytest.fail("read dispatched a provider"))
    url = f"{base}/creation-recipe/stages/outline/result"
    params = {"run_id": run_id, "invocation_key": execution["receipt"]["invocation_key"]}
    read = client.get(url, headers=headers, params=params)
    assert read.status_code == 200, read.text
    assert read.json()["run_id"] == run_id
    assert read.json()["attempt_id"] == execution["attempt_id"]
    assert read.json()["receipt"]["invocation_key"] == params["invocation_key"]
    missing = client.get(url, headers=headers, params={**params, "invocation_key": "manual:foreign"})
    assert missing.status_code == 404, missing.text
    mixed = client.get(url, headers=headers, params={**params, "attempt_id": execution["attempt_id"]})
    assert mixed.status_code == 422, mixed.text
