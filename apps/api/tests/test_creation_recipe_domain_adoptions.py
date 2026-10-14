"""Domain stages keep exact receipts and require atomic, explicit adoption."""

import hashlib
import io
import json
from contextlib import contextmanager
from copy import deepcopy

import pytest
from PIL import Image
from sqlalchemy import event

from app.config import get_settings
from app.models import (
    ChannelVariantRevision,
    ContentMasterAssetRef,
    ContentMasterRevision,
    CreativeExecution,
    CreativeExecutionPackage,
    FactPack,
    FactPackItem,
    MaterialRevision,
    ProjectEvent,
    ProjectMaterialReference,
    ProjectWorkflowOutput,
    ProviderGenerationTask,
    WorkflowStep,
    WorkflowStepAttempt,
)
from app.seed import seed_v1_channel_profiles
from app.services.factpack_service import pack_snapshot_checksum, snapshot_checksum


@pytest.fixture(autouse=True)
def isolated_media(monkeypatch, tmp_path):
    from app import runtime_config
    from app.services import asset_media, provider_media

    for key, value in {
        "APP_ENV": "test", "MATERIAL_STORAGE_BACKEND": "local", "MINIO_ENABLED": "false",
        "AI_STUDIO_MEDIA_ROOT": str(tmp_path), "AICS_GENERATION_RECEIPT_KEY_ID": "stage-fixture",
        "AICS_GENERATION_RECEIPT_KEYS": json.dumps({"stage-fixture": "12" * 32}),
    }.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(runtime_config, "_OVERRIDES", {})
    monkeypatch.setattr(asset_media, "MEDIA_ROOT", tmp_path)
    monkeypatch.setattr(provider_media, "_cache", {})
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _flow(client, db, *, with_evidence=False):
    headers = {"X-Studio-User": "recipe-domain@studio.test"}
    persona = client.post("/api/v1/content-personas", headers=headers, json={"name": "阶段作者"}).json()["id"]
    project_id = client.post("/api/v1/content-projects", headers=headers, json={"title": "领域采用"}).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project_id}/units", headers=headers,
                      json={"title": "源文章", "persona_id": persona, "modality": "text", "channel_id": "x"})
    assert unit.status_code == 201, unit.text
    unit_id = unit.json()["id"]
    base = f"/api/v1/content-projects/{project_id}/units/{unit_id}"
    seed_v1_channel_profiles(db)
    pack = FactPack(name="Isolated empty boundary", version=1, status="frozen",
                    checksum=pack_snapshot_checksum([]))
    db.add(pack)
    db.flush()
    items = []
    if with_evidence:
        snapshot = {"schema_version": 1, "evidence_kind": "author_opinion", "statement": "原文保留。",
                    "public_use_allowed": True, "model_use_allowed": True}
        item = FactPackItem(fact_pack_id=pack.id, evidence_kind="author_opinion", snapshot_json=snapshot,
                           snapshot_checksum=snapshot_checksum(snapshot), public_use_allowed=True,
                           model_use_allowed=True)
        db.add(item)
        db.flush()
        items.append(item)
        pack.checksum = pack_snapshot_checksum(items)
    db.commit()
    project_base = f"/api/v1/content-projects/{project_id}"
    response = client.post(f"{project_base}/brief/revisions", headers=headers,
                           json={"objective": "核对精确阶段采用", "expected_revision": 0})
    assert response.status_code == 201, response.text
    response = client.post(f"{project_base}/fact-boundary", headers=headers,
                           json={"fact_pack_id": pack.id, "expected_revision": 0})
    assert response.status_code == 201, response.text
    payload = {"title": "源文章", "document": {"schema": "studio.text.document.v1", "blocks": [
        {"id": "b1", "type": "paragraph", "content": [{"text": "原文保留。", "marks": []}]},
    ], "citations": []}}
    if items:
        payload["document"]["citations"] = [{"id": "c1", "block_id": "b1", "start": 0, "end": 5,
            "fact_pack_item_id": items[0].id, "selected_text_hash": hashlib.sha256("原文保留。".encode()).hexdigest()}]
    response = client.post(f"{base}/master-revisions", headers=headers, json={
        "idempotency_key": "domain-source", "payload_schema": "text.master.v2",
        "content_form": "single", "payload": payload,
        "evidence_refs": [{"fact_pack_item_id": item.id, "snapshot_checksum": item.snapshot_checksum,
                           "role": "claim", "locator": {"citation_id": "c1", "block_id": "b1",
                               "start": 0, "end": 5,
                               "selected_text_hash": hashlib.sha256("原文保留。".encode()).hexdigest()}} for item in items],
    })
    assert response.status_code == 200, response.text
    return headers, project_id, unit_id, base, response.json()


