"""Execution adapter for bounded, human-reviewed intermediate creative stages."""

from __future__ import annotations

import asyncio

from .generation.providers import (
    GenerateRequest,
    MockProvider,
    OpenAICompatibleProvider,
    effective_llm_config,
    input_hash,
    record_run,
    record_validated_stage_run,
)
from .stage_contracts import canonical, digest

OUTPUT_SCHEMAS = {
    "research.brief.v1": "research",
    "creative.angles.v1": "research",
    "content.outline.v1": "text",
    "graphic.visual-direction.v1": "graphic",
    "graphic.card-plan.v1": "graphic",
    "audio.spoken-adaptation.v1": "audio",
    "audio.voice-direction.v1": "audio",
    "video.shot-plan.v1": "video",
}


class CreativeMethodStageError(ValueError):
    pass


def _run(provider, request):
    return asyncio.run(provider.generate_json(request))


def build_request(resolved: dict) -> GenerateRequest:
    config = resolved.get("effective_config") or {}
    output_schema = config.get("output_schema")
    if output_schema not in OUTPUT_SCHEMAS:
        raise CreativeMethodStageError("creative_method_output_schema_invalid")
    count = config.get("candidate_count", 1)
    if type(count) is not int or not 1 <= count <= 5:
        raise CreativeMethodStageError("creative_method_candidate_count_invalid")
    return GenerateRequest(
        purpose="creative_method",
        channel=(resolved.get("context") or {}).get("channel"),
        system_prompt=resolved["system_prompt"],
        user_prompt=resolved["effective_prompt"],
        schema_hint="stage.creative.method.v1",
        context={
            "output_schema": output_schema,
            "candidate_count": count,
            "length": config.get("length", "medium"),
            "reference_catalog": [
                {"kind": "fact_pack_item", "id": item["item_id"], "checksum": item["checksum"]}
                for item in ((resolved.get("context") or {}).get("boundary") or {}).get("items", [])
            ] + [{"kind": "material_revision", "id": item["material_revision_id"], "checksum": item["content_hash"]}
                 for item in [*(resolved.get("context") or {}).get("asset_refs", []),
                              *(resolved.get("context") or {}).get("shared_asset_refs", [])]],
        },
        temperature=config.get("temperature"),
        max_tokens=((resolved.get("creative_configuration") or {}).get("chat_limits") or {}).get("max_tokens"),
        timeout_seconds=((resolved.get("creative_configuration") or {}).get("chat_limits") or {}).get("timeout_seconds"),
    )


def _model_projection(model: dict) -> dict:
    return {
        "provider": model.get("provider"),
        "model": model.get("model"),
        "profile": model.get("profile_id"),
        "runtime_hash": model.get("runtime_hash"),
        "configuration_revision": model.get("configuration_revision"),
    }


def _validate_output(data: object, request: GenerateRequest) -> dict:
    if not isinstance(data, dict) or set(data) != {"schema", "candidates"} or data.get("schema") != request.context["output_schema"]:
        raise CreativeMethodStageError("creative_method_output_invalid")
    candidates = data.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != request.context["candidate_count"]:
        raise CreativeMethodStageError("creative_method_candidate_count_invalid")
    normalized, identifiers = [], set()
    for index, item in enumerate(candidates, 1):
        if not isinstance(item, dict) or set(item) - {"id", "summary", "content", "references", "warnings"}:
            raise CreativeMethodStageError("creative_method_output_invalid")
        if not isinstance(item.get("summary"), str) or not 1 <= len(item["summary"].strip()) <= 1000:
            raise CreativeMethodStageError("creative_method_output_invalid")
        if not isinstance(item.get("content"), dict):
            raise CreativeMethodStageError("creative_method_output_invalid")
        refs, warnings = item.get("references", []), item.get("warnings", [])
        if (type(refs) is not list or len(refs) > 100 or type(warnings) is not list or len(warnings) > 20
                or any(type(warning) is not str or len(warning) > 500 for warning in warnings)
                or any(ref not in request.context["reference_catalog"] for ref in refs)):
            raise CreativeMethodStageError("creative_method_output_invalid")
        identifier = item.get("id", f"creative-{index}")
        from .stage_contracts import IDENTIFIER
        if type(identifier) is not str or not IDENTIFIER.fullmatch(identifier) or identifier in identifiers:
            raise CreativeMethodStageError("creative_method_candidate_id_invalid")
        identifiers.add(identifier)
        from .creative_artifacts import required_references, validate_artifact

        content = validate_artifact(data["schema"], item["content"])
        if not required_references(data["schema"], content).issubset({(ref["kind"], ref["id"]) for ref in refs}):
            raise CreativeMethodStageError("creative_method_exact_references_required")
        candidate = canonical({"id": identifier, "summary": item["summary"], "content": content,
                               "references": refs, "warnings": warnings}, max_bytes=64 * 1024)
        candidate["candidate_hash"] = digest(candidate)
        normalized.append(candidate)
    return canonical({"schema": data["schema"], "candidates": normalized}, max_bytes=128 * 1024)


