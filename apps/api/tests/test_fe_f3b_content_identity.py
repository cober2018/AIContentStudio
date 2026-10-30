"""FE-F3B identity hierarchy, revision, snapshot and production contracts."""

import pytest
from sqlalchemy import inspect

from app.models import BrandVoiceVersion, ContentUnit, IdentitySnapshot


@pytest.mark.parametrize("archived_kind", ["brand", "persona", "account"])
def test_publisher_connection_readonly_includes_full_ancestry(client, db_session, archived_kind):
    from app.models import ContentBrand, ContentPersona

    headers, persona_id, account_id = _publisher_account(client, db_session)
    persona = db_session.get(ContentPersona, persona_id)
    brand = ContentBrand(owner_user_id=persona.owner_user_id, name="品牌")
    db_session.add(brand)
    db_session.flush()
    persona.brand_id = brand.id
    db_session.commit()
    path = f"/api/v1/content-accounts/{account_id}/publisher-connection"
    assert client.get(path, headers=headers).json().get("read_only") is False
    entity_id = {"brand": brand.id, "persona": persona_id, "account": account_id}[archived_kind]
    root = {"brand": "content-brands", "persona": "content-personas", "account": "content-accounts"}[archived_kind]
    assert client.delete(f"/api/v1/{root}/{entity_id}", headers=headers).status_code == 204
    assert client.get(path, headers=headers).json()["read_only"] is True
    assert client.put(path, headers=headers, json={"expected_revision": 0, "enabled": True, "credential_version": "v1"}).status_code == 409


def _publisher_account(client, db_session, email="publisher@studio.local"):
    from app.models import User

    headers = {"X-Studio-User": email}
    persona = client.post("/api/v1/content-personas", json={"name": "作者"}, headers=headers).json()
    user = db_session.query(User).filter_by(email=email).one()
    user.role = "admin"
    db_session.commit()
    account = client.post(f"/api/v1/content-personas/{persona['id']}/accounts", json={"name": "公众号"}, headers=headers).json()
    return headers, persona["id"], account["id"]


def test_official_account_binding_is_owned_idempotent_and_not_verification(client, db_session):
    headers, persona_id, account_id = _publisher_account(client, db_session)
    path = f"/api/v1/content-accounts/{account_id}/platform-binding"
    payload = {"platform_channel": "wechat", "platform_account_id": "wx0123456789abcdef"}
    first = client.put(path, json=payload, headers=headers)
    assert first.status_code == 200, first.text
    assert first.json()["platform_account_id"] == payload["platform_account_id"]
    assert first.json()["persona_id"] == persona_id
    assert first.json()["platform_binding_state"] == "bound_unverified"
    assert client.put(path, json=payload, headers=headers).json() == first.json()
    assert client.get(f"/api/v1/content-personas/{persona_id}/accounts", headers=headers).json()[0]["platform_binding_state"] == "bound_unverified"
    assert client.put(path, json={**payload, "platform_account_id": "wx1123456789abcdef"}, headers=headers).status_code == 409
    assert client.get(f"/api/v1/content-accounts/{account_id}", headers=headers).json()["platform_account_id"] == payload["platform_account_id"]


def test_real_account_exclusivity_survives_archive_and_cross_owner(client, db_session):
    first_headers, _, first_id = _publisher_account(client, db_session)
    other_headers, _, other_id = _publisher_account(client, db_session, "other@studio.local")
    payload = {"platform_channel": "wechat", "platform_account_id": "wx0123456789abcdef"}
    assert client.put(f"/api/v1/content-accounts/{first_id}/platform-binding", json=payload, headers=first_headers).status_code == 200
    conflict = client.put(f"/api/v1/content-accounts/{other_id}/platform-binding", json=payload, headers=other_headers)
    assert conflict.status_code == 409 and conflict.json()["detail"] == "platform_identity_conflict"
    assert client.delete(f"/api/v1/content-accounts/{first_id}", headers=first_headers).status_code == 204
    assert client.put(f"/api/v1/content-accounts/{other_id}/platform-binding", json=payload, headers=other_headers).status_code == 409
    assert client.get(f"/api/v1/content-accounts/{other_id}", headers=other_headers).json()["platform_account_id"] is None
    assert client.put(f"/api/v1/content-accounts/{first_id}/platform-binding", json=payload, headers=other_headers).status_code == 404


def test_binding_rejects_editor_viewer_archived_parent_and_sensitive_input(client, db_session):
    from app.models import User

    headers, persona_id, account_id = _publisher_account(client, db_session)
    user = db_session.query(User).filter_by(email=headers["X-Studio-User"]).one()
    path = f"/api/v1/content-accounts/{account_id}/platform-binding"
    payload = {"platform_channel": "wechat", "platform_account_id": "wx0123456789abcdef"}
    for role in ("editor", "viewer"):
        user.role = role
        db_session.commit()
        assert client.put(path, json=payload, headers=headers).status_code == 403
    user.role = "admin"
    db_session.commit()
    for bad in ({**payload, "secret": "do-not-echo-secret"}, {**payload, "platform_account_id": "do-not-echo-secret"}, {**payload, "platform_channel": "x"}):
        response = client.put(path, json=bad, headers=headers)
        assert response.status_code == 422
        assert "do-not-echo-secret" not in response.text
    assert client.delete(f"/api/v1/content-personas/{persona_id}", headers=headers).status_code == 204
    assert client.put(path, json=payload, headers=headers).status_code == 409


