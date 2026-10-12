"""Append-only decisions; execution outputs never become editable history."""

from sqlalchemy import select, update

from ..models import ProjectEvent, Workflow, WorkflowRun, WorkflowStep, WorkflowStepAttempt
from .content_masters import owned_unit
from .project_authorization import authorize_project_run, lock_project_context
from .project_events import record_project_event
from .stage_contracts import IDENTIFIER, canonical, digest
from .stage_invocations import StageInvocationError, _same_key_result, require_receipt_schema

DECISIONS = frozenset({"accepted", "accepted_with_edits", "rejected", "rerun_requested", "skipped_when_allowed"})


def attempt_context(db, project_id, unit_id, node_id, user, request, *, mutable=False):
    require_receipt_schema(db)
    project, unit = owned_unit(db, project_id, unit_id, user, mutate=mutable)
    if mutable and (not user.is_active or user.role not in {"admin", "editor"}):
        raise StageInvocationError("stage_feedback_readonly", status_code=403)
    run = db.get(WorkflowRun, request.get("run_id"))
    step = db.scalar(select(WorkflowStep).where(WorkflowStep.run_id == request.get("run_id"),
                                               WorkflowStep.node_id == node_id))
    attempt = db.get(WorkflowStepAttempt, request.get("attempt_id"))
    if (run is None or run.content_unit_id != unit.id or step is None or attempt is None
            or attempt.run_id != run.id or attempt.step_id != step.id or attempt.node_id != node_id):
        raise StageInvocationError("stage_attempt_not_found", status_code=404)
    authorize_project_run(db, run, user, mutate=mutable)
    receipt = attempt.execution_receipt_json or {}
    resolved = (attempt.input_snapshot_json or {}).get("resolved_stage") or {}
    if not receipt.get("invocation_key") or not receipt.get("request_fingerprint"):
        raise StageInvocationError("stage_receipt_required")
    original = _same_key_result(db, step, receipt["invocation_key"], receipt["request_fingerprint"])
    workflow = db.get(Workflow, run.workflow_id)
    if original is None or original.id != attempt.id or workflow is None:
        raise StageInvocationError("stage_attempt_integrity")
    if request.get("expected_output_hash", attempt.output_hash) != attempt.output_hash:
        raise StageInvocationError("stage_output_changed")
    if request.get("expected_resolution_hash", attempt.input_hash) != attempt.input_hash:
        raise StageInvocationError("stage_resolution_changed")
    return project, unit, run, step, attempt, resolved


def feedback_events(db, project_id, attempt_id):
    return db.scalars(select(ProjectEvent).where(ProjectEvent.project_id == project_id,
        ProjectEvent.event_type == "creation_recipe.stage_feedback", ProjectEvent.entity_id == str(attempt_id))
        .order_by(ProjectEvent.id)).all()


def allowed_decisions(db, unit, run, step, attempt, user):
    from .content_harness.registry import registry
    from .creation_recipes import accepted_stage_target

    if (not user.is_active or user.role not in {"admin", "editor"} or unit.status == "archived"
            or unit.pinned_workflow_id != run.workflow_id or run.identity_snapshot_id != unit.identity_snapshot_id
            or run.status in {"canceled", "cancelled", "archived"}
            or attempt.attempt_no != step.attempt_no or attempt.status in {"running", "unknown"}):
        return []
    workflow = db.get(Workflow, run.workflow_id)
    node = next(item for item in workflow.definition_json["nodes"] if item["id"] == step.node_id)
    descriptor = registry.descriptor("node", node["plugin"], node["plugin_version"])
    decisions = []
    if attempt.status == "succeeded" and accepted_stage_target(db, run, step.node_id) is None:
        decisions.append("rejected")
    explicit_native_stage = descriptor.key == "media.generate" and descriptor.version in {"2", "3"}
    if not descriptor.side_effect or explicit_native_stage:
        decisions.append("rerun_requested")
    if (node.get("failure_policy") == "skip" and not descriptor.side_effect and not descriptor.human_gate
            and not descriptor.stage_contract.to_dict()["requires_human_acceptance"]):
        decisions.append("skipped_when_allowed")
    return decisions


