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
    # 与全链守卫一致：有归档/删除等生命周期数据才拒绝；全是默认 active 才回退删列
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("content_unit")}
    if "lifecycle" not in columns:
        return
    if bind.execute(sa.text("SELECT COUNT(*) FROM content_unit WHERE lifecycle != 'active'")).scalar():
        raise RuntimeError("destructive_downgrade_blocked: retain unit lifecycle and history")
    with op.batch_alter_table("content_unit") as batch:
        batch.drop_column("lifecycle")
