"""Registered CPA OpenAI-compatible image protocol.

The adapter consumes only the existing model-registration snapshot.  It never
discovers a provider, promotes a chat model to an image model, or accepts a
remote image URL as output.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import marshal
import os
import re
from io import BytesIO
from urllib.parse import quote

from fastapi import HTTPException

from .. import runtime_config
from .content_harness.providers import MediaOutput
from .media_dimensions import image_dimensions

KEY = "openai.compatible"
VERSION = "1"
ADAPTER_KEY = "openai.compatible"
PROTOCOL = "cpa.images.b64.v1"
NATIVE_PROTOCOL = "cpa.gemini.generate-content.image.v1"
MAX_PROMPT = 2000
MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_RESPONSE_BYTES = 8 * 1024 * 1024
_MODEL = re.compile(r"[A-Za-z0-9_./:-]{1,160}\Z")


def _models() -> dict:
    value = runtime_config.get_runtime("models") or {}
    return value if isinstance(value, dict) else {}


def _matches(binding: dict, version: str = VERSION) -> list[tuple[str, dict, dict]]:
    if not isinstance(binding, dict):
        return []
    model_id, base_url = binding.get("model_id"), binding.get("base_url")
    if (not isinstance(model_id, str) or not _MODEL.fullmatch(model_id)
            or not isinstance(base_url, str) or not base_url):
        return []
    stored = _models()
    providers = stored.get("providers") if isinstance(stored.get("providers"), dict) else {}
    profiles = stored.get("profiles") if isinstance(stored.get("profiles"), dict) else {}
    found = []
    for profile_id, profile in profiles.items():
        if not isinstance(profile_id, str) or not isinstance(profile, dict):
            continue
        if profile.get("provider") != "openai_compatible" or profile.get("model") != model_id:
            continue
        if "image_generation" not in profile.get("declared_capabilities", []):
            continue
        provider_id = profile.get("provider_id")
        provider = providers.get(provider_id) if isinstance(provider_id, str) else None
        if (not isinstance(provider, dict) or provider.get("enabled") is not True
                or not provider.get("api_key") or provider.get("base_url") != base_url):
            continue
        binding_cfg = (profile.get("capability_bindings") or {}).get("image_generation")
        if (not isinstance(binding_cfg, dict) or binding_cfg.get("adapter_key") != ADAPTER_KEY
                or binding_cfg.get("adapter_version") != version
                or binding.get("adapter_version") != version
                or binding_cfg.get("model_id") != model_id
                or binding_cfg.get("base_url") != base_url):
            continue
        found.append((profile_id, provider, profile))
    return found


def _receipt_key(key_id: str | None = None) -> bytes | None:
    try:
        keys = json.loads(os.environ.get("AICS_GENERATION_RECEIPT_KEYS", "{}"))
        selected = key_id or os.environ.get("AICS_GENERATION_RECEIPT_KEY_ID")
        value = keys.get(selected) if isinstance(keys, dict) else None
        if not isinstance(selected, str) or not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
            return None
        return bytes.fromhex(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None


def _safe_provider_fingerprint(version: str = VERSION) -> str | None:
    key = _receipt_key()
    if key is None:
        return None
    entries = []
    for profile_id, provider, profile in _all_profiles():
        entries.append({"profile": profile_id, "provider": profile.get("provider_id"),
                        "model": profile.get("model"), "base_url": provider.get("base_url"),
                        "enabled": provider.get("enabled") is True,
                        "credential_epoch": hmac.new(key, b"aics:cpa-credential:" + str(provider.get("api_key")).encode(), hashlib.sha256).hexdigest(),
                        "binding": (profile.get("capability_bindings") or {}).get("image_generation")})
    safe = json.dumps(sorted(entries, key=lambda item: item["profile"]), sort_keys=True, separators=(",", ":"))
    code = b"".join(marshal.dumps(method.__code__, 2) for method in
                    (CPAImageProvider.generate, CPAImageProvider.decode_native_image, CPAImageProvider._decode))
    protocol = NATIVE_PROTOCOL if version == "2" else PROTOCOL
    return hmac.new(key, b"aics:cpa-images:" + version.encode() + protocol.encode() + safe.encode() + code, hashlib.sha256).hexdigest()


def _all_profiles():
    stored = _models()
    providers = stored.get("providers") if isinstance(stored.get("providers"), dict) else {}
    profiles = stored.get("profiles") if isinstance(stored.get("profiles"), dict) else {}
    for profile_id, profile in profiles.items():
        if not isinstance(profile, dict):
            continue
        provider_id = profile.get("provider_id")
        provider = providers.get(provider_id) if isinstance(provider_id, str) else None
        if isinstance(provider, dict):
            yield profile_id, provider, profile


class CPAImageProvider:
    key = KEY
    version = VERSION

    def __init__(self, version: str = VERSION):
        if version not in {"1", "2"}:
            raise ValueError("cpa_image_protocol_unsupported")
        self.version = version
        self.protocol = NATIVE_PROTOCOL if version == "2" else PROTOCOL

    def runtime_fingerprint(self):
        return _safe_provider_fingerprint(self.version)

    def _binding_state(self, capability: str, binding: dict):
        if capability != "image_generation" or binding.get("adapter_key") != ADAPTER_KEY:
            return {"reason": "adapter_capability_unsupported", "runtime_hash": None}
        matches = _matches(binding, self.version)
        if not matches:
            return {"reason": "model_operation_unsupported", "runtime_hash": None}
        if _receipt_key() is None:
            return {"reason": "credential_continuity_unverified", "runtime_hash": None}
        return {"reason": "credential_continuity_unverified", "runtime_hash": None}

    def binding_state(self, capability: str, binding: dict):
        return self._binding_state(capability, binding)

    def execution_binding_state(self, capability: str, binding: dict):
        state = self._binding_state(capability, binding)
        runtime = _safe_provider_fingerprint(self.version) if state["reason"] == "credential_continuity_unverified" else None
        if runtime is None:
            return {"reason": "connection_unavailable", "runtime_hash": None}
        return {"reason": None, "runtime_hash": runtime}

    def durable_identity(self, model_id: str):
        matches = [item for item in _all_profiles() if item[2].get("model") == model_id
                   and "image_generation" in item[2].get("declared_capabilities", [])]
        key = _receipt_key()
        if len(matches) != 1 or key is None:
            return None
        _profile_id, provider, _profile = matches[0]
        epoch = hmac.new(key, b"aics:cpa-credential:" + str(provider.get("api_key")).encode(), hashlib.sha256).hexdigest()
        return {"credential_epoch": epoch, "protocol_version": self.protocol}

    def durable_identity_for_key(self, model_id: str, receipt_key_id: str):
        # Historical receipts use the requested signing key, while the live
        # provider config remains the sole credential source.
        matches = [item for item in _all_profiles() if item[2].get("model") == model_id
                   and "image_generation" in item[2].get("declared_capabilities", [])]
        key = _receipt_key(receipt_key_id)
        if len(matches) != 1 or key is None:
            return None
        _profile_id, provider, _profile = matches[0]
        epoch = hmac.new(key, b"aics:cpa-credential:" + str(provider.get("api_key")).encode(), hashlib.sha256).hexdigest()
        return {"credential_epoch": epoch, "protocol_version": self.protocol}

    @staticmethod
    def decode_native_image(body: dict, pixels: int) -> list[tuple[bytes, str]]:
        from PIL import Image

        candidates = body.get("candidates") if isinstance(body, dict) else None
        if not isinstance(candidates, list) or len(candidates) != 1 or not isinstance(candidates[0], dict):
            raise ValueError("cpa_image_response_invalid")
        content = candidates[0].get("content")
        parts = content.get("parts") if isinstance(content, dict) else None
        if not isinstance(parts, list) or len(parts) > 100:
            raise ValueError("cpa_image_response_invalid")
        images = []
        for part in parts:
            if not isinstance(part, dict):
                raise TypeError("cpa_image_response_invalid")
            if part.get("thought") is True:
                continue
            inline = part.get("inlineData")
            if inline is None:
                continue
            if not isinstance(inline, dict):
                raise TypeError("cpa_image_response_invalid")
            decoded = CPAImageProvider._decode({"data": [{"b64_json": inline.get("data")}]}, 1)[0]
            if inline.get("mimeType") != decoded[1]:
                raise ValueError("cpa_image_response_invalid")
            with Image.open(BytesIO(decoded[0])) as image:
                width, height = image.size
                if (image.format not in {"PNG", "JPEG", "WEBP"} or min(width, height) < 1
                        or max(width, height) > 2048 or width * height > pixels):
                    raise ValueError("cpa_image_response_limit")
                image.verify()
            with Image.open(BytesIO(decoded[0])) as image:
                image.load()
            images.append(decoded)
        if len(images) != 1:
            raise ValueError("cpa_image_response_invalid")
        return images

    @staticmethod
    def _decode(body: dict, count: int) -> list[tuple[bytes, str]]:
        data = body.get("data") if isinstance(body, dict) else None
        if not isinstance(data, list) or len(data) != count:
            raise ValueError("cpa_image_response_invalid")
        outputs = []
        total = 0
        from .materials import sniff_mime

        for item in data:
            encoded = item.get("b64_json") if isinstance(item, dict) else None
            if not isinstance(encoded, str) or len(encoded) > 7 * 1024 * 1024:
                raise ValueError("cpa_image_response_invalid")
            try:
                content = base64.b64decode(encoded, validate=True)
            except (ValueError, TypeError):
                raise ValueError("cpa_image_response_invalid") from None
            mime = sniff_mime(content, None)
            if mime not in {"image/png", "image/jpeg", "image/webp"} or not content or len(content) > MAX_IMAGE_BYTES:
                raise ValueError("cpa_image_response_invalid")
            total += len(content)
            if total > MAX_RESPONSE_BYTES:
                raise ValueError("cpa_image_response_limit")
            outputs.append((content, mime))
        return outputs

    def generate_batch(self, request: dict) -> MediaOutput:
        return self.generate(request)

    def submit_task(self, request: dict) -> MediaOutput:
        return self.generate(request)

    def generate(self, request: dict) -> MediaOutput:
        from .model_registration import provider_request

        model_id = request.get("model_id")
        profile_id = request.get("profile_id")
        prompt = request.get("prompt")
        params = request.get("parameters") if isinstance(request.get("parameters"), dict) else {}
        count = params.get("items", 1)
        if (not isinstance(profile_id, str) or not isinstance(model_id, str) or not isinstance(prompt, str)
                or not 1 <= len(prompt.strip()) <= MAX_PROMPT or request.get("source_bytes")
                or request.get("source_revision_ids") or type(count) is not int or not 1 <= count <= 4):
            return MediaOutput("unavailable")
        stored = _models()
        profile = (stored.get("profiles") or {}).get(profile_id) if isinstance(stored.get("profiles"), dict) else None
        provider_id = profile.get("provider_id") if isinstance(profile, dict) else None
        provider = (stored.get("providers") or {}).get(provider_id) if isinstance(provider_id, str) and isinstance(stored.get("providers"), dict) else None
        if (not isinstance(profile, dict) or profile.get("model") != model_id or profile.get("enabled") is False
                or "image_generation" not in profile.get("declared_capabilities", [])
                or not isinstance(provider, dict) or provider.get("enabled") is not True or not provider.get("api_key")):
            return MediaOutput("unavailable")
        binding = (profile.get("capability_bindings") or {}).get("image_generation")
        if (not isinstance(binding, dict) or binding.get("adapter_key") != ADAPTER_KEY
                or binding.get("adapter_version") != self.version
                or binding.get("model_id") != model_id or binding.get("base_url") != provider.get("base_url")):
            return MediaOutput("unavailable")
        try:
            width, height = image_dimensions(params.get("pixels", 1024 * 1024), params.get("aspect_ratio", "1:1"))
        except (TypeError, ValueError):
            return MediaOutput("unavailable")
        payload = {"model": model_id, "prompt": prompt.strip(), "n": count,
                   "size": f"{width}x{height}", "response_format": "b64_json"}
        ratio = params.get("aspect_ratio")
        if isinstance(ratio, str):
            payload["aspect_ratio"] = ratio
        path = "/images/generations"
        if self.version == "2":
            if count != 1 or not _MODEL.fullmatch(model_id):
                return MediaOutput("unavailable")
            path = "/v1beta/models/" + quote(model_id, safe="") + ":generateContent"
            payload = {"contents": [{"role": "user", "parts": [{"text": prompt.strip()}]}],
                       "generationConfig": {"responseModalities": ["IMAGE"],
                                            "imageConfig": {"aspectRatio": params.get("aspect_ratio", "1:1")}}}
        try:
            body = provider_request(provider, path, payload=payload,
                                    timeout=min(params.get("timeout_seconds", 25), 120))
        except HTTPException as exc:
            if isinstance(exc.detail, str) and exc.detail in {"provider_authentication_rejected", "provider_image_protocol_rejected", "provider_request_rejected"}:
                return MediaOutput("failed", metadata={"reason": exc.detail, "protocol": self.protocol})
            if exc.status_code in {413, 422}:
                return MediaOutput("unavailable", metadata={"reason": "provider_configuration_unavailable"})
            return MediaOutput("unknown")
        except Exception:  # noqa: BLE001 Provider diagnostics never leave this boundary.
            # A transport/authentication exception does not prove that no
            # request was sent, so the durable task keeps the outcome unknown.
            return MediaOutput("unknown")
        try:
            outputs = (self.decode_native_image(body, params.get("pixels", 1024 * 1024))
                       if self.version == "2" else self._decode(body, count))
        except Exception:  # noqa: BLE001 Invalid image codecs must not expose provider data.
            # A successful response with URLs, prose, the wrong count or bad
            # bytes is a confirmed contract failure, never a retry signal.
            return MediaOutput("failed")
        candidates = [{"content": content, "mime_type": mime, "metadata": {"candidate_index": index}}
                      for index, (content, mime) in enumerate(outputs)]
        if count == 1:
            return MediaOutput("succeeded", outputs[0][0], outputs[0][1], metadata={"protocol": self.protocol})
        return MediaOutput("succeeded", metadata={"protocol": self.protocol, "candidates": candidates})
