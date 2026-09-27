"""Project Candidate, Review and DeliveryTarget compatibility.

Revision ID: f4a000000001
Revises: f3b000000001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f4a000000001"
down_revision: str | Sequence[str] | None = "f3b000000001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _columns(table: str) -> dict[str, dict]:
    return {column["name"]: column for column in sa.inspect(op.get_bind()).get_columns(table)}


def _add(table: str, column: sa.Column) -> None:
    if column.name not in _columns(table):
        if op.get_bind().dialect.name == "sqlite" and column.foreign_keys:
            with op.batch_alter_table(table) as batch:
                batch.add_column(column)
        else:
            op.add_column(table, column)


def _index(table: str, name: str, column: str) -> None:
    if name not in {item["name"] for item in sa.inspect(op.get_bind()).get_indexes(table)}:
        op.create_index(name, table, [column])


def upgrade() -> None:
    for column in (
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("content_project.id", name="fk_content_asset_project_id")),
        sa.Column("content_unit_id", sa.Integer(), sa.ForeignKey("content_unit.id", name="fk_content_asset_content_unit_id")),
        sa.Column("identity_snapshot_id", sa.Integer(), sa.ForeignKey("identity_snapshot.id", name="fk_content_asset_identity_snapshot_id")),
        sa.Column("workflow_run_id", sa.Integer(), sa.ForeignKey("workflow_run.id", name="fk_content_asset_workflow_run_id")),
        sa.Column("candidate_hash", sa.String(64)),
    ):
        _add("content_asset", column)
    asset_nullable = [name for name in ("draft_id", "topic_brief_id", "fact_pack_id", "fact_pack_version", "approved_revision") if not _columns("content_asset")[name]["nullable"]]
    if asset_nullable:
        with op.batch_alter_table("content_asset") as batch:
            for name in asset_nullable:
                batch.alter_column(name, nullable=True)
    for name in ("project_id", "content_unit_id", "identity_snapshot_id", "workflow_run_id", "candidate_hash"):
        _index("content_asset", f"ix_content_asset_{name}", name)
    if "uq_project_candidate_hash" not in {item["name"] for item in sa.inspect(op.get_bind()).get_unique_constraints("content_asset")}:
        with op.batch_alter_table("content_asset") as batch:
            batch.create_unique_constraint("uq_project_candidate_hash", ["project_id", "content_unit_id", "candidate_hash"])

    _add("review", sa.Column("content_asset_id", sa.Integer(), sa.ForeignKey("content_asset.id", name="fk_review_content_asset_id")))
    review_nullable = [name for name in ("draft_id", "revision_no") if not _columns("review")[name]["nullable"]]
    if review_nullable:
        with op.batch_alter_table("review") as batch:
            for name in review_nullable:
                batch.alter_column(name, nullable=True)
    _index("review", "ix_review_content_asset_id", "content_asset_id")

    _add("delivery_target", sa.Column("content_account_id", sa.Integer(), sa.ForeignKey("content_account.id", name="fk_delivery_target_content_account_id")))
    _add("delivery_target", sa.Column("authorization_account_key", sa.String(300)))
    _index("delivery_target", "ix_delivery_target_content_account_id", "content_account_id")
    op.execute(sa.text("UPDATE delivery_target SET authorization_account_key = 'legacy-ref:' || account_ref WHERE authorization_account_key IS NULL"))
    unique = next((item for item in sa.inspect(op.get_bind()).get_unique_constraints("delivery_target") if item["name"] == "uq_delivery_target_authorization"), None)
    if _columns("delivery_target")["authorization_account_key"]["nullable"] or unique is None or "authorization_account_key" not in unique["column_names"]:
        with op.batch_alter_table("delivery_target") as batch:
            if _columns("delivery_target")["authorization_account_key"]["nullable"]:
                batch.alter_column("authorization_account_key", nullable=False)
            if unique is not None:
                batch.drop_constraint("uq_delivery_target_authorization", type_="unique")
            batch.create_unique_constraint(
                "uq_delivery_target_authorization",
                ["content_asset_id", "approved_candidate_hash", "channel", "content_form", "authorization_account_key", "action", "authorization_version"],
            )


def downgrade() -> None:
    connection = op.get_bind()
    project_rows = connection.execute(sa.text("SELECT COUNT(*) FROM content_asset WHERE project_id IS NOT NULL OR draft_id IS NULL OR topic_brief_id IS NULL OR fact_pack_id IS NULL OR fact_pack_version IS NULL OR approved_revision IS NULL")).scalar_one()
    project_reviews = connection.execute(sa.text("SELECT COUNT(*) FROM review WHERE content_asset_id IS NOT NULL OR draft_id IS NULL OR revision_no IS NULL")).scalar_one()
    account_targets = connection.execute(sa.text("SELECT COUNT(*) FROM delivery_target WHERE content_account_id IS NOT NULL")).scalar_one()
    if project_rows or project_reviews or account_targets:
        raise RuntimeError("FE-F4 downgrade would discard project Candidate, Review or ContentAccount links")

    with op.batch_alter_table("delivery_target") as batch:
        batch.drop_constraint("uq_delivery_target_authorization", type_="unique")
        batch.create_unique_constraint(
            "uq_delivery_target_authorization",
            ["content_asset_id", "approved_candidate_hash", "channel", "content_form", "account_ref", "action", "authorization_version"],
        )
        batch.drop_index("ix_delivery_target_content_account_id")
        batch.drop_column("authorization_account_key")
        batch.drop_column("content_account_id")

    with op.batch_alter_table("review") as batch:
        batch.drop_index("ix_review_content_asset_id")
        batch.alter_column("draft_id", nullable=False)
        batch.alter_column("revision_no", nullable=False)
        batch.drop_column("content_asset_id")

    with op.batch_alter_table("content_asset") as batch:
        batch.drop_constraint("uq_project_candidate_hash", type_="unique")
        for name in ("project_id", "content_unit_id", "identity_snapshot_id", "workflow_run_id", "candidate_hash"):
            batch.drop_index(f"ix_content_asset_{name}")
        for name in ("draft_id", "topic_brief_id", "fact_pack_id", "fact_pack_version", "approved_revision"):
            batch.alter_column(name, nullable=False)
        for name in ("candidate_hash", "workflow_run_id", "identity_snapshot_id", "content_unit_id", "project_id"):
            batch.drop_column(name)
