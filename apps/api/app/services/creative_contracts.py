"""Bounded transport contracts shared by creative packages and executions."""

import hashlib
import json
import re

from fastapi import HTTPException

from .creative_intents import contains_secret_text

MAX_FILE_BYTES = 30 * 1024 * 1024
MAX_INPUTS = 100
MAX_OUTPUT_ROWS = 500
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,99}$")
_UNSAFE_KEYS = {"api_key", "access_token", "secret", "password", "raw_output", "raw_error", "raw_response", "authorization", "file_path", "absolute_path", "local_path"}
EXECUTOR_DECLARATION_FIELDS = {"supports_checkpoint", "supports_revert", "supports_recover", "output_kinds"}
_OUTPUT_KINDS = {"image", "video", "audio", "other"}
_METADATA_KEYS = {"web_provider", "visible_model", "generated_at", "origin", "summary", "checkpoint_ref", "observation_ref", "observation_hash", "recovery_action", "readback_status", "license", "license_id", "license_url", "attribution", "correlation_id"} | EXECUTOR_DECLARATION_FIELDS


def canonical_hash(value: object) -> str:
    try:
        return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    except (TypeError, ValueError, UnicodeError):
        raise HTTPException(422, {"code": "creative_invalid_json"}) from None


def bounded_json(value: object, *, max_bytes: int = 2_000_000) -> object:
    stack = [(value, 0)]
    seen = 0
    while stack:
        item, depth = stack.pop()
        seen += 1
        if depth > 24 or seen > 20_000:
            raise HTTPException(422, {"code": "creative_json_bounds"})
        if isinstance(item, dict):
            if len(item) > 500 or any(not isinstance(key, str) or len(key) > 100 or key.lower().replace("-", "_") in _UNSAFE_KEYS for key in item):
                raise HTTPException(422, {"code": "creative_unsafe_metadata"})
            stack.extend((child, depth + 1) for child in item.values())
        elif isinstance(item, list):
            if len(item) > 1000:
                raise HTTPException(422, {"code": "creative_json_bounds"})
            stack.extend((child, depth + 1) for child in item)
        elif isinstance(item, str) and (len(item) > 100_000 or contains_secret_text(item)):
            raise HTTPException(422, {"code": "creative_unsafe_metadata"})
    try:
        raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    except (TypeError, ValueError, UnicodeError):
        raise HTTPException(422, {"code": "creative_invalid_json"}) from None
    if len(raw) > max_bytes:
        raise HTTPException(422, {"code": "creative_json_bounds"})
    return json.loads(raw)


def safe_metadata(value: dict | None) -> dict:
    value = value or {}
    if not isinstance(value, dict) or set(value) - _METADATA_KEYS:
        raise HTTPException(422, {"code": "creative_metadata_field_invalid"})
    if "web_provider" in value and (not isinstance(value["web_provider"], str) or value["web_provider"] not in {"grok", "gemini"}):
        raise HTTPException(422, {"code": "creative_web_provider_invalid"})
    if "origin" in value and (not isinstance(value["origin"], str) or value["origin"] not in {"manual_web", "codex_web"}):
        raise HTTPException(422, {"code": "creative_web_origin_invalid"})
    for key, item in value.items():
        if key == "output_kinds":
            if (not isinstance(item, list) or not 1 <= len(item) <= 4
                    or any(not isinstance(kind, str) or kind not in _OUTPUT_KINDS for kind in item)
                    or len(set(item)) != len(item)):
                raise HTTPException(422, {"code": "creative_execution_output_kinds_invalid"})
            continue
        if type(item) not in {str, bool} or isinstance(item, str) and len(item) > 2000:
            raise HTTPException(422, {"code": "creative_metadata_value_invalid"})
        if key.endswith("_ref") and not SAFE_ID.fullmatch(item if isinstance(item, str) else ""):
            raise HTTPException(422, {"code": "creative_reference_invalid"})
    return bounded_json({**value, **({"output_kinds": sorted(value["output_kinds"])} if "output_kinds" in value else {})}, max_bytes=16_000)


