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

PURPOSES = ("generate", "rewrite", "fact_check", "fact_review", "identity_review", "topic_discovery", "discoverability",
            "platform_adaptation", "text_master_edit", "form_autofill", "field_polish", "material_match")
SEARCH_VENDORS = ("minimax", "tavily")
COVER_SIZES = ("1344x768", "1024x1024", "768x1344")
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


class CoverImageUse(StrictModel):
    profile: str = Field(default="", max_length=100)
    size: str = Field(default="1344x768", max_length=20)


class UsesInput(StrictModel):
    cover_image: CoverImageUse = Field(default_factory=CoverImageUse)
    writing_cli: str = Field(default="", max_length=100)
    topic_search: str = Field(default="", max_length=20)
    shot_video: str = Field(default="mmx:MiniMax-H3", max_length=120)
    shot_video_resolution: str = Field(default="480p", pattern=r"^(480p|768p|1080p)$")
    shot_video_final_resolution: str = Field(default="480p", pattern=r"^(480p|768p|1080p)$")
    shot_image: str = Field(default="", max_length=120)


class RegistrationInput(StrictModel):
    expected_revision: int = Field(strict=True, ge=0)
    providers: dict[Identifier, ProviderInput] = Field(default_factory=dict, max_length=100)
    models: list[RegisteredModelInput] = Field(default_factory=list, max_length=100)
    default_profile: str = Field(default="", max_length=100)
    routes: dict[str, str] = Field(default_factory=dict, max_length=len(PURPOSES))
    uses: UsesInput | None = None


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
                raise HTTPException(502, reason, headers={"X-Provider-Status": str(response.status_code)})
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
                      "enabled": p.get("enabled", True), "chat": selectable(p, stored), "image": image_selectable(p, stored)}
                for key, p in stored.get("profiles", {}).items()}
    return {"revision": stored.get("revision", 0), "providers": providers, "profiles": profiles,
            "default_profile": stored.get("default_profile", ""),
            "routes": {key: stored.get("routes", {}).get(key, "") for key in PURPOSES}, "purposes": list(PURPOSES),
            "uses": uses(stored), "search_vendors": list(SEARCH_VENDORS), "cover_sizes": list(COVER_SIZES),
            "shot_video_models": shot_video_models(stored), "shot_image_models": shot_image_models(stored),
            "local_vendors": {"minimax": _minimax_view(stored)}}


def uses(stored=None) -> dict:
    stored = stored if stored is not None else (runtime_config.get_runtime(runtime_config.KEY_MODELS) or {})
    value = stored.get("uses") or {}
    cover = value.get("cover_image") or {}
    return {"cover_image": {"profile": cover.get("profile", ""), "size": cover.get("size", COVER_SIZES[0])},
            "writing_cli": value.get("writing_cli", ""), "topic_search": value.get("topic_search", ""),
            # Older saves named the MiniMax model alone; those were always the local CLI.
            "shot_video": {"MiniMax-H3": "mmx:MiniMax-H3", "MiniMax-Hailuo-2.3": "mmx:MiniMax-Hailuo-2.3"}.get(
                value.get("shot_video", "mmx:MiniMax-H3"), value.get("shot_video", "mmx:MiniMax-H3")),
            # Test runs stay at 480P to keep each paid clip cheap; raise it for the final cut.
            "shot_video_resolution": {"720p": "768p"}.get(value.get("shot_video_resolution", "480p"), value.get("shot_video_resolution", "480p")),
            "shot_video_final_resolution": value.get("shot_video_final_resolution", "480p"),
            "shot_image": value.get("shot_image") or _default_shot_image(stored)}


def vendor_of(profile, stored) -> dict | None:
    """Address + key for a profile's vendor; MiniMax comes from its card, the rest from 厂商与模型."""
    from . import minimax_cli_provider as minimax

    vendor = profile.get("provider_id") if isinstance(profile, dict) else None
    if vendor == minimax.VENDOR_ID:
        key = minimax.shared_key()
        return {"id": vendor, "base_url": minimax.chat_base_url(), "api_key": key, "enabled": bool(key)}
    provider = stored.get("providers", {}).get(vendor) if vendor else None
    return {"id": vendor, **provider} if provider else None


