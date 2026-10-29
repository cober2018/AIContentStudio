"""Stage adapters over existing domain services; only the common gate dispatches."""

import asyncio
import re

from fastapi import HTTPException
from sqlalchemy import select

from ..models import (
    ChannelVariantRevision,
    ContentMasterRevision,
    CreativeExecution,
    MaterialRevision,
    ProjectMaterialReference,
    ProjectWorkflowOutput,
    ProviderGenerationTask,
    WorkflowStep,
    WorkflowStepAttempt,
)
from .stage_contracts import RESOLVED_STAGE_MAX_BYTES, canonical, digest
from .stage_invocations import StageInvocationError

DOMAIN_PLUGINS = {
    ("media.generate", "2"): "media",
    ("media.generate", "3"): "media",
    ("stage.variant.adapt", "1"): "variant",
    ("stage.professional.prepare", "1"): "professional",
    ("stage.professional.prepare", "2"): "professional",
    ("stage.checks", "1"): "checks",
    ("stage.human.review", "1"): "human",
}
MEDIA_PARAMETERS = ("items", "pixels", "seconds", "tokens", "timeout_seconds", "aspect_ratio")


class StageDomainError(StageInvocationError):
    def __init__(self, code, *, dispatch_certainty="not_dispatched", output=None, status_code=409):
        super().__init__(code, status_code=status_code)
        self.dispatch_certainty = dispatch_certainty
        self.output = output or {}


def stage_result_policy(output):
    domain, result = output.get("domain"), output.get("result") or {}
    if domain == "checks" and result.get("checks_pass") is not True and result.get("checks_reviewable") is not True:
        return {"status": "failed", "dispatch_certainty": "confirmed_dispatched", "error": "stage_checks_blocked"}
    if domain == "media":
        state = result.get("dispatch_state")
        if state in {"unknown", "submitting"}:
            return {"status": "unknown", "dispatch_certainty": "possibly_dispatched", "error": "stage_media_original_task_unresolved"}
        if state in {"failed", "cancelled"}:
            return {"status": "failed", "dispatch_certainty": "confirmed_dispatched", "error": "stage_media_generation_failed"}
        if state not in {"running", "result_ready", "accepted"}:
            return {"status": "failed", "dispatch_certainty": "not_dispatched", "error": "stage_media_dispatch_unavailable"}
    return {"status": "succeeded", "dispatch_certainty": "confirmed_dispatched", "error": None}


def domain_for(node):
    return DOMAIN_PLUGINS.get((node.get("plugin"), str(node.get("plugin_version") or "1")))


def media_request(config, *, allow_aspect=False):
    from .generation_tasks import workflow_request

    params = dict(config.get("parameters") or {})
    for name in MEDIA_PARAMETERS:
        if name in config:
            if name in params and params[name] != config[name]:
                raise StageInvocationError("stage_media_parameter_conflict", status_code=422)
            params[name] = config[name]
    if "aspect_ratio" in params and not allow_aspect:
        raise StageInvocationError("stage_media_aspect_requires_v3", status_code=422)
    return workflow_request({**{key: config[key] for key in (
        "capability", "selected_profile", "explicit_plugin", "prompt", "source_revision_ids"
    ) if key in config}, "parameters": params})


def native_media_resolution(resolved):
    if domain_for(resolved["node"]) != "media":
        return resolved
    request = media_request(resolved["effective_config"], allow_aspect=resolved["node"].get("plugin_version") == "3")
    prompt = request["prompt"]
    # Native media accepts one bounded prompt, not the chat system/context layers.
    result = canonical({**resolved, "system_prompt": "", "effective_prompt": prompt,
        "prompt_sections": [{"key": "native_media_prompt", "text": prompt, "hash": digest(prompt)}],
        "prompt_projection": {"kind": "native_media", "context_layers_sent": False,
                              "source_revision_ids": request["source_revision_ids"]},
        "prompt_hash": digest({"system": "", "user": prompt})}, max_bytes=RESOLVED_STAGE_MAX_BYTES)
    result.pop("resolution_hash", None)
    result["resolution_hash"] = digest(result)
    return result


def media_plan_identity(plan):
    # The task binds its eventual Attempt ID into input_hash; routing itself must remain exact.
    return canonical({key: value for key, value in plan.items()
                      if key not in {"plan_signature", "plan_hash", "input_hash", "dispatch_ready"}})


