"""Hot-path read indexes: workflow step lookups and list-page filters/sorts.

纯增量索引，不改任何列/约束；对经 create_all 建出（索引已存在）的库幂等。
"""

import sqlalchemy as sa

from alembic import op

revision = "idx000000001"
down_revision = "crs000000001"
branch_labels = None
depends_on = None

# 与模型 index=True 生成的默认命名（ix_<table>_<column>）保持一致
INDEXES = (
    ("ix_workflow_step_run_id", "workflow_step", ("run_id",)),
    ("ix_content_job_status", "content_job", ("status",)),
    ("ix_draft_status", "draft", ("status",)),
    ("ix_draft_created_at", "draft", ("created_at",)),
    ("ix_material_kind", "material", ("kind",)),
    ("ix_material_status", "material", ("status",)),
    ("ix_content_asset_draft_id", "content_asset", ("draft_id",)),
    ("ix_content_asset_created_at", "content_asset", ("created_at",)),
)


def _existing(indexes, name):
    for item in indexes:
        if item["name"] == name:
            return item
    return None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    cache: dict[str, list] = {}

    def table_indexes(table: str) -> list:
        if table not in cache:
            cache[table] = inspector.get_indexes(table)
        return cache[table]

    for name, table, columns in INDEXES:
        # Fresh installs no longer create the old-version draft tables and columns.
        if not inspector.has_table(table) or not set(columns) <= {item["name"] for item in inspector.get_columns(table)}:
            continue
        existing = _existing(table_indexes(table), name)
        if existing is None:
            op.create_index(name, table, list(columns))
        elif existing.get("column_names") != list(columns):
            # 同名不同列说明库结构与模型谱系不一致，宁可不迁移也不静默错配。
            raise RuntimeError(f"index schema mismatch: {name} on {table}")


def downgrade():
    inspector = sa.inspect(op.get_bind())
    cache: dict[str, list] = {}

    def table_indexes(table: str) -> list:
        if table not in cache:
            cache[table] = inspector.get_indexes(table)
        return cache[table]

    for name, table, _columns in reversed(INDEXES):
        if inspector.has_table(table) and _existing(table_indexes(table), name) is not None:
            op.drop_index(name, table_name=table)
