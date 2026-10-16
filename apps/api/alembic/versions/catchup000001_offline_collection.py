"""Persist offline source catchup without rewriting historical opportunities."""
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
    raise RuntimeError("destructive_downgrade_blocked: retain catchup receipts")
