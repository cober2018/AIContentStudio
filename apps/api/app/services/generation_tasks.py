"""Durable one-send claims and explicit acceptance; no scheduler or retry engine."""

from __future__ import annotations

import hashlib
import hmac
import io
import json
import os
import re
import subprocess
import tempfile
import uuid
import wave
from datetime import UTC, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

from fastapi import HTTPException
from PIL import Image
from sqlalchemy import inspect, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import runtime_config
from ..models import (
    ContentProject,
    ContentUnit,
    MaterialRevision,
    ProviderGenerationTask,
    User,
    WorkflowRun,
    WorkflowStep,
    WorkflowStepAttempt,
    utcnow,
)
from . import model_capability_routing as routing
from . import provider_calls, provider_media
from .material_storage import provider as material_storage
from .project_authorization import authorize_project_run, lock_project_context

_HASH = re.compile(r"[0-9a-f]{64}\Z")
_ID = re.compile(r"[A-Za-z0-9_.-]{1,200}\Z")
_KINDS = {"image_generation": "image_provider", "video_generation": "video_provider", "tts": "tts_provider"}
_KEYS = {"openai.compatible": "image.openai", "minimax.cli": "minimax.cli", "google.native": "google.native", "xai.native": "xai.native"}


def _storage():
    from ..config import get_settings

    # This local production slice must not perform MinIO network IO under locks.
    if get_settings().material_storage_backend != "local":
        raise HTTPException(422, "generation_local_storage_required")
    return material_storage()


def _schema(db: Session):
    if not inspect(db.get_bind()).has_table("provider_generation_task"):
        raise HTTPException(409, "generation_schema_unavailable")


