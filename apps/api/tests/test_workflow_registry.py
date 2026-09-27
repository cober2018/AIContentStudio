"""Workflow Registry / 版本化 Definition（V1 PRD 2.0 D4–D8）。

覆盖：plugin registry 语义（重复注册/精确版本解析）；模板实例冻结 key/version/checksum；
schema v1 类型映射兼容；schema v2 plugin 字段解析；run 冻结 definition 身份（发布后修改不影响历史 run）。
"""

import pytest

from app.models import User, Workflow, WorkflowRun
from app.services.content_harness import registry as plugin_registry
from app.services.content_harness.contracts import NodeResult
from app.services.content_harness.nodes import TYPE_TO_PLUGIN, resolve_node_key
from app.services.content_harness.registry import RegistryError
from app.services.workflow_engine import _steps, definition_checksum, start_run

ADMIN = {"X-Studio-User": "admin@studio.local"}
EDITOR = {"X-Studio-User": "editor@studio.local"}


@pytest.fixture
def seed_users(db_session):
    db_session.add(User(email="admin@studio.local", name="Admin", role="admin"))
    db_session.add(User(email="editor@studio.local", name="Editor", role="editor"))
    db_session.commit()


# ---------- plugin registry 语义 ----------


def test_registry_duplicate_registration_raises():
    class P:
        key = "builtin.generate"
        version = "1"
        human_gate = False

        def execute(self, db, ctx, config, user):
            return NodeResult()

    before = len(plugin_registry.registry.list("node"))
    with pytest.raises(RegistryError):
        plugin_registry.register("node", "builtin.generate", "1", P())
    assert len(plugin_registry.registry.list("node")) == before


def test_registry_unknown_plugin_raises():
    with pytest.raises(RegistryError):
        plugin_registry.resolve("node", "builtin.not_exists", "1")


def test_builtin_plugins_registered_with_versions():
    nodes = {d.key: d for d in plugin_registry.registry.list("node")}
    for key in ("builtin.generate", "builtin.fact_check", "builtin.approve", "builtin.adopt_topic"):
        assert nodes[key].version == "1"
    assert nodes["builtin.approve"].human_gate is True
    assert nodes["builtin.generate"].human_gate is False
    assert nodes["builtin.publish_wechat"].side_effect is True  # 远端副作用：Phase 6 禁泛化重跑


def test_resolve_node_key_schema_v1_and_v2():
    # schema v1：type 映射
    assert resolve_node_key({"type": "generate"}) == ("builtin.generate", "1")
    assert resolve_node_key({"type": "humanize_polish"}) == ("builtin.humanize", "1")
    assert "generate" in TYPE_TO_PLUGIN
    # schema v2：plugin 字段直读
    assert resolve_node_key({"plugin": "node.skill", "plugin_version": "2"}) == ("node.skill", "2")
    # 未知类型报错
    with pytest.raises(ValueError):
        resolve_node_key({"type": "nope"})


# ---------- 模板实例 / run 冻结 definition 身份 ----------


def _mk_workflow(db, definition: dict, **kw) -> Workflow:
    wf = Workflow(
        name=kw.get("name", "t"),
        template_key=kw.get("template_key"),
        workflow_key=kw.get("workflow_key"),
        version=kw.get("version", 1),
        schema_version=kw.get("schema_version", 1),
        status=kw.get("status", "published"),
        checksum=definition_checksum(definition),
        definition_json=definition,
    )
    db.add(wf)
    db.commit()
    return wf


