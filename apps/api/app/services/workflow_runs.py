"""Run views shared by the unit run routes; the standalone workflow pages are gone."""

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import User, Workflow, WorkflowRun, WorkflowStep, WorkflowStepAttempt
from .project_authorization import authorize_project_run


def serialize_run(db: Session, run: WorkflowRun) -> dict:
    steps = db.scalars(
        select(WorkflowStep).where(WorkflowStep.run_id == run.id).order_by(WorkflowStep.id)
    ).all()
    workflow = db.get(Workflow, run.workflow_id)
    nodes = {n["id"]: n for n in (workflow.definition_json if workflow else {}).get("nodes", [])}
    steps_out = [
        {
            "id": s.id,
            "node_id": s.node_id,
            "node_type": s.node_type,
            "label": s.label or (nodes.get(s.node_id, {}).get("label") or s.node_id),
            "params": s.params_json,
            "status": s.status,
            "output": s.output_json,
            "error": s.error,
            "layout": nodes.get(s.node_id, {}).get("layout", {"x": 0, "y": 0}),
            "channel": s.params_json.get("channel"),
            "plugin_key": s.plugin_key,
            "plugin_version": s.plugin_version,
            "attempt_no": s.attempt_no,
            "stale_reason": s.stale_reason,
        }
        for s in steps
    ]
    return {
        "id": run.id,
        "workflow_id": run.workflow_id,
        "workflow_name": workflow.name if workflow else None,
        "workflow_key": run.workflow_key,
        "workflow_version": run.workflow_version,
        "definition_checksum": run.definition_checksum,
        "identity_snapshot_id": run.identity_snapshot_id,
        "identity_state": "frozen" if run.identity_snapshot_id else "legacy_identity",
        "channel": run.channel,
        "content_form": run.content_form,
        "status": run.status,
        "error": run.error,
        "params": run.params_json,
        "context": run.context_json,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "definition": workflow.definition_json if workflow else {"nodes": [], "edges": []},
        "steps": steps_out,
    }


def list_node_attempts(run_id: int, node_id: str, db: Session, user: User) -> list[dict]:
    """R2-H7：节点执行 attempt 审计历史（新旧 output 均可查，rerun 不抹历史）。"""
    run = db.get(WorkflowRun, run_id)
    if not run:
        raise HTTPException(404, "运行不存在")
    authorize_project_run(db, run, user)

    step = db.scalars(
        select(WorkflowStep).where(WorkflowStep.run_id == run_id, WorkflowStep.node_id == node_id)
    ).first()
    if not step:
        raise HTTPException(404, "节点不存在")
    rows = db.scalars(
        select(WorkflowStepAttempt)
        .where(WorkflowStepAttempt.step_id == step.id)
        .order_by(WorkflowStepAttempt.attempt_no)
    ).all()
    return [
        {
            "attempt_no": r.attempt_no,
            "status": r.status,
            "plugin_key": r.plugin_key,
            "plugin_version": r.plugin_version,
            "input_hash": r.input_hash,
            "output_hash": r.output_hash,
            "output_json": r.output_json,
            "error": r.error,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
