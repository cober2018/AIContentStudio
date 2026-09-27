"""FE-F2 project persistence contracts."""

from sqlalchemy import inspect

from app.db import Base
from app.models import Workflow, WorkflowRun


def test_project_foundation_tables_and_run_binding(db_session):
    tables = set(inspect(db_session.bind).get_table_names())
    assert {
        "content_persona",
        "content_project",
        "content_unit",
        "persona_workflow_default",
        "project_workflow_binding",
        "data_snapshot",
        "project_workflow_output",
    } <= tables
    assert "content_unit_id" in WorkflowRun.__table__.columns
    assert "workflow" in Base.metadata.tables
    assert Workflow.__table__.columns["workflow_key"] is not None


def test_project_and_unit_crud_is_owned_by_creator(client):
    alice = {"X-Studio-User": "alice@studio.local"}
    bob = {"X-Studio-User": "bob@studio.local"}
    persona = client.post("/api/v1/content-personas", json={"name": "创始人"}, headers=alice)
    assert persona.status_code == 201
    project = client.post("/api/v1/content-projects", json={"title": "发布计划", "objective": "V1"}, headers=alice)
    assert project.status_code == 201
    project_id = project.json()["id"]
    unit = client.post(
        f"/api/v1/content-projects/{project_id}/units",
        json={"title": "长文", "persona_id": persona.json()["id"], "modality": "text", "channel_id": "wechat"},
        headers=alice,
    )
    assert unit.status_code == 201
    unit_id = unit.json()["id"]
    assert client.get(f"/api/v1/content-projects/{project_id}", headers=alice).status_code == 200
    assert client.patch(f"/api/v1/content-projects/{project_id}/units/{unit_id}", json={"title": "长文 v2"}, headers=alice).json()["title"] == "长文 v2"
    assert client.get(f"/api/v1/content-projects/{project_id}", headers=bob).status_code == 404
    assert client.patch(f"/api/v1/content-projects/{project_id}/units/{unit_id}", json={"title": "越权"}, headers=bob).status_code == 404
    assert client.get("/api/v1/content-projects", headers=bob).json() == []
    assert client.delete(f"/api/v1/content-projects/{project_id}/units/{unit_id}", headers=alice).status_code == 204
    assert client.delete(f"/api/v1/content-projects/{project_id}", headers=alice).status_code == 204
    archived = client.get(f"/api/v1/content-projects/{project_id}", headers=alice)
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"
    assert client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "Again", "persona_id": persona.json()["id"], "modality": "text"}, headers=alice).status_code == 409


def test_unit_rejects_foreign_persona_and_unowned_workflow(client):
    alice = {"X-Studio-User": "alice@studio.local"}
    bob = {"X-Studio-User": "bob@studio.local"}
    project_id = client.post("/api/v1/content-projects", json={"title": "A"}, headers=alice).json()["id"]
    foreign_persona = client.post("/api/v1/content-personas", json={"name": "B"}, headers=bob).json()["id"]
    payload = {"title": "Article", "persona_id": foreign_persona, "modality": "text"}
    assert client.post(f"/api/v1/content-projects/{project_id}/units", json=payload, headers=alice).status_code == 404


def test_unit_override_only_can_edit_in_place_and_rebind_default(client):
    from test_fe_f2_workflows import _definition

    headers = {"X-Studio-User": "alice@studio.local"}
    persona_a = client.post("/api/v1/content-personas", json={"name": "A"}, headers=headers).json()["id"]
    persona_b = client.post("/api/v1/content-personas", json={"name": "B"}, headers=headers).json()["id"]
    project = client.post("/api/v1/content-projects", json={"title": "P"}, headers=headers).json()["id"]
    portable = {"nodes": [{"id": "gate", "kind": "Human", "plugin": "builtin.approve", "config": {}}], "edges": [], "visual_order": ["gate"]}
    default_response = client.post(f"/api/v1/content-personas/{persona_b}/default-workflows/graphic", headers=headers, json={"expected_revision": 0, "definition": portable})
    assert default_response.status_code == 201, default_response.text
    default = default_response.json()
    unit = client.post(f"/api/v1/content-projects/{project}/units", headers=headers, json={"title": "Old", "persona_id": persona_a, "modality": "text"}).json()
    base = f"/api/v1/content-projects/{project}/units/{unit['id']}"
    assert client.post(f"{base}/workflow-override", headers=headers, json={"expected_revision": 0, "definition": _definition()}).status_code == 201
    assert client.get(f"{base}/effective-workflow", headers=headers).json()["source"] == "project_override"
    changed = client.patch(base, headers=headers, json={"title": "New", "persona_id": persona_b, "modality": "graphic", "rebind_default": True})
    assert changed.status_code == 200, changed.text
    assert changed.json()["id"] == unit["id"]
    assert changed.json()["pinned_workflow_id"] == default["workflow_id"]
    assert client.get(f"{base}/workflow-override", headers=headers).json()["workflow_id"] is None
    assert client.delete(base, headers=headers).status_code == 204
    assert client.get(base, headers=headers).status_code == 404


