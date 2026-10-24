"""Safe product inventory contracts, isolated from application startup/probes."""

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import runtime_config
from app.db import get_db
from app.models import (
    BrandVoiceVersion,
    ChannelTemplateVersion,
    Connector,
    ConnectorEndpoint,
    DiscoverabilityProfileVersion,
    PromptVersion,
    User,
)
from app.routers.product_settings import router
from app.services.system_settings import build_settings_view as build_legacy_settings_view

BASE = "/api/v1/settings"


@pytest.fixture
def settings_client(db_session, monkeypatch):
    from app.routers import connectors, settings
    from app.services import plugin_registry, system_settings

    monkeypatch.setattr(runtime_config, "_OVERRIDES", {})

    def forbidden(*args, **kwargs):
        raise AssertionError("inventory must not probe, scan, or assemble unsafe settings")

    monkeypatch.setattr(system_settings, "build_settings_view", forbidden)
    monkeypatch.setattr(settings, "build_settings_view", forbidden)
    monkeypatch.setattr(system_settings, "plugins_view", forbidden)
    monkeypatch.setattr(system_settings, "dsh_view", forbidden)
    monkeypatch.setattr(plugin_registry, "scan_skills", forbidden)
    monkeypatch.setattr(plugin_registry, "dsh_status", forbidden)
    for role in ("admin", "editor", "reviewer", "viewer"):
        db_session.add(User(email=f"{role}@studio.local", name=role, role=role))
    db_session.commit()
    application = FastAPI()
    application.include_router(settings.router)
    application.include_router(connectors.router)
    # Local app intentionally avoids main registration and lifespan side effects.
    application.include_router(router)

    def override_db():
        yield db_session

    application.dependency_overrides[get_db] = override_db
    yield TestClient(application)


def read(client, path="product", role="admin", **params):
    response = client.get(f"{BASE}/{path}", headers={"X-Studio-User": f"{role}@studio.local"}, params=params)
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.parametrize("role", ["admin", "editor", "reviewer", "viewer"])
def test_product_sections_and_caller_capabilities(settings_client, role):
    sections = {item["key"]: item for item in read(settings_client, role=role)["sections"]}
    assert list(sections) == ["models", "data_sources", "channels", "rules", "team"]
    assert sections["models"]["editability"] == ("editable" if role == "admin" else "read_only")
    assert sections["channels"]["editability"] == "read_only"
    assert sections["team"]["editability"] == "read_only"


@pytest.mark.parametrize("url,expected", [
    ("https://api.example.com/v1", "https://api.example.com"),
    ("https://user:secret@api.example.com/v1", ""),
    ("https://api.example.com/v1?token=secret", ""),
    ("file:///private/config", ""),
    ("https://api.example.com/#secret", ""),
])
def test_models_allowlist_and_origin_only_urls(settings_client, url, expected):
    runtime_config.set_runtime("llm", {"provider": "openai_compatible", "base_url": url, "model": "real", "api_key": "unique-full-secret", "diagnostic": "PRIVATE"})
    runtime_config.set_runtime("models", {"profiles": {"primary": {"provider": "mock", "base_url": url, "model": "m", "api_key": "tiny", "enabled": True, "headers": {"secret": "PRIVATE"}}}, "routes": {"generate": "primary", "unsafe": "PRIVATE"}})
    runtime_config.set_runtime("image", {"provider": "openai", "base_url": url, "api_key": "unique-image-secret", "enabled": True, "path": "/private/file"})
    data = read(settings_client)["sections"][0]["data"]
    for profile in (data["llm"], data["models"]["profiles"]["primary"], data["image"]):
        assert profile["base_url"] == expected
        assert profile["api_key"] == {"configured": True, "masked": "••••"}
    serialized = json.dumps(data)
    for secret in ("unique-full-secret", "unique-image-secret", "tiny", "PRIVATE", "/private", "/v1", "token="):
        assert secret not in serialized


