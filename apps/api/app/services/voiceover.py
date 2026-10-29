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


PRESETS = "voice_presets"
_PRESET_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")


def presets() -> dict:
    """Named voice setups; the single setting from before becomes the first one, 男声, and the default."""
    stored = runtime_config.get_runtime(PRESETS) or {}
    if not stored.get("items"):
        before = {k: v for k, v in (runtime_config.get_runtime(KEY) or {}).items() if k != "model_id"}
        stored = {"default": "male", "items": {"male": {"name": "男声", **DEFAULT, **before}}, "personas": {}}
    model = tts_model()
    return {"default": stored.get("default"), "personas": dict(stored.get("personas") or {}), "works": dict(stored.get("works") or {}),
            "items": {key: {**DEFAULT, **value, "model_id": model} for key, value in stored["items"].items()}}


def _write(db: Session, value: dict, user: User) -> dict:
    from ..models import SystemSetting

    stored = {"default": value["default"], "personas": value["personas"], "works": value["works"],
              "items": {key: {k: v for k, v in item.items() if k != "model_id"} for key, item in value["items"].items()}}
    row = db.get(SystemSetting, PRESETS) or SystemSetting(key=PRESETS)
    row.value, row.updated_by = stored, user.email
    db.add(row)
    db.commit()
    runtime_config.set_runtime(PRESETS, stored)
    return presets()


def _fail(code: str, message: str, status: int = 422):
    raise HTTPException(status, {"code": code, "message": message})


def save_preset(db: Session, user: User, preset_id: str | None, name: str, value: dict) -> dict:
    from .model_capability_routing import tts_parameters

    current = presets()
    if preset_id is None:
        preset_id = "voice-" + hashlib.sha256(f"{name}{len(current['items'])}".encode()).hexdigest()[:8]
    elif preset_id not in current["items"] and not _PRESET_ID.fullmatch(preset_id):
        _fail("voice_preset_invalid", "声音配置标识不对")
    name = (name or "").strip()
    if not 0 < len(name) <= 40:
        _fail("voice_preset_name_invalid", "名称不能为空，最多 40 个字")
    if any(key != preset_id and item["name"] == name for key, item in current["items"].items()):
        _fail("voice_preset_name_taken", "已经有同名的声音配置")
    merged = {**DEFAULT, **current["items"].get(preset_id, {}), **{k: v for k, v in value.items() if k in DEFAULT and k != "model_id"}, "name": name}
    if merged["emotion"] not in EMOTIONS:
        _fail("voice_settings_invalid", "情绪不支持")
    try:
        tts_parameters(_parameters(merged), capability="tts")
    except (TypeError, ValueError):
        _fail("voice_settings_invalid", "配音参数超出范围")
    current["items"][preset_id] = merged
    current["default"] = current["default"] or preset_id
    return _write(db, current, user)


def delete_preset(db: Session, user: User, preset_id: str) -> dict:
    current = presets()
    if preset_id not in current["items"]:
        _fail("voice_preset_missing", "没有这套声音配置", 404)
    if preset_id == current["default"]:
        _fail("voice_preset_in_use", "默认的那套不能删，先把别的设为默认", 409)
    if preset_id in current["personas"].values() or preset_id in current["works"].values():
        _fail("voice_preset_in_use", "有角色或作品在用这套声音，不能删（角色的声音定了就不改）", 409)
    del current["items"][preset_id]
    return _write(db, current, user)


def set_default(db: Session, user: User, preset_id: str) -> dict:
    current = presets()
    if preset_id not in current["items"]:
        _fail("voice_preset_missing", "没有这套声音配置", 404)
    current["default"] = preset_id
    return _write(db, current, user)


def set_persona_preset(db: Session, user: User, persona_id: int, preset_id: str | None) -> dict:
    current = presets()
    if preset_id is None or preset_id not in current["items"]:
        _fail("voice_preset_missing", "请选一套声音配置", 404 if preset_id else 422)
    # A persona's voice is part of who it is: set once, then fixed (the same preset may serve other personas).
    already = current["personas"].get(str(persona_id))
    if already and already != preset_id:
        _fail("voice_preset_locked", f"这个角色的声音已定为「{current['items'].get(already, {}).get('name', already)}」，不能再改", 409)
    current["personas"][str(persona_id)] = preset_id
    return _write(db, current, user)


def set_work_preset(db: Session, user: User, project_id: int, unit_id: int, preset_id: str | None) -> dict:
    """A work's own pick lives beside the presets, not in its production settings, so changing it mid-way keeps the 导演稿 valid."""
    from .content_masters import owned_unit

    owned_unit(db, project_id, unit_id, user)
    current = presets()
    if preset_id is not None and preset_id not in current["items"]:
        _fail("voice_preset_missing", "没有这套声音配置", 404)
    if preset_id is None:
        current["works"].pop(str(unit_id), None)
    else:
        current["works"][str(unit_id)] = preset_id
    return _write(db, current, user)


def settings() -> dict:
    """The default voice setup."""
    current = presets()
    return {k: v for k, v in current["items"][current["default"]].items() if k != "name"}


