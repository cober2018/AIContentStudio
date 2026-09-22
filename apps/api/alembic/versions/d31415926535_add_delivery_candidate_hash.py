"""bind manual delivery targets to the approved candidate hash"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d31415926535"
down_revision: Union[str, Sequence[str], None] = "c2047840a2c6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "approved_candidate_hash" not in {c["name"] for c in inspector.get_columns("delivery_target")}:  # pragma: no branch
        op.add_column("delivery_target", sa.Column("approved_candidate_hash", sa.String(length=64), nullable=True))


def downgrade() -> None:
    # Keep authorization history recoverable when M1 is disabled.
    pass