@pytest.mark.parametrize("role,can_pull", [("admin", True), ("editor", True), ("reviewer", False), ("viewer", False)])
def test_sources_safe_metadata_and_exact_pull_role(settings_client, db_session, role, can_pull):
    connector = Connector(name="Generic", base_url="https://secret@host/path", default_headers_json={"Authorization": "PRIVATE"}, api_key_env="PRIVATE_ENV")
    db_session.add(connector)
    db_session.flush()
    db_session.add(ConnectorEndpoint(connector_id=connector.id, name="Daily", path="/PRIVATE", title_template="PRIVATE", body_template_json={"secret": "PRIVATE"}, params_json={"token": "PRIVATE"}, last_pull_status="failed", last_pull_error="PRIVATE"))
    db_session.commit()
    section = read(settings_client, "data-sources", role)
    plugins = section["data"]["plugins"]
    assert next(p for p in plugins if p["key"] == "studio.source")["available"] is True
    assert next(p for p in plugins if p["key"] == "api")["available"] is False
    row = section["data"]["connectors"][0]
    assert row["endpoint_count"] == 1
    assert row["can_configure"] is (role == "admin")
    assert row["can_pull"] is can_pull
    assert "PRIVATE" not in json.dumps(section)
    assert "base_url" not in row and "api_key_env" not in row


def test_channels_whitelist_configured_not_verified_and_fallback(settings_client, db_session):
    db_session.add(ChannelTemplateVersion(channel="zhihu", version=1, name="Profile", status="published", profile_json={"secret": "PRIVATE", "content_forms": {"answer": {"artifact_kind": "text", "default_workflow_key": "workflow.answer", "renderer_key": "renderer.answer", "rule_sets": ["rule.fact.bound"], "publisher_candidates": ["publisher.unverified"], "media_requirements": {"secret": "PRIVATE"}}}}))
    db_session.commit()
    items = read(settings_client, "channels")["data"]["items"]
    form = next(c for c in items if c["channel"] == "zhihu")["content_forms"][0]
    assert form["workflow_key"] == "workflow.answer"
    assert form["publisher_candidates"] == ["publisher.unverified"]
    assert form["capability_state"] == "configured_not_verified"
    assert form["verified"] is False
    legacy = next(c for c in items if c["channel"] == "wechat")["content_forms"][0]
    assert legacy["rule_sets"] == []
    assert legacy["effective_rule_sets"] == []
    assert legacy["rule_source"] == "none"
    assert "PRIVATE" not in json.dumps(items)


def test_cold_rules_and_resource_specific_actions(settings_client, db_session, monkeypatch):
    db_session.add_all([
        PromptVersion(channel="wechat", name="Published", version=1, template_text="PRIVATE", status="published"),
        PromptVersion(channel="wechat", name="Draft", version=2, template_text="PRIVATE", status="draft"),
        ChannelTemplateVersion(channel="wechat", name="Template", version=1, status="published", structure=["PRIVATE"]),
        BrandVoiceVersion(name="Voice", version=1, status="draft", examples=["PRIVATE"]),
        DiscoverabilityProfileVersion(profile_key="seo.wechat", channel="wechat", version=1, config_json={"secret": "PRIVATE"}),
    ])
    db_session.commit()
    data = read(settings_client, "rules")["data"]
    assert data["rules"] == []
    by_name = {t["name"]: t for t in data["templates"]["items"]}
    assert by_name["Published"]["actions"] == []
    assert "clone" not in by_name["Draft"]["actions"]
    assert "publish" in by_name["Draft"]["actions"]
    assert "archive" not in by_name["Template"]["actions"]
    assert "clone" in by_name["Template"]["actions"]
    assert by_name["seo.wechat"]["actions"] == []
    assert "PRIVATE" not in json.dumps(data)
    assert all(t["actions"] == [] for t in read(settings_client, "rules", "viewer")["data"]["templates"]["items"])


def test_team_uses_existing_authenticated_read_contract(settings_client, db_session):
    db_session.add(User(email="inactive@studio.local", name="Inactive", role="viewer", is_active=False))
    db_session.commit()
    data = read(settings_client, "team", "viewer")["data"]
    assert data["auth_mode"] == "development/header"
    assert data["current_user"]["role"] == "viewer"
    assert len(data["users"]) == 5
    assert next(u for u in data["users"] if u["name"] == "Inactive")["is_active"] is False
    assert "invite" not in data and "sso" not in data
    assert settings_client.get(f"{BASE}/team", headers={"X-Studio-User": "inactive@studio.local"}).status_code == 403


