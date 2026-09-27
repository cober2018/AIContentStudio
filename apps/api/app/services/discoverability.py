"""Discoverability 服务（D14/D15）：Pre/Post SEO 独立阶段。

- Pre：FactPack + Topic → 搜索意图/关键词/实体/问题/内容缺口/大纲建议；
- Post：Draft → 标题建议/关键词覆盖/描述/标签/alt 建议/issues；
- SEO 不自动改 Draft：apply 建议走新 Draft Revision（downstream 自然 stale）。
"""

from __future__ import annotations

import hashlib
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import (
    DiscoverabilityProfileVersion,
    DiscoverabilityReport,
    DiscoverabilityStage,
    DiscoverabilityStatus,
    FactPack,
    TopicBrief,
    User,
    utcnow,
)
from .generation.providers import GenerateRequest, get_provider, provider_model_name, record_run

PRE_FIELDS = ["search_intent", "primary_queries", "secondary_queries", "entities", "questions", "content_gaps", "outline_suggestions"]
POST_FIELDS = ["title_suggestions", "keyword_coverage", "description", "tags", "alt_suggestions", "issues"]

PRE_SYSTEM = """你是 SEO 与内容发现专家。只基于给定的事实包与选题信息输出 JSON，不引入外部事实。
输出 JSON 对象，字段：search_intent(字符串)、primary_queries(数组)、secondary_queries(数组)、entities(数组)、questions(数组)、content_gaps(数组)、outline_suggestions(数组)。"""

POST_SYSTEM = """你是 SEO 审查专家。只基于给定稿件正文与元数据输出 JSON，不得改写正文。
输出 JSON 对象，字段：title_suggestions(数组)、keyword_coverage(对象)、description(字符串)、tags(数组)、alt_suggestions(数组)、issues(数组)。"""


