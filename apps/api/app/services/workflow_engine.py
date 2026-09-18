"""工作流画布执行引擎：DAG 拓扑推进 + 人工节点挂起续跑。

节点 handler 直接调用既有路由函数/服务（同一套校验、审计、闸门），画布只是编排壳。
执行模型：同步推进（TASK_QUEUE_ENABLED 的异步模式留给 V2）；人工节点置
waiting_input 后返回，前端操作后调 complete 续跑；失败即停、可从失败节点重试。
"""

import logging
from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import (
    ContentJob,
    Draft,
    Fact,
    FactPack,
    TopicBrief,
    Workflow,
    WorkflowRun,
    WorkflowStep,
)

logger = logging.getLogger(__name__)

HUMAN_NODE_TYPES = {"adopt_topic", "approve"}


def _now():
    return datetime.now(UTC)


def _ctx_update(run: WorkflowRun, **kv) -> dict:
    """copy-on-write 更新 context：必须赋「新 dict」才能触发 SQLAlchemy 脏标记（原地改不落库）。"""
    ctx = {**(run.context_json or {}), **kv}
    run.context_json = ctx
    return ctx


# ---------- handler：每个节点类型一个，签名统一 (db, run, step, user) ----------


def _h_connector_pull(db: Session, run: WorkflowRun, step: WorkflowStep, user) -> dict:
    from ..models import ConnectorEndpoint
    from ..services import connector_service

    endpoint = db.get(ConnectorEndpoint, step.params_json.get("endpoint_id"))
    if not endpoint:
        raise ValueError("未配置有效的监测端点（endpoint_id）")
    doc, facts = connector_service.pull_endpoint(db, endpoint, user)
    source_ids = list((run.context_json or {}).get("source_ids") or []) + [doc.id]
    _ctx_update(run, source_ids=source_ids)
    return {"source_id": doc.id, "title": doc.title, "candidate_facts": facts}


def _h_extract_facts(db: Session, run: WorkflowRun, step: WorkflowStep, user) -> dict:
    """复用 sources 抽取逻辑 + 自动确认（工作流语境默认信任来源并确认，人工核对走 Source 页）。"""
    from ..routers.sources import extract_facts

    ctx = run.context_json or {}
    source_ids = ctx.get("source_ids") or []
    if not source_ids:
        raise ValueError("上游没有拉取到任何 Source")
    confirmed = 0
    for sid in source_ids:
        extract_facts(source_id=sid, db=db, user=user)  # 幂等：清旧候选重抽
        if step.params_json.get("auto_confirm", True):
            candidates = db.scalars(
                select(Fact).where(Fact.source_document_id == sid, Fact.status == "candidate")
            ).all()
            for f in candidates:
                f.status = "confirmed"
                confirmed += 1
    all_fact_ids = list(
        db.scalars(select(Fact.id).where(Fact.source_document_id.in_(source_ids))).all()
    )
    _ctx_update(run, fact_ids=all_fact_ids)
    return {"sources": len(source_ids), "auto_confirmed": confirmed}


def _h_factpack_freeze(db: Session, run: WorkflowRun, step: WorkflowStep, user) -> dict:
    from datetime import datetime

    ctx = run.context_json
    fact_ids = list(dict.fromkeys(ctx.get("fact_ids") or []))
    confirmed = db.scalars(select(Fact).where(Fact.id.in_(fact_ids), Fact.status == "confirmed")).all() if fact_ids else []
    if not confirmed:
        raise ValueError("没有已确认的事实可打包")
    name = step.params_json.get("name") or f"工作流事实包 {datetime.now(UTC).strftime('%m-%d')}"
    version = (
        db.scalar(select(FactPack.version).where(FactPack.name == name).order_by(FactPack.version.desc()).limit(1)) or 0
    ) + 1
    pack = FactPack(name=name, version=version, created_by=user.email)
    db.add(pack)
    db.flush()
    from ..models import FactPackItem

    for i, f in enumerate(confirmed):
        db.add(FactPackItem(fact_pack_id=pack.id, fact_id=f.id, sort_order=i))
    db.flush()

    from ..routers.fact_packs import freeze_fact_pack

    frozen = freeze_fact_pack(pack_id=pack.id, db=db, user=user)
    _ctx_update(run, pack_id=frozen["id"])
    return {"pack_id": frozen["id"], "name": frozen["name"], "version": frozen["version"], "items": frozen.get("item_count")}


