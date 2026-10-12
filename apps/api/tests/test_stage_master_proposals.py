"""Project-native Master proposal Stage integration on isolated Mock Provider."""

import json

import pytest
from test_creation_recipe_stages import _setup


def _stage_definition():
    return {
        "nodes": [{
            "id": "draft",
            "kind": "AI",
            "plugin": "stage.master.propose",
            "plugin_version": "1",
            "stage_schema": "stage.master.propose.v1",
            "config": {"instruction": "生成一篇结构清晰的技术文章", "candidate_count": 2, "length": "medium"},
        }],
        "edges": [],
        "visual_order": ["draft"],
    }


def test_text_master_proposal_runs_from_preview_and_stops_before_master_save(client, db_session):
    from sqlalchemy import func, select

    from app.models import ContentMasterRevision, LLMRun

    headers, _, _, base = _setup(client)
    saved = client.post(
        f"{base}/workflow-override",
        headers=headers,
        json={"expected_revision": 0, "definition": _stage_definition()},
    )
    assert saved.status_code == 201, saved.text

    started = client.post(f"{base}/runs", headers=headers, json={"params": {}})
    assert started.status_code == 201, started.text
    run_id = started.json()["id"]
    preview = client.post(
        f"{base}/creation-recipe/stages/draft/preview",
        headers=headers,
        json={"run_id": run_id, "stage_override": {"candidate_count": 2}},
    )
    assert preview.status_code == 200, preview.text
    resolved = preview.json()
    assert resolved["ready"] is True
    assert resolved["effective_config"]["candidate_count"] == 2

    executed = client.post(
        f"{base}/creation-recipe/stages/draft/run",
        headers=headers,
        json={
            "run_id": run_id,
            "expected_resolution_hash": resolved["resolution_hash"],
            "invocation_key": "draft-stage-1",
            "stage_override": {"candidate_count": 2},
        },
    )
    assert executed.status_code == 200, executed.text
    body = executed.json()
    assert body["status"] == "waiting_input"
    assert len(body["output"]["candidates"]) == 2
    assert body["receipt"]["prompt_hash"] == resolved["prompt_hash"]
    assert body["output"]["llm_run_id"] >= 1
    llm_run = db_session.get(LLMRun, body["output"]["llm_run_id"])
    assert llm_run is not None
    assert llm_run.status == "succeeded"
    assert db_session.scalar(select(func.count(ContentMasterRevision.id))) == 0

    replay = client.post(
        f"{base}/creation-recipe/stages/draft/run",
        headers=headers,
        json={
            "run_id": run_id,
            "expected_resolution_hash": resolved["resolution_hash"],
            "invocation_key": "draft-stage-1",
            "stage_override": {"candidate_count": 2},
        },
    )
    assert replay.status_code == 200, replay.text
    assert replay.json()["attempt_id"] == body["attempt_id"]


def test_text_master_proposal_preview_hash_tracks_instruction_and_candidate_count(client):
    headers, _, _, base = _setup(client)
    assert client.post(
        f"{base}/workflow-override",
        headers=headers,
        json={"expected_revision": 0, "definition": _stage_definition()},
    ).status_code == 201
    run = client.post(f"{base}/runs", headers=headers, json={"params": {}}).json()
    first = client.post(
        f"{base}/creation-recipe/stages/draft/preview",
        headers=headers,
        json={"run_id": run["id"]},
    ).json()
    second = client.post(
        f"{base}/creation-recipe/stages/draft/preview",
        headers=headers,
        json={"run_id": run["id"], "stage_override": {"instruction": "只写实现边界", "candidate_count": 3}},
    ).json()
    assert first["resolution_hash"] != second["resolution_hash"]
    assert first["prompt_hash"] != second["prompt_hash"]
    assert first["effective_config"]["candidate_count"] == 2
    assert second["effective_config"]["candidate_count"] == 3


def _running_stage(client):
    headers, project_id, unit_id, base = _setup(client)
    assert client.post(f"{base}/workflow-override", headers=headers,
                       json={"expected_revision": 0, "definition": _stage_definition()}).status_code == 201
    run_id = client.post(f"{base}/runs", headers=headers, json={"params": {}}).json()["id"]
    resolved = client.post(f"{base}/creation-recipe/stages/draft/preview", headers=headers,
                          json={"run_id": run_id}).json()
    request = {"run_id": run_id, "expected_resolution_hash": resolved["resolution_hash"],
               "invocation_key": "original-call"}
    return headers, project_id, unit_id, base, resolved, request


def test_response_loss_replay_of_running_claim_does_not_call_provider(client, db_session, monkeypatch):
    from app.models import User, WorkflowRun, WorkflowStep
    from app.services import stage_master_proposals
    from app.services.stage_invocations import prepare_invocation

    headers, _, _, base, resolved, request = _running_stage(client)
    user = db_session.query(User).filter_by(email="recipe@studio.test").one()
    run = db_session.get(WorkflowRun, request["run_id"])
    step = db_session.query(WorkflowStep).filter_by(run_id=run.id, node_id="draft").one()
    original = prepare_invocation(db_session, run=run, step=step, user=user, resolved=resolved,
                                 expected_resolution_hash=resolved["resolution_hash"], invocation_key="original-call")
    monkeypatch.setattr(stage_master_proposals, "_run", lambda *_: pytest.fail("replay dispatched provider"))
    replay = client.post(f"{base}/creation-recipe/stages/draft/run", headers=headers, json=request)
    assert replay.status_code == 200, replay.text
    assert replay.json()["attempt_id"] == original.id
    assert replay.json()["status"] == "running"