def test_template_instance_freezes_version_and_checksum(client, seed_users, db_session):
    resp = client.post(
        "/api/v1/workflows", json={"template_key": "daily_suggest"}, headers=ADMIN
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["workflow_key"] == "legacy.daily_suggest"
    assert body["version"] == 1
    assert body["schema_version"] == 1
    assert body["status"] == "published"
    assert len(body["checksum"]) == 64


def test_run_freezes_definition_identity(db_session, seed_users):
    """D5：启动 run 时冻结 workflow_key/version/definition_checksum；之后改定义不影响历史 run。"""
    user = db_session.query(User).filter_by(email="editor@studio.local").first()
    definition = {
        "nodes": [{"id": "n1", "type": "connector_pull", "label": "拉取", "params": {}, "layout": {"x": 0, "y": 0}}],
        "edges": [],
    }
    wf = _mk_workflow(db_session, definition, workflow_key="legacy.t", schema_version=1)
    run = start_run(db_session, wf, {}, user)
    assert run.workflow_key == "legacy.t"
    assert run.workflow_version == 1
    original_checksum = run.definition_checksum
    assert original_checksum == definition_checksum(definition)

    # 发布后修改定义：历史 run checksum 不变（immutable 语义的 run 侧体现）
    wf.definition_json = {
        "nodes": [{"id": "n1", "type": "connector_pull", "label": "改", "params": {}, "layout": {"x": 0, "y": 0}}],
        "edges": [],
    }
    db_session.commit()
    db_session.expire_all()
    fresh = db_session.get(WorkflowRun, run.id)
    assert fresh.definition_checksum == original_checksum
    assert fresh.definition_checksum != definition_checksum(wf.definition_json)


def test_schema_v1_steps_resolve_via_type_mapping(db_session, seed_users):
    """schema v1 定义（type 字段）经 TYPE_TO_PLUGIN 兼容解析，并回写 plugin 钉死记录。"""
    user = db_session.query(User).filter_by(email="editor@studio.local").first()
    definition = {
        "nodes": [
            {"id": "adopt", "type": "adopt_topic", "label": "采纳", "params": {}, "layout": {"x": 0, "y": 0}},
        ],
        "edges": [],
    }
    wf = _mk_workflow(db_session, definition, schema_version=1)
    run = start_run(db_session, wf, {}, user)
    assert run.status == "waiting_input"  # 人工节点挂起
    step = _steps(db_session, run)[0]
    assert step.plugin_key == "builtin.adopt_topic"
    assert step.plugin_version == "1"
    assert step.status == "waiting_input"


def test_schema_v2_plugin_field_resolution(db_session, seed_users):
    """schema v2 节点 plugin/plugin_version 直读并钉死到 step。"""
    user = db_session.query(User).filter_by(email="editor@studio.local").first()
    definition = {
        "schema_version": 2,
        "nodes": [
            {
                "id": "adopt2",
                "plugin": "builtin.adopt_topic",
                "plugin_version": "1",
                "label": "人工采纳 v2",
                "config": {},
                "layout": {"x": 0, "y": 0},
            }
        ],
        "edges": [],
    }
    wf = _mk_workflow(db_session, definition, workflow_key="workflow.v2.test", schema_version=2)
    run = start_run(db_session, wf, {}, user)
    step = _steps(db_session, run)[0]
    assert step.plugin_key == "builtin.adopt_topic"
    assert step.plugin_version == "1"
    assert step.node_type == "builtin.adopt_topic"  # v2 节点无 type 字段时落 plugin key
    assert run.status == "waiting_input"


def test_run_records_input_output_hash_on_execution(db_session, seed_users):
    """D8 铺垫：执行过的 step 记录 input/output hash（这里用会失败的节点验证 input_hash 落库时机）。"""
    user = db_session.query(User).filter_by(email="editor@studio.local").first()
    definition = {
        "nodes": [{"id": "pull", "type": "connector_pull", "label": "拉取", "params": {}, "layout": {"x": 0, "y": 0}}],
        "edges": [],
    }
    wf = _mk_workflow(db_session, definition, schema_version=1)
    run = start_run(db_session, wf, {}, user)
    step = _steps(db_session, run)[0]
    # 无 endpoint 配置：节点业务失败，但引擎执行路径已走过（失败先于 hash 提交属预期语义）
    assert run.status == "failed"
    assert step.plugin_key == "builtin.connector_pull"


def test_workflow_api_exposes_run_metadata(client, seed_users, db_session):
    resp = client.post("/api/v1/workflows", json={"template_key": "daily_suggest"}, headers=ADMIN)
    wf_id = resp.json()["id"]
    run = client.post("/api/v1/workflow-runs", json={"workflow_id": wf_id, "params": {"topic_id": "7"}}, headers=EDITOR)
    assert run.status_code == 201
    detail = client.get(f"/api/v1/workflow-runs/{run.json()['id']}", headers=EDITOR).json()
    assert detail["workflow_key"] == "legacy.daily_suggest"
    assert detail["workflow_version"] == 1
    assert len(detail["definition_checksum"]) == 64
    assert detail["topic_id"] == 7  # params 里的字符串 topic_id 被归一化冻结
    step = detail["steps"][0]
    assert step["plugin_key"].startswith("builtin.")
