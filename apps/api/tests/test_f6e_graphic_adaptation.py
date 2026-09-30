"""F6E image notes must use the exact rendered images, not canvas prompts."""

import copy
import hashlib
import io
import json
import zipfile

from sqlalchemy import select

from app.models import (
    ChannelTemplateVersion,
    ChannelVariantRevision,
    FactPack,
    FactPackItem,
    Material,
    MaterialRevision,
    ProjectEvent,
    ProjectMaterialReference,
)
from app.seed import seed_v1_channel_profiles


def _source(client, db_session, tmp_path, *, attest=True, ready=False):
    seed_v1_channel_profiles(db_session)
    db_session.add(ChannelTemplateVersion(
        channel="graphic_f6e_source", version=1, name="Graphic source", status="published",
        profile_json={"content_forms": {"final": {"artifact_kind": "image"}}},
    ))
    db_session.commit()
    headers = {"X-Studio-User": "graphic-f6e@studio.local"}
    persona = client.post("/api/v1/content-personas", json={"name": "设计师"}, headers=headers).json()["id"]
    project = client.post("/api/v1/content-projects", json={"title": "图文渠道项目"}, headers=headers).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project}/units", json={
        "title": "一张封面", "persona_id": persona, "modality": "graphic", "channel_id": None if ready else "graphic_f6e_source",
    }, headers=headers).json()["id"]
    if ready:
        brief = client.post(f"/api/v1/content-projects/{project}/brief/revisions", json={
            "objective": "准确表达图文观点", "expected_revision": 0,
        }, headers=headers)
        assert brief.status_code == 201, brief.text
        pack = FactPack(name="图文事实边界", version=1, status="frozen", checksum="c" * 64)
        db_session.add(pack)
        db_session.flush()
        db_session.add(FactPackItem(fact_pack_id=pack.id, evidence_kind="author_opinion",
                                    snapshot_json={"statement": "视觉观点"}, snapshot_checksum="d" * 64,
                                    public_use_allowed=True, model_use_allowed=True))
        db_session.commit()
        boundary = client.post(f"/api/v1/content-projects/{project}/fact-boundary", json={
            "fact_pack_id": pack.id, "expected_revision": 0,
        }, headers=headers)
        assert boundary.status_code == 201, boundary.text
    content = b"\x89PNG\r\n\x1a\nreal rendered image bytes"
    file = tmp_path / "final.png"
    file.write_bytes(content)
    material = Material(title="成品图", kind="image", status="active")
    db_session.add(material)
    db_session.flush()
    revision = MaterialRevision(
        material_id=material.id, content_hash=hashlib.sha256(content).hexdigest(), file_path=str(file),
        mime_type="image/png", status="active", public_use_allowed=True, rights_status="cleared",
    )
    db_session.add(revision)
    db_session.flush()
    db_session.add(ProjectMaterialReference(project_id=project, material_revision_id=revision.id, origin="system_library", status="active"))
    db_session.commit()
    canvas = {"id": "cover", "order": 0, "width": 1080, "height": 1440, "background": {"color": "#ffffff"}, "layers": [
        {"id": "copy", "order": 0, "type": "text", "x": 10, "y": 20, "width": 400, "height": 80, "runs": [{"text": "有证据的视觉内容", "style": {"font_size": 30, "color": "#123456"}}]},
    ]}
    payload = {"title": "有证据的视觉内容", "canvases": [canvas]}
    asset_ref = {"material_revision_id": revision.id, "content_hash": revision.content_hash, "role": "render_output", "slot_key": "cover", "placement": {"canvas_id": "cover"}}
    master_path = f"/api/v1/content-projects/{project}/units/{unit}/master-revisions"
    draft = client.post(master_path, json={"idempotency_key": "graphic-draft", "payload_schema": "graphic.master.v2", "payload": payload, "asset_refs": [asset_ref]}, headers=headers)
    assert draft.status_code == 200, draft.text
    if not attest:
        return project, unit, draft.json(), revision, headers
    readiness = client.get(f"{master_path}/{draft.json()['id']}/readiness", headers=headers)
    assert readiness.status_code == 200, readiness.text
    payload["render_asset_ref"] = [{"canvas_id": "cover", "material_revision_id": revision.id}]
    saved = client.post(master_path, json={
        "idempotency_key": "graphic-rendered", "expected_revision": 1, "payload_schema": "graphic.master.v2", "payload": payload,
        "asset_refs": [asset_ref], "render_attestation": {"confirmed": True, "render_input_hash": readiness.json()["render_input_hash"]},
    }, headers=headers)
    assert saved.status_code == 200, saved.text
    if ready:
        checks = client.post(f"{master_path}/{saved.json()['id']}/checks", headers=headers)
        assert checks.status_code == 200, checks.text
    return project, unit, saved.json(), revision, headers


