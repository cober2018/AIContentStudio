"""Real adapter and manual-render boundaries, without a renderer mock."""

import hashlib

import pytest

from app.models import (
    ChannelTemplateVersion,
    FactPack,
    FactPackItem,
    Material,
    MaterialRevision,
    ProjectMaterialReference,
)

HEADERS = {"X-Studio-User": "adapter@studio.local"}


def _unit(client, db, modality, *, suffix=""):
    channel = "wechat" if modality == "text" else f"fixture_{modality}{suffix}"
    form = "article" if modality == "text" else "final"
    if modality != "text":
        db.add(ChannelTemplateVersion(channel=channel, version=1, name="明确配置的测试渠道", status="published", profile_json={"content_forms": {form: {"artifact_kind": "image" if modality == "graphic" else "video"}}}))
        db.commit()
    persona = client.post("/api/v1/content-personas", json={"name": "作者"}, headers=HEADERS).json()["id"]
    project = client.post("/api/v1/content-projects", json={"title": "生产项目"}, headers=HEADERS).json()["id"]
    response = client.post(f"/api/v1/content-projects/{project}/units", json={"title": "成品", "persona_id": persona, "modality": modality, "channel_id": channel}, headers=HEADERS)
    assert response.status_code == 201, response.text
    unit = response.json()["id"]
    client.post(f"/api/v1/content-projects/{project}/brief/revisions", json={"objective": "明确目标", "expected_revision": 0}, headers=HEADERS)
    pack = FactPack(name=f"冻结边界{suffix}", version=1, status="frozen", checksum="p" * 64)
    db.add(pack)
    db.flush()
    db.add(FactPackItem(fact_pack_id=pack.id, evidence_kind="author_opinion", snapshot_json={"statement": "观点"}, snapshot_checksum="s" * 64, public_use_allowed=True))
    db.commit()
    response = client.post(f"/api/v1/content-projects/{project}/fact-boundary", json={"fact_pack_id": pack.id, "expected_revision": 0}, headers=HEADERS)
    assert response.status_code == 201, response.text
    return project, f"/api/v1/content-projects/{project}/units/{unit}/master-revisions"


def _render_material(db, project, tmp_path, modality, name="render"):
    content = b"\x89PNG\r\n\x1a\nexact image bytes" if modality == "graphic" else b"\x00\x00\x00\x18ftypmp42exact video bytes"
    file = tmp_path / name
    file.write_bytes(content)
    material = Material(title=name, kind="image" if modality == "graphic" else "video", status="active")
    db.add(material)
    db.flush()
    revision = MaterialRevision(material_id=material.id, content_hash=hashlib.sha256(content).hexdigest(), file_path=str(file), mime_type="image/png" if modality == "graphic" else "video/mp4", status="active", public_use_allowed=True, rights_status="cleared")
    db.add(revision)
    db.flush()
    db.add(ProjectMaterialReference(project_id=project, material_revision_id=revision.id, origin="system_library", status="active"))
    db.commit()
    return revision


def _draft_render(client, db, tmp_path, modality):
    project, path = _unit(client, db, modality)
    material = _render_material(db, project, tmp_path, modality)
    payload = {"canvases": [{"id": "canvas-a", "order": 0}]} if modality == "graphic" else {"script": "口播", "shots": [{"id": "shot-a", "order": 0}], "timeline": {}}
    payload["render_asset_ref"] = {"material_revision_id": material.id, **({"canvas_id": "canvas-a"} if modality == "graphic" else {})}
    body = {"idempotency_key": "draft", "payload": payload, "asset_refs": [{"material_revision_id": material.id, "content_hash": material.content_hash, "role": "render_output"}]}
    response = client.post(path, json=body, headers=HEADERS)
    assert response.status_code == 200, response.text
    readiness = client.get(f"{path}/{response.json()['id']}/readiness", headers=HEADERS)
    assert readiness.status_code == 200, readiness.text
    return path, body, readiness.json(), material


@pytest.mark.parametrize("modality", ["text", "graphic", "video"])
def test_registered_adapter_has_complete_contract(modality):
    from app.services import production_modalities

    factory = getattr(production_modalities, "adapter_for", None)
    assert callable(factory), "adapter registry missing"
    adapter = factory(modality, f"{modality}.master.v1")
    for name in ("validate_payload", "build_preview", "build_render_snapshot", "build_package_projection", "freeze_availability"):
        assert callable(getattr(adapter, name, None)), name
    assert set(adapter.required_check_kinds) == {"master_schema", "evidence", "rights", "render"}


def test_text_adapter_builds_truthful_deterministic_render(client, db_session):
    _, path = _unit(client, db_session, "text")
    response = client.post(path, json={"idempotency_key": "manual-text", "payload": {"title": "手工标题", "markdown": "真实手工正文"}}, headers=HEADERS)
    saved = response.json()
    response = client.get(f"{path}/{saved['id']}/readiness", headers=HEADERS)
    assert response.status_code == 200, response.text
    render = response.json()["render"]
    assert render["status"] == "ready"
    assert render["origin"] == "deterministic"
    assert render["content_hash"] == hashlib.sha256("真实手工正文".encode()).hexdigest()
    assert render["render_input_hash"] == response.json()["render_input_hash"]


