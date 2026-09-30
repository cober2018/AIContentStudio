"""F6E script adaptation must not claim a finished video or silently discard media."""

import hashlib
import io
import json
import zipfile

import pytest
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
from app.services.channel_adapters import AdapterUnavailable, VideoSpokenScriptAdapter


def _source(client, db_session, *, timed_cues=False, b_roll_file=None, ready=False):
    seed_v1_channel_profiles(db_session)
    db_session.add(ChannelTemplateVersion(
        channel="video_f6e_source", version=1, name="Video source", status="published",
        profile_json={"content_forms": {"short": {"artifact_kind": "video"}}},
    ))
    db_session.commit()
    headers = {"X-Studio-User": "video-f6e@studio.local"}
    persona = client.post("/api/v1/content-personas", json={"name": "口播作者"}, headers=headers).json()["id"]
    if ready:
        persona_revision = client.post(f"/api/v1/content-personas/{persona}/revisions", json={
            "expected_revision": 0, "profile": {"expression_style": {"forbidden_phrases": []}},
        }, headers=headers)
        assert persona_revision.status_code == 201, persona_revision.text
    project = client.post("/api/v1/content-projects", json={"title": "口播项目"}, headers=headers).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project}/units", json={
        "title": "口播脚本", "persona_id": persona, "modality": "video", "channel_id": None if ready else "video_f6e_source",
    }, headers=headers).json()["id"]
    if ready:
        brief = client.post(f"/api/v1/content-projects/{project}/brief/revisions", json={
            "objective": "准确表达口播观点", "expected_revision": 0,
        }, headers=headers)
        assert brief.status_code == 201, brief.text
        pack = FactPack(name="口播事实边界", version=1, status="frozen", checksum="c" * 64)
        db_session.add(pack)
        db_session.flush()
        db_session.add(FactPackItem(fact_pack_id=pack.id, evidence_kind="author_opinion",
                                    snapshot_json={"statement": "开场白"}, snapshot_checksum="d" * 64,
                                    public_use_allowed=True, model_use_allowed=True))
        db_session.commit()
        boundary = client.post(f"/api/v1/content-projects/{project}/fact-boundary", json={
            "fact_pack_id": pack.id, "expected_revision": 0,
        }, headers=headers)
        assert boundary.status_code == 201, boundary.text
    document = {
        "title": "短片", "aspect_ratio": [9, 16],
        "script": {"blocks": [{"id": "opening", "order": 0, "text": "开场白"}]},
        "shots": [{"id": "shot-1", "order": 0, "label": "开场", "duration_ms": 4000, "script_block_id": "opening"}],
        "timeline": {"duration_ms": 4000, "tracks": [{"id": "visual", "order": 0, "kind": "video", "items": [
            {"id": "item-1", "order": 0, "shot_id": "shot-1", "start_ms": 0, "end_ms": 4000},
        ]}]},
        "voice": {"mode": "none"}, "subtitles": {"cues": []}, "overlays": [], "music": {}, "cover": {},
    }
    if timed_cues:
        document["subtitles"]["cues"] = [{"id": "cue-1", "order": 0, "text": "开场白", "start_ms": 0, "end_ms": 2000}]
    refs = []
    if b_roll_file is not None:
        content = b"\x89PNG\r\n\x1a\nreal b-roll image bytes"
        b_roll_file.write_bytes(content)
        material = Material(title="镜头素材", kind="image", status="active")
        db_session.add(material)
        db_session.flush()
        revision = MaterialRevision(
            material_id=material.id, content_hash=hashlib.sha256(content).hexdigest(), file_path=str(b_roll_file),
            mime_type="image/png", status="active", public_use_allowed=True, rights_status="cleared",
        )
        db_session.add(revision)
        db_session.flush()
        db_session.add(ProjectMaterialReference(project_id=project, material_revision_id=revision.id, origin="system_library", status="active"))
        db_session.commit()
        document["shots"][0]["source_material_revision_id"] = revision.id
        refs.append({"material_revision_id": revision.id, "content_hash": revision.content_hash, "role": "shot_source",
                     "slot_key": "shot-1", "sort_order": 0, "placement": {"shot_id": "shot-1"}})
    saved = client.post(f"/api/v1/content-projects/{project}/units/{unit}/master-revisions", json={
        "idempotency_key": "video-script-source", "payload_schema": "video.master.v2", "payload": document,
        **({} if ready else {"content_form": "short"}), "asset_refs": refs,
    }, headers=headers)
    assert saved.status_code == 200, saved.text
    if ready:
        checks = client.post(f"/api/v1/content-projects/{project}/units/{unit}/master-revisions/{saved.json()['id']}/checks", headers=headers)
        assert checks.status_code == 200, checks.text
    return project, unit, saved.json(), headers


