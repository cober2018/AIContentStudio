"""FE-F2 additive project, unit, workflow and snapshot foundation.

Revision ID: e5fef2000001
Revises: d4audit00004
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e5fef2000001"
down_revision: str | Sequence[str] | None = "d4audit00004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = set(inspector.get_table_names())
    if "content_persona" not in existing:
        op.create_table(
            "content_persona",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_content_persona_owner_user_id", "content_persona", ["owner_user_id"])
    if "content_project" not in existing:
        op.create_table(
            "content_project",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
            sa.Column("title", sa.String(300), nullable=False),
            sa.Column("objective", sa.Text(), nullable=False),
            sa.Column("status", sa.String(30), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_content_project_owner_user_id", "content_project", ["owner_user_id"])
    if "content_unit" not in existing:
        op.create_table(
            "content_unit",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), sa.ForeignKey("content_project.id"), nullable=False),
            sa.Column("persona_id", sa.Integer(), sa.ForeignKey("content_persona.id"), nullable=False),
            sa.Column("modality", sa.String(20), nullable=False),
            sa.Column("channel_id", sa.String(100)),
            sa.Column("title", sa.String(300), nullable=False),
            sa.Column("status", sa.String(30), nullable=False),
            sa.Column("pinned_workflow_id", sa.Integer(), sa.ForeignKey("workflow.id")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_content_unit_project_id", "content_unit", ["project_id"])
    if "persona_workflow_default" not in existing:
        op.create_table(
            "persona_workflow_default",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("persona_id", sa.Integer(), sa.ForeignKey("content_persona.id"), nullable=False),
            sa.Column("modality", sa.String(20), nullable=False),
            sa.Column("workflow_id", sa.Integer(), sa.ForeignKey("workflow.id"), nullable=False),
            sa.Column("revision", sa.Integer(), nullable=False),
            sa.UniqueConstraint("persona_id", "modality", name="uq_persona_workflow_default"),
        )
    if "project_workflow_binding" not in existing:
        op.create_table(
            "project_workflow_binding",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("unit_id", sa.Integer(), sa.ForeignKey("content_unit.id"), nullable=False),
            sa.Column("workflow_id", sa.Integer(), sa.ForeignKey("workflow.id"), nullable=False),
            sa.Column("revision", sa.Integer(), nullable=False),
            sa.UniqueConstraint("unit_id", name="uq_project_workflow_binding_unit"),
        )
    if "data_snapshot" not in existing:
        op.create_table(
            "data_snapshot",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("unit_id", sa.Integer(), sa.ForeignKey("content_unit.id"), nullable=False),
            sa.Column("run_id", sa.Integer(), sa.ForeignKey("workflow_run.id")),
            sa.Column("node_id", sa.String(50), nullable=False),
            sa.Column("plugin_key", sa.String(150), nullable=False),
            sa.Column("source_ref", sa.String(255), nullable=False),
            sa.Column("source_version", sa.String(100)),
            sa.Column("checksum", sa.String(64), nullable=False),
            sa.Column("normalized_output", sa.JSON(), nullable=False),
            sa.Column("lineage_json", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_data_snapshot_unit_id", "data_snapshot", ["unit_id"])
    if "project_workflow_output" not in existing:
        op.create_table(
            "project_workflow_output",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), sa.ForeignKey("content_project.id"), nullable=False),
            sa.Column("unit_id", sa.Integer(), sa.ForeignKey("content_unit.id"), nullable=False),
            sa.Column("run_id", sa.Integer(), sa.ForeignKey("workflow_run.id"), nullable=False),
            sa.Column("node_id", sa.String(50), nullable=False),
            sa.Column("attempt_id", sa.Integer(), sa.ForeignKey("workflow_step_attempt.id")),
            sa.Column("output_kind", sa.String(30), nullable=False),
            sa.Column("entity_id", sa.Integer(), nullable=False),
            sa.Column("provenance_json", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_project_workflow_output_project_id", "project_workflow_output", ["project_id"])
    if "workflow_run" in existing and "content_unit_id" not in {column["name"] for column in inspector.get_columns("workflow_run")}:
        with op.batch_alter_table("workflow_run") as batch_op:
            batch_op.add_column(sa.Column("content_unit_id", sa.Integer(), sa.ForeignKey("content_unit.id", name="fk_workflow_run_content_unit_id")))
            batch_op.create_index("ix_workflow_run_content_unit_id", ["content_unit_id"])
    if "workflow" in existing and "owner_user_id" not in {column["name"] for column in inspector.get_columns("workflow")}:
        with op.batch_alter_table("workflow") as batch_op:
            batch_op.add_column(sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("user.id", name="fk_workflow_owner_user_id")))
            batch_op.add_column(sa.Column("scope", sa.String(30)))
            batch_op.create_index("ix_workflow_owner_user_id", ["owner_user_id"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "workflow" in inspector.get_table_names() and "owner_user_id" in {column["name"] for column in inspector.get_columns("workflow")}:
        with op.batch_alter_table("workflow") as batch_op:
            batch_op.drop_index("ix_workflow_owner_user_id")
            batch_op.drop_column("scope")
            batch_op.drop_column("owner_user_id")
    if "workflow_run" in inspector.get_table_names() and "content_unit_id" in {column["name"] for column in inspector.get_columns("workflow_run")}:
        with op.batch_alter_table("workflow_run") as batch_op:
            batch_op.drop_index("ix_workflow_run_content_unit_id")
            batch_op.drop_column("content_unit_id")
    for table, index in (
        ("project_workflow_output", "ix_project_workflow_output_project_id"),
        ("data_snapshot", "ix_data_snapshot_unit_id"),
        ("project_workflow_binding", None),
        ("persona_workflow_default", None),
        ("content_unit", "ix_content_unit_project_id"),
        ("content_project", "ix_content_project_owner_user_id"),
        ("content_persona", "ix_content_persona_owner_user_id"),
    ):
        if table in sa.inspect(bind).get_table_names():
            if index:
                op.drop_index(index, table_name=table)
            op.drop_table(table)
