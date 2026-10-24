"""Explicit starter Persona bootstrap over the existing identity/workflow truths."""

from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError, OperationalError

from ..models import (
    AccountWorkflowDefault,
    CapabilityArtifactRevision,
    ContentPersona,
    ContentPersonaRevision,
    PersonaWorkflowDefault,
    SeriesWorkflowDefault,
    User,
    Workflow,
)
from . import content_identity, creative_configuration
from .project_workflows import new_workflow_version, validate_definition, validate_portable
from .studio_creative_catalog import PRESETS, QUALITY, blueprint, digest, load_skill, validate_creative_profile


def _method(ref: str) -> dict:
    return {"source_kind": "studio_builtin", "skill_ref": ref}


def _node(node_id, kind, plugin, stage_schema, config, label):
    return {"id": node_id, "kind": kind, "plugin": plugin, "plugin_version": "1",
            "stage_schema": stage_schema, "label": label, "config": config,
            "input_mapping": {}, "output_mapping": {}, "failure_policy": "stop", "enabled": True,
            "layout": {"x": 0, "y": 0}}


def _definition(modality: str, blueprint_key: str) -> dict:
    if modality == "text":
        nodes = [
            {**_node("plan", "AI", "stage.creative.method", "stage.creative.method.v3",
                  {"output_schema": "article.plan.v1", "instruction": "给出 3 个不同论点的完整写作方案：角度、读者为什么关心、用到的事实、仍未知的部分和大纲。", "candidate_count": 3,
                   "method": _method("studio.text.article-plan@1")}, "写作方案"), "plugin_version": "3"},
            _node("write", "AI", "stage.master.propose", "stage.master.propose.v1",
                  {"purpose": "按选定方案一次写成全文", "instruction": "按已选写作方案写出完整文章：标题、开头和正文一次写完，另给两个备选标题。不要编造数字、版本或来源。",
                   "candidate_count": 1, "length": "long", "method": _method("studio.text.article-write@1")}, "成稿"),
            _node("quality", "Rule", "stage.checks", "stage.checks.v1", {}, "质量检查"),
        ]
        edges = [{"from": "plan", "to": "write"}, {"from": "write", "to": "quality"}]
        for node in nodes:
            if node["kind"] == "AI":
                node["config"]["fact_mode"] = "current" if blueprint_key == "starter.lifestyle-observer.v1" else "grounded"
    elif modality == "graphic":
        nodes = [
            _node("visual", "AI", "stage.creative.method", "stage.creative.method.v1",
                  {"output_schema": "graphic.visual-direction.v1", "instruction": "定义清晰的视觉方向、信息层级和素材需求。", "method": _method("studio.graphic.visual-director@1")}, "视觉方向"),
            _node("cards", "AI", "stage.creative.method", "stage.creative.method.v1",
                  {"output_schema": "graphic.card-plan.v1", "instruction": "把视觉方向转成卡片语义计划，不计算原始像素。", "method": _method("studio.graphic.card-plan@1")}, "卡片计划"),
            _node("master", "Tool", "stage.graphic.compose", "stage.graphic.compose.v1",
                  {"template": "editorial", "density": "low" if blueprint_key == "starter.lifestyle-observer.v1" else "medium",
                   "method": _method("studio.graphic.layout-compose@1")}, "确定性排版候选"),
            _node("quality", "Rule", "stage.checks", "stage.checks.v1", {}, "图文质量检查"),
        ]
        edges = [{"from": "visual", "to": "cards"}, {"from": "cards", "to": "master"}, {"from": "master", "to": "quality"}]
    else:
        nodes = [
            _node("master", "AI", "stage.master.propose", "stage.master.propose.v1",
                  {"purpose": "生成分镜表导演稿", "instruction": "一次写完整张分镜表：一行一个镜头，按播放顺序。每行写信息点、画面（景别、主体、动作、场景、光线）、运镜、台词（实际念的原话，标明旁白/口播/对白，没有就写无台词）、声音、备注和估计时长。一个镜头只讲一件事；信息点写要点，台词写原话，两列不重复。不要返回编号、引用或素材 id，也不要声称已经生成 MP4。",
                   "candidate_count": 1, "length": "medium", "method": _method("studio.video.script@1")}, "导演稿"),
        ]
        # The edit task builds its own director package from the saved master, so no separate prepare stage.
        edges = []
    return {"nodes": nodes, "edges": edges, "visual_order": [node["id"] for node in nodes]}


