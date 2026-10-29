"""Persona creative contracts on isolated SQLite; no live providers or bootstrap."""

from copy import deepcopy

import pytest
from sqlalchemy import select

from app.models import (
    ContentMasterRevision,
    ContentPersona,
    ContentPersonaRevision,
    PersonaWorkflowDefault,
    User,
    Workflow,
)
from app.services import creative_configuration, starter_personas
from app.services import studio_creative_catalog as catalog
from app.services.content_identity import CreativeProfile


def _profile(**changes):
    return {**deepcopy(catalog.BLUEPRINTS["starter.ai-tech-engineer.v1"]["text_creative_profile"]), **changes}


TEXT_SKILLS = [ref for ref, item in catalog.SKILLS.items() if item["modality"] in {"research", "text"}]

RESOURCE_CASES = [
    (kind, ref) for kind, pool in (
        ("skill", catalog.SKILLS), ("style_preset", catalog.PRESETS), ("quality_profile", catalog.QUALITY)
    ) for ref in pool
]

EXPECTED_RECIPE_KEYS = {
    "starter.ai-tech-engineer.v1": {
        "text": "persona.text.ai-tech.v1", "graphic": "persona.graphic.ai-tech.v1",
        "audio": "persona.audio.ai-tech.v1", "video": "persona.video.ai-tech.v1",
    },
    "starter.lifestyle-observer.v1": {
        "text": "persona.text.lifestyle.v1", "graphic": "persona.graphic.lifestyle.v1",
        "audio": "persona.audio.lifestyle.v1", "video": "persona.video.lifestyle.v1",
    },
}


@pytest.mark.parametrize("kind,ref", RESOURCE_CASES)
def test_every_shipped_resource_has_an_exact_version_and_safe_inventory(kind, ref):
    import json

    pool = {"skill": catalog.SKILLS, "style_preset": catalog.PRESETS, "quality_profile": catalog.QUALITY}[kind]
    resource = pool[ref]
    assert catalog.validate_ref(ref, kind=kind) == ref
    assert ref == f"{resource['key']}@{resource['version']}"
    assert resource["source_kind"] == "studio_builtin"
    assert resource["provenance"] == "self_developed"
    assert resource["license"] == "product_owned"
    assert catalog.digest(resource) == catalog.digest(deepcopy(resource))
    projection = catalog.inventory()[{"skill": "skills", "style_preset": "style_presets",
                                      "quality_profile": "quality_profiles"}[kind]]
    assert next(item for item in projection if item["ref"] == ref)["version"] == resource["version"]
    assert not any(value in json.dumps(resource) for value in ("/Users/", "file://", "api_key", "raw_output"))
    if kind == "skill":
        package = catalog.load_skill(ref)
        assert package["contract"]["ref"] == ref
        assert package["contract"]["parameter_schema"]["additionalProperties"] is False
        assert set(package["contract"]["parameter_schema"]["properties"]) == set(resource["tunable_fields"])
        assert len(package["instruction"]) >= 120
        assert package["package_hash"] == catalog.digest({
            key: value for key, value in package.items() if key != "package_hash"})
    elif kind == "style_preset":
        assert resource["config"]["modality"] in {"text", "graphic", "audio"}
    else:
        assert resource["checks"] and resource["human_review_required"] is True


@pytest.mark.parametrize("key", list(catalog.BLUEPRINTS))
@pytest.mark.parametrize("modality", ["text", "graphic", "audio", "video"])
def test_blueprint_profiles_pin_exact_schema_resources_and_recipe_version(key, modality):
    item = catalog.blueprint(key)
    profile = item[f"{modality}_creative_profile"]
    assert catalog.validate_creative_profile(profile) == profile
    assert profile["schema"] == f"persona.creative.{modality}.v1"
    for field, kind in (("skill_ref", "skill"), ("style_preset_ref", "style_preset"),
                        ("quality_profile_ref", "quality_profile")):
        assert catalog.validate_ref(profile[field], kind=kind) == profile[field]
    assert profile["provenance"]["default_recipe_key"] == EXPECTED_RECIPE_KEYS[key][modality]
    assert catalog.blueprint_preview(key)["checksum"] == catalog.digest(item)
    item["positioning"] = "调用方修改副本"
    assert catalog.blueprint(key)["positioning"] != item["positioning"]


@pytest.mark.parametrize("key", list(catalog.BLUEPRINTS))
@pytest.mark.parametrize("modality", ["text", "graphic", "audio", "video"])
@pytest.mark.parametrize("fault,reason", [
    ("schema", "creative_profile_invalid"),
    ("skill", "creative_profile_modality_mismatch"),
    ("preset", "creative_profile_preset_mismatch"),
    ("quality", "creative_profile_quality_mismatch"),
    ("provenance", "creative_profile_provenance_invalid"),
])
def test_blueprint_profiles_reject_schema_drift_cross_modality_refs_and_forged_metadata(
        key, modality, fault, reason):
    profile = deepcopy(catalog.BLUEPRINTS[key][f"{modality}_creative_profile"])
    if fault == "schema":
        profile["schema"] = f"persona.creative.{modality}.v999"
    elif fault == "skill":
        profile["skill_ref"] = "studio.audio.tts@1" if modality != "audio" else "studio.text.longform@1"
    elif fault == "preset":
        profile["style_preset_ref"] = ("studio.audio.calm-engineer@1" if modality != "audio"
                                       else "studio.text.deep-technical@1")
    elif fault == "quality":
        profile["quality_profile_ref"] = ("studio.quality.audio.explainer@1" if modality != "audio"
                                          else "studio.quality.text.technical@1")
    else:
        profile["provenance"]["untrusted_method_source"] = "not-an-allowed-origin"
    with pytest.raises(ValueError, match=f"^{reason}$"):
        catalog.validate_creative_profile(profile)


@pytest.mark.parametrize("key", list(catalog.BLUEPRINTS))
@pytest.mark.parametrize("recipe", ["text", "graphic", "video", "audio", "audio_asr"])
def test_all_persona_recipes_are_portable_with_exact_registered_graph_and_methods(key, recipe):
    from app.services.content_harness.nodes import bootstrap_builtin_nodes
    from app.services.content_harness.registry import registry
    from app.services.project_workflows import validate_definition, validate_portable

    bootstrap_builtin_nodes()
    definition = (starter_personas.audio_definition(key, alignment=recipe == "audio_asr")
                  if recipe.startswith("audio") else starter_personas._definition(recipe, key))
    original = deepcopy(definition)
    validated = validate_portable(validate_definition(definition), source_project_id=None, source_unit_id=None)
    assert definition == original
    node_ids = [node["id"] for node in validated["nodes"]]
    assert len(node_ids) == len(set(node_ids))
    assert set(validated["visual_order"]) == set(node_ids)
    position = {node_id: index for index, node_id in enumerate(validated["visual_order"])}
    for edge in validated["edges"]:
        assert edge["from"] in position and edge["to"] in position
        assert position[edge["from"]] < position[edge["to"]]
    for node in validated["nodes"]:
        descriptor = registry.descriptor("node", node["plugin"], node["plugin_version"])
        assert descriptor.stage_contract.to_dict()["stage_schema"] == node["stage_schema"]
        descriptor.stage_contract.validate_config(node["config"])
        if method := node["config"].get("method"):
            package = catalog.load_skill(method["skill_ref"])
            assert node["stage_schema"] in package["contract"]["compatible_stage_schemas"]
    if recipe.startswith("audio"):
        assert [node["plugin"] for node in validated["nodes"]].count("stage.audio.asr") == (recipe == "audio_asr")
        assert not any(node["plugin"] == "stage.master.propose" for node in validated["nodes"])


