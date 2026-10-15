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
    AuditLog,
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
    (b"RIFF", "audio/wav"),
    (b"%PDF", "application/pdf"),
    (b"ID3", "audio/mpeg"),
    (b"\x00\x00\x00", "video/mp4"),  # ftyp box 前缀
]
FALLBACK_MIME = "application/octet-stream"

# Passive project files are allowed only through explicit external acceptance.
EXECUTION_OTHER_MIME = {
    "text/plain", "text/vtt", "text/srt", "application/x-subrip",
    "application/json", "application/xml", "text/xml", "application/zip",
    "application/x-premiere-project", "application/vnd.adobe.premiere",
    "application/x-after-effects-project", "application/vnd.adobe.aftereffects.project",
    "application/x-aep", "application/x-resolve-project",
    "application/vnd.blackmagic-design.resolve",
}
EXECUTION_TEXT_MIME = {"text/plain", "text/vtt", "text/srt", "application/x-subrip"}

# JSON provenance cannot authorize library creation from an executor result.
_EXTERNAL_EXECUTION_ACCEPTANCE = object()


def validate_execution_file(content: bytes, declared_mime: str, kind: str) -> str:
    if not isinstance(declared_mime, str) or kind not in {"image", "video", "audio", "other"}:
        raise HTTPException(422, {"code": "execution_mime_unsupported"})
    if not content or len(content) > 30 * 1024 * 1024:
        raise HTTPException(413, {"code": "execution_file_size_invalid"})
    detected = sniff_mime(content, None)
    if detected == FALLBACK_MIME:
        if content.startswith(b"fLaC"):
            detected = "audio/flac"
        elif content.startswith(b"OggS"):
            detected = "audio/ogg" if kind == "audio" else "video/ogg"
        elif content.startswith(b"\x1a\x45\xdf\xa3"):
            detected = "audio/webm" if kind == "audio" else "video/webm"
        elif len(content) > 1 and content[0] == 255 and content[1] & 0xE0 == 0xE0:
            detected = "audio/mpeg"
        elif len(content) > 12 and content[4:8] == b"ftyp":
            detected = "video/quicktime" if content[8:12] == b"qt  " else "video/mp4"
    if kind == "audio" and detected == "video/mp4" and declared_mime == "audio/mp4":
        detected = "audio/mp4"
    if detected != FALLBACK_MIME:
        if detected != declared_mime or (kind != "other" and not detected.startswith(kind + "/")):
            raise HTTPException(422, {"code": "execution_mime_mismatch"})
        return detected
    if kind != "other" or declared_mime not in EXECUTION_OTHER_MIME:
        raise HTTPException(422, {"code": "execution_mime_unsupported"})
    if declared_mime in EXECUTION_TEXT_MIME | {"application/json", "application/xml", "text/xml"}:
        try:
            decoded = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise HTTPException(422, {"code": "execution_text_invalid"}) from None
        if "\x00" in decoded or (declared_mime == "text/vtt" and not decoded.startswith("WEBVTT")):
            raise HTTPException(422, {"code": "execution_text_invalid"})
        if declared_mime == "application/json":
            from .creative_contracts import bounded_json

            try:
                import json

                parsed = json.loads(decoded)
            except (ValueError, RecursionError):
                raise HTTPException(422, {"code": "execution_text_invalid"}) from None
            bounded_json(parsed, max_bytes=30 * 1024 * 1024)
        if declared_mime in {"application/xml", "text/xml"} and (
            not decoded.lstrip().startswith("<") or "<!DOCTYPE" in decoded.upper() or "<!ENTITY" in decoded.upper()
        ):
            raise HTTPException(422, {"code": "execution_text_invalid"})
    if declared_mime == "application/zip" and not content.startswith((b"PK\x03\x04", b"PK\x05\x06")):
        raise HTTPException(422, {"code": "execution_mime_mismatch"})
    return declared_mime


