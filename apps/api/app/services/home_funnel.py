"""今日工作台的内容漏斗：选题 → 作品 → 发布 → 效果，读取各业务表的现有记录，不另存副本。"""

from collections import defaultdict
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import (
    ContentAccount,
    ContentAsset,
    ContentOpportunity,
    ContentPersona,
    ContentProject,
    ContentUnit,
    PerformanceObservation,
    PublishedContentRecord,
    User,
    utcnow,
)
from .account_metrics_import import channel_label
from .published_history import utc

# 各平台的「看过的人次」叫法不同：抖音、视频号是播放，公众号是阅读，小红书、B站是观看/播放。
VIEW_KEYS = ("plays", "reads", "views")
ENGAGE_KEYS = ("likes", "comments", "shares", "favorites")
PENDING_TOPICS = {"new", "watching", "qualified"}
DROPPED_TOPICS = {"dismissed", "archived"}


def _stage(unit: ContentUnit) -> str:
    if unit.status == "published":
        return "published"
    if unit.status == "finalized":
        return "finalized"
    return "in_progress"


def _blank() -> dict:
    return {"topics": 0, "topics_adopted": 0, "topics_pending": 0, "topics_dropped": 0,
            "in_progress": 0, "finalized": 0, "published": 0,
            "posts": 0, "posts_studio": 0, "posts_with_metrics": 0, "views": 0, "engagements": 0, "followers_gained": 0}


def home_funnel(db: Session, user: User, days: int) -> dict:
    since = utcnow() - timedelta(days=days) if days else None
    personas = {p.id: p.name for p in db.scalars(select(ContentPersona).where(ContentPersona.owner_user_id == user.id))}
    rows: dict = defaultdict(_blank)

    topics = select(ContentOpportunity).where(ContentOpportunity.owner_user_id == user.id)
    if since:
        topics = topics.where(ContentOpportunity.created_at >= since)
    for item in db.scalars(topics):
        row = rows[item.persona_id]
        row["topics"] += 1
        if item.status == "converted":
            row["topics_adopted"] += 1
        elif item.status in PENDING_TOPICS:
            row["topics_pending"] += 1
        elif item.status in DROPPED_TOPICS:
            row["topics_dropped"] += 1

    # 搜索推广的作品不走角色选题，单独不计入漏斗。
    units = (select(ContentUnit).join(ContentProject, ContentProject.id == ContentUnit.project_id)
             .where(ContentProject.owner_user_id == user.id, ContentUnit.lifecycle == "active",
                    ContentUnit.status != "archived", ContentUnit.production_domain.in_(("persona", "product"))))
    if since:
        units = units.where(ContentUnit.created_at >= since)
    domains = {"persona": _blank(), "product": _blank()}
    for unit in db.scalars(units):
        stage = _stage(unit)
        rows[unit.persona_id][stage] += 1
        domains[unit.production_domain][stage] += 1

    records = (select(PublishedContentRecord, ContentAccount.persona_id, ContentAsset.content_unit_id)
               .outerjoin(ContentAccount, ContentAccount.id == PublishedContentRecord.content_account_id)
               .outerjoin(ContentAsset, ContentAsset.id == PublishedContentRecord.content_asset_id)
               .where(PublishedContentRecord.owner_user_id == user.id, PublishedContentRecord.status == "active"))
    if since:
        records = records.where(PublishedContentRecord.published_at >= since)
    posts = {record.id: (record, persona_id, unit_id) for record, persona_id, unit_id in db.execute(records)}

    latest: dict = defaultdict(dict)
    last_observed = None
    if posts:
        observations = db.scalars(select(PerformanceObservation).where(
            PerformanceObservation.published_content_id.in_(posts), PerformanceObservation.observation_kind == "metric",
            PerformanceObservation.numeric_value.is_not(None)).order_by(PerformanceObservation.observed_at, PerformanceObservation.id)).all()
        superseded = {o.supersedes_id for o in observations if o.supersedes_id}
        for o in observations:
            if o.id in superseded:
                continue
            latest[o.published_content_id][o.metric_key] = o.numeric_value
            observed = utc(o.observed_at)
            last_observed = observed if not last_observed or observed > last_observed else last_observed

    channels: dict = defaultdict(lambda: {"posts": 0, "views": 0, "engagements": 0, "followers_gained": 0})
    works = []
    for record_id, (record, persona_id, unit_id) in posts.items():
        values = latest.get(record_id, {})
        views = next((values[key] for key in VIEW_KEYS if key in values), None)
        engagements = sum(values.get(key, 0) for key in ENGAGE_KEYS)
        followers = values.get("followers_gained", 0)
        row, channel = rows[persona_id], channels[record.channel]
        row["posts"] += 1
        row["posts_studio"] += record.origin == "studio"
        channel["posts"] += 1
        if values:
            row["posts_with_metrics"] += 1
        for target in (row, channel):
            target["views"] += views or 0
            target["engagements"] += engagements
            target["followers_gained"] += followers
        works.append({"id": record.id, "title": record.title or "（无标题）", "channel": record.channel,
                      "channel_label": channel_label(record.channel), "persona_id": persona_id,
                      "persona_name": personas.get(persona_id), "content_unit_id": unit_id, "origin": record.origin,
                      "published_at": utc(record.published_at).isoformat() if record.published_at else None,
                      "views": views, "engagements": engagements if values else None,
                      "followers_gained": followers if values else None, "has_metrics": bool(values)})

    totals = _blank()
    for row in rows.values():
        for key, value in row.items():
            totals[key] += value
    persona_rows = [{"persona_id": pid, "persona_name": personas.get(pid) or ("未关联角色" if pid is None else f"角色 #{pid}"), **row}
                    for pid, row in rows.items()]
    persona_rows.sort(key=lambda r: (r["persona_id"] is None, -r["views"], -r["published"], -r["topics"]))
    works.sort(key=lambda w: (w["views"] is None, -(w["views"] or 0)))
    return {
        "days": days,
        "since": since.isoformat() if since else None,
        "totals": totals,
        "domains": domains,
        "personas": persona_rows,
        "channels": sorted(({"channel": key, "channel_label": channel_label(key), **value} for key, value in channels.items()),
                           key=lambda c: -c["views"]),
        "top_works": works[:8],
        "posts_without_metrics": sum(1 for w in works if not w["has_metrics"]),
        "last_observed_at": last_observed.isoformat() if last_observed else None,
        "generated_at": utcnow().isoformat(),
    }