def test_platform_binding_database_constraints_and_two_accounts(db_session):
    import pytest
    from sqlalchemy.exc import IntegrityError

    from app.models import ContentAccount, ContentPersona, User

    user = User(email="constraints@studio.local", name="owner", role="admin")
    db_session.add(user)
    db_session.flush()
    persona = ContentPersona(owner_user_id=user.id, name="作者")
    db_session.add(persona)
    db_session.commit()
    for fields in ({"platform_channel": "wechat"}, {"platform_account_id": "wx0123456789abcdef"}):
        row = ContentAccount(persona_id=persona.id, name="invalid")
        for key, value in fields.items():
            setattr(row, key, value)
        db_session.add(row)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()
    for appid in ("wx0123456789abcdef", "wx1123456789abcdef"):
        row = ContentAccount(persona_id=persona.id, name="independent")
        row.platform_channel = "wechat"
        row.platform_account_id = appid
        db_session.add(row)
    db_session.commit()
    duplicate = ContentAccount(persona_id=persona.id, name="duplicate")
    duplicate.platform_channel = "wechat"
    duplicate.platform_account_id = "wx0123456789abcdef"
    db_session.add(duplicate)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
    assert db_session.query(ContentAccount).count() == 2


def test_platform_binding_malformed_json_never_echoes_credentials(client, db_session):
    headers, _, account_id = _publisher_account(client, db_session)
    path = f"/api/v1/content-accounts/{account_id}/platform-binding"
    for raw in ('["sensitive-secret"]', '"sensitive-secret"', '{"secret":"sensitive-secret"'):
        response = client.put(path, content=raw, headers={**headers, "Content-Type": "application/json"})
        assert response.status_code == 422
        assert "sensitive-secret" not in response.text


def test_account_connection_is_safe_cas_and_account_isolated(client, db_session, monkeypatch):
    from app.models import SystemSetting

    headers, persona_id, first_id = _publisher_account(client, db_session)
    second_id = client.post(f"/api/v1/content-personas/{persona_id}/accounts", json={"name": "第二账号"}, headers=headers).json()["id"]
    for account_id, appid in ((first_id, "wx0123456789abcdef"), (second_id, "wx1123456789abcdef")):
        assert client.put(f"/api/v1/content-accounts/{account_id}/platform-binding", json={"platform_channel": "wechat", "platform_account_id": appid}, headers=headers).status_code == 200
    body = {"expected_revision": 0, "enabled": True, "credential_version": "credential-v1"}
    path = f"/api/v1/content-accounts/{first_id}/publisher-connection"
    first = client.put(path, json=body, headers=headers)
    assert first.status_code == 200, first.text
    assert first.json()["revision"] == 1
    assert first.json()["credential_ref"] == f"AICS_WECHAT_ACCOUNT_{first_id}_APPSECRET"
    assert first.json()["verified"] is False and first.json()["executable"] is False
    assert first.json()["unavailable_reason"] == "official_contract_unresolved"
    monkeypatch.setenv(first.json()["credential_ref"], "private-account-secret")
    assert "private-account-secret" not in client.get(path, headers=headers).text
    assert client.put(path, json=body, headers=headers).status_code == 409
    assert client.put(f"/api/v1/content-accounts/{second_id}/publisher-connection", json=body, headers=headers).status_code == 200
    second_before = client.get(f"/api/v1/content-accounts/{second_id}/publisher-connection", headers=headers).json()
    rotated = client.put(path, json={**body, "expected_revision": 1, "credential_version": "credential-v2"}, headers=headers)
    assert rotated.status_code == 200 and rotated.json()["revision"] == 2
    assert client.get(f"/api/v1/content-accounts/{second_id}/publisher-connection", headers=headers).json() == second_before
    assert all("private-account-secret" not in str(row.value) for row in db_session.query(SystemSetting).all())


def test_connection_rejects_unbound_foreign_viewer_and_secret_input(client, db_session):
    from app.models import User

    headers, _, account_id = _publisher_account(client, db_session)
    foreign, _, _ = _publisher_account(client, db_session, "foreign-publisher@studio.local")
    path = f"/api/v1/content-accounts/{account_id}/publisher-connection"
    payload = {"expected_revision": 0, "enabled": True, "credential_version": "v1"}
    assert client.put(path, json=payload, headers=headers).status_code == 409
    assert client.put(path, json=payload, headers=foreign).status_code == 404
    assert client.get(path, headers=foreign).status_code == 404
    user = db_session.query(User).filter_by(email=headers["X-Studio-User"]).one()
    user.role = "viewer"
    db_session.commit()
    assert client.get(path, headers=headers).status_code == 200
    assert client.put(path, json=payload, headers=headers).status_code == 403
    user.role = "admin"
    db_session.commit()
    for bad in ({**payload, "secret": "private-key"}, {**payload, "credential_ref": "OTHER_ACCOUNT_SECRET"}, {**payload, "credential_version": "private-key?token=private-key"}):
        response = client.put(path, json=bad, headers=headers)
        assert response.status_code == 422 and "private-key" not in response.text


def _concurrent_platform_binding(url):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from fastapi import HTTPException
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from app.models import ContentAccount, ContentPersona, User
    from app.services.content_identity import bind_platform_account

    engine = create_engine(url)
    with Session(engine) as db:
        user = User(email="race@studio.local", name="race", role="admin")
        db.add(user)
        db.flush()
        personas = [ContentPersona(owner_user_id=user.id, name=f"Persona {i}") for i in range(2)]
        db.add_all(personas)
        db.flush()
        accounts = [ContentAccount(persona_id=persona.id, name="独立账号") for persona in personas]
        db.add_all(accounts)
        db.commit()
        user_id = user.id
        ids = [account.id for account in accounts]
    barrier = Barrier(2)

    def bind(account_id):
        with Session(engine) as db:
            user = db.get(User, user_id)
            barrier.wait(timeout=10)
            try:
                bind_platform_account(db, user, account_id, channel="wechat", platform_account_id="wx0123456789abcdef")
                return 200
            except HTTPException as exc:
                return exc.status_code

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(bind, ids))
        assert sorted(outcomes) == [200, 409]
        with Session(engine) as db:
            rows = db.query(ContentAccount).filter(ContentAccount.platform_account_id.is_not(None)).all()
            assert len(rows) == 1
            assert rows[0].platform_account_id == "wx0123456789abcdef"
    finally:
        engine.dispose()


