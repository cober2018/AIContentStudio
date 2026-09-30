"""工作流画布执行引擎：DAG 拓扑推进 + 人工节点挂起续跑。

V1 PRD 2.0：节点执行统一经 content_harness registry 解析 plugin（版本钉死），
本文件不再新增平台 handler；旧 handler 全部薄包装为 builtin.*@1 插件，业务结果不变。
执行模型：同步推进（TASK_QUEUE_ENABLED 的异步模式留给 V2）；人工节点置
waiting_input 后返回，前端操作后调 complete 续跑；失败即停、可从失败节点重试。
"""

import hashlib
import json
import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import (
    ContentJob,
    ContentUnit,
    Draft,
    Fact,
    FactPack,
    TopicBrief,
    Workflow,
    WorkflowRun,
    WorkflowStep,
    WorkflowStepAttempt,
)
from .content_harness.contracts import NodeResult, WorkflowExecutionContext
from .content_harness.nodes import bootstrap_builtin_nodes, resolve_node_key

logger = logging.getLogger(__name__)

bootstrap_builtin_nodes()

HUMAN_NODE_TYPES = {"adopt_topic", "approve", "confirm_facts"}


def _now():
    return datetime.now(UTC)


def _channel_of(run: WorkflowRun, step: WorkflowStep) -> str | None:
    """R2-B1：target 解析——节点参数优先（catalog 实例化烘焙），run 参数兜底（共享 Bundle）。"""
    return (step.params_json or {}).get("channel") or (run.params_json or {}).get("channel")


def _form_of(run: WorkflowRun, step: WorkflowStep) -> str | None:
    return (step.params_json or {}).get("content_form") or (run.params_json or {}).get("content_form")


def canonical_checksum(payload) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()


def definition_checksum(definition: dict) -> str:
    return canonical_checksum(definition)


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
    doc, _facts, _created = connector_service.pull_endpoint(db, endpoint, user)
    source_ids = list((run.context_json or {}).get("source_ids") or []) + [doc.id]
    _ctx_update(run, source_ids=source_ids)
    return {"source_id": doc.id, "title": doc.title, "candidate_facts": _facts, "unchanged": _created}


def _h_extract_facts(db: Session, run: WorkflowRun, step: WorkflowStep, user) -> dict:
    """复用 sources 抽取逻辑 + 自动确认（工作流语境默认信任来源并确认，人工核对走 Source 页）。"""
    from ..routers.sources import extract_facts

    ctx = run.context_json or {}
    source_ids = step.params_json.get("source_ids") or ctx.get("source_ids") or []
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
        db.add(
            FactPackItem(
                fact_pack_id=pack.id,
                fact_id=f.id,
                sort_order=i,
                evidence_kind="fact",
                public_use_allowed=False,
                model_use_allowed=False,
            )
        )
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


def _h_confirm_facts_complete(db: Session, run: WorkflowRun, step: WorkflowStep, payload: dict, user) -> dict:
    """人工确认事实：payload {confirmed_ids, rejected_ids}；缺省全确认上游候选。

    状态落库后把「已确认的事实 id」写回 context（freeze 只认 confirmed）。
    """
    from ..models import FactStatus

    ctx = run.context_json or {}
    candidate_ids = ctx.get("fact_ids") or []
    confirmed_ids = [int(i) for i in (payload.get("confirmed_ids") or candidate_ids)]
    rejected_ids = {int(i) for i in (payload.get("rejected_ids") or [])}
    rows = db.scalars(select(Fact).where(Fact.id.in_(confirmed_ids))).all() if confirmed_ids else []
    kept = []
    for f in rows:
        if f.id in rejected_ids:
            f.status = FactStatus.rejected.value
            continue
        f.status = FactStatus.confirmed.value
        kept.append(f.id)
    _ctx_update(run, fact_ids=kept)
    return {"confirmed": len(kept), "rejected": len(rejected_ids)}