def execute(db, ctx, resolved: dict, user) -> dict:
    from .creation_recipes import _model
    from .creation_recipes import _model_projection as creation_model_projection

    request = build_request(resolved)
    from .creative_configuration import validate_execution
    validate_execution(db, resolved)
    model = resolved.get("model") or {}
    current, blockers = _model(resolved.get("effective_config") or {})
    if blockers or current != model:
        raise CreativeMethodStageError("stage_model_runtime_changed")
    actual = effective_llm_config("generate", profile=model["profile_id"] if model["profile_id"] != "default" else None)
    if creation_model_projection(actual) != model:
        raise CreativeMethodStageError("stage_model_runtime_changed")
    route = _model_projection(model)
    provider = MockProvider() if actual["provider"] == "mock" else OpenAICompatibleProvider(
        actual["base_url"], actual["api_key"], actual["model"], route_provenance=route,
        registered_provider=actual.get("registered_provider"),
    )
    try:
        result = _run(provider, request)
    except Exception as exc:
        record_run(db, request, None, error="stage_provider_failed", provider_name=provider.name,
                   model_name=getattr(provider, "model", None) or model.get("model"),
                   prompt_version="stage.creative.method.v1", route_provenance=route)
        raise CreativeMethodStageError("stage_provider_failed") from exc
    try:
        data = canonical(result.data)
        output = _validate_output(data, request)
    except (ValueError, TypeError, KeyError) as exc:
        record_validated_stage_run(db, request, result, error="stage_creative_output_invalid",
            provider_name=provider.name, model_name=getattr(provider, "model", None) or model.get("model"),
            prompt_version="stage.creative.method.v1", route_provenance=route)
        raise CreativeMethodStageError("stage_creative_output_invalid") from exc
    llm_run = record_validated_stage_run(db, request, result, validated_data=data,
        provider_name=provider.name, model_name=getattr(provider, "model", None) or model.get("model"),
        prompt_version="stage.creative.method.v1", route_provenance=route)
    output["llm_run_id"] = llm_run.id
    output["input_hash"] = input_hash(request)
    output["prompt_hash"] = resolved.get("prompt_hash")
    output["model"] = {"provider": provider.name, "model": getattr(provider, "model", None) or model.get("model")}
    output["output_hash"] = digest(output)
    return output


def _sealed_output(db, run, step, attempt):
    from ..models import LLMRun
    from .stage_invocations import StageInvocationError, _same_key_result

    if (attempt is None or attempt.run_id != run.id or attempt.step_id != step.id
            or attempt.node_id != step.node_id or attempt.plugin_key != "stage.creative.method"
            or attempt.plugin_version != "1" or attempt.status != "succeeded"):
        raise StageInvocationError("creative_method_attempt_integrity")
    receipt = attempt.execution_receipt_json or {}
    if _same_key_result(db, step, receipt.get("invocation_key"), receipt.get("request_fingerprint")) != attempt:
        raise StageInvocationError("creative_method_attempt_integrity")
    resolved = (attempt.input_snapshot_json or {}).get("resolved_stage") or {}
    output = attempt.output_json or {}
    request = build_request(resolved)
    llm = db.get(LLMRun, output.get("llm_run_id"))
    model = resolved.get("model") or {}
    if (llm is None or llm.status != "succeeded" or llm.purpose != request.purpose
            or llm.prompt_version != "stage.creative.method.v1" or llm.provider != model.get("provider")
            or llm.model != model.get("model") or llm.input_hash != input_hash(request)
            or output.get("input_hash") != llm.input_hash or output.get("prompt_hash") != resolved.get("prompt_hash")
            or output.get("output_hash") != digest({key: value for key, value in output.items() if key != "output_hash"})
            or receipt.get("config_hash") != resolved.get("config_hash")
            or receipt.get("method_hash") != digest(resolved.get("method"))
            or receipt.get("outcome_state") != "succeeded"
            or receipt.get("dispatch_certainty") != "confirmed_dispatched"):
        raise StageInvocationError("creative_method_attempt_integrity")
    normalized = _validate_output(llm.parsed_output_json, request)
    if normalized != {"schema": output.get("schema"), "candidates": output.get("candidates")}:
        raise StageInvocationError("creative_method_attempt_integrity")
    return output, resolved