def _visible_sources(db, project_id, ids):
    from .creative_packages import _check_derived_rights

    for revision_id in ids:
        referenced = db.scalar(select(ProjectMaterialReference.id).where(
            ProjectMaterialReference.project_id == project_id,
            ProjectMaterialReference.material_revision_id == revision_id,
            ProjectMaterialReference.status == "active",
        ).limit(1))
        generated = db.scalar(select(ProjectWorkflowOutput.id).where(
            ProjectWorkflowOutput.project_id == project_id,
            ProjectWorkflowOutput.entity_id == revision_id,
            ProjectWorkflowOutput.output_kind == "material_revision",
        ).limit(1))
        if referenced is None and generated is None:
            raise StageInvocationError("stage_media_source_not_in_project", status_code=409)
        material = db.get(MaterialRevision, revision_id)
        if material is None:
            raise StageInvocationError("stage_media_source_unavailable", status_code=409)
        _check_derived_rights(db, material)


def _variant_request(context, config):
    master = context.get("master") or {}
    if not master:
        raise StageInvocationError("master_required", status_code=409)
    request = {"source_master_revision_id": master["id"],
            "expected_source_payload_hash": master["payload_hash"],
            "expected_source_context_hash": master["context_hash"],
            "channel_id": config["channel_id"], "content_form": config["content_form"]}
    for key in ("target_account_id",):
        if key in config:
            request[key] = config[key] or None
    if "question_text" in config:
        request["question"] = {"text": config["question_text"], "confirmed": config.get("question_confirmed", False)}
        for key in ("url", "context"):
            if "question_" + key in config:
                request["question"][key] = config["question_" + key]
    return request


def professional_request(context, config, *, method=None):
    from .creative_contracts import canonical_output_contract

    basic = {"roles": [{"role_id": config["output_role"], "kind": config["output_kind"],
        "required": True, "allowed_mime": [config["output_mime"]], "min_count": config["output_count"],
        "max_count": config["output_count"], "max_bytes": config["output_max_bytes"]}]}
    # Advanced contracts cannot silently discard basic controls the UI shows as effective.
    if ("output_contract" in config
            and canonical_output_contract(config["output_contract"]) != canonical_output_contract(basic)):
        raise StageInvocationError("stage_professional_output_controls_conflict", status_code=422)
    result = {"package_schema": config["package_schema"], "objective": config["objective"].strip(),
              "constraints": config["constraints"], "acceptance_criteria": config["acceptance_criteria"],
              "output_contract": canonical_output_contract(basic)}
    if method is not None:
        instructions = method.get("instruction", "")
        extra = config.get("instruction", "")
        constraints = [*result["constraints"],
            *[instructions[offset:offset + 2000] for offset in range(0, len(instructions), 2000)]]
        if extra.strip():
            constraints.append(extra.strip())
        if len(constraints) > 50:
            raise StageInvocationError("stage_professional_constraints_bound", status_code=422)
        result["constraints"] = constraints
    if "source_variant_revision_id" in config:
        result["source_variant_revision_id"] = config["source_variant_revision_id"]
    else:
        master = context.get("master") or {}
        if not master:
            raise StageInvocationError("master_required", status_code=409)
        result["source_master_revision_id"] = master["id"]
    executor_fields = {"executor_kind", "executor_key", "executor_version"}
    supplied = executor_fields & config.keys()
    if config["prepare_execution"]:
        if supplied != executor_fields:
            raise StageInvocationError("stage_professional_executor_required", status_code=422)
        from .creative_executions import _executor

        _executor({name: config[name] for name in executor_fields})
    elif supplied:
        raise StageInvocationError("stage_professional_executor_not_consumed", status_code=422)
    return result


