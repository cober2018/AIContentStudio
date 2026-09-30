"""Bounded temporary provider previews; only explicit acceptance writes library truth."""

from __future__ import annotations

import hashlib
import io
import json
import re
import subprocess
import tempfile
import threading
import time
import uuid
import wave
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import HTTPException
from PIL import Image
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from .. import runtime_config
from ..models import AuditLog, Material, MaterialRevision, ProjectMaterialReference, User
from . import materials, provider_calls
from .content_harness import providers
from .project_authorization import lock_project_context
from .project_events import record_project_event

_HEX = re.compile(r"[0-9a-f]{64}\Z")
_MAX_BYTES = 30 * 1024 * 1024
_MAX_CACHE_BYTES = 128 * 1024 * 1024
_TTL = 900
_lock = threading.RLock()
_cache: dict[str, Preview] = {}


@dataclass
class Preview:
    actor_id: int
    provider_kind: str
    provider_key: str
    provider_version: str
    runtime_hash: str
    input_hash: str
    content: bytes
    mime_type: str
    kind: str
    content_hash: str
    project_id: int | None
    sources: tuple[tuple[int, str], ...]
    expires: float
    accepted: dict | None = None
    acceptance_hash: str | None = None
    search_origin: dict | None = None
    renderer_origin: dict | None = None
    operation_lock: threading.RLock = field(default_factory=threading.RLock, repr=False, compare=False)


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def _provider(kind: str, key: str, version: str):
    if kind == "renderer":
        from .media_renderers import resolve_renderer

        return resolve_renderer(key, version)
    try:
        provider = providers.registry.resolve(kind, key, version)
        fingerprint = provider.runtime_fingerprint()
        if provider.key != key or provider.version != version or not isinstance(fingerprint, str) or not _HEX.fullmatch(fingerprint):
            raise ValueError("runtime identity unavailable")
        return provider, fingerprint
    except Exception:  # noqa: BLE001 Runtime diagnostics must not expose credentials.
        raise HTTPException(422, "capability_unavailable") from None


def _sources(db: Session, ids: list[int], expected: tuple[tuple[int, str], ...] | None = None, *, lock: bool = False):
    refs, contents = [], []
    if lock:
        # Deterministic lock order prevents reversed input sets from deadlocking.
        for source_id in sorted(set(ids)):
            db.execute(update(MaterialRevision).where(MaterialRevision.id == source_id)
                       .values(status=MaterialRevision.status).execution_options(synchronize_session=False))
        material_ids = db.scalars(select(MaterialRevision.material_id).where(MaterialRevision.id.in_(ids))).all()
        for material_id in sorted(set(material_ids)):
            db.execute(update(Material).where(Material.id == material_id)
                       .values(status=Material.status).execution_options(synchronize_session=False))
    for source_id in ids:
        revision = db.scalar(select(MaterialRevision).where(MaterialRevision.id == source_id).execution_options(populate_existing=True))
        if revision is not None and lock:
            db.refresh(revision.material)
        if (revision is None or revision.status not in {"candidate", "usable", "active"} or revision.material.status != "active"
                or revision.model_use_allowed is not True):
            raise HTTPException(409, "provider_source_rights_unavailable")
        content = materials.read_bytes_checked(db, revision)
        if len(content) > _MAX_BYTES:
            raise HTTPException(413, "provider_source_too_large")
        refs.append((revision.id, revision.content_hash))
        contents.append(content)
    refs = tuple(refs)
    if expected is not None and refs != expected:
        raise HTTPException(409, "provider_source_changed")
    return refs, contents


def _decode(content: bytes, declared: str | None) -> tuple[str, str]:
    if not isinstance(content, bytes) or not content or len(content) > _MAX_BYTES:
        raise HTTPException(422, "provider_output_bytes_invalid")
    mime = materials.sniff_mime(content, None)
    if mime != declared:
        raise HTTPException(422, "provider_output_mime_invalid")
    try:
        if mime in {"image/png", "image/jpeg", "image/webp"}:
            with Image.open(io.BytesIO(content)) as image:
                if image.width * image.height > 16_000_000:
                    raise ValueError("pixel limit")
                image.verify()
            with Image.open(io.BytesIO(content)) as image:
                image.load()
            return "image", mime
        if mime == "audio/wav":
            with wave.open(io.BytesIO(content)) as audio:
                expected = audio.getnframes() * audio.getnchannels() * audio.getsampwidth()
                if expected > _MAX_BYTES or audio.getframerate() < 1 or len(audio.readframes(audio.getnframes())) != expected:
                    raise ValueError("audio invalid")
            return "audio", mime
        if mime == "video/mp4":
            with tempfile.TemporaryDirectory() as temporary:
                source = Path(temporary) / "output.mp4"
                source.write_bytes(content)
                result = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                         "stream=width,height", "-of", "json", str(source)],
                                        capture_output=True, timeout=10, check=False)
                streams = json.loads(result.stdout).get("streams", [])
                if result.returncode or not streams or streams[0].get("width", 0) < 1 or streams[0].get("height", 0) < 1:
                    raise ValueError("video invalid")
                if streams[0]["width"] * streams[0]["height"] > 16_000_000:
                    raise ValueError("pixel limit")
                decoded = subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-threads", "1", "-i", str(source),
                                          "-f", "null", "-"], capture_output=True, timeout=10, check=False)
                if decoded.returncode:
                    raise ValueError("video decode failed")
            return "video", mime
    except (OSError, ValueError, EOFError, wave.Error, subprocess.SubprocessError, Image.DecompressionBombError):
        raise HTTPException(422, "provider_output_decode_failed") from None
    raise HTTPException(422, "provider_output_mime_unsupported")