@pytest.mark.parametrize("with_b_roll", [False, True])
def test_spoken_script_v5_approval_and_manual_package_remain_script_only(client, db_session, tmp_path, with_b_roll):
    b_roll_file = tmp_path / "b-roll.png" if with_b_roll else None
    project, unit, master, headers = _source(client, db_session, b_roll_file=b_roll_file, ready=True)
    direct_video = client.post(f"/api/v1/content-projects/{project}/units/{unit}/candidates/freeze", json={
        "content_master_revision_id": master["id"], "expected_payload_hash": master["payload_hash"],
    }, headers=headers)
    assert direct_video.status_code == 409, direct_video.text
    variants = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    intent = {"source_master_revision_id": master["id"], "expected_source_payload_hash": master["payload_hash"],
              "expected_source_context_hash": master["context_hash"], "channel_id": "douyin", "content_form": "spoken_script"}
    preview = client.post(f"{variants}/adapt-preview", json=intent, headers=headers)
    assert preview.status_code == 200, preview.text
    declaration = {"id": "timing-note", "kind": "timing", "text": "字幕时间为估算"}
    saved = client.post(variants, json={**intent, "variant_key": "spoken-script.complete", "expected_revision": 0,
        "idempotency_key": "spoken-script.complete", "source_kind": "manual_edit",
        "payload": {**preview.json()["payload"], "declarations": [declaration]},
        "asset_refs": preview.json()["asset_refs"]}, headers=headers)
    assert saved.status_code == 201, saved.text
    checked = client.post(f"{variants}/{saved.json()['id']}/checks", headers=headers)
    assert checked.status_code == 200 and checked.json()["ready"] is True, checked.json()["source_gate"]
    candidates = f"/api/v1/content-projects/{project}/units/{unit}/candidates"
    frozen = client.post(f"{candidates}/freeze", json={"channel_variant_revision_id": saved.json()["id"],
        "expected_payload_hash": saved.json()["payload_hash"]}, headers=headers)
    assert frozen.status_code == 201, frozen.text
    candidate = frozen.json()
    assert candidate["manifest"]["target"]["artifact_kind"] == "script"
    assert candidate["manifest"]["render"].get("finished_video") is False
    approved = client.post(f"{candidates}/{candidate['id']}/approve", json={
        "candidate_hash": candidate["candidate_hash"],
        "warning_dispositions": {
            f"{row['id']}:{row['input_hash']}": "编辑已核对该提示"
            for row in candidate["manifest"]["source_master"].get("warning_checks", [])
        }}, headers=headers)
    assert approved.status_code == 200, approved.text
    target = client.post(f"{candidates}/{candidate['id']}/delivery-authorizations", json={
        "channel": "douyin", "content_form": "spoken_script", "account_ref": "manual-douyin",
        "authorization_version": "v1", "action": "copy_package"}, headers=headers)
    assert target.status_code == 201, target.text
    downloaded = client.get(f"/api/v1/delivery-targets/{target.json()['id']}/package.zip", headers=headers)
    assert downloaded.status_code == 200, downloaded.text
    with zipfile.ZipFile(io.BytesIO(downloaded.content)) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["schema_version"] == 5 and manifest["remote_call"] is False
        assert manifest["render"]["finished_video"] is False
        assert manifest["declarations"] == [declaration]
        assert archive.read("content.md").decode() == "开场白"
        assert "estimated.srt" in archive.namelist()
        assert "开场白" in archive.read("estimated.srt").decode()
        assert not any(name.endswith(".mp4") for name in archive.namelist())
        if with_b_roll:
            media = manifest["media"]
            assert len(media) == 1 and media[0]["role"] == "b_roll"
            assert archive.read(media[0]["name"]) == b_roll_file.read_bytes()
    if with_b_roll:
        db_session.get(MaterialRevision, master["assets"][0]["material_revision_id"]).public_use_allowed = False
        db_session.commit()
        denied = client.get(f"/api/v1/delivery-targets/{target.json()['id']}/package.zip", headers=headers)
        assert denied.status_code == 422 and denied.json()["detail"]["code"] == "variant_b_roll_unready"


