"""Explicit feedback and reusable Recipe improvements on an isolated database."""

from copy import deepcopy

import pytest
from sqlalchemy import event
from test_stage_master_adoptions import _accept, _proposal
from test_stage_master_proposals import _running_stage

from app.models import (
    CapabilityArtifact,
    CapabilityUse,
    ContentMasterRevision,
    ContentUnit,
    LLMRun,
    PersonaWorkflowDefault,
    ProjectEvent,
    ProjectWorkflowBinding,
    User,
    Workflow,
    WorkflowRun,
    WorkflowStep,
    WorkflowStepAttempt,
)
from app.services.stage_contracts import digest


def _stage(base):
    return f"{base}/creation-recipe/stages/draft"


def _accepted(client, *, override=None, edited=False):
    if override is None:
        headers, project_id, unit_id, base, execution, acceptance = _proposal(client)
    else:
        headers, project_id, unit_id, base, _, run_request = _running_stage(client)
        preview = client.post(f"{_stage(base)}/preview", headers=headers,
                              json={"run_id": run_request["run_id"], "stage_override": override})
        assert preview.status_code == 200, preview.text
        resolved = preview.json()
        run = client.post(f"{_stage(base)}/run", headers=headers,
                          json={**run_request, "stage_override": override,
                                "expected_resolution_hash": resolved["resolution_hash"]})
        assert run.status_code == 200, run.text
        execution = run.json()
        candidate = execution["output"]["candidates"][0]
        acceptance = {
            "run_id": execution["run_id"], "attempt_id": execution["attempt_id"],
            "expected_output_hash": execution["receipt"]["output_hash"],
            "expected_resolution_hash": resolved["resolution_hash"],
            "expected_context_hash": digest(resolved["context"]),
            "candidate_id": candidate["candidate_id"], "candidate_hash": candidate["candidate_hash"],
            "expected_revision": 0, "adoption_key": "accept-learning-proposal",
            "payload": candidate["payload"], "asset_refs": candidate["asset_refs"],
            "evidence_refs": candidate["evidence_refs"], "decision": "accepted",
        }
    if edited:
        acceptance["payload"] = {**acceptance["payload"], "title": "编辑明确改过的标题"}
        acceptance["decision"] = "accepted_with_edits"
    accepted = _accept(client, base, headers, acceptance)
    assert accepted.status_code == 200, accepted.text
    evidence = {"run_id": execution["run_id"], "attempt_id": execution["attempt_id"],
                "feedback_event_id": accepted.json()["feedback_event_id"]}
    return headers, project_id, unit_id, base, evidence


def _improvement(client, headers, base, evidence, **patch):
    request = {**evidence, **patch}
    response = client.post(f"{_stage(base)}/improvement-preview", headers=headers, json=request)
    assert response.status_code == 200, response.text
    preview = response.json()
    return preview, {**request, "expected_preview_hash": preview["preview_hash"],
                     "expected_revision": preview["expected_revision"], "idempotency_key": "save-adjustment"}


def _tuning_request(evidence):
    return {"invocation_key": "explicit-tuning", "feedback_event_ids": [evidence["feedback_event_id"]]}


@pytest.mark.parametrize("feedback_ids", [[{}], [[]], [], [True], [0], ["1"], [1, 1], list(range(1, 22))])
def test_tuning_rejects_unhashable_feedback_ids_before_claim_or_provider(
    client, db_session, monkeypatch, feedback_ids,
):
    from app.services import stage_tuning

    headers, _, _, base, _, _ = _running_stage(client)
    monkeypatch.setattr(stage_tuning.MockProvider, "generate_json",
                        lambda *_: pytest.fail("invalid feedback dispatched provider"))
    response = client.post(f"{base}/creation-recipe/stages/draft/tuning-suggestion", headers=headers,
                           json={"invocation_key": "invalid-feedback", "feedback_event_ids": feedback_ids})
    assert response.status_code == 422, response.text
    assert response.json()["detail"]["code"] == "recipe_tuning_feedback_required"
    assert db_session.query(LLMRun).count() == 0