def _prune() -> None:
    now = time.monotonic()
    for key in [key for key, preview in _cache.items() if preview.expires <= now]:
        del _cache[key]


def _get(stage_id: str, user: User) -> Preview:
    _prune()
    preview = _cache.get(stage_id)
    if preview is None or preview.actor_id != user.id:
        raise HTTPException(404, "provider_preview_unavailable_or_expired")
    return preview


def stage_output(user: User, *, kind: str, key: str, version: str, runtime_hash: str, input_hash: str,
                 output: providers.MediaOutput, project_id: int | None, sources=(), search_origin: dict | None = None,
                 renderer_origin: dict | None = None) -> dict:
    media_kind, mime = _decode(output.content, output.mime_type)
    expected_kind = (renderer_origin or {}).get("modality") if kind == "renderer" else {"image_provider": "image", "search_provider": "image", "video_provider": "video", "tts_provider": "audio"}[kind]
    if expected_kind == "graphic":
        expected_kind = "image"
    if media_kind != expected_kind:
        raise HTTPException(422, "provider_output_kind_mismatch")
    content_hash = hashlib.sha256(output.content).hexdigest()
    preview = Preview(user.id, kind, key, version, runtime_hash, input_hash,
                      output.content, mime, media_kind, content_hash, project_id, sources, time.monotonic() + _TTL,
                      search_origin=search_origin, renderer_origin=renderer_origin)
    with _lock:
        _prune()
        if (len(_cache) >= 64 or sum(item.actor_id == user.id for item in _cache.values()) >= 8
                or sum(len(item.content) for item in _cache.values()) + len(preview.content) > _MAX_CACHE_BYTES):
            raise HTTPException(429, "provider_preview_capacity")
        stage_id = uuid.uuid4().hex
        _cache[stage_id] = preview
    return {"stage_id": stage_id, "content_hash": content_hash, "mime_type": mime, "kind": media_kind,
            "provider_key": key, "provider_version": version, "input_hash": preview.input_hash,
            "public_ready": False, "verified": False, "expires_in_seconds": _TTL}


def stage(db: Session, user: User, request: dict) -> dict:
    project_id = request.get("project_id")
    if project_id is not None:
        project = lock_project_context(db, project_id, user)
        if project.status == "archived":
            raise HTTPException(409, "project_archived")
    kind, key, version = request["provider_kind"], request["provider_key"], request["provider_version"]
    provider, runtime_hash = _provider(kind, key, version)
    refs, source_bytes = _sources(db, request.get("source_revision_ids", []), lock=True)
    with _lock:
        _prune()
        if len(_cache) >= 64 or sum(preview.actor_id == user.id for preview in _cache.values()) >= 8:
            raise HTTPException(429, "provider_preview_capacity")
    try:
        output = provider_calls.call(provider.generate, {**request, "source_bytes": source_bytes, "timeout_seconds": 30})
    except provider_calls.ProviderCapacityError:
        raise HTTPException(429, "provider_execution_capacity") from None
    except TimeoutError:
        raise HTTPException(409, "provider_outcome_unknown") from None
    except Exception:  # noqa: BLE001 Provider diagnostics can contain credentials.
        raise HTTPException(502, "provider_execution_failed") from None
    finally:
        # Dispatch needs live authorization; cache publication must not hold DB locks.
        db.rollback()
    if not isinstance(output, providers.MediaOutput) or output.status != "succeeded":
        if getattr(output, "status", None) == "unavailable":
            raise HTTPException(422, "capability_unavailable")
        raise HTTPException(409, "provider_outcome_unknown" if getattr(output, "status", None) == "unknown" else "provider_execution_failed")
    return stage_output(user, kind=kind, key=key, version=version, runtime_hash=runtime_hash,
                        input_hash=_hash({**request, "sources": refs}), output=output, project_id=project_id, sources=refs)


def preview_bytes(stage_id: str, user: User) -> tuple[bytes, str]:
    with _lock:
        preview = _get(stage_id, user)
        return preview.content, preview.mime_type