def test_platform_binding_actual_sqlite_dual_connection(tmp_path):
    from sqlalchemy import create_engine

    from app.db import Base

    url = f"sqlite:///{tmp_path / 'binding-race.db'}"
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    engine.dispose()
    _concurrent_platform_binding(url)


def test_platform_binding_isolated_postgresql_migration_and_race():
    import importlib.util
    import os
    import uuid
    from pathlib import Path

    import pytest
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy import create_engine, inspect, text
    from sqlalchemy.engine import make_url

    from app.db import Base

    value = os.getenv("AICS_ACCOUNT_TEST_DATABASE_URL")
    if not value:
        pytest.skip("opt-in isolated PostgreSQL gate")
    parsed = make_url(value)
    assert parsed.host == "127.0.0.1" and parsed.port == 15439 and parsed.database == "aics_account_test"
    schema = "account_gate_" + uuid.uuid4().hex
    admin_engine = create_engine(value)
    with admin_engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA {schema}"))
    url = parsed.set(query={**parsed.query, "options": f"-csearch_path={schema}"}).render_as_string(hide_password=False)
    engine = create_engine(url)
    try:
        Base.metadata.create_all(engine)
        from sqlalchemy.orm import Session

        from app.models import ContentAccount, ContentPersona, User

        with Session(engine) as db:
            user = User(email="legacy@studio.local", name="legacy", role="admin")
            db.add(user)
            db.flush()
            persona = ContentPersona(owner_user_id=user.id, name="历史角色")
            db.add(persona)
            db.flush()
            legacy = ContentAccount(persona_id=persona.id, name="历史未绑定账号")
            db.add(legacy)
            db.commit()
            legacy_id = legacy.id
        spec = importlib.util.spec_from_file_location("account_pg_migration", Path("alembic/versions/f7c000000001_account_platform_identity.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with engine.begin() as conn:
            module.op = Operations(MigrationContext.configure(conn))
            indexes = inspect(conn).get_indexes("content_account")
            foreign_keys = inspect(conn).get_foreign_keys("content_account")
            module.downgrade()
            module.upgrade()
            module.downgrade()
            module.upgrade()
            assert inspect(conn).get_indexes("content_account") == indexes
            assert inspect(conn).get_foreign_keys("content_account") == foreign_keys
            assert conn.execute(text("SELECT name, platform_channel, platform_account_id FROM content_account WHERE id=:id"), {"id": legacy_id}).one() == ("历史未绑定账号", None, None)
        _concurrent_platform_binding(url)
        with engine.begin() as conn:
            module.op = Operations(MigrationContext.configure(conn))
            with pytest.raises(RuntimeError, match="retained platform identity"):
                module.downgrade()
            assert conn.execute(text("SELECT COUNT(*) FROM content_account WHERE platform_account_id IS NOT NULL")).scalar_one() == 1
    finally:
        engine.dispose()
        with admin_engine.begin() as conn:
            conn.execute(text(f"DROP SCHEMA {schema} CASCADE"))
        admin_engine.dispose()


def test_identity_tables_exist_without_backfilling_legacy_rows(db_session):
    tables = set(inspect(db_session.bind).get_table_names())
    assert {
        "content_brand", "content_brand_revision", "content_persona_revision",
        "content_account", "content_account_revision", "content_series",
        "content_series_revision", "identity_snapshot",
        "account_workflow_default", "series_workflow_default",
    } <= tables


def test_legacy_persona_unit_run_identity_columns_are_nullable(db_session):
    inspector = inspect(db_session.bind)
    persona = {column["name"]: column for column in inspector.get_columns("content_persona")}
    unit = {column["name"]: column for column in inspector.get_columns("content_unit")}
    run = {column["name"]: column for column in inspector.get_columns("workflow_run")}
    assert persona["brand_id"]["nullable"]
    assert {"account_id", "series_id", "identity_snapshot_id"} <= set(unit)
    assert all(unit[name]["nullable"] for name in ("account_id", "series_id", "identity_snapshot_id"))
    assert run["identity_snapshot_id"]["nullable"]


def test_identity_hierarchy_revisions_and_effective_profile(client):
    alice = {"X-Studio-User": "alice@studio.local"}
    bob = {"X-Studio-User": "bob@studio.local"}
    brand_response = client.post("/api/v1/content-brands", json={"name": "Studio"}, headers=alice)
    assert brand_response.status_code == 201, brand_response.text
    brand_id = brand_response.json()["id"]
    brand_revision = client.post(
        f"/api/v1/content-brands/{brand_id}/revisions",
        json={"expected_revision": 0, "profile": {"target_audience": ["开发者"], "expression_style": {"tone": "calm"}}},
        headers=alice,
    )
    assert brand_revision.status_code == 201, brand_revision.text
    assert client.post(f"/api/v1/content-brands/{brand_id}/revisions", json={"expected_revision": 0, "profile": {}}, headers=alice).status_code == 409
    assert client.post(f"/api/v1/content-brands/{brand_id}/revisions", json={"expected_revision": 1, "profile": {"unknown_field": "x"}}, headers=alice).status_code == 422
    persona_response = client.post(f"/api/v1/content-brands/{brand_id}/personas", json={"name": "创始人"}, headers=alice)
    assert persona_response.status_code == 201, persona_response.text
    persona_id = persona_response.json()["id"]
    account_response = client.post(f"/api/v1/content-personas/{persona_id}/accounts", json={"name": "主号"}, headers=alice)
    assert account_response.status_code == 201, account_response.text
    account_id = account_response.json()["id"]
    assert client.post(f"/api/v1/content-accounts/{account_id}/revisions", json={"expected_revision": 0, "profile": {"target_audience": None}}, headers=alice).status_code == 201
    series_response = client.post(f"/api/v1/content-accounts/{account_id}/series", json={"name": "周刊"}, headers=alice)
    assert series_response.status_code == 201, series_response.text
    series_id = series_response.json()["id"]
    effective = client.get(f"/api/v1/content-identities/effective?persona_id={persona_id}&account_id={account_id}&series_id={series_id}", headers=alice)
    assert effective.status_code == 200, effective.text
    assert effective.json()["effective_profile"]["target_audience"] is None
    assert effective.json()["field_origins"]["target_audience"] == "account"
    assert effective.json()["effective_profile"]["expression_style"] == {"tone": "calm"}
    assert effective.json()["field_origins"]["expression_style"] == "brand"
    assert client.post(f"/api/v1/content-series/{series_id}/revisions", json={"expected_revision": 0, "profile": {"expression_style": {"format": "weekly"}, "target_audience": ["读者"]}}, headers=alice).status_code == 201
    replaced = client.get(f"/api/v1/content-identities/effective?persona_id={persona_id}&account_id={account_id}&series_id={series_id}", headers=alice).json()
    assert replaced["effective_profile"]["expression_style"] == {"format": "weekly"}
    assert replaced["effective_profile"]["target_audience"] == ["读者"]
    assert replaced["field_origins"]["target_audience"] == "series"
    assert client.get(f"/api/v1/content-identities/effective?persona_id={persona_id}", headers=bob).status_code == 404


def test_new_unit_pins_truthful_snapshot_and_legacy_unit_stays_null(client, db_session):
    alice = {"X-Studio-User": "alice@studio.local"}
    persona_id = client.post("/api/v1/content-personas", json={"name": "旧角色"}, headers=alice).json()["id"]
    project_id = client.post("/api/v1/content-projects", json={"title": "身份项目"}, headers=alice).json()["id"]
    created = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "新单元", "persona_id": persona_id, "modality": "text"}, headers=alice)
    assert created.status_code == 201, created.text
    snapshot_id = created.json()["identity_snapshot_id"]
    assert isinstance(snapshot_id, int)
    row = db_session.get(IdentitySnapshot, snapshot_id)
    assert row.persona_id == persona_id
    assert row.brand_id is None and row.persona_revision_id is None
    assert row.effective_profile_json == {}
    snapshot = client.get(f"/api/v1/identity-snapshots/{snapshot_id}", headers=alice)
    assert snapshot.status_code == 200
    assert snapshot.json()["checksum"] == row.checksum
    assert snapshot.json()["readiness"] == "incomplete"
    assert client.get(f"/api/v1/identity-snapshots/{snapshot_id}", headers={"X-Studio-User": "bob@studio.local"}).status_code == 404
    legacy = ContentUnit(project_id=project_id, persona_id=persona_id, modality="text", title="历史单元")
    db_session.add(legacy)
    db_session.commit()
    assert client.get(f"/api/v1/content-projects/{project_id}/units/{legacy.id}", headers=alice).json()["identity_state"] == "legacy_identity"


