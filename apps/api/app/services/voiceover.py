"""One-click voiceover for a video: 台词 → MiniMax with the saved voice settings → library → master voice track."""

from __future__ import annotations

import copy
import hashlib
import re
import subprocess
import tempfile
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import runtime_config
from ..models import AuditLog, ContentMasterRevision, ContentUnit, ProjectMaterialReference, User

KEY = "voice_default"
# The user's MiniMax setup (2026-10-24); every field is sent as given.
DEFAULT = {"model_id": "speech-2.8-hd", "voice_id": "verify_clone_v2", "emotion": "happy", "rate": 1.0, "volume": 1.0, "pitch": 0,
           "format": "mp3", "sample_rate": 32000, "bitrate": 128000, "channels": 1, "latex_read": False, "text_normalization": False}
EMOTIONS = {"auto": None, "happy": "开心", "sad": "悲伤", "angry": "愤怒", "fearful": "恐惧", "disgusted": "厌恶", "surprised": "惊讶",
            "calm": "中性", "fluent": "流畅", "whisper": "低语"}


def tts_model() -> str:
    """The voiceover model is the first MiniMax TTS route in 设置 → AI 与模型 → 生成能力与插件."""
    models = runtime_config.get_runtime(runtime_config.KEY_MODELS) or {}
    for plugin_id in (models.get("capability_routes") or {}).get("tts", []):
        plugin = (models.get("media_plugins") or {}).get(plugin_id) or {}
        binding = (((models.get("profiles") or {}).get(plugin.get("model_profile_id")) or {}).get("capability_bindings") or {}).get("tts") or {}
        if plugin.get("enabled") and binding.get("adapter_key") == "minimax.cli" and binding.get("model_id"):
            return binding["model_id"]
    return DEFAULT["model_id"]


def settings() -> dict:
    stored = {k: v for k, v in (runtime_config.get_runtime(KEY) or {}).items() if k != "model_id"}
    return {**DEFAULT, **stored, "model_id": tts_model()}


def save_settings(db: Session, value: dict, user: User) -> dict:
    from ..models import SystemSetting
    from .model_capability_routing import tts_parameters

    merged = {**settings(), **{k: v for k, v in value.items() if k in DEFAULT and k != "model_id"}}
    if merged["emotion"] not in EMOTIONS:
        raise HTTPException(422, {"code": "voice_settings_invalid", "message": "情绪不支持"})
    try:
        tts_parameters(_parameters(merged), capability="tts")
    except (TypeError, ValueError):
        raise HTTPException(422, {"code": "voice_settings_invalid", "message": "配音参数超出范围"}) from None
    row = db.get(SystemSetting, KEY) or SystemSetting(key=KEY)
    row.value, row.updated_by = {k: v for k, v in merged.items() if k != "model_id"}, user.email
    db.add(row)
    db.commit()
    runtime_config.set_runtime(KEY, merged)
    return merged


def _parameters(config: dict) -> dict:
    parameters = {key: config[key] for key in ("voice_id", "rate", "volume", "pitch", "format", "sample_rate", "bitrate", "channels",
                                              "latex_read", "text_normalization")}
    if config["emotion"] != "auto":
        parameters["emotion"] = config["emotion"]
    return {**parameters, "subtitles": True}


def _script(document: dict) -> str:
    blocks = {block["id"]: block.get("text", "") for block in document["script"]["blocks"]}
    lines, seen = [], set()
    for shot in sorted(document["shots"], key=lambda item: item["order"]):
        block = shot.get("script_block_id")
        if block and block not in seen and blocks.get(block, "").strip():
            seen.add(block)
            lines.append(blocks[block].strip())
    return "\n".join(lines)


def _duration_ms(content: bytes, suffix: str) -> int | None:
    with tempfile.NamedTemporaryFile(suffix=suffix) as handle:
        handle.write(content)
        handle.flush()
        done = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", handle.name],
                              capture_output=True, text=True, timeout=20)
    try:
        return round(float(done.stdout.strip()) * 1000)
    except ValueError:
        return None


