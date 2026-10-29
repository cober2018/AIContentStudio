"""Persona creative-profile resolution over the existing model routing truth."""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

from fastapi import HTTPException

from . import content_identity, model_capability_routing
from .studio_creative_catalog import (
    PRESETS,
    QUALITY,
    blueprint,
    digest,
    freshness_projection,
    validate_creative_profile,
)

MODALITY_FIELDS = {
    "text": "text_creative_profile",
    "graphic": "graphic_creative_profile",
    "video": "video_creative_profile",
}


USER_MODEL_KEYS = frozenset({"model_profile_id", "selected_profile"})


def _binding_view(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if not value:
        return None
    return {"provider": value.get("provider"), "model": value.get("model"), "profile": value.get("profile")}


def _configured_binding(db, profile: dict, capability: str, *, _for_execution=False) -> dict[str, Any]:
    """Media and chat follow the routes in 设置 → AI 与模型; identity bindings are history only."""
    if capability == "chat":
        return chat_binding(profile, db=db)
    from .generation.providers import _models_override

    models = _models_override()
    selected = (models.get("routes") or {}).get("generate") or models.get("default_profile")
    # Auto must enter the planner as Auto; marking every candidate explicit
    # or promoting a plugin's model to the primary would bypass routing policy.
    planned = model_capability_routing.plan(db, capability=capability, selected_profile=selected,
        _for_execution=_for_execution)
    if planned.get("status") != "ready":
        return {"status": "blocked", "reason": planned.get("reason") or "capability_route_unavailable"}
    binding = {"provider": planned.get("adapter_key"), "model": planned.get("model_id"), "profile": planned.get("execution_profile")}
    return {"status": "ready", "selected_binding": binding, "route": planned,
            "fallback_reason": planned.get("route_reason") if planned.get("route_reason") != "selected_model_binding" else None}


def _chat_limits(db, model):
    limits = (model_capability_routing.configuration_view(db).get("policies", {}).get("limits", {}).get("chat")
              if db is not None else None)
    if limits is None and model.get("provider") == "mock":
        return {"max_tokens": 4096, "timeout_seconds": 25, "max_items": 1, "validation_only": True}
    if (not limits or type(limits.get("max_tokens")) is not int or limits["max_tokens"] < 1
            or limits.get("max_cost") is not None):
        return None
    return {"max_tokens": limits["max_tokens"], "timeout_seconds": limits["timeout_seconds"], "max_items": limits["max_items"]}


def validate_execution(db, resolved):
    from .stage_contracts import StageContractError
    creative = resolved.get("creative_configuration")
    if creative is not None and creative.get("chat_limits") is not None and _chat_limits(db, resolved["model"]) != creative.get("chat_limits"):
        raise StageContractError("stage_model_runtime_changed")


def chat_binding(profile: dict, stage_config: dict | None = None, *, db=None) -> dict:
    from .creation_recipes import _model
    from .generation.providers import _models_override

    config = {k: v for k, v in (stage_config or {}).items() if k not in USER_MODEL_KEYS}
    model, blockers = _model(config)
    if blockers or model is None:
        return {"status": "blocked", "reason": "model_profile_unavailable"}
    raw = (_models_override().get("profiles") or {}).get(model["profile_id"]) or {}
    limits = _chat_limits(db, model)
    if limits is None:
        return {"status": "blocked", "reason": "capability_limit_required"}
    return {"status": "ready", "model": model, "selected_binding": {
        "provider": raw.get("provider_id") or model["adapter_key"], "model": model["model"], "profile": model["profile_id"]},
        "fallback_reason": None, "declared_chain": None, "chat_limits": limits}


def _chat_stage_binding(profile, config, source, override, db):
    return chat_binding(profile, config, db=db), "model_route"


def production_stage_key(node, config):
    from .creative_method_stage import OUTPUT_SCHEMAS

    schema = config.get("output_schema", "")
    if OUTPUT_SCHEMAS.get(schema) == "research":
        return "research"
    if schema.startswith(("graphic.", "video.shot")):
        return "storyboard"
    if node["plugin"] == "media.generate":
        return "voice"
    if node["plugin"] == "stage.graphic.compose":
        return "storyboard"
    if node["plugin"] == "stage.professional.prepare":
        return "finish"
    return "script"


def freeze_production_stages(db, user, unit, stages, *, origin, node=None, config=None, frozen_manifest=None, execution_target=None):
    """Pin selected content once; disabled selections contribute identifiers only."""
    from ..models import CapabilityArtifactRevision
    from . import capability_memory
    from .capability_contracts import render
    from .creative_method_stage import OUTPUT_SCHEMAS
    from .studio_creative_catalog import PRODUCTION_STAGES, SKILLS, load_skill, validate_production_stages

    if frozen_manifest is not None:
        return project_frozen_production_stages(db, user, unit, stages, frozen_manifest, node=node, config=config, execution_target=execution_target)
    validate_production_stages(stages)
    rows = []
    context = None
    for definition in PRODUCTION_STAGES:
        key = definition["id"]
        if key not in stages:
            continue
        stage = stages[key]
        active, disabled, not_applicable = [], [], []
        for selected in stage["methods"]:
            if not stage["enabled"] or not selected["enabled"]:
                disabled.append(selected["id"])
                continue
            kind = selected["source_kind"]
            params = selected["parameters"]
            if kind == "installed_agent_skill":
                raise ValueError("installed_skill_exact_source_adapter_unavailable")
            applicability = None
            if kind == "studio_builtin":
                resource = SKILLS[selected["skill_ref"]]
                applicability = {"compatible_stage_schemas": resource["compatible_stage_schemas"],
                                 "output_schemas": resource["output_schemas"], "resource_modality": resource["modality"]}
                if node is not None:
                    output = ((config or {}).get("output_schema") if node["plugin"] == "stage.creative.method" else
                              (config or {}).get("package_schema") if node["plugin"] == "stage.professional.prepare" else None)
                    modality = (OUTPUT_SCHEMAS.get(output) if node["plugin"] == "stage.creative.method" else
                                "audio" if node["plugin"] == "media.generate" else unit.modality)
                    reason = ("stage_schema_not_compatible" if node.get("stage_schema") not in resource["compatible_stage_schemas"] else
                              "output_schema_not_compatible" if output is not None and output not in resource["output_schemas"] else
                              "modality_not_compatible" if modality is not None and resource["modality"] != modality else None)
                    applicability = {**applicability, "node_id": node["id"], "stage_schema": node.get("stage_schema"),
                                     "output_schema": output, "modality": modality, "status": "not_applicable" if reason else "applicable"}
                    if reason:
                        not_applicable.append({"id": selected["id"], "source_kind": kind, "skill_ref": selected["skill_ref"],
                            "version": resource["version"], "resource_hash": digest(resource), "reason": reason,
                            "applicability": applicability})
                        continue
                else:
                    applicability["status"] = "external_guidance_not_recipe_node_execution"
            if node is not None:
                from .creation_recipes import _method
                ref = ({"source_kind": kind, "skill_ref": selected["skill_ref"]} if kind == "studio_builtin" else
                       {"source_kind": kind, "artifact_id": selected["artifact_id"], "revision_id": selected["revision_id"], "arguments": params})
                method, blockers = _method(db, user, unit, node, {**(config or {}), "method": ref})
                if blockers or method is None:
                    raise ValueError(blockers[0] if blockers else "production_method_unavailable")
            elif kind == "studio_builtin":
                package = load_skill(selected["skill_ref"])
                resource = SKILLS[selected["skill_ref"]]
                method = {"source_kind": kind, "skill_ref": selected["skill_ref"], "version": resource["version"],
                          "package_hash": package["package_hash"], "contract_hash": digest(package["contract"]),
                          "provenance": package["provenance"], "instruction": package["instruction"]}
            else:
                row = capability_memory._owned(db, user, selected["artifact_id"])
                revision = db.get(CapabilityArtifactRevision, selected["revision_id"])
                if revision is None or revision.artifact_id != row.id:
                    raise ValueError("method_revision_unavailable")
                capability_memory._validate_revision(revision)
                frozen = revision.metadata_json
                if row.status not in {"saved", "pinned"} or frozen.get("status") not in {"saved", "pinned"}:
                    raise ValueError("method_not_saved")
                if row.kind not in {"prompt_skill", "recipe"} or frozen.get("kind") not in {"prompt_skill", "recipe"}:
                    raise ValueError("production_method_kind_invalid")
                if context is None:
                    context = capability_memory._context(db, user, {"project_id": unit.project_id, "unit_id": unit.id})
                if (context.get(row.scope_type) != row.scope_json
                        or context.get(frozen["scope_type"]) != frozen["scope"]):
                    raise ValueError("method_scope_mismatch")
                rendered, arguments_hash = render(revision.content_json, revision.args_schema_json, params)
                method = {"source_kind": kind, "artifact_id": row.id, "revision_id": revision.id,
                          "content_hash": revision.content_hash, "metadata_hash": digest(frozen),
                          "arguments_hash": arguments_hash, "rendered_hash": digest(rendered),
                          "instruction": json.dumps(rendered, ensure_ascii=False, sort_keys=True),
                          "rendered_content": rendered, "frozen_scope": {"scope_type": frozen["scope_type"], "scope": frozen["scope"]}}
            if kind == "capability_memory" and node is not None:
                revision = db.get(CapabilityArtifactRevision, selected["revision_id"])
                targets = revision.content_json.get("execution_targets")
                deterministic = node["plugin"] in {"stage.graphic.compose", "stage.professional.prepare"}
                reason = ("prompt_guidance_not_deterministic_recipe" if deterministic and "deterministic_parameters" not in method else
                          "execution_target_not_applicable" if not deterministic and targets is not None and "ai_planning" not in targets else None)
                applicability = {"node_id": node["id"], "plugin": node["plugin"],
                    "execution_target": "deterministic_recipe" if deterministic else "ai_planning",
                    "declared_execution_targets": targets, "status": "not_applicable" if reason else "applicable"}
                if reason:
                    skipped = {**method, "id": selected["id"], "parameters": copy.deepcopy(params),
                        "reason": reason, "applicability": applicability}
                    skipped["method_hash"] = digest(skipped)
                    not_applicable.append(skipped)
                    continue
            method = {**method, "id": selected["id"], "parameters": copy.deepcopy(params)}
            if applicability is not None:
                method["applicability"] = applicability
            method["method_hash"] = digest(method)
            active.append(method)
        rows.append({"stage": key, "title": definition["title"], "enabled": stage["enabled"],
                     "origin": origin, "methods": active, "disabled_method_ids": disabled,
                     "not_applicable_methods": not_applicable})
    manifest = {"schema": "production.methods.manifest.v1", "stages": rows,
                "legacy_stage_ids": [item["id"] for item in PRODUCTION_STAGES if item["id"] not in stages],
                "execution_rule": "For explicitly configured stages use only enabled methods in this manifest, with no automatic creative skills. Unconfigured stages retain their existing workflow behavior. Keep identity, knowledge, evidence and technical output contracts. Report exact loaded method hashes; receipt delivery is not creative quality acceptance."}
    manifest = {**manifest, "manifest_hash": digest(manifest)}
    if execution_target is not None:
        return project_frozen_production_stages(db, user, unit, stages, manifest, execution_target=execution_target)
    return manifest


def project_frozen_production_stages(db, user, unit, stages, manifest, *, node=None, config=None, execution_target=None):
    """Reuse launch-pinned content while checking current access independently."""
    from ..models import CapabilityArtifactRevision
    from . import capability_memory
    from .creative_method_stage import OUTPUT_SCHEMAS
    from .workflow_stage_recipes import deterministic_recipe

    if manifest.get("manifest_hash") != digest({key: value for key, value in manifest.items() if key != "manifest_hash"}):
        raise ValueError("production_manifest_integrity")
    projected = copy.deepcopy(manifest)
    projected["stages"] = [row for row in projected["stages"] if row["stage"] in stages]
    current_context = None
    for stage in projected["stages"]:
        active, skipped = [], []
        for method in stage["methods"]:
            kind = method["source_kind"]
            if kind == "capability_memory":
                artifact = capability_memory._owned(db, user, method["artifact_id"])
                revision = db.get(CapabilityArtifactRevision, method["revision_id"])
                if revision is None or revision.artifact_id != artifact.id or revision.content_hash != method["content_hash"]:
                    raise ValueError("method_revision_unavailable")
                capability_memory._validate_revision(revision)
                if artifact.status not in {"saved", "pinned"}:
                    raise ValueError("method_not_saved")
                if artifact.kind not in {"prompt_skill", "recipe"}:
                    raise ValueError("production_method_kind_invalid")
                if current_context is None:
                    current_context = capability_memory._context(db, user, {"project_id": unit.project_id, "unit_id": unit.id})
                frozen_scope = method["frozen_scope"]
                if (current_context.get(artifact.scope_type) != artifact.scope_json
                        or current_context.get(frozen_scope["scope_type"]) != frozen_scope["scope"]):
                    raise ValueError("method_scope_mismatch")
            if node is None:
                targets = method.get("rendered_content", {}).get("execution_targets")
                if execution_target is not None and targets is not None and execution_target not in targets:
                    skipped.append({**method, "reason": "execution_target_not_applicable",
                        "applicability": {"execution_target": execution_target, "declared_execution_targets": targets,
                            "status": "not_applicable"}})
                else:
                    active.append(method)
                continue
            reason = None
            if kind == "studio_builtin":
                applicability = method["applicability"]
                output = ((config or {}).get("output_schema") if node["plugin"] == "stage.creative.method" else
                          (config or {}).get("package_schema") if node["plugin"] == "stage.professional.prepare" else None)
                modality = (OUTPUT_SCHEMAS.get(output) if node["plugin"] == "stage.creative.method" else
                            "audio" if node["plugin"] == "media.generate" else unit.modality)
                reason = ("stage_schema_not_compatible" if node.get("stage_schema") not in applicability["compatible_stage_schemas"] else
                          "output_schema_not_compatible" if output is not None and output not in applicability["output_schemas"] else
                          "modality_not_compatible" if modality is not None and applicability["resource_modality"] != modality else None)
            else:
                rendered = method["rendered_content"]
                deterministic = node["plugin"] in {"stage.graphic.compose", "stage.professional.prepare"}
                try:
                    recipe = deterministic_recipe(rendered, node)
                except (ValueError, KeyError):
                    recipe = None
                if recipe is not None:
                    method["deterministic_parameters"] = recipe["config_patch"]
                targets = rendered.get("execution_targets")
                reason = ("prompt_guidance_not_deterministic_recipe" if deterministic and recipe is None else
                          "execution_target_not_applicable" if not deterministic and targets is not None and "ai_planning" not in targets else None)
            method["applicability"] = {**method.get("applicability", {}), "node_id": node["id"],
                "plugin": node["plugin"], "status": "not_applicable" if reason else "applicable"}
            if reason:
                skipped.append({**method, "reason": reason})
            else:
                active.append(method)
        stage["methods"], stage["not_applicable_methods"] = active, skipped
    if node is None and len(projected["stages"]) == len(manifest["stages"]) and not any(row["not_applicable_methods"] for row in projected["stages"]):
        return projected
    projected["source_manifest_hash"] = manifest["manifest_hash"]
    projected.pop("manifest_hash", None)
    projected["manifest_hash"] = digest(projected)
    return projected


def frozen_stage(db, user, unit, node, contract, context, override):
    """Read only the pinned snapshot; live Persona edits cannot change a Run."""
    from ..models import CapabilityArtifactRevision, IdentitySnapshot
    from .creation_recipes import _method
    from .stage_contracts import StageContractError

    identity = context.get("identity") or {}
    creative_input = contract.effective_config(node.get("config") or {}, override or {})[1] if node["plugin"] == "stage.creative.method" else {}
    graphic_planning = unit.modality == "graphic" and node["plugin"] in {"stage.creative.method", "stage.master.propose"}
    modality = unit.modality
    field = MODALITY_FIELDS[modality]
    from .product_context import is_product, effective_profile
    product_domain = is_product(unit)
    profile_content = ((context.get("product_context") or {}).get("creative_profiles") or effective_profile(db, unit)) if product_domain else identity.get("content") or {}
    profile = copy.deepcopy(profile_content.get(field))
    work_settings = ((context.get("production_profile") or {}).get("settings") or {})
    if not product_domain and field == "video_creative_profile" and work_settings.get(field) is not None:
        profile = copy.deepcopy(work_settings[field])
    director = node["plugin"] == "stage.professional.prepare" and str(node.get("plugin_version")) == "2"
    if profile is None or (not director and node["plugin"] not in {"stage.master.propose", "stage.creative.method", "stage.graphic.compose"}):
        return node, None, None, []
    if profile["schema"] != f"persona.creative.{modality}.v1":
        raise StageContractError("creative_profile_modality_mismatch")
    # 模型只由 设置 → AI 与模型 的路由决定：角色、商品、阶段和单次运行里存过的模型选择一律不生效。
    source = {k: v for k, v in (node.get("config") or {}).items() if k not in USER_MODEL_KEYS}
    node = {**node, "config": source}
    override = {k: v for k, v in (override or {}).items() if k not in USER_MODEL_KEYS} if override is not None else None
    profile = {**profile, "mode": "auto", "model_binding": None, "model_chain": []}
    saved_method = source.get("method") or {"source_kind": "studio_builtin", "skill_ref": profile["skill_ref"]}
    method_selection = (override or {}).get("method", saved_method)
    if type(method_selection) is not dict:
        raise StageContractError("stage_method_selection_invalid")
    stage_key = production_stage_key(node, creative_input if node["plugin"] == "stage.creative.method" else
                                     contract.effective_config(source, override or {})[1])
    selection = profile.get("production_stages", {}).get(stage_key)
    task_stages = profile_content.get("product_production_stages", {})
    task_manifest = profile_content.get("product_production_methods", {}).get(unit.modality)
    product = ((context.get("brief") or {}).get("content") or {}).get("product_context") or {}
    explicit_stages = None if product_domain else product.get("production_stages")
    if explicit_stages is not None:
        task_stages = {**task_stages, **copy.deepcopy(explicit_stages)}
        task_manifest = freeze_production_stages(db, user, unit, task_stages, origin="product_brief")
    work_stages = work_settings.get("production_stages")
    if work_stages is None and work_settings.get(field) is not None:
        work_stages = work_settings[field].get("production_stages")
    if work_stages is not None:
        task_stages = {**task_stages, **copy.deepcopy(work_stages)}
        task_manifest = freeze_production_stages(db, user, unit, task_stages, origin="work_profile", frozen_manifest=task_manifest if product_domain and explicit_stages is None else None)
    if stage_key in task_stages:
        selection = task_stages[stage_key]
    else:
        task_manifest = None
    if not product_domain and selection is not None:
        from .studio_creative_catalog import PERSONA_METHOD_TRIAL_KEYS

        selected_ref = method_selection.get("skill_ref", "")
        if selected_ref.endswith("@2") and selected_ref.rsplit("@", 1)[0] in PERSONA_METHOD_TRIAL_KEYS:
            # Explicit trial recipes upgrade matching methods, keeping each inherited switch and ordering.
            selection = copy.deepcopy(selection)
            for item in selection["methods"]:
                old_ref = item.get("skill_ref", "")
                if old_ref.rsplit("@", 1)[0] in PERSONA_METHOD_TRIAL_KEYS and old_ref.endswith("@1"):
                    item["skill_ref"] = old_ref.rsplit("@", 1)[0] + "@2"
            task_manifest = None
        if "method" in (override or {}):
            selection = {"enabled": selection["enabled"], "methods": [{
                **method_selection, "id": "run-method", "enabled": True,
                "parameters": method_selection.get("arguments", {}),
            }]}
            selection["methods"][0].pop("arguments", None)
            task_manifest = None
    if selection is None or task_manifest is None:
        try:
            validate_creative_profile(profile)
        except ValueError as exc:
            raise StageContractError(str(exc)) from None
    same_method = (method_selection.get("source_kind") == "studio_builtin"
                   and method_selection.get("skill_ref", "").rsplit("@", 1)[0] == profile["skill_ref"].rsplit("@", 1)[0])
    defaults = profile.get("parameters", {}) if same_method else {}
    if selection is not None:
        defaults = {key: value for key, value in defaults.items() if key != "instruction"}
    prepared = {**defaults, **source, "method": saved_method}
    composition = node["plugin"] == "stage.graphic.compose"
    deterministic = composition or director
    if composition:
        prepared.setdefault("preset_ref", profile["style_preset_ref"])
    base_config = contract.effective_config(prepared, override)[1]
    methods, blockers = [], []
    # Launch-pinned guidance already passed catalog validation; execution still validates the core node contract.
    base, errors = (None, []) if selection is not None and task_manifest is not None else _method(db, user, unit, node, base_config)
    blockers.extend(errors)
    if base:
        methods.append(base)
    deterministic_parameter_sources = []
    parameter_defaults = {}
    if selection is None and profile["mode"] == "composed":
        if base is not None and base.get("source_kind") != "studio_builtin":
            blockers.append("creative_composition_builtin_base_required")
        for revision_id in profile.get("capability_memory_revision_ids", []):
            revision = db.get(CapabilityArtifactRevision, revision_id)
            if revision is None:
                blockers.append("method_revision_unavailable")
                continue
            method, errors = _method(db, user, unit, node, {"method": {
                "source_kind": "capability_memory", "artifact_id": revision.artifact_id,
                "revision_id": revision_id, "arguments": {}}})
            blockers.extend(errors)
            if method:
                methods.append(method)
                if deterministic:
                    patch = method.get("deterministic_parameters")
                    if patch is None:
                        blockers.append("deterministic_stage_method_parameters_required")
                    else:
                        try:
                            candidate_config = {**prepared, **parameter_defaults, **patch}
                            contract.validate_config(candidate_config)
                        except StageContractError:
                            blockers.append("deterministic_stage_method_parameters_invalid")
                        else:
                            parameter_defaults.update(patch)
                            deterministic_parameter_sources.append({
                                "artifact_id": method["artifact_id"], "revision_id": method["revision_id"],
                                "content_hash": method["content_hash"],
                                "arguments_hash": method["arguments_hash"],
                                "metadata_hash": method["metadata_hash"],
                                "rendered_hash": method["rendered_hash"],
                                "config_patch": patch,
                            })
        if profile.get("installed_skill_refs"):
            blockers.append("installed_skill_stage_execution_unavailable")
    elif selection is None and (profile.get("capability_memory_revision_ids") or profile.get("installed_skill_refs")):
        blockers.append("creative_composition_mode_required")
    production_manifest = None
    if selection is not None:
        methods, blockers = [], []
        try:
            production_manifest = freeze_production_stages(db, user, unit, {stage_key: selection},
                origin=(identity.get("content") or {}).get("production_stage_origins", {}).get(modality, "identity_snapshot"), node=node, config=base_config,
                frozen_manifest=task_manifest)
            methods = production_manifest["stages"][0]["methods"]
        except ValueError as exc:
            blockers.append(str(exc))
        for item in methods:
            if deterministic and item.get("source_kind") == "capability_memory":
                patch = item.get("deterministic_parameters")
                if patch is None:
                    blockers.append("deterministic_stage_method_parameters_required")
                else:
                    contract.validate_config({**prepared, **parameter_defaults, **patch})
                    parameter_defaults.update(patch)
                    deterministic_parameter_sources.append({"method_hash": item["method_hash"], "config_patch": patch})
            elif item.get("source_kind") == "studio_builtin":
                parameter_defaults.update(item["parameters"])
    prepared = {**prepared, **parameter_defaults, **source}
    _, config, _ = contract.effective_config(prepared, override)
    freshness = freshness_projection(context.get("boundary"), config.get("fact_mode", "grounded")) if unit.modality == "text" else None
    if freshness and not freshness["ready"]:
        blockers.append(freshness["reason"])
    chat_origin = None
    if deterministic:
        route = {"status": "ready", "selected_binding": None, "declared_chain": []}
    elif graphic_planning and profile["capability"] != "chat":
        # Native media pins cannot be sent to the independent planning Chat executor.
        route, chat_origin = _chat_stage_binding(profile, config, source, override or {}, db)
    else:
        route, chat_origin = _chat_stage_binding(profile, config, source, override or {}, db)
    if route["status"] != "ready":
        blockers.append(route["reason"])
    elif not deterministic:
        prepared["model_profile_id"] = route["selected_binding"]["profile"]
        # The environment default is not a registered profile and must retain its existing resolution semantics.
        if route["selected_binding"]["profile"] == "default":
            prepared.pop("model_profile_id", None)
    method_base = (methods[0] if methods else {"source_kind": "studio_builtin"}) if selection is not None else base
    if composition:
        # Optional guidance does not replace the compositor tool identity.
        method_base, composition_errors = _method(db, user, unit, node, config)
        blockers.extend(composition_errors)
    method = {**(method_base or {"source_kind": "studio_builtin"}), "stack": methods,
              "instruction": "\n\n".join(item["instruction"] for item in methods)}
    snapshot = db.get(IdentitySnapshot, identity["id"]) if identity.get("id") else None
    projection = {
        "schema": "effective.creative.stage.v1", "modality": modality,
        "identity_snapshot_id": identity.get("id"), "identity_checksum": identity.get("checksum"),
        "profile_origin": "product_configuration" if product_domain else (snapshot.field_origins_json or {}).get(field) if snapshot else None,
        **({"production_domain": "product", "product_context_checksum": (context.get("product_context") or {}).get("checksum")} if product_domain else {}),
        "profile": profile, "profile_hash": digest(profile), "method_stack": methods,
        "deterministic_parameter_sources": deterministic_parameter_sources,
        "style_preset": PRESETS[profile["style_preset_ref"]],
        "quality_profile": QUALITY[profile["quality_profile_ref"]],
        "selected_binding": route.get("selected_binding"), "declared_chain": route.get("declared_chain"),
        "fallback_reason": route.get("fallback_reason"), "fallback_reasons": route.get("fallback_reasons", []),
        "chat_limits": route.get("chat_limits"),
        "freshness": freshness,
        "status": "blocked" if blockers else "configured_not_probed",
    }
    if selection is not None:
        projection["production_manifest"] = production_manifest
        projection["production_stage"] = stage_key
        projection["creative_methods_enabled"] = selection["enabled"]
    if graphic_planning and profile["capability"] != "chat":
        projection["binding_purpose"] = "planning_chat_stage_not_image_generation"
        projection["image_policy"] = {
            "mode": profile["mode"], "binding": profile.get("model_binding"), "chain": profile.get("model_chain", [])}
    if chat_origin is not None:
        projection["binding_origin"] = "model_route"
    if composition:
        preset_ref = config.get("preset_ref") or profile["style_preset_ref"]
        selected_preset = PRESETS.get(preset_ref)
        if selected_preset is None or selected_preset["config"]["modality"] != "graphic":
            blockers.append("graphic_composition_preset_invalid")
            projection["status"] = "blocked"
        else:
            projection["style_preset"] = selected_preset
            projection["style_preset_origin"] = ("run_override" if "preset_ref" in (override or {})
                else "project_stage" if "preset_ref" in source
                else "capability_memory" if "preset_ref" in parameter_defaults else "identity_creative_profile")
    return {**node, "config": prepared}, {**method, "deterministic_parameter_sources": deterministic_parameter_sources}, projection, blockers


def resolve(db, user, *, persona_id: int, account_id: int | None = None, series_id: int | None = None,
            modality: str, stage: str | None = None, override: dict | None = None,
            profile_override: dict | None = None, has_profile_override: bool = False) -> dict:
    if modality not in MODALITY_FIELDS:
        raise HTTPException(422, "creative_modality_invalid")
    identity = content_identity.effective(db, user, persona_id=persona_id, account_id=account_id, series_id=series_id)
    field = MODALITY_FIELDS[modality]
    profile = copy.deepcopy(identity.get("effective_profile", {}).get(field))
    if has_profile_override:
        profile = copy.deepcopy(profile_override)
    if not profile:
        return {"schema": "effective.creative.stage.preview.v1", "modality": modality, "stage": stage,
                "status": "blocked", "reason": "creative_profile_missing", "identity": identity}
    try:
        validate_creative_profile(profile)
        if profile["schema"] != f"persona.creative.{modality}.v1":
            raise ValueError("creative_profile_modality_mismatch")
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    layers = [{"scope": identity.get("creative_profile_origins", {}).get(field, "unknown"), "field": field,
               "profile": copy.deepcopy(profile), "hash": digest(profile)}]
    if has_profile_override:
        layers[0]["scope"] = "unsaved_preview"
    effective_profile = copy.deepcopy(profile)
    if override is not None:
        if not isinstance(override, dict) or set(override) - {"stage_instruction", "parameters", "production_stages"}:
            raise HTTPException(422, "creative_override_invalid")
        if "production_stages" in override:
            effective_profile["production_stages"] = copy.deepcopy(override["production_stages"])
        if "stage_instruction" in override:
            if not isinstance(override["stage_instruction"], str) or len(override["stage_instruction"]) > 4000:
                raise HTTPException(422, "creative_override_invalid")
            effective_profile["stage_instruction"] = override["stage_instruction"]
        if "parameters" in override:
            if not isinstance(override["parameters"], dict) or len(override["parameters"]) > 32:
                raise HTTPException(422, "creative_override_invalid")
            effective_profile["parameters"] = {**effective_profile.get("parameters", {}), **override["parameters"]}
        layers.append({"scope": "run", "profile": copy.deepcopy(override), "hash": digest(override)})
    try:
        validate_creative_profile(effective_profile)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None
    route = _configured_binding(db, effective_profile, effective_profile["capability"])
    result = {
        "schema": "effective.creative.stage.preview.v1", "modality": modality, "stage": stage,
        "status": route["status"], "reason": route.get("reason"), "layers": layers,
        "identity_revision_ids": identity.get("revision_ids"), "identity_checksum": digest(identity),
        "profile": effective_profile, "profile_hash": digest(effective_profile),
        "production_stages": copy.deepcopy(effective_profile.get("production_stages")),
        "selected_binding": route.get("selected_binding"), "declared_chain": route.get("declared_chain"),
        "fallback_reason": route.get("fallback_reason"), "route": route.get("route"),
    }
    result["resolution_hash"] = hashlib.sha256(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return result


def starter_preview(key: str) -> dict:
    try:
        return {"status": "ready", "preview": blueprint(key)}
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