@pytest.mark.parametrize("kind,ref", RESOURCE_CASES)
def test_wrong_resource_versions_and_kinds_never_silently_fall_back(kind, ref):
    with pytest.raises(ValueError, match="creative_resource_ref_unavailable"):
        catalog.validate_ref(ref.rsplit("@", 1)[0] + "@999", kind=kind)
    other = "quality_profile" if kind != "quality_profile" else "style_preset"
    with pytest.raises(ValueError, match="creative_resource_ref_unavailable"):
        catalog.validate_ref(ref, kind=other)


@pytest.fixture
def isolated_skill_package(tmp_path, monkeypatch):
    import shutil
    from pathlib import Path

    ref = "studio.text.longform@1"
    source = Path(catalog.__file__).resolve().parents[1] / "studio_skills" / catalog.SKILLS[ref]["key"] / "v1"
    target = tmp_path / "studio_skills" / catalog.SKILLS[ref]["key"] / "v1"
    shutil.copytree(source, target)
    monkeypatch.setattr(catalog, "__file__", str(tmp_path / "services" / "studio_creative_catalog.py"))
    return ref, target


@pytest.mark.parametrize("fault,reason", [
    ("missing", "studio_skill_package_unavailable"),
    ("symlink", "studio_skill_package_unavailable"),
    ("version", "studio_skill_frontmatter_invalid"),
    ("provenance", "studio_skill_provenance_invalid"),
    ("license", "studio_skill_provenance_invalid"),
    ("contract", "studio_skill_contract_drift"),
    ("tool", "studio_skill_required_tool_unavailable"),
    ("tool_version", "studio_skill_required_tool_unavailable"),
    ("reference", "studio_skill_reference_unavailable"),
    ("path", "studio_skill_reference_path_invalid"),
    ("secret", "stage_secret_or_control_forbidden"),
])
def test_package_validation_rejects_broken_provenance_tools_refs_and_secrets(
        isolated_skill_package, monkeypatch, fault, reason):
    import json

    ref, directory = isolated_skill_package
    if fault == "missing":
        (directory / "STUDIO-META.md").unlink()
    elif fault == "symlink":
        path = directory / "SKILL.md"
        original = directory.parent / "outside.md"
        path.rename(original)
        path.symlink_to(original)
    elif fault in {"version", "secret"}:
        path = directory / "SKILL.md"
        value = path.read_text()
        path.write_text(value.replace("version: 1", "version: 999") if fault == "version"
                        else value + "\nsk-abcdefghijklmnopqrstuvwxyz0123456789\n")
    elif fault in {"provenance", "license"}:
        path = directory / "STUDIO-META.md"
        value = path.read_text()
        path.write_text(value.replace("classification: self_developed", "classification: forged")
                        if fault == "provenance" else value.replace("license: product_owned", "license: unknown"))
    else:
        path = directory / "STUDIO-CONTRACT.json"
        contract = json.loads(path.read_text())
        if fault == "contract":
            contract["version"] = "999"
        elif fault in {"tool", "tool_version"}:
            tools = ["studio.missing.tool@1" if fault == "tool" else "studio.graphic.layout-compose@999"]
            resource = {**deepcopy(catalog.SKILLS[ref]), "tools": tools}
            monkeypatch.setitem(catalog.SKILLS, ref, resource)
            contract["tools"] = tools
        else:
            contract["references"] = ["references/missing.md" if fault == "reference" else "../outside.md"]
        path.write_text(json.dumps(contract, ensure_ascii=False))
    with pytest.raises(ValueError, match=reason):
        catalog.load_skill(ref)


TUNABLE_VALUES = {
    "instruction": ("解释约束与代价", "强调观察与限制"),
    "candidate_count": (1, 3), "length": ("short", "long"), "tone": ("自然", "冷静具体"),
    "density": ("low", "high"), "canvas_count": (2, 4), "aspect_ratio": ("1:1", "9:16"),
    "pace": ("slow", "fast"), "energy": ("平稳", "轻快"),
    "pause_policy": ("段落停顿", "术语前停顿"), "shot_count": (3, 7),
}
CHAT_TUNABLE_CASES = [(ref, field) for ref, item in catalog.SKILLS.items()
    if {"stage.creative.method.v1", "stage.creative.method.v3", "stage.master.propose.v1"} & set(item["compatible_stage_schemas"])
    for field in item["tunable_fields"]]


def _resolve_builtin_tunable(db, ref, field, value):
    from types import SimpleNamespace

    from app.services.content_harness.nodes import bootstrap_builtin_nodes
    from app.services.content_harness.registry import registry
    from app.services.stage_resolver import resolve_stage

    bootstrap_builtin_nodes()
    resource = catalog.SKILLS[ref]
    stage_schema = resource["compatible_stage_schemas"][0]
    descriptor = next(item for item in registry.list("node") if item.stage_contract is not None
                      and item.stage_contract.to_dict()["stage_schema"] == stage_schema)
    modality = "text" if resource["modality"] in {"research", "audio"} else resource["modality"]
    profile_modality = "audio" if resource["modality"] == "audio" else modality
    profile = deepcopy(catalog.BLUEPRINTS["starter.ai-tech-engineer.v1"][f"{profile_modality}_creative_profile"])
    if resource["modality"] != "research":
        profile.update(skill_ref=ref, parameters={field: TUNABLE_VALUES[field][0]})
    config = {"instruction": "仅整理隔离测试输入", "method": {"source_kind": "studio_builtin", "skill_ref": ref}}
    if stage_schema in {"stage.creative.method.v1", "stage.creative.method.v3"}:
        config["output_schema"] = resource["output_schemas"][0]
    config[field] = TUNABLE_VALUES[field][0]
    node = {"id": "method", "kind": descriptor.stage_contract.to_dict()["category"],
            "plugin": descriptor.key, "plugin_version": descriptor.version,
            "stage_schema": stage_schema, "config": config}
    context = {"modality": modality, "identity": {"checksum": "a" * 64,
        "content": {f"{profile_modality}_creative_profile": profile}},
        "brief": {"id": 1, "checksum": "b" * 64, "content": {"objective": "隔离合同检查"}}}
    override = {field: value}
    effective_node, method, creative, blockers = creative_configuration.frozen_stage(
        db, SimpleNamespace(id=1), SimpleNamespace(id=1, project_id=1, modality=modality),
        node, descriptor.stage_contract, context, override)
    assert not blockers, blockers
    return resolve_stage(workflow={"id": 1, "version": 1, "checksum": "c" * 64},
        node=effective_node, contract=descriptor.stage_contract, context=context, upstream={},
        method=method, model={"provider": "mock", "model": "mock-structured-v1", "profile_id": "default"},
        override=override, creative=creative)


