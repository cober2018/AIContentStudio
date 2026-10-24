"""配图素材库 / HTML 导出 / 技能目录配置 / dsh 集成 测试。"""


import pytest

from app import runtime_config
from app.models import ContentAsset
from app.services.dsh_integration import apply_default_model, snapshot, studio_view
from app.services.plugin_registry import scan_skills

ADMIN = {"X-Studio-User": "admin@studio.local"}
EDITOR = {"X-Studio-User": "editor@studio.local"}


@pytest.fixture
def seed_users(db_session):
    from app.models import User

    db_session.add(User(email="admin@studio.local", name="Admin", role="admin"))
    db_session.add(User(email="editor@studio.local", name="Editor", role="editor"))
    db_session.commit()


def _asset(db_session, channel="xiaohongshu", structured=None) -> ContentAsset:
    asset = ContentAsset(
        draft_id=0, topic_brief_id=0, channel=channel, title="测试文章标题",
        final_body="正文", structured_json=structured or {},
        fact_pack_id=1, fact_pack_version=1, approved_revision=1, reviewer="r@x",
    )
    db_session.add(asset)
    db_session.commit()
    return asset


# ---------- 配图素材 ----------


# ---------- HTML 导出 ----------


# ---------- 技能扫描目录可配置 ----------


def test_plugins_skill_dirs_custom(client, seed_users, tmp_path, reset_runtime_plugins):
    skill = tmp_path / "custom-skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text("---\nname: custom-skill\ndescription: 自定义目录技能\n---\n", encoding="utf-8")
    resp = client.put(
        "/api/v1/settings/plugins", headers=ADMIN,
        json={"skill_dirs": [str(tmp_path)], "skills_enabled": [], "mcp": []},
    )
    assert resp.status_code == 200
    body = resp.json()
    names = [s["name"] for s in body["skills"]]
    # 并集语义：默认目录 + 自定义目录都生效
    assert "custom-skill" in names
    assert len(names) > 1  # 默认目录技能仍在
    assert body["skill_dirs"] == [str(tmp_path)]


def test_plugins_skill_dirs_missing_rejected(client, seed_users, reset_runtime_plugins):
    resp = client.put(
        "/api/v1/settings/plugins", headers=ADMIN,
        json={"skill_dirs": ["/nonexistent-dir-xyz"], "skills_enabled": [], "mcp": []},
    )
    assert resp.status_code == 422


@pytest.fixture
def reset_runtime_plugins():
    yield
    runtime_config.clear_all()


def test_scan_skills_custom_dir(tmp_path):
    (tmp_path / "s1").mkdir()
    (tmp_path / "s1" / "SKILL.md").write_text("---\nname: s1\ndescription: d\n---\n", encoding="utf-8")
    assert [s["name"] for s in scan_skills([tmp_path])] == ["s1"]


# ---------- dsh 集成 ----------


def test_dsh_snapshot_reads_user_settings():
    snap = snapshot()
    assert snap["configured"] in (True, False)  # 本机有 ~/.dsh 则 True
    assert "providers" in snap and "env_keys" in snap
    view = studio_view(None)
    assert view["config"]["default_provider"] == "minimax"


def test_dsh_apply_default_model(tmp_path):
    home = tmp_path / ".dsh"
    home.mkdir()
    (home / "settings.yaml").write_text(
        "# 注释保留测试\nllm-pi-ai:\n  providers: {}\nagent-default-model:\n"
        "  provider: minimax\n  model: MiniMax-M3\n",
        encoding="utf-8",
    )
    result = apply_default_model("deepseek", "deepseek-chat", dsh_home=home)
    assert result["ok"] is True
    text = (home / "settings.yaml").read_text(encoding="utf-8")
    assert "provider: deepseek" in text and "model: deepseek-chat" in text
    assert "# 注释保留测试" in text  # 注释未被 yaml 重写破坏
    assert list(home.glob("settings.yaml.bak-*"))  # 有备份


def test_dsh_apply_rejects_unexpected_structure(tmp_path):
    home = tmp_path / ".dsh"
    home.mkdir()
    (home / "settings.yaml").write_text("other: config\n", encoding="utf-8")
    result = apply_default_model("deepseek", "deepseek-chat", dsh_home=home)
    assert result["ok"] is False


def test_dsh_put_requires_admin(client, seed_users):
    resp = client.put("/api/v1/settings/dsh", headers={"X-Studio-User": "editor@studio.local"}, json={})
    assert resp.status_code == 403
