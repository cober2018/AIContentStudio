"""Read-only Workflow projections and authoritative Stage request preparation."""

import hashlib
import hmac
import json

from fastapi import HTTPException
from sqlalchemy import select

from ..models import (
    AccountWorkflowDefault,
    ContentMasterAssetRef,
    ContentMasterEvidenceRef,
    ContentMasterRevision,
    ContentUnit,
    FactPack,
    FactPackItem,
    IdentitySnapshot,
    PersonaWorkflowDefault,
    ProjectEvent,
    ProjectWorkflowBinding,
    ProjectWorkflowOutput,
    SeriesWorkflowDefault,
    Workflow,
    WorkflowRun,
    WorkflowStep,
    WorkflowStepAttempt,
)
from .content_harness.registry import RegistryError, registry
from .content_masters import owned_unit
from .project_authorization import authorize_project_run, authorize_project_workflow
from .project_brief import current_brief, serialize_brief
from .project_evidence import current_boundary
from .stage_contracts import StageContractError, canonical, digest
from .stage_resolver import resolve_stage
from .workflow_engine import definition_checksum


def _workflow(db, project_id, unit_id, user, run_id=None):
    project, unit = owned_unit(db, project_id, unit_id, user)
    run = db.get(WorkflowRun, run_id) if run_id is not None else None
    if run_id is not None:
        if run is None or run.content_unit_id != unit.id:
            raise HTTPException(404, "运行不存在")
        authorize_project_run(db, run, user)
    workflow_id = run.workflow_id if run else unit.pinned_workflow_id
    workflow = db.get(Workflow, workflow_id) if workflow_id else None
    if workflow is None:
        return project, unit, None, run
    authorize_project_workflow(db, workflow, user)
    if workflow.checksum != definition_checksum(workflow.definition_json):
        raise HTTPException(409, {"code": "recipe_definition_integrity"})
    if run and (run.definition_checksum != workflow.checksum or run.workflow_version != workflow.version):
        raise HTTPException(409, {"code": "recipe_run_integrity"})
    return project, unit, workflow, run


def _default(db, unit):
    for model, column, entity_id, source in (
        (SeriesWorkflowDefault, SeriesWorkflowDefault.series_id, unit.series_id, "series"),
        (AccountWorkflowDefault, AccountWorkflowDefault.account_id, unit.account_id, "account"),
        (PersonaWorkflowDefault, PersonaWorkflowDefault.persona_id, unit.persona_id, "persona"),
    ):
        if entity_id:
            row = db.scalar(select(model).where(column == entity_id, model.modality == unit.modality))
            if row:
                return row, source
    return None, None


def _definition_diff(before, after):
    left = {node["id"]: node for node in before.get("nodes", [])}
    right = {node["id"]: node for node in after.get("nodes", [])}
    return {
        "added_node_ids": sorted(set(right) - set(left)), "removed_node_ids": sorted(set(left) - set(right)),
        "changed_node_ids": sorted(key for key in set(left) & set(right) if left[key] != right[key]),
        "visual_order_changed": before.get("visual_order") != after.get("visual_order"),
        "dependencies_changed": before.get("edges") != after.get("edges"),
    }


def _descriptor(node):
    try:
        return registry.descriptor("node", node.get("plugin"), node.get("plugin_version"))
    except RegistryError:
        return None


