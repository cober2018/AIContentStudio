"""Data Source selection and snapshot refresh invariants."""

from app.models import DataSnapshot, SourceDocument, WorkflowRun, WorkflowStep


def test_plugin_catalog_disconnected_sources_are_unexecutable(client):
    headers = {"X-Studio-User": "data@studio.local"}
    response = client.get("/api/v1/data-source-plugins", headers=headers)
    assert response.status_code == 200
    plugins = {item["key"]: item for item in response.json()}
    assert {"studio.source", "media.data", "notion", "obsidian", "api", "sql"} <= set(plugins)
    assert plugins["studio.source"]["available"] is True
    for key in ("media.data", "notion", "obsidian", "api", "sql"):
        assert plugins[key]["available"] is False
        assert plugins[key]["reason"]


def test_data_snapshot_refresh_changes_only_true_descendants(client, db_session):
    headers = {"X-Studio-User": "data@studio.local"}
    source = SourceDocument(title="内部来源", source_type="text", raw_text="first", parse_status="done", sha256="v1")
    db_session.add(source)
    db_session.commit()
    persona_id = client.post("/api/v1/content-personas", json={"name": "分析员"}, headers=headers).json()["id"]
    project_id = client.post("/api/v1/content-projects", json={"title": "研究"}, headers=headers).json()["id"]
    unit_id = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "日报", "persona_id": persona_id, "modality": "text"}, headers=headers).json()["id"]
    definition = {
        "nodes": [
            {"id": "data", "kind": "Data", "plugin": "data.source", "config": {"data_source_plugin_key": "studio.source", "source_ref": str(source.id)}},
            {"id": "child", "kind": "System", "plugin": "system.constant", "config": {"value": {"ok": True}}, "input_mapping": {"snapshot_id": {"node_id": "data", "output": "snapshot_id"}}},
            {"id": "sibling", "kind": "System", "plugin": "system.constant", "config": {"value": {"ok": True}}},
        ],
        "edges": [{"from": "data", "to": "child"}],
        "visual_order": ["data", "child", "sibling"],
    }
    save = client.post(f"/api/v1/content-projects/{project_id}/units/{unit_id}/workflow-override", json={"expected_revision": 0, "definition": definition}, headers=headers)
    assert save.status_code == 201, save.text
    path = f"/api/v1/content-projects/{project_id}/units/{unit_id}/runs"
    started = client.post(path, json={"params": {}}, headers=headers)
    assert started.status_code == 201, started.text
    run_id = started.json()["id"]
    assert started.json()["status"] == "succeeded"
    first_snapshot = started.json()["steps"][0]["output"]["snapshot_id"]
    assert started.json()["steps"][1]["params"]["inputs"]["snapshot_id"] == first_snapshot
    snapshot_path = f"/api/v1/content-projects/{project_id}/units/{unit_id}/snapshots/{first_snapshot}"
    assert client.get(snapshot_path, headers=headers).json()["normalized_output"]["text"] == "first"
    assert client.get(snapshot_path, headers={"X-Studio-User": "other@studio.local"}).status_code == 404
    assert db_session.get(DataSnapshot, first_snapshot).source_ref == str(source.id)
    same = client.post(f"{path}/{run_id}/nodes/data/rerun", headers=headers)
    assert same.status_code == 200
    assert {step["node_id"]: step["status"] for step in same.json()["steps"]}["child"] == "succeeded"
    source.raw_text = "second"
    source.sha256 = "v2"
    db_session.commit()
    changed = client.post(f"{path}/{run_id}/nodes/data/rerun", headers=headers)
    assert changed.status_code == 200
    steps = {step["node_id"]: step for step in changed.json()["steps"]}
    assert steps["child"]["status"] == "stale"
    assert steps["sibling"]["status"] == "succeeded"
    assert steps["data"]["output"]["snapshot_id"] != first_snapshot
    assert db_session.query(DataSnapshot).filter(DataSnapshot.run_id == run_id).count() == 3


def test_disconnected_plugin_blocks_without_snapshot(client, db_session):
    headers = {"X-Studio-User": "data@studio.local"}
    persona_id = client.post("/api/v1/content-personas", json={"name": "分析员"}, headers=headers).json()["id"]
    project_id = client.post("/api/v1/content-projects", json={"title": "研究"}, headers=headers).json()["id"]
    unit_id = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "日报", "persona_id": persona_id, "modality": "text"}, headers=headers).json()["id"]
    definition = {"nodes": [{"id": "data", "kind": "Data", "plugin": "data.source", "config": {"data_source_plugin_key": "notion", "source_ref": "some-page"}}], "edges": [], "visual_order": ["data"]}
    save = client.post(f"/api/v1/content-projects/{project_id}/units/{unit_id}/workflow-override", json={"expected_revision": 0, "definition": definition}, headers=headers)
    assert save.status_code == 201, save.text
    started = client.post(f"/api/v1/content-projects/{project_id}/units/{unit_id}/runs", json={"params": {}}, headers=headers)
    assert started.status_code == 409
    assert db_session.query(DataSnapshot).count() == 0
    assert db_session.query(WorkflowRun).count() == 0


def test_role_default_data_source_ref_is_parameterized_for_later_unit(client, db_session):
    headers = {"X-Studio-User": "data@studio.local"}
    source = SourceDocument(title="共享来源", source_type="text", raw_text="truth", parse_status="done")
    db_session.add(source)
    db_session.commit()
    persona_id = client.post("/api/v1/content-personas", json={"name": "作者"}, headers=headers).json()["id"]
    project_id = client.post("/api/v1/content-projects", json={"title": "A"}, headers=headers).json()["id"]
    first_unit = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "首条", "persona_id": persona_id, "modality": "text"}, headers=headers).json()["id"]
    definition = {"nodes": [{"id": "data", "kind": "Data", "plugin": "data.source", "config": {"data_source_plugin_key": "studio.source", "source_ref": str(source.id)}}], "edges": [], "visual_order": ["data"]}
    saved = client.post(f"/api/v1/content-personas/{persona_id}/default-workflows/text", json={"expected_revision": 0, "definition": definition, "source_project_id": project_id, "source_unit_id": first_unit}, headers=headers)
    assert saved.status_code == 201, saved.text
    assert saved.json()["definition"]["nodes"][0]["config"]["source_ref"] == {"$run_param": "source_ref"}
    later_unit = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "第二条", "persona_id": persona_id, "modality": "text"}, headers=headers).json()
    assert later_unit["pinned_workflow_id"] == saved.json()["workflow_id"]
    path = f"/api/v1/content-projects/{project_id}/units/{later_unit['id']}/runs"
    assert client.post(path, json={"params": {}}, headers=headers).status_code == 409
    run = client.post(path, json={"params": {"source_ref": str(source.id)}}, headers=headers)
    assert run.status_code == 201, run.text
    assert run.json()["status"] == "succeeded"
    assert run.json()["steps"][0]["output"]["snapshot_id"]
