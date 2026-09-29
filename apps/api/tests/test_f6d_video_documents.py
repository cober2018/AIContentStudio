"""Video v2 document and exact-profile contract regressions."""

import hashlib
import importlib
import importlib.util

import pytest


def _canonical(payload: dict) -> dict:
    assert importlib.util.find_spec("app.services.video_documents"), "Video v2 document contract missing"
    return importlib.import_module("app.services.video_documents").canonical_payload(payload)


def _document() -> dict:
    return {
        "title": "短片",
        "aspect_ratio": [9, 16],
        "script": {"blocks": [{"id": "opening", "order": 0, "text": "开场"}]},
        "shots": [{"id": "shot-1", "order": 0, "label": "开场镜头", "duration_ms": 4_000, "script_block_id": "opening", "transition": "cut"}],
        "timeline": {"duration_ms": 4_000, "tracks": [{"id": "visual", "order": 0, "kind": "video", "items": [{"id": "item-1", "order": 0, "shot_id": "shot-1", "start_ms": 0, "end_ms": 4_000}]}]},
        "voice": {"mode": "none"},
        "subtitles": {"cues": [{"id": "cue-1", "order": 0, "text": "开场", "start_ms": 0, "end_ms": 2_000}]},
        "overlays": [],
        "music": {},
        "cover": {},
    }


def test_video_v2_document_canonical_order_and_stable_ids():
    payload = _document()
    assert _canonical(payload) == payload
    assert _canonical(payload)["timeline"]["tracks"][0]["items"][0]["shot_id"] == "shot-1"


def test_empty_video_draft_is_valid_but_not_a_final_render():
    payload = _document()
    payload["script"]["blocks"] = []
    payload["shots"] = []
    payload["timeline"] = {"duration_ms": 0, "tracks": []}
    payload["subtitles"]["cues"] = []
    assert _canonical(payload) == payload


@pytest.mark.parametrize("mutation", [
    lambda doc: doc["shots"][0].update({"extra": "unsupported"}),
    lambda doc: doc["shots"].append({**doc["shots"][0], "order": 1}),
    lambda doc: doc["timeline"]["tracks"][0]["items"][0].update({"end_ms": 5_000}),
    lambda doc: doc["subtitles"]["cues"][0].update({"end_ms": 5_000}),
])
def test_video_v2_invalid_structure_fails_closed(mutation):
    payload = _document()
    mutation(payload)
    with pytest.raises(ValueError):
        _canonical(payload)


def test_exact_video_profile_applies_only_declared_bounded_rules():
    from app.services.content_harness.channel_registry import ContentFormSpec
    from app.services.video_documents import profile_reasons

    form = ContentFormSpec(
        channel="fixture", content_form="short", artifact_kind="video", source="profile", profile_version_id=1,
        video_requirements={"max_duration_ms": 5_000, "allowed_aspect_ratios": [[9, 16]], "max_shots": 1, "subtitle_required": True},
    )
    assert profile_reasons(form, _canonical(_document())) == []
    form.video_requirements = {"max_duration_ms": 3_000}
    assert profile_reasons(form, _canonical(_document())) == ["video_duration_above_profile_maximum"]
    form.video_requirements = {"unsupported": True}
    assert profile_reasons(form, _canonical(_document())) == ["video_profile_rules_invalid"]
    form.video_requirements = {"max_shots": True}
    assert profile_reasons(form, _canonical(_document())) == ["video_profile_rules_invalid"]
    form.source = "legacy_default"
    form.video_requirements = {}
    assert profile_reasons(form, _canonical(_document())) == ["video_profile_unavailable"]


def test_video_media_reuse_has_distinct_exact_shot_slots():
    from app.services.video_documents import validate_references

    payload = _document()
    first = payload["shots"][0]
    first["source_material_revision_id"] = 17
    payload["shots"].append({**first, "id": "shot-2", "order": 1})
    refs = [
        {"material_revision_id": 17, "content_hash": "a" * 64, "role": "shot_source", "slot_key": "shot-1", "sort_order": 0, "placement": {"shot_id": "shot-1"}},
        {"material_revision_id": 17, "content_hash": "a" * 64, "role": "shot_source", "slot_key": "shot-2", "sort_order": 1, "placement": {"shot_id": "shot-2"}},
    ]
    validate_references(payload, refs, [])
    with pytest.raises(ValueError):
        validate_references(payload, refs[:1], [])
    with pytest.raises(ValueError):
        validate_references(payload, [refs[0], {**refs[1], "slot_key": "shot-1"}], [])
    with pytest.raises(ValueError):
        validate_references(payload, [refs[0], {**refs[1], "placement": {"shot_id": "shot-1"}}], [])