def accepted_handoff(db, run, step, attempt, *, accepted_hash=None, accepted_decision=None):
    from ..models import ContentUnit
    from .stage_feedback import feedback_events
    from .stage_invocations import StageInvocationError

    output, _resolved = _sealed_output(db, run, step, attempt)
    unit = db.get(ContentUnit, run.content_unit_id)
    events = [item for item in feedback_events(db, unit.project_id, attempt.id)
              if item.payload_json.get("result_kind") == "creative_attempt"
              and item.payload_json.get("decision") == "accepted"]
    if not events:
        return None
    if len(events) != 1:
        raise StageInvocationError("creative_method_acceptance_integrity")
    event, payload = events[0], events[0].payload_json
    selected = next((item for item in output["candidates"] if item["id"] == payload.get("candidate_id")), None)
    if (selected is None or payload.get("accepted_hash") != selected["candidate_hash"]
            or payload.get("output_hash") != attempt.output_hash or payload.get("resolution_hash") != attempt.input_hash
            or payload.get("run_id") != run.id or payload.get("node_id") != step.node_id
            or payload.get("unit_id") != run.content_unit_id or payload.get("result_id") != attempt.id
            or accepted_hash is not None and selected["candidate_hash"] != accepted_hash
            or accepted_decision is not None and accepted_decision != "accepted"):
        raise StageInvocationError("creative_method_acceptance_integrity")
    return {"schema": "stage.handoff.v1", "run_id": run.id, "attempt_id": attempt.id,
            "attempt_no": attempt.attempt_no, "node_id": step.node_id, "plugin": attempt.plugin_key,
            "plugin_version": attempt.plugin_version, "output_kind": "creative_attempt", "entity_id": attempt.id,
            "output_schema": output["schema"], "output_hash": attempt.output_hash, "candidate_id": selected["id"],
            "accepted_hash": selected["candidate_hash"], "decision": "accepted", "summary": selected["summary"],
            "references": selected["references"], "feedback_event_id": event.id}


