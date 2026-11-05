"""Small tool: turn any local audio or video file into text, subtitles and illustrated notes, started through the creative MCP.

It reuses the reference-video breakdown's local tools (MLX Whisper, else the local whisper CLI, and ffmpeg scene cuts),
so nothing reaches the network or a paid model. Jobs are not tied to a project; their records live in one setting.
"""

from __future__ import annotations

import copy
import json
import re
import tempfile
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from ..models import SystemSetting
from .reference_video import BreakdownError, _run, scene_cuts, segments, transcribe

KEY = "media_transcriptions"
FOLDER = "转写"
KEEP = 100
# The MLX worker refuses audio over 10 minutes and stops after 120 s; 5-minute pieces finish inside both.
PIECE_MS = 300_000
MIN_FRAME_GAP_MS = 1000
MAX_FRAMES = 200
PARAGRAPH_GAP_MS = 1500
PARAGRAPH_CHARS = 300
MEDIA = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".ts", ".mts", ".m2ts", ".vob", ".ogv", ".3gp",
         ".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".opus", ".wma", ".aiff", ".aif"}
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="media-transcription")
_active: set[str] = set()
_lock = threading.Lock()


def _fail(status: int, code: str, message: str):
    raise HTTPException(status, {"code": code, "message": message})


def _jobs(db: Session) -> list[dict]:
    row = db.get(SystemSetting, KEY)
    return copy.deepcopy((row.value or {}).get("jobs", [])) if row else []


def _save(db: Session, jobs: list[dict]) -> None:
    row = db.get(SystemSetting, KEY)
    if row is None:
        row = SystemSetting(key=KEY, value={})
        db.add(row)
    row.value = {"jobs": jobs[:KEEP]}
    flag_modified(row, "value")
    db.commit()


def _update(db: Session, job_id: str, **values) -> None:
    jobs = _jobs(db)
    for job in jobs:
        if job["id"] == job_id:
            job.update(values)
    _save(db, jobs)


def _settled(job: dict) -> dict:
    # A restart ends the worker thread; a job left queued or running would otherwise wait forever.
    if job["status"] in {"queued", "running"}:
        with _lock:
            alive = job["id"] in _active
        if not alive:
            return {**job, "status": "failed", "error": {"code": "media_transcription_interrupted", "message": "平台重启，转写中断了，请重新提交"}}
    return job


def _probe(path: Path) -> dict:
    try:
        out = _run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,disposition",
                    "-of", "json", str(path)], 60).stdout
    except BreakdownError:
        _fail(422, "media_transcription_unreadable", "这个文件读不出音视频信息")
    data = json.loads(out)
    streams = data.get("streams", [])
    duration = round(float((data.get("format") or {}).get("duration") or 0) * 1000)
    if not any(item.get("codec_type") == "audio" for item in streams):
        _fail(422, "media_transcription_no_audio", "这个文件里没有声音，没法转文字")
    if duration <= 0:
        _fail(422, "media_transcription_unreadable", "读不出这个文件的时长")
    # Cover art in audio files is an attached picture, not footage, so it gets no screenshots.
    video = any(item.get("codec_type") == "video" and not (item.get("disposition") or {}).get("attached_pic") for item in streams)
    return {"duration_ms": duration, "video": video}


def _target(output_dir: str | None, name: str) -> Path:
    if output_dir:
        base = Path(output_dir).expanduser()
        if not base.is_absolute():
            _fail(422, "media_transcription_output_invalid", "输出文件夹要写完整路径")
    else:
        from .project_folders import PLATFORM_DIR, _writable_root

        root = _writable_root()
        if root is None:
            _fail(409, "material_library_unavailable", "素材库盘没连接")
        base = root / PLATFORM_DIR / FOLDER
    base.mkdir(parents=True, exist_ok=True)
    folder, number = base / name, 2
    # Earlier results are never overwritten; the folder is taken at once so a queued second run of the same file gets its own.
    while True:
        try:
            folder.mkdir()
            return folder
        except FileExistsError:
            folder, number = base / f"{name}-{number}", number + 1