def prepare_domain(db, user, unit, node, config, context, *, creative=None):
    """Pure resolution of domain inputs, routing and CAS heads; no dispatch or writes."""
    domain = domain_for(node)
    if domain is None:
        return context, None, []
    model, blockers, snapshot = None, [], {}
    try:
        if domain == "media":
            from . import generation_tasks, model_capability_routing, provider_media

            request = media_request(config, allow_aspect=str(node.get("plugin_version") or "1") == "3")
            _visible_sources(db, unit.project_id, request["source_revision_ids"])
            refs, _ = provider_media._sources(db, request["source_revision_ids"])
            sources = [{"revision_id": rid, "content_hash": value} for rid, value in refs]
            plan = model_capability_routing.plan(db, capability=request["capability"],
                selected_profile=request["selected_profile"], explicit_plugin=request["explicit_plugin"],
                parameters=request["parameters"], source_refs=sources, _for_execution=True)
            if plan.get("status") != "ready":
                blockers.append("stage_media_route_unavailable")
            else:
                generation_tasks._storage()
                key_id, _ = generation_tasks._key()
                provider_key = generation_tasks._KEYS.get(plan["adapter_key"])
                if provider_key is None:
                    raise StageInvocationError("stage_media_route_unavailable")
                provider, runtime_hash = provider_media._provider(generation_tasks._KINDS[request["capability"]],
                                                                 provider_key, plan["adapter_version"])
                identity = generation_tasks._identity(provider, plan["model_id"], key_id)
                if identity is None or not callable(getattr(provider, "submit_task", None)):
                    blockers.append("stage_media_durable_runtime_unavailable")
                model = {"profile_id": plan["execution_profile"], "provider": provider_key,
                    "model": plan["model_id"], "adapter_key": plan["adapter_key"],
                    "adapter_version": plan["adapter_version"], "runtime_hash": runtime_hash,
                    "configuration_revision": plan["configuration_revision"],
                    "credential_continuity_hash": digest(identity), "receipt_key_id": key_id,
                    "routing_plan_hash": digest(media_plan_identity(plan))}
            snapshot = {"request": request, "routing_plan": media_plan_identity(plan), "source_refs": sources}
            if context.get("run_id"):
                unresolved = db.scalar(select(ProviderGenerationTask.id).join(
                    WorkflowStepAttempt, ProviderGenerationTask.workflow_step_attempt_id == WorkflowStepAttempt.id
                ).where(WorkflowStepAttempt.run_id == context["run_id"], WorkflowStepAttempt.node_id == node["id"],
                        ProviderGenerationTask.state.in_(["unknown", "submitting", "submitted", "running", "pending"])).limit(1))
                if unresolved:
                    blockers.append("stage_media_original_task_unresolved")
        elif domain == "variant":
            from . import channel_variants, creation_recipes

            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,119}", config["variant_key"]):
                raise StageInvocationError("stage_variant_key_invalid", status_code=422)
            if config["mode"] == "deterministic" and any(key in config for key in ("instruction", "method", "model_profile_id")):
                raise StageInvocationError("stage_variant_model_controls_not_consumed", status_code=422)
            request = _variant_request(context, config)
            preview = channel_variants.adapt_preview(db, project_id=unit.project_id, unit_id=unit.id,
                                                     user=user, payload=request)
            head = db.scalar(select(ChannelVariantRevision).where(
                ChannelVariantRevision.content_unit_id == unit.id,
                ChannelVariantRevision.variant_key == config["variant_key"],
            ).order_by(ChannelVariantRevision.revision_no.desc()).limit(1))
            if head and (head.channel_id != config["channel_id"] or head.content_form != config["content_form"]):
                blockers.append("stage_variant_target_conflict")
            if head and (head.edit_summary_json or {}).get("target_account", {}).get("content_account_id") != (config.get("target_account_id") or None):
                blockers.append("stage_variant_account_conflict")
            snapshot = {"request": request, "preview": preview,
                        "variant_key": config["variant_key"], "expected_revision": head.revision_no if head else 0}
            if config["mode"] == "model_assisted":
                from .stage_master_adoptions import _live_refs

                channel_variants.guard_unknown_adaptation(db, channel_variants._model_binding(unit.project_id, unit.id, user.email, preview))
                _live_refs(db, db.get(ContentMasterRevision, context["master"]["id"]), require_model_use=True)
                if preview["evidence_refs"]:
                    blockers.append("variant_model_citation_mapping_unavailable")
                model, reasons = creation_recipes._model(config)
                blockers.extend(reasons)
        elif domain == "professional":
            from . import creative_packages

            method = None
            if str(node.get("plugin_version")) == "2":
                from .creation_recipes import _method

                if creative is not None and getattr(unit, "production_domain", "persona") != "product":
                    method = {"instruction": "\n\n".join(item["instruction"] for item in creative.get("method_stack", []))}
                else:
                    method, reasons = _method(db, user, unit, node, config)
                    blockers.extend(reasons)
                if not method:
                    raise StageInvocationError("stage_professional_method_required")
            request = professional_request(context, config, method=method)
            source, projection, master = creative_packages._source(db, unit.project_id, unit.id, user,
                master_id=request.get("source_master_revision_id"),
                variant_id=request.get("source_variant_revision_id"), current=True)
            if request["package_schema"] == "director.video.v1" and (
                    request.get("source_variant_revision_id") or source.payload_schema != "video.master.v2"):
                blockers.append("creative_director_video_v2_required")
            if "aspect_ratio" in config:
                expected_aspect = [int(part) for part in config["aspect_ratio"].split(":")]
                if (source.payload_json or {}).get("aspect_ratio") != expected_aspect:
                    blockers.append("stage_director_aspect_ratio_mismatch")
            for ref in projection["assets"]:
                creative_packages._check_asset(db, unit.project_id, ref)
            creative_packages._check_evidence(db, master, projection["evidence"])
            snapshot = {"request": request, "source_payload_hash": source.payload_hash,
                "source_context_hash": source.context_hash, "assets": projection["assets"],
                "evidence": projection["evidence"], "expected_revision": 0,
                "prepare_execution": config["prepare_execution"],
                "executor": {key: config[key] for key in ("executor_kind", "executor_key", "executor_version") if key in config}}
            if request["package_schema"] == "director.video.v1":
                plans = creative_packages.accepted_director_plans(db, unit, master)
                if plans:
                    snapshot["accepted_shot_plans"] = plans
        elif domain == "checks":
            from . import content_masters

            master = db.get(ContentMasterRevision, (context.get("master") or {}).get("id"))
            if master is None:
                raise StageInvocationError("master_required")
            snapshot = {"master_revision_id": master.id,
                        "requirements": content_masters.check_requirements(db, master), "expected_revision": 0}
        else:
            snapshot = {"instruction": config["instruction"], "expected_revision": 0}
    except HTTPException as exc:
        detail = exc.detail
        code = detail.get("code") if type(detail) is dict else detail
        blockers.append(code if type(code) is str and re.fullmatch(r"[A-Za-z0-9_.:-]{1,100}", code)
                        else "stage_domain_input_unavailable")
    except StageInvocationError as exc:
        if exc.status_code == 422:
            raise
        blockers.append(exc.code)
    return canonical({**context, "domain": {"kind": domain, **snapshot}}), model, blockers


