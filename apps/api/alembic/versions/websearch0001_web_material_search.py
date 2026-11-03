"""Web material searches: pictures found on readable pages, kept until the user picks."""
import sqlalchemy as sa
from alembic import op

revision = "websearch0001"
down_revision = "lesson0001"
branch_labels = None
depends_on = None


def upgrade():
    # An earlier step may build the whole current schema at once, so only a missing table is created.
    if "web_material_search" in set(sa.inspect(op.get_bind()).get_table_names()):
        return
    op.create_table(
        "web_material_search",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("owner_user_id", sa.Integer, sa.ForeignKey("user.id"), nullable=False, index=True),
        sa.Column("sku_id", sa.Integer, sa.ForeignKey("product_sku.id"), index=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("content_project.id"), index=True),
        sa.Column("unit_id", sa.Integer, sa.ForeignKey("content_unit.id"), index=True),
        sa.Column("query", sa.String(300), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("progress_json", sa.JSON),
        sa.Column("result_json", sa.JSON),
        sa.Column("error_code", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("status IN ('queued','running','completed','failed','interrupted')", name="ck_web_material_search_status"),
    )


def downgrade():
    op.drop_table("web_material_search")
