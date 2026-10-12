"""Add nullable input and execution receipts to workflow step attempts."""

import sqlalchemy as sa

from alembic import op

revision = "crs000000001"
down_revision = "aco000000001"
branch_labels = None
depends_on = None


_TABLE = "workflow_step_attempt"
_COLUMNS = ("input_snapshot_json", "execution_receipt_json")


def _columns() -> dict[str, dict]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table(_TABLE):
        raise RuntimeError(f"stage attempt receipt schema missing: {_TABLE}")
    return {column["name"]: column for column in inspector.get_columns(_TABLE)}


def _validate_column(name: str, column: dict) -> None:
    if not column["nullable"] or not isinstance(column["type"], sa.JSON):
        raise RuntimeError(f"stage attempt receipt schema mismatch: {_TABLE}.{name}")


def upgrade() -> None:
    columns = _columns()
    for name in _COLUMNS:
        column = columns.get(name)
        if column is None:
            op.add_column(_TABLE, sa.Column(name, sa.JSON(none_as_null=True), nullable=True))
        else:
            _validate_column(name, column)


def downgrade() -> None:
    bind = op.get_bind()
    columns = _columns()
    present = set(_COLUMNS) & columns.keys()
    if not present:
        return
    if present != set(_COLUMNS):
        raise RuntimeError(f"stage attempt receipt schema mismatch: {_TABLE}")
    if bind.execute(sa.text(
        f"SELECT 1 FROM {_TABLE} WHERE input_snapshot_json IS NOT NULL "
        "OR execution_receipt_json IS NOT NULL LIMIT 1"
    )).first():
        raise RuntimeError("refusing downgrade: retained stage attempt receipt/input snapshot")
    with op.batch_alter_table(_TABLE) as batch:
        for name in reversed(_COLUMNS):
            batch.drop_column(name)
