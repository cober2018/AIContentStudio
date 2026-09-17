"""Asset 与 Export API（STU-120~123）。"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models import AuditLog, ContentAsset, DraftStatus, ExportRecord, User
from ..services import exports

router = APIRouter(prefix="/api/v1/assets", tags=["assets"])


class ExportIn(BaseModel):
    fmt: str  # md / txt / json / srt


def _serialize(db: Session, asset: ContentAsset) -> dict:
    return {
        "id": asset.id,
        "draft_id": asset.draft_id,
        "topic_id": asset.topic_brief_id,
        "channel": asset.channel,
        "title": asset.title,
        "status": asset.status,
        "fact_pack": {
            "id": asset.fact_pack_id,
            "version": asset.fact_pack_version,
            "checksum": asset.fact_pack_checksum,
        },
        "model": {"provider": asset.model_provider, "model": asset.model_name},
        "prompt_version": asset.prompt_version,
        "reviewer": asset.reviewer,
        "approved_revision": asset.approved_revision,
        "created_at": asset.created_at.isoformat() if asset.created_at else None,
        "allowed_formats": exports.CHANNEL_ALLOWED_FORMATS.get(asset.channel, ["md", "txt", "json"]),
        "export_count": _export_count(db, asset.id),
    }


def _export_count(db: Session, asset_id: int) -> int:
    return len(db.scalars(select(ExportRecord).where(ExportRecord.asset_id == asset_id)).all())


@router.get("")
def list_assets(
    channel: str | None = None,
    topic_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(ContentAsset).order_by(ContentAsset.created_at.desc())
    if channel:
        stmt = stmt.where(ContentAsset.channel == channel)
    if topic_id:
        stmt = stmt.where(ContentAsset.topic_brief_id == topic_id)
    return [_serialize(db, a) for a in db.scalars(stmt)]


@router.get("/{asset_id}")
def get_asset(asset_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    asset = db.get(ContentAsset, asset_id)
    if not asset:
        raise HTTPException(404, "Asset 不存在")
    data = _serialize(db, asset)
    data["final_body"] = asset.final_body
    data["structured"] = asset.structured_json
    return data


@router.post("/{asset_id}/export")
def export_asset(
    asset_id: int,
    payload: ExportIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    asset = db.get(ContentAsset, asset_id)
    if not asset:
        raise HTTPException(404, "Asset 不存在")
    allowed = exports.CHANNEL_ALLOWED_FORMATS.get(asset.channel, ["md", "txt", "json"])
    if payload.fmt not in allowed:
        raise HTTPException(400, f"渠道 {asset.channel} 不支持 {payload.fmt}，允许：{allowed}")

    try:
        content = exports.EXPORTERS[payload.fmt](asset)
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    db.add(ExportRecord(asset_id=asset.id, fmt=payload.fmt, exported_by=user.email))
    if asset.status == "approved":
        asset.status = DraftStatus.exported.value
    db.add(AuditLog(event="asset.exported", actor=user.email, entity_type="content_asset", entity_id=str(asset.id),
                    detail_json={"fmt": payload.fmt}))
    db.commit()

    filename = f"asset-{asset.id}-{asset.channel}-v{asset.fact_pack_version}.{payload.fmt}"
    # 对象存储启用时产物另传一份并返回预签名 URL；上传失败不阻断导出
    from ..services import storage_service

    download_url = storage_service.export_to_storage(filename, content)
    return {
        "asset_id": asset.id,
        "fmt": payload.fmt,
        "filename": filename,
        "content": content,
        "download_url": download_url,
    }
