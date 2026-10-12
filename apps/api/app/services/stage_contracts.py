"""Bounded, version-pinned controls; no implicit interpretation of legacy config."""

import hashlib
import json
import math
import re
from copy import deepcopy
from dataclasses import dataclass

from .creative_intents import contains_secret_text

IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,149}\Z")
FORBIDDEN_FIELDS = frozenset({
    "plugin", "plugin_version", "stage_schema", "depends_on", "edges", "input_mapping", "output_mapping",
    "condition", "failure_policy", "side_effect", "human_gate", "requires_human_acceptance",
    "approval", "publication", "rights", "fact_boundary", "fact_boundary_revision_id",
})
SECRET_FIELDS = frozenset({
    "api_key", "api_secret", "access_token", "refresh_token", "authorization", "cookie", "password",
    "client_secret", "secret", "raw_output", "raw_response", "provider_error",
})


class StageContractError(ValueError):
    pass


def canonical(value, *, max_bytes=128 * 1024):
    def visit(item, depth=0):
        if depth > 12:
            raise StageContractError("stage_value_too_deep")
        if type(item) is dict:
            if len(item) > 128:
                raise StageContractError("stage_value_too_large")
            for key, child in item.items():
                if type(key) is not str or len(key) > 150 or key.lower() in SECRET_FIELDS:
                    raise StageContractError("stage_unsafe_field")
                if contains_secret_text(key):
                    raise StageContractError("stage_secret_forbidden")
                visit(child, depth + 1)
        elif type(item) is list:
            if len(item) > 256:
                raise StageContractError("stage_value_too_large")
            for child in item:
                visit(child, depth + 1)
        elif type(item) is str:
            if contains_secret_text(item) or any(ord(char) < 32 and char not in "\n\r\t" for char in item):
                raise StageContractError("stage_secret_or_control_forbidden")
        elif type(item) not in {int, float, bool, type(None)} or type(item) is float and not math.isfinite(item):
            raise StageContractError("stage_json_invalid")
    visit(value)
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    if len(encoded.encode()) > max_bytes:
        raise StageContractError("stage_value_too_large")
    return json.loads(encoded)


