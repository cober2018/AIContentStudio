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
    # 与全链守卫一致：有商品域/独立账号归属数据才拒绝；全是默认值才回退删列
    bind = op.get_bind()
    unit_columns = {column["name"] for column in sa.inspect(bind).get_columns("content_unit")}
    account_columns = {column["name"] for column in sa.inspect(bind).get_columns("content_account")}
    if "production_domain" in unit_columns and bind.execute(
            sa.text("SELECT COUNT(*) FROM content_unit WHERE production_domain IS NULL OR production_domain != 'persona'")).scalar():
        raise RuntimeError("destructive_downgrade_blocked: retain product domain and independent account ownership")
    if "owner_user_id" in account_columns and bind.execute(
            sa.text("SELECT COUNT(*) FROM content_account WHERE owner_user_id IS NOT NULL")).scalar():
        raise RuntimeError("destructive_downgrade_blocked: retain product domain and independent account ownership")
    # 本版把 persona_id 改成可空。有空值就无法收回非空约束，拒绝而不是留下更松的表。
    if "persona_id" in unit_columns and bind.execute(sa.text("SELECT COUNT(*) FROM content_unit WHERE persona_id IS NULL")).scalar():
        raise RuntimeError("destructive_downgrade_blocked: retain product domain and independent account ownership")
    if "persona_id" in account_columns and bind.execute(sa.text("SELECT COUNT(*) FROM content_account WHERE persona_id IS NULL")).scalar():
        raise RuntimeError("destructive_downgrade_blocked: retain product domain and independent account ownership")
    # batch recreate 不会自动剔除引用被删列的索引/约束，须先显式 drop（f6e 同款模式）
    if "owner_user_id" in account_columns:
        if "ix_content_account_owner_user_id" in {i["name"] for i in sa.inspect(bind).get_indexes("content_account")}:
            op.drop_index("ix_content_account_owner_user_id", table_name="content_account")
        foreign_keys = {fk["name"] for fk in sa.inspect(bind).get_foreign_keys("content_account")}
        with op.batch_alter_table("content_account") as batch:
            if "fk_content_account_owner_user_id" in foreign_keys:
                batch.drop_constraint("fk_content_account_owner_user_id", type_="foreignkey")
            batch.drop_column("owner_user_id")
            if "persona_id" in account_columns:
                batch.alter_column("persona_id", existing_type=sa.Integer(), nullable=False)
    if "production_domain" in unit_columns:
        constraints = {c["name"] for c in sa.inspect(bind).get_check_constraints("content_unit")}
        with op.batch_alter_table("content_unit") as batch:
            for name in ("ck_content_unit_production_domain", "ck_content_unit_persona_required"):
                if name in constraints:
                    batch.drop_constraint(name, type_="check")
            batch.drop_column("production_domain")
            if "persona_id" in unit_columns:
                batch.alter_column("persona_id", existing_type=sa.Integer(), nullable=False)