def test_proposal_receipt_matches_actual_request_and_three_distinct_outputs(client, db_session, monkeypatch):
    from app.models import LLMRun
    from app.services import stage_master_proposals
    from app.services.generation.providers import GenerateResult, input_hash

    headers, _, _, base, _, request = _running_stage(client)
    request["stage_override"] = {"candidate_count": 3, "length": "short"}
    resolved = client.post(f"{base}/creation-recipe/stages/draft/preview", headers=headers,
                          json={"run_id": request["run_id"], "stage_override": request["stage_override"]}).json()
    request["expected_resolution_hash"] = resolved["resolution_hash"]
    captured = []

    def generate(_provider, actual):
        captured.append(actual)
        data = {"candidates": [{"title": f"方案 {index}", "body": f"正文 {index}"} for index in range(3)]}
        return GenerateResult(data=data, raw_output=json.dumps(data), usage={})

    monkeypatch.setattr(stage_master_proposals, "_run", generate)
    response = client.post(f"{base}/creation-recipe/stages/draft/run", headers=headers, json=request)
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["output"]["candidates"]) == 3
    assert len({candidate["payload_hash"] for candidate in body["output"]["candidates"]}) == 3
    assert captured[0].user_prompt == resolved["effective_prompt"]
    assert captured[0].system_prompt == resolved["system_prompt"]
    assert '"candidate_count":3' in captured[0].user_prompt
    assert '"length":"short"' in captured[0].user_prompt
    assert body["output"]["input_hash"] == input_hash(captured[0])
    assert db_session.get(LLMRun, body["output"]["llm_run_id"]).input_hash == input_hash(captured[0])


@pytest.mark.parametrize("data", [{"candidates": []}, {"candidates": [{}]},
                                  {"candidates": [{"title": "Only title"}]},
                                  {"candidates": [{"body": "a"}] * 6},
                                  {"candidates": [{"body": "a", "asset_refs": [{"material_revision_id": 999}]}]}])
def test_invalid_or_invented_proposal_never_becomes_success(client, db_session, monkeypatch, data):
    from app.models import ContentMasterRevision, LLMRun, WorkflowStep
    from app.services import stage_master_proposals
    from app.services.generation.providers import GenerateResult

    headers, _, _, base, _, request = _running_stage(client)
    monkeypatch.setattr(stage_master_proposals, "_run",
                        lambda *_: GenerateResult(data=data, raw_output=json.dumps(data), usage={}))
    response = client.post(f"{base}/creation-recipe/stages/draft/run", headers=headers, json=request)
    assert response.status_code == 422, response.text
    assert response.json()["detail"]["code"] == "stage_proposal_output_invalid"
    assert db_session.query(ContentMasterRevision).count() == 0
    assert db_session.query(LLMRun).count() == 1
    assert db_session.query(WorkflowStep).filter_by(run_id=request["run_id"]).one().status == "failed"


def test_changed_model_after_durable_claim_is_a_confirmed_zero_dispatch_failure(client, db_session, monkeypatch):
    from app.models import LLMRun, WorkflowStepAttempt
    from app.services import creation_recipes, stage_invocations, stage_master_proposals

    headers, _, _, base, _, request = _running_stage(client)
    claim = stage_invocations._claim_invocation
    actual_model = creation_recipes._model

    def changed(config):
        model, blockers = actual_model(config)
        return {**model, "runtime_hash": "f" * 64}, blockers

    def claim_then_change(*args, **kwargs):
        result = claim(*args, **kwargs)
        monkeypatch.setattr(creation_recipes, "_model", changed)
        return result

    monkeypatch.setattr(stage_invocations, "_claim_invocation", claim_then_change)
    monkeypatch.setattr(stage_master_proposals, "_run", lambda *_: pytest.fail("changed runtime dispatched"))
    response = client.post(f"{base}/creation-recipe/stages/draft/run", headers=headers, json=request)
    assert response.status_code == 409, response.text
    assert db_session.query(LLMRun).count() == 0
    receipt = db_session.query(WorkflowStepAttempt).one().execution_receipt_json
    assert receipt["outcome_state"] == "failed_before_dispatch"
    assert receipt["dispatch_certainty"] == "not_dispatched"


def test_stage_request_uses_pinned_runtime_not_a_stale_profile_cache(client, monkeypatch):
    from app.services.generation import providers

    headers, _, _, base, _, request = _running_stage(client)

    class StaleProvider:
        name = "openai_compatible"
        model = "wrong-model"

        async def generate_json(self, _request):
            pytest.fail("stale cached provider dispatched")

    monkeypatch.setitem(providers._providers, "default", StaleProvider())
    response = client.post(f"{base}/creation-recipe/stages/draft/run", headers=headers, json=request)
    assert response.status_code == 200, response.text
    assert response.json()["output"]["model"]["provider"] == "mock"