@pytest.mark.parametrize("decision", ["rejected", "rerun_requested"])
def test_feedback_is_append_only_idempotent_and_keeps_proposal_immutable(client, db_session, decision):
    headers, _, _, base, execution, acceptance = _proposal(client)
    attempt = db_session.get(WorkflowStepAttempt, execution["attempt_id"])
    original = deepcopy((attempt.output_json, attempt.execution_receipt_json, attempt.input_snapshot_json))
    request = {key: acceptance[key] for key in (
        "run_id", "attempt_id", "expected_output_hash", "expected_resolution_hash",
    )}
    request.update(decision=decision, feedback_key="explicit-decision", note="结构需要调整", reason_tags=["clarity"])
    before = db_session.query(ProjectEvent).count()
    first = client.post(f"{_stage(base)}/feedback", headers=headers, json=request)
    assert first.status_code == 200, first.text
    replay = client.post(f"{_stage(base)}/feedback", headers=headers, json=request)
    assert replay.status_code == 200 and replay.json() == first.json()
    conflict = client.post(f"{_stage(base)}/feedback", headers=headers, json={**request, "note": "不同反馈"})
    assert conflict.status_code == 409, conflict.text
    history = client.get(f"{_stage(base)}/history", headers=headers, params={"run_id": execution["run_id"]})
    assert history.status_code == 200, history.text
    assert history.json()["items"][0]["feedback"][0]["decision"] == decision
    db_session.refresh(attempt)
    assert (attempt.output_json, attempt.execution_receipt_json, attempt.input_snapshot_json) == original
    assert db_session.query(ProjectEvent).count() == before + 1
    assert db_session.query(ContentMasterRevision).count() == 0


@pytest.mark.parametrize("decision", ["accepted", "accepted_with_edits", "skipped_when_allowed"])
def test_feedback_cannot_bypass_domain_adoption_or_required_review(client, db_session, decision):
    headers, _, _, base, _, acceptance = _proposal(client)
    before = db_session.query(ProjectEvent).count()
    request = {key: acceptance[key] for key in (
        "run_id", "attempt_id", "expected_output_hash", "expected_resolution_hash",
    )}
    response = client.post(f"{_stage(base)}/feedback", headers=headers,
                           json={**request, "decision": decision, "feedback_key": "no-shortcut"})
    assert response.status_code == (409 if decision == "skipped_when_allowed" else 422), response.text
    assert db_session.query(ProjectEvent).count() == before
    assert db_session.query(ContentMasterRevision).count() == 0


def test_content_edits_are_evidence_and_need_an_explicit_instruction_before_recipe_save(client, db_session):
    headers, _, unit_id, base, evidence = _accepted(client, edited=True)
    binding = db_session.query(ProjectWorkflowBinding).filter_by(unit_id=unit_id).one()
    original_workflow = binding.workflow_id
    preview, request = _improvement(client, headers, base, evidence)
    assert preview["content_only"] and not preview["has_config_change"]
    assert preview["config_patch"] == {} and preview["patch_source"] == "content_feedback_only"
    blocked = client.post(f"{_stage(base)}/save-adjustment", headers=headers, json=request)
    assert blocked.status_code == 422, blocked.text
    assert db_session.query(Workflow).count() == 1
    preview, request = _improvement(client, headers, base, evidence,
                                    config_patch={"instruction": "标题具体一些，正文保持事实边界"})
    assert preview["patch_source"] == "user_authored" and not preview["executed_patch"]
    saved = client.post(f"{_stage(base)}/save-adjustment", headers=headers, json=request)
    assert saved.status_code == 200, saved.text
    assert saved.json()["workflow_id"] != original_workflow
    assert db_session.get(Workflow, original_workflow).definition_json["nodes"][0]["config"]["instruction"] != \
        preview["config_patch"]["instruction"]


def test_executed_override_save_is_exact_cas_and_does_not_rebind_old_runs(client, db_session):
    patch = {"instruction": "明确阐述当前范围，不推断未知事实"}
    headers, _, unit_id, base, evidence = _accepted(client, override=patch)
    unit = db_session.get(ContentUnit, unit_id)
    original_workflow = unit.pinned_workflow_id
    attempt = db_session.get(WorkflowStepAttempt, evidence["attempt_id"])
    original_snapshot = deepcopy(attempt.input_snapshot_json)
    preview, request = _improvement(client, headers, base, evidence)
    assert preview["config_patch"] == patch and preview["executed_patch"]
    wrong_patch = client.post(f"{_stage(base)}/improvement-preview", headers=headers,
                              json={**evidence, "config_patch": {"instruction": "未执行过的修改"}})
    assert wrong_patch.status_code == 422, wrong_patch.text
    stale = client.post(f"{_stage(base)}/save-adjustment", headers=headers,
                        json={**request, "expected_revision": 0})
    assert stale.status_code == 409 and db_session.query(Workflow).count() == 1
    saved = client.post(f"{_stage(base)}/save-adjustment", headers=headers, json=request)
    assert saved.status_code == 200, saved.text
    replay = client.post(f"{_stage(base)}/save-adjustment", headers=headers, json=request)
    assert replay.status_code == 200 and replay.json() == saved.json()
    conflict = client.post(f"{_stage(base)}/save-adjustment", headers=headers,
                           json={**request, "name": "另一份调整"})
    assert conflict.status_code == 409 and db_session.query(Workflow).count() == 2
    assert db_session.get(WorkflowRun, evidence["run_id"]).workflow_id == original_workflow
    db_session.refresh(attempt)
    assert attempt.input_snapshot_json == original_snapshot
    started = client.post(f"{base}/runs", headers=headers, json={"params": {}})
    assert started.status_code == 201, started.text
    assert started.json()["workflow_id"] == saved.json()["workflow_id"]


