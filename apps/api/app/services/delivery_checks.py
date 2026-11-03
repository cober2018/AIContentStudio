"""Per-shot review hints on a delivered 小样 / 成片: exposure, brightness jumps between shots, uneven dialogue, live shots rendered brighter or darker than
their source; on the 成片 also its color tags and whether the cover matches its opening.

Readings follow the 导演稿 timeline so a hint can name the shot. They are warnings for the reviewer, never a rejection.
"""

import json
import re
import statistics
import subprocess
import time
from contextlib import contextmanager

from sqlalchemy.orm.attributes import flag_modified

from .creative_contracts import SHOT_CHECKS_CHARS

KEY = "delivery_checks"
DEFAULTS = {"overexposed_mean_luma": 180, "overexposed_clipped_percent": 5.0, "brightness_jump_luma": 40, "dialogue_spread_lu": 6.0, "cover_mismatch_mean": 6,
            "source_brightness_diff": 8, "source_highlight_diff": 5}
LIMITS = {"overexposed_mean_luma": (100, 255), "overexposed_clipped_percent": (0.1, 100), "brightness_jump_luma": (5, 255), "dialogue_spread_lu": (1, 30),
          "cover_mismatch_mean": (1, 100), "source_brightness_diff": (1, 100),
          "source_highlight_diff": (1, 100)}
CLIPPED_LUMA = 250
FIXED_SPAN_MS = 3000
MAX_SPANS = 60
DEADLINE_SECONDS = 90
# ebur128 gates out anything quieter; a span below this is music bed or silence, not speech.
SILENT_LUFS = -45.0
_FRAME_WIDTH = 160
SRGB_TAGS = {"color_primaries": "bt709", "color_transfer": "iec61966-2-1", "color_space": "bt709"}
# The cover is the 成片's opening frame, so it is looked for only within the first half second.
COVER_FRAMES_MS = (0, 100, 200, 300, 400, 500)
_COVER_WIDTH = 64
# Decoded HLG / PQ frames do not look like what the phone shows, so comparing them says nothing; the exposure check covers those.
UNCOMPARABLE_TRANSFERS = {"arib-std-b67", "smpte2084"}
SOURCE_DEADLINE_SECONDS = 60
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


def _spoken(shot: dict) -> bool:
    # A line on a shot whose speaker is none is on-screen text, not speech; measuring it would read the music bed.
    return bool(shot.get("script_block_id")) and (shot.get("board") or {}).get("speaker") != "none"


def spans(director: dict, duration_ms: int) -> tuple[str, list[dict]]:
    """Shot spans from the timeline's picture track; shot lengths in order; or fixed slices when neither is usable."""
    shots = {shot.get("id"): shot for shot in director.get("shots") or [] if isinstance(shot, dict)}
    for track in (director.get("timeline") or {}).get("tracks") or []:
        items = [item for item in track.get("items") or [] if item.get("shot_id") in shots
                 and isinstance(item.get("start_ms"), int) and isinstance(item.get("end_ms"), int) and item["end_ms"] > item["start_ms"]]
        if track.get("kind") == "video" and items:
            items.sort(key=lambda item: item["start_ms"])
            return "timeline", [{"shot_id": item["shot_id"], "order": shots[item["shot_id"]].get("order", index), "start_ms": item["start_ms"],
                                 "end_ms": min(item["end_ms"], duration_ms), "spoken": _spoken(shots[item["shot_id"]])}
                                for index, item in enumerate(items[:MAX_SPANS]) if item["start_ms"] < duration_ms]
    ordered = sorted(shots.values(), key=lambda shot: shot.get("order", 0))
    if ordered and all(isinstance(shot.get("duration_ms"), int) and shot["duration_ms"] > 0 for shot in ordered):
        result, start = [], 0
        for index, shot in enumerate(ordered[:MAX_SPANS]):
            if start >= duration_ms:
                break
            result.append({"shot_id": shot["id"], "order": shot.get("order", index), "start_ms": start,
                           "end_ms": min(start + shot["duration_ms"], duration_ms), "spoken": _spoken(shot)})
            start += shot["duration_ms"]
        return "shots", result
    return "fixed", [{"shot_id": None, "order": index, "start_ms": start, "end_ms": min(start + FIXED_SPAN_MS, duration_ms), "spoken": True}
                     for index, start in enumerate(range(0, duration_ms, FIXED_SPAN_MS)) if index < MAX_SPANS]