def test_run_copies_exact_snapshot_and_archived_identity_blocks_new_run(client):
    from test_fe_f2_workflows import _definition

    alice = {"X-Studio-User": "alice@studio.local"}
    persona_id = client.post("/api/v1/content-personas", json={"name": "作者"}, headers=alice).json()["id"]
    project_id = client.post("/api/v1/content-projects", json={"title": "运行身份"}, headers=alice).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "文章", "persona_id": persona_id, "modality": "text"}, headers=alice).json()
    base = f"/api/v1/content-projects/{project_id}/units/{unit['id']}"
    assert client.post(f"{base}/workflow-override", json={"expected_revision": 0, "definition": _definition()}, headers=alice).status_code == 201
    first = client.post(f"{base}/runs", json={"params": {}}, headers=alice)
    assert first.status_code == 201, first.text
    assert first.json()["identity_snapshot_id"] == unit["identity_snapshot_id"]
    assert client.delete(f"/api/v1/content-personas/{persona_id}", headers=alice).status_code == 204
    assert client.get(f"{base}/runs/{first.json()['id']}", headers=alice).status_code == 200
    assert client.post(f"{base}/runs", json={"params": {}}, headers=alice).status_code == 409
    assert client.post(f"{base}/runs/{first.json()['id']}/nodes/a/rerun", headers=alice).status_code == 409
    assert client.post(f"{base}/workflow-override", json={"expected_revision": 1, "definition": _definition()}, headers=alice).status_code == 409