def audio_definition(blueprint_key: str, *, alignment: bool = False) -> dict:
    lifestyle = blueprint_key == "starter.lifestyle-observer.v1"
    voice_style = "自然聊天、温暖而不说教" if lifestyle else "冷静清楚的工程师解说，保留技术名称和trade-off"
    nodes = [
        _node("spoken", "AI", "stage.creative.method", "stage.creative.method.v1", {
            "output_schema": "audio.spoken-adaptation.v1", "instruction": "只把当前已接受的Text正文或Video脚本转成适合朗读的口语稿；不添加事实，不把来源当台词，保留术语并明确发音。",
            "length": "long", "pace": "medium", "method": _method("studio.audio.spoken-adapt@1")}, "口语稿确认"),
        _node("voice", "AI", "stage.creative.method", "stage.creative.method.v1", {
            "output_schema": "audio.voice-direction.v1", "instruction": f"为已接受口语稿制定声音方案：{voice_style}。描述停顿、节奏和语速；风格名称不是供应商voice ID，不得编造ID或声纹。",
            "method": _method("studio.audio.voice-director@1")}, "声音方案确认"),
        {**_node("tts", "Tool", "media.generate", "media.generate.stage.v4", {
            "capability": "tts", "tts_source": "accepted_spoken", "method": _method("studio.audio.tts@1"),
            "items": 1, "seconds": 360, "timeout_seconds": 25}, "生成并接受真实音频"), "plugin_version": "4"},
        _node("audio_quality", "Rule", "stage.audio.qc", "stage.audio.qc.v1", {
            "method": _method("studio.audio.qc@1")}, "音频质量确认"),
    ]
    edges = [{"from": "spoken", "to": "voice"}, {"from": "spoken", "to": "tts"},
             {"from": "voice", "to": "tts"}, {"from": "tts", "to": "audio_quality"}]
    if alignment:
        nodes.insert(-1, _node("audio_asr", "Tool", "stage.audio.asr", "stage.audio.asr.v1", {
            "provider_key": "local.mlx_whisper", "provider_version": "1", "timeout_seconds": 120},
            "本机 ASR 对稿（明确执行并接受）"))
        nodes[-1]["config"].update(alignment_enabled=True, srt_mode="asr")
        edges.extend([{"from": "tts", "to": "audio_asr"}, {"from": "audio_asr", "to": "audio_quality"}])
    return {"nodes": nodes, "edges": edges,
        "visual_order": [node["id"] for node in nodes]}



def method_trial_definition(modality, blueprint_key, *, audio=False):
    """Opt-in work recipe; saved Persona defaults and the v1 templates stay untouched."""
    from .studio_creative_catalog import PERSONA_METHOD_TRIAL_KEYS

    definition = deepcopy(audio_definition(blueprint_key, alignment=True) if audio else _definition(modality, blueprint_key))
    for node in definition["nodes"]:
        config = node["config"]
        ref = (config.get("method") or {}).get("skill_ref", "")
        key = ref.rsplit("@", 1)[0]
        if key in PERSONA_METHOD_TRIAL_KEYS:
            config["method"]["skill_ref"] = key + "@2"
        if node["plugin"] == "stage.creative.method" and node["plugin_version"] == "1":
            node.update(plugin_version="2", stage_schema="stage.creative.method.v2")
            if config.get("output_schema") in {"graphic.card-plan.v1", "video.shot-plan.v1"}:
                config["output_schema"] = config["output_schema"].replace(".v1", ".v2")
    return definition


