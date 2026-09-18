"""资产配图素材服务：统一素材池（asset_media 表），按文章归属展示。

- 懒生成：资产首次查看素材时，从 structured_json 提取配图说明（小红书 image_prompts /
  公众号 image_suggestions / 封面文案）生成占位素材位，不依赖具体生图平台（PRD §6.7）；
- 上传：编辑可上传实体图片替换占位（jpg/png/webp，单张 ≤5MB），落 apps/api/media/；
- 占位渲染：动态 SVG（渠道配色 + 配图说明文字），接入生图平台前的承接层。
"""

import html
from pathlib import Path

from fastapi import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import AssetMedia, ContentAsset

MEDIA_ROOT = Path(__file__).resolve().parents[1] / "media"
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
ALLOWED_MIME = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
MAX_INLINE_SLOTS = 9


def _extract_prompts(asset: ContentAsset) -> tuple[str, list[str]]:
    """封面文案 + 文内配图说明列表（按渠道结构字段提取）。"""
    structured = asset.structured_json or {}
    cover = structured.get("cover_text") or (structured.get("titles") or [asset.title])[0] if structured else asset.title
    prompts: list[str] = []
    raw = structured.get("image_prompts") or structured.get("image_suggestions") or []
    for item in raw:
        if isinstance(item, dict):
            item = item.get("prompt") or item.get("suggestion") or item.get("text") or ""
        if isinstance(item, str) and item.strip():
            prompts.append(item.strip()[:300])
    return str(cover), prompts[:MAX_INLINE_SLOTS]


def ensure_generated(db: Session, asset: ContentAsset) -> None:
    """该资产还没有素材位时，按 structured_json 生成封面 + 配图占位（幂等懒加载，老资产同样生效）。"""
    existing = db.scalars(select(AssetMedia).where(AssetMedia.asset_id == asset.id).limit(1)).first()
    if existing is not None:
        return
    cover_text, prompts = _extract_prompts(asset)
    db.add(AssetMedia(asset_id=asset.id, kind="cover", source="generated", prompt=cover_text, sort_order=0))
    for i, prompt in enumerate(prompts, start=1):
        db.add(AssetMedia(asset_id=asset.id, kind="inline", source="generated", prompt=prompt, sort_order=i))
    db.commit()


def list_for(db: Session, asset: ContentAsset) -> list[dict]:
    ensure_generated(db, asset)
    rows = db.scalars(
        select(AssetMedia).where(AssetMedia.asset_id == asset.id).order_by(AssetMedia.sort_order, AssetMedia.id)
    ).all()
    return [
        {
            "id": m.id,
            "kind": m.kind,
            "source": m.source,
            "prompt": m.prompt,
            "mime_type": m.mime_type,
            "sort_order": m.sort_order,
            "url": f"/api/v1/assets/{asset.id}/media/{m.id}/raw",
        }
        for m in rows
    ]


def save_upload(db: Session, asset: ContentAsset, media: AssetMedia, filename: str, content: bytes, mime: str) -> None:
    ext = ALLOWED_MIME.get(mime)
    if ext is None:
        raise ValueError(f"仅支持 {'/'.join(ALLOWED_MIME.values())} 图片")
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError("单张图片不能超过 5MB")
    target_dir = MEDIA_ROOT / str(asset.id)
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{media.id}.{ext}"
    target.write_bytes(content)
    # 上传只增不改：替换 = 新增一条 upload 记录顶到同序位，历史保留（与 revision 不覆盖同哲学）
    db.add(
        AssetMedia(
            asset_id=asset.id,
            kind=media.kind,
            source="upload",
            prompt=media.prompt,
            file_path=str(target.relative_to(MEDIA_ROOT)),
            mime_type=mime,
            sort_order=media.sort_order,
        )
    )
    db.commit()


def raw_response(db: Session, asset: ContentAsset, media: AssetMedia) -> Response:
    """素材本体：上传图回文件，占位图动态渲染 SVG（渠道配色 + 配图说明）。"""
    if media.source == "upload" and media.file_path:
        path = (MEDIA_ROOT / media.file_path).resolve()
        if not str(path).startswith(str(MEDIA_ROOT.resolve())) or not path.is_file():
            return Response(content="素材文件缺失", status_code=404, media_type="text/plain")
        return Response(content=path.read_bytes(), media_type=media.mime_type or "application/octet-stream")
    themes = {
        "douyin": ("#111827", "#22d3ee", "抖音配图"),
        "xiaohongshu": ("#7f1d1d", "#f87171", "小红书配图"),
        "wechat": ("#14532d", "#4ade80", "公众号配图"),
    }
    bg, accent, label = themes.get(asset.channel, ("#1e293b", "#818cf8", "配图"))
    kind_label = "封面" if media.kind == "cover" else f"配图 {media.sort_order}"
    prompt = html.escape((media.prompt or "")[:80])
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="640" height="640" viewBox="0 0 640 640">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{bg}"/><stop offset="1" stop-color="{accent}" stop-opacity="0.6"/>
  </linearGradient></defs>
  <rect width="640" height="640" fill="url(#g)" rx="12"/>
  <rect x="40" y="40" width="110" height="30" rx="15" fill="#ffffff" opacity="0.9"/>
  <text x="95" y="61" font-family="PingFang SC, sans-serif" font-size="14" fill="{bg}" text-anchor="middle" font-weight="600">{kind_label}占位</text>
  <text x="40" y="560" font-family="PingFang SC, sans-serif" font-size="18" fill="#ffffff" opacity="0.95">{label}</text>
  <text x="40" y="592" font-family="PingFang SC, sans-serif" font-size="13" fill="#ffffff" opacity="0.75">{prompt}</text>
  <text x="40" y="120" font-family="PingFang SC, sans-serif" font-size="42" fill="#ffffff" opacity="0.35">🖼</text>
</svg>"""
    return Response(content=svg, media_type="image/svg+xml")
