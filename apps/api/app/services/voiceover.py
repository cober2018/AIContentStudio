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
           "format": "mp3", "sample_rate": 32000, "bitrate": 128000, "channels": 1, "latex_read": False, "text_normalization": False,
           "language_boost": None, "voice_modify": {"pitch": 0, "intensity": 0, "timbre": 0}}
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
    return {"default": stored.get("default"), "personas": dict(stored.get("personas") or {}),
            "items": {key: {**DEFAULT, **value, "model_id": model} for key, value in stored["items"].items()}}


def _write(db: Session, value: dict, user: User) -> dict:
    from ..models import SystemSetting

    stored = {"default": value["default"], "personas": value["personas"],
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
    if preset_id in current["personas"].values():
        _fail("voice_preset_in_use", "有角色在用这套声音，不能删（角色的声音定了就不改）", 409)
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


def settings() -> dict:
    """The default voice setup."""
    current = presets()
    return {k: v for k, v in current["items"][current["default"]].items() if k != "name"}


def settings_for(db: Session, unit) -> dict:
    """A work speaks with its persona's voice, so every work of one persona sounds the same; without a persona, the default."""
    current = presets()
    chosen, origin = None, "默认"
    if unit.persona_id is not None and current["personas"].get(str(unit.persona_id)) in current["items"]:
        chosen, origin = current["personas"][str(unit.persona_id)], "角色"
    chosen = chosen or current["default"]
    item = current["items"][chosen]
    return {**{k: v for k, v in item.items() if k != "name"}, "preset_id": chosen, "preset_name": item["name"], "preset_origin": origin}


def _parameters(config: dict) -> dict:
    parameters = {key: config[key] for key in ("voice_id", "rate", "volume", "pitch", "format", "sample_rate", "bitrate", "channels",
                                              "latex_read", "text_normalization")}
    if config["emotion"] != "auto":
        parameters["emotion"] = config["emotion"]
    if config.get("language_boost"):
        parameters["language_boost"] = config["language_boost"]
    # All-zero means "no adjustment", so the request stays the plain voice.
    if any((config.get("voice_modify") or {}).values()):
        parameters["voice_modify"] = config["voice_modify"]
    if config.get("pronunciation"):
        parameters["pronunciation"] = config["pronunciation"]
    return {**parameters, "subtitles": True}


PRONUNCIATION_HELP = ("多音字读音写在导演稿 voice.pronunciation（可选，字符串列表，最多 50 条、每条 ≤ 40 字）："
                      "每条「原文/(拼音声调数字)…」，一个字一个括号，例如 \"去重/(qu4)(chong2)\"、\"行情/(hang2)(qing2)\"。"
                      "台词照常写原文，配音时 MiniMax 按这里读；随导演稿一起给用户通过。")


def _tones(document: dict) -> list[str]:
    return list((document.get("voice") or {}).get("pronunciation") or [])


def _voice(document: dict, revision_id: int) -> dict:
    # The 导演稿's pronunciation list belongs to the voice and must survive a new voiceover.
    tones = _tones(document)
    return {"mode": "tts", "material_revision_id": revision_id, **({"pronunciation": tones} if tones else {})}


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


MAX_FIT_SPEEDUP = 1.25
DUB_END_MARGIN_MS = 100


def _shot_starts(document: dict) -> dict[str, int]:
    """Where each shot begins on the cut: the picture track when the 导演稿 has one, else shot durations in order."""
    starts: dict[str, int] = {}
    for track in sorted((document.get("timeline") or {}).get("tracks") or [], key=lambda item: item.get("order", 0)):
        if track.get("kind") == "video":
            for item in track.get("items") or []:
                if item.get("shot_id") and item["shot_id"] not in starts:
                    starts[item["shot_id"]] = item["start_ms"]
    offset = 0
    for shot in sorted(document["shots"], key=lambda item: item["order"]):
        starts.setdefault(shot["id"], offset)
        offset += shot.get("duration_ms") or 0
    return starts


def _dubbed_shots(db: Session, user: User, document: dict) -> list[dict]:
    """Shots marked with a persona; each is voiced by that persona's own fixed voice."""
    from ..models import ContentPersona

    ordered = sorted(document["shots"], key=lambda item: item["order"])
    marked = [shot for shot in ordered if (shot.get("board") or {}).get("dub_persona")]
    if not marked:
        return []
    cues = (document.get("subtitles") or {}).get("cues") or []
    blocks = {block["id"]: block.get("text", "") for block in document["script"]["blocks"]}
    current, starts = presets(), _shot_starts(document)
    personas = db.scalars(select(ContentPersona).where(ContentPersona.owner_user_id == user.id, ContentPersona.status == "active")).all()
    result = []
    for shot in marked:
        label = f"第 {shot['order'] + 1} 镜（{shot['id']}）"
        ref = shot["board"]["dub_persona"].strip()
        persona = next((row for row in personas if str(row.id) == ref or row.name == ref), None)
        if persona is None:
            _fail("voiceover_dub_persona_missing", f"{label}标的配音角色「{ref}」不存在")
        preset = current["personas"].get(str(persona.id))
        if preset not in current["items"]:
            _fail("voiceover_dub_persona_voice_missing", f"角色「{persona.name}」还没定声音，先去角色页选好声音", 409)
        line = blocks.get(shot.get("script_block_id") or "", "").strip()
        if not line:
            _fail("voiceover_dub_line_missing", f"{label}标了配音，但台词是空的")
        item = current["items"][preset]
        config = {**{k: v for k, v in item.items() if k != "name"}, "preset_id": preset, "preset_name": item["name"], "preset_origin": "角色"}
        start = starts[shot["id"]]
        index = ordered.index(shot)
        previous = ordered[index - 1] if index else None
        tail_start = start
        # The previous shot's silent tail (after its last spoken cue) may carry the start of this line: sound leads, picture cuts later.
        if previous is not None and not (previous.get("board") or {}).get("dub_persona"):
            previous_start = starts[previous["id"]]
            spoken = [cue["end_ms"] for cue in cues if cue["start_ms"] < start and cue["end_ms"] > previous_start]
            tail_start = min(start, max(spoken)) if spoken else previous_start
        result.append({"shot_id": shot["id"], "label": label, "line": line, "persona": persona.name, "config": config,
                       "start_ms": start, "duration_ms": shot.get("duration_ms") or 0, "tail_start_ms": tail_start})
    return result


def _synthesize_shots(db: Session, user: User, project_id: int, unit, shots: list[dict], total_ms: int, script_hash: str, settings: dict, master_id: int):
    from .content_harness.registry import RegistryError, registry
    from .materials import create_material, create_revision

    try:
        provider = registry.resolve("tts_provider", "minimax.cli", "1")
    except RegistryError:
        raise HTTPException(503, {"code": "voiceover_provider_unavailable", "message": "MiniMax 配音没启用"}) from None
    with tempfile.TemporaryDirectory(prefix="aics-shots-") as folder:
        placed, cues = [], []
        for index, shot in enumerate(shots):
            config = shot["config"]
            shot_end = shot["start_ms"] + shot["duration_ms"]
            room = shot_end - DUB_END_MARGIN_MS - shot["tail_start_ms"]
            for attempt in range(2):
                result = provider.generate({"prompt": shot["line"], "model_id": config["model_id"], "timeout_seconds": 300,
                                            "parameters": _parameters(config)})
                if result.status != "succeeded" or not result.content:
                    raise HTTPException(502, {"code": "voiceover_failed", "message": f"{shot['label']}（{shot['persona']}）没返回配音，请稍后再试"})
                path = Path(folder) / f"{index:03d}-{attempt}.{'mp3' if result.mime_type == 'audio/mpeg' else 'wav'}"
                path.write_bytes(result.content)
                length = _duration_ms(result.content, path.suffix) or 0
                if length <= shot["duration_ms"] or length <= room or attempt == 1:
                    break
                # The persona's own pace comes first; only a line that overflows tail plus shot gets one faster take.
                config = {**config, "rate": round(min(shot["config"]["rate"] * MAX_FIT_SPEEDUP, config["rate"] * length / max(room, 1) * 1.03), 2)}
            if length <= shot["duration_ms"]:
                voice_start = shot["start_ms"]
            elif length <= room:
                voice_start = max(shot["tail_start_ms"], shot_end - DUB_END_MARGIN_MS - length)
            else:
                tail = shot["start_ms"] - shot["tail_start_ms"]
                _fail("voiceover_dub_too_long", f"{shot['label']}的配音加快到 {config['rate']} 倍后要 {length / 1000:.1f} 秒，这一镜只有 "
                                                f"{shot['duration_ms'] / 1000:.1f} 秒（加上上一镜结尾空白 {tail / 1000:.1f} 秒共 "
                                                f"{(shot['duration_ms'] + tail) / 1000:.1f} 秒），还差 {(length - room) / 1000:.1f} 秒；"
                                                "请把这一镜改长或缩短台词", 409)
            placed.append((path, voice_start))
            cues.append(f"{index + 1}\n{_stamp(voice_start)} --> {_stamp(voice_start + length)}\n{shot['line']}\n")
            shot["fitted_rate"], shot["voice_ms"] = config["rate"], length
            shot["voice_start_ms"], shot["lead_ms"] = voice_start, shot["start_ms"] - voice_start
        joined = Path(folder) / "voice.mp3"
        inputs = [arg for path, _ in placed for arg in ("-i", str(path))]
        delays = "".join(f"[{index}:a]adelay={start}|{start}[d{index}];" for index, (_, start) in enumerate(placed))
        mix = "".join(f"[d{index}]" for index in range(len(placed)))
        done = subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *inputs, "-filter_complex",
                               f"{delays}{mix}amix=inputs={len(placed)}:normalize=0,apad=whole_dur={total_ms / 1000:.3f}[out]",
                               "-map", "[out]", "-t", f"{total_ms / 1000:.3f}", "-c:a", "libmp3lame", "-b:a", "128k", str(joined)],
                              capture_output=True, timeout=300)
        if done.returncode != 0:
            raise HTTPException(502, {"code": "voiceover_join_failed", "message": "指定镜头配音拼接失败"})
        content = joined.read_bytes()
    material = create_material(db, kind="audio", title=f"配音（指定镜头）· {unit.title}"[:200], tags=["配音"], created_by=user.email)
    revision = create_revision(
        db, material, content=content, suffix=".mp3", declared_mime="audio/mpeg", source_kind="ai_generated",
        provider_key="minimax.cli", provider_version=shots[0]["config"]["model_id"], prompt_text="\n".join(shot["line"] for shot in shots)[:4000],
        rights_status="cleared", public_use_allowed=True, model_use_allowed=True, attribution_text="MiniMax 配音",
        duration_ms=_duration_ms(content, ".mp3"),
        metadata={"subtitles_srt": "\n".join(cues), "script_hash": script_hash, "voice_settings": settings, "source_master_revision_id": master_id,
                  "dubbed_shots": [{key: shot[key] for key in ("shot_id", "persona", "start_ms", "duration_ms", "voice_ms", "fitted_rate",
                                                                    "voice_start_ms", "lead_ms", "tail_start_ms")} for shot in shots]},
        created_by=user.email)
    db.add(ProjectMaterialReference(project_id=project_id, material_revision_id=revision.id, origin="system_reference", status="active",
                                    attached_by=user.email, note="指定镜头配音"))
    db.commit()
    return revision