def _frame(fd: int, at_ms: int) -> tuple[float, float, int] | None:
    # Full range so the numbers read on the familiar 0–255 scale whatever range the file was exported in.
    done = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-protocol_whitelist", "file,pipe", "-threads", "1", "-ss", f"{at_ms / 1000:.3f}",
                           "-i", f"/dev/fd/{fd}", "-frames:v", "1", "-vf", f"scale={_FRAME_WIDTH}:-2:out_range=full,format=gray",
                           "-f", "rawvideo", "-"], pass_fds=(fd,), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=20, check=True)
    pixels = done.stdout
    if not pixels:
        return None
    counts = [0] * 256
    for value in pixels:
        counts[value] += 1
    # The 90th percentile tracks walls, white packaging and skin highlights, which an average can hide when only they get darker.
    seen, rank, p90 = 0, 0.9 * len(pixels), 255
    for level, count in enumerate(counts):
        seen += count
        if seen >= rank:
            p90 = level
            break
    return sum(pixels) / len(pixels), 100 * sum(counts[CLIPPED_LUMA:]) / len(pixels), p90


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
                    reading["luma"], reading["clipped"], reading["luma_p90"] = round(frame[0], 1), round(frame[1], 1), frame[2]
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
            "shots": [{key: shot[key] for key in ("shot_id", "order", "start_ms", "end_ms", "luma", "clipped", "luma_p90", "lufs") if key in shot} for shot in shots]}


@contextmanager
def _material(revision):
    from .material_external import is_external, open_key
    from .material_storage import LocalMaterialStorage, provider

    if is_external(revision.file_path):
        with open_key(revision.file_path) as handle:
            yield handle
        return
    storage = provider()
    if not isinstance(storage, LocalMaterialStorage):
        raise OSError("material_storage_not_local")
    with open(storage._path(revision.file_path), "rb") as handle:
        yield handle


def _transfer(fd: int) -> str:
    done = subprocess.run(["ffprobe", "-v", "error", "-protocol_whitelist", "file,pipe", "-select_streams", "v:0", "-show_entries", "stream=color_transfer",
                           "-of", "json", f"/dev/fd/{fd}"], pass_fds=(fd,), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=20, check=True)
    # JSON, not csv: phone clips carry side data that csv appends to the value.
    streams = json.loads(done.stdout[:64000]).get("streams") or [{}]
    return str(streams[0].get("color_transfer") or "")


def _source_ms(director: dict, shot: dict, revision_id: int) -> int:
    mid = (shot["start_ms"] + shot["end_ms"]) // 2
    for track in (director.get("timeline") or {}).get("tracks") or []:
        if track.get("kind") != "video":
            continue
        for item in track.get("items") or []:
            if item.get("shot_id") == shot["shot_id"] and item.get("material_revision_id") == revision_id and isinstance(item.get("start_ms"), int):
                trim = item.get("trim_start_ms") if isinstance(item.get("trim_start_ms"), int) else 0
                return max(0, trim + mid - item["start_ms"])
    return max(0, mid - shot["start_ms"])


def reported(text: str | None) -> dict[str, tuple[int, int]]:
    """The 小样 / 成片's own shot_sources (already validated on submit) as shot id → (material revision, source in-point)."""
    try:
        entries = json.loads(text) if text else []
        return {entry["shot_id"]: (entry["material_revision_id"], entry["source_in_ms"]) for entry in entries}
    except (TypeError, ValueError, KeyError):
        return {}


def manifest_clips(manifest: dict) -> dict[str, list[dict]]:
    """The edit manifest's clips per shot: where each sits in the cut, where it starts in its source and at what speed."""
    clips: dict[str, list[dict]] = {}
    for item in manifest.get("timeline") or []:
        if not isinstance(item, dict) or not all(type(item.get(key)) is int for key in ("material_revision_id", "start_ms", "end_ms", "trim_start_ms")):
            continue
        speed = item.get("speed_percent")
        clips.setdefault(item.get("shot_id"), []).append({**{key: item[key] for key in ("material_revision_id", "start_ms", "end_ms", "trim_start_ms")},
                                                          "speed": speed if type(speed) in {int, float} and 0 < speed <= 1000 else 100})
    return clips


def _located(director: dict, sources: dict, shot: dict, clips: dict, points: dict) -> tuple[int, int, str] | None:
    # The manifest is what was actually cut; the in-point reported with the cut comes next; the in-shot offset is only a guess.
    mid = (shot["start_ms"] + shot["end_ms"]) // 2
    for clip in clips.get(shot.get("shot_id")) or []:
        if clip["start_ms"] <= mid < clip["end_ms"]:
            return clip["material_revision_id"], max(0, clip["trim_start_ms"] + round((mid - clip["start_ms"]) * clip["speed"] / 100)), "manifest"
    if shot.get("shot_id") in points:
        revision_id, source_in = points[shot["shot_id"]]
        return revision_id, source_in + mid - shot["start_ms"], "reported"
    revision_id = sources.get(shot.get("shot_id"))
    return (revision_id, _source_ms(director, shot, revision_id), "estimated") if isinstance(revision_id, int) else None


