"""Explicit local ASR over accepted Audio; reads only validate frozen receipts."""

import hashlib
import re
import time

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from ..models import (
    ContentUnit,
    Material,
    MaterialRevision,
    ProjectWorkflowOutput,
    ProviderGenerationTask,
    User,
    Workflow,
    WorkflowRun,
    WorkflowStepAttempt,
)
from . import asr_suggestions, creation_recipes, materials, provider_calls, stage_audio
from .content_harness.registry import registry
from .local_mlx_asr_provider import LocalASRUnavailable, LocalMLXASRProvider
from .stage_contracts import StageContractError, canonical, digest
from .stage_invocations import StageInvocationError

_SCHEMA = "studio.audio.stage.asr.v1"
_ALIGNMENT_SCHEMA = "studio.audio.asr-alignment.v1"
_KEY, _VERSION = "local.mlx_whisper", "1"
_MAX_BYTES, _MAX_DURATION = 30 * 1024 * 1024, 600_000
_RESULT_BYTES = 48 * 1024
_HEX = re.compile(r"[0-9a-f]{64}\Z")
_TASK_ID = re.compile(r"[0-9a-f]{32}\Z")
_LOCAL_PATH = re.compile(r"file://|/(?:Users|home|private|tmp|var|etc|opt)/|(?<!\w)[A-Za-z]:[\\/]")
_SNAPSHOT_FIELDS = frozenset({
    "schema", "kind", "actor_id", "project_id", "unit_id", "run_id", "node", "workflow",
    "config", "config_hash", "accepted_target", "material_revision_id", "content_hash", "task_id",
    "task_request_hash", "task_plan_hash", "task_input_hash", "task_result_signature_hash",
    "task_acceptance_hash", "script", "script_hash", "tts_source_hash", "provider", "mime_type",
    "source_size_bytes", "duration_ms", "input_hash",
})
_RESULT_FIELDS = frozenset({
    "audio_asr", "asr_snapshot", "transcript", "cues", "duration_ms", "provider", "input_hash", "output_hash",
})
_INVALID = (HTTPException, StageInvocationError, StageContractError, ValueError, TypeError,
            KeyError, AttributeError, OSError, EOFError, SQLAlchemyError)


def _invalid(code, *, certainty="not_dispatched", status_code=409):
    from .stage_domain_integrations import StageDomainError

    raise StageDomainError(code, dispatch_certainty=certainty, status_code=status_code)


def _safe(value, *, max_bytes=_RESULT_BYTES):
    result = canonical(value, max_bytes=max_bytes)

    def visit(item):
        if isinstance(item, str) and _LOCAL_PATH.search(item):
            _invalid("stage_audio_asr_path_forbidden")
        if isinstance(item, dict):
            for child in item.values():
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)

    visit(result)
    return result


def _config(config):
    if (not isinstance(config, dict) or set(config) != {"provider_key", "provider_version", "timeout_seconds"}
            or config.get("provider_key") != _KEY or config.get("provider_version") != _VERSION
            or type(config.get("timeout_seconds")) is not int or not 1 <= config["timeout_seconds"] <= 120):
        _invalid("stage_audio_asr_config_invalid")
    return _safe(config)


def _provider():
    try:
        provider = registry.resolve("asr_provider", _KEY, _VERSION)
        if type(provider) is not LocalMLXASRProvider or provider.key != _KEY or provider.version != _VERSION:
            raise ValueError
        option = provider.option()
        if not isinstance(option, dict) or option.get("available") is not True:
            raise ValueError
        runtime = provider.runtime_fingerprint()
        if not isinstance(runtime, str) or not _HEX.fullmatch(runtime):
            raise ValueError
        return provider, {"key": _KEY, "version": _VERSION, "runtime_fingerprint": runtime}
    except Exception:  # noqa: BLE001 Runtime diagnostics may contain local paths or credentials.
        _invalid("stage_audio_asr_runtime_unavailable")


def _source(db, revision):
    if (revision.mime_type != "audio/wav" or revision.model_use_allowed is not True
            or revision.status not in {"candidate", "usable", "active"}
            or revision.material is None or revision.material.status != "active"):
        _invalid("stage_audio_asr_wav_model_rights_required")
    content = materials.read_bytes_checked(db, revision)
    if (not isinstance(content, bytes) or not 0 < len(content) <= _MAX_BYTES
            or hashlib.sha256(content).hexdigest() != revision.content_hash):
        _invalid("stage_audio_asr_bytes_invalid")
    duration = asr_suggestions._duration(content, "audio/wav")
    if type(duration) is not int or not 0 < duration <= _MAX_DURATION:
        _invalid("stage_audio_asr_duration_invalid")
    return content, duration


