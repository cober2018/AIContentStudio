"""add system_settings

Revision ID: b91c4e27af05
Revises: 151107e577eb
Create Date: 2026-09-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b91c4e27af05"
down_revision: Union[str, Sequence[str], None] = "151107e577eb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """运行时配置覆盖表（前端设置页写入，值优先于环境变量）。

    初始迁移按当前模型 create_all，模型后加入历史链的表会被提前建出；
    存在即跳过，保证全新库一次性 upgrade head 不撞 DuplicateTable。
    """
    bind = op.get_bind()
    if sa.inspect(bind).has_table("system_settings"):
        return
    op.create_table(
        "system_settings",
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("key"),
    )


def downgrade() -> None:
    op.drop_table("system_settings")
