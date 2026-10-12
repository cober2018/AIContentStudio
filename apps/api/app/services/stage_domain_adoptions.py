"""Exact adoption proofs and transaction callbacks for existing Stage domains."""

from types import SimpleNamespace

from sqlalchemy import select, update

from ..models import (
    ChannelVariantRevision,
    ContentMasterCheckRun,
    ContentMasterRevision,
    ContentProject,
    CreativeExecution,
    CreativeExecutionPackage,
    LLMRun,
    MaterialRevision,
    ProjectEvent,
    ProjectWorkflowOutput,
    ProviderGenerationTask,
    User,
    WorkflowRun,
    WorkflowStep,
    WorkflowStepAttempt,
    utcnow,
)
from . import creation_recipes
from .content_masters import owned_unit
from .stage_contracts import IDENTIFIER, canonical, digest
from .stage_domain_integrations import (
    _visible_sources,
    build_variant_request,
    domain_for,
    domain_result,
    media_plan_identity,
    media_request,
    prepare_domain,
)
from .stage_invocations import StageInvocationError, _assert_access, _same_key_result, require_receipt_schema


def _conflict(code="stage_domain_adoption_integrity"):
    raise StageInvocationError(code, status_code=409)


def _sealed(db, run, step, attempt, request, actor_email):
    if (attempt is None or attempt.run_id != run.id or attempt.step_id != step.id
            or attempt.node_id != step.node_id or attempt.status not in {"succeeded", "unknown"}):
        _conflict()
    receipt = canonical(attempt.execution_receipt_json or {})
    resolved = canonical((attempt.input_snapshot_json or {}).get("resolved_stage") or {})
    output = canonical(attempt.output_json or {})
    original = _same_key_result(db, step, receipt.get("invocation_key"), receipt.get("request_fingerprint"))
    domain = domain_for(resolved.get("node") or {})
    successful = (attempt.status == "succeeded" and receipt.get("outcome_state") == "succeeded"
                  and receipt.get("dispatch_certainty") == "confirmed_dispatched")
    recovered_media = (domain == "media" and attempt.status == "unknown"
                       and receipt.get("outcome_state") == "unknown"
                       and receipt.get("dispatch_certainty") == "possibly_dispatched")
    model = resolved.get("model") or {}
    hashes = {
        "override_hash": digest(resolved.get("override")), "method_hash": digest(resolved.get("method")),
        "upstream_hash": digest(resolved.get("upstream")),
        "model_route_hash": digest({key: model.get(key) for key in ("profile_id", "provider", "model")}),
        "adapter_hash": digest({key: model.get(key) for key in ("adapter_key", "adapter_version")}),
        "runtime_identity_hash": digest({key: model.get(key) for key in ("runtime_hash", "configuration_revision")}),
    }
    resolution_hash = digest({key: value for key, value in resolved.items() if key != "resolution_hash"})
    hashes["request_fingerprint"] = digest({"resolution_hash": resolution_hash, "override": resolved.get("override"),
                                           "automatic": receipt.get("request_mode") == "automatic"})
    if (domain is None or domain != request["domain"] or original is None or original.id != attempt.id
            or receipt.get("schema") != "creation_recipe.execution_receipt.v1"
            or not (successful or recovered_media)
            or receipt.get("request_mode") not in {"explicit", "automatic"}
            or receipt.get("workflow_run_id") != run.id or receipt.get("workflow_id") != run.workflow_id
            or receipt.get("node_id") != step.node_id or receipt.get("plugin_key") != attempt.plugin_key
            or receipt.get("plugin_version") != attempt.plugin_version
            or resolved.get("workflow") != {"id": run.workflow_id, "version": run.workflow_version, "checksum": run.definition_checksum}
            or resolved.get("node", {}).get("id") != step.node_id
            or resolved.get("node", {}).get("plugin") != attempt.plugin_key
            or resolved.get("node", {}).get("plugin_version") != attempt.plugin_version
            or attempt.input_hash != resolution_hash or resolved.get("resolution_hash") != resolution_hash
            or receipt.get("resolution_hash") != resolution_hash or request["expected_resolution_hash"] != resolution_hash
            or resolved.get("context_hash") != digest(resolved.get("context"))
            or request["expected_context_hash"] != resolved.get("context_hash")
            or receipt.get("stage_contract_hash") != resolved.get("stage_contract_hash")
            or receipt.get("config_hash") != digest(resolved.get("effective_config"))
            or receipt.get("config_hash") != resolved.get("config_hash")
            or receipt.get("prompt_hash") != resolved.get("prompt_hash")
            or receipt.get("prompt_hash") != digest({"system": resolved.get("system_prompt"), "user": resolved.get("effective_prompt")})
            or receipt.get("output_contract") != resolved.get("output_contract")
            or any(receipt.get(key) != value for key, value in hashes.items())
            or attempt.output_hash != digest(output) or receipt.get("output_hash") != attempt.output_hash
            or request["expected_output_hash"] != attempt.output_hash):
        _conflict()
    if recovered_media and output == {}:
        tasks = db.scalars(select(ProviderGenerationTask).where(
            ProviderGenerationTask.workflow_step_attempt_id == attempt.id)).all()
        if len(tasks) != 1:
            _conflict("stage_media_original_task_unavailable")
        task = tasks[0]
        # This is a read projection, not a replacement for the empty crash receipt/output.
        output = domain_result("media", resolved, {"task_id": task.id,
            "task_request_hash": task.request_hash, "task_input_hash": task.input_hash,
            "plan_hash": task.plan_hash, "dispatch_state": "unknown",
            "source_refs": task.source_refs_json, "material_bound_to_master": False})
    if (output.get("schema") != f"stage.{domain}.result.v1" or output.get("domain") != domain
            or output.get("resolution_hash") != resolution_hash or output.get("result_hash") != digest(output.get("result"))):
        _conflict()
    result, context = output["result"], resolved["context"]
    if (context.get("unit_id") != run.content_unit_id
            or context.get("run_id") != run.id or context.get("domain", {}).get("kind") != domain):
        _conflict()
    if domain == "variant" and result.get("llm_run_id"):
        from .channel_variants import _MODEL_PROMPT_VERSION, _MODEL_PURPOSE, _model_binding
        from .generation.providers import input_hash

        llm = db.get(LLMRun, result["llm_run_id"])
        original_preview = context["domain"]["preview"]
        actor = SimpleNamespace(email=actor_email)
        stored = llm.parsed_output_json if llm else {}
        proof = stored.get("provenance") or {}
        binding = _model_binding(context["project_id"], context["unit_id"], actor_email, original_preview)
        if (resolved["effective_config"].get("mode") != "model_assisted" or llm is None
                or llm.status != "succeeded" or llm.purpose != _MODEL_PURPOSE
                or llm.prompt_version != _MODEL_PROMPT_VERSION
                or llm.provider != model.get("provider") or llm.model != model.get("model")
                or llm.input_hash != input_hash(build_variant_request(resolved, original_preview, actor))
                or llm.input_hash != result["llm_input_hash"] or proof.get("input_hash") != llm.input_hash
                or proof.get("llm_run_id") != llm.id or proof.get("accepted_output_hash") != result["payload_hash"]
                or result["payload_hash"] != digest(result["payload"]) or stored.get("payload") != result["payload"]
                or any(proof.get(key) != value for key, value in binding.items())):
            _conflict("stage_variant_model_proof_invalid")
    elif domain == "variant" and (resolved["effective_config"].get("mode") != "deterministic"
                                  or {key: result.get(key) for key in context["domain"]["preview"]}
                                  != context["domain"]["preview"]):
        _conflict("stage_variant_proposal_proof_invalid")
    if domain == "media":
        from . import generation_tasks

        task = _media_task(db, attempt, resolved, result)
        owner = db.get(User, task.owner_user_id)
        if owner is None or owner.email != actor_email:
            _conflict("stage_media_task_owner_changed")
        if recovered_media and task.state not in {"result_ready", "accepted"}:
            _conflict("stage_media_original_task_unresolved")
        if recovered_media:
            generation_tasks._verify_result_receipt(task)
            proof = canonical({"schema": "creation_recipe.media_recovery.v1",
                "run_id": run.id, "node_id": step.node_id, "attempt_id": attempt.id,
                "resolution_hash": resolution_hash, "original_output_hash": attempt.output_hash,
                "original_receipt_hash": digest(receipt), "task_id": task.id,
                "task_request_hash": task.request_hash, "task_input_hash": task.input_hash,
                "plan_hash": task.plan_hash, "task_receipt_hash": digest(generation_tasks._receipt(task)),
                "task_receipt_signature_hash": digest(task.receipt_signature),
                "task_result_hash": task.result_hash,
                "task_result_receipt_hash": digest(generation_tasks._result_receipt(task)),
                "task_result_signature_hash": digest(task.result_signature),
                "domain_result_hash": output["result_hash"]})
            output = canonical({**output, "recovery_proof": {**proof, "proof_hash": digest(proof)}})
    if domain == "professional":
        _professional_entity(db, resolved, result)
    if domain == "audio_asr":
        from .stage_audio_asr import validate_asr_result

        validate_asr_result(db, result)
    if domain == "checks":
        if result.get("audio_quality") is True:
            from .stage_audio import validate_qc_result

            validate_qc_result(db, result)
        else:
            _check_rows(db, result)
    return output, resolved, receipt


