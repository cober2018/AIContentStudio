"""add M1 state check constraints to already-migrated local databases"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f16180339887"
down_revision: Union[str, Sequence[str], None] = "e27182818284"
branch_labels = None
depends_on = None


def _names(table: str) -> set[str]:
    return {item["name"] for item in sa.inspect(op.get_bind()).get_check_constraints(table) if item.get("name")}


def upgrade() -> None:
    if "ck_fact_pack_item_evidence_kind" not in _names("fact_pack_item"):
        with op.batch_alter_table("fact_pack_item") as batch:
            batch.create_check_constraint(
                "ck_fact_pack_item_evidence_kind",
                "evidence_kind IN ('fact', 'event', 'third_party_quote', 'author_opinion', 'legacy_untyped')",
            )
    if "ck_draft_media_role" not in _names("draft_media"):
        with op.batch_alter_table("draft_media") as batch:
            batch.create_check_constraint("ck_draft_media_role", "role IN ('cover', 'inline', 'attachment')")
    target_checks = _names("delivery_target")
    with op.batch_alter_table("delivery_target") as batch:
        if "ck_delivery_target_channel" not in target_checks:
            batch.create_check_constraint("ck_delivery_target_channel", "channel IN ('wechat', 'x_thread')")
        if "ck_delivery_target_action" not in target_checks:
            batch.create_check_constraint("ck_delivery_target_action", "action = 'manual_handoff'")
        if "ck_delivery_target_status" not in target_checks:
            batch.create_check_constraint(
                "ck_delivery_target_status",
                "status IN ('approved', 'target_authorized', 'package_ready', 'awaiting_manual_receipt', 'human_confirmed', 'failed', 'reconciliation_needed', 'canceled')",
            )


def downgrade() -> None:
    # New M1 history is preserved; disabling the flow is the rollback path.
    pass
