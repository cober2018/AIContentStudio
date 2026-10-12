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
            _node("evidence", "AI", "stage.creative.method", "stage.creative.method.v1",
                  {"output_schema": "research.brief.v1", "instruction": "整理可核验来源、事实、时间边界和未知项。", "method": _method("studio.research.evidence-brief@1")}, "证据简报"),
            _node("angles", "AI", "stage.creative.method", "stage.creative.method.v1",
                  {"output_schema": "creative.angles.v1", "instruction": "提出可解释、可比较的内容角度。", "method": _method("studio.research.angle-lab@1")}, "角度实验"),
            _node("outline", "AI", "stage.creative.method", "stage.creative.method.v1",
                  {"output_schema": "content.outline.v1", "instruction": "把已接受的角度组织成结构化大纲。", "method": _method("studio.text.outline@1")}, "内容大纲"),
            _node("draft", "AI", "stage.master.propose", "stage.master.propose.v1",
                  {"purpose": "生成第一版 Master 候选", "instruction": "基于已接受的证据、角度和大纲生成候选内容。", "candidate_count": 3, "length": "long", "method": _method("studio.text.longform@1")}, "初稿候选"),
            _node("quality", "Rule", "stage.checks", "stage.checks.v1", {}, "质量检查"),
            _node("refine", "AI", "stage.master.propose", "stage.master.propose.v1",
                  {"purpose": "精修 Master 候选", "instruction": "保留已验证事实，改善结构、具体性和角色表达。", "candidate_count": 2, "length": "long", "method": _method("studio.text.humanize@1")}, "精修候选"),
            _node("title", "AI", "stage.creative.method", "stage.creative.method.v1",
                  {"output_schema": "creative.angles.v1", "instruction": "生成与正文一致、不过度夸张的标题和开头方向。", "method": _method("studio.text.title-hook@1")}, "标题与开头"),
            _node("final", "AI", "stage.master.propose", "stage.master.propose.v1",
                  {"purpose": "整合最终 Master", "instruction": "采用已接受的精修正文和标题/开头候选，保留全部精确引用与事实边界；不要增加新的事实。生成完整最终稿等待人工接受。",
                   "candidate_count": 1, "length": "long", "method": _method("studio.text.longform@1")}, "最终稿确认"),
            _node("final_quality", "Rule", "stage.checks", "stage.checks.v1", {}, "最终稿质量检查"),
        ]
        edges = [{"from": "evidence", "to": "angles"}, {"from": "angles", "to": "outline"},
                 {"from": "outline", "to": "draft"}, {"from": "draft", "to": "quality"},
                 {"from": "quality", "to": "refine"}, {"from": "refine", "to": "title"},
                 {"from": "refine", "to": "final"}, {"from": "title", "to": "final"},
                 {"from": "final", "to": "final_quality"}]
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
            _node("script", "AI", "stage.creative.method", "stage.creative.method.v1",
                  {"output_schema": "content.outline.v1", "instruction": "生成角色化视频脚本结构，明确事实、旁白和视觉意图。", "method": _method("studio.video.script@1")}, "视频脚本"),
            _node("shots", "AI", "stage.creative.method", "stage.creative.method.v1",
                  {"output_schema": "video.shot-plan.v1", "instruction": "把已接受脚本拆成镜头、旁白、字幕和素材计划。", "method": _method("studio.video.shot-director@1")}, "镜头计划"),
            _node("master", "AI", "stage.master.propose", "stage.master.propose.v1",
                  {"purpose": "确认导演计划的Video Master", "instruction": "把接受的脚本和镜头计划转成完整video.master.v2提案，保留稳定镜头/脚本/时间线结构；只引用已经提供的精确素材，缺少素材明确保留待准备状态，不假装已有最终MP4。",
                   "candidate_count": 1, "length": "medium", "method": _method("studio.video.script@1")}, "导演稿确认"),
            {**_node("prepare", "Tool", "stage.professional.prepare", "stage.professional.prepare.v2",
                  {"objective": "准备交给外部专业执行器的视频导演包", "method": _method("studio.video.director-package@1"),
                   "package_schema": "director.video.v1", "prepare_execution": False, "constraints": [], "acceptance_criteria": [], "output_kind": "video", "output_mime": "video/mp4", "output_role": "final-render", "output_count": 1, "output_max_bytes": 31457280}, "专业执行准备"), "plugin_version": "2"},
        ]
        edges = [{"from": "script", "to": "shots"}, {"from": "script", "to": "master"},
                 {"from": "shots", "to": "master"}, {"from": "master", "to": "prepare"}]
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