def _execute(client, db, plugin, config, *, version="1", override=None, kind="Tool"):
    headers, project_id, unit_id, base, master = _flow(client, db, with_evidence=plugin == "stage.checks")
    schema = f"media.generate.stage.v{version}" if plugin == "media.generate" else f"{plugin}.v{version}"
    definition = {"nodes": [{"id": "domain", "kind": kind, "plugin": plugin,
        "plugin_version": version, "stage_schema": schema, "config": config}],
        "edges": [], "visual_order": ["domain"]}
    saved = client.post(f"{base}/workflow-override", headers=headers,
                        json={"expected_revision": 0, "definition": definition})
    assert saved.status_code == 201, saved.text
    run = client.post(f"{base}/runs", headers=headers, json={"params": {}})
    assert run.status_code == 201, run.text
    run_id = run.json()["id"]
    stage = f"{base}/creation-recipe/stages/domain"
    preview = client.post(f"{stage}/preview", headers=headers,
                          json={"run_id": run_id, "stage_override": override or {}})
    assert preview.status_code == 200, preview.text
    resolved = preview.json()
    assert resolved["ready"], resolved["blockers"]
    executed = client.post(f"{stage}/run", headers=headers, json={
        "run_id": run_id, "expected_resolution_hash": resolved["resolution_hash"],
        "stage_override": override or {}, "invocation_key": "domain-explicit",
    })
    assert executed.status_code == 200, executed.text
    execution = executed.json()
    assert execution["status"] == "waiting_input", json.dumps(execution, ensure_ascii=False)
    request = {"domain": execution["output"]["domain"], "run_id": run_id,
        "attempt_id": execution["attempt_id"], "expected_output_hash": execution["receipt"]["output_hash"],
        "expected_resolution_hash": resolved["resolution_hash"],
        "expected_context_hash": resolved["context_hash"], "adoption_key": "domain-adopt",
        "expected_revision": execution["output"]["result"].get("expected_revision", 0),
        "decision": "accepted"}
    return headers, project_id, unit_id, stage, master, resolved, execution, request


def _variant(client, db):
    flow = _execute(client, db, "stage.variant.adapt", {
        "variant_key": "stage-x", "channel_id": "x", "content_form": "single",
        "mode": "deterministic",
    }, kind="AI")
    request, result = flow[-1], flow[-2]["output"]["result"]
    request.update({key: result[key] for key in ("payload", "asset_refs", "evidence_refs")})
    return flow


def _professional(client, db):
    flow = _execute(client, db, "stage.professional.prepare", {
        "objective": "显式准备交接包", "prepare_execution": True,
        "executor_kind": "agent", "executor_key": "isolated-test-agent", "executor_version": "1",
        "output_kind": "image", "output_mime": "image/png", "output_role": "cover",
        "output_count": 1, "output_max_bytes": 4096,
    })
    request, result = flow[-1], flow[-2]["output"]["result"]
    request.update({key: result[key] for key in ("package_id", "execution_id")})
    return flow


def _reviewable_checks(client, db):
    flow = _execute(client, db, "stage.checks", {}, kind="Rule")
    checks = flow[-2]["output"]["result"]
    assert checks["checks_reviewable"]
    flow[-1]["warning_dispositions"] = {
        f"{row['id']}:{row['input_hash']}": "明确保留离线语义能力边界"
        for row in checks["checks"] if row["status"] == "warning"
    }
    return flow


def _adopt(client, flow, request=None):
    return client.post(f"{flow[3]}/accept-result", headers=flow[0], json=request or flow[-1])


