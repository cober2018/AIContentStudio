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


def test_f6e_additive_schema_up_down_up_on_empty_isolated_sqlite(fresh_sqlite_url):
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    from alembic import command

    cfg = Config("alembic.ini")
    cfg.attributes["configure_logger"] = False
    assert ScriptDirectory.from_config(cfg).get_heads() == ["f7a000000001"]
    command.upgrade(cfg, "head")
    engine = create_engine(fresh_sqlite_url)
    try:
        inspector = inspect(engine)
        for table in (
            "channel_variant_revision",
            "channel_variant_asset_ref",
            "channel_variant_evidence_ref",
            "channel_variant_check_run",
        ):
            assert inspector.has_table(table)
        assert "channel_variant_revision_id" in {column["name"] for column in inspector.get_columns("content_asset")}
        assert {"ck_variant_key_length", "ck_variant_artifact_kind", "ck_variant_source_kind", "ck_variant_hash_lengths"}.issubset(
            {row["name"] for row in inspector.get_check_constraints("channel_variant_revision")}
        )
        assert {"ck_variant_asset_order_nonnegative"}.issubset({row["name"] for row in inspector.get_check_constraints("channel_variant_asset_ref")})
        assert {"ck_variant_evidence_order_nonnegative"}.issubset({row["name"] for row in inspector.get_check_constraints("channel_variant_evidence_ref")})
        assert all(row.get("options", {}).get("ondelete") == "RESTRICT" for row in inspector.get_foreign_keys("channel_variant_revision"))
    finally:
        engine.dispose()
    command.downgrade(cfg, "f6a000000001")
    command.upgrade(cfg, "head")
    engine = create_engine(fresh_sqlite_url)
    try:
        assert inspect(engine).has_table("channel_variant_revision")
    finally:
        engine.dispose()


def test_f6e_downgrade_refuses_v5_candidate_even_if_variant_fk_is_missing(fresh_sqlite_url):
    from alembic.config import Config

    from alembic import command

    cfg = Config("alembic.ini")
    cfg.attributes["configure_logger"] = False
    command.upgrade(cfg, "head")
    engine = create_engine(fresh_sqlite_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text("INSERT INTO content_asset (channel, title, status, candidate_manifest_json, created_at) VALUES (:channel, :title, :status, :manifest, CURRENT_TIMESTAMP)"),
                {"channel": "wechat", "title": "历史候选", "status": "frozen", "manifest": '{"schema_version": 5}'},
            )
    finally:
        engine.dispose()
    with pytest.raises(RuntimeError, match="retained v5 Candidate history"):
        command.downgrade(cfg, "f6a000000001")
    engine = create_engine(fresh_sqlite_url)
    try:
        assert inspect(engine).has_table("channel_variant_revision")
        with engine.connect() as connection:
            assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "f6e000000001"
    finally:
        engine.dispose()


def test_f7_capability_schema_up_down_up_and_retained_evidence_guard(fresh_sqlite_url):
    from alembic.config import Config

    from alembic import command

    cfg = Config("alembic.ini")
    cfg.attributes["configure_logger"] = False
    command.upgrade(cfg, "head")
    engine = create_engine(fresh_sqlite_url)
    try:
        inspector = inspect(engine)
        assert inspector.has_table("capability_registration")
        assert inspector.has_table("capability_verification")
        assert {"ck_capability_registration_identity_nonempty", "ck_capability_registration_status",
                "ck_capability_registration_data_mapping"}.issubset(
                    {row["name"] for row in inspector.get_check_constraints("capability_registration")})
        assert {"ck_capability_verification_scope_kind", "ck_capability_verification_result"}.issubset(
            {row["name"] for row in inspector.get_check_constraints("capability_verification")})
        assert "ix_capability_verification_registration_scope_id" in {
            row["name"] for row in inspector.get_indexes("capability_verification")}
    finally:
        engine.dispose()
    command.downgrade(cfg, "f6e000000001")
    command.upgrade(cfg, "head")
    engine = create_engine(fresh_sqlite_url)
    try:
        with engine.begin() as connection:
            connection.execute(text(
                "INSERT INTO capability_registration (kind, key, version, status, config_fingerprint, created_at) "
                "VALUES ('publisher', 'wewrite', '1', 'configured', :fingerprint, CURRENT_TIMESTAMP)"
            ), {"fingerprint": "a" * 64})
            connection.execute(text(
                "INSERT INTO capability_verification (registration_id, config_fingerprint, scope_kind, scope_json, result, verified_at, evidence_json) "
                "VALUES (1, :fingerprint, 'publisher_action', '{}', 'verified', CURRENT_TIMESTAMP, '{}')"
            ), {"fingerprint": "a" * 64})
    finally:
        engine.dispose()
    with pytest.raises(RuntimeError, match="retained CapabilityVerification history"):
        command.downgrade(cfg, "f6e000000001")
