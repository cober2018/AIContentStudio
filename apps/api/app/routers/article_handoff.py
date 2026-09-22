"""M1 文章母稿、人工交付包与回填 API。

只生成本地交付包；这里不调用任何平台 API，也不把人工回填标成平台已发布。
"""

import hashlib
import io
import json
from pathlib import Path
import zipfile

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_editor
from ..models import (
    AuditLog,
    ContentAsset,
    ContentJob,
    DeliveryFeedback,
    DeliveryReceipt,
    DeliveryTarget,
    DeliveryTargetStatus,
    Draft,
    DraftMedia,
    DraftStatus,
    FactPack,
    MotherRevision,
    TopicBrief,
    User,
    utcnow,
)
from ..services import exports

router = APIRouter(prefix="/api/v1/article-handoff", tags=["article-handoff"])


class MotherRevisionIn(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    body_markdown: str = Field(min_length=1)


class AdaptationIn(BaseModel):
    channel: str
    title: str | None = None
    body_markdown: str | None = None
    thread_posts: list[str] | None = None


class TargetIn(BaseModel):
    channel: str
    content_form: str
    account_ref: str = Field(min_length=1, max_length=255)
    authorization_version: str = Field(min_length=1, max_length=64)


class ReceiptIn(BaseModel):
    status: str = Field(pattern="^(human_confirmed|reconciliation_needed|failed)$")
    evidence_ref: str | None = None
    verification_method: str | None = None
    note: str | None = None


class FeedbackIn(BaseModel):
    kind: str = "note"
    body: str = Field(min_length=1)


class DraftMediaOrderIn(BaseModel):
    media_ids: list[int]


class PublicUseRevocationIn(BaseModel):
    note: str = Field(min_length=1, max_length=1000)


def _hash(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def _target_json(target: DeliveryTarget) -> dict:
    return {
        "id": target.id,
        "asset_id": target.content_asset_id,
        "channel": target.channel,
        "content_form": target.content_form,
        "account_ref": target.account_ref,
        "action": target.action,
        "authorization_version": target.authorization_version,
        "status": target.status,
        "approved_candidate_hash": target.approved_candidate_hash,
        "receipts": [
            {
                "id": row.id,
                "status": row.status,
                "approved_candidate_hash": row.approved_candidate_hash,
                "action": row.action,
                "operator": row.operator,
                "delivered_at": row.delivered_at.isoformat() if row.delivered_at else None,
                "evidence_ref": row.evidence_ref,
                "verification_method": row.verification_method,
                "note": row.note,
            }
            for row in target.receipts
        ],
        "feedback": [{"id": row.id, "kind": row.kind, "body": row.body} for row in target.feedback],
    }


def _require_target_operator(target: DeliveryTarget, user: User) -> None:
    if target.authorized_by and target.authorized_by != user.email:
        raise HTTPException(403, "该账号交付目标未授权给当前操作人")


def _mother_json(row: MotherRevision) -> dict:
    return {
        "id": row.id,
        "topic_id": row.topic_brief_id,
        "revision_no": row.revision_no,
        "parent_revision_id": row.parent_revision_id,
        "title": row.title,
        "body_markdown": row.body_markdown,
        "evidence_checksum": row.evidence_checksum,
        "body_hash": row.body_hash,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def _media_json(row: DraftMedia) -> dict:
    return {
        "id": row.id,
        "draft_id": row.draft_id,
        "content_hash": row.content_hash,
        "role": row.role,
        "sort_order": row.sort_order,
        "mime_type": row.mime_type,
        "rights_status": row.rights_status,
        "public_use_allowed": row.public_use_allowed,
        "public_use_revoked_at": row.public_use_revoked_at.isoformat() if row.public_use_revoked_at else None,
        "metadata": row.metadata_json or {},
    }


@router.post("/topics/{topic_id}/mother-revisions", status_code=201)
def import_mother_revision(
    topic_id: int,
    payload: MotherRevisionIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_editor),
):
    topic = db.get(TopicBrief, topic_id)
    if not topic:
        raise HTTPException(404, "Topic 不存在")
    pack = topic.fact_pack
    if pack.status != "frozen" or not pack.checksum:
        raise HTTPException(409, "母稿必须绑定已冻结的证据包")
    invalid_items = [
        item.id for item in pack.items
        if item.evidence_kind == "legacy_untyped" or not item.snapshot_checksum or item.public_use_revoked_at
    ]
    if invalid_items:
        raise HTTPException(409, f"证据项尚未完成类型化冻结: {invalid_items}")
    latest = db.scalars(
        select(MotherRevision).where(MotherRevision.topic_brief_id == topic.id).order_by(MotherRevision.revision_no.desc())
    ).first()
    row = MotherRevision(
        topic_brief_id=topic.id,
        revision_no=(latest.revision_no + 1 if latest else 1),
        title=payload.title,
        body_markdown=payload.body_markdown,
        parent_revision_id=latest.id if latest else None,
        evidence_checksum=pack.checksum,
        body_hash=_hash(payload.title, payload.body_markdown),
        import_metadata_json={"source": "manual_revision" if latest else "manual_import", "preserved": not bool(latest)},
        created_by=user.email,
    )
    db.add(row)
    db.add(AuditLog(event="mother_revision.imported", actor=user.email, entity_type="mother_revision", detail_json={"topic_id": topic.id}))
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "母稿版本发生并发冲突，请刷新后重试") from exc
    db.refresh(row)
    return _mother_json(row)


@router.get("/topics/{topic_id}/mother-revisions")
def list_mother_revisions(topic_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    topic = db.get(TopicBrief, topic_id)
    if not topic:
        raise HTTPException(404, "Topic 不存在")
    rows = db.scalars(
        select(MotherRevision).where(MotherRevision.topic_brief_id == topic_id).order_by(MotherRevision.revision_no)
    ).all()
    return [_mother_json(row) for row in rows]


@router.get("/mother-revisions/{revision_id}")
def get_mother_revision(revision_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.get(MotherRevision, revision_id)
    if not row:
        raise HTTPException(404, "MotherRevision 不存在")
    return _mother_json(row)


@router.get("/mother-revisions/{revision_id}/drafts")
def list_mother_drafts(revision_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    revision = db.get(MotherRevision, revision_id)
    if not revision:
        raise HTTPException(404, "MotherRevision 不存在")
    rows = db.scalars(
        select(Draft).where(Draft.mother_revision_id == revision_id).order_by(Draft.created_at.desc())
    ).all()
    asset_by_draft = {
        asset.draft_id: asset
        for asset in db.scalars(select(ContentAsset).where(ContentAsset.draft_id.in_([row.id for row in rows])))
    } if rows else {}
    return [
        {
            "id": row.id,
            "title": row.title,
            "channel": row.content_job.channel,
            "status": row.status,
            "candidate_readiness": row.candidate_readiness,
            "fact_check": row.fact_check_json,
            "thread_posts": row.thread_posts_json,
            "media": [_media_json(media) for media in row.media],
            "asset_id": asset_by_draft[row.id].id if row.id in asset_by_draft else None,
            "approved_candidate_hash": asset_by_draft[row.id].approved_candidate_hash if row.id in asset_by_draft else None,
        }
        for row in rows
    ]


@router.post("/mother-revisions/{revision_id}/drafts", status_code=201)
def create_adaptation(
    revision_id: int,
    payload: AdaptationIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_editor),
):
    revision = db.get(MotherRevision, revision_id)
    if not revision:
        raise HTTPException(404, "MotherRevision 不存在")
    if payload.channel not in {"wechat", "x_thread"}:
        raise HTTPException(400, "M1 只支持公众号和 X Thread")
    thread_posts = None
    body = payload.body_markdown or revision.body_markdown
    if payload.channel == "x_thread":
        if not payload.thread_posts or any(not post.strip() for post in payload.thread_posts):
            raise HTTPException(422, "X Thread 必须提供有序且非空的 thread_posts")
        thread_posts = [{"index": index, "text": post.strip()} for index, post in enumerate(payload.thread_posts, 1)]
        body = "\n\n".join(f"{post['index']}. {post['text']}" for post in thread_posts)
    input_hash = _hash(payload.title or revision.title or "", body, json.dumps(thread_posts or [], ensure_ascii=False, sort_keys=True), revision.evidence_checksum or "")
    job = ContentJob(
        topic_brief_id=revision.topic_brief_id,
        channel=payload.channel,
        fact_pack_snapshot={"id": revision.topic_brief.fact_pack_id, "checksum": revision.evidence_checksum},
        status="succeeded",
        started_at=utcnow(),
        finished_at=utcnow(),
    )
    db.add(job)
    db.flush()
    draft = Draft(
        content_job_id=job.id,
        revision_no=1,
        title=payload.title or revision.title or revision.topic_brief.title,
        body=body,
        structured_json={"source": "mother_revision", "manual_adaptation": True},
        mother_revision_id=revision.id,
        evidence_checksum=revision.evidence_checksum,
        input_hash=input_hash,
        thread_posts_json=thread_posts,
        candidate_readiness="incomplete",
        status=DraftStatus.draft.value,
        created_by_type="user",
        created_by=user.email,
    )
    db.add(draft)
    db.add(AuditLog(event="draft.adapted_from_mother", actor=user.email, entity_type="draft", detail_json={"mother_revision_id": revision.id, "channel": payload.channel}))
    db.commit()
    db.refresh(draft)
    return {"draft_id": draft.id, "content_job_id": job.id, "channel": payload.channel, "mother_revision_id": revision.id, "status": draft.status}


@router.get("/drafts/{draft_id}/media")
def list_draft_media(draft_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    draft = db.get(Draft, draft_id)
    if not draft:
        raise HTTPException(404, "Draft 不存在")
    return [_media_json(row) for row in draft.media]


@router.post("/drafts/{draft_id}/media", status_code=201)
async def upload_draft_media(
    draft_id: int,
    file: UploadFile,
    role: str = "inline",
    rights_status: str = "cleared",
    public_use_allowed: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(require_editor),
):
    draft = db.get(Draft, draft_id)
    if not draft:
        raise HTTPException(404, "Draft 不存在")
    if draft.status == DraftStatus.approved.value:
        raise HTTPException(409, "已批准稿件的素材不可修改")
    if role not in {"cover", "inline", "attachment"}:
        raise HTTPException(422, "role 不受支持")
    content = await file.read()
    if not content:
        raise HTTPException(422, "素材文件为空")
    content_hash = hashlib.sha256(content).hexdigest()
    existing = db.scalars(
        select(DraftMedia).where(DraftMedia.draft_id == draft.id, DraftMedia.content_hash == content_hash)
    ).first()
    if existing:
        return _media_json(existing)
    suffix = Path(file.filename or "media.bin").suffix.lower()[:10] or ".bin"
    from ..services.asset_media import MEDIA_ROOT

    relative_path = Path("draft") / content_hash[:2] / f"{content_hash}{suffix}"
    absolute_path = MEDIA_ROOT / relative_path
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    if not absolute_path.exists():
        absolute_path.write_bytes(content)
    row = DraftMedia(
        draft_id=draft.id,
        content_hash=content_hash,
        role=role,
        sort_order=len(draft.media),
        file_path=str(relative_path),
        mime_type=file.content_type or "application/octet-stream",
        rights_status=rights_status,
        public_use_allowed=public_use_allowed,
        metadata_json={"filename": file.filename, "uploaded_by": user.email},
    )
    draft.candidate_readiness = "stale"
    db.add(row)
    db.add(AuditLog(event="draft.media_uploaded", actor=user.email, entity_type="draft", entity_id=str(draft.id), detail_json={"content_hash": content_hash, "role": role}))
    db.commit()
    db.refresh(row)
    return _media_json(row)


@router.put("/drafts/{draft_id}/media/order")
def reorder_draft_media(draft_id: int, payload: DraftMediaOrderIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    draft = db.get(Draft, draft_id)
    if not draft:
        raise HTTPException(404, "Draft 不存在")
    if draft.status == DraftStatus.approved.value:
        raise HTTPException(409, "已批准稿件的素材不可修改")
    rows = {row.id: row for row in draft.media}
    if len(payload.media_ids) != len(set(payload.media_ids)) or set(payload.media_ids) != set(rows):
        raise HTTPException(422, "media_ids 必须完整且不重复")
    for order, media_id in enumerate(payload.media_ids):
        rows[media_id].sort_order = order
    draft.candidate_readiness = "stale"
    db.commit()
    return [_media_json(rows[media_id]) for media_id in payload.media_ids]


def _block_pending_targets(db: Session, asset_ids: list[int], actor: str, reason: str) -> int:
    if not asset_ids:
        return 0
    rows = db.scalars(
        select(DeliveryTarget).where(
            DeliveryTarget.content_asset_id.in_(asset_ids),
            DeliveryTarget.status.not_in({DeliveryTargetStatus.human_confirmed.value, DeliveryTargetStatus.canceled.value}),
        )
    ).all()
    for target in rows:
        target.status = DeliveryTargetStatus.blocked.value
        db.add(AuditLog(event="delivery_target.blocked", actor=actor, entity_type="delivery_target", entity_id=str(target.id), detail_json={"reason": reason}))
    return len(rows)


@router.post("/drafts/{draft_id}/media/{media_id}/revoke-public-use")
def revoke_draft_media_public_use(
    draft_id: int,
    media_id: int,
    payload: PublicUseRevocationIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_editor),
):
    row = db.get(DraftMedia, media_id)
    if not row or row.draft_id != draft_id:
        raise HTTPException(404, "素材不存在")
    if not row.public_use_revoked_at:
        row.public_use_revoked_at = utcnow()
        row.public_use_revocation_note = payload.note
        asset_ids = list(db.scalars(select(ContentAsset.id).where(ContentAsset.draft_id == draft_id)))
        blocked = _block_pending_targets(db, asset_ids, user.email, "media_public_use_revoked")
        db.add(AuditLog(event="draft_media.public_use_revoked", actor=user.email, entity_type="draft_media", entity_id=str(row.id), detail_json={"blocked_targets": blocked, "note": payload.note}))
        db.commit()
    return _media_json(row)


@router.get("/drafts/{draft_id}/media/{media_id}/raw")
def get_draft_media_raw(draft_id: int, media_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.get(DraftMedia, media_id)
    if not row or row.draft_id != draft_id or not row.file_path:
        raise HTTPException(404, "素材不存在")
    from ..services.asset_media import MEDIA_ROOT

    path = MEDIA_ROOT / row.file_path
    if not path.is_file():
        raise HTTPException(404, "素材文件不存在")
    return FileResponse(path, media_type=row.mime_type)


@router.delete("/drafts/{draft_id}/media/{media_id}")
def delete_draft_media(draft_id: int, media_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    draft = db.get(Draft, draft_id)
    row = db.get(DraftMedia, media_id)
    if not draft or not row or row.draft_id != draft_id:
        raise HTTPException(404, "素材不存在")
    referenced = db.scalars(
        select(ContentAsset).where(ContentAsset.draft_id == draft.id, ContentAsset.approved_candidate_hash.is_not(None))
    ).first()
    if draft.status == DraftStatus.approved.value or referenced:
        raise HTTPException(409, "素材已被批准候选引用，不能删除")
    content_hash = row.content_hash
    db.delete(row)
    draft.candidate_readiness = "stale"
    db.commit()
    return {"deleted": True, "content_hash": content_hash}


@router.post("/assets/{asset_id}/targets", status_code=201)
def create_target(
    asset_id: int,
    payload: TargetIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_editor),
):
    asset = db.get(ContentAsset, asset_id)
    if not asset or asset.status not in {"approved", DraftStatus.exported.value}:
        raise HTTPException(409, "只有已批准内容才能创建人工交付目标")
    if payload.channel not in {"wechat", "x_thread"}:
        raise HTTPException(400, "M1 只支持公众号和 X Thread")
    if asset.channel != payload.channel:
        raise HTTPException(409, "目标渠道必须与批准资产渠道一致")
    expected_form = "wechat_article" if payload.channel == "wechat" else "x_thread"
    if payload.content_form != expected_form:
        raise HTTPException(400, f"{payload.channel} 的 M1 content_form 必须是 {expected_form}")
    if not asset.approved_candidate_hash:
        raise HTTPException(409, "批准资产缺少 candidate hash")
    if not asset.mother_revision_id or not asset.candidate_manifest_json:
        raise HTTPException(409, "只有完成 M1 候选批准的资产才能授权交付")
    existing = db.scalars(select(DeliveryTarget).where(
        DeliveryTarget.content_asset_id == asset.id,
        DeliveryTarget.approved_candidate_hash == asset.approved_candidate_hash,
        DeliveryTarget.channel == payload.channel,
        DeliveryTarget.content_form == payload.content_form,
        DeliveryTarget.account_ref == payload.account_ref,
        DeliveryTarget.authorization_version == payload.authorization_version,
    )).first()
    if existing:
        return _target_json(existing)
    candidate_hash = asset.approved_candidate_hash
    target = DeliveryTarget(
        content_asset_id=asset.id,
        channel=payload.channel,
        content_form=payload.content_form,
        account_ref=payload.account_ref,
        authorization_version=payload.authorization_version,
        approved_candidate_hash=candidate_hash,
        authorized_by=user.email,
        authorized_at=utcnow(),
        status=DeliveryTargetStatus.target_authorized.value,
    )
    db.add(target)
    db.add(AuditLog(event="delivery_target.authorized", actor=user.email, entity_type="delivery_target", detail_json={"asset_id": asset.id, "candidate_hash": candidate_hash, "remote_call": False}))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        concurrent = db.scalars(select(DeliveryTarget).where(
            DeliveryTarget.content_asset_id == asset.id,
            DeliveryTarget.approved_candidate_hash == candidate_hash,
            DeliveryTarget.channel == payload.channel,
            DeliveryTarget.content_form == payload.content_form,
            DeliveryTarget.account_ref == payload.account_ref,
            DeliveryTarget.authorization_version == payload.authorization_version,
        )).first()
        if concurrent:
            return _target_json(concurrent)
        raise HTTPException(409, "交付目标创建冲突，请刷新后重试")
    db.refresh(target)
    return _target_json(target)


@router.get("/assets/{asset_id}/targets")
def list_targets_for_asset(asset_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    asset = db.get(ContentAsset, asset_id)
    if not asset:
        raise HTTPException(404, "批准资产不存在")
    rows = db.scalars(select(DeliveryTarget).where(
        DeliveryTarget.content_asset_id == asset_id,
        DeliveryTarget.authorized_by == user.email,
    ).order_by(DeliveryTarget.id.desc())).all()
    return [_target_json(row) for row in rows]


@router.post("/targets/{target_id}/package")
def get_package(target_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    target = db.get(DeliveryTarget, target_id)
    if not target:
        raise HTTPException(404, "交付目标不存在")
    _require_target_operator(target, user)
    if target.status == DeliveryTargetStatus.blocked.value:
        raise HTTPException(409, "该目标的公开使用权限已撤销，不能再交付")
    asset = db.get(ContentAsset, target.content_asset_id)
    if not asset:
        raise HTTPException(404, "批准资产不存在")
    if not target.approved_candidate_hash or target.approved_candidate_hash != asset.approved_candidate_hash:
        raise HTTPException(409, "目标授权与当前批准内容哈希不一致")
    approved_manifest = asset.candidate_manifest_json or {}
    if not approved_manifest:
        raise HTTPException(409, "批准资产缺少候选清单")
    public_media = [
        media for media in approved_manifest.get("media", [])
        if media.get("public_use_allowed") is True and media.get("rights_status")
    ]
    if len(public_media) != len(approved_manifest.get("media", [])):
        raise HTTPException(409, "候选清单包含未获公开权限的素材")
    media_ids = [media.get("id") for media in public_media]
    live_media = {
        row.id: row
        for row in db.scalars(select(DraftMedia).where(DraftMedia.draft_id == asset.draft_id, DraftMedia.id.in_(media_ids)))
    } if media_ids else {}
    revoked_media = [
        media.get("id") for media in public_media
        if not isinstance(media.get("id"), int)
        or media.get("id") not in live_media
        or live_media[media["id"]].content_hash != media.get("hash")
        or live_media[media["id"]].public_use_allowed is not True
        or not live_media[media["id"]].rights_status
        or live_media[media["id"]].public_use_revoked_at
    ]
    pack = db.get(FactPack, asset.fact_pack_id)
    revoked_evidence = [item.id for item in (pack.items if pack else []) if item.public_use_revoked_at]
    if revoked_media or revoked_evidence:
        _block_pending_targets(db, [asset.id], user.email, "public_rights_revoked")
        db.commit()
        raise HTTPException(409, {"message": "公开使用权限已撤销，需重新完成候选批准和账号授权", "media": revoked_media, "evidence": revoked_evidence})
    package_media = []
    for media in public_media:
        media_id = media.get("id")
        if not isinstance(media_id, int):
            raise HTTPException(409, "批准候选清单缺少可下载的媒体标识")
        package_media.append({
            **media,
            "download_path": f"/api/v1/article-handoff/drafts/{asset.draft_id}/media/{media_id}/raw",
        })
    approved_title = approved_manifest.get("title")
    approved_body = approved_manifest.get("body_markdown")
    if not isinstance(approved_title, str) or not isinstance(approved_body, str):
        raise HTTPException(409, "批准候选清单缺少不可变正文")
    if target.channel == "wechat":
        content = {
            "markdown": approved_body,
            "html": exports.render_wechat_html(
                approved_title,
                approved_body,
                f"批准候选 {asset.approved_candidate_hash}；仅限人工发布回填",
            ),
            "title": approved_title,
        }
    else:
        content = {
            "markdown": approved_body,
            "json": json.dumps(
                {"title": approved_title, "thread_posts": approved_manifest.get("thread_posts") or []},
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
            "title": approved_title,
        }
    manifest = {
        "schema_version": 1,
        "target_id": target.id,
        "asset_id": asset.id,
        "channel": target.channel,
        "content_form": target.content_form,
        "account_ref": target.account_ref,
        "action": target.action,
        "authorization_version": target.authorization_version,
        "approved_candidate_hash": asset.approved_candidate_hash,
        "media": package_media,
        "citations": approved_manifest.get("citations", []),
        "declarations": approved_manifest.get("declarations", []),
        "remote_call": False,
        "archive_download_path": f"/api/v1/article-handoff/targets/{target.id}/package.zip",
    }
    if target.status in {DeliveryTargetStatus.target_authorized.value, DeliveryTargetStatus.package_ready.value}:
        target.status = DeliveryTargetStatus.awaiting_manual_receipt.value
    db.add(AuditLog(event="delivery_package.generated", actor=user.email, entity_type="delivery_target", entity_id=str(target.id), detail_json=manifest))
    db.commit()
    return JSONResponse({"manifest": manifest, "content": content, "notice": "本地成品包；需人工发布后回填，不代表平台已发布"})


@router.get("/targets/{target_id}/package.zip")
def download_package_archive(target_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    package_response = get_package(target_id, db, user)
    package = json.loads(package_response.body)
    manifest = package["manifest"]
    content = package["content"]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
        archive.writestr("content.md", content["markdown"])
        if content.get("html"):
            archive.writestr("content.html", content["html"])
        if content.get("json"):
            archive.writestr("thread.json", content["json"])
        archive.writestr("README.txt", "本包仅限已授权账号人工发布；完成后回到系统回填结果。")
        from ..services.asset_media import MEDIA_ROOT
        for media in manifest["media"]:
            row = db.get(DraftMedia, media["id"])
            path = MEDIA_ROOT / (row.file_path or "") if row else None
            if not row or not path or not path.is_file():
                raise HTTPException(409, "批准素材文件已缺失，不能导出成品包")
            content_bytes = path.read_bytes()
            if hashlib.sha256(content_bytes).hexdigest() != media["hash"]:
                raise HTTPException(409, "批准素材文件校验失败，不能导出成品包")
            suffix = Path(row.file_path).suffix or ".bin"
            archive.writestr(f"media/{media['sort_order']:02d}-{media['id']}{suffix}", content_bytes)
    filename = f"handoff-target-{target_id}.zip"
    return Response(
        content=buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/targets/{target_id}/receipt")
def add_receipt(target_id: int, payload: ReceiptIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    target = db.get(DeliveryTarget, target_id)
    if not target:
        raise HTTPException(404, "交付目标不存在")
    _require_target_operator(target, user)
    idempotency_key = _hash(
        str(target.id), target.approved_candidate_hash, payload.status,
        payload.evidence_ref or "", payload.verification_method or "", payload.note or "",
    )
    existing = db.scalars(select(DeliveryReceipt).where(
        DeliveryReceipt.target_id == target.id,
        DeliveryReceipt.idempotency_key == idempotency_key,
    ).order_by(DeliveryReceipt.id.desc())).first()
    if existing:
        return _target_json(target)
    if target.status not in {DeliveryTargetStatus.awaiting_manual_receipt.value, DeliveryTargetStatus.reconciliation_needed.value, DeliveryTargetStatus.failed.value}:
        raise HTTPException(409, "目标尚未生成成品包，或当前状态不可回填")
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
    db.add(AuditLog(event="delivery_receipt.recorded", actor=user.email, entity_type="delivery_target", entity_id=str(target.id), detail_json={"status": target.status, "platform_verified": False}))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return _target_json(db.get(DeliveryTarget, target.id))
    return _target_json(target)


@router.post("/targets/{target_id}/feedback", status_code=201)
def add_feedback(target_id: int, payload: FeedbackIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    target = db.get(DeliveryTarget, target_id)
    if not target:
        raise HTTPException(404, "交付目标不存在")
    row = DeliveryFeedback(target_id=target.id, kind=payload.kind, body=payload.body, observed_at=utcnow(), created_by=user.email)
    db.add(row)
    db.add(AuditLog(event="delivery_feedback.recorded", actor=user.email, entity_type="delivery_target", entity_id=str(target.id)))
    db.commit()
    return {"id": row.id, "target_id": target.id, "kind": row.kind, "body": row.body}
