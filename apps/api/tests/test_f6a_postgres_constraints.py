"""Opt-in acceptance against the dedicated, migrated local PostgreSQL database."""

import importlib.util
import os
from pathlib import Path
from uuid import uuid4

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from test_f6a_modality_adapters import HEADERS, _unit

from app.db import get_db
from app.models import ContentMasterRevision


def test_real_postgres_master_constraints_and_non_destructive_downgrade():
    url = os.environ.get("F6A_ACCEPTANCE_POSTGRES_URL")
    if not url:
        pytest.skip("Dedicated PostgreSQL acceptance database not requested")
    from sqlalchemy.engine import make_url
    parsed = make_url(url)
    assert parsed.host == "127.0.0.1" and parsed.port == 15462 and parsed.database == "f6a_acceptance"
    engine = create_engine(url)
    from app.main import app
    previous = dict(app.dependency_overrides)
    try:
        with Session(engine) as db:
            app.dependency_overrides[get_db] = lambda: db
            client = TestClient(app)
            _, path = _unit(client, db, "video", suffix=uuid4().hex[:8])
            response = client.post(path, json={"idempotency_key": "postgres-constraints", "payload": {"script": "真实约束", "shots": []}}, headers=HEADERS)
            assert response.status_code == 200, response.text
            row = db.get(ContentMasterRevision, response.json()["id"])
            assert row.modality == "video"
            constraints = inspect(engine).get_unique_constraints("content_master_revision")
            assert {item["name"] for item in constraints} >= {"uq_master_unit_revision", "uq_master_unit_idempotency"}
            columns = [column.name for column in ContentMasterRevision.__table__.columns if column.name != "id"]
            for change in ("revision_no", "idempotency_key"):
                values = {name: getattr(row, name) for name in columns}
                values[change] = 99 if change == "revision_no" else "different-key"
                with pytest.raises(IntegrityError), db.begin_nested():
                    db.execute(ContentMasterRevision.__table__.insert().values(**values))
            values = {name: getattr(row, name) for name in columns}
            values.update(revision_no=99, idempotency_key="foreign-project", project_id=2147483647)
            with pytest.raises(IntegrityError), db.begin_nested():
                db.execute(ContentMasterRevision.__table__.insert().values(**values))
            db.rollback()
        migration_path = Path(__file__).parents[1] / "alembic/versions/f6a000000001_production_content_master.py"
        spec = importlib.util.spec_from_file_location("f6a_pg_migration", migration_path)
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)
        with engine.begin() as connection:
            migration.op = Operations(MigrationContext.configure(connection))
            with pytest.raises(RuntimeError, match="history|历史|downgrade"):
                migration.downgrade()
            assert connection.scalar(select(ContentMasterRevision.id).limit(1)) is not None
            assert "content_master_check_run" in inspect(connection).get_table_names()
            assert next(column for column in inspect(connection).get_columns("content_asset") if column["name"] == "final_body")["nullable"] is True
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)
        engine.dispose()


def test_postgres_live_resource_locks_block_concurrent_revocation(tmp_path):
    url = os.environ.get("F6A_ACCEPTANCE_POSTGRES_URL")
    if not url:
        pytest.skip("Dedicated PostgreSQL acceptance database not requested")
    from sqlalchemy import text
    from sqlalchemy.exc import OperationalError
    from test_f6a_modality_adapters import _render_material

    from app.models import FactPackItem, MaterialRevision, ProjectFactBoundaryRevision
    from app.services.production_validation import lock_live_resources

    assert "127.0.0.1:15462/f6a_acceptance" in url
    engine = create_engine(url)
    from app.main import app
    previous = dict(app.dependency_overrides)
    try:
        with Session(engine) as db:
            app.dependency_overrides[get_db] = lambda: db
            client = TestClient(app)
            project, path = _unit(client, db, "text", suffix=uuid4().hex[:8])
            material = _render_material(db, project, tmp_path, "graphic", "pg-lock.png")
            master = client.post(path, json={"idempotency_key": "live-lock", "payload": {"markdown": "真实锁"}, "asset_refs": [{"material_revision_id": material.id, "content_hash": material.content_hash}]}, headers=HEADERS).json()
            row = db.get(ContentMasterRevision, master["id"])
            lock_live_resources(db, row)
            item = db.scalars(select(FactPackItem).where(FactPackItem.fact_pack_id == db.get(ProjectFactBoundaryRevision, row.fact_boundary_revision_id).fact_pack_id)).first()
            for model, identity in ((MaterialRevision, material.id), (FactPackItem, item.id)):
                with Session(engine) as revoker:
                    revoker.execute(text("SET LOCAL lock_timeout = '100ms'"))
                    with pytest.raises(OperationalError, match="lock timeout"):
                        revoker.execute(model.__table__.update().where(model.id == identity).values(public_use_allowed=False))
                    revoker.rollback()
            db.rollback()
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)
        engine.dispose()
