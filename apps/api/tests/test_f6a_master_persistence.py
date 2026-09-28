"""FE-F6A Master persistence contracts on an isolated database."""

import importlib.util
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text
from test_candidate_manifest_v2 import env as draft_env  # noqa: F401

from app.db import Base
from app.models import (
    ArtifactKind,
    ContentMasterAssetRef,
    ContentMasterCheckRun,
    ContentMasterEvidenceRef,
    ContentMasterRevision,
)


def _master_unit(client):
    headers = {"X-Studio-User": "f6a-safety@studio.local"}
    persona = client.post("/api/v1/content-personas", json={"name": "安全作者"}, headers=headers).json()["id"]
    project = client.post("/api/v1/content-projects", json={"title": "安全项目"}, headers=headers).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project}/units", json={"title": "正文", "persona_id": persona, "modality": "text"}, headers=headers).json()["id"]
    return project, unit, f"/api/v1/content-projects/{project}/units/{unit}/master-revisions", headers


@pytest.mark.parametrize("history_table", ["content_master_revision", "content_master_asset_ref", "content_master_evidence_ref", "content_master_check_run"])
def test_downgrade_refuses_master_history_before_any_ddl(history_table):
    spec = importlib.util.spec_from_file_location("f6a_migration", Path(__file__).parents[1] / "alembic/versions/f6a000000001_production_content_master.py")
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE content_asset (id INTEGER PRIMARY KEY, final_body TEXT, content_master_revision_id INTEGER)"))
        connection.execute(text(f"CREATE TABLE {history_table} (id INTEGER PRIMARY KEY)"))
        connection.execute(text(f"INSERT INTO {history_table} (id) VALUES (1)"))
        migration.op = Operations(MigrationContext.configure(connection))
        with pytest.raises(RuntimeError, match="FE-F6A.*history"):
            migration.downgrade()
        assert "content_master_revision_id" in {item["name"] for item in inspect(connection).get_columns("content_asset")}
        assert connection.scalar(text(f"SELECT count(*) FROM {history_table}")) == 1
    engine.dispose()


@pytest.mark.parametrize("body,master_id", [(None, None), ("正文", 42)])
def test_downgrade_refuses_incompatible_candidates_before_ddl(body, master_id):
    spec = importlib.util.spec_from_file_location("f6a_migration", Path(__file__).parents[1] / "alembic/versions/f6a000000001_production_content_master.py")
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE content_asset (id INTEGER PRIMARY KEY, final_body TEXT, content_master_revision_id INTEGER)"))
        connection.execute(text("INSERT INTO content_asset VALUES (1, :body, :master_id)"), {"body": body, "master_id": master_id})
        migration.op = Operations(MigrationContext.configure(connection))
        with pytest.raises(RuntimeError, match="FE-F6A.*history"):
            migration.downgrade()
        assert connection.execute(text("SELECT final_body, content_master_revision_id FROM content_asset")).one() == (body, master_id)
    engine.dispose()


def test_archived_unit_cannot_append_check_history(client, db_session):
    from app.models import ContentUnit

    _, unit, path, headers = _master_unit(client)
    saved = client.post(path, json={"idempotency_key": "archive-check", "payload": {"markdown": "内容"}}, headers=headers).json()
    db_session.get(ContentUnit, unit).status = "archived"
    db_session.commit()
    assert client.post(f"{path}/{saved['id']}/checks", headers=headers).status_code == 409
    assert client.get(f"{path}/{saved['id']}/checks", headers=headers).json()["items"] == []


@pytest.mark.parametrize("field,value", [("payload_schema", "video.master.v1"), ("source_kind", "workflow_seed")])
def test_manual_save_rejects_forged_schema_or_provenance(client, field, value):
    _, _, path, headers = _master_unit(client)
    response = client.post(path, json={"idempotency_key": "forged", "payload": {"markdown": "内容"}, field: value}, headers=headers)
    assert response.status_code == 422
    assert client.get(path, headers=headers).json()["items"] == []


