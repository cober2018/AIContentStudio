"""Retained MCP route boundaries against isolated data and storage."""

import json
import re
from contextlib import ExitStack, contextmanager
from types import SimpleNamespace

import pytest
from sqlalchemy import event, select
from sqlalchemy.orm import sessionmaker

ENDPOINT = "/api/v1/creative-mcp"
PROTOCOL = "2025-11-25"
TOKEN = "synthetic-r2-mcp-token-with-no-real-credential-0001"
TOOL_NAMES = {
    "get_context", "get_package", "get_execution", "find_capabilities", "use_capability",
    "claim_execution", "start_execution", "materialize_inputs", "report_progress",
    "report_blocker", "report_checkpoint", "submit_output", "mark_unknown",
    "reconcile_unknown", "request_human_review",
}
READ_ONLY_TOOLS = {"get_context", "get_package", "get_execution", "find_capabilities"}
FORBIDDEN_TOOLS = (
    "approve_candidate", "approve", "freeze_candidate", "publish", "publish_content",
    "wechat_draft", "deliver", "create_delivery_target", "execute_delivery",
    "save_master", "MasterSave", "accept_output", "bind_output", "read_file",
    "write_file", "execute_sql", "not_a_tool",
)


def _seed_context(db, owner, label):
    from app.models import (
        ContentMasterRevision,
        ContentPersona,
        ContentProject,
        ContentUnit,
        CreativeBriefRevision,
    )

    persona = ContentPersona(owner_user_id=owner.id, name=f"{label} persona")
    project = ContentProject(owner_user_id=owner.id, title=f"{label} project")
    db.add_all([persona, project])
    db.flush()
    unit = ContentUnit(project_id=project.id, persona_id=persona.id, modality="text", title=f"{label} unit")
    db.add(unit)
    db.flush()
    brief = CreativeBriefRevision(project_id=project.id, revision_no=1,
        objective=f"{label} private brief", checksum="b" * 64)
    db.add(brief)
    db.flush()
    master = ContentMasterRevision(project_id=project.id, content_unit_id=unit.id, revision_no=1,
        modality="text", payload_schema="text.v1", payload_json={"markdown": f"{label} private manuscript"},
        payload_hash="a" * 64, context_hash="c" * 64, creative_brief_revision_id=brief.id,
        source_kind="manual", idempotency_key=f"{label}-seed", request_fingerprint="d" * 64)
    db.add(master)
    db.commit()
    return SimpleNamespace(project=project, unit=unit, brief=brief, master=master)


@pytest.fixture(autouse=True)
def mcp_environment(db_session, monkeypatch, tmp_path):
    from app import config, db, observability, runtime_config
    from app.models import User
    from app.services import asset_media, creative_execution_files, material_storage
    from app.services.content_harness.registry import registry
    from app.services.generation import providers

    media = tmp_path / "media"
    media.mkdir(mode=0o700)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'import-only.sqlite'}")
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("REQUIRED_SCHEMA_HEAD", "")
    monkeypatch.setenv("AI_STUDIO_MEDIA_ROOT", str(media))
    values = {name: field.default for name, field in config.Settings.model_fields.items()}
    values.update(database_url=f"sqlite:///{tmp_path / 'import-only.sqlite'}", app_env="test")
    isolated = config.Settings(_env_file=None, **values)
    settings = config.get_settings()
    for name in config.Settings.model_fields:
        monkeypatch.setattr(settings, name, getattr(isolated, name))
    monkeypatch.setattr(asset_media, "MEDIA_ROOT", media)
    monkeypatch.setattr(runtime_config, "_OVERRIDES", {})
    monkeypatch.setattr(providers, "_providers", {})
    monkeypatch.setattr(observability, "_METRICS", {})

    # Even an accidental lifespan/create_all must stay on the fixture engine.
    monkeypatch.setattr(db, "engine", db_session.get_bind())
    factory = sessionmaker(bind=db_session.get_bind(), autoflush=False, expire_on_commit=False)
    monkeypatch.setattr(db, "SessionLocal", factory)
    from app import main
    from app.services.creative_mcp import Lifecycle

    monkeypatch.setattr(main, "SessionLocal", factory)
    monkeypatch.setattr(main.app.state, "creative_mcp_lifecycle", Lifecycle(), raising=False)
    monkeypatch.setattr(registry, "_items", {})
    monkeypatch.setattr(registry, "_descriptors", {})
    owner = User(email="r2-mcp-owner@studio.local", name="Owner", role="editor")
    foreign = User(email="r2-mcp-foreign@studio.local", name="Foreign", role="admin")
    db_session.add_all([owner, foreign])
    db_session.commit()
    owned = _seed_context(db_session, owner, "owned")
    other = _seed_context(db_session, foreign, "foreign")
    monkeypatch.setenv("AICS_CREATIVE_MCP_TOKEN", TOKEN)
    monkeypatch.setenv("AICS_CREATIVE_MCP_OWNER_USER_ID", str(owner.id))
    assert str(db.engine.url) == "sqlite://"
    assert material_storage.provider().root == media
    assert creative_execution_files.work_root(owner.id, 1).is_relative_to(media)
    return SimpleNamespace(app=main.app, db=db_session, media=media, owner=owner,
        foreign=foreign, owned=owned, other=other)


