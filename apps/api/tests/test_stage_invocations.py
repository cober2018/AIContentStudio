"""Persistent Stage claim/receipt behavior on an isolated database."""

from copy import deepcopy

import pytest
from test_creation_recipe_stages import _register, _setup


def _stage_context(client, db_session, monkeypatch):
    from app.models import ContentUnit, User, Workflow, WorkflowRun, WorkflowStep
    from app.services.content_harness.registry import registry

    monkeypatch.setattr(registry, "_items", dict(registry._items))
    monkeypatch.setattr(registry, "_descriptors", dict(registry._descriptors))
    _register(registry)
    headers, project_id, unit_id, base = _setup(client)
    definition = {"nodes": [{"id": "draft", "kind": "AI", "plugin": "test.stage", "plugin_version": "2",
                              "stage_schema": "test.text.stage.v1", "config": {"instruction": "写文章"}}],
                  "edges": [], "visual_order": ["draft"]}
    assert client.post(f"{base}/workflow-override", headers=headers,
                       json={"expected_revision": 0, "definition": definition}).status_code == 201
    unit = db_session.get(ContentUnit, unit_id)
    workflow_id = client.get(f"{base}/creation-recipe", headers=headers).json()["workflow_id"]
    workflow = db_session.get(Workflow, workflow_id)
    user = db_session.query(User).filter(User.email == "recipe@studio.test").one()
    run = WorkflowRun(workflow_id=workflow.id, content_unit_id=unit.id, identity_snapshot_id=unit.identity_snapshot_id,
                      workflow_version=workflow.version, definition_checksum=workflow.checksum, status="running")
    db_session.add(run)
    db_session.flush()
    step = WorkflowStep(run_id=run.id, node_id="draft", node_type="AI", plugin_key="test.stage",
                        plugin_version="2", status="pending", params_json={"instruction": "写文章"})
    db_session.add(step)
    db_session.commit()
    return headers, project_id, unit_id, user, run, step


def _resolved(db, user, run, step, override=None):
    from app.models import ContentUnit
    from app.services.creation_recipes import preview_stage

    unit = db.get(ContentUnit, run.content_unit_id)
    return preview_stage(db, unit.project_id, unit.id, step.node_id, user,
                         run_id=run.id, stage_override=override or {})


def test_claim_commits_frozen_receipt_before_external_dispatch(client, db_session, monkeypatch):
    from app.services.stage_invocations import prepare_invocation

    _, _, _, user, run, step = _stage_context(client, db_session, monkeypatch)
    resolved = _resolved(db_session, user, run, step)
    attempt = prepare_invocation(db_session, run=run, step=step, user=user, resolved=resolved,
                                 expected_resolution_hash=resolved["resolution_hash"], invocation_key="draft-run-1")
    assert attempt.status == "running"
    assert attempt.execution_receipt_json["resolution_hash"] == resolved["resolution_hash"]
    assert attempt.input_snapshot_json == {"resolved_stage": resolved}
    assert "api_key" not in str(attempt.execution_receipt_json)
    assert "http" not in str(attempt.execution_receipt_json)


def test_same_invocation_key_reuses_claim_but_different_fingerprint_conflicts(client, db_session, monkeypatch):
    from app.services.stage_invocations import StageInvocationError, prepare_invocation

    _, _, _, user, run, step = _stage_context(client, db_session, monkeypatch)
    first = _resolved(db_session, user, run, step)
    original = prepare_invocation(db_session, run=run, step=step, user=user, resolved=first,
                                  expected_resolution_hash=first["resolution_hash"], invocation_key="same-key")
    replay_attempt = prepare_invocation(db_session, run=run, step=step, user=user, resolved=first,
                                        expected_resolution_hash=first["resolution_hash"], invocation_key="same-key")
    assert replay_attempt.id == original.id and replay_attempt.status == "running"
    changed = _resolved(db_session, user, run, step, override={"candidate_count": 3})
    with pytest.raises(StageInvocationError, match="stage_invocation_conflict"):
        prepare_invocation(db_session, run=run, step=step, user=user, resolved=changed,
                           expected_resolution_hash=changed["resolution_hash"], invocation_key="same-key",
                           stage_override={"candidate_count": 3})


