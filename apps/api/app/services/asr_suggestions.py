"""Actor-scoped ASR proposals; explicit Master saves verify their provenance."""

import copy
import io
import json
import math
import subprocess
import tempfile
import threading
import time
import uuid
import wave
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import runtime_config
from ..models import ContentMasterRevision, MaterialRevision, ProjectMaterialReference, ProjectWorkflowOutput, User
from . import content_masters, provider_calls, provider_media

_lock = threading.RLock()
_cache = {}
_TTL = 900


@contextmanager
def commit_guard(receipt_id, user_id, project_id, unit_id, provenance):
    # Rechecking the old base's currentness after child flush would reject every valid save.
    with runtime_config.configuration_guard(), _lock:
        _prune()
        receipt = _cache.get(receipt_id)
        if receipt is None or (receipt.actor_id, receipt.project_id, receipt.unit_id) != (user_id, project_id, unit_id):
            raise HTTPException(422, "asr_receipt_unavailable_or_expired")
        if (receipt.master_id != provenance["base_master_id"]
                or receipt.input_hash != provenance["input_hash"]
                or provider_media._hash(receipt.output) != provenance["output_hash"]):
            raise HTTPException(409, "asr_receipt_changed")
        if provider_media._provider("asr_provider", receipt.provider_key, receipt.provider_version)[1] != receipt.runtime_hash:
            raise HTTPException(409, "asr_runtime_changed")
        yield


@dataclass(frozen=True)
class Receipt:
    actor_id: int
    project_id: int
    unit_id: int
    master_id: int
    payload_hash: str
    context_hash: str
    provider_key: str
    provider_version: str
    runtime_hash: str
    source: tuple[int, str]
    input_hash: str
    output: dict
    expires: float


def _base(db, project_id, unit_id, master_id, user):
    project, unit = content_masters.owned_unit(db, project_id, unit_id, user, mutate=True)
    row = db.get(ContentMasterRevision, master_id)
    latest = db.scalar(select(ContentMasterRevision.id).where(ContentMasterRevision.content_unit_id == unit_id).order_by(ContentMasterRevision.revision_no.desc()).limit(1))
    if row is None or row.project_id != project_id or row.content_unit_id != unit_id:
        raise HTTPException(404, "asr_master_unavailable")
    if row.payload_schema != "video.master.v2" or row.id != latest:
        raise HTTPException(409, "asr_current_video_v2_required")
    if (content_masters._hash(row.payload_json) != row.payload_hash
            or content_masters._hash(content_masters._context(db, project, unit, content_form=row.content_form)) != row.context_hash):
        raise HTTPException(409, "asr_master_changed")
    return row


def _duration(content, mime):
    provider_media._decode(content, mime)
    if mime == "audio/wav":
        with wave.open(io.BytesIO(content)) as audio:
            duration = audio.getnframes() / audio.getframerate()
    elif mime == "video/mp4":
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.mp4"
            source.write_bytes(content)
            try:
                result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(source)], capture_output=True, timeout=10, check=False)
                if result.returncode:
                    raise ValueError("duration unavailable")
                duration = float(json.loads(result.stdout)["format"]["duration"])
            except (OSError, ValueError, KeyError, subprocess.SubprocessError):
                raise HTTPException(422, "asr_source_duration_invalid") from None
    else:
        raise HTTPException(422, "asr_source_mime_unsupported")
    if not math.isfinite(duration) or not 0 < duration <= 600:
        raise HTTPException(422, "asr_source_duration_invalid")
    return math.ceil(duration * 1000)


