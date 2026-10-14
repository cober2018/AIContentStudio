"""Post-enable schema contract; all migrations use disposable SQLite files."""

from types import SimpleNamespace

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

from alembic import command

NEW_TABLES = {
    "creative_execution_package", "creative_execution", "creative_execution_output",
    "capability_artifact", "capability_artifact_revision", "capability_use",
}


def test_local_approved_schema_default_is_enabled_crs():
    from app.db import LOCAL_APPROVED_SCHEMA_HEAD

    assert LOCAL_APPROVED_SCHEMA_HEAD == "a3series00000001"


@pytest.fixture
def pre_enabled_db(tmp_path, monkeypatch):
    from app.config import get_settings

    url = f"sqlite:///{tmp_path / 'schema-lifecycle.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("AUTH_MODE", "development_header")
    monkeypatch.setenv("AUTH_HMAC_SECRET", "")
    get_settings.cache_clear()
    cfg = Config("alembic.ini")
    cfg.attributes["configure_logger"] = False
    # Initial migration uses today's metadata; downgrade removes descendant shape
    # before exercising the real pre-enable -> ACO additive path.
    command.upgrade(cfg, "aco000000001")
    command.downgrade(cfg, "f7d000000001")
    engine = create_engine(url)
    try:
        assert not NEW_TABLES.intersection(inspect(engine).get_table_names())
        assert not {"identity_issuer", "identity_subject"}.intersection(
            column["name"] for column in inspect(engine).get_columns("user")
        )
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO user (id,email,name,role,is_active,created_at) "
                              "VALUES (1,'old@studio.test','Original','admin',1,'2026-10-04 00:00:00')"))
        yield cfg, engine
    finally:
        engine.dispose()
        get_settings.cache_clear()


def _head(conn):
    return conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()


def _legacy_user(conn):
    return tuple(conn.execute(text("SELECT id,email,name,role,is_active,created_at FROM user")).one())


def test_aco_upgrade_preserves_old_row_and_identity_is_null_inert(pre_enabled_db):
    from app.config import get_settings
    from app.db import LOCAL_APPROVED_SCHEMA_HEAD, schema_head_matches
    from app.deps import get_current_user

    cfg, engine = pre_enabled_db
    with engine.connect() as conn:
        assert _head(conn) == "f7d000000001"
        before = _legacy_user(conn)
    command.upgrade(cfg, "aco000000001")
    inspector = inspect(engine)
    assert NEW_TABLES.issubset(inspector.get_table_names())
    for table in ("content_master_revision", "channel_variant_revision"):
        columns = {item["name"]: item for item in inspector.get_columns(table)}
        assert columns["creative_intent_json"]["nullable"]
        assert columns["creative_intent_hash"]["nullable"]
    identity = {item["name"]: item for item in inspector.get_columns("user")}
    assert identity["identity_issuer"]["nullable"] and identity["identity_subject"]["nullable"]
    with engine.connect() as conn:
        assert _head(conn) == "aco000000001"
        assert _legacy_user(conn) == before
        assert conn.execute(text("SELECT identity_issuer,identity_subject FROM user")).one() == (None, None)
        assert conn.execute(text("PRAGMA integrity_check")).scalar_one() == "ok"
        assert conn.execute(text("PRAGMA foreign_key_check")).all() == []
    with Session(engine) as db:
        assert not schema_head_matches(db, LOCAL_APPROVED_SCHEMA_HEAD)
        user = get_current_user(db=db, x_studio_user="old@studio.test", authorization=None)
        assert user.id == 1 and user.role == "admin"
        assert user.identity_issuer is None and user.identity_subject is None
        assert db.execute(text("SELECT count(*) FROM user")).scalar_one() == 1
    settings = get_settings()
    assert settings.app_env == "development" and settings.auth_mode == "development_header"
    assert not settings.auth_hmac_secret


def test_aco_migration_retains_exact_source_and_history_constraints(pre_enabled_db):
    cfg, engine = pre_enabled_db
    command.upgrade(cfg, "aco000000001")
    inspector = inspect(engine)
    checks = {row["name"] for row in inspector.get_check_constraints("creative_execution_package")}
    assert {"ck_creative_package_one_source", "ck_creative_package_hashes"} <= checks
    assert {tuple(row["column_names"]) for row in inspector.get_unique_constraints("creative_execution")} == {
        ("owner_user_id", "idempotency_key"),
    }
    assert {tuple(row["column_names"]) for row in inspector.get_unique_constraints("creative_execution_output")} == {
        ("execution_id", "role_id", "output_index", "attempt_no"),
    }
    for table in NEW_TABLES:
        assert inspector.get_foreign_keys(table)
        assert all(row.get("options", {}).get("ondelete") == "RESTRICT"
                   for row in inspector.get_foreign_keys(table))


