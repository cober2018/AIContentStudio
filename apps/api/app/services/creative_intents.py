"""Bounded creative decisions stored alongside immutable content revisions."""

import hashlib
import json
import re
import unicodedata
from urllib.parse import unquote

INTENT_SCHEMA = "creative.intent.v1"
MAX_INTENT_BYTES = 64 * 1024
_TEXT_FIELDS = (
    "objective", "why_now", "audience", "creative_freedom",
    "narrative_intent", "visual_intent", "audio_intent",
)
_CONSTRAINT_FIELDS = ("must_keep", "must_avoid")
_ENTRY_FIELDS = {
    "rationales": ("stable_id", "reason", 100),
    "human_confirmed_decisions": ("id", "decision", 50),
}
_FIELDS = {"schema", *_TEXT_FIELDS, *_CONSTRAINT_FIELDS, *_ENTRY_FIELDS}
_STABLE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,99}\Z")
_SENSITIVE_TEXT = re.compile(
    r"(?:\bbearer\s+\S+|\b(?:sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9_]{12,}"
    r"|github_pat_[A-Za-z0-9_]{12,}|xox[baprs]-[A-Za-z0-9-]{12,}"
    r"|(?:AKIA|ASIA)[A-Z0-9]{16}|AIza[A-Za-z0-9_-]{35}"
    r"|(?:sk|rk)_(?:live|test)_[A-Za-z0-9]{24,})\b|-----BEGIN [A-Z ]*PRIVATE KEY-----"
    r"|\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"
    r"|\b(?:api[ _-]?(?:key|secret)|access[ _-]?token|refresh[ _-]?token|client[ _-]?secret"
    r"|token|secret|password|authorization|cookie)\s*(?:[\"']\s*)?[=:]\s*\S+"
    r"|(?<![a-z0-9+.-])[a-z][a-z0-9+.-]*://[^\s/:]+:[^\s/@]*@"
    r"|[?&](?:token|key|api_key|secret|password|signature|sig|x-amz-[a-z-]+|x-goog-[a-z-]+"
    r"|awsaccesskeyid|googleaccessid|ossaccesskeyid|credential|auth|authorization|cookie"
    r"|access_token|refresh_token|client_secret|expires|se|sp|sv|sastoken)=[^\s&#]+)",
    re.IGNORECASE,
)
_RAW_TRUTH_TEXT = re.compile(
    r'["\'](?:raw[ _-]?(?:provider(?:[ _-]?(?:payload|output|response))?|output|response|payload|text)'
    r'|provider[ _-]?(?:payload|response|output)|full[ _-]?source(?:[ _-]?(?:body|text))?'
    r'|source[ _-]?(?:body|text)|identity(?:[ _-]?(?:profile|snapshot|json))?'
    r'|fact[ _-]?pack(?:[ _-]?(?:facts|items))?|choices|messages)["\']\s*:',
    re.IGNORECASE,
)


class CreativeIntentError(ValueError):
    pass


def contains_secret_text(value: str) -> bool:
    # Scan encoded credentials without changing the stored content or its canonical hash.
    scanned = unicodedata.normalize("NFKC", value)
    for _ in range(3):
        decoded = unicodedata.normalize("NFKC", unquote(scanned))
        if decoded == scanned:
            break
        scanned = decoded
    return bool(_SENSITIVE_TEXT.search(scanned))


def _text(value: object, limit: int, *, required: bool = False) -> str:
    if type(value) is not str or len(value) > limit:
        raise CreativeIntentError("creative_intent_invalid_text")
    result = unicodedata.normalize("NFC", value).strip()
    if len(result) > limit or (required and not result):
        raise CreativeIntentError("creative_intent_invalid_text")
    if any(ord(char) < 32 and char not in "\n\r\t" for char in result):
        raise CreativeIntentError("creative_intent_invalid_text")
    if contains_secret_text(result):
        raise CreativeIntentError("creative_intent_secret_forbidden")
    if result.startswith(("{", "[")) or _RAW_TRUTH_TEXT.search(result):
        raise CreativeIntentError("creative_intent_raw_truth_forbidden")
    return result


def _entries(value: object, id_key: str, text_key: str, limit: int) -> list[dict]:
    if type(value) is not list or len(value) > limit:
        raise CreativeIntentError("creative_intent_invalid_entries")
    result = []
    seen = set()
    for entry in value:
        if type(entry) is not dict or set(entry) != {id_key, text_key}:
            raise CreativeIntentError("creative_intent_invalid_entry")
        stable_id = entry[id_key]
        if type(stable_id) is not str or not _STABLE_ID.fullmatch(stable_id):
            raise CreativeIntentError("creative_intent_invalid_stable_id")
        if stable_id in seen:
            raise CreativeIntentError("creative_intent_duplicate_stable_id")
        seen.add(stable_id)
        result.append({id_key: _text(stable_id, 100, required=True),
                       text_key: _text(entry[text_key], 1000, required=True)})
    return sorted(result, key=lambda entry: entry[id_key])


def canonical_intent(value: object) -> tuple[dict | None, str | None]:
    if value is None:
        return None, None
    if type(value) is not dict or not set(value) <= _FIELDS:
        raise CreativeIntentError("creative_intent_invalid_shape")
    if value.get("schema") != INTENT_SCHEMA:
        raise CreativeIntentError("creative_intent_schema_invalid")
    canonical = {"schema": INTENT_SCHEMA}
    for field in _TEXT_FIELDS:
        canonical[field] = _text(value.get(field, ""), 2000)
    for field in _CONSTRAINT_FIELDS:
        items = value.get(field, [])
        if type(items) is not list or len(items) > 40:
            raise CreativeIntentError("creative_intent_invalid_constraints")
        canonical[field] = [_text(item, 500, required=True) for item in items]
    for field, (id_key, text_key, limit) in _ENTRY_FIELDS.items():
        canonical[field] = _entries(value.get(field, []), id_key, text_key, limit)
    try:
        encoded = json.dumps(canonical, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise CreativeIntentError("creative_intent_invalid_json") from exc
    if len(encoded) > MAX_INTENT_BYTES:
        raise CreativeIntentError("creative_intent_too_large")
    return canonical, hashlib.sha256(encoded).hexdigest()


def intent_diff(before: object, after: object) -> dict:
    previous, previous_hash = canonical_intent(before)
    current, current_hash = canonical_intent(after)
    fields = sorted(field for field in _FIELDS if (previous or {}).get(field) != (current or {}).get(field))
    entries = {}
    for field, (id_key, _, _) in _ENTRY_FIELDS.items():
        old = {entry[id_key]: entry for entry in (previous or {}).get(field, [])}
        new = {entry[id_key]: entry for entry in (current or {}).get(field, [])}
        entries[field] = {"added": sorted(new.keys() - old.keys()), "removed": sorted(old.keys() - new.keys()),
                          "changed": sorted(key for key in old.keys() & new.keys() if old[key] != new[key])}
    return {"changed": previous_hash != current_hash, "before": previous, "after": current,
            "before_hash": previous_hash, "after_hash": current_hash, "changed_fields": fields, **entries}