def _generate_dubbed(db: Session, user: User, project_id: int, unit, master, document: dict, shots: list[dict]) -> dict:
    from .edit_handoff import _save
    from .project_folders import store_new

    total = document["timeline"]["duration_ms"]
    tones = _tones(document)
    if tones:
        for shot in shots:
            shot["config"] = {**shot["config"], "pronunciation": tones}
    settings = {"mode": "selected_shots", **({"pronunciation": tones} if tones else {}), "shots": [{"shot_id": shot["shot_id"], "persona": shot["persona"], "preset_id": shot["config"]["preset_id"],
                                                     "start_ms": shot["start_ms"], "duration_ms": shot["duration_ms"],
                                                     "tail_start_ms": shot["tail_start_ms"]} for shot in shots]}
    script_hash = hashlib.sha256(repr([(shot["shot_id"], shot["line"]) for shot in shots]).encode()).hexdigest()
    revision = _reuse(db, project_id, script_hash, settings) or _synthesize_shots(
        db, user, project_id, unit, shots, total, script_hash, settings, master.id)
    store_new(db, revision, project_id, "音频")
    # Only the marked shots speak through this track; durations stay as the 导演稿 set them.
    document["voice"] = _voice(document, revision.id)
    master_id = _save(db, user, project_id, unit.id, master, document, {},
                      edit_summary={"voiceover": {"material_revision_id": revision.id, "settings": settings, "aligned": False}})
    db.add(AuditLog(event="voiceover.generated", actor=user.email, entity_type="material", entity_id=str(revision.material_id),
                    detail_json={"material_revision_id": revision.id, "master_id": master_id, "mode": "selected_shots"}))
    db.commit()
    dubbed_info = (revision.metadata_json or {}).get("dubbed_shots") or []
    return {"material_id": revision.material_id, "material_revision_id": revision.id, "master_id": master_id,
            "duration_ms": revision.duration_ms, "aligned": False, "has_timing": True, "settings": settings,
            "dubbed_shots": dubbed_info,
            "edit_notes": [f"{item['shot_id']} 的配音提前 {item['lead_ms'] / 1000:.2f} 秒进：剪辑时声音先进，画面在本镜开头再切"
                           for item in dubbed_info if item.get("lead_ms")]}