def test_empty_aco_up_down_up_preserves_user_and_null_identity(pre_enabled_db):
    cfg, engine = pre_enabled_db
    with engine.connect() as conn:
        before = _legacy_user(conn)
    command.upgrade(cfg, "aco000000001")
    command.downgrade(cfg, "f7d000000001")
    assert not NEW_TABLES.intersection(inspect(engine).get_table_names())
    command.upgrade(cfg, "aco000000001")
    with engine.connect() as conn:
        assert _legacy_user(conn) == before
        assert _head(conn) == "aco000000001"
        assert conn.execute(text("SELECT identity_issuer,identity_subject FROM user")).one() == (None, None)


@pytest.mark.parametrize("history_kind", ["capability", "package", "master_intent"])
def test_aco_downgrade_refuses_retained_history_before_schema_mutation(pre_enabled_db, history_kind):
    from app.models import (
        CapabilityArtifact,
        ContentMasterRevision,
        ContentPersona,
        ContentProject,
        ContentUnit,
        CreativeExecutionPackage,
    )

    cfg, engine = pre_enabled_db
    command.upgrade(cfg, "aco000000001")
    with Session(engine) as db:
        if history_kind == "capability":
            db.add(CapabilityArtifact(owner_user_id=1, kind="recipe", status="candidate",
                                      scope_type="owner", scope_json={}, name="Retained method"))
        else:
            persona = ContentPersona(owner_user_id=1, name="Author")
            project = ContentProject(owner_user_id=1, title="Retained project")
            db.add_all([persona, project])
            db.flush()
            unit = ContentUnit(project_id=project.id, persona_id=persona.id, modality="text", title="Unit")
            db.add(unit)
            db.flush()
            master = ContentMasterRevision(
                project_id=project.id, content_unit_id=unit.id, revision_no=1, modality="text",
                payload_schema="text.master.v2", payload_json={}, payload_hash="a" * 64,
                context_hash="b" * 64, source_kind="manual", idempotency_key="retained-master",
                request_fingerprint="c" * 64,
            )
            if history_kind == "master_intent":
                master.creative_intent_json = {"objective": "Retain this decision"}
                master.creative_intent_hash = "d" * 64
            db.add(master)
            db.flush()
            if history_kind == "package":
                db.add(CreativeExecutionPackage(
                    owner_user_id=1, project_id=project.id, content_unit_id=unit.id,
                    source_master_revision_id=master.id, package_schema="creative.execution.v1",
                    package_json={}, package_hash="e" * 64,
                    source_payload_hash=master.payload_hash, source_context_hash=master.context_hash,
                ))
        db.commit()
    with engine.connect() as conn:
        tables_before = set(inspect(conn).get_table_names())
        counts_before = {table: conn.execute(text(f'SELECT count(*) FROM "{table}"')).scalar_one()
                         for table in NEW_TABLES}
    with pytest.raises(RuntimeError, match="refusing downgrade: retained creative"):
        command.downgrade(cfg, "f8a000000001")
    with engine.connect() as conn:
        assert _head(conn) == "aco000000001"
        assert set(inspect(conn).get_table_names()) == tables_before
        assert {table: conn.execute(text(f'SELECT count(*) FROM "{table}"')).scalar_one()
                for table in NEW_TABLES} == counts_before
        assert {"creative_intent_json", "creative_intent_hash"} <= {
            row["name"] for row in inspect(conn).get_columns("content_master_revision")
        }
        assert conn.execute(text("SELECT identity_issuer,identity_subject FROM user")).one() == (None, None)


@pytest.mark.parametrize("heads", [[], ["f7d000000001"], ["aco000000001", "f7d000000001"]])
def test_local_readiness_default_rejects_old_empty_or_multiple_heads(db_session, monkeypatch, heads):
    from app.config import Settings
    from app.observability import check_health

    settings = Settings(_env_file=None, app_env="development", auth_mode="development_header",
                        required_schema_head="", task_queue_enabled=False)
    monkeypatch.setattr("app.config.get_settings", lambda: settings)
    monkeypatch.setattr("app.services.material_storage.provider", lambda: SimpleNamespace(probe=lambda: True))
    db_session.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) PRIMARY KEY)"))
    for head in heads:
        db_session.execute(text("INSERT INTO alembic_version VALUES (:head)"), {"head": head})
    db_session.commit()
    result = check_health(db_session)
    assert not result["ready"] and "schema_head_mismatch" in result["reasons"]


def test_local_readiness_default_accepts_crs_without_jwt_activation(db_session, monkeypatch):
    from app.config import Settings
    from app.observability import check_health

    settings = Settings(_env_file=None, app_env="development", auth_mode="development_header",
                        required_schema_head="", task_queue_enabled=False)
    monkeypatch.setattr("app.config.get_settings", lambda: settings)
    monkeypatch.setattr("app.services.material_storage.provider", lambda: SimpleNamespace(probe=lambda: True))
    db_session.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) PRIMARY KEY)"))
    from app.db import LOCAL_APPROVED_SCHEMA_HEAD

    db_session.execute(text("INSERT INTO alembic_version VALUES (:head)"), {"head": LOCAL_APPROVED_SCHEMA_HEAD})
    db_session.commit()
    result = check_health(db_session)
    assert result["ready"] and result["reasons"] == []
    assert settings.auth_mode == "development_header" and not settings.auth_hmac_secret
