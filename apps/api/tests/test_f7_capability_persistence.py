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
    SourceDocument,
    User,
)
from app.services import capability_integrations, connector_service, delivery, url_fetch
from app.services.capability_integrations import append_verification, is_verified_for_scope
from app.services.content_harness.registry import PluginRegistry


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
    calls = []
    payload = {"rows": [{"name": "rate", "value": 4}]}

    def fake_fetch(url, *args, **kwargs):
        calls.append(url)
        return json.dumps(payload).encode(), "application/json"

    monkeypatch.setattr(connector_service, "bounded_safe_fetch", fake_fetch, raising=False)
    monkeypatch.setattr(connector_service, "safe_fetch", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("legacy fetch used")))
    probe = client.post(probe_path, headers=admin)
    assert probe.status_code == 200, probe.text
    assert probe.json()["verified"] is True
    assert calls == ["https://example.org/daily"]
    assert client.get(inventory_path, headers=viewer).json()[0]["executable"] is True
    assert calls == ["https://example.org/daily"]
    pulled = client.post(pull_path, headers=admin)
    assert pulled.status_code == 200, pulled.text
    assert client.post(probe_path, headers=admin).status_code == 200
    def failing_fetch(url, *args, **kwargs):
        raise RuntimeError("secret-example-provider-response")

    monkeypatch.setattr(connector_service, "bounded_safe_fetch", failing_fetch)
    failed = client.post(pull_path, headers=admin)
    assert failed.status_code == 502
    assert "secret-example-provider-response" not in failed.text
    assert db_session.get(ConnectorEndpoint, endpoint.id).last_pull_error == "connector_pull_failed"
    monkeypatch.setattr(connector_service, "safe_fetch", fake_fetch)
    assert client.post(f"/api/v1/endpoints/{endpoint.id}/pull", headers=admin).status_code == 200
    assert client.get(inventory_path, headers=viewer).json()[0]["executable"] is False
    assert client.post(pull_path, headers=admin).status_code == 409
    assert client.post(probe_path, headers=admin).status_code == 502
    monkeypatch.setattr(connector_service, "bounded_safe_fetch", fake_fetch)
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


def test_f7_bounded_fetch_stops_reading_oversize_stream(monkeypatch):
    yielded = []

    class Chunks(httpx.SyncByteStream):
        def __iter__(self):
            for chunk in (b"1234", b"56", b"secret-late-chunk"):
                yielded.append(chunk)
                yield chunk

    transport = httpx.MockTransport(lambda request: httpx.Response(200, stream=Chunks()))
    real_client = httpx.Client
    monkeypatch.setattr(url_fetch.httpx, "Client", lambda **kwargs: real_client(transport=transport, **kwargs))
    monkeypatch.setattr(url_fetch, "_validate_target", lambda url: None)

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
    monkeypatch.setattr(url_fetch.httpx, "Client", lambda **kwargs: real_client(transport=httpx.MockTransport(
        lambda request: httpx.Response(200, stream=Body(), headers={"content-encoding": encoding})), **kwargs))
    monkeypatch.setattr(url_fetch, "_validate_target", lambda url: None)
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
    monkeypatch.setattr(url_fetch.httpx, "Client", lambda **kwargs: real_client(transport=httpx.MockTransport(respond), **kwargs))
    monkeypatch.setattr(url_fetch, "_validate_target", lambda url: None)
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
    monkeypatch.setattr(url_fetch.httpx, "Client", lambda **kwargs: real_client(transport=httpx.MockTransport(
        lambda request: httpx.Response(200, stream=Body())), **kwargs))
    monkeypatch.setattr(url_fetch, "_validate_target", lambda url: None)
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
    monkeypatch.setattr(url_fetch.httpx, "Client", lambda **kwargs: real_client(transport=httpx.MockTransport(respond), **kwargs))
    monkeypatch.setattr(url_fetch, "_validate_target", lambda url: None)
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
    monkeypatch.setattr(url_fetch.httpx, "Client", lambda **kwargs: real_client(transport=httpx.MockTransport(handler), **kwargs))
    monkeypatch.setattr(url_fetch, "_validate_target", lambda url: None)
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