def _claim(db, ctx, resolved):
    attempt = db.scalar(select(WorkflowStepAttempt).where(
        WorkflowStepAttempt.step_id == ctx.step.id, WorkflowStepAttempt.attempt_no == ctx.step.attempt_no,
    ))
    if (attempt is None or attempt.status != "running" or attempt.run_id != ctx.run.id
            or attempt.input_hash != resolved["resolution_hash"]
            or (attempt.input_snapshot_json or {}).get("resolved_stage") != resolved
            or (attempt.execution_receipt_json or {}).get("resolution_hash") != resolved["resolution_hash"]):
        raise StageInvocationError("stage_domain_claim_required", status_code=409)
    return attempt


def validate_media_claim(db, attempt, resolved, request):
    step = db.get(WorkflowStep, attempt.step_id)
    if (step is None or attempt.plugin_key != "media.generate" or attempt.plugin_version not in {"2", "3"}
            or step.plugin_key != "media.generate" or step.plugin_version not in {"2", "3"}
            or step.status != "running" or step.attempt_no != attempt.attempt_no
            or attempt.status != "running" or attempt.input_hash != resolved.get("resolution_hash")
            or (attempt.input_snapshot_json or {}).get("resolved_stage") != resolved
            or (attempt.execution_receipt_json or {}).get("resolution_hash") != resolved.get("resolution_hash")
            or request.get("project_id") != resolved["context"]["project_id"]
            or resolved.get("system_prompt") != "" or resolved.get("effective_prompt") != request.get("prompt")
            or resolved.get("prompt_hash") != digest({"system": "", "user": request.get("prompt")})
            or {key: value for key, value in request.items() if key not in {"project_id", "idempotency_key"}}
               != media_request(resolved["effective_config"], allow_aspect=resolved["node"].get("plugin_version") == "3")):
        raise StageInvocationError("stage_media_claim_invalid", status_code=409)
    _visible_sources(db, request["project_id"], request["source_revision_ids"])


def domain_result(domain, resolved, result):
    result = canonical(result)
    return canonical({"schema": f"stage.{domain}.result.v1", "domain": domain,
                      "resolution_hash": resolved["resolution_hash"], "result": result,
                      "result_hash": digest(result)})


