"""Register user folders whose materials are linked in place."""
import sqlalchemy as sa
from alembic import op

revision = "extmaterial0001"
down_revision = "unitlife000001"
branch_labels = None
depends_on = None


def upgrade():
    # Local bootstrap may already have created the table from the current model.
    if "material_source" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table(
        "material_source",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("label", sa.String(200), nullable=False),
        sa.Column("root_path", sa.String(1000), nullable=False),
        sa.Column("volume_uuid", sa.String(64)),
        sa.Column("created_by", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_material_source_owner_user_id", "material_source", ["owner_user_id"])


def downgrade():
    raise RuntimeError("destructive_downgrade_blocked: linked materials reference their source folders")