def test_script_only_preview_and_save_do_not_claim_finished_video(client, db_session):
    project, unit, master, headers = _source(client, db_session)
    path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    intent = {"source_master_revision_id": master["id"], "expected_source_payload_hash": master["payload_hash"],
              "expected_source_context_hash": master["context_hash"], "channel_id": "douyin", "content_form": "spoken_script"}
    preview = client.post(f"{path}/adapt-preview", json=intent, headers=headers)
    assert preview.status_code == 200, preview.text
    assert preview.json()["artifact_kind"] == "script"
    assert preview.json()["verified_remote"] is False
    assert preview.json()["payload"]["scenes"] == [{"id": "shot-1", "order": 0, "script": "开场白", "voice_text": "开场白", "b_roll_ref_keys": []}]
    assert preview.json()["payload"]["estimated_srt"] == {"estimated": True, "text": "1\n00:00:00,000 --> 00:00:04,000\n开场白"}
    saved = client.post(path, json={**intent, "variant_key": "douyin-main", "expected_revision": 0,
        "idempotency_key": "script-1", "source_kind": "deterministic_adapt", "payload": preview.json()["payload"]}, headers=headers)
    assert saved.status_code == 201, saved.text
    assert saved.json()["artifact_kind"] == "script"
    assert saved.json()["assets"] == []


def test_timed_subtitles_require_explicit_mapping_and_do_not_write_variant(client, db_session):
    project, unit, master, headers = _source(client, db_session, timed_cues=True)
    path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    response = client.post(f"{path}/adapt-preview", json={
        "source_master_revision_id": master["id"], "expected_source_payload_hash": master["payload_hash"],
        "expected_source_context_hash": master["context_hash"], "channel_id": "douyin", "content_form": "spoken_script",
    }, headers=headers)
    assert response.status_code == 422, response.text
    assert response.json()["detail"]["reason"] == "video_media_or_timing_requires_explicit_mapping"
    assert client.get(path, headers=headers).json()["items"] == []


def test_script_adapter_rejects_unmapped_b_roll_instead_of_dropping_it():
    adapter = VideoSpokenScriptAdapter()
    with pytest.raises(AdapterUnavailable, match="source_refs_require_explicit_mapping"):
        adapter.adapt({}, asset_refs=[{"slot_key": "shot-1"}], evidence_refs=[])


def test_exact_b_roll_preview_and_save(client, db_session, tmp_path):
    project, unit, master, headers = _source(client, db_session, b_roll_file=tmp_path / "b-roll.png")
    path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    intent = {"source_master_revision_id": master["id"], "expected_source_payload_hash": master["payload_hash"],
              "expected_source_context_hash": master["context_hash"], "channel_id": "douyin", "content_form": "spoken_script"}
    preview = client.post(f"{path}/adapt-preview", json=intent, headers=headers)
    assert preview.status_code == 200, preview.text
    assert preview.json()["payload"]["scenes"][0]["b_roll_ref_keys"] == ["shot-1"]
    assert preview.json()["asset_refs"][0]["role"] == "b_roll"
    assert preview.json()["asset_refs"][0]["material_revision_id"] == master["assets"][0]["material_revision_id"]
    saved = client.post(path, json={**intent, "variant_key": "douyin-b-roll", "expected_revision": 0,
        "idempotency_key": "script-b-roll", "source_kind": "deterministic_adapt", "payload": preview.json()["payload"],
        "asset_refs": preview.json()["asset_refs"]}, headers=headers)
    assert saved.status_code == 201, saved.text
    assert saved.json()["assets"][0]["content_hash"] == master["assets"][0]["content_hash"]
    assert saved.json()["artifact_kind"] == "script"


