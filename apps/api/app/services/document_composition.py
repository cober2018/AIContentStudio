"""Draft Document v1（D11）：图文 composition 的构建与操作。

Markdown 仍是文本真源；document_json 只保存图片位置/卡片顺序/平台渲染所需结构。
placement 变化 → staleness.mark_media_changed（candidate/render stale）。
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from ..models import Draft, DraftMedia
from .content_harness import staleness

DOCUMENT_SCHEMA_VERSION = 1


def build_document_from_body(body: str, media: list[DraftMedia]) -> dict:
    """从 Markdown 正文 + 有序 DraftMedia 构建 Document v1。

    块序：按 sort_order 把图片插入到正文段落之后（cover 在最前）。
    """
    blocks: list[dict] = []
    ordered = sorted(media, key=lambda m: (0 if m.role == "cover" else 1, m.sort_order))
    cover = [m for m in ordered if m.role == "cover"]
    inline = [m for m in ordered if m.role != "cover"]
    for item in cover:
        blocks.append(_image_block(item))
    for paragraph_no, para in enumerate((p for p in (body or "").split("\n\n") if p.strip()), 1):
        blocks.append({"id": f"p{paragraph_no}", "type": "paragraph", "text": para.strip()})
        if inline:
            item = inline.pop(0)
            blocks.append(_image_block(item))
    for item in inline:  # 剩余图片追加在文末
        blocks.append(_image_block(item))
    return {"schema_version": DOCUMENT_SCHEMA_VERSION, "blocks": blocks}


def _image_block(item: DraftMedia) -> dict:
    return {
        "id": f"img{item.id}",
        "type": "image",
        "draft_media_id": item.id,
        "material_revision_id": item.material_revision_id,
        "alt": item.alt_text,
        "caption": item.caption,
        "placement": item.placement_json or {},
    }


def sync_document(db: Session, draft: Draft) -> dict:
    """media/body 变化后重建 document（覆盖式；手工 composition 由 set_document 保存）。"""
    draft.document_json = build_document_from_body(draft.body, list(draft.media))
    draft.document_schema_version = DOCUMENT_SCHEMA_VERSION
    return draft.document_json


def set_document(db: Session, draft: Draft, document: dict) -> dict:
    """保存用户编排的 composition：校验 image 块引用的 draft_media 归属当前稿。"""
    if document.get("schema_version") not in (None, DOCUMENT_SCHEMA_VERSION):
        raise ValueError(f"不支持的 document schema: {document.get('schema_version')}")
    blocks = document.get("blocks")
    if not isinstance(blocks, list):
        raise TypeError("document.blocks 必须是数组")
    own_media_ids = {m.id for m in draft.media}
    for block in blocks:
        if block.get("type") == "image":
            ref = block.get("draft_media_id")
            if ref not in own_media_ids:
                raise ValueError(f"image 块引用了不属于自己的素材: {ref}")
    draft.document_json = {"schema_version": DOCUMENT_SCHEMA_VERSION, "blocks": blocks}
    draft.document_schema_version = DOCUMENT_SCHEMA_VERSION
    staleness.mark_media_changed(db, draft, reason="document_composition_changed")
    return draft.document_json
