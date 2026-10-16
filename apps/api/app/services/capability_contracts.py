"""Bounded, non-executable reusable-method documents and deterministic rendering."""

import hashlib
import json
import math
import re
import unicodedata
from urllib.parse import unquote

from fastapi import HTTPException

from .creative_intents import _RAW_TRUTH_TEXT, _SENSITIVE_TEXT

KINDS = {"prompt_skill", "recipe", "creative_pattern", "preference", "execution_template", "tool"}
STATUSES = {"candidate", "saved", "pinned", "archived", "deprecated"}
SCOPES = {"owner", "persona", "account", "series", "project", "channel", "executor"}
OUTCOMES = {"used", "accepted", "rejected", "unknown"}
MAX_BYTES = 64 * 1024
MAX_STRING = 8192
ARG_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,63}\Z")
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]*\Z")
PLACEHOLDER = re.compile(r"\{\{([^{}]*)\}\}")
_FORBIDDEN = {
    "api_key", "apikey", "access_token", "refresh_token", "client_secret", "secret", "password",
    "authorization", "cookie", "token", "credential", "credentials", "private_key", "signed_url",
    "raw_output", "raw_error", "raw_response", "raw_payload", "raw_text", "raw_provider_payload",
    "provider_payload", "provider_response", "provider_output", "source_body", "source_text",
    "full_source", "full_source_body", "full_source_text", "private_evidence", "raw_evidence",
    "identity_snapshot", "identity_profile", "fact_pack", "fact_pack_items", "messages", "choices",
    "absolute_path", "local_path", "file_path", "code", "script", "shell", "command", "argv",
    "eval", "exec", "execute", "sql", "pickle", "__proto__", "__class__", "__globals__",
}
_FORBIDDEN_COMPACT = {name.replace("_", "") for name in _FORBIDDEN}
_CREDENTIAL_TEXT = re.compile(
    r"AIza[A-Za-z0-9_-]{35}|(?:sk|rk)_(?:live|test)_[A-Za-z0-9]{24,}"
)
_UNSAFE_TEXT = re.compile(
    r"[?&](?:x-amz-[a-z-]+|x-goog-[a-z-]+|awsaccesskeyid|googleaccessid|ossaccesskeyid"
    r"|credential|auth|authorization|cookie|access_token|refresh_token|client_secret|expires|se|sp|sv|sastoken)="
    r"|(?:file|javascript|data|vbscript)\s*:|<\s*(?:script|iframe|object)\b|\bon[a-z]+\s*="
    r"|\b(?:eval|exec|compile|__import__)\s*\(|\$\(|```(?:python|javascript|bash|sh|powershell)\b"
    r"|(?:^|[\s\"'=])/(?:Users|home|etc|private|tmp|var)/|[A-Za-z]:[\\/]",
    re.IGNORECASE,
)


def error(code, status=422):
    return HTTPException(status, {"code": code})


def positive_id(value):
    if type(value) is not int or not 0 < value < 2**53:
        raise error("capability_reference_invalid")
    return value


def fields(data, allowed):
    if type(data) is not dict or set(data) - set(allowed):
        raise error("capability_fields_invalid")
    return data


def text(value, maximum=MAX_STRING, *, required=False):
    if type(value) is not str:
        raise error("capability_text_invalid")
    result = unicodedata.normalize("NFC", value)
    try:
        size = len(result.encode("utf-8"))
    except UnicodeError:
        raise error("capability_text_invalid") from None
    if size > maximum or required and not result.strip():
        raise error("capability_text_bounds")
    if any(ord(char) < 32 and char not in "\n\r\t" for char in result):
        raise error("capability_text_invalid")
    scanned = unicodedata.normalize("NFKC", result)
    for _ in range(3):
        scanned = unquote(scanned)
    if (_SENSITIVE_TEXT.search(scanned) or _CREDENTIAL_TEXT.search(scanned)
            or _RAW_TRUTH_TEXT.search(scanned) or _UNSAFE_TEXT.search(scanned)):
        raise error("capability_unsafe_payload")
    return result


