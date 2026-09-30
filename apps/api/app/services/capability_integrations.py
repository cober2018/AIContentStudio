"""Scoped capability verification; a registry row never authorizes an effect by itself."""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import UTC, datetime, timedelta
from urllib.parse import urlsplit

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import CapabilityRegistration, CapabilityVerification, ConnectorEndpoint, ContentAccount, DeliveryTarget
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
    if config_fingerprint is not None and (not renderer_match or not _HEX64.fullmatch(config_fingerprint)):
        raise ValueError("capability_registration_invalid")
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
        config_fingerprint=config_fingerprint or registration.config_fingerprint,
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
    if not _HEX64.fullmatch(actual_config_fingerprint) or (registration.kind != "renderer" and registration.config_fingerprint != actual_config_fingerprint):
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
    if scope_kind == "data_source_endpoint" and (
        wanted_scope["registration_key"] != registration.key
        or wanted_scope["registration_version"] != registration.version
        or wanted_scope["plugin_key"] != registration.data_source_plugin_key
        or wanted_scope["endpoint_id"] != registration.endpoint_id
    ):
        return False
    if scope_kind == "renderer_output" and (
        wanted_scope["renderer_key"] != registration.key or wanted_scope["renderer_version"] != registration.version
        or getattr(implementation, "mode", None) != "deterministic"
        or not callable(getattr(implementation, "supports_scope", None)) or not implementation.supports_scope(wanted_scope)
    ):
        return False
    if scope_kind == "renderer_output":
        from .renderer_capabilities import implementation_fingerprint, runtime_fingerprint

        if (registration.config_fingerprint != implementation_fingerprint(implementation)
                or actual_config_fingerprint != runtime_fingerprint(db, implementation, wanted_scope)):
            return False
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
    if target.action != "auto_draft" or target.publisher_key != "publisher.wechat.wewrite":
        return False
    if target.content_account_id is None or not target.account_ref:
        return False
    account = db.get(ContentAccount, target.content_account_id)
    if account is None or account.status != "active":
        return False
    fingerprint = publisher_runtime_fingerprint(target.publisher_key, target.publisher_version)
    if fingerprint is None:
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
    return is_verified_for_scope(db, registration, scope, fingerprint, loaded_registry)
