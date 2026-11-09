"""Durable official execution claim; crashed steps are never automatically reclaimed."""

from __future__ import annotations

import hashlib
import json
import secrets

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import OperationalError

from ..models import (
    AuditLog,
    CapabilityRegistration,
    ContentAsset,
    ContentUnit,
    DeliveryAttempt,
    DeliveryTarget,
    MaterialRevision,
    User,
    utcnow,
)
from . import wechat_official, wechat_official_transport
from .content_harness.publishers import bootstrap_publishers
from .wechat_official_render import (
    IMAGE_MESSAGE_SCHEMA,
    match_readback,
    prepare_article,
    prepare_image_message,
    validate_draft_render_bound,
    validate_official_render,
)


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def _event(db, target, attempt, event_type):
    from .project_events import record_project_event

    asset = db.get(ContentAsset, target.content_asset_id)
    payload = {"target_id": target.id, "unit_id": asset.content_unit_id, "candidate_id": asset.id,
               "attempt_status": attempt.status, "remote_id": attempt.remote_id}
    record_project_event(db, project_id=asset.project_id, event_type=event_type, actor=target.authorized_by,
                         entity_type="delivery_attempt", entity_id=attempt.id, payload=payload)
    db.add(AuditLog(event=event_type, actor=target.authorized_by, entity_type="delivery_attempt",
                    entity_id=str(attempt.id), detail_json=payload))


def validate_target(db, target, user):
    from .content_identity import _lock_account
    from .content_masters import owned_unit
    from .production_validation import validate_live_v5_candidate

    if (target.publisher_key != wechat_official.KEY or target.publisher_version != "1"
            or target.channel != "wechat" or target.content_form not in wechat_official.DRAFT_FORMS
            or target.action != "auto_draft" or type(target.content_account_id) is not int):
        raise HTTPException(422, "official_target_invalid")
    asset = db.get(ContentAsset, target.content_asset_id, populate_existing=True)
    if asset is None or asset.project_id is None:
        raise HTTPException(409, "official_render_required")
    owned_unit(db, asset.project_id, asset.content_unit_id, user, mutate=True)
    # Match authorization's existing source/profile order before account/target/registration.
    manifest = validate_live_v5_candidate(db, asset, require_approved=True, lock_live=True)
    account = _lock_account(db, user, target.content_account_id)
    unit = db.get(ContentUnit, asset.content_unit_id, populate_existing=True)
    if (account.persona_id != unit.persona_id or unit.account_id not in (None, account.id)
            or target.account_ref != account.platform_account_id or target.authorized_by != user.email):
        raise HTTPException(403, "official_account_scope_invalid")
    if target.id is not None:
        db.execute(update(DeliveryTarget).where(DeliveryTarget.id == target.id).values(status=DeliveryTarget.status)
                   .execution_options(synchronize_session=False))
        db.refresh(target)
    registration = db.scalar(select(CapabilityRegistration).where(
        CapabilityRegistration.kind == "publisher", CapabilityRegistration.key == wechat_official.KEY,
        CapabilityRegistration.version == "1").with_for_update().execution_options(populate_existing=True))
    if registration is None or registration.status != "configured":
        raise HTTPException(409, "official_publisher_unverified")
    if target.approved_candidate_hash != asset.candidate_hash:
        raise HTTPException(409, "official_candidate_changed")
    render = manifest.get("official_render")
    image_message = target.content_form == "image_message"
    if not isinstance(render, dict) or (render.get("schema") == IMAGE_MESSAGE_SCHEMA) != image_message:
        raise HTTPException(409, "official_render_required")
    if not image_message and render.get("renderer_version") not in {"2", "3"}:
        raise HTTPException(409, "official_asset_filename_required")
    if render.get("status") != "local_ready":
        raise HTTPException(409, "official_render_unavailable")
    from .wechat_official_render import upload_asset_metadata

    for slot in render["asset_slots"]:
        revision = db.get(MaterialRevision, slot["material_revision_id"], populate_existing=True)
        if revision is None or (not image_message and upload_asset_metadata(revision) != {"filename": slot["filename"], "mime_type": slot["mime_type"]}):
            raise HTTPException(409, "official_asset_metadata_changed")
        if image_message and revision.mime_type != slot["mime_type"]:
            raise HTTPException(409, "official_asset_metadata_changed")
    try:
        validate_official_render(render, manifest["content"], manifest["assets"], manifest["evidence_refs"])
    except ValueError:
        raise HTTPException(409, "official_render_invalid") from None
    if not image_message:
        try:
            validate_draft_render_bound(render)
        except ValueError:
            raise HTTPException(422, {"code": "official_body_limit",
                                      "message": "正文超过公众号草稿箱上限（少于 2 万字符、小于 1M），没有推送"}) from None
    runtime = wechat_official.resolve_runtime(db, account.id)
    return manifest, runtime


