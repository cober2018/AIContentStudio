"""Version-pinned Stage controls and pure preview, using only isolated fixtures."""

from copy import deepcopy

import pytest
from fastapi import HTTPException


def _contract():
    return {
        "stage_schema": "test.text.stage.v1", "title": "初稿", "category": "AI",
        "config_schema": {"type": "object", "additionalProperties": False, "properties": {
            "instruction": {"type": "string", "minLength": 1, "maxLength": 2000},
            "candidate_count": {"type": "integer", "minimum": 1, "maximum": 5, "default": 1},
            "model_profile_id": {"type": "string", "minLength": 1, "maxLength": 100},
        }, "required": ["instruction"]},
        "ui_schema": {"instruction": {"control": "textarea", "label": "阶段要求"},
                      "candidate_count": {"control": "number", "label": "候选数量"}},
        "tunable_fields": ["instruction", "candidate_count", "model_profile_id"],
        "input_contract": {"required_context": [], "upstream": "accepted"},
        "output_contract": {"schema": "stage.master.proposal.v1", "max_candidates": 5},
        "method_sources": ["builtin", "capability_memory"],
        "supports_preview": True, "supports_run_override": True,
        "supports_candidates": True, "requires_human_acceptance": True,
    }


class _StageExecutor:
    stage_consumed_fields = frozenset({"instruction", "candidate_count", "model_profile_id"})

    def execute(self, db, ctx, config, user):
        raise AssertionError("Preview must never dispatch")


def _register(registry):
    registry.register("node", "test.stage", "2", _StageExecutor(), stage_contract=_contract())
    return registry.descriptor("node", "test.stage", "2").stage_contract


def test_stage_descriptor_is_exact_version_and_immutable():
    from app.services.content_harness.registry import PluginRegistry

    registry = PluginRegistry()
    registry.register("node", "test.stage", "1", object())
    contract = _register(registry)
    assert registry.descriptor("node", "test.stage", "1").stage_contract is None
    assert contract.to_dict()["stage_schema"] == "test.text.stage.v1"
    mutated = contract.to_dict()
    mutated["tunable_fields"].append("approval")
    assert "approval" not in contract.to_dict()["tunable_fields"]


@pytest.mark.parametrize("field", ["prompt_that_is_ignored", "approval", "plugin", "depends_on"])
def test_registry_rejects_cosmetic_or_prohibited_tuning(field):
    from app.services.content_harness.registry import PluginRegistry, RegistryError

    value = _contract()
    value["config_schema"]["properties"][field] = {"type": "string", "maxLength": 100}
    value["tunable_fields"].append(field)
    with pytest.raises(RegistryError):
        PluginRegistry().register("node", "bad", "1", _StageExecutor(), stage_contract=value)


@pytest.mark.parametrize("config", [
    {"instruction": "写文章", "unknown": True}, {"instruction": "写文章", "candidate_count": True},
    {"instruction": "写文章", "candidate_count": 6}, {"instruction": "写文章", "candidate_count": 1.5},
    {"instruction": ""}, {"instruction": "x" * 2001},
    {"instruction": "api_key=not-allowed-secret"},
])
def test_stage_config_is_bounded_and_secret_safe(config):
    from app.services.content_harness.registry import PluginRegistry
    from app.services.stage_contracts import StageContractError

    contract = _register(PluginRegistry())
    with pytest.raises(StageContractError):
        contract.validate_config(config)


