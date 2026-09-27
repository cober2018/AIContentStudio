"""Validation and immutable versions for project production workflows."""

from copy import deepcopy
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import DiscoverabilityProfileVersion, Workflow
from .content_harness.registry import RegistryError, registry
from .data_source_plugins import descriptors as data_source_descriptors
from .workflow_engine import definition_checksum

NODE_KINDS = {"Data", "AI", "Tool", "Rule", "Human", "System"}
FAILURE_POLICIES = {"stop", "skip", "wait_human"}
KIND_PLUGINS = {
    "Data": {"data.source"},
    "AI": {"builtin.generate", "builtin.humanize", "builtin.generate_cover", "node.skill"},
    "Tool": {"builtin.connector_pull", "builtin.extract_facts", "builtin.factpack_freeze", "builtin.topic_suggest", "builtin.export"},
    "Rule": {"builtin.fact_check", "builtin.content_censor", "builtin.discoverability_post"},
    "Human": {"builtin.adopt_topic", "builtin.confirm_facts", "builtin.approve"},
    "System": {"system.constant"},
}
PORTABLE_ROOT_KEYS = {"nodes", "edges", "visual_order"}
PORTABLE_NODE_KEYS = {
    "id", "kind", "plugin", "plugin_version", "label", "config", "input_mapping", "output_mapping",
    "condition", "failure_policy", "enabled", "layout",
}
BOUND_KEYS = {
    "project_id", "content_unit_id", "unit_id", "run_id", "snapshot_id", "data_snapshot_id",
    "asset_revision_id", "draft_id", "candidate_id", "attempt_id", "output", "output_json",
    "actual_output", "entity_id",
}
PORTABLE_CONFIG_KEYS = {
    "project_id", "content_unit_id", "unit_id", "data_source_plugin_key", "provider", "model",
    "model_policy", "tool_key", "rule_key", "skill", "skill_version", "prompt_template",
    "query_template", "profile_key", "channel", "content_form", "temperature", "max_tokens",
    "timeout_sec", "auto_confirm", "name", "source_ref",
}
BOUND_LITERAL = re.compile(r"\b(?:project_id|content_unit_id|unit_id|run_id|snapshot_id|asset_revision_id|draft_id|candidate_id|attempt_id)\s*[:=]\s*\d+\b", re.I)


def _validate_mapping(mapping: object, ids: set[str], name: str) -> None:
    if not isinstance(mapping, dict):
        raise ValueError(f"{name} 必须是对象")
    for key, ref in mapping.items():
        if not isinstance(key, str) or not key:
            raise ValueError(f"{name} 的字段名无效")
        if isinstance(ref, dict) and "node_id" in ref:
            if ref["node_id"] not in ids or not isinstance(ref.get("output"), str):
                raise ValueError(f"{name} 引用了不存在的节点或输出")
        elif not isinstance(ref, (str, int, float, bool, type(None), dict)):
            raise ValueError(f"{name} 值无效")


def execution_options() -> dict:
    from .. import runtime_config
    from .generation.providers import effective_llm_config, provider_model_name

    ai = {}
    for plugin, purpose in (("builtin.generate", "generate"), ("builtin.humanize", "rewrite")):
        config = effective_llm_config(purpose)
        provider = config.get("provider") or ""
        model = provider_model_name(purpose)
        available = provider == "mock" or (provider == "openai_compatible" and bool(config.get("base_url") and config.get("api_key") and config.get("model")))
        ai[plugin] = {"provider": provider, "model": model, "available": available, "reason": "模拟模型，仅供开发验收" if provider == "mock" else None if available else "当前模型路由未配置完整"}
    image = runtime_config.get_runtime(runtime_config.KEY_IMAGE) or {}
    enabled = bool(image.get("enabled") and image.get("provider") and image.get("model"))
    ai["builtin.generate_cover"] = {"provider": image.get("provider") or "", "model": image.get("model") or "", "available": enabled, "reason": None if enabled else "AI 生图未配置或未启用"}
    ai["node.skill"] = {"provider": "", "model": "", "available": False, "reason": "由已注册 Skill Runtime 决定，不能选择模型"}
    return {"ai": ai}


def validate_ai_executor_selection(node: dict) -> None:
    config = node.get("config") or {}
    if node.get("kind") != "AI" or not ("provider" in config or "model" in config):
        return
    selected = execution_options()["ai"][node["plugin"]]
    if not selected["available"] or config.get("provider") != selected["provider"] or config.get("model") != selected["model"]:
        raise ValueError(f"节点 {node['id']} 的 Provider/Model 与当前可执行路由不一致")


def validate_definition(definition: dict) -> dict:
    if not isinstance(definition, dict):
        raise ValueError("工作流定义必须是对象")
    nodes = definition.get("nodes")
    edges = definition.get("edges")
    order = definition.get("visual_order")
    if not isinstance(nodes, list) or not isinstance(edges, list) or not isinstance(order, list):
        raise ValueError("节点、边和视觉顺序必须是列表")
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
            raise ValueError(f"节点 {node['id']} 未选择执行插件")
        if plugin not in KIND_PLUGINS[node["kind"]]:
            raise ValueError(f"节点 {node['id']} 的执行插件与类型不匹配")
        try:
            descriptor = registry.descriptor("node", plugin, str(node.get("plugin_version") or "1"))
        except RegistryError as exc:
            raise ValueError(f"节点 {node['id']} 执行插件不可用：{exc}") from exc
        if descriptor.side_effect:
            raise ValueError(f"节点 {node['id']} 包含禁止泛化执行的远端副作用")
        if node.get("kind") == "Human" and not descriptor.human_gate:
            raise ValueError(f"节点 {node['id']} 不是人工执行插件")
        if node.get("kind") != "Human" and descriptor.human_gate:
            raise ValueError(f"节点 {node['id']} 的执行插件属于人工节点")
        if not isinstance(node.get("config", {}), dict):
            raise ValueError(f"节点 {node['id']} 配置无效")
        config = node.get("config") or {}
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
        if set(config) - PORTABLE_CONFIG_KEYS:
            raise ValueError(f"节点 {node['id']} 配置包含不可移植字段")
        if node["kind"] == "Data" and "source_ref" in config:
            config["source_ref"] = {"$run_param": "source_ref"}

    def inspect(value: object, *, resolve_at_runtime: bool) -> object:
        if isinstance(value, dict):
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


def validate_reusable_profiles(db: Session, definition: dict) -> None:
    for node in definition["nodes"]:
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