def accepted_stage_target(db, run, node_id, *, project_output_id=None, accepted_attempt_id=None,
                          accepted_hash=None, accepted_decision=None):
    """Return the latest verified accepted entity for one Stage dependency."""

    if run is None or run.content_unit_id is None:
        return None
    unit = db.get(ContentUnit, run.content_unit_id)
    if unit is None:
        return None
    step = db.scalar(select(WorkflowStep).where(WorkflowStep.run_id == run.id, WorkflowStep.node_id == node_id))
    if step is not None and step.plugin_key == "stage.creative.method" and step.plugin_version == "1":
        if project_output_id is not None:
            return None
        attempt = (db.get(WorkflowStepAttempt, accepted_attempt_id) if accepted_attempt_id is not None else
            db.scalar(select(WorkflowStepAttempt).where(WorkflowStepAttempt.step_id == step.id)
                      .order_by(WorkflowStepAttempt.attempt_no.desc()).limit(1)))
        if attempt is None or attempt.status != "succeeded":
            return None
        from .creative_method_stage import accepted_handoff
        return accepted_handoff(db, run, step, attempt, accepted_hash=accepted_hash, accepted_decision=accepted_decision)
    query = select(ProjectWorkflowOutput).where(
        ProjectWorkflowOutput.run_id == run.id,
        ProjectWorkflowOutput.unit_id == run.content_unit_id,
        ProjectWorkflowOutput.node_id == node_id,
    )
    if project_output_id is not None:
        query = query.where(ProjectWorkflowOutput.id == project_output_id)
    if accepted_attempt_id is not None:
        query = query.where(ProjectWorkflowOutput.attempt_id == accepted_attempt_id)
    if project_output_id is None and accepted_attempt_id is None:
        step = db.scalar(select(WorkflowStep).where(WorkflowStep.run_id == run.id, WorkflowStep.node_id == node_id))
        attempt = db.scalar(select(WorkflowStepAttempt).where(WorkflowStepAttempt.step_id == step.id)
                            .order_by(WorkflowStepAttempt.attempt_no.desc()).limit(1)) if step else None
        if attempt is None or not (attempt.status == "succeeded" or attempt.status == "unknown"
                                  and attempt.plugin_key == "media.generate" and attempt.plugin_version in {"2", "3"}):
            return None
        query = query.where(ProjectWorkflowOutput.attempt_id == attempt.id)
    rows = db.scalars(query.order_by(ProjectWorkflowOutput.id.desc()).limit(20)).all()
    matches = []
    for row in rows:
        provenance = row.provenance_json or {}
        events = db.scalars(select(ProjectEvent).where(
            ProjectEvent.project_id == row.project_id,
            ProjectEvent.event_type == "creation_recipe.stage_feedback",
            ProjectEvent.entity_id == str(row.attempt_id),
            ProjectEvent.payload_json["project_output_id"].as_integer() == row.id,
            ProjectEvent.payload_json["decision"].as_string().in_(["accepted", "accepted_with_edits"]),
            ProjectEvent.payload_json["adoption_fingerprint"].as_string() == provenance.get("adoption_fingerprint"),
        )).all()
        event = events[0] if len(events) == 1 else None
        payload = event.payload_json if event else {}
        if (row.project_id != unit.project_id or event is None or payload.get("project_output_id") != row.id
                or payload.get("result_id") != row.entity_id
                or payload.get("decision") not in {"accepted", "accepted_with_edits"}
                or accepted_decision is not None and payload.get("decision") != accepted_decision
                or payload.get("accepted_hash") != provenance.get("accepted_payload_hash")):
            continue
        if accepted_hash is not None and payload.get("accepted_hash") != accepted_hash:
            continue
        if row.output_kind == "content_master_revision":
            master = db.get(ContentMasterRevision, row.entity_id)
            if (master is None or master.content_unit_id != run.content_unit_id
                    or master.payload_hash != payload.get("accepted_hash")
                    or master.payload_hash != digest(master.payload_json)):
                continue
            from .stage_invocations import StageInvocationError
            from .stage_master_adoptions import _accepted_result
            try:
                _accepted_result(db, master, master.edit_summary_json.get("stage_provenance") or {})
            except (StageInvocationError, StageContractError, KeyError, TypeError):
                continue
            matches.append(canonical({
                "node_id": node_id, "output_kind": row.output_kind, "entity_id": master.id,
                "attempt_id": row.attempt_id, "decision": payload["decision"],
                "payload_schema": master.payload_schema, "revision_no": master.revision_no,
                "payload_hash": master.payload_hash, "accepted_hash": payload["accepted_hash"],
                "context_hash": master.context_hash, "project_output_id": row.id,
            }))
            continue
        from .stage_domain_adoptions import accepted_domain_target
        from .stage_invocations import StageInvocationError
        try:
            target = accepted_domain_target(db, row)
        except (StageInvocationError, StageContractError, HTTPException, KeyError, TypeError, ValueError):
            continue
        if target is not None:
            matches.append(target)
    return matches[0] if len(matches) == 1 else None


