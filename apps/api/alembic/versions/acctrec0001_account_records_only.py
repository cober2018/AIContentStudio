"""Platform accounts record only the account itself.

Account profiles and account default workflows duplicated what the persona owns. Both tables
and the snapshot column that pointed at account profiles are dropped only when empty, and the
account gains an optional homepage link.
"""
import sqlalchemy as sa
from alembic import op

revision = "acctrec0001"
down_revision = "prodcat0001"
branch_labels = None
depends_on = None

TABLES = ("account_workflow_default", "content_account_revision")


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = set(inspector.get_table_names())
    if "identity_snapshot" in existing and "account_revision_id" in {item["name"] for item in inspector.get_columns("identity_snapshot")}:
        if bind.execute(sa.text('SELECT COUNT(*) FROM "identity_snapshot" WHERE "account_revision_id" IS NOT NULL')).scalar():
            raise RuntimeError("identity_snapshot.account_revision_id still holds data; not removing account profiles")
        with op.batch_alter_table("identity_snapshot", recreate="always") as batch:
            batch.drop_column("account_revision_id")
    for table in TABLES:
        if table not in existing:
            continue
        if bind.execute(sa.text(f'SELECT COUNT(*) FROM "{table}"')).scalar():
            raise RuntimeError(f"{table} still holds data; not removing account profiles")
        op.drop_table(table)
    if "content_account" in existing and "home_url" not in {item["name"] for item in inspector.get_columns("content_account")}:
        op.add_column("content_account", sa.Column("home_url", sa.String(500), nullable=True))


def downgrade():
    # Account profiles are gone for good; going back does not recreate them.
    pass