def _input_hash(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()


def seed_default_profiles(db: Session) -> int:
    """基础 discoverability profiles（幂等）。"""
    created = 0
    defaults = [
        ("seo.default", None, None, {"pre_fields": PRE_FIELDS, "post_fields": POST_FIELDS}),
        ("seo.wechat.article", "wechat", "article", {"title_length": [8, 64], "description_length": [40, 120], "pre_fields": PRE_FIELDS, "post_fields": POST_FIELDS}),
    ]
    for key, channel, form, config in defaults:
        exists = db.scalar(select(DiscoverabilityProfileVersion.id).where(DiscoverabilityProfileVersion.profile_key == key).limit(1))
        if exists:
            continue
        db.add(
            DiscoverabilityProfileVersion(
                profile_key=key, version=1, channel=channel or "", content_form=form,
                config_json=config, status="published",
                checksum=hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
            )
        )
        created += 1
    db.flush()
    return created


def _resolve_profile(db: Session, channel: str, content_form: str | None) -> DiscoverabilityProfileVersion | None:
    rows = db.scalars(
        select(DiscoverabilityProfileVersion).where(
            DiscoverabilityProfileVersion.status == "published",
            DiscoverabilityProfileVersion.channel.in_([channel, ""]),
        ).order_by(DiscoverabilityProfileVersion.id.desc())
    ).all()
    for row in rows:  # 渠道专属优先
        if row.channel == channel and (row.content_form in {None, content_form}):
            return row
    return next((r for r in rows if r.channel == ""), None)


def _run_llm(db: Session, *, system: str, user_prompt: str, purpose: str = "discoverability") -> tuple[dict, str | None, str | None]:
    provider = get_provider(purpose)
    request = GenerateRequest(purpose=purpose, channel="wechat", system_prompt=system, user_prompt=user_prompt)
    try:
        # 同步路由/worker 上下文无线程事件循环，沿用 orchestrator 的 asyncio.run 包装
        import asyncio

        result = asyncio.run(provider.generate_json(request))
        record_run(db, request, result)
        return result.data, provider.name, provider_model_name(purpose)
    except Exception as exc:
        record_run(db, request, None, error=str(exc))
        raise

def run_pre_topic(db: Session, topic: TopicBrief, user: User) -> DiscoverabilityReport:
    pack: FactPack = topic.fact_pack
    statements = [
        (item.snapshot_json or {}).get("statement") or (item.fact.statement if item.fact else "")
        for item in pack.items
    ]
    payload = {"topic": topic.title, "goal": topic.goal, "angle": topic.angle, "facts": [s for s in statements if s]}
    profile = _resolve_profile(db, channel="wechat", content_form="article")
    data, provider_name, model_name = _run_llm(db, system=PRE_SYSTEM, user_prompt=json.dumps(payload, ensure_ascii=False))
    report = {k: data.get(k) for k in PRE_FIELDS}
    complete = all(report.get(k) is not None for k in PRE_FIELDS)
    row = DiscoverabilityReport(
        topic_id=topic.id, mother_revision_id=None, draft_id=None,
        stage=DiscoverabilityStage.pre.value, channel="wechat", content_form="article",
        profile_version_id=profile.id if profile else None,
        input_hash=_input_hash(payload),
        status=DiscoverabilityStatus.ready.value if complete else DiscoverabilityStatus.incomplete.value,
        report_json=report, model_provider=provider_name, model_name=model_name,
        created_at=utcnow(),
    )
    db.add(row)
    db.flush()
    return row


def run_post_draft(db: Session, draft, user: User) -> DiscoverabilityReport:
    job = draft.content_job
    channel = job.channel
    content_form = getattr(draft, "content_form", None) or job.content_form
    payload = {
        "title": draft.title, "body": (draft.body or "")[:8000],
        "tags": (draft.structured_json or {}).get("tags"),
        "channel": channel, "content_form": content_form,
    }
    profile = _resolve_profile(db, channel=channel, content_form=content_form)
    data, provider_name, model_name = _run_llm(db, system=POST_SYSTEM, user_prompt=json.dumps(payload, ensure_ascii=False))
    report = {k: data.get(k) for k in POST_FIELDS}
    complete = all(report.get(k) is not None for k in POST_FIELDS)
    row = DiscoverabilityReport(
        topic_id=job.topic_brief_id, draft_id=draft.id,
        stage=DiscoverabilityStage.post.value, channel=channel, content_form=content_form,
        profile_version_id=profile.id if profile else None,
        input_hash=_input_hash(payload),
        status=DiscoverabilityStatus.ready.value if complete else DiscoverabilityStatus.incomplete.value,
        report_json=report, model_provider=provider_name, model_name=model_name,
        created_at=utcnow(),
    )
    db.add(row)
    db.flush()
    return row


def latest_report(db: Session, *, topic_id: int | None = None, draft_id: int | None = None, stage: str | None = None) -> DiscoverabilityReport | None:
    stmt = select(DiscoverabilityReport).order_by(DiscoverabilityReport.id.desc())
    if topic_id is not None:
        stmt = stmt.where(DiscoverabilityReport.topic_id == topic_id)
    if draft_id is not None:
        stmt = stmt.where(DiscoverabilityReport.draft_id == draft_id)
    if stage:
        stmt = stmt.where(DiscoverabilityReport.stage == stage)
    return db.scalars(stmt.limit(1)).first()


def reports_for(db: Session, *, topic_id: int | None = None, draft_id: int | None = None) -> list[DiscoverabilityReport]:
    stmt = select(DiscoverabilityReport).order_by(DiscoverabilityReport.id.desc()).limit(20)
    if topic_id is not None:
        stmt = stmt.where(DiscoverabilityReport.topic_id == topic_id)
    if draft_id is not None:
        stmt = stmt.where(DiscoverabilityReport.draft_id == draft_id)
    return list(db.scalars(stmt))


def _report_json(row: DiscoverabilityReport) -> dict:
    return {
        "id": row.id,
        "topic_id": row.topic_id,
        "draft_id": row.draft_id,
        "stage": row.stage,
        "channel": row.channel,
        "content_form": row.content_form,
        "profile_version_id": row.profile_version_id,
        "input_hash": row.input_hash,
        "status": row.status,
        "report": row.report_json or {},
        "model": {"provider": row.model_provider, "name": row.model_name},
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def apply_suggestion(
    db: Session,
    draft,
    report: DiscoverabilityReport,
    payload: dict,
    user: User,
) -> dict:
    """应用 SEO 建议 → 新 Draft Revision（D14：不自动改、不覆盖旧版本）。"""
    suggestions = (report.report_json or {}).get("title_suggestions") or []
    new_title = None
    if isinstance(payload.get("title_index"), int):
        if payload["title_index"] >= len(suggestions):
            raise ValueError(f"标题建议序号越界: {payload['title_index']}/{len(suggestions)}")
        new_title = str(suggestions[payload["title_index"]])
    elif payload.get("title"):
        new_title = str(payload["title"])
    if not new_title:
        raise ValueError("apply 需要 title 或 title_index（V1 只应用标题建议；正文/标签改动请人工编辑产生新 revision）")

    # R3-5：统一 fork——新 revision 继承 media use 并重建 document（不再直拷 document_json）
    from ..services.draft_fork import fork_draft_revision

    new_draft = fork_draft_revision(
        db,
        draft,
        title=new_title,
        created_by=user.email,
        status=draft.status if draft.status != "fact_check_failed" else "draft",
        reason=f"seo_apply:{report.id}",
    )
    db.commit()
    return {"new_draft_id": new_draft.id, "revision_no": new_draft.revision_no, "applied_title": new_title, "from_report": report.id}


def serialize(row: DiscoverabilityReport) -> dict:
    return _report_json(row)