def _h_generate(db: Session, run: WorkflowRun, step: WorkflowStep, user) -> dict:
    from ..services.content_harness import channel_registry
    from ..services.generation.orchestrator import create_jobs_for_topic
    from ..tasks import worker_tasks

    channel = _channel_of(run, step)
    if not channel:
        raise ValueError("生成节点缺少 channel（节点参数或 run 参数）")
    content_form = _form_of(run, step)
    channel_registry.resolve_content_form(db, channel, content_form)  # 未知渠道在这里失败（ChannelRegistryError ⊂ ValueError）
    topic_id = run.params_json.get("topic_id") or run.context_json.get("topic_id")
    if not topic_id:
        raise ValueError("生成需要 topic_id（人工采纳或启动参数）")
    topic = db.get(TopicBrief, topic_id)
    if not topic:
        raise ValueError(f"Topic {topic_id} 不存在")

    import time as _time

    jobs = create_jobs_for_topic(db, topic, [{"channel": channel, "content_form": content_form}], workflow_run_id=run.id)
    # 异步模式消息先于本事务 commit 到达 worker：必须先落库 job 行再入队，否则 worker 查无此 job
    db.commit()
    statuses = []
    for job in jobs:
        status = worker_tasks.dispatch_generation(db, job.id)
        statuses.append(status)
    # 异步（TASK_QUEUE_ENABLED）时 dispatch 返回 queued：轮询到终态为止，画布不区分两种模式
    deadline = _time.monotonic() + 420
    while statuses and statuses[-1] == "queued" and _time.monotonic() < deadline:
        _time.sleep(2)
        db.expire_all()
        fresh = db.get(ContentJob, jobs[0].id)
        if fresh is None:
            break
        statuses[-1] = fresh.status
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


def _latest_draft_id(db: Session, run: WorkflowRun, channel: str) -> int:
    """该渠道 content_job 的最新 revision draft（人工修稿后 context 里的旧 id 会过期）。"""
    job_id = (run.context_json.get("jobs") or {}).get(channel, {}).get("job_id")
    if not job_id:
        raise ValueError(f"渠道 {channel} 没有生成任务")
    latest = db.scalars(
        select(Draft.id).where(Draft.content_job_id == job_id).order_by(Draft.revision_no.desc()).limit(1)
    ).first()
    if not latest:
        raise ValueError(f"渠道 {channel} 没有可用的草稿")
    return latest


def _h_fact_check(db: Session, run: WorkflowRun, step: WorkflowStep, user) -> dict:
    from ..routers.generate import run_fact_check as run_fc

    channel = _channel_of(run, step)
    draft_id = _latest_draft_id(db, run, channel)
    if not draft_id:
        raise ValueError(f"渠道 {channel} 没有可校验的草稿")
    result = run_fc(draft_id=draft_id, db=db, user=user)
    return {
        "draft_id": draft_id,
        "result": result.get("result"),
        "blockers": (result.get("stats") or {}).get("blockers", 0),
        "warnings": (result.get("stats") or {}).get("warnings", 0),
    }


def _h_discoverability_post(db: Session, run: WorkflowRun, step: WorkflowStep, user) -> dict:
    """R3-2：SEO 审查作为 Workflow 独立 Stage（§6.15）。

    profile 声明了 discoverability_profile 才生成 post 报告（状态如实落库，
    incomplete 不阻断——Candidate 会冻结报告）；未声明的形态节点空转跳过。
    """
    from ..services import discoverability as disco
    from ..services.content_harness.channel_registry import ChannelRegistryError, resolve_content_form

    channel = _channel_of(run, step)
    draft_id = _latest_draft_id(db, run, channel)
    if not draft_id:
        raise ValueError(f"渠道 {channel} 没有可审查的草稿")
    try:
        spec = resolve_content_form(db, channel, _form_of(run, step))
    except ChannelRegistryError as exc:
        raise ValueError(str(exc)) from exc
    if not spec.discoverability_profile:
        return {"ran": False, "reason": f"渠道 {channel} 未声明 discoverability_profile"}
    draft = db.get(Draft, draft_id)
    report = disco.run_post_draft(db, draft, user)
    db.commit()
    return {"ran": True, "report_id": report.id, "status": report.status, "draft_id": draft_id}