def settings_for(db: Session, unit) -> dict:
    """The voice a work speaks with: its own pick, else its persona's, else the default."""
    current = presets()
    chosen, origin = None, "默认"
    picked = current["works"].get(str(unit.id))
    if picked in current["items"]:
        chosen, origin = picked, "本作品"
    elif unit.persona_id is not None and current["personas"].get(str(unit.persona_id)) in current["items"]:
        chosen, origin = current["personas"][str(unit.persona_id)], "角色"
    chosen = chosen or current["default"]
    item = current["items"][chosen]
    return {**{k: v for k, v in item.items() if k != "name"}, "preset_id": chosen, "preset_name": item["name"], "preset_origin": origin}


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


def _role_lines(document: dict) -> list[tuple[str, str]]:
    """Lines with the role that says them, only when a shot names a speaking role (drama-type product scripts)."""
    blocks = {block["id"]: block.get("text", "") for block in document["script"]["blocks"]}
    lines, seen, roles = [], set(), False
    for shot in sorted(document["shots"], key=lambda item: item["order"]):
        block = shot.get("script_block_id")
        role = ((shot.get("board") or {}).get("character") or "narrator").strip()
        roles = roles or role != "narrator"
        if block and block not in seen and blocks.get(block, "").strip():
            seen.add(block)
            lines.append((role, blocks[block].strip()))
    return lines if roles else []


def _role_voices(db: Session, roles: list[str], narrator_voice: str) -> dict:
    """Each role gets its own fixed voice: ids starting with female / male draw from that gender's voices in order."""
    from .model_capability_routing import configuration_view

    catalog = sorted(item["voice_id"] for item in configuration_view(db).get("voice_catalog") or []
                     if item.get("provider_key") == "minimax.cli" and item.get("verified"))
    pools = {gender: [voice for voice in catalog if voice.startswith(f"{gender}-") and voice != narrator_voice] for gender in ("female", "male")}
    used: dict[str, int] = {"female": 0, "male": 0}
    voices = {"narrator": narrator_voice}
    for role in dict.fromkeys(roles):
        if role in voices:
            continue
        gender = "female" if role.startswith("female") else "male" if role.startswith("male") else ("female" if len(voices) % 2 else "male")
        pool = pools[gender] or pools["female"] + pools["male"]
        if not pool:
            raise HTTPException(409, {"code": "voiceover_role_voices_missing", "message": "音色库里没有可分给角色的声音，先在设置里刷新音色"})
        voices[role] = pool[used[gender] % len(pool)]
        used[gender] += 1
    return voices


def _stamp(ms: int) -> str:
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def _synthesize_roles(db: Session, user: User, project_id: int, unit, lines: list[tuple[str, str]], script_hash: str, config: dict, master_id: int):
    from .content_harness.registry import RegistryError, registry
    from .materials import create_material, create_revision

    try:
        provider = registry.resolve("tts_provider", "minimax.cli", "1")
    except RegistryError:
        raise HTTPException(503, {"code": "voiceover_provider_unavailable", "message": "MiniMax 配音没启用"}) from None
    pieces, cues, offset = [], [], 0
    with tempfile.TemporaryDirectory(prefix="aics-roles-") as folder:
        for index, (role, line) in enumerate(lines):
            result = provider.generate({"prompt": line, "model_id": config["model_id"], "timeout_seconds": 300,
                                        "parameters": {**_parameters(config), "voice_id": config["roles"][role]}})
            if result.status != "succeeded" or not result.content:
                raise HTTPException(502, {"code": "voiceover_failed", "message": f"第 {index + 1} 句（{role}）没返回配音，请稍后再试"})
            path = Path(folder) / f"{index:03d}.{'mp3' if result.mime_type == 'audio/mpeg' else 'wav'}"
            path.write_bytes(result.content)
            length = _duration_ms(result.content, path.suffix) or 0
            pieces.append(path)
            cues.append(f"{index + 1}\n{_stamp(offset)} --> {_stamp(offset + length)}\n{line}\n")
            offset += length
        listing = Path(folder) / "list.txt"
        listing.write_text("".join(f"file '{piece}'\n" for piece in pieces), encoding="utf-8")
        joined = Path(folder) / "voice.mp3"
        done = subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
                               "-c:a", "libmp3lame", "-b:a", "128k", str(joined)], capture_output=True, timeout=300)
        if done.returncode != 0:
            raise HTTPException(502, {"code": "voiceover_join_failed", "message": "多角色配音拼接失败"})
        content = joined.read_bytes()
    material = create_material(db, kind="audio", title=f"配音（多角色）· {unit.title}"[:200], tags=["配音"], created_by=user.email)
    revision = create_revision(
        db, material, content=content, suffix=".mp3", declared_mime="audio/mpeg", source_kind="ai_generated",
        provider_key="minimax.cli", provider_version=config["model_id"], prompt_text="\n".join(line for _, line in lines)[:4000],
        rights_status="cleared", public_use_allowed=True, model_use_allowed=True, attribution_text="MiniMax 配音",
        duration_ms=_duration_ms(content, ".mp3"),
        metadata={"subtitles_srt": "\n".join(cues), "script_hash": script_hash, "voice_settings": config, "source_master_revision_id": master_id},
        created_by=user.email)
    db.add(ProjectMaterialReference(project_id=project_id, material_revision_id=revision.id, origin="system_reference", status="active",
                                    attached_by=user.email, note="一键配音（多角色）"))
    db.commit()
    return revision


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
    config = settings_for(db, unit)
    lines = _role_lines(document)
    if lines:
        config = {**config, "roles": _role_voices(db, [role for role, _ in lines], config["voice_id"])}
    script_hash = hashlib.sha256((text + repr(lines)).encode()).hexdigest()
    revision = _reuse(db, project_id, script_hash, config)
    if revision is None:
        revision = (_synthesize_roles(db, user, project_id, unit, lines, script_hash, config, master.id) if lines
                    else _synthesize(db, user, project_id, unit, text, script_hash, config, master.id))
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
            "duration_ms": revision.duration_ms, "aligned": aligned, "has_timing": bool((revision.metadata_json or {}).get("subtitles_srt")), "settings": config,
            "quality": _quality_of(db, revision, db.get(ContentMasterRevision, master_id))}


