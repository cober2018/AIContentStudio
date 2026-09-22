"""reconcile M1 nullable evidence and target authorization constraints"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e27182818284"
down_revision: Union[str, Sequence[str], None] = "d31415926535"
branch_labels = None
depends_on = None


def _columns(table: str) -> dict[str, dict]:
    return {item["name"]: item for item in sa.inspect(op.get_bind()).get_columns(table)}


def _check_names(table: str) -> set[str]:
    return {item["name"] for item in sa.inspect(op.get_bind()).get_check_constraints(table) if item.get("name")}


def _has_foreign_key(table: str, column: str) -> bool:
    return any(column in (item.get("constrained_columns") or []) for item in sa.inspect(op.get_bind()).get_foreign_keys(table))


def upgrade() -> None:
    bind = op.get_bind()
    fact_columns = _columns("fact_pack_item")
    fact_checks = _check_names("fact_pack_item")
    if fact_columns["fact_id"].get("nullable") is not True or "ck_fact_pack_item_evidence_kind" not in fact_checks:
        with op.batch_alter_table("fact_pack_item") as batch:
            if fact_columns["fact_id"].get("nullable") is not True:
                batch.alter_column("fact_id", existing_type=sa.Integer(), nullable=True)
            if "ck_fact_pack_item_evidence_kind" not in fact_checks:
                batch.create_check_constraint(
                    "ck_fact_pack_item_evidence_kind",
                    "evidence_kind IN ('fact', 'event', 'third_party_quote', 'author_opinion', 'legacy_untyped')",
                )

    draft_columns = _columns("draft")
    if "evidence_checksum" not in draft_columns or not _has_foreign_key("draft", "mother_revision_id"):
        with op.batch_alter_table("draft") as batch:
            if "evidence_checksum" not in draft_columns:
                batch.add_column(sa.Column("evidence_checksum", sa.String(length=64), nullable=True))
            if not _has_foreign_key("draft", "mother_revision_id"):
                batch.create_foreign_key("fk_draft_mother_revision", "mother_revision", ["mother_revision_id"], ["id"])

    if not _has_foreign_key("content_asset", "mother_revision_id"):
        with op.batch_alter_table("content_asset") as batch:
            batch.create_foreign_key("fk_content_asset_mother_revision", "mother_revision", ["mother_revision_id"], ["id"])

    target_columns = _columns("delivery_target")
    # Preserve records created while the first additive migration was live.
    # Rows still missing a hash remain legacy/ineligible instead of making the
    # migration fail or inventing an approval binding.
    bind.execute(sa.text("""
        UPDATE delivery_target
        SET approved_candidate_hash = (
            SELECT approved_candidate_hash FROM content_asset
            WHERE content_asset.id = delivery_target.content_asset_id
        )
        WHERE approved_candidate_hash IS NULL
    """))
    target_checks = _check_names("delivery_target")
    target_unique = next(
        (item for item in sa.inspect(op.get_bind()).get_unique_constraints("delivery_target")
         if item.get("name") == "uq_delivery_target_authorization"),
        None,
    )
    expected_unique = ["content_asset_id", "approved_candidate_hash", "channel", "content_form", "account_ref", "action", "authorization_version"]
    needs_target_change = (
        (target_columns["approved_candidate_hash"].get("nullable") is not False
         and bind.execute(sa.text("SELECT COUNT(*) FROM delivery_target WHERE approved_candidate_hash IS NULL")).scalar() == 0)
        or (target_unique or {}).get("column_names") != expected_unique
        or any(name not in target_checks for name in {
            "ck_delivery_target_channel", "ck_delivery_target_action", "ck_delivery_target_status",
        })
    )
    if needs_target_change:
        with op.batch_alter_table("delivery_target") as batch:
            if target_unique and target_unique.get("column_names") != expected_unique:
                batch.drop_constraint("uq_delivery_target_authorization", type_="unique")
            if target_columns["approved_candidate_hash"].get("nullable") is not False and bind.execute(sa.text("SELECT COUNT(*) FROM delivery_target WHERE approved_candidate_hash IS NULL")).scalar() == 0:
                batch.alter_column("approved_candidate_hash", existing_type=sa.String(length=64), nullable=False)
            if not target_unique or target_unique.get("column_names") != expected_unique:
                batch.create_unique_constraint("uq_delivery_target_authorization", expected_unique)
            if "ck_delivery_target_channel" not in target_checks:
                batch.create_check_constraint("ck_delivery_target_channel", "channel IN ('wechat', 'x_thread')")
            if "ck_delivery_target_action" not in target_checks:
                batch.create_check_constraint("ck_delivery_target_action", "action = 'manual_handoff'")
            if "ck_delivery_target_status" not in target_checks:
                batch.create_check_constraint(
                    "ck_delivery_target_status",
                    "status IN ('approved', 'target_authorized', 'package_ready', 'awaiting_manual_receipt', 'human_confirmed', 'failed', 'reconciliation_needed', 'canceled')",
                )

    receipt_columns = _columns("delivery_receipt")
    if "approved_candidate_hash" not in receipt_columns or "action" not in receipt_columns:
        with op.batch_alter_table("delivery_receipt") as batch:
            if "approved_candidate_hash" not in receipt_columns:
                batch.add_column(sa.Column("approved_candidate_hash", sa.String(length=64), nullable=True))
            if "action" not in receipt_columns:
                batch.add_column(sa.Column("action", sa.String(length=30), nullable=False, server_default="manual_handoff"))
    bind.execute(sa.text("""
        UPDATE delivery_receipt
        SET approved_candidate_hash = (
            SELECT approved_candidate_hash FROM delivery_target
            WHERE delivery_target.id = delivery_receipt.target_id
        )
        WHERE approved_candidate_hash IS NULL
    """))


def downgrade() -> None:
    # Additive M1 history is intentionally preserved. Rollback disables entry
    # points; it does not remove evidence, approvals, receipts, or feedback.
    pass
