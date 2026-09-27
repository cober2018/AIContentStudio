"""Material Library 服务（D9/§6.14）：新正式素材写入的唯一入口。

文件存储复用 MEDIA_ROOT（content-addressed 路径）；上传双校验 MIME + 魔数签名。
被 approved Candidate 引用的 Revision 不可变：替换=新 Revision（§6.14 rights 链路）。
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import (
    ContentAsset,
    Draft,
    DraftMedia,
    Material,
    MaterialKind,
    MaterialRevision,
    MaterialRevisionStatus,
    MaterialSourceKind,
)
from .content_harness import staleness

# 允许上传的图片/媒体魔数（双校验：MIME 由客户端声明，签名由字节证实）
_SIGNATURES: list[tuple[bytes, str]] = [
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
    (b"RIFF", "image/webp"),  # WEBP：RIFF....WEBP
    (b"%PDF", "application/pdf"),
    (b"ID3", "audio/mpeg"),
    (b"\x00\x00\x00", "video/mp4"),  # ftyp box 前缀
]
FALLBACK_MIME = "application/octet-stream"


def sniff_mime(content: bytes, declared: str | None) -> str:
    """魔数优先；识别不出时回退声明的白名单前缀，再回退 octet-stream。"""
    for magic, mime in _SIGNATURES:
        if content.startswith(magic):
            if mime == "image/webp" and content[8:12] != b"WEBP":
                continue
            if mime == "video/mp4" and content[4:8] != b"ftyp":
                continue
            return mime
    if declared and declared.startswith(("image/", "audio/", "video/", "application/pdf")):
        return declared
    return FALLBACK_MIME


def validate_upload(content: bytes, declared_mime: str | None) -> str:
    if not content:
        raise HTTPException(422, "素材文件为空")
    if len(content) > 30 * 1024 * 1024:
        raise HTTPException(413, "素材超过 30MB 上限")
    mime = sniff_mime(content, declared_mime)
    if mime == FALLBACK_MIME:
        raise HTTPException(422, "无法识别的文件类型（允许 PNG/JPEG/GIF/WebP/PDF/MP4/MP3）")
    return mime


def store_bytes(db: Session, content: bytes, *, subdir: str, suffix: str) -> tuple[str, str]:
    """content-addressed 存储；返回 (relative_path, content_hash)。"""
    from .asset_media import MEDIA_ROOT

    content_hash = hashlib.sha256(content).hexdigest()
    if subdir == "material":
        from .material_byte_lock import hold_until_transaction_end

        hold_until_transaction_end(db, content_hash)
    relative = Path(subdir) / content_hash[:2] / f"{content_hash}{suffix}"
    absolute = MEDIA_ROOT / relative
    absolute.parent.mkdir(parents=True, exist_ok=True)
    if not absolute.exists():
        absolute.write_bytes(content)
    return str(relative), content_hash


def create_material(
    db: Session,
    *,
    kind: str,
    title: str,
    tags: list | None = None,
    created_by: str | None = None,
) -> Material:
    if kind not in {k.value for k in MaterialKind}:
        raise HTTPException(422, f"非法素材类型: {kind}")
    row = Material(kind=kind, title=title, tags_json=tags or [], created_by=created_by)
    db.add(row)
    db.flush()
    return row


def create_revision(
    db: Session,
    material: Material,
    *,
    content: bytes,
    suffix: str = ".bin",
    declared_mime: str | None = None,
    source_kind: str = MaterialSourceKind.upload.value,
    source_url: str | None = None,
    source_metadata: dict | None = None,
    rights_status: str = "cleared",
    public_use_allowed: bool = False,
    model_use_allowed: bool = False,
    commercial_use_allowed: bool | None = None,
    attribution_text: str | None = None,
    provider_key: str | None = None,
    provider_version: str | None = None,
    prompt_text: str | None = None,
    width: int | None = None,
    height: int | None = None,
    duration_ms: int | None = None,
    metadata: dict | None = None,
    created_by: str | None = None,
) -> MaterialRevision:
    if source_kind not in {k.value for k in MaterialSourceKind}:
        raise HTTPException(422, f"非法素材来源: {source_kind}")
    mime = validate_upload(content, declared_mime) if source_kind != MaterialSourceKind.legacy.value else (declared_mime or FALLBACK_MIME)
    relative, content_hash = store_bytes(db, content, subdir="material", suffix=suffix)
    latest_no = db.scalar(
        select(MaterialRevision.revision_no)
        .where(MaterialRevision.material_id == material.id)
        .order_by(MaterialRevision.revision_no.desc())
        .limit(1)
    )
    row = MaterialRevision(
        material_id=material.id,
        revision_no=(latest_no or 0) + 1,
        source_kind=source_kind,
        source_url=source_url,
        source_metadata_json=source_metadata or {},
        content_hash=content_hash,
        file_path=relative,
        mime_type=mime,
        width=width,
        height=height,
        duration_ms=duration_ms,
        rights_status=rights_status,
        public_use_allowed=public_use_allowed,
        model_use_allowed=model_use_allowed,
        commercial_use_allowed=commercial_use_allowed,
        attribution_text=attribution_text,
        provider_key=provider_key,
        provider_version=provider_version,
        prompt_text=prompt_text,
        metadata_json=metadata or {},
        created_by=created_by,
    )
    db.add(row)
    db.flush()
    return row


def approved_revision_ids(db: Session) -> set[int]:
    """被 schema v2 批准候选引用的 material_revision ids（v1 manifest 只引用 DraftMedia）。"""
    ids: set[int] = set()
    assets = db.scalars(select(ContentAsset).where(ContentAsset.approved_candidate_hash.is_not(None))).all()
    for asset in assets:
        for media in (asset.candidate_manifest_json or {}).get("media", []):
            rid = media.get("material_revision_id")
            if isinstance(rid, int):
                ids.add(rid)
    return ids


# 兼容别名（router 历史引用）
_approved_revision_ids = approved_revision_ids


def attach_to_draft(
    db: Session,
    draft: Draft,
    revision: MaterialRevision,
    *,
    role: str = "inline",
    sort_order: int | None = None,
    alt_text: str | None = None,
    caption: str | None = None,
    placement: dict | None = None,
) -> DraftMedia:
    """MaterialRevision → DraftMedia(use)。同稿同 hash 幂等返回已有 use。"""
    if draft.status == "approved":
        raise HTTPException(409, "已批准稿件的素材不可修改")
    existing = db.scalars(
        select(DraftMedia).where(DraftMedia.draft_id == draft.id, DraftMedia.content_hash == revision.content_hash)
    ).first()
    if existing:
        return existing
    row = DraftMedia(
        draft_id=draft.id,
        content_hash=revision.content_hash,
        role=role,
        sort_order=len(draft.media) if sort_order is None else sort_order,
        material_revision_id=revision.id,
        mime_type=revision.mime_type,
        rights_status=revision.rights_status,
        public_use_allowed=revision.public_use_allowed,
        alt_text=alt_text,
        caption=caption,
        placement_json=placement,
        metadata_json={"via": "material_library"},
    )
    draft.media.append(row)  # 走 relationship：同事务内 draft.media 立即可见（sync_document 依赖）
    db.add(row)
    db.flush()
    staleness.mark_media_changed(db, draft, reason="material_attached")
    return row


def adopt_draft_media(db: Session, media: DraftMedia, *, created_by: str | None = None) -> MaterialRevision:
    """显式 adoption：旧 DraftMedia（或独立上传）提升为 Material+Revision，不批量迁移。"""
    if media.material_revision_id:
        return db.get(MaterialRevision, media.material_revision_id)
    material = create_material(
        db,
        kind=MaterialKind.image.value if (media.mime_type or "").startswith("image/") else MaterialKind.other.value,
        title=(media.metadata_json or {}).get("filename") or f"material-{media.content_hash[:8]}",
        created_by=created_by,
    )
    if media.file_path:
        from .asset_media import MEDIA_ROOT

        if not (MEDIA_ROOT / media.file_path).is_file():
            raise HTTPException(409, "原素材文件缺失，无法 adoption")
    revision = MaterialRevision(
        material_id=material.id,
        revision_no=1,
        source_kind=MaterialSourceKind.legacy.value,
        content_hash=media.content_hash,
        file_path=media.file_path,
        mime_type=media.mime_type,
        rights_status=media.rights_status,
        public_use_allowed=media.public_use_allowed,
        metadata_json={"adopted_from_draft_media": media.id},
        created_by=created_by,
    )
    # legacy 字节不强制魔数校验：历史可读优先，provenance 标记 source_kind=legacy
    db.add(revision)
    db.flush()
    media.material_revision_id = revision.id
    return revision


def revoke_public_use(db: Session, revision: MaterialRevision, note: str) -> dict:
    revision.public_use_allowed = False
    revision.status = MaterialRevisionStatus.revoked.value
    revision.metadata_json = {**(revision.metadata_json or {}), "revocation_note": note}
    draft_ids = staleness.mark_material_rights_revoked(db, revision.id, note)
    return {"material_id": revision.material_id, "revision_id": revision.id, "affected_drafts": draft_ids}


def find_usage(db: Session, material_id: int) -> dict:
    revision_ids = list(
        db.scalars(select(MaterialRevision.id).where(MaterialRevision.material_id == material_id)).all()
    )
    uses = db.scalars(select(DraftMedia).where(DraftMedia.material_revision_id.in_(revision_ids or [0]))).all()
    return {
        "material_id": material_id,
        "revisions": len(revision_ids),
        "draft_media_uses": [
            {"draft_media_id": u.id, "draft_id": u.draft_id, "role": u.role, "sort_order": u.sort_order}
            for u in uses
        ],
    }


def read_bytes_checked(db: Session, revision: MaterialRevision, *, require_public: bool = False) -> bytes:
    from .asset_media import MEDIA_ROOT

    if require_public and revision.public_use_allowed is not True:
        raise HTTPException(403, "该素材未获公开使用授权")
    path = MEDIA_ROOT / (revision.file_path or "")
    if not revision.file_path or not path.is_file():
        raise HTTPException(404, "素材文件缺失")
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != revision.content_hash:
        raise HTTPException(409, "素材字节校验失败（content hash 不一致）")
    return content