def test_saving_persona_default_changes_only_future_units(client, db_session):
    patch = {"instruction": "只在未来默认流程使用这条指令"}
    headers, project_id, unit_id, base, evidence = _accepted(client, override=patch)
    unit = db_session.get(ContentUnit, unit_id)
    original_workflow = unit.pinned_workflow_id
    preview, request = _improvement(client, headers, base, evidence, destination="persona")
    assert preview["definition_diff"]["replaces_entire_default"]
    saved = client.post(f"{_stage(base)}/save-adjustment", headers=headers, json=request)
    assert saved.status_code == 200, saved.text
    default = db_session.query(PersonaWorkflowDefault).filter_by(persona_id=unit.persona_id, modality="text").one()
    assert default.workflow_id == saved.json()["workflow_id"]
    db_session.refresh(unit)
    assert unit.pinned_workflow_id == original_workflow
    assert db_session.get(WorkflowRun, evidence["run_id"]).workflow_id == original_workflow
    new = client.post(f"/api/v1/content-projects/{project_id}/units", headers=headers,
                      json={"title": "未来文章", "persona_id": unit.persona_id, "modality": "text"})
    assert new.status_code == 201, new.text
    assert db_session.get(ContentUnit, new.json()["id"]).pinned_workflow_id == default.workflow_id


def test_stale_persona_default_preview_cannot_replace_a_newer_default(client, db_session):
    headers, _, _, base, evidence = _accepted(client, override={"instruction": "经明确采用的调整"})
    _, request = _improvement(client, headers, base, evidence, destination="persona")
    saved = client.post(f"{_stage(base)}/save-adjustment", headers=headers, json=request)
    assert saved.status_code == 200, saved.text
    before = db_session.query(ProjectEvent).count()
    stale = client.post(f"{_stage(base)}/save-adjustment", headers=headers,
                        json={**request, "idempotency_key": "another-stale-writer"})
    assert stale.status_code == 409 and stale.json()["detail"]["code"] == "recipe_improvement_preview_changed"
    default = db_session.query(PersonaWorkflowDefault).one()
    assert default.workflow_id == saved.json()["workflow_id"] and default.revision == 1
    assert db_session.query(Workflow).count() == 2 and db_session.query(ProjectEvent).count() == before


def _recipe_candidate(client, db_session):
    headers, project_id, unit_id, base, evidence = _accepted(
        client, override={"instruction": "先展示明确范围，再解释判断依据"},
    )
    preview, request = _improvement(client, headers, base, evidence, destination="capability")
    response = client.post(f"{_stage(base)}/save-adjustment", headers=headers, json=request)
    assert response.status_code == 200, response.text
    artifact = response.json()["artifact"]
    user = db_session.query(User).filter_by(email="recipe@studio.test").one()
    return headers, project_id, unit_id, base, evidence, user, artifact, preview


def _saved_recipe(client, db_session):
    from app.services import capability_memory

    values = _recipe_candidate(client, db_session)
    headers, project_id, unit_id, base, evidence, user, artifact, source = values
    artifact = capability_memory.lifecycle(db_session, user, artifact["id"],
                                           {"expected_revision": 1, "status": "saved"})
    return headers, project_id, unit_id, base, evidence, user, artifact, source


def _method_request(artifact):
    return {"artifact_id": artifact["id"], "revision_id": artifact["current_revision"]["id"]}


