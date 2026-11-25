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
    # 有数据拒绝。空库时回到 searchpromo0001 的表：删掉本版新建的表和加列，并把被替换掉的 search_plan 建回来。
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    for table in ("question_library", "question_library_revision", "search_project"):
        if table in tables and bind.execute(sa.text(f"SELECT COUNT(*) FROM {table}")).scalar():
            raise RuntimeError("destructive_downgrade_blocked: retain search promotion data")
    if "search_work" in tables and "role" in {column["name"] for column in inspector.get_columns("search_work")}:
        if bind.execute(sa.text("SELECT COUNT(*) FROM search_work")).scalar():
            raise RuntimeError("destructive_downgrade_blocked: retain search promotion data")
    revision_columns = {column["name"] for column in inspector.get_columns("promotion_subject_revision")} if "promotion_subject_revision" in tables else set()
    changed = [clause for name, clause in (
        ("status", "status != 'draft'"),
        ("origin", "origin != 'human'"),
        ("confirmed_by", "confirmed_by IS NOT NULL"),
        ("confirmed_at", "confirmed_at IS NOT NULL"),
    ) if name in revision_columns]
    if changed and bind.execute(sa.text(
            "SELECT COUNT(*) FROM promotion_subject_revision WHERE " + " OR ".join(changed))).scalar():
        raise RuntimeError("destructive_downgrade_blocked: retain search promotion data")
    for table in ("search_project", "question_library_revision", "question_library"):
        if table in tables:
            bind.execute(sa.text(f"DROP TABLE {table}"))
    if "search_work" in tables and "role" in {column["name"] for column in inspector.get_columns("search_work")}:
        bind.execute(sa.text("DROP TABLE search_work"))
        tables.discard("search_work")
    if revision_columns & {"status", "origin", "confirmed_by", "confirmed_at"}:
        checks = {row["name"] for row in inspector.get_check_constraints("promotion_subject_revision")}
        with op.batch_alter_table("promotion_subject_revision") as batch:
            if "ck_promotion_subject_revision_status" in checks:
                batch.drop_constraint("ck_promotion_subject_revision_status", type_="check")
            for name in ("confirmed_at", "confirmed_by", "origin", "status"):
                if name in revision_columns:
                    batch.drop_column(name)
    now = sa.DateTime(timezone=True)
    tables = set(sa.inspect(bind).get_table_names())
    if "search_plan" not in tables:
        op.create_table(
            "search_plan",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("project_id", sa.Integer, sa.ForeignKey("content_project.id"), nullable=False, unique=True),
            sa.Column("subject_id", sa.Integer, sa.ForeignKey("promotion_subject.id"), nullable=False, index=True),
            sa.Column("created_at", now, nullable=False),
        )
    if "search_plan_revision" not in tables:
        op.create_table(
            "search_plan_revision",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("plan_id", sa.Integer, sa.ForeignKey("search_plan.id"), nullable=False, index=True),
            sa.Column("revision_no", sa.Integer, nullable=False),
            sa.Column("status", sa.String(20), nullable=False),
            sa.Column("subject_revision_id", sa.Integer, sa.ForeignKey("promotion_subject_revision.id"), nullable=False),
            sa.Column("payload_json", sa.JSON, nullable=False),
            sa.Column("checksum", sa.String(64), nullable=False),
            sa.Column("created_by", sa.String(255), nullable=False),
            sa.Column("created_at", now, nullable=False),
            sa.Column("confirmed_at", now),
            sa.UniqueConstraint("plan_id", "revision_no", name="uq_search_plan_revision"),
            sa.CheckConstraint("status IN ('draft', 'confirmed')", name="ck_search_plan_revision_status"),
        )
    if "search_work" not in tables:
        op.create_table(
            "search_work",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("unit_id", sa.Integer, sa.ForeignKey("content_unit.id"), nullable=False, unique=True),
            sa.Column("project_id", sa.Integer, sa.ForeignKey("content_project.id"), nullable=False, index=True),
            sa.Column("plan_revision_id", sa.Integer, sa.ForeignKey("search_plan_revision.id"), nullable=False),
            sa.Column("question_id", sa.String(40), nullable=False),
            sa.Column("created_at", now, nullable=False),
        )