def test_explicit_rebind_updates_in_place_then_replaces_after_run(client):
    from test_fe_f2_workflows import _definition

    alice = {"X-Studio-User": "alice@studio.local"}
    persona_id = client.post("/api/v1/content-personas", json={"name": "作者"}, headers=alice).json()["id"]
    account_id = client.post(f"/api/v1/content-personas/{persona_id}/accounts", json={"name": "主号"}, headers=alice).json()["id"]
    series_id = client.post(f"/api/v1/content-accounts/{account_id}/series", json={"name": "专栏"}, headers=alice).json()["id"]
    project_id = client.post("/api/v1/content-projects", json={"title": "重绑"}, headers=alice).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "稿件", "persona_id": persona_id, "modality": "text"}, headers=alice).json()
    base = f"/api/v1/content-projects/{project_id}/units/{unit['id']}"
    in_place = client.patch(base, json={"account_id": account_id, "series_id": series_id, "rebind_identity": True}, headers=alice)
    assert in_place.status_code == 200, in_place.text
    assert in_place.json()["id"] == unit["id"]
    assert in_place.json()["identity_snapshot_id"] != unit["identity_snapshot_id"]
    assert in_place.json()["series_id"] == series_id
    assert client.post(f"{base}/workflow-override", json={"expected_revision": 0, "definition": _definition()}, headers=alice).status_code == 201
    run = client.post(f"{base}/runs", json={"params": {}}, headers=alice).json()
    old_snapshot = in_place.json()["identity_snapshot_id"]
    replacement = client.patch(base, json={"series_id": None, "rebind_identity": True}, headers=alice)
    assert replacement.status_code == 200, replacement.text
    assert replacement.json()["id"] != unit["id"]
    assert replacement.json()["account_id"] == account_id
    assert replacement.json()["series_id"] is None
    assert replacement.json()["identity_snapshot_id"] != old_snapshot
    assert client.get(base, headers=alice).json()["status"] == "archived"
    assert client.get(f"{base}/runs/{run['id']}", headers=alice).json()["identity_snapshot_id"] == old_snapshot
    assert client.patch(base, json={"rebind_identity": True}, headers=alice).status_code == 409
    events = client.get(f"/api/v1/content-projects/{project_id}/activity", headers=alice).json()["items"]
    replacement_event = next(event for event in events if event["event_type"] == "unit.replaced")
    assert replacement_event["payload"]["old_identity_snapshot_id"] == old_snapshot
    assert replacement_event["payload"]["new_identity_snapshot_id"] == replacement.json()["identity_snapshot_id"]


def test_hierarchical_defaults_pin_new_units_and_preserve_old_ones(client):
    portable = {"nodes": [{"id": "gate", "kind": "Human", "plugin": "builtin.confirm_facts", "config": {}}], "edges": [], "visual_order": ["gate"]}
    alice = {"X-Studio-User": "alice@studio.local"}
    bob = {"X-Studio-User": "bob@studio.local"}
    persona_id = client.post("/api/v1/content-personas", json={"name": "作者"}, headers=alice).json()["id"]
    account_id = client.post(f"/api/v1/content-personas/{persona_id}/accounts", json={"name": "主号"}, headers=alice).json()["id"]
    series_id = client.post(f"/api/v1/content-accounts/{account_id}/series", json={"name": "周刊"}, headers=alice).json()["id"]
    project_id = client.post("/api/v1/content-projects", json={"title": "工作流"}, headers=alice).json()["id"]
    persona = client.post(f"/api/v1/content-personas/{persona_id}/default-workflows/text", json={"expected_revision": 0, "definition": portable}, headers=alice)
    assert persona.status_code == 201, persona.text
    old = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "早期", "persona_id": persona_id, "modality": "text", "account_id": account_id, "series_id": series_id}, headers=alice).json()
    assert old["pinned_workflow_id"] == persona.json()["workflow_id"]
    account = client.post(f"/api/v1/content-accounts/{account_id}/default-workflows/text", json={"expected_revision": 0, "definition": portable}, headers=alice)
    assert account.status_code == 201, account.text
    assert client.post(f"/api/v1/content-accounts/{account_id}/default-workflows/text", json={"expected_revision": 0, "definition": portable}, headers=alice).status_code == 409
    middle = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "中期", "persona_id": persona_id, "modality": "text", "account_id": account_id, "series_id": series_id}, headers=alice).json()
    assert middle["pinned_workflow_id"] == account.json()["workflow_id"]
    series = client.post(f"/api/v1/content-series/{series_id}/default-workflows/text", json={"expected_revision": 0, "definition": portable}, headers=alice)
    assert series.status_code == 201, series.text
    newest = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "近期", "persona_id": persona_id, "modality": "text", "account_id": account_id, "series_id": series_id}, headers=alice).json()
    assert newest["pinned_workflow_id"] == series.json()["workflow_id"]
    assert client.get(f"/api/v1/content-projects/{project_id}/units/{old['id']}", headers=alice).json()["pinned_workflow_id"] == persona.json()["workflow_id"]
    effective = client.get(f"/api/v1/content-identities/effective-workflow?persona_id={persona_id}&account_id={account_id}&series_id={series_id}&modality=text", headers=alice)
    assert effective.status_code == 200 and effective.json()["source"] == "series"


def test_versions_overview_and_typed_brief_identity_scope(client, db_session):
    alice = {"X-Studio-User": "alice@studio.local"}
    bob = {"X-Studio-User": "bob@studio.local"}
    persona_id = client.post("/api/v1/content-personas", json={"name": "作者"}, headers=alice).json()["id"]
    foreign_persona_id = client.post("/api/v1/content-personas", json={"name": "外部"}, headers=bob).json()["id"]
    project_id = client.post("/api/v1/content-projects", json={"title": "身份回读"}, headers=alice).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "稿件", "persona_id": persona_id, "modality": "text"}, headers=alice).json()
    legacy = ContentUnit(project_id=project_id, persona_id=persona_id, modality="text", title="旧稿")
    db_session.add(legacy)
    db_session.commit()
    versions = client.get(f"/api/v1/content-projects/{project_id}/versions", headers=alice).json()
    assert any(row["id"] == str(unit["identity_snapshot_id"]) and row["unitId"] == unit["id"] for row in versions["identitySnapshots"])
    assert any(row["unitId"] == legacy.id and row["status"] == "legacy_identity" for row in versions["identityStates"])
    overview = client.get(f"/api/v1/content-projects/{project_id}/overview", headers=alice).json()
    assert {risk["code"] for risk in overview["risks"]} == {"identity_unready"}
    brief_url = f"/api/v1/content-projects/{project_id}/brief/revisions"
    invalid = client.post(brief_url, json={"expected_revision": 0, "objective": "写文章", "identity_scope": [{"persona_id": foreign_persona_id}]}, headers=alice)
    assert invalid.status_code in {404, 422}
    valid = client.post(brief_url, json={"expected_revision": 0, "objective": "写文章", "identity_scope": [{"persona_id": persona_id}, "传统标签"]}, headers=alice)
    assert valid.status_code == 201, valid.text
    assert valid.json()["identity_scope"] == [{"persona_id": persona_id}, "传统标签"]


