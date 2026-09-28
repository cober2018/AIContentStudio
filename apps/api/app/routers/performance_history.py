"""Owner-scoped history recovery and truthful performance read models."""

from collections import defaultdict
from datetime import datetime
from itertools import pairwise
from statistics import median
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_db as base_get_db
from ..deps import get_current_user, require_editor
from ..models import (
    AuditLog,
    ContentAsset,
    DeliveryReceipt,
    DeliveryTarget,
    IdentitySnapshot,
    PerformanceObservation,
    PublishedContentRecord,
    User,
    utcnow,
)
from ..services import published_history as service
from ..services.content_identity import owned_entity
from ..services.project_events import record_project_event

router = APIRouter(prefix="/api/v1", tags=["performance-history"])


def get_db(db: Session = Depends(base_get_db)):
    try:
        yield db
    finally:
        db.rollback()


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class ImportRecord(Input):
    external_key: str = Field(min_length=1, max_length=300)
    channel: str = Field(min_length=1, max_length=30)
    content_form: str | None = Field(default=None, max_length=50)
    title: str | None = Field(default=None, max_length=500)
    canonical_url: str | None = Field(default=None, max_length=2000)
    published_at: datetime | None = None
    content_snapshot: dict = Field(default_factory=dict)
    content_account_id: int | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)

    @model_validator(mode="after")
    def validate_snapshot(self):
        if len(str(self.content_snapshot)) > 100000:
            raise ValueError("历史快照超过100k上限")
        if self.published_at and self.published_at.tzinfo is None:
            raise ValueError("发布时间必须包含时区")
        if self.published_at:
            self.published_at = service.utc(self.published_at)
        if set(self.content_snapshot) - {"body", "subtitles", "media", "metadata"}:
            raise ValueError("历史快照只允许内容和媒体引用元数据")
        return self


class ImportBatch(Input):
    records: list[ImportRecord] = Field(min_length=1, max_length=100)


class ObservationIn(Input):
    observation_kind: Literal["metric", "feedback", "editorial", "correction"]
    metric_namespace: str | None = Field(default=None, max_length=100)
    metric_key: str | None = Field(default=None, max_length=100)
    numeric_value: float | None = None
    text_value: str | None = Field(default=None, max_length=20000)
    unit: str | None = Field(default=None, max_length=50)
    period_start: datetime | None = None
    period_end: datetime | None = None
    observed_at: datetime = Field(default_factory=utcnow)
    source_type: Literal["manual", "delivery_feedback", "external_import", "connector"] = "manual"
    source_ref: str | None = Field(default=None, max_length=300)
    confidence: float | None = Field(default=None, ge=0, le=1)
    measurement_mode: Literal["snapshot", "interval"] = "snapshot"
    granularity: str = Field(default="lifetime", min_length=1, max_length=50)
    cutoff: datetime | None = None
    supersedes_id: int | None = None

    @model_validator(mode="after")
    def validate_metric(self):
        for field in ["observed_at", "period_start", "period_end", "cutoff"]:
            value = getattr(self, field)
            if value is not None and value.tzinfo is None:
                raise ValueError("观察时间必须包含时区")
            if value is not None:
                setattr(self, field, service.utc(value))
        if self.cutoff is None:
            self.cutoff = self.observed_at
        if self.cutoff > self.observed_at:
            raise ValueError("指标截止时间不能晚于采集时间")
        metric = self.observation_kind == "metric" or self.numeric_value is not None
        if metric and (self.numeric_value is None or not self.metric_namespace or not self.metric_key or not self.unit):
            raise ValueError("数值观察必须声明namespace/key/value/unit")
        if not metric and not self.text_value and self.source_type != "delivery_feedback":
            raise ValueError("定性观察必须有内容")
        if self.observation_kind == "correction" and self.supersedes_id is None:
            raise ValueError("修正必须引用旧观察")
        if (self.period_start is None) != (self.period_end is None):
            raise ValueError("指标窗口须同时提供起止时间")
        if self.period_start and self.period_start >= self.period_end:
            raise ValueError("指标窗口起止顺序错误")
        if metric and self.measurement_mode == "interval" and self.period_start is None:
            raise ValueError("区间指标须声明窗口")
        return self


class RecoveryIn(Input):
    target_id: int
    publication_attestation: str = Field(min_length=1, max_length=10000)
    idempotency_key: str = Field(min_length=1, max_length=100)
    published_at: datetime | None = None
    evidence_ref: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def normalize_date(self):
        if self.published_at is not None:
            if self.published_at.tzinfo is None:
                raise ValueError("发布时间必须包含时区")
            self.published_at = service.utc(self.published_at)
        return self