def _output(raw, duration_ms):
    if not isinstance(raw, dict) or raw.get("status") != "succeeded":
        raise HTTPException(409, "asr_outcome_unknown" if isinstance(raw, dict) and raw.get("status") == "unknown" else "asr_execution_failed")
    transcript, cues = raw.get("transcript"), raw.get("cues")
    if (not isinstance(transcript, str) or len(transcript) > 100_000 or "\x00" in transcript
            or not isinstance(cues, list) or not 1 <= len(cues) <= 1000):
        raise HTTPException(422, "asr_output_invalid")
    normalized, previous_end = [], 0
    for order, cue in enumerate(cues):
        if not isinstance(cue, dict):
            raise HTTPException(422, "asr_output_invalid")
        text, start, end = cue.get("text"), cue.get("start_ms"), cue.get("end_ms")
        if (not isinstance(text, str) or not text.strip() or len(text) > 500 or "\x00" in text
                or type(start) is not int or type(end) is not int or not previous_end <= start < end <= duration_ms):
            raise HTTPException(422, "asr_output_invalid")
        normalized.append({"id": f"asr-{order + 1}", "order": order, "text": text, "start_ms": start, "end_ms": end})
        previous_end = end
    return {"transcript": transcript, "cues": normalized}


def _prune():
    for key in [key for key, receipt in _cache.items() if receipt.expires <= time.monotonic()]:
        del _cache[key]


def _capacity(user, incoming_bytes=0):
    _prune()
    if (len(_cache) >= 40 or sum(row.actor_id == user.id for row in _cache.values()) >= 8
            or sum(len(json.dumps(row.output).encode()) for row in _cache.values()) + incoming_bytes > 4_000_000):
        raise HTTPException(429, "asr_receipt_capacity")


def _visible_source(db, project_id, base, source_id):
    asset = next((ref for ref in content_masters._serialize(db, base)["assets"]
                  if ref["material_revision_id"] == source_id), None)
    if asset is None:
        raise HTTPException(422, "asr_source_not_in_master")
    material = db.get(MaterialRevision, source_id)
    if material is None or material.content_hash != asset["content_hash"]:
        raise HTTPException(409, "asr_source_changed")
    visible = db.scalar(select(ProjectMaterialReference.id).where(
        ProjectMaterialReference.project_id == project_id,
        ProjectMaterialReference.material_revision_id == source_id,
        ProjectMaterialReference.status == "active"))
    generated = db.scalars(select(ProjectWorkflowOutput).where(
        ProjectWorkflowOutput.project_id == project_id,
        ProjectWorkflowOutput.output_kind == "material_revision",
        ProjectWorkflowOutput.entity_id == source_id)).all()
    if visible is None and not any(content_masters._verified_generated_asset(db, output, material) for output in generated):
        raise HTTPException(422, "asr_source_not_project_visible")
    return (source_id, asset["content_hash"])