def test_historic_unit_replaced_and_delete_archives_without_losing_run(client):
    from test_fe_f2_workflows import _definition

    headers = {"X-Studio-User": "alice@studio.local"}
    persona = client.post("/api/v1/content-personas", json={"name": "A"}, headers=headers).json()["id"]
    project = client.post("/api/v1/content-projects", json={"title": "P"}, headers=headers).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project}/units", headers=headers, json={"title": "Old", "persona_id": persona, "modality": "text"}).json()
    base = f"/api/v1/content-projects/{project}/units/{unit['id']}"
    assert client.post(f"{base}/workflow-override", headers=headers, json={"expected_revision": 0, "definition": _definition()}).status_code == 201
    run = client.post(f"{base}/runs", headers=headers, json={"params": {}}).json()
    changed = client.patch(base, headers=headers, json={"modality": "graphic", "rebind_default": True})
    assert changed.status_code == 200, changed.text
    assert changed.json()["id"] != unit["id"]
    assert changed.json()["modality"] == "graphic"
    assert client.get(base, headers=headers).json()["status"] == "archived"
    assert client.get(f"{base}/runs/{run['id']}", headers=headers).status_code == 200
    assert client.post(f"{base}/runs/{run['id']}/nodes/a/rerun", headers=headers).status_code == 409
    assert client.post(f"/api/v1/workflow-runs/{run['id']}/nodes/a/rerun", headers=headers).status_code == 409
    assert client.delete(f"/api/v1/content-projects/{project}/units/{changed.json()['id']}", headers=headers).status_code == 204
    assert client.delete(base, headers=headers).status_code == 204
    assert client.get(base, headers=headers).json()["status"] == "archived"


def test_legacy_workflow_routes_hide_project_bound_run_and_definition(client, db_session):
    from app.models import ContentUnit, ProjectWorkflowBinding, User, WorkflowStep

    alice = {"X-Studio-User": "alice@studio.local"}
    bob = {"X-Studio-User": "bob@studio.local"}
    project_id = client.post("/api/v1/content-projects", json={"title": "私有项目"}, headers=alice).json()["id"]
    persona_id = client.post("/api/v1/content-personas", json={"name": "作者"}, headers=alice).json()["id"]
    unit_id = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "A", "persona_id": persona_id, "modality": "text"}, headers=alice).json()["id"]
    workflow = Workflow(name="private", workflow_key="project.private", version=1, status="published", definition_json={"nodes": [], "edges": []}, checksum="abc", created_by="alice@studio.local")
    db_session.add(workflow)
    db_session.flush()
    db_session.add(ProjectWorkflowBinding(unit_id=unit_id, workflow_id=workflow.id, revision=1))
    run = WorkflowRun(workflow_id=workflow.id, content_unit_id=unit_id, status="waiting_input", context_json={}, params_json={}, workflow_key=workflow.workflow_key, workflow_version=1, definition_checksum="abc")
    db_session.add(run)
    db_session.flush()
    db_session.add(WorkflowStep(run_id=run.id, node_id="human", node_type="approve", status="waiting_input", params_json={}, output_json={}))
    db_session.commit()
    db_session.expire_all()
    run_id, workflow_id = run.id, workflow.id
    assert client.get(f"/api/v1/workflow-runs/{run_id}", headers=alice).status_code == 200
    assert client.get(f"/api/v1/workflow-runs/{run_id}", headers=bob).status_code == 404
    assert client.get(f"/api/v1/workflow-runs/{run_id}/nodes/human/attempts", headers=bob).status_code == 404
    for suffix, body in [
        ("retry", None),
        ("nodes/human/rerun", None),
        ("nodes/human/rerun-from-here", None),
        ("nodes/human/complete", {"payload": {}}),
        ("cancel", None),
    ]:
        response = client.post(f"/api/v1/workflow-runs/{run_id}/{suffix}", headers=bob, json=body)
        assert response.status_code == 404, (suffix, response.text)
    assert all(item["id"] != run_id for item in client.get("/api/v1/workflow-runs", headers=bob).json())
    assert all(item["id"] != workflow_id for item in client.get("/api/v1/workflows", headers=bob).json())
    assert client.post("/api/v1/workflow-runs", headers=bob, json={"workflow_id": workflow_id, "params": {}}).status_code == 404
    assert client.post("/api/v1/workflow-runs", headers=alice, json={"workflow_id": workflow_id, "params": {}}).status_code == 409