def test_method_capture_stays_candidate_until_explicit_save_and_exact_apply(client, db_session):
    from app.services import capability_memory

    headers, _, unit_id, base, evidence, user, artifact, source = _recipe_candidate(client, db_session)
    unit = db_session.get(ContentUnit, unit_id)
    original_workflow = unit.pinned_workflow_id
    assert artifact["status"] == "candidate" and db_session.query(Workflow).count() == 1
    assert db_session.query(CapabilityUse).count() == 0
    frozen = artifact["current_revision"]["content"]
    assert frozen["base_workflow_checksum"] == source["workflow_checksum"]
    assert frozen["feedback_evidence"] == [{"event_id": evidence["feedback_event_id"],
                                           "event_hash": source["feedback_hash"]}]
    assert frozen["attempt_evidence"] == [source["attempt_evidence"]]
    blocked = client.post(f"{_stage(base)}/apply-method-preview", headers=headers, json=_method_request(artifact))
    assert blocked.status_code == 409 and blocked.json()["detail"]["code"] == "recipe_method_not_saved"
    artifact = capability_memory.lifecycle(db_session, user, artifact["id"],
                                           {"expected_revision": 1, "status": "saved"})
    selected = _method_request(artifact)
    preview = client.post(f"{_stage(base)}/apply-method-preview", headers=headers, json=selected)
    assert preview.status_code == 200, preview.text
    assert not preview.json()["auto_select"]
    assert db_session.query(Workflow).count() == 1 and unit.pinned_workflow_id == original_workflow
    request = {**selected, "expected_preview_hash": preview.json()["preview_hash"],
               "expected_revision": preview.json()["expected_revision"], "idempotency_key": "explicit-method"}
    stale = client.post(f"{_stage(base)}/apply-method", headers=headers,
                        json={**request, "expected_revision": 0})
    assert stale.status_code == 409 and db_session.query(Workflow).count() == 1
    applied = client.post(f"{_stage(base)}/apply-method", headers=headers, json=request)
    assert applied.status_code == 200, applied.text
    replay = client.post(f"{_stage(base)}/apply-method", headers=headers, json=request)
    assert replay.status_code == 200 and replay.json() == applied.json()
    conflict = client.post(f"{_stage(base)}/apply-method", headers=headers,
                           json={**request, "revision_id": artifact["current_revision"]["id"] + 1000})
    assert conflict.status_code == 409
    assert db_session.query(CapabilityUse).count() == 1 and db_session.query(Workflow).count() == 2
    use = db_session.get(CapabilityUse, applied.json()["capability_use_id"])
    assert use.artifact_revision_id == selected["revision_id"]
    assert db_session.get(WorkflowRun, evidence["run_id"]).workflow_id == original_workflow


@pytest.mark.parametrize("mutation,code", [
    ("candidate_revision", "recipe_method_not_saved"),
    ("missing_revision", "recipe_method_not_saved"),
    ("archived", "recipe_method_not_saved"),
    ("foreign_scope", "recipe_method_scope_mismatch"),
    ("contract", "recipe_method_stage_mismatch"),
    ("base_checksum", "recipe_method_base_mismatch"),
])
def test_apply_method_checks_exact_revision_scope_contract_base_and_live_status(
    client, db_session, mutation, code,
):
    from app.services import capability_memory

    headers, _, _, base, _, user, artifact, _ = _saved_recipe(client, db_session)
    request = _method_request(artifact)
    if mutation == "candidate_revision":
        request["revision_id"] = capability_memory.revisions(db_session, user, artifact["id"])["items"][-1]["id"]
    elif mutation == "missing_revision":
        request["revision_id"] += 1000
    elif mutation == "archived":
        capability_memory.lifecycle(db_session, user, artifact["id"],
                                    {"expected_revision": 2, "status": "archived"})
    elif mutation == "foreign_scope":
        other_project = client.post("/api/v1/content-projects", headers=headers,
                                    json={"title": "方法不属于当前项目"}).json()["id"]
        artifact = capability_memory.lifecycle(db_session, user, artifact["id"], {
            "expected_revision": 2, "status": "saved", "scope_type": "project", "scope": {"id": other_project},
            "confirm_scope_broadening": True,
        })
        request = _method_request(artifact)
    else:
        content = deepcopy(artifact["current_revision"]["content"])
        if mutation == "contract":
            content.update(plugin="stage.creative.method", plugin_version="1", stage_schema="stage.creative.method.v1")
        else:
            content["base_workflow_checksum"] = "a" * 64
        artifact = capability_memory.update_revision(db_session, user, artifact["id"],
            {"expected_revision": 2, "content": content, "args_schema": {}})
        request = _method_request(artifact)
    before = db_session.query(ProjectEvent).count()
    response = client.post(f"{_stage(base)}/apply-method-preview", headers=headers, json=request)
    assert response.status_code == 409, response.text
    assert response.json()["detail"]["code"] == code
    assert db_session.query(Workflow).count() == 1 and db_session.query(CapabilityUse).count() == 0
    assert db_session.query(ProjectEvent).count() == before


