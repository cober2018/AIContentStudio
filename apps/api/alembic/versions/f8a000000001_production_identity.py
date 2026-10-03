"""Add explicit issuer/subject binding for production authentication."""

import sqlalchemy as sa

from alembic import op

revision = "f8a000000001"
down_revision = "f7d000000001"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("user")}
    uniques = {item["name"] for item in inspector.get_unique_constraints("user")}
    with op.batch_alter_table("user") as batch:
        if "identity_issuer" not in columns:
            batch.add_column(sa.Column("identity_issuer", sa.String(length=500), nullable=True))
        if "identity_subject" not in columns:
            batch.add_column(sa.Column("identity_subject", sa.String(length=500), nullable=True))
        if "uq_user_identity_subject" not in uniques:
            batch.create_unique_constraint("uq_user_identity_subject", ["identity_issuer", "identity_subject"])


def downgrade():
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("user")}
    if not {"identity_issuer", "identity_subject"} <= columns:
        return
    if op.get_bind().execute(sa.text("SELECT 1 FROM user WHERE identity_issuer IS NOT NULL OR identity_subject IS NOT NULL LIMIT 1")).first():
        raise RuntimeError("refusing downgrade: retained production identity bindings")
    with op.batch_alter_table("user") as batch:
        batch.drop_constraint("uq_user_identity_subject", type_="unique")
        batch.drop_column("identity_subject")
        batch.drop_column("identity_issuer")