def accept(db, project_id, unit_id, node_id, user, request):
    from sqlalchemy import select, update

    from ..models import WorkflowStep
    from . import creation_recipes
    from .project_authorization import lock_project_context
    from .stage_feedback import attempt_context, feedback_events, invalidate_downstream, record_feedback
    from .stage_invocations import StageInvocationError, _assert_access

    request = canonical(request, max_bytes=16 * 1024)
    fingerprint = digest({"request": request, "actor_id": user.id, "project_id": project_id, "unit_id": unit_id, "node_id": node_id})
    try:
        lock_project_context(db, project_id, user)
        project, unit, run, step, attempt, resolved = attempt_context(
            db, project_id, unit_id, node_id, user, request, mutable=False)
        if not user.is_active or user.role not in {"admin", "editor"}:
            raise StageInvocationError("stage_feedback_readonly", status_code=403)
        db.execute(update(WorkflowStep).where(WorkflowStep.id == step.id).values(attempt_no=WorkflowStep.attempt_no))
        db.refresh(step)
        output, resolved = _sealed_output(db, run, step, attempt)
        candidate = next((item for item in output["candidates"] if item["id"] == request["candidate_id"]), None)
        if candidate is None or candidate["candidate_hash"] != request["candidate_hash"]:
            raise StageInvocationError("creative_method_candidate_changed")
        for event in feedback_events(db, project_id, attempt.id):
            if event.payload_json.get("feedback_key") == request["acceptance_key"]:
                if event.payload_json.get("acceptance_fingerprint") != fingerprint:
                    raise StageInvocationError("stage_feedback_key_conflict")
                target = accepted_handoff(db, run, step, attempt)
                db.commit()
                return _accept_response(db, run, node_id, attempt, target, event.id, user, replayed=True)
            if event.payload_json.get("decision") == "accepted":
                raise StageInvocationError("stage_already_accepted")
        _assert_access(db, run, user)
        if (step.attempt_no != attempt.attempt_no or step.status != "waiting_input"
                or run.workflow_id != unit.pinned_workflow_id or run.identity_snapshot_id != unit.identity_snapshot_id
                or project.status == "archived" or unit.status == "archived"):
            raise StageInvocationError("stage_attempt_not_current")
        preview = creation_recipes.preview_stage(db, project_id, unit_id, node_id, user,
            run_id=run.id, stage_override=resolved.get("override"))
        if (not preview["ready"] or preview["resolution_hash"] != attempt.input_hash
                or request["expected_context_hash"] != resolved["context_hash"]):
            raise StageInvocationError("stage_adoption_context_changed")
        event = record_feedback(db, project_id=project_id, unit_id=unit_id, run=run, step=step, attempt=attempt,
            user=user, decision="accepted", result_kind="creative_attempt", result_id=attempt.id,
            accepted_hash=candidate["candidate_hash"], feedback_key=request["acceptance_key"], note=request.get("note", ""),
            extra={"candidate_id": candidate["id"], "candidate_hash": candidate["candidate_hash"],
                   "output_schema": output["schema"], "acceptance_fingerprint": fingerprint})
        invalidate_downstream(db, run, step, candidate["candidate_hash"])
        step.status, step.error = "succeeded", None
        steps = db.scalars(select(WorkflowStep).where(WorkflowStep.run_id == run.id)).all()
        run.status = "succeeded" if all(item.status in {"succeeded", "skipped"} for item in steps) else "pending"
        run.error = None
        db.flush()
        target = accepted_handoff(db, run, step, attempt)
        event_id = event.id
        db.commit()
        return _accept_response(db, run, node_id, attempt, target, event_id, user, replayed=False)
    except BaseException:
        db.rollback()
        raise


def _accept_response(db, run, node_id, attempt, target, event_id, user, *, replayed):
    from .stage_continuation import continue_after_acceptance
    continuation = continue_after_acceptance(db, run_id=run.id, accepted_node_id=node_id,
        accepted_hash=target["accepted_hash"], accepted_attempt_id=attempt.id, accepted_decision=target["decision"], user=user)
    return {"accepted_target": target, "feedback_event_id": event_id, "replayed": replayed, "continuation": continuation}


def selected_input(db, target, *, include_content=False):
    from fastapi import HTTPException

    from ..models import FactPackItem, MaterialRevision, WorkflowStepAttempt
    from .creative_packages import _check_derived_rights
    from .materials import read_bytes_checked
    from .stage_invocations import StageInvocationError

    attempt = db.get(WorkflowStepAttempt, target["attempt_id"])
    candidate = next(item for item in attempt.output_json["candidates"] if item["id"] == target["candidate_id"])
    for ref in candidate["references"]:
        if ref["kind"] == "fact_pack_item":
            item = db.get(FactPackItem, ref["id"])
            if (item is None or item.snapshot_checksum != ref["checksum"] or item.model_use_allowed is not True
                    or item.public_use_revoked_at is not None):
                raise StageInvocationError("stage_evidence_model_use_blocked")
        else:
            material = db.get(MaterialRevision, ref["id"])
            if (material is None or material.content_hash != ref["checksum"] or material.model_use_allowed is not True
                    or material.status not in {"candidate", "usable"}
                    or material.material is None or material.material.status != "active"):
                raise StageInvocationError("stage_material_model_use_blocked")
            try:
                _check_derived_rights(db, material)
                read_bytes_checked(db, material)
            except (HTTPException, OSError) as exc:
                raise StageInvocationError("stage_material_model_use_blocked") from exc
    return {**target, **({"selected_content": candidate["content"]} if include_content else {})}
