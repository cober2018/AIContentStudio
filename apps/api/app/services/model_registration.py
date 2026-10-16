"""Provider registration over the existing configuration head; no inference on save."""

import copy
import hashlib
import ipaddress
import json
import math
import re
import socket
import time
from urllib.parse import urlsplit

import httpx
from fastapi import HTTPException
from pydantic import Field, StrictBool, ValidationError

from .. import runtime_config
from .model_capability_routing import Identifier, StrictModel, _stored, commit_configuration
from .system_settings import mask_secret
from .url_fetch import (
    OUTBOUND_HTTP_POLICIES,
    UnsafeUrlError,
    _PinnedBackend,
    enforce_outbound_host,
    outbound_scope,
    resolve_addresses,
)

PURPOSES = ("generate", "rewrite", "fact_check", "topic_discovery", "discoverability", "platform_adaptation", "text_master_edit", "form_autofill", "field_polish")
PROVIDER_REQUEST_MAX_TIMEOUT_SECONDS = OUTBOUND_HTTP_POLICIES["model_generation"].timeout_seconds


class ProviderInput(StrictModel):
    name: str = Field(min_length=1, max_length=100)
    base_url: str = Field(max_length=500)
    api_key: str = Field(default="", max_length=4096, repr=False)
    clear_key: StrictBool = False
    enabled: StrictBool = True
    trusted_private_endpoint: str = Field(default="", max_length=500)


class RegisteredModelInput(StrictModel):
    provider_id: Identifier
    model_id: str = Field(pattern=r"^[A-Za-z0-9_./:-]{1,160}$")


class RegistrationInput(StrictModel):
    expected_revision: int = Field(strict=True, ge=0)
    providers: dict[Identifier, ProviderInput] = Field(default_factory=dict, max_length=100)
    models: list[RegisteredModelInput] = Field(default_factory=list, max_length=100)
    default_profile: str = Field(default="", max_length=100)
    routes: dict[str, str] = Field(default_factory=dict, max_length=9)


def endpoint(value):
    try:
        parsed = urlsplit(value)
        if (parsed.scheme not in {"https", "http"} or not parsed.hostname or parsed.username is not None
                or parsed.password is not None or parsed.query or parsed.fragment or "\\" in value
                or any(ord(c) <= 32 for c in value) or "%" in parsed.path
                or re.search(r"token|secret|password|api[-_]?key|sk-|\.\.", parsed.path, re.IGNORECASE)
                or parsed.port == 0):
            raise ValueError()
        return value.rstrip("/")
    except ValueError as exc:
        raise HTTPException(422, "provider_endpoint_invalid") from exc


