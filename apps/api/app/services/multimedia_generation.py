"""Shared, provider-neutral contracts for local image and audio generation.

The contract deliberately stops before provider I/O.  Providers still own their
native parameters, while this module freezes the bounded request, exact binding
and receipt material that the caller is allowed to send.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Literal

from fastapi import HTTPException

MULTIMEDIA_SCHEMA = "studio.multimedia.request.v1"
IMAGE_CANDIDATE_MIN = 1
IMAGE_CANDIDATE_MAX = 4
_VOICE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,149}\Z")
_VOICE_REF = re.compile(r"(?:material_revision|local):[A-Za-z0-9_.:-]{1,180}\Z")
_IMAGE_FIELDS = {"items", "pixels", "aspect_ratio", "timeout_seconds"}
_AUDIO_FIELDS = {"items", "seconds", "timeout_seconds", "voice_id", "rate"}


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def normalize_parameters(capability: str, parameters: dict[str, Any] | None) -> dict[str, Any]:
    """Normalize only fields consumed by the selected multimedia adapter."""
    params = dict(parameters or {})
    allowed = _IMAGE_FIELDS if capability == "image_generation" else _AUDIO_FIELDS if capability == "tts" else set()
    if not allowed or set(params) - allowed:
        raise HTTPException(422, "multimedia_parameters_unsupported")
    for name in {"items", "pixels", "seconds", "timeout_seconds"}.intersection(params):
        if type(params[name]) is not int or params[name] < 1:
            raise HTTPException(422, "multimedia_parameter_invalid")
    if capability == "image_generation":
        items = params.setdefault("items", 1)
        if items > IMAGE_CANDIDATE_MAX:
            raise HTTPException(422, "multimedia_image_candidate_count_invalid")
        if "aspect_ratio" in params:
            from .media_dimensions import canonical_aspect_ratio

            try:
                params["aspect_ratio"] = canonical_aspect_ratio(params["aspect_ratio"])
            except (TypeError, ValueError):
                raise HTTPException(422, "multimedia_image_aspect_invalid") from None
    else:
        if params.get("items", 1) != 1:
            raise HTTPException(422, "multimedia_audio_single_output_required")
        voice_id = params.get("voice_id")
        rate = params.get("rate")
        if not isinstance(voice_id, str) or not _VOICE_ID.fullmatch(voice_id):
            raise HTTPException(422, "multimedia_voice_id_required")
        if type(rate) not in {int, float} or not 0.5 <= rate <= 2:
            raise HTTPException(422, "multimedia_voice_rate_invalid")
        params["rate"] = float(rate)
    return params


def normalize_request(*, capability: Literal["image_generation", "tts"], prompt: str,
                      parameters: dict[str, Any] | None, binding: dict[str, Any],
                      configuration_mode: Literal["auto", "custom", "composed"] = "auto",
                      candidate_mode: Literal["native", "fan_out"] | None = None) -> dict[str, Any]:
    if not isinstance(prompt, str) or not prompt.strip():
        raise HTTPException(422, "multimedia_prompt_required")
    if not isinstance(binding, dict) or not all(isinstance(binding.get(key), str) and binding[key] for key in
                                                ("adapter_key", "adapter_version", "model_id")):
        raise HTTPException(422, "multimedia_binding_invalid")
    normalized = normalize_parameters(capability, parameters)
    count = normalized.get("items", 1)
    if capability == "image_generation" and count > 1:
        selected_mode = candidate_mode or "fan_out"
        if selected_mode not in {"native", "fan_out"}:
            raise HTTPException(422, "multimedia_candidate_mode_invalid")
        if selected_mode == "fan_out" and configuration_mode == "custom":
            raise HTTPException(422, "multimedia_custom_batch_requires_declared_composition")
    else:
        selected_mode = "single"
    contract = {
        "schema": MULTIMEDIA_SCHEMA,
        "capability": capability,
        "prompt": prompt.strip(),
        "parameters": normalized,
        "binding": {key: binding[key] for key in ("adapter_key", "adapter_version", "model_id")},
        "configuration_mode": configuration_mode,
        "candidate_mode": selected_mode,
    }
    contract["config_hash"] = digest({key: value for key, value in contract.items() if key != "config_hash"})
    return contract


def receipt_projection(contract: dict[str, Any], *, runtime_hash: str, output_hashes: list[str],
                       selected_index: int | None = None, fallback_reason: str | None = None) -> dict[str, Any]:
    if not isinstance(runtime_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", runtime_hash):
        raise HTTPException(409, "multimedia_runtime_unverified")
    if not output_hashes or any(not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value)
                               for value in output_hashes):
        raise HTTPException(409, "multimedia_output_unverified")
    if selected_index is not None and (type(selected_index) is not int or not 0 <= selected_index < len(output_hashes)):
        raise HTTPException(422, "multimedia_candidate_selection_invalid")
    receipt = {
        "schema": "studio.multimedia.receipt.v1",
        "config_hash": contract.get("config_hash"),
        "runtime_hash": runtime_hash,
        "candidate_mode": contract.get("candidate_mode"),
        "candidate_indexes": list(range(len(output_hashes))),
        "output_hashes": list(output_hashes),
        "selected_index": selected_index,
    }
    if fallback_reason is not None:
        receipt["fallback_reason"] = fallback_reason
    receipt["receipt_hash"] = digest({key: value for key, value in receipt.items() if key != "receipt_hash"})
    return receipt


def voice_preset_projection(value: dict[str, Any], *, trusted_verified: bool = False) -> dict[str, Any]:
    """Validate a secret-free local VoicePreset projection.

    ``verified`` is provider evidence, not a client-editable flag.  Only an
    explicit provider catalog refresh may preserve it.
    """
    allowed = {"id", "label", "provider_key", "provider_version", "model_id", "profile_id", "voice_id",
               "language", "tags", "favorite", "preview_ref", "verified", "rate"}
    if not isinstance(value, dict) or set(value) - allowed:
        raise HTTPException(422, "voice_preset_invalid")
    required = ("id", "label", "provider_key", "provider_version", "model_id", "profile_id", "voice_id")
    if any(not isinstance(value.get(key), str) or not value[key] or len(value[key]) > 200 for key in required):
        raise HTTPException(422, "voice_preset_invalid")
    if any(ord(char) < 32 for char in value["label"]):
        raise HTTPException(422, "voice_preset_invalid")
    if any(not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:@-]{0,199}\Z", value[key])
           for key in ("id", "provider_key", "provider_version", "model_id", "profile_id")):
        raise HTTPException(422, "voice_preset_invalid")
    if not _VOICE_ID.fullmatch(value["voice_id"]):
        raise HTTPException(422, "voice_preset_invalid")
    language = value.get("language", "")
    if not isinstance(language, str) or len(language) > 40 or any(ord(char) < 32 for char in language):
        raise HTTPException(422, "voice_preset_invalid")
    tags = value.get("tags") or []
    if (not isinstance(tags, list) or len(tags) > 20
            or any(not isinstance(tag, str) or not re.fullmatch(r"[^\x00-\x1f]{1,60}\Z", tag) for tag in tags)):
        raise HTTPException(422, "voice_preset_invalid")
    preview_ref = value.get("preview_ref")
    if preview_ref is not None and (not isinstance(preview_ref, str) or not _VOICE_REF.fullmatch(preview_ref)):
        raise HTTPException(422, "voice_preset_invalid")
    if value.get("rate") is not None and (type(value["rate"]) not in {int, float} or not 0.5 <= value["rate"] <= 2):
        raise HTTPException(422, "voice_preset_invalid")
    from .creative_intents import contains_secret_text

    if contains_secret_text(json.dumps(value, ensure_ascii=False)):
        raise HTTPException(422, "voice_preset_unsafe_content")
    return {
        "id": value["id"], "label": value["label"], "provider_key": value["provider_key"],
        "provider_version": value["provider_version"], "model_id": value["model_id"],
        "profile_id": value["profile_id"], "voice_id": value["voice_id"],
        "language": language, "tags": list(tags),
        "favorite": value.get("favorite") is True, "preview_ref": preview_ref,
        "verified": trusted_verified and value.get("verified") is True,
        "rate": float(value["rate"]) if value.get("rate") is not None else 1.0,
    }


def voice_catalog_projection(value: list[dict[str, Any]], *, trusted_verified: bool = False) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) > 2000:
        raise HTTPException(422, "voice_catalog_invalid")
    catalog = [voice_preset_projection(item, trusted_verified=trusted_verified) for item in value]
    ids = [item["id"] for item in catalog]
    bindings = [tuple(item[key] for key in ("provider_key", "provider_version", "model_id", "profile_id", "voice_id"))
                for item in catalog]
    if len(ids) != len(set(ids)) or len(bindings) != len(set(bindings)):
        raise HTTPException(422, "voice_catalog_duplicate")
    return catalog