def _media_task(db, attempt, resolved, result):
    from . import generation_tasks

    if resolved.get("node", {}).get("plugin_version") == "4" and (
            not isinstance(resolved.get("context"), dict) or not resolved["context"].get("audio_stage")):
        _conflict("stage_audio_tts_context_unavailable")
    task = db.get(ProviderGenerationTask, result.get("task_id"))
    expected = {**media_request(resolved["effective_config"],
        allow_aspect=resolved["node"].get("plugin_version") == "3",
        **({"audio_context": resolved["context"]} if resolved["node"].get("plugin_version") == "4" else {})), "project_id": resolved["context"]["project_id"],
        "workflow_step_attempt_id": attempt.id, "stage_resolution_hash": resolved["resolution_hash"],
        "stage_config_hash": resolved["config_hash"], "stage_prompt_hash": resolved["prompt_hash"]}
    model = resolved["model"]
    if resolved["node"].get("plugin_version") == "4" and (not isinstance(model, dict) or any(
            key not in model for key in ("runtime_hash", "model", "provider", "adapter_version", "receipt_key_id", "credential_continuity_hash"))):
        _conflict("stage_audio_tts_model_unavailable")
    project = db.get(ContentProject, expected["project_id"])
    if (task is None or task.workflow_step_attempt_id != attempt.id or task.project_id != expected["project_id"]
            or project is None or task.owner_user_id != project.owner_user_id
            or task.idempotency_key != f"stage-media.{attempt.run_id}.{attempt.id}"
            or task.request_json != expected or task.request_hash != result.get("task_request_hash")
            or task.input_hash != digest({"request": expected, "sources": task.source_refs_json, "actor": task.owner_user_id})
            or task.input_hash != result.get("task_input_hash") or task.plan_hash != result.get("plan_hash")
            or task.runtime_hash != model["runtime_hash"] or task.model_id != model["model"]
            or task.provider_key != model["provider"] or task.provider_version != model["adapter_version"]
            or task.receipt_key_id != model["receipt_key_id"]
            or digest({"credential_epoch": task.credential_epoch, "protocol_version": task.protocol_version})
               != model["credential_continuity_hash"]
            or task.source_refs_json != resolved["context"]["domain"]["source_refs"]
            or resolved.get("system_prompt") != "" or resolved.get("effective_prompt") != expected["prompt"]
            or resolved.get("prompt_hash") != digest({"system": "", "user": expected["prompt"]})
            or media_plan_identity(task.plan_json) != resolved["context"]["domain"]["routing_plan"]):
        _conflict("stage_media_task_proof_invalid")
    generation_tasks._verify(task)
    return task