def _build(db, user, unit, node, config, context):
    from .stage_domain_adoptions import accepted_domain_input

    if (not isinstance(node, dict) or node.get("plugin") != "stage.audio.asr"
            or str(node.get("plugin_version")) != "1" or user.is_active is not True):
        _invalid("stage_audio_asr_node_invalid")
    config = _config(config)
    run, workflow, targets = stage_audio._dependencies(db, user, unit, node, context)
    target, revision, task, script, tts_source = stage_audio._accepted_audio(db, targets, run, user, unit)
    accepted_domain_input(db, target, require_model_use=True)
    content, duration = _source(db, revision)
    provider, runtime = _provider()
    snapshot = {"schema": _SCHEMA, "kind": "audio_asr", "actor_id": user.id,
        "project_id": unit.project_id, "unit_id": unit.id, "run_id": run.id,
        "node": {"id": node["id"], "plugin": "stage.audio.asr", "plugin_version": "1"},
        "workflow": workflow, "config": config, "config_hash": digest(config), "accepted_target": target,
        "material_revision_id": revision.id, "content_hash": revision.content_hash, "task_id": task.id,
        "task_request_hash": task.request_hash, "task_plan_hash": task.plan_hash,
        "task_input_hash": task.input_hash, "task_result_signature_hash": digest(task.result_signature),
        "task_acceptance_hash": task.acceptance_hash, "script": script, "script_hash": digest(script),
        "tts_source_hash": digest(tts_source), "provider": runtime, "mime_type": "audio/wav",
        "source_size_bytes": len(content), "duration_ms": duration}
    snapshot["input_hash"] = digest(snapshot)
    return _safe(snapshot), provider, content


def prepare_asr(db, user, unit, node, config, context):
    """Freeze source/runtime truth without dispatching inference or writing rows."""
    try:
        with db.no_autoflush:
            snapshot, _, _ = _build(db, user, unit, node, config, context)
            return canonical({**context, "domain": snapshot}), snapshot["config"], []
    except _INVALID as exc:
        code = exc.code if isinstance(exc, StageInvocationError) and exc.code.startswith("stage_audio_asr_") else "stage_audio_asr_input_unavailable"
        return context if isinstance(context, dict) else {}, config if isinstance(config, dict) else {}, [code]


def _snapshot(value):
    snapshot = _safe(value)
    if (not isinstance(snapshot, dict) or set(snapshot) != _SNAPSHOT_FIELDS
            or snapshot.get("schema") != _SCHEMA or snapshot.get("kind") != "audio_asr"
            or snapshot.get("input_hash") != digest({key: item for key, item in snapshot.items() if key != "input_hash"})
            or snapshot.get("config_hash") != digest(_config(snapshot.get("config")))
            or snapshot.get("script_hash") != digest(snapshot.get("script"))):
        _invalid("stage_audio_asr_snapshot_invalid")
    if any(type(snapshot.get(key)) is not int or snapshot[key] <= 0 for key in (
            "actor_id", "project_id", "unit_id", "run_id", "material_revision_id")):
        _invalid("stage_audio_asr_scope_invalid")
    if not isinstance(snapshot.get("task_id"), str) or not _TASK_ID.fullmatch(snapshot["task_id"]):
        _invalid("stage_audio_asr_task_invalid")
    return snapshot


def _current(db, value):
    snapshot = _snapshot(value)
    user = db.get(User, snapshot["actor_id"], populate_existing=True)
    unit = db.get(ContentUnit, snapshot["unit_id"], populate_existing=True)
    run = db.get(WorkflowRun, snapshot["run_id"], populate_existing=True)
    if (user is None or unit is None or run is None or user.is_active is not True
            or unit.project_id != snapshot["project_id"]):
        _invalid("stage_audio_asr_scope_changed")
    # Refresh only frozen dependencies so a Session identity map cannot hide a revocation.
    db.get(Workflow, run.workflow_id, populate_existing=True)
    revision = db.get(MaterialRevision, snapshot["material_revision_id"], populate_existing=True)
    if revision is not None:
        db.get(Material, revision.material_id, populate_existing=True)
    db.get(ProjectWorkflowOutput, snapshot["accepted_target"]["project_output_id"], populate_existing=True)
    task = db.get(ProviderGenerationTask, snapshot["task_id"], populate_existing=True)
    if task is not None:
        attempt = db.get(WorkflowStepAttempt, task.workflow_step_attempt_id, populate_existing=True)
        source = ((attempt.input_snapshot_json or {}).get("resolved_stage", {}).get("context", {}).get("audio_stage") or {}) if attempt else {}
        for name in ("spoken", "voice_direction"):
            source_attempt = (source.get(name) or {}).get("attempt_id")
            if type(source_attempt) is int:
                db.get(WorkflowStepAttempt, source_attempt, populate_existing=True)
    current, provider, content = _build(db, user, unit, snapshot["node"], snapshot["config"],
        {key: snapshot[key] for key in ("project_id", "unit_id", "run_id")})
    if current != snapshot:
        _invalid("stage_audio_asr_inputs_changed")
    return snapshot, provider, content


