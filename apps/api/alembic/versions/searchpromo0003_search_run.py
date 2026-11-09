"""Search promotion: background runs of the platform model, with each step recorded."""
import sqlalchemy as sa

from alembic import op

revision = "searchpromo0003"
down_revision = "searchpromo0002"
branch_labels = None
depends_on = None


def upgrade():
    # An earlier step may build the whole current schema at once, so only a missing table is created.
    if "search_run" in set(sa.inspect(op.get_bind()).get_table_names()):
        return
    now = sa.DateTime(timezone=True)
    op.create_table(
        "search_run",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("owner_user_id", sa.Integer, sa.ForeignKey("user.id"), nullable=False, index=True),
        sa.Column("subject_id", sa.Integer, sa.ForeignKey("promotion_subject.id"), index=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("content_project.id"), index=True),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("options_json", sa.JSON, nullable=False),
        sa.Column("steps_json", sa.JSON, nullable=False),
        sa.Column("error", sa.String(1000)),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("created_at", now, nullable=False),
        sa.Column("finished_at", now),
    )


def downgrade():
    raise RuntimeError("destructive_downgrade_blocked: retain search run history")