@pytest.mark.parametrize("path", ["data-sources", "rules"])
def test_inventory_pagination_is_bounded(settings_client, path):
    assert settings_client.get(f"{BASE}/{path}?limit=201").status_code == 422
    assert settings_client.get(f"{BASE}/{path}?offset=-1").status_code == 422
    data = read(settings_client, path, limit=1, offset=500)["data"]
    page = data if path == "data-sources" else data["templates"]
    assert page["limit"] == 1 and page["offset"] == 500
    assert page["connectors" if path == "data-sources" else "items"] == []


@pytest.mark.parametrize("path", ["product", "data-sources", "channels", "rules", "team"])
def test_product_inventory_has_no_write_wrappers(settings_client, path):
    assert settings_client.post(f"{BASE}/{path}", json={}).status_code == 405


@pytest.mark.parametrize("role", ["editor", "reviewer", "viewer"])
def test_existing_admin_mutators_still_deny_nonadmins(settings_client, role):
    headers = {"X-Studio-User": f"{role}@studio.local"}
    for path, body in [("llm", {"provider": "mock"}), ("models", {"profiles": [], "routes": {}}), ("image", {})]:
        assert settings_client.put(f"{BASE}/{path}", headers=headers, json=body).status_code == 403
    assert settings_client.post(f"{BASE}/llm/test", headers=headers, json={}).status_code == 403
    assert settings_client.post("/api/v1/connectors", headers=headers, json={"name": "Test", "base_url": "https://example.com"}).status_code == 403


@pytest.mark.parametrize("role", ["admin", "editor", "reviewer", "viewer"])
def test_pull_metadata_matches_real_gate_without_network(settings_client, db_session, monkeypatch, role):
    from app.services import connector_service
    connector = Connector(name="C", base_url="https://example.com")
    db_session.add(connector)
    db_session.flush()
    endpoint = ConnectorEndpoint(connector_id=connector.id, name="E", path="/data", title_template="T")
    db_session.add(endpoint)
    db_session.commit()
    calls = []

    def stop_before_network(*args):
        calls.append(True)
        raise connector_service.ConnectorError("test executor stopped")

    monkeypatch.setattr(connector_service, "pull_endpoint", stop_before_network)
    can_pull = read(settings_client, "data-sources", role)["data"]["can_pull"]
    assert calls == []
    response = settings_client.post(f"/api/v1/endpoints/{endpoint.id}/pull", headers={"X-Studio-User": f"{role}@studio.local"})
    assert response.status_code == (400 if can_pull else 403)
    assert bool(calls) is can_pull


def test_connector_inventory_and_template_pages_are_complete(settings_client, db_session):
    db_session.add_all([Connector(name=f"C{i}", base_url="https://example.com") for i in range(3)])
    db_session.add_all([PromptVersion(name=f"P{i}", channel="wechat", version=i, template_text="private", status="draft") for i in range(3)])
    db_session.commit()
    for path, list_key in [("data-sources", "connectors"), ("rules", "items")]:
        pages = [read(settings_client, path, limit=1, offset=i)["data"] for i in range(3)]
        pages = [p["templates"] if path == "rules" else p for p in pages]
        assert all(p["total"] == 3 for p in pages)
        assert len({p[list_key][0]["id"] for p in pages}) == 3


def test_inventory_selects_no_connector_secrets_or_template_bodies(settings_client, db_session):
    from sqlalchemy import event
    statements = []

    def capture(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement.lower())

    engine = db_session.get_bind()
    event.listen(engine, "before_cursor_execute", capture)
    try:
        read(settings_client, "data-sources")
        read(settings_client, "rules")
    finally:
        event.remove(engine, "before_cursor_execute", capture)
    sql = " ".join(statements)
    for column in ("default_headers_json", "api_key_env", "body_template_json", "params_json", "last_pull_error", "template_text", "config_json"):
        assert column not in sql


def test_model_inventory_does_not_mutate_runtime_snapshot(settings_client):
    snapshot = {"profiles": {"a": {"provider": "mock", "model": "one", "api_key": "secret-a"}, "b": {"provider": "mock", "model": "two", "api_key": "secret-b"}}, "routes": {"generate": "a", "rewrite": "b"}}
    runtime_config.set_runtime("models", snapshot)
    data = read(settings_client)["sections"][0]["data"]["models"]
    assert set(data["profiles"]) == {"a", "b"}
    assert data["routes"]["generate"] == "a" and data["routes"]["rewrite"] == "b"
    assert runtime_config.get_runtime("models") == snapshot