def _resolved(**changes):
    from app.services.content_harness.registry import PluginRegistry
    from app.services.stage_resolver import resolve_stage

    contract = _register(PluginRegistry())
    inputs = {
        "workflow": {"id": 8, "version": 2, "checksum": "a" * 64},
        "node": {"id": "draft", "kind": "AI", "plugin": "test.stage", "plugin_version": "2",
                 "stage_schema": "test.text.stage.v1", "config": {"instruction": "生成技术文章"}},
        "contract": contract,
        "context": {"identity": {"id": 1, "checksum": "b" * 64, "content": {"voice": "直接"}},
                    "brief": {"id": 2, "checksum": "c" * 64, "content": {"objective": "架构价值"}}},
        "upstream": {}, "method": {"source_kind": "builtin", "instruction": "只使用已证实事实"},
        "model": {"profile_id": "default", "provider": "mock", "model": "mock-structured-v1",
                  "adapter_key": "llm.mock", "adapter_version": "1", "runtime_hash": "d" * 64},
        "override": {},
    }
    inputs.update(changes)
    return resolve_stage(**inputs)


def test_preview_has_deterministic_layered_prompt_and_explicit_override():
    first = _resolved()
    assert first == _resolved()
    assert first["ready"] is True
    assert first["effective_config"]["candidate_count"] == 1
    second = _resolved(override={"instruction": "减少科普，强调架构价值", "candidate_count": 3})
    assert first["resolution_hash"] != second["resolution_hash"]
    assert first["prompt_hash"] != second["prompt_hash"]
    assert second["base_config"]["instruction"] == "生成技术文章"
    assert second["effective_config"]["candidate_count"] == 3
    assert [section["key"] for section in second["prompt_sections"]] == [
        "method", "identity", "stage_instruction", "execution_controls", "brief", "intent", "evidence", "upstream", "task_override",
    ]


def test_preview_hash_changes_on_same_label_different_runtime_or_context():
    first = _resolved()
    model = deepcopy(first["model"])
    model["runtime_hash"] = "e" * 64
    assert first["resolution_hash"] != _resolved(model=model)["resolution_hash"]
    context = deepcopy(first["context"])
    context["brief"]["checksum"] = "f" * 64
    assert first["resolution_hash"] != _resolved(context=context)["resolution_hash"]


@pytest.mark.parametrize("override", [{"plugin": "new"}, {"candidate_count": 9}, {"approval": True}])
def test_unsafe_override_rejected(override):
    from app.services.stage_contracts import StageContractError

    with pytest.raises(StageContractError):
        _resolved(override=override)


def test_expected_preview_identity_is_required_and_blockers_fail_closed():
    from app.services.stage_resolver import require_expected_resolution

    value = _resolved()
    with pytest.raises(HTTPException) as missing:
        require_expected_resolution(value, None)
    assert missing.value.status_code == 422
    with pytest.raises(HTTPException) as drift:
        require_expected_resolution(value, "f" * 64)
    assert drift.value.status_code == 409
    require_expected_resolution(value, value["resolution_hash"])
    blocked = _resolved(blockers=["upstream_acceptance_required"])
    with pytest.raises(HTTPException):
        require_expected_resolution(blocked, blocked["resolution_hash"])


def _setup(client):
    headers = {"X-Studio-User": "recipe@studio.test"}
    persona = client.post("/api/v1/content-personas", json={"name": "作者"}, headers=headers).json()["id"]
    project = client.post("/api/v1/content-projects", json={"title": "写作"}, headers=headers).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project}/units", headers=headers,
                       json={"title": "文章", "persona_id": persona, "modality": "text"}).json()["id"]
    return headers, project, unit, f"/api/v1/content-projects/{project}/units/{unit}"


def test_recipe_projects_legacy_without_reinterpreting_or_writing(client, db_session):
    from sqlalchemy import func, select

    from app.models import ProjectEvent, Workflow

    headers, _, _, base = _setup(client)
    definition = {"nodes": [{"id": "old", "kind": "System", "plugin": "system.constant",
                            "config": {"value": "original"}}], "edges": [], "visual_order": ["old"]}
    assert client.post(f"{base}/workflow-override", headers=headers,
                       json={"expected_revision": 0, "definition": definition}).status_code == 201
    count = db_session.scalar(select(func.count(ProjectEvent.id)))
    result = client.get(f"{base}/creation-recipe", headers=headers)
    assert result.status_code == 200, result.text
    data = result.json()
    assert data["source"] == "project_override"
    assert data["stages"][0]["mode"] == "advanced_legacy"
    assert data["stages"][0]["controls"] is None
    assert data["workflow_id"] == db_session.scalar(select(Workflow.id))
    assert db_session.scalar(select(func.count(ProjectEvent.id))) == count
    other = {"X-Studio-User": "other@studio.test"}
    assert client.post("/api/v1/content-personas", headers=other, json={"name": "其他用户"}).status_code == 201
    assert client.get(f"{base}/creation-recipe", headers=other).status_code == 404
    assert client.post(f"{base}/creation-recipe/stages/old/preview", headers=headers, json={}).status_code == 409


