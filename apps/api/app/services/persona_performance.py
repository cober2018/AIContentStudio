"""效果复盘·角色表现：一个角色在各平台的作品按发布顺序排开，并标出业务上值得注意的事件。

只读已有的发布记录和效果录入；同一平台内互相比较（各平台口径不同），基准样本不足时不下相对结论。
"""

from collections import defaultdict
from datetime import timedelta
from statistics import median

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import AccountFollowerSnapshot, ContentAccount, ContentPersona, PerformanceObservation, PublishedContentRecord, User, utcnow
from .account_metrics_import import LOCAL_ZONE, channel_label
from .published_history import utc

VIEW_KEYS = ("plays", "reads", "views")
ENGAGE_KEYS = ("likes", "comments", "shares", "favorites")
RETENTION_KEYS = ("completion_rate", "read_completion_rate", "avg_play_ratio")
BOUNCE_KEYS = ("bounce_rate_2s", "bounce_rate_3s")
MIN_BASELINE = 5  # 同平台少于 5 条有数据的作品，不判断「高于/低于平常」
MILESTONES = (100_000, 10_000, 1_000)

# 事件类型：key → (名称, 说明, 倾向)。倾向 good / bad / info 只决定页面上的标记样式。
EVENT_TYPES = {
    "breakout": ("爆款", "播放/阅读达到该平台平常水平的 3 倍以上", "good"),
    "comment_peak": ("评论高峰", "评论数达到平常 3 倍以上，或两次录入之间新增 20 条以上", "good"),
    "follower_spike": ("涨粉高峰", "这条作品带来的关注达到平常 3 倍以上", "good"),
    "high_engagement": ("高互动", "互动率（点赞评论分享收藏 ÷ 播放）达到平常 2 倍以上", "good"),
    "strong_retention": ("留存好", "完播率/完读率/播放进度达到平常 1.5 倍以上", "good"),
    "long_tail": ("长尾回升", "发布 7 天后，两次录入之间播放/阅读又涨了一半以上", "good"),
    "milestone": ("里程碑", "单条作品播放/阅读首次过 1 千、1 万或 10 万", "good"),
    "new_channel": ("首发新平台", "这个角色在该平台的第一条作品", "info"),
    "comeback": ("断更后恢复", "距上一条发布超过 14 天", "info"),
    "hook_drop": ("开头流失", "开头几秒跳出率达到平常 1.5 倍以上", "bad"),
    "cold_start": ("冷启动不佳", "发布 3 天以上，播放/阅读不到平常的 30%", "bad"),
    "no_data": ("待复盘", "发布 2 天以上还没有效果数据", "bad"),
}


def _first(values: dict, keys) -> float | None:
    return next((values[k] for k in keys if k in values), None)


def _history(db: Session, record_ids) -> dict[int, list[tuple]]:
    """每条作品按录入日期排好的数值快照：[(录入时间, {指标: 值})]，同一天以最后一次为准。"""
    rows = db.scalars(select(PerformanceObservation).where(
        PerformanceObservation.published_content_id.in_(record_ids), PerformanceObservation.observation_kind == "metric",
        PerformanceObservation.numeric_value.is_not(None)).order_by(PerformanceObservation.observed_at, PerformanceObservation.id)).all()
    superseded = {r.supersedes_id for r in rows if r.supersedes_id}
    days: dict = defaultdict(dict)
    for r in rows:
        if r.id in superseded:
            continue
        at = utc(r.observed_at)
        day = at.astimezone(LOCAL_ZONE).date()
        slot = days[(r.published_content_id, day)]
        slot.setdefault("_at", at)
        slot["_at"] = max(slot["_at"], at)
        slot[r.metric_key] = r.numeric_value
    result: dict = defaultdict(list)
    for (rid, _day), values in sorted(days.items(), key=lambda item: (item[0][0], item[0][1])):
        at = values.pop("_at")
        merged = dict(result[rid][-1][1]) if result[rid] else {}
        merged.update(values)
        result[rid].append((at, merged))
    return result


def personas_overview(db: Session, user: User) -> list[dict]:
    counts: dict = defaultdict(int)
    for persona_id, in db.execute(select(ContentAccount.persona_id).join(
            PublishedContentRecord, PublishedContentRecord.content_account_id == ContentAccount.id).where(
            PublishedContentRecord.owner_user_id == user.id, PublishedContentRecord.status == "active")):
        counts[persona_id] += 1
    personas = db.scalars(select(ContentPersona).where(ContentPersona.owner_user_id == user.id)).all()
    items = [{"persona_id": p.id, "name": p.name, "posts": counts.get(p.id, 0)} for p in personas if p.status != "deleted"]
    return sorted(items, key=lambda p: (-p["posts"], p["persona_id"]))


