"""Canonical editor-independent Video Master v2 document contract."""

import hashlib
import json
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


def _enum(value: object, allowed: set[str], code: str) -> str:
    if not isinstance(value, str) or value not in allowed:
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


def canonical_production(value: object) -> dict:
    row = _object(value, {"schema", "source_mode", "web_provider", "prompt", "reference_material_revision_id", "prompt_reference", "requested_generation_duration_ms", "audio_intent", "continuity_reference"}, "video_production_invalid")
    if row.get("schema") not in ("video.shot-production.v1", "video.shot-production.v2"):
        _fail("video_production_schema_invalid")
    result = {"schema": row["schema"], "source_mode": _enum(row.get("source_mode"), {"existing", "api_image", "web_video", "ae"}, "video_production_mode_invalid")}
    if "prompt" in row:
        result["prompt"] = _text(row["prompt"], 2000, "video_production_prompt_invalid")
    if "reference_material_revision_id" in row:
        result["reference_material_revision_id"] = _revision_id(row["reference_material_revision_id"], "video_production_reference_invalid")
    if "prompt_reference" in row:
        if row["schema"] != "video.shot-production.v2":
            _fail("video_production_prompt_reference_invalid")
        reference = _object(row["prompt_reference"], {"revision_id", "content_hash"}, "video_production_prompt_reference_invalid")
        content_hash = reference.get("content_hash")
        if not isinstance(content_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", content_hash):
            _fail("video_production_prompt_reference_invalid")
        result["prompt_reference"] = {"revision_id": _revision_id(reference.get("revision_id"), "video_production_prompt_reference_invalid"), "content_hash": content_hash}
    if "continuity_reference" in row:
        reference = _object(row["continuity_reference"], {"shot_id", "material_revision_id", "content_hash", "kind"}, "video_continuity_reference_invalid")
        content_hash = reference.get("content_hash")
        if not isinstance(content_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", content_hash):
            _fail("video_continuity_reference_invalid")
        result["continuity_reference"] = {
            "shot_id": _id(reference.get("shot_id"), "video_continuity_reference_invalid"),
            "material_revision_id": _revision_id(reference.get("material_revision_id"), "video_continuity_reference_invalid"),
            "content_hash": content_hash,
            "kind": _enum(reference.get("kind"), {"composition"}, "video_continuity_kind_unsupported"),
        }
    if result["source_mode"] == "web_video":
        result["web_provider"] = _enum(row.get("web_provider"), {"grok", "gemini"}, "video_web_provider_invalid")
        if row["schema"] == "video.shot-production.v1" and not result.get("prompt", "").strip():
            _fail("video_production_prompt_required")
        result["requested_generation_duration_ms"] = _int(row.get("requested_generation_duration_ms"), 1000, 15000, "video_generation_duration_invalid")
        result["audio_intent"] = _enum(row.get("audio_intent", "mute"), {"mute", "keep"}, "video_audio_intent_invalid")
    elif any(key in row for key in ("web_provider", "requested_generation_duration_ms", "audio_intent")):
        _fail("video_web_fields_require_web_mode")
    return result


def validate_continuity_dependencies(shots: list[dict]) -> None:
    by_id = {shot["id"]: shot for shot in shots}
    edges = {}
    for shot in shots:
        reference = (shot.get("production") or {}).get("continuity_reference")
        if not reference:
            continue
        target = reference["shot_id"]
        if target == shot["id"]:
            _fail("video_continuity_self_reference")
        if target not in by_id:
            _fail("video_continuity_shot_missing")
        edges[shot["id"]] = target
    completed = set()
    for start in edges:
        visiting = set()
        current = start
        while current in edges and current not in completed:
            if current in visiting:
                _fail("video_continuity_cycle")
            visiting.add(current)
            current = edges[current]
        completed.update(visiting)


def canonical_postproduction(value: object, shot_ids: set[str], duration: int) -> dict:
    row = _object(value, {"schema", "phase", "fps", "resolution", "ae_shot_ids", "parent_output_id", "parent_output_hash", "parent_material_revision_id", "feedback", "ae_compositions"}, "video_postproduction_invalid")
    if row.get("schema") != "video.postproduction.v1":
        _fail("video_postproduction_schema_invalid")
    result = {"schema": row["schema"], "phase": _enum(row.get("phase"), {"rough_cut", "refinement", "final"}, "video_postproduction_phase_invalid"), "fps": _int(row.get("fps", 30), 1, 60, "video_postproduction_fps_invalid")}
    resolution = row.get("resolution")
    if not isinstance(resolution, list) or len(resolution) != 2:
        _fail("video_postproduction_resolution_invalid")
    result["resolution"] = [_int(n, 16, 8192, "video_postproduction_resolution_invalid") for n in resolution]
    ae = row.get("ae_shot_ids", [])
    if not isinstance(ae, list) or len(ae) > 300 or any(not isinstance(i, str) or i not in shot_ids for i in ae) or len(set(ae)) != len(ae):
        _fail("video_ae_shot_invalid")
    result["ae_shot_ids"] = ae
    compositions = row.get("ae_compositions", [])
    if not isinstance(compositions, list) or len(compositions) != len(ae) or len(ae) > 15:
        _fail("video_ae_compositions_invalid")
    result["ae_compositions"] = []
    for index, raw in enumerate(compositions):
        comp = _object(raw, {"shot_id", "role_id", "duration_ms", "resolution", "fps", "alpha_required"}, "video_ae_compositions_invalid")
        role_id = "ae_intermediate" if len(ae) == 1 else f"ae_intermediate_{index + 1}"
        size = comp.get("resolution")
        if comp.get("shot_id") != ae[index] or comp.get("role_id", role_id) != role_id or not isinstance(size, list) or len(size) != 2 or type(comp.get("alpha_required")) is not bool:
            _fail("video_ae_compositions_invalid")
        result["ae_compositions"].append({"shot_id": ae[index], "role_id": role_id,
            "duration_ms": _int(comp.get("duration_ms"), 1, duration, "video_ae_duration_invalid"),
            "resolution": [_int(n, 16, 8192, "video_ae_resolution_invalid") for n in size],
            "fps": _int(comp.get("fps"), 1, 60, "video_ae_fps_invalid"), "alpha_required": comp["alpha_required"]})
    parent = {"parent_output_id", "parent_output_hash", "parent_material_revision_id"}
    if parent & row.keys():
        if not parent <= row.keys() or not isinstance(row["parent_output_hash"], str) or not re.fullmatch(r"[0-9a-f]{64}", row["parent_output_hash"]):
            _fail("video_feedback_parent_invalid")
        result.update({"parent_output_id": _revision_id(row["parent_output_id"], "video_feedback_parent_invalid"), "parent_output_hash": row["parent_output_hash"], "parent_material_revision_id": _revision_id(row["parent_material_revision_id"], "video_feedback_parent_invalid")})
    feedback = row.get("feedback", [])
    if not isinstance(feedback, list) or len(feedback) > 100 or (feedback and not parent <= row.keys()):
        _fail("video_feedback_invalid")
    result["feedback"] = []
    for item in feedback:
        item = _object(item, {"time_ms", "note"}, "video_feedback_invalid")
        note = _text(item.get("note"), 2000, "video_feedback_invalid")
        if not note.strip():
            _fail("video_feedback_invalid")
        result["feedback"].append({"time_ms": _int(item.get("time_ms"), 0, duration, "video_feedback_invalid"), "note": note})
    return result


def canonical_capture_plan(value: object) -> dict:
    row = _object(value, {"schema", "route", "script_structure", "script_confirmation", "task_confirmation"}, "video_capture_plan_invalid")
    if row.get("schema") != "video.capture-plan.v1":
        _fail("video_capture_plan_schema_invalid")
    result = {"schema": row["schema"]}
    if "route" in row:
        result["route"] = _enum(row["route"], {"real", "ai", "mixed"}, "video_capture_route_invalid")
    if "script_structure" in row:
        result["script_structure"] = _text(row["script_structure"], 10_000, "video_capture_script_structure_invalid")
    for field in ("script_confirmation", "task_confirmation"):
        if field not in row:
            continue
        allowed = {"source_master_revision_id", "content_hash"}
        if field == "task_confirmation":
            allowed.add("production_profile_revision_id")
        ref = _object(row[field], allowed, "video_capture_confirmation_invalid")
        digest = ref.get("content_hash")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            _fail("video_capture_confirmation_invalid")
        result[field] = {"source_master_revision_id": _revision_id(ref.get("source_master_revision_id"), "video_capture_confirmation_invalid"), "content_hash": digest}
        if field == "task_confirmation":
            result[field]["production_profile_revision_id"] = _revision_id(ref.get("production_profile_revision_id"), "video_capture_confirmation_invalid")
    return result


def capture_content_hash(document: dict, kind: str) -> str:
    plan = document.get("capture_plan") or {}
    projection = {"route": plan.get("route"), "script_structure": plan.get("script_structure", "")}
    if kind == "task":
        # Narration and adopted media evolve after filming without changing the shot instructions.
        fields = {"id", "order", "label", "purpose", "duration_ms", "framing", "transition", "filming", "production"}
        projection.update(aspect_ratio=document.get("aspect_ratio"), shots=[{key: value for key, value in shot.items() if key in fields} for shot in document.get("shots", [])])
    return hashlib.sha256(json.dumps(projection, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


BOARD_CAMERA = {"fixed", "push_in", "pull_out", "follow", "orbit", "pan"}
BOARD_SPEAKER = {"narration", "presenter", "dialogue", "none"}


def canonical_board(value: object) -> dict:
    """Storyboard columns of one shot; the spoken line stays in the script block it points to."""
    board = _object(value, {"message", "visual", "camera", "speaker", "sound", "notes", "material_request"}, "video_shot_board_invalid")
    result = {key: _text(board.get(key, ""), limit, "video_shot_board_invalid")
              for key, limit in (("message", 500), ("visual", 1000), ("sound", 500), ("notes", 500))}
    result["camera"] = _enum(board.get("camera", "fixed"), BOARD_CAMERA, "video_shot_board_invalid")
    result["speaker"] = _enum(board.get("speaker", "narration"), BOARD_SPEAKER, "video_shot_board_invalid")
    # Only present on 导演稿 written with a material request, so older masters keep their hashes.
    if "material_request" in board:
        result["material_request"] = _text(board["material_request"], 1000, "video_shot_board_invalid")
    return result


def canonical_capture_takes(value: object) -> list[dict]:
    if not isinstance(value, list) or len(value) > 100:
        _fail("video_capture_takes_invalid")
    result = []
    for raw in value:
        row = _object(raw, {"id", "source_master_revision_id", "task_content_hash", "material_revision_id", "content_hash", "state", "review_note", "trim_start_ms", "trim_end_ms"}, "video_capture_take_invalid")
        take = {"id": _id(row.get("id"), "video_capture_take_invalid"),
                "state": _enum(row.get("state"), {"pending", "usable", "reshoot", "rejected"}, "video_capture_take_state_invalid")}
        for field in ("source_master_revision_id", "material_revision_id"):
            take[field] = _revision_id(row.get(field), "video_capture_take_reference_invalid")
        for field in ("task_content_hash", "content_hash"):
            if not isinstance(row.get(field), str) or not re.fullmatch(r"[0-9a-f]{64}", row[field]):
                _fail("video_capture_take_hash_invalid")
            take[field] = row[field]
        if "review_note" in row:
            take["review_note"] = _text(row["review_note"], 4000, "video_capture_take_note_invalid")
        if "trim_start_ms" in row or "trim_end_ms" in row or take["state"] == "usable":
            take["trim_start_ms"] = _int(row.get("trim_start_ms"), 0, _MAX_DURATION_MS, "video_capture_take_trim_invalid")
            take["trim_end_ms"] = _int(row.get("trim_end_ms"), 1, _MAX_DURATION_MS, "video_capture_take_trim_invalid")
            if take["trim_end_ms"] <= take["trim_start_ms"]:
                _fail("video_capture_take_trim_invalid")
        result.append(take)
    return result


def canonical_filming(value: object) -> dict:
    text_fields = {"subject", "action", "camera_position", "angle", "focus", "evidence_requirement", "audio_note"}
    row = _object(value, text_fields | {"scene_id", "filming_order", "raw_duration_ms"}, "video_filming_invalid")
    result = {}
    if "scene_id" in row:
        result["scene_id"] = _text(row["scene_id"], 100, "video_filming_scene_invalid")
    if "filming_order" in row:
        result["filming_order"] = _int(row["filming_order"], 0, 299, "video_filming_order_invalid")
    if "raw_duration_ms" in row:
        result["raw_duration_ms"] = _int(row["raw_duration_ms"], 1, _MAX_DURATION_MS, "video_filming_duration_invalid")
    for field in sorted(text_fields):
        if field in row:
            result[field] = _text(row[field], 2000, f"video_filming_{field}_invalid")
    return result


def canonical_payload(raw: object) -> dict:
    payload = _object(raw, {"title", "aspect_ratio", "script", "shots", "timeline", "voice", "subtitles", "overlays", "music", "cover", "render_asset_ref", "postproduction", "capture_plan"}, "video_payload_invalid")
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
    if "capture_plan" in payload:
        result["capture_plan"] = canonical_capture_plan(payload["capture_plan"])
    block_ids = {block["id"] for block in blocks}

    shots = []
    for raw_shot in _ordered(payload.get("shots"), maximum=300, code="video_shots_invalid"):
        shot = _object(raw_shot, {"id", "order", "label", "purpose", "duration_ms", "script_block_id", "source_material_revision_id", "framing", "transition", "production", "filming", "capture_takes", "board"}, "video_shot_invalid")
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
            normalized["framing"] = _enum(shot["framing"], {"wide", "medium", "close", "custom"}, "video_framing_invalid")
        if "transition" in shot:
            normalized["transition"] = _enum(shot["transition"], {"cut", "fade", "dissolve"}, "video_transition_invalid")
        if "production" in shot:
            normalized["production"] = canonical_production(shot["production"])
        if "filming" in shot:
            normalized["filming"] = canonical_filming(shot["filming"])
        if "capture_takes" in shot:
            normalized["capture_takes"] = canonical_capture_takes(shot["capture_takes"])
        if "board" in shot:
            normalized["board"] = canonical_board(shot["board"])
        shots.append(normalized)
    take_ids = [take["id"] for shot in shots for take in shot.get("capture_takes", [])]
    if len(take_ids) != len(set(take_ids)):
        _fail("video_capture_take_id_duplicate")
    validate_continuity_dependencies(shots)
    result["shots"] = shots
    shot_ids = {shot["id"] for shot in shots}

    timeline = _object(payload.get("timeline"), {"duration_ms", "tracks"}, "video_timeline_invalid")
    duration = _int(timeline.get("duration_ms"), 0, _MAX_DURATION_MS, "video_timeline_duration_invalid")
    if duration == 0 and shots:
        _fail("video_timeline_duration_invalid")
    tracks = []
    for raw_track in _ordered(timeline.get("tracks"), maximum=16, code="video_tracks_invalid"):
        track = _object(raw_track, {"id", "order", "kind", "items"}, "video_track_invalid")
        _enum(track.get("kind"), {"video", "audio", "subtitle", "overlay", "music"}, "video_track_kind_invalid")
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
    _enum(voice.get("mode"), {"none", "recorded", "tts"}, "video_voice_invalid")
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
    if "postproduction" in payload:
        result["postproduction"] = canonical_postproduction(payload["postproduction"], shot_ids, duration)
        width, height = result["postproduction"]["resolution"]
        if width * result["aspect_ratio"][1] != height * result["aspect_ratio"][0]:
            _fail("video_postproduction_aspect_mismatch")
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
        for take in shot.get("capture_takes", []):
            add("capture_take", take["id"], take["material_revision_id"], {"shot_id": shot["id"], "take_id": take["id"]})
        reference = (shot.get("production") or {}).get("reference_material_revision_id")
        if reference is not None:
            add("shot_reference", shot["id"], reference, {"shot_id": shot["id"]})
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
    parent = (document.get("postproduction") or {}).get("parent_material_revision_id")
    if parent is not None:
        add("postproduction_parent", "rough_cut", parent, {"postproduction": "parent"})
    if "render_asset_ref" in document:
        add("render_output", "final", document["render_asset_ref"]["material_revision_id"], {"render": "final"})
    return expected


def validate_references(payload: object, asset_refs: object, evidence_refs: object) -> None:
    document = canonical_payload(payload)
    expected_media = _expected_media(document)
    slots = [(ref["role"], ref["slot_key"]) for ref in expected_media]
    if len(slots) != len(set(slots)):
        _fail("video_asset_slot_duplicate")
    if not isinstance(asset_refs, list) or not isinstance(evidence_refs, list) or len(asset_refs) != len(expected_media):
        _fail("video_reference_count_mismatch")
    for actual, expected in zip(asset_refs, expected_media, strict=True):
        if not isinstance(actual, dict) or set(actual) - {*expected, "content_hash"}:
            _fail("video_asset_placement_mismatch")
        if any(actual.get(key) != value for key, value in expected.items()):
            _fail("video_asset_placement_mismatch")
        content_hash = actual.get("content_hash")
        if not isinstance(content_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", content_hash):
            _fail("video_asset_hash_invalid")