def _assert_association(db, accepted, flow):
    target = accepted["accepted_target"]
    output = db.get(ProjectWorkflowOutput, accepted["project_output_id"])
    feedback = db.get(ProjectEvent, accepted["feedback_event_id"])
    assert output.entity_id == target["entity_id"]
    assert output.attempt_id == flow[-2]["attempt_id"]
    assert output.provenance_json["resolution_hash"] == flow[-3]["resolution_hash"]
    assert feedback.event_type == "creation_recipe.stage_feedback"
    assert feedback.payload_json["project_output_id"] == output.id
    assert feedback.payload_json["accepted_hash"] == target["accepted_hash"]


@contextmanager
def _feedback_write_failure(db):
    def fail_feedback(session, _flush_context, _instances):
        if any(isinstance(row, ProjectEvent) and row.event_type == "creation_recipe.stage_feedback"
               for row in session.new):
            raise RuntimeError("isolated feedback persistence failure")

    event.listen(db, "before_flush", fail_feedback)
    try:
        yield
    finally:
        event.remove(db, "before_flush", fail_feedback)


def test_variant_execution_is_proposal_then_exact_immutable_adoption(client, db_session):
    flow = _variant(client, db_session)
    assert db_session.query(ChannelVariantRevision).count() == 0
    assert db_session.query(ProjectWorkflowOutput).count() == 0
    attempt = db_session.get(WorkflowStepAttempt, flow[-2]["attempt_id"])
    original = deepcopy((attempt.output_json, attempt.execution_receipt_json))
    response = _adopt(client, flow)
    assert response.status_code == 200, response.text
    _assert_association(db_session, response.json(), flow)
    variant = db_session.get(ChannelVariantRevision, response.json()["accepted_target"]["entity_id"])
    assert variant.payload_json == flow[-1]["payload"]
    assert variant.source_master_revision_id == flow[4]["id"]
    replay = _adopt(client, flow)
    assert replay.status_code == 200 and replay.json()["project_output_id"] == response.json()["project_output_id"]
    assert db_session.query(ChannelVariantRevision).count() == 1
    assert (attempt.output_json, attempt.execution_receipt_json) == original
    changed = {**flow[-1], "adoption_key": "domain-adopt", "note": "不同采用请求"}
    conflict = _adopt(client, flow, changed)
    assert conflict.status_code == 409, conflict.text


def test_professional_stage_adopts_prepared_execution_without_dispatch(client, db_session):
    flow = _professional(client, db_session)
    assert db_session.query(CreativeExecutionPackage).count() == 1
    row = db_session.query(CreativeExecution).one()
    before = (row.state, row.dispatch_certainty, row.revision_no)
    assert before[0:2] == ("prepared", "not_dispatched")
    assert db_session.query(ProjectWorkflowOutput).count() == 0
    response = _adopt(client, flow)
    assert response.status_code == 200, response.text
    _assert_association(db_session, response.json(), flow)
    assert response.json()["accepted_target"]["output_kind"] == "creative_execution"
    db_session.refresh(row)
    assert (row.state, row.dispatch_certainty, row.revision_no) == before
    assert db_session.query(ContentMasterRevision).count() == 1
    assert db_session.query(MaterialRevision).count() == 0
    replay = _adopt(client, flow)
    assert replay.status_code == 200 and replay.json()["project_output_id"] == response.json()["project_output_id"]
    assert db_session.query(CreativeExecution).count() == 1


@pytest.mark.parametrize("domain", ["variant", "professional", "checks"])
def test_domain_feedback_failure_rolls_back_adoption_association(client, db_session, domain):
    prepare = {"variant": _variant, "professional": _professional, "checks": _reviewable_checks}
    flow = prepare[domain](client, db_session)
    attempt = db_session.get(WorkflowStepAttempt, flow[-2]["attempt_id"])
    original = deepcopy((attempt.output_json, attempt.execution_receipt_json))

    with _feedback_write_failure(db_session), pytest.raises(RuntimeError, match="isolated feedback persistence failure"):
        _adopt(client, flow)
    assert db_session.query(ProjectWorkflowOutput).count() == 0
    assert db_session.query(ProjectEvent).filter_by(event_type="creation_recipe.stage_feedback").count() == 0
    assert db_session.query(ChannelVariantRevision).count() == 0
    step = db_session.query(WorkflowStep).filter_by(run_id=flow[-1]["run_id"], node_id="domain").one()
    assert step.status == "waiting_input"
    db_session.refresh(attempt)
    assert (attempt.output_json, attempt.execution_receipt_json) == original
    retry = _adopt(client, flow)
    assert retry.status_code == 200, retry.text


