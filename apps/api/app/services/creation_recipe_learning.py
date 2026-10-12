"""Explicitly preserve successful Stage tuning in existing versioned domains."""

from copy import deepcopy

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from ..models import (
    AccountWorkflowDefault,
    CapabilityUse,
    ContentUnit,
    PersonaWorkflowDefault,
    ProjectEvent,
    ProjectWorkflowBinding,
    SeriesWorkflowDefault,
    Workflow,
)
from . import capability_memory, content_identity, creation_recipes
from .content_masters import owned_unit
from .project_authorization import lock_project_context
from .project_events import record_project_event
from .project_workflows import new_workflow_version, validate_definition, validate_portable, validate_reusable_profiles
from .stage_contracts import IDENTIFIER, canonical, digest
from .stage_feedback import attempt_context, feedback_events
from .stage_invocations import StageInvocationError

DEFAULTS = {"persona": (PersonaWorkflowDefault, "persona_id"),
            "account": (AccountWorkflowDefault, "account_id"), "series": (SeriesWorkflowDefault, "series_id")}


def _binding(db, unit, destination):
    if destination == "project":
        return db.scalar(select(ProjectWorkflowBinding).where(ProjectWorkflowBinding.unit_id == unit.id))
    model, field = DEFAULTS[destination]
    identity_id = getattr(unit, field)
    return db.scalar(select(model).where(getattr(model, field) == identity_id, model.modality == unit.modality))


def _destination(db, unit, user, destination, scope_id=None):
    if destination not in {"project", "capability", *DEFAULTS}:
        raise StageInvocationError("recipe_destination_invalid", status_code=422)
    if destination in DEFAULTS:
        identity_id = getattr(unit, DEFAULTS[destination][1])
        if identity_id is None or scope_id is not None and scope_id != identity_id:
            raise StageInvocationError("recipe_destination_scope_mismatch", status_code=422)
        content_identity.owned_entity(db, user, destination, identity_id, mutable=False)
    return _binding(db, unit, destination) if destination != "capability" else None


def _diff(before, after):
    missing = {"unset": True}
    return [{"field": key, "before": before.get(key, missing), "after": after.get(key, missing)}
            for key in sorted(set(before) | set(after)) if before.get(key, missing) != after.get(key, missing)]


def _definition_diff(db, binding, definition):
    previous = db.get(Workflow, binding.workflow_id) if binding else None
    before = previous.definition_json if previous else {"nodes": [], "edges": [], "visual_order": []}
    left, right = ({node["id"]: node for node in value["nodes"]} for value in (before, definition))
    return {"replaces_entire_default": True, "previous_workflow_id": previous.id if previous else None,
        "previous_checksum": previous.checksum if previous else None,
        "nodes": [{"node_id": key, "change": "added" if key not in left else "removed" if key not in right else "modified",
                   "fields": _diff(left.get(key, {}), right.get(key, {}))}
                  for key in sorted(set(left) | set(right)) if left.get(key) != right.get(key)],
        "edges": {"before": before["edges"], "after": definition["edges"]},
        "visual_order": {"before": before["visual_order"], "after": definition["visual_order"]}}


def _replace_config(workflow, node_id, patch):
    definition = deepcopy(workflow.definition_json)
    node = next((node for node in definition["nodes"] if node["id"] == node_id), None)
    if node is None:
        raise StageInvocationError("recipe_stage_not_found", status_code=404)
    descriptor = creation_recipes._descriptor(node)
    if descriptor is None or descriptor.stage_contract is None:
        raise StageInvocationError("recipe_stage_contract_required", status_code=422)
    _, effective, _ = descriptor.stage_contract.effective_config(node.get("config") or {}, patch)
    node["config"] = effective
    return validate_definition(definition), node


def _validate_methods(db, user, unit, definition, destination):
    default_scopes = {
        "persona": {"owner", "persona", "executor"},
        "account": {"owner", "persona", "account", "executor"},
        "series": {"owner", "persona", "account", "series", "executor"},
    }
    for node in definition["nodes"]:
        config = node.get("config") or {}
        method = config.get("method")
        descriptor = creation_recipes._descriptor(node)
        if method is None or descriptor is None or descriptor.stage_contract is None:
            continue
        if method.get("source_kind") not in descriptor.stage_contract.to_dict()["method_sources"]:
            raise StageInvocationError("recipe_method_source_not_supported", status_code=422)
        _, blockers = creation_recipes._method(db, user, unit, node, config)
        if blockers:
            raise StageInvocationError("recipe_method_unavailable")
        if destination in DEFAULTS and method["source_kind"] == "capability_memory":
            artifact = capability_memory.get_artifact(db, user, method["artifact_id"])
            revision = next(item for item in capability_memory.revisions(db, user, artifact["id"])["items"]
                            if item["id"] == method["revision_id"])
            if any(scope not in default_scopes[destination] for scope in (
                    artifact["scope_type"], revision["metadata"]["scope_type"])):
                raise StageInvocationError("recipe_method_default_scope_mismatch", status_code=422)


