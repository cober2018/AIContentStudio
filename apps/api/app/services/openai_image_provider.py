"""One-shot configured image generation; durable acceptance stays in provider_media."""

import base64
import hashlib
import hmac
import ipaddress
import json
import marshal
import secrets
import socket
import time
from urllib.parse import urlsplit

import httpx
from httpcore._backends.sync import SyncBackend

from app.services.content_harness.providers import MediaOutput
from app.services.url_fetch import (
    OUTBOUND_HTTP_POLICIES,
    enforce_outbound_host,
    outbound_scope,
    resolve_addresses,
)
from app.services.url_fetch import (
    _PinnedBackend as PinnedHttpBackend,
)

_IDENTITY_KEY = secrets.token_bytes(32)
MAX_RESPONSE_BYTES = OUTBOUND_HTTP_POLICIES["image"].response_bytes
REQUEST_TIMEOUT_SECONDS = OUTBOUND_HTTP_POLICIES["image"].timeout_seconds
MAX_IMAGE_BYTES = 5 * 1024 * 1024
_MODELS = {"gpt-image-1", "gpt-image-1-mini", "gpt-image-1.5"}


class _PinnedBackend(SyncBackend):
    def __init__(self, host, address, deadline=None):
        self.host, self.address = host, address
        self.deadline = deadline

    def connect_tcp(self, host, port, timeout=None, local_address=None, socket_options=None):
        if host != self.host or port != 443:
            raise OSError("provider_target_mismatch")
        # TCP uses the checked address; httpcore still negotiates TLS for the original host.
        return PinnedHttpBackend(self.host, port, self.address, self.deadline).connect_tcp(
            host, port, timeout=timeout, local_address=local_address, socket_options=socket_options)


def _config():
    from .model_registration import cover_image_config

    value = cover_image_config()
    # An OpenAI image model chosen for 封面生图 goes to the native images API; others go through wewrite.
    if value is None or not (value["model"] in _MODELS or value["model"].startswith("dall-e-")):
        return None
    config = {key: value.get(key) for key in ("model", "size", "base_url", "api_key")}
    if any(not isinstance(item, str) or not item or any(ord(c) < 32 for c in item) for item in config.values()):
        return None
    model, size = config["model"], config["size"]
    sizes = (
        {"1024x1024", "1536x1024", "1024x1536", "auto"}
        if model in _MODELS
        else (
            {"256x256", "512x512", "1024x1024"}
            if model == "dall-e-2"
            else {"1024x1024", "1792x1024", "1024x1792"}
            if model == "dall-e-3"
            else set()
        )
    )
    if size not in sizes:
        return None
    try:
        enforce_outbound_host(config["base_url"])
        url = urlsplit(config["base_url"])
        if (
            url.scheme != "https"
            or not url.hostname
            or url.username
            or url.password
            or url.query
            or url.fragment
            or url.port not in (None, 443)
        ):
            return None
    except ValueError:
        return None
    if url.path not in ("/v1", "/v1/"):
        return None
    return config


def _identity(config):
    credential = hmac.new(_IDENTITY_KEY, config["api_key"].encode(), hashlib.sha256).hexdigest()
    code = b"".join(
        marshal.dumps(fn.__code__, 2)
        for fn in (_config, _identity, _PinnedBackend.connect_tcp, OpenAIImageProvider.generate)
    )
    safe = {key: value for key, value in config.items() if key != "api_key"}
    return hashlib.sha256(json.dumps(safe, sort_keys=True).encode() + credential.encode() + code).hexdigest()


class OpenAIImageProvider:
    key = "image.openai"
    version = "1"

    def runtime_fingerprint(self):
        config = _config()
        return _identity(config) if config else None

    def generate(self, request):
        config = _config()
        prompt = request.get("prompt")
        if (
            not config
            or request.get("source_bytes")
            or request.get("source_revision_ids")
            or not isinstance(prompt, str)
            or not prompt.strip()
            or len(prompt) > (1000 if config["model"] == "dall-e-2" else 2000)
        ):
            return MediaOutput("unavailable")
        started = time.monotonic()
        deadline = started + REQUEST_TIMEOUT_SECONDS
        try:
            host = urlsplit(config["base_url"]).hostname
            with outbound_scope(deadline):
                addresses = resolve_addresses(host, 443)
            if not addresses or any(
                item[0] not in {socket.AF_INET, socket.AF_INET6}
                or not ipaddress.ip_address(item[4][0]).is_global
                for item in addresses
            ):
                return MediaOutput("unavailable")
        except (OSError, ValueError):
            return MediaOutput("unavailable")
        payload = {"model": config["model"], "size": config["size"], "prompt": prompt, "n": 1}
        payload["output_format" if config["model"] in _MODELS else "response_format"] = (
            "png" if config["model"] in _MODELS else "b64_json"
        )
        request_body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        if len(request_body) > OUTBOUND_HTTP_POLICIES["image"].request_bytes:
            return MediaOutput("unavailable")
        try:
            remaining = REQUEST_TIMEOUT_SECONDS - (time.monotonic() - started)
            if remaining <= 0:
                return MediaOutput("unavailable")
            transport = httpx.HTTPTransport(retries=0, trust_env=False)
            transport._pool._network_backend = _PinnedBackend(host, addresses[0][4][0], deadline)
            with (
                outbound_scope(deadline),
                httpx.Client(timeout=remaining, follow_redirects=False, trust_env=False, transport=transport) as client,
                client.stream(
                    "POST",
                    config["base_url"].rstrip("/") + "/images/generations",
                    headers={"Authorization": "Bearer " + config["api_key"], "Accept-Encoding": "identity", "Content-Type": "application/json"},
                    content=request_body,
                ) as response,
            ):
                if response.status_code != 200:
                    return MediaOutput(
                        "unknown" if response.status_code >= 500 or 300 <= response.status_code < 400 else "failed"
                    )
                if response.headers.get("content-type", "").split(";")[0].strip() != "application/json":
                    return MediaOutput("failed")
                if response.headers.get("content-encoding", "identity").strip().lower() != "identity":
                    return MediaOutput("failed")
                chunks, length = [], 0
                for chunk in response.iter_bytes():
                    length += len(chunk)
                    if length > MAX_RESPONSE_BYTES or time.monotonic() - started >= REQUEST_TIMEOUT_SECONDS:
                        return MediaOutput("unknown")
                    chunks.append(chunk)
                body = json.loads(b"".join(chunks))
                if time.monotonic() - started >= REQUEST_TIMEOUT_SECONDS:
                    return MediaOutput("unknown")
            data = body.get("data") if isinstance(body, dict) else None
            if (
                not isinstance(data, list)
                or len(data) != 1
                or not isinstance(data[0], dict)
                or not isinstance(data[0].get("b64_json"), str)
            ):
                return MediaOutput("failed")
            content = base64.b64decode(data[0]["b64_json"], validate=True)
            if len(content) > MAX_IMAGE_BYTES or not content.startswith(b"\x89PNG\r\n\x1a\n"):
                return MediaOutput("failed")
            if _config() != config:
                return MediaOutput("unknown")
            return MediaOutput("succeeded", content, "image/png")
        except (httpx.HTTPError, OSError):
            return MediaOutput("unknown")
        except (ValueError, TypeError):
            return MediaOutput("failed")
