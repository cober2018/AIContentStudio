"""FE-F2 workflow design/versioning boundaries."""

from app.models import ContentUnit, Workflow


def _setup(client):
    headers = {"X-Studio-User": "designer@studio.local"}
    persona_id = client.post("/api/v1/content-personas", json={"name": "创始人"}, headers=headers).json()["id"]
    project_id = client.post("/api/v1/content-projects", json={"title": "A"}, headers=headers).json()["id"]
    unit_id = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "文章", "persona_id": persona_id, "modality": "text"}, headers=headers).json()["id"]
    return headers, persona_id, project_id, unit_id


def _definition():
    return {
        "nodes": [
            {"id": "a", "kind": "System", "plugin": "system.constant", "config": {"value": {"result": "ok"}}},
            {"id": "b", "kind": "Human", "plugin": "builtin.approve", "config": {}, "input_mapping": {"source": {"node_id": "a", "output": "result"}}},
        ],
        "edges": [{"from": "a", "to": "b"}],
        "visual_order": ["a", "b"],
    }


def test_override_conflict_and_visual_order_preserves_edges(client, db_session):
    headers, _persona_id, project_id, unit_id = _setup(client)
    path = f"/api/v1/content-projects/{project_id}/units/{unit_id}/workflow-override"
    first = client.post(path, headers=headers, json={"expected_revision": 0, "definition": _definition()})
    assert first.status_code == 201, first.text
    first_id = first.json()["workflow_id"]
    assert first.json()["revision"] == 1
    reordered = _definition()
    reordered["visual_order"] = ["b", "a"]
    second = client.post(path, headers=headers, json={"expected_revision": 1, "definition": reordered})
    assert second.status_code == 201, second.text
    assert second.json()["revision"] == 2
    assert second.json()["workflow_id"] != first_id
    assert client.post(path, headers=headers, json={"expected_revision": 1, "definition": _definition()}).status_code == 409
    saved = client.get(path, headers=headers).json()
    assert saved["definition"]["visual_order"] == ["b", "a"]
    assert saved["definition"]["edges"] == [{"from": "a", "to": "b"}]
    assert db_session.get(Workflow, first_id).definition_json["visual_order"] == ["a", "b"]


def test_invalid_graph_and_mapping_rejected_without_changing_binding(client):
    headers, _, project_id, unit_id = _setup(client)
    path = f"/api/v1/content-projects/{project_id}/units/{unit_id}/workflow-override"
    bad = _definition()
    bad["edges"].append({"from": "b", "to": "a"})
    assert client.post(path, headers=headers, json={"expected_revision": 0, "definition": bad}).status_code == 422
    bad = _definition()
    bad["nodes"][1]["input_mapping"]["source"]["node_id"] = "missing"
    assert client.post(path, headers=headers, json={"expected_revision": 0, "definition": bad}).status_code == 422
    bad = _definition()
    bad["nodes"].append({**bad["nodes"][0]})
    assert client.post(path, headers=headers, json={"expected_revision": 0, "definition": bad}).status_code == 422
    bad = _definition()
    bad["nodes"][0]["plugin"] = "builtin.publish_wechat"
    assert client.post(path, headers=headers, json={"expected_revision": 0, "definition": bad}).status_code == 422
    bad = _definition()
    bad["nodes"][0]["kind"] = "Data"
    bad["nodes"][0]["plugin"] = "data.source"
    bad["nodes"][0]["config"] = {"data_source_plugin_key": "unregistered", "source_ref": "1"}
    assert client.post(path, headers=headers, json={"expected_revision": 0, "definition": bad}).status_code == 422
    assert client.get(path, headers=headers).json()["revision"] == 0


def test_ai_executor_selection_matches_effective_runtime(client):
    headers, _, project_id, unit_id = _setup(client)
    options = client.get("/api/v1/workflow-execution-options", headers=headers)
    assert options.status_code == 200
    choice = options.json()["ai"]["builtin.generate"]
    assert set(choice) >= {"provider", "model", "available", "reason"}
    assert "api_key" not in str(options.json())
    path = f"/api/v1/content-projects/{project_id}/units/{unit_id}/workflow-override"
    definition = {"nodes": [{"id": "generate", "kind": "AI", "plugin": "builtin.generate", "config": {"provider": choice["provider"], "model": choice["model"]}}], "edges": [], "visual_order": ["generate"]}
    assert client.post(path, headers=headers, json={"expected_revision": 0, "definition": definition}).status_code == 201
    definition["nodes"][0]["config"]["model"] = "unconfigured-model"
    assert client.post(path, headers=headers, json={"expected_revision": 1, "definition": definition}).status_code == 422
    assert client.get(path, headers=headers).json()["revision"] == 1