def _h_humanize_polish(db: Session, run: WorkflowRun, step: WorkflowStep, user) -> dict:
    """去 AI 味二次精炼（humanizer-zh 规则注入 system）：全文改写为新 revision，事实数字不动。"""
    import asyncio

    from ..routers.generate import DraftUpdateIn, update_draft
    from ..services.generation.providers import GenerateRequest, get_provider
    from ..services.writing_pipeline import HUMANIZE_SYSTEM

    channel = _channel_of(run, step)
    draft_id = _latest_draft_id(db, run, channel)
    draft = db.get(Draft, draft_id)
    provider = get_provider("rewrite")
    if provider.name == "mock":
        return {"draft_id": draft_id, "humanized": False, "note": "mock 跳过精炼"}
    request = GenerateRequest(
        purpose="humanize",
        channel=channel,
        system_prompt=HUMANIZE_SYSTEM,
        user_prompt=draft.body,
    )
    result = asyncio.run(provider.generate_text(request))
    cleaned = result.strip()
    if not cleaned or len(cleaned) < len(draft.body) * 0.5:
        raise ValueError("去 AI 味改写结果异常（过短），保留原稿人工处理")
    updated = update_draft(
        draft_id=draft_id, payload=DraftUpdateIn(body=cleaned), db=db, user=user
    )
    return {"draft_id": updated["id"], "humanized": True, "revision": updated["revision_no"]}


def _h_content_censor(db: Session, run: WorkflowRun, step: WorkflowStep, user) -> dict:
    """合规审查（content-censor）：RED 自动合规改写为新 revision + 补平台免责声明。"""
    from ..routers.generate import DraftUpdateIn, update_draft
    from ..services.writing_pipeline import censor_text

    channel = _channel_of(run, step) or "wechat"
    platform = {"wechat": "wechat", "xiaohongshu": "xiaohongshu", "douyin": "douyin"}.get(channel, "general")
    draft_id = _latest_draft_id(db, run, channel)
    draft = db.get(Draft, draft_id)
    report = censor_text(draft.body, platform=platform)
    applied = False
    if report.get("patched_text"):
        updated = update_draft(
            draft_id=draft_id, payload=DraftUpdateIn(body=report["patched_text"]), db=db, user=user
        )
        draft_id = updated["id"]
        applied = True
    if report["result"] == "blocker":
        reds = "、".join(i.get("word") or "" for i in report["issues"] if i.get("level") == "RED")
        raise ValueError(f"合规审查 RED 未清零（{reds}），已自动改写仍命中，需人工处理")
    return {
        "draft_id": draft_id,
        "result": report["result"],
        "red": sum(1 for i in report["issues"] if i.get("level") == "RED"),
        "yellow": sum(1 for i in report["issues"] if i.get("level") == "YELLOW"),
        "applied_rewrite": applied,
        "disclaimer_appended": report.get("disclaimer_appended", False),
    }


def _h_generate_cover(db: Session, run: WorkflowRun, step: WorkflowStep, user) -> dict:
    """AI 封面（wewrite image-gen，16:9 深色科技风）；失败降级不阻断，发布时回退占位图。"""
    from .. import runtime_config
    from ..models import ContentJob
    from ..services.asset_media import MEDIA_ROOT
    from ..services.writing_pipeline import generate_cover_image

    image_cfg = runtime_config.get_runtime(runtime_config.KEY_IMAGE) or {}
    if not image_cfg.get("enabled"):
        return {"generated": False, "skipped": "AI 生图未启用（设置 → 模型服务 → AI 生图）"}
    channel = _channel_of(run, step) or "wechat"
    job_id = (run.context_json.get("jobs") or {}).get(channel, {}).get("job_id")
    prompt = step.params_json.get("prompt")
    if not prompt and job_id:
        job = db.get(ContentJob, job_id)
        structured = (db.get(Draft, _latest_draft_id(db, run, channel)) if job else None)
        data = structured.structured_json if structured else {}
        prompt = (data.get("image_suggestions") or data.get("image_prompts") or [""])[0]
    prompt = prompt or "16:9 深色科技风封面：发光数据流、全息数仓架构，无文字"
    out = MEDIA_ROOT / "working" / f"run{run.id}_{channel}_cover.png"
    generated = generate_cover_image(prompt, out)
    covers = {**((run.context_json or {}).get("covers") or {})}
    if generated:
        covers[channel] = str(out)
        _ctx_update(run, covers=covers)
    result = {"generated": generated, "path": str(out) if generated else None, "prompt": prompt[:80]}
    if generated and run.content_unit_id is not None and out.is_file():
        from ..services import materials as materials_service

        material = materials_service.create_material(db, kind="image", title=f"工作流封面 · {channel}", created_by=user.email)
        revision = materials_service.create_revision(
            db, material,
            content=out.read_bytes(), suffix=".png", declared_mime="image/png",
            source_kind="ai_generated", rights_status="review_required", public_use_allowed=False,
            model_use_allowed=False, prompt_text=prompt, created_by=user.email,
        )
        result["material_revision_id"] = revision.id
    return result


