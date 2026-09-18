"""add workflow tables

Revision ID: e6f9a3b21d47
Revises: d4e7f2a90c18
Create Date: 2026-09-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "e6f9a3b21d47"
down_revision: Union[str, Sequence[str], None] = "d4e7f2a90c18"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """工作流画布三表：定义 / 执行 / 步。

    初始迁移按当前模型 create_all，模型后加入历史链的表会被提前建出；
    逐表存在即跳过，保证全新库一次性 upgrade head 不撞 DuplicateTable。
    """
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("workflow"):
        op.create_table(
            "workflow",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("template_key", sa.String(length=50), nullable=True),
            sa.Column("definition_json", sa.JSON(), nullable=False),
            sa.Column("enabled", sa.Boolean(), nullable=False),
            sa.Column("created_by", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
    if not inspector.has_table("workflow_run"):
        op.create_table(
            "workflow_run",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("workflow_id", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("context_json", sa.JSON(), nullable=False),
            sa.Column("params_json", sa.JSON(), nullable=False),
            sa.Column("error", sa.Text(), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["workflow_id"], ["workflow.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    if not inspector.has_table("workflow_step"):
        op.create_table(
            "workflow_step",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("run_id", sa.Integer(), nullable=False),
            sa.Column("node_id", sa.String(length=50), nullable=False),
            sa.Column("node_type", sa.String(length=30), nullable=False),
            sa.Column("label", sa.String(length=200), nullable=True),
            sa.Column("params_json", sa.JSON(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("output_json", sa.JSON(), nullable=False),
            sa.Column("error", sa.Text(), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["run_id"], ["workflow_run.id"]),
            sa.PrimaryKeyConstraint("id"),
        )


def downgrade() -> None:
    op.drop_table("workflow_step")
    op.drop_table("workflow_run")
    op.drop_table("workflow")