def generate(db: Session, user: User, project_id: int, unit_id: int, lines: list[str] | None = None) -> dict:
    from .edit_handoff import _save

    from .product_video import require_persona
    from .project_folders import require_library

    require_persona(db, unit_id)
    require_library()
    unit = db.get(ContentUnit, unit_id)
    master = db.scalar(select(ContentMasterRevision).where(ContentMasterRevision.content_unit_id == unit_id)
                       .order_by(ContentMasterRevision.revision_no.desc()).limit(1))
    if unit is None or unit.project_id != project_id or master is None or master.payload_schema != "video.master.v2":
        raise HTTPException(409, {"code": "voiceover_master_required", "message": "先采用导演稿，再生成配音"})
    document = copy.deepcopy(master.payload_json)
    if lines is not None:
        return _redub(db, user, project_id, unit, master, document, lines)
    dubbed = _dubbed_shots(db, user, document)
    if dubbed:
        return _generate_dubbed(db, user, project_id, unit, master, document, dubbed)
    text = _script(document)
    if not text:
        raise HTTPException(409, {"code": "voiceover_script_empty", "message": "分镜表的台词列是空的"})
    config = settings_for(db, unit)
    if _tones(document):
        config = {**config, "pronunciation": _tones(document)}
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
    document["voice"] = _voice(document, revision.id)
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
        raise HTTPException(502, {"code": "voiceover_failed", "message": (result.metadata or {}).get("reason") or "MiniMax 没返回配音，请稍后再试"})
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