def _professional_entity(db, resolved, result):
    package = db.get(CreativeExecutionPackage, result.get("package_id"))
    snapshot, context = resolved["context"]["domain"], resolved["context"]
    request = snapshot["request"]
    if (package is None or (package.project_id, package.content_unit_id) != (context["project_id"], context["unit_id"])
            or package.package_hash != result.get("package_hash") or package.package_hash != digest(package.package_json)
            or package.package_schema != request["package_schema"]
            or package.source_master_revision_id != request.get("source_master_revision_id")
            or package.source_variant_revision_id != request.get("source_variant_revision_id")
            or package.source_payload_hash != snapshot["source_payload_hash"]
            or package.source_context_hash != snapshot["source_context_hash"]
            or any(package.package_json.get(key) != request[key] for key in (
                "objective", "constraints", "output_contract", "acceptance_criteria"))):
        _conflict("stage_professional_package_proof_invalid")
    execution = db.get(CreativeExecution, result["execution_id"]) if result.get("execution_id") else None
    if snapshot["prepare_execution"]:
        if (execution is None or execution.package_id != package.id
                or execution.project_id != context["project_id"] or execution.content_unit_id != context["unit_id"]
                or execution.owner_user_id != package.owner_user_id
                or {key: getattr(execution, key) for key in snapshot["executor"]} != snapshot["executor"]
                or result.get("executor") != snapshot["executor"]):
            _conflict("stage_professional_execution_proof_invalid")
    elif result.get("execution_id") is not None:
        _conflict("stage_professional_execution_proof_invalid")
    accepted = {"package_id": package.id, "package_hash": package.package_hash,
                "execution_id": execution.id if execution else None, "executor": snapshot["executor"]}
    return execution or package, digest(accepted)


def _check_rows(db, result, *, requirements=None):
    rows = []
    for frozen in result["checks"]:
        row = db.get(ContentMasterCheckRun, frozen["id"])
        expected = {"id": row.id, "check_kind": row.check_kind, "input_hash": row.input_hash,
                    "status": row.status, "report": row.report_json} if row else None
        if row is None or row.master_revision_id != result["master_revision_id"] or expected != frozen:
            _conflict("stage_checks_proof_invalid")
        if requirements is not None and row.input_hash != (requirements.get(row.check_kind) or {}).get("input_hash"):
            _conflict("stage_checks_inputs_changed")
        if requirements is not None and (row.profile_key, row.profile_version) != (
                requirements[row.check_kind]["profile_key"], requirements[row.check_kind]["profile_version"]):
            _conflict("stage_checks_inputs_changed")
        rows.append(row)
    if not rows or len({row.check_kind for row in rows}) != len(rows):
        _conflict("stage_checks_proof_invalid")
    if requirements is not None and {row.check_kind for row in rows} != set(requirements):
        _conflict("stage_checks_inputs_changed")
    return rows


def _check_dispositions(checks, dispositions):
    if not checks or any(item["status"] not in {"pass", "warning"} for item in checks):
        _conflict("stage_checks_blocked")
    expected = {f"{item['id']}:{item['input_hash']}" for item in checks if item["status"] == "warning"}
    dispositions = dispositions or {}
    if (type(dispositions) is not dict or set(dispositions) != expected
            or any(type(note) is not str or not note.strip() or len(note) > 2000 for note in dispositions.values())):
        _conflict("stage_check_warning_disposition_required")