def recipe_view(db, project_id, unit_id, user, *, run_id=None):
    project, unit, workflow, run = _workflow(db, project_id, unit_id, user, run_id)
    readonly = project.status == "archived" or unit.status == "archived" or user.role not in {"editor", "admin"}
    if workflow is None:
        return {"workflow_id": None, "source": "unbound", "stages": [], "history": [], "readonly": readonly}
    binding = db.scalar(select(ProjectWorkflowBinding).where(ProjectWorkflowBinding.unit_id == unit.id))
    default, default_source = _default(db, unit)
    default_workflow = db.get(Workflow, default.workflow_id) if default else None
    if default_workflow:
        authorize_project_workflow(db, default_workflow, user)
    source = "project_override" if binding and binding.workflow_id == workflow.id else workflow.scope or "workflow"
    if run is None:
        run = db.scalar(select(WorkflowRun).where(WorkflowRun.content_unit_id == unit.id,
            WorkflowRun.workflow_id == workflow.id).order_by(WorkflowRun.id.desc()).limit(1))
    readonly = readonly or bool(run and (run.workflow_id != unit.pinned_workflow_id
                                        or run.identity_snapshot_id != unit.identity_snapshot_id))
    steps = {row.node_id: row for row in db.scalars(select(WorkflowStep).where(
        WorkflowStep.run_id == run.id)).all()} if run else {}
    nodes = {node["id"]: node for node in workflow.definition_json.get("nodes", [])}
    order = workflow.definition_json.get("visual_order") or list(nodes)
    stages = []
    for node_id in order:
        node, step = nodes[node_id], steps.get(node_id)
        descriptor = _descriptor(node)
        contract = descriptor.stage_contract.to_dict() if descriptor and descriptor.stage_contract else None
        attempt = db.scalar(select(WorkflowStepAttempt).where(WorkflowStepAttempt.step_id == step.id)
            .order_by(WorkflowStepAttempt.attempt_no.desc(), WorkflowStepAttempt.id.desc()).limit(1)) if step else None
        accepted = accepted_stage_target(db, run, node_id) if run else None
        outputs = db.scalars(select(ProjectWorkflowOutput).where(ProjectWorkflowOutput.run_id == run.id,
            ProjectWorkflowOutput.node_id == node_id).order_by(ProjectWorkflowOutput.id.desc()).limit(10)).all() if run else []
        product_stale = False
        if attempt:
            committed = current_brief(db, project.id)
            frozen_brief = ((attempt.input_snapshot_json or {}).get("resolved_stage", {}).get("context", {}).get("brief") or {})
            product_stale = bool(committed and committed.product_context_json and frozen_brief
                                 and frozen_brief.get("checksum") != committed.checksum)
        stages.append({
            "node_id": node_id, "kind": node.get("kind", node.get("type")),
            "plugin": node.get("plugin"), "plugin_version": str(node.get("plugin_version") or "1"),
            "base_config": descriptor.stage_contract.validate_config(node.get("config", {})) if contract else None,
            "label": canonical(node.get("label") or (contract or {}).get("title") or node_id),
            "mode": "stage" if contract else "advanced_legacy", "controls": contract,
            "status": "stale" if product_stale else step.status if step else "not_started", "requires_human_acceptance":
                contract["requires_human_acceptance"] if contract else None,
            "readiness": "readonly" if readonly else "preview_required" if contract else "advanced_legacy",
            "dependencies": [edge["from"] for edge in workflow.definition_json.get("edges", []) if edge["to"] == node_id],
            "last_attempt": {"id": attempt.id, "attempt_no": attempt.attempt_no, "status": attempt.status,
                "input_hash": attempt.input_hash, "output_hash": attempt.output_hash} if attempt else None,
            "accepted_target": accepted, "associated_outputs": [{"id": item.id, "kind": item.output_kind,
                "entity_id": item.entity_id, "attempt_id": item.attempt_id} for item in outputs],
            "blockers": (["historical_or_archived"] if readonly else []) + (["product_inputs_changed"] if product_stale else []) + ([step.error] if step and step.error else []),
            "local_dirty": None,
        })
    history = db.scalars(select(Workflow).where(Workflow.workflow_key == workflow.workflow_key,
        Workflow.owner_user_id == workflow.owner_user_id).order_by(Workflow.version.desc()).limit(50)).all() if workflow.workflow_key else [workflow]
    # Registry contracts are independently bounded; read wrappers must not consume their input-depth budget.
    result = canonical({
        "schema": "creation.recipe.v1", "workflow_id": workflow.id, "workflow_version": workflow.version,
        "definition_checksum": workflow.checksum, "source": source,
        "source_revision": binding.revision if binding and binding.workflow_id == workflow.id else workflow.version,
        "readonly": readonly, "run_id": run.id if run else None,
        "stages": [{**stage, "controls": None} for stage in stages],
        "inherited_default": {"source": default_source, "revision": default.revision, "workflow_id": default.workflow_id,
            "checksum": default_workflow.checksum, "diff": _definition_diff(default_workflow.definition_json,
                workflow.definition_json)} if default and default_workflow else None,
        "history": [{"workflow_id": item.id, "version": item.version, "checksum": item.checksum,
            "parent_id": item.parent_id, "diff": _definition_diff(workflow.definition_json, item.definition_json)}
            for item in history],
    })
    for stage, source_stage in zip(result["stages"], stages):
        stage["controls"] = canonical(source_stage["controls"], max_bytes=32 * 1024)
    if len(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()) > 128 * 1024:
        raise StageContractError("stage_value_too_large")
    return result