def test_video_media_roles_include_timeline_voice_music_cover_and_one_render():
    from app.services.video_documents import validate_references

    payload = _document()
    payload["timeline"]["tracks"][0]["items"][0]["material_revision_id"] = 22
    payload["voice"] = {"mode": "recorded", "material_revision_id": 18}
    payload["music"] = {"material_revision_id": 19}
    payload["cover"] = {"material_revision_id": 20}
    payload["render_asset_ref"] = {"material_revision_id": 21}
    placements = [
        (22, "timeline_media", "item-1", {"track_id": "visual", "item_id": "item-1", "start_ms": 0, "end_ms": 4_000}),
        (18, "voice_audio", "voice", {"voice": "main"}),
        (19, "music_audio", "music", {"music": "main"}),
        (20, "cover_image", "cover", {"cover": "main"}),
        (21, "render_output", "final", {"render": "final"}),
    ]
    refs = [
        {"material_revision_id": revision_id, "content_hash": "a" * 64, "role": role, "slot_key": slot, "sort_order": index, "placement": placement}
        for index, (revision_id, role, slot, placement) in enumerate(placements)
    ]
    validate_references(payload, refs, [])
    with pytest.raises(ValueError):
        validate_references(payload, refs + [refs[-1]], [])
    with pytest.raises(ValueError):
        validate_references(payload, [*refs[:-1], {**refs[-1], "role": "timeline_media"}], [])


def test_video_v2_master_save_round_trips_canonical_document(client):
    headers = {"X-Studio-User": "video-v2-contract@studio.local"}
    persona = client.post("/api/v1/content-personas", json={"name": "视频创作者"}, headers=headers).json()["id"]
    project = client.post("/api/v1/content-projects", json={"title": "视频项目"}, headers=headers).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project}/units", json={"title": "短片", "persona_id": persona, "modality": "video"}, headers=headers).json()["id"]
    path = f"/api/v1/content-projects/{project}/units/{unit}/master-revisions"
    document = _document()
    response = client.post(path, json={"idempotency_key": "v2-first", "payload_schema": "video.master.v2", "payload": document}, headers=headers)
    assert response.status_code == 200, response.text
    saved = response.json()
    assert saved["payload_schema"] == "video.master.v2"
    assert saved["payload"] == document
    assert client.get(f"{path}/{saved['id']}", headers=headers).json()["payload"] == document


def test_video_v2_readiness_uses_exact_published_profile(client, db_session):
    from app.models import ChannelTemplateVersion

    headers = {"X-Studio-User": "video-profile-check@studio.local"}
    db_session.add(ChannelTemplateVersion(
        channel="short_video_fixture", version=1, name="短视频", status="published",
        profile_json={"content_forms": {"short": {"artifact_kind": "video", "video_requirements": {"max_shots": 1}}}},
    ))
    db_session.commit()
    persona = client.post("/api/v1/content-personas", json={"name": "视频作者"}, headers=headers).json()["id"]
    project = client.post("/api/v1/content-projects", json={"title": "视频规则", "channels": ["short_video_fixture"]}, headers=headers).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project}/units", json={"title": "短片", "persona_id": persona, "modality": "video", "channel_id": "short_video_fixture"}, headers=headers).json()["id"]
    path = f"/api/v1/content-projects/{project}/units/{unit}/master-revisions"
    document = _document()
    document["shots"].append({**document["shots"][0], "id": "shot-2", "order": 1})
    saved = client.post(path, json={"idempotency_key": "two-shots", "payload_schema": "video.master.v2", "payload": document, "content_form": "short"}, headers=headers)
    assert saved.status_code == 200, saved.text
    readiness = client.get(f"{path}/{saved.json()['id']}/readiness", headers=headers)
    assert readiness.status_code == 200, readiness.text
    assert "video_shot_count_above_profile_maximum" in readiness.json()["adapter_availability"]["reasons"]


def test_video_v2_render_input_hash_changes_with_published_profile(client, db_session):
    from app.models import ChannelTemplateVersion

    headers = {"X-Studio-User": "video-profile-hash@studio.local"}
    db_session.add(ChannelTemplateVersion(channel="video_hash_fixture", version=1, name="规则一版", status="published", profile_json={"content_forms": {"short": {"artifact_kind": "video", "video_requirements": {"max_shots": 2}}}}))
    db_session.commit()
    persona = client.post("/api/v1/content-personas", json={"name": "视频规则作者"}, headers=headers).json()["id"]
    project = client.post("/api/v1/content-projects", json={"title": "规则哈希", "channels": ["video_hash_fixture"]}, headers=headers).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project}/units", json={"title": "短片", "persona_id": persona, "modality": "video", "channel_id": "video_hash_fixture"}, headers=headers).json()["id"]
    path = f"/api/v1/content-projects/{project}/units/{unit}/master-revisions"
    saved = client.post(path, json={"idempotency_key": "profile-one", "payload_schema": "video.master.v2", "payload": _document(), "content_form": "short"}, headers=headers)
    assert saved.status_code == 200, saved.text
    first = client.get(f"{path}/{saved.json()['id']}/readiness", headers=headers).json()["render_input_hash"]
    db_session.add(ChannelTemplateVersion(channel="video_hash_fixture", version=2, name="规则二版", status="published", profile_json={"content_forms": {"short": {"artifact_kind": "video", "video_requirements": {"max_shots": 3}}}}))
    db_session.commit()
    second = client.get(f"{path}/{saved.json()['id']}/readiness", headers=headers).json()["render_input_hash"]
    assert second != first