def _minimax_view(stored=None) -> dict:
    from .minimax_cli_provider import VENDOR_ID, vendor_status

    stored = stored if stored is not None else (runtime_config.get_runtime(runtime_config.KEY_MODELS) or {})
    profiles = stored.get("profiles", {})
    on_minimax = {key for key, p in profiles.items() if p.get("provider_id") == VENDOR_ID and p.get("enabled", True)}
    chosen = uses(stored)
    labels = []
    if stored.get("default_profile") in on_minimax or set(stored.get("routes", {}).values()) & on_minimax:
        labels.append("写作与对话")
    if chosen["cover_image"]["profile"] in on_minimax:
        labels.append("封面生图")
    if chosen["writing_cli"] in on_minimax:
        labels.append("写作工具")
    if chosen["topic_search"] == VENDOR_ID:
        labels.append("选题搜索")
    labels += ["配音", "语音转文字", "视频与素材生图"]
    return {**vendor_status(), "uses": labels}


def selectable(profile, stored):
    if not profile.get("enabled", True) or "chat" not in profile.get("declared_capabilities", ["chat"]):
        return False
    if profile.get("provider") == "mock" and not profile.get("provider_id"):
        return True
    vendor = vendor_of(profile, stored)
    return bool(profile.get("model") and vendor and vendor.get("enabled") and vendor.get("api_key"))


def image_selectable(profile, stored):
    if not profile.get("enabled", True) or "image_generation" not in profile.get("declared_capabilities", []):
        return False
    vendor = vendor_of(profile, stored)
    return bool(profile.get("model") and vendor and vendor.get("enabled") and vendor.get("api_key"))


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
        from .minimax_cli_provider import VENDOR_ID

        for model in value.models:
            if model.provider_id not in providers and model.provider_id != VENDOR_ID:
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
        if value.uses is not None:
            cover, writing, search = value.uses.cover_image, value.uses.writing_cli, value.uses.topic_search
            if cover.profile and (cover.profile not in profiles or not image_selectable(profiles[cover.profile], merged)):
                raise HTTPException(422, "model_selection_unavailable")
            if cover.size not in COVER_SIZES:
                raise HTTPException(422, "cover_image_size_invalid")
            if writing and (writing not in profiles or not selectable(profiles[writing], merged)):
                raise HTTPException(422, "model_selection_unavailable")
            if search and search not in SEARCH_VENDORS:
                raise HTTPException(422, "topic_search_vendor_invalid")
            if search == "tavily" and not providers.get("tavily", {}).get("api_key"):
                raise HTTPException(422, "topic_search_vendor_unavailable")
            if value.uses.shot_image and value.uses.shot_image not in {item["id"] for item in shot_image_models(merged)}:
                raise HTTPException(422, "shot_image_model_unavailable")
            if value.uses.shot_video and value.uses.shot_video not in {item["id"] for item in shot_video_models(merged)}:
                raise HTTPException(422, "shot_video_model_unavailable")
            merged["uses"] = value.uses.model_dump()
        merged["schema_version"] = max(2, merged.get("schema_version", 1))
        merged["revision"] = value.expected_revision + 1
        commit_configuration(db, merged, expected_revision=value.expected_revision, actor=actor)
        sync_cli_files()
        return configuration_view(db)


def discover(db, provider_id):
    from .minimax_cli_provider import CHAT_MODELS, VENDOR_ID

    if provider_id == VENDOR_ID:
        return {"models": list(CHAT_MODELS), "verified_capabilities": False}
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


MMX_VIDEO = {"mmx:MiniMax-H3": "MiniMax 本机命令行 · MiniMax-H3（首帧 + 尾帧、可选画幅、4–15 秒）",
             "mmx:MiniMax-Hailuo-2.3": "MiniMax 本机命令行 · MiniMax-Hailuo-2.3（只用首帧、固定 6 秒）"}


def shot_image_models(stored) -> list[dict]:
    """Shot-still choices: registered models bound to 生图 over the OpenAI-compatible protocol (v2 = Gemini native)."""
    providers, items = stored.get("providers") or {}, []
    for key, profile in (stored.get("profiles") or {}).items():
        binding = (profile.get("capability_bindings") or {}).get("image_generation") or {}
        vendor = providers.get(profile.get("provider_id")) or {}
        if binding.get("adapter_key") == "openai.compatible" and profile.get("enabled", True) and vendor.get("enabled") and vendor.get("api_key"):
            kind = "Gemini 原生" if binding.get("adapter_version") == "2" or "gemini" in str(binding.get("model_id") or "") else "改图接口"
            items.append({"id": key, "label": f"{vendor.get('name') or profile.get('provider_id')} · {binding.get('model_id') or profile.get('model')}（{kind}，带商品参考图）"})
    return items


