"""R2-H7: workflow_step_attempt 审计表（节点 rerun 新旧 output 均可审计）

Revision ID: d4audit00004
Revises: c3delivery00003
Create Date: 2026-09-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d4audit00004"
down_revision: str | Sequence[str] | None = "c3delivery00003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_table(engine, table: str) -> bool:
    from sqlalchemy import inspect

    return inspect(engine).has_table(table)


def upgrade() -> None:
    bind = op.get_bind()
    if _has_table(bind, "workflow_step_attempt"):
        # 全新库：初始迁移按当前模型 create_all 已建表（与 a1/b2 相同防御）
        return
    op.create_table(
        "workflow_step_attempt",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("step_id", sa.Integer(), sa.ForeignKey("workflow_step.id"), nullable=False),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("workflow_run.id"), nullable=False),
        sa.Column("node_id", sa.String(50), nullable=False),
        sa.Column("plugin_key", sa.String(150), nullable=True),
        sa.Column("plugin_version", sa.String(50), nullable=True),
        sa.Column("attempt_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("output_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("output_hash", sa.String(64), nullable=True),
        sa.Column("input_hash", sa.String(64), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_workflow_step_attempt_step", "workflow_step_attempt", ["step_id", "attempt_no"])


def downgrade() -> None:
    op.drop_index("ix_workflow_step_attempt_step", table_name="workflow_step_attempt")
    op.drop_table("workflow_step_attempt")
