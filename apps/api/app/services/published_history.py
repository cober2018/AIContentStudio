"""Published history preserves source truth and explicit measurement semantics."""

import hashlib
import json
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..models import (
    ContentAsset,
    DeliveryFeedback,
    DeliveryReceipt,
    DeliveryTarget,
    PerformanceObservation,
    PublishedContentRecord,
    User,
    utcnow,
)
from .project_authorization import authorize_project_target


def checksum(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, default=str, separators=(",", ":")).encode()
    ).hexdigest()


def utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def owned_record(db: Session, user: User, record_id: int, *, mutate=False):
    row = db.get(PublishedContentRecord, record_id)
    if row is None or row.owner_user_id != user.id:
        raise HTTPException(404, "已发布内容不存在")
    if mutate and row.status == "archived":
        raise HTTPException(409, "已归档历史只可读取")
    return row


def owned_target(db: Session, user: User, target_id: int, *, mutate=False):
    target = db.get(DeliveryTarget, target_id)
    if target is None or (target.authorized_by is not None and target.authorized_by != user.email):
        raise HTTPException(404, "交付目标不存在")
    authorize_project_target(db, target, user, mutate=mutate)
    asset = db.get(ContentAsset, target.content_asset_id)
    if asset.project_id is None and target.authorized_by != user.email:
        raise HTTPException(404, "交付归属无法核实")
    return target


def observation_json(row):
    data = {col.name: getattr(row, col.name) for col in row.__table__.columns}
    data["payload"] = data.pop("payload_json") or {}
    data["measurement_mode"] = data["payload"].get("measurement_mode", "snapshot")
    return data


def _coverage_fields(row, asset, *, has_metric: bool, has_feedback: bool):
    content = row.content_snapshot_json or {}

    def state(value):
        return "known" if value is not None and value != "" and value != [] and value != {} else "missing"

    return {
        "title": state(row.title),
        "body": state(asset.final_body if asset else content.get("body")),
        "media": state((asset.candidate_manifest_json or {}).get("media") if asset else content.get("media")),
        "subtitles": state(content.get("subtitles")),
        "identity": "known" if row.identity_snapshot_id else "unknown",
        "account": "known" if row.content_account_id is not None else state(row.account_ref_snapshot),
        "channel": state(row.channel),
        "published_at": "known" if row.published_at else "unknown",
        "metrics": "known" if has_metric else "missing",
        "comments_feedback": "known" if has_feedback else "missing",
        "production_provenance": "known" if row.origin == "studio" and row.content_asset_id else "unknown",
    }


def coverage(db: Session, row, *, cutoff=None):
    asset = db.get(ContentAsset, row.content_asset_id) if row.content_asset_id else None
    observations = select(PerformanceObservation.id).where(PerformanceObservation.published_content_id == row.id)
    if cutoff is not None:
        observations = observations.where(PerformanceObservation.observed_at <= cutoff)
    metric = db.scalar(observations.where(PerformanceObservation.numeric_value.is_not(None)).limit(1))
    feedback = db.scalar(observations.where(PerformanceObservation.observation_kind == "feedback").limit(1))
    return _coverage_fields(row, asset, has_metric=metric is not None, has_feedback=feedback is not None)


MODEL_VERIFICATION = "third_party_model_browser"


def _evidence_fields(row, receipt):
    # A model clicking 发表 in the user's browser is not a human attestation; without a work URL it proves nothing public yet.
    if row.origin != "studio":
        return {"confirmed_by": None, "publication_verified": None, "pending_link": False}
    by = "model" if receipt is not None and receipt.verification_method == MODEL_VERIFICATION else "human"
    linked = bool(row.canonical_url and row.canonical_url.startswith(("http://", "https://")))
    verified = by == "human" or linked
    return {"confirmed_by": by, "publication_verified": verified, "pending_link": not verified}


def publication_evidence(db: Session, row) -> dict:
    receipt = db.get(DeliveryReceipt, row.delivery_receipt_id) if row.delivery_receipt_id else None
    return _evidence_fields(row, receipt)


