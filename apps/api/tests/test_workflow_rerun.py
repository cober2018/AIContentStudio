"""Node Rerun（V1 PRD 2.0 / capability: workflow-rerun-staleness）。

覆盖：rerun 不重置上游；output 变化 → downstream stale（不自动重跑）；
rerun-from-here 重置当前+下游；副作用节点泛化重跑被拒（API 409）。
"""

import pytest

from app.models import User, Workflow
from app.services.content_harness import registry as plugin_registry
from app.services.content_harness.contracts import NodeResult
from app.services.content_harness.registry import RegistryError
from app.services.workflow_engine import _steps, definition_checksum, rerun_from_here, rerun_node, start_run


class CounterPlugin:
    """每次执行输出递增：用于验证 rerun 产生新 output。"""

    key = "test.counter"
    version = "1"
    human_gate = False
    side_effect = False
    calls = 0

    def execute(self, db, ctx, config, user):
        CounterPlugin.calls += 1
        return NodeResult(output={"n": CounterPlugin.calls, "node": ctx.step.node_id})


class FixedPlugin:
    key = "test.fixed"
    version = "1"
    human_gate = False
    side_effect = False

    def execute(self, db, ctx, config, user):
        return NodeResult(output={"fixed": True, "node": ctx.step.node_id})


class SideEffectPlugin:
    key = "test.publisher_side_effect"
    version = "1"
    human_gate = False
    side_effect = True

    def execute(self, db, ctx, config, user):
        return NodeResult(output={"sent": True})


@pytest.fixture
def plugins():
    for plugin in (CounterPlugin(), FixedPlugin(), SideEffectPlugin()):
        try:
            plugin_registry.register("node", plugin.key, plugin.version, plugin, side_effect=plugin.side_effect)
        except RegistryError:
            pass
        # 重复注册容错：类属性共享，无需重新注册
    CounterPlugin.calls = 0


@pytest.fixture
def wf(db_session):
    definition = {
        "nodes": [
            {"id": "a", "plugin": "test.counter", "plugin_version": "1", "label": "A", "config": {}, "layout": {"x": 0, "y": 0}},
            {"id": "b", "plugin": "test.fixed", "plugin_version": "1", "label": "B", "config": {}, "layout": {"x": 1, "y": 0}},
            {"id": "c", "plugin": "test.counter", "plugin_version": "1", "label": "C", "config": {}, "layout": {"x": 2, "y": 0}},
        ],
        "edges": [{"from": "a", "to": "b"}, {"from": "b", "to": "c"}],
    }
    row = Workflow(
        name="rerun", workflow_key="workflow.rerun.test", version=1, schema_version=2, status="published",
        checksum=definition_checksum(definition), definition_json=definition,
    )
    db_session.add(row)
    db_session.commit()
    return row


@pytest.fixture
def user(db_session):
    row = User(email="editor@studio.local", name="E", role="editor")
    db_session.add(row)
    db_session.commit()
    return row


def test_rerun_changes_output_and_marks_downstream_stale(db_session, wf, user, plugins):
    run = start_run(db_session, wf, {}, user)
    assert run.status == "succeeded"
    by_node = {s.node_id: s for s in _steps(db_session, run)}
    old_n = by_node["a"].output_json["n"]

    rerun_node(db_session, run, "a", user)
    db_session.expire_all()
    by_node = {s.node_id: s for s in _steps(db_session, run)}
    assert by_node["a"].status == "succeeded"
    assert by_node["a"].attempt_no == 2  # R2-H7：初次执行=attempt 1（审计行），rerun 后=2
    assert by_node["a"].output_json["n"] > old_n  # 新 output 可审计（旧 output 在历史 commit 中）
    # output 变化 → 下游 stale
    assert by_node["b"].status == "stale"
    assert "upstream a" in by_node["b"].stale_reason
    assert by_node["c"].status == "stale"


def test_rerun_same_output_keeps_downstream(db_session, wf, user, plugins):
    run = start_run(db_session, wf, {}, user)
    rerun_node(db_session, run, "b", user)  # fixed 输出不变
    db_session.expire_all()
    by_node = {s.node_id: s for s in _steps(db_session, run)}
    assert by_node["b"].status == "succeeded"
    assert by_node["c"].status == "succeeded"  # output 未变 → downstream 不 stale


def test_rerun_from_here_resets_current_and_downstream(db_session, wf, user, plugins):
    run = start_run(db_session, wf, {}, user)
    rerun_from_here(db_session, run, "b", user)
    db_session.expire_all()
    by_node = {s.node_id: s for s in _steps(db_session, run)}
    assert by_node["a"].status == "succeeded"  # 上游不重置
    assert by_node["b"].status in {"pending", "succeeded"}  # 重置后立即推进
    assert by_node["c"].status in {"pending", "succeeded"}


def test_side_effect_node_rerun_rejected(db_session, wf, user, plugins):
    """Publisher/远端副作用节点：泛化 rerun API MUST reject。"""
    run = start_run(db_session, wf, {}, user)
    from app.models import WorkflowStep

    step = WorkflowStep(run_id=run.id, node_id="pub", node_type="test.publisher_side_effect", label="pub",
                        params_json={}, plugin_key="test.publisher_side_effect", plugin_version="1", status="succeeded")
    db_session.add(step)
    db_session.commit()
    with pytest.raises(ValueError, match="副作用"):
        rerun_node(db_session, run, "pub", user)


def test_rerun_from_here_rejected_when_downstream_has_side_effect(db_session, user, plugins):
    """rerun-from-here 波及图中的副作用节点同样被拒。"""
    definition = {
        "nodes": [
            {"id": "a", "plugin": "test.counter", "plugin_version": "1", "label": "A", "config": {}, "layout": {"x": 0, "y": 0}},
            {"id": "pub", "plugin": "test.publisher_side_effect", "plugin_version": "1", "label": "PUB", "config": {}, "layout": {"x": 1, "y": 0}},
        ],
        "edges": [{"from": "a", "to": "pub"}],
    }
    row = Workflow(
        name="rerun2", workflow_key="workflow.rerun.test2", version=1, schema_version=2, status="published",
        checksum=definition_checksum(definition), definition_json=definition,
    )
    db_session.add(row)
    db_session.commit()
    run = start_run(db_session, row, {}, user)
    with pytest.raises(ValueError, match="副作用"):
        rerun_from_here(db_session, run, "a", user)


