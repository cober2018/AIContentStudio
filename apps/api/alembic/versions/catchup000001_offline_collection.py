"""Persist offline source catchup without rewriting historical opportunities."""
import sqlalchemy as sa

from alembic import op

revision = "catchup000001"
down_revision = "discovery000001"
branch_labels = None
depends_on = None


def upgrade():
    from app.models import DiscoveryCatchupBatch, DiscoveryCatchupSource

    for model in (DiscoveryCatchupBatch, DiscoveryCatchupSource):
        model.__table__.create(op.get_bind(), checkfirst=True)


def downgrade():
    # 与全链守卫一致：有数据拒绝且不做任何 schema 改动；空库才 drop 本版本新建的表
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    for table in ("discovery_catchup_source", "discovery_catchup_batch"):
        if table in tables and bind.execute(sa.text(f"SELECT COUNT(*) FROM {table}")).scalar():
            raise RuntimeError("destructive_downgrade_blocked: retain catchup receipts")
    for table in ("discovery_catchup_source", "discovery_catchup_batch"):
        if table in tables:
            bind.execute(sa.text(f"DROP TABLE {table}"))