def record_json(db: Session, row):
    data = {col.name: getattr(row, col.name) for col in row.__table__.columns}
    data["content_snapshot"] = data.pop("content_snapshot_json") or {}
    data.pop("coverage_json")
    data["coverage"] = coverage(db, row)
    data.update(publication_evidence(db, row))
    data["matched_work"] = matched_work(db, row)
    return data


def records_json(db: Session, rows) -> list[dict]:
    """列表页批量版 record_json：asset/observations/receipt 各一次 in_ 预取，避免每行 4-5 次查询。"""
    row_ids = [row.id for row in rows]
    if not row_ids:
        return []
    asset_ids = [row.content_asset_id for row in rows if row.content_asset_id]
    assets = {a.id: a for a in db.scalars(select(ContentAsset).where(ContentAsset.id.in_(asset_ids)))} if asset_ids else {}
    receipt_ids = [row.delivery_receipt_id for row in rows if row.delivery_receipt_id]
    receipts = {r.id: r for r in db.scalars(select(DeliveryReceipt).where(DeliveryReceipt.id.in_(receipt_ids)))} if receipt_ids else {}
    metric_ids = set(db.scalars(select(PerformanceObservation.published_content_id).where(
        PerformanceObservation.published_content_id.in_(row_ids), PerformanceObservation.numeric_value.is_not(None))))
    feedback_ids = set(db.scalars(select(PerformanceObservation.published_content_id).where(
        PerformanceObservation.published_content_id.in_(row_ids), PerformanceObservation.observation_kind == "feedback")))
    out = []
    for row in rows:
        data = {col.name: getattr(row, col.name) for col in row.__table__.columns}
        data["content_snapshot"] = data.pop("content_snapshot_json") or {}
        data.pop("coverage_json")
        data["coverage"] = _coverage_fields(row, assets.get(row.content_asset_id),
                                            has_metric=row.id in metric_ids, has_feedback=row.id in feedback_ids)
        data.update(_evidence_fields(row, receipts.get(row.delivery_receipt_id)))
        out.append(data)
    return out


def sync_receipt(
    db: Session, user: User, receipt: DeliveryReceipt, *, published_at=None, publication_time_evidence=None
):
    if receipt.status != "human_confirmed" or receipt.delivered_at is None:
        return None
    target = owned_target(db, user, receipt.target_id)
    # Confirming official draft delivery is not attesting public publication.
    if (target.publisher_key == "publisher.wechat.official" and target.publisher_version == "1"
            and target.action == "auto_draft"):
        return None
    if any(a.status == "unknown" and not (a.response_metadata_json or {}).get("reconciled") for a in target.attempts):
        return None
    asset = db.get(ContentAsset, target.content_asset_id)
    candidate_hash = asset.candidate_hash or asset.approved_candidate_hash
    if not candidate_hash:
        return None
    if candidate_hash != receipt.approved_candidate_hash or candidate_hash != target.approved_candidate_hash:
        raise HTTPException(409, "Receipt 与冻结候选哈希不一致")
    existing = db.scalar(select(PublishedContentRecord).where(PublishedContentRecord.delivery_receipt_id == receipt.id))
    if existing:
        if existing.owner_user_id != user.id:
            raise HTTPException(404, "已发布内容不存在")
        return existing
    # 外部导入的记录已匹配到这个交付目标：接上回执，不另建一条重复统计。
    matched = db.scalar(select(PublishedContentRecord).where(
        PublishedContentRecord.owner_user_id == user.id, PublishedContentRecord.status == "active",
        PublishedContentRecord.delivery_target_id == target.id, PublishedContentRecord.delivery_receipt_id.is_(None)))
    if matched:
        matched.delivery_receipt_id = receipt.id
        db.flush()
        return matched
    row = PublishedContentRecord(
        owner_user_id=user.id,
        origin="studio",
        content_asset_id=asset.id,
        delivery_target_id=target.id,
        delivery_receipt_id=receipt.id,
        content_account_id=target.content_account_id,
        identity_snapshot_id=asset.identity_snapshot_id,
        channel=target.channel,
        content_form=target.content_form,
        account_ref_snapshot=target.account_ref,
        title=asset.title,
        content_hash=candidate_hash,
        content_snapshot_json={
            "confirmation_time": receipt.delivered_at.isoformat(),
            "publication_time_source": "unknown",
        },
        published_at=utc(published_at) if published_at else None,
        coverage_json={},
        created_by=user.email,
    )
    if published_at is not None:
        if published_at.tzinfo is None or not publication_time_evidence or not publication_time_evidence.strip():
            raise HTTPException(422, "发布时间须有时区和明确的人工依据")
        row.content_snapshot_json = {
            **row.content_snapshot_json,
            "publication_time_source": "human_attested",
            "publication_time_evidence": publication_time_evidence,
        }
    db.add(row)
    db.flush()
    return row