def trusted_literal_address(host):
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        return None
    if literal.version == 4 and (host == "127.0.0.1" or any(
            literal in ipaddress.ip_network(net) for net in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"))):
        return str(literal)
    return None


def target(provider):
    base = endpoint(provider["base_url"])
    try:
        enforce_outbound_host(base)
    except UnsafeUrlError:
        raise HTTPException(422, "provider_target_forbidden") from None
    parsed = urlsplit(base)
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    address = trusted_literal_address(parsed.hostname)
    if address is not None and provider.get("trusted_private_endpoint") == base:
        return base, parsed, port, address
    if parsed.scheme != "https":
        raise HTTPException(422, "trusted_private_endpoint_required")
    try:
        addresses = resolve_addresses(parsed.hostname, port)
        if not addresses or any(info[0] not in {socket.AF_INET, socket.AF_INET6}
                                or not ipaddress.ip_address(info[4][0]).is_global
                                or ipaddress.ip_address(info[4][0]).is_multicast for info in addresses):
            raise ValueError()
        return base, parsed, port, addresses[0][4][0]
    except (OSError, ValueError) as exc:
        raise HTTPException(422, "provider_target_unavailable") from exc


def provider_request(provider, path, *, payload=None, timeout=10, image_input=False):
    """Pin validated TCP target while retaining TLS hostname and suppress raw diagnostics."""
    native_image = re.fullmatch(r"/v1beta/models/([A-Za-z0-9_.~-]|%[0-9A-F]{2}){1,480}:generateContent", path) is not None
    if path not in {"/models", "/chat/completions", "/images/generations"} and not native_image:
        raise HTTPException(422, "provider_operation_invalid")
    if not provider.get("enabled", True) or not provider.get("api_key"):
        raise HTTPException(422, "provider_credential_unavailable")
    timeout_value = float(timeout)
    if not math.isfinite(timeout_value):
        timeout_value = PROVIDER_REQUEST_MAX_TIMEOUT_SECONDS
    policy = "model_discovery" if path == "/models" else "image" if path == "/images/generations" or native_image else "model_generation"
    if image_input:
        if path != "/chat/completions":
            raise HTTPException(422, "provider_image_operation_invalid")
        policy = "model_vision"
    limit = OUTBOUND_HTTP_POLICIES[policy]
    deadline = time.monotonic() + min(max(timeout_value, 0.1), limit.timeout_seconds)
    headers = {"Authorization": "Bearer " + provider["api_key"], "Accept-Encoding": "identity"}
    request_body = None
    if payload is not None:
        try:
            request_body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
        except (TypeError, ValueError, RecursionError) as exc:
            raise HTTPException(422, "provider_request_payload_invalid") from exc
        if len(request_body) > limit.request_bytes:
            raise HTTPException(413, "provider_request_limit")
        headers["Content-Type"] = "application/json"
    with outbound_scope(deadline):
        base, parsed, port, address = target(provider)
    if native_image:
        # The registered gateway's OpenAI /v1 prefix maps to its native sibling.
        # Validate/pin the original endpoint so private endpoint trust is unchanged.
        if parsed.path not in {"", "/v1"}:
            raise HTTPException(422, "provider_operation_invalid")
        base = parsed._replace(path="").geturl().rstrip("/")
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise HTTPException(504, "provider_timeout")
    transport = httpx.HTTPTransport(retries=0, trust_env=False)
    transport._pool._network_backend = _PinnedBackend(parsed.hostname, port, address, deadline)
    try:
        with (
            outbound_scope(deadline),
            httpx.Client(transport=transport, timeout=remaining, trust_env=False, follow_redirects=False) as client,
            client.stream("GET" if payload is None else "POST", base + path,
                          headers=headers, content=request_body) as response,
        ):
            if response.status_code != 200:
                reason = ("provider_authentication_rejected" if response.status_code in {401, 403}
                          else "provider_image_protocol_rejected" if response.status_code == 400 and (native_image or path == "/images/generations")
                          else "provider_request_rejected")
                raise HTTPException(502, reason)
            if response.headers.get("content-encoding", "identity").strip().lower() != "identity":
                raise HTTPException(502, "provider_response_encoding_invalid")
            data = bytearray()
            for chunk in response.iter_bytes():
                if len(data) + len(chunk) > limit.response_bytes or time.monotonic() >= deadline:
                    raise HTTPException(502, "provider_response_limit")
                data.extend(chunk)
            if time.monotonic() >= deadline:
                raise HTTPException(504, "provider_timeout")
            return json.loads(data)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, "provider_request_failed") from exc


def profile_id(provider_id, model_id):
    return "registered." + hashlib.sha256(f"{provider_id}\0{model_id}".encode()).hexdigest()[:24]


def configuration_view(db):
    stored = _stored(db)
    providers = {}
    for key, value in stored.get("providers", {}).items():
        providers[key] = {"name": value.get("name", key), "base_url": value.get("base_url", ""),
                          "enabled": value.get("enabled", False), "protocol": "openai_compatible",
                          "trusted_private_endpoint": value.get("trusted_private_endpoint", ""), "api_key": mask_secret(value.get("api_key"))}
    profiles = {key: {"provider_id": p.get("provider_id"), "model_id": p.get("model", ""),
                      "enabled": p.get("enabled", True), "chat": selectable(p, stored)}
                for key, p in stored.get("profiles", {}).items()}
    return {"revision": stored.get("revision", 0), "providers": providers, "profiles": profiles,
            "default_profile": stored.get("default_profile", ""),
            "routes": {key: stored.get("routes", {}).get(key, "") for key in PURPOSES}, "purposes": list(PURPOSES)}


def selectable(profile, stored):
    if not profile.get("enabled", True) or "chat" not in profile.get("declared_capabilities", ["chat"]):
        return False
    if profile.get("provider_id"):
        provider = stored.get("providers", {}).get(profile["provider_id"], {})
        return bool(profile.get("model") and provider.get("enabled") and provider.get("api_key"))
    if profile.get("provider") == "mock":
        return True
    return bool(profile.get("provider") == "openai_compatible" and profile.get("model") and profile.get("base_url") and profile.get("api_key"))


def save_configuration(db, raw, *, actor):
    try:
        value = RegistrationInput.model_validate(raw)
    except ValidationError as exc:
        raise HTTPException(422, "provider_registration_invalid") from exc
    with runtime_config.configuration_guard():
        stored = _stored(db)
        if stored.get("revision", 0) != value.expected_revision:
            raise HTTPException(409, "configuration_revision_conflict")
        merged = copy.deepcopy(stored)
        providers = merged.setdefault("providers", {})
        for key, config in value.providers.items():
            base = endpoint(config.base_url)
            private = endpoint(config.trusted_private_endpoint) if config.trusted_private_endpoint else ""
            if private and private != base:
                raise HTTPException(422, "trusted_endpoint_mismatch")
            # No discovery or DNS on save; execution validates and pins the actual target.
            parsed = urlsplit(base)
            if parsed.scheme == "http" and (trusted_literal_address(parsed.hostname) is None or private != base):
                raise HTTPException(422, "trusted_private_endpoint_required")
            credential = "" if config.clear_key else config.api_key or providers.get(key, {}).get("api_key", "")
            if any(ord(c) < 33 or ord(c) > 126 for c in credential):
                raise HTTPException(422, "provider_credential_invalid")
            providers[key] = {"name": config.name, "protocol": "openai_compatible", "base_url": base,
                              "api_key": credential, "enabled": config.enabled, "trusted_private_endpoint": private}
        profiles = merged.setdefault("profiles", {})
        for model in value.models:
            if model.provider_id not in providers:
                raise HTTPException(422, "provider_missing")
            key = profile_id(model.provider_id, model.model_id)
            profiles[key] = {**profiles.get(key, {}), "provider_id": model.provider_id, "model": model.model_id,
                             "provider": "openai_compatible", "enabled": profiles.get(key, {}).get("enabled", True),
                             "declared_capabilities": profiles.get(key, {}).get("declared_capabilities", ["chat"])}
        if set(value.routes) - set(PURPOSES):
            raise HTTPException(422, "model_purpose_invalid")
        for choice in [value.default_profile, *value.routes.values()]:
            if choice and (choice not in profiles or not selectable(profiles[choice], merged)):
                raise HTTPException(422, "model_selection_unavailable")
        merged["routes"] = {**merged.get("routes", {}), **value.routes}
        merged["default_profile"] = value.default_profile
        merged["schema_version"] = max(2, merged.get("schema_version", 1))
        merged["revision"] = value.expected_revision + 1
        commit_configuration(db, merged, expected_revision=value.expected_revision, actor=actor)
        return configuration_view(db)


def discover(db, provider_id):
    provider = _stored(db).get("providers", {}).get(provider_id)
    if provider is None:
        raise HTTPException(404, "provider_missing")
    body = provider_request(provider, "/models")
    items = body.get("data") if isinstance(body, dict) else None
    if not isinstance(items, list) or len(items) > 2000:
        raise HTTPException(502, "provider_model_list_invalid")
    ids = {item["id"] for item in items if isinstance(item, dict) and isinstance(item.get("id"), str)
           and re.fullmatch(r"[A-Za-z0-9_./:-]{1,160}", item["id"])}
    return {"models": sorted(ids), "verified_capabilities": False}
