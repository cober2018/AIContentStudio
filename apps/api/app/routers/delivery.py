"""通用交付 API（§6.25）：targets/execute/package/receipt/feedback/reconcile。

旧 `/article-handoff/...` 路径保留为兼容 alias（M1 manual_handoff 语义不变）。
"""

from datetime import UTC

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.routing import APIRoute
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_editor
from ..models import (
    AuditLog,
    ContentAsset,
    DeliveryAction,
    DeliveryAttempt,
    DeliveryFeedback,
    DeliveryReceipt,
    DeliveryTarget,
    DeliveryTargetStatus,
    User,
    utcnow,
)
from ..services import capability_integrations, published_history
from ..services import delivery as delivery_service
from ..services.project_authorization import authorize_project_asset, authorize_project_target
from ..services.project_events import record_project_event


class ReconciliationRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()

        async def safe_handler(request: Request):
            try:
                return await handler(request)
            except RequestValidationError:
                # Default validation echoes request values that may contain secrets.
                if self.path.endswith(("/reconcile", "/official-readback")):
                    return JSONResponse(status_code=422, content={"detail": "reconciliation_input_invalid"})
                raise

        return safe_handler


router = APIRouter(prefix="/api/v1", tags=["delivery"], route_class=ReconciliationRoute)


class GenericTargetIn(BaseModel):
    channel: str
    content_form: str
    account_ref: str = Field(min_length=1, max_length=255)
    content_account_id: int | None = None
    authorization_version: str = Field(min_length=1, max_length=64)
    action: str = DeliveryAction.copy_package.value


class OfficialReadbackIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_attempt_id: int = Field(gt=0)


class ReceiptIn(BaseModel):
    status: str = Field(pattern="^(human_confirmed|reconciliation_needed|failed)$")
    evidence_ref: str | None = None
    verification_method: str | None = None
    note: str | None = None
    published_at: AwareDatetime | None = None
    publication_time_evidence: str | None = None

    @model_validator(mode="after")
    def validate_publication_time(self):
        if self.published_at is not None or self.publication_time_evidence is not None:
            if (self.status != "human_confirmed" or self.published_at is None
                    or not self.publication_time_evidence or not self.publication_time_evidence.strip()):
                raise ValueError("实际发布时间须由人工确认并提供非空依据")
            self.published_at = self.published_at.astimezone(UTC)
        return self


class FeedbackIn(BaseModel):
    kind: str = "note"
    body: str = Field(min_length=1)


class ReconcileIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    resolution: str = Field(pattern="^(delivered|not_delivered)$")
    note: str | None = Field(default=None, max_length=2000)
    evidence_ref: str | None = Field(default=None, pattern="^sha256:[0-9a-f]{64}$")
    expected_attempt_id: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def require_evidence(self):
        if self.evidence_ref is None and not (self.note or "").strip():
            raise ValueError("对账须提供非空核验说明或证据摘要")
        return self


