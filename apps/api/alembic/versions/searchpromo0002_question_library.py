"""Search promotion v2: confirmed subject drafts, question library on the subject, one project per question."""
import sqlalchemy as sa

from alembic import op

revision = "searchpromo0002"
down_revision = "searchpromo0001"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    now = sa.DateTime(timezone=True)
    columns = {column["name"] for column in inspector.get_columns("promotion_subject_revision")}
    if "status" not in columns:
        with op.batch_alter_table("promotion_subject_revision") as batch:
            batch.add_column(sa.Column("status", sa.String(20), nullable=False, server_default="draft"))
            batch.add_column(sa.Column("origin", sa.String(20), nullable=False, server_default="human"))
            batch.add_column(sa.Column("confirmed_by", sa.String(255)))
            batch.add_column(sa.Column("confirmed_at", now))
            batch.create_check_constraint("ck_promotion_subject_revision_status", "status IN ('draft', 'confirmed')")
    # The first version kept plans on projects; no work was ever opened from one, so it is replaced, not carried over.
    old_work = "search_work" in tables and "plan_revision_id" in {c["name"] for c in inspector.get_columns("search_work")}
    if old_work:
        if bind.execute(sa.text("SELECT COUNT(*) FROM search_work")).scalar():
            raise RuntimeError("search_work_rows_present: first-version works must be removed by hand before this migration")
        op.drop_table("search_work")
        tables.discard("search_work")
    for table in ("search_plan_revision", "search_plan"):
        if table in tables:
            op.drop_table(table)
    if "question_library" not in tables:
        op.create_table(
            "question_library",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("subject_id", sa.Integer, sa.ForeignKey("promotion_subject.id"), nullable=False, unique=True),
            sa.Column("created_at", now, nullable=False),
        )
    if "question_library_revision" not in tables:
        op.create_table(
            "question_library_revision",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("library_id", sa.Integer, sa.ForeignKey("question_library.id"), nullable=False, index=True),
            sa.Column("revision_no", sa.Integer, nullable=False),
            sa.Column("subject_revision_id", sa.Integer, sa.ForeignKey("promotion_subject_revision.id"), nullable=False),
            sa.Column("payload_json", sa.JSON, nullable=False),
            sa.Column("checksum", sa.String(64), nullable=False),
            sa.Column("origin", sa.String(20), nullable=False),
            sa.Column("created_by", sa.String(255), nullable=False),
            sa.Column("created_at", now, nullable=False),
            sa.UniqueConstraint("library_id", "revision_no", name="uq_question_library_revision"),
        )
    if "search_project" not in tables:
        op.create_table(
            "search_project",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("project_id", sa.Integer, sa.ForeignKey("content_project.id"), nullable=False, unique=True),
            sa.Column("subject_id", sa.Integer, sa.ForeignKey("promotion_subject.id"), nullable=False, index=True),
            sa.Column("subject_revision_id", sa.Integer, sa.ForeignKey("promotion_subject_revision.id"), nullable=False),
            sa.Column("library_revision_id", sa.Integer, sa.ForeignKey("question_library_revision.id"), nullable=False),
            sa.Column("question_id", sa.String(40), nullable=False),
            sa.Column("settings_json", sa.JSON, nullable=False),
            sa.Column("created_by", sa.String(255), nullable=False),
            sa.Column("created_at", now, nullable=False),
        )
    if "search_work" not in tables:
        op.create_table(
            "search_work",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("unit_id", sa.Integer, sa.ForeignKey("content_unit.id"), nullable=False, unique=True),
            sa.Column("project_id", sa.Integer, sa.ForeignKey("content_project.id"), nullable=False, index=True),
            sa.Column("role", sa.String(20), nullable=False),
            sa.Column("created_at", now, nullable=False),
            sa.CheckConstraint("role IN ('core', 'derived')", name="ck_search_work_role"),
        )


def downgrade():
    raise RuntimeError("destructive_downgrade_blocked: retain search promotion data")