def _speech(document: dict) -> dict | None:
    track = next((track for track in document["timeline"]["tracks"] if track["kind"] == "dialogue"), None)
    if track is None or not track["items"]:
        return None
    speeds = {item.get("speed_percent", 100) for item in track["items"]}
    return {"speed_percent": speeds.pop() if len(speeds) == 1 else None, "duration_ms": document["timeline"]["duration_ms"]}


def _rescale(document: dict, old: int, new: int) -> None:
    """The whole cut follows the spoken pace: every time point moves by one ratio, so cuts that lined up still line up."""
    def at(ms: int) -> int:
        return round(ms * old / new)

    duration = at(document["timeline"]["duration_ms"])
    document["timeline"]["duration_ms"] = duration
    shots = sorted(document["shots"], key=lambda shot: shot["order"])
    cursor, lengths = 0, {}
    for shot in shots:
        end = cursor + shot["duration_ms"]
        shot["duration_ms"] = lengths[shot["id"]] = max(1, at(end) - at(cursor))
        cursor = end
    for track in document["timeline"]["tracks"]:
        items = sorted(track["items"], key=lambda item: item["start_ms"])
        starts = [at(item["start_ms"]) for item in items]
        for position, item in enumerate(items):
            start = starts[position]
            if track["kind"] == "dialogue":
                # The voice length comes from the clip and the speed; rounding must not push it into the next segment.
                end = start + round((item["trim_end_ms"] - item["trim_start_ms"]) * 100 / new)
                limit = starts[position + 1] if position + 1 < len(items) else duration
                item["end_ms"] = min(end, limit)
                if new == 100:
                    item.pop("speed_percent", None)
                else:
                    item["speed_percent"] = new
            else:
                end = at(item["end_ms"])
                if "shot_id" in item:
                    end = min(end, start + lengths[item["shot_id"]])
                item["end_ms"] = end
            item["start_ms"] = start
    for row in [*document["subtitles"]["cues"], *document["overlays"]]:
        row["start_ms"], row["end_ms"] = at(row["start_ms"]), at(row["end_ms"])
    post = document.get("postproduction")
    if post:
        for comp in post.get("ae_compositions", []):
            comp["duration_ms"] = lengths[comp["shot_id"]]
        for note in post.get("feedback", []):
            note["time_ms"] = min(at(note["time_ms"]), duration)


def set_speed(db: Session, user: User, project_id: int, unit_id: int, speed_percent: int) -> dict:
    """Whole-video speech speed for live dialogue; music keeps its speed and is cut to the new length in the edit."""
    from .content_masters import owned_unit
    from .edit_handoff import _save

    owned_unit(db, project_id, unit_id, user, mutate=True)
    master = db.scalar(select(ContentMasterRevision).where(ContentMasterRevision.content_unit_id == unit_id)
                       .order_by(ContentMasterRevision.revision_no.desc()).limit(1))
    if master is None or master.payload_schema != "video.master.v2":
        raise HTTPException(409, {"code": "speech_speed_master_required", "message": "先采用导演稿，再调语速"})
    document = copy.deepcopy(master.payload_json)
    speech = _speech(document)
    if speech is None:
        raise HTTPException(409, {"code": "speech_speed_no_dialogue", "message": "这个作品没有口播声音轨，不用调语速"})
    old = speech["speed_percent"]
    if old is None:
        raise HTTPException(409, {"code": "speech_speed_mixed", "message": "各段口播的语速不一样，先让第三方模型把导演稿统一成一个语速"})
    if old == speed_percent:
        return status(db, user, project_id, unit_id)
    _rescale(document, old, speed_percent)
    master_id = _save(db, user, project_id, unit_id, master, document, {},
                      edit_summary={"speech_speed": {"from": old, "to": speed_percent}})
    db.add(AuditLog(event="voiceover.speed_set", actor=user.email, entity_type="content_unit", entity_id=str(unit_id),
                    detail_json={"master_id": master_id, "from": old, "to": speed_percent}))
    db.commit()
    return status(db, user, project_id, unit_id)


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
    speech = _speech(master.payload_json) if master and master.payload_schema == "video.master.v2" else None
    return {"voice": voice, "settings": settings_for(db, unit), "emotions": {k: v for k, v in EMOTIONS.items() if v}, "speech": speech}


