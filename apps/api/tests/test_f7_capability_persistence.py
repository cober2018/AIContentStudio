"""FE-F7 durable capability identity stays separate from executable verification."""

import json

import httpx
import pytest
from fastapi import HTTPException
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from app.models import (
    AuditLog,
    CapabilityRegistration,
    CapabilityVerification,
    Connector,
    ConnectorEndpoint,
    ContentAccount,
    ContentPersona,
    DeliveryTarget,
    SourceDocument,
    User,
)
from app.services import capability_integrations, connector_service, delivery, url_fetch
from app.services.capability_integrations import append_verification, is_verified_for_scope
from app.services.content_harness.registry import PluginRegistry


def _official_accounts(db, monkeypatch):
    from app.models import SystemSetting

    monkeypatch.setenv("AICS_WECHAT_RUNTIME_IDENTITY_KEY", "isolated-runtime-identity-key" * 2)

    user = User(email="official-owner@studio.local", name="Owner", role="admin")
    db.add(user)
    db.flush()
    persona = ContentPersona(owner_user_id=user.id, name="作者")
    db.add(persona)
    db.flush()
    accounts = []
    for suffix in ("a", "b"):
        account = ContentAccount(persona_id=persona.id, name=suffix, platform_channel="wechat", platform_account_id="wx" + suffix * 16)
        db.add(account)
        db.flush()
        ref = f"AICS_WECHAT_ACCOUNT_{account.id}_APPSECRET"
        db.add(SystemSetting(key=f"wechat.official.account.{account.id}", value={
            "revision": 1, "enabled": True, "credential_ref": ref,
            "credential_version": "v1", "platform_account_id": account.platform_account_id,
        }))
        monkeypatch.setenv(ref, suffix * 32)
        monkeypatch.setenv(ref + "_VERSION", "v1")
        accounts.append(account)
    db.commit()
    return user, accounts


def _official_scope(account):
    return {"channel": "wechat", "content_form": "article", "action": "auto_draft",
            "content_account_id": account.id, "account_ref": account.platform_account_id,
            "publisher_key": "publisher.wechat.official", "publisher_version": "1"}


def test_official_runtime_and_token_cache_are_exact_account_isolated(db_session, monkeypatch):
    from app.services import wechat_official

    _, (a, b) = _official_accounts(db_session, monkeypatch)
    first = wechat_official.resolve_runtime(db_session, a.id)
    second = wechat_official.resolve_runtime(db_session, b.id)
    assert first.fingerprint != second.fingerprint
    assert first.secret not in repr(first)
    cache = wechat_official.TokenCache()
    cache.put(first, "token-account-a", expires_in=7200)
    cache.put(second, "token-account-b", expires_in=7200)
    assert cache.get(first) == "token-account-a"
    assert cache.get(second) == "token-account-b"
    monkeypatch.setenv(f"AICS_WECHAT_ACCOUNT_{a.id}_APPSECRET", "rotated" * 5)
    rotated = wechat_official.resolve_runtime(db_session, a.id)
    assert rotated.fingerprint != first.fingerprint
    assert cache.get(rotated) is None
    assert wechat_official.resolve_runtime(db_session, b.id).fingerprint == second.fingerprint
    assert cache.get(second) == "token-account-b"
    cache.revoke(second)
    assert cache.get(second) is None
    cache.put(first, "expiry", expires_in=60)
    assert cache.get(first, now=10**15) is None
    monkeypatch.delenv(f"AICS_WECHAT_ACCOUNT_{a.id}_APPSECRET")
    with pytest.raises(HTTPException, match="official_credentials_unavailable"):
        wechat_official.resolve_runtime(db_session, a.id)


def test_official_verification_uses_server_account_hash_not_client_or_registration_hash(db_session, monkeypatch):
    from app.services import wechat_official

    user, (a, b) = _official_accounts(db_session, monkeypatch)
    implementation = wechat_official.OfficialWechatPublisher()
    registration = CapabilityRegistration(kind="publisher", key=implementation.key, version="1", status="configured",
                                          config_fingerprint=wechat_official.implementation_fingerprint())
    db_session.add(registration)
    db_session.flush()
    scope = _official_scope(a)
    with pytest.raises(ValueError, match="official_contract_unresolved"):
        append_verification(db_session, registration, scope_kind="publisher_action", scope=scope,
                            result="verified", actor=user.email, evidence={"kind": "human_readback", "reference_hash": "c" * 64})
    assert db_session.scalars(select(CapabilityVerification)).all() == []
    monkeypatch.setattr(wechat_official, "remote_contract_ready", lambda: True)
    with pytest.raises(ValueError, match="capability_registration_invalid"):
        append_verification(db_session, registration, scope_kind="publisher_action", scope=scope,
                            result="verified", actor=user.email, evidence={"kind": "human_readback", "reference_hash": "c" * 64},
                            config_fingerprint="f" * 64)
    events = []
    for account in (a, b):
        event = append_verification(db_session, registration, scope_kind="publisher_action", scope=_official_scope(account),
                                    result="verified", actor=user.email, evidence={"kind": "human_readback", "reference_hash": "c" * 64})
        assert event.config_fingerprint == wechat_official.scope_fingerprint(db_session, _official_scope(account))
        assert event.config_fingerprint != registration.config_fingerprint
        events.append(event)
    db_session.commit()
    loaded = PluginRegistry()
    loaded.register("publisher", implementation.key, "1", implementation)
    for account, event in zip((a, b), events):
        assert is_verified_for_scope(db_session, registration, _official_scope(account), event.config_fingerprint, loaded)
        assert capability_integrations.publisher_target_verified(db_session, DeliveryTarget(**_official_scope(account)), loaded)
    from datetime import UTC, datetime, timedelta

    assert not is_verified_for_scope(db_session, registration, scope, events[0].config_fingerprint, loaded,
                                    now=datetime.now(UTC) + timedelta(days=2))
    monkeypatch.setenv(f"AICS_WECHAT_ACCOUNT_{a.id}_APPSECRET", "new-secret" * 4)
    assert not is_verified_for_scope(db_session, registration, scope, events[0].config_fingerprint, loaded)
    assert is_verified_for_scope(db_session, registration, _official_scope(b), events[1].config_fingerprint, loaded)
    assert not is_verified_for_scope(db_session, registration, {**_official_scope(b), "account_ref": a.platform_account_id}, events[1].config_fingerprint, loaded)
    append_verification(db_session, registration, scope_kind="publisher_action", scope=_official_scope(b),
                        result="revoked", actor=user.email, evidence={"kind": "revocation"})
    db_session.commit()
    assert not is_verified_for_scope(db_session, registration, _official_scope(b), events[1].config_fingerprint, loaded)


