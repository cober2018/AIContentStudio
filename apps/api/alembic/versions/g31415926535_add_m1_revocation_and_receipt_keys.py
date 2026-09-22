"""add M1 public-use revocation controls and receipt idempotency"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "g31415926535"
down_revision: Union[str, Sequence[str], None] = "f16180339887"
branch_labels = None
depends_on = None


def _columns(table: str) -> set[str]:
    return {item["name"] for item in sa.inspect(op.get_bind()).get_columns(table)}


def _checks(table: str) -> set[str]:
    return {item["name"] for item in sa.inspect(op.get_bind()).get_check_constraints(table) if item.get("name")}


def upgrade() -> None:
    for table in ("fact_pack_item", "draft_media"):
        columns = _columns(table)
        with op.batch_alter_table(table) as batch:
            if "public_use_revoked_at" not in columns:
                batch.add_column(sa.Column("public_use_revoked_at", sa.DateTime(timezone=True), nullable=True))
            if "public_use_revocation_note" not in columns:
                batch.add_column(sa.Column("public_use_revocation_note", sa.Text(), nullable=True))

    receipt_columns = _columns("delivery_receipt")
    receipt_uniques = {item.get("name") for item in sa.inspect(op.get_bind()).get_unique_constraints("delivery_receipt")}
    with op.batch_alter_table("delivery_receipt") as batch:
        if "idempotency_key" not in receipt_columns:
            batch.add_column(sa.Column("idempotency_key", sa.String(length=64), nullable=True))
        if "uq_delivery_receipt_idempotency" not in receipt_uniques:
            batch.create_unique_constraint("uq_delivery_receipt_idempotency", ["target_id", "idempotency_key"])
    op.execute("UPDATE delivery_receipt SET idempotency_key = 'legacy-' || id WHERE idempotency_key IS NULL")

    target_checks = _checks("delivery_target")
    if "ck_delivery_target_status" in target_checks:
        with op.batch_alter_table("delivery_target") as batch:
            batch.drop_constraint("ck_delivery_target_status", type_="check")
            batch.create_check_constraint(
                "ck_delivery_target_status",
                "status IN ('approved', 'target_authorized', 'package_ready', 'awaiting_manual_receipt', 'human_confirmed', 'failed', 'reconciliation_needed', 'blocked', 'canceled')",
            )


def downgrade() -> None:
    # Revocations and receipt keys are audit evidence; rollback disables M1 entry points only.
    pass