def _default_shot_image(stored) -> str:
    # grok keeps the product closest to the reference in the 2026-10-29 test, so it is the default when registered.
    items = shot_image_models(stored)
    return next((item["id"] for item in items if "grok" in item["label"]), items[0]["id"] if items else "")


def shot_video_models(stored) -> list[dict]:
    """Image-to-video choices: the local MiniMax CLI plus every registered model bound to 生视频 over the OpenAI-compatible protocol."""
    items = [{"id": key, "label": label} for key, label in MMX_VIDEO.items()]
    providers = stored.get("providers") or {}
    for key, profile in (stored.get("profiles") or {}).items():
        binding = (profile.get("capability_bindings") or {}).get("video_generation") or {}
        vendor = providers.get(profile.get("provider_id")) or {}
        if binding.get("adapter_key") == "openai.compatible" and profile.get("enabled", True) and vendor.get("enabled") and vendor.get("api_key"):
            items.append({"id": key, "label": f"{vendor.get('name') or profile.get('provider_id')} · {binding.get('model_id') or profile.get('model')}（视频接口，首帧 + 尾帧）"})
    return items


def topic_search_vendor() -> str:
    return uses()["topic_search"]


def sync_cli_files() -> None:
    """Local CLIs (mmx, wewrite, dsh) read their own files; they are written from 厂商与模型 + 用途, never edited by hand."""
    import logging
    import os
    from pathlib import Path

    import yaml

    from . import minimax_cli_provider as minimax
    from .writing_pipeline import WEWRITE_HOME

    minimax.sync_cli_login()
    stored = runtime_config.get_runtime(runtime_config.KEY_MODELS) or {}
    profiles, chosen = stored.get("profiles", {}), uses(stored)
    try:
        cover = profiles.get(chosen["cover_image"]["profile"])
        vendor = vendor_of(cover, stored) if cover else None
        path = WEWRITE_HOME / "config.yaml"
        data = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}) if path.exists() else {}
        before = copy.deepcopy(data)
        if vendor and vendor.get("api_key"):
            data["image"] = {"providers": [{"provider": "minimax" if vendor["id"] == minimax.VENDOR_ID else "openai",
                                            "api_key": vendor["api_key"], "model": cover["model"], "base_url": vendor["base_url"]}]}
        else:
            data.pop("image", None)
        if data != before:
            minimax.write_private(path, yaml.safe_dump(data, allow_unicode=True, sort_keys=False))

        writing = profiles.get(chosen["writing_cli"])
        vendor = vendor_of(writing, stored) if writing else None
        if vendor and vendor.get("api_key"):
            home = Path.home() / ".dsh"
            env_name = "MINIMAX_API_KEY" if vendor["id"] == minimax.VENDOR_ID else f"AICS_{re.sub(r'[^A-Z0-9]', '_', vendor['id'].upper())}_API_KEY"
            settings_path = home / "settings.yaml"
            data = (yaml.safe_load(settings_path.read_text(encoding="utf-8")) or {}) if settings_path.exists() else {}
            before = copy.deepcopy(data)
            providers = data.setdefault("llm-pi-ai", {}).setdefault("providers", {})
            entry = providers.get(vendor["id"]) or {}
            models = [m for m in entry.get("models") or [] if isinstance(m, dict)]
            if writing["model"] not in {m.get("id") for m in models}:
                models.insert(0, {"id": writing["model"]})
            providers[vendor["id"]] = {**entry, "apiKeyEnv": env_name, "api": "openai-completions",
                                       "baseURL": vendor["base_url"], "models": models}
            data["agent-default-model"] = {"provider": vendor["id"], "model": writing["model"]}
            if data != before:
                minimax.write_private(settings_path, yaml.safe_dump(data, allow_unicode=True, sort_keys=False))
            env_path = home / "env.local"
            text = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
            line = f'export {env_name}="{vendor["api_key"]}"'
            pattern = rf"^export {env_name}=.*$"
            updated = (re.sub(pattern, lambda _: line, text, flags=re.MULTILINE) if re.search(pattern, text, flags=re.MULTILINE)
                       else text.rstrip("\n") + ("\n" if text else "") + line + "\n")
            if updated != text:
                minimax.write_private(env_path, updated)
                os.chmod(env_path, 0o600)
    except (OSError, ValueError, yaml.YAMLError):
        logging.getLogger(__name__).warning("model_cli_sync_failed")


