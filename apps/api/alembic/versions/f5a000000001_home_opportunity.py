"""Add FE-F5A Opportunity decision resources.

Revision ID: f5a000000001
Revises: f4a000000001
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f5a000000001"
down_revision: str | Sequence[str] | None = "f4a000000001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table(name: str, *columns, **kwargs) -> None:
    # The initial migration bootstraps from current metadata on empty databases.
    if not sa.inspect(op.get_bind()).has_table(name):
        op.create_table(name, *columns, **kwargs)


def _index(name: str, table: str, columns: list[str]) -> None:
    if name not in {item["name"] for item in sa.inspect(op.get_bind()).get_indexes(table)}:
        op.create_index(name, table, columns)


def upgrade() -> None:
    _table(
        "content_opportunity",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False),
        sa.Column("relevant_until", sa.DateTime(timezone=True)),
        sa.Column("created_by", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "status IN ('new','watching','qualified','dismissed','converted','archived')",
            name="ck_content_opportunity_status",
        ),
        sa.CheckConstraint("priority IN ('low','normal','high')", name="ck_content_opportunity_priority"),
    )
    _index("ix_content_opportunity_owner_user_id", "content_opportunity", ["owner_user_id"])
    _index(
        "ix_content_opportunity_owner_status_priority",
        "content_opportunity",
        ["owner_user_id", "status", "priority", "updated_at"],
    )
    _table(
        "content_opportunity_signal",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("opportunity_id", sa.Integer(), sa.ForeignKey("content_opportunity.id"), nullable=False),
        sa.Column("signal_type", sa.String(30), nullable=False),
        sa.Column("source_entity_id", sa.Integer()),
        sa.Column("external_ref", sa.String(1000)),
        sa.Column("label", sa.String(300), nullable=False),
        sa.Column("annotation_json", sa.JSON(), nullable=False),
        sa.Column("source_checksum", sa.String(64)),
        sa.Column("source_version", sa.String(100)),
        sa.Column("observed_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("attached_by", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("detached_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("opportunity_id", "signal_type", "source_entity_id", name="uq_opportunity_signal_resource"),
        sa.CheckConstraint("status IN ('active','detached')", name="ck_opportunity_signal_status"),
    )
    _index("ix_content_opportunity_signal_opportunity_id", "content_opportunity_signal", ["opportunity_id"])
    _index(
        "ix_opportunity_signal_type_status", "content_opportunity_signal", ["opportunity_id", "signal_type", "status"]
    )
    _table(
        "content_opportunity_assessment_revision",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("opportunity_id", sa.Integer(), sa.ForeignKey("content_opportunity.id"), nullable=False),
        sa.Column("revision_no", sa.Integer(), nullable=False),
        sa.Column("parent_revision_id", sa.Integer(), sa.ForeignKey("content_opportunity_assessment_revision.id")),
        sa.Column("assessment_json", sa.JSON(), nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("analysis_source", sa.String(30), nullable=False),
        sa.Column("analysis_provider_key", sa.String(100)),
        sa.Column("analysis_provider_version", sa.String(100)),
        sa.Column("created_by", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("opportunity_id", "revision_no", name="uq_opportunity_assessment_revision"),
    )
    _index(
        "ix_content_opportunity_assessment_revision_opportunity_id",
        "content_opportunity_assessment_revision",
        ["opportunity_id"],
    )
    _table(
        "opportunity_project_conversion",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("opportunity_id", sa.Integer(), sa.ForeignKey("content_opportunity.id"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("content_project.id"), nullable=False),
        sa.Column(
            "assessment_revision_id",
            sa.Integer(),
            sa.ForeignKey("content_opportunity_assessment_revision.id"),
            nullable=False,
        ),
        sa.Column("idempotency_key", sa.String(100), nullable=False),
        sa.Column("conversion_snapshot_json", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("opportunity_id", name="uq_opportunity_conversion_opportunity"),
        sa.UniqueConstraint("project_id", name="uq_opportunity_conversion_project"),
        sa.UniqueConstraint("idempotency_key", name="uq_opportunity_conversion_key"),
    )
    _index("ix_opportunity_project_conversion_opportunity_id", "opportunity_project_conversion", ["opportunity_id"])
    _index("ix_opportunity_project_conversion_project_id", "opportunity_project_conversion", ["project_id"])


def downgrade() -> None:
    op.drop_table("opportunity_project_conversion")
    op.drop_table("content_opportunity_assessment_revision")
    op.drop_table("content_opportunity_signal")
    op.drop_table("content_opportunity")
