"""Read-only Audio QC over accepted MaterialRevision bytes and durable receipts."""

from __future__ import annotations

import hashlib
import hmac
import io
import json
import math
import os
import re
import selectors
import shutil
import struct
import subprocess
import tempfile
import time
import unicodedata
import wave

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import (
    ContentMasterAssetRef,
    ContentMasterRevision,
    ContentProject,
    ContentUnit,
    Material,
    MaterialRevision,
    ProviderGenerationTask,
    SystemSetting,
    User,
)
from . import generation_tasks, materials, studio_creative_catalog

_HASH = re.compile(r"[0-9a-f]{64}\Z")
_ID = re.compile(r"[A-Za-z0-9_.:-]{1,150}\Z")
_PROFILE_REFS = {"studio.quality.audio.explainer@1", "studio.quality.audio.conversational@1"}
_MAX_BYTES = 30 * 1024 * 1024
_MAX_SAMPLES = 12_000_000
_MAX_SECONDS = 600
_PROCESS_SECONDS = 10
_ASR_FIELDS = {"master_revision_id", "receipt_id", "output_hash"}
_SUBTITLE_LIMIT = 16 * 1024
_ALIGNMENT_RULES = {"max_cues": 1000, "max_text_characters": 100000,
                    "max_srt_bytes": _SUBTITLE_LIMIT, "estimated_line_characters": 42,
                    "max_estimated_cues": 256, "comparison": "normalized_positional_characters"}
_FORMATS = {"audio/wav": "wav", "audio/mpeg": "mp3", "audio/flac": "flac",
            "audio/ogg": "ogg", "audio/mp4": "mov"}
_RULES = {"max_bytes": _MAX_BYTES, "max_duration_ms": _MAX_SECONDS * 1000,
          "max_samples": _MAX_SAMPLES, "process_timeout_seconds": _PROCESS_SECONDS,
          "silence_amplitude": 0.001, "clipping_amplitude": 0.999,
          "clipping_blocker_ratio": 0.01, "clipping_warning_ratio": 0.001,
          "edge_silence_warning_ms": 2000, "silence_warning_ratio": 0.9,
          "rms_warning_min_dbfs": -35, "rms_warning_max_dbfs": -6}


class _Unavailable(ValueError):
    pass


class _Invalid(ValueError):
    pass


def _hash(value):
    return generation_tasks._hash(value)


def _digest(value):
    return value if isinstance(value, str) and _HASH.fullmatch(value) else None


def _identifier(value):
    return value if isinstance(value, str) and _ID.fullmatch(value) else None


def _issue(report, severity, code):
    item = {"severity": severity, "code": code}
    if item not in report["issues"] and len(report["issues"]) < 32:
        report["issues"].append(item)


def _finish(report):
    severities = {item["severity"] for item in report["issues"]}
    report["status"] = next((status for status in ("blocker", "incomplete", "warning")
                             if status in severities), "pass")
    report["coverage"]["complete"] = report["status"] not in {"blocker", "incomplete"}
    return report


def _pipe(program, arguments, content, output_limit, deadline):
    # Fixed binaries/demuxers and pipe-only protocols cannot follow client paths or URLs.
    executable = shutil.which(program) if program in {"ffprobe", "ffmpeg"} else None
    if executable is None:
        raise _Unavailable("audio_local_tool_unavailable")
    process = None
    try:
        process = subprocess.Popen([executable, *arguments], stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                   env={key: os.environ[key] for key in ("PATH", "LANG", "LC_ALL")
                                        if key in os.environ})
        output, offset = bytearray(), 0
        with selectors.DefaultSelector() as selector:
            for stream, event in ((process.stdin, selectors.EVENT_WRITE),
                                  (process.stdout, selectors.EVENT_READ)):
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, event)
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise _Unavailable("audio_local_tool_timeout")
                for key, _ in selector.select(remaining):
                    if key.fileobj is process.stdin:
                        try:
                            offset += os.write(key.fd, memoryview(content)[offset:offset + 65536])
                        except BrokenPipeError:
                            offset = len(content)
                        except BlockingIOError:
                            continue
                        if offset == len(content):
                            selector.unregister(key.fileobj)
                            process.stdin.close()
                    else:
                        try:
                            chunk = os.read(key.fd, min(65536, output_limit - len(output) + 1))
                        except BlockingIOError:
                            continue
                        if not chunk:
                            selector.unregister(key.fileobj)
                        elif len(output) + len(chunk) > output_limit:
                            raise _Unavailable("audio_decoded_size_limit")
                        else:
                            output.extend(chunk)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise _Unavailable("audio_local_tool_timeout")
        if process.wait(timeout=remaining) != 0:
            raise _Invalid("audio_decode_invalid")
        return bytes(output)
    except (OSError, subprocess.SubprocessError):
        raise _Unavailable("audio_local_tool_unavailable") from None
    finally:
        if process is not None:
            if process.poll() is None:
                process.kill()
            process.wait()
            for stream in (process.stdin, process.stdout):
                if stream is not None:
                    stream.close()