def prepare(db, target_id, user):
    bootstrap_publishers()
    try:
        target = db.get(DeliveryTarget, target_id, populate_existing=True)
        if target is None:
            raise HTTPException(404, "official_target_missing")
        manifest, runtime = validate_target(db, target, user)
        if target.status != "target_authorized":
            raise HTTPException(409, "official_execution_claimed")
        last = db.scalar(select(DeliveryAttempt).where(DeliveryAttempt.target_id == target_id)
                         .order_by(DeliveryAttempt.attempt_no.desc()).limit(1))
        if last is not None and not (last.status == "unknown"
                                    and (last.response_metadata_json or {}).get("reconciled") == "not_delivered"):
            raise HTTPException(409, "official_execution_claimed")
        attempt_no = last.attempt_no + 1 if last else 1
        claim = secrets.token_hex(32)
        metadata = {"schema": "wechat.official.execution.v1", "claim_hash": _hash(claim),
                    "runtime_fingerprint": runtime.fingerprint, "candidate_hash": target.approved_candidate_hash,
                    "render_hash": manifest["official_render"]["render_hash"], "resource_mapping": [],
                    "completed_steps": [], "in_flight": None}
        attempt = DeliveryAttempt(target_id=target.id, attempt_no=attempt_no,
            idempotency_key=_hash([target.id, target.approved_candidate_hash, attempt_no]),
            publisher_key=target.publisher_key, publisher_version=target.publisher_version,
            request_hash=_hash([target.approved_candidate_hash, metadata["render_hash"], runtime.fingerprint]),
            status="prepared", started_at=utcnow(), response_metadata_json=metadata)
        db.add(attempt)
        db.flush()
        attempt_id = attempt.id
        registration = db.scalar(select(CapabilityRegistration).where(
            CapabilityRegistration.kind == "publisher", CapabilityRegistration.key == wechat_official.KEY,
            CapabilityRegistration.version == "1"))
        # The user pushes with the code that is running now; a confirmed draft is checked against it.
        registration.config_fingerprint = wechat_official.implementation_fingerprint()
        _event(db, target, attempt, "delivery.prepared")
        db.commit()
        return attempt_id, claim
    except (HTTPException, OperationalError) as exc:
        db.rollback()
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(409, "official_execution_busy") from None


def _claimed(db, target_id, attempt_id, claim, user, *, readback=False):
    target = db.get(DeliveryTarget, target_id, populate_existing=True)
    manifest, runtime = validate_target(db, target, user)
    attempt = db.get(DeliveryAttempt, attempt_id, populate_existing=True)
    last_id = db.scalar(select(DeliveryAttempt.id).where(DeliveryAttempt.target_id == target_id)
                        .order_by(DeliveryAttempt.attempt_no.desc()).limit(1))
    metadata = dict(attempt.response_metadata_json or {}) if attempt else {}
    if (attempt is None or attempt.target_id != target_id or last_id != attempt_id
            or attempt.status not in {"prepared", "running"}
            or target.status != ("reconciliation_needed" if readback else "target_authorized")
            or metadata.get("claim_hash") != _hash(claim)
            or metadata.get("runtime_fingerprint") != runtime.fingerprint
            or metadata.get("candidate_hash") != target.approved_candidate_hash
            or metadata.get("render_hash") != manifest["official_render"]["render_hash"]):
        raise HTTPException(409, "official_execution_claim_invalid")
    return target, attempt, manifest, runtime, metadata