@pytest.fixture
def mcp_clients(mcp_environment, monkeypatch):
    from fastapi.testclient import TestClient

    from app.db import get_db

    env = mcp_environment

    def override_db():
        yield env.db

    monkeypatch.setattr(env.app, "dependency_overrides", {**env.app.dependency_overrides, get_db: override_db})
    with ExitStack() as cleanup:
        def make(peer="127.0.0.1", base_url="http://127.0.0.1:8000"):
            # Do not enter TestClient: the production lifespan is outside this route test.
            client = TestClient(env.app, base_url=base_url, client=(peer, 45000), follow_redirects=False)
            cleanup.callback(client.close)
            return client

        yield make


def _rpc(client, method, params=None, *, authorization=f"Bearer {TOKEN}", headers=None, notification=False):
    request_headers = {"Accept": "application/json, text/event-stream", "MCP-Protocol-Version": PROTOCOL}
    if authorization is not None:
        request_headers["Authorization"] = authorization
    request_headers.update(headers or {})
    message = {"jsonrpc": "2.0", "method": method, "params": params or {}}
    if not notification:
        message["id"] = 7
    return client.post(ENDPOINT, json=message, headers=request_headers)


def _assert_response(response, status=200):
    assert response.status_code == status, response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert re.fullmatch(r"[0-9a-f]{32}", response.headers["x-creative-mcp-trace"])
    assert response.headers["x-trace-id"]
    assert TOKEN not in response.text
    if response.content and "error" in response.json():
        assert response.json()["error"]["data"]["trace_id"] == response.headers["x-creative-mcp-trace"]


def _ready(client):
    response = _rpc(client, "initialize", {"protocolVersion": PROTOCOL, "capabilities": {},
        "clientInfo": {"name": "retained-r2-tests", "version": "1"}})
    _assert_response(response)
    result = response.json()["result"]
    assert result["protocolVersion"] == PROTOCOL
    assert result["capabilities"]["tools"] == {"listChanged": False}
    response = _rpc(client, "notifications/initialized", notification=True)
    _assert_response(response, 202)
    assert response.content == b""


def _db_snapshot(db):
    from app.db import Base

    return {table.name: list(db.execute(select(table).order_by(*table.primary_key.columns)).mappings())
        for table in Base.metadata.sorted_tables}


def _files_snapshot(root):
    return {str(path.relative_to(root)): (path.stat().st_mode, path.read_bytes() if path.is_file() else None)
        for path in root.rglob("*")}


@contextmanager
def _no_business_writes(env):
    before = _db_snapshot(env.db)
    files = _files_snapshot(env.media)
    writes, commits = [], []
    engine = env.db.get_bind()

    def record_write(connection, cursor, statement, parameters, context, executemany):
        if (context.isinsert or context.isupdate or context.isdelete or context.isddl
                or re.match(r"\s*(INSERT|UPDATE|DELETE|REPLACE|CREATE|ALTER|DROP)\b", statement, re.IGNORECASE)):
            writes.append(statement)

    def record_commit(session):
        commits.append(True)

    event.listen(engine, "before_cursor_execute", record_write)
    event.listen(env.db, "before_commit", record_commit)
    try:
        yield
    finally:
        event.remove(engine, "before_cursor_execute", record_write)
        event.remove(env.db, "before_commit", record_commit)
    assert writes == []
    assert commits == []
    assert not env.db.new and not env.db.dirty and not env.db.deleted
    assert _db_snapshot(env.db) == before
    assert _files_snapshot(env.media) == files


