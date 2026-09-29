"""Video v2 document and exact-profile contract regressions."""

import hashlib
import importlib
import importlib.util
import json
from copy import deepcopy
from types import SimpleNamespace

import pytest
from fastapi import HTTPException


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


def _legacy_video_master(client):
    headers = {"X-Studio-User": "video-upgrade@studio.local"}
    persona = client.post("/api/v1/content-personas", json={"name": "视频升级作者"}, headers=headers).json()["id"]
    project = client.post("/api/v1/content-projects", json={"title": "旧视频升级"}, headers=headers).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project}/units", json={"title": "旧镜头", "persona_id": persona, "modality": "video"}, headers=headers).json()["id"]
    path = f"/api/v1/content-projects/{project}/units/{unit}/master-revisions"
    legacy = {"title": "旧稿", "script": "原有口播", "shots": [{"id": "shot-1", "order": 0, "label": "旧镜头"}]}
    response = client.post(path, json={"idempotency_key": "legacy-video", "payload_schema": "video.master.v1", "payload": legacy}, headers=headers)
    assert response.status_code == 200, response.text
    return path, headers, response.json()


def test_video_v1_upgrade_preview_reports_only_stored_facts_and_missing_v2_fields(client):
    path, headers, source = _legacy_video_master(client)
    preview_response = client.get(f"{path}/{source['id']}/video-v2-upgrade-preview", headers=headers)
    assert preview_response.status_code == 200, preview_response.text
    preview = preview_response.json()
    assert preview["source_payload_hash"] == source["payload_hash"]
    assert preview["source_fields"]["script"] == "原有口播"
    assert preview["source_fields"]["shots"] == [{"id": "shot-1", "order": 0}]
    assert "aspect_ratio_requires_explicit_input" in preview["warnings"]
    assert "timeline_requires_explicit_input" in preview["warnings"]
    assert preview["payload"] is None


def test_video_v1_upgrade_requires_acknowledged_complete_document_and_preserves_history(client, db_session):
    from app.models import ContentMasterRevision

    path, headers, source = _legacy_video_master(client)
    preview = client.get(f"{path}/{source['id']}/video-v2-upgrade-preview", headers=headers).json()
    document = _document()
    document["script"]["blocks"][0]["text"] = "原有口播"
    body = {
        "expected_revision": 1, "expected_payload_hash": source["payload_hash"],
        "expected_context_hash": preview["current_context_hash"], "idempotency_key": "explicit-video-upgrade",
        "payload": document, "asset_refs": [], "evidence_refs": [],
        "acknowledged_warnings": preview["warnings"],
    }
    url = f"{path}/{source['id']}/video-v2-upgrade"
    direct = client.post(path, json={"idempotency_key": "implicit-video-upgrade", "expected_revision": 1, "payload_schema": "video.master.v2", "payload": document}, headers=headers)
    assert direct.status_code == 409
    unacknowledged = client.post(url, json={**body, "acknowledged_warnings": []}, headers=headers)
    assert unacknowledged.status_code == 422
    incomplete = client.post(url, json={**body, "payload": {"shots": []}}, headers=headers)
    assert incomplete.status_code == 422
    accepted = client.post(url, json=body, headers=headers)
    assert accepted.status_code == 200, accepted.text
    child = accepted.json()
    assert child["payload_schema"] == "video.master.v2"
    assert child["source_kind"] == "explicit_upgrade"
    assert child["parent_revision_id"] == source["id"]
    assert child["payload"] == document
    assert child["edit_summary"]["conversion_warnings"] == preview["warnings"]
    assert len(child["edit_summary"]["upgrade_request"]["request_hash"]) == 64
    assert "payload" not in child["edit_summary"]["upgrade_request"]
    assert client.post(url, json=body, headers=headers).json()["id"] == child["id"]
    assert client.get(f"{path}/{source['id']}", headers=headers).json()["payload_hash"] == source["payload_hash"]
    reverse = client.post(path, json={"idempotency_key": "reverse-video-schema", "expected_revision": 2, "payload_schema": "video.master.v1", "payload": source["payload"]}, headers=headers)
    assert reverse.status_code == 409
    assert reverse.json()["detail"]["code"] == "explicit_master_upgrade_required"
    wrong_source = client.post(f"{path}/{child['id']}/video-v2-upgrade", json={**body, "expected_revision": 2, "idempotency_key": "wrong-source"}, headers=headers)
    assert wrong_source.status_code == 409
    assert wrong_source.json()["detail"]["code"] == "video_v1_upgrade_source_required"
    assert db_session.query(ContentMasterRevision).filter_by(content_unit_id=source["content_unit_id"]).count() == 2