def start(db: Session, user, path: str, output_dir: str | None = None) -> dict:
    source = Path(path.strip()).expanduser()
    if not source.is_absolute():
        _fail(422, "media_transcription_path_invalid", "请给文件的完整路径")
    if not source.is_file():
        _fail(422, "media_transcription_missing", "找不到这个文件")
    if source.suffix.lower() not in MEDIA:
        _fail(422, "media_transcription_not_media", "只支持常见的音频和视频文件")
    info = _probe(source)
    name = re.sub(r"[\\/:*?\"<>|]", "_", source.stem).strip() or "转写"
    folder = _target(output_dir, name)
    job = {"id": uuid.uuid4().hex[:12], "status": "queued", "source": str(source), "name": name, "folder": str(folder),
           "duration_ms": info["duration_ms"], "video": info["video"], "files": {}, "by": user.email,
           "started_at": datetime.now(UTC).isoformat()}
    _save(db, [job, *_jobs(db)])
    with _lock:
        _active.add(job["id"])
    _executor.submit(_execute, job["id"], source, folder, info)
    return result(db, job["id"])


def result(db: Session, job_id: str) -> dict:
    job = next((item for item in _jobs(db) if item["id"] == job_id), None)
    if job is None:
        _fail(404, "media_transcription_not_found", "没有这个转写任务")
    return _settled(job)


def listing(db: Session) -> dict:
    return {"jobs": [_settled(job) for job in _jobs(db)]}


def _execute(job_id: str, source: Path, folder: Path, info: dict) -> None:
    from ..db import SessionLocal

    try:
        with SessionLocal() as db:
            _update(db, job_id, status="running")
        try:
            summary, failure = make(source, folder, info), None
        except BreakdownError as exc:
            summary, failure = {}, {"code": "media_transcription_failed", "message": exc.message}
        except Exception as exc:  # noqa: BLE001 The page shows a failed job instead of one stuck in running.
            summary, failure = {}, {"code": "media_transcription_failed", "message": f"转写出错：{type(exc).__name__}"}
        if failure is not None:
            try:
                folder.rmdir()
            except OSError:
                pass  # keeps whatever was already written
        with SessionLocal() as db:
            _update(db, job_id, status="done" if failure is None else "failed", error=failure,
                    finished_at=datetime.now(UTC).isoformat(), **summary)
    finally:
        with _lock:
            _active.discard(job_id)


def _speech(source: Path, duration_ms: int) -> tuple[list[dict], str | None, str | None]:
    """Sentence cues over the whole file; longer files go through the 10-minute engine piece by piece."""
    if duration_ms <= PIECE_MS:
        found = transcribe(source, duration_ms)
        return found["segments"], found["engine"], found.get("reason")
    cues, engines, reasons = [], set(), []
    with tempfile.TemporaryDirectory(prefix="aics-transcribe-") as work:
        for offset in range(0, duration_ms, PIECE_MS):
            length = min(PIECE_MS, duration_ms - offset)
            piece = Path(work) / f"piece-{offset // PIECE_MS:03d}.wav"
            _run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{offset / 1000:.3f}", "-t", f"{length / 1000:.3f}", "-i", str(source),
                  "-map", "0:a:0", "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(piece)], 300)
            found = transcribe(piece, length)
            engines.add(found["engine"])
            if found.get("reason"):
                reasons.append(found["reason"])
            cues.extend({**cue, "start_ms": cue["start_ms"] + offset, "end_ms": cue["end_ms"] + offset} for cue in found["segments"])
            piece.unlink(missing_ok=True)
    engine = "、".join(sorted(item for item in engines if item)) or None
    return cues, engine, "；".join(reasons)[:300] or None


def _clock(ms: int, separator: str = ".") -> str:
    hours, rest = divmod(ms, 3_600_000)
    minutes, rest = divmod(rest, 60_000)
    seconds, millis = divmod(rest, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}{separator}{millis:03d}"