def test_snapshot_remains_immutable_after_profile_and_voice_revision(client, db_session):
    alice = {"X-Studio-User": "alice@studio.local"}
    voice = BrandVoiceVersion(name="全局语气", version=1, status="published")
    draft_voice = BrandVoiceVersion(name="未发布", version=1, status="draft")
    db_session.add_all([voice, draft_voice]); db_session.commit()
    brand_id = client.post("/api/v1/content-brands", json={"name": "Studio"}, headers=alice).json()["id"]
    brand_revisions = f"/api/v1/content-brands/{brand_id}/revisions"
    assert client.post(brand_revisions, json={"expected_revision": 0, "profile": {"positioning": "可靠写作", "brand_voice_version_id": voice.id}}, headers=alice).status_code == 201
    assert client.post(brand_revisions, json={"expected_revision": 1, "profile": {"brand_voice_version_id": draft_voice.id}}, headers=alice).status_code == 422
    persona_id = client.post(f"/api/v1/content-brands/{brand_id}/personas", json={"name": "主编"}, headers=alice).json()["id"]
    project_id = client.post("/api/v1/content-projects", json={"title": "快照"}, headers=alice).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "第一版", "persona_id": persona_id, "modality": "text"}, headers=alice).json()
    first = client.get(f"/api/v1/identity-snapshots/{unit['identity_snapshot_id']}", headers=alice).json()
    assert first["brand_voice_version_id"] == voice.id and first["effective_profile"]["positioning"] == "可靠写作"
    assert client.post(brand_revisions, json={"expected_revision": 1, "profile": {"positioning": "新定位", "brand_voice_version_id": voice.id}}, headers=alice).status_code == 201
    assert client.get(f"/api/v1/identity-snapshots/{unit['identity_snapshot_id']}", headers=alice).json() == first
    assert client.get(f"/api/v1/content-identities/effective?persona_id={persona_id}", headers=alice).json()["effective_profile"]["positioning"] == "新定位"
    refreshed = client.patch(f"/api/v1/content-projects/{project_id}/units/{unit['id']}", json={"rebind_identity": True}, headers=alice)
    assert refreshed.status_code == 200
    assert refreshed.json()["identity_snapshot_id"] != first["id"]
    second = client.get(f"/api/v1/identity-snapshots/{refreshed.json()['identity_snapshot_id']}", headers=alice).json()
    assert second["checksum"] != first["checksum"] and second["effective_profile"]["positioning"] == "新定位"
    account_voice = BrandVoiceVersion(name="账号语气", version=1, status="published")
    db_session.add(account_voice); db_session.commit()
    account_id = client.post(f"/api/v1/content-personas/{persona_id}/accounts", json={"name": "主号"}, headers=alice).json()["id"]
    assert client.post(f"/api/v1/content-accounts/{account_id}/revisions", json={"expected_revision": 0, "profile": {"brand_voice_version_id": account_voice.id}}, headers=alice).status_code == 201
    account_unit = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "账号稿", "persona_id": persona_id, "account_id": account_id, "modality": "text"}, headers=alice).json()
    account_snapshot = client.get(f"/api/v1/identity-snapshots/{account_unit['identity_snapshot_id']}", headers=alice).json()
    assert account_snapshot["brand_voice_version_id"] == account_voice.id
    assert account_snapshot["field_origins"]["brand_voice_version_id"] == "account"


def test_hierarchy_rejects_mismatched_children_and_archived_parent(client):
    alice = {"X-Studio-User": "alice@studio.local"}
    bob = {"X-Studio-User": "bob@studio.local"}
    brand_id = client.post("/api/v1/content-brands", json={"name": "品牌"}, headers=alice).json()["id"]
    first = client.post(f"/api/v1/content-brands/{brand_id}/personas", json={"name": "甲"}, headers=alice).json()["id"]
    second = client.post(f"/api/v1/content-brands/{brand_id}/personas", json={"name": "乙"}, headers=alice).json()["id"]
    account_id = client.post(f"/api/v1/content-personas/{first}/accounts", json={"name": "账号"}, headers=alice).json()["id"]
    series_id = client.post(f"/api/v1/content-accounts/{account_id}/series", json={"name": "栏目"}, headers=alice).json()["id"]
    project_id = client.post("/api/v1/content-projects", json={"title": "项目"}, headers=alice).json()["id"]
    units = f"/api/v1/content-projects/{project_id}/units"
    assert client.post(units, json={"title": "错层级", "persona_id": second, "account_id": account_id, "series_id": series_id, "modality": "text"}, headers=alice).status_code == 404
    assert client.post(units, json={"title": "外部", "persona_id": first, "account_id": account_id, "modality": "text"}, headers=bob).status_code == 404
    assert client.get(units, headers=alice).json() == []
    assert client.delete(f"/api/v1/content-brands/{brand_id}", headers=alice).status_code == 204
    assert client.get(f"/api/v1/content-identities/effective?persona_id={first}", headers=alice).status_code == 200
    assert client.post(units, json={"title": "已归档", "persona_id": first, "modality": "text"}, headers=alice).status_code == 409
    assert client.post(f"/api/v1/content-personas/{first}/accounts", json={"name": "新号"}, headers=alice).status_code == 409


