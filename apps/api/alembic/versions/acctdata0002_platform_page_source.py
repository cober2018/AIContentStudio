"""Account data import may come straight from the logged-in platform backend (source kind platform_page)."""
import sqlalchemy as sa
from alembic import op

revision = "acctdata0002"
down_revision = "searchpromo0003"
branch_labels = None
depends_on = None

OLD = "source_kind IN ('screenshot','copied_text','export_file')"
NEW = "source_kind IN ('platform_page','screenshot','copied_text','export_file')"


def _swap(rule: str) -> None:
    if "account_metric_import" not in set(sa.inspect(op.get_bind()).get_table_names()):
        return
    with op.batch_alter_table("account_metric_import", recreate="always") as batch:
        batch.drop_constraint("ck_account_metric_import_source", type_="check")
        batch.create_check_constraint("ck_account_metric_import_source", rule)


def upgrade():
    _swap(NEW)


def downgrade():
    if op.get_bind().execute(sa.text("SELECT COUNT(*) FROM account_metric_import WHERE source_kind = 'platform_page'")).scalar():
        raise RuntimeError("account_metric_import still holds platform_page batches; not narrowing source kinds")
    _swap(OLD)