def _accepted_feedback(db, project_id, run, step, attempt, feedback_id):
    events = feedback_events(db, project_id, attempt.id)
    event = next((event for event in events if event.id == feedback_id), None) if feedback_id else next(
        (event for event in reversed(events) if event.payload_json.get("decision") in {"accepted", "accepted_with_edits"}), None)
    if event is None or event.payload_json.get("decision") not in {"accepted", "accepted_with_edits"}:
        raise StageInvocationError("recipe_accepted_feedback_required", status_code=422)
    target = creation_recipes.accepted_stage_target(db, run, step.node_id,
        project_output_id=event.payload_json.get("project_output_id"), accepted_attempt_id=attempt.id,
        accepted_hash=event.payload_json.get("accepted_hash"), accepted_decision=event.payload_json.get("decision"))
    if target is None:
        raise StageInvocationError("recipe_feedback_integrity")
    return event, target


def _creative_method_scope(db, unit):
    from ..models import IdentitySnapshot

    snapshot = db.get(IdentitySnapshot, unit.identity_snapshot_id) if unit.identity_snapshot_id else None
    if not snapshot or not any(snapshot.effective_profile_json.get(f"{modality}_creative_profile")
                               for modality in ("text", "graphic", "audio", "video")):
        return None
    if any(getattr(snapshot, key) != getattr(unit, key) for key in ("persona_id", "account_id", "series_id")):
        raise StageInvocationError("recipe_identity_scope_mismatch")
    for kind, identity_id in (("series", unit.series_id), ("account", unit.account_id), ("persona", unit.persona_id)):
        if identity_id:
            return {"scope_type": kind, "scope": {"id": identity_id}}
    return {"scope_type": "project", "scope": {"id": unit.project_id}}