@pytest.mark.parametrize("peer,base_url,origin", [
    ("127.0.0.1", "http://127.0.0.1:8000", None),
    ("127.0.0.1", "http://localhost:8000", "http://localhost:5173"),
    ("::1", "http://[::1]:8000", "http://[::1]:8000"),
    ("::1", "http://localhost:8000", "https://localhost:8000"),
    ("127.0.0.1", "http://127.0.0.1:8000", "https://127.0.0.1:5173"),
])
def test_loopback_peer_host_and_origin_are_accepted(mcp_environment, mcp_clients, peer, base_url, origin):
    client = mcp_clients(peer, base_url)
    with _no_business_writes(mcp_environment):
        response = _rpc(client, "ping", headers={"Origin": origin} if origin else {})
        _assert_response(response)
        assert response.json() == {"jsonrpc": "2.0", "id": 7, "result": {}}


@pytest.mark.parametrize("peer", ["192.0.2.1", "0.0.0.0", "testclient", "::ffff:192.0.2.1"])
def test_non_loopback_peer_is_rejected_even_with_valid_host_and_token(mcp_environment, mcp_clients, peer):
    with _no_business_writes(mcp_environment):
        response = _rpc(mcp_clients(peer), "ping", headers={"Origin": "http://localhost:5173"})
        _assert_response(response, 403)
        assert response.json()["error"]["data"]["code"] == "creative_mcp_loopback_required"


@pytest.mark.parametrize("header,value,code", [
    ("Host", "example.invalid:8000", "creative_mcp_host_invalid"),
    ("Host", "127.0.0.1:8001", "creative_mcp_host_invalid"),
    ("Host", "localhost", "creative_mcp_host_invalid"),
    ("Host", "localhost:8000@example.invalid", "creative_mcp_host_invalid"),
    ("Host", "::1:8000", "creative_mcp_host_invalid"),
    ("Origin", "https://example.invalid:8000", "creative_mcp_origin_invalid"),
    ("Origin", "null", "creative_mcp_origin_invalid"),
    ("Origin", "http://localhost:8001", "creative_mcp_origin_invalid"),
    ("Origin", "http://localhost:5173/", "creative_mcp_origin_invalid"),
    ("Origin", "http://localhost:5173?redirect=1", "creative_mcp_origin_invalid"),
    ("Origin", "http://user@localhost:5173", "creative_mcp_origin_invalid"),
    ("Forwarded", "for=127.0.0.1;host=localhost:8000", "creative_mcp_headers_invalid"),
    ("X-Forwarded-For", "127.0.0.1", "creative_mcp_headers_invalid"),
    ("X-Real-IP", "127.0.0.1", "creative_mcp_headers_invalid"),
])
def test_host_origin_and_proxy_identity_are_guarded(mcp_environment, mcp_clients, header, value, code):
    with _no_business_writes(mcp_environment):
        response = _rpc(mcp_clients(), "ping", headers={header: value})
        _assert_response(response, 403)
        assert response.json()["error"]["data"]["code"] == code


@pytest.mark.parametrize("authorization", [None, "", "Bearer invalid", f"bearer {TOKEN}", f"Basic {TOKEN}",
    f"Bearer {TOKEN}-wrong"])
def test_missing_or_invalid_bearer_does_not_use_header_identity(mcp_environment, mcp_clients, authorization):
    with _no_business_writes(mcp_environment):
        response = _rpc(mcp_clients(), "ping", authorization=authorization,
            headers={"X-Studio-User": mcp_environment.foreign.email, "X-Studio-Role": "admin"})
        _assert_response(response, 401)
        assert response.headers["www-authenticate"] == 'Bearer realm="aics-creative-mcp"'
        assert response.json()["error"]["data"]["code"] == "creative_mcp_unauthorized"


