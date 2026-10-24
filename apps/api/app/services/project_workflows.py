"""Validation and immutable versions for project production workflows."""

import json
import re
from copy import deepcopy

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import DiscoverabilityProfileVersion, Workflow
from .content_harness.registry import RegistryError, registry
from .data_source_plugins import descriptors as data_source_descriptors
from .workflow_engine import _validate_generation_output_mapping, definition_checksum

NODE_KINDS = {"Data", "AI", "Tool", "Rule", "Human", "System"}
FAILURE_POLICIES = {"stop", "skip", "wait_human"}
KIND_PLUGINS = {
    "Data": {"data.source"},
    "AI": {"node.skill", "media.generate"},
    "Tool": {"builtin.connector_pull", "builtin.extract_facts", "builtin.factpack_freeze"},
    "Rule": set(),
    "Human": {"builtin.confirm_facts"},
    "System": {"system.constant"},
}
PORTABLE_ROOT_KEYS = {"nodes", "edges", "visual_order"}
PORTABLE_NODE_KEYS = {
    "id", "kind", "plugin", "plugin_version", "label", "config", "input_mapping", "output_mapping",
    "condition", "failure_policy", "enabled", "layout",
    "stage_schema",
}
BOUND_KEYS = {
    "project_id", "content_unit_id", "unit_id", "run_id", "snapshot_id", "data_snapshot_id",
    "asset_revision_id", "candidate_id", "attempt_id", "output", "output_json",
    "actual_output", "entity_id",
}
PORTABLE_CONFIG_KEYS = {
    "project_id", "content_unit_id", "unit_id", "data_source_plugin_key", "provider", "model",
    "model_policy", "model_profile_id", "tool_key", "rule_key", "skill", "skill_version", "prompt_template",
    "query_template", "profile_key", "channel", "content_form", "temperature", "max_tokens",
    "timeout_sec", "auto_confirm", "name", "source_ref",
    "capability", "selected_profile", "explicit_plugin", "prompt", "parameters", "source_revision_ids",
}
BOUND_LITERAL = re.compile(r"\b(?:project_id|content_unit_id|unit_id|run_id|snapshot_id|asset_revision_id|candidate_id|attempt_id)\s*[:=]\s*\d+\b", re.IGNORECASE)


def _validate_mapping(mapping: object, ids: set[str], name: str) -> None:
    if not isinstance(mapping, dict):
        raise ValueError(f"{name} 必须是对象")  # noqa: TRY004 - API 将配置错误统一映射为 422。
    for key, ref in mapping.items():
        if not isinstance(key, str) or not key:
            raise ValueError(f"{name} 的字段名无效")
        if isinstance(ref, dict) and "node_id" in ref:
            if ref["node_id"] not in ids or not isinstance(ref.get("output"), str):
                raise ValueError(f"{name} 引用了不存在的节点或输出")
        elif not isinstance(ref, (str, int, float, bool, type(None), dict)):
            raise ValueError(f"{name} 值无效")


def execution_options() -> dict:
    return {"ai": {"node.skill": {"provider": "", "model": "", "available": False, "reason": "由已注册 Skill Runtime 决定，不能选择模型"}}}


def validate_ai_executor_selection(node: dict) -> None:
    config = node.get("config") or {}
    if node.get("kind") != "AI" or not ("provider" in config or "model" in config or "model_profile_id" in config):
        return
    selected = execution_options()["ai"][node["plugin"]]
    if config.get("model_profile_id"):
        selected = next((p for p in selected.get("profiles", []) if p["profile_id"] == config["model_profile_id"]), None)
        if selected is None:
            raise ValueError("所选模型配置不可执行")
    if not selected["available"]:
        raise ValueError(f"节点 {node['id']} 的 Provider/Model 与当前可执行路由不一致")
    if config.get("provider") and config["provider"] != selected["provider"]:
        raise ValueError(f"节点 {node['id']} 的 Provider/Model 与当前可执行路由不一致")
    if config.get("model") and config["model"] != selected["model"]:
        raise ValueError(f"节点 {node['id']} 的 Provider/Model 与当前可执行路由不一致")