def improvement_preview(db, project_id, unit_id, node_id, user, request):
    request = canonical(request, max_bytes=32 * 1024)
    _, unit, run, step, attempt, resolved = attempt_context(db, project_id, unit_id, node_id, user, request)
    event, target = _accepted_feedback(db, project_id, run, step, attempt, request.get("feedback_event_id"))
    workflow = db.get(Workflow, run.workflow_id)
    destination = request.get("destination", "project")
    binding = _destination(db, unit, user, destination, request.get("scope_id"))
    if unit.pinned_workflow_id != workflow.id:
        raise StageInvocationError("recipe_base_no_longer_current")
    base, effective = resolved["base_config"], resolved["effective_config"]
    patch = {key: effective[key] for key in resolved.get("override", {}) if effective.get(key) != base.get(key)}
    patch_source = "accepted_override" if patch else "content_feedback_only"
    if request.get("tuning_suggestion_id") is not None:
        from .stage_tuning import verified_patch

        patch = verified_patch(db, user, unit_id, node_id, workflow, request)
        node = next(item for item in workflow.definition_json["nodes"] if item["id"] == node_id)
        base, effective, patch = creation_recipes._descriptor(node).stage_contract.effective_config(node.get("config") or {}, patch)
        patch = {key: value for key, value in patch.items() if value != base.get(key)}
        patch_source = "model_suggestion"
    elif "config_patch" in request:
        authored = request["config_patch"]
        node = next(item for item in workflow.definition_json["nodes"] if item["id"] == node_id)
        contract = creation_recipes._descriptor(node).stage_contract
        if patch:
            if authored != patch:
                raise StageInvocationError("recipe_patch_not_executed", status_code=422)
        else:
            allowed = {"instruction", "method"} & set(contract.to_dict()["tunable_fields"])
            if type(authored) is not dict or not authored or set(authored) - allowed:
                raise StageInvocationError("recipe_authored_method_required", status_code=422)
            base, effective, patch = contract.effective_config(node.get("config") or {}, authored)
            patch = {key: value for key, value in patch.items() if value != base.get(key)}
            patch_source = "user_authored"
    definition, node = _replace_config(workflow, node_id, patch)
    _validate_methods(db, user, unit, definition, destination)
    if destination in DEFAULTS:
        definition = validate_portable(definition, source_project_id=project_id, source_unit_id=unit_id)
        validate_reusable_profiles(db, definition, user=user)
    result = canonical({"schema": "creation_recipe.improvement_preview.v1", "destination": destination,
        "scope_id": getattr(unit, DEFAULTS[destination][1]) if destination in DEFAULTS else project_id,
        "unit_id": unit_id, "run_id": run.id, "attempt_id": attempt.id, "node_id": node_id,
        "workflow_id": workflow.id, "workflow_checksum": workflow.checksum,
        "feedback_event_id": event.id, "feedback_hash": digest(event.payload_json),
        "accepted_hash": target["accepted_hash"], "config_patch": patch, "diff": _diff(base, effective),
        "has_config_change": bool(patch), "content_only": not patch,
        "patch_source": patch_source, "executed_patch": patch_source == "accepted_override" and bool(patch),
        "expected_revision": binding.revision if binding else 0,
        "destination_workflow_id": binding.workflow_id if binding else None,
        "definition_diff": _definition_diff(db, binding, definition) if destination in DEFAULTS else None,
        "definition": definition, "definition_hash": digest(definition),
        "destinations": [{"key": value, "scope_id": getattr(unit, DEFAULTS[value][1]) if value in DEFAULTS else project_id}
                         for value in ["project", *DEFAULTS, "capability"]
                         if value not in DEFAULTS or getattr(unit, DEFAULTS[value][1]) is not None],
        "tuning_suggestion_id": request.get("tuning_suggestion_id"),
        "message": "仅修改正文不构成流程配置调整。请明确编写指令、选择方法，或调节后重新运行并接受。" if not patch else None,
        "attempt_evidence": {"attempt_id": attempt.id, "resolution_hash": attempt.input_hash,
            "config_hash": attempt.execution_receipt_json["config_hash"],
            "prompt_hash": attempt.execution_receipt_json["prompt_hash"],
            "output_hash": attempt.output_hash, "accepted_hash": target["accepted_hash"]},
        "node": {key: node[key] for key in ("id", "plugin", "plugin_version", "stage_schema")}})
    creative_scope = _creative_method_scope(db, unit) if destination == "capability" else None
    if creative_scope:
        result["method_scope"] = creative_scope
    result["preview_hash"] = digest(result)
    return result


def _event_replay(db, project_id, event_type, key, fingerprint):
    rows = db.scalars(select(ProjectEvent).where(ProjectEvent.project_id == project_id,
        ProjectEvent.event_type == event_type).order_by(ProjectEvent.id.desc())).all()
    for event in rows:
        data = event.payload_json or {}
        if data.get("idempotency_key") == key:
            if data.get("fingerprint") != fingerprint:
                raise StageInvocationError("recipe_idempotency_conflict")
            return data["result"]
    return None


def _write_binding(db, *, unit, user, definition, destination, expected_revision, name):
    binding = _destination(db, unit, user, destination)
    revision = binding.revision if binding else 0
    if type(expected_revision) is not int or expected_revision != revision:
        raise StageInvocationError("recipe_revision_conflict")
    content_identity.hierarchy(db, user, persona_id=unit.persona_id, account_id=unit.account_id,
                              series_id=unit.series_id, mutable=True)
    definition = validate_definition(definition)
    _validate_methods(db, user, unit, definition, destination)
    if destination in DEFAULTS:
        definition = validate_portable(definition, source_project_id=unit.project_id, source_unit_id=unit.id)
        validate_reusable_profiles(db, definition, user=user)
        entity_id = getattr(unit, DEFAULTS[destination][1])
        key, scope = f"{destination}.{entity_id}.{unit.modality}", f"{destination}_default"
    else:
        key, scope = f"project.unit.{unit.id}", "project"
    workflow = new_workflow_version(db, key=key, name=name[:200], definition=definition,
                                   owner_user_id=user.id, scope=scope, created_by=user.email)
    if binding:
        changed = db.execute(update(type(binding)).where(type(binding).id == binding.id,
            type(binding).revision == expected_revision).values(workflow_id=workflow.id, revision=revision + 1)
            .execution_options(synchronize_session=False))
        if changed.rowcount != 1:
            raise StageInvocationError("recipe_revision_conflict")
    else:
        model = ProjectWorkflowBinding if destination == "project" else DEFAULTS[destination][0]
        fields = {"unit_id": unit.id} if destination == "project" else {
            DEFAULTS[destination][1]: getattr(unit, DEFAULTS[destination][1]), "modality": unit.modality}
        db.add(model(**fields, workflow_id=workflow.id, revision=1))
    if destination == "project":
        previous = unit.pinned_workflow_id
        changed = db.execute(update(ContentUnit).where(ContentUnit.id == unit.id,
            ContentUnit.pinned_workflow_id == previous).values(pinned_workflow_id=workflow.id)
            .execution_options(synchronize_session=False))
        if changed.rowcount != 1:
            raise StageInvocationError("recipe_revision_conflict")
        db.refresh(unit)
    db.flush()
    return {"destination": destination, "workflow_id": workflow.id, "workflow_version": workflow.version,
            "definition_checksum": workflow.checksum, "revision": revision + 1}