@pytest.mark.parametrize("ref,field", CHAT_TUNABLE_CASES)
def test_each_exposed_chat_tunable_reaches_the_actual_executor_request(db_session, ref, field):
    import json

    from app.services import creative_method_stage, stage_master_proposals

    first, changed = (_resolve_builtin_tunable(db_session, ref, field, value)
                      for value in TUNABLE_VALUES[field])
    assert first["ready"] and changed["ready"]
    assert first["resolution_hash"] != changed["resolution_hash"]
    assert first["config_hash"] != changed["config_hash"]
    assert first["prompt_hash"] != changed["prompt_hash"]
    assert changed["creative_configuration"]["method_stack"][0]["skill_ref"] == ref
    builder = (creative_method_stage.build_request if changed["node"]["plugin"] == "stage.creative.method"
               else stage_master_proposals.build_master_request)
    request = builder(changed)
    assert request.user_prompt == changed["effective_prompt"]
    assert request.system_prompt == changed["system_prompt"]
    sections = {item["key"]: item["text"] for item in changed["prompt_sections"]}
    if field == "instruction":
        assert sections["stage_instruction"] == TUNABLE_VALUES[field][1]
        assert TUNABLE_VALUES[field][1] in request.user_prompt
    else:
        assert json.loads(sections["execution_controls"])[field] == TUNABLE_VALUES[field][1]
    if field in {"candidate_count", "length"}:
        assert request.context[field] == TUNABLE_VALUES[field][1]
    assert changed["override"][field] == TUNABLE_VALUES[field][1]


def test_consumption_matrix_covers_every_shipped_tunable():
    tool_fields = {
        ("studio.graphic.layout-compose", "template"), ("studio.graphic.layout-compose", "density"),
        ("studio.audio.tts", "voice"), ("studio.audio.tts", "rate"),
        ("studio.video.director-package", "instruction"), ("studio.video.director-package", "aspect_ratio"),
    }
    covered = set(CHAT_TUNABLE_CASES) | {
        (ref, field) for ref, resource in catalog.SKILLS.items() for field in resource["tunable_fields"]
        if (resource["key"], field) in tool_fields
    }
    declared = {(ref, field) for ref, resource in catalog.SKILLS.items() for field in resource["tunable_fields"]}
    assert covered == declared


@pytest.mark.parametrize("ratio", ["1:1", "4:3", "3:4", "16:9", "9:16"])
def test_director_instruction_and_aspect_are_consumed_without_dispatch(db_session, monkeypatch, ratio):
    from types import SimpleNamespace

    from app.models import CreativeExecution, CreativeExecutionPackage
    from app.services import (
        creative_configuration,
        creative_packages,
        stage_domain_integrations,
        stage_resolver,
        starter_personas,
    )
    from app.services.content_harness.nodes import bootstrap_builtin_nodes
    from app.services.content_harness.registry import registry

    bootstrap_builtin_nodes()
    # New video workflows no longer include this stage; older runs still do.
    node = {**starter_personas._node("prepare", "Tool", "stage.professional.prepare", "stage.professional.prepare.v2",
        {"objective": "准备交给外部专业执行器的视频导演包", "method": starter_personas._method("studio.video.director-package@1"),
         "package_schema": "director.video.v1", "prepare_execution": False, "constraints": [], "acceptance_criteria": [],
         "output_kind": "video", "output_mime": "video/mp4", "output_role": "final-render", "output_count": 1,
         "output_max_bytes": 31457280}, "专业执行准备"), "plugin_version": "2"}
    contract = registry.descriptor("node", node["plugin"], node["plugin_version"]).stage_contract
    saved_config = deepcopy(node["config"])
    override = {"instruction": "镜头停留便于读图", "aspect_ratio": ratio}
    user, unit = SimpleNamespace(id=1), SimpleNamespace(id=1, project_id=1, production_domain="persona")
    context = {"master": {"id": 1}, "identity": {"content": {
        "video_creative_profile": deepcopy(catalog.BLUEPRINTS["starter.ai-tech-engineer.v1"]["video_creative_profile"]),
    }}}
    source = SimpleNamespace(payload_schema="video.master.v2", payload_json={"aspect_ratio": [int(part) for part in ratio.split(":")]},
                             payload_hash="a" * 64, context_hash="b" * 64, origin_project_output_id=None)
    # Source loading is outside this narrow adapter test; the real request/gate remains under test.
    monkeypatch.setattr(creative_packages, "_source", lambda *_args, **_kwargs:
                        (source, {"assets": [], "evidence": []}, source))
    monkeypatch.setattr(creative_packages, "_check_evidence", lambda *_args: None)
    effective_node, method, creative, blockers = creative_configuration.frozen_stage(
        db_session, user, SimpleNamespace(id=1, project_id=1, modality="video"), node, contract, context, override)
    assert not blockers, blockers
    assert node["config"] == saved_config
    config = contract.effective_config(effective_node["config"], override)[1]
    resolved, model, blockers = stage_domain_integrations.prepare_domain(
        db_session, user, unit, effective_node, config, context, creative=creative)
    assert not blockers, blockers
    request = resolved["domain"]["request"]
    assert "镜头停留便于读图" in request["constraints"]
    assert catalog.load_skill("studio.video.director-package@1")["instruction"] in request["constraints"]
    instruction_v1 = catalog.load_skill("studio.video.director-package@1")["instruction"]
    node_v2 = deepcopy(node)
    node_v2["config"] = {**node["config"], "method": {**node["config"]["method"], "skill_ref": "studio.video.director-package@2"}}
    effective_v2, method_v2, creative_v2, blockers_v2 = creative_configuration.frozen_stage(
        db_session, user, SimpleNamespace(id=1, project_id=1, modality="video"), node_v2, contract, context, override)
    assert not blockers_v2, blockers_v2
    config_v2 = contract.effective_config(effective_v2["config"], override)[1]
    resolved_v2, _, blockers_v2 = stage_domain_integrations.prepare_domain(
        db_session, user, unit, effective_v2, config_v2, context, creative=creative_v2)
    assert not blockers_v2, blockers_v2
    instruction_v2 = catalog.load_skill("studio.video.director-package@2")["instruction"]
    constraints_v2 = resolved_v2["domain"]["request"]["constraints"]
    assert instruction_v2 in constraints_v2
    assert instruction_v1 not in constraints_v2
    assert instruction_v2 != instruction_v1
    assert method_v2["skill_ref"] == "studio.video.director-package@2"
    assert config_v2["method"]["skill_ref"] == "studio.video.director-package@2"
    switched = deepcopy(context)
    switched["identity"]["content"]["video_creative_profile"]["production_stages"] = {"finish": {
        "enabled": True, "methods": [{"id": "director-trial", "source_kind": "studio_builtin", "enabled": True,
            "skill_ref": "studio.video.director-package@2", "parameters": {}}]}}
    effective_switched, method_switched, creative_switched, blockers_switched = creative_configuration.frozen_stage(
        db_session, user, SimpleNamespace(id=1, project_id=1, modality="video"), node, contract, switched, override)
    assert not blockers_switched, blockers_switched
    config_switched = contract.effective_config(effective_switched["config"], override)[1]
    resolved_switched, _, blockers_switched = stage_domain_integrations.prepare_domain(
        db_session, user, unit, effective_switched, config_switched, switched, creative=creative_switched)
    assert not blockers_switched, blockers_switched
    switched_constraints = resolved_switched["domain"]["request"]["constraints"]
    assert instruction_v2 in switched_constraints and instruction_v1 not in switched_constraints
    assert method_switched["skill_ref"] == "studio.video.director-package@2"
    disabled = deepcopy(switched)
    disabled["identity"]["content"]["video_creative_profile"]["production_stages"]["finish"]["enabled"] = False
    effective_off, _, creative_off, blockers_off = creative_configuration.frozen_stage(
        db_session, user, SimpleNamespace(id=1, project_id=1, modality="video"), node, contract, disabled, override)
    assert not blockers_off, blockers_off
    config_off = contract.effective_config(effective_off["config"], override)[1]
    resolved_off, _, blockers_off = stage_domain_integrations.prepare_domain(
        db_session, user, unit, effective_off, config_off, disabled, creative=creative_off)
    assert not blockers_off, blockers_off
    assert instruction_v1 not in resolved_off["domain"]["request"]["constraints"]
    assert instruction_v2 not in resolved_off["domain"]["request"]["constraints"]
    assert request["source_master_revision_id"] == 1 and model is None
    preview = stage_resolver.resolve_stage(
        workflow={"id": 1, "version": 1, "checksum": "c" * 64}, node=effective_node,
        contract=contract, context=resolved, upstream={}, method=method, model=model,
        override=override, creative=creative)
    assert preview["ready"], preview["blockers"]
    assert preview["override"] == override
    assert preview["effective_config"]["instruction"] == "镜头停留便于读图"
    assert preview["effective_config"]["aspect_ratio"] == ratio
    source.payload_json = {"aspect_ratio": [7, 5]}
    _, _, blocked = stage_domain_integrations.prepare_domain(
        db_session, user, unit, effective_node, config, context, creative=creative)
    assert "stage_director_aspect_ratio_mismatch" in blocked
    assert db_session.query(CreativeExecution).count() == db_session.query(CreativeExecutionPackage).count() == 0