def canonical(value, *, max_bytes=MAX_BYTES):
    nodes = 0

    def normalize(item, depth):
        nonlocal nodes
        nodes += 1
        if depth > 12 or nodes > 4000:
            raise error("capability_json_bounds")
        if type(item) is dict:
            if len(item) > 100:
                raise error("capability_json_bounds")
            result = {}
            for key, child in item.items():
                key = text(key, 100)
                if key in result:
                    raise error("capability_normalization_key_collision")
                normalized = unicodedata.normalize("NFKC", key).lower().replace("-", "_").replace(" ", "_")
                compact = normalized.replace("_", "")
                if (normalized in _FORBIDDEN or normalized.startswith(("$", "raw_", "full_source_"))
                        or compact in _FORBIDDEN_COMPACT
                        or compact.startswith(("rawsource", "rawprovider", "fullsource"))):
                    raise error("capability_unsafe_payload")
                result[key] = normalize(child, depth + 1)
            return result
        elif type(item) is list:
            if len(item) > 100:
                raise error("capability_json_bounds")
            return [normalize(child, depth + 1) for child in item]
        elif type(item) is str:
            return text(item)
        elif type(item) in {int, float}:
            if abs(item) > 2**53 or type(item) is float and not math.isfinite(item):
                raise error("capability_number_invalid")
        elif item is not None and type(item) is not bool:
            raise error("capability_json_invalid")
        return item

    value = normalize(value, 0)
    try:
        raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    except (TypeError, ValueError, UnicodeError, RecursionError):
        raise error("capability_json_invalid") from None
    if len(raw) > max_bytes:
        raise error("capability_json_bounds")
    return json.loads(raw)


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def args_schema(value):
    value = canonical(value)
    fields(value, {"type", "properties", "required", "additionalProperties", "description"})
    if value.get("type", "object") != "object" or value.get("additionalProperties", False) is not False:
        raise error("capability_args_schema_invalid")
    if "description" in value:
        text(value["description"], 2000)
    props = value.get("properties", {})
    required = value.get("required", [])
    if (type(props) is not dict or len(props) > 30 or type(required) is not list
            or any(type(name) is not str for name in required) or len(set(required)) != len(required)
            or set(required) - set(props)):
        raise error("capability_args_schema_invalid")
    for name, spec in props.items():
        if not ARG_NAME.fullmatch(name):
            raise error("capability_argument_name_invalid")
        fields(spec, {"type", "enum", "description", "minLength", "maxLength", "minimum", "maximum"})
        kind = spec.get("type")
        if type(kind) is not str or kind not in {"string", "number", "integer", "boolean"}:
            raise error("capability_argument_type_invalid")
        if "description" in spec:
            text(spec["description"], 2000)
        if kind == "string":
            if "minimum" in spec or "maximum" in spec:
                raise error("capability_args_schema_invalid")
            low, high = spec.get("minLength", 0), spec.get("maxLength", MAX_STRING)
            if type(low) is not int or type(high) is not int or not 0 <= low <= high <= MAX_STRING:
                raise error("capability_args_schema_invalid")
        elif "minLength" in spec or "maxLength" in spec:
            raise error("capability_args_schema_invalid")
        if kind == "boolean" and ("minimum" in spec or "maximum" in spec):
            raise error("capability_args_schema_invalid")
        for key in ("minimum", "maximum"):
            if key in spec and type(spec[key]) not in {int, float}:
                raise error("capability_args_schema_invalid")
        if "minimum" in spec and "maximum" in spec and spec["minimum"] > spec["maximum"]:
            raise error("capability_args_schema_invalid")
        if "enum" in spec:
            enum = spec["enum"]
            if type(enum) is not list or not 1 <= len(enum) <= 50:
                raise error("capability_args_schema_invalid")
            for member in enum:
                validate_argument(member, {k: v for k, v in spec.items() if k != "enum"})
    return {**value, "type": "object", "properties": props, "required": sorted(required), "additionalProperties": False}


def validate_argument(value, spec):
    kind = spec["type"]
    if (kind == "string" and type(value) is not str or kind == "boolean" and type(value) is not bool
            or kind == "integer" and type(value) is not int
            or kind == "number" and type(value) not in {int, float}):
        raise error("capability_argument_type_invalid")
    if kind == "string":
        text(value)
        if not spec.get("minLength", 0) <= len(value) <= spec.get("maxLength", MAX_STRING):
            raise error("capability_argument_bounds")
    if kind in {"integer", "number"} and (
        abs(value) > 2**53 or type(value) is float and not math.isfinite(value)
        or "minimum" in spec and value < spec["minimum"] or "maximum" in spec and value > spec["maximum"]
    ):
        raise error("capability_argument_bounds")
    if "enum" in spec and not any(type(value) is type(item) and value == item for item in spec["enum"]):
        raise error("capability_argument_enum_invalid")


