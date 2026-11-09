"""Writing-model verdicts on warning checks."""
import sqlalchemy as sa
from alembic import op

revision = "warnjudge0001"
down_revision = "thirdparty0001"
branch_labels = None
depends_on = None


def upgrade():
    # An earlier step may build the whole current schema at once, so only a missing table is created.
    if "check_warning_judgment" in set(sa.inspect(op.get_bind()).get_table_names()):
        return
    op.create_table(
        "check_warning_judgment",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("check_run_id", sa.Integer, sa.ForeignKey("content_master_check_run.id"), nullable=False, index=True),
        sa.Column("input_hash", sa.String(64), nullable=False),
        sa.Column("judge", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("verdict", sa.String(20)),
        sa.Column("reason", sa.String(1000)),
        sa.Column("model_label", sa.String(120)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("judged_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("check_run_id", "input_hash", name="uq_check_warning_judgment"),
    )


def downgrade():
    op.drop_table("check_warning_judgment")