def migrate_to_single_source(db) -> None:
    """One-time: old per-section model rows become vendor-linked profiles and 用途, then are deleted."""
    from sqlalchemy import select

    from ..models import SystemSetting
    from .minimax_cli_provider import VENDOR_ID

    stored = _stored(db)
    if stored.get("schema_version", 1) >= 3:
        return
    merged = copy.deepcopy(stored)
    profiles = merged.setdefault("profiles", {})
    chosen = uses(merged)

    def chat_profile(model):
        key = profile_id(VENDOR_ID, model)
        profiles.setdefault(key, {"provider_id": VENDOR_ID, "model": model, "provider": "openai_compatible",
                                  "enabled": True, "declared_capabilities": ["chat"]})
        return key

    for key, profile in profiles.items():
        bindings = profile.get("capability_bindings") or {}
        if not profile.get("provider_id") and any((b or {}).get("base_url") == "local://mmx" for b in bindings.values()):
            profile["provider_id"] = VENDOR_ID
            profile["model"] = next(b["model_id"] for b in bindings.values() if b and b.get("model_id"))
    legacy = [key for key, p in profiles.items() if not p.get("provider_id") and p.get("provider") != "mock"]
    for key in legacy:
        profiles.pop(key)
    merged["routes"] = {k: v for k, v in (merged.get("routes") or {}).items() if v not in legacy}
    if merged.get("default_profile") in legacy:
        merged["default_profile"] = ""

    rows = {row.key: row for row in db.scalars(select(SystemSetting).where(
        SystemSetting.key.in_(["llm", "image", "dsh"]) | SystemSetting.key.like("discovery.%")))}
    llm = rows.get("llm")
    llm_host = urlsplit(str((llm.value or {}).get("base_url") or "")).hostname if llm else None
    if llm_host and "minimax" in llm_host and llm.value.get("model"):
        chat_profile(llm.value["model"])
    image = rows.get("image")
    if image and (image.value or {}).get("enabled") and image.value.get("provider") == "minimax" and not chosen["cover_image"]["profile"]:
        cover = next((k for k, p in profiles.items() if p.get("provider_id") == VENDOR_ID
                      and "image_generation" in p.get("declared_capabilities", [])), "")
        size = image.value.get("size")
        chosen["cover_image"] = {"profile": cover, "size": size if size in COVER_SIZES else COVER_SIZES[0]}
    dsh = rows.get("dsh")
    if dsh and (dsh.value or {}).get("default_provider") == "minimax" and dsh.value.get("default_model") and not chosen["writing_cli"]:
        chosen["writing_cli"] = chat_profile(dsh.value["default_model"])
    for key, row in rows.items():
        if re.fullmatch(r"discovery\.\d+", key):
            value = dict(row.value or {})
            if not chosen["topic_search"] and value.get("search_provider") in SEARCH_VENDORS:
                chosen["topic_search"] = value["search_provider"]
            value.pop("search_provider", None)
            value.pop("credential_source", None)
            row.value = value
    voice = db.get(SystemSetting, "voice_default")
    if voice is not None and "model_id" in (voice.value or {}):
        voice.value = {k: v for k, v in voice.value.items() if k != "model_id"}
        runtime_config.set_runtime("voice_default", voice.value)
    for key in ("llm", "image", "dsh"):
        if key in rows:
            db.delete(rows[key])
            runtime_config.clear_runtime(key)
    db.flush()
    merged["uses"] = chosen
    merged["schema_version"] = 3
    merged["revision"] = stored.get("revision", 0) + 1
    commit_configuration(db, merged, expected_revision=stored.get("revision", 0), actor="system:unify-model-config")


def cover_image_config() -> dict | None:
    """The 封面生图 use resolved to its vendor; None when not chosen or the vendor has no key."""
    stored = runtime_config.get_runtime(runtime_config.KEY_MODELS) or {}
    chosen = uses(stored)["cover_image"]
    profile = stored.get("profiles", {}).get(chosen["profile"])
    vendor = vendor_of(profile, stored) if profile else None
    if not vendor or not vendor.get("api_key") or not profile.get("model"):
        return None
    return {"vendor_id": vendor["id"], "model": profile["model"], "size": chosen["size"],
            "base_url": vendor["base_url"], "api_key": vendor["api_key"]}
