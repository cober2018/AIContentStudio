"""Alembic 迁移链回归：全新库 upgrade head 必须一次性成功。

初始迁移按当前模型 create_all，而后续增量迁移会 create_table 同一批表
（模型晚于历史链加入的表）。曾因此全新库升级必撞 DuplicateTable
（生产部署实测踩中）。此处用全新 SQLite 文件库验证整条链可跑通。
"""

import pytest
from sqlalchemy import create_engine, inspect, text


@pytest.fixture
def fresh_sqlite_url(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path}/migrate.db"
    monkeypatch.setenv("DATABASE_URL", url)
    from app.config import get_settings

    get_settings.cache_clear()
    yield url
    get_settings.cache_clear()


def test_alembic_upgrade_head_on_fresh_db(fresh_sqlite_url):
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    from alembic import command

    cfg = Config("alembic.ini")
    # 不让 alembic 的 fileConfig 重配 logging（会禁用既有 logger，干扰其他测试）
    cfg.attributes["configure_logger"] = False
    command.upgrade(cfg, "head")

    heads = ScriptDirectory.from_config(cfg).get_heads()
    engine = create_engine(fresh_sqlite_url)
    try:
        inspector = inspect(engine)
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        assert version in heads
        # 覆盖三个后续增量迁移的表 + 业务主干表
        for table in ("user", "system_settings", "asset_media", "workflow", "workflow_step"):
            assert inspector.has_table(table), f"缺表: {table}"
    finally:
        engine.dispose()