def _key(request, user, *, project_id, unit_id, node_id=None):
    key = request.get("idempotency_key")
    if type(key) is not str or not IDENTIFIER.fullmatch(key):
        raise StageInvocationError("recipe_idempotency_key_required", status_code=422)
    return key, digest({"actor_id": user.id, "project_id": project_id, "unit_id": unit_id,
                        "node_id": node_id, "request": request})


def save_adjustment(db, project_id, unit_id, node_id, user, request):
    request = canonical(request, max_bytes=32 * 1024)
    key, fingerprint = _key(request, user, project_id=project_id, unit_id=unit_id, node_id=node_id)
    try:
        lock_project_context(db, project_id, user)
        _, unit = owned_unit(db, project_id, unit_id, user, mutate=True)
        if user.role not in {"editor", "admin"} or not user.is_active:
            raise StageInvocationError("recipe_readonly", status_code=403)
        replay = _event_replay(db, project_id, "creation_recipe.adjustment_saved", key, fingerprint)
        if replay is not None:
            return replay
        preview = improvement_preview(db, project_id, unit_id, node_id, user, request)
        if preview["preview_hash"] != request.get("expected_preview_hash"):
            raise StageInvocationError("recipe_improvement_preview_changed")
        if not preview["config_patch"]:
            raise StageInvocationError("recipe_explicit_config_change_required", status_code=422)
        if request.get("expected_revision") != preview["expected_revision"]:
            raise StageInvocationError("recipe_revision_conflict")
        name = request.get("name") or f"{unit.title} · 有效调整"
        if type(name) is not str or not 1 <= len(name) <= 200:
            raise StageInvocationError("recipe_name_invalid", status_code=422)
        if preview["destination"] == "capability":
            capability_memory._ready(db)
            node = preview["node"]
            content = {"content_schema": "workflow.stage.recipe.v1",
                "base_workflow_checksum": preview["workflow_checksum"], "node_id": node_id,
                "plugin": node["plugin"], "plugin_version": node["plugin_version"],
                "stage_schema": node["stage_schema"], "config_patch": preview["config_patch"],
                "feedback_evidence": [{"event_id": preview["feedback_event_id"], "event_hash": preview["feedback_hash"]}],
                "attempt_evidence": [preview["attempt_evidence"]]}
            method_kind = request.get("method_kind", "recipe")
            if method_kind == "prompt_skill":
                instruction = preview["config_patch"].get("instruction")
                if not instruction:
                    raise StageInvocationError("recipe_prompt_adjustment_required", status_code=422)
                content = {"instruction": instruction, "stage_origin": {
                    "workflow_checksum": preview["workflow_checksum"], "node_id": node_id,
                    "feedback_event_id": preview["feedback_event_id"], "feedback_hash": preview["feedback_hash"]}}
            elif method_kind != "recipe":
                raise StageInvocationError("recipe_method_kind_invalid", status_code=422)
            scope = preview.get("method_scope") or {"scope_type": "project", "scope": {"id": project_id}}
            result = capability_memory._create(db, user, {"kind": method_kind, "name": name,
                "content": content, "args_schema": {}, **scope},
                provenance={"source_kind": "creation_recipe_feedback", "feedback_event_id": preview["feedback_event_id"],
                            "feedback_hash": preview["feedback_hash"], "patch_source": preview["patch_source"],
                            **({"persona_id": unit.persona_id, "account_id": unit.account_id, "series_id": unit.series_id,
                                "identity_snapshot_id": unit.identity_snapshot_id} if preview.get("method_scope") else {})},
                dedupe=True, candidate_only=True)
            result = {"destination": "capability", "artifact": result, "status": "candidate"}
        else:
            result = _write_binding(db, unit=unit, user=user, definition=preview["definition"],
                destination=preview["destination"], expected_revision=preview["expected_revision"], name=name)
        record_project_event(db, project_id=project_id, event_type="creation_recipe.adjustment_saved",
            actor=user.email, entity_type="workflow_stage", entity_id=node_id,
            payload={"unit_id": unit_id, "idempotency_key": key, "fingerprint": fingerprint,
                     "preview_hash": preview["preview_hash"], "feedback_event_id": preview["feedback_event_id"],
                     "config_patch": preview["config_patch"], "patch_source": preview["patch_source"],
                     "executed_patch": preview["executed_patch"], "result": result})
        db.commit()
        return result
    except IntegrityError:
        db.rollback()
        raise StageInvocationError("recipe_revision_conflict") from None
    except BaseException:
        db.rollback()
        raise