def attach_feedback(db: Session, user: User, data):
    if data.source_type != "delivery_feedback":
        if data.source_type == "connector":
            raise HTTPException(409, "capability_unavailable: 未接入已验证指标Connector")
        return
    if (
        data.observation_kind == "metric"
        or data.numeric_value is not None
        or not data.source_ref
        or not data.source_ref.isdigit()
    ):
        raise HTTPException(422, "DeliveryFeedback只能作为明确的定性来源")
    row = db.get(DeliveryFeedback, int(data.source_ref))
    if row is None:
        raise HTTPException(404, "反馈不存在")
    owned_target(db, user, row.target_id)
    return row


def metric_scope(row):
    payload = row.payload_json or {}
    return (
        row.metric_namespace,
        row.metric_key,
        row.unit,
        payload.get("measurement_mode", "snapshot"),
        utc(row.period_start).isoformat() if row.period_start else None,
        utc(row.period_end).isoformat() if row.period_end else None,
        payload.get("granularity", "lifetime"),
    )


def _owned_unit(db: Session, user: User, unit_id: int):
    from ..models import ContentProject, ContentUnit

    unit = db.get(ContentUnit, unit_id)
    project = db.get(ContentProject, unit.project_id) if unit else None
    if unit is None or project is None or project.owner_user_id != user.id or unit.lifecycle != "active":
        raise HTTPException(404, "站内作品不存在")
    return unit


def _unit_assets(db: Session, unit_id: int) -> list[int]:
    return list(db.scalars(select(ContentAsset.id).where(ContentAsset.content_unit_id == unit_id).order_by(ContentAsset.id.desc())))


def match_candidates(db: Session, user: User, record_id: int, q: str | None = None, limit: int = 30) -> dict:
    """站内作品，平台标题和作品名不必一样：该平台有交付目标、还没记录的排前面。"""
    from ..models import ContentProject, ContentUnit

    record = owned_record(db, user, record_id)
    query = (select(ContentUnit).join(ContentProject, ContentProject.id == ContentUnit.project_id)
             .where(ContentProject.owner_user_id == user.id, ContentUnit.lifecycle == "active",
                    ContentUnit.id.in_(select(ContentAsset.content_unit_id).where(ContentAsset.content_unit_id.is_not(None)))))
    if q and q.strip():
        query = query.where(ContentUnit.title.contains(q.strip()))
    units = db.scalars(query.order_by(ContentUnit.id.desc()).limit(200)).all()
    items = []
    for unit in units:
        assets = _unit_assets(db, unit.id)
        target = db.scalar(select(DeliveryTarget).where(DeliveryTarget.content_asset_id.in_(assets),
                                                        DeliveryTarget.channel == record.channel).limit(1))
        existing = db.scalar(select(PublishedContentRecord.id).where(
            PublishedContentRecord.owner_user_id == user.id, PublishedContentRecord.status == "active",
            PublishedContentRecord.channel == record.channel, PublishedContentRecord.content_asset_id.in_(assets),
            PublishedContentRecord.id != record.id).limit(1))
        items.append({"content_unit_id": unit.id, "title": unit.title, "modality": unit.modality,
                      "status": unit.status, "has_target": target is not None, "existing_record_id": existing})
    items.sort(key=lambda i: (not (i["has_target"] and i["existing_record_id"] is None), -i["content_unit_id"]))
    return {"record_id": record.id, "channel": record.channel, "items": items[:limit]}


