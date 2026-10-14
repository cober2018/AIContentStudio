"""Delivery Router 服务（D21–D25/§6.24）：唯一远端副作用入口。

执行顺序（D22）：validate → persist attempt(prepared) → COMMIT → call publisher → persist result。
超时无法确认 → attempt=unknown + target=reconciliation_needed；不自动 fallback 重发。
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..models import (
    AuditLog,
    ContentAccount,
    ContentAsset,
    ContentUnit,
    DeliveryAction,
    DeliveryAttempt,
    DeliveryReceipt,
    DeliveryTarget,
    DeliveryTargetStatus,
    DraftMedia,
    MaterialRevision,
    Review,
    utcnow,
)
from .capability_integrations import publisher_target_verified
from .content_harness.channel_registry import resolve_content_form
from .content_harness.contracts import PublisherResult
from .content_harness.publishers import bootstrap_publishers
from .content_harness.registry import registry

ACTIONS = {a.value for a in DeliveryAction}
_SAFE_REMOTE_ID = re.compile(r"[A-Za-z0-9_-]{1,128}\Z")
_SAFE_REASON = re.compile(r"[a-z][a-z0-9_]{0,79}\Z")


def _hash(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def safe_publisher_result(result: PublisherResult) -> PublisherResult:
    status = result.status if result.status in {"succeeded", "failed", "unknown"} else "unknown"
    remote_id = result.remote_id if isinstance(result.remote_id, str) and _SAFE_REMOTE_ID.fullmatch(result.remote_id) else None
    if result.remote_id is not None and remote_id is None:
        status = "unknown"
    raw_metadata = result.metadata if isinstance(result.metadata, dict) else {}
    metadata = {}
    if raw_metadata.get("channel") in {"wechat", "x", "xiaohongshu", "douyin"}:
        metadata["channel"] = raw_metadata["channel"]
    if type(raw_metadata.get("draft_box")) is bool:
        metadata["draft_box"] = raw_metadata["draft_box"]
    reason = result.error if isinstance(result.error, str) and _SAFE_REASON.fullmatch(result.error) else None
    if status != "succeeded" and reason is None:
        reason = "publisher_result_unconfirmed" if status == "unknown" else "publisher_execution_failed"
    return PublisherResult(status=status, remote_id=remote_id, metadata=metadata, error=reason)


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


def project_v5_wewrite_payload(manifest: dict) -> dict:
    """Project the exact approved article into the legacy CLI input without rewriting it."""
    target = manifest.get("target") or {}
    if (manifest.get("schema_version") != 5 or target.get("channel") != "wechat"
            or target.get("content_form") != "article" or target.get("artifact_kind") != "text"):
        raise HTTPException(422, "capability_unavailable: 仅支持v5公众号图文")
    title = (manifest.get("content") or {}).get("title")
    body = (manifest.get("render") or {}).get("text")
    assets = manifest.get("assets") or []
    covers = [ref for ref in assets if ref.get("role") == "cover"]
    if (not isinstance(title, str) or not title.strip() or len(title) > 64
            or not isinstance(body, str) or not body.strip() or len(covers) != 1
            or not isinstance(covers[0].get("material_revision_id"), int)):
        raise HTTPException(409, "v5公众号候选缺少可发布的冻结标题、正文或唯一封面")
    return {**manifest, "render": {**manifest["render"], "payload": {
        "title": title, "digest": title, "markdown": body,
    }}}


def _v5_cover_bytes(db: Session, manifest: dict) -> bytes:
    from .materials import read_bytes_checked, sniff_mime

    cover = next(ref for ref in manifest["assets"] if ref["role"] == "cover")
    revision = db.get(MaterialRevision, cover["material_revision_id"])
    if revision is None or revision.mime_type not in {"image/png", "image/jpeg"}:
        raise HTTPException(422, "capability_unavailable: 公众号封面需为PNG或JPEG")
    data = read_bytes_checked(db, revision, require_public=True)
    if (hashlib.sha256(data).hexdigest() != cover["content_hash_snapshot"]
            or sniff_mime(data, None) != revision.mime_type):
        raise HTTPException(409, "v5封面与冻结哈希不一致")
    return data


def authorize_target(db: Session, asset: ContentAsset, payload, user, *, _short_draft_request=None) -> DeliveryTarget:
    """通用交付目标授权：channel/form/action 经 Registry 验证（D21），幂等。"""
    schema = (asset.candidate_manifest_json or {}).get("schema_version")
    is_variant = schema == 5
    is_master = not is_variant and (asset.content_master_revision_id is not None or schema == 4)
    if is_variant:
        from .content_masters import owned_unit
        from .production_validation import validate_live_v5_candidate

        owned_unit(db, asset.project_id, asset.content_unit_id, user, mutate=True)
        db.refresh(asset)
        validate_live_v5_candidate(db, asset, require_approved=True, lock_live=True)
        if payload.action not in {DeliveryAction.copy_package.value, DeliveryAction.manual_handoff.value, DeliveryAction.auto_draft.value}:
            raise HTTPException(422, "capability_unavailable: v5远端账号/渠道/形态/动作尚未验证")
        if payload.channel != asset.channel or payload.content_form != asset.content_form:
            raise HTTPException(409, "目标渠道与形态必须与冻结Variant一致")
    elif is_master:
        from .content_masters import owned_unit
        from .production_validation import validate_live_v4_candidate

        owned_unit(db, asset.project_id, asset.content_unit_id, user, mutate=True)
        db.refresh(asset)
        validate_live_v4_candidate(db, asset, require_approved=True, lock_live=True)
        if payload.action not in {DeliveryAction.copy_package.value, DeliveryAction.manual_handoff.value}:
            raise HTTPException(422, "capability_unavailable: v4当前仅支持本地成品包/人工交付")
        if payload.content_form != asset.content_form:
            raise HTTPException(409, "目标内容形态必须与冻结候选一致")
    if asset.project_id is not None:
        from .project_authorization import authorize_project_asset

        authorize_project_asset(db, asset, user, mutate=True)
    if asset.status not in {"approved", "exported"} or not asset.approved_candidate_hash:
        raise HTTPException(409, "只有已批准内容才能创建交付目标")
    content_account_id = getattr(payload, "content_account_id", None)
    if asset.project_id is not None:
        from .candidates import candidate_hash
        if candidate_hash(asset.candidate_manifest_json or {}) != asset.candidate_hash or asset.candidate_hash != asset.approved_candidate_hash:
            raise HTTPException(409, "项目候选哈希与已批准内容不一致")
        approved = db.scalar(select(Review.id).where(
            Review.content_asset_id == asset.id,
            Review.decision == "approved",
            Review.candidate_hash == asset.candidate_hash,
        ).order_by(Review.id.desc()).limit(1))
        if approved is None:
            raise HTTPException(409, "项目候选尚未经过独立内容审批")
        if not is_variant:
            from .production_validation import latest_legacy_candidate_id

            current_candidate_id = latest_legacy_candidate_id(db, asset.content_unit_id)
            if current_candidate_id != asset.id:
                raise HTTPException(409, "历史候选只可查看，不能新增交付授权")
        unit = db.get(ContentUnit, asset.content_unit_id)
        if unit is None or (not is_variant and unit.channel_id and unit.channel_id != payload.channel):
            raise HTTPException(409, "目标渠道与内容单元不一致")
        frozen_account = (asset.candidate_manifest_json or {}).get("target", {}).get("account") if is_variant else None
        if frozen_account is not None and frozen_account["content_account_id"] != content_account_id:
            raise HTTPException(409, {"code": "candidate_target_account_mismatch"})
        if content_account_id is not None:
            account = db.get(ContentAccount, content_account_id)
            if account is None or account.status != "active" or account.persona_id != unit.persona_id:
                raise HTTPException(404, "内容账号不存在")
            # v5 现代候选：origin 账号不再是目标锁；每个目标账号独立授权。
            # legacy（master）候选保持固定账号语义，不得静默松绑。
            if not is_variant and unit.account_id is not None and unit.account_id != account.id:
                raise HTTPException(404, "内容账号不存在")
            # 已登记平台的账号必须与目标渠道一致；老式未绑平台账号保持原行为。
            if account.platform_channel and account.platform_channel != payload.channel:
                raise HTTPException(422, "内容账号平台与目标渠道不一致")
            if is_variant:
                from .series_targets import guard_enabled_binding

                guard_enabled_binding(db, series_id=unit.series_id, account_id=account.id, content_form=payload.content_form)
                if frozen_account is None:
                    from ..models import ContentAccountRevision

                    target_revision = db.scalar(select(ContentAccountRevision).where(ContentAccountRevision.account_id == account.id)
                        .order_by(ContentAccountRevision.revision_no.desc()).limit(1))
                    if target_revision is not None and target_revision.profile_json:
                        raise HTTPException(409, {"code": "target_specific_adaptation_required"})
        if payload.action in {DeliveryAction.auto_draft.value, DeliveryAction.assisted_draft.value} and not is_variant:
            raise HTTPException(422, "capability_unavailable: 内容账号尚无已验证的渠道/远端发布映射")
    elif content_account_id is not None:
        raise HTTPException(422, "旧候选不能推断新的内容账号归属")
    account_key = f"content-account:{content_account_id}" if content_account_id is not None else f"legacy-ref:{payload.account_ref}"
    try:
        spec = resolve_content_form(db, payload.channel, payload.content_form)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if payload.action not in ACTIONS:
        raise HTTPException(422, f"action 只允许 {sorted(ACTIONS)}")
    publisher, publisher_key, publisher_version = resolve_publisher(spec.channel, spec.content_form, payload.action)
    official = (is_variant and payload.action == DeliveryAction.auto_draft.value
                and payload.channel == "wechat" and content_account_id is not None
                and db.get(ContentAccount, content_account_id).platform_channel == "wechat")
    if official:
        from . import wechat_official
        from .wechat_official_delivery import validate_target

        publisher_key, publisher_version = wechat_official.KEY, wechat_official.VERSION
        publisher = registry.resolve("publisher", publisher_key, publisher_version)
        scope_target = DeliveryTarget(content_asset_id=asset.id, content_account_id=content_account_id,
            channel=payload.channel, content_form=payload.content_form, action=payload.action,
            account_ref=payload.account_ref, publisher_key=publisher_key, publisher_version=publisher_version,
            approved_candidate_hash=asset.approved_candidate_hash, authorized_by=user.email)
        validate_target(db, scope_target, user, _short_draft_request=_short_draft_request)
    elif _short_draft_request is not None:
        raise HTTPException(422, "official_experiment_scope_invalid")
    capability = None
    if publisher is not None:
        capability = publisher.capability(spec.channel, spec.content_form, payload.account_ref)
        cap_dict = {
            "publisher_key": capability.publisher_key, "action": capability.action,
            "available": capability.available, "reason": capability.reason,
            "verified": bool(getattr(publisher, "verified", lambda: True)()),
        }
        if capability.available is False and not official:
            raise HTTPException(422, f"capability_unavailable: {capability.reason}")
        capability = cap_dict
    else:
        capability = {"publisher_key": publisher_key, "action": payload.action, "available": True, "verified": False, "legacy": True}
    if official:
        capability = {"publisher_key": publisher_key, "action": payload.action,
                      "available": True, "verified": _short_draft_request is None,
                      "remote_verified": _short_draft_request is None}
        if _short_draft_request is not None:
            capability.update(available=False, reason="bounded_experiment_only")
    elif is_variant and payload.action == DeliveryAction.auto_draft.value:
        projected = project_v5_wewrite_payload(asset.candidate_manifest_json or {})
        _v5_cover_bytes(db, projected)
        scope_target = DeliveryTarget(content_account_id=content_account_id, channel=payload.channel,
                                      content_form=payload.content_form, action=payload.action,
                                      account_ref=payload.account_ref, publisher_key=publisher_key,
                                      publisher_version=publisher_version)
        if not publisher_target_verified(db, scope_target, registry):
            raise HTTPException(422, "publisher_unverified: 当前账号、渠道、形态、动作或配置尚无有效验证")
        capability = {**capability, "verified": True, "remote_verified": True}
    elif is_variant:
        capability = {**capability, "manual": True, "remote_verified": False}
    if content_account_id is not None:
        # 冻结精确目标账号身份：平台字符串不是账号，同平台 A/B 是不同目标。
        from ..models import ContentAccountRevision

        account = db.get(ContentAccount, content_account_id)
        account_revision = db.scalar(select(ContentAccountRevision).where(ContentAccountRevision.account_id == account.id).order_by(ContentAccountRevision.revision_no.desc()).limit(1))
        capability = {**capability, "target_account": {
            "content_account_id": account.id, "platform_channel": account.platform_channel,
            "platform_account_id": account.platform_account_id,
            "account_revision_id": account_revision.id if account_revision else None,
            "account_profile_checksum": account_revision.checksum if account_revision else None,
        }}
    # 渠道一致性：v1 资产仍要求与批准渠道一致；v2 同样
    if asset.channel != payload.channel:
        raise HTTPException(409, "目标渠道必须与批准资产渠道一致")

    existing = db.scalars(
        select(DeliveryTarget).where(
            DeliveryTarget.content_asset_id == asset.id,
            DeliveryTarget.approved_candidate_hash == asset.approved_candidate_hash,
            DeliveryTarget.channel == payload.channel,
            DeliveryTarget.content_form == payload.content_form,
            DeliveryTarget.authorization_account_key == account_key,
            DeliveryTarget.action == payload.action,
            DeliveryTarget.authorization_version == payload.authorization_version,
        )
    ).first()
    if existing:
        if existing.account_ref != payload.account_ref:
            raise HTTPException(409, "账号引用已变化，请使用新的显式授权版本")
        return existing
    target = DeliveryTarget(
        content_asset_id=asset.id,
        content_account_id=content_account_id,
        channel=payload.channel,
        content_form=payload.content_form,
        account_ref=payload.account_ref,
        authorization_account_key=account_key,
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
        db.flush()
        if asset.project_id is not None:
            from .project_events import record_project_event

            record_project_event(db, project_id=asset.project_id, event_type="delivery.authorized", actor=user.email,
                                 entity_type="delivery_target", entity_id=target.id,
                                 payload={"unit_id": asset.content_unit_id, "candidate_id": asset.id, "candidate_hash": asset.candidate_hash, "action": target.action})
        if is_master or is_variant:
            db.flush()
            db.expire_all()
            owned_unit(db, asset.project_id, asset.content_unit_id, user, mutate=True)
            if is_variant:
                validate_live_v5_candidate(db, asset, require_approved=True, lock_live=True)
            else:
                validate_live_v4_candidate(db, asset, require_approved=True, lock_live=True)
            if target.approved_candidate_hash != asset.candidate_hash:
                raise HTTPException(409, "授权提交前候选发生变化")
        if _short_draft_request is None:
            db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception:  # noqa: BLE001 并发幂等
        db.rollback()
        if _short_draft_request is not None:
            raise HTTPException(409, "official_experiment_prepare_conflict") from None
        concurrent = db.scalars(
            select(DeliveryTarget).where(
                DeliveryTarget.content_asset_id == asset.id,
                DeliveryTarget.approved_candidate_hash == asset.approved_candidate_hash,
                DeliveryTarget.channel == payload.channel,
                DeliveryTarget.content_form == payload.content_form,
                DeliveryTarget.authorization_account_key == account_key,
                DeliveryTarget.action == payload.action,
                DeliveryTarget.authorization_version == payload.authorization_version,
            )
        ).first()
        if concurrent:
            if concurrent.account_ref != payload.account_ref:
                raise HTTPException(409, "账号引用已变化，请使用新的显式授权版本")
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
    if manifest.get("schema_version") == 5:
        from .production_validation import validate_live_v5_candidate

        return validate_live_v5_candidate(db, asset, require_approved=True, lock_live=True)
    if manifest.get("schema_version") == 4 or asset.content_master_revision_id is not None:
        raise HTTPException(422, "capability_unavailable: v4尚无已验证Publisher适配器，请使用本地成品包")
    if asset.project_id is not None:
        from .project_review import live_evidence_reasons

        evidence_reasons = live_evidence_reasons(db, asset.project_id, manifest)
        if evidence_reasons:
            raise HTTPException(409, {"code": "evidence_unready", "reasons": evidence_reasons})
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
    request_input = (manifest.get("render") or {}).get("payload") or {}
    if manifest.get("schema_version") == 5:
        request_input = {"payload": request_input, "cover_hash": next(
            ref["content_hash_snapshot"] for ref in manifest["assets"] if ref["role"] == "cover")}
    request_hash = _hash(json.dumps(request_input, ensure_ascii=False, sort_keys=True, default=str))
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
    if target.publisher_key == "publisher.wechat.official":
        from .wechat_official_delivery import execute

        return execute(db, target_id, user)
    from .project_authorization import authorize_project_target

    authorize_project_target(db, target, user, mutate=True)
    if target.authorized_by and target.authorized_by != user.email:
        raise HTTPException(403, "该账号交付目标未授权给当前操作人")
    if target.status == DeliveryTargetStatus.blocked.value:
        raise HTTPException(409, "该目标的公开使用权限已撤销，不能再交付")
    if target.action == DeliveryAction.manual_handoff.value:
        raise HTTPException(409, "manual_handoff 目标走成品包 + 人工回填，不能 execute")
    if target.action == DeliveryAction.auto_draft.value and not publisher_target_verified(db, target, registry):
        raise HTTPException(409, "publisher_unverified：当前账号、渠道、形态、动作或配置尚无有效验证")
    # R3-3：统一实时校验在 prepare（落 attempt）之前——校验失败不产生 attempt
    asset = _asset_of(db, target)
    manifest = validate_live_candidate_payload(db, asset)
    if manifest.get("schema_version") == 5:
        if target.action != DeliveryAction.auto_draft.value or target.publisher_key != "publisher.wechat.wewrite":
            raise HTTPException(422, "capability_unavailable: v5远端动作尚未验证")
        manifest = project_v5_wewrite_payload(manifest)
        cover_bytes = _v5_cover_bytes(db, manifest)
    else:
        cover_bytes = None

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
        if asset.project_id is not None:
            from .project_events import record_project_event

            record_project_event(db, project_id=asset.project_id, event_type="delivery.failed", actor=user.email,
                                 entity_type="delivery_attempt", entity_id=attempt.id, payload={"target_id": target.id})
        db.commit()
        raise HTTPException(422, f"publisher 未注册: {target.publisher_key}") from exc

    attempt.status = "running"
    db.commit()

    if target.publisher_key == "publisher.wechat.wewrite":
        manifest = {**manifest, "_cover_bytes": cover_bytes if cover_bytes is not None else _cover_bytes(db, asset, manifest)}
        if cover_bytes is not None:
            from .materials import sniff_mime

            manifest["_cover_mime"] = sniff_mime(cover_bytes, None)
    try:
        result = safe_publisher_result(publisher.deliver(manifest, target, attempt))
    except Exception:  # noqa: BLE001 外部效果可能已发生；不得重试，也不得持久化可能含密钥的异常原文。
        result = PublisherResult(status="unknown", error="publisher_result_unconfirmed")

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
    if asset.project_id is not None:
        from .project_events import record_project_event

        event_type = {"succeeded": "delivery.succeeded", "unknown": "delivery.unknown", "failed": "delivery.failed"}[attempt.status]
        record_project_event(db, project_id=asset.project_id, event_type=event_type, actor=user.email,
                             entity_type="delivery_attempt", entity_id=attempt.id,
                             payload={"unit_id": asset.content_unit_id, "candidate_id": asset.id, "target_id": target.id, "attempt_status": attempt.status})
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
    from .project_authorization import authorize_project_target

    authorize_project_target(db, target, user, mutate=True)
    if target.authorized_by and target.authorized_by != user.email:
        raise HTTPException(403, "该账号交付目标未授权给当前操作人")
    # Serialize the decision with other reconciliations before reading the attempt head.
    db.execute(update(DeliveryTarget).where(DeliveryTarget.id == target.id)
               .values(status=DeliveryTarget.status).execution_options(synchronize_session=False))
    db.refresh(target)
    authorize_project_target(db, target, user, mutate=True)
    last = db.scalars(
        select(DeliveryAttempt).where(DeliveryAttempt.target_id == target.id).order_by(DeliveryAttempt.attempt_no.desc()).limit(1)
    ).first()
    resolution = payload.resolution
    evidence_ref = getattr(payload, "evidence_ref", None)
    if evidence_ref is None:
        note = (payload.note or "").strip()
        if not note or len(note) > 2000:
            raise HTTPException(422, "reconciliation_evidence_required")
        evidence_ref = "sha256:" + hashlib.sha256(note.encode("utf-8")).hexdigest()
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", evidence_ref) or resolution not in {"delivered", "not_delivered"}:
        raise HTTPException(422, "reconciliation_evidence_invalid")
    expected = getattr(payload, "expected_attempt_id", None)
    if expected is not None and (last is None or last.id != expected):
        raise HTTPException(409, "reconciliation_attempt_changed")
    if (target.publisher_key == "publisher.wechat.official" and last is not None
            and last.status in {"prepared", "running"}):
        if expected != last.id:
            raise HTTPException(409, "reconciliation_attempt_required")
        # Only an explicit evidenced decision invalidates an interrupted worker's private claim.
        last.response_metadata_json = {**(last.response_metadata_json or {}),
            "claim_hash": _hash("manual-interruption", str(last.id), evidence_ref), "interrupted": True}
        last.status = "unknown"
        target.status = DeliveryTargetStatus.reconciliation_needed.value
    if target.action == DeliveryAction.auto_draft.value and (last is None or last.status != "unknown"):
        raise HTTPException(409, "reconciliation_unknown_attempt_required")
    decision_key = _hash(str(target.id), target.approved_candidate_hash, str(last.id if last else 0), resolution, evidence_ref)
    previous = db.scalar(select(AuditLog).where(AuditLog.event == "delivery_target.reconciled",
        AuditLog.entity_type == "delivery_target", AuditLog.entity_id == str(target.id)).order_by(AuditLog.id.desc()).limit(1))
    if previous and (previous.detail_json or {}).get("decision_key") == decision_key:
        return {"target_id": target.id, "status": target.status}
    if (last and (last.response_metadata_json or {}).get("reconciled") is not None
            or target.status != DeliveryTargetStatus.reconciliation_needed.value):
        raise HTTPException(409, "reconciliation_decision_conflict")
    if resolution == "delivered":
        target.status = DeliveryTargetStatus.human_confirmed.value
        db.add(DeliveryReceipt(target_id=target.id, approved_candidate_hash=target.approved_candidate_hash,
            action=target.action, idempotency_key=decision_key, status="human_confirmed", operator=user.email,
            delivered_at=utcnow(), evidence_ref=evidence_ref, verification_method="human_reconciliation"))
    elif resolution == "not_delivered":
        target.status = DeliveryTargetStatus.target_authorized.value
    if last:
        last.response_metadata_json = {**(last.response_metadata_json or {}), "reconciled": resolution,
                                       "evidence_ref": evidence_ref, "decision_key": decision_key}
    db.add(AuditLog(event="delivery_target.reconciled", actor=user.email, entity_type="delivery_target",
                    entity_id=str(target.id), detail_json={"resolution": resolution, "evidence_ref": evidence_ref,
                        "decision_key": decision_key, "attempt_id": last.id if last else None, "platform_verified": False}))
    asset = db.get(ContentAsset, target.content_asset_id)
    if asset.project_id is not None:
        from .project_events import record_project_event

        record_project_event(db, project_id=asset.project_id, event_type="delivery.reconciled", actor=user.email,
                             entity_type="delivery_target", entity_id=target.id, payload={"resolution": resolution, "unit_id": asset.content_unit_id})
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
                from .materials import read_bytes_checked

                return read_bytes_checked(db, revision, require_public=True)
            raise HTTPException(409, "批准素材版本不存在")
        dm_id = media.get("draft_media_id")
        if isinstance(dm_id, int):
            row = db.get(DraftMedia, dm_id)
            if row and row.file_path:
                from .material_storage import read_legacy_bytes

                try:
                    return read_legacy_bytes(row.file_path, expected_hash=media.get("hash") or row.content_hash)
                except (OSError, ValueError):
                    return b""
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
    if manifest.get("schema_version") == 5:
        from .production_packages import build_v5_package

        return build_v5_package(db, target, asset)
    if manifest.get("schema_version") == 4 or asset.content_master_revision_id is not None:
        from .production_packages import build_v4_package

        return build_v4_package(db, target, asset)
    if asset.project_id is not None:
        if manifest.get("schema_version") != 3:
            raise HTTPException(409, "项目候选缺少 v3 冻结清单")
        validate_live_candidate_payload(db, asset)
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
        if live is False or (asset.project_id is not None and live is not True):
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
        "schema_version": 3 if asset.project_id is not None else 2,
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
    if asset.project_id is not None:
        package_manifest["candidate"] = {"id": asset.id, "hash": asset.candidate_hash}
        package_manifest["project"] = manifest["project"]
        package_manifest["identity"] = manifest["identity"]
        package_manifest["evidence"] = manifest["evidence"]
        package_manifest["production"] = manifest["production"]
    return {"manifest": package_manifest, "content": content}


def package_zip_bytes(db: Session, target: DeliveryTarget) -> tuple[bytes, str]:
    """v2 通用成品包（保留 media order/placement 与交付说明）。v1 目标由 article_handoff 兼容路径处理。"""
    package = build_copy_package(db, target)
    manifest, content = package["manifest"], package["content"]
    if manifest["schema_version"] == 5:
        from .production_packages import v5_zip_bytes

        return v5_zip_bytes(db, target, package)
    if manifest["schema_version"] == 4:
        from .production_packages import v4_zip_bytes

        return v4_zip_bytes(db, target, package)
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
            media_id = media.get("draft_media_id") or media.get("material_revision_id")
            archive.writestr(f"media/{(media.get('sort_order') or 0):02d}-{media_id}{suffix}", data)
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
    from .material_storage import read_legacy_bytes

    rid = media.get("material_revision_id")
    if isinstance(rid, int):
        revision = db.get(MaterialRevision, rid)
        if revision and revision.file_path:
            from .materials import read_bytes_checked

            return read_bytes_checked(db, revision)
        raise HTTPException(409, "批准素材版本不存在")
    dm_id = media.get("draft_media_id")
    if isinstance(dm_id, int):
        row = db.get(DraftMedia, dm_id)
        if row and row.file_path and not row.material_revision_id:
            try:
                return read_legacy_bytes(row.file_path, expected_hash=media.get("hash") or row.content_hash)
            except (OSError, ValueError):
                return None
        if row and row.material_revision_id:
            revision = db.get(MaterialRevision, row.material_revision_id)
            if revision and revision.file_path:
                from .materials import read_bytes_checked

                try:
                    return read_bytes_checked(db, revision)
                except HTTPException:
                    return None
    return None