def test_image_note_v5_freeze_approval_and_manual_package_use_exact_render_bytes(client, db_session, tmp_path):
    project, unit, master, image, headers = _source(client, db_session, tmp_path, ready=True)
    variants = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    intent = {"source_master_revision_id": master["id"], "expected_source_payload_hash": master["payload_hash"],
              "expected_source_context_hash": master["context_hash"], "channel_id": "xiaohongshu", "content_form": "image_note"}
    preview = client.post(f"{variants}/adapt-preview", json=intent, headers=headers)
    assert preview.status_code == 200, preview.text
    declaration = {"id": "rights-note", "kind": "rights", "text": "图片来源已核对"}
    saved = client.post(variants, json={**intent, "variant_key": "image-note.complete", "expected_revision": 0,
        "idempotency_key": "image-note.complete", "source_kind": "manual_edit",
        "payload": {**preview.json()["payload"], "declarations": [declaration]},
        "asset_refs": preview.json()["asset_refs"]}, headers=headers)
    assert saved.status_code == 201, saved.text
    checked = client.post(f"{variants}/{saved.json()['id']}/checks", headers=headers)
    assert checked.status_code == 200 and checked.json()["ready"] is True, checked.text
    candidates = f"/api/v1/content-projects/{project}/units/{unit}/candidates"
    frozen = client.post(f"{candidates}/freeze", json={"channel_variant_revision_id": saved.json()["id"],
        "expected_payload_hash": saved.json()["payload_hash"]}, headers=headers)
    assert frozen.status_code == 201, frozen.text
    candidate = frozen.json()
    assert candidate["manifest"]["target"]["artifact_kind"] == "image"
    approved = client.post(f"{candidates}/{candidate['id']}/approve", json={
        "candidate_hash": candidate["candidate_hash"],
        "warning_dispositions": {
            f"{row['id']}:{row['input_hash']}": "编辑已核对该提示"
            for row in candidate["manifest"]["source_master"].get("warning_checks", [])
        }}, headers=headers)
    assert approved.status_code == 200, approved.text
    target = client.post(f"{candidates}/{candidate['id']}/delivery-authorizations", json={
        "channel": "xiaohongshu", "content_form": "image_note", "account_ref": "manual-xiaohongshu",
        "authorization_version": "v1", "action": "copy_package"}, headers=headers)
    assert target.status_code == 201, target.text
    downloaded = client.get(f"/api/v1/delivery-targets/{target.json()['id']}/package.zip", headers=headers)
    assert downloaded.status_code == 200, downloaded.text
    with zipfile.ZipFile(io.BytesIO(downloaded.content)) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["schema_version"] == 5 and manifest["remote_call"] is False
        assert manifest["target"]["content_form"] == "image_note"
        assert manifest["declarations"] == [declaration]
        media = manifest["media"]
        assert len(media) == 1 and media[0]["material_revision_id"] == image.id
        assert archive.read(media[0]["name"]) == (tmp_path / "final.png").read_bytes()
        assert "cards.json" in archive.namelist()
    image.public_use_allowed = False
    db_session.commit()
    blocked = client.get(f"/api/v1/delivery-targets/{target.json()['id']}/package.zip", headers=headers)
    assert blocked.status_code in {403, 409, 422}, blocked.text


