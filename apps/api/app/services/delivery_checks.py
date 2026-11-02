"""Per-shot review hints on a delivered 小样 / 成片: exposure, brightness jumps between shots, uneven dialogue.

Readings follow the 导演稿 timeline so a hint can name the shot. They are warnings for the reviewer, never a rejection.
"""

import json
import re
import statistics
import subprocess
import time

from sqlalchemy.orm.attributes import flag_modified

KEY = "delivery_checks"
DEFAULTS = {"overexposed_mean_luma": 180, "overexposed_clipped_percent": 5.0, "brightness_jump_luma": 40, "dialogue_spread_lu": 6.0}
LIMITS = {"overexposed_mean_luma": (100, 255), "overexposed_clipped_percent": (0.1, 100), "brightness_jump_luma": (5, 255), "dialogue_spread_lu": (1, 30)}
CLIPPED_LUMA = 250
FIXED_SPAN_MS = 3000
MAX_SPANS = 60
DEADLINE_SECONDS = 90
# ebur128 gates out anything quieter; a span below this is music bed or silence, not speech.
SILENT_LUFS = -45.0
_FRAME_WIDTH = 160
_INTEGRATED = re.compile(r"Integrated loudness:\s*I:\s*(-?[0-9.]+|-inf) LUFS")


def thresholds(db) -> dict:
    from ..models import SystemSetting

    row = db.get(SystemSetting, KEY)
    saved = dict(row.value or {}) if row else {}
    return {key: saved[key] if type(saved.get(key)) in {int, float} else default for key, default in DEFAULTS.items()}


def set_thresholds(db, values: dict, actor: str | None) -> dict:
    from fastapi import HTTPException

    from ..models import SystemSetting

    current = thresholds(db)
    for key, value in values.items():
        low, high = LIMITS.get(key, (1, 0))
        if type(value) not in {int, float} or not low <= value <= high:
            raise HTTPException(422, {"code": "delivery_checks_threshold_invalid", "field": key})
        current[key] = value
    row = db.get(SystemSetting, KEY)
    if row is None:
        row = SystemSetting(key=KEY, value={})
        db.add(row)
    row.value = current
    row.updated_by = actor
    flag_modified(row, "value")
    db.commit()
    return current


def view(db) -> dict:
    return {"thresholds": thresholds(db), "defaults": DEFAULTS, "limits": {key: list(value) for key, value in LIMITS.items()}}


def spans(director: dict, duration_ms: int) -> tuple[str, list[dict]]:
    """Shot spans from the timeline's picture track; shot lengths in order; or fixed slices when neither is usable."""
    shots = {shot.get("id"): shot for shot in director.get("shots") or [] if isinstance(shot, dict)}
    for track in (director.get("timeline") or {}).get("tracks") or []:
        items = [item for item in track.get("items") or [] if item.get("shot_id") in shots
                 and isinstance(item.get("start_ms"), int) and isinstance(item.get("end_ms"), int) and item["end_ms"] > item["start_ms"]]
        if track.get("kind") == "video" and items:
            items.sort(key=lambda item: item["start_ms"])
            return "timeline", [{"shot_id": item["shot_id"], "order": shots[item["shot_id"]].get("order", index), "start_ms": item["start_ms"],
                                 "end_ms": min(item["end_ms"], duration_ms), "spoken": bool(shots[item["shot_id"]].get("script_block_id"))}
                                for index, item in enumerate(items[:MAX_SPANS]) if item["start_ms"] < duration_ms]
    ordered = sorted(shots.values(), key=lambda shot: shot.get("order", 0))
    if ordered and all(isinstance(shot.get("duration_ms"), int) and shot["duration_ms"] > 0 for shot in ordered):
        result, start = [], 0
        for index, shot in enumerate(ordered[:MAX_SPANS]):
            if start >= duration_ms:
                break
            result.append({"shot_id": shot["id"], "order": shot.get("order", index), "start_ms": start,
                           "end_ms": min(start + shot["duration_ms"], duration_ms), "spoken": bool(shot.get("script_block_id"))})
            start += shot["duration_ms"]
        return "shots", result
    return "fixed", [{"shot_id": None, "order": index, "start_ms": start, "end_ms": min(start + FIXED_SPAN_MS, duration_ms), "spoken": True}
                     for index, start in enumerate(range(0, duration_ms, FIXED_SPAN_MS)) if index < MAX_SPANS]