@pytest.mark.parametrize("setting,value", [
    ("AICS_CREATIVE_MCP_TOKEN", ""),
    ("AICS_CREATIVE_MCP_TOKEN", "too-short"),
    ("AICS_CREATIVE_MCP_OWNER_USER_ID", ""),
    ("AICS_CREATIVE_MCP_OWNER_USER_ID", "0"),
])
def test_missing_explicit_token_or_owner_fails_closed(mcp_environment, mcp_clients, monkeypatch, setting, value):
    monkeypatch.setenv(setting, value)
    with _no_business_writes(mcp_environment):
        response = _rpc(mcp_clients(), "ping", headers={"X-Studio-User": mcp_environment.foreign.email})
        _assert_response(response, 503)
        assert response.json()["error"]["data"]["code"] == "creative_mcp_not_configured"


@pytest.mark.parametrize("owner_state", ["absent", "inactive", "viewer", "reviewer"])
def test_token_requires_an_existing_active_editor_or_admin(mcp_environment, mcp_clients, monkeypatch, owner_state):
    env = mcp_environment
    if owner_state == "absent":
        monkeypatch.setenv("AICS_CREATIVE_MCP_OWNER_USER_ID", "900001")
    elif owner_state == "inactive":
        env.owner.is_active = False
    else:
        env.owner.role = owner_state
    env.db.commit()
    with _no_business_writes(env):
        response = _rpc(mcp_clients(), "ping", headers={"X-Studio-User": env.foreign.email, "X-Studio-Role": "admin"})
        _assert_response(response, 403)
        assert response.json()["error"]["data"]["code"] == "creative_mcp_owner_unavailable"


@pytest.mark.parametrize("transport", ["tool", "resource"])
def test_correct_token_reads_only_the_explicit_owners_context(mcp_environment, mcp_clients, transport):
    env, client = mcp_environment, mcp_clients()
    with _no_business_writes(env):
        _ready(client)
        params = {"project_id": env.owned.project.id, "unit_id": env.owned.unit.id}
        headers = {"X-Studio-User": env.foreign.email, "X-Studio-Role": "admin"}
        if transport == "tool":
            response = _rpc(client, "tools/call", {"name": "get_context", "arguments": params}, headers=headers)
            _assert_response(response)
            result = response.json()["result"]
            assert result["isError"] is False
            data = result["structuredContent"]
            assert json.loads(result["content"][0]["text"]) == data
        else:
            uri = f"aics://projects/{params['project_id']}/units/{params['unit_id']}/context"
            response = _rpc(client, "resources/read", {"uri": uri}, headers=headers)
            _assert_response(response)
            contents = response.json()["result"]["contents"]
            assert len(contents) == 1 and contents[0]["uri"] == uri
            data = json.loads(contents[0]["text"])
        assert data["project"]["id"] == env.owned.project.id
        assert data["unit"]["id"] == env.owned.unit.id
        assert data["brief"]["objective"] == env.owned.brief.objective
        assert data["master"]["id"] == env.owned.master.id
        assert "foreign private" not in response.text


def test_tools_list_is_the_exact_restricted_whitelist(mcp_environment, mcp_clients):
    client = mcp_clients()
    with _no_business_writes(mcp_environment):
        _ready(client)
        response = _rpc(client, "tools/list")
        _assert_response(response)
        tools = response.json()["result"]["tools"]
        names = [tool["name"] for tool in tools]
        assert len(names) == 15 and set(names) == TOOL_NAMES
        assert not set(names).intersection(FORBIDDEN_TOOLS)
        for tool in tools:
            readonly = tool["name"] in READ_ONLY_TOOLS
            assert tool["annotations"] == {"readOnlyHint": readonly, "destructiveHint": not readonly,
                "idempotentHint": readonly, "openWorldHint": False}
            assert tool["inputSchema"]["additionalProperties"] is False


@pytest.mark.parametrize("name", FORBIDDEN_TOOLS)
def test_unknown_and_forbidden_tools_are_rejected_without_writes(mcp_environment, mcp_clients, name):
    env, client = mcp_environment, mcp_clients()
    with _no_business_writes(env):
        _ready(client)
        arguments = {
            "project_id": env.owned.project.id, "unit_id": env.owned.unit.id,
            "idempotency_key": "forbidden-call", "payload": {"markdown": "must never be saved"},
        }
        if name in {"read_file", "write_file"}:
            arguments = {"path": str(env.media / "unrelated.txt"), "content": "must never be written"}
        elif name == "execute_sql":
            arguments = {"sql": "DELETE FROM content_master_revision"}
        response = _rpc(client, "tools/call", {"name": name, "arguments": arguments})
        _assert_response(response)
        message = response.json()
        assert message["id"] == 7 and "result" not in message
        assert message["error"]["code"] == -32602
        assert message["error"]["data"]["code"] == "creative_mcp_unknown_tool"
        assert message["error"]["data"]["category"] == "invalid_arguments"


