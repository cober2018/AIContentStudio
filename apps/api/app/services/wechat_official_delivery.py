"""Durable official execution claim; crashed steps are never automatically reclaimed."""

from __future__ import annotations

import hashlib
import json
import secrets
import time

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError, OperationalError

from ..models import (
    AuditLog,
    CapabilityRegistration,
    CapabilityVerification,
    ContentAsset,
    ContentUnit,
    DeliveryAttempt,
    DeliveryTarget,
    MaterialRevision,
    User,
    utcnow,
)
from . import wechat_official, wechat_official_transport
from .capability_integrations import publisher_target_verified
from .content_harness.publishers import bootstrap_publishers
from .content_harness.registry import registry
from .wechat_official_render import (
    match_readback,
    prepare_article,
    validate_article_render,
    validate_html_draft_render_bound,
    validate_short_draft_render_bound,
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


def _experiment_scope(target, attempt_id, runtime):
    return {"account_id": target.content_account_id, "appid": runtime.appid,
            "candidate_id": target.content_asset_id, "candidate_hash": target.approved_candidate_hash,
            "target_id": target.id, "attempt_id": attempt_id, "runtime_fingerprint": runtime.fingerprint,
            "actor": target.authorized_by, "action": target.action, "channel": target.channel,
            "content_form": target.content_form}


def _validate_experiment_request(authority, target, runtime, user):
    fields = {"account_id", "appid", "candidate_id", "candidate_hash", "actor", "expires_at"}
    if (not isinstance(authority, dict) or set(authority) not in (fields, fields | {"mode"}) or target.id is not None
            or authority.get("mode", "short") not in {"short", "html"}
            or user.role != "admin" or authority["actor"] != user.email
            or type(authority["account_id"]) is not int or type(authority["candidate_id"]) is not int
            or authority["account_id"] != runtime.account_id or authority["appid"] != runtime.appid
            or authority["candidate_id"] != target.content_asset_id
            or authority["candidate_hash"] != target.approved_candidate_hash
            or type(authority["expires_at"]) is not int
            or not int(time.time()) < authority["expires_at"] <= int(time.time()) + 900):
        raise HTTPException(403, "official_experiment_scope_invalid")


def validate_target(db, target, user, *, _short_draft_request=None):
    from .content_identity import _lock_account
    from .content_masters import owned_unit
    from .production_validation import validate_live_v5_candidate

    if (target.publisher_key != wechat_official.KEY or target.publisher_version != "1"
            or target.channel != "wechat" or target.content_form != "article" or target.action != "auto_draft"
            or type(target.content_account_id) is not int):
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
    if registration is None:
        raise HTTPException(409, "official_publisher_unverified")
    if target.approved_candidate_hash != asset.candidate_hash:
        raise HTTPException(409, "official_candidate_changed")
    if not isinstance(manifest.get("official_render"), dict):
        raise HTTPException(409, "official_render_required")
    render = manifest["official_render"]
    if render.get("renderer_version") not in {"2", "3"} or render.get("status") != "local_ready":
        raise HTTPException(409, "official_asset_filename_required")
    from .wechat_official_render import upload_asset_metadata

    for slot in render["asset_slots"]:
        revision = db.get(MaterialRevision, slot["material_revision_id"], populate_existing=True)
        if revision is None or upload_asset_metadata(revision) != {"filename": slot["filename"], "mime_type": slot["mime_type"]}:
            raise HTTPException(409, "official_asset_metadata_changed")
    try:
        validate_article_render(manifest["official_render"], manifest["content"], manifest["assets"], manifest["evidence_refs"])
    except ValueError:
        raise HTTPException(409, "official_render_invalid") from None
    if manifest["official_render"]["status"] != "local_ready":
        raise HTTPException(409, "official_render_unavailable")
    runtime = wechat_official.resolve_runtime(db, account.id)
    snapshot = target.capability_snapshot_json or {}
    proofs = [snapshot[key] for key in ("short_draft_authority", "html_draft_authority") if key in snapshot]
    if len(proofs) > 1:
        raise HTTPException(403, "official_experiment_scope_invalid")
    experimental = _short_draft_request is not None or bool(proofs)
    if experimental:
        actor = db.get(User, user.id, populate_existing=True)
        if actor is None or actor.is_active is not True or actor.role != "admin":
            raise HTTPException(403, "official_experiment_scope_invalid")
        if (registration.status != "configured"
                or registration.config_fingerprint != wechat_official.implementation_fingerprint()
                or not isinstance(registry.resolve("publisher", wechat_official.KEY, "1"), wechat_official.OfficialWechatPublisher)):
            raise HTTPException(409, "official_publisher_unverified")
        scope = {"channel": target.channel, "content_form": target.content_form, "action": target.action,
                 "content_account_id": target.content_account_id, "account_ref": target.account_ref,
                 "publisher_key": target.publisher_key, "publisher_version": target.publisher_version}
        events = db.scalars(select(CapabilityVerification).where(
            CapabilityVerification.registration_id == registration.id,
            CapabilityVerification.scope_kind == "publisher_action").order_by(CapabilityVerification.id.desc())).all()
        latest = next((event for event in events if event.scope_json == scope), None)
        if latest is not None and latest.result != "verified":
            raise HTTPException(409, "official_publisher_unverified")
        if _short_draft_request is not None:
            _validate_experiment_request(_short_draft_request, target, runtime, user)
        else:
            attempt = db.scalar(select(DeliveryAttempt).where(DeliveryAttempt.target_id == target.id)
                                .order_by(DeliveryAttempt.attempt_no.desc()).limit(1))
            if (attempt is None or not wechat_official.check_draft_authority(
                    proofs[0], _experiment_scope(target, attempt.id, runtime))):
                raise HTTPException(403, "official_experiment_scope_invalid")
        try:
            mode = _short_draft_request.get("mode", "short") if _short_draft_request is not None else (
                "html" if proofs[0]["schema"] == "wechat.html-draft.authority.v1" else "short")
            validator = validate_html_draft_render_bound if mode == "html" else validate_short_draft_render_bound
            validator(manifest["official_render"])
        except ValueError:
            raise HTTPException(422, "official_experiment_body_limit") from None
    elif not wechat_official.remote_contract_ready() or not publisher_target_verified(db, target, registry):
        raise HTTPException(409, "official_publisher_unverified")
    return manifest, runtime


def prepare_short_draft_experiment(db, asset, payload, user, *, authority):
    """Internal explicit operator authority; never inferred from a normal HTTP request."""
    from .delivery import authorize_target

    bootstrap_publishers()
    try:
        target = authorize_target(db, asset, payload, user, _short_draft_request=authority)
        last = db.scalar(select(DeliveryAttempt.id).where(DeliveryAttempt.target_id == target.id).limit(1))
        if last is not None or target.status != "target_authorized":
            raise HTTPException(409, "official_execution_claimed")
        runtime = wechat_official.resolve_runtime(db, target.content_account_id)
        claim = secrets.token_hex(32)
        render = asset.candidate_manifest_json["official_render"]
        metadata = {"schema": "wechat.official.execution.v1", "claim_hash": _hash(claim),
                    "runtime_fingerprint": runtime.fingerprint, "candidate_hash": target.approved_candidate_hash,
                    "render_hash": render["render_hash"], "resource_mapping": [], "completed_steps": [], "in_flight": None}
        attempt = DeliveryAttempt(target_id=target.id, attempt_no=1,
            idempotency_key=_hash([target.id, target.approved_candidate_hash, 1]),
            publisher_key=target.publisher_key, publisher_version=target.publisher_version,
            request_hash=_hash([target.approved_candidate_hash, metadata["render_hash"], runtime.fingerprint]),
            status="prepared", started_at=utcnow(), response_metadata_json=metadata)
        db.add(attempt)
        db.flush()
        html_mode = authority.get("mode", "short") == "html"
        signer = wechat_official.sign_html_draft_authority if html_mode else wechat_official.sign_short_draft_authority
        proof = signer(_experiment_scope(target, attempt.id, runtime),
                                                          expires_at=authority["expires_at"])
        target.capability_snapshot_json = {**target.capability_snapshot_json, "html_draft_authority" if html_mode else "short_draft_authority": proof}
        db.flush()
        validate_target(db, target, user)
        _event(db, target, attempt, "delivery.prepared")
        ids = target.id, attempt.id
        db.commit()
        return *ids, claim
    except (HTTPException, ValueError, IntegrityError, OperationalError) as exc:
        db.rollback()
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(409, "official_experiment_prepare_conflict") from None


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
        if any(key in (target.capability_snapshot_json or {}) for key in ("short_draft_authority", "html_draft_authority")):
            raise HTTPException(409, "official_execution_claimed")
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
    proof = (target.capability_snapshot_json or {}).get("html_draft_authority") or (target.capability_snapshot_json or {}).get("short_draft_authority")
    client = (wechat_official_transport.OfficialTransport(experiment_authority=proof,
              experiment_scope=_experiment_scope(target, attempt_id, runtime)) if proof is not None
              else wechat_official_transport.OfficialTransport())
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
                method = client.upload_cover if slot["usage"] == "cover" else client.upload_inline
                return {**slot, "account_id": current_runtime.account_id, "appid": current_runtime.appid,
                        "runtime_fingerprint": current_runtime.fingerprint,
                        "remote_ref": method(token, data, slot["mime_type"], slot["filename"])}

            _step(db, target_id, attempt_id, claim, user, f"asset_{index}", upload,
                  lambda attempt, metadata, value: metadata["resource_mapping"].append(value))
        _step(db, target_id, attempt_id, claim, user, "create",
              lambda manifest, runtime, metadata: client.create_draft(token, prepare_article(manifest, runtime, metadata["resource_mapping"])),
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
    proof = (target.capability_snapshot_json or {}).get("html_draft_authority") or (target.capability_snapshot_json or {}).get("short_draft_authority")
    client = (wechat_official_transport.OfficialTransport(experiment_authority=proof,
              experiment_scope=_experiment_scope(target, attempt_id, runtime)) if proof is not None
              else wechat_official_transport.OfficialTransport())
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