@pytest.mark.parametrize("ref", TEXT_SKILLS)
def test_shipped_text_method_package_has_real_instructions_and_exact_contract(ref):
    resource = catalog.load_skill(ref)
    assert resource["contract"]["ref"] == ref
    assert resource["contract"]["tunable_fields"] == catalog.SKILLS[ref]["tunable_fields"]
    assert len(resource["instruction"]) > 120
    assert resource["package_hash"] == catalog.digest({
        "instruction": resource["instruction"], "contract": resource["contract"], "provenance": resource["provenance"]})
    assert resource["provenance"]["classification"] == "self_developed"


@pytest.mark.parametrize("key", list(catalog.BLUEPRINTS))
def test_text_recipe_is_plan_then_write_then_checks(key):
    definition = starter_personas._definition("text", key)
    nodes = {node["id"]: node for node in definition["nodes"]}
    assert nodes["plan"]["config"]["output_schema"] == "article.plan.v1"
    assert nodes["write"]["plugin"] == "stage.master.propose"
    assert nodes["quality"]["plugin"] == "stage.checks"
    assert definition["edges"] == [{"from": "plan", "to": "write"}, {"from": "write", "to": "quality"}]
    assert definition["visual_order"] == ["plan", "write", "quality"]


@pytest.mark.parametrize("profile, phrase", [
    ("studio.quality.text.technical@1", "这项技术颠覆一切"),
    ("studio.quality.text.lifestyle@1", "不看后悔一辈子"),
])
def test_persona_quality_uses_frozen_rules_and_never_calls_a_model(profile, phrase):
    from app.services.text_documents import convert_legacy_text
    payload = convert_legacy_text({"title": "真实观察", "markdown": phrase})["payload"]
    report = catalog.text_quality(profile, payload)
    assert report["status"] == "blocker"
    assert report["quality_profile_ref"] == profile
    assert report["human_review_required"] is True
    assert report["coverage"]["semantic"] == "not_run"


def test_current_facts_need_fresh_as_of_but_explicit_reflection_is_distinct():
    from datetime import UTC, datetime, timedelta
    now = datetime.now(UTC)
    old = {"items": [{"item_id": 1, "checksum": "a" * 64, "snapshot": {"as_of": (now - timedelta(days=60)).isoformat()}}]}
    fresh = {"items": [{"item_id": 2, "checksum": "b" * 64, "kind": "fact", "fresh_source_verified": True,
        "snapshot": {"source_id": 1, "as_of": now.isoformat()}}]}
    assert catalog.freshness_projection(old, "current", now=now)["ready"] is False
    assert catalog.freshness_projection(fresh, "current", now=now)["ready"] is True
    assert catalog.freshness_projection(old, "reflection", now=now)["mode"] == "reflection"
    assert catalog.freshness_projection(old, "reflection", now=now)["ready"] is True


@pytest.mark.parametrize("kind, verified", [("author_opinion", True), ("legacy_untyped", True), ("fact", False)])
def test_recent_opinion_or_unproven_source_does_not_authorize_current_facts(kind, verified):
    from datetime import UTC, datetime
    now = datetime.now(UTC)
    boundary = {"items": [{"item_id": 1, "checksum": "a" * 64, "kind": kind, "fresh_source_verified": verified,
        "snapshot": {"source_id": 1, "as_of": now.isoformat()}}]}
    assert catalog.freshness_projection(boundary, "current", now=now)["ready"] is False


def test_technical_code_example_is_not_an_uncited_numeric_fact():
    from app.services.text_documents import convert_legacy_text
    payload = convert_legacy_text({"title": "配置示例", "markdown": "```python\ntimeout = '30秒'\n```"})["payload"]
    report = catalog.text_quality("studio.quality.text.technical@1", payload)
    assert not any(item["reason"] == "persona_numeric_claim_citation_missing" for item in report["issues"])


@pytest.mark.parametrize("markdown, selection, blocked", [
    ("这里是观察，性能提高99%", "这里是观察", True),
    ("这里是观察，性能提高99%", "性能提高99%", False),
    ("- 第一项观察\n- 性能提高99%", "第一项观察", True),
    ("- 第一项观察\n- 性能提高99%", "性能提高99%", False),
])
def test_numeric_claim_requires_exact_same_paragraph_or_list_item_range(markdown, selection, blocked):
    from app.services.text_documents import convert_legacy_text
    ref = {"fact_pack_item_id": 1, "snapshot_checksum": "a" * 64, "role": "claim", "locator": {"text": selection}}
    payload = convert_legacy_text({"title": "范围核验", "markdown": markdown}, evidence_refs=[ref])["payload"]
    assert payload["document"]["citations"]
    report = catalog.text_quality("studio.quality.text.technical@1", payload)
    assert any(item["reason"] == "persona_numeric_claim_citation_missing" for item in report["issues"]) is blocked


@pytest.mark.parametrize("key", list(catalog.BLUEPRINTS))
def test_starter_profiles_validate_without_a_fallback_chain(key):
    for field in ("text", "graphic", "audio", "video"):
        value = catalog.BLUEPRINTS[key][f"{field}_creative_profile"]
        assert CreativeProfile.model_validate(value).model_dump(by_alias=True)["model_chain"] == []


