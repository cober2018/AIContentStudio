"""Separate product ownership without rewriting identity or execution history."""
import sqlalchemy as sa

from alembic import op

revision = "productdomain0001"
down_revision = "sku000000001"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    unit_columns = {column["name"]: column for column in inspector.get_columns("content_unit")}
    if "production_domain" not in unit_columns:
        with op.batch_alter_table("content_unit") as batch:
            batch.add_column(sa.Column("production_domain", sa.String(20), nullable=False, server_default="persona"))
            batch.alter_column("persona_id", existing_type=sa.Integer(), nullable=True)
            batch.create_check_constraint("ck_content_unit_production_domain", "production_domain IN ('persona', 'product')")
            batch.create_check_constraint("ck_content_unit_persona_required", "production_domain = 'product' OR persona_id IS NOT NULL")
    # Only durable launch/work references establish domain; project titles and shared briefs do not.
    for table in ("product_creation_launch", "product_sku_work"):
        bind.execute(sa.text(f"""UPDATE content_unit SET production_domain = 'product'
            WHERE EXISTS (SELECT 1 FROM {table} ref WHERE ref.unit_id = content_unit.id
                          AND ref.project_id = content_unit.project_id)"""))
    account_columns = {column["name"] for column in inspector.get_columns("content_account")}
    if "owner_user_id" not in account_columns:
        with op.batch_alter_table("content_account") as batch:
            batch.add_column(sa.Column("owner_user_id", sa.Integer(), nullable=True))
            batch.create_foreign_key("fk_content_account_owner_user_id", "user", ["owner_user_id"], ["id"])
            batch.create_index("ix_content_account_owner_user_id", ["owner_user_id"])
            batch.alter_column("persona_id", existing_type=sa.Integer(), nullable=True)
    bind.execute(sa.text("""UPDATE content_account SET owner_user_id =
        (SELECT owner_user_id FROM content_persona WHERE content_persona.id = content_account.persona_id)
        WHERE owner_user_id IS NULL AND persona_id IS NOT NULL"""))


def downgrade():
    raise RuntimeError("destructive_downgrade_blocked: retain product domain and independent account ownership")
