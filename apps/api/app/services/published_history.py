"""Published history preserves source truth and explicit measurement semantics."""

import hashlib
import json
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import (
    ContentAsset,
    DeliveryFeedback,
    DeliveryReceipt,
    DeliveryTarget,
    PerformanceObservation,
    PublishedContentRecord,
    User,
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


def coverage(db: Session, row, *, cutoff=None):
    content = row.content_snapshot_json or {}
    asset = db.get(ContentAsset, row.content_asset_id) if row.content_asset_id else None
    observations = select(PerformanceObservation.id).where(PerformanceObservation.published_content_id == row.id)
    if cutoff is not None:
        observations = observations.where(PerformanceObservation.observed_at <= cutoff)
    metric = db.scalar(observations.where(PerformanceObservation.numeric_value.is_not(None)).limit(1))
    feedback = db.scalar(observations.where(PerformanceObservation.observation_kind == "feedback").limit(1))

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
        "metrics": "known" if metric is not None else "missing",
        "comments_feedback": "known" if feedback is not None else "missing",
        "production_provenance": "known" if row.origin == "studio" and row.content_asset_id else "unknown",
    }


def record_json(db: Session, row):
    data = {col.name: getattr(row, col.name) for col in row.__table__.columns}
    data["content_snapshot"] = data.pop("content_snapshot_json") or {}
    data.pop("coverage_json")
    data["coverage"] = coverage(db, row)
    return data


def sync_receipt(
    db: Session, user: User, receipt: DeliveryReceipt, *, published_at=None, publication_time_evidence=None
):
    if receipt.status != "human_confirmed" or receipt.delivered_at is None:
        return None
    target = owned_target(db, user, receipt.target_id)
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