def _h_suggest_topics(db: Session, run: WorkflowRun, step: WorkflowStep, user) -> dict:
    from ..services.topic_suggest import suggest_for_pack

    ctx = run.context_json
    pack_id = step.params_json.get("pack_id") or ctx.get("pack_id")
    pack = db.get(FactPack, pack_id) if pack_id else None
    if not pack:
        raise ValueError("荐题需要冻结 FactPack（上游打包节点或参数 pack_id）")
    result = suggest_for_pack(db, pack, count=int(step.params_json.get("count", 3)))
    _ctx_update(run, suggestions=result["suggestions"])
    return {"candidates": len(result["suggestions"]), "model": result["model"]}


def _h_adopt_topic_complete(db: Session, run: WorkflowRun, step: WorkflowStep, payload: dict, user) -> dict:
    """人工采纳：payload {index, channels, overrides?} → 创建 Topic。"""
    from ..routers.topics import TopicCreateIn, create_topic

    ctx = run.context_json
    suggestions = ctx.get("suggestions") or []
    index = int(payload.get("index", 0))
    if index >= len(suggestions):
        raise ValueError(f"候选序号越界：{index}/{len(suggestions)}")
    s = suggestions[index]
    channels = payload.get("channels") or ["douyin", "xiaohongshu", "wechat"]
    overrides = payload.get("overrides") or {}
    created = create_topic(
        payload=TopicCreateIn(
            title=overrides.get("title") or s["title"],
            audience=overrides.get("audience") or s.get("audience"),
            goal=overrides.get("goal") or s.get("goal"),
            angle=overrides.get("angle") or s.get("angle"),
            core_thesis=overrides.get("core_thesis") or s.get("core_thesis"),
            must_include=s.get("must_include") or [],
            forbidden=s.get("forbidden") or [],
            cta=s.get("cta"),
            fact_pack_id=s["fact_pack_id"],
            channels=channels,
        ),
        db=db,
        user=user,
    )
    _ctx_update(run, topic_id=created["id"])
    return {"topic_id": created["id"], "title": created["title"]}


def _h_generate(db: Session, run: WorkflowRun, step: WorkflowStep, user) -> dict:
    from ..routers.topics import VALID_CHANNELS
    from ..services.generation.orchestrator import create_jobs_for_topic
    from ..tasks import worker_tasks

    channel = step.params_json.get("channel")
    if channel not in VALID_CHANNELS:
        raise ValueError(f"未知渠道: {channel}")
    topic_id = run.params_json.get("topic_id") or run.context_json.get("topic_id")
    if not topic_id:
        raise ValueError("生成需要 topic_id（人工采纳或启动参数）")
    topic = db.get(TopicBrief, topic_id)
    if not topic:
        raise ValueError(f"Topic {topic_id} 不存在")

    jobs = create_jobs_for_topic(db, topic, [channel])
    statuses = []
    for job in jobs:
        status = worker_tasks.dispatch_generation(db, job.id)
        statuses.append(status)
    fresh_job = db.get(ContentJob, jobs[0].id)
    if fresh_job and fresh_job.status != "succeeded":
        # 真实模型偶发解析失败等：把生成失败暴露为节点失败（画布可重试），而不是静默往下走
        raise ValueError(f"生成失败（{channel}）：{fresh_job.error or fresh_job.status}")
    draft = db.scalars(
        select(Draft).where(Draft.content_job_id == jobs[0].id).order_by(Draft.revision_no.desc()).limit(1)
    ).first()
    jobs_ctx = {**((run.context_json or {}).get("jobs") or {}), channel: {"job_id": jobs[0].id, "draft_id": draft.id if draft else None}}
    _ctx_update(run, jobs=jobs_ctx)
    return {"job_id": jobs[0].id, "status": statuses[0], "draft_id": draft.id if draft else None, "title": draft.title if draft else None}


def _h_fact_check(db: Session, run: WorkflowRun, step: WorkflowStep, user) -> dict:
    from ..routers.generate import run_fact_check as run_fc

    channel = step.params_json.get("channel")
    draft_id = (run.context_json.get("jobs") or {}).get(channel, {}).get("draft_id")
    if not draft_id:
        raise ValueError(f"渠道 {channel} 没有可校验的草稿")
    result = run_fc(draft_id=draft_id, db=db, user=user)
    return {
        "draft_id": draft_id,
        "result": result.get("result"),
        "blockers": (result.get("stats") or {}).get("blockers", 0),
        "warnings": (result.get("stats") or {}).get("warnings", 0),
    }