def source_brightness(db, director: dict, checks: dict, points: dict | None = None, clips: dict | None = None) -> None:
    """Adds, for each shot cut from an SDR video material, the source's luma at the same moment and a warning when the delivered frame differs.

    The delivered reading is the one inspect already took at the shot's middle. Unreadable or HLG / PQ sources are left out. Each source reading
    says where its moment came from (manifest / reported / estimated), so the reviewer knows how far to trust it.
    """
    from ..models import MaterialRevision
    from .material_external import ExternalMaterialError

    sources = {shot.get("id"): shot.get("source_material_revision_id") for shot in director.get("shots") or [] if isinstance(shot, dict)}
    wanted: dict[int, list[tuple[dict, int, str]]] = {}
    for shot in checks["shots"]:
        located = _located(director, sources, shot, clips or {}, points or {}) if "luma" in shot else None
        if located:
            wanted.setdefault(located[0], []).append((shot, located[1], located[2]))
    deadline = time.monotonic() + SOURCE_DEADLINE_SECONDS
    for revision_id, shots in wanted.items():
        if time.monotonic() > deadline:
            checks["status"] = "partial"
            break
        revision = db.get(MaterialRevision, revision_id)
        if revision is None or not (revision.mime_type or "").startswith("video/") or not revision.file_path:
            continue
        try:
            with _material(revision) as handle:
                fd = handle.fileno()
                if _transfer(fd) in UNCOMPARABLE_TRANSFERS:
                    continue
                for shot, at_ms, basis in shots:
                    if time.monotonic() > deadline:
                        checks["status"] = "partial"
                        break
                    frame = _frame(fd, at_ms)
                    if frame:
                        shot["source_luma"], shot["source_p90"], shot["source_basis"] = round(frame[0], 1), frame[2], basis
        except (OSError, ValueError, subprocess.SubprocessError, ExternalMaterialError):
            continue
    limit = checks["thresholds"]["source_brightness_diff"]
    highlight = checks["thresholds"].get("source_highlight_diff", DEFAULTS["source_highlight_diff"])
    for shot in checks["shots"]:
        if "source_luma" in shot and abs(shot["luma"] - shot["source_luma"]) > limit:
            checks["warnings"].append({"code": "source_brightness_diff", "shot_id": shot["shot_id"], "order": shot["order"], "luma": shot["luma"],
                                       "source_luma": shot["source_luma"], "diff": round(shot["luma"] - shot["source_luma"], 1),
                                       "source_basis": shot["source_basis"]})
        # A large white or bright overlay lifts the delivered highlights, so that reading can come out brighter than the source.
        if "source_p90" in shot and "luma_p90" in shot and abs(shot["luma_p90"] - shot["source_p90"]) > highlight:
            checks["warnings"].append({"code": "source_highlight_diff", "shot_id": shot["shot_id"], "order": shot["order"], "luma_p90": shot["luma_p90"],
                                       "source_p90": shot["source_p90"], "diff": shot["luma_p90"] - shot["source_p90"], "source_basis": shot["source_basis"]})


def recheck_sources(db, director: dict, stored: str, points: dict, clips: dict) -> str | None:
    """The stored 小样 / 成片 readings with the source comparison redone from the edit manifest; None when they can't be rebuilt.

    The manifest comes after the cut, so the delivered frames already read are reused and only the sources are sampled again.
    """
    try:
        checks = json.loads(stored)
        rows = checks["shots"]
        if not isinstance(rows, list) or not rows or checks.get("truncated"):
            return None
        if isinstance(rows[0], list):
            # The slimmed form keeps only [shot_id, luma, lufs, source_luma, luma_p90, source_p90]; positions come back from the timeline.
            # Readings stored before highlights were measured have four entries and get the average comparison only.
            spans_by_id = {span["shot_id"]: span for span in spans(director, 10**9)[1]}
            rows = [{**{key: spans_by_id[row[0]][key] for key in ("shot_id", "order", "start_ms", "end_ms")},
                     **({"luma": row[1]} if row[1] is not None else {}), **({"lufs": row[2]} if row[2] is not None else {}),
                     **({"luma_p90": row[4]} if len(row) > 4 and row[4] is not None else {})} for row in rows]
        shots = [{key: value for key, value in row.items() if key not in {"source_luma", "source_p90", "source_basis"}} for row in rows]
    except (TypeError, ValueError, KeyError, IndexError):
        return None
    checks = {**checks, "shots": shots, "thresholds": {**thresholds(db), **checks.get("thresholds", {})},
              "warnings": [warning for warning in checks.get("warnings") or [] if warning.get("code") not in {"source_brightness_diff", "source_highlight_diff"}]}
    source_brightness(db, director, checks, points, clips)
    return compact(checks)