def test_project_only_method_cannot_be_saved_to_persona_default_and_archive_invalidates_preview(client, db_session):
    from app.services import capability_memory

    headers, project_id, _, base, evidence = _accepted(client)
    user = db_session.query(User).filter_by(email="recipe@studio.test").one()
    method = capability_memory.create_artifact(db_session, user, {
        "kind": "prompt_skill", "name": "项目专用写作指令", "content": {"instruction": "仅用于当前项目"},
        "args_schema": {}, "scope_type": "project", "scope": {"id": project_id},
    })
    method = capability_memory.lifecycle(db_session, user, method["id"], {"expected_revision": 1, "status": "saved"})
    patch = {"method": {"source_kind": "capability_memory", "artifact_id": method["id"],
                        "revision_id": method["current_revision"]["id"], "arguments_json": "{}"}}
    blocked = client.post(f"{_stage(base)}/improvement-preview", headers=headers,
                          json={**evidence, "destination": "persona", "config_patch": patch})
    assert blocked.status_code == 422, blocked.text
    assert blocked.json()["detail"]["code"] == "recipe_method_default_scope_mismatch"
    _, request = _improvement(client, headers, base, evidence, config_patch=patch)
    capability_memory.lifecycle(db_session, user, method["id"], {"expected_revision": 2, "status": "archived"})
    response = client.post(f"{_stage(base)}/save-adjustment", headers=headers, json=request)
    assert response.status_code == 409 and response.json()["detail"]["code"] == "recipe_method_unavailable"
    assert db_session.query(Workflow).count() == 1 and db_session.query(PersonaWorkflowDefault).count() == 0


def test_rejected_feedback_cannot_be_promoted_as_accepted_learning(client, db_session):
    headers, _, _, base, _, acceptance = _proposal(client)
    request = {key: acceptance[key] for key in (
        "run_id", "attempt_id", "expected_output_hash", "expected_resolution_hash",
    )}
    feedback = client.post(f"{_stage(base)}/feedback", headers=headers,
                           json={**request, "decision": "rejected", "feedback_key": "not-success"})
    assert feedback.status_code == 200, feedback.text
    response = client.post(f"{_stage(base)}/improvement-preview", headers=headers,
                           json={**request, "feedback_event_id": feedback.json()["feedback_event_id"]})
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "recipe_accepted_feedback_required"
    assert db_session.query(CapabilityArtifact).count() == 0 and db_session.query(Workflow).count() == 1


def test_tuning_claim_commits_exact_feedback_before_dispatch_and_suggestion_never_saves_itself(
    client, db_session, monkeypatch,
):
    from app.services import stage_tuning
    from app.services.generation.providers import input_hash

    headers, _, unit_id, base, evidence = _accepted(client)
    original_generate = stage_tuning.MockProvider.generate_json
    captured, committed = [], []

    def after_commit(_session):
        committed.append(True)

    async def generate(provider, request):
        captured.append(request)
        row = db_session.query(LLMRun).filter_by(prompt_version=stage_tuning.PROMPT_VERSION).one()
        assert committed and row.status == "pending"
        projection = row.parsed_output_json["projection"]
        feedback = db_session.get(ProjectEvent, evidence["feedback_event_id"])
        assert projection["feedback"][0]["event_hash"] == digest(feedback.payload_json)
        assert projection["feedback"][0]["accepted_hash"] == feedback.payload_json["accepted_hash"]
        assert row.parsed_output_json["claim"]["projection_hash"] == digest(projection)
        assert row.input_hash == input_hash(request)
        return await original_generate(provider, request)

    event.listen(db_session, "after_commit", after_commit)
    monkeypatch.setattr(stage_tuning.MockProvider, "generate_json", generate)
    request = _tuning_request(evidence)
    try:
        first = client.post(f"{_stage(base)}/tuning-suggestion", headers=headers, json=request)
    finally:
        event.remove(db_session, "after_commit", after_commit)
    assert first.status_code == 200, first.text
    suggestion = first.json()
    assert suggestion["feedback_event_ids"] == [evidence["feedback_event_id"]]
    assert suggestion["suggestion_hash"] == digest({key: value for key, value in suggestion.items() if key != "suggestion_hash"})
    original_workflow = db_session.get(ContentUnit, unit_id).pinned_workflow_id
    replay = client.post(f"{_stage(base)}/tuning-suggestion", headers=headers, json=request)
    assert replay.status_code == 200 and replay.json() == suggestion and len(captured) == 1
    assert db_session.query(Workflow).count() == 1 and db_session.query(CapabilityArtifact).count() == 0
    assert db_session.get(ContentUnit, unit_id).pinned_workflow_id == original_workflow
    conflict = client.post(f"{_stage(base)}/tuning-suggestion", headers=headers,
                           json={**request, "model_profile_id": "different-model"})
    assert conflict.status_code == 409 and len(captured) == 1
    preview, save = _improvement(client, headers, base, evidence,
        tuning_suggestion_id=suggestion["llm_run_id"], expected_suggestion_hash=suggestion["suggestion_hash"])
    assert preview["patch_source"] == "model_suggestion" and not preview["executed_patch"]
    saved = client.post(f"{_stage(base)}/save-adjustment", headers=headers, json=save)
    assert saved.status_code == 200, saved.text
    assert db_session.get(Workflow, saved.json()["workflow_id"]).definition_json["nodes"][0]["config"]["candidate_count"] == 3


