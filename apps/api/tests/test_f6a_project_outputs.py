"""Only persisted, attempt-backed Masters enter workflow output history."""

import pytest
from test_f6a_modality_adapters import HEADERS, _unit

from app.models import (
    ContentMasterRevision,
    ProjectWorkflowOutput,
    Workflow,
    WorkflowRun,
    WorkflowStep,
    WorkflowStepAttempt,
)
from app.services.project_outputs import associate_step_output


def _output(client, db):
    _, path = _unit(client, db, "text")
    saved = client.post(path, json={"idempotency_key": "node", "payload": {"markdown": "持久成品"}}, headers=HEADERS).json()
    master = db.get(ContentMasterRevision, saved["id"])
    workflow = Workflow(name="Future persisted Master emitter", definition_json={"nodes": []})
    db.add(workflow)
    db.flush()
    run = WorkflowRun(workflow_id=workflow.id, content_unit_id=master.content_unit_id, identity_snapshot_id=master.identity_snapshot_id, status="running")
    db.add(run)
    db.flush()
    master.origin_workflow_run_id = run.id
    step = WorkflowStep(run_id=run.id, node_id="master", node_type="System", plugin_key="future.master", status="succeeded", output_json={"content_master_revision_id": master.id}, output_hash="a" * 64)
    db.add(step)
    db.flush()
    attempt = WorkflowStepAttempt(run_id=run.id, step_id=step.id, node_id=step.node_id, plugin_key=step.plugin_key, status="succeeded", output_json=step.output_json, output_hash=step.output_hash)
    db.add(attempt)
    db.commit()
    return master, run, step, attempt


def test_verified_master_output_is_associated_once_and_serialized(client, db_session):
    master, run, step, attempt = _output(client, db_session)
    output = associate_step_output(db_session, run, step, attempt.id)
    assert output is not None
    assert output.output_kind == "content_master_revision"
    assert output.provenance_json["payload_hash"] == master.payload_hash
    assert associate_step_output(db_session, run, step, attempt.id).id == output.id
    db_session.commit()
    rows = client.get(f"/api/v1/content-projects/{master.project_id}/units/{master.content_unit_id}/outputs", headers=HEADERS).json()
    assert rows[0]["entity_id"] == master.id


@pytest.mark.parametrize("problem", ["foreign_unit", "foreign_run", "identity", "failed", "step_failed", "attempt_output", "output_hash", "replaced_attempt"])
def test_unverified_master_output_is_not_associated(client, db_session, problem):
    master, run, step, attempt = _output(client, db_session)
    if problem == "foreign_unit":
        run.content_unit_id = None
    elif problem == "foreign_run":
        master.origin_workflow_run_id = None
    elif problem == "identity":
        run.identity_snapshot_id = None
    elif problem == "failed":
        attempt.status = "failed"
    elif problem == "step_failed":
        step.status = "failed"
    elif problem == "attempt_output":
        attempt.output_json = {}
    elif problem == "output_hash":
        attempt.output_hash = "b" * 64
    else:
        db_session.add(WorkflowStepAttempt(run_id=run.id, step_id=step.id, node_id=step.node_id, plugin_key=step.plugin_key, status="failed", output_json={}))
    db_session.commit()
    assert associate_step_output(db_session, run, step, attempt.id) is None
    assert db_session.query(ProjectWorkflowOutput).count() == 0