def test_idempotent_replay_survives_upstream_context_drift(client, db_session):
    from app.models import ContentUnit

    _, unit, path, headers = _master_unit(client)
    body = {"idempotency_key": "lost-response", "payload": {"markdown": "内容"}}
    saved = client.post(path, json=body, headers=headers).json()
    db_session.get(ContentUnit, unit).channel_id = "wechat"
    db_session.commit()
    response = client.post(path, json=body, headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["id"] == saved["id"]
    assert "stale_channel" in response.json()["readiness"]["reasons"]


def test_empty_text_can_draft_but_is_not_render_ready(client):
    _, _, path, headers = _master_unit(client)
    response = client.post(path, json={"idempotency_key": "empty-draft", "payload": {"markdown": ""}}, headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["readiness"]["state"] == "incomplete_context"
    checks = client.post(f"{path}/{response.json()['id']}/checks", headers=headers).json()["items"]
    assert next(item for item in checks if item["check_kind"] == "render")["status"] == "incomplete"


def test_document_without_supported_renderer_does_not_claim_render_pass(client):
    _, _, path, headers = _master_unit(client)
    saved = client.post(path, json={"idempotency_key": "document", "payload": {"document": {"blocks": [{"text": "内容"}]}}}, headers=headers).json()
    checks = client.post(f"{path}/{saved['id']}/checks", headers=headers).json()["items"]
    assert next(item for item in checks if item["check_kind"] == "render")["status"] == "incomplete"


def test_evidence_ref_rejects_missing_frozen_checksum(client, draft_env):  # noqa: F811
    from app.models import FactPackItem, ProjectFactBoundaryRevision

    db, topic, _ = draft_env
    project, _, path, headers = _master_unit(client)
    db.add(ProjectFactBoundaryRevision(project_id=project, revision_no=1, fact_pack_id=topic.fact_pack_id, fact_pack_version=topic.fact_pack_version, fact_pack_checksum=topic.fact_pack.checksum))
    item = FactPackItem(fact_pack_id=topic.fact_pack_id, evidence_kind="author_opinion", snapshot_checksum=None)
    db.add(item)
    db.commit()
    response = client.post(path, json={"idempotency_key": "invalid-evidence", "payload": {"markdown": "内容"}, "evidence_refs": [{"fact_pack_item_id": item.id, "snapshot_checksum": None}]}, headers=headers)
    assert response.status_code == 422, response.text
    assert client.get(path, headers=headers).json()["items"] == []


def test_master_read_is_bounded_and_detail_is_owner_scoped(client):
    _, _, path, headers = _master_unit(client)
    saved = client.post(path, json={"idempotency_key": "detail", "payload": {"markdown": "内容"}}, headers=headers).json()
    assert client.get(f"{path}/{saved['id']}", headers=headers).json()["id"] == saved["id"]
    assert client.get(f"{path}/{saved['id']}", headers={"X-Studio-User": "foreign@studio.local"}).status_code == 404
    assert client.get(f"{path}?limit=1001", headers=headers).status_code == 422


def test_new_master_defaults_parent_to_current_head(client):
    _, _, path, headers = _master_unit(client)
    first = client.post(path, json={"idempotency_key": "parent-1", "payload": {"markdown": "第一版"}}, headers=headers).json()
    second = client.post(path, json={"expected_revision": 1, "idempotency_key": "parent-2", "payload": {"markdown": "第二版"}}, headers=headers).json()
    assert second["parent_revision_id"] == first["id"]
    conflict = client.post(path, json={"expected_revision": 2, "parent_revision_id": first["id"], "idempotency_key": "parent-3", "payload": {"markdown": "第三版"}}, headers=headers)
    assert conflict.status_code == 409


def test_payload_rejects_excessive_depth_before_persistence(client):
    _, _, path, headers = _master_unit(client)
    nested = {}
    for _ in range(40):
        nested = {"child": nested}
    response = client.post(path, json={"idempotency_key": "deep", "payload": {"markdown": "内容", "structured": nested}}, headers=headers)
    assert response.status_code == 422
    assert client.get(path, headers=headers).json()["items"] == []


def test_candidate_freeze_requires_exactly_one_source(client):
    project, unit, _, headers = _master_unit(client)
    path = f"/api/v1/content-projects/{project}/units/{unit}/candidates/freeze"
    assert client.post(path, json={}, headers=headers).status_code == 422
    assert client.post(path, json={"project_output_id": 1, "content_master_revision_id": 1}, headers=headers).status_code == 422


def test_checks_append_history_and_current_selects_latest_blocker(client, db_session):
    _, _, path, headers = _master_unit(client)
    master = client.post(path, json={"idempotency_key": "latest-check", "payload": {"markdown": "内容"}}, headers=headers).json()
    check_path = f"{path}/{master['id']}/checks"
    first = client.post(check_path, headers=headers).json()["items"]
    second = client.post(check_path, headers=headers).json()["items"]
    assert first[0]["id"] != second[0]["id"]
    assert first[0]["input_hash"] == second[0]["input_hash"]
    db_session.add(ContentMasterCheckRun(master_revision_id=master["id"], check_kind="master_schema", profile_key="text.master.v1", profile_version="1", input_hash=second[0]["input_hash"], status="blocker", report_json={"reason": "later_blocker"}))
    db_session.commit()
    current = client.get(f"{check_path}/current", headers=headers)
    assert current.status_code == 200, current.text
    assert next(item for item in current.json()["items"] if item["check_kind"] == "master_schema")["status"] == "blocker"


def test_check_projection_becomes_stale_without_rewriting_history(client, db_session):
    from app.models import ContentUnit

    _, unit, path, headers = _master_unit(client)
    master = client.post(path, json={"idempotency_key": "stale-check", "payload": {"markdown": "内容"}}, headers=headers).json()
    check_path = f"{path}/{master['id']}/checks"
    old = client.post(check_path, headers=headers).json()["items"]
    db_session.get(ContentUnit, unit).channel_id = "wechat"
    db_session.commit()
    current = client.get(f"{check_path}/current", headers=headers)
    assert current.status_code == 200
    assert all(item["status"] == "stale" for item in current.json()["items"])
    assert db_session.get(ContentMasterCheckRun, old[0]["id"]).status == "pass"


@pytest.mark.parametrize("status", ["succeeded", "failed", "stale", "replaced"])
def test_draft_seed_requires_current_successful_attempt(client, draft_env, status):  # noqa: F811
    from app.models import ContentUnit, ProjectWorkflowOutput, Workflow, WorkflowRun, WorkflowStep, WorkflowStepAttempt

    db, _, draft = draft_env
    project, unit, path, headers = _master_unit(client)
    workflow = Workflow(name="Seed", workflow_key="seed", version=1, definition_json={}, checksum="w" * 64)
    db.add(workflow)
    db.flush()
    run = WorkflowRun(workflow_id=workflow.id, content_unit_id=unit, identity_snapshot_id=db.get(ContentUnit, unit).identity_snapshot_id, status="succeeded")
    db.add(run)
    db.flush()
    draft.content_job.workflow_run_id = run.id
    step = WorkflowStep(run_id=run.id, node_id="generate", node_type="AI", status="succeeded" if status == "replaced" else status, attempt_no=1, output_json={"draft_id": draft.id}, output_hash="o" * 64)
    db.add(step)
    db.flush()
    attempt = WorkflowStepAttempt(step_id=step.id, run_id=run.id, node_id=step.node_id, attempt_no=1, status="succeeded", output_json={"draft_id": draft.id}, output_hash=step.output_hash, input_hash="i" * 64)
    db.add(attempt)
    db.flush()
    output = ProjectWorkflowOutput(project_id=project, unit_id=unit, run_id=run.id, node_id=step.node_id, attempt_id=attempt.id, output_kind="draft", entity_id=draft.id)
    db.add(output)
    if status == "replaced":
        step.attempt_no = 2
        db.add(WorkflowStepAttempt(step_id=step.id, run_id=run.id, node_id=step.node_id, attempt_no=2, status="failed", output_json={}))
    db.commit()
    response = client.post(f"{path}/from-output", json={"project_output_id": output.id, "idempotency_key": "seed"}, headers=headers)
    if status == "succeeded":
        assert response.status_code == 200, response.text
        provenance = response.json()["edit_summary"]["workflow_source"]
        assert provenance["draft_id"] == draft.id and provenance["attempt_id"] == attempt.id
        assert provenance["draft_input_hash"] == draft.input_hash
    else:
        assert response.status_code == 409, response.text
        assert client.get(path, headers=headers).json()["items"] == []


def test_master_models_keep_exact_revision_and_ref_columns():
    engine = create_engine("sqlite:///:memory:")
    try:
        Base.metadata.create_all(engine)
        inspector = inspect(engine)
        master = {column["name"] for column in inspector.get_columns("content_master_revision")}
        assert {
            "project_id", "content_unit_id", "revision_no", "parent_revision_id", "modality",
            "channel_id", "content_form", "payload_schema", "payload_json", "payload_hash",
            "context_hash", "identity_snapshot_id", "creative_brief_revision_id",
            "fact_boundary_revision_id", "origin_workflow_run_id", "origin_project_output_id",
            "source_kind", "edit_summary_json", "idempotency_key", "request_fingerprint",
            "created_by", "created_at",
        } <= master
        assert ContentMasterRevision.__tablename__ == "content_master_revision"
        assert ContentMasterAssetRef.__tablename__ == "content_master_asset_ref"
        assert ContentMasterEvidenceRef.__tablename__ == "content_master_evidence_ref"
        assert ContentMasterCheckRun.__tablename__ == "content_master_check_run"
        assert {"content_master_revision_id", "final_body"} <= {
            column["name"] for column in inspector.get_columns("content_asset")
        }
        assert next(column for column in inspector.get_columns("content_asset") if column["name"] == "final_body")["nullable"]
        assert ArtifactKind.video.value == "video"
    finally:
        engine.dispose()


def test_master_revision_has_unit_scoped_unique_keys():
    engine = create_engine("sqlite:///:memory:")
    try:
        Base.metadata.create_all(engine)
        keys = {
            tuple(item["column_names"])
            for item in inspect(engine).get_unique_constraints("content_master_revision")
        }
        assert ("content_unit_id", "revision_no") in keys
        assert ("content_unit_id", "idempotency_key") in keys
    finally:
        engine.dispose()


def test_master_save_is_append_only_idempotent_and_cas(client):
    headers = {"X-Studio-User": "f6a-owner@studio.local"}
    persona = client.post("/api/v1/content-personas", json={"name": "Master作者"}, headers=headers).json()["id"]
    project = client.post("/api/v1/content-projects", json={"title": "Master项目"}, headers=headers).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project}/units", json={"title": "正文", "persona_id": persona, "modality": "text"}, headers=headers).json()["id"]
    path = f"/api/v1/content-projects/{project}/units/{unit}/master-revisions"
    body = {"expected_revision": 0, "idempotency_key": "master-1", "payload": {"markdown": "第一版"}}
    first = client.post(path, json=body, headers=headers)
    assert first.status_code == 200, first.text
    replay = client.post(path, json=body, headers=headers)
    assert replay.status_code == 200 and replay.json()["id"] == first.json()["id"]
    conflict = client.post(path, json={**body, "idempotency_key": "master-2"}, headers=headers)
    assert conflict.status_code == 409
    assert client.get(path, headers=headers).json()["items"][0]["payload_hash"] == first.json()["payload_hash"]


def test_master_checks_are_input_bound_and_report_incomplete_context(client):
    headers = {"X-Studio-User": "f6a-checker@studio.local"}
    persona = client.post("/api/v1/content-personas", json={"name": "检查作者"}, headers=headers).json()["id"]
    project = client.post("/api/v1/content-projects", json={"title": "检查项目"}, headers=headers).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project}/units", json={"title": "正文", "persona_id": persona, "modality": "text"}, headers=headers).json()["id"]
    path = f"/api/v1/content-projects/{project}/units/{unit}/master-revisions"
    saved = client.post(path, json={"idempotency_key": "check-1", "payload": {"markdown": "检查"}}, headers=headers).json()
    checks = client.post(f"{path}/{saved['id']}/checks", headers=headers)
    assert checks.status_code == 200
    by_kind = {item["check_kind"]: item for item in checks.json()["items"]}
    assert by_kind["master_schema"]["status"] == "pass"
    assert by_kind["evidence"]["status"] == "incomplete"
    assert client.post(f"{path}/{saved['id']}/checks", headers=headers).json()["items"][0]["input_hash"] == checks.json()["items"][0]["input_hash"]