@pytest.mark.parametrize("url,expected,redacted", [
    ("https://api.example.com/compatible/v1", "https://api.example.com/compatible/v1", False),
    ("https://api.example.com/v1?version=2026", "https://api.example.com/v1?version=2026", False),
    ("https://api.example.com/v1?api-version=2026-09-28", "https://api.example.com/v1?api-version=2026-09-28", False),
    ("https://api.example.com/v1?subscription-key=REVIEW_SENTINEL", "", True),
    ("https://api.example.com/v1?opaque=REVIEW_SENTINEL", "", True),
    ("https://api.example.com/v1?version=2026&opaque=REVIEW_SENTINEL", "", True),
    ("https://user:PRIVATE@api.example.com/v1", "", True),
    ("https://api.example.com/v1?api_key=PRIVATE", "", True),
    ("https://api.example.com/v1?ACCESS_TOKEN=PRIVATE", "", True),
    ("https://api.example.com/v1?%61pi%5Fkey=PRIVATE", "", True),
    ("https://api.example.com/token/PRIVATE/v1", "", True),
    ("https://api.example.com/v1/sk-PRIVATE", "", True),
    ("https://api.example.com/v1#PRIVATE", "", True),
    ("file:///private/runtime", "", True),
    ("", "", False),
])
def test_legacy_provider_views_preserve_clean_urls_and_flag_redaction(settings_client, url, expected, redacted):
    from app.services import system_settings
    runtime_config.set_runtime("llm", {"provider": "mock", "base_url": url})
    runtime_config.set_runtime("models", {"profiles": {"primary": {"provider": "mock", "base_url": url}}})
    runtime_config.set_runtime("image", {"provider": "openai", "base_url": url})
    for view in (system_settings.llm_view(), system_settings.models_view()["profiles"]["primary"], system_settings.image_view()):
        assert view["base_url"] == expected
        assert view["base_url_redacted"] is redacted
        assert "PRIVATE" not in json.dumps(view)
        assert "REVIEW_SENTINEL" not in json.dumps(view)
    assert runtime_config.get_runtime("llm")["base_url"] == url


def test_legacy_settings_get_redacts_urls_without_inventory_side_effects(settings_client, monkeypatch):
    from app.routers import settings
    from app.services import system_settings
    monkeypatch.setattr(settings, "build_settings_view", build_legacy_settings_view)
    monkeypatch.setattr(system_settings, "plugins_view", dict)
    monkeypatch.setattr(system_settings, "dsh_view", dict)
    runtime_config.set_runtime("llm", {"base_url": "https://user:PRIVATE@api.example.com/v1"})
    runtime_config.set_runtime("models", {"profiles": {"primary": {"base_url": "https://api.example.com/v1?token=PRIVATE"}}})
    runtime_config.set_runtime("image", {"base_url": "https://api.example.com/v1?key=PRIVATE"})
    response = settings_client.get(BASE, headers={"X-Studio-User": "admin@studio.local"})
    assert response.status_code == 200
    body = response.json()
    for view in (body["llm"], body["models"]["profiles"]["primary"], body["image"]):
        assert view["base_url"] == "" and view["base_url_redacted"] is True
    assert "PRIVATE" not in response.text


@pytest.mark.parametrize("role", ["editor", "reviewer", "viewer"])
def test_legacy_inventory_denies_nonadmins_before_unsafe_calls(settings_client, monkeypatch, role):
    from app.routers import settings
    calls = []

    def inventory():
        calls.append(True)
        return {"unsafe_inventory": True}

    monkeypatch.setattr(settings, "build_settings_view", inventory)
    response = settings_client.get(BASE, headers={"X-Studio-User": f"{role}@studio.local"})
    assert response.status_code == 403
    assert calls == []


def test_legacy_inventory_admin_keeps_existing_response(settings_client, monkeypatch):
    from app.routers import settings
    calls = []
    payload = {"llm": {"provider": "mock"}, "plugins": {"skills": []}, "dsh": {"status": "test"}}

    def inventory():
        calls.append(True)
        return payload

    monkeypatch.setattr(settings, "build_settings_view", inventory)
    response = settings_client.get(BASE, headers={"X-Studio-User": "admin@studio.local"})
    assert response.status_code == 200
    assert response.json() == payload
    assert calls == [True]