def _step(db, target_id, attempt_id, claim, user, name, operation, record, *, readback=False):
    _target, attempt, _, _, metadata = _claimed(db, target_id, attempt_id, claim, user, readback=readback)
    if metadata.get("in_flight") is not None or name in metadata["completed_steps"]:
        raise HTTPException(409, "official_step_already_claimed")
    metadata["in_flight"] = name
    attempt.status = "running"
    attempt.response_metadata_json = metadata
    db.commit()
    # Durable in-flight marker survives a process crash, before reacquiring live authorization.
    _target, attempt, manifest, runtime, metadata = _claimed(db, target_id, attempt_id, claim, user, readback=readback)
    if metadata.get("in_flight") != name:
        raise HTTPException(409, "official_step_claim_invalid")
    value = operation(manifest, runtime, metadata)
    record(attempt, metadata, value)
    metadata["completed_steps"] = [*metadata["completed_steps"], name]
    metadata["in_flight"] = None
    attempt.response_metadata_json = metadata
    db.commit()
    return value


def _finish(db, target_id, attempt_id, claim, *, error=None):
    db.rollback()
    db.execute(update(DeliveryTarget).where(DeliveryTarget.id == target_id).values(status=DeliveryTarget.status)
               .execution_options(synchronize_session=False))
    target = db.get(DeliveryTarget, target_id, populate_existing=True)
    attempt = db.get(DeliveryAttempt, attempt_id, populate_existing=True)
    metadata = dict(attempt.response_metadata_json or {})
    if metadata.get("claim_hash") != _hash(claim) or attempt.status not in {"prepared", "running"}:
        raise HTTPException(409, "official_execution_claim_invalid")
    if error is None and (metadata.get("readback_hash") or
                          (metadata.get("create_confirmed") and attempt.remote_id)):
        attempt.status, target.status = "succeeded", "awaiting_manual_receipt"
        attempt.error = None
    else:
        partial = bool(metadata.get("resource_mapping") or attempt.remote_id or metadata.get("in_flight"))
        attempt.status = "unknown" if partial else "failed"
        target.status = "reconciliation_needed" if partial else "failed"
        attempt.error = "official_result_unconfirmed" if partial else "official_execution_blocked"
        # Never persist exception text: even provider failures may contain credentials or approved content.
        metadata["failure_diagnostic"] = wechat_official_transport.failure_diagnostic(error)
        attempt.response_metadata_json = metadata
    attempt.finished_at = utcnow()
    _event(db, target, attempt, f"delivery.{attempt.status}")
    db.commit()
    return {"attempt_id": attempt.id, "attempt_no": attempt.attempt_no, "status": attempt.status,
            "remote_id": attempt.remote_id, "error": attempt.error, "target_status": target.status}


def execute(db, target_id, user):
    attempt_id, claim = prepare(db, target_id, user)
    return execute_prepared(db, target_id, attempt_id, claim, user)