def _acceptance_events(db, output):
    return db.scalars(select(ProjectEvent).where(
        ProjectEvent.project_id == output.project_id, ProjectEvent.event_type == "creation_recipe.stage_feedback",
        ProjectEvent.entity_id == str(output.attempt_id),
        ProjectEvent.payload_json["project_output_id"].as_integer() == output.id,
        ProjectEvent.payload_json["decision"].as_string().in_(["accepted", "accepted_with_edits"]),
        ProjectEvent.payload_json["adoption_fingerprint"].as_string()
            == (output.provenance_json or {}).get("adoption_fingerprint"),
    )).all()


def accepted_domain_target(db, output):
    provenance = output.provenance_json or {}
    if provenance.get("schema") != "creation_recipe.domain_adoption.v1":
        return None
    run = db.get(WorkflowRun, output.run_id)
    step = db.scalar(select(WorkflowStep).where(WorkflowStep.run_id == output.run_id, WorkflowStep.node_id == output.node_id))
    attempt = db.get(WorkflowStepAttempt, output.attempt_id)
    events = _acceptance_events(db, output)
    if (run is None or step is None or len(events) != 1 or run.content_unit_id != output.unit_id
            or provenance.get("project_output_id") != output.id or provenance.get("result_kind") != output.output_kind
            or provenance.get("result_id") != output.entity_id or provenance.get("attempt_id") != output.attempt_id
            or provenance.get("run_id") != output.run_id or provenance.get("node_id") != output.node_id
            or provenance.get("project_id") != output.project_id or provenance.get("unit_id") != output.unit_id):
        _conflict()
    event = events[0]
    proof = event.payload_json or {}
    if (proof.get("schema") != "creation_recipe.stage_feedback.v1"
            or proof.get("accepted_hash") != provenance.get("accepted_payload_hash")
            or any(proof.get(key) != value for key, value in provenance.items() if key != "schema")):
        _conflict()
    original, resolved, _ = _sealed(db, run, step, attempt, {
        "domain": provenance["domain"], "expected_output_hash": provenance["output_hash"],
        "expected_resolution_hash": provenance["resolution_hash"], "expected_context_hash": provenance["context_hash"],
    }, provenance["actor_email"])
    accepted_hash, revision, context_hash = provenance["accepted_payload_hash"], None, None
    if provenance["domain"] == "variant":
        row = db.get(ChannelVariantRevision, output.entity_id)
        result = original["result"]
        if (row is None or output.output_kind != "channel_variant_revision" or row.project_id != output.project_id
                or row.content_unit_id != output.unit_id or row.payload_hash != digest(row.payload_json)
                or row.payload_hash != accepted_hash or row.edit_summary_json.get("stage_provenance") != provenance
                or row.channel_id != result["channel_id"] or row.content_form != result["content_form"]
                or row.variant_key != result["variant_key"]
                or row.source_master_revision_id != result["source_master_revision_id"]
                or row.source_master_payload_hash != result["source_payload_hash"]
                or row.source_master_context_hash != result["source_context_hash"]
                or row.profile_hash != result["profile_hash"] or row.adapter_key != result["adapter_key"]
                or row.adapter_version != result["adapter_version"]):
            _conflict()
        from .channel_variants import validate_stored_model_provenance

        validate_stored_model_provenance(db, row, db.get(ContentMasterRevision, row.source_master_revision_id))
        revision, context_hash = row.revision_no, row.context_hash
    elif provenance["domain"] == "media":
        from . import generation_tasks

        task = _media_task(db, attempt, resolved, original["result"])
        generation_tasks._verify_result_receipt(task)
        row = db.get(MaterialRevision, output.entity_id)
        if (row is None or output.output_kind != "material_revision" or task.state != "accepted"
                or task.owner_user_id != provenance["actor_id"]
                or task.accepted_material_revision_id != row.id or task.result_hash != row.content_hash
                or row.content_hash != accepted_hash or task.acceptance_hash != provenance.get("rights_hash")
                or (row.metadata_json or {}).get("stage_provenance") != provenance):
            _conflict()
        if original.get("recovery_proof") != provenance.get("media_recovery_proof"):
            _conflict("stage_media_recovery_proof_invalid")
        revision = row.revision_no
    elif provenance["domain"] == "professional":
        row, value = _professional_entity(db, resolved, original["result"])
        kind = "creative_execution" if isinstance(row, CreativeExecution) else "creative_execution_package"
        if output.output_kind != kind or output.entity_id != row.id or value != accepted_hash:
            _conflict()
        revision = provenance["accepted_revision"]
    else:
        if output.output_kind != "workflow_step_attempt" or output.entity_id != attempt.id or accepted_hash != original["result_hash"]:
            _conflict()
        if provenance["domain"] == "checks":
            _check_dispositions(original["result"]["checks"], provenance.get("warning_dispositions"))
    return canonical({"node_id": output.node_id, "output_kind": output.output_kind, "entity_id": output.entity_id,
        "attempt_id": output.attempt_id, "decision": provenance["decision"], "accepted_hash": accepted_hash,
        "payload_hash": accepted_hash, "revision_no": revision, "context_hash": context_hash,
        "project_output_id": output.id, "feedback_event_id": event.id, "domain": provenance["domain"],
        **({"warning_dispositions": provenance.get("warning_dispositions", {})} if provenance["domain"] == "checks" else {})})