def test_checks_warning_requires_exact_disposition_before_association(client, db_session):
    flow = _execute(client, db_session, "stage.checks", {}, kind="Rule")
    result = flow[-2]["output"]["result"]
    warnings = {f"{row['id']}:{row['input_hash']}": "人工保留离线语义能力边界"
                for row in result["checks"] if row["status"] == "warning"}
    assert warnings, result
    assert result["checks_reviewable"] and not result["checks_pass"]
    original = deepcopy(flow[-2]["output"])
    missing = _adopt(client, flow)
    assert missing.status_code == 409 and missing.json()["detail"]["code"] == "stage_check_warning_disposition_required"
    assert db_session.query(ProjectWorkflowOutput).count() == 0
    wrong = _adopt(client, flow, {**flow[-1], "warning_dispositions": {"foreign:hash": "不匹配的解释"}})
    assert wrong.status_code == 409
    accepted = _adopt(client, flow, {**flow[-1], "warning_dispositions": warnings})
    assert accepted.status_code == 200, accepted.text
    _assert_association(db_session, accepted.json(), flow)
    assert accepted.json()["accepted_target"]["warning_dispositions"] == warnings
    assert db_session.get(WorkflowStepAttempt, flow[-2]["attempt_id"]).output_json == original


@pytest.fixture
def image_provider(monkeypatch, db_session):
    from app.services import model_capability_routing
    from app.services.content_harness import providers
    from app.services.content_harness import registry as registry_module
    from app.services.content_harness.registry import PluginRegistry
    from app.services.media_dimensions import image_dimensions

    class ModelAdapter:
        key, version = "minimax.cli", "1"

        def binding_state(self, capability, binding):
            return {"runtime_hash": "a" * 64, "reason": None}

    class ImageProvider:
        key, version = "minimax.cli", "1"
        calls = []
        contents = []

        def runtime_fingerprint(self):
            return "a" * 64

        def durable_identity(self, model_id):
            return {"credential_epoch": "b" * 64, "protocol_version": "stage-fixture.v1"}

        def submit_task(self, request):
            self.calls.append(deepcopy(request))
            params = request["parameters"]
            stream = io.BytesIO()
            Image.new("RGB", image_dimensions(params["pixels"], params["aspect_ratio"]), "blue").save(stream, "PNG")
            self.contents.append(stream.getvalue())
            return providers.MediaOutput("succeeded", stream.getvalue(), "image/png")

    loaded = PluginRegistry()
    loaded._items = dict(registry_module.registry._items)
    loaded._descriptors = dict(registry_module.registry._descriptors)
    for kind in ("model_provider", "image_provider"):
        token = (kind, "minimax.cli", "1")
        loaded._items.pop(token, None)
        loaded._descriptors.pop(token, None)
    image = ImageProvider()
    loaded.register("model_provider", "minimax.cli", "1", ModelAdapter())
    loaded.register("image_provider", "minimax.cli", "1", image)
    monkeypatch.setattr(registry_module, "registry", loaded)
    monkeypatch.setattr(providers, "registry", loaded)
    model_capability_routing.save_configuration(db_session, {
        "profiles": {"fixture.image": {"declared_capabilities": ["image_generation"], "capability_bindings": {
            "image_generation": {"adapter_key": "minimax.cli", "adapter_version": "1", "model_id": "image-01",
                "base_url": "local://mmx", "credential_ref": "ISOLATED_IMAGE_KEY"}}}},
        "media_plugins": {}, "capability_routes": {"image_generation": []},
        "policies": {"limits": {"image_generation": {"max_items": 1, "max_pixels": 1048576, "timeout_seconds": 10}}},
    }, expected_revision=0, actor="isolated-fixture")
    return image


