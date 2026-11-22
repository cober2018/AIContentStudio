"""Each account's total followers, one reading per day, so a persona's whole-network followers can be summed and tracked."""
import sqlalchemy as sa
from alembic import op

revision = "acctfollow0001"
down_revision = "acctdata0002"
branch_labels = None
depends_on = None


def upgrade():
    # 早期基线迁移按模型建全表，新库里这张表可能已经在了。
    if "account_follower_snapshot" in set(sa.inspect(op.get_bind()).get_table_names()):
        return
    op.create_table(
        "account_follower_snapshot",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("owner_user_id", sa.Integer, sa.ForeignKey("user.id"), nullable=False),
        sa.Column("content_account_id", sa.Integer, sa.ForeignKey("content_account.id"), nullable=False),
        sa.Column("followers", sa.Integer, nullable=False),
        sa.Column("observed_on", sa.String(10), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_name", sa.String(300), nullable=False),
        sa.Column("created_by", sa.String(255)),
        sa.UniqueConstraint("content_account_id", "observed_on", name="uq_account_follower_day"),
    )
    op.create_index("ix_account_follower_snapshot_owner_user_id", "account_follower_snapshot", ["owner_user_id"])
    op.create_index("ix_account_follower_snapshot_content_account_id", "account_follower_snapshot", ["content_account_id"])


def downgrade():
    if op.get_bind().execute(sa.text("SELECT COUNT(*) FROM account_follower_snapshot")).scalar():
        raise RuntimeError("account_follower_snapshot still holds readings; not dropping")
    op.drop_table("account_follower_snapshot")
