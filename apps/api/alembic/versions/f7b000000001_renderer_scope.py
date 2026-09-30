"""Widen existing capability verification scopes without rewriting evidence."""

import sqlalchemy as sa

from alembic import op

revision = "f7b000000001"
down_revision = "f7a000000001"
branch_labels = None
depends_on = None

_NAME = "ck_capability_verification_scope_kind"
_OLD = "scope_kind IN ('publisher_action', 'data_source_endpoint')"
_NEW = "scope_kind IN ('publisher_action', 'data_source_endpoint', 'renderer_output')"


def _scope_constraint():
    return next(item["sqltext"] for item in sa.inspect(op.get_bind()).get_check_constraints("capability_verification") if item["name"] == _NAME)


def upgrade():
    if "renderer_output" not in _scope_constraint():
        with op.batch_alter_table("capability_verification") as batch:
            batch.drop_constraint(_NAME, type_="check")
            batch.create_check_constraint(_NAME, _NEW)


def downgrade():
    if op.get_bind().execute(sa.text("SELECT 1 FROM capability_verification WHERE scope_kind = 'renderer_output' LIMIT 1")).first():
        raise RuntimeError("refusing downgrade: retained renderer verification")
    if "renderer_output" in _scope_constraint():
        with op.batch_alter_table("capability_verification") as batch:
            batch.drop_constraint(_NAME, type_="check")
            batch.create_check_constraint(_NAME, _OLD)
