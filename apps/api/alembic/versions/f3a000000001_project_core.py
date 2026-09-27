"""FE-F3A project core references, revisions and activity.

Revision ID: f3a000000001
Revises: e5fef2000001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f3a000000001"
down_revision: str | Sequence[str] | None = "e5fef2000001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _create_table(name: str, *columns: sa.Column, **kwargs) -> None:
    if not sa.inspect(op.get_bind()).has_table(name):
        op.create_table(name, *columns, **kwargs)


def _create_index(name: str, table: str, columns: list[str]) -> None:
    if name not in {index["name"] for index in sa.inspect(op.get_bind()).get_indexes(table)}:
        op.create_index(name, table, columns)


def upgrade() -> None:
    _create_table(
        "creative_brief_revision",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("content_project.id"), nullable=False),
        sa.Column("revision_no", sa.Integer(), nullable=False),
        sa.Column("parent_revision_id", sa.Integer(), sa.ForeignKey("creative_brief_revision.id")),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("primary_audience", sa.Text()),
        sa.Column("core_message", sa.Text()),
        sa.Column("angle", sa.Text()),
        sa.Column("required_evidence_json", sa.JSON(), nullable=False),
        sa.Column("content_constraints_json", sa.JSON(), nullable=False),
        sa.Column("identity_scope_json", sa.JSON(), nullable=False),
        sa.Column("modality_scope_json", sa.JSON(), nullable=False),
        sa.Column("channel_scope_json", sa.JSON(), nullable=False),
        sa.Column("cta", sa.Text()),
        sa.Column("references_json", sa.JSON(), nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("created_by", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("project_id", "revision_no", name="uq_creative_brief_project_revision"),
    )
    _create_index("ix_creative_brief_project_created", "creative_brief_revision", ["project_id", "created_at"])
    _create_table(
        "project_source_binding",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("content_project.id"), nullable=False),
        sa.Column("source_document_id", sa.Integer(), sa.ForeignKey("source_document.id"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("note", sa.Text()),
        sa.Column("attached_by", sa.String(255)),
        sa.Column("attached_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("detached_by", sa.String(255)),
        sa.Column("detached_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("project_id", "source_document_id", name="uq_project_source"),
    )
    _create_index("ix_project_source_project_status", "project_source_binding", ["project_id", "status"])
    _create_table(
        "project_fact_boundary_revision",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("content_project.id"), nullable=False),
        sa.Column("revision_no", sa.Integer(), nullable=False),
        sa.Column("parent_revision_id", sa.Integer(), sa.ForeignKey("project_fact_boundary_revision.id")),
        sa.Column("fact_pack_id", sa.Integer(), sa.ForeignKey("fact_pack.id"), nullable=False),
        sa.Column("fact_pack_version", sa.Integer(), nullable=False),
        sa.Column("fact_pack_checksum", sa.String(64), nullable=False),
        sa.Column("created_by", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("project_id", "revision_no", name="uq_project_fact_boundary_revision"),
    )
    _create_index("ix_project_fact_boundary_project_created", "project_fact_boundary_revision", ["project_id", "created_at"])
    _create_table(
        "project_material_reference",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("content_project.id"), nullable=False),
        sa.Column("material_revision_id", sa.Integer(), sa.ForeignKey("material_revision.id"), nullable=False),
        sa.Column("origin", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("note", sa.Text()),
        sa.Column("attached_by", sa.String(255)),
        sa.Column("attached_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("detached_by", sa.String(255)),
        sa.Column("detached_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("project_id", "material_revision_id", name="uq_project_material_revision"),
    )
    _create_index("ix_project_material_project_status", "project_material_reference", ["project_id", "status"])
    _create_table(
        "project_event",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("content_project.id"), nullable=False),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("entity_type", sa.String(50)),
        sa.Column("entity_id", sa.String(80)),
        sa.Column("actor", sa.String(255)),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    _create_index("ix_project_event_project_id_id", "project_event", ["project_id", "id"])
    _create_index("ix_project_event_project_created", "project_event", ["project_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_project_event_project_created", table_name="project_event")
    op.drop_index("ix_project_event_project_id_id", table_name="project_event")
    op.drop_table("project_event")
    op.drop_index("ix_project_material_project_status", table_name="project_material_reference")
    op.drop_table("project_material_reference")
    op.drop_index("ix_project_fact_boundary_project_created", table_name="project_fact_boundary_revision")
    op.drop_table("project_fact_boundary_revision")
    op.drop_index("ix_project_source_project_status", table_name="project_source_binding")
    op.drop_table("project_source_binding")
    op.drop_index("ix_creative_brief_project_created", table_name="creative_brief_revision")
    op.drop_table("creative_brief_revision")