def _pcm(content, mime, deadline, report):
    if mime == "audio/wav":
        if content[:4] != b"RIFF" or content[8:12] != b"WAVE":
            raise _Invalid("audio_mime_mismatch")
        try:
            with wave.open(io.BytesIO(content), "rb") as audio:
                rate, channels, width, frames = (audio.getframerate(), audio.getnchannels(),
                                                 audio.getsampwidth(), audio.getnframes())
                if rate > 0:
                    report["measured"]["duration_ms"] = round(frames * 1000 / rate, 3)
                    report["coverage"]["mime_duration"] = "wav_header_only"
                _dimensions(rate, channels, frames)
                if width not in {1, 2, 3, 4} or audio.getcomptype() != "NONE":
                    raise _Unavailable("audio_pcm_format_unavailable")
                pcm = audio.readframes(frames)
                if len(pcm) != frames * channels * width:
                    raise _Invalid("audio_truncated_frames")
                return pcm, rate, channels, width, "wave"
        except (EOFError, OSError):
            raise _Invalid("audio_decode_invalid") from None
        except ValueError as exc:
            if isinstance(exc, (_Invalid, _Unavailable)):
                raise
            raise _Invalid("audio_decode_invalid") from None
        except wave.Error as exc:
            # Non-PCM WAV needs the same bounded decoder as compressed audio.
            if not str(exc).startswith("unknown format:"):
                raise _Invalid("audio_decode_invalid") from None
    if mime not in _FORMATS:
        raise _Unavailable("audio_mime_unsupported")
    arguments = ["-v", "error", "-protocol_whitelist", "pipe", "-f", _FORMATS[mime],
                 "-i", "pipe:0", "-select_streams", "a", "-show_entries",
                 "stream=sample_rate,channels,duration:format=duration", "-of", "json"]
    raw = _pipe("ffprobe", arguments, content, 8192, deadline)
    try:
        probe = json.loads(raw)
        streams = probe["streams"]
        if len(streams) != 1:
            raise _Invalid("audio_stream_contract_invalid")
        rate, channels = int(streams[0]["sample_rate"]), streams[0]["channels"]
        _dimensions(rate, channels, 1)
        duration = streams[0].get("duration", probe.get("format", {}).get("duration"))
        if duration is not None:
            duration = float(duration)
            if not math.isfinite(duration) or duration > _MAX_SECONDS or duration <= 0:
                raise _Invalid("audio_duration_out_of_bounds")
            report["measured"]["duration_ms"] = round(duration * 1000, 3)
            report["coverage"]["mime_duration"] = "probe_only"
    except (_Invalid, _Unavailable):
        raise
    except (ValueError, TypeError, KeyError, IndexError):
        raise _Invalid("audio_probe_invalid") from None
    pcm = _pipe("ffmpeg", ["-nostdin", "-v", "error", "-xerror", "-threads", "1",
                          "-protocol_whitelist", "pipe", "-f", _FORMATS[mime], "-i", "pipe:0",
                          "-map", "0:a:0", "-vn", "-sn", "-dn", "-t", str(_MAX_SECONDS + 1),
                          "-ac", str(channels), "-ar", str(rate), "-c:a", "pcm_s16le",
                          "-f", "s16le", "pipe:1"], content, _MAX_SAMPLES * 2, deadline)
    if len(pcm) % (channels * 2):
        raise _Invalid("audio_truncated_frames")
    _dimensions(rate, channels, len(pcm) // (channels * 2))
    return pcm, rate, channels, 2, "ffmpeg"


def _dimensions(rate, channels, frames):
    if (type(rate) is not int or type(channels) is not int or not 1 <= rate <= 192000
            or not 1 <= channels <= 8):
        raise _Invalid("audio_stream_contract_invalid")
    if frames <= 0 or frames > rate * _MAX_SECONDS:
        raise _Invalid("audio_duration_out_of_bounds")
    if frames * channels > _MAX_SAMPLES:
        raise _Unavailable("audio_sample_limit")


def _measure(pcm, rate, channels, width, deadline):
    frames = len(pcm) // (width * channels)
    limit = 1 << (width * 8 - 1)
    square_sum, clipped, silent, first, last = 0, 0, 0, None, None
    peak = 0
    frame_size = width * channels
    for frame in range(frames):
        if frame % 4096 == 0 and time.monotonic() >= deadline:
            raise _Unavailable("audio_measurement_timeout")
        start = frame * frame_size
        block = pcm[start:start + frame_size]
        if width == 1:
            samples = [value - 128 for value in block]
        elif width in {2, 4}:
            samples = struct.unpack("<" + ("h" if width == 2 else "i") * channels, block)
        else:
            samples = [int.from_bytes(block[index:index + 3], "little", signed=True)
                       for index in range(0, frame_size, 3)]
        frame_peak = max(abs(value) for value in samples)
        peak = max(peak, frame_peak)
        square_sum += sum(value * value for value in samples)
        clipped += sum(value == limit - 1 or abs(value) >= limit * _RULES["clipping_amplitude"]
                       for value in samples)
        # A quiet channel must not hide speech in another channel through downmix cancellation.
        if frame_peak <= limit * _RULES["silence_amplitude"]:
            silent += 1
        else:
            first = frame if first is None else first
            last = frame
    rms = math.sqrt(square_sum / (frames * channels)) / limit
    return {"duration_ms": round(frames * 1000 / rate, 3), "sample_rate_hz": rate,
            "channels": channels, "sample_width_bytes": width, "rms": round(rms, 8),
            "rms_dbfs": round(20 * math.log10(rms), 3) if rms else None,
            "peak": round(peak / limit, 8), "clipping_ratio": round(clipped / (frames * channels), 8),
            "silence_ratio": round(silent / frames, 8),
            "leading_silence_ms": round((first if first is not None else frames) * 1000 / rate, 3),
            "trailing_silence_ms": round((frames - last - 1 if last is not None else frames) * 1000 / rate, 3)}


def _task(db, revision, supplied, report, size):
    task_id = supplied if isinstance(supplied, str) else getattr(supplied, "id", None)
    query = select(ProviderGenerationTask.__table__)
    query = query.where(ProviderGenerationTask.id == task_id) if supplied is not None else query.where(
        ProviderGenerationTask.accepted_material_revision_id == revision.id)
    rows = db.execute(query.limit(2)).mappings().all()
    if len(rows) != 1:
        _issue(report, "incomplete" if not rows else "blocker", "audio_accepted_task_unavailable")
        return None
    row = ProviderGenerationTask(**dict(rows[0]))
    if supplied is not None and not isinstance(supplied, str) and any(
        getattr(supplied, field, None) != getattr(row, field) for field in
        ("state", "request_hash", "plan_hash", "accepted_material_revision_id", "result_hash")):
        _issue(report, "blocker", "audio_task_changed")
        return None
    if (row.state != "accepted" or row.accepted_material_revision_id != revision.id
            or row.provider_kind != "tts_provider" or row.result_hash != revision.content_hash
            or row.result_size != size or row.result_mime != revision.mime_type
            or _digest(row.acceptance_hash) is None):
        _issue(report, "blocker", "audio_accepted_task_mismatch")
        return None
    try:
        generation_tasks._verify(row)
        if not isinstance(row.result_signature, str) or not hmac.compare_digest(
            generation_tasks._sign(row, generation_tasks._result_receipt(row)), row.result_signature):
            raise ValueError
    except HTTPException as exc:
        unavailable = exc.detail == "generation_receipt_key_unavailable"
        _issue(report, "incomplete" if unavailable else "blocker",
               "audio_receipt_key_unavailable" if unavailable else "audio_task_receipt_invalid")
        return None
    except (TypeError, ValueError, KeyError):
        _issue(report, "blocker", "audio_task_receipt_invalid")
        return None
    request, plan, source = row.request_json, row.plan_json, revision.source_metadata_json or {}
    parameters = plan.get("parameters", {})
    requested_parameters = request.get("parameters", {})
    if (request.get("capability") != "tts" or plan.get("required_capability") != "tts"
            or plan.get("status") != "ready" or plan.get("dispatch_ready") is not True
            or plan.get("selected_profile") != request.get("selected_profile")
            or plan.get("model_id") != row.model_id or plan.get("adapter_version") != row.provider_version
            or generation_tasks._KEYS.get(plan.get("adapter_key")) != row.provider_key
            or plan.get("input_hash") != row.input_hash or plan.get("runtime_hash") != row.runtime_hash
            or plan.get("source_refs") != row.source_refs_json
            or _hash({"request": request, "sources": row.source_refs_json, "actor": row.owner_user_id}) != row.input_hash
            or revision.source_kind != "ai_generated" or revision.provider_key != row.provider_key
            or revision.provider_version != row.provider_version or source.get("provider_kind") != row.provider_kind
            or source.get("runtime_hash") != row.runtime_hash or source.get("input_hash") != row.input_hash
            or source.get("source_refs") != row.source_refs_json
            or not isinstance(parameters, dict) or not isinstance(requested_parameters, dict)
            or any(parameters.get(key) != value for key, value in requested_parameters.items())
            or type(parameters.get("seconds")) is not int or parameters["seconds"] <= 0):
        _issue(report, "blocker", "audio_provenance_mismatch")
        return None
    report["task"] = {"task_id": _identifier(row.id), "provider_key": _identifier(row.provider_key),
                      "provider_version": _identifier(row.provider_version), "model_id": _identifier(row.model_id),
                      "selected_profile": _identifier(plan.get("selected_profile")),
                      "execution_profile": _identifier(plan.get("execution_profile")),
                      "request_hash": row.request_hash, "plan_hash": row.plan_hash}
    report["coverage"]["accepted_task"] = "verified"
    report["coverage"]["provider_model"] = "verified_receipt"
    configuration = db.execute(select(SystemSetting.value).where(SystemSetting.key == "models")).scalar_one_or_none()
    if not isinstance(configuration, dict):
        _issue(report, "incomplete", "audio_current_binding_unavailable")
    else:
        profiles = configuration.get("profiles", {})
        selected = profiles.get(plan.get("selected_profile"), {})
        execution = profiles.get(plan.get("execution_profile"), {})
        binding = execution.get("capability_bindings", {}).get("tts")
        try:
            binding = generation_tasks.routing.Binding.model_validate(binding).model_dump(mode="json")
        except ValueError:
            binding = None
        plugin_id = plan.get("plugin_id")
        plugin = configuration.get("media_plugins", {}).get(plugin_id, {}) if plugin_id else None
        if (not selected or selected.get("enabled", True) is not True
                or not execution or execution.get("enabled", True) is not True
                or "tts" not in execution.get("declared_capabilities", []) or not isinstance(binding, dict)
                or _hash(binding) != plan.get("binding_hash")
                or plugin_id and (plugin.get("enabled") is not True or plugin.get("capability") != "tts"
                                  or plugin.get("model_profile_id") != plan.get("execution_profile")
                                  or plugin.get("registry_key") not in {None, plan.get("adapter_key")}
                                  or plugin.get("registry_version") != plan.get("adapter_version"))):
            _issue(report, "blocker", "audio_current_binding_changed")
        else:
            report["coverage"]["current_binding"] = "verified"
    applied = generation_tasks.tts_applied_parameters(row)
    if applied is None:
        report["coverage"]["voice_rate"] = "applied_parameters_not_recorded"
        _issue(report, "incomplete", "audio_applied_voice_rate_unavailable")
    elif source.get("tts_applied_parameters") != applied:
        report["coverage"]["voice_rate"] = "receipt_mismatch"
        _issue(report, "blocker", "audio_applied_voice_rate_mismatch")
    else:
        report["coverage"]["voice_rate"] = "verified_signed_result_and_material_receipt"
        report["task"]["tts_applied_parameters"] = applied
    return row


def alignment_options(value):
    """Validate explicit read-only receipt/SRT controls without interpreting legacy receipts."""
    if (not isinstance(value, dict) or set(value) - (_ASR_FIELDS | {"enabled", "srt_mode"})
            or type(value.get("enabled")) is not bool
            or not isinstance(value.get("srt_mode", "none"), str)
            or value.get("srt_mode", "none") not in {"none", "asr", "estimated"}):
        raise _Unavailable("audio_alignment_options_invalid")
    enabled, mode = value["enabled"], value.get("srt_mode", "none")
    if enabled:
        if (not _ASR_FIELDS <= set(value) or type(value["master_revision_id"]) is not int
                or not 1 <= value["master_revision_id"] <= 9007199254740991 or not isinstance(value["receipt_id"], str)
                or re.fullmatch(r"[0-9a-f]{32}", value["receipt_id"]) is None
                or _digest(value["output_hash"]) is None):
            raise _Unavailable("audio_alignment_receipt_required")
    elif set(value) & _ASR_FIELDS or mode == "asr":
        raise _Unavailable("audio_alignment_enable_required")
    return enabled, mode


def _accepted_asr(db, revision, task, options, duration_ms):
    from . import asr_suggestions

    master = db.execute(select(ContentMasterRevision.__table__).where(
        ContentMasterRevision.id == options["master_revision_id"])).mappings().first()
    if master is None or master["payload_schema"] != "video.master.v2":
        raise _Invalid("audio_alignment_accepted_receipt_required")
    summary = master["edit_summary_json"]
    provenance = summary.get("asr_provenance") if isinstance(summary, dict) else None
    if (not isinstance(provenance, dict) or summary.get("asr_receipt_id") != options["receipt_id"]
            or provenance.get("status") != "verified_output_match"
            or provenance.get("output_hash") != options["output_hash"]
            or provenance.get("source") != {"revision_id": revision.id, "content_hash": revision.content_hash}
            or any(_digest(provenance.get(key)) is None for key in
                   ("runtime_hash", "input_hash", "output_hash", "accepted_cues_hash"))
            or _identifier(provenance.get("provider_key")) is None
            or _identifier(provenance.get("provider_version")) is None):
        raise _Invalid("audio_alignment_receipt_mismatch")
    base_id = provenance.get("base_master_id")
    if type(base_id) is not int or base_id <= 0 or master["parent_revision_id"] != base_id:
        raise _Invalid("audio_alignment_receipt_mismatch")
    base = db.execute(select(ContentMasterRevision.__table__).where(
        ContentMasterRevision.id == base_id)).mappings().first()
    actor = db.execute(select(User.id, User.email, User.is_active).where(User.id == task.owner_user_id)).first()
    project = db.execute(select(ContentProject.owner_user_id, ContentProject.status).where(
        ContentProject.id == task.project_id)).first()
    unit = db.execute(select(ContentUnit.project_id, ContentUnit.status, ContentUnit.lifecycle).where(
        ContentUnit.id == master["content_unit_id"])).first()
    source = db.execute(select(MaterialRevision.__table__).where(
        MaterialRevision.id == revision.id)).mappings().first()
    if (actor is None or actor.is_active is not True or project is None or project.status == "archived"
            or project.owner_user_id != task.owner_user_id or unit is None or unit.status == "archived" or unit.lifecycle != "active"
            or unit.project_id != task.project_id or master["project_id"] != task.project_id
            or master["created_by"] != actor.email or source is None or source["model_use_allowed"] is not True
            or source["content_hash"] != revision.content_hash or source["status"] not in {"active", "usable"}
            or base is None or base["payload_schema"] != "video.master.v2"
            or base["project_id"] != master["project_id"]
            or base["content_unit_id"] != master["content_unit_id"]
            or type(base["revision_no"]) is not int or type(master["revision_no"]) is not int
            or base["revision_no"] + 1 != master["revision_no"]
            or _digest(base["context_hash"]) is None or master["context_hash"] != base["context_hash"]):
        raise _Invalid("audio_alignment_scope_or_rights_changed")
    for row in (base, master):
        if (not isinstance(row["payload_json"], dict) or _digest(row["payload_hash"]) is None
                or _hash(row["payload_json"]) != row["payload_hash"]):
            raise _Invalid("audio_alignment_master_changed")
        reference = db.execute(select(ContentMasterAssetRef.content_hash_snapshot).where(
            ContentMasterAssetRef.master_revision_id == row["id"],
            ContentMasterAssetRef.material_revision_id == revision.id,
            ContentMasterAssetRef.content_hash_snapshot == revision.content_hash).limit(1)).scalar_one_or_none()
        if reference != revision.content_hash:
            raise _Invalid("audio_alignment_source_not_in_master")
    payload = master["payload_json"]
    subtitles, timeline = payload.get("subtitles"), payload.get("timeline")
    if not isinstance(subtitles, dict) or not isinstance(timeline, dict):
        raise _Invalid("audio_alignment_cues_invalid")
    cues, timeline = subtitles.get("cues"), timeline.get("duration_ms")
    if (type(timeline) is not int or not 0 < timeline <= _MAX_SECONDS * 1000
            or not isinstance(cues, list) or not 1 <= len(cues) <= _ALIGNMENT_RULES["max_cues"]
            or sum(len(cue.get("text", "")) if isinstance(cue, dict) and isinstance(cue.get("text"), str)
                   else _ALIGNMENT_RULES["max_text_characters"] + 1 for cue in cues)
               > _ALIGNMENT_RULES["max_text_characters"]):
        raise _Invalid("audio_alignment_cues_invalid")
    # Reuse the accepted ASR segment validator, not its expiring cache or inference path.
    try:
        normalized = asr_suggestions._output({"status": "succeeded", "transcript": "", "cues": cues},
                                              min(timeline, duration_ms))["cues"]
    except HTTPException:
        raise _Invalid("audio_alignment_cues_invalid") from None
    if normalized != cues or _hash(cues) != provenance["accepted_cues_hash"]:
        raise _Invalid("audio_alignment_cues_changed")
    proof = {"master_revision_id": master["id"], "receipt_id": options["receipt_id"],
             "output_hash": provenance["output_hash"], "provenance_hash": _hash(provenance),
             "input_hash": provenance["input_hash"], "accepted_cues_hash": provenance["accepted_cues_hash"],
             "base_master_id": base_id, "base_payload_hash": base["payload_hash"],
             "master_payload_hash": master["payload_hash"], "context_hash": master["context_hash"],
             "material_revision_id": revision.id, "content_hash": revision.content_hash,
             "provider_key": provenance["provider_key"], "provider_version": provenance["provider_version"],
             "runtime_hash": provenance["runtime_hash"], "rules_hash": _hash(_ALIGNMENT_RULES)}
    return proof, cues


def _srt(revision, script, cues, duration_ms, *, estimated, proof=None):
    from .stage_contracts import StageContractError, canonical

    def timestamp(milliseconds):
        hours, remainder = divmod(milliseconds, 3600000)
        minutes, remainder = divmod(remainder, 60000)
        seconds, remainder = divmod(remainder, 1000)
        return f"{hours:02}:{minutes:02}:{seconds:02},{remainder:03}"

    lines, byte_size = [], 0
    for index, cue in enumerate(cues, 1):
        text = cue["text"]
        if ("\r" in text or "-->" in text or re.search(r"\n[ \t]*\n", text)
                or any(ord(char) < 32 and char not in "\n\t" for char in text)):
            raise _Unavailable("audio_subtitles_text_unsupported")
        if estimated:
            text = "[ESTIMATED / 估算；非ASR时轴] " + text
        block = f"{index}\n{timestamp(cue['start_ms'])} --> {timestamp(cue['end_ms'])}\n{text}\n\n"
        byte_size += len(block.encode())
        if byte_size > _SUBTITLE_LIMIT:
            raise _Unavailable("audio_subtitles_size_limit")
        lines.append(block)
    srt = "".join(lines)
    result = {"schema": "studio.audio.subtitles.v1", "mode": "estimated" if estimated else "asr",
              "estimated": estimated, "timing_basis": "script_character_weighted_estimate" if estimated else "accepted_asr_segments",
              "label": "估算字幕 / 非 ASR 时轴" if estimated else "已保存 ASR 分段时轴 / 非逐词对齐",
              "filename": "audio-estimated.srt" if estimated else "audio-asr.srt",
              "srt": srt, "srt_hash": hashlib.sha256(srt.encode()).hexdigest(), "cue_count": len(cues),
              "duration_ms": duration_ms, "material_revision_id": revision.id, "content_hash": revision.content_hash,
              "script_hash": hashlib.sha256(script.encode()).hexdigest(), "rules_hash": _hash(_ALIGNMENT_RULES)}
    if proof is not None:
        result.update({key: proof[key] for key in ("master_revision_id", "receipt_id", "output_hash", "asr_output_hash") if key in proof})
        if proof.get("schema") == "studio.audio.asr-alignment.v1":
            result["asr_attempt_id"] = proof["accepted_target"]["entity_id"]
    try:
        return canonical(result, max_bytes=24 * 1024)
    except StageContractError:
        raise _Unavailable("audio_subtitles_unsafe_or_size_limit") from None


def _estimated_cues(script, duration_ms):
    width = _ALIGNMENT_RULES["estimated_line_characters"]
    texts = [line[offset:offset + width].strip() for line in script.splitlines()
             for offset in range(0, len(line), width) if line[offset:offset + width].strip()]
    if not 1 <= len(texts) <= min(_ALIGNMENT_RULES["max_estimated_cues"], duration_ms):
        raise _Unavailable("audio_estimated_subtitles_bounds")
    total, cumulative, previous, cues = sum(map(len, texts)), 0, 0, []
    for index, text in enumerate(texts):
        cumulative += len(text)
        end = index + 1 + (duration_ms - len(texts)) * cumulative // total
        cues.append({"text": text, "start_ms": previous, "end_ms": end})
        previous = end
    return cues


def _alignment(db, revision, task, script, alignment, report, *, accepted_stage_asr=None):
    if alignment is None:
        return
    try:
        if accepted_stage_asr is None:
            enabled, mode = alignment_options(alignment)
        else:
            if (not isinstance(alignment, dict) or set(alignment) != {"enabled", "srt_mode"}
                    or alignment["enabled"] is not True or alignment["srt_mode"] not in {"none", "asr", "estimated"}):
                raise _Invalid("audio_alignment_stage_options_invalid")
            enabled, mode = True, alignment["srt_mode"]
        if not enabled and mode == "none":
            return
        if enabled:
            report["coverage"]["asr_alignment"] = "unverified"
        if (task is None or not isinstance(script, str) or not 0 < len(script) <= 10000
                or not script.strip() or script != task.request_json.get("prompt")):
            raise _Unavailable("audio_alignment_signed_script_required")
        duration = report["measured"]["duration_ms"]
        if type(duration) not in {int, float} or not math.isfinite(duration) or not 0 < duration <= _MAX_SECONDS * 1000:
            raise _Unavailable("audio_alignment_duration_unavailable")
        duration_ms = math.ceil(duration)
        def accepted_proof():
            if accepted_stage_asr is None:
                return _accepted_asr(db, revision, task, alignment, duration_ms)
            from .stage_audio_asr import validate_alignment
            from .stage_invocations import StageInvocationError

            try:
                value, segments = validate_alignment(db, accepted_stage_asr, revision, task, script)
            except (StageInvocationError, HTTPException, ValueError, TypeError, KeyError):
                raise _Invalid("audio_alignment_stage_receipt_invalid") from None
            if any(cue["end_ms"] > duration_ms for cue in segments):
                raise _Invalid("audio_alignment_cues_invalid")
            return value, segments

        proof, cues = accepted_proof() if enabled else (None, None)
        if enabled:
            def normalized(text):
                return "".join(char.casefold() for char in text if not char.isspace()
                               and not unicodedata.category(char).startswith("P"))
            # Only accepted cue texts are durable; the original full transcript is not retained.
            expected, observed = normalized(script), normalized("".join(cue["text"] for cue in cues))
            size = max(len(expected), len(observed), 1)
            differences = sum(left != right for left, right in zip(expected, observed)) + abs(len(expected) - len(observed))
            report["alignment"] = {**proof, "script_hash": hashlib.sha256(script.encode()).hexdigest(),
                "transcript_basis": "accepted_asr_cues", "comparison": _ALIGNMENT_RULES["comparison"],
                "timing_alignment": "verified_asr_segment_timing", "word_alignment": "not_run",
                "expected_characters": len(expected), "observed_characters": len(observed),
                "different_characters": differences, "difference_ratio": round(differences / size, 6)}
            report["coverage"]["asr_alignment"] = "verified_accepted_receipt_comparison"
            if differences:
                _issue(report, "warning", "audio_transcript_script_differs")
        if mode != "none":
            try:
                report["subtitles"] = _srt(revision, script,
                    _estimated_cues(script, duration_ms) if mode == "estimated" else cues,
                    duration_ms, estimated=mode == "estimated", proof=proof if mode == "asr" else None)
                if mode == "estimated":
                    _issue(report, "warning", "audio_subtitles_estimated_not_asr")
            except _Unavailable as exc:
                _issue(report, "incomplete", str(exc))
        if enabled and accepted_proof()[0] != proof:
            raise _Invalid("audio_alignment_receipt_changed_during_check")
    except _Unavailable as exc:
        _issue(report, "incomplete", str(exc))
    except _Invalid as exc:
        report.pop("alignment", None)
        report.pop("subtitles", None)
        report["coverage"]["asr_alignment"] = "unverified"
        _issue(report, "blocker", str(exc))
    except (ValueError, TypeError, KeyError, AttributeError):
        report.pop("alignment", None)
        report.pop("subtitles", None)
        report["coverage"]["asr_alignment"] = "unverified"
        _issue(report, "blocker", "audio_alignment_receipt_invalid")


def check_audio(db: Session, revision: MaterialRevision, *, task=None, quality_profile_ref,
                script=None, alignment=None, accepted_stage_asr=None) -> dict:
    """Return a bounded snapshot; consumers must rerun it after replacement or revocation.

    Alignment requires explicit enabled/master_revision_id/receipt_id/output_hash
    over a saved exact-output ASR receipt. Optional srt_mode is none/asr/estimated;
    estimated timing is labeled inside every cue. No ASR calls or writes occur.
    """
    report = {"schema": "studio.audio.qc.v1", "material_id": None, "material_revision_id": None,
              "content_hash": None, "quality_profile_ref": None, "quality_profile_hash": None,
              "rules_hash": _hash(_RULES), "thresholds": dict(_RULES), "status": "incomplete",
              "issues": [], "measured": {"duration_ms": None, "rms": None, "rms_dbfs": None,
              "clipping_ratio": None, "silence_ratio": None, "leading_silence_ms": None,
              "trailing_silence_ms": None}, "human_review_required": True,
              "coverage": {"bytes_hash": "not_run", "mime_duration": "not_run", "waveform": "not_run",
                           "accepted_task": "not_run", "provider_model": "not_run", "voice_rate": "not_run",
                           "current_binding": "not_run", "asr_alignment": "not_run",
                           "loudness": "not_run", "perceptual_quality": "human_review_required"}}
    try:
        if not isinstance(quality_profile_ref, str) or quality_profile_ref not in _PROFILE_REFS:
            raise ValueError
        studio_creative_catalog.validate_ref(quality_profile_ref, kind="quality_profile")
        report.update(quality_profile_ref=quality_profile_ref,
                      quality_profile_hash=studio_creative_catalog.digest(studio_creative_catalog.QUALITY[quality_profile_ref]))
    except (ValueError, KeyError):
        _issue(report, "blocker", "audio_quality_profile_invalid")
        return _finish(report)
    revision_id = getattr(revision, "id", None)
    if type(revision_id) is not int or revision_id <= 0:
        _issue(report, "blocker", "audio_revision_invalid")
        return _finish(report)
    try:
        # Table projections read live truth without flushing or overwriting the caller's dirty ORM objects.
        with db.no_autoflush:
            data = db.execute(select(MaterialRevision.__table__).where(MaterialRevision.id == revision_id)).mappings().first()
            if data is None:
                _issue(report, "blocker", "audio_revision_unavailable")
                return _finish(report)
            live = MaterialRevision(**dict(data))
            report.update(material_id=live.material_id, material_revision_id=live.id,
                          content_hash=_digest(live.content_hash))
            parent = db.execute(select(Material.kind, Material.status).where(Material.id == live.material_id)).first()
            if (parent is None or parent.kind != "audio" or parent.status != "active"
                    or live.status not in {"usable", "active"} or _digest(live.content_hash) is None
                    or any(getattr(revision, field, None) != getattr(live, field) for field in
                           ("material_id", "content_hash", "mime_type", "status"))):
                _issue(report, "blocker", "audio_revision_changed_or_revoked")
                return _finish(report)
            if get_settings().material_storage_backend != "local":
                _issue(report, "incomplete", "audio_local_storage_required")
                return _finish(report)
            try:
                content = materials.read_bytes_checked(db, live)
            except (HTTPException, OSError, ValueError, RuntimeError):
                _issue(report, "blocker", "audio_live_bytes_unavailable_or_changed")
                return _finish(report)
            if not content or len(content) > _MAX_BYTES:
                _issue(report, "blocker", "audio_byte_limit")
                return _finish(report)
            report["coverage"]["bytes_hash"] = "verified_live_bytes"
            report["measured"]["byte_size"] = len(content)
            accepted_task = _task(db, live, task, report, len(content))
            if script is not None and (accepted_task is None or not isinstance(script, str)
                                      or len(script) > 10000 or script != accepted_task.request_json.get("prompt")):
                _issue(report, "blocker", "audio_signed_script_mismatch")
            deadline = time.monotonic() + _PROCESS_SECONDS
            try:
                pcm, rate, channels, width, decoder = _pcm(content, live.mime_type, deadline, report)
                measured = _measure(pcm, rate, channels, width, deadline)
                report["measured"].update(measured)
                report["coverage"].update(mime_duration="verified_decoded_bytes", waveform=decoder,
                                           loudness="rms_dbfs_only_lufs_not_measured")
                if accepted_task is not None and measured["duration_ms"] > accepted_task.plan_json["parameters"]["seconds"] * 1000:
                    _issue(report, "blocker", "audio_requested_duration_exceeded")
                if measured["silence_ratio"] == 1:
                    _issue(report, "blocker", "audio_silent")
                if measured["clipping_ratio"] >= _RULES["clipping_blocker_ratio"]:
                    _issue(report, "blocker", "audio_gross_clipping")
                elif measured["clipping_ratio"] >= _RULES["clipping_warning_ratio"]:
                    _issue(report, "warning", "audio_clipping")
                if (measured["leading_silence_ms"] > _RULES["edge_silence_warning_ms"]
                        or measured["trailing_silence_ms"] > _RULES["edge_silence_warning_ms"]
                        or measured["silence_ratio"] >= _RULES["silence_warning_ratio"]):
                    _issue(report, "warning", "audio_excessive_silence")
                if measured["rms_dbfs"] is not None and not (
                    _RULES["rms_warning_min_dbfs"] <= measured["rms_dbfs"] <= _RULES["rms_warning_max_dbfs"]):
                    _issue(report, "warning", "audio_rms_outside_bounds")
            except _Unavailable as exc:
                _issue(report, "incomplete", str(exc))
            except _Invalid as exc:
                _issue(report, "blocker", str(exc))
            _alignment(db, live, accepted_task, script, alignment, report, accepted_stage_asr=accepted_stage_asr)
            final = db.execute(select(MaterialRevision.__table__).where(MaterialRevision.id == live.id)).mappings().first()
            parent_status = db.execute(select(Material.status).where(Material.id == live.material_id)).scalar_one_or_none()
            if (final is None or parent_status != "active" or any(final[field] != getattr(live, field)
                    for field in ("material_id", "content_hash", "mime_type", "status", "file_path",
                                  "provider_key", "provider_version", "source_metadata_json"))):
                _issue(report, "blocker", "audio_revision_changed_during_check")
            else:
                try:
                    materials.read_bytes_checked(db, live)
                except (HTTPException, OSError, ValueError, RuntimeError):
                    _issue(report, "blocker", "audio_live_bytes_changed_during_check")
            if accepted_task is not None:
                final_task = db.execute(select(ProviderGenerationTask.__table__).where(
                    ProviderGenerationTask.id == accepted_task.id)).mappings().first()
                if final_task is None or any(final_task[field] != getattr(accepted_task, field)
                    for field in ("state", "accepted_material_revision_id", "request_hash", "plan_hash", "result_hash",
                                  "request_json", "plan_json", "receipt_signature", "result_signature")):
                    _issue(report, "blocker", "audio_task_changed_during_check")
    except Exception:  # noqa: BLE001 DB, storage and decoder diagnostics can contain private data.
        if alignment is not None:
            report.pop("alignment", None)
            report.pop("subtitles", None)
            if isinstance(alignment, dict) and alignment.get("enabled") is True:
                report["coverage"]["asr_alignment"] = "unavailable"
        _issue(report, "incomplete", "audio_qc_unavailable")
    return _finish(report)


def _loudnorm(executable, content, audio_filter, output, timeout):
    done = subprocess.run([executable, "-nostdin", "-hide_banner", "-protocol_whitelist", "pipe,file", "-threads", "1",
                           "-i", "pipe:0", "-af", audio_filter, *output], input=content, capture_output=True,
                          timeout=timeout, check=True, env={key: os.environ[key] for key in ("PATH", "LANG", "LC_ALL") if key in os.environ})
    text = done.stderr[-8192:].decode("utf-8", "replace")
    return done.stdout, json.loads(text[text.rindex("{"):text.rindex("}") + 1])


def master_loudness(content: bytes, *, target_lufs: float = -16.0, true_peak_dbtp: float = -1.5) -> tuple[bytes, dict]:
    """Two-pass EBU R128 normalization; dynamic mode acts as the limiter when the peak ceiling needs it."""
    executable = shutil.which("ffmpeg")
    if executable is None or len(content) > _MAX_BYTES:
        raise HTTPException(422, {"code": "audio_mastering_unavailable"})
    try:
        with wave.open(io.BytesIO(content)) as source:
            rate, channels, frames = source.getframerate(), source.getnchannels(), source.getnframes()
        target = f"I={target_lufs}:TP={true_peak_dbtp}:LRA=11"
        _, first = _loudnorm(executable, content, f"loudnorm={target}:print_format=json", ["-f", "null", "-"], 120)
        measured = ":".join(f"{name}={first[key]}" for name, key in (("measured_I", "input_i"), ("measured_TP", "input_tp"),
                            ("measured_LRA", "input_lra"), ("measured_thresh", "input_thresh"), ("offset", "target_offset")))
        # A seekable file keeps complete WAV header sizes, which a pipe cannot.
        with tempfile.NamedTemporaryFile(suffix=".wav") as target_file:
            _, second = _loudnorm(executable, content, f"loudnorm={target}:{measured}:linear=true:print_format=json",
                                  ["-ar", str(rate), "-ac", str(channels), "-c:a", "pcm_s16le", "-fflags", "+bitexact", "-y", target_file.name], 180)
            mastered = target_file.read()
        with wave.open(io.BytesIO(mastered)) as result:
            if result.getnframes() != frames:
                raise ValueError("duration_changed")
    except (OSError, ValueError, KeyError, EOFError, wave.Error, subprocess.SubprocessError):
        raise HTTPException(422, {"code": "audio_mastering_failed"}) from None
    report = {"schema": "studio.audio.loudness-master.v1", "target_lufs": target_lufs, "true_peak_ceiling_dbtp": true_peak_dbtp,
              "input": {"integrated_lufs": float(first["input_i"]), "true_peak_dbtp": float(first["input_tp"]), "lra_lu": float(first["input_lra"])},
              "output": {"integrated_lufs": float(second["output_i"]), "true_peak_dbtp": float(second["output_tp"]), "lra_lu": float(second["output_lra"])},
              "normalization_type": second.get("normalization_type"), "sample_rate": rate, "channels": channels, "frames": frames}
    return mastered, report


class AudioQC:
    key = "studio.audio.qc"
    version = "1"
    consumed_fields = frozenset()
    execute = staticmethod(check_audio)


def bootstrap() -> None:
    from .content_harness.registry import RegistryError, registry

    try:
        registry.resolve("tool_provider", AudioQC.key, AudioQC.version)
    except RegistryError:
        registry.register("tool_provider", AudioQC.key, AudioQC.version, AudioQC(),
                          label="Studio Audio QC")
