"""Built-in Node Plugins（D6）：把 workflow_engine 的既有 handler 薄包装为 registry 插件。

- 业务行为零变化：execute 直接委托旧 handler（同一套校验/审计/闸门）；
- schema v1 节点 `{"type": "generate"}` 经 TYPE_TO_PLUGIN 映射到 `builtin.generate@1`；
- schema v2 节点直接写 `{"plugin": "node.skill", "plugin_version": "1"}`（Phase 7 起使用）。
"""

from __future__ import annotations

from ..contracts import NodeResult, WorkflowExecutionContext, node_config_of  # noqa: F401  re-export（R4.1 统一语义）
from ..registry import registry

# schema v1 node type → builtin plugin key（旧定义兼容层，loader 内存映射，不改历史 JSON）
TYPE_TO_PLUGIN: dict[str, str] = {
    "connector_pull": "builtin.connector_pull",
    "extract_facts": "builtin.extract_facts",
    "factpack_freeze": "builtin.factpack_freeze",
    "suggest_topics": "builtin.topic_suggest",
    "generate": "builtin.generate",
    "humanize_polish": "builtin.humanize",
    "content_censor": "builtin.content_censor",
    "generate_cover": "builtin.generate_cover",
    "fact_check": "builtin.fact_check",
    "discoverability_post": "builtin.discoverability_post",
    "export": "builtin.export",
    "publish_wechat": "builtin.publish_wechat",
    "adopt_topic": "builtin.adopt_topic",
    "confirm_facts": "builtin.confirm_facts",
    "approve": "builtin.approve",
}


class LegacyHandlerNodePlugin:
    """以 (db, run, step, user) 签名委托 workflow_engine 旧 handler 的通用插件。"""

    key = ""
    version = "1"
    human_gate = False
    side_effect = False
    label = ""
    handler_name = ""
    complete_handler_name = ""

    @property
    def _handler(self):
        from ....services import workflow_engine as legacy  # 延迟导入避免循环

        return getattr(legacy, self.handler_name)

    def execute(self, db, ctx: WorkflowExecutionContext, config: dict, user) -> NodeResult:
        return NodeResult(output=self._handler(db, ctx.run, ctx.step, user) or {})


class LegacyHumanNodePlugin(LegacyHandlerNodePlugin):
    """人工节点：human_gate=True，complete 委托旧 COMPLETE_HANDLERS 实现。"""

    human_gate = True

    def complete(self, db, ctx: WorkflowExecutionContext, payload: dict, user) -> NodeResult:
        from ....services import workflow_engine as legacy

        handler = getattr(legacy, self.complete_handler_name)
        return NodeResult(output=handler(db, ctx.run, ctx.step, payload or {}, user) or {})


class SkillNodePlugin:
    """node.skill@1（R2-H5）：按节点 config.skill 把执行委托给已注册 SkillRuntime。

    preflight_workflow 会在启动前拒绝「没有任何可执行 runtime」的工作流；
    本插件是真正的执行路径：runtime 返回 unavailable 即节点失败（如实报告，不静默跳过）。
    """

    key = "node.skill"
    version = "1"
    human_gate = False
    side_effect = False

    def _runtime(self):
        # R3-1：相对导入修正（nodes 的上级包才是 content_harness）
        from .. import skill_runtime

        skill_runtime.bootstrap_skill_runtimes()
        return skill_runtime.resolve_executable_runtime()

    def execute(self, db, ctx: WorkflowExecutionContext, config: dict, user) -> NodeResult:
        from ..contracts import SkillExecutionResult

        runtime = self._runtime()
        name = config.get("skill") or "unknown"
        if runtime is None:
            raise ValueError(
                f"技能 {name} 无可执行 SkillRuntime（内置 runtime 不执行外部技能；DSH 契约核实后注册）"
            )
        result: SkillExecutionResult = runtime.execute(
            {"name": name, "version": config.get("skill_version") or "unversioned"},
            {"params": config, "context": {"run_id": ctx.run.id if ctx.run else None}},
            timeout_sec=int(config.get("timeout_sec") or 120),
        )
        if result.status != "succeeded":
            raise ValueError(f"技能 {name} 执行失败（{result.status}）：{result.error or '无详情'}")
        return NodeResult(output={"skill": name, "result": result.output or {}})