@pytest.mark.parametrize("data", [
    {"config_patch": {"rights": {"public": True}}, "explanation": "改变权利"},
    {"config_patch": {"instruction": "改写"}, "explanation": "越界字段", "workflow": {}},
    {"config_patch": {}, "explanation": "空差异"},
    {"config_patch": {"candidate_count": 6}, "explanation": "超出合同"},
])
def test_tuning_rejects_unbounded_provider_output_and_preserves_failed_claim_without_retry(
    client, db_session, monkeypatch, data,
):
    from app.services import stage_tuning
    from app.services.generation.providers import GenerateResult

    headers, _, _, base, evidence = _accepted(client)
    calls = []

    async def invalid_output(_provider, request):
        calls.append(request)
        return GenerateResult(data=data, raw_output="third-party raw output must not persist", usage={})

    monkeypatch.setattr(stage_tuning.MockProvider, "generate_json", invalid_output)
    request = _tuning_request(evidence)
    first = client.post(f"{_stage(base)}/tuning-suggestion", headers=headers, json=request)
    assert first.status_code == 409 and first.json()["detail"]["code"] == "recipe_tuning_output_invalid"
    row = db_session.query(LLMRun).filter_by(prompt_version=stage_tuning.PROMPT_VERSION).one()
    assert row.status == "failed" and row.raw_output is None and "suggestion" not in row.parsed_output_json
    replay = client.post(f"{_stage(base)}/tuning-suggestion", headers=headers, json=request)
    assert replay.status_code == 409 and replay.json()["detail"]["code"] == "recipe_tuning_original_unresolved"
    assert len(calls) == 1 and db_session.query(Workflow).count() == 1


def test_tuning_response_loss_remains_unknown_and_identical_request_never_retries(client, db_session, monkeypatch):
    from app.services import stage_tuning

    headers, _, _, base, evidence = _accepted(client)
    calls = []

    async def response_lost(_provider, request):
        calls.append(request)
        raise TimeoutError("secret upstream diagnostic")

    monkeypatch.setattr(stage_tuning.MockProvider, "generate_json", response_lost)
    request = _tuning_request(evidence)
    first = client.post(f"{_stage(base)}/tuning-suggestion", headers=headers, json=request)
    replay = client.post(f"{_stage(base)}/tuning-suggestion", headers=headers, json=request)
    assert first.status_code == replay.status_code == 409
    assert first.json()["detail"]["code"] == replay.json()["detail"]["code"] == "recipe_tuning_original_unresolved"
    row = db_session.query(LLMRun).filter_by(prompt_version=stage_tuning.PROMPT_VERSION).one()
    assert row.status == "unknown" and row.raw_output is None and row.error == "recipe_tuning_original_unresolved"
    assert "secret upstream diagnostic" not in first.text and len(calls) == 1


def test_tuning_model_drift_after_persistent_claim_stops_before_provider(client, db_session, monkeypatch):
    from app import runtime_config
    from app.services import stage_tuning

    headers, _, _, base, evidence = _accepted(client)
    monkeypatch.setattr(runtime_config, "_OVERRIDES", {})
    monkeypatch.setattr(stage_tuning.MockProvider, "generate_json",
                        lambda *_: pytest.fail("drifted claim dispatched provider"))
    changed = []

    def change_model_after_commit(_session):
        if not changed:
            changed.append(True)
            runtime_config.set_runtime(runtime_config.KEY_MODELS, {
                "profiles": {"changed": {"provider": "mock", "model": "changed-after-claim"}}, "default_profile": "changed"})

    event.listen(db_session, "after_commit", change_model_after_commit)
    request = _tuning_request(evidence)
    try:
        response = client.post(f"{_stage(base)}/tuning-suggestion", headers=headers, json=request)
    finally:
        event.remove(db_session, "after_commit", change_model_after_commit)
    assert response.status_code == 409 and response.json()["detail"]["code"] == "recipe_tuning_resolution_changed"
    row = db_session.query(LLMRun).filter_by(prompt_version=stage_tuning.PROMPT_VERSION).one()
    assert row.status == "failed" and row.error == "failed_before_dispatch"
    assert client.post(f"{_stage(base)}/tuning-suggestion", headers=headers, json=request).status_code == 409


