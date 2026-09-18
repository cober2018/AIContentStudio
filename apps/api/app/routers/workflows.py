"""工作流画布 API：模板实例化 / 启动 / 详情 / 人工节点完成 / 重试。"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_admin, require_editor
from ..models import User, Workflow, WorkflowRun, WorkflowStep, utcnow
from ..services import workflow_engine
from ..services.workflow_templates import TEMPLATES, build_definition

router = APIRouter(prefix="/api/v1", tags=["workflows"])


class WorkflowCreateIn(BaseModel):
    template_key: str
    name: str | None = None
    params: dict = {}


class RunCreateIn(BaseModel):
    workflow_id: int
    params: dict = {}


class NodeCompleteIn(BaseModel):
    payload: dict = {}


def _serialize_workflow(w: Workflow, db: Session) -> dict:
    runs = db.scalars(
        select(WorkflowRun).where(WorkflowRun.workflow_id == w.id).order_by(WorkflowRun.id.desc()).limit(10)
    ).all()
    return {
        "id": w.id,
        "name": w.name,
        "description": w.description,
        "template_key": w.template_key,
        "enabled": w.enabled,
        "node_count": len(w.definition_json.get("nodes", [])),
        "runs": [
            {
                "id": r.id,
                "status": r.status,
                "error": (r.error or "")[:160],
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            }
            for r in runs
        ],
    }


def _serialize_run(db: Session, run: WorkflowRun) -> dict:
    steps = db.scalars(
        select(WorkflowStep).where(WorkflowStep.run_id == run.id).order_by(WorkflowStep.id)
    ).all()
    workflow = db.get(Workflow, run.workflow_id)
    nodes = {n["id"]: n for n in (workflow.definition_json if workflow else {}).get("nodes", [])}
    return {
        "id": run.id,
        "workflow_id": run.workflow_id,
        "workflow_name": workflow.name if workflow else None,
        "status": run.status,
        "error": run.error,
        "params": run.params_json,
        "context": run.context_json,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "definition": workflow.definition_json if workflow else {"nodes": [], "edges": []},
        "steps": [
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
            }
            for s in steps
        ],
    }


@router.get("/workflows/templates")
def list_templates(user: User = Depends(get_current_user)):
    return [
        {"key": key, "name": t["name"], "description": t["description"], "params_schema": t["params_schema"]}
        for key, t in TEMPLATES.items()
    ]


@router.post("/workflows", status_code=201)
def create_workflow(payload: WorkflowCreateIn, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    if payload.template_key not in TEMPLATES:
        raise HTTPException(404, f"未知模板: {payload.template_key}")
    template = TEMPLATES[payload.template_key]
    workflow = Workflow(
        name=payload.name or template["name"],
        description=template["description"],
        template_key=payload.template_key,
        definition_json=build_definition(payload.template_key, payload.params),
        created_by=user.email,
    )
    db.add(workflow)
    db.commit()
    return _serialize_workflow(workflow, db)


@router.get("/workflows")
def list_workflows(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    workflows = db.scalars(select(Workflow).order_by(Workflow.id.desc())).all()
    return [_serialize_workflow(w, db) for w in workflows]


@router.post("/workflow-runs", status_code=201)
def create_run(payload: RunCreateIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    workflow = db.get(Workflow, payload.workflow_id)
    if not workflow or not workflow.enabled:
        raise HTTPException(404, "工作流不存在或已停用")
    run = workflow_engine.start_run(db, workflow, payload.params, user)
    return _serialize_run(db, run)


@router.get("/workflow-runs/{run_id}")
def get_run(run_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    run = db.get(WorkflowRun, run_id)
    if not run:
        raise HTTPException(404, "运行不存在")
    return _serialize_run(db, run)


@router.post("/workflow-runs/{run_id}/nodes/{node_id}/complete")
def complete_node(
    run_id: int,
    node_id: str,
    payload: NodeCompleteIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_editor),
):
    run = db.get(WorkflowRun, run_id)
    if not run:
        raise HTTPException(404, "运行不存在")
    try:
        run = workflow_engine.complete_node(db, run, node_id, payload.payload, user)
    except ValueError as exc:
        raise HTTPException(409, str(exc))
    return _serialize_run(db, run)


@router.post("/workflow-runs/{run_id}/retry")
def retry_run(run_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    run = db.get(WorkflowRun, run_id)
    if not run:
        raise HTTPException(404, "运行不存在")
    try:
        run = workflow_engine.retry_run(db, run, user)
    except ValueError as exc:
        raise HTTPException(409, str(exc))
    return _serialize_run(db, run)


@router.post("/workflow-runs/{run_id}/cancel")
def cancel_run(run_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    run = db.get(WorkflowRun, run_id)
    if not run or run.status not in {"running", "waiting_input"}:
        raise HTTPException(409, "仅运行中/等待人工的运行可取消")
    run.status = "canceled"
    run.finished_at = utcnow()
    db.commit()
    return _serialize_run(db, run)
