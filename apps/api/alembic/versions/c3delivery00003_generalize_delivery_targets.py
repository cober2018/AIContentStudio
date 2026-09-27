"""V1 PRD 2.0 Content Harness — Migration C（additive）。

覆盖（开发 OpenSpec §5 Migration C + §6.23 折入）：
- 新表 delivery_attempt
- delivery_target：+ publisher_key/publisher_version/capability_snapshot_json/requested_at；
  重建 check constraints（去 channel enum check；action 扩四值）
- content_asset：+ artifact_kind/content_form/workflow_key/workflow_version（§6.23 查询列，
  原文未列入 §5 清单，折入本迁移避免第四次 migration——见 design.md D5-a）

历史 target：publisher_key='publisher.copy.legacy'，不改变历史 receipt。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c3delivery00003"
down_revision: Union[str, Sequence[str], None] = "b2material00002"
branch_labels = None
depends_on = None


def _has_table(engine, table: str) -> bool:
    return table in set(sa.inspect(engine).get_table_names())


def _columns(table: str) -> dict[str, dict]:
    return {item["name"]: item for item in sa.inspect(op.get_bind()).get_columns(table)}


def _check_names(table: str) -> set[str]:
    return {item["name"] for item in sa.inspect(op.get_bind()).get_check_constraints(table) if item.get("name")}


NEW_ACTION_CHECK = "action IN ('manual_handoff', 'copy_package', 'assisted_draft', 'auto_draft')"


def upgrade() -> None:
    bind = op.get_bind()

    # ---- delivery_attempt ----
    if not _has_table(bind, "delivery_attempt"):
        op.create_table(
            "delivery_attempt",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("target_id", sa.Integer(), sa.ForeignKey("delivery_target.id"), nullable=False),
            sa.Column("attempt_no", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("idempotency_key", sa.String(length=64), nullable=False),
            sa.Column("publisher_key", sa.String(length=150), nullable=True),
            sa.Column("publisher_version", sa.String(length=50), nullable=True),
            sa.Column("request_hash", sa.String(length=64), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="prepared"),
            sa.Column("remote_id", sa.String(length=200), nullable=True),
            sa.Column("response_metadata_json", sa.JSON(), nullable=True),
            sa.Column("error", sa.Text(), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("target_id", "attempt_no", name="uq_delivery_attempt_no"),
            sa.UniqueConstraint("idempotency_key", name="uq_delivery_attempt_idempotency"),
        )

    # ---- delivery_target：新列 + 约束重建 ----
    dt_cols = _columns("delivery_target")
    with op.batch_alter_table("delivery_target") as batch:
        for col in (
            sa.Column("publisher_key", sa.String(length=150), nullable=True),
            sa.Column("publisher_version", sa.String(length=50), nullable=True),
            sa.Column("capability_snapshot_json", sa.JSON(), nullable=True),
            sa.Column("requested_at", sa.DateTime(timezone=True), nullable=True),
        ):
            if col.name not in dt_cols:
                batch.add_column(col)
    bind.execute(sa.text("UPDATE delivery_target SET publisher_key = 'publisher.copy.legacy' WHERE publisher_key IS NULL"))

    checks = _check_names("delivery_target")
    with op.batch_alter_table("delivery_target") as batch:
        if "ck_delivery_target_channel" in checks:
            batch.drop_constraint("ck_delivery_target_channel", type_="check")
        if "ck_delivery_target_action" in checks:
            batch.drop_constraint("ck_delivery_target_action", type_="check")
        if "ck_delivery_target_action" not in _check_names("delivery_target"):
            batch.create_check_constraint("ck_delivery_target_action", NEW_ACTION_CHECK)

    # ---- content_asset：v2 查询列 ----
    ca_cols = _columns("content_asset")
    with op.batch_alter_table("content_asset") as batch:
        for col in (
            sa.Column("artifact_kind", sa.String(length=20), nullable=True),
            sa.Column("content_form", sa.String(length=50), nullable=True),
            sa.Column("workflow_key", sa.String(length=120), nullable=True),
            sa.Column("workflow_version", sa.Integer(), nullable=True),
        ):
            if col.name not in ca_cols:
                batch.add_column(col)
    bind.execute(sa.text("UPDATE content_asset SET artifact_kind = 'script' WHERE artifact_kind IS NULL AND channel = 'douyin'"))
    bind.execute(sa.text("UPDATE content_asset SET artifact_kind = 'text' WHERE artifact_kind IS NULL"))


def downgrade() -> None:
    # Additive：交付历史（含 attempts）不回滚删除
    pass