def validate_definition(definition: dict) -> dict:
    if not isinstance(definition, dict):
        raise ValueError("工作流定义必须是对象")  # noqa: TRY004 - API 将配置错误统一映射为 422。
    nodes = definition.get("nodes")
    edges = definition.get("edges")
    order = definition.get("visual_order")
    if not isinstance(nodes, list) or not isinstance(edges, list) or not isinstance(order, list):
        raise ValueError("节点、边和视觉顺序必须是列表")  # noqa: TRY004 - API 将配置错误统一映射为 422。
    ids = [node.get("id") for node in nodes if isinstance(node, dict)]
    if len(ids) != len(nodes) or any(not isinstance(node_id, str) or not node_id for node_id in ids) or len(set(ids)) != len(ids):
        raise ValueError("节点 ID 缺失或重复")
    id_set = set(ids)
    if len(order) != len(ids) or set(order) != id_set:
        raise ValueError("视觉顺序须包含每个节点且仅包含一次")
    for node in nodes:
        if node.get("kind") not in NODE_KINDS:
            raise ValueError(f"节点 {node['id']} 类型无效")
        plugin = node.get("plugin")
        if not isinstance(plugin, str):
            raise ValueError(f"节点 {node['id']} 未选择执行插件")  # noqa: TRY004 - API 将配置错误统一映射为 422。
        try:
            descriptor = registry.descriptor("node", plugin, str(node.get("plugin_version") or "1"))
        except RegistryError as exc:
            raise ValueError(f"节点 {node['id']} 执行插件不可用：{exc}") from exc
        stage = descriptor.stage_contract
        if stage:
            metadata = stage.to_dict()
            if (node.get("stage_schema") != metadata["stage_schema"]
                    or node.get("plugin_version") != descriptor.version or node["kind"] != metadata["category"]):
                raise ValueError("stage_contract_pin_mismatch")
            stage.validate_config(node.get("config", {}))
        elif plugin not in KIND_PLUGINS[node["kind"]] or "stage_schema" in node:
            raise ValueError(f"节点 {node['id']} 的执行插件与类型不匹配")
        if descriptor.side_effect and plugin != "media.generate":
            raise ValueError(f"节点 {node['id']} 包含禁止泛化执行的远端副作用")
        if node.get("kind") == "Human" and not descriptor.human_gate:
            raise ValueError(f"节点 {node['id']} 不是人工执行插件")
        if node.get("kind") != "Human" and descriptor.human_gate:
            raise ValueError(f"节点 {node['id']} 的执行插件属于人工节点")
        if not isinstance(node.get("config", {}), dict):
            raise ValueError(f"节点 {node['id']} 配置无效")  # noqa: TRY004 - API 将配置错误统一映射为 422。
        config = node.get("config") or {}
        if plugin == "media.generate":
            if descriptor.version in {"2", "3"}:
                from .stage_domain_integrations import media_request

                media_request(config, allow_aspect=descriptor.version == "3")
            elif descriptor.version != "4":
                from .generation_tasks import workflow_request

                mapped = node.get("input_mapping") or {}
                workflow_request({**config, "inputs": {key: "mapped" if key == "prompt" else [] for key in mapped}})
            elif node.get("input_mapping"):
                raise ValueError("Audio Stage 仅接受明确接受的上游稿件，不支持原始输入映射")
            if node.get("failure_policy", "stop") != "stop":
                raise ValueError("持久生成节点不允许跳过或泛化重试失败")
        if not stage:
            validate_ai_executor_selection(node)
        if node["kind"] == "Data":
            keys = {item["key"] for item in data_source_descriptors()}
            source_ref = config.get("source_ref")
            if config.get("data_source_plugin_key") not in keys or not (isinstance(source_ref, str) or source_ref == {"$run_param": "source_ref"}):
                raise ValueError(f"节点 {node['id']} 未选择已注册数据来源或来源引用")
        if node.get("failure_policy", "stop") not in FAILURE_POLICIES:
            raise ValueError(f"节点 {node['id']} 失败策略无效")
        if "condition" in node:
            condition = node["condition"]
            if not isinstance(condition, dict) or condition and (set(condition) != {"input", "equals"} or not isinstance(condition.get("input"), str) or condition["input"] not in (node.get("input_mapping") or {})):
                raise ValueError(f"节点 {node['id']} 条件无效或缺少输入映射")
        _validate_mapping(node.get("input_mapping", {}), id_set, "input_mapping")
        output_mapping = node.get("output_mapping", {})
        if not isinstance(output_mapping, dict) or any(not isinstance(key, str) or not key or not isinstance(value, str) or not value for key, value in output_mapping.items()):
            raise ValueError(f"节点 {node['id']} 输出映射无效")
        _validate_generation_output_mapping(node)
    adjacency = {node_id: [] for node_id in ids}
    for edge in edges:
        if not isinstance(edge, dict) or edge.get("from") not in id_set or edge.get("to") not in id_set:
            raise ValueError("依赖边引用了不存在的节点")
        adjacency[edge["from"]].append(edge["to"])
    edge_pairs = {(edge["from"], edge["to"]) for edge in edges}
    for node in nodes:
        for ref in (node.get("input_mapping") or {}).values():
            if isinstance(ref, dict) and "node_id" in ref and (ref["node_id"], node["id"]) not in edge_pairs:
                raise ValueError(f"节点 {node['id']} 的输入映射缺少对应依赖边")
    state: dict[str, int] = {}

    def visit(node_id: str) -> None:
        if state.get(node_id) == 1:
            raise ValueError("依赖图存在环")
        if state.get(node_id) == 2:
            return
        state[node_id] = 1
        for child in adjacency[node_id]:
            visit(child)
        state[node_id] = 2

    for node_id in ids:
        visit(node_id)
    return deepcopy(definition)