def accepted_entity_projection(db, target, user):
    kind, entity_id = target["output_kind"], target["entity_id"]
    if kind == "content_master_revision":
        from .content_masters import _serialize

        entity = _serialize(db, db.get(ContentMasterRevision, entity_id))
    elif kind == "channel_variant_revision":
        from .channel_variants import _serialize

        entity = _serialize(db, db.get(ChannelVariantRevision, entity_id))
    elif kind == "material_revision":
        material = db.get(MaterialRevision, entity_id)
        entity = {"id": material.id, "material_id": material.material_id, "content_hash": material.content_hash,
                  "mime_type": material.mime_type, "revision_no": material.revision_no, "status": material.status,
                  "public_use_allowed": material.public_use_allowed, "model_use_allowed": material.model_use_allowed,
                  "commercial_use_allowed": material.commercial_use_allowed, "bound_to_master": False}
    elif kind in {"creative_execution", "creative_execution_package"}:
        from . import creative_executions, creative_packages

        row = db.get(CreativeExecution, entity_id) if kind == "creative_execution" else db.get(CreativeExecutionPackage, entity_id)
        entity = (creative_executions._projection(db, row, user) if kind == "creative_execution"
                  else creative_packages.package_projection(db, row, user))
    elif kind == "creative_attempt":
        from .creative_method_stage import accepted_handoff

        attempt = db.get(WorkflowStepAttempt, entity_id)
        if attempt is None or accepted_handoff(db, db.get(WorkflowRun, attempt.run_id),
                db.get(WorkflowStep, attempt.step_id), attempt) != target:
            _conflict("creative_method_acceptance_integrity")
        candidate = next(item for item in attempt.output_json["candidates"] if item["id"] == target["candidate_id"])
        entity = {"id": entity_id, "output_schema": target["output_schema"], "result": candidate["content"],
                  "summary": candidate["summary"], "references": candidate["references"]}
    else:
        entity = {"id": entity_id, "result": canonical(db.get(WorkflowStepAttempt, entity_id).output_json)["result"]}
    return canonical({"kind": kind, "id": entity_id, "accepted_hash": target["accepted_hash"],
                      "revision_no": target.get("revision_no"), "entity": entity})


def accepted_domain_input(db, target, *, require_model_use=False, local_audio_qc=False):
    from .materials import read_bytes_checked

    output = db.get(ProjectWorkflowOutput, target["project_output_id"])
    if output is None or accepted_domain_target(db, output) != target:
        _conflict()
    kind, entity_id = target["output_kind"], target["entity_id"]
    result = {**target}
    if kind == "material_revision":
        from .creative_packages import _check_derived_rights

        material = db.get(MaterialRevision, entity_id)
        local_inspection = local_audio_qc and not require_model_use and material.material.kind == "audio"
        if (material.status not in {"candidate", "usable", "active"} or material.material.status != "active"
                or require_model_use and material.model_use_allowed is not True
                or material.rights_status == "revoked"
                or not local_inspection and not (material.public_use_allowed is True or material.model_use_allowed is True)):
            _conflict("stage_accepted_material_rights_changed")
        read_bytes_checked(db, material)
        _check_derived_rights(db, material)
        result["asset_refs"] = [{"material_revision_id": entity_id, "content_hash": material.content_hash}]
        result["payload"] = {"material_revision_id": entity_id, "content_hash": material.content_hash, "mime_type": material.mime_type}
    elif kind == "channel_variant_revision":
        from . import channel_variants
        from .creative_packages import _check_asset

        row = db.get(ChannelVariantRevision, entity_id)
        if channel_variants._drift_reasons(db, row):
            _conflict("stage_accepted_variant_context_changed")
        projection = channel_variants._serialize(db, row)
        for ref in projection["assets"]:
            if require_model_use:
                _check_asset(db, row.project_id, ref)
        master = db.get(ContentMasterRevision, row.source_master_revision_id)
        from .stage_master_adoptions import _live_refs

        _live_refs(db, master, require_model_use=require_model_use)
        result.update(payload=canonical(row.payload_json), asset_refs=projection["assets"],
                      evidence_refs=projection["evidence"])
    elif kind in {"creative_execution", "creative_execution_package"}:
        from .creative_packages import owned_package

        package = db.get(CreativeExecutionPackage, entity_id) if kind == "creative_execution_package" else db.get(
            CreativeExecutionPackage, db.get(CreativeExecution, entity_id).package_id)
        actor = db.get(User, package.owner_user_id)
        if actor is None:
            _conflict("stage_accepted_professional_owner_unavailable")
        owned_package(db, package.project_id, package.content_unit_id, package.id, actor, current=True)
        result["payload"] = {"package_id": package.id, "package_hash": package.package_hash,
                             "preparation_only": True, "professional_dispatch_required": True}
    else:
        attempt = db.get(WorkflowStepAttempt, entity_id)
        if target["domain"] == "audio_asr":
            from .stage_audio_asr import validate_asr_result

            validate_asr_result(db, attempt.output_json["result"])
        if target["domain"] == "checks":
            from .content_masters import check_requirements

            body = attempt.output_json["result"]
            if body.get("checks_pass") is not True and body.get("checks_reviewable") is not True:
                _conflict("stage_checks_blocked")
            _check_dispositions(body["checks"], target.get("warning_dispositions"))
            if body.get("audio_quality") is True:
                from .stage_audio import validate_qc_result

                validate_qc_result(db, body)
            else:
                _check_rows(db, body, requirements=check_requirements(db, db.get(
                    ContentMasterRevision, body["master_revision_id"])))
                # Full reports remain at the exact CheckRun; forwarding render bytes and
                # duplicate current-check reports makes an otherwise bounded stage overflow.
                result["payload"] = {
                    "schema": "stage.checks.handoff.v1",
                    "master_revision_id": body["master_revision_id"],
                    "checks_pass": body["checks_pass"],
                    "checks_reviewable": body.get("checks_reviewable", False),
                    "blockers": body.get("blockers", []),
                    "checks": [{
                        "id": check["id"], "check_kind": check["check_kind"],
                        "input_hash": check["input_hash"], "status": check["status"],
                        "report_hash": digest(check["report"]),
                        "report": {key: value for key, value in check["report"].items()
                                   if key in {"reasons", "warnings", "issues", "coverage", "persona_quality"}},
                    } for check in body["checks"]],
                }
        if "payload" not in result:
            result["payload"] = attempt.output_json["result"]
    return canonical(result)