@pytest.mark.parametrize("changes", [
    {"model_binding": {"provider": "", "model": "m", "profile": "p"}, "mode": "custom"},
    {"parameters": {"instruction": "sk-abcdefghijklmnopqrstuvwxyz0123456789"}},
    {"parameters": {"file": "/Users/private/input.png"}},
    {"parameters": {"approval": True}},
    {"parameters": {"arbitrary_ui_field": 1}},
    {"mode": "auto", "model_chain": [{"provider": "a", "model": "m", "profile": "p"}]},
    {"mode": "custom", "model_binding": {"provider": "a", "model": "m", "profile": "p"},
     "model_chain": [{"provider": "b", "model": "n", "profile": "q"}]},
])
def test_creative_profile_rejects_unsafe_or_undeclared_config(changes):
    with pytest.raises(ValueError):
        catalog.validate_creative_profile(_profile(**changes))


def _identity(client):
    headers = {"X-Studio-User": "persona-contract@studio.test"}
    created = client.post("/api/v1/content-personas", headers=headers, json={"name": "技术角色"})
    assert created.status_code == 201, created.text
    return headers, created.json()["id"]


def test_creative_identity_whole_replacement_clear_cas_and_frozen_snapshot(client, db_session):
    headers, persona = _identity(client)
    body = {"expected_revision": 0, "profile": {"text_creative_profile": _profile()}}
    saved = client.post(f"/api/v1/content-personas/{persona}/revisions", headers=headers, json=body)
    assert saved.status_code == 201, saved.text
    account = client.post(f"/api/v1/content-personas/{persona}/accounts", headers=headers, json={"name": "账号"}).json()["id"]
    series = client.post(f"/api/v1/content-accounts/{account}/series", headers=headers, json={"name": "栏目"}).json()["id"]
    path = f"/api/v1/content-identities/effective?persona_id={persona}&account_id={account}&series_id={series}"
    assert client.get(path, headers=headers).json()["creative_profile_origins"]["text_creative_profile"] == "persona"
    replacement = _profile(style_preset_ref="studio.text.engineering-explainer@1", parameters={"length": "short"})
    assert client.post(f"/api/v1/content-accounts/{account}/revisions", headers=headers,
                       json={"expected_revision": 0, "profile": {"text_creative_profile": replacement}}).status_code == 201
    result = client.get(path, headers=headers).json()
    assert result["creative_profile_origins"]["text_creative_profile"] == "account"
    assert result["effective_profile"]["text_creative_profile"]["parameters"] == {"length": "short"}
    from app.services.content_identity import create_snapshot
    user = db_session.scalar(select(User).where(User.email == headers["X-Studio-User"]))
    snapshot = create_snapshot(db_session, user, persona_id=persona, account_id=account, series_id=series)
    db_session.commit()
    frozen_hash = snapshot.checksum
    assert client.post(f"/api/v1/content-series/{series}/revisions", headers=headers,
                       json={"expected_revision": 0, "profile": {"text_creative_profile": None}}).status_code == 201
    assert client.get(path, headers=headers).json()["effective_profile"]["text_creative_profile"] is None
    historical = client.get(f"/api/v1/identity-snapshots/{snapshot.id}", headers=headers).json()
    assert historical["checksum"] == frozen_hash
    assert historical["effective_profile"]["text_creative_profile"]["parameters"] == {"length": "short"}
    assert client.post(f"/api/v1/content-personas/{persona}/revisions", headers=headers, json=body).status_code == 409


@pytest.mark.parametrize("value", [_profile(), None])
def test_brand_creative_fields_are_rejected_even_when_null(client, value):
    headers, _ = _identity(client)
    brand = client.post("/api/v1/content-brands", headers=headers, json={"name": "共同品牌"}).json()["id"]
    response = client.post(f"/api/v1/content-brands/{brand}/revisions", headers=headers,
                           json={"expected_revision": 0, "profile": {"text_creative_profile": value}})
    assert response.status_code == 422, response.text


@pytest.mark.parametrize("key", list(catalog.BLUEPRINTS))
def test_starter_preview_no_write_and_apply_preserves_later_edits(client, db_session, key):
    from app.services.project_workflows import definition_checksum, validate_definition, validate_portable

    headers, _ = _identity(client)
    before = db_session.query(ContentPersona).count()
    preview = client.post("/api/v1/content-identities/starter-preview", headers=headers, json={"blueprint_key": key})
    assert preview.status_code == 200, preview.text
    assert db_session.query(ContentPersona).count() == before
    first = client.post("/api/v1/content-identities/starter-apply", headers=headers, json={"blueprint_key": key})
    assert first.status_code == 201, first.text
    persona = first.json()["persona_id"]
    assert db_session.query(PersonaWorkflowDefault).filter_by(persona_id=persona).count() == 3
    profile = db_session.get(ContentPersonaRevision, first.json()["revision_id"]).profile_json
    owner = db_session.scalar(select(User).where(User.email == headers["X-Studio-User"]))
    bindings = list(db_session.scalars(select(PersonaWorkflowDefault).where(
        PersonaWorkflowDefault.persona_id == persona)))
    assert {binding.modality for binding in bindings} == {"text", "graphic", "video"}
    workflow_ids = {}
    for binding in bindings:
        workflow = db_session.get(Workflow, binding.workflow_id)
        expected = validate_portable(validate_definition(starter_personas._definition(binding.modality, key)),
                                     source_project_id=None, source_unit_id=None)
        assert workflow.workflow_key == f"persona.{persona}.{binding.modality}"
        assert workflow.scope == "persona_default" and workflow.owner_user_id == owner.id
        assert workflow.version == binding.revision == 1
        assert workflow.schema_version == 2 and workflow.status == "published"
        assert workflow.definition_json == expected
        assert workflow.checksum == definition_checksum(expected)
        assert profile[f"{binding.modality}_creative_profile"]["provenance"]["default_recipe_key"] == (
            EXPECTED_RECIPE_KEYS[key][binding.modality])
        workflow_ids[binding.modality] = (binding.id, workflow.id)
    assert client.post(f"/api/v1/content-personas/{persona}/revisions", headers=headers,
                       json={"expected_revision": 1, "profile": {**profile, "positioning": "我的新定位"}}).status_code == 201
    replay = client.post("/api/v1/content-identities/starter-apply", headers=headers, json={"blueprint_key": key}).json()
    assert replay["created"] is False and replay["persona_id"] == persona
    assert replay["current_revision"] == 2
    assert db_session.query(ContentPersona).count() == before + 1
    assert {binding.modality: (binding.id, binding.workflow_id) for binding in db_session.scalars(
        select(PersonaWorkflowDefault).where(PersonaWorkflowDefault.persona_id == persona))} == workflow_ids


@pytest.mark.parametrize("key", list(catalog.BLUEPRINTS))
@pytest.mark.parametrize("modality", ["text", "graphic", "video"])
def test_default_workflow_pins_executable_stage_contracts(key, modality):
    from app.services.project_workflows import validate_definition, validate_portable
    value = validate_portable(validate_definition(starter_personas._definition(modality, key)),
                              source_project_id=None, source_unit_id=None)
    assert value["nodes"]
    for node in value["nodes"]:
        method = node["config"].get("method")
        if method:
            catalog.validate_ref(method["skill_ref"], kind="skill")


