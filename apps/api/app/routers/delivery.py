"""通用交付 API（§6.25）：targets/execute/package/receipt/feedback/reconcile。

旧 `/article-handoff/...` 路径保留为兼容 alias（M1 manual_handoff 语义不变）。
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_editor
from ..models import (
    AuditLog,
    ContentAsset,
    DeliveryAction,
    DeliveryFeedback,
    DeliveryReceipt,
    DeliveryTarget,
    DeliveryTargetStatus,
    User,
    utcnow,
)
from ..services import delivery as delivery_service

router = APIRouter(prefix="/api/v1", tags=["delivery"])


class GenericTargetIn(BaseModel):
    channel: str
    content_form: str
    account_ref: str = Field(min_length=1, max_length=255)
    authorization_version: str = Field(min_length=1, max_length=64)
    action: str = DeliveryAction.copy_package.value


class ReceiptIn(BaseModel):
    status: str = Field(pattern="^(human_confirmed|reconciliation_needed|failed)$")
    evidence_ref: str | None = None
    verification_method: str | None = None
    note: str | None = None


class FeedbackIn(BaseModel):
    kind: str = "note"
    body: str = Field(min_length=1)


class ReconcileIn(BaseModel):
    resolution: str  # delivered / not_delivered
    note: str | None = None


def _target_json(target: DeliveryTarget, with_attempts: bool = True) -> dict:
    data = {
        "id": target.id,
        "asset_id": target.content_asset_id,
        "channel": target.channel,
        "content_form": target.content_form,
        "account_ref": target.account_ref,
        "action": target.action,
        "authorization_version": target.authorization_version,
        "status": target.status,
        "approved_candidate_hash": target.approved_candidate_hash,
        "publisher_key": target.publisher_key,
        "publisher_version": target.publisher_version,
        "capability": target.capability_snapshot_json,
        "requested_at": target.requested_at.isoformat() if target.requested_at else None,
        "receipts": [
            {"id": r.id, "status": r.status, "operator": r.operator, "evidence_ref": r.evidence_ref, "note": r.note}
            for r in target.receipts
        ],
    }
    if with_attempts:
        data["attempts"] = [
            {
                "id": a.id, "attempt_no": a.attempt_no, "status": a.status,
                "remote_id": a.remote_id, "error": a.error, "request_hash": a.request_hash,
                "started_at": a.started_at.isoformat() if a.started_at else None,
                "finished_at": a.finished_at.isoformat() if a.finished_at else None,
            }
            for a in target.attempts
        ]
    return data


def _own_target(db: Session, target_id: int, user: User) -> DeliveryTarget:
    target = db.get(DeliveryTarget, target_id)
    if not target:
        raise HTTPException(404, "交付目标不存在")
    if target.authorized_by and target.authorized_by != user.email:
        raise HTTPException(403, "该账号交付目标未授权给当前操作人")
    return target


@router.post("/assets/{asset_id}/delivery-targets", status_code=201)
def create_delivery_target(asset_id: int, payload: GenericTargetIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    asset = db.get(ContentAsset, asset_id)
    if not asset:
        raise HTTPException(404, "批准资产不存在")
    target = delivery_service.authorize_target(db, asset, payload, user)
    return _target_json(target)


@router.get("/assets/{asset_id}/delivery-targets")
def list_delivery_targets(asset_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(
        select(DeliveryTarget).where(DeliveryTarget.content_asset_id == asset_id, DeliveryTarget.authorized_by == user.email)
        .order_by(DeliveryTarget.id.desc())
    ).all()
    return [_target_json(t) for t in rows]


@router.get("/delivery-targets/{target_id}")
def get_delivery_target(target_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _target_json(_own_target(db, target_id, user))


@router.post("/delivery-targets/{target_id}/execute")
def execute_delivery_target(target_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    """远端副作用唯一入口：prepared→COMMIT→publisher→result；unknown 不自动重发。"""
    result = delivery_service.execute_attempt(db, target_id, user)
    return result


@router.get("/delivery-targets/{target_id}/package.zip")
def download_package(target_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    target = _own_target(db, target_id, user)
    if target.status == DeliveryTargetStatus.blocked.value:
        raise HTTPException(409, "该目标的公开使用权限已撤销，不能再交付")
    if target.action == DeliveryAction.manual_handoff.value:
        # v1 M1 目标：复用既有成品包路径（兼容 alias 反向：新路径委托旧实现）
        from .article_handoff import download_package_archive

        return download_package_archive(target_id, db, user)
    data, filename = delivery_service.package_zip_bytes(db, target)
    return Response(content=data, media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.post("/delivery-targets/{target_id}/package")
def preview_package(target_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    target = _own_target(db, target_id, user)
    if target.action == DeliveryAction.manual_handoff.value:
        from .article_handoff import get_package

        return get_package(target_id, db, user)
    package = delivery_service.build_copy_package(db, target)
    # 与 M1 语义一致：成品包生成后等待人工发布回填
    if target.status in {DeliveryTargetStatus.target_authorized.value, DeliveryTargetStatus.package_ready.value}:
        target.status = DeliveryTargetStatus.awaiting_manual_receipt.value
    db.commit()
    return package


@router.post("/delivery-targets/{target_id}/receipt")
def add_receipt(target_id: int, payload: ReceiptIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    target = _own_target(db, target_id, user)
    idempotency_key = delivery_service._hash(
        str(target.id), target.approved_candidate_hash, payload.status,
        payload.evidence_ref or "", payload.verification_method or "", payload.note or "",
    )
    existing = db.scalars(
        select(DeliveryReceipt).where(DeliveryReceipt.target_id == target.id, DeliveryReceipt.idempotency_key == idempotency_key)
    ).first()
    if existing:
        return _target_json(target, with_attempts=False)
    if target.status not in {
        DeliveryTargetStatus.awaiting_manual_receipt.value,
        DeliveryTargetStatus.reconciliation_needed.value,
        DeliveryTargetStatus.failed.value,
    }:
        raise HTTPException(409, "目标尚未生成成品包/未执行交付，或当前状态不可回填")
    receipt = DeliveryReceipt(
        target_id=target.id,
        approved_candidate_hash=target.approved_candidate_hash,
        action=target.action,
        idempotency_key=idempotency_key,
        status=payload.status,
        operator=user.email,
        delivered_at=utcnow(),
        evidence_ref=payload.evidence_ref,
        verification_method=payload.verification_method,
        note=payload.note,
    )
    target.status = {
        "human_confirmed": DeliveryTargetStatus.human_confirmed.value,
        "reconciliation_needed": DeliveryTargetStatus.reconciliation_needed.value,
        "failed": DeliveryTargetStatus.failed.value,
    }[payload.status]
    db.add(receipt)
    db.add(AuditLog(event="delivery_receipt.recorded", actor=user.email, entity_type="delivery_target",
                    entity_id=str(target.id), detail_json={"status": target.status, "platform_verified": False}))
    db.commit()
    return _target_json(target, with_attempts=False)


@router.post("/delivery-targets/{target_id}/feedback", status_code=201)
def add_feedback(target_id: int, payload: FeedbackIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    target = _own_target(db, target_id, user)
    row = DeliveryFeedback(target_id=target.id, kind=payload.kind, body=payload.body, observed_at=utcnow(), created_by=user.email)
    db.add(row)
    db.add(AuditLog(event="delivery_feedback.recorded", actor=user.email, entity_type="delivery_target", entity_id=str(target.id)))
    db.commit()
    return {"id": row.id, "target_id": target.id, "kind": row.kind, "body": row.body}


@router.post("/delivery-targets/{target_id}/reconcile")
def reconcile(target_id: int, payload: ReconcileIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    """unknown 远端结果的人工对账契约（不自动重发）。"""
    return delivery_service.reconcile_attempt(db, target_id, payload, user)