def test_new_stage_definition_requires_exact_contract_pin(client, monkeypatch):
    from app.services.content_harness.registry import registry

    monkeypatch.setattr(registry, "_items", dict(registry._items))
    monkeypatch.setattr(registry, "_descriptors", dict(registry._descriptors))
    _register(registry)
    headers, _, _, base = _setup(client)
    node = {"id": "draft", "kind": "AI", "plugin": "test.stage", "plugin_version": "2",
            "config": {"instruction": "写文章"}}
    body = {"expected_revision": 0, "definition": {"nodes": [node], "edges": [], "visual_order": ["draft"]}}
    path = f"{base}/workflow-override"
    assert client.post(path, headers=headers, json=body).status_code == 422
    node["stage_schema"] = "test.text.stage.v1"
    result = client.post(path, headers=headers, json=body)
    assert result.status_code == 201, result.text
    assert client.get(f"{base}/creation-recipe", headers=headers).json()["stages"][0]["mode"] == "stage"
    preview = client.post(f"{base}/creation-recipe/stages/draft/preview", headers=headers,
                          json={"stage_override": {"candidate_count": 3}})
    assert preview.status_code == 200, preview.text
    assert preview.json()["effective_config"]["candidate_count"] == 3
    assert preview.json()["model"]["provider"] == "mock"
    assert "api_key" not in preview.text
    started = client.post(f"{base}/runs", headers=headers, json={"params": {}})
    assert started.status_code == 201, started.text
    assert started.json()["status"] == "running"
    assert client.get(f"{base}/runs", headers=headers).json()[0]["id"] == started.json()["id"]


@pytest.mark.parametrize("mutation", [
    {"category": []}, {"input_contract": {"upstream": []}}, {"supports_preview": "true"},
    {"tunable_fields": ["not_supported"]}, {"ui_schema": {"extra": {"control": "text", "label": "extra"}}},
])
def test_invalid_contract_metadata_is_typed_failure(mutation):
    from app.services.content_harness.registry import PluginRegistry, RegistryError

    value = {**_contract(), **mutation}
    with pytest.raises(RegistryError):
        PluginRegistry().register("node", "bad", "1", _StageExecutor(), stage_contract=value)


def test_model_route_identity_hides_credentials_and_detects_rotation(monkeypatch):
    from app import runtime_config
    from app.services.creation_recipes import _model

    monkeypatch.setattr(runtime_config, "_OVERRIDES", {})
    config = {"provider": "openai_compatible", "base_url": "https://model.invalid/v1",
              "api_key": "sk-first-private-value", "model": "registered-model"}
    runtime_config.set_runtime(runtime_config.KEY_LLM, config)
    first, blockers = _model({})
    assert not blockers
    assert "sk-first" not in str(first) and "model.invalid" not in str(first)
    runtime_config.set_runtime(runtime_config.KEY_LLM, {**config, "api_key": "sk-next-private-value"})
    second, _ = _model({})
    assert first["model"] == second["model"]
    assert first["runtime_hash"] != second["runtime_hash"]
    missing, blockers = _model({"model_profile_id": "not_registered"})
    assert missing is None and blockers == ["model_profile_unavailable"]