def test_image_note_preview_and_save_freeze_exact_rendered_image(client, db_session, tmp_path):
    project, unit, master, image, headers = _source(client, db_session, tmp_path)
    path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    intent = {"source_master_revision_id": master["id"], "expected_source_payload_hash": master["payload_hash"],
              "expected_source_context_hash": master["context_hash"], "channel_id": "xiaohongshu", "content_form": "image_note"}
    preview = client.post(f"{path}/adapt-preview", json=intent, headers=headers)
    assert preview.status_code == 200, preview.text
    assert preview.json()["payload_schema"] == "xiaohongshu.image_note.v1"
    assert preview.json()["payload"]["cards"][0]["image_ref_key"] == "cover"
    assert preview.json()["asset_refs"][0]["material_revision_id"] == image.id
    assert preview.json()["asset_refs"][0]["content_hash_snapshot"] == image.content_hash
    assert client.get(path, headers=headers).json()["items"] == []
    saved = client.post(path, json={**intent, "variant_key": "xiaohongshu-primary", "expected_revision": 0,
        "idempotency_key": "image-note-1", "source_kind": "deterministic_adapt", "payload": preview.json()["payload"],
        "asset_refs": preview.json()["asset_refs"]}, headers=headers)
    assert saved.status_code == 201, saved.text
    assert saved.json()["assets"][0]["material_revision_id"] == image.id
    assert saved.json()["assets"][0]["content_hash"] == image.content_hash
    checks = client.post(f"{path}/{saved.json()['id']}/checks", headers=headers)
    assert checks.status_code == 200, checks.text
    by_kind = {item["check_kind"]: item for item in checks.json()["items"]}
    assert by_kind["variant_rights"]["status"] == "pass"
    assert by_kind["variant_profile"]["status"] == "pass"
    assert by_kind["variant_render"]["status"] == "pass"
    assert by_kind["variant_package"]["status"] == "pass"
    assert checks.json()["ready"] is False
    image.public_use_allowed = False
    db_session.commit()
    drifted = client.get(f"{path}/{saved.json()['id']}/checks", headers=headers)
    assert drifted.status_code == 200, drifted.text
    assert "assets_or_render_changed" in drifted.json()["drift_reasons"]
    assert next(item for item in drifted.json()["items"] if item["check_kind"] == "variant_rights")["status"] == "stale"


def test_image_note_preview_rejects_prompt_only_and_revoked_image(client, db_session, tmp_path):
    project, unit, master, image, headers = _source(client, db_session, tmp_path)
    path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    intent = {"source_master_revision_id": master["id"], "expected_source_payload_hash": master["payload_hash"],
              "expected_source_context_hash": master["context_hash"], "channel_id": "xiaohongshu", "content_form": "image_note"}
    image.public_use_allowed = False
    db_session.commit()
    rejected = client.post(f"{path}/adapt-preview", json=intent, headers=headers)
    assert rejected.status_code == 422, rejected.text
    assert rejected.json()["detail"]["code"] == "variant_render_unready"
    assert client.get(path, headers=headers).json()["items"] == []


def test_image_note_preview_rejects_unrendered_graphic_master(client, db_session, tmp_path):
    project, unit, master, _, headers = _source(client, db_session, tmp_path, attest=False)
    path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    response = client.post(f"{path}/adapt-preview", json={
        "source_master_revision_id": master["id"], "expected_source_payload_hash": master["payload_hash"],
        "expected_source_context_hash": master["context_hash"], "channel_id": "xiaohongshu", "content_form": "image_note",
    }, headers=headers)
    assert response.status_code == 422, response.text
    assert response.json()["detail"]["code"] == "variant_render_unready"
    assert client.get(path, headers=headers).json()["items"] == []


def test_image_note_save_rejects_tampered_refs_without_partial_write(client, db_session, tmp_path):
    project, unit, master, _, headers = _source(client, db_session, tmp_path)
    path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    intent = {"source_master_revision_id": master["id"], "expected_source_payload_hash": master["payload_hash"],
              "expected_source_context_hash": master["context_hash"], "channel_id": "xiaohongshu", "content_form": "image_note"}
    preview = client.post(f"{path}/adapt-preview", json=intent, headers=headers).json()
    body = {**intent, "variant_key": "tampered", "expected_revision": 0, "idempotency_key": "tampered-1",
            "payload": preview["payload"], "asset_refs": preview["asset_refs"]}
    bad_hash = client.post(path, json={**body, "asset_refs": [{**preview["asset_refs"][0], "content_hash_snapshot": "f" * 64}]}, headers=headers)
    assert bad_hash.status_code == 422, bad_hash.text
    bad_order = client.post(path, json={**body, "idempotency_key": "tampered-2", "asset_refs": [{**preview["asset_refs"][0], "sort_order": []}]}, headers=headers)
    assert bad_order.status_code == 422, bad_order.text
    assert client.get(path, headers=headers).json()["items"] == []


def test_image_note_rights_revoked_before_commit_rolls_back_refs_and_event(client, db_session, tmp_path, monkeypatch):
    from app.services import channel_variants as service

    project, unit, master, image, headers = _source(client, db_session, tmp_path)
    path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    intent = {"source_master_revision_id": master["id"], "expected_source_payload_hash": master["payload_hash"],
              "expected_source_context_hash": master["context_hash"], "channel_id": "xiaohongshu", "content_form": "image_note"}
    preview = client.post(f"{path}/adapt-preview", json=intent, headers=headers).json()
    original = service.record_project_event

    def revoke_on_event(db, **kwargs):
        result = original(db, **kwargs)
        db.get(MaterialRevision, image.id).public_use_allowed = False
        db.flush()
        return result

    monkeypatch.setattr(service, "record_project_event", revoke_on_event)
    response = client.post(path, json={**intent, "variant_key": "xiaohongshu-primary", "expected_revision": 0,
        "idempotency_key": "revoked-race", "source_kind": "deterministic_adapt", "payload": preview["payload"],
        "asset_refs": preview["asset_refs"]}, headers=headers)
    assert response.status_code == 409, response.text
    assert db_session.scalars(select(ChannelVariantRevision)).all() == []
    assert db_session.scalars(select(ProjectEvent).where(ProjectEvent.event_type == "channel_variant.saved")).all() == []
    db_session.expire(image)
    assert image.public_use_allowed is True