def test_ai_runtime_change_blocks_old_selected_model_before_execution(client):
    from app import runtime_config

    headers, _, project_id, unit_id = _setup(client)
    choice = client.get("/api/v1/workflow-execution-options", headers=headers).json()["ai"]["builtin.generate"]
    definition = {"nodes": [{"id": "generate", "kind": "AI", "plugin": "builtin.generate", "config": {"provider": choice["provider"], "model": choice["model"]}}], "edges": [], "visual_order": ["generate"]}
    base = f"/api/v1/content-projects/{project_id}/units/{unit_id}"
    assert client.post(f"{base}/workflow-override", headers=headers, json={"expected_revision": 0, "definition": definition}).status_code == 201
    before = runtime_config.get_runtime(runtime_config.KEY_LLM)
    try:
        runtime_config.set_runtime(runtime_config.KEY_LLM, {"provider": "openai_compatible", "model": "different-model", "base_url": "https://example.invalid", "api_key": "test"})
        response = client.post(f"{base}/runs", headers=headers, json={"params": {}})
        assert response.status_code == 409
        assert "Provider/Model" in response.text
        assert client.get(f"{base}/runs", headers=headers).json() == []
    finally:
        if before is None:
            runtime_config.clear_runtime(runtime_config.KEY_LLM)
        else:
            runtime_config.set_runtime(runtime_config.KEY_LLM, before)


def test_ai_runtime_change_also_blocks_node_rerun(client):
    from app import runtime_config

    headers, _, project_id, unit_id = _setup(client)
    choice = client.get("/api/v1/workflow-execution-options", headers=headers).json()["ai"]["builtin.generate"]
    definition = {"nodes": [{"id": "generate", "kind": "AI", "plugin": "builtin.generate", "config": {"provider": choice["provider"], "model": choice["model"]}}], "edges": [], "visual_order": ["generate"]}
    base = f"/api/v1/content-projects/{project_id}/units/{unit_id}"
    assert client.post(f"{base}/workflow-override", headers=headers, json={"expected_revision": 0, "definition": definition}).status_code == 201
    first = client.post(f"{base}/runs", headers=headers, json={"params": {}}).json()
    assert first["status"] == "failed"
    before = runtime_config.get_runtime(runtime_config.KEY_LLM)
    try:
        runtime_config.set_runtime(runtime_config.KEY_LLM, {"provider": "openai_compatible", "model": "different-model", "base_url": "https://example.invalid", "api_key": "test"})
        rerun = client.post(f"{base}/runs/{first['id']}/nodes/generate/rerun", headers=headers)
        assert rerun.status_code == 200
        assert "Provider/Model" in rerun.json()["steps"][0]["error"]
    finally:
        if before is None:
            runtime_config.clear_runtime(runtime_config.KEY_LLM)
        else:
            runtime_config.set_runtime(runtime_config.KEY_LLM, before)


def test_persona_default_portability_and_old_unit_pin(client, db_session):
    headers, persona_id, project_id, unit_id = _setup(client)
    path = f"/api/v1/content-personas/{persona_id}/default-workflows/text"
    bad = _definition()
    bad["nodes"][0]["config"] = {"snapshot_id": 42}
    assert client.post(path, headers=headers, json={"expected_revision": 0, "definition": bad, "source_project_id": project_id, "source_unit_id": unit_id}).status_code == 422
    assert client.get(path, headers=headers).json()["revision"] == 0
    portable = {"nodes": [{"id": "rule", "kind": "Rule", "plugin": "builtin.fact_check", "config": {"project_id": project_id}}], "edges": [], "visual_order": ["rule"]}
    good = client.post(path, headers=headers, json={"expected_revision": 0, "definition": portable, "source_project_id": project_id, "source_unit_id": unit_id})
    assert good.status_code == 201, good.text
    assert good.json()["definition"]["nodes"][0]["config"]["project_id"] == {"$context": "project.id"}
    assert db_session.get(ContentUnit, unit_id).pinned_workflow_id is None
    later = client.post(f"/api/v1/content-projects/{project_id}/units", headers=headers, json={"title": "第二条", "persona_id": persona_id, "modality": "text"})
    assert later.json()["pinned_workflow_id"] == good.json()["workflow_id"]
    assert client.post(path, headers=headers, json={"expected_revision": 0, "definition": portable, "source_project_id": project_id, "source_unit_id": unit_id}).status_code == 409


