"""Bounded optional tuning suggestions; accepted patches still require versioned save."""

import asyncio

from sqlalchemy import select

from ..models import LLMRun, ProjectEvent
from . import creation_recipes
from .content_masters import owned_unit
from .generation.providers import (
    GenerateRequest,
    MockProvider,
    OpenAICompatibleProvider,
    effective_llm_config,
    input_hash,
)
from .project_authorization import lock_project_context
from .stage_contracts import IDENTIFIER, canonical, digest
from .stage_feedback import attempt_context
from .stage_invocations import StageInvocationError

PROMPT_VERSION = "stage.recipe.tune.v1"


def _input(db, project_id, unit_id, node_id, user, request):
    _, _unit, workflow, _ = creation_recipes._workflow(db, project_id, unit_id, user)
    if workflow is None:
        raise StageInvocationError("recipe_workflow_required")
    node = next((item for item in workflow.definition_json["nodes"] if item["id"] == node_id), None)
    descriptor = creation_recipes._descriptor(node) if node else None
    if descriptor is None or descriptor.stage_contract is None:
        raise StageInvocationError("recipe_stage_contract_required")
    ids = request.get("feedback_event_ids")
    if (type(ids) is not list or not 1 <= len(ids) <= 20
            or any(type(value) is not int or value <= 0 for value in ids) or len(set(ids)) != len(ids)):
        raise StageInvocationError("recipe_tuning_feedback_required", status_code=422)
    evidence = []
    for event_id in ids:
        event = db.get(ProjectEvent, event_id)
        payload = event.payload_json or {} if event else {}
        if (event is None or event.project_id != project_id or event.event_type != "creation_recipe.stage_feedback"
                or payload.get("unit_id") != unit_id or payload.get("node_id") != node_id):
            raise StageInvocationError("recipe_tuning_feedback_not_found", status_code=404)
        _, _, _, _, attempt, resolved = attempt_context(db, project_id, unit_id, node_id, user,
            {"run_id": payload["run_id"], "attempt_id": payload["attempt_id"]})
        if (resolved["node"]["plugin"] != node["plugin"] or resolved["node"]["plugin_version"] != node["plugin_version"]
                or resolved["node"]["stage_schema"] != node["stage_schema"]):
            raise StageInvocationError("recipe_tuning_contract_changed")
        evidence.append({"event_id": event.id, "event_hash": digest(payload), "attempt_id": attempt.id,
            "decision": payload["decision"], "note": payload.get("note", ""), "reason_tags": payload.get("reason_tags", []),
            "config_hash": payload["config_hash"], "prompt_hash": payload["prompt_hash"],
            "output_hash": payload["output_hash"], "accepted_hash": payload.get("accepted_hash"),
            "base_config": resolved["base_config"], "effective_config": resolved["effective_config"]})
    model, blockers = creation_recipes._model({})
    if blockers:
        raise StageInvocationError("recipe_tuning_model_unavailable")
    metadata = descriptor.stage_contract.to_dict()
    projection = canonical({"project_id": project_id, "unit_id": unit_id, "owner_id": user.id,
        "node_id": node_id, "workflow_id": workflow.id, "workflow_checksum": workflow.checksum,
        "stage_contract_hash": digest(metadata), "base_config": descriptor.stage_contract.validate_config(node.get("config") or {}),
        "tunable_schema": {key: metadata["config_schema"]["properties"][key] for key in metadata["tunable_fields"]},
        "feedback": evidence, "model": model})
    return descriptor.stage_contract, projection


def _request(projection, key):
    import json

    return GenerateRequest(purpose="generate", channel=None,
        system_prompt="Suggest only a bounded config_patch using tunable_schema fields and explanation. "
                      "No graph, plugin, mapping, rights, evidence, approval or publication changes. Do not copy content.",
        user_prompt=json.dumps({"invocation_key": key, **projection}, ensure_ascii=False, sort_keys=True),
        schema_hint="creation_recipe.tuning.v1", context={"stage_schema": "creation_recipe.tuning.v1",
            "base_config": projection["base_config"], "tunable_schema": projection["tunable_schema"]})