def match_record(db: Session, user: User, record_id: int, unit_id: int) -> PublishedContentRecord:
    """外部导入的发布记录归到站内作品。数据和平台编号跟着走，以后按平台编号导入仍落到这条。"""
    from ..models import AuditLog

    record = owned_record(db, user, record_id, mutate=True)
    if record.origin != "external_import":
        raise HTTPException(409, "只有外部导入的发布记录可以匹配站内作品")
    unit = _owned_unit(db, user, unit_id)
    assets = _unit_assets(db, unit.id)
    if not assets:
        raise HTTPException(409, "这个站内作品还没有成稿，不能匹配")
    target = db.scalar(select(DeliveryTarget).where(DeliveryTarget.content_asset_id.in_(assets),
                                                    DeliveryTarget.channel == record.channel)
                       .order_by(DeliveryTarget.id.desc()).limit(1))
    existing = db.scalar(select(PublishedContentRecord).where(
        PublishedContentRecord.owner_user_id == user.id, PublishedContentRecord.status == "active",
        PublishedContentRecord.channel == record.channel, PublishedContentRecord.content_asset_id.in_(assets),
        PublishedContentRecord.id != record.id).order_by(PublishedContentRecord.id).limit(1))
    detail = {"content_unit_id": unit.id, "from_title": record.title, "previous_asset_id": record.content_asset_id}
    if existing is not None:
        # 同一作品同一平台已有记录：把数据并过去，这条归档，只算一次。
        if existing.external_key and record.external_key and existing.external_key != record.external_key:
            raise HTTPException(409, f"作品在这个平台已有另一条记录（#{existing.id}，平台编号不同），请先核对是不是两次发布")
        moved = db.execute(update(PerformanceObservation).where(PerformanceObservation.published_content_id == record.id)
                           .values(published_content_id=existing.id)).rowcount
        key, record.external_key = record.external_key, None
        db.flush()
        existing.external_key = existing.external_key or key
        for field in ("canonical_url", "published_at", "content_account_id", "content_form"):
            if getattr(existing, field) is None:
                setattr(existing, field, getattr(record, field))
        existing.content_snapshot_json = {**(existing.content_snapshot_json or {}), "platform_title": record.title,
                                          "merged_records": [*(existing.content_snapshot_json or {}).get("merged_records", []), record.id]}
        existing.updated_at = utcnow()
        record.status = "archived"
        record.content_snapshot_json = {**(record.content_snapshot_json or {}), "merged_into": existing.id,
                                        "external_key": key}
        record.updated_at = utcnow()
        db.add(AuditLog(event="published_content.merged", actor=user.email, entity_type=record.__tablename__,
                        entity_id=str(record.id), detail_json={**detail, "into": existing.id, "observations_moved": moved}))
        return existing
    asset_id = target.content_asset_id if target else assets[0]
    asset = db.get(ContentAsset, asset_id)
    record.content_asset_id = asset_id
    record.delivery_target_id = target.id if target else None
    record.identity_snapshot_id = record.identity_snapshot_id or asset.identity_snapshot_id
    if record.content_account_id is None and target is not None:
        record.content_account_id = target.content_account_id
    record.content_snapshot_json = {**(record.content_snapshot_json or {}),
                                    "matched": {"content_unit_id": unit.id, "by": user.email, "at": utcnow().isoformat()}}
    record.updated_at = utcnow()
    db.add(AuditLog(event="published_content.matched", actor=user.email, entity_type=record.__tablename__,
                    entity_id=str(record.id), detail_json={**detail, "asset_id": asset_id,
                                                           "target_id": record.delivery_target_id}))
    return record


def matched_work(db: Session, row) -> dict | None:
    from ..models import ContentUnit

    asset = db.get(ContentAsset, row.content_asset_id) if row.content_asset_id else None
    unit = db.get(ContentUnit, asset.content_unit_id) if asset and asset.content_unit_id else None
    return {"content_unit_id": unit.id, "project_id": unit.project_id, "title": unit.title} if unit else None