@pytest.fixture
def saved_stage(client, monkeypatch):
    from app.services.content_harness.registry import registry

    monkeypatch.setattr(registry, "_items", dict(registry._items))
    monkeypatch.setattr(registry, "_descriptors", dict(registry._descriptors))
    _register(registry)
    headers, project, unit, base = _setup(client)
    node = {"id": "draft", "kind": "AI", "plugin": "test.stage", "plugin_version": "2",
            "stage_schema": "test.text.stage.v1", "config": {"instruction": "写文章"}}
    body = {"expected_revision": 0, "definition": {"nodes": [node], "edges": [], "visual_order": ["draft"]}}
    assert client.post(f"{base}/workflow-override", headers=headers, json=body).status_code == 201
    return headers, project, unit, base


def test_preview_never_calls_model_or_persists_any_result(client, db_session, saved_stage, monkeypatch):
    from sqlalchemy import func, select

    from app.models import ContentMasterRevision, LLMRun, ProjectEvent, WorkflowRun
    from app.services.generation import providers

    headers, _, _, base = saved_stage
    before = {model: db_session.scalar(select(func.count(model.id)))
              for model in (ContentMasterRevision, LLMRun, ProjectEvent, WorkflowRun)}
    def forbid(*args, **kwargs):
        raise AssertionError("Preview tried to instantiate a model executor")
    monkeypatch.setattr(providers, "get_provider", forbid)
    result = client.post(f"{base}/creation-recipe/stages/draft/preview", headers=headers, json={})
    assert result.status_code == 200, result.text
    assert before == {model: db_session.scalar(select(func.count(model.id))) for model in before}
    assert client.post(f"{base}/creation-recipe/stages/draft/preview", headers=headers,
                       json={"stage_override": {"approval": True}}).status_code == 422


def test_recipe_history_and_inherited_pin_do_not_rebind(client, db_session, saved_stage):
    from app.models import PersonaWorkflowDefault, Workflow

    headers, _, unit_id, base = saved_stage
    first = client.get(f"{base}/creation-recipe", headers=headers).json()
    definition = db_session.get(Workflow, first["workflow_id"]).definition_json
    changed = deepcopy(definition)
    changed["nodes"][0]["config"]["instruction"] = "重点谈架构"
    assert client.post(f"{base}/workflow-override", headers=headers,
                       json={"expected_revision": 1, "definition": changed}).status_code == 201
    after = client.get(f"{base}/creation-recipe", headers=headers).json()
    assert [row["version"] for row in after["history"]] == [2, 1]
    assert after["history"][1]["diff"]["changed_node_ids"] == ["draft"]
    assert db_session.get(Workflow, first["workflow_id"]).definition_json == definition
    from app.models import ContentUnit

    unit = db_session.get(ContentUnit, unit_id)
    db_session.add(PersonaWorkflowDefault(persona_id=unit.persona_id, modality="text",
                                         workflow_id=first["workflow_id"], revision=4))
    db_session.commit()
    projection = client.get(f"{base}/creation-recipe", headers=headers).json()
    assert projection["workflow_id"] == after["workflow_id"]
    assert projection["inherited_default"]["revision"] == 4
    assert projection["inherited_default"]["diff"]["changed_node_ids"] == ["draft"]


def test_foreign_run_is_not_usable_as_preview_context(client, db_session, saved_stage):
    from app.models import WorkflowRun

    headers, _, _, base = saved_stage
    workflow_id = client.get(f"{base}/creation-recipe", headers=headers).json()["workflow_id"]
    run = WorkflowRun(workflow_id=workflow_id, content_unit_id=9999)
    db_session.add(run)
    db_session.commit()
    assert client.post(f"{base}/creation-recipe/stages/draft/preview", headers=headers,
                       json={"run_id": run.id}).status_code == 404


def test_archived_preview_is_readable_but_not_executable(client, db_session, saved_stage):
    from app.models import ContentUnit

    headers, _, unit_id, base = saved_stage
    db_session.get(ContentUnit, unit_id).status = "archived"
    db_session.commit()
    assert client.get(f"{base}/creation-recipe", headers=headers).json()["readonly"] is True
    preview = client.post(f"{base}/creation-recipe/stages/draft/preview", headers=headers, json={}).json()
    assert preview["ready"] is False and "archived_readonly" in preview["blockers"]