def _h_approve(db: Session, run: WorkflowRun, step: WorkflowStep, payload: dict, user) -> dict:
    """人工批准：提交审核 + 批准（沿用既有 409 闸门），产出 Asset。"""
    from fastapi import HTTPException

    from ..routers.generate import submit_for_review
    from ..routers.reviews import DecisionIn, approve

    channel = _channel_of(run, step)
    draft_id = _latest_draft_id(db, run, channel)
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

    channel = _channel_of(run, step)
    asset_id = (run.context_json.get("assets") or {}).get(channel)
    if not asset_id:
        raise ValueError(f"渠道 {channel} 没有已批准的资产可导出")
    files = []
    for fmt in step.params_json.get("formats") or ["md"]:
        result = export_asset(asset_id=asset_id, payload=ExportIn(fmt=fmt), db=db, user=user)
        files.append(result["filename"])
    return {"asset_id": asset_id, "files": files}


def _h_publish_wechat(db: Session, run: WorkflowRun, step: WorkflowStep, user) -> dict:
    # Retain the historical node key, not its unscoped remote execution path.
    raise ValueError("旧工作流禁止直接发布；请经 Delivery Router 完成精确账号验证和交付授权")


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


# 旧 handler 中央表：仅供兼容参考与插件包装，引擎执行路径已改为 registry resolve（D6）
HANDLERS = {
    "connector_pull": _h_connector_pull,
    "extract_facts": _h_extract_facts,
    "factpack_freeze": _h_factpack_freeze,
    "suggest_topics": _h_suggest_topics,
    "generate": _h_generate,
    "humanize_polish": _h_humanize_polish,
    "content_censor": _h_content_censor,
    "generate_cover": _h_generate_cover,
    "fact_check": _h_fact_check,
    "discoverability_post": _h_discoverability_post,
    "export": _h_export,
    "publish_wechat": _h_publish_wechat,
}

# 人工节点的完成动作（complete 时调用）；其余节点无 complete 语义
COMPLETE_HANDLERS = {
    "adopt_topic": _h_adopt_topic_complete,
    "approve": _h_approve,
    "confirm_facts": _h_confirm_facts_complete,
}


# ---------- 引擎：拓扑推进 ----------


def _steps(db: Session, run: WorkflowRun) -> list[WorkflowStep]:
    return list(db.scalars(select(WorkflowStep).where(WorkflowStep.run_id == run.id).order_by(WorkflowStep.id)))


def _resolve_step_plugin(db: Session, run: WorkflowRun, step: WorkflowStep):
    """D6：节点执行统一走 registry resolve。

    优先用 step 上钉死的 plugin key/version；历史 run 的 step 无记录时按节点定义
    （schema v2 plugin 字段 / schema v1 type 映射）解析并回写钉死。
    """
    from .content_harness import registry as plugin_registry
    from .content_harness.nodes import TYPE_TO_PLUGIN

    if step.plugin_key:
        return plugin_registry.resolve("node", step.plugin_key, step.plugin_version)
    node = next(
        (
            n
            for n in (db.get(Workflow, run.workflow_id).definition_json or {}).get("nodes", [])
            if n.get("id") == step.node_id
        ),
        {},
    )
    try:
        key, version = resolve_node_key(node or {"type": step.node_type})
    except ValueError:
        # 节点定义缺失时兜底：直接把 step.node_type 当 plugin key（自定义注册场景）
        key, version = TYPE_TO_PLUGIN.get(step.node_type, step.node_type), "1"
    step.plugin_key = key
    step.plugin_version = version
    return plugin_registry.resolve("node", key, version)


def _node_config(db: Session, run: WorkflowRun, node_id: str) -> dict:
    return next((item for item in (db.get(Workflow, run.workflow_id).definition_json or {}).get("nodes", []) if item.get("id") == node_id), {})


