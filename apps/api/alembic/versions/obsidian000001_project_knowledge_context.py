"""Append-only project knowledge selections; no existing row rewrite."""

import sqlalchemy as sa

from alembic import op

revision = "obsidian000001"
down_revision = "a3series00000001"
branch_labels = None
depends_on = None


def upgrade():
    if "project_knowledge_context_revision" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table(
        "project_knowledge_context_revision",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("content_project.id"), nullable=False),
        sa.Column("revision_no", sa.Integer(), nullable=False),
        sa.Column("parent_revision_id", sa.Integer(), sa.ForeignKey("project_knowledge_context_revision.id")),
        sa.Column("items_json", sa.JSON(), nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("project_id", "revision_no", name="uq_project_knowledge_revision"),
        sa.CheckConstraint("revision_no > 0", name="ck_project_knowledge_revision_positive"),
    )
    op.create_index("ix_project_knowledge_context_revision_project_id", "project_knowledge_context_revision", ["project_id"])


def downgrade():
    if "project_knowledge_context_revision" not in sa.inspect(op.get_bind()).get_table_names():
        return
    if op.get_bind().execute(sa.text("SELECT COUNT(*) FROM project_knowledge_context_revision")).scalar():
        raise RuntimeError("destructive_downgrade_blocked: knowledge context revisions exist")
    op.drop_table("project_knowledge_context_revision")
