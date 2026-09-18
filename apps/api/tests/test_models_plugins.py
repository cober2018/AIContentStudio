"""多模型 Profiles + 场景路由 + 技能插件登记 测试。"""

import pytest

from app import runtime_config
from app.services.generation.providers import (
    effective_llm_config,
    reset_provider_cache,
)
from app.services.plugin_registry import scan_skills

ADMIN = {"X-Studio-User": "admin@studio.local"}
EDITOR = {"X-Studio-User": "editor@studio.local"}


@pytest.fixture
def seed_users(db_session):
    from app.models import User

    db_session.add(User(email="admin@studio.local", name="Admin", role="admin"))
    db_session.add(User(email="editor@studio.local", name="Editor", role="editor"))
    db_session.commit()


@pytest.fixture
def reset_runtime():
    yield
    runtime_config.clear_all()
    reset_provider_cache()


def _put_models(client, **overrides):
    payload = {
        "profiles": [
            {"name": "minimax", "provider": "openai_compatible", "base_url": "https://api.minimax.cn/v1",
             "model": "MiniMax-M3", "api_key": "sk-mm-1111"},
            {"name": "deepseek", "provider": "openai_compatible", "base_url": "https://api.deepseek.com/v1",
             "model": "deepseek-chat", "api_key": "sk-ds-2222"},
        ],
        "routes": {"generate": "minimax", "fact_check": "deepseek"},
    }
    payload.update(overrides)
    return client.put("/api/v1/settings/models", headers=ADMIN, json=payload)


def test_models_profiles_masked_and_routed(client, seed_users, reset_runtime):
    resp = _put_models(client)
    assert resp.status_code == 200
    body = resp.json()
    assert body["profiles"]["minimax"]["api_key"]["configured"] is True
    assert "sk-mm-1111" not in resp.text  # 明文永不回显
    assert body["routes"]["generate"] == "minimax"
    assert body["routes"]["fact_check"] == "deepseek"

    # 场景路由生效：生成走 minimax，校验走 deepseek；无 purpose 走默认（env mock）
    assert effective_llm_config("generate")["model"] == "MiniMax-M3"
    assert effective_llm_config("fact_check")["model"] == "deepseek-chat"
    assert effective_llm_config()["provider"] == "mock"


def test_models_disabled_profile_not_routed(client, seed_users, reset_runtime):
    """enabled=False 的 Profile 不参与路由，回落默认。"""
    resp = _put_models(client)
    assert resp.status_code == 200
    assert effective_llm_config("fact_check")["model"] == "deepseek-chat"
    # 关掉 deepseek
    payload = {
        "profiles": [
            {"name": "minimax", "provider": "openai_compatible", "base_url": "https://x/v1", "model": "m", "api_key": "k"},
            {"name": "deepseek", "provider": "mock", "enabled": False},
        ],
        "routes": {"generate": "minimax", "fact_check": "deepseek"},
    }
    resp = client.put("/api/v1/settings/models", headers=ADMIN, json=payload)
    assert resp.status_code == 200
    cfg = effective_llm_config("fact_check")
    assert cfg["profile"] == "default"  # disabled → 回落默认
    assert cfg["provider"] == "mock"


def test_models_route_to_missing_profile_rejected(client, seed_users, reset_runtime):
    resp = _put_models(client, routes={"generate": "ghost"})
    assert resp.status_code == 422


def test_models_requires_admin(client, seed_users, reset_runtime):
    resp = client.put("/api/v1/settings/models", headers=EDITOR, json={"profiles": [], "routes": {}})
    assert resp.status_code == 403


def test_models_api_key_blank_keeps_existing(client, seed_users, reset_runtime):
    assert _put_models(client).status_code == 200
    # 只改模型名，key 留空 → 保持 sk-mm-1111
    payload = {
        "profiles": [
            {"name": "minimax", "provider": "openai_compatible", "base_url": "https://api.minimax.cn/v1",
             "model": "MiniMax-M4", "api_key": ""},
        ],
        "routes": {"generate": "minimax"},
    }
    resp = client.put("/api/v1/settings/models", headers=ADMIN, json=payload)
    assert resp.status_code == 200
    assert effective_llm_config("generate")["api_key"] == "sk-mm-1111"
    assert effective_llm_config("generate")["model"] == "MiniMax-M4"


def test_plugins_put_and_view(client, seed_users, reset_runtime):
    resp = client.put(
        "/api/v1/settings/plugins",
        headers=ADMIN,
        json={"skills_enabled": ["wewrite-write"], "mcp": [{"name": "browser", "url": "http://localhost:9222"}]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "wewrite-write" in body["skills_enabled"]
    assert body["mcp"][0]["name"] == "browser"
    # 自动发现的技能列表在视图里（本机 .agents/.zcode skills）
    assert len(body["skills"]) > 0


def test_plugins_unknown_skill_rejected(client, seed_users, reset_runtime):
    resp = client.put(
        "/api/v1/settings/plugins", headers=ADMIN, json={"skills_enabled": ["no-such-skill"]}
    )
    assert resp.status_code == 422


def test_scan_skills_reads_frontmatter(tmp_path):
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: my-skill\ndescription: 用于测试的技能\n---\n# body", encoding="utf-8"
    )
    (tmp_path / "empty-dir").mkdir()  # 无 SKILL.md 应跳过
    skills = scan_skills([tmp_path])
    assert len(skills) == 1
    assert skills[0]["name"] == "my-skill"
    assert skills[0]["description"] == "用于测试的技能"