def _prepare_step_params(db: Session, run: WorkflowRun, step: WorkflowStep) -> None:
    definition = (db.get(Workflow, run.workflow_id).definition_json or {})
    node = next((item for item in definition.get("nodes", []) if item.get("id") == step.node_id), {})
    if run.content_unit_id is not None:
        from ..models import ContentUnit
        from .project_workflows import resolve_placeholders

        unit = db.get(ContentUnit, run.content_unit_id)
        if unit is None:
            raise ValueError("项目内容单元不存在")
        resolved_config = resolve_placeholders(node.get("config") or {}, project_id=unit.project_id, unit_id=unit.id, run_params=run.params_json or {})
        step.params_json = {**(step.params_json or {}), **resolved_config}
    mapping = node.get("input_mapping") or {}
    if mapping:
        upstream = {row.node_id: row for row in _steps(db, run)}
        inputs = {}
        for name, ref in mapping.items():
            if isinstance(ref, dict) and "node_id" in ref:
                source = upstream.get(ref["node_id"])
                if source is None or source.status != "succeeded" or ref.get("output") not in (source.output_json or {}):
                    raise ValueError(f"输入映射 {name} 的上游输出不可用")
                inputs[name] = source.output_json[ref["output"]]
            else:
                inputs[name] = ref
        step.params_json = {**(step.params_json or {}), "inputs": inputs}


def _execute_node(db: Session, run: WorkflowRun, step: WorkflowStep, user, *, payload: dict | None = None) -> dict:
    _prepare_step_params(db, run, step)
    node = _node_config(db, run, step.node_id)
    if run.content_unit_id is not None:
        from .project_workflows import validate_ai_executor_selection

        validate_ai_executor_selection(node)
    plugin = _resolve_step_plugin(db, run, step)
    ctx = WorkflowExecutionContext(db=db, run=run, step=step, config=step.params_json or {})
    if payload is not None:
        result: NodeResult = plugin.complete(db, ctx, payload, user)
    else:
        result = plugin.execute(db, ctx, step.params_json or {}, user)
    output = dict(result.output or {})
    for alias, source_key in (node.get("output_mapping") or {}).items():
        if source_key not in output:
            raise ValueError(f"输出映射 {alias} 引用了不存在的结果字段 {source_key}")
        output[alias] = output[source_key]
    step.input_hash = canonical_checksum(step.params_json or {})
    step.output_hash = canonical_checksum(output)
    return output


def _fail_step(db: Session, run: WorkflowRun, step: WorkflowStep, exc: Exception, user=None) -> WorkflowRun:
    db.rollback()
    fresh = db.get(WorkflowStep, step.id)
    node = _node_config(db, run, fresh.node_id)
    policy = node.get("failure_policy", "stop") if run.content_unit_id is not None else "stop"
    if policy in {"skip", "wait_human"}:
        fresh.status = "skipped" if policy == "skip" else "waiting_input"
        fresh.error = str(exc)[:500]
        fresh.finished_at = _now()
        _record_attempt(db, fresh, "failed", error=str(exc))
        run.status = "running" if policy == "skip" else "waiting_input"
        run.error = f"节点「{fresh.label or fresh.node_id}」等待处理：{str(exc)[:300]}" if policy == "wait_human" else None
        db.commit()
        return advance(db, run, user) if policy == "skip" else run
    fresh.status = "failed"
    fresh.error = str(exc)[:500]
    fresh.finished_at = _now()
    _record_attempt(db, fresh, "failed", error=str(exc))
    run.status = "failed"
    run.error = f"节点「{fresh.label or fresh.node_id}」失败：{str(exc)[:300]}"
    db.commit()
    return run


def _record_attempt(db: Session, step: WorkflowStep, status: str, *, error: str | None = None) -> int:
    """R2-H7：节点每次终态执行沉淀一行不可变审计（含 output）。

    WorkflowStep 只保留「当前」输出；rerun 覆盖前旧 output 已在本表——新旧 output 均可审计。
    """
    from sqlalchemy import func

    last = db.scalar(
        select(func.max(WorkflowStepAttempt.attempt_no)).where(WorkflowStepAttempt.step_id == step.id)
    )
    attempt_no = (last or 0) + 1
    if (step.attempt_no or 0) < attempt_no:
        step.attempt_no = attempt_no
    attempt = WorkflowStepAttempt(
            step_id=step.id,
            run_id=step.run_id,
            node_id=step.node_id,
            plugin_key=step.plugin_key,
            plugin_version=step.plugin_version,
            attempt_no=attempt_no,
            status=status,
            output_json=step.output_json or {},
            output_hash=step.output_hash,
            input_hash=step.input_hash,
            error=error[:2000] if error else None,
            created_at=_now(),
        )
    db.add(attempt)
    db.flush()
    return attempt.id