@pytest.mark.parametrize("body", [
    '{"api_key":"sk-private-test-material"}',
    '{"run_id":"sk-private-test-material"}',
    '{"stage_override":{},"stage_override":{"instruction":"sk-private-test-material"}}',
    '{"stage_override":{"candidate_count":NaN}}',
    '{"stage_override":{"instruction":"' + "x" * (128 * 1024) + '"}}',
], ids=["extra_secret", "invalid_secret_type", "duplicate_keys", "non_finite", "oversized"])
def test_preview_input_errors_do_not_echo_secrets_or_parse_ambiguous_json(client, saved_stage, body):
    headers, _, _, base = saved_stage
    result = client.post(f"{base}/creation-recipe/stages/draft/preview", headers=headers,
                         content=body, json=None)
    assert result.status_code == 422
    assert "sk-private-test-material" not in result.text
    assert len(result.content) < 2000


def test_preview_selected_memory_revision_is_exact_pure_and_not_name_fallback(client, db_session, saved_stage):
    from sqlalchemy import func, select

    from app.models import CapabilityUse, ContentUnit, User
    from app.services import capability_memory
    from app.services.creation_recipes import _method

    _, _, unit_id, _ = saved_stage
    user = db_session.scalar(select(User).where(User.email == "recipe@studio.test"))
    unit = db_session.get(ContentUnit, unit_id)
    methods = []
    for instruction in ("方法一", "方法二"):
        item = capability_memory.create_artifact(db_session, user, {
            "kind": "prompt_skill", "name": "相同名字", "content": {"prompt": instruction},
            "args_schema": {}, "scope_type": "owner", "scope": {"id": user.id},
        })
        methods.append(capability_memory.lifecycle(db_session, user, item["id"], {
            "expected_revision": 1, "status": "saved", "scope_type": "owner", "scope": {"id": user.id},
        }))
    selected = methods[1]
    selection = {"source_kind": "capability_memory", "artifact_id": selected["id"],
                 "revision_id": selected["current_revision"]["id"], "arguments": {}}
    value, blockers = _method(db_session, user, unit, {"plugin": "test.stage", "plugin_version": "2"},
                              {"method": selection})
    assert not blockers and value["artifact_id"] == selected["id"]
    assert "方法二" in value["instruction"] and "方法一" not in value["instruction"]
    assert db_session.scalar(select(func.count(CapabilityUse.id))) == 0
    with pytest.raises(HTTPException):
        _method(db_session, User(id=999, is_active=True), unit,
                {"plugin": "test.stage", "plugin_version": "2"}, {"method": selection})


def test_inventory_only_skill_is_not_previewed_as_executable(client, db_session, saved_stage, monkeypatch):
    from sqlalchemy import select

    from app.models import ContentUnit, User
    from app.services import capability_memory
    from app.services.content_harness.skill_runtime import bootstrap_skill_runtimes
    from app.services.creation_recipes import _method

    _, _, unit_id, _ = saved_stage
    unit = db_session.get(ContentUnit, unit_id)
    user = db_session.scalar(select(User).where(User.email == "recipe@studio.test"))
    bootstrap_skill_runtimes()
    monkeypatch.setattr(capability_memory, "installed_skills", lambda db, user: {"items": [{
        "id": "a" * 64, "source_kind": "installed_agent_skill", "name": "installed-only", "version": "1",
    }]})
    result, blockers = _method(db_session, user, unit, {"plugin": "test.stage", "plugin_version": "2"},
        {"method": {"source_kind": "installed_agent_skill", "skill_id": "a" * 64,
                    "version": "1", "runtime_key": "skill_runtime.builtin", "runtime_version": "1"}})
    assert result is None and blockers == ["skill_runtime_identity_unverified"]


