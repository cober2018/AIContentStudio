"""Account data import batches: what a third-party model read from platform screenshots or exports."""
import sqlalchemy as sa
from alembic import op

revision = "acctdata0001"
down_revision = "acctrec0001"
branch_labels = None
depends_on = None


def upgrade():
    # An earlier step may build the whole current schema at once, so only a missing table is created.
    if "account_metric_import" in set(sa.inspect(op.get_bind()).get_table_names()):
        return
    op.create_table(
        "account_metric_import",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("owner_user_id", sa.Integer, sa.ForeignKey("user.id"), nullable=False, index=True),
        sa.Column("content_account_id", sa.Integer, sa.ForeignKey("content_account.id"), nullable=False, index=True),
        sa.Column("channel", sa.String(30), nullable=False),
        sa.Column("source_kind", sa.String(20), nullable=False),
        sa.Column("source_name", sa.String(300), nullable=False),
        sa.Column("source_checksum", sa.String(128), nullable=False),
        sa.Column("created_record_ids", sa.JSON, nullable=False),
        sa.Column("counts_json", sa.JSON, nullable=False),
        sa.Column("created_by", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("undone_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("source_kind IN ('screenshot','copied_text','export_file')", name="ck_account_metric_import_source"),
    )


def downgrade():
    op.drop_table("account_metric_import")