def advance(db: Session, run: WorkflowRun, user) -> WorkflowRun:
    """从当前断点推进：自动节点逐个执行，人工节点挂起，失败即停。"""
    from .content_harness import registry as plugin_registry

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
        skipped = [s for s in pending if any(steps[dep].status == "skipped" for dep in deps.get(s.node_id, []) if dep in steps)]
        if skipped:
            for step in skipped:
                step.status = "skipped"
                step.stale_reason = "上游节点已跳过"
            db.commit()
            continue
        ready = [
            s
            for s in pending
            if all(steps[dep].status == "succeeded" for dep in deps.get(s.node_id, []) if dep in steps)
        ]
        if not ready:
            # 无可执行节点且仍有 pending → 挂起在人工节点（status 应已置 waiting_input）
            return run
        step = ready[0]
        if run.content_unit_id is not None:
            node = _node_config(db, run, step.node_id)
            if node.get("enabled") is False:
                step.status = "skipped"
                step.stale_reason = "节点已停用"
                db.commit()
                continue
            condition = node.get("condition") or {}
            if condition:
                try:
                    _prepare_step_params(db, run, step)
                    if (step.params_json or {}).get("inputs", {}).get(condition["input"]) != condition["equals"]:
                        step.status = "skipped"
                        step.stale_reason = "执行条件未满足"
                        db.commit()
                        continue
                except Exception as exc:
                    return _fail_step(db, run, step, exc, user)
        try:
            _resolve_step_plugin(db, run, step)
            descriptor = plugin_registry.descriptor("node", step.plugin_key, step.plugin_version)
        except Exception as exc:  # noqa: BLE001 未知 plugin：与旧“未知节点类型”一致按节点失败处理
            return _fail_step(db, run, step, exc, user)
        # 人工节点以 plugin descriptor 为准（D6）；v1 type 集合兜底历史定义
        if descriptor.human_gate or step.node_type in HUMAN_NODE_TYPES:
            step.status = "waiting_input"
            run.status = "waiting_input"
            db.commit()
            return run
        step.status = "running"
        step.started_at = _now()
        run.status = "running"
        db.commit()
        try:
            output = _execute_node(db, run, step, user)
            step.output_json = output
            step.status = "succeeded"
            step.finished_at = _now()
            attempt_id = _record_attempt(db, step, "succeeded")
            from .project_outputs import associate_step_output

            associate_step_output(db, run, step, attempt_id)
            db.commit()
            logger.info("workflow_step_ok run=%s node=%s plugin=%s", run.id, step.node_id, step.plugin_key)
        except Exception as exc:  # noqa: BLE001 节点失败即停，可从失败节点重试
            return _fail_step(db, run, step, exc, user)


def start_run(db: Session, workflow: Workflow, params: dict | None, user, *, advance_now: bool = True, content_unit_id: int | None = None) -> WorkflowRun:
    # D17 preflight：技能缺失在启动前暴露，而不是运行中 ImportError
    from .content_harness.skill_runtime import preflight_workflow

    problems = preflight_workflow(db, workflow.definition_json or {})
    if problems:
        raise ValueError("Workflow preflight 失败：" + "；".join(problems))

    identity_snapshot_id = None
    if content_unit_id is not None:
        from .content_identity import hierarchy

        unit = db.get(ContentUnit, content_unit_id)
        if unit is None or unit.status == "archived":
            raise ValueError("已归档或不存在的内容单元不可启动新运行")
        hierarchy(db, user, persona_id=unit.persona_id, account_id=unit.account_id, series_id=unit.series_id, mutable=True)
        identity_snapshot_id = unit.identity_snapshot_id

    p = params or {}
    topic_id = p.get("topic_id")
    try:
        topic_id = int(topic_id) if topic_id is not None else None
    except (TypeError, ValueError):
        topic_id = None
    run = WorkflowRun(
        workflow_id=workflow.id,
        content_unit_id=content_unit_id,
        identity_snapshot_id=identity_snapshot_id,
        params_json=p,
        context_json={},
        # D5：启动时冻结 definition 身份与目标上下文
        topic_id=topic_id,
        channel=p.get("channel"),
        content_form=p.get("content_form"),
        workflow_key=workflow.workflow_key,
        workflow_version=workflow.version,
        definition_checksum=workflow.checksum or definition_checksum(workflow.definition_json),
    )
    db.add(run)
    db.flush()
    from .content_harness.nodes import node_config_of

    for node in workflow.definition_json.get("nodes", []):
        try:
            plugin_key, plugin_version = resolve_node_key(node)
        except ValueError:
            plugin_key, plugin_version = None, None
        db.add(
            WorkflowStep(
                run_id=run.id,
                node_id=node["id"],
                node_type=node.get("kind") or node.get("type") or node.get("plugin") or "",
                label=node.get("label"),
                # R4-B1：schema v2 config 为真源（优先），v1 params 兼容合并
                params_json=node_config_of(node),
                plugin_key=plugin_key,
                plugin_version=plugin_version,
            )
        )
    db.commit()
    if not advance_now:
        # R2-B1：异步模式下由 worker 任务推进（HTTP 请求不阻塞等待真实模型）
        return run
    return advance(db, run, user)


