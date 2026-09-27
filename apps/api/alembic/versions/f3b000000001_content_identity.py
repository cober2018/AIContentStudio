"""FE-F3B versioned content identity and frozen production snapshots.

Revision ID: f3b000000001
Revises: f3a000000001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f3b000000001"
down_revision: str | Sequence[str] | None = "f3a000000001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table(name: str, *columns, **kwargs) -> None:
    if not sa.inspect(op.get_bind()).has_table(name):
        op.create_table(name, *columns, **kwargs)


def _index(name: str, table: str, columns: list[str]) -> None:
    if name not in {item["name"] for item in sa.inspect(op.get_bind()).get_indexes(table)}:
        op.create_index(name, table, columns)


def _revision_table(name: str, parent: str, constraint: str) -> None:
    _table(
        name,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(parent + "_id", sa.Integer(), sa.ForeignKey(f"content_{parent}.id"), nullable=False),
        sa.Column("revision_no", sa.Integer(), nullable=False),
        sa.Column("profile_json", sa.JSON(), nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("created_by", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(parent + "_id", "revision_no", name=constraint),
    )
    _index(f"ix_{name}_{parent}_id", name, [parent + "_id"])


def _add_columns(table: str, columns: list[sa.Column], indexes: list[tuple[str, list[str]]]) -> None:
    existing = {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table)}
    missing = [column for column in columns if column.name not in existing]
    if missing:
        with op.batch_alter_table(table) as batch:
            for column in missing:
                batch.add_column(column)
    for name, fields in indexes:
        _index(name, table, fields)


def upgrade() -> None:
    _table(
        "content_brand",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    _index("ix_content_brand_owner_user_id", "content_brand", ["owner_user_id"])
    _add_columns("content_persona", [
        sa.Column("brand_id", sa.Integer(), sa.ForeignKey("content_brand.id", name="fk_content_persona_brand_id")),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
    ], [("ix_content_persona_brand_id", ["brand_id"])])
    _table(
        "content_account",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("persona_id", sa.Integer(), sa.ForeignKey("content_persona.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    _index("ix_content_account_persona_id", "content_account", ["persona_id"])
    _table(
        "content_series",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("content_account.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    _index("ix_content_series_account_id", "content_series", ["account_id"])

    for name, parent, constraint in (
        ("content_brand_revision", "brand", "uq_content_brand_revision"),
        ("content_persona_revision", "persona", "uq_content_persona_revision"),
        ("content_account_revision", "account", "uq_content_account_revision"),
        ("content_series_revision", "series", "uq_content_series_revision"),
    ):
        _revision_table(name, parent, constraint)

    _table(
        "identity_snapshot",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("brand_id", sa.Integer(), sa.ForeignKey("content_brand.id")),
        sa.Column("brand_revision_id", sa.Integer(), sa.ForeignKey("content_brand_revision.id")),
        sa.Column("persona_id", sa.Integer(), sa.ForeignKey("content_persona.id"), nullable=False),
        sa.Column("persona_revision_id", sa.Integer(), sa.ForeignKey("content_persona_revision.id")),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("content_account.id")),
        sa.Column("account_revision_id", sa.Integer(), sa.ForeignKey("content_account_revision.id")),
        sa.Column("series_id", sa.Integer(), sa.ForeignKey("content_series.id")),
        sa.Column("series_revision_id", sa.Integer(), sa.ForeignKey("content_series_revision.id")),
        sa.Column("brand_voice_version_id", sa.Integer(), sa.ForeignKey("brand_voice_version.id")),
        sa.Column("effective_profile_json", sa.JSON(), nullable=False),
        sa.Column("field_origins_json", sa.JSON(), nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("created_by", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    _index("ix_identity_snapshot_owner_user_id", "identity_snapshot", ["owner_user_id"])
    _index("ix_identity_snapshot_persona_id", "identity_snapshot", ["persona_id"])

    for name, parent, constraint in (
        ("account_workflow_default", "account", "uq_account_workflow_default"),
        ("series_workflow_default", "series", "uq_series_workflow_default"),
    ):
        _table(
            name,
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(parent + "_id", sa.Integer(), sa.ForeignKey(f"content_{parent}.id"), nullable=False),
            sa.Column("modality", sa.String(20), nullable=False),
            sa.Column("workflow_id", sa.Integer(), sa.ForeignKey("workflow.id"), nullable=False),
            sa.Column("revision", sa.Integer(), nullable=False),
            sa.UniqueConstraint(parent + "_id", "modality", name=constraint),
        )
        _index(f"ix_{name}_{parent}_id", name, [parent + "_id"])

    _add_columns("content_unit", [
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("content_account.id", name="fk_content_unit_account_id")),
        sa.Column("series_id", sa.Integer(), sa.ForeignKey("content_series.id", name="fk_content_unit_series_id")),
        sa.Column("identity_snapshot_id", sa.Integer(), sa.ForeignKey("identity_snapshot.id", name="fk_content_unit_identity_snapshot_id")),
    ], [
        ("ix_content_unit_account_id", ["account_id"]),
        ("ix_content_unit_series_id", ["series_id"]),
        ("ix_content_unit_identity_snapshot_id", ["identity_snapshot_id"]),
    ])
    _add_columns("workflow_run", [
        sa.Column("identity_snapshot_id", sa.Integer(), sa.ForeignKey("identity_snapshot.id", name="fk_workflow_run_identity_snapshot_id")),
    ], [("ix_workflow_run_identity_snapshot_id", ["identity_snapshot_id"])])


def downgrade() -> None:
    for table, columns, indexes in (
        ("workflow_run", ["identity_snapshot_id"], ["ix_workflow_run_identity_snapshot_id"]),
        ("content_unit", ["account_id", "series_id", "identity_snapshot_id"], ["ix_content_unit_account_id", "ix_content_unit_series_id", "ix_content_unit_identity_snapshot_id"]),
    ):
        with op.batch_alter_table(table) as batch:
            for name in indexes:
                batch.drop_index(name)
            for name in columns:
                batch.drop_column(name)
    for table, index in (
        ("series_workflow_default", "ix_series_workflow_default_series_id"),
        ("account_workflow_default", "ix_account_workflow_default_account_id"),
        ("identity_snapshot", "ix_identity_snapshot_persona_id"),
    ):
        op.drop_index(index, table_name=table)
        if table == "identity_snapshot":
            op.drop_index("ix_identity_snapshot_owner_user_id", table_name=table)
        op.drop_table(table)
    for table, parent in (
        ("content_series_revision", "series"),
        ("content_account_revision", "account"),
        ("content_persona_revision", "persona"),
        ("content_brand_revision", "brand"),
    ):
        op.drop_index(f"ix_{table}_{parent}_id", table_name=table)
        op.drop_table(table)
    op.drop_index("ix_content_series_account_id", table_name="content_series")
    op.drop_table("content_series")
    op.drop_index("ix_content_account_persona_id", table_name="content_account")
    op.drop_table("content_account")
    with op.batch_alter_table("content_persona") as batch:
        batch.drop_index("ix_content_persona_brand_id")
        batch.drop_column("status")
        batch.drop_column("brand_id")
    op.drop_index("ix_content_brand_owner_user_id", table_name="content_brand")
    op.drop_table("content_brand")