def _h_approve(db: Session, run: WorkflowRun, step: WorkflowStep, payload: dict, user) -> dict:
    """人工批准：提交审核 + 批准（沿用既有 409 闸门），产出 Asset。"""
    from fastapi import HTTPException

    from ..routers.generate import submit_for_review
    from ..routers.reviews import DecisionIn, approve

    channel = step.params_json.get("channel")
    draft_id = (run.context_json.get("jobs") or {}).get(channel, {}).get("draft_id")
    if not draft_id:
        raise ValueError(f"渠道 {channel} 没有可批准的草稿")
    submit_for_review(draft_id=draft_id, db=db, user=user)
    try:
        result = approve(draft_id=draft_id, payload=DecisionIn(comment="工作流画布批准"), db=db, user=user)
    except HTTPException as exc:
        raise ValueError(f"批准被闸门拦截：{exc.detail}") from exc
    assets_ctx = {**((run.context_json or {}).get("assets") or {}), channel: result["asset_id"]}
    _ctx_update(run, assets=assets_ctx)
    return {"asset_id": result["asset_id"]}


def _h_export(db: Session, run: WorkflowRun, step: WorkflowStep, user) -> dict:
    from ..routers.assets import ExportIn, export_asset

    channel = step.params_json.get("channel")
    asset_id = (run.context_json.get("assets") or {}).get(channel)
    if not asset_id:
        raise ValueError(f"渠道 {channel} 没有已批准的资产可导出")
    files = []
    for fmt in step.params_json.get("formats") or ["md"]:
        result = export_asset(asset_id=asset_id, payload=ExportIn(fmt=fmt), db=db, user=user)
        files.append(result["filename"])
    return {"asset_id": asset_id, "files": files}


def _h_publish_wechat(db: Session, run: WorkflowRun, step: WorkflowStep, user) -> dict:
    """公众号草稿箱：导出 MD + 封面（上传真图优先，否则占位 PNG）→ wewrite publish。"""
    import subprocess
    import tempfile
    from pathlib import Path

    from sqlalchemy import select as sa_select

    from ..models import AssetMedia
    from ..services.exports import export_markdown

    channel = "wechat"
    asset_id = (run.context_json.get("assets") or {}).get(channel)
    if not asset_id:
        raise ValueError("公众号线没有已批准的资产")
    from ..models import ContentAsset

    asset = db.get(ContentAsset, asset_id)
    with tempfile.TemporaryDirectory() as tmp:
        md_path = Path(tmp) / "article.md"
        md_path.write_text(export_markdown(asset), encoding="utf-8")
        uploaded = db.scalars(
            sa_select(AssetMedia).where(
                AssetMedia.asset_id == asset_id, AssetMedia.kind == "cover", AssetMedia.source == "upload"
            )
        ).first()
        if uploaded and uploaded.file_path:
            from ..services.asset_media import MEDIA_ROOT

            cover_path = MEDIA_ROOT / uploaded.file_path
        else:
            cover_path = Path(tmp) / "cover.png"
            cover_path.write_bytes(_placeholder_png())
        title = asset.title[:60]
        digest = (asset.title[:54]) or title
        cmd = [
            "wewrite", "publish", str(md_path),
            "--cover", str(cover_path), "--title", title, "--digest", digest,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180, check=False)
        output = (proc.stdout or "") + (proc.stderr or "")
        if proc.returncode != 0 or "Draft created" not in output:
            raise ValueError(f"wewrite 发布失败：{output[-300:]}")
    media_id = output.split("Draft created! media_id:")[-1].strip().splitlines()[0]
    return {"asset_id": asset_id, "draft_media_id": media_id}


def _placeholder_png() -> bytes:
    import struct
    import zlib

    w, h = 900, 383
    rgb = (30, 41, 59)
    raw = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


HANDLERS: dict[str, Callable[..., dict]] = {
    "connector_pull": _h_connector_pull,
    "extract_facts": _h_extract_facts,
    "factpack_freeze": _h_factpack_freeze,
    "suggest_topics": _h_suggest_topics,
    "generate": _h_generate,
    "fact_check": _h_fact_check,
    "export": _h_export,
    "publish_wechat": _h_publish_wechat,
}

