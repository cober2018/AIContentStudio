"""Scoped capability verification; a registry row never authorizes an effect by itself."""

from __future__ import annotations

import hashlib
import json
import marshal
import os
import re
import sys
import types
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..models import (
    CapabilityRegistration,
    CapabilityVerification,
    ConnectorEndpoint,
    ContentAccount,
    DeliveryAttempt,
    DeliveryReceipt,
    DeliveryTarget,
)
from .content_harness.registry import PluginRegistry, RegistryError

_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_SAFE_ID = re.compile(r"[A-Za-z0-9_.:@-]{1,150}\Z")
_PUBLISHER_SCOPE = frozenset({
    "channel", "content_form", "action", "content_account_id", "account_ref",
    "publisher_key", "publisher_version",
})
_DATA_SOURCE_SCOPE = frozenset({"plugin_key", "registration_key", "registration_version", "endpoint_id"})
_RENDERER_SCOPE = frozenset({"renderer_key", "renderer_version", "modality", "payload_schema", "channel", "content_form", "output_mime"})
_EVIDENCE_KEYS = frozenset({"kind", "reference_hash", "reason_code", "input_hash", "output_hash"})
_SENSITIVE_KEY = re.compile(r"(?:secret|token|password|authorization|cookie|signature|api[_-]?key)", re.IGNORECASE)
_BOUNDED_WECHAT_DRAFT_REASON = "account_bound_draft_confirmed"


def is_bounded_official_draft_scope(scope: dict) -> bool:
    return (
        isinstance(scope, dict)
        and scope.get("publisher_key") == "publisher.wechat.official"
        and scope.get("publisher_version") == "1"
        and scope.get("channel") == "wechat"
        and scope.get("content_form") == "article"
        and scope.get("action") == "auto_draft"
    )