def stage_result(db, project_id, unit_id, node_id, user, *, run_id, attempt_id=None, invocation_key=None):
    from .stage_invocations import (
        StageInvocationError,
        _attempts,
        _execution_result,
        _same_key_result,
        require_receipt_schema,
    )

    project, unit, _, run = _workflow(db, project_id, unit_id, user, run_id)
    require_receipt_schema(db)
    if (attempt_id is None) == (invocation_key is None):
        raise StageInvocationError("stage_result_selector_required", status_code=422)
    step = db.scalar(select(WorkflowStep).where(WorkflowStep.run_id == run.id, WorkflowStep.node_id == node_id))
    attempt = db.get(WorkflowStepAttempt, attempt_id) if attempt_id is not None else None
    if invocation_key is not None and step is not None:
        attempt = next((item for item in _attempts(db, step.id)
                        if (item.execution_receipt_json or {}).get("invocation_key") == invocation_key), None)
    if (step is None or attempt is None or attempt.step_id != step.id
            or attempt.run_id != run.id or attempt.node_id != node_id):
        raise StageInvocationError("stage_attempt_not_found", status_code=404)
    receipt = attempt.execution_receipt_json or {}
    if receipt.get("schema") != "creation_recipe.execution_receipt.v1":
        raise StageInvocationError("stage_receipt_unavailable", status_code=409)
    verified = _same_key_result(db, step, receipt.get("invocation_key"), receipt.get("request_fingerprint"))
    if verified is None or verified.id != attempt.id:
        raise StageInvocationError("stage_attempt_integrity", status_code=409)
    resolved = (attempt.input_snapshot_json or {}).get("resolved_stage") or {}
    accepted = accepted_stage_target(db, run, node_id, accepted_attempt_id=attempt.id)
    from .content_masters import _serialize
    accepted_master = (_serialize(db, db.get(ContentMasterRevision, accepted["entity_id"]))
                       if accepted and accepted["output_kind"] == "content_master_revision" else None)
    from .stage_domain_adoptions import accepted_entity_projection
    from .stage_domain_integrations import domain_output
    from .stage_feedback import allowed_decisions
    accepted_entity = accepted_entity_projection(db, accepted, user) if accepted else None
    domain = (resolved.get("context") or {}).get("domain") or {}
    projected = domain_output(db, attempt, user)
    recovered_media = (domain.get("kind") == "media" and step.status == "unknown"
                       and ((projected or {}).get("live") or {}).get("state") in {"result_ready", "accepted"})
    return {**_execution_result(run, step, attempt), "resolved_stage": resolved,
            "expected_context_hash": digest(resolved.get("context")),
            "expected_revision": domain.get("expected_revision",
                (resolved.get("context", {}).get("master") or {}).get("revision_no", 0)),
            "is_current": project.status != "archived" and unit.status != "archived"
                and run.workflow_id == unit.pinned_workflow_id and run.identity_snapshot_id == unit.identity_snapshot_id
                and step.attempt_no == attempt.attempt_no and (step.status in {"waiting_input", "succeeded"} or recovered_media),
            "accepted_target": accepted, "accepted_master": accepted_master,
            "domain_output": projected, "accepted_entity": accepted_entity,
            "allowed_decisions": [] if project.status == "archived" else allowed_decisions(
                db, unit, run, step, attempt, user)}


def _model(config):
    from .generation.providers import LLMError, _models_override, effective_llm_config

    try:
        models = _models_override()
        # Creative purpose is prompt text, not a registered model route.
        purpose = "generate"
        intended = config.get("model_profile_id") or (models.get("routes") or {}).get(purpose) or models.get("default_profile")
        # Passing the selected route explicitly prevents legacy fallback from substituting a different model.
        if intended is not None and (type(intended) is not str or not intended):
            return None, ["model_profile_unavailable"]
        actual = effective_llm_config(purpose, profile=intended)
        if intended is not None and actual["profile"] != intended:
            return None, ["model_profile_unavailable"]
    except LLMError:
        return None, ["model_profile_unavailable"]
    provider = actual["provider"]
    if provider not in {"mock", "openai_compatible"} or provider != "mock" and not all(
            actual.get(key) for key in ("model", "base_url", "api_key")):
        return None, ["model_runtime_unavailable"]
    return _model_projection(actual), []


def _model_projection(actual):
    from .model_capability_routing import _PLAN_SIGNING_KEY

    provider = actual["provider"]
    # Reuse the routing process's continuity key; no endpoint/credential enters public projections.
    runtime_hash = hmac.new(_PLAN_SIGNING_KEY, json.dumps(actual, sort_keys=True,
        separators=(",", ":")).encode(), hashlib.sha256).hexdigest()
    return {"profile_id": actual["profile"], "provider": provider,
        "model": "mock-structured-v1" if provider == "mock" else actual["model"],
        "adapter_key": f"generation.{provider}", "adapter_version": "1", "runtime_hash": runtime_hash,
        "configuration_revision": actual.get("configuration_revision"), "status": "configured_not_probed"}


