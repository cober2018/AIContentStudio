"""F6E script adaptation must not claim a finished video or silently discard media."""

import pytest

from app.models import ChannelTemplateVersion
from app.seed import seed_v1_channel_profiles
from app.services.channel_adapters import AdapterUnavailable, VideoSpokenScriptAdapter


def _source(client, db_session, *, timed_cues=False):
    seed_v1_channel_profiles(db_session)
    db_session.add(ChannelTemplateVersion(
        channel="video_f6e_source", version=1, name="Video source", status="published",
        profile_json={"content_forms": {"short": {"artifact_kind": "video"}}},
    ))
    db_session.commit()
    headers = {"X-Studio-User": "video-f6e@studio.local"}
    persona = client.post("/api/v1/content-personas", json={"name": "口播作者"}, headers=headers).json()["id"]
    project = client.post("/api/v1/content-projects", json={"title": "口播项目"}, headers=headers).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project}/units", json={
        "title": "口播脚本", "persona_id": persona, "modality": "video", "channel_id": "video_f6e_source",
    }, headers=headers).json()["id"]
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
    saved = client.post(f"/api/v1/content-projects/{project}/units/{unit}/master-revisions", json={
        "idempotency_key": "video-script-source", "payload_schema": "video.master.v2", "payload": document,
        "content_form": "short",
    }, headers=headers)
    assert saved.status_code == 200, saved.text
    return project, unit, saved.json(), headers


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
    assert "estimated_srt" not in preview.json()["payload"]
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