@pytest.mark.parametrize("transport", ["tool", "resource"])
@pytest.mark.parametrize("scope", ["foreign", "mixed"])
def test_foreign_context_is_denied_before_content_reads_or_serialization(mcp_environment, mcp_clients, transport, scope):
    env, client = mcp_environment, mcp_clients()
    _ready(client)
    project_id = env.other.project.id if scope == "foreign" else env.owned.project.id
    unit_id = env.other.unit.id
    statements = []

    def record_read(connection, cursor, statement, parameters, context, executemany):
        statements.append(statement.lower())

    with _no_business_writes(env):
        engine = env.db.get_bind()
        event.listen(engine, "before_cursor_execute", record_read)
        try:
            headers = {"X-Studio-User": env.foreign.email, "X-Studio-Role": "admin"}
            if transport == "tool":
                response = _rpc(client, "tools/call", {"name": "get_context", "arguments": {
                    "project_id": project_id, "unit_id": unit_id}}, headers=headers)
                _assert_response(response)
                result = response.json()["result"]
                assert result["isError"] is True
                data = result["structuredContent"]
                assert json.loads(result["content"][0]["text"]) == data
                assert data["status"] == 404
            else:
                response = _rpc(client, "resources/read",
                    {"uri": f"aics://projects/{project_id}/units/{unit_id}/context"}, headers=headers)
                _assert_response(response)
                message = response.json()
                assert set(message) == {"jsonrpc", "id", "error"}
                assert message["jsonrpc"] == "2.0" and message["id"] == 7
                assert message["error"]["code"] == -32000
                assert message["error"]["message"] == "not_found"
                data = message["error"]["data"]
                assert set(data) == {"code", "category", "trace_id"}
        finally:
            event.remove(engine, "before_cursor_execute", record_read)
        assert data["code"] == "creative_domain_not_found"
        assert data["category"] == "not_found"
        assert "project" not in data and "master" not in data and "brief" not in data
        for table in ("creative_brief_revision", "content_master_revision", "project_fact_boundary_revision"):
            assert not any(table in statement for statement in statements), statements
        assert env.other.brief.objective not in response.text
        assert "foreign private manuscript" not in response.text


@pytest.mark.parametrize("inventory", ["tools/list", "resources/list", "resources/templates/list", "status", "capabilities"])
def test_inventory_is_readonly_with_zero_business_writes(mcp_environment, mcp_clients, inventory):
    env, client = mcp_environment, mcp_clients()
    with _no_business_writes(env):
        _ready(client)
        if inventory == "status":
            response = _rpc(client, "resources/read", {"uri": "aics://creative-mcp/status"})
        elif inventory == "capabilities":
            response = _rpc(client, "tools/call", {"name": "find_capabilities", "arguments": {
                "project_id": env.owned.project.id, "unit_id": env.owned.unit.id}})
        else:
            response = _rpc(client, inventory)
        _assert_response(response)
        result = response.json()["result"]
        if inventory == "tools/list":
            assert {tool["name"] for tool in result["tools"]} == TOOL_NAMES
        elif inventory == "resources/list":
            assert [resource["uri"] for resource in result["resources"]] == ["aics://creative-mcp/status"]
        elif inventory == "resources/templates/list":
            assert {item["name"] for item in result["resourceTemplates"]} == {"context", "package", "execution", "capabilities"}
        elif inventory == "status":
            status = json.loads(result["contents"][0]["text"])
            assert status["transport_sessions"] is False
            assert status["capability_memory"] == {"available": True, "execution": False,
                "explicit_selection_required": True, "code": None}
        else:
            assert result["isError"] is False
            assert result["structuredContent"] == {"items": [], "total": 0, "limit": 20, "offset": 0}