def _current(db, project_id, unit_id, node_id, user, run, step, attempt, resolved, request):
    project, unit = owned_unit(db, project_id, unit_id, user, mutate=True)
    db.refresh(run)
    db.refresh(step)
    _assert_access(db, run, user)
    recovered_media = (request["domain"] == "media" and step.status == "unknown"
                       and attempt.status == "unknown")
    if (run.workflow_id != unit.pinned_workflow_id or run.identity_snapshot_id != unit.identity_snapshot_id
            or step.attempt_no != attempt.attempt_no or not (step.status == "waiting_input" or recovered_media)
            or step.output_hash != attempt.output_hash or step.output_json != attempt.output_json):
        _conflict("stage_attempt_not_current")
    if db.scalar(select(ProjectWorkflowOutput.id).where(ProjectWorkflowOutput.attempt_id == attempt.id).limit(1)):
        _conflict("stage_already_accepted")
    current, blockers = creation_recipes._context(db, project, unit, run)
    if resolved.get("node", {}).get("plugin") == "media.generate" and resolved["node"].get("plugin_version") == "4":
        from .stage_audio import prepare_tts, tts_request

        current, effective, audio_blockers = prepare_tts(db, user, unit, resolved["node"], resolved["effective_config"], current)
        blockers.extend(audio_blockers)
        if not audio_blockers and tts_request(effective, current) != tts_request(resolved["effective_config"], resolved["context"]):
            _conflict("stage_audio_tts_config_changed")
    frozen = {key: value for key, value in resolved["context"].items() if key != "domain"}
    if blockers or current != frozen or digest(resolved["context"]) != request["expected_context_hash"]:
        _conflict("stage_adoption_context_changed")
    return project, unit


def _persist(db, project_id, unit_id, user, run, step, attempt, resolved, request, fingerprint,
             kind, entity, accepted_hash, extra=None):
    from .stage_feedback import invalidate_downstream, record_feedback

    _current(db, project_id, unit_id, step.node_id, user, run, step, attempt, resolved, request)
    verified, _, _ = _sealed(db, run, step, attempt, request, user.email)
    if request["domain"] == "media":
        _visible_sources(db, project_id, resolved["context"]["domain"]["request"]["source_revision_ids"])
        if verified.get("recovery_proof"):
            extra = {**(extra or {}), "media_recovery_proof": verified["recovery_proof"]}
    provenance = canonical({"schema": "creation_recipe.domain_adoption.v1", "domain": request["domain"],
        "project_id": project_id, "unit_id": unit_id, "workflow_id": run.workflow_id,
        "workflow_version": run.workflow_version, "workflow_checksum": run.definition_checksum,
        "run_id": run.id, "node_id": step.node_id, "attempt_id": attempt.id,
        "attempt_no": attempt.attempt_no, "plugin_key": attempt.plugin_key, "plugin_version": attempt.plugin_version,
        "config_hash": resolved["config_hash"], "prompt_hash": resolved["prompt_hash"],
        "resolution_hash": resolved["resolution_hash"], "context_hash": resolved["context_hash"],
        "output_hash": attempt.output_hash, "result_kind": kind, "result_id": entity.id,
        "accepted_payload_hash": accepted_hash, "decision": request["decision"],
        "adoption_key": request["adoption_key"], "adoption_fingerprint": fingerprint,
        "actor_id": user.id, "actor_email": user.email,
        "accepted_revision": getattr(entity, "revision_no", 0), **(extra or {})})
    output = ProjectWorkflowOutput(project_id=project_id, unit_id=unit_id, run_id=run.id,
        node_id=step.node_id, attempt_id=attempt.id, output_kind=kind, entity_id=entity.id,
        provenance_json=provenance, created_at=utcnow())
    db.add(output)
    db.flush()
    provenance = {**provenance, "project_output_id": output.id}
    output.provenance_json = provenance
    if kind == "channel_variant_revision":
        entity.edit_summary_json = {**(entity.edit_summary_json or {}), "stage_provenance": provenance}
    elif kind == "material_revision":
        entity.metadata_json = {**(entity.metadata_json or {}), "stage_provenance": provenance}
    record_feedback(db, project_id=project_id, unit_id=unit_id, run=run, step=step, attempt=attempt,
        user=user, decision=request["decision"], result_kind=kind, result_id=entity.id,
        accepted_hash=accepted_hash, project_output_id=output.id, note=request.get("note", ""),
        reason_tags=request.get("reason_tags", []), feedback_key="stage-adopt:" + digest(request["adoption_key"]),
        extra={key: value for key, value in provenance.items() if key != "schema"})
    invalidate_downstream(db, run, step, accepted_hash)
    step.status, step.error = "succeeded", None
    db.flush()
    statuses = db.scalars(select(WorkflowStep.status).where(WorkflowStep.run_id == run.id)).all()
    run.status = "succeeded" if all(status == "succeeded" for status in statuses) else "running"
    run.error = None
    run.finished_at = utcnow() if run.status == "succeeded" else None
    db.flush()
    if accepted_domain_target(db, output) is None:
        _conflict()
    return output


