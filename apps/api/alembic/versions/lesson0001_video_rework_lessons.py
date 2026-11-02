"""Video rework records and the lessons drawn from them."""
import sqlalchemy as sa
from alembic import op

revision = "lesson0001"
down_revision = "acctdata0001"
branch_labels = None
depends_on = None


def upgrade():
    # An earlier step may build the whole current schema at once, so only missing tables are created.
    existing = set(sa.inspect(op.get_bind()).get_table_names())
    if "video_lesson" not in existing:
        op.create_table(
            "video_lesson",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("owner_user_id", sa.Integer, sa.ForeignKey("user.id"), nullable=False, index=True),
            sa.Column("title", sa.String(200), nullable=False),
            sa.Column("rule", sa.Text, nullable=False),
            sa.Column("scope", sa.String(200), nullable=False),
            sa.Column("status", sa.String(20), nullable=False),
            sa.Column("occurrences", sa.Integer, nullable=False),
            sa.Column("source_record_ids", sa.JSON, nullable=False),
            sa.Column("source_unit_ids", sa.JSON, nullable=False),
            sa.Column("proposed_by", sa.String(255)),
            sa.Column("decided_by", sa.String(255)),
            sa.Column("decided_at", sa.DateTime(timezone=True)),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.CheckConstraint("status IN ('proposed','active','rejected','retired')", name="ck_video_lesson_status"),
        )
    if "video_rework_record" not in existing:
        op.create_table(
            "video_rework_record",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("owner_user_id", sa.Integer, sa.ForeignKey("user.id"), nullable=False, index=True),
            sa.Column("project_id", sa.Integer, sa.ForeignKey("content_project.id"), nullable=False, index=True),
            sa.Column("unit_id", sa.Integer, sa.ForeignKey("content_unit.id"), nullable=False, index=True),
            sa.Column("stage", sa.String(20), nullable=False),
            sa.Column("target_id", sa.Integer, nullable=False),
            sa.Column("time_ms", sa.Integer),
            sa.Column("note", sa.Text, nullable=False),
            sa.Column("lesson_id", sa.Integer, sa.ForeignKey("video_lesson.id"), index=True),
            sa.Column("created_by", sa.String(255)),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.CheckConstraint("stage IN ('sample','final')", name="ck_video_rework_record_stage"),
        )


def downgrade():
    op.drop_table("video_rework_record")
    op.drop_table("video_lesson")