def test_old_unit_effective_workflow_remains_pinned_after_default_advances(client):
    headers, persona_id, project_id, _ = _setup(client)
    default_path = f"/api/v1/content-personas/{persona_id}/default-workflows/text"
    first_definition = {"nodes": [{"id": "gate", "kind": "Human", "plugin": "builtin.approve", "config": {}}], "edges": [], "visual_order": ["gate"]}
    first_response = client.post(default_path, headers=headers, json={"expected_revision": 0, "definition": first_definition})
    assert first_response.status_code == 201, first_response.text
    first = first_response.json()
    unit = client.post(f"/api/v1/content-projects/{project_id}/units", headers=headers, json={"title": "Pinned", "persona_id": persona_id, "modality": "text"}).json()
    second_definition = {**first_definition, "nodes": [{**first_definition["nodes"][0], "label": "new"}]}
    second_response = client.post(default_path, headers=headers, json={"expected_revision": 1, "definition": second_definition})
    assert second_response.status_code == 201, second_response.text
    second = second_response.json()
    assert first["workflow_id"] != second["workflow_id"]
    base = f"/api/v1/content-projects/{project_id}/units/{unit['id']}"
    effective = client.get(f"{base}/effective-workflow", headers=headers)
    assert effective.status_code == 200
    assert effective.json()["workflow_id"] == first["workflow_id"]
    assert effective.json()["definition"] == first["definition"]
    assert effective.json()["source"] == "persona_default"
    assert client.get(f"{base}/effective-workflow", headers={"X-Studio-User": "other@studio.local"}).status_code == 404
    started = client.post(f"{base}/runs", headers=headers, json={"params": {}})
    assert started.status_code == 201, started.text
    assert started.json()["workflow_id"] == first["workflow_id"]


def test_role_default_rejects_bound_values_outside_runtime_config(client):
    headers, persona_id, project_id, unit_id = _setup(client)
    path = f"/api/v1/content-personas/{persona_id}/default-workflows/text"
    for field, value in (("input_mapping", {"metadata": {"project_id": project_id}}), ("condition", {"input": "x", "equals": {"unit_id": unit_id}})):
        definition = _definition()
        definition["nodes"][0]["config"] = {}
        definition["nodes"][0][field] = value
        if field == "condition":
            definition["nodes"][0]["input_mapping"] = {"x": 1}
        response = client.post(path, headers=headers, json={"expected_revision": 0, "definition": definition, "source_project_id": project_id, "source_unit_id": unit_id})
        assert response.status_code == 422, (field, response.text)
        assert "项目绑定值" in response.text, (field, response.text)
    assert client.get(path, headers=headers).json()["revision"] == 0


def test_project_run_uses_existing_engine_and_records_attempt(client, db_session):
    headers, _, project_id, unit_id = _setup(client)
    bob = {"X-Studio-User": "other@studio.local"}
    definition = {"nodes": [{"id": "constant", "kind": "System", "plugin": "system.constant", "config": {"value": {"text": "real result"}}}], "edges": [], "visual_order": ["constant"]}
    save = client.post(f"/api/v1/content-projects/{project_id}/units/{unit_id}/workflow-override", headers=headers, json={"expected_revision": 0, "definition": definition})
    assert save.status_code == 201, save.text
    path = f"/api/v1/content-projects/{project_id}/units/{unit_id}/runs"
    started = client.post(path, headers=headers, json={"params": {}})
    assert started.status_code == 201, started.text
    run_id = started.json()["id"]
    assert started.json()["status"] == "succeeded"
    assert started.json()["steps"][0]["output"] == {"text": "real result"}
    assert started.json()["definition_checksum"] == save.json()["definition_checksum"]
    assert client.get(f"{path}/{run_id}", headers=bob).status_code == 404
    attempts = client.get(f"{path}/{run_id}/nodes/constant/attempts", headers=headers)
    assert attempts.status_code == 200
    assert attempts.json()[0]["output_json"] == {"text": "real result"}
    rerun = client.post(f"{path}/{run_id}/nodes/constant/rerun", headers=headers)
    assert rerun.status_code == 200, rerun.text
    assert len(client.get(f"{path}/{run_id}/nodes/constant/attempts", headers=headers).json()) == 2


def test_step_kind_and_failed_rerun_does_not_reuse_prior_output(client, monkeypatch):
    from app.services import workflow_engine

    headers, _, project_id, unit_id = _setup(client)
    base = f"/api/v1/content-projects/{project_id}/units/{unit_id}"
    definition = {"nodes": [{"id": "constant", "kind": "System", "plugin": "system.constant", "config": {"value": {"text": "old"}}}], "edges": [], "visual_order": ["constant"]}
    assert client.post(f"{base}/workflow-override", headers=headers, json={"expected_revision": 0, "definition": definition}).status_code == 201
    run = client.post(f"{base}/runs", headers=headers, json={"params": {}}).json()
    assert run["steps"][0]["node_type"] == "System"

    def fail(*_args):
        raise ValueError("rerun failed")

    monkeypatch.setattr(workflow_engine, "_execute_node", fail)
    rerun = client.post(f"{base}/runs/{run['id']}/nodes/constant/rerun", headers=headers)
    assert rerun.status_code == 200, rerun.text
    assert rerun.json()["steps"][0]["output"] == {}
    attempts = client.get(f"{base}/runs/{run['id']}/nodes/constant/attempts", headers=headers).json()
    assert [(item["status"], item["output_json"]) for item in attempts] == [("succeeded", {"text": "old"}), ("failed", {})]


