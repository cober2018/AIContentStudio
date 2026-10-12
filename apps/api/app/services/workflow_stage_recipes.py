"""Reusable bounded config patches, never a second Workflow definition."""

import re

from .stage_contracts import IDENTIFIER, canonical

SCHEMA = "workflow.stage.recipe.v1"


def validate_recipe(content):
    content = canonical(content, max_bytes=32 * 1024)
    required = {"content_schema", "base_workflow_checksum", "node_id", "plugin", "plugin_version",
                "stage_schema", "config_patch", "feedback_evidence", "attempt_evidence"}
    if (type(content) is not dict or set(content) - required - {"instruction", "tags"}
            or required - set(content) or content["content_schema"] != SCHEMA
            or type(content["base_workflow_checksum"]) is not str
            or not re.fullmatch(r"[a-f0-9]{64}", content["base_workflow_checksum"])):
        raise ValueError("workflow_stage_recipe_invalid")
    for key in ("node_id", "plugin", "plugin_version", "stage_schema"):
        if type(content[key]) is not str or not IDENTIFIER.fullmatch(content[key]):
            raise ValueError("workflow_stage_recipe_identity_invalid")
    from .content_harness.registry import RegistryError, registry
    try:
        descriptor = registry.descriptor("node", content["plugin"], content["plugin_version"])
    except RegistryError:
        raise ValueError("workflow_stage_recipe_contract_unavailable") from None
    contract = descriptor.stage_contract
    if contract is None or contract.to_dict()["stage_schema"] != content["stage_schema"]:
        raise ValueError("workflow_stage_recipe_contract_unavailable")
    patch = content["config_patch"]
    if (type(patch) is not dict or not patch or set(patch) - set(contract.to_dict()["tunable_fields"])
            or any(key in patch for key in ("plugin", "depends_on", "human_gate", "side_effect", "rights"))):
        raise ValueError("workflow_stage_recipe_patch_invalid")
    from .stage_contracts import _validate
    for key, value in patch.items():
        _validate(value, contract.to_dict()["config_schema"]["properties"][key])
    refs = content["feedback_evidence"]
    if (type(refs) is not list or not 1 <= len(refs) <= 20 or any(type(ref) is not dict
            or set(ref) != {"event_id", "event_hash"} or type(ref["event_id"]) is not int
            or ref["event_id"] <= 0 or type(ref["event_hash"]) is not str
            or not re.fullmatch(r"[a-f0-9]{64}", ref["event_hash"]) for ref in refs)):
        raise ValueError("workflow_stage_recipe_feedback_invalid")
    attempts = content["attempt_evidence"]
    fields = {"attempt_id", "resolution_hash", "config_hash", "prompt_hash", "output_hash", "accepted_hash"}
    if (type(attempts) is not list or not 1 <= len(attempts) <= 20
            or any(type(item) is not dict or set(item) != fields
                   or type(item["attempt_id"]) is not int or item["attempt_id"] <= 0
                   or any(type(item[key]) is not str or not re.fullmatch(r"[a-f0-9]{64}", item[key])
                          for key in fields - {"attempt_id"}) for item in attempts)):
        raise ValueError("workflow_stage_recipe_attempt_invalid")
    return content


def deterministic_recipe(content, node):
    recipe = validate_recipe(content)
    if (recipe["plugin"] != node.get("plugin")
            or recipe["plugin_version"] != str(node.get("plugin_version"))
            or recipe["stage_schema"] != node.get("stage_schema")):
        raise ValueError("deterministic_stage_method_parameters_required")
    # A composed extension supplies parameters, never a new executor or base method.
    selectors = {"method", "output_schema", "package_schema", "model_profile_id", "selected_profile", "explicit_plugin"}
    if selectors.intersection(recipe["config_patch"]):
        raise ValueError("deterministic_stage_method_parameters_invalid")
    return recipe