def test_studio_method_preview_and_run_never_creates_a_master(client, db_session):
    from test_creation_recipe_stages import _setup
    headers, _, _, base = _setup(client)
    definition = {"nodes": [{"id": "research", "kind": "AI", "plugin": "stage.creative.method", "plugin_version": "1",
        "stage_schema": "stage.creative.method.v1", "config": {"output_schema": "research.brief.v1",
            "instruction": "只整理输入证据，不编造来源", "candidate_count": 2,
            "method": {"source_kind": "studio_builtin", "skill_ref": "studio.research.evidence-brief@1"}}}],
        "edges": [], "visual_order": ["research"]}
    saved = client.post(f"{base}/workflow-override", headers=headers, json={"expected_revision": 0, "definition": definition})
    assert saved.status_code == 201, saved.text
    run = client.post(f"{base}/runs", headers=headers, json={"params": {}})
    assert run.status_code == 201, run.text
    preview = client.post(f"{base}/creation-recipe/stages/research/preview", headers=headers, json={"run_id": run.json()["id"]})
    assert preview.status_code == 200, preview.text
    assert preview.json()["ready"] is True, preview.text
    executed = client.post(f"{base}/creation-recipe/stages/research/run", headers=headers, json={
        "run_id": run.json()["id"], "expected_resolution_hash": preview.json()["resolution_hash"], "invocation_key": "research-1"})
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "waiting_input"
    assert executed.json()["output"]["schema"] == "research.brief.v1"
    assert len(executed.json()["output"]["candidates"]) == 2
    assert db_session.query(ContentMasterRevision).count() == 0
    result = client.get(f"{base}/creation-recipe/stages/research/result", headers=headers,
        params={"run_id": run.json()["id"], "attempt_id": executed.json()["attempt_id"]})
    assert result.status_code == 200, result.text
    value = result.json()
    candidate = value["output"]["candidates"][0]
    request = {"run_id": value["run_id"], "attempt_id": value["attempt_id"],
        "expected_output_hash": value["receipt"]["output_hash"],
        "expected_resolution_hash": value["receipt"]["resolution_hash"], "expected_context_hash": value["expected_context_hash"],
        "candidate_id": candidate["id"], "candidate_hash": candidate["candidate_hash"], "acceptance_key": "accept-research-1"}
    adopted = client.post(f"{base}/creation-recipe/stages/research/accept-creative", headers=headers, json=request)
    assert adopted.status_code == 200, adopted.text
    assert adopted.json()["accepted_target"]["output_kind"] == "creative_attempt"
    assert adopted.json()["accepted_target"]["accepted_hash"] == candidate["candidate_hash"]
    readback = client.get(f"{base}/creation-recipe/stages/research/result", headers=headers,
        params={"run_id": value["run_id"], "attempt_id": value["attempt_id"]})
    assert readback.status_code == 200, readback.text
    assert readback.json()["accepted_entity"]["entity"]["result"] == candidate["content"]
    replay = client.post(f"{base}/creation-recipe/stages/research/accept-creative", headers=headers, json=request)
    assert replay.status_code == 200 and replay.json()["replayed"] is True, replay.text
    assert db_session.query(ContentMasterRevision).count() == 0


def _creative_run(client, profile=None):
    headers, persona = _identity(client)
    saved = client.post(f"/api/v1/content-personas/{persona}/revisions", headers=headers,
        json={"expected_revision": 0, "profile": {"text_creative_profile": profile or _profile(
            parameters={"length": "long"}, stage_instruction="优先解释真实工程代价")}})
    assert saved.status_code == 201, saved.text
    project = client.post("/api/v1/content-projects", headers=headers, json={"title": "角色化创作"}).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project}/units", headers=headers,
        json={"title": "技术文章", "modality": "text", "persona_id": persona}).json()["id"]
    base = f"/api/v1/content-projects/{project}/units/{unit}"
    definition = {"nodes": [{"id": "draft", "kind": "AI", "plugin": "stage.master.propose", "plugin_version": "1",
        "stage_schema": "stage.master.propose.v1", "config": {"instruction": "生成有边界的文章", "length": "medium"}}],
        "edges": [], "visual_order": ["draft"]}
    response = client.post(f"{base}/workflow-override", headers=headers, json={"expected_revision": 0, "definition": definition})
    assert response.status_code == 201, response.text
    run = client.post(f"{base}/runs", headers=headers, json={"params": {}})
    assert run.status_code == 201, run.text
    return headers, persona, base, run.json()["id"]


def test_real_stage_reads_frozen_creative_profile_and_receipt(client, db_session):
    from app.models import WorkflowStepAttempt

    headers, persona, base, run_id = _creative_run(client)
    request = {"run_id": run_id, "stage_override": {"length": "short"}}
    response = client.post(f"{base}/creation-recipe/stages/draft/preview", headers=headers, json=request)
    assert response.status_code == 200, response.text
    preview = response.json()
    assert preview["ready"] is True, preview
    assert preview["base_config"]["length"] == "medium"
    assert preview["effective_config"]["length"] == "short"
    creative = preview["creative_configuration"]
    assert creative["style_preset"]["ref"] == "studio.text.deep-technical@1"
    assert creative["method_stack"][0]["skill_ref"] == "studio.text.longform@1"
    assert "优先解释真实工程代价" in preview["effective_prompt"]
    assert creative["selected_binding"]["model"] == "mock-structured-v1"
    changed = client.post(f"/api/v1/content-personas/{persona}/revisions", headers=headers, json={
        "expected_revision": 1, "profile": {"text_creative_profile": _profile(stage_instruction="这是新的配置")}})
    assert changed.status_code == 201, changed.text
    again = client.post(f"{base}/creation-recipe/stages/draft/preview", headers=headers, json=request).json()
    assert again["resolution_hash"] == preview["resolution_hash"]
    executed = client.post(f"{base}/creation-recipe/stages/draft/run", headers=headers, json={**request,
        "expected_resolution_hash": preview["resolution_hash"], "invocation_key": "persona-draft-1"})
    assert executed.status_code == 200, executed.text
    attempt = db_session.get(WorkflowStepAttempt, executed.json()["attempt_id"])
    assert attempt.input_snapshot_json["resolved_stage"]["creative_configuration"] == creative
    assert db_session.query(ContentMasterRevision).count() == 0


def test_current_fact_stage_blocks_without_fresh_sources_and_requires_explicit_mode(client, db_session):
    from app.models import LLMRun
    headers, _, base, run = _creative_run(client)
    request = {"run_id": run, "stage_override": {"fact_mode": "current"}}
    before = db_session.query(LLMRun).count()
    preview = client.post(f"{base}/creation-recipe/stages/draft/preview", headers=headers, json=request)
    assert preview.status_code == 200, preview.text
    assert preview.json()["ready"] is False
    assert "fresh_current_evidence_required" in preview.json()["blockers"]
    assert db_session.query(LLMRun).count() == before
    request["stage_override"]["fact_mode"] = "reflection"
    reflected = client.post(f"{base}/creation-recipe/stages/draft/preview", headers=headers, json=request)
    assert reflected.status_code == 200, reflected.text
    assert reflected.json()["ready"] is True
    assert reflected.json()["creative_configuration"]["freshness"]["mode"] == "reflection"
    assert reflected.json()["resolution_hash"] != preview.json()["resolution_hash"]


