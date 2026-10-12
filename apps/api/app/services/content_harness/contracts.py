"""Content Harness 契约（开发 OpenSpec §6.2）：全系统统一结构，禁止各模块自行发明。

数据类承载跨模块传递的元数据；Protocol 定义 plugin 需要满足的最小接口。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:  # pragma: no cover
    from sqlalchemy.orm import Session

    from ...models import User, WorkflowRun, WorkflowStep
    from ..stage_contracts import StageContract


# ---------- Node ----------


def node_config_of(node: dict) -> dict:
    """R4.1：节点参数合并的唯一语义——schema v2 以 config 为真源（优先），v1 沿用 params。

    放在 contracts（无依赖模块）供 start_run / preflight_workflow / _is_target_agnostic
    等所有读节点配置的路径共用，杜绝「preflight 读 config、执行读 params」类契约分裂。
    """
    return {**(node.get("params") or {}), **(node.get("config") or {})}


@dataclass
class PluginDescriptor:
    """registry 中一个 plugin 的描述（node/rule/renderer/publisher/asset_provider/material_search/skill_runtime）。"""

    kind: str
    key: str
    version: str
    label: str | None = None
    human_gate: bool = False
    side_effect: bool = False  # 远端副作用 plugin：禁止泛化 rerun（Phase 6 生效）
    stage_contract: StageContract | None = None


@dataclass
class WorkflowExecutionContext:
    """节点执行上下文：引擎在 resolve 出 plugin 后构造，wrapper 借此复用既有 handler。"""

    db: Session
    run: WorkflowRun
    step: WorkflowStep
    config: dict = field(default_factory=dict)

    @property
    def params(self) -> dict:
        return self.step.params_json or {}

    @property
    def context(self) -> dict:
        return self.run.context_json or {}


@dataclass
class NodeResult:
    output: dict = field(default_factory=dict)


class NodePlugin(Protocol):
    """工作流节点插件（D6）。human 节点另需实现 complete()。"""

    key: str
    version: str
    human_gate: bool

    def execute(self, db: Session, ctx: WorkflowExecutionContext, config: dict, user: User) -> NodeResult: ...


# ---------- Rule / Render / Publisher / Material / Skill ----------


@dataclass
class RuleResult:
    key: str
    version: str
    status: str  # pass / warning / blocker / incomplete
    details: dict = field(default_factory=dict)


@dataclass
class RenderResult:
    renderer_key: str
    version: str
    payload: dict = field(default_factory=dict)
    content_hash: str | None = None
    warnings: list[str] = field(default_factory=list)


@dataclass
class PublisherCapability:
    publisher_key: str
    channel: str
    content_form: str
    action: str  # copy_package / assisted_draft / auto_draft
    available: bool
    reason: str | None = None  # 不可用时必填，如 unverified / account_not_authorized


@dataclass
class PublisherResult:
    status: str  # succeeded / failed / unknown
    remote_id: str | None = None
    metadata: dict = field(default_factory=dict)  # 只存安全 metadata，禁止 token/cookie
    error: str | None = None


@dataclass
class MaterialSearchResult:
    provider_key: str
    items: list[dict] = field(default_factory=list)  # {source_url, preview_url, width, height, license...}


@dataclass
class SkillExecutionResult:
    status: str  # succeeded / failed / unavailable
    output: dict = field(default_factory=dict)
    error: str | None = None