def color_tags(source) -> dict | None:
    """The video stream's color tags when they are not sRGB (untagged included); None when they are or the file can't be read."""
    fd = source.fileno()
    try:
        done = subprocess.run(["ffprobe", "-v", "error", "-protocol_whitelist", "file,pipe", "-select_streams", "v:0",
                               "-show_entries", "stream=" + ",".join(SRGB_TAGS), "-of", "json", f"/dev/fd/{fd}"],
                              pass_fds=(fd,), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=20, check=True)
        stream = json.loads(done.stdout[:64000])["streams"][0]
    except (OSError, ValueError, KeyError, IndexError, subprocess.SubprocessError):
        return None
    finally:
        source.seek(0)
    found = {key: str(stream.get(key) or "unknown") for key in SRGB_TAGS}
    return None if found == SRGB_TAGS else {"code": "color_tags_not_srgb", **found}


def _rgb(fd: int, size: str, at_ms: int | None) -> bytes:
    # To RGB at full size first, then shrink: shrinking the YUV frame first would blur chroma differently from the RGB cover and read as a color difference.
    seek = ["-ss", f"{at_ms / 1000:.3f}"] if at_ms is not None else []
    done = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-protocol_whitelist", "file,pipe", "-threads", "1", *seek, "-i", f"/dev/fd/{fd}",
                           "-frames:v", "1", "-vf", f"format=rgb24,scale={size}:flags=area", "-f", "rawvideo", "-"],
                          pass_fds=(fd,), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=20, check=True)
    return done.stdout


def cover_match(cover, final, limits: dict) -> dict | None:
    """The 成片 frame in the first half second closest to the cover, with the per-channel mean difference; None when either can't be read."""
    try:
        cover_fd, final_fd = cover.fileno(), final.fileno()
        width = _COVER_WIDTH
        probe = subprocess.run(["ffprobe", "-v", "error", "-protocol_whitelist", "file,pipe", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                                "-of", "csv=p=0", f"/dev/fd/{final_fd}"], pass_fds=(final_fd,), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=20, check=True)
        final_width, final_height = (int(value) for value in probe.stdout.decode().strip().split(",")[:2])
        size = f"{width}:{max(2, round(width * final_height / final_width / 2) * 2)}"
        picture = _rgb(cover_fd, size, None)
        best = None
        for at_ms in COVER_FRAMES_MS:
            frame = _rgb(final_fd, size, at_ms)
            if not picture or len(frame) != len(picture):
                continue
            channels = [sum(abs(a - b) for a, b in zip(picture[c::3], frame[c::3])) / (len(picture) // 3) for c in range(3)]
            if best is None or sum(channels) < sum(best[1]):
                best = (at_ms, channels)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    finally:
        cover.seek(0)
        final.seek(0)
    if best is None:
        return None
    at_ms, channels = best
    mean = round(sum(channels) / 3, 1)
    return {"at_ms": at_ms, "mean": mean, "rgb": [round(value, 1) for value in channels], "threshold": limits["cover_mismatch_mean"]}


def cover_warning(check: dict | None) -> dict | None:
    return {"code": "cover_color_mismatch", **check} if check and check["mean"] > check["threshold"] else None


def compact(result: dict, limit: int = SHOT_CHECKS_CHARS) -> str:
    """Output metadata holds flat strings of bounded length; per-shot readings give way before the warnings do."""
    text = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if len(text) <= limit:
        return text
    slim = {**result, "shots": [[shot.get("shot_id"), shot.get("luma"), shot.get("lufs"), shot.get("source_luma"), shot.get("luma_p90"), shot.get("source_p90")]
                                for shot in result["shots"]]}
    text = json.dumps(slim, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if len(text) <= limit:
        return text
    slim = {**result, "shots": [], "warnings": []}
    # The source comparison is what a forgotten overlay setting shows up in, so it is the last thing to lose.
    ranked = sorted(result["warnings"], key=lambda warning: warning.get("code") not in {"source_brightness_diff", "source_highlight_diff"})
    for warning in ranked:
        trial = {**slim, "warnings": [*slim["warnings"], warning]}
        if len(json.dumps(trial, ensure_ascii=False, sort_keys=True, separators=(",", ":"))) > limit - 40:
            slim["truncated"] = True
            break
        slim = trial
    return json.dumps(slim, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
