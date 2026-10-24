"""Add reversible list archive and history-preserving deletion."""
import sqlalchemy as sa
from alembic import op

revision = "unitlife000001"
down_revision = "productdomain0001"
branch_labels = None
depends_on = None


def upgrade():
    # Fresh installs may create the current model in an earlier bootstrap migration.
    if "lifecycle" in {column["name"] for column in sa.inspect(op.get_bind()).get_columns("content_unit")}:
        return
    op.add_column("content_unit", sa.Column("lifecycle", sa.String(20), nullable=False, server_default="active"))


def downgrade():
    raise RuntimeError("destructive_downgrade_blocked: retain unit lifecycle and history")