def execute_prepared(db, target_id, attempt_id, claim, user):
    target, _attempt, _manifest, runtime, _metadata = _claimed(db, target_id, attempt_id, claim, user)
    if (_attempt.status != "prepared" or _metadata.get("in_flight") is not None
            or _metadata.get("completed_steps") or _metadata.get("execution_started")):
        raise HTTPException(409, "official_execution_claimed")
    # Persist the worker start under the target lock before any second worker can reuse the claim.
    _attempt.response_metadata_json = {**_metadata, "execution_started": True}
    db.commit()
    client = wechat_official_transport.OfficialTransport()
    image_message = target.content_form == "image_message"
    db.rollback()
    try:
        token = _step(db, target_id, attempt_id, claim, user, "token",
            lambda manifest, runtime, metadata: client.token(runtime), lambda attempt, metadata, value: None)
        _target, _attempt, manifest, _runtime, _metadata = _claimed(db, target_id, attempt_id, claim, user)
        slots = list(manifest["official_render"]["asset_slots"])
        db.rollback()
        for index, slot in enumerate(slots):
            def upload(current, current_runtime, state, slot=slot):
                from .materials import read_bytes_checked, sniff_mime

                revision = db.get(MaterialRevision, slot["material_revision_id"], populate_existing=True)
                if revision is None:
                    raise HTTPException(409, "official_asset_missing")
                data = read_bytes_checked(db, revision, require_public=True)
                if hashlib.sha256(data).hexdigest() != slot["content_hash"] or sniff_mime(data, None) != revision.mime_type:
                    raise HTTPException(409, "official_asset_changed")
                # Covers and image-message pictures are permanent materials; article body pictures use uploadimg.
                method = client.upload_cover if slot["usage"] in {"cover", "image"} else client.upload_inline
                return {**slot, "account_id": current_runtime.account_id, "appid": current_runtime.appid,
                        "runtime_fingerprint": current_runtime.fingerprint,
                        "remote_ref": method(token, data, slot["mime_type"], slot["filename"])}

            _step(db, target_id, attempt_id, claim, user, f"asset_{index}", upload,
                  lambda attempt, metadata, value: metadata["resource_mapping"].append(value))
        def create(manifest, runtime, metadata):
            if image_message:
                return client.create_image_message(token, prepare_image_message(manifest, runtime, metadata["resource_mapping"]))
            return client.create_draft(token, prepare_article(manifest, runtime, metadata["resource_mapping"]))

        _step(db, target_id, attempt_id, claim, user, "create", create,
              lambda attempt, metadata, value: (setattr(attempt, "remote_id", value),
                                                metadata.update(create_confirmed=True)))
        return _finish(db, target_id, attempt_id, claim)
    except (HTTPException, ValueError, OSError) as error:
        return _finish(db, target_id, attempt_id, claim, error=error)


def readback(db, target_id, expected_attempt_id, user):
    bootstrap_publishers()
    try:
        target = db.get(DeliveryTarget, target_id, populate_existing=True)
        if target is None:
            raise HTTPException(404, "official_target_missing")
        _manifest, runtime = validate_target(db, target, user)
        if target.content_form != "article":
            # draft/get readback is only implemented for articles; image messages are confirmed in the 公众号 backend.
            raise HTTPException(409, "official_readback_unavailable")
        attempt = db.scalar(select(DeliveryAttempt).where(DeliveryAttempt.target_id == target_id)
                            .order_by(DeliveryAttempt.attempt_no.desc()).limit(1))
        metadata = dict(attempt.response_metadata_json or {}) if attempt else {}
        if (attempt is None or attempt.id != expected_attempt_id or attempt.status != "unknown"
                or not attempt.remote_id or target.status != "reconciliation_needed"
                or metadata.get("readback_claimed") or metadata.get("runtime_fingerprint") != runtime.fingerprint
                or metadata.get("candidate_hash") != target.approved_candidate_hash):
            raise HTTPException(409, "official_readback_unavailable")
        claim = secrets.token_hex(32)
        metadata.update(claim_hash=_hash(claim), readback_claimed=True, in_flight=None)
        attempt.response_metadata_json = metadata
        attempt.status = "running"
        attempt_id = attempt.id
        db.commit()
    except (HTTPException, OperationalError) as exc:
        db.rollback()
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(409, "official_readback_busy") from None
    client = wechat_official_transport.OfficialTransport()
    try:
        token = _step(db, target_id, attempt_id, claim, user, "readback_token",
            lambda manifest, runtime, metadata: client.token(runtime), lambda *args: None, readback=True)
        _step(db, target_id, attempt_id, claim, user, "explicit_read",
            lambda manifest, runtime, metadata: match_readback(prepare_article(manifest, runtime, metadata["resource_mapping"]),
                client.read_draft(token, db.get(DeliveryAttempt, attempt_id).remote_id)),
            lambda attempt, metadata, value: metadata.update(readback_hash=value), readback=True)
        return _finish(db, target_id, attempt_id, claim)
    except (HTTPException, ValueError, OSError) as error:
        return _finish(db, target_id, attempt_id, claim, error=error)