def test_persona_master_freezes_creative_provenance_and_reuses_persistent_identity_checks(client, db_session):
    headers, _, base, run = _creative_run(client)
    preview = client.post(f"{base}/creation-recipe/stages/draft/preview", headers=headers, json={"run_id": run}).json()
    executed = client.post(f"{base}/creation-recipe/stages/draft/run", headers=headers, json={
        "run_id": run, "expected_resolution_hash": preview["resolution_hash"], "invocation_key": "quality-draft"})
    assert executed.status_code == 200, executed.text
    result = executed.json()
    candidate = result["output"]["candidates"][0]
    request = {"run_id": run, "attempt_id": result["attempt_id"],
        "expected_output_hash": result["receipt"]["output_hash"], "expected_resolution_hash": preview["resolution_hash"],
        "expected_context_hash": preview["context_hash"], "candidate_id": candidate["candidate_id"],
        "candidate_hash": candidate["candidate_hash"], "expected_revision": 0, "adoption_key": "persona-quality",
        "payload": candidate["payload"], "asset_refs": candidate["asset_refs"], "evidence_refs": candidate["evidence_refs"],
        "decision": "accepted"}
    saved = client.post(f"{base}/creation-recipe/stages/draft/accept-master", headers=headers, json=request)
    assert saved.status_code == 200, saved.text
    master = saved.json()["master"]
    provenance = master["edit_summary"]["stage_provenance"]
    assert provenance["creative_configuration"] == preview["creative_configuration"]
    assert provenance["creative_configuration"]["method_stack"][0]["package_hash"]
    checks = client.post(f"{base}/master-revisions/{master['id']}/checks", headers=headers, json={})
    assert checks.status_code == 200, checks.text
    identity = next(item for item in checks.json()["items"] if item["check_kind"] == "text_identity")
    quality = identity["report"]["persona_quality"]
    assert quality["quality_profile_ref"] == "studio.quality.text.technical@1"
    assert quality["quality_profile_hash"] == catalog.digest(catalog.QUALITY[quality["quality_profile_ref"]])
    assert quality["coverage"]["semantic"] == "not_run"


@pytest.mark.parametrize("key", list(catalog.BLUEPRINTS))
def test_two_personas_complete_text_recipe_then_exact_candidate_review_and_zip(client, db_session, key):
    import io
    import json
    import zipfile
    from datetime import UTC, datetime

    from app.models import Fact, FactPack, FactPackItem, SourceDocument, WorkflowStepAttempt
    from app.services.factpack_service import evidence_snapshot, pack_snapshot_checksum, snapshot_checksum

    headers = {"X-Studio-User": f"{key}@studio.test"}
    initialized = client.post("/api/v1/content-identities/starter-apply", headers=headers, json={"blueprint_key": key})
    assert initialized.status_code == 201, initialized.text
    persona = initialized.json()["persona_id"]
    project = client.post("/api/v1/content-projects", headers=headers, json={"title": key}).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project}/units", headers=headers,
        json={"title": "文字闭环", "modality": "text", "persona_id": persona, "channel_id": "wechat"})
    assert unit.status_code == 201, unit.text
    base = f"/api/v1/content-projects/{project}/units/{unit.json()['id']}"
    assert client.post(f"/api/v1/content-projects/{project}/brief/revisions", headers=headers,
        json={"expected_revision": 0, "objective": "测试角色化文字创作，不代表真实质量"}).status_code == 201
    pack = FactPack(name="隔离证据", version=1, status="frozen")
    db_session.add(pack); db_session.flush()
    statement = "隔离验收限定 3 个初稿、2 个精修、1 个最终稿；仅为测试输入，不是现实事实。"
    source = SourceDocument(title="隔离测试任务书", source_type="text", raw_text=statement,
        as_of=datetime.now(UTC).date().isoformat(), parse_status="parsed")
    db_session.add(source); db_session.flush()
    fact = Fact(source_document_id=source.id, statement=statement, as_of=source.as_of, status="approved")
    db_session.add(fact); db_session.flush()
    item = FactPackItem(fact_pack_id=pack.id, fact=fact, evidence_kind="fact",
        public_use_allowed=True, model_use_allowed=True)
    snapshot = evidence_snapshot(item)
    item.snapshot_json, item.snapshot_checksum = snapshot, snapshot_checksum(snapshot)
    db_session.add(item); db_session.flush(); pack.checksum = pack_snapshot_checksum([item]); db_session.commit()
    assert client.post(f"/api/v1/content-projects/{project}/fact-boundary", headers=headers,
        json={"fact_pack_id": pack.id, "expected_revision": 0}).status_code == 201
    run_response = client.post(f"{base}/runs", headers=headers, json={"params": {}})
    assert run_response.status_code == 201, run_response.text
    run = run_response.json()["id"]
    master = None
    for node_id in ("plan", "write", "quality"):
        preview = client.post(f"{base}/creation-recipe/stages/{node_id}/preview", headers=headers, json={"run_id": run})
        assert preview.status_code == 200 and preview.json()["ready"], (node_id, preview.text)
        resolved = preview.json()
        executed = client.post(f"{base}/creation-recipe/stages/{node_id}/run", headers=headers, json={
            "run_id": run, "expected_resolution_hash": resolved["resolution_hash"], "invocation_key": f"e2e-{node_id}"})
        assert executed.status_code == 200, (node_id, executed.text)
        result = executed.json()
        request = {"run_id": run, "attempt_id": result["attempt_id"], "expected_output_hash": result["receipt"]["output_hash"],
            "expected_resolution_hash": result["receipt"]["resolution_hash"], "expected_context_hash": resolved["context_hash"]}
        output = result["output"]
        if node_id == "quality":
            assert result["status"] == "waiting_input", [(c["check_kind"], c["status"], c["report"].get("reasons")) for c in output["result"]["checks"]]
            warnings = {f"{c['id']}:{c['input_hash']}": "隔离测试确认提醒，不声称语义审核已完成"
                for c in output["result"]["checks"] if c["status"] == "warning"}
            if warnings:
                missing = client.post(f"{base}/creation-recipe/stages/{node_id}/accept-result", headers=headers,
                    json={**request, "domain": "checks", "expected_revision": 0,
                        "adoption_key": f"missing-{node_id}", "decision": "accepted"})
                assert missing.status_code == 409, missing.text
                assert missing.json()["detail"]["code"] == "stage_check_warning_disposition_required"
            accepted = client.post(f"{base}/creation-recipe/stages/{node_id}/accept-result", headers=headers,
                json={**request, "domain": "checks", "expected_revision": 0, "adoption_key": f"accept-{node_id}",
                    "warning_dispositions": warnings, "decision": "accepted"})
        elif node_id == "write":
            choice = output["candidates"][-1]
            accepted = client.post(f"{base}/creation-recipe/stages/{node_id}/accept-master", headers=headers,
                json={**request, "candidate_id": choice["candidate_id"], "candidate_hash": choice["candidate_hash"],
                    "expected_revision": master["revision_no"] if master else 0, "adoption_key": f"accept-{node_id}",
                    "payload": choice["payload"], "asset_refs": choice["asset_refs"], "evidence_refs": choice["evidence_refs"], "decision": "accepted"})
            assert accepted.status_code == 200, (node_id, accepted.text)
            master = accepted.json()["master"]
        else:
            choice = output["candidates"][0]
            count = db_session.query(ContentMasterRevision).count()
            accepted = client.post(f"{base}/creation-recipe/stages/{node_id}/accept-creative", headers=headers,
                json={**request, "candidate_id": choice["id"], "candidate_hash": choice["candidate_hash"], "acceptance_key": f"accept-{node_id}"})
            assert db_session.query(ContentMasterRevision).count() == count
        assert accepted.status_code == 200, (node_id, accepted.text)
    assert master["revision_no"] == 1
    frozen = client.post(f"{base}/candidates/freeze", headers=headers,
        json={"content_master_revision_id": master["id"], "expected_payload_hash": master["payload_hash"]})
    assert frozen.status_code == 201, frozen.text
    candidate = frozen.json()
    checks = candidate["manifest"]["checks"]
    review = client.post(f"{base}/candidates/{candidate['id']}/approve", headers=headers,
        json={"candidate_hash": candidate["candidate_hash"], "warning_dispositions": {
            f"{c['id']}:{c['input_hash']}": "人工确认隔离检查提醒" for c in checks if c["status"] == "warning"}})
    assert review.status_code == 200, review.text
    target = client.post(f"{base}/candidates/{candidate['id']}/delivery-authorizations", headers=headers,
        json={"channel": "wechat", "content_form": "article", "account_ref": "manual", "authorization_version": "text-e2e", "action": "copy_package"})
    assert target.status_code == 201, target.text
    package = client.get(f"/api/v1/delivery-targets/{target.json()['id']}/package.zip", headers=headers)
    assert package.status_code == 200, package.text
    with zipfile.ZipFile(io.BytesIO(package.content)) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["content_master"]["id"] == master["id"]
        assert archive.read("content.md").decode()
    attempt = db_session.get(WorkflowStepAttempt, master["edit_summary"]["stage_provenance"]["attempt_id"])
    assert attempt.input_snapshot_json["resolved_stage"]["creative_configuration"]["quality_profile"]["ref"] == catalog.BLUEPRINTS[key]["text_creative_profile"]["quality_profile_ref"]