def _method(db, user, unit, node, config):
    selected = config.get("method")
    if selected is None:
        return {"source_kind": "builtin", "key": node["plugin"], "version": str(node["plugin_version"]),
                "instruction": "严格遵守已固定身份、任务与事实约束；输出仅为待人工接受的候选。"}, []
    if type(selected) is not dict:
        raise StageContractError("stage_method_selection_invalid")
    kind = selected.get("source_kind")
    if kind == "studio_builtin":
        from .studio_creative_catalog import SKILLS, load_skill, validate_ref

        if set(selected) != {"source_kind", "skill_ref"}:
            raise StageContractError("stage_method_selection_invalid")
        try:
            ref = validate_ref(selected["skill_ref"], kind="skill")
        except ValueError as exc:
            raise StageContractError(str(exc)) from None
        resource = SKILLS.get(ref)
        if resource is None:
            return None, ["studio_skill_unavailable"]
        if node.get("stage_schema") not in resource["compatible_stage_schemas"]:
            return None, ["studio_skill_stage_incompatible"]
        if node["plugin"] == "stage.creative.method" and config.get("output_schema") not in resource["output_schemas"]:
            return None, ["studio_skill_output_incompatible"]
        if (node["plugin"] == "stage.professional.prepare"
                and config.get("package_schema") not in resource["output_schemas"]):
            return None, ["studio_skill_output_incompatible"]
        try:
            package = load_skill(ref)
        except ValueError as exc:
            return None, [str(exc)]
        return {"source_kind": kind, "skill_ref": ref, "key": resource["key"],
                "version": resource["version"], "resource_hash": digest(resource),
                "package_hash": package["package_hash"], "contract_hash": digest(package["contract"]),
                "provenance": package["provenance"], "instruction": package["instruction"]}, []
    if kind == "capability_memory":
        from . import capability_memory
        from .capability_contracts import render
        from .workflow_stage_recipes import deterministic_recipe

        if set(selected) == {"source_kind", "artifact_id", "revision_id", "arguments_json"}:
            try:
                arguments = canonical(json.loads(selected["arguments_json"]), max_bytes=4000)
            except (ValueError, TypeError):
                raise StageContractError("stage_method_arguments_invalid") from None
            if type(arguments) is not dict:
                raise StageContractError("stage_method_arguments_invalid")
            selected = {key: value for key, value in selected.items() if key != "arguments_json"}
            selected["arguments"] = arguments
        elif set(selected) == {"source_kind", "artifact_id", "revision_id"}:
            selected = {**selected, "arguments": {}}
        if set(selected) != {"source_kind", "artifact_id", "revision_id", "arguments"}:
            raise StageContractError("stage_method_selection_invalid")
        artifact = capability_memory.get_artifact(db, user, selected["artifact_id"])
        if artifact["status"] not in {"saved", "pinned"} or artifact["kind"] not in {"recipe", "prompt_skill"}:
            return None, ["method_not_saved"]
        revisions = capability_memory.revisions(db, user, artifact["id"])["items"]
        revision = next((item for item in revisions if item["id"] == selected["revision_id"]), None)
        if revision is None or revision["metadata"].get("status") not in {"saved", "pinned"}:
            return None, ["method_revision_unavailable"]
        expected = {"owner": user.id, "project": unit.project_id, "persona": unit.persona_id,
                    "account": unit.account_id, "series": unit.series_id}
        def applies(scope_type, scope):
            return not (scope_type in expected and scope.get("id") != expected[scope_type]
                or scope_type == "channel" and scope.get("channel_id") != unit.channel_id
                or scope_type == "executor" and (scope.get("executor_kind") != "node"
                    or scope.get("executor_key") != node["plugin"]
                    or scope.get("executor_version") != str(node["plugin_version"])))
        frozen = revision["metadata"]
        if not applies(artifact["scope_type"], artifact["scope"]) or not applies(frozen["scope_type"], frozen["scope"]):
            return None, ["method_scope_mismatch"]
        rendered, args_hash = render(revision["content"], revision["args_schema"], selected["arguments"])
        method = {"source_kind": kind, "artifact_id": artifact["id"], "revision_id": revision["id"],
            "content_hash": revision["content_hash"], "arguments_hash": args_hash,
            "metadata_hash": digest(frozen), "matched_scope": {"scope_type": frozen["scope_type"], "scope": frozen["scope"]},
            "current_restrictions": {"status": artifact["status"], "scope_type": artifact["scope_type"], "scope": artifact["scope"]},
            "rendered_hash": digest(rendered), "instruction": json.dumps(rendered, ensure_ascii=False, sort_keys=True)}
        # Deterministic tools may consume only a validated, typed workflow recipe.
        # Free-form Capability Memory instructions remain instructions for AI stages;
        # they must never become hidden layout or provider behavior.
        try:
            recipe = deterministic_recipe(rendered, node)
        except (ValueError, KeyError):
            recipe = None
        if recipe is not None:
            method["deterministic_parameters"] = recipe["config_patch"]
            method["deterministic_recipe"] = {
                "content_schema": recipe["content_schema"], "node_id": recipe["node_id"],
                "plugin": recipe["plugin"], "plugin_version": recipe["plugin_version"],
                "stage_schema": recipe["stage_schema"],
            }
        return method, []
    if kind == "installed_agent_skill":
        from .capability_memory import installed_skills
        from .content_harness.skill_runtime import _enabled_skills

        if set(selected) != {"source_kind", "skill_id", "version", "runtime_key", "runtime_version"}:
            raise StageContractError("stage_method_selection_invalid")
        skill = next((item for item in installed_skills(db, user)["items"] if item["id"] == selected["skill_id"]), None)
        if skill is None or skill["version"] != selected["version"]:
            return None, ["installed_skill_unavailable"]
        gated, enabled = _enabled_skills(db)
        if gated and skill["name"] not in enabled:
            return None, ["installed_skill_disabled"]
        try:
            runtime = registry.resolve("skill_runtime", selected["runtime_key"], selected["runtime_version"])
        except RegistryError:
            return None, ["skill_runtime_unavailable"]
        # Existing inventory/runtime metadata does not prove an exact skill executable binding.
        identities = getattr(runtime, "stage_skill_bindings", None)
        if type(identities) is not dict:
            return None, ["skill_runtime_identity_unverified"]
        value = identities.get(skill["id"])
        if (type(value) is not dict or value.get("executable") is not True
                or value.get("descriptor_hash") != digest(skill) or not value.get("runtime_hash")):
            return None, ["skill_runtime_unavailable"]
        # A descriptor binding alone does not provide the Stage invocation/receipt adapter.
        plugin = registry.resolve("node", node["plugin"], node["plugin_version"])
        if (not callable(getattr(runtime, "execute_stage", None))
                or not callable(getattr(plugin, "execute_skill_resolved", None))):
            return None, ["installed_skill_stage_execution_unavailable"]
        return {"source_kind": kind, "skill_id": skill["id"], "version": skill["version"],
            "descriptor_hash": digest(skill), "runtime_key": selected["runtime_key"],
            "runtime_version": selected["runtime_version"], "runtime_hash": value["runtime_hash"],
            "instruction": skill["description"]}, []
    raise StageContractError("stage_method_selection_invalid")