def sniff_mime(content: bytes, declared: str | None) -> str:
    """魔数优先；识别不出时回退声明的白名单前缀，再回退 octet-stream。"""
    for magic, mime in _SIGNATURES:
        if content.startswith(magic):
            if mime == "image/webp" and content[8:12] != b"WEBP":
                continue
            if mime == "audio/wav" and content[8:12] != b"WAVE":
                continue
            if mime == "video/mp4" and content[4:8] != b"ftyp":
                continue
            if mime == "video/mp4" and content[8:12] == b"qt  ":
                return "video/quicktime"
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
    content_hash = hashlib.sha256(content).hexdigest()
    if subdir == "material":
        from .material_byte_lock import hold_until_transaction_end

        hold_until_transaction_end(db, content_hash)
    relative = Path(subdir) / content_hash[:2] / f"{content_hash}{suffix}"
    from .material_storage import provider

    provider().put(str(relative), content)
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
    _execution_acceptance: object | None = None,
    _execution_stream=None,
    _stream_maximum: int = 30 * 1024 * 1024,
) -> MaterialRevision:
    if source_kind not in {k.value for k in MaterialSourceKind}:
        raise HTTPException(422, f"非法素材来源: {source_kind}")
    if source_kind == "external_execution":
        if _execution_acceptance is not _EXTERNAL_EXECUTION_ACCEPTANCE:
            raise HTTPException(403, {"code": "external_execution_acceptance_required"})
        if (not isinstance(source_metadata, dict)
                or any(type(source_metadata.get(key)) is not int or source_metadata[key] < 1 for key in ("execution_id", "output_id", "package_id"))
                or not isinstance(source_metadata.get("package_hash"), str) or len(source_metadata["package_hash"]) != 64):
            raise HTTPException(422, {"code": "external_execution_provenance_required"})
        mime = declared_mime if _execution_stream is not None else validate_execution_file(content, declared_mime, material.kind)
    else:
        mime = validate_upload(content, declared_mime) if source_kind != MaterialSourceKind.legacy.value else (declared_mime or FALLBACK_MIME)
    if _execution_stream is not None:
        if source_kind != "external_execution" or _execution_acceptance is not _EXTERNAL_EXECUTION_ACCEPTANCE:
            raise HTTPException(403, {"code": "external_execution_acceptance_required"})
        from .creative_media_stream import inspect
        from .material_byte_lock import hold_until_transaction_end
        from .material_storage import LocalMaterialStorage, provider
        _size, content_hash = inspect(_execution_stream, _stream_maximum)
        hold_until_transaction_end(db, content_hash)
        relative = f"material/{content_hash[:2]}/{content_hash}{suffix}"
        storage = provider()
        if not isinstance(storage, LocalMaterialStorage):
            raise HTTPException(409, {"code": "execution_local_storage_required"})
        storage.put_stream(relative, _execution_stream, maximum=_stream_maximum, expected_hash=content_hash)
    else:
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
    """被 schema v2 批准候选引用的 material_revision ids（v1 manifest 只引用 DraftMedia）。

    只取 manifest 列而不是整行 ORM：该表 final_body/structured_json 都是大字段，
    逐行反序列化整行只为读 manifest 的代价随候选数线性放大。
    """
    ids: set[int] = set()
    manifests = db.scalars(
        select(ContentAsset.candidate_manifest_json).where(ContentAsset.approved_candidate_hash.is_not(None))
    )
    for manifest in manifests:
        for media in (manifest or {}).get("media", []):
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
        from .material_storage import provider

        try:
            legacy_bytes = provider().read(media.file_path)
        except (FileNotFoundError, OSError, ValueError):
            raise HTTPException(409, "原素材文件缺失，无法 adoption") from None
        if hashlib.sha256(legacy_bytes).hexdigest() != media.content_hash:
            raise HTTPException(409, "原素材校验失败，无法 adoption")
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
    if require_public and revision.public_use_allowed is not True:
        raise HTTPException(403, "该素材未获公开使用授权")
    if not revision.file_path:
        raise HTTPException(404, "素材文件缺失")
    try:
        from .material_storage import provider

        content = provider().read(revision.file_path)
    except (FileNotFoundError, OSError):
        raise HTTPException(404, "素材文件缺失") from None
    except (ValueError, RuntimeError):
        raise HTTPException(409, "素材存储不可用") from None
    if hashlib.sha256(content).hexdigest() != revision.content_hash:
        raise HTTPException(409, "素材字节校验失败（content hash 不一致）")
    return content


def storage_diagnostics(db: Session, *, limit: int = 200) -> dict:
    """Bounded operator diagnostics without exposing storage locations."""
    from .material_storage import provider

    storage = provider()
    rows = db.scalars(select(MaterialRevision).order_by(MaterialRevision.id).limit(limit)).all()
    issues: list[dict] = []
    for revision in rows:
        code = None
        if not revision.file_path:
            code = "missing_storage_key"
        else:
            try:
                if not storage.exists(revision.file_path):
                    code = "missing_bytes"
                elif hashlib.sha256(storage.read(revision.file_path)).hexdigest() != revision.content_hash:
                    code = "content_hash_mismatch"
            except FileNotFoundError:
                code = "missing_bytes"
            except (OSError, RuntimeError, ValueError):
                code = "storage_unavailable"
        if code:
            issues.append({"revision_id": revision.id, "material_id": revision.material_id, "code": code})

    orphan_rows = db.scalars(
        select(AuditLog).where(AuditLog.event == "material.upload_orphan_candidate").order_by(AuditLog.id.desc()).limit(limit)
    ).all()
    orphan_candidates = [
        {"audit_id": row.id, "entity_id": row.entity_id}
        for row in orphan_rows
        if not (row.detail_json or {}).get("cleanup_status")
    ]
    return {
        "provider": storage.name,
        "checked_revisions": len(rows),
        "issue_count": len(issues),
        "issues": issues,
        "orphan_candidate_count": len(orphan_candidates),
        "orphan_candidates": orphan_candidates,
        "truncated": len(rows) >= limit,
    }


def verify_bytes_checked(db: Session, revision: MaterialRevision, *, require_public: bool = False) -> bytes:
    """Verify opted-in execution media incrementally; return only a MIME header."""
    if revision.source_kind != "external_execution":
        return read_bytes_checked(db, revision, require_public=require_public)
    if require_public and revision.public_use_allowed is not True:
        raise HTTPException(403, "该素材未获公开使用授权")
    from .creative_media_stream import material_file
    try:
        with material_file(revision, 512 * 1024 * 1024) as source:
            return source.read(64)
    except OSError:
        raise HTTPException(409, {"code": "execution_input_unavailable"}) from None