class HistoryPatch(Input):
    title: str | None = Field(default=None, max_length=500)
    canonical_url: str | None = Field(default=None, max_length=2000)


def audit(db, user, event, row):
    db.add(AuditLog(event=event, actor=user.email, entity_type=row.__tablename__, entity_id=str(row.id)))


def commit(db):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "历史记录或修正已被另一请求提交")


def query_time(value):
    if value is not None and value.tzinfo is None:
        raise HTTPException(422, "查询时间必须包含时区")
    return service.utc(value) if value is not None else None


def cohort(
    db,
    user,
    channel=None,
    content_account_id=None,
    date_from=None,
    date_to=None,
    content_form=None,
    identity_scope_type=None,
    identity_scope_id=None,
):
    date_from, date_to = query_time(date_from), query_time(date_to)
    query = select(PublishedContentRecord).where(
        PublishedContentRecord.owner_user_id == user.id, PublishedContentRecord.status == "active"
    )
    if channel:
        query = query.where(PublishedContentRecord.channel == channel)
    if content_account_id is not None:
        owned_entity(db, user, "account", content_account_id)
        query = query.where(PublishedContentRecord.content_account_id == content_account_id)
    if content_form:
        query = query.where(PublishedContentRecord.content_form == content_form)
    if identity_scope_type or identity_scope_id is not None:
        if identity_scope_type not in {"brand", "persona", "account", "series"} or identity_scope_id is None:
            raise HTTPException(422, "身份筛选须声明类型和ID")
        owned_entity(db, user, identity_scope_type, identity_scope_id)
        query = query.join(IdentitySnapshot, IdentitySnapshot.id == PublishedContentRecord.identity_snapshot_id).where(
            getattr(IdentitySnapshot, identity_scope_type + "_id") == identity_scope_id
        )
    if date_from:
        query = query.where(PublishedContentRecord.published_at >= date_from)
    if date_to:
        query = query.where(PublishedContentRecord.published_at < date_to)
    if date_from and date_to and date_from >= date_to:
        raise HTTPException(422, "日期范围错误")
    return query