def _profile_payload(item: dict, key: str) -> dict:
    result = {field: deepcopy(value) for field, value in item.items()
              if field not in {"key", "name", "version"} and not field.endswith("_creative_profile")}
    for field in ("text_creative_profile", "graphic_creative_profile", "audio_creative_profile", "video_creative_profile"):
        profile = deepcopy(item[field])
        profile["provenance"] = {**(profile.get("provenance") or {}), "blueprint_key": key, "blueprint_version": item["version"]}
        result[field] = profile
    return result


def _blueprint_persona(db, user, key: str):
    item = blueprint(key)
    rows = db.scalars(select(ContentPersona).where(ContentPersona.owner_user_id == user.id).order_by(ContentPersona.id)).all()
    for persona in rows:
        revision = content_identity.current_revision(db, "persona", persona.id)
        history = db.scalars(select(ContentPersonaRevision).where(
            ContentPersonaRevision.persona_id == persona.id).order_by(ContentPersonaRevision.revision_no)).all()
        # A fork's initial revision points to its own immutable recipes, not the bootstrap root.
        if history and any((((history[0].profile_json.get(field) or {}).get("provenance") or {}).get(
                "default_recipe_key") or "").startswith(f"persona.{persona.id}.fork.")
                for field in creative_configuration.MODALITY_FIELDS.values()):
            continue
        keys = {((row.profile_json.get(field) or {}).get("provenance") or {}).get("blueprint_key")
                for row in history
                for field in ("text_creative_profile", "graphic_creative_profile", "audio_creative_profile", "video_creative_profile")}
        if key in keys:
            return persona, revision, item
    if any(persona.name == item["name"] for persona in rows):
        raise HTTPException(409, "starter_blueprint_name_conflict")
    return None, None, item


def preview(key: str) -> dict:
    item = blueprint(key)
    return {"schema": "starter.persona.apply-preview.v1", "blueprint": key, "version": item["version"],
            "name": item["name"], "profile_checksum": digest(_profile_payload(item, key)),
            "workflow_modalities": ["text", "graphic", "video"], "profile": item}


def fork(db, user, key: str, *, name: str, expected_profile_checksum: str) -> dict:
    """Explicitly create a separate blueprint copy; bootstrap lookup must never adopt it."""
    try:
        if not user.is_active or user.role not in {"editor", "admin"}:
            raise HTTPException(403, "starter_blueprint_readonly")
        try:
            item = blueprint(key)
        except ValueError:
            raise HTTPException(404, "starter_blueprint_not_found") from None
        if expected_profile_checksum != preview(key)["profile_checksum"]:
            raise HTTPException(409, "starter_blueprint_preview_changed")
        name = name.strip()
        if not name or len(name) > 200 or name == item["name"]:
            raise HTTPException(422, "starter_fork_distinct_name_required")
        locked = db.execute(update(User).where(User.id == user.id, User.is_active.is_(True),
            User.role.in_(["editor", "admin"])).values(is_active=User.is_active))
        if locked.rowcount != 1:
            raise HTTPException(403, "starter_blueprint_readonly")
        if db.scalar(select(ContentPersona.id).where(ContentPersona.owner_user_id == user.id,
                ContentPersona.name == name)) is not None:
            raise HTTPException(409, "starter_fork_name_conflict")
        persona = ContentPersona(owner_user_id=user.id, name=name)
        db.add(persona)
        db.flush()
        profile = _profile_payload(item, key)
        workflows = []
        for modality in ("text", "graphic", "video"):
            recipe_key = f"persona.{persona.id}.fork.{modality}"
            profile[f"{modality}_creative_profile"]["provenance"]["default_recipe_key"] = recipe_key
            definition = validate_portable(validate_definition(_definition(modality, key)),
                source_project_id=None, source_unit_id=None)
            workflow = new_workflow_version(db, key=recipe_key, name=f"{name} × {modality}",
                definition=definition, owner_user_id=user.id, scope="persona_default", created_by=user.email)
            db.add(PersonaWorkflowDefault(persona_id=persona.id, modality=modality,
                workflow_id=workflow.id, revision=1))
            workflows.append({"modality": modality, "workflow_id": workflow.id, "checksum": workflow.checksum})
        desired = content_identity.IdentityProfile.model_validate(profile).model_dump(
            mode="json", by_alias=True, exclude_unset=True)
        revision = ContentPersonaRevision(persona_id=persona.id, revision_no=1, profile_json=desired,
            checksum=content_identity.checksum(desired), created_by=user.email)
        db.add(revision)
        db.flush()
        result = {"status": "forked", "created": True, "persona_id": persona.id,
            "revision_id": revision.id, "revision_no": 1, "profile_checksum": revision.checksum,
            "blueprint": key, "blueprint_version": item["version"], "workflows": workflows}
        db.commit()
        return result
    except (IntegrityError, OperationalError):
        db.rollback()
        raise HTTPException(409, "starter_blueprint_apply_conflict") from None
    except ValueError:
        db.rollback()
        raise HTTPException(422, "starter_fork_profile_invalid") from None
    except BaseException:
        db.rollback()
        raise


