"""Asset 与 Export API（STU-120~123）。"""

import html

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_editor
from ..models import AssetMedia, AuditLog, ContentAsset, DraftStatus, ExportRecord, User
from ..services import asset_media, exports

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
        "mother_revision_id": asset.mother_revision_id,
        "approved_candidate_hash": asset.approved_candidate_hash,
        "candidate_manifest": asset.candidate_manifest_json,
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


@router.get("/{asset_id}/cover.svg")
def asset_cover(asset_id: int, db: Session = Depends(get_db)):
    """动态封面图（SVG，前端 <img> 直接引用故不做 Header 鉴权，内容仅标题/渠道/日期）。"""
    asset = db.get(ContentAsset, asset_id)
    if not asset:
        raise HTTPException(404, "Asset 不存在")
    themes = {
        "douyin": ("#111827", "#22d3ee", "#ec4899", "抖音口播"),
        "xiaohongshu": ("#7f1d1d", "#f87171", "#fbbf24", "小红书图文"),
        "wechat": ("#14532d", "#4ade80", "#a7f3d0", "公众号文章"),
    }
    bg, accent, accent2, channel_label = themes.get(asset.channel, ("#1e293b", "#818cf8", "#c7d2fe", asset.channel))
    title = html.escape(asset.title or "未命名内容")
    if len(asset.title or "") > 26:
        # 手动断两行，SVG text 不自动换行
        title = html.escape(asset.title[:26]) + "<tspan x='60' dy='52'>" + html.escape((asset.title)[26:52]) + ("…" if len(asset.title) > 52 else "") + "</tspan>"
    date = (asset.created_at.strftime("%Y-%m-%d") if asset.created_at else "")
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360" viewBox="0 0 640 360">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{bg}"/><stop offset="1" stop-color="{accent}" stop-opacity="0.55"/>
    </linearGradient>
  </defs>
  <rect width="640" height="360" fill="url(#g)" rx="16"/>
  <circle cx="580" cy="40" r="90" fill="{accent2}" opacity="0.18"/>
  <circle cx="60" cy="330" r="70" fill="{accent}" opacity="0.22"/>
  <rect x="60" y="58" width="96" height="28" rx="14" fill="{accent2}" opacity="0.9"/>
  <text x="108" y="77" font-family="PingFang SC, sans-serif" font-size="14" fill="{bg}" text-anchor="middle" font-weight="600">{channel_label}</text>
  <text x="60" y="150" font-family="PingFang SC, sans-serif" font-size="30" fill="#ffffff" font-weight="700">{title}</text>
  <text x="60" y="300" font-family="PingFang SC, sans-serif" font-size="16" fill="#e2e8f0" opacity="0.85">{date} · 事实包 v{asset.fact_pack_version} · {html.escape(asset.model_name or "")}</text>
</svg>"""
    return Response(content=svg, media_type="image/svg+xml")


@router.get("/{asset_id}/media")
def list_asset_media(asset_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """素材列表（懒生成占位位：小红书 image_prompts / 公众号 image_suggestions / 封面文案）。"""
    asset = db.get(ContentAsset, asset_id)
    if not asset:
        raise HTTPException(404, "Asset 不存在")
    return asset_media.list_for(db, asset)


class MediaSlotIn(BaseModel):
    kind: str = "inline"  # cover / inline
    prompt: str = ""


@router.post("/{asset_id}/media", status_code=201)
def add_media_slot(
    asset_id: int,
    payload: MediaSlotIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_editor),
):
    """手动加一个配图位（占位，可随后上传实体图）。"""
    asset = db.get(ContentAsset, asset_id)
    if not asset:
        raise HTTPException(404, "Asset 不存在")
    if payload.kind not in ("cover", "inline"):
        raise HTTPException(422, "kind 只允许 cover / inline")
    next_order = asset_media.list_for(db, asset)[-1]["sort_order"] + 1 if asset_media.list_for(db, asset) else 1
    row = AssetMedia(asset_id=asset_id, kind=payload.kind, source="generated", prompt=payload.prompt or None, sort_order=next_order)
    db.add(row)
    db.commit()
    return {"id": row.id, "kind": row.kind, "prompt": row.prompt, "sort_order": row.sort_order}


@router.post("/{asset_id}/media/{media_id}/upload")
async def upload_asset_media(
    asset_id: int,
    media_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_editor),
):
    """上传实体图替换占位（只增不改：新记录顶同序位，历史保留）。"""
    asset = db.get(ContentAsset, asset_id)
    media = db.get(AssetMedia, media_id)
    if not asset or not media or media.asset_id != asset_id:
        raise HTTPException(404, "素材位不存在")
    content = await file.read()
    try:
        asset_media.save_upload(db, asset, media, file.filename or "", content, file.content_type or "")
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    db.add(AuditLog(event="asset.media_uploaded", actor=user.email, entity_type="content_asset",
                    entity_id=str(asset_id), detail_json={"media_id": media_id}))
    db.commit()
    return {"ok": True}


@router.get("/{asset_id}/media/{media_id}/raw")
def raw_asset_media(asset_id: int, media_id: int, db: Session = Depends(get_db)):
    """素材本体（占位 SVG / 上传图片）；<img> 直接引用故不做 Header 鉴权，内容仅配图说明。"""
    asset = db.get(ContentAsset, asset_id)
    media = db.get(AssetMedia, media_id)
    if not asset or not media or media.asset_id != asset_id:
        raise HTTPException(404, "素材不存在")
    return asset_media.raw_response(db, asset, media)


@router.delete("/{asset_id}/media/{media_id}")
def delete_asset_media(
    asset_id: int,
    media_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_editor),
):
    media = db.get(AssetMedia, media_id)
    if not media or media.asset_id != asset_id:
        raise HTTPException(404, "素材不存在")
    db.delete(media)
    db.commit()
    return {"deleted": True}


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