# 人工节点的完成动作（complete 时调用）；其余节点无 complete 语义
COMPLETE_HANDLERS: dict[str, Callable[..., dict]] = {
    "adopt_topic": _h_adopt_topic_complete,
    "approve": _h_approve,
}


# ---------- 引擎：拓扑推进 ----------


def _steps(db: Session, run: WorkflowRun) -> list[WorkflowStep]:
    return list(db.scalars(select(WorkflowStep).where(WorkflowStep.run_id == run.id).order_by(WorkflowStep.id)))


def advance(db: Session, run: WorkflowRun, user) -> WorkflowRun:
    """从当前断点推进：自动节点逐个执行，人工节点挂起，失败即停。"""
    definition = db.get(Workflow, run.workflow_id).definition_json
    deps: dict[str, list[str]] = {}
    for edge in definition.get("edges", []):
        deps.setdefault(edge["to"], []).append(edge["from"])

    while True:
        steps = {s.node_id: s for s in _steps(db, run)}
        pending = [s for s in steps.values() if s.status == "pending"]
        if not pending:
            if run.status == "running":
                run.status = "succeeded"
                run.finished_at = _now()
                db.commit()
            return run
        ready = [
            s
            for s in pending
            if all(steps[dep].status == "succeeded" for dep in deps.get(s.node_id, []) if dep in steps)
        ]
        if not ready:
            # 无可执行节点且仍有 pending → 挂起在人工节点（status 应已置 waiting_input）
            return run
        step = ready[0]
        if step.node_type in HUMAN_NODE_TYPES:
            step.status = "waiting_input"
            run.status = "waiting_input"
            db.commit()
            return run
        step.status = "running"
        step.started_at = _now()
        run.status = "running"
        db.commit()
        try:
            handler = HANDLERS.get(step.node_type)
            if handler is None:
                raise ValueError(f"未知节点类型: {step.node_type}")
            output = handler(db, run, step, user)
            step.output_json = output
            step.status = "succeeded"
            step.finished_at = _now()
            db.commit()
            logger.info("workflow_step_ok run=%s node=%s", run.id, step.node_id)
        except Exception as exc:  # noqa: BLE001 节点失败即停，可从失败节点重试
            db.rollback()
            fresh = db.get(WorkflowStep, step.id)
            fresh.status = "failed"
            fresh.error = str(exc)[:500]
            fresh.finished_at = _now()
            run.status = "failed"
            run.error = f"节点「{fresh.label or fresh.node_id}」失败：{str(exc)[:300]}"
            db.commit()
            return run


def start_run(db: Session, workflow: Workflow, params: dict | None, user) -> WorkflowRun:
    run = WorkflowRun(workflow_id=workflow.id, params_json=params or {}, context_json={})
    db.add(run)
    db.flush()
    for node in workflow.definition_json.get("nodes", []):
        db.add(
            WorkflowStep(
                run_id=run.id,
                node_id=node["id"],
                node_type=node["type"],
                label=node.get("label"),
                params_json=node.get("params", {}),
            )
        )
    db.commit()
    return advance(db, run, user)


def complete_node(db: Session, run: WorkflowRun, node_id: str, payload: dict, user) -> WorkflowRun:
    step = db.scalars(
        select(WorkflowStep).where(WorkflowStep.run_id == run.id, WorkflowStep.node_id == node_id)
    ).first()
    if not step:
        raise ValueError(f"节点 {node_id} 不存在")
    if run.status != "waiting_input" or step.status != "waiting_input":
        raise ValueError(f"节点当前状态 {step.status} 不可操作（run={run.status}）")
    handler = COMPLETE_HANDLERS.get(step.node_type)
    if handler is None:
        raise ValueError(f"节点 {step.node_type} 不是人工节点")
    step.status = "running"
    db.commit()
    output = handler(db, run, step, payload or {}, user)
    step.output_json = output
    step.status = "succeeded"
    step.finished_at = _now()
    run.status = "running"
    db.commit()
    return advance(db, run, user)


def retry_run(db: Session, run: WorkflowRun, user) -> WorkflowRun:
    """从失败节点重试：失败步骤与下游 pending 重置。"""
    if run.status != "failed":
        raise ValueError("只有失败的运行可以重试")
    for step in _steps(db, run):
        if step.status == "failed":
            step.status = "pending"
            step.error = None
    run.status = "running"
    run.error = None
    db.commit()
    return advance(db, run, user)