def test_unsaved_profile_preview_does_not_save_persona(client, db_session):
    headers, persona = _identity(client)
    profile = _profile(stage_instruction="这次先试试")
    response = client.post("/api/v1/content-identities/creative-preview", headers=headers, json={
        "persona_id": persona, "modality": "text", "profile_override": profile})
    assert response.status_code == 200, response.text
    assert response.json()["profile"] == profile
    assert response.json()["layers"][0]["scope"] == "unsaved_preview"
    assert db_session.query(ContentPersonaRevision).count() == 0


def test_removed_blueprint_provenance_does_not_create_duplicate(client, db_session):
    headers, _ = _identity(client)
    key = "starter.ai-tech-engineer.v1"
    applied = client.post("/api/v1/content-identities/starter-apply", headers=headers, json={"blueprint_key": key}).json()
    persona = applied["persona_id"]
    changed = client.post(f"/api/v1/content-personas/{persona}/revisions", headers=headers,
        json={"expected_revision": 1, "profile": {"positioning": "已改成自己的配置"}})
    assert changed.status_code == 201, changed.text
    client.patch(f"/api/v1/content-personas/{persona}", headers=headers, json={"name": "我的技术角色"})
    before = db_session.query(ContentPersona).count()
    replay = client.post("/api/v1/content-identities/starter-apply", headers=headers, json={"blueprint_key": key})
    assert replay.status_code == 201, replay.text
    assert replay.json()["created"] is False
    assert replay.json()["persona_id"] == persona
    assert db_session.query(ContentPersona).count() == before


def _research_run(client):
    from test_creation_recipe_stages import _setup
    headers, _, _, base = _setup(client)
    nodes = [{"id": node_id, "kind": "AI", "plugin": "stage.creative.method", "plugin_version": "1",
        "stage_schema": "stage.creative.method.v1", "config": {"output_schema": schema,
            "instruction": "只使用已接受输入，保留未知", "candidate_count": 2,
            "method": {"source_kind": "studio_builtin", "skill_ref": skill}}}
        for node_id, schema, skill in [("research", "research.brief.v1", "studio.research.evidence-brief@1"),
                                      ("angles", "creative.angles.v1", "studio.research.angle-lab@1")]]
    response = client.post(f"{base}/workflow-override", headers=headers, json={"expected_revision": 0,
        "definition": {"nodes": nodes, "edges": [{"from": "research", "to": "angles"}], "visual_order": ["research", "angles"]}})
    assert response.status_code == 201, response.text
    run = client.post(f"{base}/runs", headers=headers, json={"params": {}}).json()["id"]
    preview = client.post(f"{base}/creation-recipe/stages/research/preview", headers=headers, json={"run_id": run}).json()
    executed = client.post(f"{base}/creation-recipe/stages/research/run", headers=headers, json={
        "run_id": run, "expected_resolution_hash": preview["resolution_hash"], "invocation_key": "research-test"})
    assert executed.status_code == 200, executed.text
    value = executed.json()
    candidate = value["output"]["candidates"][1]
    request = {"run_id": run, "attempt_id": value["attempt_id"], "expected_output_hash": value["receipt"]["output_hash"],
        "expected_resolution_hash": value["receipt"]["resolution_hash"], "expected_context_hash": preview["context_hash"],
        "candidate_id": candidate["id"], "candidate_hash": candidate["candidate_hash"], "acceptance_key": "research-choice"}
    return headers, base, run, request


def test_intermediate_acceptance_releases_only_the_selected_upstream(client, db_session):
    from app.models import ProjectWorkflowOutput
    headers, base, run, request = _research_run(client)
    before = client.post(f"{base}/creation-recipe/stages/angles/preview", headers=headers, json={"run_id": run}).json()
    assert "upstream_acceptance_required" in before["blockers"]
    adopted = client.post(f"{base}/creation-recipe/stages/research/accept-creative", headers=headers, json=request)
    assert adopted.status_code == 200, adopted.text
    after = client.post(f"{base}/creation-recipe/stages/angles/preview", headers=headers, json={"run_id": run})
    assert after.status_code == 200, after.text
    assert after.json()["ready"] is True
    handoff = after.json()["upstream"]["research"]
    assert handoff["candidate_id"] == "method-02"
    assert handoff["accepted_hash"] == request["candidate_hash"]
    assert handoff["selected_content"]["question"].endswith("候选 2")
    assert "candidates" not in handoff and "raw_output" not in handoff
    assert db_session.query(ProjectWorkflowOutput).count() == 0
    assert db_session.query(ContentMasterRevision).count() == 0


@pytest.mark.parametrize("change", ["candidate_hash", "context", "foreign", "tamper"])
def test_intermediate_acceptance_rejects_foreign_or_changed_input(client, db_session, change):
    from app.models import ProjectEvent, WorkflowStepAttempt
    headers, base, _run, request = _research_run(client)
    if change == "candidate_hash":
        request["candidate_hash"] = "a" * 64
    elif change == "context":
        request["expected_context_hash"] = "b" * 64
    elif change == "foreign":
        headers = {"X-Studio-User": "foreign@studio.test"}
    else:
        attempt = db_session.get(WorkflowStepAttempt, request["attempt_id"])
        attempt.output_json = {**attempt.output_json, "schema": "foreign.output.v1"}
        db_session.commit()
    count = db_session.query(ProjectEvent).count()
    result = client.post(f"{base}/creation-recipe/stages/research/accept-creative", headers=headers, json=request)
    assert result.status_code in {404, 409}, result.text
    assert db_session.query(ProjectEvent).count() == count
    assert db_session.query(ContentMasterRevision).count() == 0