def test_evidence_preview_excludes_disallowed_snapshots_and_binds_live_revocation(client, db_session, saved_stage):
    from app.models import FactPack, FactPackItem, ProjectFactBoundaryRevision, utcnow
    from app.services.factpack_service import pack_snapshot_checksum, snapshot_checksum

    headers, project_id, _, base = saved_stage
    pack = FactPack(name="Exact boundary", status="frozen", version=1)
    db_session.add(pack)
    db_session.flush()
    items = []
    for index, allowed in enumerate((True, False)):
        snapshot = {"schema_version": 1, "evidence_kind": "author_opinion",
                    "statement": "可用证据" if allowed else "禁止发给模型的原文", "model_use_allowed": allowed}
        row = FactPackItem(fact_pack_id=pack.id, sort_order=index, evidence_kind="author_opinion",
            snapshot_json=snapshot, snapshot_checksum=snapshot_checksum(snapshot),
            model_use_allowed=allowed, public_use_allowed=True)
        db_session.add(row)
        items.append(row)
    db_session.flush()
    pack.checksum = pack_snapshot_checksum(items)
    db_session.add(ProjectFactBoundaryRevision(project_id=project_id, revision_no=1,
        fact_pack_id=pack.id, fact_pack_version=1, fact_pack_checksum=pack.checksum))
    db_session.commit()
    path = f"{base}/creation-recipe/stages/draft/preview"
    before = client.post(path, headers=headers, json={})
    assert before.status_code == 200, before.text
    assert "可用证据" in before.text and "禁止发给模型的原文" not in before.text
    assert before.json()["context"]["boundary"]["excluded"] == [
        {"item_id": items[1].id, "reason": "model_use_not_allowed"},
    ]
    items[0].public_use_revoked_at = utcnow()
    db_session.commit()
    after = client.post(path, headers=headers, json={})
    assert after.json()["ready"] is False
    assert "evidence_revoked" in after.json()["blockers"]
    assert before.json()["resolution_hash"] != after.json()["resolution_hash"]
    assert "可用证据" not in after.text


def test_successful_upstream_proposal_is_not_accepted_content(client, db_session, saved_stage):
    from app.models import ContentUnit, Workflow, WorkflowRun, WorkflowStep
    from app.services.workflow_engine import definition_checksum

    headers, _, unit_id, base = saved_stage
    unit = db_session.get(ContentUnit, unit_id)
    workflow = db_session.get(Workflow, unit.pinned_workflow_id)
    definition = deepcopy(workflow.definition_json)
    upstream = {**definition["nodes"][0], "id": "outline"}
    definition["nodes"] = [upstream, definition["nodes"][0]]
    definition["edges"] = [{"from": "outline", "to": "draft"}]
    definition["visual_order"] = ["outline", "draft"]
    assert client.post(f"{base}/workflow-override", headers=headers,
                       json={"expected_revision": 1, "definition": definition}).status_code == 201
    workflow = db_session.get(Workflow, unit.pinned_workflow_id)
    run = WorkflowRun(workflow_id=workflow.id, content_unit_id=unit.id, identity_snapshot_id=unit.identity_snapshot_id,
        workflow_version=workflow.version, definition_checksum=definition_checksum(definition), status="waiting_input")
    db_session.add(run)
    db_session.flush()
    db_session.add(WorkflowStep(run_id=run.id, node_id="outline", node_type="AI", status="succeeded",
        output_json={"proposal": "不可自动采用"}, output_hash="a" * 64))
    db_session.commit()
    preview = client.post(f"{base}/creation-recipe/stages/draft/preview", headers=headers,
                          json={"run_id": run.id}).json()
    assert preview["ready"] is False and "upstream_acceptance_required" in preview["blockers"]
    assert preview["upstream"] == {}


