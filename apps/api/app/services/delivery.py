"""Delivery Router 服务（D21–D25/§6.24）：唯一远端副作用入口。

执行顺序（D22）：validate → persist attempt(prepared) → COMMIT → call publisher → persist result。
超时无法确认 → attempt=unknown + target=reconciliation_needed；不自动 fallback 重发。
"""

from __future__ import annotations

import hashlib
import io
import json
import zipfile

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import (
    AuditLog,
    ContentAsset,
    DeliveryAction,
    DeliveryAttempt,
    DeliveryTarget,
    DeliveryTargetStatus,
    DraftMedia,
    MaterialRevision,
    utcnow,
)
from .content_harness.channel_registry import resolve_content_form
from .content_harness.publishers import bootstrap_publishers
from .content_harness.registry import registry

ACTIONS = {a.value for a in DeliveryAction}


def _hash(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def resolve_publisher(channel: str, content_form: str, action: str):
    """按 action 选 publisher：copy_package → publisher.copy；auto_draft/assisted_draft → 渠道 verified/可用 publisher。"""
    bootstrap_publishers()
    if action == DeliveryAction.copy_package.value:
        return registry.resolve("publisher", "publisher.copy", "1"), "publisher.copy", "1"
    if action == DeliveryAction.manual_handoff.value:
        return None, "publisher.copy.legacy", "1"
    if action == DeliveryAction.auto_draft.value:
        if channel == "wechat":
            return registry.resolve("publisher", "publisher.wechat.wewrite", "1"), "publisher.wechat.wewrite", "1"
        raise HTTPException(422, f"capability_unavailable: {channel} 尚无已注册的 auto_draft publisher")
    raise HTTPException(422, f"action {action} 尚无 publisher 实现")


def authorize_target(db: Session, asset: ContentAsset, payload, user) -> DeliveryTarget:
    """通用交付目标授权：channel/form/action 经 Registry 验证（D21），幂等。"""
    if asset.status not in {"approved", "exported"} or not asset.approved_candidate_hash:
        raise HTTPException(409, "只有已批准内容才能创建交付目标")
    try:
        spec = resolve_content_form(db, payload.channel, payload.content_form)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if payload.action not in ACTIONS:
        raise HTTPException(422, f"action 只允许 {sorted(ACTIONS)}")
    publisher, publisher_key, publisher_version = resolve_publisher(spec.channel, spec.content_form, payload.action)
    capability = None
    if publisher is not None:
        capability = publisher.capability(spec.channel, spec.content_form, payload.account_ref)
        cap_dict = {
            "publisher_key": capability.publisher_key, "action": capability.action,
            "available": capability.available, "reason": capability.reason,
            "verified": bool(getattr(publisher, "verified", lambda: True)()),
        }
        if capability.available is False:
            raise HTTPException(422, f"capability_unavailable: {capability.reason}")
        capability = cap_dict
    else:
        capability = {"publisher_key": publisher_key, "action": payload.action, "available": True, "verified": False, "legacy": True}
    # 渠道一致性：v1 资产仍要求与批准渠道一致；v2 同样
    if asset.channel != payload.channel:
        raise HTTPException(409, "目标渠道必须与批准资产渠道一致")

    existing = db.scalars(
        select(DeliveryTarget).where(
            DeliveryTarget.content_asset_id == asset.id,
            DeliveryTarget.approved_candidate_hash == asset.approved_candidate_hash,
            DeliveryTarget.channel == payload.channel,
            DeliveryTarget.content_form == payload.content_form,
            DeliveryTarget.account_ref == payload.account_ref,
            DeliveryTarget.action == payload.action,
            DeliveryTarget.authorization_version == payload.authorization_version,
        )
    ).first()
    if existing:
        return existing
    target = DeliveryTarget(
        content_asset_id=asset.id,
        channel=payload.channel,
        content_form=payload.content_form,
        account_ref=payload.account_ref,
        action=payload.action,
        authorization_version=payload.authorization_version,
        approved_candidate_hash=asset.approved_candidate_hash,
        authorized_by=user.email,
        authorized_at=utcnow(),
        requested_at=utcnow(),
        publisher_key=publisher_key,
        publisher_version=publisher_version,
        capability_snapshot_json=capability,
        status=DeliveryTargetStatus.target_authorized.value,
    )
    db.add(target)
    db.add(AuditLog(event="delivery_target.authorized", actor=user.email, entity_type="delivery_target",
                    detail_json={"asset_id": asset.id, "action": payload.action, "publisher": publisher_key,
                                 "capability": capability, "remote_call": payload.action == DeliveryAction.auto_draft.value}))
    try:
        db.commit()
    except Exception:  # noqa: BLE001 并发幂等
        db.rollback()
        concurrent = db.scalars(
            select(DeliveryTarget).where(DeliveryTarget.id == target.id)
        ).first()
        if concurrent:
            return concurrent
        raise HTTPException(409, "交付目标创建冲突，请刷新后重试") from None
    db.refresh(target)
    return target


def _asset_of(db: Session, target: DeliveryTarget) -> ContentAsset:
    asset = db.get(ContentAsset, target.content_asset_id)
    if not asset:
        raise HTTPException(404, "批准资产不存在")
    if not target.approved_candidate_hash or target.approved_candidate_hash != asset.approved_candidate_hash:
        raise HTTPException(409, "目标授权与当前批准内容哈希不一致（candidate mismatch）")
    return asset


def validate_live_candidate_payload(db: Session, asset: ContentAsset) -> dict:
    """R3-3：任何 Publisher 远端调用前的统一实时校验（Approved Candidate ≠ 现实世界时的最后一道闸）。

    - manifest 本体未被篡改：重算 candidate hash 与批准值一致；
    - render payload 已冻结（payload + content_hash 在批准时进入 candidate hash）；
    - 每个批准媒体：实时权利未撤销 + 实际字节 SHA-256 与批准 manifest 的 hash 一致。
    任一失败 → 409，不发起远端调用、不产生 DeliveryAttempt。
    """
    from .candidates import candidate_hash

    manifest = asset.candidate_manifest_json or {}
    if candidate_hash(manifest) != asset.approved_candidate_hash:
        raise HTTPException(409, "候选清单与批准哈希不一致（candidate integrity failed），拒绝远端交付")
    render = manifest.get("render") or {}
    if not render.get("payload") or not render.get("content_hash"):
        raise HTTPException(409, "render payload 未冻结，拒绝远端交付")
    for media in manifest.get("media", []):
        mid = media.get("material_revision_id") or media.get("draft_media_id")
        if _live_media_rights(db, media) is False:
            raise HTTPException(409, f"素材公开使用权限已撤销，拒绝远端交付: {mid}")
        data = _media_bytes(db, media)
        if data is None:
            raise HTTPException(409, f"批准素材无法定位实际文件，拒绝远端交付: {mid}")
        if hashlib.sha256(data).hexdigest() != media.get("hash"):
            raise HTTPException(409, f"批准素材字节与批准哈希不一致（文件已被替换/损坏），拒绝远端交付: {mid}")
    return manifest


def prepare_attempt(db: Session, target: DeliveryTarget, manifest: dict) -> DeliveryAttempt:
    """persist attempt(prepared)。调用方必须 COMMIT 后再调远端（D22 顺序）。

    unknown 且已对账 not_delivered 的尝试允许发起新 attempt（reconcile 契约）。
    """
    last = db.scalars(
        select(DeliveryAttempt).where(DeliveryAttempt.target_id == target.id).order_by(DeliveryAttempt.attempt_no.desc()).limit(1)
    ).first()
    if last:
        reconciled_not_delivered = (
            last.status == "unknown"
            and (last.response_metadata_json or {}).get("reconciled") == "not_delivered"
        )
        if last.status in {"prepared", "running", "succeeded"} or (last.status == "unknown" and not reconciled_not_delivered):
            raise HTTPException(409, f"已有 {last.status} 状态的尝试（#{last.attempt_no}），不可重复发起；unknown 请走 reconcile")
    attempt_no = (last.attempt_no + 1) if last else 1
    request_hash = _hash(json.dumps((manifest.get("render") or {}).get("payload") or {}, ensure_ascii=False, sort_keys=True, default=str))
    attempt = DeliveryAttempt(
        target_id=target.id,
        attempt_no=attempt_no,
        idempotency_key=_hash(str(target.id), target.approved_candidate_hash, str(attempt_no)),
        publisher_key=target.publisher_key,
        publisher_version=target.publisher_version,
        request_hash=request_hash,
        status="prepared",
        started_at=utcnow(),
    )
    db.add(attempt)
    db.flush()
    return attempt


def execute_attempt(db: Session, target_id: int, user) -> dict:
    bootstrap_publishers()
    target = db.get(DeliveryTarget, target_id)
    if not target:
        raise HTTPException(404, "交付目标不存在")
    if target.authorized_by and target.authorized_by != user.email:
        raise HTTPException(403, "该账号交付目标未授权给当前操作人")
    if target.status == DeliveryTargetStatus.blocked.value:
        raise HTTPException(409, "该目标的公开使用权限已撤销，不能再交付")
    if target.action == DeliveryAction.manual_handoff.value:
        raise HTTPException(409, "manual_handoff 目标走成品包 + 人工回填，不能 execute")
    # R2-M10：unverified publisher 的自动执行默认禁止（未真实验收的自动能力不可执行）。
    # 显式放行：system_settings delivery.allow_unverified_auto_draft=true
    snapshot = target.capability_snapshot_json or {}
    if target.action == DeliveryAction.auto_draft.value and snapshot.get("verified") is False:
        from .. import runtime_config

        delivery_cfg = runtime_config.get_runtime(runtime_config.KEY_DELIVERY) or {}
        if delivery_cfg.get("allow_unverified_auto_draft") is not True:
            raise HTTPException(
                409,
                "publisher unverified：未真实验收的自动能力默认禁止执行（完成后可在设置 → 交付开启 allow_unverified_auto_draft 显式放行）",
            )
    # R3-3：统一实时校验在 prepare（落 attempt）之前——校验失败不产生 attempt
    asset = _asset_of(db, target)
    manifest = validate_live_candidate_payload(db, asset)

    attempt = prepare_attempt(db, target, manifest)
    # D22：prepared 先落库（commit 由 SessionLocal 事务语义保证——路由层在调用远端前 commit）
    db.commit()

    publisher = None
    try:
        publisher = registry.resolve("publisher", target.publisher_key or "", target.publisher_version or "1")
    except Exception as exc:
        attempt.status = "failed"
        attempt.error = f"publisher 未注册: {exc}"[:500]
        attempt.finished_at = utcnow()
        target.status = DeliveryTargetStatus.failed.value
        db.commit()
        raise HTTPException(422, f"publisher 未注册: {target.publisher_key}") from exc

    attempt.status = "running"
    db.commit()

    if target.publisher_key == "publisher.wechat.wewrite":
        manifest = {**manifest, "_cover_bytes": _cover_bytes(db, asset, manifest)}
    result = publisher.deliver(manifest, target, attempt)

    attempt.finished_at = utcnow()
    attempt.response_metadata_json = result.metadata or {}
    if result.status == "succeeded":
        attempt.status = "succeeded"
        attempt.remote_id = result.remote_id
        target.status = DeliveryTargetStatus.awaiting_manual_receipt.value  # 远端草稿已建，人工发布后回填
    elif result.status == "unknown":
        attempt.status = "unknown"
        attempt.error = (result.error or "")[:500]
        target.status = DeliveryTargetStatus.reconciliation_needed.value
    else:
        attempt.status = "failed"
        attempt.error = (result.error or "")[:500]
        target.status = DeliveryTargetStatus.failed.value
    db.add(AuditLog(event="delivery_attempt.finished", actor=user.email, entity_type="delivery_attempt",
                    entity_id=str(attempt.id), detail_json={"status": attempt.status, "remote_id": attempt.remote_id, "publisher": target.publisher_key}))
    db.commit()
    return {
        "attempt_id": attempt.id, "attempt_no": attempt.attempt_no, "status": attempt.status,
        "remote_id": attempt.remote_id, "error": attempt.error, "target_status": target.status,
    }


def reconcile_attempt(db: Session, target_id: int, payload, user) -> dict:
    """unknown 结果的人工对账：delivered → 回填 receipt；not_delivered → 允许重新授权执行。"""
    target = db.get(DeliveryTarget, target_id)
    if not target:
        raise HTTPException(404, "交付目标不存在")
    if target.status != DeliveryTargetStatus.reconciliation_needed.value:
        raise HTTPException(409, "只有 reconciliation_needed 的目标需要对账")
    last = db.scalars(
        select(DeliveryAttempt).where(DeliveryAttempt.target_id == target.id).order_by(DeliveryAttempt.attempt_no.desc()).limit(1)
    ).first()
    resolution = payload.resolution
    if resolution == "delivered":
        target.status = DeliveryTargetStatus.human_confirmed.value
        if last:
            last.response_metadata_json = {**(last.response_metadata_json or {}), "reconciled": "delivered", "note": payload.note}
    elif resolution == "not_delivered":
        target.status = DeliveryTargetStatus.target_authorized.value
        if last:
            last.response_metadata_json = {**(last.response_metadata_json or {}), "reconciled": "not_delivered", "note": payload.note}
    else:
        raise HTTPException(422, "resolution 只允许 delivered / not_delivered")
    db.add(AuditLog(event="delivery_target.reconciled", actor=user.email, entity_type="delivery_target",
                    entity_id=str(target.id), detail_json={"resolution": resolution, "note": payload.note}))
    db.commit()
    return {"target_id": target.id, "status": target.status}


def _cover_bytes(db: Session, asset: ContentAsset, manifest: dict) -> bytes:
    """已批准媒体中 role=cover 的真实字节（无 cover 返回空 → publisher 按缺失封面 fail）。"""
    for media in manifest.get("media", []):
        if media.get("role") != "cover":
            continue
        rid = media.get("material_revision_id")
        if isinstance(rid, int):
            revision = db.get(MaterialRevision, rid)
            if revision and revision.file_path:
                from .asset_media import MEDIA_ROOT

                path = MEDIA_ROOT / revision.file_path
                if path.is_file():
                    return path.read_bytes()
        dm_id = media.get("draft_media_id")
        if isinstance(dm_id, int):
            row = db.get(DraftMedia, dm_id)
            if row and row.file_path:
                from .asset_media import MEDIA_ROOT

                path = MEDIA_ROOT / row.file_path
                if path.is_file():
                    return path.read_bytes()
    return b""


# ---------- Copy Package（D25）：manifest/render 驱动的通用成品包 ----------


def _live_media_rights(db: Session, media: dict) -> bool | None:
    """实时权利检查（R4.1：与 rule/readiness 完全同语义，堵住 use 级撤权旁路）。

    manifest 同时带 draft_media_id + material_revision_id 时**必须先查 use 行**——
    早期实现先查 MaterialRevision 即 return，会漏掉「仅对本稿撤权」的 use（Rights Gate 旁路）。
    有 use 行 → effective_media_rights(use)（use + revision 双层）；无 use 行才退化为 revision-only。
    None=无法定位（跳过），False=已撤销/未授权，True=OK。
    """
    from .content_harness.rules import effective_media_rights

    dm_id = media.get("draft_media_id")
    if isinstance(dm_id, int):
        row = db.get(DraftMedia, dm_id)
        if row is not None:
            return effective_media_rights(row) is None
    rid = media.get("material_revision_id")
    if isinstance(rid, int):
        revision = db.get(MaterialRevision, rid)
        if revision:
            return revision.public_use_allowed is True and revision.status != "revoked"
    return None


def build_copy_package(db: Session, target: DeliveryTarget) -> dict:
    asset = _asset_of(db, target)
    manifest = asset.candidate_manifest_json or {}
    render = (manifest.get("render") or {}).get("payload") or {}
    title = manifest.get("content", {}).get("title") or asset.title
    content: dict = {"markdown": render.get("markdown") or manifest.get("content", {}).get("body_markdown") or asset.final_body, "title": title}
    if render.get("html"):
        content["html"] = render["html"]
    if manifest.get("content", {}).get("thread_posts"):
        content["json"] = json.dumps({"title": title, "thread_posts": manifest["content"]["thread_posts"]}, ensure_ascii=False, sort_keys=True)
    media_entries = []
    for media in manifest.get("media", []):
        if media.get("rights", {}).get("public_use_allowed") is not True:
            raise HTTPException(409, f"候选清单包含未获公开权限的素材: {media.get('draft_media_id')}")
        # 实时权利复核：批准快照之后撤权（revision/status 或 use 行 revoked）必须阻止
        live = _live_media_rights(db, media)
        if live is False:
            raise HTTPException(409, f"素材公开使用权限已撤销: {media.get('material_revision_id') or media.get('draft_media_id')}")
        media_entries.append({
            "draft_media_id": media.get("draft_media_id"),
            "material_revision_id": media.get("material_revision_id"),
            "hash": media.get("hash"),
            "role": media.get("role"),
            "sort_order": media.get("sort_order"),
            "placement": media.get("placement") or {},
            "alt_text": media.get("alt_text"),
            "caption": media.get("caption"),
        })
    package_manifest = {
        "schema_version": 2,
        "target_id": target.id,
        "asset_id": asset.id,
        "channel": target.channel,
        "content_form": target.content_form,
        "account_ref": target.account_ref,
        "action": target.action,
        "authorization_version": target.authorization_version,
        "approved_candidate_hash": asset.approved_candidate_hash,
        "renderer": (manifest.get("render") or {}).get("renderer_key"),
        "media": media_entries,
        "citations": manifest.get("citations", []),
        "declarations": manifest.get("declarations", []),
        "remote_call": False,
    }
    return {"manifest": package_manifest, "content": content}


def package_zip_bytes(db: Session, target: DeliveryTarget) -> tuple[bytes, str]:
    """v2 通用成品包（保留 media order/placement 与交付说明）。v1 目标由 article_handoff 兼容路径处理。"""
    package = build_copy_package(db, target)
    manifest, content = package["manifest"], package["content"]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
        archive.writestr("content.md", content["markdown"])
        if content.get("html"):
            archive.writestr("content.html", content["html"])
        if content.get("json"):
            archive.writestr("thread.json", content["json"])
        archive.writestr(
            "publish-guide.md",
            f"# 交付说明\n\n- 渠道：{target.channel} / {target.content_form}\n- 账号：{target.account_ref}\n"
            f"- 候选哈希：{target.approved_candidate_hash}\n- 动作：{target.action}\n\n"
            "媒体请按 manifest.media 的 sort_order 与 placement 顺序摆放；发布完成后回填回执。\n",
        )
        for media in manifest["media"]:
            data = _media_bytes(db, media)
            if data is None:
                raise HTTPException(409, "批准素材文件缺失，不能导出成品包")
            if hashlib.sha256(data).hexdigest() != media.get("hash"):
                raise HTTPException(409, "批准素材文件校验失败，不能导出成品包")
            suffix = _media_suffix(db, media)
            archive.writestr(f"media/{(media.get('sort_order') or 0):02d}-{media.get('draft_media_id')}{suffix}", data)
    filename = f"delivery-target-{target.id}.zip"
    return buffer.getvalue(), filename


def _media_suffix(db: Session, media: dict) -> str:
    """R4-N1：按实际 mime 推导包内媒体扩展名（不再硬编码 .png）。"""
    mimes: list[str] = []
    rid = media.get("material_revision_id")
    if isinstance(rid, int):
        revision = db.get(MaterialRevision, rid)
        if revision:
            mimes.append(revision.mime_type or "")
    dm_id = media.get("draft_media_id")
    if isinstance(dm_id, int):
        row = db.get(DraftMedia, dm_id)
        if row:
            mimes.append(row.mime_type or "")
    mime = next((m for m in mimes if m), "")
    table = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/webp": ".webp",
        "image/gif": ".gif",
        "application/pdf": ".pdf",
        "video/mp4": ".mp4",
        "audio/mpeg": ".mp3",
    }
    return table.get(mime.lower(), ".bin")


def _media_bytes(db: Session, media: dict) -> bytes | None:
    from .asset_media import MEDIA_ROOT

    rid = media.get("material_revision_id")
    if isinstance(rid, int):
        revision = db.get(MaterialRevision, rid)
        if revision and revision.file_path:
            path = MEDIA_ROOT / revision.file_path
            if path.is_file():
                return path.read_bytes()
    dm_id = media.get("draft_media_id")
    if isinstance(dm_id, int):
        row = db.get(DraftMedia, dm_id)
        if row and row.file_path:
            path = MEDIA_ROOT / row.file_path
            if path.is_file():
                return path.read_bytes()
        if row and row.material_revision_id:
            revision = db.get(MaterialRevision, row.material_revision_id)
            if revision and revision.file_path:
                path = MEDIA_ROOT / revision.file_path
                if path.is_file():
                    return path.read_bytes()
    return None
