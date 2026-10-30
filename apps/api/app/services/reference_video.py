"""Breaking down a reference video for a video work: the platform's free local part, then the third-party model's reading.

The platform runs only local tools here (no paid model): a timed transcript (local MLX Whisper, else the local whisper
CLI), scene cuts, one time-labelled frame grid per page of segments, and loudness. The third-party model reads those with
studio.video.reference-breakdown and saves the analysis, timeline and shooting list. The reference never becomes project
material, so its footage and watermark cannot reach the cut.
"""

from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from itertools import pairwise
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from ..models import MaterialRevision, SystemSetting, User

KEY = "reference_video"
FOLDER = "参考拆解"
MAX_MS = 600_000
MAX_UPLOAD = 1024 ** 3
SCENE = 0.2
MIN_SEGMENT_MS = 300
ROWS_PER_SHEET = 6
CELL = 240
WHISPER_MODEL = Path.home() / ".cache" / "whisper" / "large-v3-turbo.pt"
_WHISPER = ("/opt/homebrew/Caskroom/miniconda/base/bin/whisper",)
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="reference-video")
_active: set[int] = set()
_active_lock = threading.Lock()


class BreakdownError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(code)
        self.code, self.message = code, message


def _fail(status: int, code: str, message: str):
    raise HTTPException(status, {"code": code, "message": message})


def _run(arguments: list[str], timeout: int, env: dict | None = None) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(arguments, capture_output=True, timeout=timeout, check=True, stdin=subprocess.DEVNULL, env=env)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
        raise BreakdownError("reference_video_tool_failed", f"{Path(arguments[0]).name} 没跑完：{type(exc).__name__}") from None


def probe(path: Path) -> dict:
    out = _run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate",
                "-of", "json", str(path)], 60).stdout
    data = json.loads(out)
    video = next((item for item in data.get("streams", []) if item.get("codec_type") == "video"), None)
    if video is None:
        raise BreakdownError("reference_video_not_video", "这个文件里没有画面")
    num, _, den = str(video.get("r_frame_rate") or "0/1").partition("/")
    duration = round(float((data.get("format") or {}).get("duration") or 0) * 1000)
    if not 0 < duration <= MAX_MS:
        raise BreakdownError("reference_video_too_long", "参考视频要在 10 分钟以内")
    return {"duration_ms": duration, "width": video.get("width"), "height": video.get("height"),
            "fps": round(float(num) / float(den or 1), 2) if float(den or 1) else None,
            "has_audio": any(item.get("codec_type") == "audio" for item in data.get("streams", []))}


def scene_cuts(path: Path, duration_ms: int, threshold: float = SCENE) -> list[int]:
    """Times (ms) where the picture changes abruptly; flashes shorter than MIN_SEGMENT_MS merge into their neighbour."""
    err = _run(["ffmpeg", "-nostdin", "-hide_banner", "-i", str(path), "-an", "-vf", f"select='gt(scene,{threshold})',showinfo",
                "-f", "null", "-"], 600).stderr.decode("utf-8", "replace")
    cuts = []
    for found in re.finditer(r"pts_time:([0-9.]+)", err):
        at = round(float(found.group(1)) * 1000)
        if at - (cuts[-1] if cuts else 0) >= MIN_SEGMENT_MS and duration_ms - at >= MIN_SEGMENT_MS:
            cuts.append(at)
    return cuts


def segments(cuts: list[int], duration_ms: int) -> list[dict]:
    edges = [0, *cuts, duration_ms]
    return [{"index": index + 1, "start_ms": start, "end_ms": end} for index, (start, end) in enumerate(pairwise(edges))]


def _frame(path: Path, at_ms: int):
    from PIL import Image

    out = _run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{at_ms / 1000:.3f}", "-i", str(path), "-frames:v", "1",
                "-vf", f"scale={CELL}:-2", "-f", "image2pipe", "-vcodec", "png", "-"], 60).stdout
    return Image.open(io.BytesIO(out)).convert("RGB")


def _clock(ms: int) -> str:
    return f"{ms // 60000:02d}:{ms % 60000 / 1000:04.1f}"


