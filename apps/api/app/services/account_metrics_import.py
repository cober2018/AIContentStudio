"""Account data that a third-party model read from platform screenshots or exports, written into 效果复盘 as batches."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ..models import (
    AccountMetricImport,
    AuditLog,
    ContentAccount,
    PerformanceObservation,
    PublishedContentRecord,
    User,
    utcnow,
)
from . import published_history as history
from .content_identity import owned_entity

# Platform exports and screenshots show China time, and "the same day" means the user's day, not UTC.
LOCAL_ZONE = ZoneInfo("Asia/Shanghai")
SOURCE_TYPE = "platform_import"
RATE, SECONDS, COUNT = "ratio", "seconds", "count"

# Each platform accepts only these keys; anything else is refused so a misread column cannot invent metrics.
PLATFORM_METRICS: dict[str, dict[str, tuple[str, str]]] = {
    "douyin": {
        "plays": ("播放量", COUNT), "completion_rate": ("完播率", RATE), "completion_rate_5s": ("5s完播率", RATE),
        "cover_ctr": ("封面点击率", RATE), "bounce_rate_2s": ("2s跳出率", RATE), "avg_play_seconds": ("平均播放时长", SECONDS),
        "likes": ("点赞", COUNT), "shares": ("分享", COUNT), "comments": ("评论", COUNT), "favorites": ("收藏", COUNT),
        "profile_visits": ("主页访问量", COUNT), "followers_gained": ("粉丝增量", COUNT),
    },
    "wechat": {
        "reads": ("阅读", COUNT), "likes": ("点赞", COUNT), "shares": ("分享", COUNT), "recommends": ("推荐/爱心", COUNT),
        "comments": ("留言", COUNT), "highlights": ("划线（含义待确认）", COUNT), "reposts": ("转载（含义待确认）", COUNT),
    },
    "xiaohongshu": {
        "views": ("观看/阅读", COUNT), "likes": ("点赞", COUNT), "comments": ("评论", COUNT),
        "favorites": ("收藏", COUNT), "shares": ("分享", COUNT),
    },
    "bilibili": {
        "views": ("播放", COUNT), "likes": ("点赞", COUNT), "comments": ("评论", COUNT), "favorites": ("收藏", COUNT),
        "shares": ("分享", COUNT), "coins": ("投币", COUNT), "danmaku": ("弹幕", COUNT),
    },
}
# Gains can be negative (unfollows); every other metric is a count, rate or duration.
SIGNED = {"followers_gained"}


def channel_label(channel: str | None) -> str | None:
    from .content_harness.channel_registry import CHANNEL_LABELS, PLANNED_CHANNELS

    if not channel:
        return None
    return (PLANNED_CHANNELS.get(channel) or {}).get("label") or CHANNEL_LABELS.get(channel, channel)


def batch_link(batch_id: int) -> str:
    return f"/learning?tab=history&view=imports&batch={batch_id}"


def list_accounts(db: Session, user: User) -> dict:
    from ..models import ContentPersona

    rows = db.execute(
        select(ContentAccount, ContentPersona.name)
        .outerjoin(ContentPersona, ContentPersona.id == ContentAccount.persona_id)
        .where(ContentAccount.status == "active")
        .order_by(ContentAccount.id)
    ).all()
    accounts = []
    for account, persona_name in rows:
        try:
            owned_entity(db, user, "account", account.id)
        except HTTPException:
            continue
        accounts.append({
            "id": account.id, "name": account.name, "platform_channel": account.platform_channel,
            "platform_label": channel_label(account.platform_channel), "persona_id": account.persona_id,
            "persona_name": persona_name, "importable": account.platform_channel in PLATFORM_METRICS,
        })
    return {"accounts": accounts, "metric_keys": {channel: sorted(keys) for channel, keys in PLATFORM_METRICS.items()}}


def parse_published_at(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.strip().replace("/", "-"))
    except ValueError:
        raise HTTPException(422, {"code": "account_import_published_at_invalid",
                                  "message": f"发布时间看不懂：{value[:40]}，请用 YYYY-MM-DD HH:MM[:SS]"})
    return history.utc(parsed if parsed.tzinfo else parsed.replace(tzinfo=LOCAL_ZONE))


def _validate(channel: str, rows: list[dict]) -> None:
    allowed = PLATFORM_METRICS[channel]
    problems = []
    for index, row in enumerate(rows, 1):
        unknown = (set(row["metrics"]) | set(row.get("uncertain") or ())) - set(allowed)
        if unknown:
            problems.append(f"第{index}行有本平台不收的数据项：{', '.join(sorted(unknown))}")
        for key, value in row["metrics"].items():
            if key not in allowed:
                continue
            if allowed[key][1] == RATE and not 0 <= value <= 1:
                problems.append(f"第{index}行 {key} 是比率，须写成 0–1 的小数（如 23.18% 写 0.2318）")
            elif key not in SIGNED and value < 0:
                problems.append(f"第{index}行 {key} 不能是负数")
    if problems:
        raise HTTPException(422, {"code": "account_import_rows_invalid", "message": "；".join(problems[:20]),
                                  "allowed_metrics": sorted(allowed)})


def _record(db: Session, user: User, account: ContentAccount, row: dict, published_at: datetime):
    """Matches the work by account, platform, title and publish time; returns (record, created)."""
    title = row["title"].strip()
    found = db.scalar(select(PublishedContentRecord).where(
        PublishedContentRecord.owner_user_id == user.id,
        PublishedContentRecord.content_account_id == account.id,
        PublishedContentRecord.channel == account.platform_channel,
        PublishedContentRecord.title == title,
        PublishedContentRecord.published_at == published_at,
    ).order_by(PublishedContentRecord.id).limit(1))
    if found:
        return found, False
    # Deterministic key, so the same work read from two different files never becomes two works.
    key = "account_import:" + history.checksum([account.id, title, published_at.isoformat()])[:48]
    found = db.scalar(select(PublishedContentRecord).where(
        PublishedContentRecord.owner_user_id == user.id, PublishedContentRecord.channel == account.platform_channel,
        PublishedContentRecord.external_key == key))
    if found:
        return found, False
    snapshot = {"metadata": {"source": SOURCE_TYPE}}
    record = PublishedContentRecord(
        owner_user_id=user.id, origin="external_import", external_key=key, channel=account.platform_channel,
        content_form=row.get("content_form"), title=title, canonical_url=row.get("url"), published_at=published_at,
        content_account_id=account.id, account_ref_snapshot=account.name, content_snapshot_json=snapshot,
        content_hash=history.checksum({"external_key": key, "title": title, "published_at": published_at.isoformat()}),
        created_by=user.email,
    )
    db.add(record)
    db.flush()
    db.add(AuditLog(event="published_content.imported", actor=user.email, entity_type=record.__tablename__,
                    entity_id=str(record.id), detail_json={"source": SOURCE_TYPE}))
    return record, True


def import_metrics(db: Session, user: User, account_id: int, source: dict, rows: list[dict]) -> dict:
    account = owned_entity(db, user, "account", account_id, mutable=True)
    channel = account.platform_channel
    if channel not in PLATFORM_METRICS:
        raise HTTPException(422, {"code": "account_import_platform_unsupported",
                                  "message": f"{channel_label(channel) or '该账号'}暂不支持导入数据，支持：{', '.join(PLATFORM_METRICS)}"})
    existing = db.scalar(select(AccountMetricImport).where(
        AccountMetricImport.owner_user_id == user.id, AccountMetricImport.content_account_id == account.id,
        AccountMetricImport.source_checksum == source["checksum"], AccountMetricImport.undone_at.is_(None)))
    if existing:
        return {"skipped": True, "batch_id": existing.id, "reason": "这份文件或截图已导入过", "counts": existing.counts_json,
                "link": batch_link(existing.id)}
    _validate(channel, rows)
    published = [parse_published_at(row["published_at"]) for row in rows]
    now = utcnow()
    local_day = now.astimezone(LOCAL_ZONE).replace(hour=0, minute=0, second=0, microsecond=0)
    day_start, day_end = history.utc(local_day), history.utc(local_day + timedelta(days=1))
    batch = AccountMetricImport(owner_user_id=user.id, content_account_id=account.id, channel=channel,
                                source_kind=source["kind"], source_name=source["name"], source_checksum=source["checksum"],
                                created_record_ids=[], counts_json={}, created_by=user.email, created_at=now)
    db.add(batch)
    db.flush()
    ref = f"import_batch:{batch.id}"
    created, updated, skipped, written, replaced, uncertain_count = [], set(), 0, 0, 0, 0
    allowed = PLATFORM_METRICS[channel]
    for row, published_at in zip(rows, published, strict=True):
        record, is_new = _record(db, user, account, row, published_at)
        if record.status != "active":
            skipped += len(row["metrics"])
            continue
        if is_new:
            created.append(record.id)
        else:
            updated.add(record.id)
        uncertain = set(row.get("uncertain") or ())
        # An uncertain cell without any value is only noted, never stored as a number.
        skipped += len(uncertain - set(row["metrics"]))
        for key, value in row["metrics"].items():
            corrected = select(PerformanceObservation.supersedes_id).where(PerformanceObservation.supersedes_id.is_not(None))
            # Same work, metric and day keeps only the newest import; manual entries and corrected ones stay.
            replaced += db.execute(delete(PerformanceObservation).where(
                PerformanceObservation.published_content_id == record.id,
                PerformanceObservation.metric_namespace == channel,
                PerformanceObservation.metric_key == key,
                PerformanceObservation.source_type == SOURCE_TYPE,
                PerformanceObservation.observed_at >= day_start,
                PerformanceObservation.observed_at < day_end,
                PerformanceObservation.id.not_in(corrected),
            ).execution_options(synchronize_session=False)).rowcount
            payload = {"measurement_mode": "snapshot", "granularity": "lifetime", "cutoff": now.isoformat(),
                       "import_batch_id": batch.id, "source_kind": source["kind"], "label": allowed[key][0]}
            if key in uncertain:
                payload["uncertain"] = True
                uncertain_count += 1
            db.add(PerformanceObservation(
                published_content_id=record.id, observation_kind="metric", metric_namespace=channel, metric_key=key,
                numeric_value=float(value), unit=allowed[key][1], observed_at=now, source_type=SOURCE_TYPE,
                source_ref=ref, source_checksum=source["checksum"][:64], payload_json=payload, created_by=user.email))
            written += 1
    counts = {"rows": len(rows), "records_created": len(created), "records_updated": len(updated - set(created)),
              "observations": written, "replaced_same_day": replaced, "uncertain": uncertain_count, "skipped": skipped}
    batch.created_record_ids, batch.counts_json = created, counts
    db.add(AuditLog(event="account_metric_import.created", actor=user.email, entity_type=batch.__tablename__,
                    entity_id=str(batch.id), detail_json={"account_id": account.id, **counts}))
    db.commit()
    return {"skipped": False, "batch_id": batch.id, "counts": counts, "link": batch_link(batch.id)}


def batch_json(batch: AccountMetricImport, account: ContentAccount | None) -> dict:
    return {"id": batch.id, "content_account_id": batch.content_account_id, "account_name": account.name if account else None,
            "channel": batch.channel, "channel_label": channel_label(batch.channel), "source_kind": batch.source_kind,
            "source_name": batch.source_name, "counts": batch.counts_json or {}, "created_at": batch.created_at,
            "undone_at": batch.undone_at}


def list_batches(db: Session, user: User, account_id: int | None, limit: int, offset: int) -> dict:
    query = select(AccountMetricImport).where(AccountMetricImport.owner_user_id == user.id)
    if account_id is not None:
        owned_entity(db, user, "account", account_id)
        query = query.where(AccountMetricImport.content_account_id == account_id)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.scalars(query.order_by(AccountMetricImport.id.desc()).offset(offset).limit(limit)).all()
    return {"items": [batch_json(row, db.get(ContentAccount, row.content_account_id)) for row in rows],
            "total": total, "limit": limit, "offset": offset}


def undo_batch(db: Session, user: User, batch_id: int) -> dict:
    batch = db.get(AccountMetricImport, batch_id)
    if batch is None or batch.owner_user_id != user.id:
        raise HTTPException(404, "导入批次不存在")
    if batch.undone_at is not None:
        raise HTTPException(409, "这批已撤销")
    corrected = select(PerformanceObservation.supersedes_id).where(PerformanceObservation.supersedes_id.is_not(None))
    removed = db.execute(delete(PerformanceObservation).where(
        PerformanceObservation.source_ref == f"import_batch:{batch.id}", PerformanceObservation.id.not_in(corrected),
    ).execution_options(synchronize_session=False)).rowcount
    removed_records = []
    for record_id in batch.created_record_ids or []:
        held = db.scalar(select(PerformanceObservation.id).where(PerformanceObservation.published_content_id == record_id).limit(1))
        record = db.get(PublishedContentRecord, record_id)
        if record is not None and held is None:
            db.delete(record)
            removed_records.append(record_id)
    batch.undone_at = utcnow()
    db.add(AuditLog(event="account_metric_import.undone", actor=user.email, entity_type=batch.__tablename__,
                    entity_id=str(batch.id), detail_json={"observations_removed": removed, "records_removed": removed_records}))
    db.commit()
    return {**batch_json(batch, db.get(ContentAccount, batch.content_account_id)),
            "observations_removed": removed, "records_removed": len(removed_records)}
