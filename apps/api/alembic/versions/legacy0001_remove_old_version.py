"""Remove the old version: draft-era tables and the columns that pointed at them.

The old topic / draft / parent-draft flow was test-only and never published anything.
Each table is dropped only when empty, so real data is never lost by accident.
"""
import sqlalchemy as sa
from alembic import op

revision = "legacy0001"
down_revision = "matmatch0001"
branch_labels = None
depends_on = None

TABLES = ("draft_claim", "draft_check_run", "draft_media", "discoverability_report", "asset_media",
          "draft", "content_job", "mother_revision", "topic_brief")
COLUMNS = {"content_asset": ("draft_id", "topic_brief_id", "mother_revision_id"), "review": ("draft_id",), "workflow_run": ("topic_id",)}


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = set(inspector.get_table_names())
    for table, columns in COLUMNS.items():
        present = [column for column in columns if table in existing
                   and column in {item["name"] for item in inspector.get_columns(table)}]
        for column in present:
            if bind.execute(sa.text(f'SELECT COUNT(*) FROM "{table}" WHERE "{column}" IS NOT NULL')).scalar():
                raise RuntimeError(f"{table}.{column} still holds data; not removing the old version")
        if present:
            indexes = [index["name"] for index in inspector.get_indexes(table) if set(index["column_names"]) & set(present)]
            with op.batch_alter_table(table, recreate="always") as batch:
                for name in indexes:
                    batch.drop_index(name)
                for column in present:
                    batch.drop_column(column)
    for table in TABLES:
        if table not in existing:
            continue
        if bind.execute(sa.text(f'SELECT COUNT(*) FROM "{table}"')).scalar():
            raise RuntimeError(f"{table} still holds data; not removing the old version")
        op.drop_table(table)


def downgrade():
    # The old version is gone for good; going back does not recreate it.
    pass