def generate(db: Session, user: User, project_id: int, unit_id: int) -> dict:
    from .edit_handoff import _save

    unit = db.get(ContentUnit, unit_id)
    master = db.scalar(select(ContentMasterRevision).where(ContentMasterRevision.content_unit_id == unit_id)
                       .order_by(ContentMasterRevision.revision_no.desc()).limit(1))
    if unit is None or unit.project_id != project_id or master is None or master.payload_schema != "video.master.v2":
        raise HTTPException(409, {"code": "voiceover_master_required", "message": "先采用导演稿，再生成配音"})
    document = copy.deepcopy(master.payload_json)
    text = _script(document)
    if not text:
        raise HTTPException(409, {"code": "voiceover_script_empty", "message": "分镜表的台词列是空的"})
    config = settings()
    script_hash = hashlib.sha256(text.encode()).hexdigest()
    revision = _reuse(db, project_id, script_hash, config)
    if revision is None:
        revision = _synthesize(db, user, project_id, unit, text, script_hash, config, master.id)
    from .project_folders import store_new

    store_new(db, revision, project_id, "音频")
    document["voice"] = {"mode": "tts", "material_revision_id": revision.id}
    aligned = align_to_voice(db, document, (revision.metadata_json or {}).get("subtitles_srt"), revision.duration_ms)
    master_id = _save(db, user, project_id, unit_id, master, document, {},
                      edit_summary={"voiceover": {"material_revision_id": revision.id, "settings": config, "aligned": aligned}})
    db.add(AuditLog(event="voiceover.generated", actor=user.email, entity_type="material", entity_id=str(revision.material_id),
                    detail_json={"material_revision_id": revision.id, "master_id": master_id}))
    db.commit()
    return {"material_id": revision.material_id, "material_revision_id": revision.id, "master_id": master_id,
            "duration_ms": revision.duration_ms, "aligned": aligned, "has_timing": bool((revision.metadata_json or {}).get("subtitles_srt")), "settings": config}


def _cues(srt: str) -> list[tuple[int, int, str]]:
    def ms(stamp):
        h, m, rest = stamp.strip().split(":")
        sec, milli = rest.split(",")
        return ((int(h) * 60 + int(m)) * 60 + int(sec)) * 1000 + int(milli)
    cues = []
    for block in re.split(r"\n\s*\n", srt.strip()):
        lines = block.strip().splitlines()
        if len(lines) >= 3 and "-->" in lines[1]:
            start, end = lines[1].split("-->")
            cues.append((ms(start), ms(end), "".join(lines[2:])))
    return cues


def _plain(text: str) -> str:
    return re.sub(r"[\W_]+", "", text)


def _clip_ms(revision) -> int | None:
    if revision.duration_ms:
        return revision.duration_ms
    from .material_storage import provider

    # Older uploads have no recorded length; read it from the bytes the edit will actually use.
    try:
        return _duration_ms(provider().read(revision.file_path), Path(revision.file_path).suffix or ".mp4")
    except (OSError, ValueError):
        return None


def align_to_voice(db: Session, document: dict, srt: str | None, voice_ms: int | None) -> bool:
    """Shot lengths follow the narration: each narrated shot starts where its line starts.

    When a source clip is shorter than its line, the next shot's picture comes in early (a J-cut),
    so no clip is stretched past its real length. Unmatched text leaves the estimates unchanged.
    """
    from ..models import MaterialRevision

    cues = _cues(srt or "")
    blocks = {block["id"]: _plain(block.get("text", "")) for block in document["script"]["blocks"]}
    shots = sorted(document["shots"], key=lambda item: item["order"])
    starts, index, buffer = {}, 0, ""
    for shot in shots:
        target = blocks.get(shot.get("script_block_id") or "", "")
        if not target:
            continue
        if index >= len(cues):
            return False
        start, buffer = cues[index][0], ""
        while index < len(cues) and len(buffer) < len(target):
            buffer += _plain(cues[index][2])
            index += 1
        if buffer != target:
            return False
        starts[shot["id"]] = start
    if not starts or shots[0]["id"] not in starts:
        return False
    tail = 600
    voice_end = max((voice_ms or cues[-1][1]), cues[-1][1])
    end = voice_end + tail
    bounds = [starts.get(shot["id"]) for shot in shots]
    last_line = max(position for position, shot in enumerate(shots) if shot["id"] in starts)
    # Shots without a line keep their estimated share between the narrated ones.
    for position, value in enumerate(bounds):
        if value is None:
            bounds[position] = bounds[position - 1] + shots[position - 1]["duration_ms"]
    # Shots after the last line are a silent ending: picture outlasts the voice instead of stopping with it.
    if last_line < len(shots) - 1:
        bounds[last_line + 1] = voice_end + tail
        for position in range(last_line + 2, len(shots)):
            bounds[position] = bounds[position - 1] + shots[position - 1]["duration_ms"]
        end = bounds[-1] + shots[-1]["duration_ms"]
    bounds.append(end)
    limits = []
    for shot in shots:
        revision = db.get(MaterialRevision, shot.get("source_material_revision_id")) if shot.get("source_material_revision_id") else None
        limits.append(_clip_ms(revision) if revision and (revision.mime_type or "").startswith("video/") else None)
    for position in range(len(shots) - 1):
        limit = limits[position]
        if limit and bounds[position + 1] - bounds[position] > limit:
            bounds[position + 1] = bounds[position] + limit
    for position, shot in enumerate(shots):
        length = bounds[position + 1] - bounds[position]
        if length <= 0 or (limits[position] and length > limits[position]):
            return False
        shot["duration_ms"] = length
    for track in document["timeline"]["tracks"]:
        for item in track["items"]:
            if item.get("shot_id") in starts or any(item.get("shot_id") == shot["id"] for shot in shots):
                position = next(i for i, shot in enumerate(shots) if shot["id"] == item["shot_id"])
                item["start_ms"], item["end_ms"] = bounds[position], bounds[position + 1]
    document["timeline"]["duration_ms"] = end
    post = document.get("postproduction")
    if post:
        lengths = {shot["id"]: shot["duration_ms"] for shot in shots}
        for comp in post.get("ae_compositions", []):
            comp["duration_ms"] = lengths[comp["shot_id"]]
    return True