@pytest.mark.parametrize("modality", ["graphic", "video"])
def test_exact_manual_render_confirmation_is_append_only_and_packageable(client, db_session, tmp_path, modality):
    from app.models import ContentMasterRevision
    from app.services import production_modalities

    path, body, readiness, material = _draft_render(client, db_session, tmp_path, modality)
    assert readiness["render"]["status"] == "incomplete"
    confirmed = client.post(path, json={**body, "idempotency_key": "confirmed", "expected_revision": 1, "render_attestation": {"confirmed": True, "render_input_hash": readiness["render_input_hash"]}}, headers=HEADERS)
    assert confirmed.status_code == 200, confirmed.text
    current = client.get(f"{path}/{confirmed.json()['id']}/readiness", headers=HEADERS).json()
    assert current["render"]["status"] == "ready"
    assert current["render"]["origin"] == "manual"
    assert current["render"]["attested_by"] == HEADERS["X-Studio-User"]
    assert current["render_input_hash"] == readiness["render_input_hash"]
    checks = client.post(f"{path}/{confirmed.json()['id']}/checks", headers=HEADERS).json()["items"]
    assert next(item for item in checks if item["check_kind"] == "render")["status"] == "pass"
    old = client.get(f"{path}/1/readiness", headers=HEADERS).json()
    assert old["render"]["status"] == "incomplete"
    adapter = production_modalities.adapter_for(modality)
    master = db_session.get(ContentMasterRevision, confirmed.json()["id"])
    package = adapter.build_package_projection(db_session, master)
    assert package["material_outputs"][0]["material_revision_id"] == material.id
    assert "file_path" not in str(package)


@pytest.mark.parametrize("change", ["payload", "context", "asset_set", "evidence_set", "forged_actor", "bytes", "mime", "rights", "canvas_coverage"])
def test_render_binding_cannot_be_reused_for_changed_or_unverified_inputs(client, db_session, tmp_path, change):
    path, body, readiness, material = _draft_render(client, db_session, tmp_path, "graphic")
    attestation = {"confirmed": True, "render_input_hash": readiness["render_input_hash"]}
    if change == "payload":
        body["payload"]["title"] = "内容已变"
    elif change == "context":
        project = path.split("/")[4]
        client.post(f"/api/v1/content-projects/{project}/brief/revisions", json={"expected_revision": 1, "objective": "新目标"}, headers=HEADERS)
    elif change == "asset_set":
        body["asset_refs"].append({"material_revision_id": material.id, "content_hash": material.content_hash, "role": "inline"})
    elif change == "evidence_set":
        item = db_session.query(FactPackItem).one()
        body["evidence_refs"] = [{"fact_pack_item_id": item.id, "snapshot_checksum": item.snapshot_checksum}]
    elif change == "forged_actor":
        body["edit_summary"] = {"render_attestation": {"origin": "manual", "render_input_hash": readiness["render_input_hash"], "attested_by": "forged"}}
        attestation = None
    elif change == "bytes":
        from pathlib import Path

        Path(material.file_path).write_bytes(b"replaced bytes")
    elif change == "mime":
        material.mime_type = "video/mp4"
        db_session.commit()
    elif change == "rights":
        material.public_use_allowed = False
        db_session.commit()
    elif change == "canvas_coverage":
        body["payload"]["canvases"].append({"id": "canvas-b", "order": 1})
        saved = client.post(path, json={**body, "idempotency_key": "multi-draft", "expected_revision": 1}, headers=HEADERS).json()
        readiness = client.get(f"{path}/{saved['id']}/readiness", headers=HEADERS).json()
        attestation["render_input_hash"] = readiness["render_input_hash"]
        body["expected_revision"] = 2
    response = client.post(path, json={**body, "idempotency_key": "bad-confirmation", "expected_revision": body.get("expected_revision", 1), "render_attestation": attestation}, headers=HEADERS)
    assert response.status_code == 422, response.text


def test_render_ready_does_not_invent_channel_modality_support(client, db_session, tmp_path):
    from app.models import ContentUnit

    path, body, _readiness, _ = _draft_render(client, db_session, tmp_path, "graphic")
    unit = db_session.get(ContentUnit, int(path.split("/")[6]))
    unit.channel_id = "wechat"
    db_session.commit()
    response = client.post(path, json={**body, "idempotency_key": "unsupported", "expected_revision": 1}, headers=HEADERS)
    assert response.status_code == 200, response.text
    projected = client.get(f"{path}/{response.json()['id']}/readiness", headers=HEADERS).json()
    assert projected["adapter_availability"]["available"] is False
    assert "unsupported_channel_modality" in projected["adapter_availability"]["reasons"]


