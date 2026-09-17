"""initial schema

Revision ID: 151107e577eb
Revises:
Create Date: 2026-09-17 13:42:49.245388

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.db import Base
from app import models  # noqa: F401  注册全部模型


# revision identifiers, used by Alembic.
revision: str = '151107e577eb'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """从当前模型全量建表（初始迁移；后续变更用 autogenerate 增量迁移）。"""
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
