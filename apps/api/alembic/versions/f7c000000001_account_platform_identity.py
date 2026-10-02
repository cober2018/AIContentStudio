"""Add exclusive platform identity to existing accounts without inferring legacy bindings."""

import sqlalchemy as sa

from alembic import op

revision = "f7c000000001"
down_revision = "f7b000000001"
branch_labels = None
depends_on = None

_PAIR = "ck_content_account_platform_pair"
_UNIQUE = "uq_content_account_platform_identity"
_EXPRESSION = "(platform_channel IS NULL AND platform_account_id IS NULL) OR (platform_channel IS NOT NULL AND platform_account_id IS NOT NULL)"


def upgrade():
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("content_account")}
    checks = {item["name"] for item in inspector.get_check_constraints("content_account")}
    uniques = {item["name"] for item in inspector.get_unique_constraints("content_account")}
    if {"platform_channel", "platform_account_id"} <= columns and _PAIR in checks and _UNIQUE in uniques:
        return
    with op.batch_alter_table("content_account") as batch:
        if "platform_channel" not in columns:
            batch.add_column(sa.Column("platform_channel", sa.String(50), nullable=True))
        if "platform_account_id" not in columns:
            batch.add_column(sa.Column("platform_account_id", sa.String(128), nullable=True))
        if _PAIR not in checks:
            batch.create_check_constraint(_PAIR, _EXPRESSION)
        if _UNIQUE not in uniques:
            batch.create_unique_constraint(_UNIQUE, ["platform_channel", "platform_account_id"])


def downgrade():
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("content_account")}
    if "platform_channel" not in columns and "platform_account_id" not in columns:
        return
    predicates = [f"{name} IS NOT NULL" for name in ("platform_channel", "platform_account_id") if name in columns]
    if op.get_bind().execute(sa.text("SELECT 1 FROM content_account WHERE " + " OR ".join(predicates) + " LIMIT 1")).first():
        raise RuntimeError("refusing downgrade: retained platform identity")
    checks = {item["name"] for item in inspector.get_check_constraints("content_account")}
    uniques = {item["name"] for item in inspector.get_unique_constraints("content_account")}
    with op.batch_alter_table("content_account") as batch:
        if _UNIQUE in uniques:
            batch.drop_constraint(_UNIQUE, type_="unique")
        if _PAIR in checks:
            batch.drop_constraint(_PAIR, type_="check")
        for name in ("platform_account_id", "platform_channel"):
            if name in columns:
                batch.drop_column(name)