@pytest.mark.parametrize("change,expected_code", [
    ("source_hash", "master_upgrade_source_conflict"),
    ("context_hash", "master_upgrade_source_conflict"),
    ("script", "legacy_script_changed_during_upgrade"),
    ("shot", "legacy_shots_changed_during_upgrade"),
    ("render", "video_upgrade_render_requires_new_attestation"),
])
def test_video_v1_upgrade_rejects_stale_or_unsafe_child_without_history(client, db_session, change, expected_code):
    from app.models import ContentMasterRevision

    path, headers, source = _legacy_video_master(client)
    preview = client.get(f"{path}/{source['id']}/video-v2-upgrade-preview", headers=headers).json()
    document = _document()
    document["script"]["blocks"][0]["text"] = "原有口播"
    body = {
        "expected_revision": 1, "expected_payload_hash": source["payload_hash"],
        "expected_context_hash": preview["current_context_hash"], "idempotency_key": f"unsafe-{change}",
        "payload": document, "asset_refs": [], "evidence_refs": [], "acknowledged_warnings": preview["warnings"],
    }
    if change == "source_hash":
        body["expected_payload_hash"] = "0" * 64
    elif change == "context_hash":
        body["expected_context_hash"] = "0" * 64
    elif change == "script":
        document["script"]["blocks"][0]["text"] = "改写旧稿"
    elif change == "shot":
        document["shots"][0]["id"] = "other-shot"
        document["timeline"]["tracks"][0]["items"][0]["shot_id"] = "other-shot"
    else:
        document["render_asset_ref"] = {"material_revision_id": 42}
    response = client.post(f"{path}/{source['id']}/video-v2-upgrade", json=body, headers=headers)
    assert response.status_code in {409, 422}, response.text
    assert response.json()["detail"]["code"] == expected_code
    assert db_session.query(ContentMasterRevision).filter_by(content_unit_id=source["content_unit_id"]).count() == 1


def test_video_v1_upgrade_rejects_stale_head_and_idempotency_reuse(client, db_session):
    from app.models import ContentMasterRevision

    path, headers, source = _legacy_video_master(client)
    preview = client.get(f"{path}/{source['id']}/video-v2-upgrade-preview", headers=headers).json()
    document = _document()
    document["script"]["blocks"][0]["text"] = "原有口播"
    intent = {
        "expected_revision": 1, "expected_payload_hash": source["payload_hash"],
        "expected_context_hash": preview["current_context_hash"], "idempotency_key": "upgrade-retry",
        "payload": document, "asset_refs": [], "evidence_refs": [], "acknowledged_warnings": preview["warnings"],
    }
    url = f"{path}/{source['id']}/video-v2-upgrade"
    accepted = client.post(url, json=intent, headers=headers)
    assert accepted.status_code == 200, accepted.text
    changed = client.post(url, json={**intent, "expected_revision": 2}, headers=headers)
    assert changed.status_code == 409
    assert changed.json()["detail"]["code"] == "master_upgrade_idempotency_conflict"
    stale = client.post(url, json={**intent, "idempotency_key": "late-upgrade"}, headers=headers)
    assert stale.status_code == 409
    assert stale.json()["detail"]["code"] == "master_upgrade_source_conflict"
    assert db_session.query(ContentMasterRevision).filter_by(content_unit_id=source["content_unit_id"]).count() == 2


