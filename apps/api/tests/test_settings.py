"""系统配置总览 API 测试：脱敏回显。"""

import pytest

from app import runtime_config
from app.config import get_settings
from app.services.generation.providers import (
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


def test_get_settings_masks_secrets(client, seed_users, reset_runtime_config):
    resp = client.get("/api/v1/settings", headers=ADMIN)
    assert resp.status_code == 200
    body = resp.json()
    # 模型厂商与密钥只在 AI 与模型 里配置，这个总览不再带模型配置
    assert "llm" not in body and "image" not in body and "dsh" not in body
    # 连接串只隐藏凭据，其余保留
    assert body["database"]["url"].startswith("sqlite")
    assert body["queue"]["queues"] == ["default", "llm", "ingestion", "export"]
    assert body["security"]["ssrf_allow_private"] is False