def method_inventory(db, project_id, unit_id, user):
    from .. import runtime_config
    from .generation.providers import LLMError, effective_llm_config

    _, unit = owned_unit(db, project_id, unit_id, user)
    configured = runtime_config.get_runtime(runtime_config.KEY_MODELS) or {}
    from .model_capability_routing import configuration_view

    capabilities = configuration_view(db)["profiles"]
    profiles = []
    for profile_id, data in (configured.get("profiles") or {}).items():
        try:
            actual = effective_llm_config("generate", profile=profile_id)
            available = actual["provider"] in {"mock", "openai_compatible"} and (
                actual["provider"] == "mock" or bool(actual.get("base_url") and actual.get("api_key") and actual.get("model")))
        except LLMError:
            available = False
        declared = capabilities.get(profile_id, {}).get("capabilities", {})
        profiles.append({"id": profile_id, "label": data.get("model") or profile_id,
                         "model": data.get("model"), "provider": data.get("provider_id") or data.get("provider"),
                         "capabilities": {key: {"declared": value.get("declared", False),
                             "configured": value.get("configured", False), "state": value.get("state"),
                             "reason": value.get("reason")} for key, value in declared.items()},
                         "available": available, "reason": None if available else "模型未配置或聊天路由不可用"})
    if not profiles:
        model, blockers = creation_recipes._model({})
        if model:
            profiles.append({"id": model["profile_id"], "label": model["model"], "available": not blockers})
    methods = []
    for kind in ("recipe", "prompt_skill"):
        offset = 0
        while True:
            page = capability_memory.discover(db, user, {"project_id": project_id, "unit_id": unit_id,
                                                        "kind": kind, "limit": 20, "offset": offset})
            for artifact in page["items"]:
                revision = artifact["current_revision"]
                methods.append({"source_kind": "capability_memory", "artifact_id": artifact["id"],
                    "revision_id": revision["id"], "name": artifact["name"], "kind": kind,
                    "status": artifact["status"], "matched_scope": artifact["matched_scope"],
                    "content_schema": revision["content"].get("content_schema"),
                    "arguments_schema": revision["args_schema"], "selection": {"source_kind": "capability_memory",
                        "artifact_id": artifact["id"], "revision_id": revision["id"], "arguments": {}}})
            offset += page["limit"]
            if offset >= page["total"]:
                break
    installed = [{**item, "available": False, "reason": "已安装清单不是经过验证的Stage执行绑定"}
                 for item in capability_memory.installed_skills(db, user)["items"]]
    media_profiles = []
    # Native capability profiles need not have a separate chat-model registration.
    for profile_id, profile in capabilities.items():
        bindings = profile.get("capability_bindings", {})
        states = {key: {name: value.get(name) for name in
                  ("declared", "configured", "executable", "verified", "reason")}
                  | {"state": "executable" if value.get("executable") else "unavailable",
                     "provider": bindings.get(key, {}).get("adapter_key"),
                     "model": bindings.get(key, {}).get("model_id")}
                  for key, value in profile.get("capabilities", {}).items() if key != "chat"}
        media_profiles.append({"id": profile_id,
            "label": (configured.get("profiles") or {}).get(profile_id, {}).get("model") or profile_id,
            "capabilities": states, "available": any(state.get("declared") and state.get("executable")
                                                        for state in states.values())})
    return {"model_profiles": profiles, "methods": methods, "installed_skills": installed,
            "media_profiles": media_profiles,
            "auto_select": False, "unit_id": unit.id}