def test_revision_unique_race_returns_409_without_partial_revision(client, monkeypatch):
    from app.services import content_identity

    alice = {"X-Studio-User": "alice@studio.local"}
    brand_id = client.post("/api/v1/content-brands", json={"name": "竞态"}, headers=alice).json()["id"]
    url = f"/api/v1/content-brands/{brand_id}/revisions"
    assert client.post(url, json={"expected_revision": 0, "profile": {"positioning": "第一版"}}, headers=alice).status_code == 201
    original = content_identity.current_revision
    monkeypatch.setattr(content_identity, "current_revision", lambda *_args: None)
    assert client.post(url, json={"expected_revision": 0, "profile": {"positioning": "冲突版"}}, headers=alice).status_code == 409
    monkeypatch.setattr(content_identity, "current_revision", original)
    revisions = client.get(url, headers=alice).json()
    assert len(revisions) == 1 and revisions[0]["profile"]["positioning"] == "第一版"


def test_account_default_portability_gate_and_old_unit_pin(client):
    alice = {"X-Studio-User": "alice@studio.local"}
    persona_id = client.post("/api/v1/content-personas", json={"name": "作者"}, headers=alice).json()["id"]
    account_id = client.post(f"/api/v1/content-personas/{persona_id}/accounts", json={"name": "号"}, headers=alice).json()["id"]
    project_id = client.post("/api/v1/content-projects", json={"title": "默认"}, headers=alice).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "旧单元", "persona_id": persona_id, "account_id": account_id, "modality": "text"}, headers=alice).json()
    url = f"/api/v1/content-accounts/{account_id}/default-workflows/text"
    project_bound = {"nodes": [{"id": "gate", "kind": "Tool", "plugin": "builtin.extract_facts", "config": {"project_id": project_id}}], "edges": [], "visual_order": ["gate"]}
    assert client.post(url, json={"expected_revision": 0, "definition": project_bound}, headers=alice).status_code == 422
    assert client.get(url, headers=alice).json()["workflow_id"] is None
    portable = {"nodes": [{"id": "gate", "kind": "Human", "plugin": "builtin.confirm_facts", "config": {}}], "edges": [], "visual_order": ["gate"]}
    saved = client.post(url, json={"expected_revision": 0, "definition": portable}, headers=alice)
    assert saved.status_code == 201
    assert client.get(f"/api/v1/content-projects/{project_id}/units/{unit['id']}", headers=alice).json()["pinned_workflow_id"] is None


def test_identity_refresh_keeps_compatible_project_override_and_workflow_rebind_refreshes_snapshot(client):
    from test_fe_f2_workflows import _definition

    alice = {"X-Studio-User": "alice@studio.local"}
    persona_id = client.post("/api/v1/content-personas", json={"name": "作者"}, headers=alice).json()["id"]
    project_id = client.post("/api/v1/content-projects", json={"title": "刷新"}, headers=alice).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "稿件", "persona_id": persona_id, "modality": "text"}, headers=alice).json()
    base = f"/api/v1/content-projects/{project_id}/units/{unit['id']}"
    override = client.post(f"{base}/workflow-override", json={"expected_revision": 0, "definition": _definition()}, headers=alice).json()
    assert client.post(f"/api/v1/content-personas/{persona_id}/revisions", json={"expected_revision": 0, "profile": {"positioning": "新定位"}}, headers=alice).status_code == 201
    refreshed = client.patch(base, json={"rebind_identity": True}, headers=alice)
    assert refreshed.status_code == 200, refreshed.text
    assert refreshed.json()["id"] == unit["id"]
    assert refreshed.json()["identity_snapshot_id"] != unit["identity_snapshot_id"]
    assert refreshed.json()["pinned_workflow_id"] == override["workflow_id"]
    assert client.get(f"{base}/workflow-override", headers=alice).json()["workflow_id"] == override["workflow_id"]
    assert client.post(f"/api/v1/content-personas/{persona_id}/revisions", json={"expected_revision": 1, "profile": {"positioning": "再更新"}}, headers=alice).status_code == 201
    changed = client.patch(base, json={"modality": "graphic"}, headers=alice)
    assert changed.status_code == 200, changed.text
    assert changed.json()["identity_snapshot_id"] != refreshed.json()["identity_snapshot_id"]
    assert changed.json()["pinned_workflow_id"] is None
    assert client.get(f"{base}/workflow-override", headers=alice).json()["workflow_id"] is None


def test_identity_refresh_after_run_forks_and_keeps_compatible_project_override(client):
    from test_fe_f2_workflows import _definition

    alice = {"X-Studio-User": "alice@studio.local"}
    persona_id = client.post("/api/v1/content-personas", json={"name": "作者"}, headers=alice).json()["id"]
    project_id = client.post("/api/v1/content-projects", json={"title": "历史刷新"}, headers=alice).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "稿件", "persona_id": persona_id, "modality": "text"}, headers=alice).json()
    base = f"/api/v1/content-projects/{project_id}/units/{unit['id']}"
    override = client.post(f"{base}/workflow-override", json={"expected_revision": 0, "definition": _definition()}, headers=alice).json()
    run = client.post(f"{base}/runs", json={"params": {}}, headers=alice)
    assert run.status_code == 201, run.text
    old_snapshot_id = run.json()["identity_snapshot_id"]
    assert client.post(f"/api/v1/content-personas/{persona_id}/revisions", json={"expected_revision": 0, "profile": {"positioning": "更新"}}, headers=alice).status_code == 201
    replacement = client.patch(base, json={"rebind_identity": True}, headers=alice)
    assert replacement.status_code == 200, replacement.text
    replacement = replacement.json()
    assert replacement["id"] != unit["id"]
    assert replacement["identity_snapshot_id"] != old_snapshot_id
    assert replacement["pinned_workflow_id"] == override["workflow_id"]
    new_base = f"/api/v1/content-projects/{project_id}/units/{replacement['id']}"
    assert client.get(f"{new_base}/workflow-override", headers=alice).json()["workflow_id"] == override["workflow_id"]
    assert client.get(f"{base}/runs/{run.json()['id']}", headers=alice).json()["identity_snapshot_id"] == old_snapshot_id