def test_official_verification_api_blocks_unresolved_contract_and_can_revoke_without_secret(client, db_session, monkeypatch):
    from app.services import wechat_official

    user, (a, _) = _official_accounts(db_session, monkeypatch)
    payload = {**_official_scope(a), "result": "verified", "reference_hash": "c" * 64, "confirm_readback": True}
    response = client.post("/api/v1/settings/publisher-verifications", json=payload, headers={"X-Studio-User": user.email})
    assert response.status_code == 409
    assert response.json()["detail"] == "official_contract_unresolved"
    monkeypatch.setattr(wechat_official, "remote_contract_ready", lambda: True)
    response = client.post("/api/v1/settings/publisher-verifications", json=payload, headers={"X-Studio-User": user.email})
    assert response.status_code == 201, response.text
    registration = db_session.get(CapabilityRegistration, response.json()["registration_id"])
    assert registration.config_fingerprint == wechat_official.implementation_fingerprint()
    monkeypatch.delenv(f"AICS_WECHAT_ACCOUNT_{a.id}_APPSECRET")
    response = client.post("/api/v1/settings/publisher-verifications", json={**payload, "result": "revoked"}, headers={"X-Studio-User": user.email})
    assert response.status_code == 201, response.text
    assert db_session.get(CapabilityVerification, response.json()["verification_id"]).result == "revoked"


def test_official_inventory_never_resolves_credentials(client, db_session, monkeypatch):
    from app.services import wechat_official

    user, (a, _) = _official_accounts(db_session, monkeypatch)
    registration = CapabilityRegistration(kind="publisher", key="publisher.wechat.official", version="1", status="configured",
                                          config_fingerprint=wechat_official.implementation_fingerprint())
    db_session.add(registration)
    db_session.flush()
    monkeypatch.setattr(wechat_official, "remote_contract_ready", lambda: True)
    append_verification(db_session, registration, scope_kind="publisher_action", scope=_official_scope(a), result="verified",
                        actor=user.email, evidence={"kind": "human_readback", "reference_hash": "c" * 64})
    db_session.commit()
    monkeypatch.setattr(wechat_official, "remote_contract_ready", lambda: False)
    monkeypatch.setattr(wechat_official, "resolve_runtime", lambda *args: pytest.fail("inventory read secret"))
    response = client.get("/api/v1/settings/capabilities", headers={"X-Studio-User": user.email})
    assert response.status_code == 200, response.text
    publisher = next(row for row in response.json()["publishers"] if row["scope"]["publisher_key"] == "publisher.wechat.official")
    assert publisher["verified"] is False and publisher["executable"] is False
    assert publisher["reason"] == "official_contract_unresolved"


def test_official_fingerprint_survives_module_reload_but_requires_explicit_identity_key(db_session, monkeypatch):
    import importlib.util
    import sys

    from app.services import wechat_official

    _, (a, _) = _official_accounts(db_session, monkeypatch)
    fingerprint = wechat_official.resolve_runtime(db_session, a.id).fingerprint
    # A fresh module models another worker without invalidating the shared Registry's class.
    name = "app.services._wechat_identity_reload_fixture"
    spec = importlib.util.spec_from_file_location(name, wechat_official.__file__)
    reloaded = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, reloaded)
    spec.loader.exec_module(reloaded)
    assert reloaded.resolve_runtime(db_session, a.id).fingerprint == fingerprint
    monkeypatch.delenv("AICS_WECHAT_RUNTIME_IDENTITY_KEY")
    with pytest.raises(HTTPException, match="official_identity_key_unavailable"):
        wechat_official.resolve_runtime(db_session, a.id)


def test_official_revoke_wrong_account_ref_is_safe_conflict(client, db_session, monkeypatch):
    from app.services import wechat_official

    user, (a, b) = _official_accounts(db_session, monkeypatch)
    registration = CapabilityRegistration(kind="publisher", key="publisher.wechat.official", version="1", status="configured",
                                          config_fingerprint=wechat_official.implementation_fingerprint())
    db_session.add(registration)
    db_session.commit()
    payload = {**_official_scope(a), "account_ref": b.platform_account_id, "result": "revoked", "reference_hash": "c" * 64, "confirm_readback": True}
    response = client.post("/api/v1/settings/publisher-verifications", json=payload, headers={"X-Studio-User": user.email})
    assert response.status_code == 409
    assert response.json()["detail"] == "official_account_scope_mismatch"
    assert db_session.scalars(select(CapabilityVerification)).all() == []


