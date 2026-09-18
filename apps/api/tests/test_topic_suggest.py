"""AI 选题发现（topic_discovery 场景路由）测试。"""

import pytest

from app import runtime_config
from app.services.generation.providers import effective_llm_config, reset_provider_cache

ADMIN = {"X-Studio-User": "admin@studio.local"}
EDITOR = {"X-Studio-User": "editor@studio.local"}


@pytest.fixture
def seed_users(db_session):
    from app.models import User

    db_session.add(User(email="admin@studio.local", name="Admin", role="admin"))
    db_session.add(User(email="editor@studio.local", name="Editor", role="editor"))
    db_session.commit()


@pytest.fixture
def frozen_pack(client, seed_users, db_session):
    """走完整流程建一个 frozen 包：建 Source → 抽取 → 确认 → 建包 → 加条目 → 冻结。"""
    src = client.post(
        "/api/v1/sources/text",
        headers=EDITOR,
        json={
            "title": "测试事实材料",
            "content": "上证指数收涨1.2%，成交额达到9850亿元。科创50指数上涨2.4%。两市超4100只个股上涨。",
            "as_of": "2026-09-18",
        },
    ).json()
    client.post(f"/api/v1/sources/{src['id']}/extract-facts", headers=EDITOR)
    facts = [f for f in client.get("/api/v1/facts?status=candidate", headers=EDITOR).json()]
    assert facts, "抽取应产生候选事实"
    for f in facts:
        client.post(f"/api/v1/facts/{f['id']}/confirm", headers=EDITOR)
    pack = client.post(
        "/api/v1/fact-packs", headers=EDITOR, json={"name": "荐题测试包", "description": ""}
    ).json()
    for f in facts:
        client.post(
            f"/api/v1/fact-packs/{pack['id']}/items", headers=EDITOR, json={"fact_id": f["id"]}
        )
    resp = client.post(f"/api/v1/fact-packs/{pack['id']}/freeze", headers=EDITOR)
    assert resp.status_code == 200, resp.text
    return resp.json()


@pytest.fixture
def reset_runtime():
    yield
    runtime_config.clear_all()
    reset_provider_cache()


def test_suggest_with_mock_returns_candidates(client, seed_users, frozen_pack):
    resp = client.post(
        "/api/v1/topics/suggest", headers=EDITOR, params={"fact_pack_id": frozen_pack["id"], "count": 3}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["fact_pack"]["id"] == frozen_pack["id"]
    assert body["model"]["provider"] == "mock"
    assert 1 <= len(body["suggestions"]) <= 3
    for s in body["suggestions"]:
        assert s["title"]
        assert s["core_thesis"]
        assert isinstance(s["must_include"], list) and s["must_include"]
        assert s["fact_pack_id"] == frozen_pack["id"]


def test_suggest_requires_frozen_pack(client, seed_users, db_session):
    from app.models import FactPack

    pack = FactPack(name="未冻结", version=1, status="draft")
    db_session.add(pack)
    db_session.commit()
    resp = client.post("/api/v1/topics/suggest", headers=EDITOR, params={"fact_pack_id": pack.id})
    assert resp.status_code == 409


def test_suggest_editor_only(client, seed_users, db_session):
    from app.models import User

    db_session.add(User(email="viewer@studio.local", name="Viewer", role="viewer"))
    db_session.commit()
    resp = client.post(
        "/api/v1/topics/suggest",
        headers={"X-Studio-User": "viewer@studio.local"},
        params={"fact_pack_id": 1},
    )
    assert resp.status_code == 403


def test_suggest_missing_pack_404(client, seed_users):
    resp = client.post("/api/v1/topics/suggest", headers=EDITOR, params={"fact_pack_id": 9999})
    assert resp.status_code == 404


def test_topic_discovery_route_falls_back_to_disabled_profile(client, seed_users, reset_runtime):
    """路由指向停用 Profile 时回落默认（mock），荐题仍可用。"""
    payload = {
        "profiles": [{"name": "ds", "provider": "mock", "enabled": False}],
        "routes": {"topic_discovery": "ds"},
    }
    assert client.put("/api/v1/settings/models", headers=ADMIN, json=payload).status_code == 200
    config = effective_llm_config("topic_discovery")
    assert config["profile"] == "default"
    assert config["provider"] == "mock"