def validate_portable(definition: dict, *, source_project_id: int | None, source_unit_id: int | None) -> dict:
    if set(definition) - PORTABLE_ROOT_KEYS:
        raise ValueError("角色默认模板包含未支持的顶层字段")
    portable = deepcopy(definition)
    for node in portable["nodes"]:
        if set(node) - PORTABLE_NODE_KEYS:
            raise ValueError(f"节点 {node['id']} 包含不可移植字段")
        config = node.get("config") or {}
        if node.get("plugin") == "media.generate" and config.get("source_revision_ids"):
            raise ValueError("默认模板不能固定项目素材版本；请使用输入映射")
        stage = registry.descriptor("node", node["plugin"], str(node.get("plugin_version") or "1")).stage_contract
        portable_keys = set(stage.to_dict()["config_schema"]["properties"]) if stage else PORTABLE_CONFIG_KEYS
        if set(config) - portable_keys:
            raise ValueError(f"节点 {node['id']} 配置包含不可移植字段")
        if stage:
            stage.validate_config(config)
            if any(config.get(key) for key in ("source_revision_ids", "material_revision_ids", "source_master_revision_id")):
                raise ValueError("默认模板不能固定当前素材或Master版本")
        if node["kind"] == "Data" and "source_ref" in config:
            config["source_ref"] = {"$run_param": "source_ref"}

    def inspect(value: object, *, resolve_at_runtime: bool) -> object:
        if isinstance(value, dict):
            if value.get("source_kind") == "capability_memory":
                keys = {"source_kind", "artifact_id", "revision_id"}
                if (set(value) not in (keys, keys | {"arguments"}, keys | {"arguments_json"})
                        or type(value["artifact_id"]) is not int or type(value["revision_id"]) is not int):
                    raise ValueError("默认模板包含无效方法引用")
                if "arguments_json" in value:
                    arguments = json.loads(value["arguments_json"])
                    if type(arguments) is not dict:
                        raise ValueError("默认模板包含无效方法参数")
                    return {**value, "arguments_json": json.dumps(inspect(arguments, resolve_at_runtime=False),
                                                                  ensure_ascii=False, sort_keys=True, separators=(",", ":"))}
                if "arguments" in value:
                    return {**value, "arguments": inspect(value["arguments"], resolve_at_runtime=False)}
                return value
            if set(value) == {"node_id", "output"} and isinstance(value["node_id"], str) and isinstance(value["output"], str):
                return value
            result = {}
            for key, child in value.items():
                if resolve_at_runtime and key == "project_id" and source_project_id is not None and child == source_project_id:
                    result[key] = {"$context": "project.id"}
                    continue
                if resolve_at_runtime and key in {"content_unit_id", "unit_id"} and source_unit_id is not None and child == source_unit_id:
                    result[key] = {"$context": "unit.id"}
                    continue
                if resolve_at_runtime and key == "model_profile_id":
                    from .generation.providers import LLMError, effective_llm_config

                    if not isinstance(child, str) or not child:
                        raise ValueError("角色默认模板引用了无效模型配置")
                    try:
                        effective_llm_config(profile=child)
                    except LLMError as exc:
                        raise ValueError("角色默认模板引用了不可用模型配置") from exc
                    result[key] = child
                    continue
                if key in BOUND_KEYS or key.endswith("_id") and key != "node_id":
                    raise ValueError(f"角色默认模板包含项目绑定值：{key}")
                result[key] = inspect(child, resolve_at_runtime=resolve_at_runtime)
            return result
        elif isinstance(value, list):
            return [inspect(child, resolve_at_runtime=resolve_at_runtime) for child in value]
        elif isinstance(value, str) and BOUND_LITERAL.search(value):
            raise ValueError("角色默认模板包含项目绑定 ID 字面量")
        return value

    for node in portable["nodes"]:
        for key, value in node.items():
            if key != "id":
                node[key] = inspect(value, resolve_at_runtime=key == "config")
    return portable


