"""Add reference-only system knowledge collections."""

import sqlalchemy as sa

from alembic import op

revision = "f5c000000001"
down_revision = "f5b000000001"
branch_labels = None
depends_on = None


def upgrade():
    existing = set(sa.inspect(op.get_bind()).get_table_names())
    # Initial migration uses live metadata on fresh databases.
    if "knowledge_collection" not in existing:
        op.create_table(
            "knowledge_collection",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(300), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="active"),
            sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_by", sa.String(255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.CheckConstraint("status IN ('active','archived')", name="ck_knowledge_collection_status"),
            sa.CheckConstraint("revision > 0", name="ck_knowledge_collection_revision"),
        )
    if "knowledge_collection_item" not in existing:
        op.create_table(
            "knowledge_collection_item",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("collection_id", sa.Integer(), sa.ForeignKey("knowledge_collection.id"), nullable=False),
            sa.Column("item_type", sa.String(30), nullable=False),
            sa.Column("source_document_id", sa.Integer(), sa.ForeignKey("source_document.id"), nullable=True),
            sa.Column("fact_pack_id", sa.Integer(), sa.ForeignKey("fact_pack.id"), nullable=True),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("note", sa.Text(), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="active"),
            sa.Column("added_by", sa.String(255), nullable=True),
            sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("detached_at", sa.DateTime(timezone=True), nullable=True),
            sa.CheckConstraint(
                "(item_type = 'source_document' AND source_document_id IS NOT NULL AND fact_pack_id IS NULL) OR (item_type = 'fact_pack' AND fact_pack_id IS NOT NULL AND source_document_id IS NULL)",
                name="ck_knowledge_item_resource",
            ),
            sa.CheckConstraint("status IN ('active','detached')", name="ck_knowledge_item_status"),
            sa.CheckConstraint("sort_order >= 0", name="ck_knowledge_item_sort_order"),
            sa.UniqueConstraint("collection_id", "source_document_id", name="uq_knowledge_item_source"),
            sa.UniqueConstraint("collection_id", "fact_pack_id", name="uq_knowledge_item_pack"),
        )
    indexes = {row["name"] for row in sa.inspect(op.get_bind()).get_indexes("knowledge_collection_item")}
    if "ix_knowledge_item_collection_status_order" not in indexes:
        op.create_index(
            "ix_knowledge_item_collection_status_order",
            "knowledge_collection_item",
            ["collection_id", "status", "sort_order", "id"],
        )


def downgrade():
    op.drop_index("ix_knowledge_item_collection_status_order", table_name="knowledge_collection_item")
    op.drop_table("knowledge_collection_item")
    op.drop_table("knowledge_collection")