def record_feedback(db, *, project_id, unit_id, run, step, attempt, user, decision,
                    result_kind=None, result_id=None, accepted_hash=None, project_output_id=None,
                    note="", reason_tags=None, feedback_key=None, extra=None):
    if decision not in DECISIONS:
        raise StageInvocationError("stage_feedback_decision_invalid", status_code=422)
    tags = reason_tags or []
    if (type(note) is not str or len(note) > 2000 or type(tags) is not list or len(tags) > 10
            or any(type(tag) is not str or len(tag) > 80 for tag in tags)):
        raise StageInvocationError("stage_feedback_bounds", status_code=422)
    if feedback_key is not None and (type(feedback_key) is not str or not IDENTIFIER.fullmatch(feedback_key)):
        raise StageInvocationError("stage_feedback_key_invalid", status_code=422)
    receipt = attempt.execution_receipt_json or {}
    data = canonical({**(extra or {}), "schema": "creation_recipe.stage_feedback.v1",
        "unit_id": unit_id, "workflow_id": run.workflow_id, "workflow_version": run.workflow_version,
        "workflow_checksum": run.definition_checksum, "run_id": run.id, "node_id": step.node_id,
        "attempt_id": attempt.id, "plugin_key": attempt.plugin_key, "plugin_version": attempt.plugin_version,
        "config_hash": receipt.get("config_hash"), "prompt_hash": receipt.get("prompt_hash"),
        "resolution_hash": receipt.get("resolution_hash"), "output_hash": attempt.output_hash,
        "decision": decision, "result_kind": result_kind, "result_id": result_id,
        "accepted_hash": accepted_hash, "project_output_id": project_output_id,
        "note": note, "reason_tags": tags, "feedback_key": feedback_key})
    record_method_outcome(db, attempt, decision)
    return record_project_event(db, project_id=project_id, event_type="creation_recipe.stage_feedback",
        actor=user.email, entity_type="workflow_step_attempt", entity_id=attempt.id, payload=data)


def record_method_outcome(db, attempt, decision):
    from ..models import CapabilityUse

    receipt = attempt.execution_receipt_json or {}
    use_ids = receipt.get("capability_use_ids") or ([receipt["capability_use_id"]] if receipt.get("capability_use_id") else [])
    if use_ids and decision in {"accepted", "accepted_with_edits", "rejected"}:
        outcome = "rejected" if decision == "rejected" else "accepted"
        db.execute(update(CapabilityUse).where(CapabilityUse.id.in_(use_ids), CapabilityUse.outcome == "used")
                   .values(outcome=outcome).execution_options(synchronize_session="fetch"))


def invalidate_downstream(db, run, step, accepted_hash):
    attempt = db.scalar(select(WorkflowStepAttempt).where(WorkflowStepAttempt.step_id == step.id)
                        .order_by(WorkflowStepAttempt.attempt_no.desc()).limit(1))
    if attempt:
        record_method_outcome(db, attempt, "accepted")
    workflow = db.get(Workflow, run.workflow_id)
    children = {}
    for edge in (workflow.definition_json or {}).get("edges", []):
        children.setdefault(edge["from"], set()).add(edge["to"])
    affected, pending = set(), []
    for child in children.get(step.node_id, set()):
        downstream = db.scalar(select(WorkflowStep).where(WorkflowStep.run_id == run.id, WorkflowStep.node_id == child))
        attempt = db.scalar(select(WorkflowStepAttempt).where(WorkflowStepAttempt.step_id == downstream.id)
                            .order_by(WorkflowStepAttempt.attempt_no.desc()).limit(1)) if downstream else None
        upstream = ((attempt.input_snapshot_json or {}).get("resolved_stage") or {}).get("upstream") or {} if attempt else {}
        consumed = upstream.get(step.node_id)
        if consumed is not None and consumed.get("accepted_hash", consumed.get("payload_hash")) != accepted_hash:
            affected.add(child)
            pending.append(child)
    while pending:
        for child in children.get(pending.pop(0), set()):
            if child not in affected:
                affected.add(child)
                pending.append(child)
    for downstream in db.scalars(select(WorkflowStep).where(WorkflowStep.run_id == run.id,
                                                           WorkflowStep.node_id.in_(affected))):
        attempt = db.scalar(select(WorkflowStepAttempt).where(WorkflowStepAttempt.step_id == downstream.id)
                            .order_by(WorkflowStepAttempt.attempt_no.desc()).limit(1))
        if attempt is None:
            continue
        downstream.stale_reason = "accepted_stage_input_changed"
        if downstream.status not in {"running", "unknown"}:
            downstream.status = "stale"
            downstream.error = "accepted_stage_input_changed"
        # Running/unknown claims remain unresolved; a stale flag must never make them safe to resend.