def suggest(db: Session, project_id: int, unit_id: int, master_id: int, user: User, request: dict) -> dict:
    started = time.monotonic()
    base = _base(db, project_id, unit_id, master_id, user)
    if request["base_payload_hash"] != base.payload_hash:
        raise HTTPException(409, "asr_master_changed")
    source_id = request["source_revision_id"]
    source = _visible_source(db, project_id, base, source_id)
    refs, contents = provider_media._sources(db, [source_id], (source,), lock=True)
    revision = db.get(MaterialRevision, source_id)
    source_mime = revision.mime_type
    provider, runtime = provider_media._provider("asr_provider", request["provider_key"], request["provider_version"])
    from .local_mlx_asr_provider import TIMEOUT_SECONDS, LocalASRUnavailable, LocalMLXASRProvider

    local = type(provider) is LocalMLXASRProvider
    # Local probing/decoding must stay inside the same offline process boundary.
    duration = min(600_000 if local else _duration(contents[0], source_mime), base.payload_json["timeline"]["duration_ms"])
    if duration <= 0:
        raise HTTPException(422, "asr_timeline_duration_required")
    timeout = TIMEOUT_SECONDS - (time.monotonic() - started) if local else 30
    if timeout <= 2:
        raise HTTPException(409, "asr_outcome_unknown")
    with _lock:
        _capacity(user)
    # Keep project/source authorization serialized through dispatch, not just save.
    try:
        provider_request = {"source_bytes": contents[0], "source_hash": refs[0][1], "mime_type": source_mime,
                            "max_duration_ms": duration, "timeout_seconds": timeout}
        raw = (provider_calls.call(provider.transcribe, provider_request, timeout_seconds=timeout) if local
               else provider_calls.call(provider.transcribe, provider_request))
    except provider_calls.ProviderCapacityError:
        raise HTTPException(429, "provider_execution_capacity") from None
    except TimeoutError:
        raise HTTPException(409, "asr_outcome_unknown") from None
    except LocalASRUnavailable:
        raise HTTPException(422, "local_asr_unavailable") from None
    except Exception:  # noqa: BLE001 External diagnostics can include secrets.
        raise HTTPException(502, "asr_execution_failed") from None
    if local and provider.runtime_fingerprint() != runtime:
        raise HTTPException(409, "asr_runtime_changed")
    if local:
        source_duration = raw.get("source_duration_ms") if isinstance(raw, dict) else None
        if type(source_duration) is not int or not 0 < source_duration <= 600_000:
            raise HTTPException(422, "asr_source_duration_invalid")
        duration = min(duration, source_duration)
    input_hash = provider_media._hash({"master_id": base.id, "payload_hash": base.payload_hash, "context_hash": base.context_hash,
        "source": refs[0], "runtime_hash": runtime, "duration_ms": duration})
    fields = (user.id, project_id, unit_id, base.id, base.payload_hash, base.context_hash, request["provider_key"], request["provider_version"], runtime, refs[0], input_hash)
    output = _output(raw, duration)
    receipt_id = uuid.uuid4().hex
    receipt = Receipt(*fields, output=output, expires=time.monotonic() + _TTL)
    with _lock:
        _capacity(user, len(json.dumps(output).encode()))
        _cache[receipt_id] = receipt
    return {"receipt_id": receipt_id, **copy.deepcopy(output), "source": {"revision_id": refs[0][0], "content_hash": refs[0][1]},
        "provider_key": request["provider_key"], "provider_version": request["provider_version"], "runtime_hash": runtime,
        "input_hash": input_hash, "output_hash": provider_media._hash(output), "expires_in_seconds": _TTL, "verified": False}


def verify_for_save(db, project_id, unit_id, user, base, payload, receipt_id):
    with _lock:
        _prune()
        receipt = _cache.get(receipt_id) if isinstance(receipt_id, str) else None
        if receipt is None or (receipt.actor_id, receipt.project_id, receipt.unit_id) != (user.id, project_id, unit_id):
            raise HTTPException(422, "asr_receipt_unavailable_or_expired")
    if (base is None or base.payload_schema != "video.master.v2" or base.id != receipt.master_id
            or base.payload_hash != receipt.payload_hash or base.context_hash != receipt.context_hash):
        raise HTTPException(409, "asr_master_changed")
    if provider_media._provider("asr_provider", receipt.provider_key, receipt.provider_version)[1] != receipt.runtime_hash:
        raise HTTPException(409, "asr_runtime_changed")
    _base(db, project_id, unit_id, base.id, user)
    if _visible_source(db, project_id, base, receipt.source[0]) != receipt.source:
        raise HTTPException(409, "asr_source_changed")
    provider_media._sources(db, [receipt.source[0]], (receipt.source,), lock=True)
    matching = payload["subtitles"]["cues"] == receipt.output["cues"]
    return {"provider_key": receipt.provider_key, "provider_version": receipt.provider_version, "runtime_hash": receipt.runtime_hash,
        "base_master_id": receipt.master_id, "source": {"revision_id": receipt.source[0], "content_hash": receipt.source[1]},
        "input_hash": receipt.input_hash, "output_hash": provider_media._hash(receipt.output),
        "accepted_cues_hash": provider_media._hash(payload["subtitles"]["cues"]),
        "status": "verified_output_match" if matching else "subsequently_modified"}