def test_f7_v5_wewrite_projection_uses_only_frozen_article_and_cover():
    manifest = {
        "schema_version": 5,
        "target": {"channel": "wechat", "content_form": "article", "artifact_kind": "text"},
        "content": {"title": "冻结标题"},
        "render": {"text": "冻结标题\n\n冻结正文"},
        "assets": [{"role": "cover", "material_revision_id": 7, "content_hash_snapshot": "a" * 64}],
    }
    projected = delivery.project_v5_wewrite_payload(manifest)
    assert projected["render"]["payload"] == {
        "title": "冻结标题", "digest": "冻结标题", "markdown": "冻结标题\n\n冻结正文",
    }
    assert projected["assets"] == manifest["assets"]
    assert projected["schema_version"] == 5
    for changed in (
        {**manifest, "render": {"text": ""}},
        {**manifest, "assets": []},
        {**manifest, "target": {"channel": "x", "content_form": "single", "artifact_kind": "text"}},
        {**manifest, "content": {"title": "x" * 65}},
    ):
        with pytest.raises(HTTPException):
            delivery.project_v5_wewrite_payload(changed)


@pytest.mark.parametrize("channel,form", [("xiaohongshu", "image_note"), ("douyin", "spoken_script")])
def test_f7_remote_publisher_without_verified_adapter_is_unavailable(channel, form):
    with pytest.raises(HTTPException) as error:
        delivery.resolve_publisher(channel, form, "auto_draft")
    assert error.value.status_code == 422


def test_f7_publisher_human_verification_is_owned_scoped_and_revocable(client, db_session, monkeypatch):
    admin = User(email="publisher-admin@studio.local", name="Admin", role="admin")
    viewer = User(email="publisher-viewer@studio.local", name="Viewer", role="viewer")
    db_session.add_all([admin, viewer])
    db_session.flush()
    persona = ContentPersona(owner_user_id=admin.id, name="作者")
    db_session.add(persona)
    db_session.flush()
    account = ContentAccount(persona_id=persona.id, name="公众号", status="active")
    db_session.add(account)
    db_session.commit()
    monkeypatch.setenv("WEWRITE_CREDENTIAL_VERSION", "credential-v1")
    monkeypatch.setenv("WEWRITE_BINARY_VERSION", "binary-v1")
    unavailable = capability_integrations.publisher_runtime_fingerprint("publisher.wechat.wewrite", "1")
    assert unavailable is None
    headers = {"X-Studio-User": admin.email}
    payload = {"channel": "wechat", "content_form": "article", "action": "auto_draft",
               "content_account_id": account.id, "account_ref": "official-account-1",
               "publisher_key": "publisher.wechat.wewrite", "publisher_version": "1",
               "result": "verified", "reference_hash": "a" * 64, "confirm_readback": True}
    path = "/api/v1/settings/publisher-verifications"
    assert client.post(path, json=payload, headers={"X-Studio-User": viewer.email}).status_code == 403
    assert client.post(path, json={**payload, "confirm_readback": False}, headers=headers).status_code == 422
    assert client.post(path, json=payload, headers=headers).status_code == 409
    assert db_session.scalars(select(CapabilityVerification)).all() == []
    monkeypatch.setattr(capability_integrations, "publisher_runtime_fingerprint", lambda *args: "a" * 64)
    verified = client.post(path, json=payload, headers=headers)
    assert verified.status_code == 201, verified.text
    inventory = client.get("/api/v1/settings/capabilities", headers=headers)
    assert inventory.status_code == 200, inventory.text
    assert "private/verified" not in inventory.text
    publisher = next(row for row in inventory.json()["publishers"] if row["scope"]["content_account_id"] == account.id)
    assert publisher["verified"] is True
    hidden = client.get("/api/v1/settings/capabilities", headers={"X-Studio-User": viewer.email})
    assert hidden.status_code == 200 and hidden.json()["publishers"] == []
    revoked = client.post(path, json={**payload, "result": "revoked"}, headers=headers)
    assert revoked.status_code == 201, revoked.text
    after = client.get("/api/v1/settings/capabilities", headers=headers)
    assert after.json()["publishers"][0]["verified"] is False
    assert db_session.scalar(select(CapabilityVerification).where(
        CapabilityVerification.id == verified.json()["verification_id"])).result == "verified"