def apply_method_preview(db, project_id, unit_id, node_id, user, request):
    from .workflow_stage_recipes import validate_recipe

    _, unit, workflow, _ = creation_recipes._workflow(db, project_id, unit_id, user)
    if workflow is None:
        raise StageInvocationError("recipe_workflow_required")
    artifact = capability_memory.get_artifact(db, user, request.get("artifact_id"))
    revision = next((item for item in capability_memory.revisions(db, user, artifact["id"])["items"]
                     if item["id"] == request.get("revision_id")), None)
    if (revision is None or artifact["kind"] != "recipe" or artifact["status"] not in {"saved", "pinned"}
            or revision["metadata"].get("status") not in {"saved", "pinned"}):
        raise StageInvocationError("recipe_method_not_saved")
    candidates = capability_memory.discover(db, user, {"project_id": project_id, "unit_id": unit_id,
                                                       "kind": "recipe", "limit": 20})
    # Scope is explicit; ordering never chooses a hidden winner.
    selected = creation_recipes._method(db, user, unit, {
        "plugin": revision["content"].get("plugin"), "plugin_version": revision["content"].get("plugin_version")},
        {"method": {"source_kind": "capability_memory", "artifact_id": artifact["id"],
                    "revision_id": revision["id"], "arguments": {}}})
    if selected[1]:
        raise StageInvocationError("recipe_method_scope_mismatch")
    content = validate_recipe(revision["content"])
    node = next((node for node in workflow.definition_json["nodes"] if node["id"] == node_id), None)
    if node is None or any(node.get(key) != content[key] for key in ("plugin", "plugin_version", "stage_schema")):
        raise StageInvocationError("recipe_method_stage_mismatch")
    if content["base_workflow_checksum"] != workflow.checksum:
        raise StageInvocationError("recipe_method_base_mismatch")
    definition, adjusted = _replace_config(workflow, node_id, content["config_patch"])
    destination = request.get("destination", "project")
    if destination == "capability":
        raise StageInvocationError("recipe_method_destination_invalid", status_code=422)
    binding = _destination(db, unit, user, destination, request.get("scope_id"))
    _validate_methods(db, user, unit, definition, destination)
    if destination in DEFAULTS:
        definition = validate_portable(definition, source_project_id=project_id, source_unit_id=unit_id)
        validate_reusable_profiles(db, definition, user=user)
    result = canonical({"artifact_id": artifact["id"], "revision_id": revision["id"],
        "content_hash": revision["content_hash"], "matched_scope": selected[0]["matched_scope"],
        "node_id": node_id, "workflow_id": workflow.id, "workflow_checksum": workflow.checksum,
        "destination": destination, "expected_revision": binding.revision if binding else 0,
        "definition_diff": _definition_diff(db, binding, definition) if destination in DEFAULTS else None,
        "diff": _diff(node.get("config") or {}, adjusted["config"]), "definition": definition,
        "scope_matches": [item["matched_scope"] for item in candidates["items"]], "auto_select": False})
    result["preview_hash"] = digest(result)
    return result


def apply_method(db, project_id, unit_id, node_id, user, request):
    request = canonical(request, max_bytes=32 * 1024)
    key, fingerprint = _key(request, user, project_id=project_id, unit_id=unit_id, node_id=node_id)
    try:
        lock_project_context(db, project_id, user)
        _, unit = owned_unit(db, project_id, unit_id, user, mutate=True)
        if user.role not in {"editor", "admin"} or not user.is_active:
            raise StageInvocationError("recipe_readonly", status_code=403)
        replay = _event_replay(db, project_id, "creation_recipe.method_applied", key, fingerprint)
        if replay is not None:
            return replay
        preview = apply_method_preview(db, project_id, unit_id, node_id, user, request)
        if preview["preview_hash"] != request.get("expected_preview_hash"):
            raise StageInvocationError("recipe_method_preview_changed")
        result = _write_binding(db, unit=unit, user=user, definition=preview["definition"],
            destination=preview["destination"], expected_revision=request.get("expected_revision"),
            name=request.get("name") or f"{unit.title} · 复用方法")
        use = CapabilityUse(artifact_revision_id=preview["revision_id"], owner_user_id=user.id,
            project_id=project_id, rendered_arguments_hash=digest({}), outcome="used", created_by=user.email)
        db.add(use)
        db.flush()
        result["capability_use_id"] = use.id
        record_project_event(db, project_id=project_id, event_type="creation_recipe.method_applied", actor=user.email,
            entity_type="capability_artifact_revision", entity_id=preview["revision_id"],
            payload={"unit_id": unit_id, "idempotency_key": key, "fingerprint": fingerprint,
                     "artifact_revision_id": preview["revision_id"], "result": result})
        db.commit()
        return result
    except IntegrityError:
        db.rollback()
        raise StageInvocationError("recipe_revision_conflict") from None
    except BaseException:
        db.rollback()
        raise