def _contains_sensitive_key(value: object) -> bool:
    if isinstance(value, dict):
        return any(_SENSITIVE_KEY.search(str(key)) or _contains_sensitive_key(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_sensitive_key(item) for item in value)
    return False


def endpoint_config_fingerprint(endpoint: ConnectorEndpoint) -> str | None:
    connector = endpoint.connector
    if connector is None or not connector.is_active or connector.connector_type != "generic_rest":
        return None
    parsed = urlsplit(connector.base_url or "")
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        return None
    if not endpoint.path or "?" in endpoint.path or "#" in endpoint.path or endpoint.method != "GET":
        return None
    if connector.auth_style == "none":
        credential_version = "none"
    elif connector.auth_style in {"bearer", "header"} and connector.api_key_env and re.fullmatch(r"[A-Z_][A-Z0-9_]{0,99}", connector.api_key_env):
        credential_version = os.getenv(f"{connector.api_key_env}_VERSION")
        if not os.getenv(connector.api_key_env) or not credential_version or not _SAFE_ID.fullmatch(credential_version):
            return None
    else:
        return None
    headers = connector.default_headers_json or {}
    if not isinstance(headers, dict) or any(
        key.lower() not in {"accept", "content-type", "user-agent"}
        or not isinstance(value, str) or len(value) > 200 or "\n" in value or "\r" in value
        for key, value in headers.items()
    ):
        return None
    config_parts = (endpoint.params_json, endpoint.body_template_json, endpoint.fact_mapping_json, endpoint.pagination_json)
    if any(_contains_sensitive_key(part) for part in config_parts):
        return None
    pagination = endpoint.pagination_json or {}
    if not isinstance(pagination, dict):
        return None
    max_pages = pagination.get("max_pages", 20)
    page_size = pagination.get("page_size", 500)
    if type(max_pages) is not int or not 1 <= max_pages <= 20 or type(page_size) is not int or not 1 <= page_size <= 500:
        return None
    if any(len(json.dumps(part, ensure_ascii=False, default=str).encode()) > 16_384 for part in config_parts):
        return None
    identity = {
        "executor": data_connector_implementation_fingerprint(),
        "connector_id": connector.id,
        "endpoint_id": endpoint.id,
        "base_url": connector.base_url,
        "auth_style": connector.auth_style,
        "auth_header_name": connector.auth_header_name,
        "api_key_env": connector.api_key_env,
        "credential_version": credential_version,
        "headers": headers,
        "path": endpoint.path,
        "method": endpoint.method,
        "params": endpoint.params_json,
        "body_template": endpoint.body_template_json,
        "fact_mapping": endpoint.fact_mapping_json,
        "pagination": endpoint.pagination_json,
        "title_template": endpoint.title_template,
        "as_of_path": endpoint.as_of_path,
        "trust_level": endpoint.trust_level,
    }
    return hashlib.sha256(json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def data_connector_implementation_fingerprint() -> str:
    from . import connector_service, url_fetch

    parts = [str(sys.version_info[:3]).encode()]
    for module in (connector_service, url_fetch):
        # Source bytes bind policy constants; loaded callables also detect in-process replacement.
        parts.extend((module.__name__.encode(), Path(module.__file__).read_bytes()))
        for name, value in sorted(vars(module).items()):
            if isinstance(value, types.FunctionType) and (value.__module__ == module.__name__ or name == "bounded_safe_fetch"):
                parts.extend((name.encode(), marshal.dumps(value.__code__, 2)))
            elif isinstance(value, type) and value.__module__ == module.__name__:
                for method_name, method in sorted(vars(value).items()):
                    if isinstance(method, types.FunctionType):
                        parts.extend((method_name.encode(), marshal.dumps(method.__code__, 2)))
    return hashlib.sha256(b"".join(parts)).hexdigest()


def _scope(scope_kind: str, scope: dict) -> dict:
    expected = {"publisher_action": _PUBLISHER_SCOPE, "data_source_endpoint": _DATA_SOURCE_SCOPE,
                "renderer_output": _RENDERER_SCOPE}.get(scope_kind)
    if not isinstance(scope, dict) or expected is None or set(scope) != expected:
        raise ValueError("capability_scope_invalid")
    int_key = {"publisher_action": "content_account_id", "data_source_endpoint": "endpoint_id"}.get(scope_kind)
    if int_key is not None and (type(scope[int_key]) is not int or scope[int_key] < 1):
        raise ValueError("capability_scope_invalid")
    for key, value in scope.items():
        if key == int_key:
            continue
        valid = isinstance(value, str) and (value in {"text/markdown", "image/png", "image/jpeg", "image/webp", "video/mp4"} if key == "output_mime" else _SAFE_ID.fullmatch(value))
        if not valid:
            raise ValueError("capability_scope_invalid")
    return {key: scope[key] for key in sorted(scope)}


def _evidence(result: str, evidence: dict) -> dict:
    if result not in {"verified", "failed", "revoked"} or not isinstance(evidence, dict):
        raise ValueError("capability_evidence_invalid")
    if set(evidence) - _EVIDENCE_KEYS:
        raise ValueError("capability_evidence_invalid")
    kind = evidence.get("kind")
    if result == "verified":
        if kind not in {"human_readback", "platform_readback", "render_readback"} or not _HEX64.fullmatch(str(evidence.get("reference_hash", ""))):
            raise ValueError("capability_evidence_invalid")
    elif kind not in {"revocation", "probe_failure"}:
        raise ValueError("capability_evidence_invalid")
    if "reason_code" in evidence and not _SAFE_ID.fullmatch(str(evidence["reason_code"])):
        raise ValueError("capability_evidence_invalid")
    if any(not _HEX64.fullmatch(str(evidence[key])) for key in ("input_hash", "output_hash") if key in evidence):
        raise ValueError("capability_evidence_invalid")
    if kind == "render_readback" and not {"input_hash", "output_hash"}.issubset(evidence):
        raise ValueError("capability_evidence_invalid")
    return {key: evidence[key] for key in sorted(evidence)}


def append_verification(
    db: Session,
    registration: CapabilityRegistration,
    *,
    scope_kind: str,
    scope: dict,
    result: str,
    actor: str,
    evidence: dict,
    expires_at: datetime | None = None,
    config_fingerprint: str | None = None,
    allow_bounded_official_draft: bool = False,
) -> CapabilityVerification:
    safe_scope = _scope(scope_kind, scope)
    safe_evidence = _evidence(result, evidence)
    if registration.id is None or not _HEX64.fullmatch(registration.config_fingerprint):
        raise ValueError("capability_registration_invalid")
    publisher_match = (scope_kind == "publisher_action" and registration.kind == "publisher"
                       and safe_scope["publisher_key"] == registration.key and safe_scope["publisher_version"] == registration.version)
    data_match = (scope_kind == "data_source_endpoint" and registration.kind == "data_connector"
                  and safe_scope["registration_key"] == registration.key
                  and safe_scope["registration_version"] == registration.version
                  and safe_scope["plugin_key"] == registration.data_source_plugin_key
                  and safe_scope["endpoint_id"] == registration.endpoint_id)
    renderer_match = (scope_kind == "renderer_output" and registration.kind == "renderer"
                      and safe_scope["renderer_key"] == registration.key and safe_scope["renderer_version"] == registration.version)
    if not (publisher_match or data_match or renderer_match):
        raise ValueError("capability_scope_registration_mismatch")
    official_match = publisher_match and registration.key == "publisher.wechat.official" and registration.version == "1"
    if config_fingerprint is not None and (not renderer_match or not _HEX64.fullmatch(config_fingerprint)):
        raise ValueError("capability_registration_invalid")
    if official_match:
        from . import wechat_official

        # Serialize official verification changes with each bounded dispatch decision.
        db.execute(update(CapabilityRegistration).where(CapabilityRegistration.id == registration.id)
                   .values(status=CapabilityRegistration.status).execution_options(synchronize_session=False))
        db.refresh(registration)

        if result == "verified" and registration.config_fingerprint != wechat_official.implementation_fingerprint():
            raise ValueError("capability_registration_invalid")
        bounded_experiment = (
            allow_bounded_official_draft
            and is_bounded_official_draft_scope(safe_scope)
            and safe_evidence.get("reason_code") == _BOUNDED_WECHAT_DRAFT_REASON
        )
        if result == "verified" and not wechat_official.remote_contract_ready() and not bounded_experiment:
            raise ValueError("official_contract_unresolved")
        if result == "verified":
            account_fingerprint = wechat_official.scope_fingerprint(db, safe_scope)
            if account_fingerprint is None:
                raise ValueError("capability_scope_registration_mismatch")
        else:
            account = db.get(ContentAccount, safe_scope["content_account_id"], populate_existing=True)
            if account is None or account.platform_channel != "wechat" or account.platform_account_id != safe_scope["account_ref"]:
                raise ValueError("capability_scope_registration_mismatch")
            prior = db.scalars(select(CapabilityVerification).where(CapabilityVerification.registration_id == registration.id,
                              CapabilityVerification.scope_kind == scope_kind).order_by(CapabilityVerification.id.desc())).all()
            latest = next((event for event in prior if event.scope_json == safe_scope), None)
            account_fingerprint = latest.config_fingerprint if latest else registration.config_fingerprint
    else:
        account_fingerprint = None
    if result == "verified" and (renderer_match != (safe_evidence.get("kind") == "render_readback")):
        raise ValueError("capability_evidence_invalid")
    if not actor or len(actor) > 255:
        raise ValueError("capability_actor_invalid")
    now = datetime.now(UTC)
    expiry = expires_at or (now + timedelta(days=1) if result == "verified" else None)
    if result == "verified" and (expiry is None or expiry <= now):
        raise ValueError("capability_expiry_invalid")
    row = CapabilityVerification(
        registration_id=registration.id,
        config_fingerprint=account_fingerprint or config_fingerprint or registration.config_fingerprint,
        scope_kind=scope_kind,
        scope_json=safe_scope,
        result=result,
        verified_by=actor,
        verified_at=now,
        expires_at=expiry,
        evidence_json=safe_evidence,
    )
    db.add(row)
    db.flush()
    return row


def is_verified_for_scope(
    db: Session,
    registration: CapabilityRegistration,
    scope: dict,
    actual_config_fingerprint: str,
    loaded_registry: PluginRegistry,
    *,
    now: datetime | None = None,
) -> bool:
    if registration.id is None or registration.status != "configured":
        return False
    official_match = registration.kind == "publisher" and registration.key == "publisher.wechat.official" and registration.version == "1"
    if not _HEX64.fullmatch(actual_config_fingerprint) or (registration.kind != "renderer" and not official_match and registration.config_fingerprint != actual_config_fingerprint):
        return False
    scope_kind = {"publisher": "publisher_action", "data_connector": "data_source_endpoint", "renderer": "renderer_output"}.get(registration.kind)
    if scope_kind is None:
        return False
    try:
        wanted_scope = _scope(scope_kind, scope)
        implementation = loaded_registry.resolve(registration.kind, registration.key, registration.version)
    except (ValueError, RegistryError):
        return False
    if scope_kind == "publisher_action" and (wanted_scope["publisher_key"] != registration.key or wanted_scope["publisher_version"] != registration.version):
        return False
    latest = None
    if official_match:
        from . import wechat_official

        if (not isinstance(implementation, wechat_official.OfficialWechatPublisher)
                or registration.config_fingerprint != wechat_official.implementation_fingerprint()
                or actual_config_fingerprint != wechat_official.scope_fingerprint(db, wanted_scope)):
            return False
        events = db.scalars(select(CapabilityVerification).where(
            CapabilityVerification.registration_id == registration.id,
            CapabilityVerification.scope_kind == scope_kind,
        ).order_by(CapabilityVerification.id.desc())).all()
        latest = next((event for event in events if event.scope_json == wanted_scope), None)
        if not wechat_official.remote_contract_ready() and not (
            latest is not None and latest.evidence_json.get("reason_code") == _BOUNDED_WECHAT_DRAFT_REASON
        ):
            return False
    if scope_kind == "data_source_endpoint" and (
        wanted_scope["registration_key"] != registration.key
        or wanted_scope["registration_version"] != registration.version
        or wanted_scope["plugin_key"] != registration.data_source_plugin_key
        or wanted_scope["endpoint_id"] != registration.endpoint_id
    ):
        return False
    if scope_kind == "renderer_output" and (
        wanted_scope["renderer_key"] != registration.key or wanted_scope["renderer_version"] != registration.version
    ):
        return False
    if scope_kind == "renderer_output":
        from .renderer_capabilities import ProductionRenderer, implementation_fingerprint, runtime_fingerprint

        if isinstance(implementation, ProductionRenderer):
            if (implementation.mode != "deterministic" or not implementation.supports_scope(wanted_scope)
                    or registration.config_fingerprint != implementation_fingerprint(implementation)
                    or actual_config_fingerprint != runtime_fingerprint(db, implementation, wanted_scope)):
                return False
        else:
            from .media_renderers import resolve_renderer, scope_fingerprint

            try:
                media, fingerprint = resolve_renderer(registration.key, registration.version)
            except HTTPException:
                return False
            if (media is not implementation or registration.config_fingerprint != fingerprint
                    or actual_config_fingerprint != scope_fingerprint(db, media, wanted_scope)):
                return False
    if latest is None:
        events = db.scalars(select(CapabilityVerification).where(
            CapabilityVerification.registration_id == registration.id,
            CapabilityVerification.scope_kind == scope_kind,
        ).order_by(CapabilityVerification.id.desc())).all()
        latest = next((event for event in events if event.scope_json == wanted_scope), None)
    if latest is None or latest.result != "verified" or latest.config_fingerprint != actual_config_fingerprint:
        return False
    at = now or datetime.now(UTC)
    expiry = latest.expires_at
    if expiry is None:
        return False
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=UTC)
    return at < expiry


def publisher_runtime_fingerprint(key: str, version: str) -> str | None:
    """Installed CLI cannot prove account binding or immutable approved-content upload.

    Its global account config and Markdown converter are outside the frozen contract;
    operator version labels must never turn that runtime into a verified Publisher.
    """
    return None


def publisher_target_verified(db: Session, target: DeliveryTarget, loaded_registry: PluginRegistry) -> bool:
    official = target.publisher_key == "publisher.wechat.official" and target.publisher_version == "1"
    if target.action != "auto_draft" or target.publisher_key != "publisher.wechat.wewrite" and not official:
        return False
    if target.content_account_id is None or not target.account_ref:
        return False
    account = db.get(ContentAccount, target.content_account_id)
    if account is None or account.status != "active":
        return False
    registration = db.scalar(select(CapabilityRegistration).where(
        CapabilityRegistration.kind == "publisher",
        CapabilityRegistration.key == target.publisher_key,
        CapabilityRegistration.version == target.publisher_version,
    ))
    if registration is None or registration.endpoint_id is not None:
        return False
    scope = {
        "channel": target.channel,
        "content_form": target.content_form,
        "action": target.action,
        "content_account_id": account.id,
        "account_ref": target.account_ref,
        "publisher_key": target.publisher_key,
        "publisher_version": target.publisher_version,
    }
    if official:
        from . import wechat_official

        fingerprint = wechat_official.scope_fingerprint(db, scope)
    else:
        fingerprint = publisher_runtime_fingerprint(target.publisher_key, target.publisher_version)
    if fingerprint is None:
        return False
    return is_verified_for_scope(db, registration, scope, fingerprint, loaded_registry)


def promote_confirmed_official_draft(
    db: Session,
    target: DeliveryTarget,
    receipt: DeliveryReceipt,
    actor: str,
) -> CapabilityVerification | None:
    """Promote one confirmed official draft into the exact capability ledger."""
    if not (
        receipt.status == "human_confirmed"
        and target.publisher_key == "publisher.wechat.official"
        and target.publisher_version == "1"
        and target.action == "auto_draft"
    ):
        return None
    if target.channel != "wechat" or target.content_form != "article" or target.content_account_id is None:
        raise ValueError("official_draft_capability_scope_invalid")
    attempt = db.scalars(
        select(DeliveryAttempt)
        .where(DeliveryAttempt.target_id == target.id, DeliveryAttempt.status == "succeeded")
        .order_by(DeliveryAttempt.id.desc())
    ).first()
    if attempt is None or not isinstance(attempt.remote_id, str) or not attempt.remote_id.strip():
        raise ValueError("official_draft_capability_requires_media_id")
    if attempt.publisher_key not in {None, target.publisher_key} or attempt.publisher_version not in {None, target.publisher_version}:
        raise ValueError("official_draft_capability_publisher_mismatch")
    account = db.get(ContentAccount, target.content_account_id, populate_existing=True)
    if account is None or account.status != "active" or account.platform_channel != "wechat" or account.platform_account_id != target.account_ref:
        raise ValueError("official_draft_capability_account_mismatch")
    scope = {
        "channel": target.channel,
        "content_form": target.content_form,
        "action": target.action,
        "content_account_id": account.id,
        "account_ref": target.account_ref,
        "publisher_key": target.publisher_key,
        "publisher_version": target.publisher_version,
    }
    registration = db.scalar(select(CapabilityRegistration).where(
        CapabilityRegistration.kind == "publisher",
        CapabilityRegistration.key == target.publisher_key,
        CapabilityRegistration.version == target.publisher_version,
    ))
    if registration is None or registration.status != "configured" or registration.endpoint_id is not None:
        raise ValueError("official_draft_capability_registration_unavailable")
    from . import wechat_official

    runtime_fingerprint = wechat_official.scope_fingerprint(db, scope)
    metadata = attempt.response_metadata_json
    if (runtime_fingerprint is None or registration.config_fingerprint != wechat_official.implementation_fingerprint()
            or not isinstance(metadata, dict) or metadata.get("runtime_fingerprint") != runtime_fingerprint):
        raise ValueError("official_draft_capability_runtime_changed")
    remote_hash = hashlib.sha256(attempt.remote_id.encode("utf-8")).hexdigest()
    input_hash = attempt.request_hash if _HEX64.fullmatch(attempt.request_hash or "") else None
    reference_hash = hashlib.sha256(json.dumps({
        "target_id": target.id,
        "attempt_id": attempt.id,
        "receipt_id": receipt.id,
        "candidate_hash": target.approved_candidate_hash,
        "remote_id_hash": remote_hash,
    }, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    events = db.scalars(select(CapabilityVerification).where(
        CapabilityVerification.registration_id == registration.id,
        CapabilityVerification.scope_kind == "publisher_action",
    ).order_by(CapabilityVerification.id.desc())).all()
    existing = next((event for event in events
                     if event.scope_json == _scope("publisher_action", scope)
                     and event.result == "verified"
                     and event.config_fingerprint == runtime_fingerprint
                     and (event.evidence_json or {}).get("reference_hash") == reference_hash), None)
    if existing is not None:
        return existing
    evidence = {
        "kind": "human_readback",
        "reason_code": _BOUNDED_WECHAT_DRAFT_REASON,
        "reference_hash": reference_hash,
        "output_hash": remote_hash,
    }
    if input_hash is not None:
        evidence["input_hash"] = input_hash
    return append_verification(
        db,
        registration,
        scope_kind="publisher_action",
        scope=scope,
        result="verified",
        actor=actor,
        evidence=evidence,
        allow_bounded_official_draft=True,
    )