def test_channel_account_desk_accepts_public_handles_only(client, db_session):
    from app.models import ContentAccount, User

    headers, persona_id, existing_id = _publisher_account(client, db_session)
    user = db_session.query(User).filter_by(email=headers["X-Studio-User"]).one()
    path = f"/api/v1/content-personas/{persona_id}/channel-accounts"
    user.role = "editor"
    db_session.commit()
    assert client.post(path, json={"name": "小红书", "platform_channel": "xiaohongshu", "platform_account_id": "zhishu_note"}, headers=headers).status_code == 403
    user.role = "admin"
    db_session.commit()
    secret = "do-not-echo-secret"
    for bad in (
        {"name": "小红书", "platform_channel": "xiaohongshu", "platform_account_id": secret, "password": secret},
        {"name": "小红书", "platform_channel": "xiaohongshu", "platform_account_id": "my-password"},
        {"name": "小红书", "platform_channel": "xiaohongshu", "platform_account_id": "https://user:secret@example.com"},
        {"name": "公众号", "platform_channel": "wechat", "platform_account_id": "zhishu_talk"},
        {"name": "旧线程", "platform_channel": "x_thread", "platform_account_id": "old_thread"},
        {"name": "没有", "platform_channel": "not-a-channel", "platform_account_id": "nobody"},
    ):
        response = client.post(path, json=bad, headers=headers)
        assert response.status_code == 422, response.text
        assert secret not in response.text
        assert "https://user" not in response.text
    created = client.post(path, json={"name": "小红书主号", "platform_channel": "xiaohongshu", "platform_account_id": "知数笔记"}, headers=headers)
    assert created.status_code == 201, created.text
    assert created.json()["platform_channel"] == "xiaohongshu"
    assert created.json()["platform_binding_state"] == "bound_unverified"
    assert created.json()["id"] != existing_id
    assert client.post(path, json={"name": "重复", "platform_channel": "xiaohongshu", "platform_account_id": "知数笔记"}, headers=headers).status_code == 409
    assert db_session.get(ContentAccount, existing_id).platform_account_id is None
    assert client.put(
        f"/api/v1/content-accounts/{existing_id}/platform-binding",
        json={"platform_channel": "x", "platform_account_id": "wx0123456789abcdef"},
        headers=headers,
    ).status_code == 422


def test_persona_portraits_are_own_model_usable_images_and_personas_only(client):
    import io

    from PIL import Image

    alice = {"X-Studio-User": "alice@studio.local"}
    bob = {"X-Studio-User": "bob@studio.local"}

    def upload(headers, color, model_use="true"):
        image = io.BytesIO()
        Image.new("RGB", (8, 8), color).save(image, format="PNG")
        result = client.post(f"/api/v1/materials/upload?kind=image&rights_status=cleared&model_use_allowed={model_use}",
                             headers=headers, files={"file": ("face.png", image.getvalue(), "image/png")})
        assert result.status_code == 201, result.text
        return result.json()["revisions"][-1]["id"]

    brand_id = client.post("/api/v1/content-brands", json={"name": "Studio"}, headers=alice).json()["id"]
    persona_id = client.post(f"/api/v1/content-brands/{brand_id}/personas", json={"name": "宝妈"}, headers=alice).json()["id"]
    account_id = client.post(f"/api/v1/content-personas/{persona_id}/accounts", json={"name": "主号"}, headers=alice).json()["id"]
    # A persona revision written before the field existed still loads.
    assert client.post(f"/api/v1/content-personas/{persona_id}/revisions", json={"expected_revision": 0, "profile": {"positioning": "宝妈"}}, headers=alice).status_code == 201
    assert "portrait_material_revision_ids" not in client.get(f"/api/v1/content-identities/effective?persona_id={persona_id}", headers=alice).json()["effective_profile"]
    own, other, closed = upload(alice, "red"), upload(bob, "blue"), upload(alice, "green", model_use="false")
    path = f"/api/v1/content-personas/{persona_id}/revisions"
    for ids in ([other], [closed], [own, own + 999], [own] * 2 + [other, closed]):
        assert client.post(path, json={"expected_revision": 1, "profile": {"portrait_material_revision_ids": ids}}, headers=alice).status_code == 422
    assert client.post(f"/api/v1/content-accounts/{account_id}/revisions", json={"expected_revision": 0, "profile": {"portrait_material_revision_ids": [own]}}, headers=alice).json()["detail"] == "portrait_persona_only"
    saved = client.post(path, json={"expected_revision": 1, "profile": {"positioning": "宝妈", "portrait_material_revision_ids": [own, own]}}, headers=alice)
    assert saved.status_code == 201, saved.text
    assert saved.json()["profile"]["portrait_material_revision_ids"] == [own]
    assert client.get(f"/api/v1/content-identities/effective?persona_id={persona_id}", headers=alice).json()["effective_profile"]["portrait_material_revision_ids"] == [own]
    portraits = client.get(f"/api/v1/content-personas/{persona_id}/portraits", headers=alice).json()["items"]
    assert [(item["material_revision_id"], item["usable"]) for item in portraits] == [(own, True)] and portraits[0]["material_id"]
    assert client.get(f"/api/v1/content-personas/{persona_id}/portraits", headers=bob).status_code == 404