@router.post("/published-content/import", status_code=201)
def import_history(payload: ImportBatch, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    for _attempt in range(2):
        try:
            return import_records(payload, db, user)
        except IntegrityError:
            db.rollback()
    raise HTTPException(409, "外部历史已被另一请求提交，请重新读取")


def import_records(payload, db, user):
    items = []
    for record in payload.records:
        if record.content_account_id:
            owned_entity(db, user, "account", record.content_account_id)
        fingerprint = service.checksum(record.model_dump(mode="json"))
        row = db.scalar(
            select(PublishedContentRecord).where(
                PublishedContentRecord.owner_user_id == user.id,
                PublishedContentRecord.channel == record.channel,
                PublishedContentRecord.external_key == record.external_key,
            )
        )
        if row:
            if row.content_hash != fingerprint:
                raise HTTPException(409, "重复外部标识携带不同历史快照")
        else:
            row = PublishedContentRecord(
                owner_user_id=user.id,
                origin="external_import",
                external_key=record.external_key,
                channel=record.channel,
                content_form=record.content_form,
                title=record.title,
                canonical_url=record.canonical_url,
                published_at=record.published_at,
                content_hash=fingerprint,
                content_snapshot_json=record.content_snapshot,
                content_account_id=record.content_account_id,
                created_by=user.email,
                confidence=record.confidence,
            )
            db.add(row)
            db.flush()
            audit(db, user, "published_content.imported", row)
        items.append(row)
    commit(db)
    return {"items": [service.record_json(db, r) for r in items], "total": len(items)}


@router.post("/published-content", status_code=201)
def create_history(payload: ImportRecord, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return import_history(ImportBatch(records=[payload]), db, user)["items"][0]


@router.post("/published-content/sync-studio")
def sync_studio(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(require_editor),
):
    targets = (
        select(DeliveryTarget.id)
        .join(ContentAsset, ContentAsset.id == DeliveryTarget.content_asset_id)
        .where(DeliveryTarget.authorized_by == user.email)
    )
    receipts = db.scalars(
        select(DeliveryReceipt)
        .where(
            DeliveryReceipt.target_id.in_(targets),
            DeliveryReceipt.status == "human_confirmed",
            DeliveryReceipt.delivered_at.is_not(None),
        )
        .order_by(DeliveryReceipt.id)
        .offset(offset)
        .limit(limit)
    ).all()
    items, skipped = [], []
    for receipt in receipts:
        row = service.sync_receipt(db, user, receipt)
        if row:
            items.append(row)
        else:
            skipped.append(receipt.id)
    missing = db.scalars(
        select(DeliveryTarget.id)
        .where(
            DeliveryTarget.id.in_(targets),
            DeliveryTarget.status == "human_confirmed",
            ~DeliveryTarget.id.in_(
                select(DeliveryReceipt.target_id).where(DeliveryReceipt.status == "human_confirmed")
            ),
        )
        .limit(limit)
    ).all()
    commit(db)
    return {
        "items": [service.record_json(db, r) for r in items],
        "missing_confirmation_target_ids": missing,
        "skipped_receipt_ids": skipped,
        "processed": len(receipts),
        "offset": offset,
        "limit": limit,
        "next_offset": offset + len(receipts),
    }


@router.post("/published-content/confirm-reconciled", status_code=201)
def confirm_reconciled(payload: RecoveryIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    target = service.owned_target(db, user, payload.target_id, mutate=True)
    db.execute(update(DeliveryTarget).where(DeliveryTarget.id == target.id).values(status=DeliveryTarget.status))
    db.refresh(target)
    if target.status != "human_confirmed" or any(
        a.status == "unknown" and not (a.response_metadata_json or {}).get("reconciled") for a in target.attempts
    ):
        raise HTTPException(409, "必须先完成对账，不能把未知结果当成发布")
    asset = db.get(ContentAsset, target.content_asset_id)
    if not asset or (asset.candidate_hash or asset.approved_candidate_hash) != target.approved_candidate_hash:
        raise HTTPException(409, "冻结候选哈希不一致")
    if not payload.publication_attestation.strip() or (payload.published_at and payload.published_at.tzinfo is None):
        raise HTTPException(422, "发布确认不能为空；真实发布时间必须包含时区")
    fingerprint = service.checksum(payload.model_dump(mode="json"))
    key = "f5b:" + service.checksum([user.id, target.id, payload.idempotency_key])[:60]
    existing_history = db.scalar(
        select(PublishedContentRecord).where(
            PublishedContentRecord.owner_user_id == user.id,
            PublishedContentRecord.delivery_target_id == target.id,
        )
    )
    recovery_claim = (
        (existing_history.content_snapshot_json or {}).get("publication_recoveries", {}).get(key)
        if existing_history
        else None
    )
    if recovery_claim:
        if recovery_claim["checksum"] != fingerprint:
            raise HTTPException(409, "发布确认重试内容冲突")
        existing_receipt = db.get(DeliveryReceipt, existing_history.delivery_receipt_id)
        if not existing_receipt or service.sync_receipt(db, user, existing_receipt) is None:
            raise HTTPException(409, "发布回执血缘尚不可核实")
        commit(db)
        return service.record_json(db, existing_history)
    recovery = db.scalar(
        select(AuditLog).where(
            AuditLog.event == "publication.recovery_attested",
            AuditLog.entity_type == "delivery_target",
            AuditLog.entity_id == str(target.id),
            AuditLog.actor == user.email,
            AuditLog.detail_json["recovery_key"].as_string() == key,
        )
    )
    if recovery:
        if recovery.detail_json["checksum"] != fingerprint:
            raise HTTPException(409, "发布确认重试内容冲突")
        row = service.owned_record(db, user, recovery.detail_json["published_content_id"])
        existing_receipt = db.get(DeliveryReceipt, row.delivery_receipt_id)
        if not existing_receipt or service.sync_receipt(db, user, existing_receipt) is None:
            raise HTTPException(409, "发布回执血缘尚不可核实")
        commit(db)
        return service.record_json(db, row)
    receipt = db.scalar(
        select(DeliveryReceipt).where(DeliveryReceipt.target_id == target.id, DeliveryReceipt.idempotency_key == key)
    )
    if receipt:
        if receipt.note != fingerprint:
            raise HTTPException(409, "发布确认重试内容冲突")
        row = service.sync_receipt(db, user, receipt)
        if row is None:
            raise HTTPException(409, "发布回执血缘或未知状态尚不可核实")
        commit(db)
        return service.record_json(db, row)
    if target.status != "human_confirmed" or any(
        a.status == "unknown" and not (a.response_metadata_json or {}).get("reconciled") for a in target.attempts
    ):
        raise HTTPException(409, "必须先完成对账，不能把未知结果当成发布")
    receipt = db.scalar(
        select(DeliveryReceipt).where(
            DeliveryReceipt.target_id == target.id,
            DeliveryReceipt.status == "human_confirmed",
            DeliveryReceipt.delivered_at.is_not(None),
        )
    )
    asset = db.get(ContentAsset, target.content_asset_id)
    if (asset.candidate_hash or asset.approved_candidate_hash) != target.approved_candidate_hash:
        raise HTTPException(409, "冻结候选哈希不一致")
    if receipt is None:
        receipt = DeliveryReceipt(
            target_id=target.id,
            approved_candidate_hash=target.approved_candidate_hash,
            action=target.action,
            idempotency_key=key,
            status="human_confirmed",
            delivered_at=utcnow(),
            operator=user.email,
            evidence_ref=payload.evidence_ref,
            verification_method="human_attestation",
            note=fingerprint,
        )
        db.add(receipt)
        db.flush()
    row = service.sync_receipt(db, user, receipt)
    if row is None:
        raise HTTPException(409, "发布回执血缘尚不可核实")
    if row.status == "archived":
        raise HTTPException(409, "历史已归档，不可改写")
    if (
        row.published_at is not None
        and payload.published_at is not None
        and service.utc(row.published_at) != payload.published_at
    ):
        raise HTTPException(409, "已有发布时间与声明冲突")
    row.published_at = payload.published_at or row.published_at
    row.content_snapshot_json = {
        **row.content_snapshot_json,
        "publication_attestation": payload.publication_attestation,
        "publication_time_source": "human_attestation" if row.published_at else "unknown",
        "publication_recoveries": {
            **(row.content_snapshot_json or {}).get("publication_recoveries", {}),
            key: {"checksum": fingerprint, "receipt_id": receipt.id},
        },
    }
    db.add(
        AuditLog(
            event="publication.recovery_attested",
            actor=user.email,
            entity_type="delivery_target",
            entity_id=str(target.id),
            detail_json={
                "recovery_key": key,
                "checksum": fingerprint,
                "published_content_id": row.id,
                "receipt_id": receipt.id,
            },
        )
    )
    audit(db, user, "published_content.confirmed_after_reconciliation", row)
    if asset.project_id:
        record_project_event(
            db,
            project_id=asset.project_id,
            event_type="delivery.publication_confirmed",
            actor=user.email,
            entity_type="delivery_receipt",
            entity_id=receipt.id,
            payload={"target_id": target.id, "published_content_id": row.id},
        )
    commit(db)
    return service.record_json(db, row)


@router.get("/published-content")
def list_history(
    channel: str | None = None,
    content_account_id: int | None = None,
    content_form: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    status: Literal["active", "archived"] = "active",
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    date_from, date_to = query_time(date_from), query_time(date_to)
    if date_from and date_to and date_from >= date_to:
        raise HTTPException(422, "日期范围错误")
    if content_account_id is not None:
        owned_entity(db, user, "account", content_account_id)
    q = select(PublishedContentRecord).where(
        PublishedContentRecord.owner_user_id == user.id, PublishedContentRecord.status == status
    )
    if channel:
        q = q.where(PublishedContentRecord.channel == channel)
    if content_account_id:
        q = q.where(PublishedContentRecord.content_account_id == content_account_id)
    if content_form:
        q = q.where(PublishedContentRecord.content_form == content_form)
    if date_from:
        q = q.where(PublishedContentRecord.published_at >= date_from)
    if date_to:
        q = q.where(PublishedContentRecord.published_at < date_to)
    total = db.scalar(select(func.count()).select_from(q.subquery()))
    rows = db.scalars(q.order_by(PublishedContentRecord.id.desc()).offset(offset).limit(limit)).all()
    return {"items": [service.record_json(db, r) for r in rows], "total": total, "limit": limit, "offset": offset}


@router.get("/published-content/{record_id}")
def history_detail(record_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.record_json(db, service.owned_record(db, user, record_id))


@router.patch("/published-content/{record_id}")
def patch_history(
    record_id: int, payload: HistoryPatch, db: Session = Depends(get_db), user: User = Depends(require_editor)
):
    row = service.owned_record(db, user, record_id, mutate=True)
    if row.origin != "external_import":
        raise HTTPException(409, "Studio历史保持冻结候选真源")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    row.updated_at = utcnow()
    audit(db, user, "published_content.metadata_updated", row)
    commit(db)
    return service.record_json(db, row)


@router.delete("/published-content/{record_id}", status_code=204)
def archive_history(record_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    row = service.owned_record(db, user, record_id)
    if row.status != "archived":
        row.status = "archived"
        audit(db, user, "published_content.archived", row)
    commit(db)


@router.post("/published-content/{record_id}/observations", status_code=201)
def add_observation(
    record_id: int, payload: ObservationIn, db: Session = Depends(get_db), user: User = Depends(require_editor)
):
    record = service.owned_record(db, user, record_id, mutate=True)
    locked = db.execute(
        update(PublishedContentRecord)
        .where(
            PublishedContentRecord.id == record_id,
            PublishedContentRecord.owner_user_id == user.id,
            PublishedContentRecord.status == "active",
        )
        .values(updated_at=PublishedContentRecord.updated_at)
    )
    if locked.rowcount != 1:
        raise HTTPException(409, "历史已归档，不可追加观察")
    db.refresh(record)
    values = payload.model_dump(exclude={"measurement_mode", "granularity", "cutoff"})
    feedback = service.attach_feedback(db, user, payload)
    if feedback:
        if record.delivery_target_id != feedback.target_id:
            raise HTTPException(422, "反馈与发布记录的交付血缘不一致")
        values["text_value"] = feedback.body
        values["source_checksum"] = service.checksum({"id": feedback.id, "body": feedback.body})
    row = PerformanceObservation(
        published_content_id=record_id,
        payload_json={
            "measurement_mode": payload.measurement_mode,
            "granularity": payload.granularity,
            "cutoff": payload.cutoff.isoformat(),
        },
        created_by=user.email,
        **values,
    )
    if payload.supersedes_id is not None:
        prior = db.get(PerformanceObservation, payload.supersedes_id)
        if prior is None or prior.published_content_id != record_id:
            raise HTTPException(404, "原观察不存在")
        if service.metric_scope(row) != service.metric_scope(prior):
            raise HTTPException(422, "修正不能改变指标口径")
        if (row.numeric_value is None) != (prior.numeric_value is None):
            raise HTTPException(422, "数值与定性观察不能互相替代")
        if db.scalar(select(PerformanceObservation.id).where(PerformanceObservation.supersedes_id == prior.id)):
            raise HTTPException(409, "原观察已有修正")
    db.add(row)
    db.flush()
    audit(db, user, "performance_observation.recorded", row)
    commit(db)
    return service.observation_json(row)


@router.get("/published-content/{record_id}/observations")
def list_observations(
    record_id: int,
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service.owned_record(db, user, record_id)
    q = select(PerformanceObservation).where(PerformanceObservation.published_content_id == record_id)
    return {
        "items": [
            service.observation_json(r)
            for r in db.scalars(
                q.order_by(PerformanceObservation.observed_at.desc(), PerformanceObservation.id.desc())
                .offset(offset)
                .limit(limit)
            )
        ],
        "total": db.scalar(select(func.count()).select_from(q.subquery())),
        "offset": offset,
        "limit": limit,
    }


@router.get("/learning/coverage")
def get_coverage(
    channel: str | None = None,
    content_account_id: int | None = None,
    content_form: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    identity_scope_type: str | None = None,
    identity_scope_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = cohort(
        db, user, channel, content_account_id, date_from, date_to, content_form, identity_scope_type, identity_scope_id
    )
    return coverage_result(db, q)


def coverage_result(db, q, metric_ids=None, cutoff=None, unavailable=None):
    total = db.scalar(select(func.count()).select_from(q.subquery()))
    rows = db.scalars(q.order_by(PublishedContentRecord.id).limit(1000)).all()
    counts = defaultdict(lambda: {"known": 0, "missing": 0, "unknown": 0})
    years = defaultdict(int)
    for row in rows:
        years[str(row.published_at.year) if row.published_at else "unknown"] += 1
        fields = service.coverage(db, row, cutoff=cutoff)
        if metric_ids is not None:
            fields["metrics"] = (
                "known"
                if row.id in metric_ids
                else "unknown"
                if unavailable is True or row.id in (unavailable or set())
                else "missing"
            )
        for key, state in fields.items():
            counts[key][state] += 1
    return {
        "record_count": total,
        "sample_count": len(rows),
        "coverage": dict(counts),
        "years": dict(years),
        "incomplete": total > len(rows),
        "limitations": ["Missing data is not zero", "Receipt confirmation time is not publication time"]
        + (["Bounded to 1000 records"] if total > len(rows) else []),
    }


@router.get("/learning/analysis")
def analyze(
    channel: str | None = None,
    content_account_id: int | None = None,
    content_form: str | None = None,
    metric_namespace: str | None = None,
    metric_key: str | None = None,
    unit: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    cutoff: datetime | None = None,
    identity_scope_type: str | None = None,
    identity_scope_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cutoff = query_time(cutoff)
    q = cohort(
        db, user, channel, content_account_id, date_from, date_to, content_form, identity_scope_type, identity_scope_id
    )
    ids = q.with_only_columns(PublishedContentRecord.id)
    obs = select(PerformanceObservation).where(
        PerformanceObservation.published_content_id.in_(ids), PerformanceObservation.numeric_value.is_not(None)
    )
    if metric_namespace:
        obs = obs.where(PerformanceObservation.metric_namespace == metric_namespace)
    if metric_key:
        obs = obs.where(PerformanceObservation.metric_key == metric_key)
    if unit:
        obs = obs.where(PerformanceObservation.unit == unit)
    if cutoff:
        obs = obs.where(PerformanceObservation.observed_at <= cutoff)
    observation_total = db.scalar(select(func.count()).select_from(obs.subquery()))
    observations = db.scalars(
        obs.order_by(PerformanceObservation.observed_at, PerformanceObservation.id).limit(10001)
    ).all()
    superseded = {r.supersedes_id for r in observations if r.supersedes_id}
    effective = [r for r in observations if r.id not in superseded] if len(observations) <= 10000 else []
    snapshots, intervals = {}, defaultdict(list)
    for row in effective:
        key = (row.published_content_id, *service.metric_scope(row))
        if key[4] == "snapshot":
            snapshots[key] = row
        else:
            intervals[(row.published_content_id, *key[1:4], key[7])].append(row)
    selected, limitations = (
        list(snapshots.values()),
        ["Incompatible metric keys/units/windows are not normalized", "Missing metrics are not zero"],
    )
    excluded = set()
    for values in intervals.values():
        values.sort(key=lambda r: r.period_start)
        if any(service.utc(a.period_end) > service.utc(b.period_start) for a, b in pairwise(values)):
            limitations.append("Overlapping interval observations excluded; scope cannot be aggregated")
            excluded.update(r.published_content_id for r in values)
        else:
            selected.extend(values)
    groups = defaultdict(list)
    for row in selected:
        groups[service.metric_scope(row)].append(row)
    result = []
    for key, values in groups.items():
        values.sort(key=lambda row: (service.utc(row.observed_at), row.id))
        nums = [r.numeric_value for r in values]
        result.append(
            {
                "metric_namespace": key[0],
                "metric_key": key[1],
                "unit": key[2],
                "measurement_mode": key[3],
                "period_start": key[4],
                "period_end": key[5],
                "granularity": key[6],
                "sample_count": len({r.published_content_id for r in values}),
                "sum": sum(nums),
                "min": min(nums),
                "max": max(nums),
                "average": sum(nums) / len(nums),
                "median": median(nums),
                "trend": [
                    {
                        "observed_at": r.observed_at,
                        "published_content_id": r.published_content_id,
                        "value": r.numeric_value,
                    }
                    for r in values[:100]
                ],
                "trend_incomplete": len(values) > 100,
            }
        )
    metrics_coverage = coverage_result(
        db, q, {r.published_content_id for r in selected}, cutoff, True if len(observations) > 10000 else excluded
    )
    dated_scope = cohort(
        db, user, channel, content_account_id, None, None, content_form, identity_scope_type, identity_scope_id
    )
    unknown_dates = db.scalar(
        select(func.count()).select_from(dated_scope.where(PublishedContentRecord.published_at.is_(None)).subquery())
    )
    if len(observations) > 10000:
        limitations.append(
            "Analysis unavailable: observation bound exceeded; narrow the cohort/cutoff before computing latest values"
        )
    missing_metrics = metrics_coverage["coverage"].get("metrics", {}).get("missing", 0)
    if missing_metrics:
        limitations.append("Incomplete metric coverage: comparisons may use different sampled populations")
    return {
        "groups": result,
        "record_count": metrics_coverage["record_count"],
        "observation_count": observation_total,
        "sampled_observation_count": len(observations),
        "sample_count": len({r.published_content_id for r in selected}),
        "coverage": metrics_coverage["coverage"],
        "missing_date_count": unknown_dates,
        "limitations": limitations,
        "incomplete": len(observations) > 10000 or metrics_coverage["incomplete"],
        "computed": len(observations) <= 10000,
    }