# Redubbing chosen lines in place: only those lines are voiced again and spliced into the current voice at their own start,
# so every other line, the shot lengths and the cut stay exactly as they were.
REDUB_GAP_MS = 250
REDUB_MAX_LINES = 20
SILENCE_NOISE, SILENCE_SECONDS = "-40dB", 0.15
SEAM_PAD_MS = 40
TRIM_PAD_MS = 30
RATE_RANGE = (0.6, 1.6)
CUE_TOLERANCE_MS = 300


def _ordered_lines(document: dict) -> list[dict]:
    """Spoken lines in the order the whole voiceover reads them (as _script builds it), each with its role."""
    blocks = {block["id"]: block.get("text", "") for block in document["script"]["blocks"]}
    lines, seen = [], set()
    for shot in sorted(document["shots"], key=lambda item: item["order"]):
        block = shot.get("script_block_id")
        if block and block not in seen and blocks.get(block, "").strip():
            seen.add(block)
            lines.append({"id": block, "text": blocks[block].strip(), "role": ((shot.get("board") or {}).get("character") or "narrator").strip()})
    return lines


def _audio_format(path: Path) -> tuple[int, int]:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=sample_rate,channels",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=False, timeout=30).stdout.strip().split(",")
    try:
        return int(out[0]), int(out[1])
    except (IndexError, ValueError):
        _fail("voiceover_audio_unreadable", "当前配音读不出来", 409)


def _pcm(path: Path, rate: int, channels: int):
    from array import array

    done = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(path), "-f", "s16le", "-acodec", "pcm_s16le",
                           "-ar", str(rate), "-ac", str(channels), "-"], capture_output=True, check=False, timeout=300)
    if done.returncode != 0:
        _fail("voiceover_audio_unreadable", "配音解码失败", 409)
    samples = array("h")
    samples.frombytes(done.stdout)
    return samples


def _speech_runs(path: Path, duration_ms: int) -> list[tuple[int, int]]:
    err = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-i", str(path), "-af",
                          f"silencedetect=noise={SILENCE_NOISE}:d={SILENCE_SECONDS}", "-f", "null", "-"],
                         capture_output=True, text=True, check=False, timeout=300).stderr
    starts = [round(float(value) * 1000) for value in re.findall(r"silence_start: (-?[0-9.]+)", err)]
    ends = [round(float(value) * 1000) for value in re.findall(r"silence_end: ([0-9.]+)", err)]
    runs, position = [], 0
    for index, start in enumerate(starts):
        if start - position > 0:
            runs.append((max(0, position), start))
        position = ends[index] if index < len(ends) else duration_ms
    if duration_ms - position > 0:
        runs.append((position, duration_ms))
    return [run for run in runs if run[1] - run[0] >= 30]


def _group_cues(cues: list[tuple[int, int, str]], lines: list[dict]) -> list[tuple[int, int]] | None:
    spans, index = [], 0
    for line in lines:
        target, buffer = _plain(line["text"]), ""
        if index >= len(cues):
            return None
        start = cues[index][0]
        while index < len(cues) and len(buffer) < len(target):
            buffer += _plain(cues[index][2])
            index += 1
        if buffer != target:
            return None
        spans.append((start, cues[index - 1][1]))
    return spans


