"""Canonical editor-independent Video Master v2 document contract."""

import math
import re

from .content_harness.channel_registry import ContentFormSpec


class VideoDocumentError(ValueError):
    pass


_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,99}$")
_MAX_DURATION_MS = 8 * 60 * 60 * 1_000


def _fail(code: str) -> None:
    raise VideoDocumentError(code)


def _object(value: object, allowed: set[str], code: str) -> dict:
    if not isinstance(value, dict) or set(value) - allowed:
        _fail(code)
    return value


def _id(value: object, code: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        _fail(code)
    return value


def _int(value: object, minimum: int, maximum: int, code: str) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        _fail(code)
    return value


def _text(value: object, maximum: int, code: str) -> str:
    if not isinstance(value, str) or len(value) > maximum or "\x00" in value:
        _fail(code)
    return value


def _ordered(value: object, *, maximum: int, code: str) -> list[dict]:
    if not isinstance(value, list) or len(value) > maximum:
        _fail(code)
    ids: set[str] = set()
    orders: set[int] = set()
    for row in value:
        if not isinstance(row, dict):
            _fail(code)
        item_id = _id(row.get("id"), code)
        order = _int(row.get("order"), 0, maximum, code)
        if item_id in ids or order in orders:
            _fail(code)
        ids.add(item_id)
        orders.add(order)
    if orders != set(range(len(value))):
        _fail(code)
    return sorted(value, key=lambda row: row["order"])


def _revision_id(value: object, code: str) -> int:
    return _int(value, 1, 2**63 - 1, code)


def _ratio(value: object) -> list[int]:
    if not isinstance(value, list) or len(value) != 2:
        _fail("video_aspect_ratio_invalid")
    width = _int(value[0], 1, 8192, "video_aspect_ratio_invalid")
    height = _int(value[1], 1, 8192, "video_aspect_ratio_invalid")
    if math.gcd(width, height) != 1:
        _fail("video_aspect_ratio_not_reduced")
    return [width, height]


def _time_bounds(row: dict, duration: int, code: str) -> None:
    start = _int(row.get("start_ms"), 0, duration, code)
    end = _int(row.get("end_ms"), 1, duration, code)
    if start >= end:
        _fail(code)


def canonical_payload(raw: object) -> dict:
    payload = _object(raw, {"title", "aspect_ratio", "script", "shots", "timeline", "voice", "subtitles", "overlays", "music", "cover", "render_asset_ref"}, "video_payload_invalid")
    result = {
        "title": _text(payload.get("title", ""), 500, "video_title_invalid"),
        "aspect_ratio": _ratio(payload.get("aspect_ratio")),
    }
    script = _object(payload.get("script"), {"blocks"}, "video_script_invalid")
    blocks = []
    for raw_block in _ordered(script.get("blocks"), maximum=200, code="video_script_blocks_invalid"):
        block = _object(raw_block, {"id", "order", "text"}, "video_script_block_invalid")
        blocks.append({"id": block["id"], "order": block["order"], "text": _text(block.get("text"), 10_000, "video_script_text_invalid")})
    result["script"] = {"blocks": blocks}
    block_ids = {block["id"] for block in blocks}

    shots = []
    for raw_shot in _ordered(payload.get("shots"), maximum=300, code="video_shots_invalid"):
        shot = _object(raw_shot, {"id", "order", "label", "purpose", "duration_ms", "script_block_id", "source_material_revision_id", "framing", "transition"}, "video_shot_invalid")
        normalized = {
            "id": shot["id"], "order": shot["order"],
            "label": _text(shot.get("label", ""), 200, "video_shot_label_invalid"),
            "duration_ms": _int(shot.get("duration_ms"), 1, _MAX_DURATION_MS, "video_shot_duration_invalid"),
        }
        if "purpose" in shot:
            normalized["purpose"] = _text(shot["purpose"], 1000, "video_shot_purpose_invalid")
        if "script_block_id" in shot:
            normalized["script_block_id"] = _id(shot["script_block_id"], "video_script_ref_invalid")
            if normalized["script_block_id"] not in block_ids:
                _fail("video_script_ref_missing")
        if "source_material_revision_id" in shot:
            normalized["source_material_revision_id"] = _revision_id(shot["source_material_revision_id"], "video_source_revision_invalid")
        if "framing" in shot:
            if shot["framing"] not in {"wide", "medium", "close", "custom"}:
                _fail("video_framing_invalid")
            normalized["framing"] = shot["framing"]
        if "transition" in shot:
            if shot["transition"] not in {"cut", "fade", "dissolve"}:
                _fail("video_transition_invalid")
            normalized["transition"] = shot["transition"]
        shots.append(normalized)
    result["shots"] = shots
    shot_ids = {shot["id"] for shot in shots}

    timeline = _object(payload.get("timeline"), {"duration_ms", "tracks"}, "video_timeline_invalid")
    duration = _int(timeline.get("duration_ms"), 0, _MAX_DURATION_MS, "video_timeline_duration_invalid")
    if duration == 0 and shots:
        _fail("video_timeline_duration_invalid")
    tracks = []
    for raw_track in _ordered(timeline.get("tracks"), maximum=16, code="video_tracks_invalid"):
        track = _object(raw_track, {"id", "order", "kind", "items"}, "video_track_invalid")
        if track.get("kind") not in {"video", "audio", "subtitle", "overlay", "music"}:
            _fail("video_track_kind_invalid")
        items = []
        for raw_item in _ordered(track.get("items"), maximum=300, code="video_timeline_items_invalid"):
            item = _object(raw_item, {"id", "order", "shot_id", "material_revision_id", "start_ms", "end_ms", "trim_start_ms", "trim_end_ms", "volume"}, "video_timeline_item_invalid")
            _time_bounds(item, duration, "video_timeline_item_time_invalid")
            normalized = {"id": item["id"], "order": item["order"], "start_ms": item["start_ms"], "end_ms": item["end_ms"]}
            if "shot_id" in item:
                normalized["shot_id"] = _id(item["shot_id"], "video_timeline_shot_invalid")
                if normalized["shot_id"] not in shot_ids or track["kind"] != "video":
                    _fail("video_timeline_shot_invalid")
            if "material_revision_id" in item:
                normalized["material_revision_id"] = _revision_id(item["material_revision_id"], "video_timeline_media_invalid")
            elif track["kind"] in {"audio", "music"}:
                _fail("video_audio_placement_unbound")
            if "trim_start_ms" in item or "trim_end_ms" in item:
                trim_start = _int(item.get("trim_start_ms", 0), 0, _MAX_DURATION_MS, "video_trim_invalid")
                trim_end = _int(item.get("trim_end_ms"), 1, _MAX_DURATION_MS, "video_trim_invalid")
                if trim_start >= trim_end or trim_end - trim_start < item["end_ms"] - item["start_ms"]:
                    _fail("video_trim_invalid")
                normalized.update({"trim_start_ms": trim_start, "trim_end_ms": trim_end})
            if "volume" in item:
                volume = item["volume"]
                if type(volume) not in (int, float) or not math.isfinite(volume) or not 0 <= volume <= 2:
                    _fail("video_volume_invalid")
                normalized["volume"] = volume
            items.append(normalized)
        tracks.append({"id": track["id"], "order": track["order"], "kind": track["kind"], "items": items})
    if any(shot["duration_ms"] > duration for shot in shots):
        _fail("video_shot_timeline_duration_invalid")
    shot_durations = {shot["id"]: shot["duration_ms"] for shot in shots}
    if any(item["end_ms"] - item["start_ms"] > shot_durations[item["shot_id"]] for track in tracks for item in track["items"] if "shot_id" in item):
        _fail("video_shot_timeline_duration_invalid")
    result["timeline"] = {"duration_ms": duration, "tracks": tracks}

    voice = _object(payload.get("voice"), {"mode", "material_revision_id"}, "video_voice_invalid")
    if voice.get("mode") not in {"none", "recorded", "tts"}:
        _fail("video_voice_invalid")
    if (voice["mode"] == "none") == ("material_revision_id" in voice):
        _fail("video_voice_revision_invalid")
    result["voice"] = {"mode": voice["mode"]}
    if "material_revision_id" in voice:
        result["voice"]["material_revision_id"] = _revision_id(voice["material_revision_id"], "video_voice_revision_invalid")

    subtitles = _object(payload.get("subtitles"), {"cues"}, "video_subtitles_invalid")
    cues = []
    previous_end = 0
    for raw_cue in _ordered(subtitles.get("cues"), maximum=1000, code="video_cues_invalid"):
        cue = _object(raw_cue, {"id", "order", "text", "start_ms", "end_ms"}, "video_cue_invalid")
        _time_bounds(cue, duration, "video_cue_time_invalid")
        if cue["start_ms"] < previous_end:
            _fail("video_cue_overlap")
        previous_end = cue["end_ms"]
        cues.append({"id": cue["id"], "order": cue["order"], "text": _text(cue.get("text"), 500, "video_cue_text_invalid"), "start_ms": cue["start_ms"], "end_ms": cue["end_ms"]})
    result["subtitles"] = {"cues": cues}

    overlays = []
    for raw_overlay in _ordered(payload.get("overlays"), maximum=300, code="video_overlays_invalid"):
        overlay = _object(raw_overlay, {"id", "order", "text", "start_ms", "end_ms", "x", "y"}, "video_overlay_invalid")
        _time_bounds(overlay, duration, "video_overlay_time_invalid")
        text = _text(overlay.get("text"), 1000, "video_overlay_text_invalid")
        if not text.strip():
            _fail("video_overlay_text_invalid")
        if "x" not in overlay or "y" not in overlay:
            _fail("video_overlay_position_invalid")
        normalized = {"id": overlay["id"], "order": overlay["order"], "text": text, "start_ms": overlay["start_ms"], "end_ms": overlay["end_ms"]}
        for coordinate in ("x", "y"):
            if coordinate in overlay:
                value = overlay[coordinate]
                if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
                    _fail("video_overlay_position_invalid")
                normalized[coordinate] = value
        overlays.append(normalized)
    result["overlays"] = overlays

    for field in ("music", "cover"):
        value = _object(payload.get(field), {"material_revision_id"}, f"video_{field}_invalid")
        result[field] = {"material_revision_id": _revision_id(value["material_revision_id"], f"video_{field}_invalid")} if "material_revision_id" in value else {}
    if "render_asset_ref" in payload:
        ref = _object(payload["render_asset_ref"], {"material_revision_id"}, "video_render_ref_invalid")
        result["render_asset_ref"] = {"material_revision_id": _revision_id(ref.get("material_revision_id"), "video_render_ref_invalid")}
    return result


def legacy_upgrade_preview(payload: dict, asset_refs: list[dict], evidence_refs: list[dict]) -> dict:
    warnings = ["aspect_ratio_requires_explicit_input", "timeline_requires_explicit_input", "shot_durations_require_explicit_input"]
    title = payload.get("title")
    script = payload.get("script")
    if not isinstance(title, str) or len(title) > 500:
        warnings.append("legacy_title_requires_review")
        title = None
    if not isinstance(script, str):
        warnings.append("legacy_script_requires_review")
        script = None
    if any(set(shot) - {"id", "order"} for shot in payload.get("shots", [])) or set(payload) - {"title", "script", "shots"}:
        warnings.append("legacy_fields_require_review")
    if asset_refs or evidence_refs:
        warnings.append("legacy_refs_require_explicit_mapping")
    if payload.get("render_asset_ref") or any(ref.get("role") == "render_output" for ref in asset_refs):
        warnings.append("legacy_render_requires_new_attestation")
    return {
        "payload": None,
        "source_fields": {"title": title, "script": script, "shots": [{"id": shot["id"], "order": index} for index, shot in enumerate(payload.get("shots", []))]},
        "warnings": warnings,
    }


def profile_reasons(form: ContentFormSpec, document: dict) -> list[str]:
    if form.source != "profile" or form.artifact_kind != "video" or form.profile_version_id is None:
        return ["video_profile_unavailable"]
    rules = form.video_requirements
    allowed = {"max_duration_ms", "allowed_aspect_ratios", "max_shots", "subtitle_required", "cover_required"}
    if not isinstance(rules, dict) or set(rules) - allowed:
        return ["video_profile_rules_invalid"]
    maximum_duration = rules.get("max_duration_ms")
    maximum_shots = rules.get("max_shots")
    if maximum_duration is not None and (type(maximum_duration) is not int or not 1 <= maximum_duration <= _MAX_DURATION_MS):
        return ["video_profile_rules_invalid"]
    if maximum_shots is not None and (type(maximum_shots) is not int or not 1 <= maximum_shots <= 300):
        return ["video_profile_rules_invalid"]
    ratios = rules.get("allowed_aspect_ratios")
    if ratios is not None:
        if not isinstance(ratios, list) or not 1 <= len(ratios) <= 50:
            return ["video_profile_rules_invalid"]
        try:
            if any(_ratio(pair) != pair for pair in ratios):
                return ["video_profile_rules_invalid"]
        except VideoDocumentError:
            return ["video_profile_rules_invalid"]
    for key in ("subtitle_required", "cover_required"):
        if key in rules and type(rules[key]) is not bool:
            return ["video_profile_rules_invalid"]
    media_rules = form.media_requirements
    if not isinstance(media_rules, dict) or set(media_rules) - {"cover", "inline"} or any(value not in {"required", "optional"} for value in media_rules.values()):
        return ["video_profile_rules_invalid"]
    reasons = []
    if maximum_duration is not None and document["timeline"]["duration_ms"] > maximum_duration:
        reasons.append("video_duration_above_profile_maximum")
    if ratios is not None and document["aspect_ratio"] not in ratios:
        reasons.append("video_aspect_ratio_not_allowed")
    if maximum_shots is not None and len(document["shots"]) > maximum_shots:
        reasons.append("video_shot_count_above_profile_maximum")
    if rules.get("subtitle_required") and not document["subtitles"]["cues"]:
        reasons.append("video_subtitle_required")
    if (rules.get("cover_required") or media_rules.get("cover") == "required") and "material_revision_id" not in document["cover"]:
        reasons.append("video_cover_required")
    if media_rules.get("inline") == "required" and not any("source_material_revision_id" in shot for shot in document["shots"]):
        reasons.append("video_inline_media_required")
    return reasons


def _expected_media(document: dict) -> list[dict]:
    expected: list[dict] = []

    def add(role: str, slot: str, revision_id: int, placement: dict) -> None:
        expected.append({"material_revision_id": revision_id, "role": role, "slot_key": slot, "sort_order": len(expected), "placement": placement})

    for shot in document["shots"]:
        if "source_material_revision_id" in shot:
            add("shot_source", shot["id"], shot["source_material_revision_id"], {"shot_id": shot["id"]})
    for track in document["timeline"]["tracks"]:
        for item in track["items"]:
            if "material_revision_id" in item:
                placement = {"track_id": track["id"], "item_id": item["id"], "start_ms": item["start_ms"], "end_ms": item["end_ms"]}
                for key in ("trim_start_ms", "trim_end_ms", "volume"):
                    if key in item:
                        placement[key] = item[key]
                add("timeline_media", item["id"], item["material_revision_id"], placement)
    for field, role in (("voice", "voice_audio"), ("music", "music_audio"), ("cover", "cover_image")):
        if "material_revision_id" in document[field]:
            add(role, field, document[field]["material_revision_id"], {field: "main"})
    if "render_asset_ref" in document:
        add("render_output", "final", document["render_asset_ref"]["material_revision_id"], {"render": "final"})
    return expected


def validate_references(payload: object, asset_refs: object, evidence_refs: object) -> None:
    document = canonical_payload(payload)
    if not isinstance(asset_refs, list) or not isinstance(evidence_refs, list) or len(asset_refs) != len(_expected_media(document)):
        _fail("video_reference_count_mismatch")
    for actual, expected in zip(asset_refs, _expected_media(document), strict=True):
        if not isinstance(actual, dict) or set(actual) - {*expected, "content_hash"}:
            _fail("video_asset_placement_mismatch")
        if any(actual.get(key) != value for key, value in expected.items()):
            _fail("video_asset_placement_mismatch")
        content_hash = actual.get("content_hash")
        if not isinstance(content_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", content_hash):
            _fail("video_asset_hash_invalid")