def _media(client, db, image_provider):
    flow = _execute(client, db, "media.generate", {
        "capability": "image_generation", "selected_profile": "fixture.image", "prompt": "原始有限图片要求",
        "items": 1, "pixels": 262144, "timeout_seconds": 10, "aspect_ratio": "1:1",
    }, version="3", override={"prompt": "本次明确图片要求", "aspect_ratio": "3:4"})
    task = db.get(ProviderGenerationTask, flow[-2]["output"]["result"]["task_id"])
    flow[-1].update(task_id=task.id, expected_revision=task.revision, expected_result_hash=task.result_hash,
        rights={"confirmed": True, "title": "Explicit fixture image", "license_code": "local-test-only",
            "license_evidence_hash": "c" * 64, "public_use_allowed": False, "model_use_allowed": False,
            "commercial_use_allowed": False})
    return flow, task


def test_media_v3_controls_bind_signed_task_and_adoption_without_master_binding(client, db_session, image_provider):
    from app.services import generation_tasks, materials

    flow, task = _media(client, db_session, image_provider)
    assert len(image_provider.calls) == 1
    assert image_provider.calls[0]["prompt"] == "本次明确图片要求"
    assert image_provider.calls[0]["parameters"]["aspect_ratio"] == "3:4"
    assert task.request_json["parameters"]["aspect_ratio"] == "3:4"
    assert task.request_json["stage_resolution_hash"] == flow[-3]["resolution_hash"]
    generation_tasks._verify(task)
    generation_tasks._verify_result_receipt(task)
    original = deepcopy((task.request_json, task.plan_json, task.receipt_signature))
    assert db_session.query(MaterialRevision).count() == 0
    response = _adopt(client, flow)
    assert response.status_code == 200, response.text
    _assert_association(db_session, response.json(), flow)
    material = db_session.get(MaterialRevision, response.json()["accepted_target"]["entity_id"])
    assert material.content_hash == hashlib.sha256(image_provider.contents[0]).hexdigest()
    assert materials.read_bytes_checked(db_session, material) == image_provider.contents[0]
    assert material.public_use_allowed is False and material.model_use_allowed is False
    assert db_session.query(ProjectMaterialReference).filter_by(material_revision_id=material.id).count() == 1
    assert db_session.query(ContentMasterAssetRef).count() == 0
    assert db_session.query(ContentMasterRevision).count() == 1
    assert (task.request_json, task.plan_json, task.receipt_signature) == original
    replay = _adopt(client, flow)
    assert replay.status_code == 200 and replay.json()["project_output_id"] == response.json()["project_output_id"]
    assert len(image_provider.calls) == 1 and db_session.query(MaterialRevision).count() == 1


@pytest.mark.parametrize("tamper", ["request_receipt", "result_receipt", "result_bytes"])
def test_media_receipt_tampering_cannot_adopt_any_material(client, db_session, image_provider, tamper):
    from app.services import generation_tasks

    flow, task = _media(client, db_session, image_provider)
    if tamper == "request_receipt":
        task.receipt_signature = "d" * 64
    elif tamper == "result_receipt":
        task.result_signature = "d" * 64
    else:
        storage = generation_tasks._storage()
        (storage.root / task.result_storage_key).write_bytes(b"modified result bytes")
    db_session.commit()
    response = _adopt(client, flow)
    assert response.status_code == 409, response.text
    assert db_session.query(MaterialRevision).count() == 0
    assert db_session.query(ProjectWorkflowOutput).count() == 0
    assert db_session.query(ContentMasterAssetRef).count() == 0
    assert len(image_provider.calls) == 1


def test_media_feedback_failure_rolls_back_material_and_project_link(client, db_session, image_provider):
    flow, task = _media(client, db_session, image_provider)
    original = deepcopy((task.state, task.revision, task.result_signature))
    with _feedback_write_failure(db_session), pytest.raises(RuntimeError, match="isolated feedback persistence failure"):
        _adopt(client, flow)
    assert db_session.query(MaterialRevision).count() == 0
    assert db_session.query(ProjectMaterialReference).count() == 0
    assert db_session.query(ProjectWorkflowOutput).count() == 0
    assert db_session.query(ProjectEvent).filter_by(event_type="creation_recipe.stage_feedback").count() == 0
    db_session.refresh(task)
    assert (task.state, task.revision, task.result_signature) == original
    assert task.accepted_material_revision_id is None
    db_session.expunge_all()
    response = _adopt(client, flow)
    assert response.status_code == 200, response.text
    _assert_association(db_session, response.json(), flow)
    assert len(image_provider.calls) == 1
