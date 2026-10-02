"""Versioned native model contracts used by capability routing.

This module deliberately builds and validates provider requests without sending
them. Dispatch remains behind the existing bounded provider/media execution
path, so a configured model cannot become a verified capability merely because
its name looks like a media model.
"""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True, slots=True)
class NativeOperation:
    capability: str
    models: frozenset[str]
    method: str
    path: str
    auth_header: str


class NativeModelAdapter:
    key: str
    version = "1"

    def __init__(self, key: str, *, host: str, operations: tuple[NativeOperation, ...]):
        self.key = key
        self.host = host
        self.operations = operations

    def _operation(self, capability: str, model_id: str) -> NativeOperation | None:
        return next((item for item in self.operations
                     if item.capability == capability and model_id in item.models), None)

    def binding_state(self, capability: str, binding: dict) -> dict:
        model_id = binding.get("model_id")
        base_url = binding.get("base_url")
        credential_ref = binding.get("credential_ref")
        if not isinstance(model_id, str) or not isinstance(base_url, str) or not isinstance(credential_ref, str):
            return {"reason": "binding_invalid", "runtime_hash": None}
        operation = self._operation(capability, model_id)
        if operation is None:
            return {"reason": "adapter_capability_unsupported", "runtime_hash": None}
        parsed = urlsplit(base_url)
        if parsed.scheme != "https" or parsed.hostname != self.host or parsed.username or parsed.password:
            return {"reason": "connection_unavailable", "runtime_hash": None}
        # A protocol codec is not an executor. Until bounded dispatch and exact
        # acceptance revalidation are wired, even complete config must block.
        return {"reason": "connection_unavailable", "runtime_hash": None}

    def build_request(self, capability: str, binding: dict, *, prompt: str, inputs: list[dict] | None = None) -> dict:
        operation = self._operation(capability, binding.get("model_id"))
        if operation is None:
            raise ValueError("model_operation_unsupported")
        if (not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 2000
                or inputs or binding.get("base_url") != f"https://{self.host}"):
            raise ValueError("native_request_invalid")
        if self.key == "google.native":
            payload = {"model": binding["model_id"], "input": [{"type": "text", "text": prompt}]}
        else:
            payload = {"model": binding["model_id"], "prompt": prompt, "n": 1, "response_format": "b64_json"}
        return {"method": operation.method, "path": operation.path, "auth_header": operation.auth_header, "payload": payload}

    def image_bytes(self, body: dict) -> tuple[bytes, str]:
        if self.key != "xai.native" or not isinstance(body, dict):
            raise ValueError("native_response_unsupported")
        data = body.get("data")
        if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], dict):
            raise ValueError("native_response_invalid")
        encoded = data[0].get("b64_json")
        if not isinstance(encoded, str) or len(encoded) > 7 * 1024 * 1024:
            raise ValueError("native_response_invalid")
        try:
            content = base64.b64decode(encoded, validate=True)
        except ValueError:
            raise ValueError("native_response_invalid") from None
        if not content or len(content) > 5 * 1024 * 1024:
            raise ValueError("native_response_invalid")
        from .materials import sniff_mime

        mime = sniff_mime(content, None)
        if mime not in {"image/png", "image/jpeg", "image/webp"}:
            raise ValueError("native_response_invalid")
        return content, mime


GOOGLE_NATIVE = NativeModelAdapter(
    "google.native",
    host="generativelanguage.googleapis.com",
    operations=(
        NativeOperation("image_generation", frozenset({"gemini-3.1-flash-image", "gemini-3-pro-image", "gemini-2.5-flash-image"}), "POST", "/v1beta/interactions", "x-goog-api-key"),
    ),
)

XAI_NATIVE = NativeModelAdapter(
    "xai.native",
    host="api.x.ai",
    operations=(
        NativeOperation("image_generation", frozenset({"grok-imagine-image", "grok-imagine-image-2.0"}), "POST", "/v1/images/generations", "Authorization: Bearer"),
    ),
)

# MiniMax is registered as a known adapter key so configuration can explain why
# a binding is unavailable. No operation is enabled until its official contract
# is verified; this intentionally prevents a chat endpoint from being reused as
# a media or voice endpoint.
MINIMAX_NATIVE = NativeModelAdapter("minimax.native", host="api.minimax.io", operations=())


def bootstrap_native_model_adapters() -> None:
    if os.getenv("AICS_ENABLE_NATIVE_MODEL_ADAPTERS") != "1":
        return
    from .content_harness.registry import registry

    for adapter in (GOOGLE_NATIVE, XAI_NATIVE, MINIMAX_NATIVE):
        if adapter.key not in {item.key for item in registry.list("model_provider")}:
            registry.register("model_provider", adapter.key, adapter.version, adapter, label=f"{adapter.key} native adapter")
