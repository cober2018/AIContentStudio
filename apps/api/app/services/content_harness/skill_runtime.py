"""Skill Execution 与 Discovery 分离（D17/§6.17）。

- SkillRuntime 协议：execute(skill, input_payload, timeout) → SkillExecutionResult；
- BuiltIn adapter：进程内技能适配（当前为占位实现——本仓没有需要独立进程执行的内置技能）；
- dsh adapter：原文要求「只有在实际本地 DSH invocation contract 被核实后才实现，
  禁止猜测不存在的 DSH HTTP endpoint」——故 V1 不注册；
- preflight_workflow：运行前发现 required skill 未安装/未启用（而非运行中 ImportError）；
- 外部 Skill 只有「产出后回调」时继续走 ExternalContent ingest（兼容，不在本模块）。
"""

from __future__ import annotations

from typing import Any, Protocol

from sqlalchemy.orm import Session

from .contracts import SkillExecutionResult
from .registry import registry

DASH_ADAPTER_KEY = "skill_runtime.dsh"  # 预留：真实 DSH 契约核实后才注册


class SkillRuntime(Protocol):
    key: str
    version: str

    def execute(self, skill: dict[str, Any], input_payload: dict, timeout_sec: int) -> SkillExecutionResult: ...


class BuiltInSkillRuntime:
    """进程内技能适配：V1 无独立进程内置技能，执行即 unavailable（如实报告，不猜行为）。"""

    key = "skill_runtime.builtin"
    version = "1"

    def execute(self, skill: dict[str, Any], input_payload: dict, timeout_sec: int) -> SkillExecutionResult:
        return SkillExecutionResult(
            status="unavailable",
            error=f"内置 runtime 未实现技能 {skill.get('name')} 的执行（外部 Skill 产出回填走 ExternalContent ingest）",
        )


_BOOTSTRAPPED = False


def bootstrap_skill_runtimes() -> None:
    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return
    if "skill_runtime.builtin" not in {d.key for d in registry.list("skill_runtime")}:
        registry.register("skill_runtime", "skill_runtime.builtin", "1", BuiltInSkillRuntime(), label="内置技能运行时")
    _BOOTSTRAPPED = True


def resolve_executable_runtime():
    """R2-H5：返回第一个「非内置占位」的可执行 runtime；没有则 None。

    BuiltInSkillRuntime 如实不执行任何技能（只报 unavailable）——它不构成可执行能力；
    真实 runtime（如 DSH 契约核实后的 adapter）注册后即可被执行链路发现。
    """
    bootstrap_skill_runtimes()
    for descriptor in registry.list("skill_runtime"):
        if descriptor.key != "skill_runtime.builtin":
            return registry.resolve("skill_runtime", descriptor.key, descriptor.version)
    return None


def _enabled_skills(db: Session | None) -> tuple[bool, set[str]]:
    """启用集（R3-4 三态语义，安全边界）：

    - plugins 配置不存在或无 skills_enabled 键 → (False, set())：系统默认政策（不启用 enable gate）；
    - skills_enabled = [] → (True, set())：明确全部禁用（用户取消所有勾选 = 一个都不许用）；
    - skills_enabled = [...] → (True, 集合)：只允许列表内技能。
    """
    try:
        from ... import runtime_config

        plugins = runtime_config.get_runtime(runtime_config.KEY_PLUGINS) or {}
        if "skills_enabled" not in plugins:
            return False, set()
        enabled = plugins.get("skills_enabled")
        return True, set(enabled) if isinstance(enabled, list) else set()
    except Exception:  # noqa: BLE001
        return False, set()


def _referenced_skills(definition: dict) -> list[dict[str, str]]:
    """扫描节点定义中对技能的引用：config.skill / params.skill（skill node 或引用外部技能的节点）。"""
    from .contracts import node_config_of

    refs: list[dict[str, str]] = []
    for node in definition.get("nodes", []):
        config = node_config_of(node)  # R4.1：与执行同语义（config 优先合并），preflight 不再有盲区
        skill = config.get("skill")
        if skill:
            refs.append(
                {
                    "node_id": node.get("id"),
                    "skill": str(skill),
                    "skill_version": str(config.get("skill_version") or "unversioned"),
                }
            )
    return refs


def _has_skill_nodes(definition: dict) -> bool:
    """schema v2 plugin=node.skill 或 schema v1 type=skill 的节点。"""
    return any(
        (n.get("plugin") == "node.skill" or n.get("type") == "skill") for n in definition.get("nodes", [])
    )


def preflight_workflow(db: Session | None, definition: dict) -> list[str]:
    """D17：运行前发现 required skill not installed/enabled。

    返回问题列表（空 = 通过）；engine 在 start_run 前调用，非空即拒绝启动。
    R2-H5：node.skill 工作流在无可执行 runtime 时启动前拒绝（而不是运行期失败）。
    """
    from ...services import plugin_registry

    problems: list[str] = []
    installed = {s["name"]: s for s in plugin_registry.scan_skills()}
    gate_active, enabled = _enabled_skills(db)
    for ref in _referenced_skills(definition):
        skill = ref["skill"]
        if skill not in installed:
            problems.append(f"required skill not installed: {skill} (node {ref['node_id']})")
        elif gate_active and skill not in enabled:
            problems.append(f"required skill not enabled: {skill} (node {ref['node_id']})")
        elif ref["skill_version"] not in {"unversioned", installed[skill]["version"]}:
            problems.append(
                f"skill version mismatch: {skill}@{ref['skill_version']} != {installed[skill]['version']} (node {ref['node_id']})"
            )
    if _has_skill_nodes(definition) and resolve_executable_runtime() is None:
        problems.append(
            "node.skill 无可执行 SkillRuntime（内置 runtime 不执行外部技能；DSH 契约核实后注册）"
        )
    return problems