def test_f7_registration_is_unique_by_exact_kind_key_version(db_session):
    first = CapabilityRegistration(
        kind="publisher", key="api", version="1", status="configured",
        config_fingerprint="a" * 64, endpoint_id=None,
    )
    db_session.add(first)
    db_session.commit()
    db_session.add(CapabilityRegistration(
        kind="publisher", key="api", version="1", status="configured",
        config_fingerprint="b" * 64, endpoint_id=None,
    ))
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_f7_verification_rejects_invalid_scope_kind_at_database_boundary(db_session):
    registration = CapabilityRegistration(kind="publisher", key="publisher.wechat.wewrite", version="1",
                                          status="configured", config_fingerprint="a" * 64)
    db_session.add(registration)
    db_session.flush()
    db_session.add(CapabilityVerification(registration_id=registration.id, config_fingerprint="a" * 64,
                                          scope_kind="unscoped", scope_json={}, result="verified",
                                          evidence_json={}))
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_f7_registration_rejects_unknown_registry_kind_at_database_boundary(db_session):
    db_session.add(CapabilityRegistration(kind="unregistered_kind", key="api", version="1", status="configured",
                                          config_fingerprint="a" * 64))
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_f7_multiple_profiles_require_explicit_plugin_and_endpoint_mapping(db_session):
    connector = Connector(name="API", base_url="https://example.org", auth_style="none")
    db_session.add(connector)
    db_session.flush()
    endpoints = [ConnectorEndpoint(connector_id=connector.id, name=name, path=f"/{name}", title_template=name)
                 for name in ("one", "two")]
    db_session.add_all(endpoints)
    db_session.flush()
    db_session.add(CapabilityRegistration(
        kind="data_connector", key="profile.one", version="1", status="configured",
        config_fingerprint="a" * 64, data_source_plugin_key="api", endpoint_id=endpoints[0].id,
    ))
    db_session.add(CapabilityRegistration(
        kind="data_connector", key="profile.two", version="1", status="configured",
        config_fingerprint="b" * 64, data_source_plugin_key="api", endpoint_id=endpoints[1].id,
    ))
    db_session.commit()
    db_session.add(CapabilityRegistration(
        kind="data_connector", key="profile.invalid", version="1", status="configured",
        config_fingerprint="c" * 64, endpoint_id=endpoints[0].id,
    ))
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_f7_verification_is_separate_append_only_evidence(db_session):
    registration = CapabilityRegistration(
        kind="publisher", key="publisher.wechat.wewrite", version="1",
        status="configured", config_fingerprint="a" * 64,
    )
    db_session.add(registration)
    db_session.flush()
    first = CapabilityVerification(
        registration_id=registration.id, config_fingerprint="a" * 64,
        scope_kind="publisher_action", scope_json={"channel": "wechat", "content_form": "article", "action": "auto_draft"},
        result="verified", verified_by="admin@studio.local", evidence_json={"kind": "human_readback"},
    )
    second = CapabilityVerification(
        registration_id=registration.id, config_fingerprint="a" * 64,
        scope_kind="publisher_action", scope_json={"channel": "wechat", "content_form": "article", "action": "auto_draft"},
        result="revoked", verified_by="admin@studio.local", evidence_json={"kind": "revocation"},
    )
    db_session.add_all((first, second))
    db_session.commit()
    assert first.id != second.id
    assert inspect(db_session.bind).has_table("capability_registration")
    assert inspect(db_session.bind).has_table("capability_verification")


def test_f7_scope_version_fingerprint_revocation_and_loaded_executor(db_session):
    registration = CapabilityRegistration(
        kind="publisher", key="publisher.wechat.wewrite", version="1",
        status="configured", config_fingerprint="a" * 64,
    )
    db_session.add(registration)
    db_session.flush()
    registry = PluginRegistry()
    registry.register("publisher", registration.key, "1", object())
    scope = {
        "channel": "wechat", "content_form": "article", "action": "auto_draft",
        "content_account_id": 12, "account_ref": "account-A",
        "publisher_key": registration.key, "publisher_version": "1",
    }
    assert not is_verified_for_scope(db_session, registration, scope, "a" * 64, registry)
    append_verification(
        db_session, registration, scope_kind="publisher_action", scope=scope,
        result="verified", actor="admin@studio.local",
        evidence={"kind": "human_readback", "reference_hash": "c" * 64},
    )
    db_session.commit()
    assert is_verified_for_scope(db_session, registration, scope, "a" * 64, registry)
    assert not is_verified_for_scope(db_session, registration, {**scope, "account_ref": "account-B"}, "a" * 64, registry)
    assert not is_verified_for_scope(db_session, registration, scope, "b" * 64, registry)
    assert not is_verified_for_scope(db_session, registration, scope, "a" * 64, PluginRegistry())
    append_verification(
        db_session, registration, scope_kind="publisher_action", scope=scope,
        result="revoked", actor="admin@studio.local", evidence={"kind": "revocation", "reason_code": "operator_revoked"},
    )
    db_session.commit()
    assert not is_verified_for_scope(db_session, registration, scope, "a" * 64, registry)


def test_f7_verification_rejects_secret_bearing_scope_or_evidence(db_session):
    registration = CapabilityRegistration(
        kind="publisher", key="publisher.wechat.wewrite", version="1",
        status="configured", config_fingerprint="a" * 64,
    )
    db_session.add(registration)
    db_session.flush()
    with pytest.raises(ValueError):
        append_verification(db_session, registration, scope_kind="publisher_action", scope={"token": "secret"},
                            result="verified", actor="admin@studio.local", evidence={"kind": "human_readback", "reference_hash": "c" * 64})
    with pytest.raises(ValueError):
        append_verification(db_session, registration, scope_kind="publisher_action", scope={
            "channel": "wechat", "content_form": "article", "action": "auto_draft", "content_account_id": 12,
            "account_ref": "account-A", "publisher_key": registration.key, "publisher_version": "1",
        }, result="verified", actor="admin@studio.local", evidence={"kind": "human_readback", "raw_output": "secret"})


