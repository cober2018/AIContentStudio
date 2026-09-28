"""Small, explicit modality registry for Production Core."""

import json
from dataclasses import dataclass


@dataclass(frozen=True)
class ModalityDescriptor:
    modality: str
    payload_schema: str
    required_checks: tuple[str, ...]
    candidate_freeze_available: bool
    unavailable_reason: str | None = None


def _validate_text(payload: dict) -> list[str]:
    if not isinstance(payload, dict):
        return ["payload_not_object"]
    if payload.get("markdown") is not None and not isinstance(payload["markdown"], str):
        return ["markdown_must_be_string"]
    if payload.get("document") is not None and not isinstance(payload["document"], dict):
        return ["document_must_be_object"]
    return []


def _validate_graphic(payload: dict) -> list[str]:
    if not isinstance(payload, dict) or not isinstance(payload.get("canvases", []), list):
        return ["canvases_must_be_array"]
    return []


def _validate_video(payload: dict) -> list[str]:
    if not isinstance(payload, dict) or not isinstance(payload.get("shots", []), list):
        return ["shots_must_be_array"]
    return []


DESCRIPTORS = {
    "text": ModalityDescriptor("text", "text.master.v1", ("master_schema", "evidence", "rights", "render"), True),
    "graphic": ModalityDescriptor("graphic", "graphic.master.v1", ("master_schema", "evidence", "rights", "render"), False, "final_render_required"),
    "video": ModalityDescriptor("video", "video.master.v1", ("master_schema", "evidence", "rights", "render"), False, "final_render_required"),
}


VALIDATORS = {"text": _validate_text, "graphic": _validate_graphic, "video": _validate_video}


def descriptor(modality: str) -> ModalityDescriptor:
    return DESCRIPTORS.get(modality) or ModalityDescriptor(modality, f"{modality}.master.v1", ("master_schema",), False, "unsupported_modality")


def validate_payload(modality: str, payload: dict, *, for_freeze: bool = False) -> list[str]:
    bounds = validate_json_bounds(payload)
    if bounds:
        return bounds
    errors = VALIDATORS.get(modality, lambda value: ["unsupported_modality"])(payload)
    if for_freeze and modality == "text" and not (payload.get("document") or (payload.get("markdown") or "").strip()):
        errors.append("text_content_missing")
    if for_freeze and modality == "text" and payload.get("document") and not (payload.get("markdown") or "").strip():
        errors.append("document_renderer_unavailable")
    if for_freeze and modality in {"graphic", "video"}:
        errors.append("final_render_required")
    return errors


def validate_json_bounds(value: object) -> list[str]:
    stack = [(value, 0)]
    visited = 0
    while stack:
        item, depth = stack.pop()
        visited += 1
        if depth > 32:
            return ["payload_too_deep"]
        if visited > 20_000:
            return ["payload_too_many_values"]
        if isinstance(item, (list, dict)):
            if len(item) > 1000:
                return ["payload_collection_too_large"]
            stack.extend((child, depth + 1) for child in (item.values() if isinstance(item, dict) else item))
    try:
        canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    except (TypeError, ValueError):
        return ["payload_invalid_json"]
    return ["payload_too_large"] if len(canonical) > 2_000_000 else []