def accept_result(db, project_id, unit_id, node_id, user, request):
    require_receipt_schema(db)
    request = canonical(request, max_bytes=128 * 1024)
    if not IDENTIFIER.fullmatch(request.get("adoption_key", "")):
        raise StageInvocationError("stage_adoption_key_invalid", status_code=422)
    try:
        _, _, _, run = creation_recipes._workflow(db, project_id, unit_id, user, request["run_id"])
        _assert_access(db, run, user, mutate=False)
        owned_unit(db, project_id, unit_id, user, mutate=True)
        step = db.scalar(select(WorkflowStep).where(WorkflowStep.run_id == run.id, WorkflowStep.node_id == node_id))
        if step is None:
            raise StageInvocationError("stage_not_found", status_code=404)
        db.execute(update(WorkflowStep).where(WorkflowStep.id == step.id)
                   .values(attempt_no=WorkflowStep.attempt_no).execution_options(synchronize_session=False))
        db.refresh(step)
        attempt = db.get(WorkflowStepAttempt, request["attempt_id"])
        output, resolved, _ = _sealed(db, run, step, attempt, request, user.email)
        if request["domain"] == "variant":
            from .channel_variant_documents import canonical_payload

            request["payload"] = canonical_payload(output["result"]["payload_schema"], request["payload"],
                asset_refs=request["asset_refs"], evidence_refs=request["evidence_refs"])
        fingerprint = digest({"request": request, "project_id": project_id, "unit_id": unit_id,
                              "node_id": node_id, "actor_id": user.id})
        prior = db.scalars(select(ProjectWorkflowOutput).where(ProjectWorkflowOutput.run_id == run.id,
            ProjectWorkflowOutput.node_id == node_id, ProjectWorkflowOutput.unit_id == unit_id,
            ProjectWorkflowOutput.provenance_json["adoption_key"].as_string() == request["adoption_key"])).all()
        if prior:
            if len(prior) != 1 or prior[0].provenance_json.get("adoption_fingerprint") != fingerprint:
                _conflict("stage_adoption_key_conflict")
            target = accepted_domain_target(db, prior[0])
            if target is None:
                _conflict()
            db.commit()
            return _response(db, run, node_id, target, user)
        _project, unit = _current(db, project_id, unit_id, node_id, user, run, step, attempt, resolved, request)
        domain, result = request["domain"], output["result"]
        accepted = {}

        def save_acceptance(entity, kind, value, extra=None):
            row = _persist(db, project_id, unit_id, user, run, step, attempt, resolved, request,
                           fingerprint, kind, entity, value, extra)
            accepted["output_id"] = row.id

        if domain == "media":
            from . import generation_tasks

            task = _media_task(db, attempt, resolved, result)
            candidate_index = request.get("candidate_index", 0)
            if type(candidate_index) is not int or not 0 <= candidate_index <= 3:
                _conflict("multimedia_candidate_selection_invalid")
            selected_hash = task.result_hash
            if task.plan_json.get("parameters", {}).get("items", 1) > 1:
                manifest = generation_tasks._batch_manifest(task, required=True)
                if candidate_index >= len(manifest["candidates"]):
                    _conflict("stage_media_candidate_invalid")
                selected_hash = manifest["candidates"][candidate_index]["hash"]
            if (request.get("task_id") != task.id or task.owner_user_id != user.id
                    or task.state not in {"result_ready", "accepted"}
                    or request["expected_revision"] != task.revision
                    or request.get("expected_result_hash") != selected_hash):
                _conflict("stage_media_result_changed")
            if request["decision"] != "accepted":
                raise StageInvocationError("stage_media_edits_unavailable", status_code=422)
            rights = request["rights"]
            generation_tasks.accept(db, user, task.id, request["expected_revision"],
                {**rights, "candidate_index": candidate_index},
                stage_adoption=lambda material: save_acceptance(material, "material_revision", material.content_hash,
                    {"task_id": task.id, "task_request_hash": task.request_hash, "task_result_hash": task.result_hash,
                     "rights_hash": task.acceptance_hash}))
        elif domain == "variant":
            from . import channel_variants
            from .channel_variant_documents import canonical_payload

            payload = canonical_payload(result["payload_schema"], request["payload"],
                asset_refs=request["asset_refs"], evidence_refs=request["evidence_refs"])
            edited = (payload != result["payload"] or request["asset_refs"] != result["asset_refs"]
                      or request["evidence_refs"] != result["evidence_refs"])
            if request["decision"] != ("accepted_with_edits" if edited else "accepted"):
                raise StageInvocationError("stage_acceptance_decision_mismatch", status_code=422)
            if request["expected_revision"] != result["expected_revision"]:
                _conflict("stage_variant_revision_conflict")
            current, _, reasons = prepare_domain(db, user, unit, resolved["node"], resolved["effective_config"],
                                                  {key: value for key, value in resolved["context"].items() if key != "domain"})
            if reasons or current["domain"] != resolved["context"]["domain"]:
                _conflict("stage_variant_context_changed")
            save = {"variant_key": result["variant_key"], "expected_revision": request["expected_revision"],
                "source_master_revision_id": result["source_master_revision_id"],
                "expected_source_payload_hash": result["source_payload_hash"],
                "expected_source_context_hash": result["source_context_hash"],
                "expected_profile_hash": result["profile_hash"], "channel_id": result["channel_id"],
                "content_form": result["content_form"], "payload": payload,
                "asset_refs": request["asset_refs"], "evidence_refs": request["evidence_refs"],
                "idempotency_key": "stage-adopt:" + digest({"run_id": run.id, "node_id": node_id, "key": request["adoption_key"]}),
                "source_kind": "manual_edit" if edited else "model_assisted" if result.get("llm_run_id") else "deterministic_adapt",
                "edit_summary": {"stage_source_output_hash": attempt.output_hash, "original_llm_run_id": result.get("llm_run_id")}}
            if result.get("llm_run_id") and not edited:
                save["llm_provenance"] = {"llm_run_id": result["llm_run_id"]}
            channel_variants.save_revision(db, project_id=project_id, unit_id=unit_id, user=user, payload=save,
                stage_adoption=lambda variant: save_acceptance(variant, "channel_variant_revision", variant.payload_hash))
        elif domain == "professional":
            from .creative_packages import owned_package

            entity, value = _professional_entity(db, resolved, result)
            if (request["decision"] != "accepted" or request.get("package_id") != result["package_id"]
                    or request.get("execution_id") != result.get("execution_id")
                    or request["expected_revision"] != result["expected_revision"]):
                _conflict("stage_professional_choice_changed")
            owned_package(db, project_id, unit_id, result["package_id"], user, current=True, mutate=True)
            if isinstance(entity, CreativeExecution) and (
                    entity.state != "prepared" or entity.dispatch_certainty != "not_dispatched"
                    or entity.revision_no != request["expected_revision"]):
                _conflict("stage_professional_preparation_changed")
            kind = "creative_execution" if isinstance(entity, CreativeExecution) else "creative_execution_package"
            save_acceptance(entity, kind, value)
            db.commit()
        else:
            if request["decision"] != "accepted" or request["expected_revision"] != 0:
                raise StageInvocationError("stage_review_choice_invalid", status_code=422)
            if domain == "checks":
                from .content_masters import check_requirements, current_checks

                if result.get("audio_quality") is True:
                    from .stage_audio import validate_qc_result

                    checks = validate_qc_result(db, result)
                else:
                    _check_rows(db, result, requirements=check_requirements(db, db.get(ContentMasterRevision, result["master_revision_id"])))
                    checks = current_checks(db, project_id, unit_id, result["master_revision_id"], user)
                if not checks or any(not item["is_current"] for item in checks):
                    _conflict("stage_checks_blocked")
                _check_dispositions(checks, request.get("warning_dispositions"))
            save_acceptance(attempt, "workflow_step_attempt", output["result_hash"],
                {"warning_dispositions": request.get("warning_dispositions") or {}} if domain == "checks" else None)
            db.commit()
        target = accepted_domain_target(db, db.get(ProjectWorkflowOutput, accepted["output_id"]))
        if target is None:
            _conflict()
        return _response(db, run, node_id, target, user)
    except BaseException:
        db.rollback()
        raise


def _response(db, run, node_id, target, user):
    from .stage_continuation import continue_after_acceptance

    continuation = continue_after_acceptance(db, run_id=run.id, accepted_node_id=node_id,
        accepted_hash=target["accepted_hash"], accepted_output_id=target["project_output_id"],
        accepted_attempt_id=target["attempt_id"], accepted_decision=target["decision"], user=user)
    return {"schema": "creation_recipe.domain_acceptance.v1", "accepted_target": target,
            "accepted_entity": accepted_entity_projection(db, target, user),
            "project_output_id": target["project_output_id"], "feedback_event_id": target["feedback_event_id"],
            "decision": target["decision"], "continuation": continuation}