def _line_spans(revision, path: Path, duration_ms: int, lines: list[dict], document: dict, chosen: list[int]) -> list[tuple[int, int]]:
    srt = (revision.metadata_json or {}).get("subtitles_srt")
    if srt:
        spans = _group_cues(_cues(srt), lines)
        if spans is None:
            _fail("voiceover_line_split_unclear", "配音自带的逐句时间和台词对不上，没法定位每句", 409)
        return spans
    runs = _speech_runs(path, duration_ms)
    cues = [(cue["start_ms"], cue["end_ms"], cue["text"]) for cue in (document.get("subtitles") or {}).get("cues") or []]
    grouped = _group_cues(cues, lines) if cues else None
    if grouped:
        return _snapped(grouped, runs, lines, chosen)
    chars = [len(_plain(line["text"])) for line in lines]
    count, total_chars = len(runs), sum(chars)
    if count < len(lines) or not total_chars:
        _fail("voiceover_line_split_unclear", f"配音里只听出 {count} 段有声，比台词的 {len(lines)} 句还少，没法定位每句", 409)
    prefix = [0]
    for start, end in runs:
        prefix.append(prefix[-1] + end - start)
    speech = prefix[-1]
    # Consecutive speech runs go to the lines whose share of the characters they best match.
    inf = float("inf")
    best = [[inf] * (count + 1) for _ in range(len(lines) + 1)]
    back = [[0] * (count + 1) for _ in range(len(lines) + 1)]
    best[0][0] = 0.0
    for i in range(1, len(lines) + 1):
        expected = chars[i - 1] / total_chars * speech
        for k in range(i, count - (len(lines) - i) + 1):
            for j in range(i - 1, k):
                if best[i - 1][j] == inf:
                    continue
                cost = best[i - 1][j] + ((prefix[k] - prefix[j]) - expected) ** 2
                if cost < best[i][k]:
                    best[i][k], back[i][k] = cost, j
    edges, k = [count], count
    for i in range(len(lines), 0, -1):
        k = back[i][k]
        edges.append(k)
    edges.reverse()
    spans = [(runs[edges[i]][0], runs[edges[i + 1] - 1][1]) for i in range(len(lines))]
    overall = total_chars / (speech / 1000)
    for i, line in enumerate(lines):
        rate = chars[i] / max((prefix[edges[i + 1]] - prefix[edges[i]]) / 1000, 0.001)
        if not RATE_RANGE[0] <= rate / overall <= RATE_RANGE[1]:
            _fail("voiceover_line_split_unclear", f"按停顿分句后，第 {i + 1} 句「{line['text'][:12]}」的语速不正常（每秒 {rate:.1f} 字，整条平均 {overall:.1f} 字），分组不可靠", 409)
    return spans


def _snapped(grouped: list[tuple[int, int]], runs: list[tuple[int, int]], lines: list[dict], chosen: list[int]) -> list[tuple[int, int]]:
    """Subtitle times moved onto the speech edges they mark.

    Only the edges this redub cuts at must find one: other lines keep their audio untouched, and a pair of
    them read without a pause between must not block redubbing elsewhere."""
    def edge(i: int, side: int) -> int:
        at = grouped[i][side]
        nearest = min((run[side] for run in runs), key=lambda value: abs(value - at), default=None)
        if nearest is None or abs(nearest - at) > CUE_TOLERANCE_MS:
            gap = "" if nearest is None else f"，离最近的停顿差 {abs(nearest - at) / 1000:.2f} 秒"
            _fail("voiceover_line_split_unclear", f"第 {i + 1} 句「{lines[i]['text'][:12]}」字幕{'起点' if side == 0 else '终点'} {at / 1000:.2f} 秒附近"
                  f"找不到停顿{gap}，没法定位这句", 409)
        return nearest

    spans = list(grouped)
    for i in chosen:
        if i:
            spans[i - 1] = (spans[i - 1][0], edge(i - 1, 1))
        if i + 1 < len(spans):
            spans[i + 1] = (edge(i + 1, 0), spans[i + 1][1])
    for i in chosen:
        spans[i] = (edge(i, 0), edge(i, 1))
    for i in chosen:
        before = spans[i - 1][1] if i else 0
        after = spans[i + 1][0] if i + 1 < len(spans) else spans[i][1]
        if not before <= spans[i][0] < spans[i][1] <= after:
            _fail("voiceover_line_split_unclear", f"第 {i + 1} 句「{lines[i]['text'][:12]}」按字幕吸到停顿后是 {spans[i][0] / 1000:.2f}–{spans[i][1] / 1000:.2f} 秒，"
                  "和前后句重叠，字幕时间不可靠", 409)
    return spans


def _trimmed(samples, rate: int, channels: int):
    """The new line without its leading and trailing silence, keeping a few ms so no consonant is clipped."""
    threshold = 328  # -40 dBFS on 16-bit samples
    frames = len(samples) // channels
    first = next((i for i in range(frames) if any(abs(samples[i * channels + c]) > threshold for c in range(channels))), None)
    if first is None:
        return samples[:0]
    last = next(i for i in range(frames - 1, -1, -1) if any(abs(samples[i * channels + c]) > threshold for c in range(channels)))
    pad = rate * TRIM_PAD_MS // 1000
    return samples[max(0, first - pad) * channels:min(frames, last + 1 + pad) * channels]