def persona_followers(db: Session, user: User, persona_id: int) -> dict:
    """全网粉丝：这个角色每个账号最近一次录到的粉丝总数相加；没录过的账号单独列出，不当 0。"""
    accounts = db.scalars(select(ContentAccount).where(ContentAccount.owner_user_id == user.id,
                                                       ContentAccount.persona_id == persona_id, ContentAccount.status == "active")).all()
    snaps = db.scalars(select(AccountFollowerSnapshot).where(
        AccountFollowerSnapshot.content_account_id.in_([a.id for a in accounts]))
        .order_by(AccountFollowerSnapshot.observed_on)).all() if accounts else []
    by_account: dict = defaultdict(list)
    for s in snaps:
        by_account[s.content_account_id].append(s)
    rows = []
    for a in accounts:
        history = by_account.get(a.id, [])
        latest, first = (history[-1], history[0]) if history else (None, None)
        rows.append({"account_id": a.id, "account_name": a.name, "channel": a.platform_channel,
                     "channel_label": channel_label(a.platform_channel),
                     "followers": latest.followers if latest else None, "observed_on": latest.observed_on if latest else None,
                     "change": latest.followers - first.followers if latest and first is not latest else None,
                     "since": first.observed_on if latest and first is not latest else None,
                     "history": [{"observed_on": s.observed_on, "followers": s.followers} for s in history[-30:]]})
    rows.sort(key=lambda r: (r["followers"] is None, -(r["followers"] or 0)))
    known = [r for r in rows if r["followers"] is not None]
    # 按日期累加：每天取各账号截至当天最近一次的数，只在所有已录账号都有数之后才画（否则前段偏低）。
    days = sorted({s.observed_on for s in snaps})
    trend = []
    for day in days:
        values = [next((s.followers for s in reversed(by_account[r["account_id"]]) if s.observed_on <= day), None) for r in known]
        if all(v is not None for v in values):
            trend.append({"observed_on": day, "followers": sum(values)})
    return {"total": sum(r["followers"] for r in known) if known else None, "accounts": rows,
            "recorded": len(known), "missing": len(rows) - len(known),
            "last_observed_on": max((r["observed_on"] for r in known), default=None), "trend": trend}


