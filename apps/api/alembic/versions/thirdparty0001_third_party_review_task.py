"""Third-party writer semantic reviews waiting for the external model to submit."""
import sqlalchemy as sa
from alembic import op

revision = "thirdparty0001"
down_revision = "websearch0001"
branch_labels = None
depends_on = None


def upgrade():
    # An earlier step may build the whole current schema at once, so only a missing table is created.
    if "third_party_review_task" in set(sa.inspect(op.get_bind()).get_table_names()):
        return
    op.create_table(
        "third_party_review_task",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("master_revision_id", sa.Integer, sa.ForeignKey("content_master_revision.id"), nullable=False, index=True),
        sa.Column("purpose", sa.String(40), nullable=False),
        sa.Column("input_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("request_json", sa.JSON),
        sa.Column("issues_json", sa.JSON),
        sa.Column("model_label", sa.String(120)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("master_revision_id", "purpose", "input_hash", name="uq_third_party_review_task"),
    )


def downgrade():
    op.drop_table("third_party_review_task")
