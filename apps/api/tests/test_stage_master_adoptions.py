"""Exact, transactional Text proposal adoption on a disposable Mock database."""

from copy import deepcopy

import pytest
from test_stage_master_proposals import _running_stage

from app.models import (
    ContentAsset,
    ContentMasterRevision,
    ContentUnit,
    ProjectEvent,
    ProjectWorkflowOutput,
    User,
    WorkflowStepAttempt,
)
from app.services.stage_contracts import digest


def _proposal(client):
    headers, project_id, unit_id, base, resolved, request = _running_stage(client)
    response = client.post(f"{base}/creation-recipe/stages/draft/run", headers=headers, json=request)
    assert response.status_code == 200, response.text
    execution = response.json()
    candidate = execution["output"]["candidates"][0]
    acceptance = {
        "run_id": execution["run_id"], "attempt_id": execution["attempt_id"],
        "expected_output_hash": execution["receipt"]["output_hash"],
        "expected_resolution_hash": resolved["resolution_hash"],
        "expected_context_hash": digest(resolved["context"]),
        "candidate_id": candidate["candidate_id"],
        "candidate_hash": digest({key: value for key, value in candidate.items() if key != "candidate_hash"}),
        "expected_revision": 0, "adoption_key": "accept-first-proposal",
        "payload": candidate["payload"], "asset_refs": candidate["asset_refs"],
        "evidence_refs": candidate["evidence_refs"], "decision": "accepted", "note": "采用第一版",
    }
    return headers, project_id, unit_id, base, execution, acceptance


def _accept(client, base, headers, acceptance):
    return client.post(f"{base}/creation-recipe/stages/draft/accept-master", headers=headers, json=acceptance)


def test_acceptance_commits_master_output_feedback_but_preserves_original_attempt(client, db_session):
    headers, _, _, base, execution, acceptance = _proposal(client)
    attempt = db_session.get(WorkflowStepAttempt, execution["attempt_id"])
    original = deepcopy((attempt.output_json, attempt.output_hash, attempt.input_snapshot_json, attempt.execution_receipt_json))
    response = _accept(client, base, headers, acceptance)
    assert response.status_code == 200, response.text
    body = response.json()
    master = db_session.get(ContentMasterRevision, body["master"]["id"])
    output = db_session.get(ProjectWorkflowOutput, body["project_output_id"])
    feedback = db_session.get(ProjectEvent, body["feedback_event_id"])
    assert master.payload_schema == "text.master.v2" and master.source_kind == "workflow_stage"
    assert master.origin_workflow_run_id == execution["run_id"]
    assert master.origin_project_output_id == output.id
    assert output.attempt_id == attempt.id and output.entity_id == master.id
    assert feedback.event_type == "creation_recipe.stage_feedback"
    assert feedback.payload_json["schema"] == "creation_recipe.stage_feedback.v1"
    assert feedback.payload_json["accepted_hash"] == master.payload_hash
    assert feedback.payload_json["decision"] == "accepted"
    assert master.edit_summary_json["stage_provenance"]["candidate_hash"] == acceptance["candidate_hash"]
    assert master.payload_hash == digest(acceptance["payload"])
    db_session.refresh(attempt)
    assert (attempt.output_json, attempt.output_hash, attempt.input_snapshot_json, attempt.execution_receipt_json) == original
    assert db_session.query(ContentAsset).count() == 0


