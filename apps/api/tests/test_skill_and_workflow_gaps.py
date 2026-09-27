"""验收补缺测试：D16 plugin 元数据、D17 skill_runtime preflight、D4 workflow clone/publish。"""


from app.models import User, Workflow
from app.services.plugin_registry import scan_skills, skill_descriptor
from app.services.workflow_engine import definition_checksum

ADMIN = {"X-Studio-User": "admin@studio.local"}
EDITOR = {"X-Studio-User": "editor@studio.local"}


# ---------- D16：plugin_registry frontmatter 元数据 ----------


def test_scan_skills_parses_extended_frontmatter(tmp_path):
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: studio-xueqiu-article\n"
        "description: 雪球量化写作\n"
        "version: 1.0.0\n"
        "license: MIT\n"
        "kind: skill\n"
        "capabilities: writing, finance\n"
        "---\n\n正文不应被当作系统指令消费。\n",
        encoding="utf-8",
    )
    skills = scan_skills((tmp_path,))
    assert len(skills) == 1
    s = skills[0]
    assert s["name"] == "studio-xueqiu-article"
    assert s["version"] == "1.0.0"
    assert s["license"] == "MIT"
    assert s["kind"] == "skill"
    assert s["capabilities"] == ["writing", "finance"]
    assert skill_descriptor("studio-xueqiu-article", (tmp_path,))["version"] == "1.0.0"


def test_scan_skills_defaults_for_legacy_frontmatter(tmp_path):
    skill_dir = tmp_path / "old-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: old-skill\ndescription: 旧技能\n---\n正文", encoding="utf-8")
    s = scan_skills((tmp_path,))[0]
    assert s["version"] == "unversioned"
    assert s["license"] == "unknown"
    assert s["kind"] == "skill"
    assert s["capabilities"] == []


# ---------- D17：skill_runtime preflight ----------


def test_preflight_detects_missing_and_version_mismatch(tmp_path, monkeypatch):
    from app.services.content_harness import skill_runtime

    installed = tmp_path / "s1"
    installed.mkdir()
    (installed / "SKILL.md").write_text(
        "---\nname: skill-a\nversion: 2.0.0\n---\n正文", encoding="utf-8"
    )
    import app.services.plugin_registry as pr

    monkeypatch.setattr(pr, "scan_skills", lambda dirs=None: scan_skills((tmp_path,)))

    definition = {
        "nodes": [
            {"id": "n1", "plugin": "node.skill", "config": {"skill": "skill-a", "skill_version": "2.0.0"}},
            {"id": "n2", "plugin": "node.skill", "config": {"skill": "skill-missing"}},
            {"id": "n3", "plugin": "node.skill", "config": {"skill": "skill-a", "skill_version": "1.0.0"}},
        ],
        "edges": [],
    }
    problems = skill_runtime.preflight_workflow(None, definition)
    assert any("not installed" in p and "skill-missing" in p for p in problems)
    assert any("version mismatch" in p and "skill-a" in p for p in problems)
    assert not any("n1" in p for p in problems)  # 匹配版本无问题

    ok = {"nodes": [{"id": "n1", "plugin": "node.skill", "config": {"skill": "skill-a"}}], "edges": []}
    problems = skill_runtime.preflight_workflow(None, ok)
    # R2-H5：无「可执行」runtime（内置 runtime 只如实报 unavailable）→ 启动前拒绝
    assert any("无可执行 SkillRuntime" in p for p in problems)

    # 注册一个非内置 runtime 后放行
    from app.services.content_harness.registry import registry as reg

    class _Runtime:
        key = "skill_runtime.fake"
        version = "1"

        def execute(self, skill, payload, timeout_sec):
            from app.services.content_harness.contracts import SkillExecutionResult

            return SkillExecutionResult(status="succeeded", output={})

    reg.register("skill_runtime", "skill_runtime.fake", "1", _Runtime())
    try:
        assert skill_runtime.preflight_workflow(None, ok) == []
    finally:
        reg._items.pop(("skill_runtime", "skill_runtime.fake", "1"), None)
        reg._descriptors.pop(("skill_runtime", "skill_runtime.fake", "1"), None)


def test_preflight_blocks_start_run(client, db_session):
    """preflight 失败 → 创建 run 被拒（启动前而非运行中）。"""
    db_session.add(User(email="admin@studio.local", name="A", role="admin"))

    definition = {
        "nodes": [{"id": "w", "plugin": "node.skill", "config": {"skill": "definitely-not-installed-skill"}}],
        "edges": [],
    }
    wf = Workflow(
        name="skill wf", workflow_key="workflow.skill.test", version=1, schema_version=2, status="published",
        checksum=definition_checksum(definition), definition_json=definition,
    )
    db_session.add(wf)
    db_session.commit()
    resp = client.post("/api/v1/workflow-runs", json={"workflow_id": wf.id, "params": {}}, headers=EDITOR)
    assert resp.status_code == 409
    assert "preflight" in resp.json()["detail"]
    assert "definitely-not-installed-skill" in resp.json()["detail"]


def test_builtin_skill_runtime_reports_unavailable():
    from app.services.content_harness.contracts import SkillExecutionResult
    from app.services.content_harness.registry import registry
    from app.services.content_harness.skill_runtime import bootstrap_skill_runtimes

    bootstrap_skill_runtimes()
    runtime = registry.resolve("skill_runtime", "skill_runtime.builtin", "1")
    result = runtime.execute({"name": "x"}, {}, 5)
    assert isinstance(result, SkillExecutionResult)
    assert result.status == "unavailable"


# ---------- D4：workflow clone / publish immutable ----------


def test_workflow_clone_and_publish_lifecycle(client, db_session):
    db_session.add(User(email="admin@studio.local", name="A", role="admin"))
    definition = {
        "nodes": [{"id": "a", "plugin": "builtin.adopt_topic", "plugin_version": "1", "label": "A", "config": {}, "layout": {"x": 0, "y": 0}}],
        "edges": [],
    }
    source = Workflow(
        name="wf", workflow_key="workflow.clone.test", version=1, schema_version=2, status="published",
        checksum=definition_checksum(definition), definition_json=definition, created_by="admin@studio.local",
    )
    db_session.add(source)
    db_session.commit()

    # published 不可再 publish（immutable）
    again = client.post(f"/api/v1/workflows/{source.id}/publish", headers=ADMIN)
    assert again.status_code == 409
    assert "immutable" in again.json()["detail"]

    # clone → draft v2（parent 指向 source）
    clone = client.post(f"/api/v1/workflows/{source.id}/clone", headers=ADMIN)
    assert clone.status_code == 201, clone.json()
    body = clone.json()
    assert body["version"] == 2
    assert body["status"] == "draft"
    assert body["checksum"] is None

    # draft 修改定义后 publish 冻结 checksum；历史 v1 checksum 不变
    clone_row = db_session.get(Workflow, body["id"])
    clone_row.definition_json = {
        "nodes": [{"id": "a", "plugin": "builtin.adopt_topic", "plugin_version": "1", "label": "改", "config": {}, "layout": {"x": 0, "y": 0}}],
        "edges": [],
    }
    db_session.commit()
    published = client.post(f"/api/v1/workflows/{body['id']}/publish", headers=ADMIN)
    assert published.status_code == 200
    assert published.json()["checksum"] == definition_checksum(clone_row.definition_json)
    assert published.json()["checksum"] != source.checksum