@pytest.mark.parametrize("function_name", ["_fetch_all_pages", "map_response_to_facts", "bounded_safe_fetch"])
def test_f7_endpoint_verification_rejects_loaded_executor_change(db_session, monkeypatch, function_name):
    from app.services import data_source_plugins

    connector = Connector(name="API", base_url="https://example.org", auth_style="none")
    db_session.add(connector)
    db_session.flush()
    endpoint = ConnectorEndpoint(connector_id=connector.id, name="daily", path="/daily", title_template="daily")
    db_session.add(endpoint)
    db_session.flush()
    fingerprint = capability_integrations.endpoint_config_fingerprint(endpoint)
    registration = CapabilityRegistration(kind="data_connector", key="profile.code-drift", version="1",
        status="configured", config_fingerprint=fingerprint, data_source_plugin_key="api", endpoint_id=endpoint.id)
    db_session.add(registration)
    db_session.flush()
    scope = {"plugin_key": "api", "registration_key": registration.key,
             "registration_version": registration.version, "endpoint_id": endpoint.id}
    append_verification(db_session, registration, scope_kind="data_source_endpoint", scope=scope,
                        result="verified", actor="admin@studio.local",
                        evidence={"kind": "platform_readback", "reference_hash": "d" * 64})
    db_session.commit()
    assert data_source_plugins.verified_data_endpoint(db_session, registration, "api") == endpoint
    original = getattr(connector_service, function_name)
    monkeypatch.setattr(connector_service, function_name, lambda *args, **kwargs: None)
    assert capability_integrations.endpoint_config_fingerprint(endpoint) != fingerprint
    with pytest.raises(ValueError, match="配置或凭据版本已变化"):
        data_source_plugins.verified_data_endpoint(db_session, registration, "api")
    monkeypatch.setattr(connector_service, function_name, original)
    assert capability_integrations.endpoint_config_fingerprint(endpoint) == fingerprint


def test_f7_endpoint_identity_needs_credential_version_and_tracks_config_edit(db_session, monkeypatch):
    connector = Connector(
        name="API", base_url="https://example.org", auth_style="bearer", api_key_env="F7_TEST_API_KEY",
    )
    db_session.add(connector)
    db_session.flush()
    endpoint = ConnectorEndpoint(connector_id=connector.id, name="daily", path="/daily", title_template="daily")
    db_session.add(endpoint)
    db_session.flush()
    monkeypatch.setenv("F7_TEST_API_KEY", "secret-never-stored")
    assert capability_integrations.endpoint_config_fingerprint(endpoint) is None
    monkeypatch.setenv("F7_TEST_API_KEY_VERSION", "v1")
    original = capability_integrations.endpoint_config_fingerprint(endpoint)
    assert isinstance(original, str) and len(original) == 64
    assert "secret-never-stored" not in original
    endpoint.path = "/changed"
    assert capability_integrations.endpoint_config_fingerprint(endpoint) != original
    endpoint.path = "/daily"
    monkeypatch.setenv("F7_TEST_API_KEY_VERSION", "v2")
    assert capability_integrations.endpoint_config_fingerprint(endpoint) != original


@pytest.mark.parametrize("pagination", [
    {"type": "page", "max_pages": 21},
    {"type": "page", "max_pages": 0},
    {"type": "offset", "page_size": 501},
    {"type": "offset", "page_size": 0},
    {"type": "page", "max_pages": "unbounded"},
])
def test_f7_data_endpoint_rejects_unbounded_pagination(db_session, pagination):
    connector = Connector(name="API", base_url="https://example.org", auth_style="none")
    db_session.add(connector)
    db_session.flush()
    endpoint = ConnectorEndpoint(
        connector_id=connector.id, name="daily", path="/daily", title_template="daily",
        pagination_json=pagination,
    )
    db_session.add(endpoint)
    db_session.flush()
    assert capability_integrations.endpoint_config_fingerprint(endpoint) is None


def test_f7_data_connector_verification_requires_exact_profile_and_loaded_executor(db_session):
    connector = Connector(name="API", base_url="https://example.org", auth_style="none")
    db_session.add(connector)
    db_session.flush()
    endpoint = ConnectorEndpoint(connector_id=connector.id, name="daily", path="/daily", title_template="daily")
    db_session.add(endpoint)
    db_session.flush()
    fingerprint = capability_integrations.endpoint_config_fingerprint(endpoint)
    registration = CapabilityRegistration(
        kind="data_connector", key="profile.daily", version="1", status="configured",
        config_fingerprint=fingerprint, data_source_plugin_key="api", endpoint_id=endpoint.id,
    )
    db_session.add(registration)
    db_session.flush()
    registry = PluginRegistry()
    registry.register("data_connector", registration.key, registration.version, object())
    scope = {
        "plugin_key": "api", "registration_key": registration.key,
        "registration_version": registration.version, "endpoint_id": endpoint.id,
    }
    append_verification(db_session, registration, scope_kind="data_source_endpoint", scope=scope,
                        result="verified", actor="admin@studio.local",
                        evidence={"kind": "platform_readback", "reference_hash": "d" * 64})
    db_session.commit()
    assert is_verified_for_scope(db_session, registration, scope, fingerprint, registry)
    assert not is_verified_for_scope(db_session, registration, {**scope, "plugin_key": "notion"}, fingerprint, registry)
    assert not is_verified_for_scope(db_session, registration, scope, fingerprint, PluginRegistry())