@pytest.mark.parametrize("mutation", ["suggestion_hash", "input_hash", "projection_hash", "expected_hash", "feedback", "owner"])
def test_tuning_promotion_revalidates_receipt_feedback_and_owner_without_workflow_write(
    client, db_session, mutation,
):
    headers, _, _, base, evidence = _accepted(client)
    response = client.post(f"{_stage(base)}/tuning-suggestion", headers=headers, json=_tuning_request(evidence))
    assert response.status_code == 200, response.text
    suggestion = response.json()
    request = {**evidence, "tuning_suggestion_id": suggestion["llm_run_id"],
               "expected_suggestion_hash": suggestion["suggestion_hash"]}
    row = db_session.get(LLMRun, suggestion["llm_run_id"])
    data = deepcopy(row.parsed_output_json)
    if mutation == "expected_hash":
        request["expected_suggestion_hash"] = "a" * 64
    elif mutation == "input_hash":
        row.input_hash = "b" * 64
    elif mutation == "suggestion_hash":
        data["suggestion"]["config_patch"] = {"candidate_count": 4}
    elif mutation == "projection_hash":
        data["projection"]["feedback"][0]["event_hash"] = "c" * 64
    elif mutation == "owner":
        data["claim"]["owner_id"] += 1
    else:
        data["suggestion"]["feedback_event_ids"] = [evidence["feedback_event_id"] + 1000]
        data["suggestion"]["suggestion_hash"] = digest({key: value for key, value in data["suggestion"].items()
                                                     if key != "suggestion_hash"})
        request["expected_suggestion_hash"] = data["suggestion"]["suggestion_hash"]
    row.parsed_output_json = data
    db_session.commit()
    response = client.post(f"{_stage(base)}/improvement-preview", headers=headers, json=request)
    assert response.status_code == 409, response.text
    assert response.json()["detail"]["code"] == "recipe_tuning_receipt_invalid"
    assert db_session.query(Workflow).count() == 1


@pytest.mark.parametrize("requires_acceptance", [False, True])
def test_skip_policy_only_skips_a_stage_without_required_human_acceptance(
    client, db_session, monkeypatch, requires_acceptance,
):
    from test_creation_recipe_stages import _contract, _setup, _StageExecutor

    from app.services.content_harness.registry import registry
    from app.services.stage_invocations import finalize_invocation, prepare_invocation

    monkeypatch.setattr(registry, "_items", dict(registry._items))
    monkeypatch.setattr(registry, "_descriptors", dict(registry._descriptors))
    contract = _contract()
    contract["requires_human_acceptance"] = requires_acceptance
    registry.register("node", "test.skip", "1", _StageExecutor(), stage_contract=contract)
    headers, _, _, base = _setup(client)
    definition = {"nodes": [{"id": "draft", "kind": "AI", "plugin": "test.skip", "plugin_version": "1",
        "stage_schema": "test.text.stage.v1", "config": {"instruction": "局部可选阶段"}, "failure_policy": "skip"}],
        "edges": [], "visual_order": ["draft"]}
    saved = client.post(f"{base}/workflow-override", headers=headers,
                        json={"expected_revision": 0, "definition": definition})
    assert saved.status_code == 201, saved.text
    started = client.post(f"{base}/runs", headers=headers, json={"params": {}})
    assert started.status_code == 201, started.text
    run = db_session.get(WorkflowRun, started.json()["id"])
    step = db_session.query(WorkflowStep).filter_by(run_id=run.id, node_id="draft").one()
    user = db_session.query(User).filter_by(email="recipe@studio.test").one()
    preview = client.post(f"{_stage(base)}/preview", headers=headers, json={"run_id": run.id})
    assert preview.status_code == 200, preview.text
    resolved = preview.json()
    attempt = prepare_invocation(db_session, run=run, step=step, user=user, resolved=resolved,
                                 expected_resolution_hash=resolved["resolution_hash"], invocation_key="optional-stage")
    attempt = finalize_invocation(db_session, attempt_id=attempt.id, status="failed",
                                   dispatch_certainty="not_dispatched")
    original = deepcopy((attempt.output_json, attempt.execution_receipt_json, attempt.input_snapshot_json))
    request = {"run_id": run.id, "attempt_id": attempt.id, "expected_output_hash": attempt.output_hash,
               "expected_resolution_hash": attempt.input_hash, "decision": "skipped_when_allowed",
               "feedback_key": "skip-explicitly"}
    before = db_session.query(ProjectEvent).count()
    response = client.post(f"{_stage(base)}/feedback", headers=headers, json=request)
    if requires_acceptance:
        assert response.status_code == 409, response.text
        assert db_session.query(ProjectEvent).count() == before
        assert db_session.get(WorkflowStep, step.id).status == "failed"
    else:
        assert response.status_code == 200, response.text
        replay = client.post(f"{_stage(base)}/feedback", headers=headers, json=request)
        assert replay.status_code == 200 and replay.json() == response.json()
        assert db_session.query(ProjectEvent).count() == before + 1
        assert db_session.get(WorkflowStep, step.id).status == "skipped"
        assert db_session.get(WorkflowRun, run.id).status == "succeeded"
    db_session.refresh(attempt)
    assert (attempt.output_json, attempt.execution_receipt_json, attempt.input_snapshot_json) == original