def test_b_roll_revocation_blocks_adaptation_without_writes(client, db_session, tmp_path):
    project, unit, master, headers = _source(client, db_session, b_roll_file=tmp_path / "b-roll.png")
    db_session.get(MaterialRevision, master["assets"][0]["material_revision_id"]).public_use_allowed = False
    db_session.commit()
    path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    preview = client.post(f"{path}/adapt-preview", json={
        "source_master_revision_id": master["id"], "expected_source_payload_hash": master["payload_hash"],
        "expected_source_context_hash": master["context_hash"], "channel_id": "douyin", "content_form": "spoken_script",
    }, headers=headers)
    assert preview.status_code == 422, preview.text
    assert preview.json()["detail"]["code"] == "variant_b_roll_unready"
    assert client.get(path, headers=headers).json()["items"] == []


def test_b_roll_missing_bytes_or_tampered_binding_rejects_without_variant(client, db_session, tmp_path):
    file = tmp_path / "b-roll.png"
    project, unit, master, headers = _source(client, db_session, b_roll_file=file)
    path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    intent = {"source_master_revision_id": master["id"], "expected_source_payload_hash": master["payload_hash"],
              "expected_source_context_hash": master["context_hash"], "channel_id": "douyin", "content_form": "spoken_script"}
    preview = client.post(f"{path}/adapt-preview", json=intent, headers=headers).json()
    body = {**intent, "variant_key": "douyin-main", "expected_revision": 0, "idempotency_key": "tampered-b-roll",
            "payload": preview["payload"], "asset_refs": [{**preview["asset_refs"][0], "content_hash_snapshot": "f" * 64}]}
    tampered = client.post(path, json=body, headers=headers)
    assert tampered.status_code == 422, tampered.text
    assert tampered.json()["detail"]["code"] == "variant_b_roll_binding_mismatch"
    file.write_bytes(b"corrupted image bytes")
    missing = client.post(f"{path}/adapt-preview", json=intent, headers=headers)
    assert missing.status_code == 422, missing.text
    assert missing.json()["detail"]["code"] == "variant_b_roll_bytes_unverified"
    assert client.get(path, headers=headers).json()["items"] == []


def test_b_roll_rights_change_during_save_rolls_back_variant_and_event(client, db_session, tmp_path, monkeypatch):
    from app.services import channel_variants as service

    project, unit, master, headers = _source(client, db_session, b_roll_file=tmp_path / "b-roll.png")
    path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    intent = {"source_master_revision_id": master["id"], "expected_source_payload_hash": master["payload_hash"],
              "expected_source_context_hash": master["context_hash"], "channel_id": "douyin", "content_form": "spoken_script"}
    preview = client.post(f"{path}/adapt-preview", json=intent, headers=headers).json()
    original = service.record_project_event

    def revoke_on_event(db, **kwargs):
        result = original(db, **kwargs)
        db.get(MaterialRevision, master["assets"][0]["material_revision_id"]).public_use_allowed = False
        db.flush()
        return result

    monkeypatch.setattr(service, "record_project_event", revoke_on_event)
    response = client.post(path, json={**intent, "variant_key": "douyin-main", "expected_revision": 0,
        "idempotency_key": "race-revoke", "payload": preview["payload"], "asset_refs": preview["asset_refs"]}, headers=headers)
    assert response.status_code == 409, response.text
    assert db_session.scalars(select(ChannelVariantRevision)).all() == []
    assert db_session.scalars(select(ProjectEvent).where(ProjectEvent.event_type == "channel_variant.saved")).all() == []