def submit_feedback(db, project_id, unit_id, node_id, user, request):
    request = canonical(request, max_bytes=16 * 1024)
    if not request.get("expected_output_hash") or not request.get("expected_resolution_hash"):
        raise StageInvocationError("stage_feedback_hashes_required", status_code=422)
    decision, key = request.get("decision"), request.get("feedback_key")
    if decision not in {"rejected", "rerun_requested", "skipped_when_allowed"}:
        raise StageInvocationError("stage_acceptance_requires_domain_adoption", status_code=422)
    if type(key) is not str or not IDENTIFIER.fullmatch(key):
        raise StageInvocationError("stage_feedback_key_invalid", status_code=422)
    try:
        lock_project_context(db, project_id, user)
        _, unit, run, step, attempt, _resolved = attempt_context(
            db, project_id, unit_id, node_id, user, request, mutable=True)
        fingerprint = digest({"request": request, "actor_id": user.id})
        for event in feedback_events(db, project_id, attempt.id):
            if (event.payload_json or {}).get("feedback_key") == key:
                if event.payload_json.get("feedback_fingerprint") != fingerprint:
                    raise StageInvocationError("stage_feedback_key_conflict")
                return {"feedback_event_id": event.id, "feedback": event.payload_json}
        if attempt.status in {"running", "unknown"}:
            raise StageInvocationError("stage_reconciliation_required")
        if (unit.pinned_workflow_id != run.workflow_id or attempt.attempt_no != step.attempt_no
                or run.status in {"canceled", "cancelled", "archived"}):
            raise StageInvocationError("stage_feedback_not_current")
        if decision not in allowed_decisions(db, unit, run, step, attempt, user):
            raise StageInvocationError("stage_feedback_decision_not_allowed")
        from .creation_recipes import accepted_stage_target
        accepted = accepted_stage_target(db, run, node_id)
        if decision == "rejected":
            if accepted is not None or attempt.status != "succeeded":
                raise StageInvocationError("stage_result_already_adopted")
            step.status, step.error = "blocked", "stage_result_rejected"
            run.status, run.error = "blocked", "stage_result_rejected"
        elif decision == "skipped_when_allowed":
            workflow = db.get(Workflow, run.workflow_id)
            node = next((item for item in workflow.definition_json.get("nodes", []) if item["id"] == node_id), {})
            from .content_harness.registry import registry
            descriptor = registry.descriptor("node", node.get("plugin"), node.get("plugin_version"))
            if (node.get("failure_policy") != "skip" or descriptor.side_effect or descriptor.human_gate
                    or descriptor.stage_contract.to_dict()["requires_human_acceptance"]):
                raise StageInvocationError("stage_skip_not_allowed")
            step.status, step.error = "skipped", None
            remaining = db.scalars(select(WorkflowStep).where(WorkflowStep.run_id == run.id)).all()
            run.status = "succeeded" if all(item.status in {"succeeded", "skipped"} for item in remaining) else "pending"
        else:
            if run.status == "succeeded":
                run.status = "pending"
        event = record_feedback(db, project_id=project_id, unit_id=unit_id, run=run, step=step,
            attempt=attempt, user=user, decision=decision, note=request.get("note", ""),
            reason_tags=request.get("reason_tags", []), feedback_key=key,
            extra={"feedback_fingerprint": fingerprint})
        db.flush()
        response = {"feedback_event_id": event.id, "feedback": event.payload_json}
        db.commit()
        return response
    except BaseException:
        db.rollback()
        raise


def history(db, project_id, unit_id, node_id, user, *, run_id):
    require_receipt_schema(db)
    owned_unit(db, project_id, unit_id, user)
    run = db.get(WorkflowRun, run_id)
    if run is None or run.content_unit_id != unit_id:
        raise StageInvocationError("stage_run_not_found", status_code=404)
    authorize_project_run(db, run, user)
    step = db.scalar(select(WorkflowStep).where(WorkflowStep.run_id == run_id, WorkflowStep.node_id == node_id))
    if step is None:
        raise StageInvocationError("stage_not_found", status_code=404)
    items = []
    for attempt in db.scalars(select(WorkflowStepAttempt).where(WorkflowStepAttempt.step_id == step.id)
                              .order_by(WorkflowStepAttempt.attempt_no.desc()).limit(100)):
        receipt = attempt.execution_receipt_json or {}
        items.append({"attempt_id": attempt.id, "attempt_no": attempt.attempt_no, "status": attempt.status,
            "output_hash": attempt.output_hash, "input_hash": attempt.input_hash,
            "receipt": canonical(receipt), "feedback": [{"id": event.id, "created_at": event.created_at.isoformat(),
                **event.payload_json} for event in feedback_events(db, project_id, attempt.id)]})
    return {"run_id": run_id, "node_id": node_id, "items": items}