def digest(value):
    return hashlib.sha256(json.dumps(canonical(value), ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def _schema(schema, depth=0):
    if type(schema) is not dict or depth > 6:
        raise StageContractError("stage_config_schema_invalid")
    kind = schema.get("type")
    if type(kind) is not str:
        raise StageContractError("stage_config_schema_invalid")
    allowed = {"type", "default", "enum", "description"}
    if kind == "object":
        allowed |= {"properties", "required", "additionalProperties"}
        properties, required = schema.get("properties"), schema.get("required", [])
        if (schema.get("additionalProperties") is not False or type(properties) is not dict or len(properties) > 32
                or type(required) is not list or any(type(key) is not str for key in required)
                or len(set(required)) != len(required) or set(required) - set(properties)):
            raise StageContractError("stage_config_schema_invalid")
        for key, child in properties.items():
            if type(key) is not str or not IDENTIFIER.fullmatch(key) or key in FORBIDDEN_FIELDS:
                raise StageContractError("stage_prohibited_field")
            _schema(child, depth + 1)
    elif kind == "string":
        allowed |= {"minLength", "maxLength"}
        if (type(schema.get("maxLength")) is not int or not 1 <= schema["maxLength"] <= 16000
                or type(schema.get("minLength", 0)) is not int
                or not 0 <= schema.get("minLength", 0) <= schema["maxLength"]):
            raise StageContractError("stage_config_schema_unbounded")
    elif kind in {"integer", "number"}:
        allowed |= {"minimum", "maximum"}
        if any(type(schema.get(key)) not in {int, float} or not math.isfinite(schema[key])
               for key in ("minimum", "maximum")) or schema["minimum"] > schema["maximum"]:
            raise StageContractError("stage_config_schema_unbounded")
    elif kind == "array":
        allowed |= {"items", "minItems", "maxItems"}
        if (type(schema.get("maxItems")) is not int or not 0 <= schema["maxItems"] <= 50
                or type(schema.get("minItems", 0)) is not int
                or not 0 <= schema.get("minItems", 0) <= schema["maxItems"]):
            raise StageContractError("stage_config_schema_unbounded")
        _schema(schema.get("items"), depth + 1)
    elif kind != "boolean":
        raise StageContractError("stage_config_schema_invalid")
    if set(schema) - allowed:
        raise StageContractError("stage_config_schema_keyword_unsupported")
    if "enum" in schema:
        if type(schema["enum"]) is not list or not 1 <= len(schema["enum"]) <= 30:
            raise StageContractError("stage_config_schema_invalid")
        for value in schema["enum"]:
            _validate(value, {key: value for key, value in schema.items() if key not in {"enum", "default"}})
    if "default" in schema:
        _validate(schema["default"], schema)


def _validate(value, schema):
    kind = schema["type"]
    valid_type = {
        "object": type(value) is dict, "array": type(value) is list, "string": type(value) is str,
        "boolean": type(value) is bool, "integer": type(value) is int, "number": type(value) in {int, float},
    }[kind]
    if not valid_type:
        raise StageContractError("stage_config_type_invalid")
    if "enum" in schema and not any(type(value) is type(item) and value == item for item in schema["enum"]):
        raise StageContractError("stage_config_enum_invalid")
    if kind == "object":
        properties = schema["properties"]
        if set(value) - set(properties):
            raise StageContractError("stage_config_unknown_field")
        result = deepcopy(value)
        for key, child in properties.items():
            if key not in result and "default" in child:
                result[key] = deepcopy(child["default"])
        if set(schema.get("required", [])) - set(result):
            raise StageContractError("stage_config_required_field_missing")
        return {key: _validate(child, properties[key]) for key, child in result.items()}
    if kind == "array":
        if not schema.get("minItems", 0) <= len(value) <= schema["maxItems"]:
            raise StageContractError("stage_config_limit_invalid")
        return [_validate(child, schema["items"]) for child in value]
    if kind == "string" and not schema.get("minLength", 0) <= len(value) <= schema["maxLength"]:
        raise StageContractError("stage_config_limit_invalid")
    if kind in {"integer", "number"} and not schema["minimum"] <= value <= schema["maximum"]:
        raise StageContractError("stage_config_limit_invalid")
    return value


@dataclass(frozen=True)
class StageContract:
    _json: str

    @classmethod
    def from_dict(cls, value, *, consumed_fields):
        value = canonical(value, max_bytes=32 * 1024)
        fields = {
            "stage_schema", "title", "category", "config_schema", "ui_schema", "tunable_fields",
            "input_contract", "output_contract", "method_sources", "supports_preview", "supports_run_override",
            "supports_candidates", "requires_human_acceptance",
        }
        if type(value) is not dict or set(value) != fields:
            raise StageContractError("stage_contract_fields_invalid")
        if (type(value["stage_schema"]) is not str or not IDENTIFIER.fullmatch(value["stage_schema"])
                or type(value["title"]) is not str or not 1 <= len(value["title"]) <= 200
                or type(value["category"]) is not str
                or value["category"] not in {"Data", "AI", "Tool", "Rule", "Human", "System"}):
            raise StageContractError("stage_contract_identity_invalid")
        _schema(value["config_schema"])
        if value["config_schema"]["type"] != "object":
            raise StageContractError("stage_config_schema_invalid")
        properties, tunable = value["config_schema"]["properties"], value["tunable_fields"]
        if (type(tunable) is not list or any(type(key) is not str for key in tunable)
                or len(set(tunable)) != len(tunable) or set(tunable) - set(properties)
                or not isinstance(consumed_fields, (set, frozenset, tuple)) or set(properties) - set(consumed_fields)):
            raise StageContractError("stage_executor_unconsumed_field")
        ui = value["ui_schema"]
        if type(ui) is not dict or set(ui) - set(tunable):
            raise StageContractError("stage_ui_field_not_tunable")
        controls = {"textarea": {"string"}, "text": {"string"}, "number": {"integer", "number"},
                    "select": {"string", "integer"}, "toggle": {"boolean"}, "method": {"object"}}
        for key, item in ui.items():
            if (type(item) is not dict or set(item) != {"control", "label"}
                    or type(item.get("control")) is not str or item["control"] not in controls
                    or properties[key]["type"] not in controls[item["control"]]
                    or type(item.get("label")) is not str or not 1 <= len(item["label"]) <= 100):
                raise StageContractError("stage_ui_schema_invalid")
        for key in ("supports_preview", "supports_run_override", "supports_candidates", "requires_human_acceptance"):
            if type(value[key]) is not bool:
                raise StageContractError("stage_contract_flag_invalid")
        for key in ("input_contract", "output_contract"):
            if type(value[key]) is not dict:
                raise StageContractError("stage_contract_io_invalid")
        inputs = value["input_contract"]
        required = inputs.get("required_context", [])
        if (set(inputs) - {"required_context", "upstream"} or type(required) is not list
                or any(type(key) is not str or key not in {"identity", "brief", "boundary", "master", "intent"}
                       for key in required) or type(inputs.get("upstream", "accepted")) is not str
                or inputs.get("upstream", "accepted") not in {"accepted", "output"}):
            raise StageContractError("stage_contract_input_invalid")
        sources = value["method_sources"]
        if (type(sources) is not list or any(type(key) is not str or key not in {
                "builtin", "studio_builtin", "capability_memory", "installed_agent_skill", "creative_execution"} for key in sources)
                or len(set(sources)) != len(sources)):
            raise StageContractError("stage_method_sources_invalid")
        return cls(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))

    def to_dict(self):
        return json.loads(self._json)

    def validate_config(self, value):
        return _validate(canonical(value, max_bytes=32 * 1024), self.to_dict()["config_schema"])

    def effective_config(self, base, override):
        contract = self.to_dict()
        base = self.validate_config(base)
        override = canonical(override, max_bytes=32 * 1024)
        if (type(override) is not dict or set(override) - set(contract["tunable_fields"])
                or override and not contract["supports_run_override"]):
            raise StageContractError("stage_override_not_supported")
        return base, self.validate_config({**base, **override}), override
