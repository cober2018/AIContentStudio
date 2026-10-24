"""Durable Stage invocation claims for the Creation Recipe control loop.

This module deliberately owns only the pre-dispatch receipt and its terminal
outcome.  It does not call a provider, create a Master, or create a second
execution-history table.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime

from sqlalchemy import inspect, select, update
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from ..models import ContentProject, ContentUnit, Workflow, WorkflowRun, WorkflowStep, WorkflowStepAttempt
from .content_harness.registry import RegistryError, registry
from .stage_contracts import RESOLVED_STAGE_MAX_BYTES, StageContractError, canonical, digest

_KEY = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,149}\Z")
_RECEIPT_COLUMNS = frozenset({"input_snapshot_json", "execution_receipt_json"})
_TERMINAL = frozenset({"succeeded", "failed", "unknown"})


class StageInvocationError(ValueError):
    """A safe, typed failure before or during a Stage invocation."""

    def __init__(self, code: str, *, status_code: int = 409, detail: dict | None = None):
        self.code = code
        self.status_code = status_code
        self.detail = detail or {}
        super().__init__(code)

    @property
    def body(self) -> dict:
        return {**self.detail, "code": self.code}


def receipt_schema_available(db: Session) -> bool:
    """Return whether the additive receipt columns exist on this database."""

    # A second Engine checkout can roll back a shared SQLite connection's
    # in-flight LLMRun; inspect the Session's transaction instead.
    columns = {item["name"] for item in inspect(db.connection()).get_columns("workflow_step_attempt")}
    return _RECEIPT_COLUMNS <= columns


def require_receipt_schema(db: Session) -> None:
    if not receipt_schema_available(db):
        raise StageInvocationError("stage_receipt_schema_upgrade_required", status_code=503)


def _safe_time() -> str:
    return datetime.now(UTC).isoformat()


def _stage_descriptor(step: WorkflowStep):
    if not step.plugin_key or not step.plugin_version:
        raise StageInvocationError("stage_plugin_required", status_code=422)
    try:
        descriptor = registry.descriptor("node", step.plugin_key, step.plugin_version)
    except RegistryError as exc:
        raise StageInvocationError("stage_plugin_unavailable", status_code=422) from exc
    if descriptor.stage_contract is None:
        raise StageInvocationError("stage_contract_required", status_code=422)
    return descriptor


def _assert_access(db: Session, run: WorkflowRun, user, *, mutate: bool = True) -> None:
    workflow = db.get(Workflow, run.workflow_id)
    if workflow is None:
        raise StageInvocationError("workflow_not_found", status_code=404)
    if run.content_unit_id is not None:
        unit = db.get(ContentUnit, run.content_unit_id)
        project = db.get(ContentProject, unit.project_id) if unit else None
        if unit is None or project is None or project.owner_user_id != user.id:
            raise StageInvocationError("stage_run_not_found", status_code=404)
        if unit.lifecycle_readonly or project.status == "archived":
            raise StageInvocationError("stage_run_archived", status_code=409)
    elif workflow.owner_user_id is not None and workflow.owner_user_id != user.id:
        raise StageInvocationError("stage_run_not_found", status_code=404)
    if user.role not in {"admin", "editor"}:
        raise StageInvocationError("stage_run_readonly", status_code=403)
    if mutate and run.status in {"canceled", "cancelled", "succeeded", "archived"}:
        raise StageInvocationError("stage_run_readonly", status_code=409)


def _validate_resolution(resolved: dict, expected_resolution_hash: str) -> dict:
    if not isinstance(resolved, dict) or not isinstance(resolved.get("resolution_hash"), str):
        raise StageInvocationError("stage_resolution_required", status_code=422)
    if not _KEY.fullmatch(expected_resolution_hash or "") or len(expected_resolution_hash) != 64:
        raise StageInvocationError("stage_preview_required", status_code=422)
    if resolved["resolution_hash"] != expected_resolution_hash:
        raise StageInvocationError("stage_resolution_changed", status_code=409)
    if resolved.get("ready") is not True:
        raise StageInvocationError("stage_blocked", status_code=409)
    try:
        return canonical(resolved, max_bytes=RESOLVED_STAGE_MAX_BYTES)
    except StageContractError as exc:
        raise StageInvocationError("stage_resolution_invalid", status_code=422) from exc


def _attempts(db: Session, step_id: int) -> list[WorkflowStepAttempt]:
    return db.scalars(
        select(WorkflowStepAttempt).where(WorkflowStepAttempt.step_id == step_id).order_by(WorkflowStepAttempt.attempt_no)
    ).all()


def _receipt_for(attempt: WorkflowStepAttempt) -> dict:
    return dict(attempt.execution_receipt_json or {})


def _same_key_result(db: Session, step: WorkflowStep, invocation_key: str, fingerprint: str):
    for attempt in _attempts(db, step.id):
        receipt = _receipt_for(attempt)
        if receipt.get("invocation_key") != invocation_key:
            continue
        if receipt.get("request_fingerprint") != fingerprint:
            raise StageInvocationError("stage_invocation_conflict", status_code=409)
        snapshot = attempt.input_snapshot_json or {}
        resolved = snapshot.get("resolved_stage") or {}
        if (receipt.get("workflow_run_id") != step.run_id or receipt.get("node_id") != step.node_id
                or receipt.get("plugin_key") != step.plugin_key or receipt.get("plugin_version") != step.plugin_version
                or receipt.get("resolution_hash") != attempt.input_hash
                or resolved.get("resolution_hash") != attempt.input_hash
                or digest({key: value for key, value in resolved.items() if key != "resolution_hash"}) != attempt.input_hash
                or attempt.status in _TERMINAL and (
                    digest(attempt.output_json or {}) != attempt.output_hash
                    or receipt.get("output_hash") != attempt.output_hash)):
            raise StageInvocationError("stage_attempt_integrity", status_code=409)
        return attempt
    return None


def _prior_unresolved(db: Session, step: WorkflowStep) -> bool:
    return any(
        (attempt.status == "unknown" or _receipt_for(attempt).get("dispatch_certainty") == "possibly_dispatched")
        and not _receipt_for(attempt).get("abandoned")
        for attempt in _attempts(db, step.id)
    )


def abandon_unknown_attempt(db: Session, *, project_id: int, unit_id: int, node_id: str, run_id: int, attempt_id: int, user) -> dict:
    """The user settles an attempt whose outcome cannot be known, so the stage can run again.

    The attempt stays unknown, since that is still the truth; the receipt records who gave it up and when.
    """
    from .content_masters import owned_unit

    require_receipt_schema(db)
    owned_unit(db, project_id, unit_id, user, mutate=True)
    if not user.is_active or user.role not in {"admin", "editor"}:
        raise StageInvocationError("stage_feedback_readonly", status_code=403)
    run = db.get(WorkflowRun, run_id)
    step = db.scalar(select(WorkflowStep).where(WorkflowStep.run_id == run_id, WorkflowStep.node_id == node_id))
    attempt = db.get(WorkflowStepAttempt, attempt_id)
    if run is None or run.content_unit_id != unit_id or step is None or attempt is None or attempt.step_id != step.id:
        raise StageInvocationError("stage_attempt_not_found", status_code=404)
    _assert_access(db, run, user)
    if attempt.status != "unknown" or attempt.attempt_no != step.attempt_no:
        raise StageInvocationError("stage_attempt_not_current", status_code=409)
    receipt = _receipt_for(attempt)
    if not receipt.get("abandoned"):
        receipt["abandoned"] = {"by_user_id": user.id, "at": _safe_time()}
        attempt.execution_receipt_json = canonical(receipt, max_bytes=128 * 1024)
        step.status, step.error = "failed", "stage_dispatch_abandoned"
        run.status, run.error = "failed", "stage_dispatch_abandoned"
        db.commit()
    db.refresh(run); db.refresh(step); db.refresh(attempt)
    return _execution_result(run, step, attempt)


def _request_fingerprint(expected_resolution_hash: str, override: dict, automatic: bool = False) -> str:
    if not _KEY.fullmatch(expected_resolution_hash or "") or len(expected_resolution_hash) != 64:
        raise StageInvocationError("stage_preview_required", status_code=422)
    return digest({"resolution_hash": expected_resolution_hash, "override": override, "automatic": bool(automatic)})


def _execution_result(run: WorkflowRun, step: WorkflowStep, attempt: WorkflowStepAttempt) -> dict:
    descriptor = _stage_descriptor(step)
    awaiting = descriptor.stage_contract.to_dict()["requires_human_acceptance"]
    status = ("waiting_input" if awaiting else "succeeded") if attempt.status == "succeeded" else attempt.status
    if attempt.attempt_no == step.attempt_no and step.status in {"succeeded", "stale", "blocked", "skipped"}:
        status = step.status
    return {
        "schema": "creation_recipe.stage_execution.v1", "run_id": run.id, "node_id": step.node_id,
        "attempt_id": attempt.id, "status": status,
        "output": attempt.output_json or {}, "receipt": attempt.execution_receipt_json or {},
    }


def _claim_invocation(
    db: Session,
    *,
    run: WorkflowRun,
    step: WorkflowStep,
    user,
    resolved: dict,
    expected_resolution_hash: str,
    invocation_key: str,
    stage_override: dict | None = None,
    automatic: bool = False,
) -> tuple[WorkflowStepAttempt, bool]:
    """Claim an existing Step/Attempt and commit its receipt before dispatch.

    This function intentionally stops at the durable claim.  The caller must
    invoke a provider only after it receives the returned attempt.
    """

    require_receipt_schema(db)
    _assert_access(db, run, user)
    descriptor = _stage_descriptor(step)
    if step.run_id != run.id or resolved.get("workflow", {}).get("id") != run.workflow_id:
        raise StageInvocationError("stage_resolution_invalid", status_code=422)
    node = resolved.get("node") or {}
    if (node.get("id"), node.get("plugin"), node.get("plugin_version")) != (
            step.node_id, step.plugin_key, step.plugin_version):
        raise StageInvocationError("stage_resolution_invalid", status_code=422)
    if not _KEY.fullmatch(invocation_key or ""):
        raise StageInvocationError("stage_invocation_key_invalid", status_code=422)
    resolved = _validate_resolution(resolved, expected_resolution_hash)
    try:
        override = canonical(stage_override or {}, max_bytes=32 * 1024)
        _, effective, _ = descriptor.stage_contract.effective_config(resolved.get("base_config", {}), override)
        if (effective != resolved.get("effective_config") or override != resolved.get("override")
                or digest(effective) != resolved.get("config_hash")
                or digest({key: value for key, value in resolved.items() if key != "resolution_hash"})
                != expected_resolution_hash):
            raise StageInvocationError("stage_resolution_invalid", status_code=422)
    except StageInvocationError:
        raise
    except StageContractError as exc:
        raise StageInvocationError(str(exc), status_code=422) from exc
    try:
        snapshot = canonical({"resolved_stage": resolved}, max_bytes=RESOLVED_STAGE_MAX_BYTES)
    except StageContractError as exc:
        raise StageInvocationError("stage_receipt_bounds", status_code=422) from exc
    fingerprint = _request_fingerprint(expected_resolution_hash, override, automatic)
    # A database write lock serializes claims on SQLite and PostgreSQL; an
    # in-process mutex cannot protect another API/Worker process.
    try:
        locked = db.execute(update(WorkflowStep).where(
            WorkflowStep.id == step.id, WorkflowStep.run_id == run.id,
        ).values(attempt_no=WorkflowStep.attempt_no).execution_options(synchronize_session=False))
        if locked.rowcount != 1:
            raise StageInvocationError("stage_not_found", status_code=404)
        db.refresh(step)
        db.refresh(run)
        _assert_access(db, run, user)
        existing = _same_key_result(db, step, invocation_key, fingerprint)
        if existing is not None:
            db.commit()
            return existing, False
        if _prior_unresolved(db, step):
            raise StageInvocationError("stage_unknown_reconciliation_required", status_code=409)
        if any(attempt.status == "running" for attempt in _attempts(db, step.id)):
            raise StageInvocationError("stage_invocation_in_progress", status_code=409)
    except StageInvocationError:
        db.rollback()
        raise
    except OperationalError as exc:
        db.rollback()
        raise StageInvocationError("stage_invocation_busy", status_code=409) from exc

    attempt_no = max((attempt.attempt_no for attempt in _attempts(db, step.id)), default=0) + 1
    method = resolved.get("method") or {}
    capability_use_id = None
    capability_use_ids = []
    consumed_methods = method.get("stack") or [method]
    for consumed in consumed_methods:
        if consumed.get("source_kind") != "capability_memory":
            continue
        from ..models import CapabilityArtifactRevision, CapabilityUse

        revision = db.get(CapabilityArtifactRevision, consumed.get("revision_id"))
        if revision is None or revision.artifact_id != consumed.get("artifact_id") or revision.content_hash != consumed.get("content_hash"):
            db.rollback()
            raise StageInvocationError("stage_method_revision_changed")
        unit = db.get(ContentUnit, run.content_unit_id)
        usage = CapabilityUse(artifact_revision_id=revision.id, owner_user_id=user.id,
            project_id=unit.project_id, rendered_arguments_hash=consumed["arguments_hash"], outcome="used", created_by=user.email)
        db.add(usage)
        db.flush()
        capability_use_ids.append(usage.id)
    if method.get("source_kind") == "capability_memory" and capability_use_ids:
        capability_use_id = capability_use_ids[0]
    receipt = canonical({
        "schema": "creation_recipe.execution_receipt.v1",
        "request_mode": "automatic" if automatic else "explicit",
        "prepared_by_server": True,
        "invocation_key": invocation_key,
        "request_fingerprint": fingerprint,
        "workflow_run_id": run.id,
        "workflow_id": run.workflow_id,
        "node_id": step.node_id,
        "plugin_key": step.plugin_key,
        "plugin_version": step.plugin_version,
        "stage_contract_hash": digest(_stage_descriptor(step).stage_contract.to_dict()),
        "resolution_hash": expected_resolution_hash,
        "config_hash": resolved["config_hash"],
        "override_hash": digest(override),
        "method_hash": digest(resolved.get("method")),
        "prompt_hash": resolved["prompt_hash"],
        "upstream_hash": digest(resolved.get("upstream")),
        "model_route_hash": digest({
            key: (resolved.get("model") or {}).get(key)
            for key in ("profile_id", "provider", "model")
        }),
        "adapter_hash": digest({
            key: (resolved.get("model") or {}).get(key)
            for key in ("adapter_key", "adapter_version")
        }),
        "runtime_identity_hash": digest({
            key: (resolved.get("model") or {}).get(key)
            for key in ("runtime_hash", "configuration_revision")
        }),
        "output_contract": resolved.get("output_contract", {}),
        "dispatch_certainty": "not_dispatched",
        "created_at": _safe_time(),
        "capability_use_id": capability_use_id,
        "capability_use_ids": capability_use_ids,
    }, max_bytes=128 * 1024)
    attempt = WorkflowStepAttempt(
        step_id=step.id,
        run_id=run.id,
        node_id=step.node_id,
        plugin_key=step.plugin_key,
        plugin_version=step.plugin_version,
        attempt_no=attempt_no,
        status="running",
        output_json={},
        input_hash=expected_resolution_hash,
        input_snapshot_json=snapshot,
        execution_receipt_json=receipt,
        created_at=datetime.now(UTC),
    )
    db.add(attempt)
    step.attempt_no = attempt_no
    step.status = "running"
    step.input_hash = expected_resolution_hash
    step.output_json = {}
    step.output_hash = None
    step.error = None
    step.started_at = datetime.now(UTC)
    step.finished_at = None
    run.status = "running"
    db.flush()
    db.commit()
    db.refresh(attempt)
    return attempt, True


def prepare_invocation(db: Session, **kwargs) -> WorkflowStepAttempt:
    return _claim_invocation(db, **kwargs)[0]


def finalize_invocation(
    db: Session,
    *,
    attempt_id: int,
    output: dict | None = None,
    status: str,
    dispatch_certainty: str,
    error: str | None = None,
    provider_failure: dict | None = None,
) -> WorkflowStepAttempt:
    """Finalize one claimed attempt exactly once, preserving its frozen input."""

    require_receipt_schema(db)
    if status not in _TERMINAL:
        raise StageInvocationError("stage_outcome_invalid", status_code=422)
    if dispatch_certainty not in {"not_dispatched", "possibly_dispatched", "confirmed_dispatched"}:
        raise StageInvocationError("stage_dispatch_certainty_invalid", status_code=422)
    attempt = db.get(WorkflowStepAttempt, attempt_id)
    if attempt is None:
        raise StageInvocationError("stage_attempt_not_found", status_code=404)
    if attempt.status in _TERMINAL:
        return attempt
    if attempt.status != "running":
        raise StageInvocationError("stage_attempt_not_claimed", status_code=409)
    safe_output = canonical(output or {}, max_bytes=128 * 1024)
    safe_codes = {"stage_proposal_output_invalid", "stage_creative_output_invalid", "stage_provider_failed", "stage_provider_rejected", "stage_executor_unavailable",
                  "stage_resolution_changed", "stage_model_runtime_changed", "stage_checks_blocked",
                  "stage_media_generation_failed", "stage_media_dispatch_unavailable",
                  "stage_media_original_task_unresolved", "stage_variant_context_changed"}
    safe_error = error if error in safe_codes else "stage_execution_failed" if error else None
    if dispatch_certainty == "not_dispatched":
        safe_error = "failed_before_dispatch"
        status = "failed"
    elif dispatch_certainty == "possibly_dispatched":
        status = "unknown"
        safe_error = "stage_dispatch_unknown"
    receipt = _receipt_for(attempt)
    receipt["dispatch_certainty"] = dispatch_certainty
    receipt["outcome_state"] = "failed_before_dispatch" if dispatch_certainty == "not_dispatched" else status
    receipt["output_hash"] = digest(safe_output)
    receipt["finalized_at"] = _safe_time()
    if provider_failure:
        receipt["provider_failure"] = {key: provider_failure.get(key) for key in ("reason", "status", "answered")}
    sealed = db.execute(update(WorkflowStepAttempt).where(
        WorkflowStepAttempt.id == attempt.id, WorkflowStepAttempt.status == "running",
    ).values(output_json=safe_output, output_hash=digest(safe_output), status=status, error=safe_error,
             execution_receipt_json=canonical(receipt, max_bytes=128 * 1024))
        .execution_options(synchronize_session=False))
    if sealed.rowcount == 1:
        step = db.get(WorkflowStep, attempt.step_id)
        awaiting = _stage_descriptor(step).stage_contract.to_dict()["requires_human_acceptance"]
        step_status = ("waiting_input" if awaiting else "succeeded") if status == "succeeded" else status
        projected = db.execute(update(WorkflowStep).where(
            WorkflowStep.id == attempt.step_id, WorkflowStep.attempt_no == attempt.attempt_no,
        ).values(output_json=safe_output, output_hash=digest(safe_output), status=step_status,
                 error=safe_error, finished_at=datetime.now(UTC))
            .execution_options(synchronize_session="fetch"))
        if projected.rowcount == 1:
            run_status = step_status
            if step_status == "succeeded":
                statuses = db.scalars(select(WorkflowStep.status).where(WorkflowStep.run_id == attempt.run_id)).all()
                run_status = "succeeded" if all(value in {"succeeded", "skipped"} for value in statuses) else "running"
            db.execute(update(WorkflowRun).where(WorkflowRun.id == attempt.run_id)
                       .values(status=run_status, error=safe_error).execution_options(synchronize_session="fetch"))
    db.commit()
    db.refresh(attempt)
    return attempt


def reconcile_running_attempt(db: Session, *, project_id: int, unit_id: int, node_id: str,
                              run_id: int, attempt_id: int, user) -> dict:
    """Explicitly convert an abandoned pre-dispatch claim to unknown.

    A process may exit after the durable claim and before the provider call
    returns. The system cannot infer whether the provider received the request,
    so reconciliation seals the attempt as unknown and prevents automatic
    resubmission.
    """

    require_receipt_schema(db)
    from .content_masters import owned_unit

    owned_unit(db, project_id, unit_id, user)
    run = db.get(WorkflowRun, run_id)
    step = db.scalar(select(WorkflowStep).where(WorkflowStep.run_id == run_id, WorkflowStep.node_id == node_id))
    attempt = db.get(WorkflowStepAttempt, attempt_id)
    if run is None or run.content_unit_id != unit_id or step is None or attempt is None:
        raise StageInvocationError("stage_run_not_found", status_code=404)
    _assert_access(db, run, user)
    if attempt.step_id != step.id or attempt.run_id != run.id or attempt.node_id != node_id:
        raise StageInvocationError("stage_attempt_not_found", status_code=404)
    if attempt.status != "running":
        return _execution_result(run, step, attempt)
    sealed = finalize_invocation(
        db, attempt_id=attempt.id, status="unknown", dispatch_certainty="possibly_dispatched",
        error="stage_dispatch_unknown",
    )
    db.refresh(run); db.refresh(step)
    return _execution_result(run, step, sealed)


def execute_stage(
    db: Session,
    project_id: int,
    unit_id: int,
    node_id: str,
    user,
    *,
    run_id: int,
    expected_resolution_hash: str,
    invocation_key: str,
    stage_override: dict | None = None,
    automatic: bool = False,
) -> dict:
    """Execute one prepared Stage and stop before human adoption.

    The claim is committed before the provider call. A successful proposal is
    only a waiting-input Step output; no Master, Material, Variant, approval or
    publication state is changed here.
    """

    from .content_harness.contracts import WorkflowExecutionContext
    from .content_masters import owned_unit
    from .creation_recipes import preview_stage

    require_receipt_schema(db)
    owned_unit(db, project_id, unit_id, user)
    run = db.get(WorkflowRun, run_id)
    if run is None or run.content_unit_id != unit_id:
        raise StageInvocationError("stage_run_not_found", status_code=404)
    step = db.scalar(select(WorkflowStep).where(WorkflowStep.run_id == run.id, WorkflowStep.node_id == node_id))
    if step is None:
        raise StageInvocationError("stage_not_found", status_code=404)
    _assert_access(db, run, user, mutate=False)
    if not _KEY.fullmatch(invocation_key or ""):
        raise StageInvocationError("stage_invocation_key_invalid", status_code=422)
    override = canonical(stage_override or {}, max_bytes=32 * 1024)
    existing = _same_key_result(db, step, invocation_key, _request_fingerprint(
        expected_resolution_hash, override, automatic))
    if existing is not None:
        return _execution_result(run, step, existing)
    if automatic and step.plugin_key == "stage.audio.asr":
        raise StageInvocationError("stage_manual_execution_required", status_code=409)
    _assert_access(db, run, user)
    owned_unit(db, project_id, unit_id, user, mutate=True)
    resolved = preview_stage(
        db, project_id, unit_id, node_id, user,
        run_id=run.id, stage_override=stage_override or {},
    )
    blockers = resolved.get("blockers") or []
    if not resolved.get("ready") or blockers:
        raise StageInvocationError("stage_blocked", status_code=409)
    plugin = registry.resolve("node", step.plugin_key, step.plugin_version)
    execute_resolved = getattr(plugin, "execute_resolved", None)
    if not callable(execute_resolved):
        raise StageInvocationError("stage_executor_unavailable", status_code=422)
    attempt, claimed = _claim_invocation(
        db, run=run, step=step, user=user, resolved=resolved,
        expected_resolution_hash=expected_resolution_hash,
        invocation_key=invocation_key,
        stage_override=stage_override or {},
        automatic=automatic,
    )
    if not claimed:
        return _execution_result(run, step, attempt)
    ctx = WorkflowExecutionContext(db=db, run=run, step=step, config=resolved.get("effective_config") or {})
    try:
        db.expire_all()
        current = preview_stage(db, project_id, unit_id, node_id, user,
                                run_id=run.id, stage_override=stage_override or {})
        if current.get("resolution_hash") != expected_resolution_hash or not current.get("ready"):
            raise StageInvocationError("stage_resolution_changed", status_code=409)
        result = execute_resolved(db, ctx, resolved, user)
        output = canonical(getattr(result, "output", None) or {}, max_bytes=128 * 1024)
        from .stage_domain_integrations import stage_result_policy

        policy = stage_result_policy(output)
        finalized = finalize_invocation(
            db, attempt_id=attempt.id, output=output, **policy,
        )
    except Exception as exc:  # provider failures remain explicit and never auto-retry
        from .stage_domain_integrations import StageDomainError

        code = str(exc) if str(exc) in {"stage_proposal_output_invalid", "stage_creative_output_invalid", "stage_provider_failed", "stage_provider_rejected",
                                       "stage_model_runtime_changed", "stage_resolution_changed"} else "stage_execution_failed"
        certainty = ("not_dispatched" if code in {"stage_model_runtime_changed", "stage_resolution_changed"} else
                     "confirmed_dispatched" if code in {"stage_proposal_output_invalid", "stage_creative_output_invalid", "stage_provider_rejected"} else "possibly_dispatched")
        if isinstance(exc, StageDomainError):
            code, certainty = exc.code, exc.dispatch_certainty
        elif step.plugin_key == "stage.graphic.compose":
            code, certainty = "graphic_composition_failed", "confirmed_dispatched"
        finalized = finalize_invocation(
            db, attempt_id=attempt.id, status="failed", dispatch_certainty=certainty,
            error=code, output=exc.output if isinstance(exc, StageDomainError) else None,
            provider_failure=getattr(exc, "failure", None),
        )
        if certainty == "not_dispatched":
            raise StageInvocationError(code, status_code=409) from exc
        if certainty == "possibly_dispatched":
            raise StageInvocationError("stage_dispatch_unknown", status_code=409) from exc
        raise StageInvocationError(code, status_code=422) from exc

    db.refresh(step)
    return _execution_result(run, step, finalized)