def recipe_options(db, project_id, unit_id, user):
    from .content_harness.registry import registry

    _, unit, workflow, _ = creation_recipes._workflow(db, project_id, unit_id, user)
    binding = _binding(db, unit, "project")
    options = []
    for key, title, instructions in (
        ("content-core", "研究 → 大纲 → 初稿 → 精修", [("research", "研究", "梳理当前任务、事实边界与值得展开的角度"),
            ("outline", "大纲", "根据已经接受的研究，提出清晰的大纲"),
            ("draft", "初稿", "根据已经接受的大纲生成完整内容"),
            ("refine", "精修", "精修已接受的初稿，保持事实与身份边界")]),
        ("single-proposal", "直接生成候选", [("draft", "内容候选", "围绕当前任务生成可供选择的完整内容")]),
    ):
        descriptor = registry.descriptor("node", "stage.master.propose", "1")
        schema = descriptor.stage_contract.to_dict()["stage_schema"]
        nodes = [{"id": node_id, "kind": "AI", "plugin": descriptor.key, "plugin_version": descriptor.version,
            "stage_schema": schema, "label": label, "config": {"instruction": instruction, "candidate_count": 3},
            "input_mapping": {}, "output_mapping": {}, "failure_policy": "stop"}
            for node_id, label, instruction in instructions]
        definition = {"nodes": nodes, "edges": [{"from": nodes[index - 1]["id"], "to": node["id"]}
            for index, node in enumerate(nodes) if index], "visual_order": [node["id"] for node in nodes]}
        definition = validate_definition(definition)
        options.append({"key": key, "title": title, "definition": definition, "definition_hash": digest(definition),
                        "modality": unit.modality, "requires_explicit_save": True})
    target = {"text": ("wechat", "article"), "graphic": ("xiaohongshu", "image_note"),
              "video": ("douyin", "spoken_script")}[unit.modality]
    nodes = deepcopy(options[0]["definition"]["nodes"])
    additions = [("checks", "stage.checks", "1", "检查内容", {}),
        ("channel", "stage.variant.adapt", "1", "渠道版本", {"variant_key": f"{target[0]}.{target[1]}",
            "channel_id": target[0], "content_form": target[1], "mode": "deterministic"})]
    if unit.modality in {"graphic", "video"}:
        from .. import runtime_config

        selected_profile = (runtime_config.get_runtime(runtime_config.KEY_MODELS) or {}).get("default_profile") or "default"
        media_version = "3" if unit.modality == "graphic" else "2"
        media_config = {
            "capability": "image_generation" if unit.modality == "graphic" else "tts",
            "selected_profile": selected_profile,
            "prompt": "根据当前已接受的内容生成插图" if unit.modality == "graphic"
                else "为当前已接受的脚本生成配音",
            "items": 1,
        }
        if unit.modality == "graphic":
            media_config["aspect_ratio"] = "1:1"
        media = ("media", "media.generate", media_version, "配图" if unit.modality == "graphic" else "配音",
            media_config)
        additions.insert(0, media)
    if unit.modality == "video":
        additions.append(("director", "stage.professional.prepare", "1", "导演交接", {
            "package_schema": "director.video.v1", "objective": "按当前脚本、镜头与精确素材制作成片；仅准备交接，不自动派发", "prepare_execution": False}))
    for node_id, plugin, version, label, config in additions:
        descriptor = registry.descriptor("node", plugin, version)
        contract = descriptor.stage_contract.to_dict()
        nodes.append({"id": node_id, "kind": contract["category"], "plugin": plugin, "plugin_version": version,
            "stage_schema": contract["stage_schema"], "label": label, "config": config, "input_mapping": {},
            "output_mapping": {}, "failure_policy": "stop"})
    # Media adoption does not bind a Master. The following check/variant consumes the explicit Master context.
    edges = [{"from": nodes[index - 1]["id"], "to": node["id"]} for index, node in enumerate(nodes) if index]
    definition = validate_definition({"nodes": nodes, "edges": edges, "visual_order": [node["id"] for node in nodes]})
    options.append({"key": "production-loop", "title": "完整生产链（含素材 / 渠道 / 专业交接）",
        "definition": definition, "definition_hash": digest(definition), "modality": unit.modality,
        "requires_explicit_save": True})
    if unit.identity_snapshot_id:
        from ..models import IdentitySnapshot
        from .starter_personas import _definition
        from .studio_creative_catalog import BLUEPRINTS

        snapshot = db.get(IdentitySnapshot, unit.identity_snapshot_id)
        profile = (snapshot.effective_profile_json or {}).get(f"{unit.modality}_creative_profile") if snapshot else None
        key = ((profile or {}).get("provenance") or {}).get("blueprint_key")
        if key in BLUEPRINTS:
            definition = validate_definition(_definition(unit.modality, key))
            options.insert(0, {"key": f"{key}.{unit.modality}", "title": f"{BLUEPRINTS[key]['name']} · {unit.modality} 默认创作流程",
                "definition": definition, "definition_hash": digest(definition), "modality": unit.modality,
                "requires_explicit_save": True})
        if unit.modality in {"text", "video"} and snapshot:
            from ..models import ContentMasterRevision
            from .starter_personas import audio_definition

            audio_profile = (snapshot.effective_profile_json or {}).get("audio_creative_profile")
            audio_key = ((audio_profile or {}).get("provenance") or {}).get("blueprint_key")
            source = db.scalar(select(ContentMasterRevision).where(ContentMasterRevision.content_unit_id == unit.id)
                .order_by(ContentMasterRevision.revision_no.desc()).limit(1))
            if audio_key in BLUEPRINTS and source and source.payload_schema in {"text.master.v2", "video.master.v2"}:
                definition = validate_definition(audio_definition(audio_key))
                options.insert(1, {"key": f"{audio_key}.audio", "title": f"{BLUEPRINTS[audio_key]['name']} · 从当前已接受稿创作音频",
                    "definition": definition, "definition_hash": digest(definition), "modality": unit.modality,
                    "output_kind": "audio_material", "requires_explicit_save": True})
                aligned = validate_definition(audio_definition(audio_key, alignment=True))
                options.insert(2, {"key": f"{audio_key}.audio-asr", "title": f"{BLUEPRINTS[audio_key]['name']} · 音频＋本机ASR对稿／字幕（须明确执行）",
                    "definition": aligned, "definition_hash": digest(aligned), "modality": unit.modality,
                    "output_kind": "audio_material", "requires_explicit_save": True})
    return {"items": options, "expected_revision": binding.revision if binding else 0,
            "current_workflow_id": workflow.id if workflow else None,
            "current_checksum": workflow.checksum if workflow else None}