def build_variant_request(resolved, preview, user):
    from .channel_variants import _MODEL_PURPOSE, _model_binding
    from .generation.providers import GenerateRequest

    context = resolved["context"]
    binding = _model_binding(context["project_id"], context["unit_id"], user.email, preview)
    return GenerateRequest(purpose=_MODEL_PURPOSE, channel=preview["channel_id"],
        system_prompt=resolved["system_prompt"], user_prompt=resolved["effective_prompt"],
        schema_hint=preview["payload_schema"], context={"binding": binding, "source_proposal": preview["payload"]})


def _model_variant(db, resolved, preview, user):
    from . import channel_variants, creation_recipes
    from .channel_variant_documents import canonical_payload
    from .generation.providers import (
        MockProvider,
        OpenAICompatibleProvider,
        effective_llm_config,
        record_run,
        record_validated_stage_run,
    )

    binding = channel_variants._model_binding(resolved["context"]["project_id"], resolved["context"]["unit_id"], user.email, preview)
    try:
        channel_variants.guard_unknown_adaptation(db, binding)
    except HTTPException as exc:
        raise StageDomainError("variant_model_unknown_unresolved") from exc
    model = resolved["model"]
    live, blockers = creation_recipes._model(resolved["effective_config"])
    if blockers or live != model:
        raise StageDomainError("stage_model_runtime_changed")
    actual = effective_llm_config("generate", profile=model["profile_id"] if model["profile_id"] != "default" else None)
    if creation_recipes._model_projection(actual) != model:
        raise StageDomainError("stage_model_runtime_changed")
    route = {key: model.get(key) for key in ("provider", "model", "runtime_hash", "configuration_revision")}
    route["profile"] = model["profile_id"]
    provider = MockProvider() if actual["provider"] == "mock" else OpenAICompatibleProvider(
        actual["base_url"], actual["api_key"], actual["model"],
        registered_provider=actual.get("registered_provider"), route_provenance=route)
    request = build_variant_request(resolved, preview, user)
    try:
        result = asyncio.run(provider.generate_json(request))
    except Exception as exc:
        try:
            run = record_run(db, request, None, error="stage_provider_result_unknown", provider_name=provider.name,
                       model_name=model["model"], prompt_version=channel_variants._MODEL_PROMPT_VERSION)
            run.status = "unknown"
            run.parsed_output_json = {"unknown_binding": binding}
            db.flush()
        except Exception as record_error:
            raise StageDomainError("stage_provider_failed", dispatch_certainty="possibly_dispatched") from record_error
        raise StageDomainError("stage_provider_failed", dispatch_certainty="possibly_dispatched") from exc
    try:
        canonical(result.data, max_bytes=128 * 1024)
        if len((result.raw_output or "").encode()) > 128 * 1024:
            raise ValueError("stage_proposal_output_invalid")
        proposed = canonical_payload(preview["payload_schema"], result.data.get("payload"),
                                     asset_refs=preview["asset_refs"], evidence_refs=preview["evidence_refs"])
    except (ValueError, TypeError, KeyError) as exc:
        try:
            record_validated_stage_run(db, request, result, error="stage_proposal_output_invalid",
                provider_name=provider.name, model_name=model["model"],
                prompt_version=channel_variants._MODEL_PROMPT_VERSION, route_provenance=route)
        except Exception as record_error:
            raise StageDomainError("stage_variant_receipt_failed", dispatch_certainty="confirmed_dispatched") from record_error
        raise StageDomainError("stage_proposal_output_invalid", dispatch_certainty="confirmed_dispatched") from exc
    try:
        run = record_validated_stage_run(db, request, result, validated_data={"payload": proposed},
            provider_name=provider.name, model_name=model["model"],
            prompt_version=channel_variants._MODEL_PROMPT_VERSION, route_provenance=route)
    except Exception as exc:
        raise StageDomainError("stage_variant_receipt_failed", dispatch_certainty="confirmed_dispatched") from exc
    binding = channel_variants._model_binding(resolved["context"]["project_id"], resolved["context"]["unit_id"], user.email, preview)
    receipt = {"llm_run_id": run.id, "purpose": channel_variants._MODEL_PURPOSE, "provider": run.provider,
        "model": run.model, "prompt_version": run.prompt_version, "input_hash": run.input_hash,
        "accepted_output_hash": digest(proposed), "status": "succeeded", **binding}
    run.parsed_output_json = {"payload": proposed, "provenance": receipt}
    try:
        db.flush()
    except Exception as exc:
        raise StageDomainError("stage_variant_receipt_failed", dispatch_certainty="confirmed_dispatched") from exc
    return {**preview, "payload": proposed, "payload_hash": digest(proposed),
            "llm_run_id": run.id, "llm_input_hash": run.input_hash}


