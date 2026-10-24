"""Add versioned SKU content assets without changing existing projects."""
import sqlalchemy as sa
from alembic import op

revision = "sku000000001"
down_revision = "formassist000001"
branch_labels = None
depends_on = None


def ident():
    return sa.Column("id", sa.Integer(), primary_key=True)


def fk(name, target, nullable=False):
    return sa.Column(name, sa.Integer(), sa.ForeignKey(target, ondelete="RESTRICT"), nullable=nullable)


def created():
    return sa.Column("created_at", sa.DateTime(timezone=True), nullable=False)


def upgrade():
    tables = {"product_sku", "product_sku_revision", "product_sku_plan", "product_sku_work", "production_profile_revision", "product_sku_reference"}
    present = tables.intersection(sa.inspect(op.get_bind()).get_table_names())
    # The legacy initial migration creates current model metadata on fresh installs.
    if present == tables:
        return
    if present:
        raise RuntimeError("partial_sku_schema_requires_recovery")
    op.create_table("product_sku", ident(), fk("owner_user_id", "user.id"),
        sa.Column("code", sa.String(40), unique=True), sa.Column("request_key", sa.String(100), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False), sa.Column("default_plan_id", sa.Integer()), created(),
        sa.UniqueConstraint("owner_user_id", "request_key", name="uq_product_sku_request"), sqlite_autoincrement=True)
    op.create_index("ix_product_sku_owner_user_id", "product_sku", ["owner_user_id"])
    op.create_table("product_sku_revision", ident(), fk("sku_id", "product_sku.id"),
        sa.Column("revision", sa.Integer(), nullable=False), sa.Column("external_code", sa.String(300), nullable=False),
        sa.Column("product_json", sa.JSON(), nullable=False), fk("primary_image_revision_id", "material_revision.id", True),
        sa.Column("primary_image_kind", sa.String(20), nullable=False), created(),
        sa.UniqueConstraint("sku_id", "revision", name="uq_product_sku_revision"))
    op.create_index("ix_product_sku_revision_sku_id", "product_sku_revision", ["sku_id"])
    op.create_table("product_sku_plan", ident(), fk("sku_id", "product_sku.id"),
        sa.Column("plan_key", sa.String(100), nullable=False), sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False), sa.Column("settings_json", sa.JSON(), nullable=False),
        fk("source_unit_id", "content_unit.id", True), created(),
        sa.UniqueConstraint("sku_id", "plan_key", "revision", name="uq_product_sku_plan_revision"))
    op.create_index("ix_product_sku_plan_sku_id", "product_sku_plan", ["sku_id"])
    op.create_table("product_sku_work", ident(), fk("sku_id", "product_sku.id"),
        fk("sku_revision_id", "product_sku_revision.id"), fk("project_id", "content_project.id"),
        fk("unit_id", "content_unit.id"), fk("plan_id", "product_sku_plan.id", True),
        sa.Column("settings_snapshot_json", sa.JSON(), nullable=False), created(),
        sa.UniqueConstraint("unit_id", name="uq_product_sku_work_unit"))
    op.create_index("ix_product_sku_work_sku_id", "product_sku_work", ["sku_id"])
    op.create_table("production_profile_revision", ident(), fk("unit_id", "content_unit.id"),
        sa.Column("revision", sa.Integer(), nullable=False), sa.Column("settings_json", sa.JSON(), nullable=False),
        sa.Column("settings_hash", sa.String(64), nullable=False), sa.Column("created_by", sa.String(255), nullable=False), created(),
        sa.UniqueConstraint("unit_id", "revision", name="uq_production_profile_revision"))
    op.create_index("ix_production_profile_revision_unit_id", "production_profile_revision", ["unit_id"])
    op.create_table("product_sku_reference", ident(), fk("sku_id", "product_sku.id"),
        fk("master_id", "content_master_revision.id"), sa.Column("master_hash", sa.String(64), nullable=False),
        fk("profile_revision_id", "production_profile_revision.id", True), created(),
        sa.UniqueConstraint("sku_id", "master_id", name="uq_product_sku_reference"))
    op.create_index("ix_product_sku_reference_sku_id", "product_sku_reference", ["sku_id"])


def downgrade():
    tables = ("product_sku_reference", "production_profile_revision", "product_sku_work", "product_sku_plan", "product_sku_revision", "product_sku")
    if any(op.get_bind().execute(sa.text(f"SELECT COUNT(*) FROM {table}")).scalar() for table in tables):
        raise RuntimeError("destructive_downgrade_blocked: retain SKU content history")
    for table in tables:
        op.drop_table(table)