def _hash(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _key(key_id: str | None = None) -> tuple[str, bytes]:
    # An explicit local secret survives restart; never generate a startup key.
    try:
        keys = json.loads(os.environ.get("AICS_GENERATION_RECEIPT_KEYS", "{}"))
        key_id = key_id or os.environ.get("AICS_GENERATION_RECEIPT_KEY_ID")
        if not isinstance(key_id, str) or not _ID.fullmatch(key_id) or not isinstance(keys, dict) or len(keys) > 8:
            raise ValueError
        raw = keys.get(key_id)
        if not isinstance(raw, str) or not re.fullmatch(r"[0-9a-f]{64}", raw):
            raise ValueError
        return key_id, bytes.fromhex(raw)
    except (TypeError, ValueError):
        raise HTTPException(409, "generation_receipt_key_unavailable") from None


def _receipt(row: ProviderGenerationTask) -> dict:
    return {"id": row.id, "owner": row.owner_user_id, "project": row.project_id,
            "attempt": row.workflow_step_attempt_id, "request": row.request_hash,
            "plan": row.plan_hash, "runtime": row.runtime_hash, "credential": row.credential_epoch,
            "input": row.input_hash, "kind": row.provider_kind, "provider": row.provider_key,
            "version": row.provider_version, "model": row.model_id, "protocol": row.protocol_version,
            "key_id": row.receipt_key_id}


def _sign(row: ProviderGenerationTask, value: dict) -> str:
    return hmac.new(_key(row.receipt_key_id)[1], _hash(value).encode(), hashlib.sha256).hexdigest()


def _verify(row: ProviderGenerationTask) -> None:
    request_hash = _hash({"request": row.request_json, "plan": row.plan_json, "sources": row.source_refs_json})
    if (_hash(row.plan_json) != row.plan_hash or request_hash != row.request_hash
            or not hmac.compare_digest(_sign(row, _receipt(row)), row.receipt_signature)):
        raise HTTPException(409, "generation_receipt_invalid")


def _result_receipt(row: ProviderGenerationTask) -> dict:
    return {**_receipt(row), "job": row.provider_job_id, "file": row.provider_file_id,
            "storage": row.result_storage_key, "mime": row.result_mime,
            "hash": row.result_hash, "size": row.result_size}


def _get(db: Session, user: User, task_id: str, *, mutate: bool = False) -> ProviderGenerationTask:
    _schema(db)
    row = db.scalar(select(ProviderGenerationTask).where(ProviderGenerationTask.id == task_id,
        ProviderGenerationTask.owner_user_id == user.id).execution_options(populate_existing=True))
    if row is None:
        raise HTTPException(404, "generation_task_unavailable")
    if row.project_id is not None:
        project = lock_project_context(db, row.project_id, user) if mutate else db.get(ContentProject, row.project_id)
        if project is None or project.owner_user_id != user.id:
            raise HTTPException(404, "generation_task_unavailable")
        if mutate and project.status == "archived":
            raise HTTPException(409, "project_archived")
    if row.workflow_step_attempt_id is not None:
        attempt = db.get(WorkflowStepAttempt, row.workflow_step_attempt_id)
        run = db.get(WorkflowRun, attempt.run_id) if attempt else None
        unit = db.get(ContentUnit, run.content_unit_id) if run else None
        if unit is None or unit.project_id != row.project_id:
            raise HTTPException(404, "generation_task_unavailable")
        authorize_project_run(db, run, user, mutate=mutate)
    return row


def view(row: ProviderGenerationTask) -> dict:
    # Never expose prompts, connection config, download URLs or raw provider data.
    return {"task_id": row.id, "state": row.state, "revision": row.revision,
            "provider_key": row.provider_key, "provider_version": row.provider_version,
            "model_id": row.model_id, "project_id": row.project_id,
            "workflow_step_attempt_id": row.workflow_step_attempt_id,
            "capability": row.request_json.get("capability"),
            "selected_profile": row.plan_json.get("selected_profile"),
            "execution_profile": row.plan_json.get("execution_profile"),
            "plugin_id": row.plan_json.get("plugin_id"),
            "route_reason": row.plan_json.get("route_reason"),
            "frozen_parameters": {key: value for key, value in row.plan_json.get("parameters", {}).items()
                                  if key in {"items", "pixels", "seconds", "timeout_seconds"} and type(value) is int},
            "reason": row.reason_code, "has_original_job": row.provider_job_id is not None,
            "content_hash": row.result_hash, "mime_type": row.result_mime,
            "material_revision_id": row.accepted_material_revision_id,
            "created_at": row.created_at.isoformat(), "updated_at": row.updated_at.isoformat(), "verified": False}


def read(db: Session, user: User, task_id: str) -> dict:
    return view(_get(db, user, task_id))


def list_tasks(db: Session, user: User) -> list[dict]:
    _schema(db)
    rows = db.scalars(select(ProviderGenerationTask).where(ProviderGenerationTask.owner_user_id == user.id)
        .order_by(ProviderGenerationTask.created_at.desc(), ProviderGenerationTask.id.desc()).limit(50)).all()
    return [view(row) for row in rows]


def _identity(provider, model_id: str, receipt_key_id: str | None = None) -> dict | None:
    # Providers must prove a safe, stable credential context; CLI version is not it.
    method = getattr(provider, "durable_identity", None)
    if not callable(method):
        return None
    try:
        historical = getattr(provider, "durable_identity_for_key", None)
        value = historical(model_id, receipt_key_id) if receipt_key_id is not None and callable(historical) else method(model_id)
        if (not isinstance(value, dict) or set(value) != {"credential_epoch", "protocol_version"}
                or not isinstance(value["credential_epoch"], str) or not _HASH.fullmatch(value["credential_epoch"])
                or not isinstance(value["protocol_version"], str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,50}", value["protocol_version"])):
            return None
        return value
    except Exception:  # noqa: BLE001 Never project provider auth diagnostics.
        return None


def prepare(db: Session, user: User, request: dict, *, workflow_attempt: WorkflowStepAttempt | None = None) -> dict:
    _schema(db)
    _storage()
    key_id, _ = _key()
    idempotency_key = request["idempotency_key"]
    old = db.scalar(select(ProviderGenerationTask).where(ProviderGenerationTask.owner_user_id == user.id,
        ProviderGenerationTask.idempotency_key == idempotency_key))
    normalized = {key: value for key, value in request.items() if key != "idempotency_key"}
    if workflow_attempt is not None:
        run = db.get(WorkflowRun, workflow_attempt.run_id)
        unit = db.get(ContentUnit, run.content_unit_id) if run else None
        step = db.get(WorkflowStep, workflow_attempt.step_id)
        if (unit is None or unit.project_id != request.get("project_id") or step is None
                or step.run_id != run.id or step.node_id != workflow_attempt.node_id
                or workflow_attempt.status != "started" or workflow_attempt.plugin_key != "media.generate"
                or step.plugin_key != "media.generate"):
            raise HTTPException(409, "generation_workflow_scope_invalid")
        authorize_project_run(db, run, user, mutate=True)
        normalized["workflow_step_attempt_id"] = workflow_attempt.id
    if old is not None:
        _get(db, user, old.id, mutate=True)
        _verify(old)
        if old.request_json != normalized:
            raise HTTPException(409, "generation_idempotency_conflict")
        return view(old)
    project_id = request.get("project_id")
    if project_id is not None and lock_project_context(db, project_id, user).status == "archived":
        raise HTTPException(409, "project_archived")
    refs, _ = provider_media._sources(db, request.get("source_revision_ids", []), lock=True)
    sources = [{"revision_id": rid, "content_hash": digest} for rid, digest in refs]
    input_hash = _hash({"request": normalized, "sources": sources, "actor": user.id})
    plan = routing.plan(db, capability=request["capability"], selected_profile=request["selected_profile"],
        explicit_plugin=request.get("explicit_plugin"), input_hash=input_hash, source_refs=sources,
        parameters=request.get("parameters", {}), _for_execution=True)
    if plan.get("status") != "ready":
        raise HTTPException(422, plan.get("reason") or "execution_plan_unavailable")
    routing.revalidate_plan(db, plan)
    kind = _KINDS[request["capability"]]
    provider_key = _KEYS.get(plan["adapter_key"])
    if provider_key is None:
        raise HTTPException(422, "capability_unavailable")
    provider, runtime_hash = provider_media._provider(kind, provider_key, plan["adapter_version"])
    identity = _identity(provider, plan["model_id"], key_id)
    # Process-local signatures are not used as persistent authorization receipts.
    frozen = {key: value for key, value in plan.items() if key not in {"plan_signature", "plan_hash"}}
    row = ProviderGenerationTask(id=uuid.uuid4().hex, owner_user_id=user.id, project_id=project_id,
        workflow_step_attempt_id=workflow_attempt.id if workflow_attempt else None,
        idempotency_key=idempotency_key, request_json=normalized, plan_json=frozen,
        plan_hash=_hash(frozen), request_hash=_hash({"request": normalized, "plan": frozen, "sources": sources}),
        source_refs_json=sources, input_hash=input_hash, runtime_hash=runtime_hash,
        credential_epoch=identity["credential_epoch"] if identity else "0" * 64,
        protocol_version=identity["protocol_version"] if identity else "unverified",
        receipt_key_id=key_id, provider_kind=kind, provider_key=provider_key,
        provider_version=plan["adapter_version"], model_id=plan["model_id"], state="prepared", revision=1,
        reason_code=None if identity else "credential_continuity_unverified")
    row.receipt_signature = _sign(row, _receipt(row))
    try:
        db.add(row)
        db.commit()
    except IntegrityError:
        db.rollback()
        # Unique owner/key races are read back, not re-sent.
        existing = db.scalar(select(ProviderGenerationTask).where(ProviderGenerationTask.owner_user_id == user.id,
            ProviderGenerationTask.idempotency_key == idempotency_key))
        if existing is None or existing.request_hash != row.request_hash:
            raise HTTPException(409, "generation_idempotency_conflict") from None
        _get(db, user, existing.id, mutate=True)
        _verify(existing)
        return view(existing)
    return view(row)


def workflow_request(config: dict) -> dict:
    allowed = {"capability", "selected_profile", "explicit_plugin", "prompt", "parameters", "source_revision_ids", "inputs"}
    if not isinstance(config, dict) or set(config) - allowed:
        raise ValueError("生成节点配置含未支持字段")
    inputs = config.get("inputs") or {}
    if not isinstance(inputs, dict) or set(inputs) - {"prompt", "source_revision_ids"}:
        raise ValueError("生成节点输入映射无效")
    request = {key: config.get(key) for key in ("capability", "selected_profile", "explicit_plugin")}
    request.update(prompt=inputs.get("prompt", config.get("prompt")),
        source_revision_ids=inputs.get("source_revision_ids", config.get("source_revision_ids", [])),
        parameters=config.get("parameters", {}))
    if (not isinstance(request["capability"], str) or request["capability"] not in _KINDS
            or not isinstance(request["selected_profile"], str)
            or not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", request["selected_profile"])
            or request["explicit_plugin"] is not None and (not isinstance(request["explicit_plugin"], str)
                or not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", request["explicit_plugin"]))):
        raise ValueError("生成节点能力或模型/插件引用无效")
    if not isinstance(request["prompt"], str) or not 1 <= len(request["prompt"].strip()) <= 2000:
        raise ValueError("生成节点需要有界提示词")
    ids, params = request["source_revision_ids"], request["parameters"]
    if (not isinstance(ids, list) or len(ids) > 4 or any(type(item) is not int or item < 1 for item in ids)
            or not isinstance(params, dict) or set(params) - {"items", "pixels", "seconds", "tokens", "timeout_seconds"}
            or any(type(value) is not int or value < 1 for value in params.values())):
        raise ValueError("生成节点来源或授权参数无效")
    return request


def _workflow_context(db: Session, run: WorkflowRun, step: WorkflowStep, user: User):
    from .workflow_engine import canonical_checksum

    if user.role not in {"admin", "editor"}:
        raise HTTPException(403, "generation_editor_required")
    unit = db.get(ContentUnit, run.content_unit_id) if run.content_unit_id else None
    if unit is None or step.run_id != run.id or step.plugin_key != "media.generate":
        raise HTTPException(409, "generation_workflow_scope_invalid")
    lock_project_context(db, unit.project_id, user)
    db.execute(update(WorkflowStep).where(WorkflowStep.id == step.id).values(status=WorkflowStep.status)
        .execution_options(synchronize_session=False))
    db.refresh(run)
    db.refresh(step)
    authorize_project_run(db, run, user, mutate=True)
    if run.status == "canceled" or step.status not in {"running", "waiting_input", "succeeded"}:
        raise HTTPException(409, "generation_workflow_state_invalid")
    started = db.scalar(select(WorkflowStepAttempt).where(WorkflowStepAttempt.step_id == step.id,
        WorkflowStepAttempt.status == "started", WorkflowStepAttempt.plugin_key == "media.generate")
        .order_by(WorkflowStepAttempt.id).limit(1))
    if started is not None and started.input_hash != canonical_checksum(step.params_json or {}):
        raise HTTPException(409, "generation_workflow_input_changed")
    return unit, started


def _workflow_output(db: Session, user: User, row: ProviderGenerationTask) -> dict:
    output = {"generation_task_id": row.id, "generation_started_attempt_id": row.workflow_step_attempt_id,
              "generation_state": row.state, "reason": row.reason_code, "generated": False}
    if row.state in {"result_ready", "accepted"}:
        _live(db, row)
        _bytes(row)
    if row.state == "accepted":
        from .materials import read_bytes_checked

        revision = db.get(MaterialRevision, row.accepted_material_revision_id)
        if (revision is None or revision.content_hash != row.result_hash
                or revision.status not in {"usable", "active", "candidate"}
                or revision.material is None or revision.material.status != "active"):
            raise HTTPException(409, "provider_accepted_revision_unavailable")
        if hashlib.sha256(read_bytes_checked(db, revision)).hexdigest() != row.result_hash:
            raise HTTPException(409, "provider_accepted_revision_unavailable")
        output.update(generated=True, material_revision_id=revision.id, content_hash=row.result_hash,
            media_kind=revision.material.kind)
    return output


def workflow_execute(db: Session, run: WorkflowRun, step: WorkflowStep, config: dict, user: User) -> dict:
    from .workflow_engine import _record_attempt, canonical_checksum

    _schema(db)
    request = workflow_request(config)
    unit, started = _workflow_context(db, run, step, user)
    if step.status == "succeeded":
        return step.output_json
    if started is None:
        step.input_hash = canonical_checksum(step.params_json or {})
        started = db.get(WorkflowStepAttempt, _record_attempt(db, step, "started"))
        db.commit()
    request.update(project_id=unit.project_id, idempotency_key=f"workflow.{run.id}.{step.id}")
    prepared = prepare(db, user, request, workflow_attempt=started)
    row = _get(db, user, prepared["task_id"], mutate=True)
    if row.state == "prepared":
        try:
            execute(db, user, row.id, row.revision)
        except Exception:
            db.rollback()
            row = _get(db, user, row.id, mutate=True)
            if row.state == "prepared":
                raise
        row = _get(db, user, row.id, mutate=True)
    return _workflow_output(db, user, row)


def workflow_complete(db: Session, run: WorkflowRun, step: WorkflowStep, payload: dict, user: User) -> dict:
    if set(payload) - {"action"} or payload.get("action", "refresh") not in {"refresh", "recover", "submit_prepared"}:
        raise HTTPException(422, "generation_workflow_action_invalid")
    _schema(db)
    _, started = _workflow_context(db, run, step, user)
    if step.status == "succeeded":
        return step.output_json
    row = db.scalar(select(ProviderGenerationTask).where(
        ProviderGenerationTask.workflow_step_attempt_id == started.id,
        ProviderGenerationTask.owner_user_id == user.id)) if started else None
    action = payload.get("action", "refresh")
    if action == "submit_prepared":
        if row is not None and row.state != "prepared":
            raise HTTPException(409, "generation_already_claimed")
        return workflow_execute(db, run, step, step.params_json or {}, user)
    if row is None:
        raise HTTPException(409, "generation_workflow_task_unprepared")
    _get(db, user, row.id, mutate=True)
    _verify(row)
    if action == "recover":
        recover(db, user, row.id, row.revision)
        row = _get(db, user, row.id, mutate=True)
    return _workflow_output(db, user, row)


def _live(db: Session, row: ProviderGenerationTask, *, first_send: bool = False, check_sources: bool = True):
    _storage()
    _verify(row)
    plan = row.plan_json
    if first_send and routing.configuration_view(db)["revision"] != plan["configuration_revision"]:
        raise HTTPException(409, "execution_plan_stale")
    provider, runtime_hash = provider_media._provider(row.provider_kind, row.provider_key, row.provider_version)
    identity = _identity(provider, row.model_id, row.receipt_key_id)
    if identity is None:
        raise HTTPException(409, "credential_continuity_unverified")
    if (runtime_hash != row.runtime_hash or identity["credential_epoch"] != row.credential_epoch
            or identity["protocol_version"] != row.protocol_version):
        raise HTTPException(409, "provider_runtime_changed")
    refs = tuple((item["revision_id"], item["content_hash"]) for item in row.source_refs_json)
    source_bytes = provider_media._sources(db, [item[0] for item in refs], refs, lock=True)[1] if check_sources else []
    return provider, source_bytes


def _cas(db: Session, row: ProviderGenerationTask, expected: int, **values):
    if expected != row.revision:
        raise HTTPException(409, "generation_revision_conflict")
    changed = db.execute(update(ProviderGenerationTask).where(ProviderGenerationTask.id == row.id,
        ProviderGenerationTask.owner_user_id == row.owner_user_id, ProviderGenerationTask.revision == expected,
        ProviderGenerationTask.state == row.state, ProviderGenerationTask.lease_token == row.lease_token)
        .values(**values, revision=expected + 1, updated_at=utcnow()).execution_options(synchronize_session=False))
    if changed.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "generation_revision_conflict")
    db.flush()
    db.refresh(row)


def _video_limit(content: bytes, seconds: int) -> None:
    # Decode already proves playable bytes; duration must come from the same
    # bytes rather than a provider claim or a previous render's metadata.
    try:
        with tempfile.TemporaryDirectory(prefix="aics-duration-") as temporary:
            source = Path(temporary) / "result.mp4"
            source.write_bytes(content)
            with tempfile.TemporaryFile() as output:
                result = subprocess.run(
                    ["ffprobe", "-v", "error", "-protocol_whitelist", "file",
                     "-select_streams", "v:0", "-show_entries", "stream=duration:format=duration",
                     "-of", "json", str(source)],
                    stdout=output, stderr=subprocess.DEVNULL, timeout=10, check=False,
                )
                output.seek(0)
                raw = output.read(4097)
        if result.returncode or not raw or len(raw) > 4096:
            raise ValueError
        probe = json.loads(raw)
        streams = probe.get("streams")
        if not isinstance(streams, list) or len(streams) != 1:
            raise ValueError
        durations = [streams[0].get("duration"), probe.get("format", {}).get("duration")]
        measured = []
        for duration in durations:
            if not isinstance(duration, str) or not re.fullmatch(r"[0-9]{1,9}(?:\.[0-9]{1,9})?", duration):
                raise ValueError
            value = Decimal(duration)
            if not value.is_finite() or value <= 0:
                raise ValueError
            measured.append(value)
    except (OSError, ValueError, TypeError, AttributeError, InvalidOperation, subprocess.SubprocessError):
        raise HTTPException(422, "generation_video_duration_unverified") from None
    if max(measured) > Decimal(seconds):
        raise HTTPException(422, "generation_output_limit_exceeded")


def _output(db: Session, row: ProviderGenerationTask, user: User, token: str, output) -> dict:
    row = _get(db, user, row.id)
    if row.lease_token != token or row.state not in {"submitting", "running", "unknown"}:
        raise HTTPException(409, "generation_stale_worker")
    # Persist evidence from the original claim even if the project/rights changed
    # while it was running. Eligibility is checked separately on query/accept.
    _verify(row)
    if not isinstance(output, provider_media.providers.MediaOutput):
        output = provider_media.providers.MediaOutput("unknown")
    if not isinstance(output.metadata, dict):
        raise HTTPException(409, "generation_job_invalid")
    # A valid media file does not prove it belongs to this original provider job.
    for field, original in (("job_id", row.provider_job_id), ("file_id", row.provider_file_id)):
        returned = output.metadata.get(field)
        required = original is not None and (output.status == "succeeded"
            or field == "job_id" and output.status in {"failed", "cancelled"})
        if (returned is not None and (not isinstance(returned, str) or not _ID.fullmatch(returned)
                or original is not None and returned != original) or required and returned != original):
            raise HTTPException(409, "generation_job_invalid" if field == "job_id" else "generation_file_invalid")
    values = {"lease_token": None, "lease_expires_at": None}
    if output.status == "succeeded":
        kind, mime = provider_media._decode(output.content, output.mime_type)
        if kind != {"image_provider": "image", "video_provider": "video", "tts_provider": "audio"}[row.provider_kind]:
            raise HTTPException(422, "provider_output_kind_mismatch")
        limits = row.plan_json["parameters"]
        if limits.get("items") != 1:
            raise HTTPException(422, "generation_single_result_required")
        if kind == "image":
            with Image.open(io.BytesIO(output.content)) as image:
                if image.width * image.height > limits["pixels"]:
                    raise HTTPException(422, "generation_output_limit_exceeded")
        elif kind == "audio" and mime == "audio/wav":
            with wave.open(io.BytesIO(output.content)) as audio:
                if audio.getnframes() > limits["seconds"] * audio.getframerate():
                    raise HTTPException(422, "generation_output_limit_exceeded")
        elif kind == "video":
            _video_limit(output.content, limits["seconds"])
        digest = hashlib.sha256(output.content).hexdigest()
        # Random task ID, not a provider-supplied path. Bytes precede DB linkage.
        path = f"generation/{row.id}/{digest}.bin"
        _storage().put(path, output.content)
        if hashlib.sha256(_storage().read(path)).hexdigest() != digest:
            raise HTTPException(409, "generation_result_corrupt")
        values.update(state="result_ready", reason_code=None, result_storage_key=path,
            result_hash=digest, result_size=len(output.content), result_mime=mime)
    elif output.status == "running":
        job = output.metadata.get("job_id")
        if not isinstance(job, str) or not _ID.fullmatch(job) or row.provider_job_id not in {None, job}:
            raise HTTPException(409, "generation_job_invalid")
        file_id = output.metadata.get("file_id")
        if file_id is not None and (not isinstance(file_id, str) or not _ID.fullmatch(file_id)
                or row.provider_file_id not in {None, file_id}):
            raise HTTPException(409, "generation_file_invalid")
        values.update(state="running", provider_job_id=job,
            reason_code=output.metadata.get("reason") if output.metadata.get("reason") in
                ("generation_download_unavailable",) else None)
        if file_id is not None:
            values["provider_file_id"] = file_id
    else:
        confirmed_failure = output.status == "failed" or output.status == "unavailable" and row.provider_job_id is None
        state = "failed" if confirmed_failure else "cancelled" if output.status == "cancelled" else "unknown"
        values.update(state=state, reason_code="provider_execution_failed" if state == "failed" else "provider_outcome_unknown")
        if state == "unknown" and output.metadata.get("reason") == "generation_job_expired":
            values["reason_code"] = "generation_job_expired"
    _cas(db, row, row.revision, **values)
    if row.state in {"result_ready", "running"}:
        row.result_signature = _sign(row, _result_receipt(row))
    db.commit()
    return view(row)


def execute(db: Session, user: User, task_id: str, expected: int) -> dict:
    row = _get(db, user, task_id, mutate=True)
    if row.state != "prepared":
        raise HTTPException(409, "generation_already_claimed")
    provider, source_bytes = _live(db, row, first_send=True)
    token = uuid.uuid4().hex
    params = row.plan_json["parameters"]
    request = {"prompt": row.request_json["prompt"], "model_id": row.model_id, "source_bytes": source_bytes,
        "source_revision_ids": [item["revision_id"] for item in row.source_refs_json],
        "timeout_seconds": min(params["timeout_seconds"], 25), "parameters": params}
    submit = getattr(provider, "submit_task", None)
    if not callable(submit):
        raise HTTPException(422, "durable_provider_dispatch_unavailable")
    _cas(db, row, expected, state="submitting", lease_token=token,
         lease_expires_at=utcnow() + timedelta(seconds=40), reason_code=None)
    # Later revocation gates acceptance, not this committed one-send authority;
    # holding database locks across provider IO would block rights writers.
    db.commit()
    try:
        output = provider_calls.call(submit, request)
    except provider_calls.ProviderCapacityError:
        # No send occurred, but this committed claim is conservatively not reused.
        output = provider_media.providers.MediaOutput("failed")
    except Exception:  # noqa: BLE001 Timeout or exception cannot prove non-delivery.
        output = provider_media.providers.MediaOutput("unknown")
    try:
        return _output(db, row, user, token, output)
    except Exception:
        db.rollback()
        # Persisted submitting claim remains uncertain, never reset to prepared.
        raise


def recover(db: Session, user: User, task_id: str, expected: int) -> dict:
    row = _get(db, user, task_id, mutate=True)
    _verify(row)
    if row.revision != expected:
        raise HTTPException(409, "generation_revision_conflict")
    if row.state not in {"submitting", "running", "unknown"}:
        raise HTTPException(409, "generation_recovery_unavailable")
    expiry = row.lease_expires_at
    if expiry and expiry.replace(tzinfo=UTC) > utcnow():
        raise HTTPException(409, "generation_operation_running")
    if row.provider_job_id is None:
        _cas(db, row, expected, state="unknown", reason_code="generation_original_job_unknown",
             lease_token=None, lease_expires_at=None)
        db.commit()
        return view(row)
    if not row.result_signature or not hmac.compare_digest(_sign(row, _result_receipt(row)), row.result_signature):
        raise HTTPException(409, "generation_job_integrity_invalid")
    if row.query_count >= 120:
        raise HTTPException(409, "generation_query_limit_reached")
    if row.updated_at.replace(tzinfo=UTC) + timedelta(seconds=5) > utcnow():
        raise HTTPException(429, "generation_query_interval_required")
    provider, _ = _live(db, row, check_sources=False)
    query = getattr(provider, "query_task", None)
    if not callable(query):
        raise HTTPException(422, "generation_query_unavailable")
    token = uuid.uuid4().hex
    _cas(db, row, expected, lease_token=token, lease_expires_at=utcnow() + timedelta(seconds=40), query_count=row.query_count + 1)
    db.commit()
    request = {"job_id": row.provider_job_id, "file_id": row.provider_file_id,
        "model_id": row.model_id, "protocol_version": row.protocol_version, "timeout_seconds": 25}
    try:
        output = provider_calls.call(query, request)
    except Exception:  # noqa: BLE001 Recovery polls the original job only once per explicit request.
        output = provider_media.providers.MediaOutput("unknown")
    return _output(db, row, user, token, output)


def _bytes(row: ProviderGenerationTask) -> bytes:
    _verify(row)
    if (row.state not in {"result_ready", "accepted"} or not row.result_signature
            or not hmac.compare_digest(_sign(row, _result_receipt(row)), row.result_signature)):
        raise HTTPException(409, "generation_result_unavailable")
    key = row.result_storage_key
    if not isinstance(key, str) or not key.startswith(f"generation/{row.id}/") or Path(key).is_absolute() or ".." in Path(key).parts:
        raise HTTPException(409, "generation_result_corrupt")
    try:
        content = _storage().read(key)
    except (OSError, ValueError):
        raise HTTPException(409, "generation_result_unavailable") from None
    if len(content) != row.result_size or hashlib.sha256(content).hexdigest() != row.result_hash:
        raise HTTPException(409, "generation_result_corrupt")
    provider_media._decode(content, row.result_mime)
    return content


def raw(db: Session, user: User, task_id: str) -> tuple[bytes, str]:
    row = _get(db, user, task_id)
    return _bytes(row), row.result_mime


def accept(db: Session, user: User, task_id: str, expected: int, decision: dict) -> dict:
    row = _get(db, user, task_id, mutate=True)
    _verify(row)
    decision_hash = _hash(decision)
    if row.state == "accepted":
        if row.acceptance_hash != decision_hash:
            raise HTTPException(409, "provider_acceptance_conflict")
        # Idempotency preserves identity, not permission to reuse invalid bytes.
        _live(db, row)
        _bytes(row)
        revision = db.get(MaterialRevision, row.accepted_material_revision_id)
        if (revision is None or revision.status not in {"usable", "active", "candidate"}
                or revision.content_hash != row.result_hash or revision.material is None
                or revision.material.status != "active"):
            raise HTTPException(409, "provider_accepted_revision_unavailable")
        from .materials import read_bytes_checked

        if hashlib.sha256(read_bytes_checked(db, revision)).hexdigest() != row.result_hash:
            raise HTTPException(409, "provider_accepted_revision_unavailable")
        return {"material_id": revision.material_id, "material_revision_id": revision.id, "content_hash": revision.content_hash}
    _live(db, row)
    content = _bytes(row)
    # Lock before writing library truth; loser cannot create duplicate revisions.
    _cas(db, row, expected, reason_code=None)
    result = provider_media.stage_output(user, kind=row.provider_kind, key=row.provider_key,
        version=row.provider_version, runtime_hash=row.runtime_hash, input_hash=row.input_hash,
        output=provider_media.providers.MediaOutput("succeeded", content, row.result_mime),
        project_id=row.project_id, sources=tuple((item["revision_id"], item["content_hash"]) for item in row.source_refs_json))
    stage_id = result["stage_id"]
    try:
        # Match existing DB→configuration lock order and retain protection until
        # both the immutable revision and task linkage are durably committed.
        with runtime_config.configuration_guard():
            saved = provider_media.accept(db, user, stage_id, decision, commit=False)
            _live(db, row)
            row.state = "accepted"
            row.accepted_material_revision_id = saved["material_revision_id"]
            row.acceptance_hash = decision_hash
            db.commit()
        return saved
    except Exception:
        db.rollback()
        raise
    finally:
        with provider_media._lock:
            provider_media._cache.pop(stage_id, None)