def complete_node(db: Session, run: WorkflowRun, node_id: str, payload: dict, user) -> WorkflowRun:
    step = db.scalars(
        select(WorkflowStep).where(WorkflowStep.run_id == run.id, WorkflowStep.node_id == node_id)
    ).first()
    if not step:
        raise ValueError(f"节点 {node_id} 不存在")
    if run.status != "waiting_input" or step.status != "waiting_input":
        raise ValueError(f"节点当前状态 {step.status} 不可操作（run={run.status}）")
    node = _node_config(db, run, node_id)
    if run.content_unit_id is not None and node.get("failure_policy") == "wait_human" and step.error:
        action = (payload or {}).get("action")
        if action not in {"retry", "skip"}:
            raise ValueError("失败节点需要人工选择 retry 或 skip")
        step.status = "pending" if action == "retry" else "skipped"
        step.error = None
        run.status = "running"
        run.error = None
        db.commit()
        return advance(db, run, user)
    plugin = _resolve_step_plugin(db, run, step)
    if not hasattr(plugin, "complete"):
        raise ValueError(f"节点 {step.node_type} 不是人工节点")
    step.status = "running"
    db.commit()
    try:
        output = _execute_node(db, run, step, user, payload=payload or {})
    except Exception:
        # 操作被闸门拒绝（如 blocker 未解决）：节点恢复等待态，人工处理后可再次提交
        db.rollback()
        step.status = "waiting_input"
        db.commit()
        raise
    step.output_json = output
    step.status = "succeeded"
    step.finished_at = _now()
    attempt_id = _record_attempt(db, step, "succeeded")
    from .project_outputs import associate_step_output

    associate_step_output(db, run, step, attempt_id)
    run.status = "running"
    db.commit()
    return advance(db, run, user)


def retry_run(db: Session, run: WorkflowRun, user) -> WorkflowRun:
    """从失败节点重试：失败步骤与下游 pending 重置。"""
    if run.status != "failed":
        raise ValueError("只有失败的运行可以重试")
    from ..models import ContentAsset

    asset_ids = ((run.context_json or {}).get("assets") or {}).values()
    if any(
        asset and asset.mother_revision_id
        for asset_id in asset_ids
        for asset in [db.get(ContentAsset, asset_id)]
    ):
        raise ValueError("M1 人工交付不允许通过旧工作流重试远端副作用")
    for step in _steps(db, run):
        if step.status == "failed":
            step.status = "pending"
            step.error = None
            step.output_json = {}
            step.output_hash = None
    run.status = "running"
    run.error = None
    db.commit()
    return advance(db, run, user)


# ---------- Node-level Rerun（D27/Phase 6）----------


def _definition_of(db: Session, run: WorkflowRun) -> dict:
    return (db.get(Workflow, run.workflow_id).definition_json or {})


def _downstream(definition: dict, node_id: str) -> list[str]:
    """BFS 后继（不含自身）。"""
    adj: dict[str, list[str]] = {}
    for edge in definition.get("edges", []):
        adj.setdefault(edge["from"], []).append(edge["to"])
    seen: list[str] = []
    queue = list(adj.get(node_id, []))
    while queue:
        current = queue.pop(0)
        if current in seen:
            continue
        seen.append(current)
        queue.extend(adj.get(current, []))
    return seen


def _resolve_or_none(db: Session, run: WorkflowRun, step: WorkflowStep):
    from .content_harness import registry as plugin_registry

    try:
        plugin = _resolve_step_plugin(db, run, step)
        descriptor = plugin_registry.descriptor("node", step.plugin_key, step.plugin_version)
        return plugin, descriptor
    except Exception:  # noqa: BLE001
        return None, None