def test_accept_with_edits_records_two_hashes_and_exact_committed_replay(client, db_session):
    headers, _, unit_id, base, execution, acceptance = _proposal(client)
    original_payload_hash = digest(acceptance["payload"])
    acceptance["payload"] = {**acceptance["payload"], "title": "人工修订标题"}
    acceptance["decision"] = "accepted_with_edits"
    response = _accept(client, base, headers, acceptance)
    assert response.status_code == 200, response.text
    result = response.json()
    provenance = result["master"]["edit_summary"]["stage_provenance"]
    assert provenance["proposal_payload_hash"] == original_payload_hash
    assert provenance["accepted_payload_hash"] == digest(acceptance["payload"]) != original_payload_hash
    events = db_session.query(ProjectEvent).count()
    db_session.get(ContentUnit, unit_id).channel_id = "x"
    db_session.commit()
    replay = _accept(client, base, headers, acceptance)
    assert replay.status_code == 200, replay.text
    assert replay.json()["master"]["id"] == result["master"]["id"]
    assert replay.json()["project_output_id"] == result["project_output_id"]
    assert replay.json()["feedback_event_id"] == result["feedback_event_id"]
    assert db_session.query(ContentMasterRevision).count() == 1
    assert db_session.query(ProjectEvent).count() == events
    assert db_session.get(WorkflowStepAttempt, execution["attempt_id"]).output_json["candidates"][0]["payload_hash"] == original_payload_hash
    conflicting = {**acceptance, "note": "不同请求复用键"}
    assert _accept(client, base, headers, conflicting).status_code == 409


@pytest.mark.parametrize("field,value", [
    ("expected_output_hash", "a" * 64), ("candidate_hash", "b" * 64),
    ("expected_context_hash", "c" * 64), ("expected_resolution_hash", "d" * 64),
    ("expected_revision", 4), ("candidate_id", "not-a-candidate"),
])
def test_foreign_stale_or_inexact_acceptance_writes_nothing(client, db_session, field, value):
    headers, _, _, base, _, acceptance = _proposal(client)
    events = db_session.query(ProjectEvent).count()
    response = _accept(client, base, headers, {**acceptance, field: value})
    assert response.status_code in {404, 409}, response.text
    assert db_session.query(ContentMasterRevision).count() == 0
    assert db_session.query(ProjectWorkflowOutput).count() == 0
    assert db_session.query(ProjectEvent).count() == events


@pytest.mark.parametrize("boundary", ["_associate_adoption", "_record_feedback"])
def test_association_or_feedback_failure_rolls_back_entire_master_acceptance(client, db_session, monkeypatch, boundary):
    from app.services import stage_master_adoptions
    from app.services.stage_invocations import StageInvocationError

    headers, _, _, base, _, acceptance = _proposal(client)
    events = db_session.query(ProjectEvent).count()

    def reject(*_args, **_kwargs):
        raise StageInvocationError("stage_acceptance_write_rejected", status_code=409)

    monkeypatch.setattr(stage_master_adoptions, boundary, reject)
    response = _accept(client, base, headers, acceptance)
    assert response.status_code == 409, response.text
    assert db_session.query(ContentMasterRevision).count() == 0
    assert db_session.query(ProjectWorkflowOutput).count() == 0
    assert db_session.query(ProjectEvent).count() == events


def test_context_or_current_attempt_drift_blocks_adoption(client, db_session):
    headers, _, unit_id, base, _, acceptance = _proposal(client)
    db_session.get(ContentUnit, unit_id).channel_id = "x"
    db_session.commit()
    assert _accept(client, base, headers, acceptance).status_code == 409
    assert db_session.query(ContentMasterRevision).count() == 0


@pytest.mark.parametrize("mutation", ["output", "receipt", "snapshot"])
def test_tampered_sealed_proposal_or_receipt_cannot_be_accepted(client, db_session, mutation):
    headers, _, _, base, execution, acceptance = _proposal(client)
    attempt = db_session.get(WorkflowStepAttempt, execution["attempt_id"])
    if mutation == "output":
        attempt.output_json = {**attempt.output_json, "forged": True}
    elif mutation == "receipt":
        attempt.execution_receipt_json = {**attempt.execution_receipt_json, "prompt_hash": "f" * 64}
    else:
        attempt.input_snapshot_json = {"resolved_stage": {"forged": True}}
    db_session.commit()
    assert _accept(client, base, headers, acceptance).status_code == 409
    assert db_session.query(ContentMasterRevision).count() == 0