def tuning_suggestion(db, project_id, unit_id, node_id, user, request):
    request = canonical(request, max_bytes=16 * 1024)
    key = request.get("invocation_key")
    if type(key) is not str or not IDENTIFIER.fullmatch(key):
        raise StageInvocationError("recipe_tuning_invocation_required", status_code=422)
    lock_project_context(db, project_id, user)
    owned_unit(db, project_id, unit_id, user, mutate=True)
    if not user.is_active or user.role not in {"editor", "admin"}:
        raise StageInvocationError("recipe_readonly", status_code=403)
    fingerprint = digest({"request": request, "owner_id": user.id, "project_id": project_id, "unit_id": unit_id, "node_id": node_id})
    for row in db.scalars(select(LLMRun).where(LLMRun.prompt_version == PROMPT_VERSION).order_by(LLMRun.id.desc())):
        data = row.parsed_output_json or {}
        identity = data.get("claim") or {}
        if identity.get("owner_id") == user.id and identity.get("invocation_key") == key:
            if identity.get("fingerprint") != fingerprint:
                raise StageInvocationError("recipe_tuning_idempotency_conflict")
            if row.status != "succeeded":
                raise StageInvocationError("recipe_tuning_original_unresolved")
            return data["suggestion"]
    contract, projection = _input(db, project_id, unit_id, node_id, user, request)
    generated_request = _request(projection, key)
    model = projection["model"]
    claim = {"owner_id": user.id, "project_id": project_id, "unit_id": unit_id, "node_id": node_id,
        "invocation_key": key, "fingerprint": fingerprint, "projection_hash": digest(projection)}
    row = LLMRun(provider=model["provider"], model=model["model"], purpose="generate", input_hash=input_hash(generated_request),
        prompt_version=PROMPT_VERSION, status="pending", parsed_output_json={"claim": claim, "projection": projection})
    db.add(row)
    db.commit()
    db.refresh(row)
    try:
        _, current = _input(db, project_id, unit_id, node_id, user, request)
        actual = effective_llm_config("generate", profile=model["profile_id"] if model["profile_id"] != "default" else None)
        if digest(current) != claim["projection_hash"] or creation_recipes._model_projection(actual) != model:
            raise StageInvocationError("recipe_tuning_resolution_changed")
    except Exception:  # noqa: BLE001 - Seal a durable claim before any provider dispatch, regardless of preflight failure.
        row.status, row.error = "failed", "failed_before_dispatch"
        db.commit()
        raise StageInvocationError("recipe_tuning_resolution_changed") from None
    provider = MockProvider() if actual["provider"] == "mock" else OpenAICompatibleProvider(
        actual["base_url"], actual["api_key"], actual["model"], registered_provider=actual.get("registered_provider"))
    received = False
    try:
        response = asyncio.run(provider.generate_json(generated_request))
        received = True
        data = canonical(response.data, max_bytes=16 * 1024)
        if type(data) is not dict or set(data) != {"config_patch", "explanation"} or not data["config_patch"]:
            raise ValueError("invalid_tuning")
        base, effective, patch = contract.effective_config(projection["base_config"], data["config_patch"])
        if type(data["explanation"]) is not str or not 1 <= len(data["explanation"]) <= 4000:
            raise ValueError("invalid_tuning")
        suggestion = canonical({"schema": "creation_recipe.tuning.v1", "llm_run_id": row.id,
            "input_hash": row.input_hash, "model": model, "config_patch": patch, "explanation": data["explanation"],
            "base_config": base, "effective_config": effective, "source_hash": claim["projection_hash"],
            "workflow_checksum": projection["workflow_checksum"], "feedback_event_ids": request["feedback_event_ids"]})
        suggestion["suggestion_hash"] = digest(suggestion)
        row.parsed_output_json = {"claim": claim, "projection": projection, "suggestion": suggestion}
        row.status, row.error, row.raw_output = "succeeded", None, None
        row.usage_json = {"model_route": model, "suggestion_hash": suggestion["suggestion_hash"]}
        db.commit()
        return suggestion
    except Exception as exc:  # noqa: BLE001 - Persist uncertainty without exposing third-party error or retrying dispatch.
        db.rollback()
        row = db.get(LLMRun, row.id)
        from .generation.providers import LLMError

        received = received or isinstance(exc, LLMError) and str(exc) in {
            "provider_response_invalid", "模型输出无法解析为 JSON（含一次修复尝试）"}
        row.status = "failed" if received else "unknown"
        row.error = "recipe_tuning_output_invalid" if received else "recipe_tuning_original_unresolved"
        row.raw_output = None
        db.commit()
        raise StageInvocationError(row.error) from None


def verified_patch(db, user, unit_id, node_id, workflow, request):
    row = db.get(LLMRun, request.get("tuning_suggestion_id"))
    data = row.parsed_output_json or {} if row else {}
    claim, projection, suggestion = data.get("claim", {}), data.get("projection", {}), data.get("suggestion", {})
    if (row is None or row.status != "succeeded" or row.prompt_version != PROMPT_VERSION
            or claim.get("owner_id") != user.id or claim.get("unit_id") != unit_id or claim.get("node_id") != node_id
            or request.get("feedback_event_id") not in suggestion.get("feedback_event_ids", [])
            or projection.get("workflow_checksum") != workflow.checksum
            or digest(projection) != claim.get("projection_hash")
            or row.input_hash != input_hash(_request(projection, claim.get("invocation_key")))
            or suggestion.get("suggestion_hash") != digest({key: value for key, value in suggestion.items() if key != "suggestion_hash"})
            or request.get("expected_suggestion_hash") != suggestion.get("suggestion_hash")):
        raise StageInvocationError("recipe_tuning_receipt_invalid")
    return request.get("config_patch", suggestion["config_patch"])