def sheets(path: Path, parts: list[dict], out: Path) -> list[str]:
    """First, middle and last frame of each segment in one row, with the segment number and source times written on."""
    from PIL import Image, ImageDraw, ImageFont

    font = ImageFont.load_default(size=16)
    names = []
    for page, offset in enumerate(range(0, len(parts), ROWS_PER_SHEET), 1):
        rows = []
        for part in parts[offset:offset + ROWS_PER_SHEET]:
            length = part["end_ms"] - part["start_ms"]
            edge = min(150, length // 4)
            times = [part["start_ms"] + edge, part["start_ms"] + length // 2, part["end_ms"] - edge]
            part["frames_ms"] = times
            rows.append((part, [_frame(path, at) for at in times]))
        height = max(image.height for _part, frames in rows for image in frames)
        label = 56
        sheet = Image.new("RGB", (label + 3 * CELL + 4 * 4, len(rows) * (height + 24) + 4), "white")
        draw = ImageDraw.Draw(sheet)
        for row, (part, frames) in enumerate(rows):
            top = 4 + row * (height + 24)
            draw.text((6, top + height // 2 - 10), f"#{part['index']}", fill="black", font=font)
            for column, (image, at) in enumerate(zip(frames, part["frames_ms"])):
                left = label + 4 + column * (CELL + 4)
                sheet.paste(image, (left, top))
                draw.text((left + 2, top + height + 2), _clock(at), fill="black", font=font)
        name = f"grid-{page:02d}.jpg"
        sheet.save(out / name, quality=85)
        for part, _frames in rows:
            part["grid"] = name
        names.append(name)
    return names


def loudness(path: Path) -> dict | None:
    err = _run(["ffmpeg", "-nostdin", "-hide_banner", "-nostats", "-i", str(path), "-vn", "-af", "ebur128=peak=true",
                "-f", "null", "-"], 600).stderr.decode("utf-8", "replace")
    summary = err.rsplit("Summary:", 1)[-1]
    values = {}
    for key, pattern in (("integrated_lufs", r"I:\s+(-?[0-9.]+) LUFS"), ("range_lu", r"LRA:\s+(-?[0-9.]+) LU"),
                         ("true_peak_dbfs", r"Peak:\s+(-?[0-9.]+|-inf) dBFS")):
        found = re.search(pattern, summary)
        values[key] = float(found.group(1)) if found and found.group(1) != "-inf" else None
    return values if values["integrated_lufs"] is not None else None


def _mlx(audio: Path, duration_ms: int) -> dict:
    from .local_mlx_asr_provider import LocalMLXASRProvider

    content = audio.read_bytes()
    result = LocalMLXASRProvider().transcribe({"source_bytes": content, "source_hash": hashlib.sha256(content).hexdigest(),
                                               "mime_type": "audio/wav", "max_duration_ms": duration_ms, "timeout_seconds": 120})
    # The sandboxed worker returns sentence-level times only; that is enough to line speech up with the cuts.
    return {"engine": "local.mlx_whisper", "segments": result["cues"], "words": []}


def _whisper(audio: Path, folder: Path) -> dict:
    command = shutil.which("whisper") or next((item for item in _WHISPER if Path(item).is_file()), None)
    # Only an already downloaded model: the fallback must never reach the network.
    if command is None or not WHISPER_MODEL.is_file():
        raise BreakdownError("reference_video_asr_unavailable", "本机转写不可用")
    # Word timestamps crash this install (exit 139), so the fallback gives sentence times like the MLX worker.
    # Its conda torch and numpy each bring their own OpenMP; without the flag it aborts on start.
    _run([command, str(audio), "--model", WHISPER_MODEL.stem, "--model_dir", str(WHISPER_MODEL.parent), "--language", "zh",
          "--output_format", "json", "--output_dir", str(folder), "--fp16", "False", "--verbose", "False"], 900,
         env={**os.environ, "KMP_DUPLICATE_LIB_OK": "TRUE", "HF_HUB_OFFLINE": "1"})
    data = json.loads((folder / f"{audio.stem}.json").read_text("utf-8"))
    parts = [{"text": item["text"].strip(), "start_ms": round(item["start"] * 1000), "end_ms": round(item["end"] * 1000)}
             for item in data.get("segments", []) if str(item.get("text") or "").strip()]
    return {"engine": "whisper.large-v3-turbo", "language": data.get("language"), "segments": parts, "words": []}


def transcribe(path: Path, duration_ms: int) -> dict:
    with tempfile.TemporaryDirectory(prefix="aics-reference-") as folder:
        audio = Path(folder) / "audio.wav"
        _run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(path), "-map", "0:a:0", "-vn", "-ac", "1", "-ar", "16000",
              "-c:a", "pcm_s16le", str(audio)], 300)
        reasons = []
        for engine in (lambda: _mlx(audio, duration_ms), lambda: _whisper(audio, Path(folder))):
            try:
                result = engine()
                if result["segments"]:
                    return result
                reasons.append("没听到人声")
            except BreakdownError as exc:
                reasons.append(exc.message)
            except Exception as exc:  # noqa: BLE001 Either local engine may be missing; the other one is tried.
                reasons.append(str(exc) or type(exc).__name__)
        return {"engine": None, "segments": [], "words": [], "reason": "；".join(reasons)[:300]}


def local_breakdown(source: Path, out: Path) -> dict:
    """Everything free about one reference video, written into out/; returns the summary kept on the work."""
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("grid-*.jpg"):
        old.unlink()
    info = probe(source)
    parts = segments(scene_cuts(source, info["duration_ms"]), info["duration_ms"])
    grids = sheets(source, parts, out)
    transcript = transcribe(source, info["duration_ms"]) if info["has_audio"] else {"engine": None, "segments": [], "words": [], "reason": "没有声音"}
    for part in parts:
        part["speech"] = "".join(cue["text"] for cue in transcript["segments"]
                                 if cue["start_ms"] < part["end_ms"] and cue["end_ms"] > part["start_ms"])[:500]
    level = loudness(source) if info["has_audio"] else None
    (out / "transcript.json").write_text(json.dumps(transcript, ensure_ascii=False, indent=1), "utf-8")
    (out / "cuts.json").write_text(json.dumps({**info, "loudness": level, "segments": parts}, ensure_ascii=False, indent=1), "utf-8")
    return {"folder": str(out), **info, "cuts": len(parts) - 1, "segments": len(parts),
            "average_shot_ms": round(info["duration_ms"] / len(parts)), "loudness": level,
            "transcript_engine": transcript["engine"], "transcript_reason": transcript.get("reason"),
            "transcript": "\n".join(cue["text"] for cue in transcript["segments"])[:4000],
            "files": {"transcript": str(out / "transcript.json"), "cuts": str(out / "cuts.json"), "grids": [str(out / name) for name in grids]}}


def _records(db: Session) -> dict:
    row = db.get(SystemSetting, KEY)
    return dict(row.value or {}) if row else {}


def _record(db: Session, unit_id: int) -> dict | None:
    return copy.deepcopy(_records(db).get(str(unit_id)))


def _put(db: Session, unit_id: int, record: dict) -> None:
    row = db.get(SystemSetting, KEY)
    if row is None:
        row = SystemSetting(key=KEY, value={})
        db.add(row)
    value = dict(row.value or {})
    value[str(unit_id)] = record
    row.value = value
    flag_modified(row, "value")
    db.flush()


def _folder(db: Session, project_id: int, unit_id: int) -> Path:
    from . import project_folders

    return project_folders._work_folder(db, project_id, unit_id) / FOLDER


def _source(db: Session, project_id: int, revision_id: int, folder: Path) -> Path:
    from . import materials

    revision = db.get(MaterialRevision, revision_id)
    if revision is None or revision.material.status != "active" or revision.material.kind != "video":
        _fail(422, "reference_video_invalid", "参考视频必须是素材库里的一条视频")
    path = materials.local_file_checked(db, revision)
    if path is not None:
        return path
    # Storage that is not a plain local file is copied once next to the results; the material itself is untouched.
    target = folder / f"参考视频-{revision_id}{Path(revision.file_path or '').suffix or '.mp4'}"
    target.write_bytes(materials.read_bytes_checked(db, revision))
    return target


def start(db: Session, user: User, project_id: int, unit_id: int, material_revision_id: int | None = None,
          upload: tuple[bytes, str] | None = None) -> dict:
    """Starts the local breakdown in the background; read it with result()."""
    from .content_masters import owned_unit

    _project, unit = owned_unit(db, project_id, unit_id, user, mutate=True)
    if unit.modality != "video":
        _fail(409, "reference_video_video_only", "只有视频作品能拆参考视频")
    if (material_revision_id is None) == (upload is None):
        _fail(422, "reference_video_source_required", "选一条素材库里的视频，或上传一个参考视频")
    with _active_lock:
        if unit_id in _active:
            _fail(409, "reference_video_running", "这条参考视频还在拆，稍等再看结果")
    folder = _folder(db, project_id, unit_id)
    folder.mkdir(parents=True, exist_ok=True)
    if upload is not None:
        content, filename = upload
        suffix = Path(filename or "").suffix.lower()
        if suffix not in {".mp4", ".mov", ".m4v", ".webm"} or not 0 < len(content) <= MAX_UPLOAD:
            _fail(422, "reference_video_upload_invalid", "请上传 MP4 / MOV / WebM 视频，最大 1 GB")
        for old in folder.glob("参考视频*"):
            old.unlink()
        source = folder / f"参考视频{suffix}"
        source.write_bytes(content)
        origin = {"kind": "upload", "filename": Path(filename).name[:200]}
    else:
        source = _source(db, project_id, material_revision_id, folder)
        origin = {"kind": "library", "material_revision_id": material_revision_id}
    previous = _record(db, unit_id) or {}
    _put(db, unit_id, {"status": "running", "source": origin, "path": str(source), "folder": str(folder),
                       "started_at": datetime.now(UTC).isoformat(), "by": user.email,
                       # A new reference starts a new reading; the old one is kept only while the same video is re-run.
                       "breakdown": previous.get("breakdown") if previous.get("source") == origin else None})
    db.commit()
    with _active_lock:
        _active.add(unit_id)
    _executor.submit(_execute, unit_id, source, folder)
    return result(db, user, project_id, unit_id)


def _execute(unit_id: int, source: Path, folder: Path) -> None:
    from ..db import SessionLocal

    try:
        try:
            summary, failure = local_breakdown(source, folder), None
        except BreakdownError as exc:
            summary, failure = None, {"code": exc.code, "message": exc.message}
        except Exception as exc:  # noqa: BLE001 The page shows a failed breakdown instead of one stuck in running.
            summary, failure = None, {"code": "reference_video_failed", "message": f"拆解出错：{type(exc).__name__}"}
        with SessionLocal() as db:
            record = _record(db, unit_id) or {}
            record.update(status="done" if failure is None else "failed", summary=summary, error=failure,
                          finished_at=datetime.now(UTC).isoformat())
            _put(db, unit_id, record)
            db.commit()
    finally:
        with _active_lock:
            _active.discard(unit_id)


def shot_list(db: Session, unit_id: int, record: dict | None) -> list[dict]:
    """The model's shooting list; without one, every 导演稿 shot marked 需要实拍."""
    saved = ((record or {}).get("breakdown") or {}).get("shot_list")
    if saved:
        return saved
    from . import video_chain

    master = video_chain._latest(db, unit_id)
    shots = sorted((master.payload_json or {}).get("shots", []), key=lambda item: item["order"]) if master and master.payload_schema == "video.master.v2" else []
    return [{"shot_id": shot["id"], "what": (shot.get("board") or {}).get("visual") or shot.get("label") or "",
             "who": (shot.get("board") or {}).get("character") or "", "framing": shot.get("framing") or "",
             "camera": (shot.get("board") or {}).get("camera") or "", "seconds": round(shot["duration_ms"] / 1000, 1),
             "notes": (shot.get("board") or {}).get("material_request") or ""}
            for shot in shots if (shot.get("board") or {}).get("source_kind") == "shoot"]


def result(db: Session, user: User, project_id: int, unit_id: int) -> dict:
    from .content_masters import owned_unit

    owned_unit(db, project_id, unit_id, user)
    record = _record(db, unit_id)
    if record is None:
        return {"status": "none", "shot_list": shot_list(db, unit_id, None)}
    with _active_lock:
        running = unit_id in _active
    if record["status"] == "running" and not running:
        # The process restarted while it ran; the files are rebuilt on the next start.
        record.update(status="failed", error={"code": "reference_video_interrupted", "message": "拆解被打断了，请重新开始"})
    view = {key: record.get(key) for key in ("status", "source", "folder", "started_at", "finished_at", "summary", "error", "breakdown")}
    return {**view, "shot_list": shot_list(db, unit_id, record),
            "next": "按 studio.video.reference-breakdown 读拼图和转写，写整体分析、时间线和拍摄清单，用 save_reference_breakdown 存下，再写导演稿"
            if record["status"] == "done" and not record.get("breakdown") else None}


def brief_view(db: Session, unit_id: int) -> dict | None:
    """What get_video_brief says about the work's reference; None when it has none."""
    record = _record(db, unit_id)
    if record is None:
        return None
    return {"status": record["status"], "summary": record.get("summary"), "has_breakdown": bool(record.get("breakdown")),
            "read": "get_reference_video(project_id, unit_id) 看完整结果"}


def _text(value: object, limit: int) -> str:
    return str(value or "").strip()[:limit]


def save_breakdown(db: Session, user: User, project_id: int, unit_id: int, payload: dict) -> dict:
    from .content_masters import owned_unit

    owned_unit(db, project_id, unit_id, user, mutate=True)
    record = _record(db, unit_id)
    if record is None or record["status"] != "done":
        _fail(409, "reference_video_not_ready", "参考视频还没拆完，先用 analyze_reference_video 拆，等结果 done")
    timeline = [{"start_ms": int(item.get("start_ms") or 0), "end_ms": int(item.get("end_ms") or 0),
                 **{key: _text(item.get(key), 600) for key in ("speech", "picture", "overlays", "purpose")}}
                for item in payload.get("timeline") or []]
    if any(not 0 <= item["start_ms"] < item["end_ms"] <= MAX_MS for item in timeline):
        _fail(422, "reference_video_timeline_invalid", "时间线每段的开始要早于结束，都在 10 分钟以内")
    shots = [{key: _text(item.get(key), 400) for key in ("shot_id", "what", "who", "framing", "camera", "notes")}
             | {"seconds": round(float(item.get("seconds") or 0), 1)} for item in payload.get("shot_list") or []]
    record["breakdown"] = {"analysis": _text(payload.get("analysis"), 6000), "timeline": timeline, "shot_list": shots,
                           "brand_material": [_text(item, 200) for item in payload.get("brand_material") or []],
                           "saved_at": datetime.now(UTC).isoformat()}
    _put(db, unit_id, record)
    db.commit()
    return {"saved": True, "timeline": len(timeline), "shot_list": len(shots),
            "next": "用 save_director_draft 写这条作品的导演稿：结构和节奏照参考，口播换成本商品 / 本角色的说法，每镜写 board.source_kind；然后停下等用户"}


def export_shot_list(db: Session, user: User, project_id: int, unit_id: int) -> dict:
    """The shooting list as Markdown in <项目>/导演稿/, for the person who films."""
    from ..models import ContentUnit
    from . import project_folders
    from .content_masters import owned_unit

    owned_unit(db, project_id, unit_id, user)
    record = _record(db, unit_id)
    shots = shot_list(db, unit_id, record)
    if not shots:
        _fail(409, "reference_video_shot_list_empty", "还没有需要实拍的镜头")
    try:
        folder = project_folders.ensure_project_dir(db, project_id) / "导演稿"
    except FileNotFoundError:
        raise project_folders._drive_down() from None
    db.commit()
    title = re.split(r"[｜|]", db.get(ContentUnit, unit_id).title)[0].strip() or "作品"
    lines = [f"# 拍摄清单 · {title}", ""]
    brand = ((record or {}).get("breakdown") or {}).get("brand_material") or []
    if brand:
        lines += ["需要品牌真实资料（不拍、不生成）：" + "；".join(brand), ""]
    lines += ["| # | 镜头 | 拍什么 | 谁出镜 | 景别 | 机位 / 运镜 | 时长（秒） | 注意事项 |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for index, shot in enumerate(shots, 1):
        cells = [shot.get("shot_id"), shot.get("what"), shot.get("who"), shot.get("framing"), shot.get("camera"), shot.get("seconds"), shot.get("notes")]
        lines.append(f"| {index} | " + " | ".join(str(cell or "").replace("|", "／").replace("\n", " ") for cell in cells) + " |")
    target = folder / f"拍摄清单-{project_folders._clean(title) or '作品'}-{unit_id}.md"
    target.write_text("\n".join(lines) + "\n", "utf-8")
    return {"path": str(target), "shots": len(shots)}