@pytest.mark.parametrize("field", ["model_route_hash", "runtime_identity_hash", "adapter_hash", "override_hash", "request_fingerprint"])
def test_each_receipt_identity_hash_is_verified_at_acceptance(client, db_session, field):
    headers, _, _, base, execution, acceptance = _proposal(client)
    attempt = db_session.get(WorkflowStepAttempt, execution["attempt_id"])
    attempt.execution_receipt_json = {**attempt.execution_receipt_json, field: "e" * 64}
    db_session.commit()
    assert _accept(client, base, headers, acceptance).status_code == 409
    assert db_session.query(ContentMasterRevision).count() == 0


def test_llm_run_must_match_actual_frozen_request_before_acceptance(client, db_session):
    from app.models import LLMRun

    headers, _, _, base, execution, acceptance = _proposal(client)
    llm = db_session.get(LLMRun, execution["output"]["llm_run_id"])
    llm.input_hash = "d" * 64
    db_session.commit()
    assert _accept(client, base, headers, acceptance).status_code == 409
    assert db_session.query(ContentMasterRevision).count() == 0


def test_acceptance_requires_current_authorized_editor_and_cannot_accept_twice(client, db_session):
    headers, _, _, base, _, acceptance = _proposal(client)
    actor = db_session.query(User).filter_by(email="recipe@studio.test").one()
    actor.role = "viewer"
    db_session.commit()
    assert _accept(client, base, headers, acceptance).status_code == 403
    actor.role = "admin"
    db_session.commit()
    assert _accept(client, base, headers, acceptance).status_code == 200
    assert _accept(client, base, headers, {**acceptance, "adoption_key": "another-decision"}).status_code == 409
    assert db_session.query(ContentMasterRevision).count() == 1


def test_standalone_save_cannot_forge_stage_provenance(client, db_session):
    headers, _, _, base, _, acceptance = _proposal(client)
    response = client.post(f"{base}/master-revisions", headers=headers, json={
        "expected_revision": 0, "idempotency_key": "fake-stage", "payload_schema": "text.master.v2",
        "payload": acceptance["payload"], "edit_summary": {"stage_provenance": {"verified": True}},
    })
    assert response.status_code == 422, response.text
    assert db_session.query(ContentMasterRevision).count() == 0


@pytest.mark.parametrize("same_key", [True, False])
def test_competing_adoptions_commit_only_one_master_and_one_feedback(client, db_session, tmp_path, same_key):
    import sqlite3
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from app.services.stage_invocations import StageInvocationError
    from app.services.stage_master_adoptions import accept_master

    _, project_id, unit_id, _, _, acceptance = _proposal(client)
    user_id = db_session.query(User).filter_by(email="recipe@studio.test").one().id
    db_session.commit()
    path = tmp_path / "competing-adoption.db"
    with sqlite3.connect(path) as copied:
        db_session.connection().connection.driver_connection.backup(copied)
    engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False, "timeout": 5})
    barrier = Barrier(2)

    def accept(index):
        with Session(engine) as db:
            actor = db.get(User, user_id)
            request = {**acceptance, "adoption_key": acceptance["adoption_key"] if same_key else f"decision-{index}"}
            barrier.wait(timeout=5)
            try:
                return accept_master(db, project_id, unit_id, "draft", actor, request)["master"]["id"]
            except StageInvocationError as exc:
                assert not same_key
                assert exc.code in {"stage_already_accepted", "stage_run_readonly"}
                return None

    try:
        with ThreadPoolExecutor(max_workers=2) as workers:
            results = list(workers.map(accept, range(2)))
        assert len({result for result in results if result is not None}) == 1
        with Session(engine) as db:
            assert db.query(ContentMasterRevision).count() == 1
            assert db.query(ProjectWorkflowOutput).count() == 1
            assert db.query(ProjectEvent).filter_by(event_type="creation_recipe.stage_feedback").count() == 1
    finally:
        engine.dispose()