def _short(ms: int) -> str:
    hours, rest = divmod(ms // 1000, 3600)
    return f"{hours:d}:{rest // 60:02d}:{rest % 60:02d}" if hours else f"{rest // 60:02d}:{rest % 60:02d}"


def _paragraphs(cues: list[dict]) -> list[str]:
    paragraphs, current, last_end = [], "", None
    for cue in cues:
        text = cue["text"].strip()
        if current and (cue["start_ms"] - last_end >= PARAGRAPH_GAP_MS or len(current) >= PARAGRAPH_CHARS):
            paragraphs.append(current)
            current = ""
        # Whisper gives Chinese sentences without closing punctuation, so a comma keeps joined cues readable.
        if not current or re.search(r"[，。！？、；：,.!?;:]$", current):
            current += text
        else:
            current += f"，{text}" if re.search(r"[\u4e00-\u9fff]$", current) else f" {text}"
        last_end = cue["end_ms"]
    return [*paragraphs, current] if current else paragraphs


def _frames(source: Path, duration_ms: int, images: Path) -> list[dict]:
    """One picture at the start and after each scene change, spaced and capped so slides are kept without flooding the notes."""
    starts = [0]
    for cut in scene_cuts(source, duration_ms, timeout=3600):
        if cut - starts[-1] >= MIN_FRAME_GAP_MS:
            starts.append(cut)
    if len(starts) > MAX_FRAMES:
        step = len(starts) / MAX_FRAMES
        starts = [starts[int(index * step)] for index in range(MAX_FRAMES)]
    parts = segments(starts[1:], duration_ms)
    images.mkdir(parents=True, exist_ok=True)
    for part in parts:
        # A little past the cut, so the picture is the new scene rather than the transition frame.
        at = part["start_ms"] + min(500, (part["end_ms"] - part["start_ms"]) // 2)
        part["image"] = f"frame_{part['index']:04d}.jpg"
        _run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{at / 1000:.3f}", "-i", str(source), "-frames:v", "1",
              "-vf", "scale='min(1280,iw)':-2", "-q:v", "3", str(images / part["image"])], 60)
    return parts


def make(source: Path, folder: Path, info: dict) -> dict:
    duration = info["duration_ms"]
    cues, engine, reason = _speech(source, duration)
    if not cues:
        raise BreakdownError("media_transcription_empty", reason or "没听到人声")
    name = folder.name
    txt, srt, md = folder / f"{name}.txt", folder / f"{name}.srt", folder / f"{name}.md"
    txt.write_text("\n".join(cue["text"].strip() for cue in cues) + "\n", "utf-8")
    srt.write_text("\n".join(f"{index}\n{_clock(cue['start_ms'], ',')} --> {_clock(cue['end_ms'], ',')}\n{cue['text'].strip()}\n"
                             for index, cue in enumerate(cues, 1)), "utf-8")
    lines = [f"# {name}", "", f"> 来源：{source} · 时长 {_short(duration)} · 生成于 {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M')}", ""]
    frames = 0
    if info["video"]:
        parts = _frames(source, duration, folder / "images")
        frames = len(parts)
        for part in parts:
            # A cue belongs to the scene it starts in, so no sentence is split across two pictures.
            spoken = [cue for cue in cues if part["start_ms"] <= cue["start_ms"] < part["end_ms"]]
            lines += [f"## {_short(part['start_ms'])}", "", f"![画面 {_short(part['start_ms'])}](images/{part['image']})", ""]
            lines += [*(f"{paragraph}\n" for paragraph in _paragraphs(spoken))]
    else:
        lines += [f"{paragraph}\n" for paragraph in _paragraphs(cues)]
    md.write_text("\n".join(lines).rstrip() + "\n", "utf-8")
    preview = "".join(cue["text"].strip() for cue in cues)[:500]
    return {"engine": engine, "cues": len(cues), "frames": frames, "preview": preview,
            "files": {"txt": str(txt), "srt": str(srt), "md": str(md), **({"images": str(folder / "images")} if frames else {})}}


def reveal(db: Session, job_id: str) -> dict:
    import subprocess

    job = result(db, job_id)
    folder = Path(job["folder"])
    if not folder.is_dir():
        _fail(404, "media_transcription_folder_missing", "输出文件夹不在了（可能被移走，或素材盘没接）")
    subprocess.run(["open", str(folder)], check=False, timeout=10)
    return {"opened": str(folder)}