@pytest.mark.parametrize("endpoint", ["creation-recipe", "creation-recipe/stages/draft/preview"])
def test_recipe_reads_do_not_provision_unknown_header_identity(client, db_session, saved_stage, endpoint):
    from sqlalchemy import func, select

    from app.models import User

    _, _, _, base = saved_stage
    count = db_session.scalar(select(func.count(User.id)))
    headers = {"X-Studio-User": "not-provisioned@studio.test"}
    result = (client.post(f"{base}/{endpoint}", headers=headers, json={}) if endpoint.endswith("preview")
              else client.get(f"{base}/{endpoint}", headers=headers))
    assert result.status_code == 403
    assert db_session.scalar(select(func.count(User.id))) == count


@pytest.mark.parametrize("profile", [None, {"provider": "mock", "enabled": False}])
def test_stage_model_never_falls_back_from_unavailable_generate_route(monkeypatch, profile):
    from app import runtime_config
    from app.services.creation_recipes import _model

    monkeypatch.setattr(runtime_config, "_OVERRIDES", {})
    runtime_config.set_runtime(runtime_config.KEY_LLM, {"provider": "mock"})
    runtime_config.set_runtime(runtime_config.KEY_MODELS, {
        "profiles": {"selected": profile} if profile else {}, "routes": {"generate": "selected"},
    })
    value, blockers = _model({})
    assert value is None and blockers == ["model_profile_unavailable"]


def test_historical_memory_revision_does_not_inherit_new_project_scope(client, db_session, saved_stage):
    from sqlalchemy import select

    from app.models import ContentUnit, User
    from app.services import capability_memory
    from app.services.creation_recipes import _method

    headers, project_a, unit_a, _ = saved_stage
    project_b = client.post("/api/v1/content-projects", json={"title": "另一个项目"}, headers=headers).json()["id"]
    user = db_session.scalar(select(User).where(User.email == "recipe@studio.test"))
    unit = db_session.get(ContentUnit, unit_a)
    item = capability_memory.create_artifact(db_session, user, {
        "kind": "prompt_skill", "name": "项目方法", "content": {"prompt": "仅用于项目A"},
        "args_schema": {}, "scope_type": "project", "scope": {"id": project_a},
    })
    item = capability_memory.lifecycle(db_session, user, item["id"], {
        "expected_revision": 1, "status": "saved",
    })
    old_revision = item["current_revision"]["id"]
    capability_memory.lifecycle(db_session, user, item["id"], {
        "expected_revision": 2, "status": "saved", "scope_type": "project", "scope": {"id": project_b},
        "confirm_scope_broadening": True,
    })
    other_unit = ContentUnit(id=999, project_id=project_b, modality="text", persona_id=unit.persona_id)
    value, blockers = _method(db_session, user, other_unit, {"plugin": "test.stage", "plugin_version": "2"},
        {"method": {"source_kind": "capability_memory", "artifact_id": item["id"],
                    "revision_id": old_revision, "arguments": {}}})
    assert value is None and blockers == ["method_scope_mismatch"]


@pytest.mark.parametrize("bad_type", [[], {}, None, False])
def test_malformed_schema_type_is_typed_registry_failure(bad_type):
    from app.services.content_harness.registry import PluginRegistry, RegistryError

    value = _contract()
    value["config_schema"]["properties"]["candidate_count"]["type"] = bad_type
    with pytest.raises(RegistryError):
        PluginRegistry().register("node", "bad", "1", _StageExecutor(), stage_contract=value)


@pytest.mark.parametrize("override", [[], False])
def test_false_like_override_is_not_silently_empty(override):
    from app.services.stage_contracts import StageContractError

    with pytest.raises(StageContractError):
        _resolved(override=override)


