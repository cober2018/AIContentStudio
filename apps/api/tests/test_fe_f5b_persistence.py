from sqlalchemy import inspect

from app import models


def test_learning_migration_follows_f5a():
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(Config("alembic.ini"))
    assert script.get_current_head() == "f5b000000001"
    assert script.get_revision("f5b000000001").down_revision == "f5a000000001"


def test_learning_resources_have_durable_constraints(db_session):
    names = [
        "PublishedContentRecord",
        "PerformanceObservation",
        "ContentInsight",
        "LearningCandidate",
        "LearningCandidateEvidence",
        "ContentMemoryEntry",
        "ContentMemoryRevision",
    ]
    assert all(hasattr(models, name) for name in names)
    tables = set(inspect(db_session.bind).get_table_names())
    assert {getattr(models, name).__tablename__ for name in names} <= tables
    assert "revision_no" in models.LearningCandidate.__table__.columns
    assert "source_learning_candidate_id" in models.ContentMemoryEntry.__table__.columns
    assert "delivery_receipt_id" in models.PublishedContentRecord.__table__.columns


def test_isolated_upgrade_downgrade_preserves_prior_history(tmp_path):
    import os
    import sqlite3
    import subprocess
    import sys

    path = tmp_path / "migration.db"
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{path}"}

    def migrate(*args):
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *args], env=env, capture_output=True, text=True, check=False
        )
        assert result.returncode == 0, result.stdout + result.stderr

    migrate("upgrade", "head")
    migrate("downgrade", "f5a000000001")
    with sqlite3.connect(path) as db:
        db.execute(
            "INSERT INTO user (email,name,role,is_active,created_at) VALUES ('migration@studio.local','History','editor',1,'2026-09-28')"
        )
        original = db.execute("SELECT id,email FROM user").fetchall()
        assert "published_content_record" not in {
            row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    migrate("upgrade", "head")
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT id,email FROM user").fetchall() == original
        assert db.execute("SELECT COUNT(*) FROM published_content_record").fetchone()[0] == 0
        assert db.execute("SELECT version_num FROM alembic_version").fetchone()[0] == "f5b000000001"


def test_new_constraints_compile_for_postgresql():
    from sqlalchemy.dialects import postgresql
    from sqlalchemy.schema import CreateTable

    for model in [
        models.PublishedContentRecord,
        models.PerformanceObservation,
        models.ContentInsight,
        models.LearningCandidate,
        models.LearningCandidateEvidence,
        models.ContentMemoryEntry,
        models.ContentMemoryRevision,
    ]:
        ddl = str(CreateTable(model.__table__).compile(dialect=postgresql.dialect()))
        assert "CREATE TABLE" in ddl and "PRIMARY KEY" in ddl