@pytest.mark.parametrize("mutation", ["project", "unit", "node", "event_type", "missing"])
def test_tuning_rejects_feedback_from_another_context_before_claim_and_provider(
    client, db_session, monkeypatch, mutation,
):
    from app.services import stage_tuning

    headers, project_id, _, base, evidence = _accepted(client)
    original = db_session.get(ProjectEvent, evidence["feedback_event_id"])
    request = _tuning_request(evidence)
    if mutation == "missing":
        request["feedback_event_ids"] = [original.id + 1000]
    else:
        payload = deepcopy(original.payload_json)
        if mutation == "unit":
            payload["unit_id"] += 1000
        elif mutation == "node":
            payload["node_id"] = "different-stage"
        if mutation == "project":
            project_id = client.post("/api/v1/content-projects", headers=headers,
                                     json={"title": "其他反馈项目"}).json()["id"]
        unrelated = ProjectEvent(project_id=project_id,
            event_type="unrelated.event" if mutation == "event_type" else original.event_type,
            entity_type=original.entity_type, entity_id=original.entity_id, payload_json=payload, actor=original.actor)
        db_session.add(unrelated)
        db_session.commit()
        request["feedback_event_ids"] = [unrelated.id]
    monkeypatch.setattr(stage_tuning.MockProvider, "generate_json",
                        lambda *_: pytest.fail("foreign feedback dispatched provider"))
    response = client.post(f"{_stage(base)}/tuning-suggestion", headers=headers, json=request)
    assert response.status_code == 404 and response.json()["detail"]["code"] == "recipe_tuning_feedback_not_found"
    assert db_session.query(LLMRun).filter_by(prompt_version=stage_tuning.PROMPT_VERSION).count() == 0


@pytest.mark.parametrize("status", ["running", "unknown"])
def test_unresolved_attempt_cannot_request_rerun_through_feedback(client, db_session, status):
    from app.services.stage_invocations import finalize_invocation, prepare_invocation

    headers, _, _, base, resolved, request = _running_stage(client)
    run = db_session.get(WorkflowRun, request["run_id"])
    step = db_session.query(WorkflowStep).filter_by(run_id=run.id, node_id="draft").one()
    user = db_session.query(User).filter_by(email="recipe@studio.test").one()
    attempt = prepare_invocation(db_session, run=run, step=step, user=user, resolved=resolved,
        expected_resolution_hash=resolved["resolution_hash"], invocation_key="awaiting-provider")
    if status == "unknown":
        attempt = finalize_invocation(db_session, attempt_id=attempt.id, status="unknown",
                                       dispatch_certainty="possibly_dispatched")
    request = {"run_id": run.id, "attempt_id": attempt.id, "expected_output_hash": attempt.output_hash or "pending",
               "expected_resolution_hash": attempt.input_hash, "decision": "rerun_requested",
               "feedback_key": "never-resend-unresolved"}
    before = db_session.query(ProjectEvent).count()
    response = client.post(f"{_stage(base)}/feedback", headers=headers, json=request)
    assert response.status_code == 409, response.text
    expected_code = "stage_output_changed" if status == "running" else "stage_reconciliation_required"
    assert response.json()["detail"]["code"] == expected_code
    assert db_session.query(ProjectEvent).count() == before
    db_session.refresh(attempt)
    assert attempt.status == status