def _plugin(key: str, handler: str, label: str, *, complete: str | None = None, side_effect: bool = False):
    attrs = {"key": key, "handler_name": handler, "label": label, "side_effect": side_effect}
    if complete:
        attrs["complete_handler_name"] = complete
        base: type = LegacyHumanNodePlugin
    else:
        base = LegacyHandlerNodePlugin
    return type(f"_Plugin_{key.replace('.', '_')}", (base,), attrs)


# (key, execute handler, label, complete handler, side_effect)
_BUILTIN_SPECS: list[tuple[str, str, str, str | None, bool]] = [
    ("builtin.connector_pull", "_h_connector_pull", "拉取监测数据", None, False),
    ("builtin.extract_facts", "_h_extract_facts", "抽取候选事实", None, False),
    ("builtin.factpack_freeze", "_h_factpack_freeze", "打包冻结 FactPack", None, False),
    ("builtin.topic_suggest", "_h_suggest_topics", "AI 荐题", None, False),
    ("builtin.generate", "_h_generate", "生成稿件", None, False),
    ("builtin.humanize", "_h_humanize_polish", "去 AI 味精炼", None, False),
    ("builtin.content_censor", "_h_content_censor", "合规审查", None, False),
    ("builtin.generate_cover", "_h_generate_cover", "AI 封面", None, False),
    ("builtin.fact_check", "_h_fact_check", "事实校验", None, False),
    ("builtin.discoverability_post", "_h_discoverability_post", "SEO 审查（post）", None, False),
    ("builtin.export", "_h_export", "本地导出", None, False),
    ("builtin.publish_wechat", "_h_publish_wechat", "公众号草稿箱（遗留，显式启用）", None, True),
    ("builtin.adopt_topic", "_h_adopt_topic_complete", "人工采纳选题", "_h_adopt_topic_complete", False),
    ("builtin.confirm_facts", "_h_confirm_facts_complete", "人工确认事实", "_h_confirm_facts_complete", False),
    ("builtin.approve", "_h_approve", "人工批准", "_h_approve", False),
]

# 直接注册的非 handler 插件（R2-H5：node.skill 可执行节点）
_DIRECT_PLUGINS = [SkillNodePlugin]

_bootstrapped = False


def bootstrap_builtin_nodes() -> None:
    """注册 built-in 节点插件（幂等）。engine 模块导入时调用。"""
    global _bootstrapped
    if _bootstrapped:
        return
    for key, handler, label, complete, side_effect in _BUILTIN_SPECS:
        if key in {d.key for d in registry.list("node")}:
            continue
        plugin_cls = _plugin(key, handler, label, complete=complete, side_effect=side_effect)
        registry.register(
            "node",
            key,
            "1",
            plugin_cls(),  # 注册实例：execute/complete 以绑定方法被引擎调用
            label=label,
            human_gate=complete is not None,
            side_effect=side_effect,
        )
    for plugin_cls in _DIRECT_PLUGINS:
        if plugin_cls.key not in {d.key for d in registry.list("node")}:
            registry.register("node", plugin_cls.key, plugin_cls.version, plugin_cls(), label="Skill 执行")
    _bootstrapped = True


def resolve_node_key(node: dict) -> tuple[str, str]:
    """从节点定义解析 plugin key/version：schema v2 读 plugin 字段，schema v1 按 type 映射。"""
    plugin = node.get("plugin")
    if plugin:
        return str(plugin), str(node.get("plugin_version") or "1")
    node_type = node.get("type") or ""
    key = TYPE_TO_PLUGIN.get(str(node_type))
    if not key:
        raise ValueError(f"未知节点类型: {node_type or node}")
    return key, "1"