def test_all_canvases_have_exact_outputs_and_revocation_invalidates_render(client, db_session, tmp_path):
    from app.models import ContentMasterRevision
    from app.services.production_modalities import adapter_for

    path, body, _, first = _draft_render(client, db_session, tmp_path, "graphic")
    second = _render_material(db_session, int(path.split("/")[4]), tmp_path, "graphic", "second")
    body["payload"]["canvases"].append({"id": "canvas-b", "order": 1})
    body["payload"]["render_asset_ref"] = [{"material_revision_id": first.id, "canvas_id": "canvas-a"}, {"material_revision_id": second.id, "canvas_id": "canvas-b"}]
    body["asset_refs"].append({"material_revision_id": second.id, "content_hash": second.content_hash, "role": "render_output", "sort_order": 1})
    saved = client.post(path, json={**body, "idempotency_key": "two-canvases", "expected_revision": 1}, headers=HEADERS).json()
    projected = client.get(f"{path}/{saved['id']}/readiness", headers=HEADERS).json()
    confirmed = client.post(path, json={**body, "idempotency_key": "two-confirmed", "expected_revision": 2, "render_attestation": {"confirmed": True, "render_input_hash": projected["render_input_hash"]}}, headers=HEADERS)
    assert confirmed.status_code == 200, confirmed.text
    master = db_session.get(ContentMasterRevision, confirmed.json()["id"])
    adapter = adapter_for("graphic")
    assert len(adapter.build_render_snapshot(db_session, master)["outputs"]) == 2
    assert len(adapter.build_package_projection(db_session, master)["material_outputs"]) == 2
    client.post(f"{path}/{master.id}/checks", headers=HEADERS)
    second.public_use_allowed = False
    db_session.commit()
    projected = client.get(f"{path}/{master.id}/readiness", headers=HEADERS).json()
    assert projected["render"]["status"] == "incomplete"
    assert projected["candidate_freeze_available"] is False
    assert next(check for check in projected["checks"] if check["check_kind"] == "render")["status"] == "stale"


@pytest.mark.parametrize("modality,payload", [("graphic", {"canvases": ["bad"]}), ("graphic", {"canvases": [{"id": []}]}), ("graphic", {"canvases": [{"id": "same"}, {"id": "same"}]}), ("video", {"shots": [{"id": "s", "order": -1}]}), ("video", {"shots": [{"id": "s"}, {"id": "s"}]}), ("text", {"title": {}, "markdown": "内容"}), ("text", {"markdown": "内容", "structured": "bad"})])
def test_adapter_rejects_invalid_stable_envelopes_before_storage(client, db_session, modality, payload):
    _, path = _unit(client, db_session, modality)
    response = client.post(path, json={"idempotency_key": "invalid", "payload": payload}, headers=HEADERS)
    assert response.status_code == 422, response.text


def test_check_profile_tracks_actual_adapter_version(client, db_session, monkeypatch):
    from app.models import ContentMasterCheckRun
    from app.services.production_modalities import adapter_for

    _, path = _unit(client, db_session, "text")
    saved = client.post(path, json={"idempotency_key": "version", "payload": {"markdown": "内容"}}, headers=HEADERS).json()
    client.post(f"{path}/{saved['id']}/checks", headers=HEADERS)
    monkeypatch.setattr(adapter_for("text", "text.master.v1"), "version", "2")
    checks = client.get(f"{path}/{saved['id']}/checks/current", headers=HEADERS).json()["items"]
    assert all(check["status"] == "stale" for check in checks)
    client.post(f"{path}/{saved['id']}/checks", headers=HEADERS)
    checks = client.get(f"{path}/{saved['id']}/checks/current", headers=HEADERS).json()["items"]
    assert all(check["status"] == "pass" and check["is_current"] for check in checks)
    assert all(db_session.get(ContentMasterCheckRun, check["id"]).profile_version == "2" for check in checks)


@pytest.mark.parametrize("declaration", [{"material_revision_id": 1, "canvas_id": []}, {"material_revision_id": True, "canvas_id": "canvas-a"}])
def test_malformed_render_declaration_fails_closed(client, db_session, tmp_path, declaration):
    path, body, _, _ = _draft_render(client, db_session, tmp_path, "graphic")
    body["payload"]["render_asset_ref"] = declaration
    draft = client.post(path, json={**body, "idempotency_key": "bad-shape", "expected_revision": 1}, headers=HEADERS)
    assert draft.status_code == 422, draft.text


def test_empty_video_shell_cannot_become_ready_even_with_real_bytes(client, db_session, tmp_path):
    path, body, _, _ = _draft_render(client, db_session, tmp_path, "video")
    body["payload"] = {"shots": [], "timeline": {}, "render_asset_ref": body["payload"]["render_asset_ref"]}
    saved = client.post(path, json={**body, "idempotency_key": "empty-shell", "expected_revision": 1}, headers=HEADERS)
    assert saved.status_code == 200, saved.text
    projected = client.get(f"{path}/{saved.json()['id']}/readiness", headers=HEADERS).json()
    confirmed = client.post(path, json={**body, "idempotency_key": "empty-confirmed", "expected_revision": 2, "render_attestation": {"confirmed": True, "render_input_hash": projected["render_input_hash"]}}, headers=HEADERS)
    assert confirmed.status_code == 422, confirmed.text