def test_image_note_card_order_must_match_frozen_ref_order(client, db_session, tmp_path):
    project, unit, master, image, headers = _source(client, db_session, tmp_path)
    content = b"\x89PNG\r\n\x1a\nsecond rendered image bytes"
    file = tmp_path / "second.png"
    file.write_bytes(content)
    material = Material(title="第二张", kind="image", status="active")
    db_session.add(material)
    db_session.flush()
    second = MaterialRevision(material_id=material.id, content_hash=hashlib.sha256(content).hexdigest(), file_path=str(file),
                              mime_type="image/png", status="active", public_use_allowed=True, rights_status="cleared")
    db_session.add(second)
    db_session.flush()
    db_session.add(ProjectMaterialReference(project_id=project, material_revision_id=second.id, origin="system_library", status="active"))
    db_session.commit()
    payload = copy.deepcopy(master["payload"])
    canvas = copy.deepcopy(payload["canvases"][0])
    canvas["id"] = "second"
    canvas["order"] = 1
    canvas["layers"][0]["id"] = "copy2"
    payload["canvases"].append(canvas)
    payload["render_asset_ref"].append({"canvas_id": "second", "material_revision_id": second.id})
    refs = [
        {"material_revision_id": image.id, "content_hash": image.content_hash, "role": "render_output", "slot_key": "cover", "sort_order": 0, "placement": {"canvas_id": "cover"}},
        {"material_revision_id": second.id, "content_hash": second.content_hash, "role": "render_output", "slot_key": "second", "sort_order": 1, "placement": {"canvas_id": "second"}},
    ]
    master_path = f"/api/v1/content-projects/{project}/units/{unit}/master-revisions"
    draft = client.post(master_path, json={"idempotency_key": "two-cards-draft", "expected_revision": 2,
        "payload_schema": "graphic.master.v2", "payload": payload, "asset_refs": refs}, headers=headers)
    assert draft.status_code == 200, draft.text
    readiness = client.get(f"{master_path}/{draft.json()['id']}/readiness", headers=headers).json()
    saved = client.post(master_path, json={"idempotency_key": "two-cards-render", "expected_revision": 3,
        "payload_schema": "graphic.master.v2", "payload": payload, "asset_refs": refs,
        "render_attestation": {"confirmed": True, "render_input_hash": readiness["render_input_hash"]}}, headers=headers)
    assert saved.status_code == 200, saved.text
    source = saved.json()
    path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    intent = {"source_master_revision_id": source["id"], "expected_source_payload_hash": source["payload_hash"],
              "expected_source_context_hash": source["context_hash"], "channel_id": "xiaohongshu", "content_form": "image_note"}
    preview = client.post(f"{path}/adapt-preview", json=intent, headers=headers)
    assert preview.status_code == 200, preview.text
    assert [card["image_ref_key"] for card in preview.json()["payload"]["cards"]] == ["cover", "second"]
    reversed_cards = list(reversed(preview.json()["payload"]["cards"]))
    for index, card in enumerate(reversed_cards):
        card["order"] = index
    response = client.post(path, json={**intent, "variant_key": "image-note-order", "expected_revision": 0,
        "idempotency_key": "wrong-order", "payload": {**preview.json()["payload"], "cards": reversed_cards},
        "asset_refs": preview.json()["asset_refs"]}, headers=headers)
    assert response.status_code == 422, response.text
    assert response.json()["detail"]["code"] == "variant_asset_order_mismatch"
    reordered_refs = [{**ref, "sort_order": 1 - ref["sort_order"]} for ref in preview.json()["asset_refs"]]
    accepted = client.post(path, json={**intent, "variant_key": "image-note-order", "expected_revision": 0,
        "idempotency_key": "right-order", "payload": {**preview.json()["payload"], "cards": reversed_cards},
        "asset_refs": reordered_refs}, headers=headers)
    assert accepted.status_code == 201, accepted.text
    assert [ref["slot_key"] for ref in accepted.json()["assets"]] == ["second", "cover"]
