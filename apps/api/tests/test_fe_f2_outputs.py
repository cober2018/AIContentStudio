"""Only verified workflow-produced revisions enter the owning project pool."""

import hashlib

from app.models import Material, MaterialRevision, ProjectWorkflowOutput, WorkflowRun, WorkflowStep, WorkflowStepAttempt
from app.services.project_outputs import associate_step_output


def test_project_shared_asset_links_existing_revision_and_attempt(client, db_session, tmp_path):
    alice = {"X-Studio-User": "asset@studio.local"}
    bob = {"X-Studio-User": "other@studio.local"}
    persona_id = client.post("/api/v1/content-personas", json={"name": "设计师"}, headers=alice).json()["id"]
    project_id = client.post("/api/v1/content-projects", json={"title": "视觉项目"}, headers=alice).json()["id"]
    unit_id = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "图文", "persona_id": persona_id, "modality": "graphic"}, headers=alice).json()["id"]
    from app.models import Workflow

    workflow = Workflow(name="cover", workflow_key="project.cover", version=1, status="published", definition_json={"nodes": [], "edges": []}, checksum="checksum", owner_user_id=1, scope="project")
    db_session.add(workflow)
    db_session.flush()
    run = WorkflowRun(workflow_id=workflow.id, content_unit_id=unit_id, status="succeeded", context_json={}, params_json={}, definition_checksum="checksum")
    db_session.add(run)
    db_session.flush()
    material = Material(kind="screenshot", title="实际生成图", status="active")
    db_session.add(material)
    db_session.flush()
    content = b"\x89PNG\r\n\x1a\n" + b"actual-bytes"
    file_path = tmp_path / "actual.png"
    file_path.write_bytes(content)
    revision = MaterialRevision(material_id=material.id, revision_no=1, content_hash=hashlib.sha256(content).hexdigest(), file_path=str(file_path), mime_type="image/png", source_kind="ai_generated", rights_status="review_required", public_use_allowed=False)
    db_session.add(revision)
    db_session.flush()
    step = WorkflowStep(run_id=run.id, node_id="cover", node_type="AI", plugin_key="media.screenshot", status="succeeded", params_json={}, output_json={"generated": True, "material_revision_id": revision.id})
    db_session.add(step)
    db_session.flush()
    attempt = WorkflowStepAttempt(step_id=step.id, run_id=run.id, node_id="cover", plugin_key=step.plugin_key, attempt_no=1, status="succeeded", output_json=step.output_json)
    db_session.add(attempt)
    db_session.flush()
    assert associate_step_output(db_session, run, step, attempt.id) is not None
    db_session.commit()
    assets = client.get(f"/api/v1/content-projects/{project_id}/shared-assets", headers=alice)
    assert assets.status_code == 200
    assert assets.json()[0]["material_revision_id"] == revision.id
    assert assets.json()[0]["attempt_id"] == attempt.id
    assert assets.json()[0]["rights_status"] == "review_required"
    reference = client.post(f"/api/v1/content-projects/{project_id}/materials/references", json={"material_revision_id": revision.id}, headers=alice)
    assert reference.status_code == 201, reference.text
    combined = client.get(f"/api/v1/content-projects/{project_id}/shared-assets", headers=alice).json()
    assert {item["source_type"] for item in combined} == {"workflow", "system_reference"}
    assert {item["material_revision_id"] for item in combined} == {revision.id}
    assert len({item["key"] for item in combined}) == 2
    assert db_session.query(MaterialRevision).count() == 1
    assert client.get(f"/api/v1/content-projects/{project_id}/shared-assets", headers=bob).status_code == 404


def test_system_constant_cannot_fabricate_asset_association(db_session):
    workflow = __import__("app.models", fromlist=["Workflow"]).Workflow(name="constant", definition_json={"nodes": [], "edges": []})
    db_session.add(workflow)
    db_session.flush()
    run = WorkflowRun(workflow_id=workflow.id, status="succeeded", context_json={}, params_json={})
    db_session.add(run)
    db_session.flush()
    step = WorkflowStep(run_id=run.id, node_id="a", node_type="System", plugin_key="system.constant", output_json={"material_revision_id": 42}, params_json={})
    db_session.add(step)
    db_session.flush()
    assert associate_step_output(db_session, run, step, 1) is None
    assert db_session.query(ProjectWorkflowOutput).count() == 0


def test_missing_media_bytes_cannot_enter_project_asset_pool(client, db_session, tmp_path):
    from app.models import Workflow

    headers = {"X-Studio-User": "missing-media@studio.local"}
    persona_id = client.post("/api/v1/content-personas", json={"name": "设计师"}, headers=headers).json()["id"]
    project_id = client.post("/api/v1/content-projects", json={"title": "空素材"}, headers=headers).json()["id"]
    unit_id = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "图文", "persona_id": persona_id, "modality": "graphic"}, headers=headers).json()["id"]
    workflow = Workflow(name="cover", workflow_key="project.missing-cover", version=1, status="published", definition_json={"nodes": [], "edges": []}, checksum="checksum", owner_user_id=1, scope="project")
    db_session.add(workflow)
    db_session.flush()
    run = WorkflowRun(workflow_id=workflow.id, content_unit_id=unit_id, status="succeeded", context_json={}, params_json={})
    db_session.add(run)
    db_session.flush()
    material = Material(kind="screenshot", title="丢失文件", status="active")
    db_session.add(material)
    db_session.flush()
    revision = MaterialRevision(material_id=material.id, revision_no=1, content_hash=hashlib.sha256(b"missing").hexdigest(), file_path=str(tmp_path / "not-found.png"), mime_type="image/png", source_kind="ai_generated", rights_status="review_required", public_use_allowed=False)
    db_session.add(revision)
    db_session.flush()
    step = WorkflowStep(run_id=run.id, node_id="cover", node_type="AI", plugin_key="media.screenshot", status="succeeded", params_json={}, output_json={"generated": True, "material_revision_id": revision.id})
    db_session.add(step)
    db_session.flush()
    assert associate_step_output(db_session, run, step, 1) is None