def _output(snapshot, raw):
    duration = raw.get("source_duration_ms") if isinstance(raw, dict) else None
    if type(duration) is not int or not 0 < duration <= _MAX_DURATION or abs(duration - snapshot["duration_ms"]) > 1:
        _invalid("stage_audio_asr_output_duration_invalid")
    normalized = asr_suggestions._output(raw, min(duration, snapshot["duration_ms"]))
    if (len(normalized["cues"]) > 256
            or normalized["transcript"] != "\n".join(cue["text"] for cue in normalized["cues"])):
        _invalid("stage_audio_asr_output_invalid")
    result = {"audio_asr": True, "asr_snapshot": snapshot, **normalized, "duration_ms": duration,
              "provider": snapshot["provider"], "input_hash": snapshot["input_hash"]}
    result["output_hash"] = digest(result)
    return _safe(result)


def execute_asr(db, snapshot):
    """Dispatch once; the caller owns the durable invocation claim and Unknown gate."""
    started = time.monotonic()
    try:
        with db.no_autoflush:
            snapshot, provider, content = _current(db, snapshot)
    except _INVALID:
        _invalid("stage_audio_asr_preflight_changed")
    timeout = snapshot["config"]["timeout_seconds"] - (time.monotonic() - started)
    if timeout <= 0:
        _invalid("stage_audio_asr_deadline_exhausted")
    request = {"source_bytes": content, "source_hash": snapshot["content_hash"], "mime_type": "audio/wav",
               "max_duration_ms": snapshot["duration_ms"], "timeout_seconds": timeout}
    try:
        raw = provider_calls.call(provider.transcribe, request, timeout_seconds=timeout)
    except provider_calls.ProviderCapacityError:
        _invalid("stage_audio_asr_capacity", status_code=429)
    except TimeoutError:
        _invalid("stage_audio_asr_unknown", certainty="possibly_dispatched")
    except LocalASRUnavailable as exc:
        preflight = str(exc) in {"local_asr_not_enabled", "local_asr_offline_runtime_unavailable",
            "local_asr_configuration_missing", "local_asr_runtime_missing", "local_asr_cached_model_missing",
            "local_asr_audio_tools_missing", "local_asr_source_invalid", "local_asr_deadline_invalid"}
        _invalid("stage_audio_asr_unavailable", certainty="not_dispatched" if preflight else "confirmed_dispatched")
    except Exception:  # noqa: BLE001 Uncertain adapter failures must not expose diagnostics or authorize retry.
        _invalid("stage_audio_asr_unknown", certainty="possibly_dispatched")
    if isinstance(raw, dict) and raw.get("status") == "unknown":
        _invalid("stage_audio_asr_unknown", certainty="possibly_dispatched")
    try:
        result = _output(snapshot, raw)
        with db.no_autoflush:
            _current(db, snapshot)
        return result
    except _INVALID:
        _invalid("stage_audio_asr_result_invalid_or_stale", certainty="confirmed_dispatched")


def validate_asr_result(db, result):
    """Validate shape/currentness only; accepted_domain_input supplies the durable seal."""
    try:
        result = _safe(result)
        if (not isinstance(result, dict) or set(result) != _RESULT_FIELDS or result.get("audio_asr") is not True
                or result.get("output_hash") != digest({key: item for key, item in result.items() if key != "output_hash"})):
            _invalid("stage_audio_asr_result_invalid")
        with db.no_autoflush:
            snapshot, _, _ = _current(db, result["asr_snapshot"])
        expected = _output(snapshot, {"status": "succeeded", "source_duration_ms": result["duration_ms"],
                                     "transcript": result["transcript"], "cues": result["cues"]})
        if result != expected:
            _invalid("stage_audio_asr_result_invalid")
        return expected
    except _INVALID:
        _invalid("stage_audio_asr_result_invalid_or_stale")