def validate_reusable_profiles(db: Session, definition: dict, *, user) -> None:
    for node in definition["nodes"]:
        method = (node.get("config") or {}).get("method")
        if type(method) is dict and method.get("source_kind") == "capability_memory":
            from ..models import CapabilityArtifact, CapabilityArtifactRevision

            artifact = db.get(CapabilityArtifact, method["artifact_id"])
            revision = db.get(CapabilityArtifactRevision, method["revision_id"])
            if (artifact is None or revision is None or revision.artifact_id != artifact.id
                    or artifact.status not in {"saved", "pinned"}
                    or revision.metadata_json.get("status") not in {"saved", "pinned"}
                    or artifact.scope_type == "project" or revision.metadata_json.get("scope_type") == "project"
                    or artifact.owner_user_id != user.id):
                raise ValueError("默认模板不能固化项目范围或不可用方法")
        profile_key = (node.get("config") or {}).get("profile_key")
        if profile_key is None:
            continue
        if not isinstance(profile_key, str) or not db.scalar(select(DiscoverabilityProfileVersion.id).where(DiscoverabilityProfileVersion.profile_key == profile_key, DiscoverabilityProfileVersion.status == "published").limit(1)):
            raise ValueError(f"节点 {node['id']} 引用了不可共享或不存在的 Profile")


def resolve_placeholders(value: object, *, project_id: int, unit_id: int, run_params: dict) -> object:
    if value == {"$context": "project.id"}:
        return project_id
    if value == {"$context": "unit.id"}:
        return unit_id
    if value == {"$run_param": "source_ref"}:
        ref = run_params.get("source_ref")
        if not isinstance(ref, str) or not ref:
            raise ValueError("运行参数缺少 source_ref")
        return ref
    if isinstance(value, dict):
        return {key: resolve_placeholders(child, project_id=project_id, unit_id=unit_id, run_params=run_params) for key, child in value.items()}
    if isinstance(value, list):
        return [resolve_placeholders(child, project_id=project_id, unit_id=unit_id, run_params=run_params) for child in value]
    return value


def new_workflow_version(db: Session, *, key: str, name: str, definition: dict, owner_user_id: int, scope: str, created_by: str) -> Workflow:
    version = db.scalar(select(Workflow.version).where(Workflow.workflow_key == key).order_by(Workflow.version.desc()).limit(1)) or 0
    workflow = Workflow(
        name=name,
        workflow_key=key,
        version=version + 1,
        status="published",
        schema_version=2,
        checksum=definition_checksum(definition),
        definition_json=deepcopy(definition),
        owner_user_id=owner_user_id,
        scope=scope,
        created_by=created_by,
    )
    db.add(workflow)
    db.flush()
    return workflow
