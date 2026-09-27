"""工作流画布 API：模板实例化 / 启动 / 详情 / 人工节点完成 / 重试。"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_admin, require_editor, require_editor_or_reviewer
from ..models import User, Workflow, WorkflowRun, WorkflowStep, utcnow
from ..services import workflow_engine
from ..services.workflow_templates import TEMPLATES, build_definition

router = APIRouter(prefix="/api/v1", tags=["workflows"])


class WorkflowCreateIn(BaseModel):
    template_key: str | None = None
    catalog_key: str | None = None  # V1：共享 Workflow Bundle（schema v2）
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
        "workflow_key": w.workflow_key,
        "version": w.version,
        "status": w.status,
        "schema_version": w.schema_version,
        "checksum": w.checksum,
        "enabled": w.enabled,
        "node_count": len(w.definition_json.get("nodes", [])),
        "runs": [
            {
                "id": r.id,
                "status": r.status,
                "error": (r.error or "")[:160],
                "topic_id": r.topic_id,
                "channel": r.channel,
                "content_form": r.content_form,
                "workflow_key": r.workflow_key,
                "workflow_version": r.workflow_version,
                "definition_checksum": (r.definition_checksum or "")[:12],
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
        "topic_id": run.topic_id,
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


@router.get("/workflows/templates")
def list_templates(user: User = Depends(get_current_user)):
    return [
        {"key": key, "name": t["name"], "description": t["description"], "params_schema": t["params_schema"]}
        for key, t in TEMPLATES.items()
    ]


@router.post("/workflows", status_code=201)
def create_workflow(payload: WorkflowCreateIn, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    if payload.catalog_key:
        # V1 PRD 2.0（7.2）：共享 Workflow Bundle 实例化（schema v2，多平台复用）
        from ..services.workflow_templates import build_catalog_workflow

        try:
            definition = build_catalog_workflow(payload.catalog_key, payload.params)
        except ValueError as exc:
            raise HTTPException(404, str(exc)) from exc
        max_version = db.scalars(
            select(Workflow.version).where(Workflow.workflow_key == payload.catalog_key).order_by(Workflow.version.desc()).limit(1)
        ).first() or 0
        workflow = Workflow(
            name=payload.name or payload.catalog_key,
            description=f"共享 Bundle · {payload.catalog_key} · {payload.params.get('channel', '')}",
            template_key=None,
            workflow_key=payload.catalog_key,
            version=max_version + 1,
            schema_version=2,
            status="published",
            checksum=workflow_engine.definition_checksum(definition),
            definition_json=definition,
            created_by=user.email,
        )
        db.add(workflow)
        db.commit()
        return _serialize_workflow(workflow, db)

    if not payload.template_key or payload.template_key not in TEMPLATES:
        raise HTTPException(404, f"未知模板: {payload.template_key}")
    template = TEMPLATES[payload.template_key]
    definition = build_definition(payload.template_key, payload.params)
    workflow = Workflow(
        name=payload.name or template["name"],
        description=template["description"],
        template_key=payload.template_key,
        # 模板实例仍为 schema v1 定义（引擎经 registry 兼容解析）；版本化 catalog 在 Phase 7 切换
        workflow_key=f"legacy.{payload.template_key}",
        version=1,
        schema_version=1,
        status="published",
        checksum=workflow_engine.definition_checksum(definition),
        definition_json=definition,
        created_by=user.email,
    )
    db.add(workflow)
    db.commit()
    return _serialize_workflow(workflow, db)


@router.get("/workflows/catalog")
def workflow_catalog(user: User = Depends(get_current_user)):
    """Workflow Bundle catalog（§9.1）：legacy 模板 available；标准 workflow families Phase 7 启用。"""
    from ..services.workflow_templates import CATALOG_FAMILIES

    items = [
        {"key": key, "name": t["name"], "description": t["description"], "status": "available", "kind": "legacy"}
        for key, t in TEMPLATES.items()
    ]
    items += [
        {"key": key, "name": label, "description": "共享 Workflow Bundle（Phase 7 启用）", "status": "reserved", "kind": "bundle"}
        for key, label in CATALOG_FAMILIES
    ]
    return items


@router.post("/workflows/{workflow_id}/clone", status_code=201)
def clone_workflow(workflow_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    """§6.28：clone 为新 draft 版本（published 不可改——修改 = clone 新版本，D4 immutable）。"""
    source = db.get(Workflow, workflow_id)
    if not source:
        raise HTTPException(404, "工作流不存在")
    if not source.workflow_key:
        raise HTTPException(409, "legacy 无 key 工作流不能 clone（从模板/catalog 重新创建）")
    max_version = db.scalars(
        select(Workflow.version).where(Workflow.workflow_key == source.workflow_key).order_by(Workflow.version.desc()).limit(1)
    ).first() or 0
    clone = Workflow(
        name=f"{source.name} (v{max_version + 1})",
        description=source.description,
        template_key=source.template_key,
        workflow_key=source.workflow_key,
        version=max_version + 1,
        parent_id=source.id,
        schema_version=source.schema_version,
        status="draft",
        checksum=None,  # publish 时冻结
        definition_json=source.definition_json,
        created_by=user.email,
    )
    db.add(clone)
    db.commit()
    return _serialize_workflow(clone, db)


@router.post("/workflows/{workflow_id}/publish")
def publish_workflow(workflow_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    """§6.28：draft → published（checksum 冻结）；published immutable（再改须 clone）。"""
    workflow = db.get(Workflow, workflow_id)
    if not workflow:
        raise HTTPException(404, "工作流不存在")
    if workflow.status == "published":
        raise HTTPException(409, "已发布版本 immutable，请 clone 新版本")
    if workflow.status == "archived":
        raise HTTPException(409, "已归档版本不能发布，请 clone 新版本")
    workflow.status = "published"
    workflow.checksum = workflow_engine.definition_checksum(workflow.definition_json)
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
    try:
        run = workflow_engine.start_run(db, workflow, payload.params, user)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
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
    user: User = Depends(require_editor_or_reviewer),
):
    """人工节点完成（R2：批准类人工节点由 reviewer 触发；节点内部仍走各自闸门）。"""
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


@router.post("/workflow-runs/{run_id}/nodes/{node_id}/rerun")
def rerun_node(run_id: int, node_id: str, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    """D27：节点新 attempt；output 变化 → downstream stale（不自动重跑）。"""
    run = db.get(WorkflowRun, run_id)
    if not run:
        raise HTTPException(404, "运行不存在")
    try:
        run = workflow_engine.rerun_node(db, run, node_id, user)
    except ValueError as exc:
        raise HTTPException(409, str(exc))
    return _serialize_run(db, run)


@router.post("/workflow-runs/{run_id}/nodes/{node_id}/rerun-from-here")
def rerun_from_here(run_id: int, node_id: str, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    """D27：当前+downstream 置 pending 重跑；产生新 Revision，不回滚历史实体。"""
    run = db.get(WorkflowRun, run_id)
    if not run:
        raise HTTPException(404, "运行不存在")
    try:
        run = workflow_engine.rerun_from_here(db, run, node_id, user)
    except ValueError as exc:
        raise HTTPException(409, str(exc))
    return _serialize_run(db, run)


@router.get("/workflow-runs/{run_id}/nodes/{node_id}/attempts")
def list_node_attempts(run_id: int, node_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """R2-H7：节点执行 attempt 审计历史（新旧 output 均可查，rerun 不抹历史）。"""
    from ..models import WorkflowStep, WorkflowStepAttempt

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


@router.get("/workflow-runs")
def list_runs(
    topic_id: int | None = None,
    channel: str | None = None,
    content_form: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """§6.28：按 target 维度检索 runs（一个 Platform×ContentForm 一个 Run）。"""
    stmt = select(WorkflowRun).order_by(WorkflowRun.id.desc()).limit(100)
    if topic_id is not None:
        stmt = stmt.where(WorkflowRun.topic_id == topic_id)
    if channel:
        stmt = stmt.where(WorkflowRun.channel == channel)
    if content_form:
        stmt = stmt.where(WorkflowRun.content_form == content_form)
    runs = db.scalars(stmt).all()
    return [
        {
            "id": r.id,
            "workflow_id": r.workflow_id,
            "status": r.status,
            "topic_id": r.topic_id,
            "channel": r.channel,
            "content_form": r.content_form,
            "workflow_key": r.workflow_key,
            "workflow_version": r.workflow_version,
            "definition_checksum": (r.definition_checksum or "")[:12],
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
        }
        for r in runs
    ]


@router.post("/workflow-runs/{run_id}/cancel")
def cancel_run(run_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    run = db.get(WorkflowRun, run_id)
    if not run or run.status not in {"running", "waiting_input"}:
        raise HTTPException(409, "仅运行中/等待人工的运行可取消")
    run.status = "canceled"
    run.finished_at = utcnow()
    db.commit()
    return _serialize_run(db, run)
