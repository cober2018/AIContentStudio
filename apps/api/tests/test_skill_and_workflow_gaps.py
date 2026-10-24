"""验收补缺测试：D16 plugin 元数据、D17 skill_runtime preflight、D4 workflow clone/publish。"""


from app.services.plugin_registry import scan_skills, skill_descriptor

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


# ---------- D4：workflow clone / publish immutable ----------


