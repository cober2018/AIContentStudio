from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import get_settings


class Base(DeclarativeBase):
    pass


def _engine_kwargs(url: str) -> dict:
    if url.startswith("sqlite"):
        # FastAPI 多线程写 SQLite 需要放宽 check_same_thread；外键约束默认关闭需显式开启
        return {"connect_args": {"check_same_thread": False}}
    return {"pool_pre_ping": True}


engine = create_engine(get_settings().database_url, **_engine_kwargs(get_settings().database_url))

# Approved local schema includes inert identity ancestry, not JWT activation.
LOCAL_APPROVED_SCHEMA_HEAD = "formassist000001"

if get_settings().database_url.startswith("sqlite"):
    # 异步队列（Celery 多进程）与 API 并发写 SQLite 的前提：WAL 允许读写并发，
    # busy_timeout 让写锁等待而非立刻报 database is locked（生产 PostgreSQL 无需此段）
    from sqlalchemy import event

    @event.listens_for(engine, "connect")
    def _sqlite_pragma(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=8000")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def schema_head_matches(db, expected_head: str) -> bool:
    """Validate the approved local chain or exact production migration head."""
    from pathlib import Path

    from alembic.script import ScriptDirectory
    from sqlalchemy import text

    if not expected_head:
        return False
    try:
        script = ScriptDirectory(str(Path(__file__).resolve().parents[1] / "alembic"))
        heads = script.get_heads()
        database_heads = db.execute(text("SELECT version_num FROM alembic_version")).scalars().all()
        if len(heads) != 1 or database_heads != [expected_head]:
            return False
        if get_settings().app_env != "production" and expected_head == LOCAL_APPROVED_SCHEMA_HEAD:
            return any(revision.revision == expected_head for revision in script.iterate_revisions(heads[0], "base"))
    except Exception:  # noqa: BLE001 Missing/corrupt migration history must fail closed.
        return False
    return heads[0] == expected_head


def init_db() -> None:
    from . import models  # noqa: F401  确保模型注册后再建表

    # Durable generation schema requires an explicit operator migration even
    # in a local development process that otherwise creates legacy tables.
    migration_only = {"form_assistance_session", "discovery_catchup_batch", "discovery_catchup_source", "discovery_source", "persona_source_subscription", "discovery_item", "discovery_event", "persona_research_run", "product_creation_launch", "project_knowledge_context_revision", "provider_generation_task", "creative_execution_package", "creative_execution",
                      "creative_execution_output", "capability_artifact", "capability_artifact_revision", "capability_use"}
    Base.metadata.create_all(engine, tables=[table for table in Base.metadata.sorted_tables
        if table.name not in migration_only])