# Short-video narration is mixed around -16 LUFS; well below -23 sounds quiet on a phone, above -9 clips.
LOUDNESS_RANGE = (-23.0, -9.0)
CHARS_PER_SECOND = (2.5, 8.0)


def _loudness(content: bytes, suffix: str) -> float | None:
    with tempfile.NamedTemporaryFile(suffix=suffix) as handle:
        handle.write(content)
        handle.flush()
        done = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", handle.name, "-af", "ebur128", "-f", "null", "-"],
                              capture_output=True, text=True, timeout=60)
    found = re.findall(r"I:\s+(-?[0-9.]+) LUFS", done.stderr)
    return float(found[-1]) if found else None


def check_audio(content: bytes, suffix: str, text: str, voice_name: str) -> dict:
    """What the voice file itself shows: it plays, its length fits the lines, it is loud enough, and which voice it used."""
    items = []
    duration = _duration_ms(content, suffix)
    items.append({"key": "file", "name": "文件", "pass": bool(duration), "detail": "能正常播放" if duration else "文件打不开或是空的"})
    if duration:
        chars = len(_plain(text))
        speed = chars / (duration / 1000) if duration else 0
        low, high = CHARS_PER_SECOND
        fits = low <= speed <= high
        items.append({"key": "duration", "name": "时长", "pass": fits,
                      "detail": f"{duration / 1000:.1f} 秒，{chars} 字，每秒 {speed:.1f} 字" + ("" if fits else "，和台词对不上（可能漏读或拖长）")})
        level = _loudness(content, suffix)
        if level is None:
            items.append({"key": "loudness", "name": "音量", "pass": False, "detail": "量不出响度"})
        else:
            quiet, loud = LOUDNESS_RANGE
            items.append({"key": "loudness", "name": "音量", "pass": quiet <= level <= loud,
                          "detail": f"{level:.1f} LUFS" + ("，偏小声，剪辑时要提响度" if level < quiet else "，偏大声，可能破音" if level > loud else "，正常")})
    items.append({"key": "voice", "name": "声音", "pass": True, "detail": f"用的是「{voice_name}」"})
    return {"status": "ok" if all(item["pass"] for item in items) else "warning", "items": items}


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


def _quality_of(db: Session, revision, master) -> dict | None:
    from sqlalchemy.orm.attributes import flag_modified

    from .material_storage import provider

    meta = dict(revision.metadata_json or {})
    if meta.get("quality"):
        return meta["quality"]
    try:
        content = provider().read(revision.file_path)
    except (OSError, ValueError):
        return None
    voice = meta.get("voice_settings") or {}
    meta["quality"] = check_audio(content, Path(revision.file_path).suffix or ".mp3", _script(master.payload_json) if master else "",
                                  voice.get("preset_name") or voice.get("voice_id") or "未知")
    revision.metadata_json = meta
    flag_modified(revision, "metadata_json")
    db.commit()
    return meta["quality"]


def status(db: Session, user: User, project_id: int, unit_id: int) -> dict:
    from .content_masters import owned_unit

    _project, unit = owned_unit(db, project_id, unit_id, user)
    master = db.scalar(select(ContentMasterRevision).where(ContentMasterRevision.content_unit_id == unit_id)
                       .order_by(ContentMasterRevision.revision_no.desc()).limit(1))
    from ..models import MaterialRevision

    voice = dict(((master.payload_json or {}).get("voice") if master else None) or {"mode": "none"})
    revision = db.get(MaterialRevision, voice["material_revision_id"]) if voice.get("material_revision_id") else None
    if revision is not None:
        voice["material_id"], voice["duration_ms"] = revision.material_id, revision.duration_ms
        voice["quality"] = _quality_of(db, revision, master)
    return {"voice": voice, "settings": settings_for(db, unit), "emotions": {k: v for k, v in EMOTIONS.items() if v}}
