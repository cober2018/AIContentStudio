"""Video v2 document and exact-profile contract regressions."""

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