def test_expected_hash_drift_and_unsafe_override_fail_before_claim(client, db_session, monkeypatch):
    from app.services.stage_invocations import StageInvocationError, prepare_invocation

    _, _, _, user, run, step = _stage_context(client, db_session, monkeypatch)
    resolved = _resolved(db_session, user, run, step)
    with pytest.raises(StageInvocationError, match="stage_resolution_changed"):
        prepare_invocation(db_session, run=run, step=step, user=user, resolved=resolved,
                           expected_resolution_hash="f" * 64, invocation_key="drift")
    with pytest.raises(StageInvocationError, match="stage_override_not_supported"):
        prepare_invocation(db_session, run=run, step=step, user=user, resolved=resolved,
                           expected_resolution_hash=resolved["resolution_hash"], invocation_key="unsafe",
                           stage_override={"approval": True})


def test_finalize_preserves_frozen_input_and_is_idempotent(client, db_session, monkeypatch):
    from app.services.stage_invocations import finalize_invocation, prepare_invocation

    _, _, _, user, run, step = _stage_context(client, db_session, monkeypatch)
    resolved = _resolved(db_session, user, run, step)
    attempt = prepare_invocation(db_session, run=run, step=step, user=user, resolved=resolved,
                                 expected_resolution_hash=resolved["resolution_hash"], invocation_key="finalize")
    before = deepcopy(attempt.input_snapshot_json)
    done = finalize_invocation(db_session, attempt_id=attempt.id, status="succeeded",
                               dispatch_certainty="confirmed_dispatched", output={"candidates": [{"id": "a"}]})
    replay = finalize_invocation(db_session, attempt_id=attempt.id, status="failed",
                                 dispatch_certainty="possibly_dispatched", output={"tampered": True})
    assert done.status == replay.status == "succeeded"
    assert replay.input_snapshot_json == before
    assert replay.output_json == {"candidates": [{"id": "a"}]}


def test_possible_dispatch_blocks_all_new_invocations_until_reconciliation(client, db_session, monkeypatch):
    from app.services.stage_invocations import StageInvocationError, finalize_invocation, prepare_invocation

    _, _, _, user, run, step = _stage_context(client, db_session, monkeypatch)
    resolved = _resolved(db_session, user, run, step)
    first = prepare_invocation(db_session, run=run, step=step, user=user, resolved=resolved,
                               expected_resolution_hash=resolved["resolution_hash"], invocation_key="unknown-1")
    finalize_invocation(db_session, attempt_id=first.id, status="unknown", dispatch_certainty="possibly_dispatched")
    with pytest.raises(StageInvocationError, match="reconciliation"):
        prepare_invocation(db_session, run=run, step=step, user=user, resolved=resolved,
                           expected_resolution_hash=resolved["resolution_hash"], invocation_key="auto-2", automatic=True)
    with pytest.raises(StageInvocationError, match="reconciliation"):
        prepare_invocation(db_session, run=run, step=step, user=user, resolved=resolved,
                           expected_resolution_hash=resolved["resolution_hash"], invocation_key="explicit-2")


def test_running_claim_blocks_different_key_and_override_must_match_resolution(client, db_session, monkeypatch):
    from app.services.stage_invocations import StageInvocationError, prepare_invocation

    _, _, _, user, run, step = _stage_context(client, db_session, monkeypatch)
    resolved = _resolved(db_session, user, run, step)
    prepare_invocation(db_session, run=run, step=step, user=user, resolved=resolved,
                       expected_resolution_hash=resolved["resolution_hash"], invocation_key="first")
    with pytest.raises(StageInvocationError, match="in_progress"):
        prepare_invocation(db_session, run=run, step=step, user=user, resolved=resolved,
                           expected_resolution_hash=resolved["resolution_hash"], invocation_key="second")
    with pytest.raises(StageInvocationError, match="stage_resolution_invalid"):
        prepare_invocation(db_session, run=run, step=step, user=user, resolved=resolved,
                           expected_resolution_hash=resolved["resolution_hash"], invocation_key="wrong-config",
                           stage_override={"candidate_count": 3})