def accept(db: Session, user: User, stage_id: str, decision: dict) -> dict:
    with _lock:
        preview = _get(stage_id, user)
    with preview.operation_lock:
        with _lock:
            if _get(stage_id, user) is not preview:
                raise HTTPException(409, "provider_preview_changed")
        decision_hash = _hash(decision)
        if not decision.get("confirmed"):
            raise HTTPException(422, "provider_acceptance_required")
        if decision.get("license_code") == "CC-BY-4.0" and not (decision.get("attribution_text") or "").strip():
            raise HTTPException(422, "provider_attribution_required")
        if preview.search_origin and any(decision.get(field) != preview.search_origin[field] for field in
                                         ("license_code", "license_evidence_hash", "attribution_text")):
            raise HTTPException(422, "search_license_decision_mismatch")
        if preview.accepted is not None:
            if preview.acceptance_hash != decision_hash:
                raise HTTPException(409, "provider_acceptance_conflict")
            revision = db.get(MaterialRevision, preview.accepted["material_revision_id"])
            if revision is None or revision.status not in {"candidate", "usable", "active"}:
                raise HTTPException(409, "provider_accepted_revision_unavailable")
            return preview.accepted
        if preview.renderer_origin:
            from .media_renderers import revalidate_preview

            revalidate_preview(db, user, preview, decision)
        if _provider(preview.provider_kind, preview.provider_key, preview.provider_version)[1] != preview.runtime_hash:
            raise HTTPException(409, "provider_runtime_changed")
        if hashlib.sha256(preview.content).hexdigest() != preview.content_hash:
            raise HTTPException(409, "provider_preview_corrupt")
        if preview.project_id is not None:
            project = lock_project_context(db, preview.project_id, user)
            if project.status == "archived":
                raise HTTPException(409, "project_archived")
        if not preview.renderer_origin:
            _sources(db, [row[0] for row in preview.sources], preview.sources, lock=True)
        safe = {"provider_kind": preview.provider_kind, "runtime_hash": preview.runtime_hash,
                "input_hash": preview.input_hash, "source_refs": [{"revision_id": rid, "content_hash": digest} for rid, digest in preview.sources],
                "license_code": decision["license_code"], "license_evidence_hash": decision["license_evidence_hash"]}
        if preview.search_origin:
            safe.update({field: preview.search_origin[field] for field in ("source_id", "fetch_url_hash")})
        if preview.renderer_origin:
            safe["renderer_origin"] = preview.renderer_origin
        suffix = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "audio/wav": ".wav", "video/mp4": ".mp4"}[preview.mime_type]
        try:
            material = materials.create_material(db, kind=preview.kind, title=decision["title"], created_by=user.email)
            revision = materials.create_revision(db, material, content=preview.content, suffix=suffix,
                                                 declared_mime=preview.mime_type, source_kind="web_search" if preview.search_origin else "upstream" if preview.renderer_origin else "ai_generated", source_metadata=safe,
                                                 source_url=preview.search_origin.get("source_url") if preview.search_origin else None,
                                                 provider_key=preview.provider_key, provider_version=preview.provider_version,
                                                 public_use_allowed=decision["public_use_allowed"], model_use_allowed=decision["model_use_allowed"],
                                                 commercial_use_allowed=decision["commercial_use_allowed"], created_by=user.email)
            revision.attribution_text = decision.get("attribution_text")
            revision.status = "usable"
            if preview.project_id is not None:
                reference = ProjectMaterialReference(project_id=preview.project_id, material_revision_id=revision.id,
                                                     origin="system_reference", status="active", attached_by=user.email)
                db.add(reference)
                db.flush()
                record_project_event(db, project_id=preview.project_id, event_type="asset.attached", actor=user.email,
                                     entity_type="material_revision", entity_id=revision.id,
                                     payload={"reference_id": reference.id, "content_hash": revision.content_hash})
            db.add(AuditLog(event="provider.media_accepted", actor=user.email, entity_type="material_revision",
                            entity_id=str(revision.id), detail_json=safe))
            if preview.renderer_origin:
                revalidate_preview(db, user, preview, decision)
            with runtime_config.configuration_guard():
                if _provider(preview.provider_kind, preview.provider_key, preview.provider_version)[1] != preview.runtime_hash:
                    raise HTTPException(409, "provider_runtime_changed")
                with _lock:
                    if _get(stage_id, user) is not preview or hashlib.sha256(preview.content).hexdigest() != preview.content_hash:
                        raise HTTPException(409, "provider_preview_changed")
                    db.commit()
        except Exception:
            db.rollback()
            raise
        preview.accepted = {"material_id": material.id, "material_revision_id": revision.id, "content_hash": revision.content_hash}
        preview.acceptance_hash = decision_hash
        return preview.accepted
