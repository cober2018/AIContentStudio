"""系统配置管理页 API 测试：脱敏回显 / RBAC / 运行时覆盖生效与回落。"""

import pytest

from app import runtime_config
from app.config import get_settings
from app.services.generation.providers import (
    OpenAICompatibleProvider,
    effective_llm_config,
    get_provider,
    provider_model_name,
    reset_provider_cache,
)

ADMIN = {"X-Studio-User": "admin@studio.local"}
EDITOR = {"X-Studio-User": "editor@studio.local"}


@pytest.fixture
def seed_users(db_session):
    """内存库无种子用户：admin 不会自动建号（默认角色是 editor），需显式种入。"""
    from app.models import User

    db_session.add(User(email="admin@studio.local", name="Admin", role="admin"))
    db_session.add(User(email="editor@studio.local", name="Editor", role="editor"))
    db_session.commit()


@pytest.fixture
def reset_runtime_config():
    """settings API 会改进程级缓存，测试后必须复位，避免污染其他用例。"""
    yield
    runtime_config.clear_all()
    reset_provider_cache()
    get_settings.cache_clear()


def test_get_settings_masks_secrets(client, seed_users, monkeypatch, reset_runtime_config):
    monkeypatch.setenv("LLM_API_KEY", "sk-secret-abcd1234")
    get_settings.cache_clear()
    resp = client.get("/api/v1/settings", headers=ADMIN)
    assert resp.status_code == 200
    body = resp.json()
    # 已配置内容必须展示（用户核心诉求），但密钥只能看到掩码
    assert body["llm"]["api_key"]["configured"] is True
    assert "1234" in body["llm"]["api_key"]["masked"]
    assert "sk-secret-abcd1234" not in resp.text
    assert body["llm"]["provider"] == "mock"
    assert body["llm"]["overridden"] is False
    # 连接串只隐藏凭据，其余保留
    assert body["database"]["url"].startswith("sqlite")
    assert body["queue"]["queues"] == ["default", "llm", "ingestion", "export"]
    assert body["security"]["ssrf_allow_private"] is False


def test_put_llm_requires_admin(client, seed_users, reset_runtime_config):
    resp = client.put(
        "/api/v1/settings/llm",
        headers=EDITOR,
        json={"provider": "openai_compatible", "base_url": "https://api.x.com/v1", "model": "m1", "api_key": "k"},
    )
    assert resp.status_code == 403


def test_put_llm_openai_compatible_requires_fields(client, seed_users, reset_runtime_config):
    resp = client.put("/api/v1/settings/llm", headers=ADMIN, json={"provider": "openai_compatible"})
    assert resp.status_code == 422


def test_put_llm_override_takes_effect(client, seed_users, reset_runtime_config):
    payload = {
        "provider": "openai_compatible",
        "base_url": "https://api.minimax.example/v1",
        "model": "abab-test",
        "api_key": "sk-override-9876",
    }
    resp = client.put("/api/v1/settings/llm", headers=ADMIN, json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["provider"] == "openai_compatible"
    assert body["overridden"] is True
    assert body["api_key"]["configured"] is True
    assert "sk-override-9876" not in resp.text  # 回显脱敏

    # 生效配置与 provider 实例都切到覆盖值
    config = effective_llm_config()
    assert config["provider"] == "openai_compatible"
    assert config["model"] == "abab-test"
    provider = get_provider()
    assert isinstance(provider, OpenAICompatibleProvider)
    assert provider.model == "abab-test"
    assert provider_model_name() == "abab-test"


def test_put_llm_keeps_existing_api_key_when_blank(client, seed_users, reset_runtime_config):
    first = {
        "provider": "openai_compatible",
        "base_url": "https://api.x.com/v1",
        "model": "m1",
        "api_key": "sk-keep-1122",
    }
    assert client.put("/api/v1/settings/llm", headers=ADMIN, json=first).status_code == 200
    # 只改模型名，api_key 留空 → 保持原值
    resp = client.put(
        "/api/v1/settings/llm",
        headers=ADMIN,
        json={"provider": "openai_compatible", "base_url": "https://api.x.com/v1", "model": "m2", "api_key": ""},
    )
    assert resp.status_code == 200
    assert effective_llm_config()["api_key"] == "sk-keep-1122"
    assert effective_llm_config()["model"] == "m2"


def test_delete_llm_override_falls_back_to_env(client, seed_users, monkeypatch, reset_runtime_config):
    payload = {
        "provider": "openai_compatible",
        "base_url": "https://api.x.com/v1",
        "model": "m1",
        "api_key": "k",
    }
    assert client.put("/api/v1/settings/llm", headers=ADMIN, json=payload).status_code == 200
    resp = client.delete("/api/v1/settings/llm", headers=ADMIN)
    assert resp.status_code == 200
    assert resp.json()["provider"] == "mock"
    assert resp.json()["overridden"] is False
    assert get_provider().name == "mock"


def test_delete_llm_override_requires_admin(client, seed_users, reset_runtime_config):
    resp = client.delete("/api/v1/settings/llm", headers=EDITOR)
    assert resp.status_code == 403


def test_llm_connection_test_mock(client, seed_users, reset_runtime_config):
    resp = client.post("/api/v1/settings/llm/test", headers=ADMIN, json={"provider": "mock"})
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_llm_connection_test_bad_endpoint_reports_error(client, seed_users, reset_runtime_config):
    payload = {
        "provider": "openai_compatible",
        "base_url": "http://localhost:9",
        "model": "m",
        "api_key": "k",
    }
    resp = client.post("/api/v1/settings/llm/test", headers=ADMIN, json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is False
    assert body["error"]


def test_mock_inject_switch_via_override(client, seed_users, db_session, reset_runtime_config):
    """设置页可切换 mock 注入无源数字，无需重启/改 env。"""
    resp = client.put(
        "/api/v1/settings/llm",
        headers=ADMIN,
        json={"provider": "mock", "mock_inject_unfact_number": True},
    )
    assert resp.status_code == 200
    assert resp.json()["mock_inject_unfact_number"] is True
    assert effective_llm_config()["mock_inject_unfact_number"] is True
