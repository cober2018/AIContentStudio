"""Acceptance-gated continuation for the Creation Recipe runtime."""

from fastapi import HTTPException
from sqlalchemy import select

from ..models import ContentUnit, Workflow, WorkflowRun, WorkflowStep, WorkflowStepAttempt
from . import creation_recipes
from .content_harness.registry import RegistryError, registry
from .stage_contracts import StageContractError, digest
from .stage_invocations import StageInvocationError, execute_stage


def _descendants(definition, source_node_id):
    edges = {}
    for edge in definition.get("edges", []):
        edges.setdefault(edge["from"], set()).add(edge["to"])
    found, pending = set(), [source_node_id]
    while pending:
        node_id = pending.pop(0)
        for child in sorted(edges.get(node_id, set())):
            if child not in found:
                found.add(child)
                pending.append(child)
    return found


def _blocked(db, run, step, node_id, code, *, blockers=None):
    reasons = blockers or [code]
    if step is not None and step.status in {"running", "unknown", "failed", "stale", "waiting_input"}:
        return {"status": step.status, "node_id": node_id, "code": step.error or code, "blockers": reasons}
    if step is not None:
        step.status = "blocked"
        step.error = code
    run.status = "blocked"
    run.error = code
    db.commit()
    return {"status": "blocked", "node_id": node_id, "code": code, "blockers": reasons}


def continue_after_acceptance(db, *, run_id, accepted_node_id, accepted_hash, user,
                              accepted_output_id=None, accepted_attempt_id=None,
                              accepted_decision=None):
    """Prepare and execute the next dependency-ready Stage once.

    The acceptance transaction has already committed before this function is
    called. Automatic execution is therefore recoverable through the durable
    invocation key and never makes acceptance depend on provider availability.
    """

    run = db.get(WorkflowRun, run_id)
    if run is None or run.content_unit_id is None:
        return {"status": "blocked", "code": "stage_run_not_found"}
    unit = db.get(ContentUnit, run.content_unit_id)
    project_id = unit.project_id if unit else None
    workflow = db.get(Workflow, run.workflow_id)
    if unit is None or workflow is None or project_id is None:
        return {"status": "blocked", "code": "stage_context_not_found"}
    if run.status in {"canceled", "cancelled", "failed", "unknown", "archived"}:
        return {"status": "blocked", "code": "stage_run_not_continuable"}

    accepted = creation_recipes.accepted_stage_target(
        db, run, accepted_node_id, project_output_id=accepted_output_id,
        accepted_attempt_id=accepted_attempt_id, accepted_hash=accepted_hash,
        accepted_decision=accepted_decision,
    )
    if accepted is None:
        return {"status": "blocked", "code": "accepted_target_integrity"}

    definition = workflow.definition_json or {}
    nodes = {node["id"]: node for node in definition.get("nodes", [])}
    steps = {step.node_id: step for step in db.scalars(
        select(WorkflowStep).where(WorkflowStep.run_id == run.id)
    ).all()}
    order = definition.get("visual_order") or list(nodes)
    dependencies = {}
    for edge in definition.get("edges", []):
        dependencies.setdefault(edge["to"], []).append(edge["from"])

    dependency_wait = None
    for node_id in order:
        step = steps.get(node_id)
        if step is None:
            return _blocked(db, run, None, node_id, "stage_dependency_missing")
        if step.status in {"succeeded", "skipped"}:
            continue
        if step.status != "pending":
            attempt = db.scalar(select(WorkflowStepAttempt).where(WorkflowStepAttempt.step_id == step.id)
                                .order_by(WorkflowStepAttempt.attempt_no.desc()).limit(1))
            receipt = attempt.execution_receipt_json or {} if attempt else {}
            return {"status": step.status, "node_id": node_id, "code": step.error,
                    "attempt_id": attempt.id if attempt else None,
                    "resolution_hash": receipt.get("resolution_hash"),
                    "invocation_key": receipt.get("invocation_key"), "request_mode": "automatic"}
        deps = dependencies.get(node_id, [])
        if any(steps.get(dep) is None for dep in deps):
            return _blocked(db, run, step, node_id, "stage_dependency_missing")
        if any(steps[dep].status in {"failed", "stale", "unknown"} for dep in deps):
            dependency_wait = dependency_wait or {"status": "blocked", "node_id": node_id,
                                                   "code": "stage_dependency_blocked"}
            continue
        if not all(steps[dep].status in {"succeeded", "skipped"} for dep in deps):
            dependency_wait = dependency_wait or {"status": "pending", "node_id": node_id,
                                                   "code": "stage_dependency_not_ready"}
            continue
        node = nodes[node_id]
        try:
            descriptor = registry.descriptor("node", node.get("plugin"), str(node.get("plugin_version") or "1"))
        except RegistryError:
            return _blocked(db, run, step, node_id, "stage_plugin_unavailable")
        if descriptor.stage_contract is None:
            return _blocked(db, run, step, node_id, "legacy_stage_auto_continue_unsupported")
        if node.get("plugin") == "stage.audio.asr":
            return {"status": "pending", "node_id": node_id,
                    "code": "stage_manual_execution_required", "request_mode": "explicit"}
        try:
            resolved = creation_recipes.preview_stage(
                db, project_id, unit.id, node_id, user, run_id=run.id, stage_override={}
            )
        except (HTTPException, StageContractError, ValueError):
            return _blocked(db, run, step, node_id, "stage_preview_failed")
        if not resolved.get("ready"):
            return _blocked(db, run, step, node_id, "stage_blocked", blockers=resolved.get("blockers") or ["stage_blocked"])
        master_context = (resolved.get("context") or {}).get("master") or {}
        if (accepted["output_kind"] == "content_master_revision" and (
                master_context.get("id") != accepted["entity_id"]
                or master_context.get("payload_hash") != accepted_hash
                or master_context.get("context_hash") != accepted.get("context_hash"))):
            return _blocked(db, run, step, node_id, "accepted_context_changed")
        if accepted["output_kind"] != "content_master_revision":
            direct_upstream = (resolved.get("upstream") or {}).get(accepted_node_id)
            if accepted_node_id in deps and (direct_upstream is None or direct_upstream.get("accepted_hash") != accepted_hash):
                return _blocked(db, run, step, node_id, "accepted_context_changed")
        accepted_input = {
            "run_id": run.id, "accepted_node_id": accepted_node_id,
            "accepted_hash": accepted_hash, "node_id": node_id,
            "resolution_hash": resolved["resolution_hash"],
        }
        invocation_key = "auto-accept:" + digest(accepted_input)
        try:
            result = execute_stage(
                db, project_id, unit.id, node_id, user,
                run_id=run.id, expected_resolution_hash=resolved["resolution_hash"],
                invocation_key=invocation_key, stage_override={}, automatic=True,
            )
        except StageInvocationError as exc:
            blocked = _blocked(db, run, step, node_id, exc.code)
            blocked.update(resolution_hash=resolved["resolution_hash"], invocation_key=invocation_key)
            return blocked
        if result.get("status") == "succeeded" and not descriptor.stage_contract.to_dict()["requires_human_acceptance"]:
            db.refresh(step)
            continue
        return {
            "status": result.get("status", "blocked"), "node_id": node_id,
            "attempt_id": result.get("attempt_id"), "resolution_hash": resolved["resolution_hash"],
            "invocation_key": invocation_key, "request_mode": "automatic",
        }
    return dependency_wait or {"status": "complete", "node_id": accepted_node_id, "request_mode": "automatic"}