def test_video_v2_source_media_reuse_requires_live_kind_bytes_rights_and_project_reference(client, db_session, tmp_path):
    from app.models import (
        ContentMasterAssetRef,
        ContentMasterRevision,
        Material,
        MaterialRevision,
        ProjectMaterialReference,
    )

    headers = {"X-Studio-User": "video-media@studio.local"}
    persona = client.post("/api/v1/content-personas", json={"name": "媒体作者"}, headers=headers).json()["id"]
    project = client.post("/api/v1/content-projects", json={"title": "媒体项目"}, headers=headers).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project}/units", json={"title": "双镜头", "persona_id": persona, "modality": "video"}, headers=headers).json()["id"]
    path = f"/api/v1/content-projects/{project}/units/{unit}/master-revisions"
    content = b"\x89PNG\r\n\x1a\nvideo source still"
    file = tmp_path / "still.png"
    file.write_bytes(content)
    material = Material(title="源画面", kind="audio", status="active")
    db_session.add(material)
    db_session.flush()
    revision = MaterialRevision(material_id=material.id, content_hash=hashlib.sha256(content).hexdigest(), file_path=str(file), mime_type="image/png", status="candidate", public_use_allowed=True, rights_status="cleared")
    db_session.add(revision)
    db_session.flush()
    project_ref = ProjectMaterialReference(project_id=project, material_revision_id=revision.id, origin="system_library", status="active")
    db_session.add(project_ref)
    db_session.commit()
    payload = _document()
    payload["shots"][0]["source_material_revision_id"] = revision.id
    payload["shots"].append({**payload["shots"][0], "id": "shot-2", "order": 1})
    refs = [
        {"material_revision_id": revision.id, "content_hash": revision.content_hash, "role": "shot_source", "slot_key": shot_id, "sort_order": index, "placement": {"shot_id": shot_id}}
        for index, shot_id in enumerate(("shot-1", "shot-2"))
    ]
    wrong_kind = client.post(path, json={"idempotency_key": "wrong-kind", "payload_schema": "video.master.v2", "payload": payload, "asset_refs": refs}, headers=headers)
    assert wrong_kind.status_code == 422, wrong_kind.text
    material.kind = "image"
    db_session.commit()
    wrong_hash = client.post(path, json={"idempotency_key": "wrong-hash", "payload_schema": "video.master.v2", "payload": payload, "asset_refs": [{**refs[0], "content_hash": "f" * 64}, refs[1]]}, headers=headers)
    assert wrong_hash.status_code == 422, wrong_hash.text
    accepted = client.post(path, json={"idempotency_key": "two-placements", "payload_schema": "video.master.v2", "payload": payload, "asset_refs": refs}, headers=headers)
    assert accepted.status_code == 200, accepted.text
    assert [item["slot_key"] for item in accepted.json()["assets"]] == ["shot-1", "shot-2"]
    project_ref.status = "detached"
    db_session.commit()
    foreign = client.post(path, json={"idempotency_key": "not-visible", "expected_revision": 1, "payload_schema": "video.master.v2", "payload": payload, "asset_refs": refs}, headers=headers)
    assert foreign.status_code == 422, foreign.text
    project_ref.status = "active"
    db_session.commit()
    file.write_bytes(b"corrupted bytes")
    bad_bytes = client.post(path, json={"idempotency_key": "bad-bytes", "expected_revision": 1, "payload_schema": "video.master.v2", "payload": payload, "asset_refs": refs}, headers=headers)
    assert bad_bytes.status_code == 422, bad_bytes.text
    file.write_bytes(content)
    revision.public_use_allowed = False
    db_session.commit()
    revoked = client.post(path, json={"idempotency_key": "revoked", "expected_revision": 1, "payload_schema": "video.master.v2", "payload": payload, "asset_refs": refs}, headers=headers)
    assert revoked.status_code == 422, revoked.text
    assert db_session.query(ContentMasterRevision).filter_by(content_unit_id=unit).count() == 1
    assert db_session.query(ContentMasterAssetRef).count() == 2