def test_reconcile_endpoint_seals_abandoned_claim_as_unknown(client, db_session, monkeypatch):
    from app.services.stage_invocations import prepare_invocation

    headers, project_id, unit_id, user, run, step = _stage_context(client, db_session, monkeypatch)
    resolved = _resolved(db_session, user, run, step)
    attempt = prepare_invocation(db_session, run=run, step=step, user=user, resolved=resolved,
                                 expected_resolution_hash=resolved["resolution_hash"], invocation_key="abandoned")
    result = client.post(
        f"/api/v1/content-projects/{project_id}/units/{unit_id}/creation-recipe/stages/{step.node_id}/reconcile",
        headers=headers, json={"run_id": run.id, "attempt_id": attempt.id},
    )
    assert result.status_code == 200, result.text
    assert result.json()["status"] == "unknown"
    assert db_session.get(type(attempt), attempt.id).execution_receipt_json["dispatch_certainty"] == "possibly_dispatched"


@pytest.mark.parametrize("mismatched_field", ["step_id", "run_id", "node_id"])
def test_reconcile_rejects_attempt_outside_exact_stage(client, db_session, monkeypatch, mismatched_field):
    from app.models import WorkflowStepAttempt

    headers, project_id, unit_id, _, run, step = _stage_context(client, db_session, monkeypatch)
    fields = {"step_id": step.id, "run_id": run.id, "node_id": step.node_id}
    fields[mismatched_field] = "foreign-node" if mismatched_field == "node_id" else fields[mismatched_field] + 100
    attempt = WorkflowStepAttempt(**fields, plugin_key=step.plugin_key, plugin_version=step.plugin_version,
                                  attempt_no=1, status="succeeded", output_json={"private": "foreign-result"})
    db_session.add(attempt)
    db_session.commit()
    response = client.post(
        f"/api/v1/content-projects/{project_id}/units/{unit_id}/creation-recipe/stages/{step.node_id}/reconcile",
        headers=headers, json={"run_id": run.id, "attempt_id": attempt.id},
    )
    assert response.status_code == 404
    assert "foreign-result" not in response.text
    assert attempt.status == "succeeded"


def test_finalization_never_exposes_provider_error_text(client, db_session, monkeypatch):
    from app.services.stage_invocations import finalize_invocation, prepare_invocation

    _, _, _, user, run, step = _stage_context(client, db_session, monkeypatch)
    resolved = _resolved(db_session, user, run, step)
    attempt = prepare_invocation(db_session, run=run, step=step, user=user, resolved=resolved,
                                 expected_resolution_hash=resolved["resolution_hash"], invocation_key="safe-error")
    done = finalize_invocation(db_session, attempt_id=attempt.id, status="failed",
                               dispatch_certainty="confirmed_dispatched", error="api_key=private-value https://private")
    assert done.error == "stage_execution_failed"


def test_receipt_probe_does_not_rollback_pending_business_rows(db_session):
    from app.models import User
    from app.services.stage_invocations import receipt_schema_available

    user = User(email="pending@studio.test", name="Pending", role="editor")
    db_session.add(user)
    db_session.flush()
    user_id = user.id
    assert receipt_schema_available(db_session)
    db_session.commit()
    db_session.expire_all()
    assert db_session.get(User, user_id) is not None