def adopt_recipe(db, project_id, unit_id, user, request):
    from .stage_invocations import require_receipt_schema

    require_receipt_schema(db)
    request = canonical(request, max_bytes=16 * 1024)
    key, fingerprint = _key(request, user, project_id=project_id, unit_id=unit_id)
    try:
        lock_project_context(db, project_id, user)
        _, unit = owned_unit(db, project_id, unit_id, user, mutate=True)
        if user.role not in {"admin", "editor"} or not user.is_active:
            raise StageInvocationError("recipe_readonly", status_code=403)
        replay = _event_replay(db, project_id, "creation_recipe.selected", key, fingerprint)
        if replay is not None:
            return replay
        options = recipe_options(db, project_id, unit_id, user)
        option = next((item for item in options["items"] if item["key"] == request.get("recipe_key")), None)
        if (option is None or option["definition_hash"] != request.get("expected_definition_hash")
                or options["current_workflow_id"] != request.get("expected_workflow_id")):
            raise StageInvocationError("recipe_selection_changed")
        result = _write_binding(db, unit=unit, user=user, definition=option["definition"], destination="project",
                                expected_revision=request.get("expected_revision"), name=option["title"])
        record_project_event(db, project_id=project_id, event_type="creation_recipe.selected", actor=user.email,
            entity_type="workflow", entity_id=result["workflow_id"], payload={"unit_id": unit_id,
            "idempotency_key": key, "fingerprint": fingerprint, "recipe_key": option["key"], "result": result})
        db.commit()
        return result
    except IntegrityError:
        db.rollback()
        raise StageInvocationError("recipe_revision_conflict") from None
    except BaseException:
        db.rollback()
        raise