def _match(result, revision, task, script):
    snapshot = result["asr_snapshot"]
    if (snapshot["material_revision_id"] != revision.id or snapshot["content_hash"] != revision.content_hash
            or snapshot["task_id"] != task.id or snapshot["project_id"] != task.project_id
            or snapshot["script"] != script or snapshot["script_hash"] != digest(script)
            or task.accepted_material_revision_id != revision.id or task.request_json.get("prompt") != script
            or any(snapshot[key] != getattr(task, field) for key, field in (
                ("task_request_hash", "request_hash"), ("task_plan_hash", "plan_hash"),
                ("task_input_hash", "input_hash"), ("task_acceptance_hash", "acceptance_hash")))
            or snapshot["task_result_signature_hash"] != digest(task.result_signature)):
        _invalid("stage_audio_asr_alignment_source_changed")


def _alignment(db, target, revision, task, script):
    from .stage_domain_adoptions import accepted_domain_input

    if (not isinstance(target, dict) or target.get("output_kind") != "workflow_step_attempt"
            or target.get("domain") != "audio_asr" or target.get("decision") != "accepted"
            or target.get("attempt_id") != target.get("entity_id")):
        _invalid("stage_audio_asr_accepted_attempt_required")
    attempt = db.get(WorkflowStepAttempt, target["attempt_id"], populate_existing=True)
    receipt = attempt.execution_receipt_json or {} if attempt else {}
    if (attempt is None or attempt.status != "succeeded" or attempt.plugin_key != "stage.audio.asr"
            or str(attempt.plugin_version) != "1" or receipt.get("request_mode") != "explicit"):
        _invalid("stage_audio_asr_accepted_attempt_required")
    run = db.get(WorkflowRun, attempt.run_id, populate_existing=True)
    if run is None or creation_recipes.accepted_stage_target(db, run, target["node_id"]) != target:
        _invalid("stage_audio_asr_accepted_attempt_changed")
    selected = accepted_domain_input(db, target, require_model_use=True)
    result = validate_asr_result(db, selected["payload"])
    snapshot = result["asr_snapshot"]
    if (attempt.run_id != snapshot["run_id"] or attempt.node_id != target["node_id"]
            or snapshot["node"]["id"] != target["node_id"] or target.get("accepted_hash") != digest(result)):
        _invalid("stage_audio_asr_accepted_attempt_changed")
    _match(result, revision, task, script)
    proof = {"schema": _ALIGNMENT_SCHEMA, "accepted_target": target, "asr_output_hash": result["output_hash"],
        "asr_result_hash": digest(result), "asr_input_hash": result["input_hash"],
        **{key: snapshot[key] for key in ("actor_id", "project_id", "unit_id", "run_id",
            "material_revision_id", "content_hash", "task_id", "script_hash")},
        "provider": result["provider"], "duration_ms": result["duration_ms"],
        "timing_basis": "verified_asr_segment_timing", "word_alignment": "not_run"}
    return _safe(proof), result["cues"]


def accepted_alignment(db, targets, run, user, unit, revision, task, script):
    """Select one direct accepted ASR handoff, never a client-supplied transcript."""
    try:
        with db.no_autoflush:
            matches = [target for target in targets if target and target.get("output_kind") == "workflow_step_attempt"
                       and target.get("domain") == "audio_asr" and target.get("decision") == "accepted"]
            if len(matches) != 1:
                _invalid("stage_audio_asr_one_accepted_attempt_required")
            proof, _ = _alignment(db, matches[0], revision, task, script)
            if (proof["run_id"] != run.id or proof["actor_id"] != user.id
                    or proof["unit_id"] != unit.id or proof["project_id"] != unit.project_id):
                _invalid("stage_audio_asr_alignment_scope_changed")
            return proof
    except _INVALID:
        _invalid("stage_audio_asr_alignment_unavailable")


def validate_alignment(db, proof, revision, task, script):
    """Re-read sealed accepted timing and reject any modified, foreign or stale proof."""
    try:
        with db.no_autoflush:
            proof = _safe(proof)
            if not isinstance(proof, dict) or proof.get("schema") != _ALIGNMENT_SCHEMA:
                _invalid("stage_audio_asr_alignment_invalid")
            current, cues = _alignment(db, proof["accepted_target"], revision, task, script)
            if current != proof:
                _invalid("stage_audio_asr_alignment_changed")
            return current, cues
    except _INVALID:
        _invalid("stage_audio_asr_alignment_unavailable")