def _reuse(db: Session, project_id: int, script_hash: str, config: dict):
    from ..models import MaterialRevision

    # The same lines with the same settings were already paid for; a retry uses that file.
    rows = db.scalars(select(MaterialRevision).join(ProjectMaterialReference, ProjectMaterialReference.material_revision_id == MaterialRevision.id)
                      .where(ProjectMaterialReference.project_id == project_id, MaterialRevision.provider_key == "minimax.cli")
                      .order_by(MaterialRevision.id.desc()).limit(20)).all()
    return next((row for row in rows if (row.metadata_json or {}).get("script_hash") == script_hash
                 and (row.metadata_json or {}).get("voice_settings") == config), None)


def _synthesize(db: Session, user: User, project_id: int, unit, text: str, script_hash: str, config: dict, master_id: int):
    from .content_harness.registry import RegistryError, registry
    from .materials import create_material, create_revision

    try:
        provider = registry.resolve("tts_provider", "minimax.cli", "1")
    except RegistryError:
        raise HTTPException(503, {"code": "voiceover_provider_unavailable", "message": "MiniMax 配音没启用"}) from None
    result = provider.generate({"prompt": text, "model_id": config["model_id"], "parameters": _parameters(config), "timeout_seconds": 300})
    if result.status != "succeeded" or not result.content:
        # A failed or unclear call is not repeated automatically; the supplier may have charged it.
        raise HTTPException(502, {"code": "voiceover_failed", "message": "MiniMax 没返回配音，请稍后再试"})
    suffix = {"audio/mpeg": ".mp3", "audio/flac": ".flac"}.get(result.mime_type, ".wav")
    meta = result.metadata or {}
    material = create_material(db, kind="audio", title=f"配音 · {unit.title}"[:200], tags=["配音"], created_by=user.email)
    revision = create_revision(
        db, material, content=result.content, suffix=suffix, declared_mime=result.mime_type, source_kind="ai_generated",
        provider_key="minimax.cli", provider_version=config["model_id"], prompt_text=text[:4000],
        rights_status="cleared", public_use_allowed=True, model_use_allowed=True, attribution_text="MiniMax 配音",
        duration_ms=_duration_ms(result.content, suffix),
        metadata={"tts_applied_parameters": meta.get("tts_applied_parameters"), "subtitles_srt": meta.get("subtitles_srt"),
                  "script_hash": script_hash, "voice_settings": config, "source_master_revision_id": master_id},
        created_by=user.email)
    db.add(ProjectMaterialReference(project_id=project_id, material_revision_id=revision.id, origin="system_reference", status="active",
                                    attached_by=user.email, note="一键配音"))
    # Kept even if saving the master fails afterwards, so a retry does not pay for the same voice again.
    db.commit()
    return revision


def status(db: Session, user: User, project_id: int, unit_id: int) -> dict:
    from .content_masters import owned_unit

    owned_unit(db, project_id, unit_id, user)
    master = db.scalar(select(ContentMasterRevision).where(ContentMasterRevision.content_unit_id == unit_id)
                       .order_by(ContentMasterRevision.revision_no.desc()).limit(1))
    from ..models import MaterialRevision

    voice = dict(((master.payload_json or {}).get("voice") if master else None) or {"mode": "none"})
    revision = db.get(MaterialRevision, voice["material_revision_id"]) if voice.get("material_revision_id") else None
    if revision is not None:
        voice["material_id"], voice["duration_ms"] = revision.material_id, revision.duration_ms
    return {"voice": voice, "settings": settings(), "emotions": {k: v for k, v in EMOTIONS.items() if v}}
