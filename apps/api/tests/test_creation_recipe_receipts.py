"""Isolated migration coverage for Creation Recipe stage attempt receipts."""

import importlib.util
import sqlite3
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text
from test_aco_schema_lifecycle import pre_enabled_db  # noqa: F401

_MIGRATION_PATH = Path(__file__).parents[1] / "alembic/versions/crs000000001_stage_attempt_receipts.py"
_RECEIPT_COLUMNS = {"input_snapshot_json", "execution_receipt_json"}


def _migration_module():
    spec = importlib.util.spec_from_file_location("stage_attempt_receipts", _MIGRATION_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _bind_migration(module, connection):
    module.op = Operations(MigrationContext.configure(connection))


def _create_legacy_attempt(connection):
    connection.execute(text(
        "CREATE TABLE workflow_step_attempt ("
        "id INTEGER PRIMARY KEY, output_json JSON NOT NULL DEFAULT '{}'"
        ")"
    ))
    connection.execute(text("INSERT INTO workflow_step_attempt (id) VALUES (1)"))


def test_stage_attempt_receipts_preserve_legacy_null_rows_across_idempotent_up_down_up(tmp_path):
    module = _migration_module()
    engine = create_engine(f"sqlite:///{tmp_path / 'stage-attempt.db'}")
    try:
        with engine.begin() as connection:
            _create_legacy_attempt(connection)
            _bind_migration(module, connection)
            module.upgrade()
            module.upgrade()

            columns = {column["name"]: column for column in inspect(connection).get_columns("workflow_step_attempt")}
            assert _RECEIPT_COLUMNS <= columns.keys()
            assert all(columns[name]["nullable"] for name in _RECEIPT_COLUMNS)
            assert connection.execute(text(
                "SELECT input_snapshot_json, execution_receipt_json "
                "FROM workflow_step_attempt WHERE id = 1"
            )).one() == (None, None)

            module.downgrade()
            assert not (_RECEIPT_COLUMNS & {
                column["name"] for column in inspect(connection).get_columns("workflow_step_attempt")
            })
            assert connection.execute(text(
                "SELECT id, output_json FROM workflow_step_attempt WHERE id = 1"
            )).one() == (1, "{}")

            _bind_migration(module, connection)
            module.upgrade()
            assert _RECEIPT_COLUMNS <= {
                column["name"] for column in inspect(connection).get_columns("workflow_step_attempt")
            }
    finally:
        engine.dispose()


def test_old_aco_shape_still_supports_legacy_orm_attempts(tmp_path):
    from sqlalchemy.orm import Session

    from app.db import Base
    from app.models import WorkflowStepAttempt
    from app.services.stage_invocations import StageInvocationError, require_receipt_schema

    engine = create_engine(f"sqlite:///{tmp_path / 'old-aco.db'}")
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE workflow_step_attempt DROP COLUMN input_snapshot_json"))
        connection.execute(text("ALTER TABLE workflow_step_attempt DROP COLUMN execution_receipt_json"))
    try:
        with Session(engine) as db:
            legacy = WorkflowStepAttempt(step_id=1, run_id=1, node_id="legacy", status="succeeded",
                                         output_json={"historical": True})
            db.add(legacy)
            db.commit()
            legacy_id = legacy.id
            db.expunge_all()
            loaded = db.get(WorkflowStepAttempt, legacy_id)
            assert loaded.output_json == {"historical": True}
            with pytest.raises(StageInvocationError, match="schema_upgrade_required"):
                require_receipt_schema(db)
            assert db.execute(text("SELECT count(*) FROM workflow_step_attempt")).scalar_one() == 1
            assert not _RECEIPT_COLUMNS.intersection(
                column["name"] for column in inspect(db.connection()).get_columns("workflow_step_attempt"))
    finally:
        engine.dispose()


@pytest.mark.parametrize("column", sorted(_RECEIPT_COLUMNS))
def test_stage_attempt_receipts_refuse_downgrade_when_data_would_be_destroyed(tmp_path, column):
    module = _migration_module()
    engine = create_engine(f"sqlite:///{tmp_path / f'{column}.db'}")
    try:
        with engine.begin() as connection:
            _create_legacy_attempt(connection)
            _bind_migration(module, connection)
            module.upgrade()
            connection.execute(text(
                f"UPDATE workflow_step_attempt SET {column} = :payload WHERE id = 1"
            ), {"payload": '{"receipt":"retained"}'})

            with pytest.raises(RuntimeError, match="retained stage attempt receipt/input snapshot"):
                module.downgrade()

            assert _RECEIPT_COLUMNS <= {
                item["name"] for item in inspect(connection).get_columns("workflow_step_attempt")
            }
            assert connection.execute(text(
                f"SELECT {column} FROM workflow_step_attempt WHERE id = 1"
            )).scalar_one() == '{"receipt":"retained"}'
    finally:
        engine.dispose()


def test_real_aco_copy_up_down_up_retains_attempt_and_null_identity(pre_enabled_db, tmp_path, monkeypatch):  # noqa: F811
    from sqlalchemy.orm import Session

    from alembic import command
    from app.config import get_settings
    from app.models import Workflow, WorkflowRun, WorkflowStep, WorkflowStepAttempt

    cfg, original = pre_enabled_db
    command.upgrade(cfg, "crs000000001")
    command.downgrade(cfg, "aco000000001")
    with Session(original) as db:
        workflow = Workflow(name="历史流程", definition_json={"nodes": [], "edges": []})
        db.add(workflow)
        db.flush()
        run = WorkflowRun(workflow_id=workflow.id, status="succeeded")
        db.add(run)
        db.flush()
        step = WorkflowStep(run_id=run.id, node_id="legacy", node_type="System", status="succeeded")
        db.add(step)
        db.flush()
        db.add(WorkflowStepAttempt(run_id=run.id, step_id=step.id, node_id="legacy", status="succeeded",
                                   output_json={"old": "unchanged"}, output_hash="a" * 64))
        db.commit()
    copied_path = tmp_path / "aco-copy.db"
    with original.connect() as source, sqlite3.connect(copied_path) as copied:
        source.connection.driver_connection.backup(copied)
    url = f"sqlite:///{copied_path}"
    monkeypatch.setenv("DATABASE_URL", url)
    get_settings.cache_clear()
    engine = create_engine(url)
    try:
        for operation, expected in ((command.upgrade, "crs000000001"),
                                    (command.downgrade, "aco000000001"),
                                    (command.upgrade, "crs000000001")):
            operation(cfg, expected)
            with engine.connect() as connection:
                assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == expected
                assert connection.execute(text("SELECT output_hash FROM workflow_step_attempt")).scalar_one() == "a" * 64
                assert connection.execute(text("SELECT identity_issuer,identity_subject FROM user")).one() == (None, None)
                assert connection.execute(text("PRAGMA integrity_check")).scalar_one() == "ok"
                assert connection.execute(text("PRAGMA foreign_key_check")).all() == []
                if expected == "crs000000001":
                    assert connection.execute(text("SELECT input_snapshot_json,execution_receipt_json "
                                                   "FROM workflow_step_attempt")).one() == (None, None)
                else:
                    assert not _RECEIPT_COLUMNS.intersection(
                        column["name"] for column in inspect(connection).get_columns("workflow_step_attempt"))
        with original.connect() as connection:
            assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "aco000000001"
    finally:
        engine.dispose()
        get_settings.cache_clear()
