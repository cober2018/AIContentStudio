"""Product categories with versioned profiles (skills, styles, look, camera plan)."""
import sqlalchemy as sa
from alembic import op

revision = "prodcat0001"
down_revision = "legacy0001"
branch_labels = None
depends_on = None


def upgrade():
    # An earlier step may build the whole current schema at once, so only missing tables are created.
    existing = set(sa.inspect(op.get_bind()).get_table_names())
    if "product_category" not in existing:
        _category()
    if "product_category_revision" not in existing:
        _revision()


def _category():
    op.create_table(
        "product_category",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("owner_user_id", sa.Integer, sa.ForeignKey("user.id"), nullable=False, index=True),
        sa.Column("key", sa.String(60), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("revision", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("owner_user_id", "key", name="uq_product_category_key"),
    )


def _revision():
    op.create_table(
        "product_category_revision",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("category_id", sa.Integer, sa.ForeignKey("product_category.id"), nullable=False, index=True),
        sa.Column("revision", sa.Integer, nullable=False),
        sa.Column("profile_json", sa.JSON, nullable=False),
        sa.Column("created_by", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("category_id", "revision", name="uq_product_category_revision"),
    )


def downgrade():
    op.drop_table("product_category_revision")
    op.drop_table("product_category")