def _frozen_video_candidate():
    from app.models import ContentAsset
    from app.services.candidates import candidate_hash

    document = _document()
    document["render_asset_ref"] = {"material_revision_id": 42}
    video_hash = "a" * 64
    profile = {"source": "profile", "version_id": 7, "artifact_kind": "video", "video_requirements": {}, "media_requirements": {}}
    asset = {"id": 9, "material_revision_id": 42, "content_hash": video_hash, "role": "render_output", "slot_key": "final", "sort_order": 0, "placement": {"render": "final"}, "rights_snapshot": {}}
    input_snapshot = {
        "project_id": 1, "unit_id": 2, "schema": "video.master.v2", "context_hash": "b" * 64,
        "payload": {key: value for key, value in document.items() if key != "render_asset_ref"},
        "assets": [], "evidence": [], "video_profile": profile,
    }
    input_hash = hashlib.sha256(json.dumps(input_snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    output = {"material_revision_id": 42, "content_hash": video_hash, "mime_type": "video/mp4", "canvas_id": None, "rights_snapshot": {}}
    manifest = {
        "schema_version": 4, "project": {"id": 1, "unit_id": 2, "modality": "video"},
        "content_master": {"payload_schema": "video.master.v2", "payload_hash": hashlib.sha256(json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest(), "context_hash": "b" * 64},
        "content": document, "assets": [asset], "evidence_refs": [],
        "render": {"status": "ready", "origin": "manual", "attested_by": "editor@studio.local", "render_input_hash": input_hash, "video_profile": profile, "outputs": [output]},
        "production": {"edit_summary": {"render_attestation": {"origin": "manual", "confirmed": True, "render_input_hash": input_hash, "attested_by": "editor@studio.local", "outputs": [{"material_revision_id": 42, "content_hash": video_hash, "canvas_id": None}]}}},
    }
    return ContentAsset(title="Video", channel="video", candidate_manifest_json=manifest, candidate_hash=candidate_hash(manifest))


def test_frozen_video_v2_accepts_canonical_exact_manual_render():
    from app.services.project_review_projection import candidate_preview

    preview = candidate_preview(_frozen_video_candidate())
    assert preview["render"]["outputs"][0]["material_revision_id"] == 42


@pytest.mark.parametrize("change", [
    lambda manifest: manifest["assets"].clear(),
    lambda manifest: manifest["assets"].append(deepcopy(manifest["assets"][0])),
    lambda manifest: manifest["assets"][0].update({"slot_key": "other"}),
    lambda manifest: manifest["assets"][0].update({"content_hash": "f" * 64}),
    lambda manifest: manifest["render"]["outputs"][0].update({"mime_type": "image/png"}),
    lambda manifest: manifest["render"].update({"attested_by": "other@studio.local"}),
    lambda manifest: manifest["content"].update({"unknown": True}),
    lambda manifest: manifest["content_master"].update({"payload_hash": "f" * 64}),
    lambda manifest: manifest["render"].update({"render_input_hash": "f" * 64}),
    lambda manifest: manifest["production"]["edit_summary"]["render_attestation"].update({"outputs": []}),
])
def test_frozen_video_v2_rejects_cross_field_tampering_even_with_rehashed_candidate(change):
    from app.services.candidates import candidate_hash
    from app.services.project_review_projection import candidate_preview

    asset = _frozen_video_candidate()
    change(asset.candidate_manifest_json)
    asset.candidate_hash = candidate_hash(asset.candidate_manifest_json)
    with pytest.raises(HTTPException) as exc:
        candidate_preview(asset)
    assert exc.value.status_code == 409
    assert exc.value.detail["code"] == "frozen_candidate_integrity_failed"


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


@pytest.mark.parametrize("empty,expected", [(False, "pass"), (True, "incomplete")])
def test_video_v2_structure_and_timeline_checks_use_append_only_master_runs(client, db_session, empty, expected):
    from app.models import ContentMasterCheckRun

    headers = {"X-Studio-User": f"video-checks-{empty}@studio.local"}
    persona = client.post("/api/v1/content-personas", json={"name": "视频检查作者"}, headers=headers).json()["id"]
    project = client.post("/api/v1/content-projects", json={"title": "视频检查"}, headers=headers).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project}/units", json={"title": "短片", "persona_id": persona, "modality": "video"}, headers=headers).json()["id"]
    path = f"/api/v1/content-projects/{project}/units/{unit}/master-revisions"
    document = _document()
    if empty:
        document["script"]["blocks"] = []
        document["shots"] = []
        document["timeline"] = {"duration_ms": 0, "tracks": []}
        document["subtitles"]["cues"] = []
    saved = client.post(path, json={"idempotency_key": f"check-{empty}", "payload_schema": "video.master.v2", "payload": document}, headers=headers)
    assert saved.status_code == 200, saved.text
    master_id = saved.json()["id"]
    run = client.post(f"{path}/{master_id}/checks", headers=headers)
    assert run.status_code == 200, run.text
    checks = {item["check_kind"]: item for item in run.json()["items"]}
    assert checks["video_structure"]["status"] == expected
    assert checks["video_timeline"]["status"] == expected
    assert checks["video_structure"]["report"]["coverage"]["deterministic"] == "complete"
    assert checks["video_timeline"]["report"]["coverage"]["deterministic"] == "complete"
    assert checks["video_identity"]["status"] != "pass"
    assert checks["video_identity"]["report"]["reasons"] == ["identity_profile_invalid"]
    assert checks["video_identity"]["report"]["coverage"]["semantic"] == "unavailable"
    assert checks["video_platform"]["status"] != "pass"
    current = {item["check_kind"]: item for item in client.get(f"{path}/{master_id}/checks/current", headers=headers).json()["items"]}
    assert current["video_structure"]["is_current"] is True
    assert current["video_timeline"]["is_current"] is True
    assert db_session.query(ContentMasterCheckRun).filter_by(master_revision_id=master_id).count() == len(checks)


def test_video_identity_explicit_phrase_blocks_but_visual_and_audio_remain_unverified(monkeypatch):
    checks = importlib.import_module("app.services.video_master_checks")
    monkeypatch.setattr(checks, "_semantic_review", lambda *args, **kwargs: ([], {"semantic": "verified"}))
    snapshot = SimpleNamespace(id=7, checksum="i" * 64, effective_profile_json={"expression_style": {"forbidden_phrases": ["开场"]}})
    db = SimpleNamespace(get=lambda model, key: snapshot)
    master = SimpleNamespace(identity_snapshot_id=7)
    status, report = checks._identity(db, master, _canonical(_document()), {"metadata": {"semantic": {"configured": True}}})
    assert status == "blocker"
    assert report["issues"][0]["reason"] == "explicit_identity_forbidden_phrase"
    assert report["coverage"]["semantic"] == "verified"
    assert report["coverage"]["visual_semantics"] == "unavailable"
    assert report["coverage"]["audio_semantics"] == "unavailable"


def test_video_identity_verified_text_is_only_warning_when_media_unverified(monkeypatch):
    checks = importlib.import_module("app.services.video_master_checks")
    monkeypatch.setattr(checks, "_semantic_review", lambda *args, **kwargs: ([], {"semantic": "verified"}))
    snapshot = SimpleNamespace(id=7, checksum="i" * 64, effective_profile_json={"expression_style": {"forbidden_phrases": []}})
    db = SimpleNamespace(get=lambda model, key: snapshot)
    master = SimpleNamespace(identity_snapshot_id=7)
    status, report = checks._identity(db, master, _canonical(_document()), {"metadata": {"semantic": {"configured": True}}})
    assert status == "warning"
    assert report["coverage"]["semantic"] == "verified"
    assert report["coverage"]["visual_semantics"] == "unavailable"
    assert report["coverage"]["audio_semantics"] == "unavailable"


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


@pytest.mark.parametrize("mutation", [
    lambda doc: doc["shots"][0].update({"duration_ms": 5_000}),
    lambda doc: doc["shots"][0].update({"duration_ms": 2_000}),
])
def test_video_v2_rejects_shot_and_timeline_duration_inconsistency(mutation):
    payload = _document()
    mutation(payload)
    with pytest.raises(ValueError, match="video_shot_timeline_duration_invalid"):
        _canonical(payload)


@pytest.mark.parametrize("kind", ["audio", "music"])
def test_video_v2_rejects_unbound_placed_audio(kind):
    payload = _document()
    payload["timeline"]["tracks"].append({
        "id": "sound", "order": 1, "kind": kind,
        "items": [{"id": "sound-1", "order": 0, "start_ms": 0, "end_ms": 2_000}],
    })
    with pytest.raises(ValueError, match="video_audio_placement_unbound"):
        _canonical(payload)


def test_video_v2_allows_empty_audio_track_and_whole_composition_voice_music():
    payload = _document()
    payload["timeline"]["tracks"].append({"id": "sound", "order": 1, "kind": "audio", "items": []})
    payload["voice"] = {"mode": "recorded", "material_revision_id": 18}
    payload["music"] = {"material_revision_id": 19}
    assert _canonical(payload) == payload


def test_video_v2_rejects_overlapping_subtitle_cues():
    payload = _document()
    payload["subtitles"]["cues"].append({"id": "cue-2", "order": 1, "text": "重叠", "start_ms": 1_000, "end_ms": 3_000})
    with pytest.raises(ValueError, match="video_cue_overlap"):
        _canonical(payload)


@pytest.mark.parametrize("overlay", [
    {"id": "overlay-1", "order": 0, "text": "字幕条", "start_ms": 0, "end_ms": 1_000, "x": 0.5},
    {"id": "overlay-1", "order": 0, "text": "", "start_ms": 0, "end_ms": 1_000, "x": 0.5, "y": 0.5},
])
def test_video_v2_overlay_requires_exact_position_and_visible_text(overlay):
    payload = _document()
    payload["overlays"] = [overlay]
    with pytest.raises(ValueError, match="video_overlay_(position|text)_invalid"):
        _canonical(payload)


def test_video_v2_overlay_keeps_explicit_bounded_position():
    payload = _document()
    payload["overlays"] = [{"id": "overlay-1", "order": 0, "text": "重点", "start_ms": 0, "end_ms": 1_000, "x": 0.25, "y": 0.75}]
    assert _canonical(payload)["overlays"] == payload["overlays"]


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


def test_video_v2_preview_projects_exact_saved_structure_without_render_claim(client):
    headers = {"X-Studio-User": "video-preview@studio.local"}
    persona = client.post("/api/v1/content-personas", json={"name": "预览作者"}, headers=headers).json()["id"]
    project = client.post("/api/v1/content-projects", json={"title": "预览项目"}, headers=headers).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project}/units", json={"title": "视频单元", "persona_id": persona, "modality": "video"}, headers=headers).json()["id"]
    path = f"/api/v1/content-projects/{project}/units/{unit}/master-revisions"
    document = _document()
    document["overlays"] = [{"id": "overlay-1", "order": 0, "text": "重点", "start_ms": 0, "end_ms": 1_000, "x": 0.25, "y": 0.75}]
    saved = client.post(path, json={"idempotency_key": "preview-one", "payload_schema": "video.master.v2", "payload": document}, headers=headers)
    assert saved.status_code == 200, saved.text
    preview = client.get(f"{path}/{saved.json()['id']}/readiness", headers=headers).json()["preview"]
    assert preview["kind"] == "local_assembly_preview"
    assert preview["script_blocks"] == document["script"]["blocks"]
    assert preview["shots"] == document["shots"]
    assert preview["timeline"] == document["timeline"]
    assert preview["subtitles"] == document["subtitles"]
    assert preview["overlays"] == document["overlays"]
    assert preview["final_render_verified"] is False


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
    checked = client.post(f"{path}/{saved.json()['id']}/checks", headers=headers)
    assert checked.status_code == 200, checked.text
    platform = next(item for item in checked.json()["items"] if item["check_kind"] == "video_platform")
    assert platform["status"] == "blocker"
    assert "video_shot_count_above_profile_maximum" in platform["report"]["reasons"]
    db_session.add(ChannelTemplateVersion(
        channel="short_video_fixture", version=2, name="短视频新版", status="published",
        profile_json={"content_forms": {"short": {"artifact_kind": "video", "video_requirements": {"max_shots": 2}}}},
    ))
    db_session.commit()
    current = {item["check_kind"]: item for item in client.get(f"{path}/{saved.json()['id']}/checks/current", headers=headers).json()["items"]}
    assert current["video_platform"]["is_current"] is False
    assert current["video_platform"]["status"] == "stale"


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