def test_condition_and_failure_policy_are_not_silent(client):
    headers, _, project_id, unit_id = _setup(client)
    base = f"/api/v1/content-projects/{project_id}/units/{unit_id}"
    definition = {
        "nodes": [
            {"id": "source", "kind": "System", "plugin": "system.constant", "config": {"value": {"flag": False}}},
            {"id": "conditional", "kind": "System", "plugin": "system.constant", "config": {"value": {"ran": True}}, "input_mapping": {"flag": {"node_id": "source", "output": "flag"}}, "condition": {"input": "flag", "equals": True}},
            {"id": "child", "kind": "System", "plugin": "system.constant", "config": {"value": {"ran": True}}},
        ],
        "edges": [{"from": "source", "to": "conditional"}, {"from": "conditional", "to": "child"}],
        "visual_order": ["source", "conditional", "child"],
    }
    assert client.post(f"{base}/workflow-override", headers=headers, json={"expected_revision": 0, "definition": definition}).status_code == 201
    run = client.post(f"{base}/runs", headers=headers, json={"params": {}}).json()
    assert run["status"] == "succeeded"
    assert {step["node_id"]: step["status"] for step in run["steps"]} == {"source": "succeeded", "conditional": "skipped", "child": "skipped"}

    failing = {"nodes": [{"id": "fallback", "kind": "System", "plugin": "system.constant", "config": {}, "failure_policy": "wait_human"}], "edges": [], "visual_order": ["fallback"]}
    assert client.post(f"{base}/workflow-override", headers=headers, json={"expected_revision": 1, "definition": failing}).status_code == 201
    waiting = client.post(f"{base}/runs", headers=headers, json={"params": {}}).json()
    assert waiting["status"] == "waiting_input"
    completed = client.post(f"{base}/runs/{waiting['id']}/nodes/fallback/complete", headers=headers, json={"payload": {"action": "skip"}})
    assert completed.status_code == 200
    assert completed.json()["status"] == "succeeded"


def test_output_mapping_and_historical_run_checksum(client):
    headers, _, project_id, unit_id = _setup(client)
    base = f"/api/v1/content-projects/{project_id}/units/{unit_id}"
    first = {"nodes": [{"id": "a", "kind": "System", "plugin": "system.constant", "config": {"value": {"value": 1}}, "output_mapping": {"alias": "value"}}], "edges": [], "visual_order": ["a"]}
    saved = client.post(f"{base}/workflow-override", headers=headers, json={"expected_revision": 0, "definition": first}).json()
    old = client.post(f"{base}/runs", headers=headers, json={"params": {}}).json()
    assert old["steps"][0]["output"]["alias"] == 1
    second = {"nodes": [{"id": "a", "kind": "System", "plugin": "system.constant", "config": {"value": {"value": 2}}}], "edges": [], "visual_order": ["a"]}
    latest = client.post(f"{base}/workflow-override", headers=headers, json={"expected_revision": 1, "definition": second}).json()
    assert latest["definition_checksum"] != saved["definition_checksum"]
    reread = client.get(f"{base}/runs/{old['id']}", headers=headers).json()
    assert reread["definition_checksum"] == saved["definition_checksum"]
    assert reread["definition"]["nodes"][0]["config"]["value"]["value"] == 1


def test_side_effect_node_cannot_generic_rerun(client, db_session):
    from app.models import WorkflowRun, WorkflowStep

    headers, _, project_id, unit_id = _setup(client)
    workflow = Workflow(name="legacy side effect", workflow_key="project.side-effect", version=1, status="published", definition_json={"nodes": [{"id": "deliver", "kind": "Tool", "plugin": "builtin.publish_wechat", "config": {}}], "edges": [], "visual_order": ["deliver"]}, owner_user_id=1, scope="project")
    db_session.add(workflow)
    db_session.flush()
    run = WorkflowRun(workflow_id=workflow.id, content_unit_id=unit_id, status="succeeded", context_json={}, params_json={})
    db_session.add(run)
    db_session.flush()
    db_session.add(WorkflowStep(run_id=run.id, node_id="deliver", node_type="Tool", plugin_key="builtin.publish_wechat", plugin_version="1", status="succeeded", params_json={}, output_json={}))
    db_session.commit()
    response = client.post(f"/api/v1/content-projects/{project_id}/units/{unit_id}/runs/{run.id}/nodes/deliver/rerun", headers=headers)
    assert response.status_code == 409
    assert db_session.get(WorkflowRun, run.id).status == "succeeded"