def _context(db, project, unit, run):
    from .factpack_service import pack_snapshot_checksum, snapshot_checksum

    blockers = []
    snapshot_id = run.identity_snapshot_id if run else unit.identity_snapshot_id
    identity = db.get(IdentitySnapshot, snapshot_id) if snapshot_id else None
    if identity and identity.owner_user_id != project.owner_user_id:
        raise HTTPException(409, {"code": "stage_identity_integrity"})
    brief, boundary = current_brief(db, project.id), current_boundary(db, project.id)
    if brief and brief.product_context_json:
        from ..models import MaterialRevision
        from .project_brief import validate_product_context

        try:
            product = validate_product_context(db, brief.product_context_json)
            if any(not db.get(MaterialRevision, r["material_revision_id"]).model_use_allowed for r in product["material_refs"]):
                blockers.append("product_material_model_use_required")
        except (HTTPException, ValueError):
            blockers.append("product_evidence_unavailable")
    master = db.scalar(select(ContentMasterRevision).where(ContentMasterRevision.content_unit_id == unit.id)
        .order_by(ContentMasterRevision.revision_no.desc()).limit(1))
    context = {
        "project_id": project.id, "unit_id": unit.id, "modality": unit.modality, "channel": unit.channel_id,
        "run_id": run.id if run else None,
        "identity": {"id": identity.id, "checksum": identity.checksum,
                     "content": identity.effective_profile_json} if identity else None,
        "brief": {"id": brief.id, "checksum": brief.checksum, "content": {
            key: value for key, value in serialize_brief(brief).items()
            if key not in {"created_by", "created_at", "references"}}} if brief else None,
        "master": {"id": master.id, "payload_schema": master.payload_schema,
                   "revision_no": master.revision_no, "content_form": master.content_form,
                   "payload_hash": master.payload_hash, "context_hash": master.context_hash} if master else None,
        "intent": {"hash": master.creative_intent_hash, "content": master.creative_intent_json}
                  if master and master.creative_intent_json else None,
        "boundary": None,
        "asset_refs": [{"material_revision_id": ref.material_revision_id,
            "content_hash": ref.content_hash_snapshot, "role": ref.role, "slot_key": ref.slot_key,
            "sort_order": ref.sort_order, "placement": ref.placement_json}
            for ref in db.scalars(select(ContentMasterAssetRef).where(
                ContentMasterAssetRef.master_revision_id == master.id
            ).order_by(ContentMasterAssetRef.sort_order, ContentMasterAssetRef.id).limit(101)).all()] if master else [],
        "evidence_refs": [{"fact_pack_item_id": ref.fact_pack_item_id, "snapshot_checksum": ref.snapshot_checksum,
            "role": ref.role, "sort_order": ref.sort_order, "content_locator_json": ref.content_locator_json}
            for ref in db.scalars(select(ContentMasterEvidenceRef).where(
                ContentMasterEvidenceRef.master_revision_id == master.id
            ).order_by(ContentMasterEvidenceRef.sort_order, ContentMasterEvidenceRef.id).limit(101)).all()] if master else [],
    }
    if any(len(context[key]) > 100 for key in ("asset_refs", "evidence_refs")):
        blockers.append("stage_master_refs_limit")
    if unit.modality == "text":
        from .obsidian_knowledge import stage_context

        knowledge, knowledge_blockers = stage_context(db, unit, run)
        if knowledge is not None:
            context["knowledge_context"] = knowledge
        blockers.extend(knowledge_blockers)
    workflow = db.get(Workflow, run.workflow_id if run else unit.pinned_workflow_id) if (run or unit.pinned_workflow_id) else None
    if workflow and any(node.get("plugin") == "stage.graphic.compose" for node in workflow.definition_json.get("nodes", [])):
        from ..models import MaterialRevision, ProjectMaterialReference
        from .content_masters import _verified_generated_asset
        from .materials import read_bytes_checked
        from .project_assets import shared_assets

        items = shared_assets(db, project.id)
        eligible, excluded, seen = [], [], set()
        for item in items:
            revision_id = item["material_revision_id"]
            if revision_id in seen or len(seen) >= 100:
                continue
            seen.add(revision_id)
            material = db.get(MaterialRevision, revision_id)
            reference = db.get(ProjectMaterialReference, item["reference_id"]) if item.get("reference_id") else None
            output = db.get(ProjectWorkflowOutput, item["project_output_id"]) if item.get("project_output_id") else None
            reason = None
            if (material is None or material.status in {"revoked", "archived", "rejected"}
                    or material.material.status != "active" or material.material.kind not in {"image", "chart"}
                    or material.public_use_allowed is not True or material.model_use_allowed is not True):
                reason = "shared_visual_rights_unavailable"
            elif not (reference and reference.project_id == project.id and reference.status == "active"
                    or output and output.project_id == project.id and _verified_generated_asset(db, output, material)):
                reason = "shared_visual_lineage_unverified"
            else:
                try:
                    from .creative_packages import _check_derived_rights

                    _check_derived_rights(db, material)
                    read_bytes_checked(db, material, require_public=True)
                except (HTTPException, OSError):
                    reason = "shared_visual_bytes_unavailable"
            if reason:
                excluded.append({"material_revision_id": revision_id, "reason": reason})
            else:
                eligible.append({"material_revision_id": revision_id, "content_hash": material.content_hash,
                    "kind": material.material.kind, "mime_type": material.mime_type})
        context["shared_asset_refs"] = sorted(eligible, key=lambda item: item["material_revision_id"])
        context["shared_assets_coverage"] = {"limit": 100, "truncated": len({item["material_revision_id"] for item in items}) > 100,
            "excluded": sorted(excluded, key=lambda item: item["material_revision_id"])}
    if master:
        if master.payload_hash != digest(master.payload_json):
            blockers.append("stage_master_payload_integrity")
        context["master"] = {**context["master"], "payload": canonical(master.payload_json),
                             "asset_refs": context["asset_refs"], "evidence_refs": context["evidence_refs"]}
    if boundary:
        pack = db.get(FactPack, boundary.fact_pack_id)
        if (pack is None or pack.status != "frozen" or pack.checksum != boundary.fact_pack_checksum
                or pack.version != boundary.fact_pack_version):
            blockers.append("fact_boundary_changed")
        else:
            items = db.scalars(select(FactPackItem).where(FactPackItem.fact_pack_id == pack.id)
                .order_by(FactPackItem.sort_order, FactPackItem.id).limit(101)).all()
            if len(items) > 100:
                blockers.append("evidence_preview_limit")
            included, excluded = [], []
            intact = len(items) <= 100 and pack_snapshot_checksum(items) == pack.checksum and all(
                type(item.snapshot_json) is dict and item.snapshot_json
                and snapshot_checksum(item.snapshot_json) == item.snapshot_checksum for item in items)
            if len(items) <= 100 and not intact:
                blockers.append("evidence_integrity")
            # Never place an unverified frozen snapshot into the request, even when execution is blocked.
            for item in items if intact else []:
                if item.public_use_revoked_at is not None:
                    blockers.append("evidence_revoked")
                if item.model_use_allowed is not True or item.public_use_revoked_at is not None:
                    excluded.append({"item_id": item.id, "reason": "revoked" if item.public_use_revoked_at else "model_use_not_allowed"})
                elif not item.snapshot_checksum or not item.snapshot_json:
                    blockers.append("evidence_snapshot_missing")
                else:
                    fact = item.fact if item.evidence_kind in {"fact", "event"} else None
                    source = fact.source_document if fact else None
                    source_verified = bool(source and not source.is_archived
                        and source.id == item.snapshot_json.get("source_id"))
                    included.append({"item_id": item.id, "checksum": item.snapshot_checksum,
                                     "kind": item.evidence_kind, "snapshot": item.snapshot_json,
                                     "fresh_source_verified": source_verified})
            context["boundary"] = {"id": boundary.id, "revision": boundary.revision_no,
                "fact_pack_id": pack.id, "fact_pack_version": pack.version, "checksum": pack.checksum,
                "items": included, "excluded": excluded}
    if project.status == "archived" or unit.status == "archived":
        blockers.append("archived_readonly")
    if run and (run.workflow_id != unit.pinned_workflow_id or run.identity_snapshot_id != unit.identity_snapshot_id):
        blockers.append("historical_context_readonly")
    if run and run.status in {"canceled", "cancelled"}:
        blockers.append("run_cancelled")
    return context, blockers