def rerun_node(db: Session, run: WorkflowRun, node_id: str, user) -> WorkflowRun:
    """Rerun Node：上游不变，当前节点新 attempt；output hash 变化 → downstream 标 stale（不自动重跑）。"""

    step = db.scalars(select(WorkflowStep).where(WorkflowStep.run_id == run.id, WorkflowStep.node_id == node_id)).first()
    if not step:
        raise ValueError(f"节点 {node_id} 不存在")
    if run.status == "canceled":
        raise ValueError("已取消的运行不可重跑")
    if run.content_unit_id is not None:
        node = _node_config(db, run, node_id)
        if node.get("enabled") is False:
            raise ValueError("已停用的节点不可单独运行")
        dependency_ids = [edge["from"] for edge in _definition_of(db, run).get("edges", []) if edge["to"] == node_id]
        statuses = {item.node_id: item.status for item in _steps(db, run)}
        if any(statuses.get(dep) != "succeeded" for dep in dependency_ids):
            raise ValueError("上游节点尚未成功，不能单独运行")
    _plugin_obj, descriptor = _resolve_or_none(db, run, step)
    if descriptor is None:
        raise ValueError(f"节点 {node_id} 无法解析 plugin")
    if descriptor.side_effect:
        raise ValueError("远端副作用节点禁止泛化重跑；请通过 Delivery reconciliation/retry 契约处理")
    if descriptor.human_gate:
        raise ValueError("人工节点须通过完成人工步骤操作")

    old_output_hash = step.output_hash
    old_data_checksum = (step.output_json or {}).get("data_checksum")
    step.attempt_no = (step.attempt_no or 0) + 1
    step.status = "running"
    step.error = None
    step.stale_reason = None
    step.output_json = {}
    step.output_hash = None
    run.status = "running"
    db.commit()
    try:
        output = _execute_node(db, run, step, user)
    except Exception as exc:  # noqa: BLE001
        return _fail_step(db, run, step, exc, user)
    step.output_json = output
    step.status = "succeeded"
    step.finished_at = _now()
    new_data_checksum = output.get("data_checksum")
    changed = (old_data_checksum != new_data_checksum) if old_data_checksum is not None and new_data_checksum is not None else bool(old_output_hash) and step.output_hash != old_output_hash
    marked = 0
    if changed:
        from .content_harness.staleness import mark_workflow_downstream_stale

        marked = mark_workflow_downstream_stale(
            db, run, node_id, f"upstream {node_id} output changed (attempt #{step.attempt_no})"
        )
        logger.info("workflow_rerun run=%s node=%s downstream_stale=%s", run.id, node_id, marked)
    attempt_id = _record_attempt(db, step, "succeeded")
    from .project_outputs import associate_step_output

    associate_step_output(db, run, step, attempt_id)
    if run.content_unit_id is not None:
        statuses = {item.status for item in _steps(db, run)}
        run.status = "stale" if marked else "succeeded" if statuses == {"succeeded"} else "waiting_input" if "waiting_input" in statuses else "running"
        if run.status == "succeeded":
            run.finished_at = _now()
    db.commit()
    return run


def rerun_from_here(db: Session, run: WorkflowRun, node_id: str, user) -> WorkflowRun:
    """Rerun From Here：当前+downstream 置 pending 重跑；不回滚历史实体（产生新 Revision）。"""
    step = db.scalars(select(WorkflowStep).where(WorkflowStep.run_id == run.id, WorkflowStep.node_id == node_id)).first()
    if not step:
        raise ValueError(f"节点 {node_id} 不存在")
    if run.status == "canceled":
        raise ValueError("已取消的运行不可重跑")
    definition = _definition_of(db, run)
    affected = [node_id] + _downstream(definition, node_id)
    for s in _steps(db, run):
        if s.node_id not in affected:
            continue
        _, descriptor = _resolve_or_none(db, run, s)
        if descriptor is not None and descriptor.side_effect:
            raise ValueError(f"下游包含远端副作用节点（{s.node_id}），禁止 rerun-from-here 自动重跑；请走 Delivery 契约")
    for s in _steps(db, run):
        if s.node_id in affected:
            s.status = "pending"
            s.error = None
            s.stale_reason = None
            s.output_json = {}
            s.output_hash = None
    run.status = "running"
    run.error = None
    db.commit()
    return advance(db, run, user)