def _frame(fd: int, at_ms: int) -> tuple[float, float] | None:
    # Full range so the numbers read on the familiar 0–255 scale whatever range the file was exported in.
    done = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-protocol_whitelist", "file,pipe", "-threads", "1", "-ss", f"{at_ms / 1000:.3f}",
                           "-i", f"/dev/fd/{fd}", "-frames:v", "1", "-vf", f"scale={_FRAME_WIDTH}:-2:out_range=full,format=gray",
                           "-f", "rawvideo", "-"], pass_fds=(fd,), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=20, check=True)
    pixels = done.stdout
    if not pixels:
        return None
    return sum(pixels) / len(pixels), 100 * sum(1 for value in pixels if value >= CLIPPED_LUMA) / len(pixels)


def _speech(fd: int, start_ms: int, end_ms: int) -> float | None:
    if end_ms - start_ms < 400:
        return None
    done = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-protocol_whitelist", "file,pipe", "-threads", "1", "-ss", f"{start_ms / 1000:.3f}",
                           "-t", f"{(end_ms - start_ms) / 1000:.3f}", "-i", f"/dev/fd/{fd}", "-vn", "-af", "ebur128=framelog=quiet", "-f", "null", "-"],
                          pass_fds=(fd,), stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=20, check=True)
    found = _INTEGRATED.findall(done.stderr[-4096:].decode("utf-8", "replace"))
    if not found or found[-1] == "-inf":
        return None
    value = float(found[-1])
    return value if value > SILENT_LUFS else None


def inspect(source, director: dict, duration_ms: int, has_audio: bool, limits: dict) -> dict:
    fd = source.fileno()
    basis, parts = spans(director or {}, duration_ms)
    deadline = time.monotonic() + DEADLINE_SECONDS
    shots, partial = [], False
    try:
        for part in parts:
            if time.monotonic() > deadline:
                partial = True
                break
            reading = {**part}
            try:
                frame = _frame(fd, (part["start_ms"] + part["end_ms"]) // 2)
                if frame:
                    reading["luma"], reading["clipped"] = round(frame[0], 1), round(frame[1], 1)
                if has_audio and part["spoken"]:
                    level = _speech(fd, part["start_ms"], part["end_ms"])
                    if level is not None:
                        reading["lufs"] = round(level, 1)
            except (OSError, ValueError, subprocess.SubprocessError):
                pass
            shots.append(reading)
    finally:
        source.seek(0)
    warnings = []
    for shot in shots:
        if "luma" in shot and (shot["luma"] > limits["overexposed_mean_luma"] or shot["clipped"] > limits["overexposed_clipped_percent"]):
            warnings.append({"code": "shot_overexposed", "shot_id": shot["shot_id"], "order": shot["order"], "luma": shot["luma"], "clipped": shot["clipped"]})
    lit = [shot for shot in shots if "luma" in shot]
    for before, after in zip(lit, lit[1:]):
        if abs(after["luma"] - before["luma"]) > limits["brightness_jump_luma"]:
            warnings.append({"code": "shot_brightness_jump", "shot_id": after["shot_id"], "order": after["order"], "from_shot_id": before["shot_id"],
                             "from_order": before["order"], "from_luma": before["luma"], "luma": after["luma"]})
    spoken = [shot for shot in shots if "lufs" in shot]
    if len(spoken) >= 2:
        median = statistics.median(shot["lufs"] for shot in spoken)
        for shot in spoken:
            if abs(shot["lufs"] - median) > limits["dialogue_spread_lu"]:
                warnings.append({"code": "dialogue_level_uneven", "shot_id": shot["shot_id"], "order": shot["order"], "lufs": shot["lufs"],
                                 "median_lufs": round(median, 1), "diff_lu": round(shot["lufs"] - median, 1)})
    return {"status": "partial" if partial else "measured", "basis": basis, "thresholds": limits, "warnings": warnings,
            "shots": [{key: shot[key] for key in ("shot_id", "order", "start_ms", "end_ms", "luma", "clipped", "lufs") if key in shot} for shot in shots]}


def compact(result: dict, limit: int = 2000) -> str:
    """Output metadata holds flat strings of at most 2000 characters; per-shot readings give way before the warnings do."""
    text = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if len(text) <= limit:
        return text
    slim = {**result, "shots": [[shot.get("shot_id"), shot.get("luma"), shot.get("lufs")] for shot in result["shots"]]}
    text = json.dumps(slim, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if len(text) <= limit:
        return text
    slim = {**result, "shots": [], "warnings": []}
    for warning in result["warnings"]:
        trial = {**slim, "warnings": [*slim["warnings"], warning]}
        if len(json.dumps(trial, ensure_ascii=False, sort_keys=True, separators=(",", ":"))) > limit - 40:
            slim["truncated"] = True
            break
        slim = trial
    return json.dumps(slim, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