def _recipe(db, identity: dict, user, modality: str) -> dict | None:
    for scope, model, field in (("series", SeriesWorkflowDefault, "series_id"),
            ("account", AccountWorkflowDefault, "account_id"), ("persona", PersonaWorkflowDefault, "persona_id")):
        entity_id = identity.get(field)
        if entity_id is None:
            continue
        binding = db.scalar(select(model).where(getattr(model, field) == entity_id, model.modality == modality))
        if binding is not None:
            workflow = db.get(Workflow, binding.workflow_id)
            return {"source": scope, "binding_revision": binding.revision, "workflow_id": binding.workflow_id,
                "workflow_version": workflow.version if workflow else None,
                "checksum": workflow.checksum if workflow else None,
                "available": bool(workflow and workflow.owner_user_id == user.id and workflow.status == "published"),
                "definition": deepcopy(workflow.definition_json) if workflow else {}}
    return None


def readiness(db, user, *, persona_id: int, account_id: int | None = None, series_id: int | None = None) -> dict:
    """Read-only configuration readiness, not rendered-output or human-quality acceptance."""
    from .creation_recipes import _method
    from .stage_contracts import StageContractError

    with db.no_autoflush:
        identity = content_identity.effective(db, user, persona_id=persona_id, account_id=account_id, series_id=series_id)
        hierarchy = content_identity.hierarchy(db, user, persona_id=persona_id, account_id=account_id, series_id=series_id)
        archived = any(row.status == "archived" for _, row in hierarchy.members())
        unit = SimpleNamespace(project_id=None, persona_id=persona_id, account_id=account_id,
            series_id=series_id, channel_id=None)
        modalities = {}
        for modality, field in creative_configuration.MODALITY_FIELDS.items():
            profile = deepcopy(identity["effective_profile"].get(field))
            origin = identity["creative_profile_origins"].get(field)
            report = {"status": "blocked", "reasons": [], "profile": profile,
                "profile_hash": digest(profile), "profile_source": origin,
                "profile_revision_id": identity["revision_ids"].get(origin), "recipe": _recipe(db, identity, user, modality),
                "selected_binding": None, "declared_chain": [], "fallback_reason": None,
                "resources": [], "quality_acceptance": "not_evaluated"}
            blockers, incomplete = [], []
            if not user.is_active:
                blockers.append("identity_owner_inactive")
            if archived:
                blockers.append("identity_archived")
            if not profile:
                blockers.append("creative_profile_missing")
                report["reasons"] = blockers
                modalities[modality] = report
                continue
            try:
                validate_creative_profile(profile)
                if profile["schema"] != f"persona.creative.{modality}.v1":
                    raise ValueError("creative_profile_modality_mismatch")
                recipe = report["recipe"]
                if modality == "audio" and recipe is None:
                    key = profile.get("provenance", {}).get("blueprint_key")
                    if key:
                        blueprint(key)
                        definition = validate_portable(validate_definition(audio_definition(key)),
                            source_project_id=None, source_unit_id=None)
                        recipe = report["recipe"] = {"source": "studio_builtin_audio", "blueprint": key,
                            "checksum": digest(definition), "available": True, "definition": definition}
                        incomplete.append("audio_recipe_requires_explicit_project_selection")
                if not recipe or not recipe["available"]:
                    blockers.append("default_recipe_unavailable")
                elif recipe.get("definition"):
                    validate_portable(validate_definition(recipe["definition"]),
                        source_project_id=None, source_unit_id=None)
                refs = [profile["skill_ref"], *[node.get("config", {})["method"]["skill_ref"]
                    for node in (recipe or {}).get("definition", {}).get("nodes", [])
                    if node.get("config", {}).get("method", {}).get("source_kind") == "studio_builtin"]]
                for ref in dict.fromkeys(refs):
                    package = load_skill(ref)
                    report["resources"].append({"ref": ref, "package_hash": package["package_hash"]})
                report["preset"] = {"ref": profile["style_preset_ref"], "hash": digest(PRESETS[profile["style_preset_ref"]])}
                report["quality"] = {"ref": profile["quality_profile_ref"], "hash": digest(QUALITY[profile["quality_profile_ref"]])}
                if profile["mode"] != "composed" and (profile.get("capability_memory_revision_ids") or profile.get("installed_skill_refs")):
                    blockers.append("creative_composition_mode_required")
                for revision_id in profile.get("capability_memory_revision_ids", []):
                    revision = db.get(CapabilityArtifactRevision, revision_id)
                    if revision is None:
                        blockers.append("method_revision_unavailable")
                        continue
                    _, reasons = _method(db, user, unit, {"plugin": "stage.creative.method", "plugin_version": "1"},
                        {"method": {"source_kind": "capability_memory", "artifact_id": revision.artifact_id,
                            "revision_id": revision_id, "arguments": {}}})
                    blockers.extend(reasons)
                if profile.get("installed_skill_refs"):
                    blockers.append("installed_skill_stage_execution_unavailable")
                if profile.get("capability_memory_revision_ids"):
                    deterministic_nodes = [node for node in (recipe or {}).get("definition", {}).get("nodes", [])
                        if node.get("plugin") in {"stage.graphic.compose", "stage.audio.qc"}
                        or (node.get("plugin") == "stage.professional.prepare"
                            and str(node.get("plugin_version")) == "2")]
                    for node in deterministic_nodes:
                        for revision_id in profile["capability_memory_revision_ids"]:
                            revision = db.get(CapabilityArtifactRevision, revision_id)
                            if revision is None:
                                continue
                            method, reasons = _method(db, user, unit, node, {"method": {
                                "source_kind": "capability_memory", "artifact_id": revision.artifact_id,
                                "revision_id": revision_id, "arguments": {}}})
                            if reasons or not method or "deterministic_parameters" not in method:
                                blockers.append("deterministic_stage_method_parameters_required")
                route = creative_configuration._configured_binding(db, profile, profile["capability"])
                report.update(selected_binding=route.get("selected_binding"), declared_chain=route.get("declared_chain"),
                    fallback_reason=route.get("fallback_reason"))
                if route["status"] != "ready":
                    (incomplete if modality == "graphic" and profile["mode"] == "auto" else blockers).append(
                        route.get("reason") or "model_binding_unavailable")
                if modality in {"graphic", "audio"}:
                    planning = creative_configuration.chat_binding({"mode": "auto", "model_binding": None}, db=db)
                    report["planning_binding"] = planning.get("selected_binding")
                    if planning["status"] != "ready":
                        blockers.append("planning_chat_unavailable")
                model = route.get("model") or {}
                if model.get("provider") == "mock":
                    incomplete.append("mock_provider_contract_only")
                if modality == "graphic":
                    incomplete.append("graphic_render_scope_requires_project_master")
                elif modality == "audio":
                    voice = profile.get("parameters", {}).get("voice")
                    if not voice:
                        blockers.append("tts_voice_id_not_configured")
                    runtime_hash = (route.get("route") or {}).get("runtime_hash")
                    if route["status"] == "ready" and not runtime_hash:
                        blockers.append("tts_runtime_unverified")
                    incomplete.append("tts_voice_and_output_require_execution_validation")
                elif modality == "video":
                    incomplete.append("external_video_execution_required")
                if (identity["effective_profile"].get("public_fact_policy") or {}).get("fresh_source_required_for_current_claims"):
                    report["current_facts_require_fresh_source"] = True
            except (ValueError, HTTPException) as exc:
                reason = str(exc) if isinstance(exc, StageContractError) else (
                    str(exc) if isinstance(exc, ValueError) else "creative_resource_or_scope_unavailable")
                blockers.append(reason)
            report["status"] = "blocked" if blockers else "partial" if incomplete else "ready"
            report["reasons"] = list(dict.fromkeys([*blockers, *incomplete]))
            if report["recipe"]:
                report["recipe"].pop("definition", None)
            modalities[modality] = report
        result = {"schema": "persona.creative.readiness.v1", "persona_id": persona_id,
            "creative_root": {"scope": "persona", "id": persona_id}, "account_id": account_id,
            "series_id": series_id, "identity_revision_ids": identity["revision_ids"],
            "identity_checksum": digest(identity), "modalities": modalities,
            "coverage": "read_only_configuration_not_provider_or_quality_acceptance"}
        result["readiness_hash"] = digest(result)
        return result


