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
    "audio": "audio_creative_profile",
    "video": "video_creative_profile",
}


def _binding_view(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if not value:
        return None
    return {"provider": value.get("provider"), "model": value.get("model"), "profile": value.get("profile")}


def _configured_binding(db, profile: dict, capability: str, *, _for_execution=False) -> dict[str, Any]:
    if capability == "chat":
        return chat_binding(profile, db=db)
    view = model_capability_routing.configuration_view(db)
    binding = profile.get("model_binding")
    if profile.get("mode") == "composed" and not binding:
        return {"status": "blocked", "reason": "composed_binding_missing", "declared_chain": []}
    if profile.get("mode") == "custom":
        if not binding:
            return {"status": "blocked", "reason": "custom_binding_missing"}
        profile_id = binding.get("profile")
        registered = view["profiles"].get(profile_id)
        if not registered:
            return {"status": "blocked", "reason": "custom_profile_missing", "binding": _binding_view(binding)}
        actual = registered.get("capability_bindings", {}).get(capability)
        if not actual or actual.get("adapter_key") != binding.get("provider") or actual.get("model_id") != binding.get("model"):
            return {"status": "blocked", "reason": "custom_binding_mismatch", "binding": _binding_view(binding)}
        planned = model_capability_routing.plan(db, capability=capability, selected_profile=profile_id,
            explicit_profile=profile_id, _for_execution=_for_execution)
        if planned.get("status") != "ready":
            return {"status": "blocked", "reason": planned.get("reason") or "custom_binding_unavailable", "binding": _binding_view(binding)}
        if (planned.get("adapter_key") != binding["provider"] or planned.get("model_id") != binding["model"]
                or planned.get("execution_profile") != profile_id):
            return {"status": "blocked", "reason": "custom_binding_mismatch", "binding": _binding_view(binding)}
        return {"status": "ready", "selected_binding": _binding_view(binding), "route": planned, "fallback_reason": None}

    if profile.get("mode") == "composed" and binding:
        chain = [binding, *(profile.get("model_chain") or [])]
        reasons = []
        for index, candidate in enumerate(chain):
            profile_id = candidate.get("profile")
            registered = view["profiles"].get(profile_id) or {}
            actual = registered.get("capability_bindings", {}).get(capability)
            if not actual or actual.get("adapter_key") != candidate.get("provider") or actual.get("model_id") != candidate.get("model"):
                reasons.append("declared_binding_mismatch")
                continue
            planned = model_capability_routing.plan(db, capability=capability, selected_profile=profile_id,
                explicit_profile=profile_id, _for_execution=_for_execution)
            if (planned.get("status") == "ready" and planned.get("adapter_key") == candidate["provider"]
                    and planned.get("model_id") == candidate["model"] and planned.get("execution_profile") == profile_id):
                return {"status": "ready", "selected_binding": _binding_view(candidate), "route": planned,
                        "fallback_reason": None if index == 0 else "declared_chain_previous_unavailable", "declared_chain": [_binding_view(item) for item in chain], "fallback_reasons": reasons}
            reasons.append(planned.get("reason") or "declared_binding_unavailable")
        return {"status": "blocked", "reason": "declared_model_chain_unavailable", "declared_chain": [_binding_view(item) for item in chain], "fallback_reasons": reasons}

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

    config = stage_config or {}
    binding = profile.get("model_binding")
    mode = profile["mode"]
    chain = [binding, *profile.get("model_chain", [])] if binding else []
    reasons = []
    if mode in {"custom", "composed"} and not binding:
        return {"status": "blocked", "reason": f"{mode}_binding_missing", "declared_chain": []}
    if chain:
        for index, candidate in enumerate(chain):
            if config.get("model_profile_id") not in {None, candidate["profile"]}:
                reasons.append("stage_binding_not_declared")
                continue
            model, blockers = _model({"model_profile_id": candidate["profile"]})
            if blockers or model is None:
                reasons.append("declared_binding_unavailable")
                continue
            raw = (_models_override().get("profiles") or {}).get(candidate["profile"]) or {}
            provider = raw.get("provider_id") or model["adapter_key"]
            if (candidate["provider"] != provider or candidate["model"] != model["model"]
                    or candidate["profile"] != model["profile_id"]):
                reasons.append("declared_binding_mismatch")
                continue
            limits = _chat_limits(db, model)
            if limits is None:
                reasons.append("capability_limit_required")
                continue
            return {"status": "ready", "selected_binding": _binding_view(candidate), "model": model,
                    "chat_limits": limits,
                    "declared_chain": [_binding_view(item) for item in chain] if mode == "composed" else None,
                    "fallback_reason": None if index == 0 else "declared_chain_previous_unavailable",
                    "fallback_reasons": reasons}
        return {"status": "blocked", "reason": "custom_binding_unavailable" if mode == "custom" else "declared_model_chain_unavailable",
                "declared_chain": [_binding_view(item) for item in chain], "fallback_reasons": reasons}
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
    from .creation_recipes import _model
    from .generation.providers import _models_override

    origin = ("run_override" if "model_profile_id" in override else
              "project_stage" if "model_profile_id" in source else "identity_creative_profile")
    if origin == "identity_creative_profile":
        return chat_binding(profile, config, db=db), origin
    selected = config["model_profile_id"]
    registered = (_models_override().get("profiles") or {}).get(selected)
    model, blockers = _model({"model_profile_id": selected})
    if not registered or blockers or model is None or model["profile_id"] != selected:
        return {"status": "blocked", "reason": "explicit_stage_binding_unavailable"}, origin
    binding = {"provider": registered.get("provider_id") or model["adapter_key"],
               "model": model["model"], "profile": selected}
    # A higher-scope user selection is a new exact pin, never a fallback search.
    return chat_binding({"mode": "custom", "model_binding": binding}, config, db=db), origin


def production_stage_key(node, config):
    from .creative_method_stage import OUTPUT_SCHEMAS

    schema = config.get("output_schema", "")
    if OUTPUT_SCHEMAS.get(schema) == "research":
        return "research"
    if schema.startswith(("graphic.", "video.shot")):
        return "storyboard"
    if schema.startswith("audio.") or node["plugin"] == "media.generate":
        return "voice"
    if node["plugin"] == "stage.audio.qc":
        return "review"
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
                                "audio" if node["plugin"] in {"media.generate", "stage.audio.qc"} else unit.modality)
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
                deterministic = node["plugin"] in {"stage.graphic.compose", "stage.professional.prepare", "stage.audio.qc"}
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
                            "audio" if node["plugin"] in {"media.generate", "stage.audio.qc"} else unit.modality)
                reason = ("stage_schema_not_compatible" if node.get("stage_schema") not in applicability["compatible_stage_schemas"] else
                          "output_schema_not_compatible" if output is not None and output not in applicability["output_schemas"] else
                          "modality_not_compatible" if modality is not None and applicability["resource_modality"] != modality else None)
            else:
                rendered = method["rendered_content"]
                deterministic = node["plugin"] in {"stage.graphic.compose", "stage.professional.prepare", "stage.audio.qc"}
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
    native_tts = node["plugin"] == "media.generate" and str(node.get("plugin_version")) == "4"
    audio_qc = node["plugin"] == "stage.audio.qc"
    creative_input = contract.effective_config(node.get("config") or {}, override or {})[1] if node["plugin"] == "stage.creative.method" else {}
    output_schema = creative_input.get("output_schema", "")
    audio_planning = node["plugin"] == "stage.creative.method" and output_schema.startswith("audio.")
    graphic_planning = unit.modality == "graphic" and node["plugin"] in {"stage.creative.method", "stage.master.propose"}
    modality = "audio" if native_tts or audio_qc or audio_planning else unit.modality
    field = MODALITY_FIELDS[modality]
    profile = copy.deepcopy((identity.get("content") or {}).get(field))
    director = node["plugin"] == "stage.professional.prepare" and str(node.get("plugin_version")) == "2"
    if profile is None or (not (director or native_tts or audio_qc) and node["plugin"] not in {"stage.master.propose", "stage.creative.method", "stage.graphic.compose"}):
        return node, None, None, []
    if profile["schema"] != f"persona.creative.{modality}.v1":
        raise StageContractError("creative_profile_modality_mismatch")
    source = node.get("config") or {}
    saved_method = source.get("method") or {"source_kind": "studio_builtin", "skill_ref": profile["skill_ref"]}
    method_selection = (override or {}).get("method", saved_method)
    if type(method_selection) is not dict:
        raise StageContractError("stage_method_selection_invalid")
    stage_key = production_stage_key(node, creative_input if node["plugin"] == "stage.creative.method" else
                                     contract.effective_config(source, override or {})[1])
    selection = profile.get("production_stages", {}).get(stage_key)
    task_stages = (identity.get("content") or {}).get("product_production_stages", {})
    task_manifest = (identity.get("content") or {}).get("product_production_methods", {}).get(unit.modality)
    if stage_key in task_stages:
        selection = task_stages[stage_key]
    elif modality != unit.modality:
        task_manifest = None
    if selection is None or task_manifest is None:
        try:
            validate_creative_profile(profile)
        except ValueError as exc:
            raise StageContractError(str(exc)) from None
    defaults = profile.get("parameters", {}) if method_selection.get("skill_ref") == profile["skill_ref"] else {}
    if selection is not None:
        defaults = {key: value for key, value in defaults.items() if key != "instruction"}
    prepared = {**defaults, **source, "method": saved_method}
    composition = node["plugin"] == "stage.graphic.compose"
    deterministic = composition or director or audio_qc
    if composition:
        prepared.setdefault("preset_ref", profile["style_preset_ref"])
    if audio_qc:
        prepared.setdefault("quality_profile_ref", profile["quality_profile_ref"])
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
    elif native_tts:
        route_profile = copy.deepcopy(profile)
        if "selected_profile" in config:
            registered = model_capability_routing.configuration_view(db)["profiles"].get(config["selected_profile"], {})
            actual = registered.get("capability_bindings", {}).get("tts") or {}
            route_profile.update(mode="custom", model_chain=[], model_binding={
                "profile": config["selected_profile"], "provider": actual.get("adapter_key"), "model": actual.get("model_id")})
        # Stage preparation needs local continuity checks; ordinary profile inventory stays unprobed.
        route = _configured_binding(db, route_profile, "tts", _for_execution=True)
        if (selection is None and len(methods) != 1 or selection is not None
                and any(item.get("source_kind") != "studio_builtin" for item in methods)):
            blockers.append("native_tts_method_stack_unsupported")
        if route["status"] == "ready":
            prepared["selected_profile"] = route["selected_binding"]["profile"]
            plugin = (route.get("route") or {}).get("plugin_id")
            if plugin:
                prepared.setdefault("explicit_plugin", plugin)
    elif audio_planning or (graphic_planning and profile["capability"] != "chat"):
        # Native media pins cannot be sent to the independent planning Chat executor.
        route, chat_origin = _chat_stage_binding({"mode": "auto", "model_binding": None},
                                                config, source, override or {}, db)
        if chat_origin == "identity_creative_profile":
            chat_origin = "authorized_planning_chat_default"
    else:
        route, chat_origin = _chat_stage_binding(profile, config, source, override or {}, db)
    if route["status"] != "ready":
        blockers.append(route["reason"])
    elif not deterministic and not native_tts:
        prepared["model_profile_id"] = route["selected_binding"]["profile"]
        # The environment default is not a registered profile and must retain its existing resolution semantics.
        if route["selected_binding"]["profile"] == "default":
            prepared.pop("model_profile_id", None)
    method_base = (methods[0] if methods else {"source_kind": "studio_builtin"}) if selection is not None else base
    method = {**(method_base or {"source_kind": "studio_builtin"}), "stack": methods,
              "instruction": "\n\n".join(item["instruction"] for item in methods)}
    snapshot = db.get(IdentitySnapshot, identity["id"]) if identity.get("id") else None
    projection = {
        "schema": "effective.creative.stage.v1", "modality": modality,
        "identity_snapshot_id": identity.get("id"), "identity_checksum": identity.get("checksum"),
        "profile_origin": (snapshot.field_origins_json or {}).get(field) if snapshot else None,
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
    if audio_planning or (graphic_planning and profile["capability"] != "chat"):
        projection["binding_purpose"] = "planning_chat_stage_not_native_tts" if audio_planning else "planning_chat_stage_not_image_generation"
        projection["native_tts_policy" if audio_planning else "image_policy"] = {
            "mode": profile["mode"], "binding": profile.get("model_binding"), "chain": profile.get("model_chain", [])}
    if chat_origin is not None:
        projection["binding_origin"] = chat_origin
        if chat_origin in {"run_override", "project_stage"}:
            projection["binding_override"] = {
                "requested_profile": config["model_profile_id"], "origin": chat_origin,
                "identity_mode": profile["mode"], "identity_binding": profile.get("model_binding"),
                "identity_chain": profile.get("model_chain", []), "selected_binding": route.get("selected_binding"),
                "reason": "explicit_stage_binding",
            }
    if native_tts:
        projection["binding_origin"] = "run_override" if "selected_profile" in (override or {}) else "project_stage" if "selected_profile" in source else "identity_creative_profile"
        if "selected_profile" in config:
            projection["binding_override"] = {
                "requested_profile": config["selected_profile"], "origin": projection["binding_origin"],
                "identity_mode": profile["mode"], "identity_binding": profile.get("model_binding"),
                "identity_chain": profile.get("model_chain", []), "selected_binding": route.get("selected_binding"),
                "reason": "explicit_stage_binding",
            }
    if audio_qc:
        projection["quality_profile"] = QUALITY[config["quality_profile_ref"]]
        projection["quality_profile_origin"] = ("run_override" if "quality_profile_ref" in (override or {})
            else "project_stage" if "quality_profile_ref" in source
            else "capability_memory" if "quality_profile_ref" in parameter_defaults else "identity_creative_profile")
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
