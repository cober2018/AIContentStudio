"""add asset_media

Revision ID: d4e7f2a90c18
Revises: b91c4e27af05
Create Date: 2026-09-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "d4e7f2a90c18"
down_revision: Union[str, Sequence[str], None] = "b91c4e27af05"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """资产配图素材（统一素材池，asset 归属随文展示）。

    初始迁移按当前模型 create_all，模型后加入历史链的表会被提前建出；
    存在即跳过，保证全新库一次性 upgrade head 不撞 DuplicateTable。
    """
    bind = op.get_bind()
    if sa.inspect(bind).has_table("asset_media"):
        return
    op.create_table(
        "asset_media",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=10), nullable=False),
        sa.Column("source", sa.String(length=10), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=True),
        sa.Column("file_path", sa.String(length=300), nullable=True),
        sa.Column("mime_type", sa.String(length=50), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["content_asset.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("asset_media")