def _redub(db: Session, user: User, project_id: int, unit, master, document: dict, line_ids: list[str]) -> dict:
    import wave

    from ..models import MaterialRevision
    from .edit_handoff import _save
    from .materials import create_material, create_revision, local_file_checked, read_bytes_checked
    from .project_folders import store_new

    wanted = list(dict.fromkeys(line_ids))
    if not 0 < len(wanted) <= REDUB_MAX_LINES:
        _fail("voiceover_lines_invalid", f"一次重配 1 到 {REDUB_MAX_LINES} 句")
    voice = document.get("voice") or {}
    if voice.get("mode") != "tts" or not voice.get("material_revision_id"):
        _fail("voiceover_redub_needs_voice", "还没有整条配音，先整条生成一次", 409)
    if _dubbed_shots(db, user, document):
        _fail("voiceover_redub_dubbed", "这个作品按镜头指定角色配音，不能只重配几句；改了台词请整体重新生成", 409)
    if any(track.get("kind") == "dialogue" for track in document["timeline"]["tracks"]):
        _fail("voiceover_redub_dialogue_track", "时间线上有口播声音轨，成片的声音由它决定；换整条配音不会生效。先去掉口播声音轨再重配", 409)
    lines = _ordered_lines(document)
    positions = {line["id"]: index for index, line in enumerate(lines)}
    missing = [item for item in wanted if item not in positions]
    if missing:
        _fail("voiceover_lines_invalid", f"这些句子不在配音台词里：{', '.join(missing)}")
    revision = db.get(MaterialRevision, voice["material_revision_id"])
    if revision is None:
        _fail("voiceover_redub_needs_voice", "当前配音素材不在了", 409)
    config = settings_for(db, unit)
    if _tones(document):
        config = {**config, "pronunciation": _tones(document)}
    roles = _role_voices(db, [line["role"] for line in lines], config["voice_id"]) if any(line["role"] != "narrator" for line in lines) else None
    try:
        from .content_harness.registry import RegistryError, registry

        provider = registry.resolve("tts_provider", "minimax.cli", "1")
    except RegistryError:
        raise HTTPException(503, {"code": "voiceover_provider_unavailable", "message": "MiniMax 配音没启用"}) from None
    with tempfile.TemporaryDirectory(prefix="aics-redub-") as folder:
        source = local_file_checked(db, revision)
        if source is None:
            source = Path(folder) / f"voice{Path(revision.file_path or '').suffix or '.mp3'}"
            source.write_bytes(read_bytes_checked(db, revision))
        rate, channels = _audio_format(source)
        original = _pcm(source, rate, channels)
        total_ms = len(original) // channels * 1000 // rate
        spans = _line_spans(revision, source, total_ms, lines, document, [positions[item] for item in wanted])
        per_ms = rate * channels / 1000
        fps = (document.get("postproduction") or {}).get("fps") or 60
        fade = round(rate / fps) * channels
        patched = original[:]
        placed = []
        for line_id in sorted(wanted, key=positions.get):
            index = positions[line_id]
            line = lines[index]
            start, end = spans[index]
            following = spans[index + 1][0] if index + 1 < len(spans) else total_ms
            previous_end = spans[index - 1][1] if index else 0
            parameters = _parameters(config) if roles is None else {**_parameters(config), "voice_id": roles[line["role"]]}
            result = provider.generate({"prompt": line["text"], "model_id": config["model_id"], "parameters": parameters, "timeout_seconds": 300})
            if result.status != "succeeded" or not result.content:
                raise HTTPException(502, {"code": "voiceover_failed", "message": (result.metadata or {}).get("reason") or f"第 {index + 1} 句没返回配音，请稍后再试"})
            clip = Path(folder) / f"line-{index:03d}{'.mp3' if result.mime_type == 'audio/mpeg' else '.wav'}"
            clip.write_bytes(result.content)
            new = _trimmed(_pcm(clip, rate, channels), rate, channels)
            length = len(new) // channels * 1000 // rate
            limit = following - REDUB_GAP_MS if index + 1 < len(spans) else total_ms
            if start + length > max(end, limit):
                short = (start + length - max(end, limit)) / 1000
                _fail("voiceover_line_too_long", f"第 {index + 1} 句「{line['text'][:12]}」新配音 {length / 1000:.2f} 秒，用掉后面的停顿还差 {short:.2f} 秒放不下；"
                      "可以缩短这句台词，或整条重新生成", 409)
            covered = max(end, start + length)
            # Seams sit inside the pauses around the line, so no word of a neighbouring line is touched.
            seam_a = start - min(SEAM_PAD_MS, max(0, start - previous_end) // 2)
            seam_b = min(total_ms, covered + min(SEAM_PAD_MS, max(0, following - covered) // 2))
            a, b = round(seam_a * per_ms) // channels * channels, round(seam_b * per_ms) // channels * channels
            at = round(start * per_ms) // channels * channels
            for position in range(a, b):
                patched[position] = 0
            # Rounding at the very end must never lengthen the voice.
            new = new[:len(patched) - at]
            patched[at:at + len(new)] = new
            for offset in range(fade):
                # One frame of fade on the original side of each seam: out before it, in after it.
                frame = offset // channels
                weight = frame / (fade // channels)
                if a - fade + offset >= 0:
                    patched[a - fade + offset] = int(original[a - fade + offset] * (1 - weight))
                if b + offset < len(patched):
                    patched[b + offset] = int(original[b + offset] * weight)
            placed.append({"line_id": line_id, "order": index + 1, "old_start_ms": start, "old_end_ms": end,
                           "new_start_ms": start, "new_end_ms": start + length, "seams_ms": [seam_a, seam_b]})
        output = Path(folder) / "voice.wav"
        with wave.open(str(output), "wb") as handle:
            handle.setnchannels(channels)
            handle.setsampwidth(2)
            handle.setframerate(rate)
            handle.writeframes(patched.tobytes())
        content = output.read_bytes()
    srt = (revision.metadata_json or {}).get("subtitles_srt")
    if srt:
        kept = [cue for cue in _cues(srt) if not any(item["old_start_ms"] <= (cue[0] + cue[1]) // 2 <= item["old_end_ms"] for item in placed)]
        kept += [(item["new_start_ms"], item["new_end_ms"], lines[item["order"] - 1]["text"]) for item in placed]
        kept.sort()
        srt = "\n".join(f"{n}\n{_stamp(cue[0])} --> {_stamp(cue[1])}\n{cue[2]}\n" for n, cue in enumerate(kept, 1))
    material = create_material(db, kind="audio", title=f"配音（重配 {len(placed)} 句）· {unit.title}"[:200], tags=["配音"], created_by=user.email)
    new_revision = create_revision(
        db, material, content=content, suffix=".wav", declared_mime="audio/wav", source_kind="ai_generated",
        provider_key="minimax.cli", provider_version=config["model_id"], prompt_text="\n".join(lines[item["order"] - 1]["text"] for item in placed)[:4000],
        rights_status="cleared", public_use_allowed=True, model_use_allowed=True, attribution_text="MiniMax 配音",
        duration_ms=_duration_ms(content, ".wav"),
        metadata={"subtitles_srt": srt, "voice_settings": config, "redub": {"from_revision_id": revision.id, "lines": placed},
                  "source_master_revision_id": master.id},
        created_by=user.email)
    db.add(ProjectMaterialReference(project_id=project_id, material_revision_id=new_revision.id, origin="system_reference", status="active",
                                    attached_by=user.email, note=f"重配 {len(placed)} 句"))
    db.commit()
    store_new(db, new_revision, project_id, "音频")
    for item in placed:
        cues = [cue for cue in document["subtitles"]["cues"] if item["old_start_ms"] <= (cue["start_ms"] + cue["end_ms"]) // 2 <= item["old_end_ms"]]
        weights = [max(len(_plain(cue["text"])), 1) for cue in cues]
        span, position = item["new_end_ms"] - item["new_start_ms"], item["new_start_ms"]
        for cue, weight in zip(cues, weights):
            # Without the new clip's own phrase times, each cue keeps its share of the line by characters.
            cue["start_ms"] = position
            position = item["new_start_ms"] + round(span * sum(weights[:cues.index(cue) + 1]) / sum(weights))
            cue["end_ms"] = position
    document["voice"] = _voice(document, new_revision.id)
    master_id = _save(db, user, project_id, unit.id, master, document, {},
                      edit_summary={"voiceover": {"material_revision_id": new_revision.id, "settings": config, "aligned": False,
                                                  "redub": {"from_revision_id": revision.id, "lines": [item["line_id"] for item in placed]}}})
    db.add(AuditLog(event="voiceover.redubbed", actor=user.email, entity_type="material", entity_id=str(new_revision.material_id),
                    detail_json={"material_revision_id": new_revision.id, "master_id": master_id, "from_revision_id": revision.id,
                                 "lines": [item["line_id"] for item in placed]}))
    db.commit()
    return {"material_id": new_revision.material_id, "material_revision_id": new_revision.id, "master_id": master_id,
            "duration_ms": new_revision.duration_ms, "aligned": False, "has_timing": bool(srt), "settings": config,
            "redub": {"from_revision_id": revision.id, "billed_lines": len(placed), "lines": placed}}