@pytest.mark.parametrize("tamper", ["snapshot", "item_checksum", "pack_checksum"])
def test_preview_never_exposes_tampered_frozen_evidence(client, db_session, saved_stage, tamper):
    from app.models import FactPack, FactPackItem, ProjectFactBoundaryRevision
    from app.services.factpack_service import pack_snapshot_checksum, snapshot_checksum

    headers, project_id, _, base = saved_stage
    pack = FactPack(name="Frozen", status="frozen", version=1)
    db_session.add(pack)
    db_session.flush()
    snapshot = {"schema_version": 1, "statement": "真实原文", "model_use_allowed": True}
    item = FactPackItem(fact_pack_id=pack.id, evidence_kind="author_opinion", sort_order=0,
        snapshot_json=snapshot, snapshot_checksum=snapshot_checksum(snapshot), model_use_allowed=True)
    db_session.add(item)
    db_session.flush()
    pack.checksum = pack_snapshot_checksum([item])
    boundary = ProjectFactBoundaryRevision(project_id=project_id, revision_no=1,
        fact_pack_id=pack.id, fact_pack_version=1, fact_pack_checksum=pack.checksum)
    db_session.add(boundary)
    db_session.commit()
    if tamper == "snapshot":
        item.snapshot_json = {**snapshot, "statement": "伪造原文"}
    elif tamper == "item_checksum":
        item.snapshot_checksum = "f" * 64
    else:
        pack.checksum = boundary.fact_pack_checksum = "f" * 64
    db_session.commit()
    result = client.post(f"{base}/creation-recipe/stages/draft/preview", headers=headers, json={})
    assert result.status_code == 200, result.text
    assert result.json()["ready"] is False
    assert "evidence_integrity" in result.json()["blockers"]
    assert "真实原文" not in result.text and "伪造原文" not in result.text


@pytest.mark.parametrize("operation", ["advance", "rerun_node", "rerun_from_here", "retry_run", "complete_node", "_execute_node"])
def test_legacy_mutation_entrypoints_cannot_bypass_stage_claim(client, db_session, saved_stage, operation):
    from sqlalchemy import func, select

    from app.models import ContentUnit, User, Workflow, WorkflowRun, WorkflowStep, WorkflowStepAttempt
    from app.services import workflow_engine

    _, _, unit_id, _ = saved_stage
    unit = db_session.get(ContentUnit, unit_id)
    workflow = db_session.get(Workflow, unit.pinned_workflow_id)
    user = db_session.scalar(select(User).where(User.email == "recipe@studio.test"))
    run = WorkflowRun(workflow_id=workflow.id, content_unit_id=unit.id, identity_snapshot_id=unit.identity_snapshot_id,
        workflow_version=workflow.version, definition_checksum=workflow.checksum,
        status="failed" if operation == "retry_run" else "waiting_input")
    db_session.add(run)
    db_session.flush()
    step = WorkflowStep(run_id=run.id, node_id="draft", node_type="AI", plugin_key="test.stage", plugin_version="2",
        status="failed" if operation == "retry_run" else "pending" if operation == "advance" else "waiting_input",
        output_json={"preserve": "history"}, output_hash="a" * 64)
    db_session.add(step)
    db_session.commit()
    before = run.status, step.status, step.output_json, step.output_hash
    args = [db_session, run]
    if operation in {"rerun_node", "rerun_from_here", "complete_node"}:
        args.append(step.node_id)
    elif operation == "_execute_node":
        args.append(step)
    if operation == "complete_node":
        args.append({})
    args.append(user)
    with pytest.raises(ValueError, match="stage_invocation_required"):
        getattr(workflow_engine, operation)(*args)
    db_session.expire_all()
    assert before == (run.status, step.status, step.output_json, step.output_hash)
    assert db_session.scalar(select(func.count(WorkflowStepAttempt.id))) == 0


@pytest.mark.parametrize("depth, accepted", [(16, True), (17, False)])
def test_nested_invocation_envelope_remains_bounded(depth, accepted):
    from app.services.stage_contracts import StageContractError, canonical

    value = "frozen field"
    for _ in range(depth):
        value = {"item": value}
    if accepted:
        assert canonical(value) == value
    else:
        with pytest.raises(StageContractError, match="stage_value_too_deep"):
            canonical(value)
