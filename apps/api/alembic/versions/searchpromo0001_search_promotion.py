"""Search promotion: its own production domain, promotion subjects and search plans."""
import sqlalchemy as sa

from alembic import op

revision = "searchpromo0001"
down_revision = "warnjudge0001"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    constraints = {row[0] for row in bind.execute(sa.text("SELECT sql FROM sqlite_master WHERE name = 'content_unit'"))} if bind.dialect.name == "sqlite" else set()
    if not any("'search'" in (sql or "") for sql in constraints):
        with op.batch_alter_table("content_unit") as batch:
            batch.drop_constraint("ck_content_unit_production_domain", type_="check")
            batch.drop_constraint("ck_content_unit_persona_required", type_="check")
            batch.create_check_constraint("ck_content_unit_production_domain", "production_domain IN ('persona', 'product', 'search')")
            batch.create_check_constraint("ck_content_unit_persona_required", "production_domain IN ('product', 'search') OR persona_id IS NOT NULL")
    now = sa.DateTime(timezone=True)
    # An earlier step may build the whole current schema at once, so only missing tables are created.
    if "promotion_category" not in tables:
        op.create_table(
            "promotion_category",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("owner_user_id", sa.Integer, sa.ForeignKey("user.id"), nullable=False, index=True),
            sa.Column("top_key", sa.String(20), nullable=False),
            sa.Column("name", sa.String(60), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="active"),
            sa.Column("sort_order", sa.Integer, nullable=False),
            sa.Column("created_at", now, nullable=False),
            sa.CheckConstraint("top_key IN ('physical', 'digital', 'service', 'org')", name="ck_promotion_category_top"),
            sa.UniqueConstraint("owner_user_id", "top_key", "name", name="uq_promotion_category_name"),
        )
    if "promotion_subject" not in tables:
        op.create_table(
            "promotion_subject",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("owner_user_id", sa.Integer, sa.ForeignKey("user.id"), nullable=False, index=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="active"),
            sa.Column("created_at", now, nullable=False),
        )
    if "promotion_subject_revision" not in tables:
        op.create_table(
            "promotion_subject_revision",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("subject_id", sa.Integer, sa.ForeignKey("promotion_subject.id"), nullable=False, index=True),
            sa.Column("revision_no", sa.Integer, nullable=False),
            sa.Column("payload_json", sa.JSON, nullable=False),
            sa.Column("checksum", sa.String(64), nullable=False),
            sa.Column("created_by", sa.String(255), nullable=False),
            sa.Column("created_at", now, nullable=False),
            sa.UniqueConstraint("subject_id", "revision_no", name="uq_promotion_subject_revision"),
        )
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


def downgrade():
    # 有数据拒绝。空库时删掉本版的表，并把 production_domain 的检查收回到商品域那一版（不含 search）。
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    unit_columns = {column["name"] for column in inspector.get_columns("content_unit")} if "content_unit" in tables else set()
    if "production_domain" in unit_columns and bind.execute(
            sa.text("SELECT COUNT(*) FROM content_unit WHERE production_domain = 'search'")).scalar():
        raise RuntimeError("destructive_downgrade_blocked: retain search promotion data")
    for table in (
        "promotion_category",
        "promotion_subject",
        "promotion_subject_revision",
        "search_plan",
        "search_plan_revision",
        "search_work",
    ):
        if table in tables and bind.execute(sa.text(f"SELECT COUNT(*) FROM {table}")).scalar():
            raise RuntimeError("destructive_downgrade_blocked: retain search promotion data")
    for table in ("search_work", "search_plan_revision", "search_plan", "promotion_subject_revision", "promotion_subject", "promotion_category"):
        if table in tables:
            bind.execute(sa.text(f"DROP TABLE {table}"))
    if "production_domain" in unit_columns:
        names = {row["name"] for row in sa.inspect(bind).get_check_constraints("content_unit")}
        with op.batch_alter_table("content_unit") as batch:
            if "ck_content_unit_production_domain" in names:
                batch.drop_constraint("ck_content_unit_production_domain", type_="check")
            if "ck_content_unit_persona_required" in names:
                batch.drop_constraint("ck_content_unit_persona_required", type_="check")
            batch.create_check_constraint("ck_content_unit_production_domain", "production_domain IN ('persona', 'product')")
            batch.create_check_constraint("ck_content_unit_persona_required", "production_domain = 'product' OR persona_id IS NOT NULL")