def reference_style(content):
    fields(content, {"content_schema", "text", "tags", "observations"})
    text(content.get("text"), required=True)
    observations = content.get("observations")
    if type(observations) is not list or len(observations) > 100:
        raise error("reference_style_observations_invalid")
    for observation in observations:
        if type(observation) is not dict:
            raise error("reference_style_observation_invalid")
        fields(observation, {"modality", "certainty", "statement", "reference", "locator"})
        modality = observation.get("modality")
        if (type(modality) is not str or modality not in {"text", "image", "video"}
                or type(observation.get("certainty")) is not str
                or observation["certainty"] not in {"direct", "inferred", "unknown"}):
            raise error("reference_style_observation_invalid")
        text(observation.get("statement"), 2048, required=True)
        text(observation.get("locator"), 2048, required=True)
        reference = observation.get("reference")
        if type(reference) is not dict:
            raise error("reference_style_reference_invalid")
        fields(reference, {"kind", "id", "content_hash"})
        if type(reference.get("kind")) is not str or reference["kind"] not in {"material_revision", "source"}:
            raise error("reference_style_reference_invalid")
        positive_id(reference.get("id"))
        if not re.fullmatch(r"[0-9a-f]{64}", text(reference.get("content_hash"), 64, required=True)):
            raise error("reference_style_reference_invalid")


def artifact(kind, content, schema):
    if type(kind) is not str or kind not in KINDS or type(content) is not dict or not content:
        raise error("capability_artifact_invalid")
    content = canonical(content)
    if content.get("content_schema") == "workflow.stage.recipe.v1":
        from .workflow_stage_recipes import validate_recipe

        if kind != "recipe":
            raise error("workflow_stage_recipe_kind_invalid")
        try:
            validate_recipe(content)
        except ValueError:
            raise error("workflow_stage_recipe_invalid") from None
    if content.get("content_schema") == "persona.reference-style.v1":
        if kind != "creative_pattern":
            raise error("reference_style_kind_invalid")
        reference_style(content)
    targets = content.get("execution_targets")
    if targets is not None and (type(targets) is not list or not targets or len(targets) > 2
            or any(type(target) is not str or target not in {"ai_planning", "external_executor"} for target in targets)
            or len(set(targets)) != len(targets)):
        raise error("capability_execution_targets_invalid")
    schema = args_schema(schema)
    tags = content.get("tags", [])
    if type(tags) is not list or len(tags) > 30 or any(type(tag) is not str or not tag.strip() for tag in tags):
        raise error("capability_tags_invalid")
    for tag in tags:
        text(tag, 100)
    def scan(item):
        if isinstance(item, str):
            for match in PLACEHOLDER.finditer(item):
                if not ARG_NAME.fullmatch(match[1]) or match[1] not in schema["properties"]:
                    raise error("capability_template_argument_invalid")
        elif isinstance(item, (dict, list)):
            for child in item.values() if isinstance(item, dict) else item:
                scan(child)
    scan(content)
    payload = canonical({"kind": kind, "content": content, "args_schema": schema})
    return content, schema, digest(payload)


def render(content, schema, arguments):
    arguments = canonical(arguments)
    if type(arguments) is not dict or set(arguments) - set(schema["properties"]) or set(schema["required"]) - set(arguments):
        raise error("capability_arguments_invalid")
    for name, value in arguments.items():
        validate_argument(value, schema["properties"][name])
    def substitute(item):
        if type(item) is str:
            def replace(match):
                if match[1] not in arguments:
                    raise error("capability_template_argument_missing")
                value = arguments[match[1]]
                return value if type(value) is str else json.dumps(value, allow_nan=False)
            return text(PLACEHOLDER.sub(replace, item))
        if type(item) is list:
            return [substitute(child) for child in item]
        if type(item) is dict:
            return {key: substitute(child) for key, child in item.items()}
        return item
    # Validate the complete response before recording a use; MCP cannot fail after commit on size.
    rendered = canonical(substitute(content))
    return rendered, digest(arguments)