@pytest.mark.parametrize("different_key", [False, True])
def test_competing_disk_sqlite_claims_create_only_one_attempt(client, db_session, monkeypatch, tmp_path, different_key):
    import sqlite3
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session

    from app.models import User, WorkflowRun, WorkflowStep, WorkflowStepAttempt
    from app.services.stage_invocations import StageInvocationError, _claim_invocation

    _, _, _, user, run, step = _stage_context(client, db_session, monkeypatch)
    resolved = _resolved(db_session, user, run, step)
    db_session.commit()
    path = tmp_path / "competing.db"
    with sqlite3.connect(path) as target:
        db_session.connection().connection.driver_connection.backup(target)
    engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False, "timeout": 2})
    barrier = Barrier(2)
    run_id, step_id, user_id = run.id, step.id, user.id

    def claim(index):
        with Session(engine) as db:
            actor, current_run, current_step = db.get(User, user_id), db.get(WorkflowRun, run_id), db.get(WorkflowStep, step_id)
            barrier.wait(timeout=5)
            try:
                attempt, claimed = _claim_invocation(db, run=current_run, step=current_step, user=actor,
                    resolved=resolved, expected_resolution_hash=resolved["resolution_hash"],
                    invocation_key=f"claim-{index}" if different_key else "same-key")
                return claimed, attempt.id
            except StageInvocationError as exc:
                return False, exc.code

    try:
        with ThreadPoolExecutor(max_workers=2) as workers:
            results = list(workers.map(claim, range(2)))
        assert sum(claimed for claimed, _ in results) == 1
        with Session(engine) as db:
            attempts = db.scalars(select(WorkflowStepAttempt)).all()
            assert len(attempts) == 1
            assert attempts[0].attempt_no == 1
    finally:
        engine.dispose()


def test_pre_dispatch_failure_can_retry_with_new_key_without_rewriting_history(client, db_session, monkeypatch):
    from app.services.stage_invocations import finalize_invocation, prepare_invocation

    _, _, _, user, run, step = _stage_context(client, db_session, monkeypatch)
    resolved = _resolved(db_session, user, run, step)
    first = prepare_invocation(db_session, run=run, step=step, user=user, resolved=resolved,
                               expected_resolution_hash=resolved["resolution_hash"], invocation_key="not-sent")
    done = finalize_invocation(db_session, attempt_id=first.id, status="failed", dispatch_certainty="not_dispatched")
    second = prepare_invocation(db_session, run=run, step=step, user=user, resolved=resolved,
                                expected_resolution_hash=resolved["resolution_hash"], invocation_key="fresh-key")
    assert second.id != done.id and second.attempt_no == 2
    assert done.status == "failed" and done.execution_receipt_json["outcome_state"] == "failed_before_dispatch"


def test_competing_finalizations_seal_exactly_one_output_and_matching_step(client, db_session, monkeypatch, tmp_path):
    import sqlite3
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from app.models import WorkflowRun, WorkflowStep, WorkflowStepAttempt
    from app.services.stage_contracts import digest
    from app.services.stage_invocations import finalize_invocation, prepare_invocation

    _, _, _, user, run, step = _stage_context(client, db_session, monkeypatch)
    resolved = _resolved(db_session, user, run, step)
    attempt = prepare_invocation(db_session, run=run, step=step, user=user, resolved=resolved,
                                 expected_resolution_hash=resolved["resolution_hash"], invocation_key="race-finalize")
    attempt_id, step_id, run_id = attempt.id, step.id, run.id
    db_session.commit()
    path = tmp_path / "finalize.db"
    with sqlite3.connect(path) as copied:
        db_session.connection().connection.driver_connection.backup(copied)
    engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False, "timeout": 5})
    barrier = Barrier(2)

    def seal(index):
        with Session(engine) as db:
            before = db.get(WorkflowStepAttempt, attempt_id)
            assert before.status == "running"
            barrier.wait(timeout=5)
            result = finalize_invocation(db, attempt_id=attempt_id, output={"winner": index},
                                         status="succeeded", dispatch_certainty="confirmed_dispatched")
            return result.output_hash

    try:
        with ThreadPoolExecutor(max_workers=2) as workers:
            hashes = list(workers.map(seal, range(2)))
        with Session(engine) as db:
            sealed = db.get(WorkflowStepAttempt, attempt_id)
            projected = db.get(WorkflowStep, step_id)
            assert len(set(hashes)) == 1
            assert sealed.output_json in ({"winner": 0}, {"winner": 1})
            assert sealed.output_hash == digest(sealed.output_json) == projected.output_hash
            assert sealed.execution_receipt_json["output_hash"] == sealed.output_hash
            assert sealed.output_json == projected.output_json
            assert projected.status == db.get(WorkflowRun, run_id).status == "waiting_input"
            assert sealed.input_snapshot_json == {"resolved_stage": resolved}
    finally:
        engine.dispose()