def persona_timeline(db: Session, user: User, persona_id: int, days: int) -> dict:
    now = utcnow()
    since = now - timedelta(days=days) if days else None
    rows = db.execute(select(PublishedContentRecord, ContentAccount.name).join(
        ContentAccount, ContentAccount.id == PublishedContentRecord.content_account_id).where(
        PublishedContentRecord.owner_user_id == user.id, PublishedContentRecord.status == "active",
        ContentAccount.persona_id == persona_id)).all()
    history = _history(db, [r.id for r, _ in rows]) if rows else {}

    works = []
    for record, account_name in rows:
        snaps = history.get(record.id, [])
        latest = snaps[-1][1] if snaps else {}
        views = _first(latest, VIEW_KEYS)
        engagements = sum(latest.get(k, 0) for k in ENGAGE_KEYS) if latest else None
        published = utc(record.published_at) if record.published_at else None
        works.append({
            "id": record.id, "title": record.title or "（无标题）", "channel": record.channel,
            "channel_label": channel_label(record.channel), "account_name": account_name, "origin": record.origin,
            "published_at": published.astimezone(LOCAL_ZONE).isoformat() if published else None, "_published": published, "_created": utc(record.created_at),
            "views": views, "likes": latest.get("likes"), "comments": latest.get("comments"),
            "shares": latest.get("shares"), "favorites": latest.get("favorites"),
            "followers_gained": latest.get("followers_gained"), "engagements": engagements,
            "engagement_rate": engagements / views if views else None,
            "retention": _first(latest, RETENTION_KEYS), "bounce": _first(latest, BOUNCE_KEYS),
            "observations": len(snaps), "last_observed_at": snaps[-1][0].isoformat() if snaps else None,
            "events": [], "_snaps": snaps,
        })
    # 没有发布时间的排在最后，不参与「断更」判断。
    works.sort(key=lambda w: (w["_published"] is None, w["_published"] or now, w["id"]))

    def baseline(channel: str, key: str) -> float | None:
        values = [w[key] for w in works if w["channel"] == channel and w[key] is not None]
        return median(values) if len(values) >= MIN_BASELINE else None

    baselines = {(c, k): baseline(c, k) for c in {w["channel"] for w in works}
                 for k in ("views", "comments", "followers_gained", "engagement_rate", "retention", "bounce")}

    def add(work: dict, kind: str, detail: str, at=None) -> None:
        name, _, tone = EVENT_TYPES[kind]
        work["events"].append({"type": kind, "label": name, "tone": tone, "detail": detail,
                               "at": (at or work["_published"]).astimezone(LOCAL_ZONE).isoformat() if (at or work["_published"]) else None})

    seen_channels, previous = set(), None
    for w in works:
        c, published = w["channel"], w["_published"]
        if c not in seen_channels:
            seen_channels.add(c)
            add(w, "new_channel", f"第一条{w['channel_label']}作品")
        if published and previous and (published - previous).days > 14:
            add(w, "comeback", f"距上一条 {(published - previous).days} 天")
        if published:
            previous = published
        base = lambda key: baselines.get((c, key))  # noqa: E731
        if w["views"] is not None and base("views") and w["views"] >= 3 * base("views"):
            add(w, "breakout", f"{w['views']:.0f}，平常约 {base('views'):.0f}")
        if w["comments"] is not None and base("comments") and w["comments"] >= max(10, 3 * base("comments")):
            add(w, "comment_peak", f"{w['comments']:.0f} 条评论，平常约 {base('comments'):.0f}")
        if w["followers_gained"] is not None and base("followers_gained") is not None and w["followers_gained"] >= max(5, 3 * base("followers_gained")):
            add(w, "follower_spike", f"带来 {w['followers_gained']:.0f} 个关注，平常约 {base('followers_gained'):.0f}")
        if w["engagement_rate"] is not None and (w["views"] or 0) >= 100 and base("engagement_rate") and w["engagement_rate"] >= 2 * base("engagement_rate"):
            add(w, "high_engagement", f"互动率 {w['engagement_rate']:.1%}，平常约 {base('engagement_rate'):.1%}")
        if w["retention"] is not None and base("retention") and w["retention"] >= 1.5 * base("retention"):
            add(w, "strong_retention", f"{w['retention']:.1%}，平常约 {base('retention'):.1%}")
        if w["bounce"] is not None and base("bounce") and w["bounce"] >= 1.5 * base("bounce"):
            add(w, "hook_drop", f"跳出率 {w['bounce']:.1%}，平常约 {base('bounce'):.1%}")
        top = next((m for m in MILESTONES if (w["views"] or 0) >= m), None)
        if top:
            # 记在第一次录到过线的那天，不是最近一次录入。
            crossed = next(at for at, values in w["_snaps"] if (_first(values, VIEW_KEYS) or 0) >= top)
            add(w, "milestone", f"播放/阅读过 {top // 10000} 万" if top >= 10000 else f"播放/阅读过 {top}", crossed)
        age = (now - published).days if published else None
        if age is not None and age >= 3 and w["views"] is not None and base("views") and w["views"] <= 0.3 * base("views"):
            add(w, "cold_start", f"{w['views']:.0f}，平常约 {base('views'):.0f}")
        if not w["_snaps"] and (now - (published or w["_created"])).days >= 2:
            add(w, "no_data", f"发布 {age} 天，未录入效果" if age is not None else "没有发布时间，也未录入效果", published or w["_created"])
        for (at_a, a), (at_b, b) in zip(w["_snaps"], w["_snaps"][1:]):
            va, vb = _first(a, VIEW_KEYS), _first(b, VIEW_KEYS)
            if published and va and vb and (at_a - published).days >= 7 and vb - va >= max(200, 0.5 * va):
                add(w, "long_tail", f"{va:.0f} → {vb:.0f}", at_b)
            ca, cb = a.get("comments"), b.get("comments")
            if ca is not None and cb is not None and cb - ca >= 20:
                add(w, "comment_peak", f"两次录入之间新增 {cb - ca:.0f} 条评论", at_b)

    shown = [w for w in works if not since or (w["_published"] and w["_published"] >= since)]
    channels: dict = defaultdict(lambda: {"posts": 0, "views": 0.0, "engagements": 0.0, "followers_gained": 0.0, "with_data": 0})
    for w in shown:
        s = channels[w["channel"]]
        s["posts"] += 1
        if w["observations"]:
            s["with_data"] += 1
        s["views"] += w["views"] or 0
        s["engagements"] += w["engagements"] or 0
        s["followers_gained"] += w["followers_gained"] or 0
    events = sorted(({**e, "work_id": w["id"], "title": w["title"], "channel": w["channel"], "channel_label": w["channel_label"]}
                     for w in shown for e in w["events"]), key=lambda e: e["at"] or "", reverse=True)
    for w in works:
        for key in ("_published", "_created", "_snaps"):
            w.pop(key)
    persona = db.get(ContentPersona, persona_id)
    return {
        "persona_id": persona_id, "persona_name": persona.name if persona else None, "days": days,
        "works": shown,
        "events": events,
        "event_types": [{"type": k, "label": v[0], "description": v[1], "tone": v[2]} for k, v in EVENT_TYPES.items()],
        "channels": sorted(({"channel": k, "channel_label": channel_label(k), **v, "median_views": baselines.get((k, "views"))}
                            for k, v in channels.items()), key=lambda c: -c["views"]),
        "totals": {"posts": len(shown), "with_data": sum(1 for w in shown if w["observations"]),
                   "views": sum(w["views"] or 0 for w in shown), "engagements": sum(w["engagements"] or 0 for w in shown),
                   "followers_gained": sum(w["followers_gained"] or 0 for w in shown)},
        "last_observed_at": max((w["last_observed_at"] for w in shown if w["last_observed_at"]), default=None),
        "followers": persona_followers(db, user, persona_id),
    }