def test_f7_admin_configures_and_probes_read_only_data_capability(client, db_session, monkeypatch):
    admin = {"X-Studio-User": "data-admin@studio.local"}
    viewer = {"X-Studio-User": "data-viewer@studio.local"}
    db_session.add_all([
        User(email="data-admin@studio.local", name="Admin", role="admin"),
        User(email="data-viewer@studio.local", name="Viewer", role="viewer"),
    ])
    connector = Connector(name="API", base_url="https://example.org", auth_style="none")
    db_session.add(connector)
    db_session.flush()
    endpoint = ConnectorEndpoint(
        connector_id=connector.id, name="daily", path="/daily", method="GET", title_template="daily",
        fact_mapping_json={"items_path": "rows", "statement": "{name}={value}", "fields": {"value": "{value}"}},
    )
    db_session.add(endpoint)
    db_session.commit()
    path = "/api/v1/data-source-capabilities"
    config = {"key": "profile.daily", "version": "1", "plugin_key": "api", "endpoint_id": endpoint.id}
    calls = []
    payload = {"rows": [{"name": "rate", "value": 4}]}
    fetch_failure = False

    def fake_fetch(url, *args, **kwargs):
        if fetch_failure:
            raise RuntimeError("secret-example-provider-response")
        calls.append(url)
        return json.dumps(payload).encode(), "application/json"

    # The configured profile must bind the same test executor that its probe will run.
    monkeypatch.setattr(connector_service, "bounded_safe_fetch", fake_fetch, raising=False)
    monkeypatch.setattr(connector_service, "safe_fetch", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("legacy fetch used")))
    assert client.post(path, json=config, headers=viewer).status_code == 403
    created = client.post(path, json=config, headers=admin)
    assert created.status_code == 201, created.text
    capability_id = created.json()["id"]
    assert created.json()["verified"] is False
    inventory_path = "/api/v1/data-source-capabilities"
    inventory = client.get(inventory_path, headers=viewer)
    assert inventory.status_code == 200
    assert inventory.json()[0]["source_ref"] == f"capability:{capability_id}@1"
    assert inventory.json()[0]["executable"] is False
    assert client.post(path, json=config, headers=admin).status_code == 409
    pull_path = f"{path}/{capability_id}/pull"
    probe_path = f"{path}/{capability_id}/probe"
    assert client.post(pull_path, headers=admin).status_code == 409
    assert client.post(probe_path, headers=viewer).status_code == 403
    probe = client.post(probe_path, headers=admin)
    assert probe.status_code == 200, probe.text
    assert probe.json()["verified"] is True
    assert calls == ["https://example.org/daily"]
    assert client.get(inventory_path, headers=viewer).json()[0]["executable"] is True
    assert calls == ["https://example.org/daily"]
    pulled = client.post(pull_path, headers=admin)
    assert pulled.status_code == 200, pulled.text
    assert client.post(probe_path, headers=admin).status_code == 200
    fetch_failure = True
    failed = client.post(pull_path, headers=admin)
    assert failed.status_code == 502
    assert "secret-example-provider-response" not in failed.text
    assert db_session.get(ConnectorEndpoint, endpoint.id).last_pull_error == "connector_pull_failed"
    fetch_failure = False
    monkeypatch.setattr(connector_service, "safe_fetch", fake_fetch)
    assert client.post(f"/api/v1/endpoints/{endpoint.id}/pull", headers=admin).status_code == 200
    assert client.get(inventory_path, headers=viewer).json()[0]["executable"] is False
    assert client.post(pull_path, headers=admin).status_code == 409
    fetch_failure = True
    assert client.post(probe_path, headers=admin).status_code == 502
    fetch_failure = False
    assert client.post(probe_path, headers=admin).status_code == 200
    payload["rows"] = []
    assert client.post(probe_path, headers=admin).status_code == 422
    assert client.post(pull_path, headers=admin).status_code == 409
    endpoint.path = "/new-daily"
    db_session.commit()
    assert client.post(pull_path, headers=admin).status_code == 409
    assert client.get(inventory_path, headers=viewer).json()[0]["executable"] is False
    payload["rows"] = [{"name": "rate", "value": 5}]
    successor = client.post(path, json={**config, "version": "2"}, headers=admin)
    assert successor.status_code == 201, successor.text
    successor_id = successor.json()["id"]
    assert client.post(f"{path}/{successor_id}/probe", headers=admin).status_code == 200
    assert client.post(f"{path}/{successor_id}/pull", headers=admin).status_code == 200
    assert client.post(pull_path, headers=admin).status_code == 409
    audit = db_session.scalars(select(AuditLog).where(
        AuditLog.entity_type == "capability_registration",
    )).all()
    assert any(row.event == "data_source_capability.configured" and row.entity_id == str(capability_id) for row in audit)
    assert any(row.event == "data_source_capability.probed" and row.detail_json.get("result") == "verified" for row in audit)
    assert any(row.event == "data_source_capability.probed" and row.detail_json.get("result") == "failed" for row in audit)
    assert "secret-example-provider-response" not in json.dumps([row.detail_json for row in audit])
    failures = db_session.scalars(select(AuditLog).where(
        AuditLog.event == "connector.pull_failed", AuditLog.entity_id == str(endpoint.id),
    )).all()
    assert failures and all(row.actor == "data-admin@studio.local" for row in failures)
    assert all(row.detail_json == {"reason_code": "connector_pull_failed"} for row in failures)