def test_committed_retry_reads_original_result_before_current_context_checks(client, monkeypatch):
    from app.services import creation_recipes

    headers, _, _, base, _, request = _running_stage(client)
    response = client.post(f"{base}/creation-recipe/stages/draft/run", headers=headers, json=request)
    assert response.status_code == 200, response.text
    monkeypatch.setattr(creation_recipes, "preview_stage", lambda *_args, **_kwargs:
                        pytest.fail("committed replay re-resolved a changed context"))
    replay = client.post(f"{base}/creation-recipe/stages/draft/run", headers=headers, json=request)
    assert replay.status_code == 200, replay.text
    assert replay.json()["attempt_id"] == response.json()["attempt_id"]
    assert replay.json()["output"] == response.json()["output"]


def test_context_drift_after_claim_is_detected_before_model_call(client, db_session, monkeypatch):
    from app.models import ContentUnit, LLMRun, WorkflowStepAttempt
    from app.services import stage_invocations, stage_master_proposals

    headers, _, unit_id, base, _, request = _running_stage(client)
    claim = stage_invocations._claim_invocation

    def claim_then_change(*args, **kwargs):
        result = claim(*args, **kwargs)
        unit = db_session.get(ContentUnit, unit_id)
        original_channel = unit.channel_id
        unit.channel_id = "x" if original_channel != "x" else "wechat"
        assert unit.channel_id != original_channel
        db_session.commit()
        return result

    monkeypatch.setattr(stage_invocations, "_claim_invocation", claim_then_change)
    monkeypatch.setattr(stage_master_proposals, "_run", lambda *_: pytest.fail("changed context dispatched"))
    response = client.post(f"{base}/creation-recipe/stages/draft/run", headers=headers, json=request)
    assert response.status_code == 409, response.text
    assert db_session.query(LLMRun).count() == 0
    assert db_session.query(WorkflowStepAttempt).one().execution_receipt_json["dispatch_certainty"] == "not_dispatched"


def test_client_cannot_replace_server_input_snapshot(client, db_session):
    from app.models import WorkflowStepAttempt

    headers, _, _, base, _, request = _running_stage(client)
    request["input_snapshot"] = {"forged": True}
    response = client.post(f"{base}/creation-recipe/stages/draft/run", headers=headers, json=request)
    assert response.status_code == 422, response.text
    assert db_session.query(WorkflowStepAttempt).count() == 0


def test_stage_run_requires_receipt_schema_before_writing_run_or_steps(client, db_session, monkeypatch):
    from app.models import ProjectEvent, WorkflowRun, WorkflowStep
    from app.services import stage_invocations

    headers, _, _, base = _setup(client)
    assert client.post(f"{base}/workflow-override", headers=headers,
                       json={"expected_revision": 0, "definition": _stage_definition()}).status_code == 201
    events_before = db_session.query(ProjectEvent).count()
    monkeypatch.setattr(stage_invocations, "receipt_schema_available", lambda _db: False)
    response = client.post(f"{base}/runs", headers=headers, json={"params": {}})
    assert response.status_code == 503, response.text
    assert response.json()["detail"]["code"] == "stage_receipt_schema_upgrade_required"
    assert db_session.query(WorkflowRun).count() == 0
    assert db_session.query(WorkflowStep).count() == 0
    assert db_session.query(ProjectEvent).count() == events_before


@pytest.mark.parametrize("modality", ["graphic", "video"])
def test_existing_graphic_video_proposals_preserve_explicit_master_adoption(client, db_session, modality):
    from app.models import ContentMasterRevision, ContentUnit, LLMRun, WorkflowStepAttempt

    headers, _, unit_id, base, _, request = _running_stage(client)
    db_session.get(ContentUnit, unit_id).modality = modality
    db_session.commit()
    preview = client.post(f"{base}/creation-recipe/stages/draft/preview", headers=headers,
                          json={"run_id": request["run_id"]})
    assert preview.status_code == 200, preview.text
    assert preview.json()["ready"] is True
    request["expected_resolution_hash"] = preview.json()["resolution_hash"]
    response = client.post(f"{base}/creation-recipe/stages/draft/run", headers=headers, json=request)
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "waiting_input"
    assert all(candidate["payload_schema"] == f"{modality}.master.v2" for candidate in response.json()["output"]["candidates"])
    assert db_session.query(LLMRun).count() == db_session.query(WorkflowStepAttempt).count() == 1
    assert db_session.query(ContentMasterRevision).count() == 0


@pytest.mark.parametrize("modality", ["audio", "unknown", "TEXT"])
def test_unsupported_master_modality_is_still_rejected_before_request_creation(modality):
    from app.services.stage_master_proposals import StageProposalError, build_master_request
    with pytest.raises(StageProposalError, match="stage_modality_unavailable"):
        build_master_request({"context": {"modality": modality}})