def apply(db, user, key: str) -> dict:
    try:
        if not user.is_active or user.role not in {"editor", "admin"}:
            raise HTTPException(403, "starter_blueprint_readonly")
        # The existing owner row serializes bootstrap across API processes without a new uniqueness table.
        locked = db.execute(update(User).where(User.id == user.id).values(is_active=User.is_active))
        if locked.rowcount != 1:
            raise HTTPException(404, "starter_blueprint_owner_not_found")
        result = _apply_locked(db, user, key)
        db.commit()
        return result
    except (IntegrityError, OperationalError):
        db.rollback()
        raise HTTPException(409, "starter_blueprint_apply_conflict") from None
    except BaseException:
        db.rollback()
        raise


def _apply_locked(db, user, key: str) -> dict:
    try:
        persona, current, item = _blueprint_persona(db, user, key)
    except ValueError:
        raise HTTPException(404, "starter_blueprint_not_found") from None
    desired = content_identity.IdentityProfile.model_validate(_profile_payload(item, key)).model_dump(
        mode="json", by_alias=True, exclude_unset=True)
    desired_checksum = content_identity.checksum(desired)
    if persona is not None:
        return {"status": "already_initialized", "created": False, "persona_id": persona.id,
                "current_revision": current.revision_no if current else 0,
                "current_checksum": current.checksum if current else None,
                "desired_checksum": desired_checksum, "requires_explicit_replace": True}
    persona = ContentPersona(owner_user_id=user.id, name=item["name"])
    db.add(persona)
    db.flush()
    revision = ContentPersonaRevision(persona_id=persona.id, revision_no=1, profile_json=desired,
                                      checksum=desired_checksum, created_by=user.email)
    db.add(revision)
    workflows = []
    try:
        for modality in ("text", "graphic", "video"):
            definition = validate_portable(validate_definition(_definition(modality, key)), source_project_id=None, source_unit_id=None)
            workflow = new_workflow_version(db, key=f"persona.{persona.id}.{modality}", name=f"{persona.name} × {modality}",
                                            definition=definition, owner_user_id=user.id, scope="persona_default", created_by=user.email)
            binding = PersonaWorkflowDefault(persona_id=persona.id, modality=modality, workflow_id=workflow.id, revision=1)
            db.add(binding)
            workflows.append({"modality": modality, "workflow_id": workflow.id, "checksum": workflow.checksum})
        db.flush()
    except (ValueError, IntegrityError) as exc:
        db.rollback()
        if isinstance(exc, IntegrityError):
            raise HTTPException(409, "starter_blueprint_apply_conflict") from None
        raise HTTPException(422, str(exc)) from None
    db.refresh(persona)
    return {"status": "initialized", "created": True, "persona_id": persona.id, "revision_id": revision.id,
            "revision_no": 1, "profile_checksum": revision.checksum, "workflows": workflows,
            "blueprint": key}
