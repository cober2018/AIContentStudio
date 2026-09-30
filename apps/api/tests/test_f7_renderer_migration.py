"""Renderer scope widening preserves old evidence and refuses lossy downgrade."""

import importlib.util
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateTable

from app.db import Base
from app.models import CapabilityRegistration, CapabilityVerification


def migration():
    path = Path("alembic/versions/f7b000000001_renderer_scope.py")
    assert path.exists(), "Renderer scope migration required"
    spec = importlib.util.spec_from_file_location("renderer_scope", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_renderer_scope_migration_up_down_up_preserves_legacy_evidence(tmp_path):
    module = migration()
    engine = create_engine(f"sqlite:///{tmp_path / 'renderer.db'}")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE capability_verification (id INTEGER PRIMARY KEY, scope_kind VARCHAR(50) NOT NULL, scope_json JSON NOT NULL, result VARCHAR(20) NOT NULL, evidence_json JSON NOT NULL, CONSTRAINT ck_capability_verification_scope_kind CHECK (scope_kind IN ('publisher_action','data_source_endpoint')))"))
        connection.execute(text("INSERT INTO capability_verification VALUES (1, 'publisher_action', '{}', 'verified', '{\"reference_hash\":\"legacy\"}')"))
        module.op = Operations(MigrationContext.configure(connection))
        module.upgrade()
        module.upgrade()
        assert "renderer_output" in next(item["sqltext"] for item in inspect(connection).get_check_constraints("capability_verification") if item["name"] == "ck_capability_verification_scope_kind")
        assert connection.execute(text("SELECT evidence_json FROM capability_verification WHERE id=1")).scalar_one() == '{"reference_hash":"legacy"}'
        module.downgrade()
        assert "renderer_output" not in next(item["sqltext"] for item in inspect(connection).get_check_constraints("capability_verification") if item["name"] == "ck_capability_verification_scope_kind")
        module.upgrade()
        connection.execute(text("INSERT INTO capability_verification VALUES (2, 'renderer_output', '{}', 'verified', '{}')"))
        with pytest.raises(RuntimeError, match="retained renderer verification"):
            module.downgrade()
        assert connection.execute(text("SELECT COUNT(*) FROM capability_verification")).scalar_one() == 2
    engine.dispose()


def test_renderer_scope_is_in_postgresql_compatible_ddl():
    ddl = str(CreateTable(CapabilityVerification.__table__).compile(dialect=postgresql.dialect()))
    assert "renderer_output" in ddl


def test_full_existing_table_indexes_foreign_keys_and_rows_survive(tmp_path):
    module = migration()
    engine = create_engine(f"sqlite:///{tmp_path / 'existing.db'}")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        registration = CapabilityRegistration(kind="publisher", key="publisher.legacy", version="1", config_fingerprint="a" * 64)
        db.add(registration)
        db.flush()
        db.add(CapabilityVerification(registration_id=registration.id, config_fingerprint="a" * 64,
            scope_kind="publisher_action", scope_json={"preserved": True}, result="verified", evidence_json={"reference_hash": "b" * 64}))
        db.commit()
    with engine.begin() as connection:
        module.op = Operations(MigrationContext.configure(connection))
        indexes = inspect(connection).get_indexes("capability_verification")
        foreign_keys = inspect(connection).get_foreign_keys("capability_verification")
        module.downgrade()
        old = connection.execute(text("SELECT * FROM capability_verification")).all()
        module.upgrade()
        assert connection.execute(text("SELECT * FROM capability_verification")).all() == old
        assert inspect(connection).get_indexes("capability_verification") == indexes
        assert inspect(connection).get_foreign_keys("capability_verification") == foreign_keys
    engine.dispose()