def _execute_domain(db, ctx, resolved, user):
    attempt = _claim(db, ctx, resolved)
    domain = domain_for(resolved["node"])
    snapshot = resolved["context"]["domain"]
    project_id, unit_id = resolved["context"]["project_id"], resolved["context"]["unit_id"]
    if domain == "media":
        from . import generation_tasks

        request = {**media_request(resolved["effective_config"], allow_aspect=resolved["node"].get("plugin_version") == "3"), "project_id": project_id,
                   "idempotency_key": f"stage-media.{ctx.run.id}.{attempt.id}"}
        prepared = generation_tasks.prepare(db, user, request, workflow_attempt=attempt, stage_resolution=resolved)
        task = generation_tasks._get(db, user, prepared["task_id"], mutate=True)
        if task.state == "prepared":
            generation_tasks.execute(db, user, task.id, task.revision)
            task = generation_tasks._get(db, user, task.id)
        result = {"task_id": task.id, "task_request_hash": task.request_hash, "task_input_hash": task.input_hash,
                  "plan_hash": task.plan_hash, "dispatch_state": task.state,
                  "source_refs": task.source_refs_json, "material_bound_to_master": False}
    elif domain == "variant":
        from . import channel_variants

        result = channel_variants.adapt_preview(db, project_id=project_id, unit_id=unit_id,
                                               user=user, payload=snapshot["request"])
        if result != snapshot["preview"]:
            raise StageInvocationError("stage_resolution_changed", status_code=409)
        if resolved["effective_config"]["mode"] == "model_assisted":
            result = _model_variant(db, resolved, result, user)
            db.expire_all()
            try:
                current = channel_variants.adapt_preview(db, project_id=project_id, unit_id=unit_id,
                                                         user=user, payload=snapshot["request"])
            except (HTTPException, StageInvocationError, ValueError, KeyError, TypeError) as exc:
                raise StageDomainError("stage_variant_context_changed", dispatch_certainty="confirmed_dispatched") from exc
            if current != snapshot["preview"]:
                raise StageDomainError("stage_variant_context_changed", dispatch_certainty="confirmed_dispatched")
        result = {**result, "variant_key": snapshot["variant_key"],
                  "expected_revision": snapshot["expected_revision"], "persisted_variant": False}
    elif domain == "professional":
        from . import creative_executions, creative_packages

        package = creative_packages.create_package(db, project_id=project_id, unit_id=unit_id,
                                                  user=user, payload=snapshot["request"])
        execution = None
        if snapshot["prepare_execution"]:
            execution = creative_executions.prepare_execution(db, project_id, unit_id,
                {"package_id": package["id"], "idempotency_key": f"stage-execution.{ctx.run.id}.{attempt.id}",
                 **snapshot["executor"]}, user)
        result = {"package_id": package["id"], "package_hash": package["package_hash"],
            "package_schema": package["package_schema"], "execution_id": execution["id"] if execution else None,
            "expected_revision": execution["revision_no"] if execution else 0,
            "executor": snapshot["executor"], "dispatch_state": "not_dispatched"}
    elif domain == "checks":
        from . import content_masters

        checks = content_masters.run_checks(db, project_id, unit_id, snapshot["master_revision_id"], user)
        current = content_masters.current_checks(db, project_id, unit_id, snapshot["master_revision_id"], user)
        checks_pass = bool(current) and all(item["is_current"] and item["status"] == "pass" for item in current)
        checks_reviewable = bool(current) and all(item["is_current"] and item["status"] in {"pass", "warning"} for item in current)
        result = {"master_revision_id": snapshot["master_revision_id"], "checks": canonical(checks),
                  "current_checks": canonical(current), "checks_pass": checks_pass, "checks_reviewable": checks_reviewable,
                  "blockers": [item["check_kind"] for item in current
                               if not item["is_current"] or item["status"] not in {"pass", "warning"}], "expected_revision": 0}
    elif domain == "human":
        result = {"instruction": snapshot["instruction"], "context_hash": resolved["context_hash"],
                  "upstream_hash": digest(resolved["upstream"]), "expected_revision": 0,
                  "approval_granted": False}
    else:
        raise StageInvocationError("stage_executor_unavailable", status_code=422)
    return domain_result(domain, resolved, result)


