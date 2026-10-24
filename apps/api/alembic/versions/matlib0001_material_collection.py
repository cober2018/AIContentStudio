"""Material collections for the material library."""
import sqlalchemy as sa
from alembic import op

revision = "matlib0001"
down_revision = "extmaterial0001"
branch_labels = None
depends_on = None


def upgrade():
    tables = sa.inspect(op.get_bind()).get_table_names()
    # Local bootstrap may already have created these tables from the current model.
    if "material_collection" not in tables:
        op.create_table(
            "material_collection",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
            sa.Column("name", sa.String(300), nullable=False),
            sa.Column("description", sa.Text()),
            sa.Column("status", sa.String(20), nullable=False),
            sa.Column("revision", sa.Integer(), nullable=False),
            sa.Column("created_by", sa.String(255)),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.CheckConstraint("status IN ('active','archived')", name="ck_material_collection_status"),
        )
        op.create_index("ix_material_collection_owner_user_id", "material_collection", ["owner_user_id"])
    if "material_collection_item" not in tables:
        op.create_table(
            "material_collection_item",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("collection_id", sa.Integer(), sa.ForeignKey("material_collection.id"), nullable=False),
            sa.Column("material_id", sa.Integer(), sa.ForeignKey("material.id"), nullable=False),
            sa.Column("note", sa.Text()),
            sa.Column("added_by", sa.String(255)),
            sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("collection_id", "material_id", name="uq_material_collection_item"),
        )
        op.create_index("ix_material_collection_item_collection_id", "material_collection_item", ["collection_id"])
        op.create_index("ix_material_collection_item_material_id", "material_collection_item", ["material_id"])


def downgrade():
    raise RuntimeError("destructive_downgrade_blocked: collections hold user curation")