def preview_stage(db, project_id, unit_id, node_id, user, *, run_id=None, stage_override=None):
    project, unit, workflow, run = _workflow(db, project_id, unit_id, user, run_id)
    node = next((node for node in workflow.definition_json.get("nodes", []) if node.get("id") == node_id), None) if workflow else None
    if node is None:
        raise HTTPException(404, "阶段不存在")
    descriptor = _descriptor(node)
    if descriptor is None or descriptor.stage_contract is None:
        raise HTTPException(409, {"code": "legacy_stage_preview_unsupported"})
    contract = descriptor.stage_contract
    stage_override = {} if stage_override is None else stage_override
    context, blockers = _context(db, project, unit, run)
    from .creative_configuration import frozen_stage
    node, creative_method, creative, creative_blockers = frozen_stage(
        db, user, unit, node, contract, context, stage_override)
    if context.get("identity") and isinstance(context["identity"].get("content"), dict):
        identity_content = context["identity"]["content"]
        manifests = identity_content.get("product_production_methods")
        if manifests is not None:
            # The snapshot retains every stage; this execution carries its selected stage and source hashes.
            context["identity"] = {**context["identity"], "content": {
                **{key: value for key, value in identity_content.items() if key not in {"product_production_methods", "product_production_stages"}},
                "product_production_manifest_refs": {key: value["manifest_hash"] for key, value in manifests.items()},
            }}
    _, config, _ = contract.effective_config(node.get("config", {}), stage_override)
    if node.get("enabled") is False:
        blockers.append("stage_disabled")
    if user.role == "viewer":
        blockers.append("viewer_readonly")
    from .stage_domain_integrations import domain_for, prepare_domain
    context, domain_model, domain_blockers = prepare_domain(db, user, unit, node, config, context, creative=creative)
    model, model_blockers = (_model(config) if node["kind"] == "AI" and domain_for(node) is None else (domain_model, []))
    if node["kind"] == "AI" and model is not None and context.get("master"):
        from .stage_invocations import StageInvocationError
        from .stage_master_adoptions import _live_refs
        try:
            _live_refs(db, db.get(ContentMasterRevision, context["master"]["id"]), require_model_use=True)
        except StageInvocationError as exc:
            blockers.append(exc.code)
    method, method_blockers = (creative_method, []) if creative is not None else _method(db, user, unit, node, config)
    upstream = {}
    if "domain" in context:
        upstream["__domain_input__"] = context["domain"]
    elif context.get("master"):
        master = db.get(ContentMasterRevision, context["master"]["id"])
        upstream["__current_master__"] = {"payload_schema": master.payload_schema,
            "payload_hash": master.payload_hash, "payload": canonical(master.payload_json),
            "asset_refs": context["asset_refs"], "evidence_refs": context["evidence_refs"]}
    for edge in workflow.definition_json.get("edges", []):
        if edge["to"] != node_id:
            continue
        step = db.scalar(select(WorkflowStep).where(WorkflowStep.run_id == run.id,
            WorkflowStep.node_id == edge["from"])) if run else None
        proposal_waiting_review = False
        if step is not None and step.status == "waiting_input":
            latest_attempt = db.scalar(select(WorkflowStepAttempt).where(
                WorkflowStepAttempt.step_id == step.id,
            ).order_by(WorkflowStepAttempt.attempt_no.desc(), WorkflowStepAttempt.id.desc()).limit(1))
            proposal_waiting_review = latest_attempt is not None and latest_attempt.status == "succeeded"
        if step is None or (step.status != "succeeded" and not proposal_waiting_review):
            blockers.append("upstream_not_succeeded")
            continue
        if contract.to_dict()["input_contract"].get("upstream", "accepted") == "accepted":
            accepted = accepted_stage_target(db, run, edge["from"])
            if accepted is None:
                # Success alone never releases content; only the immutable
                # ProjectWorkflowOutput + feedback proof can do so.
                blockers.append("upstream_acceptance_required")
                continue
            if accepted["output_kind"] == "creative_attempt":
                from .creative_method_stage import selected_input
                from .stage_invocations import StageInvocationError
                from .studio_creative_catalog import SKILLS
                selected_method = config.get("method") or {}
                selected_skill = SKILLS.get(selected_method.get("skill_ref"), {})
                try:
                    upstream[edge["from"]] = selected_input(db, accepted,
                        include_content=selected_skill.get("requires_selected_upstream") is True)
                except (StageInvocationError, HTTPException) as exc:
                    blockers.append(exc.code if isinstance(exc, StageInvocationError) else "accepted_creative_input_unavailable")
                continue
            if accepted["output_kind"] != "content_master_revision":
                from .stage_domain_adoptions import accepted_domain_input
                from .stage_invocations import StageInvocationError
                try:
                    upstream[edge["from"]] = accepted_domain_input(db, accepted,
                        require_model_use=node["kind"] == "AI",
                        local_audio_qc=node["plugin"] == "stage.audio.qc" and str(node.get("plugin_version")) == "1")
                except (StageInvocationError, HTTPException) as exc:
                    blockers.append(exc.code if isinstance(exc, StageInvocationError) else "accepted_domain_input_unavailable")
                continue
            from . import content_masters
            master = db.get(ContentMasterRevision, accepted["entity_id"])
            if content_masters._serialize(db, master)["readiness"]["state"] == "stale":
                blockers.append("accepted_context_changed")
                continue
            from .stage_invocations import StageInvocationError
            from .stage_master_adoptions import _live_refs
            try:
                _live_refs(db, master, require_model_use=node["kind"] == "AI")
            except StageInvocationError as exc:
                blockers.append(exc.code)
                continue
            if (creative is not None and node["plugin"] == "stage.master.propose" and "__current_master__" in upstream
                    and master.id == context["master"]["id"]):
                # The exact current payload is already present; retain adoption lineage
                # without copying the same document into the final-stage prompt twice.
                upstream[edge["from"]] = {**accepted, "payload_ref": "__current_master__"}
            else:
                upstream[edge["from"]] = {**accepted, "payload": canonical(master.payload_json)}
            continue
        upstream[edge["from"]] = {"node_id": edge["from"], "output_hash": step.output_hash,
                                  "output": step.output_json}
    resolved = resolve_stage(workflow={"id": workflow.id, "version": workflow.version, "checksum": workflow.checksum},
        node=node, contract=contract, context=context, upstream=upstream, method=method, model=model,
        override=stage_override, creative=creative,
        blockers=[*blockers, *model_blockers, *method_blockers, *domain_blockers, *creative_blockers])
    from .stage_domain_integrations import native_media_resolution

    return native_media_resolution(resolved)