def _target_json(target: DeliveryTarget, with_attempts: bool = True) -> dict:
    data = {
        "id": target.id,
        "asset_id": target.content_asset_id,
        "channel": target.channel,
        "content_form": target.content_form,
        "account_ref": target.account_ref,
        "content_account_id": target.content_account_id,
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


def _own_target(db: Session, target_id: int, user: User, *, mutate: bool = False) -> DeliveryTarget:
    target = db.get(DeliveryTarget, target_id)
    if not target:
        raise HTTPException(404, "交付目标不存在")
    authorize_project_target(db, target, user, mutate=mutate)
    if target.authorized_by and target.authorized_by != user.email:
        raise HTTPException(403, "该账号交付目标未授权给当前操作人")
    if mutate and target.publisher_key == "publisher.wechat.official" and target.publisher_version == "1":
        from sqlalchemy import update

        from ..services.project_authorization import lock_project_context

        asset = db.get(ContentAsset, target.content_asset_id)
        if asset.project_id is not None:
            lock_project_context(db, asset.project_id, user)
        db.execute(update(DeliveryTarget).where(DeliveryTarget.id == target.id).values(status=DeliveryTarget.status)
                   .execution_options(synchronize_session=False))
        db.refresh(target)
        authorize_project_target(db, target, user, mutate=True)
        if target.authorized_by and target.authorized_by != user.email:
            raise HTTPException(403, "该账号交付目标未授权给当前操作人")
    return target


@router.post("/assets/{asset_id}/delivery-targets", status_code=201)
def create_delivery_target(asset_id: int, payload: GenericTargetIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    asset = db.get(ContentAsset, asset_id)
    if not asset:
        raise HTTPException(404, "批准资产不存在")
    authorize_project_asset(db, asset, user, mutate=True)
    target = delivery_service.authorize_target(db, asset, payload, user)
    return _target_json(target)


@router.get("/assets/{asset_id}/delivery-targets")
def list_delivery_targets(asset_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    asset = db.get(ContentAsset, asset_id)
    if asset is not None:
        authorize_project_asset(db, asset, user)
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


@router.post("/delivery-targets/{target_id}/official-readback")
def readback_official_target(target_id: int, payload: OfficialReadbackIn,
                            db: Session = Depends(get_db), user: User = Depends(require_editor)):
    from ..services.wechat_official_delivery import readback

    return readback(db, target_id, payload.expected_attempt_id, user)


@router.get("/delivery-targets/{target_id}/package.zip")
def download_package(target_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    target = _own_target(db, target_id, user, mutate=True)
    if target.status == DeliveryTargetStatus.blocked.value:
        raise HTTPException(409, "该目标的公开使用权限已撤销，不能再交付")
    data, filename = delivery_service.package_zip_bytes(db, target)
    if target.status in {DeliveryTargetStatus.target_authorized.value, DeliveryTargetStatus.package_ready.value}:
        target.status = DeliveryTargetStatus.awaiting_manual_receipt.value
        db.commit()
    return Response(content=data, media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.post("/delivery-targets/{target_id}/package")
def preview_package(target_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    target = _own_target(db, target_id, user, mutate=True)
    package = delivery_service.build_copy_package(db, target)
    # 与 M1 语义一致：成品包生成后等待人工发布回填
    if target.status in {DeliveryTargetStatus.target_authorized.value, DeliveryTargetStatus.package_ready.value}:
        target.status = DeliveryTargetStatus.awaiting_manual_receipt.value
    db.commit()
    return package


@router.post("/delivery-targets/{target_id}/receipt")
def add_receipt(target_id: int, payload: ReceiptIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    target = _own_target(db, target_id, user, mutate=True)
    if (target.publisher_key == "publisher.wechat.official" and target.publisher_version == "1"
            and target.action == "auto_draft"
            and (payload.published_at is not None or payload.publication_time_evidence is not None)):
        raise HTTPException(422, "official_draft_receipt_cannot_claim_publication")
    if (target.publisher_key == "publisher.wechat.official" and target.publisher_version == "1"
            and target.action == "auto_draft" and db.scalar(select(DeliveryAttempt.id).where(
                DeliveryAttempt.target_id == target.id, DeliveryAttempt.status.in_(["prepared", "running"])).limit(1))):
        raise HTTPException(409, "official_reconciliation_required")
    if target.status == DeliveryTargetStatus.reconciliation_needed.value or any(
        attempt.status == "unknown" and (attempt.response_metadata_json or {}).get("reconciled") is None
        for attempt in target.attempts
    ):
        raise HTTPException(409, "交付结果待核对，必须先完成对账")
    key_parts = [
        str(target.id), target.approved_candidate_hash, payload.status,
        payload.evidence_ref or "", payload.verification_method or "", payload.note or "",
    ]
    # Preserve old receipt keys so retries can repair missing history.
    if payload.published_at is not None:
        key_parts.extend([payload.published_at.isoformat(), payload.publication_time_evidence])
    idempotency_key = delivery_service._hash(*key_parts)
    existing = db.scalars(
        select(DeliveryReceipt).where(DeliveryReceipt.target_id == target.id, DeliveryReceipt.idempotency_key == idempotency_key)
    ).first()
    if existing:
        try:
            db.flush()
            published_history.sync_receipt(db, user, existing, published_at=payload.published_at,
                                           publication_time_evidence=payload.publication_time_evidence)
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, "回执或发布历史保存冲突，请重试")
        except Exception:
            db.rollback()
            raise
        return _target_json(target, with_attempts=False)
    if target.status not in {
        DeliveryTargetStatus.awaiting_manual_receipt.value,
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
    asset = db.get(ContentAsset, target.content_asset_id)
    try:
        db.flush()
        published_history.sync_receipt(db, user, receipt, published_at=payload.published_at,
                                       publication_time_evidence=payload.publication_time_evidence)
        if asset.project_id is not None:
            record_project_event(db, project_id=asset.project_id, event_type="delivery.receipt_recorded", actor=user.email,
                                 entity_type="delivery_receipt", entity_id=receipt.id,
                                 payload={"unit_id": asset.content_unit_id, "candidate_id": asset.id, "target_id": target.id, "status": receipt.status})
        capability_integrations.promote_confirmed_official_draft(db, target, receipt, user.email)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(409, str(exc)) from exc
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "回执或发布历史保存冲突，请重试")
    except Exception:
        db.rollback()
        raise
    return _target_json(target, with_attempts=False)


@router.post("/delivery-targets/{target_id}/feedback", status_code=201)
def add_feedback(target_id: int, payload: FeedbackIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    target = _own_target(db, target_id, user, mutate=True)
    row = DeliveryFeedback(target_id=target.id, kind=payload.kind, body=payload.body, observed_at=utcnow(), created_by=user.email)
    db.add(row)
    db.add(AuditLog(event="delivery_feedback.recorded", actor=user.email, entity_type="delivery_target", entity_id=str(target.id)))
    db.commit()
    return {"id": row.id, "target_id": target.id, "kind": row.kind, "body": row.body}


@router.post("/delivery-targets/{target_id}/reconcile")
def reconcile(target_id: int, payload: ReconcileIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    """unknown 远端结果的人工对账契约（不自动重发）。"""
    return delivery_service.reconcile_attempt(db, target_id, payload, user)
