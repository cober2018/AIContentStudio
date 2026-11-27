"""One body (full article) per project and fixed forms on works; form revisions record the body revision they came from."""
import sqlalchemy as sa
from alembic import op

revision = "bodyform0001"
down_revision = "acctfollow0001"
branch_labels = None
depends_on = None


def _columns(table: str) -> set[str]:
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade():
    # 早期基线迁移按模型建全表，新库里这些列可能已经在了。
    if "form_plan_json" not in _columns("content_project"):
        with op.batch_alter_table("content_project") as batch:
            batch.add_column(sa.Column("form_plan_json", sa.JSON, nullable=True))
    if "form" not in _columns("content_unit"):
        with op.batch_alter_table("content_unit") as batch:
            batch.add_column(sa.Column("form", sa.String(30), nullable=True))
    if "source_body_revision_id" not in _columns("content_master_revision"):
        with op.batch_alter_table("content_master_revision") as batch:
            batch.add_column(sa.Column("source_body_revision_id", sa.Integer, nullable=True))
            batch.create_foreign_key("fk_master_source_body_revision", "content_master_revision", ["source_body_revision_id"], ["id"])


def downgrade():
    with op.batch_alter_table("content_master_revision") as batch:
        batch.drop_constraint("fk_master_source_body_revision", type_="foreignkey")
        batch.drop_column("source_body_revision_id")
    with op.batch_alter_table("content_unit") as batch:
        batch.drop_column("form")
    with op.batch_alter_table("content_project") as batch:
        batch.drop_column("form_plan_json")