def test_f7_post_endpoint_cannot_be_registered_as_read_only_data_capability(client, db_session):
    admin = {"X-Studio-User": "data-admin@studio.local"}
    db_session.add(User(email="data-admin@studio.local", name="Admin", role="admin"))
    connector = Connector(name="API", base_url="https://example.org", auth_style="none")
    db_session.add(connector)
    db_session.flush()
    endpoint = ConnectorEndpoint(connector_id=connector.id, name="query", path="/query", method="POST", title_template="query")
    db_session.add(endpoint)
    db_session.commit()
    response = client.post("/api/v1/data-source-capabilities", json={
        "key": "profile.query", "version": "1", "plugin_key": "api", "endpoint_id": endpoint.id,
    }, headers=admin)
    assert response.status_code == 409


@pytest.mark.parametrize("address", ["93.184.216.34", "2606:4700:4700::1111"])
def test_f7_pinned_transport_uses_checked_ip_without_hostname_resolution(monkeypatch, address):
    import socket

    from httpcore._backends.sync import SyncBackend

    resolutions, connections = [], []
    def resolve(host, port, **kwargs):
        resolutions.append((host, port))
        return [(socket.AF_INET6 if ":" in address else socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, port))]
    def connect(self, host, port, **kwargs):
        connections.append((host, port))
        return object()
    monkeypatch.setattr(socket, "getaddrinfo", resolve)
    monkeypatch.setattr(SyncBackend, "connect_tcp", connect)
    with url_fetch.pinned_transport("https://example.org/data") as transport:
        backend = transport._pool._network_backend
        backend.connect_tcp("example.org", 443)
        assert resolutions == [("example.org", 443)]
        assert connections == [(address, 443)]
        with pytest.raises(OSError):
            backend.connect_tcp("127.0.0.1", 443)


@pytest.mark.parametrize("invalid", ["127.0.0.1", "10.0.0.1", "169.254.169.254", "224.0.0.1", "ff02::1", "::1"])
def test_f7_pinned_transport_rejects_mixed_dns_even_with_legacy_private_opt_in(monkeypatch, invalid):
    import socket
    monkeypatch.setattr(url_fetch, "get_settings", lambda: type("Settings", (), {"ssrf_allow_private": True})())
    monkeypatch.setattr(socket, "getaddrinfo", lambda *args, **kwargs: [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 443)) for ip in ["93.184.216.34", invalid]])
    with pytest.raises(url_fetch.UnsafeUrlError):
        url_fetch.pinned_transport("https://example.org/data")