def execute_domain(db, ctx, resolved, user):
    try:
        return _execute_domain(db, ctx, resolved, user)
    except StageDomainError:
        raise
    except (HTTPException, StageInvocationError, ValueError, KeyError, TypeError) as exc:
        code = exc.code if isinstance(exc, StageInvocationError) else (
            exc.detail.get("code") if isinstance(exc, HTTPException) and type(exc.detail) is dict else
            exc.detail if isinstance(exc, HTTPException) else "stage_domain_input_invalid")
        if type(code) is not str or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,100}", code):
            code = "stage_domain_input_invalid"
        output, certainty = {}, "not_dispatched"
        if domain_for(resolved["node"]) == "media":
            db.rollback()
            attempt = db.scalar(select(WorkflowStepAttempt).where(
                WorkflowStepAttempt.step_id == ctx.step.id,
                WorkflowStepAttempt.input_hash == resolved["resolution_hash"],
            ).order_by(WorkflowStepAttempt.attempt_no.desc()).limit(1))
            task = db.scalar(select(ProviderGenerationTask).where(
                ProviderGenerationTask.workflow_step_attempt_id == attempt.id)) if attempt else None
            if task and task.state != "prepared":
                certainty = "possibly_dispatched" if task.state in {"submitting", "unknown", "running"} else "confirmed_dispatched"
                output = domain_result("media", resolved, {"task_id": task.id,
                    "task_request_hash": task.request_hash, "task_input_hash": task.input_hash,
                    "plan_hash": task.plan_hash, "dispatch_state": task.state,
                    "source_refs": task.source_refs_json, "material_bound_to_master": False})
        raise StageDomainError(code, dispatch_certainty=certainty, output=output) from exc


def domain_output(db, attempt, user):
    """Safe result projection from original output plus current domain-owned state."""
    node = {"plugin": attempt.plugin_key, "plugin_version": attempt.plugin_version}
    domain = domain_for(node)
    if domain is None:
        return None
    output = canonical(attempt.output_json or {})
    result = output.get("result") or {}
    live = None
    if domain == "media":
        from . import generation_tasks

        task = db.scalar(select(ProviderGenerationTask).where(
            ProviderGenerationTask.workflow_step_attempt_id == attempt.id,
            ProviderGenerationTask.owner_user_id == user.id,
        ))
        if task:
            generation_tasks._get(db, user, task.id)
            generation_tasks._verify(task)
            live = generation_tasks.view(task)
            if attempt.status == "unknown" and task.state in {"result_ready", "accepted"}:
                from ..models import WorkflowRun
                from .stage_domain_adoptions import _sealed

                resolved = (attempt.input_snapshot_json or {}).get("resolved_stage") or {}
                output, _, _ = _sealed(db, db.get(WorkflowRun, attempt.run_id), db.get(WorkflowStep, attempt.step_id),
                    attempt, {"domain": "media", "expected_output_hash": attempt.output_hash,
                              "expected_resolution_hash": resolved.get("resolution_hash"),
                              "expected_context_hash": resolved.get("context_hash")}, user.email)
                result = output["result"]
    elif domain == "professional" and result:
        from . import creative_executions, creative_packages

        context = (attempt.input_snapshot_json or {})["resolved_stage"]["context"]
        package = creative_packages.get_package(db, context["project_id"], context["unit_id"], result["package_id"], user)
        live = {"package": {key: package[key] for key in ("id", "package_schema", "package_hash", "is_current", "reasons")},
                "execution": None, "materials_require_explicit_content_save": True}
        if result.get("execution_id"):
            execution = db.get(CreativeExecution, result["execution_id"])
            live["execution"] = creative_executions._projection(db,
                creative_executions._owned(db, context["project_id"], context["unit_id"], execution.id, user), user)
    return canonical({"schema": output.get("schema", f"stage.{domain}.result.v1"), "domain": domain,
                      "result": result, "result_hash": output.get("result_hash"), "live": live,
                      "recovery_proof": output.get("recovery_proof")})