def executor_descriptor(identity: dict, metadata: dict, *, require_complete: bool = False) -> dict:
    fields = EXECUTOR_DECLARATION_FIELDS & metadata.keys()
    # Older partial capability metadata remains readable, but is not a complete declaration.
    if fields and (require_complete or "output_kinds" in fields) and fields != EXECUTOR_DECLARATION_FIELDS:
        raise HTTPException(422, {"code": "creative_execution_descriptor_incomplete"})
    return {**identity, **{key: metadata.get(key) for key in sorted(EXECUTOR_DECLARATION_FIELDS)},
        "declaration_status": "declared" if fields == EXECUTOR_DECLARATION_FIELDS else "undeclared",
        "runtime_verified": False}


def canonical_output_contract(value: dict) -> dict:
    if not isinstance(value, dict) or set(value) - {"roles", "media_transfer_policy"} or not isinstance(value.get("roles"), list) or not 1 <= len(value["roles"]) <= 20:
        raise HTTPException(422, {"code": "creative_output_contract_invalid"})
    policy = value.get("media_transfer_policy")
    if policy is not None and (not isinstance(policy, dict) or set(policy) != {"schema", "max_file_bytes", "max_total_bytes", "max_concurrent_transfers"}
                or policy["schema"] != "creative.media-transfer.v1"
                or type(policy["max_file_bytes"]) is not int or not 1 <= policy["max_file_bytes"] <= 512 * 1024 * 1024
                or type(policy["max_total_bytes"]) is not int or not policy["max_file_bytes"] <= policy["max_total_bytes"] <= 4 * 1024**3
                or type(policy["max_concurrent_transfers"]) is not int or policy["max_concurrent_transfers"] != 1):
        raise HTTPException(422, {"code": "creative_transfer_policy_invalid"})
    maximum = policy["max_file_bytes"] if policy else MAX_FILE_BYTES
    roles = []
    ids = set()
    for role in value["roles"]:
        fields = {"role_id", "kind", "required", "allowed_mime", "min_count", "max_count", "max_bytes"}
        if not isinstance(role, dict) or set(role) != fields or not isinstance(role["role_id"], str) or not SAFE_ID.fullmatch(role["role_id"]) or role["role_id"] in ids:
            raise HTTPException(422, {"code": "creative_output_role_invalid"})
        if not isinstance(role["kind"], str) or role["kind"] not in {"image", "video", "audio", "other"} or type(role["required"]) is not bool:
            raise HTTPException(422, {"code": "creative_output_kind_invalid"})
        lo, hi, size = role["min_count"], role["max_count"], role["max_bytes"]
        if any(type(item) is not int for item in (lo, hi, size)) or not 0 <= lo <= hi <= 20 or hi < 1 or not 1 <= size <= maximum or (role["required"] and lo < 1) or (not role["required"] and lo != 0):
            raise HTTPException(422, {"code": "creative_output_counts_invalid"})
        mimes = role["allowed_mime"]
        if not isinstance(mimes, list) or not 1 <= len(mimes) <= 10 or any(not isinstance(mime, str) or not re.fullmatch(r"[a-z0-9.+-]+/[a-z0-9.+-]+", mime) for mime in mimes) or len(set(mimes)) != len(mimes):
            raise HTTPException(422, {"code": "creative_output_mime_invalid"})
        prefix = {"image": "image/", "audio": "audio/", "video": "video/"}.get(role["kind"])
        if prefix and any(not mime.startswith(prefix) for mime in mimes):
            raise HTTPException(422, {"code": "creative_output_kind_mime_mismatch"})
        ids.add(role["role_id"])
        roles.append({**role, "allowed_mime": sorted(mimes)})
    if not any(role["required"] for role in roles):
        raise HTTPException(422, {"code": "creative_required_output_missing"})
    return {"roles": sorted(roles, key=lambda item: item["role_id"]), **({"media_transfer_policy": dict(policy)} if policy else {})}