@pytest.mark.parametrize("commons", [False, True])
def test_f7_fetch_redirect_pins_each_tcp_hop_and_preserves_tls_host(monkeypatch, commons):
    import socket

    from httpcore._backends.sync import SyncBackend

    from app.services import material_search

    host = "upload.wikimedia.org" if commons else "example.org"
    dns, tcp, tls, requests, closed = [], [], [], [], []
    def resolve(name, port, **kwargs):
        dns.append(name)
        assert name == host
        address = "93.184.216.34" if len(dns) == 1 else "1.1.1.1"
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, port))]
    class Stream:
        def __init__(self, redirect):
            self.body = (b"HTTP/1.1 302 Found\r\nLocation: /next\r\nContent-Length: 0\r\n\r\n" if redirect
                         else b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok")
        def read(self, max_bytes, timeout=None):
            body, self.body = self.body, b""
            return body
        def write(self, data, timeout=None):
            requests.append(data)
        def start_tls(self, ssl_context, server_hostname=None, timeout=None):
            assert ssl_context.check_hostname
            tls.append(server_hostname)
            return self
        def get_extra_info(self, info):
            return None
        def close(self):
            closed.append(True)
    def connect(self, name, port, **kwargs):
        tcp.append((name, port))
        return Stream(len(tcp) == 1)
    monkeypatch.setattr(socket, "getaddrinfo", resolve)
    monkeypatch.setattr(SyncBackend, "connect_tcp", connect)
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:8888")
    fetch = material_search.commons_fetch if commons else url_fetch.bounded_safe_fetch
    if commons:
        result = fetch(f"https://{host}/image.png", 100)
    else:
        result = fetch(f"https://{host}/data", max_bytes=100)
    assert result[0] == b"ok"
    assert dns == [host, host]
    assert tcp == [("93.184.216.34", 443), ("1.1.1.1", 443)]
    assert tls == [host, host]
    assert sum(b"Host: " + host.encode() in request for request in requests) == 2
    assert len(closed) >= 2


def test_f7_bounded_fetch_stops_reading_oversize_stream(monkeypatch):
    yielded = []

    class Chunks(httpx.SyncByteStream):
        def __iter__(self):
            for chunk in (b"1234", b"56", b"secret-late-chunk"):
                yielded.append(chunk)
                yield chunk

    transport = httpx.MockTransport(lambda request: httpx.Response(200, stream=Chunks()))
    real_client = httpx.Client
    monkeypatch.setattr(url_fetch.httpx, "Client", lambda **kwargs: real_client(**(kwargs | {"transport": transport})))
    monkeypatch.setattr(url_fetch, "pinned_transport", lambda url: None)

    with pytest.raises(url_fetch.UnsafeUrlError, match="响应超过大小限制"):
        url_fetch.bounded_safe_fetch("https://example.org/data", max_bytes=5)
    assert yielded == [b"1234", b"56"]


@pytest.mark.parametrize("encoding", ["gzip", "br", "deflate", "identity, gzip"])
def test_f7_bounded_fetch_refuses_compression_before_read(monkeypatch, encoding):
    read = []
    class Body(httpx.SyncByteStream):
        def __iter__(self):
            read.append(True)
            yield b"private-compressed-body"
    real_client = httpx.Client
    monkeypatch.setattr(url_fetch.httpx, "Client", lambda **kwargs: real_client(**(kwargs | {"transport": httpx.MockTransport(
        lambda request: httpx.Response(200, stream=Body(), headers={"content-encoding": encoding}))})))
    monkeypatch.setattr(url_fetch, "pinned_transport", lambda url: None)
    with pytest.raises(url_fetch.UnsafeUrlError, match="压缩"):
        url_fetch.bounded_safe_fetch("https://example.org/data")
    assert not read


def test_f7_bounded_fetch_forces_identity_without_changing_caller_headers(monkeypatch):
    original = {"aCcEpT-EnCoDiNg": "gzip", "Authorization": "Bearer isolated-secret"}
    def respond(request):
        assert request.headers["accept-encoding"] == "identity"
        assert request.headers["authorization"] == original["Authorization"]
        return httpx.Response(200, content=b"ok")
    real_client = httpx.Client
    monkeypatch.setattr(url_fetch.httpx, "Client", lambda **kwargs: real_client(**(kwargs | {"transport": httpx.MockTransport(respond)})))
    monkeypatch.setattr(url_fetch, "pinned_transport", lambda url: None)
    assert url_fetch.bounded_safe_fetch("https://example.org/data", headers=original)[0] == b"ok"
    assert original["aCcEpT-EnCoDiNg"] == "gzip"


def test_f7_bounded_fetch_has_total_read_deadline(monkeypatch):
    ticks, read = [0], []
    class Body(httpx.SyncByteStream):
        def __iter__(self):
            for index in range(100):
                ticks[0] += 6
                read.append(index)
                yield b"x"
    real_client = httpx.Client
    monkeypatch.setattr(url_fetch.httpx, "Client", lambda **kwargs: real_client(**(kwargs | {"transport": httpx.MockTransport(
        lambda request: httpx.Response(200, stream=Body()))})))
    monkeypatch.setattr(url_fetch, "pinned_transport", lambda url: None)
    monkeypatch.setattr(url_fetch, "time", type("Clock", (), {"monotonic": staticmethod(lambda: ticks[0])}), raising=False)
    with pytest.raises(url_fetch.UnsafeUrlError, match="时限"):
        url_fetch.bounded_safe_fetch("https://example.org/data")
    assert read == [0, 1]


@pytest.mark.parametrize("status", [200, 302])
def test_f7_deadline_rejects_empty_body_or_next_redirect(monkeypatch, status):
    ticks, calls = [0], []
    def respond(request):
        calls.append(True)
        ticks[0] += 11
        return httpx.Response(status, content=b"", headers={"location": "https://example.org/next"})
    real_client = httpx.Client
    monkeypatch.setattr(url_fetch.httpx, "Client", lambda **kwargs: real_client(**(kwargs | {"transport": httpx.MockTransport(respond)})))
    monkeypatch.setattr(url_fetch, "pinned_transport", lambda url: None)
    monkeypatch.setattr(url_fetch, "time", type("Clock", (), {"monotonic": staticmethod(lambda: ticks[0])}), raising=False)
    with pytest.raises(url_fetch.UnsafeUrlError, match="时限"):
        url_fetch.bounded_safe_fetch("https://example.org/data")
    assert calls == [True]


@pytest.mark.parametrize("destination", ["https://other.example/data", "http://example.org/data"])
def test_f7_bounded_fetch_rejects_cross_origin_or_downgrade_before_sending_headers(monkeypatch, destination):
    seen = []
    def handler(request):
        seen.append(str(request.url))
        return httpx.Response(302, headers={"location": destination})
    real_client = httpx.Client
    monkeypatch.setattr(url_fetch.httpx, "Client", lambda **kwargs: real_client(**(kwargs | {"transport": httpx.MockTransport(handler)})))
    monkeypatch.setattr(url_fetch, "pinned_transport", lambda url: None)
    with pytest.raises(url_fetch.UnsafeUrlError, match="重定向目标"):
        url_fetch.bounded_safe_fetch("https://example.org/data", headers={"Authorization": "Bearer isolated-secret"})
    assert seen == ["https://example.org/data"]


def test_f7_mapped_pull_rejects_overfull_page_before_source_write(db_session, monkeypatch):
    user = User(email="data-admin@studio.local", name="Admin", role="admin")
    connector = Connector(name="API", base_url="https://example.org", auth_style="none")
    db_session.add_all((user, connector))
    db_session.flush()
    endpoint = ConnectorEndpoint(
        connector_id=connector.id, name="daily", path="/daily", method="GET", title_template="daily",
        pagination_json={"type": "page", "max_pages": 1, "page_size": 500},
        fact_mapping_json={"items_path": "rows", "statement": "{name}", "fields": {"value": "{value}"}},
    )
    db_session.add(endpoint)
    db_session.commit()
    monkeypatch.setattr(connector_service, "bounded_safe_fetch", lambda *args, **kwargs: (
        json.dumps({"rows": [{"name": "row", "value": i} for i in range(501)]}).encode(), "application/json",
    ))
    with pytest.raises(connector_service.ConnectorError, match="connector_response_item_limit"):
        connector_service.pull_endpoint(db_session, endpoint, user, dedup_mode="mapped_facts", bounded=True)
    assert db_session.query(SourceDocument).count() == 0
