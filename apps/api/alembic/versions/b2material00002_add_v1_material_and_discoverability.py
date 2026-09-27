"""V1 PRD 2.0 Content Harness — Migration B（additive）。

覆盖（开发 OpenSpec §5 Migration B）：
- 新表：material / material_revision / discoverability_profile_version / discoverability_report
- draft_media：+ material_revision_id / placement_json / alt_text / caption

不变量：不批量把旧 DraftMedia 复制成 Material（首次编辑/复用时显式 adoption），
migration 不伪造原素材 provenance。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b2material00002"
down_revision: Union[str, Sequence[str], None] = "a1harness00001"
branch_labels = None
depends_on = None


def _has_table(engine, table: str) -> bool:
    return table in set(sa.inspect(engine).get_table_names())


def _columns(table: str) -> dict[str, dict]:
    return {item["name"]: item for item in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()

    if not _has_table(bind, "material"):
        op.create_table(
            "material",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("kind", sa.String(length=20), nullable=False, server_default="image"),
            sa.Column("title", sa.String(length=500), nullable=False),
            sa.Column("tags_json", sa.JSON(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
            sa.Column("created_by", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        )

    if not _has_table(bind, "material_revision"):
        op.create_table(
            "material_revision",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("material_id", sa.Integer(), sa.ForeignKey("material.id"), nullable=False),
            sa.Column("revision_no", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("parent_revision_id", sa.Integer(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="candidate"),
            sa.Column("source_kind", sa.String(length=30), nullable=False, server_default="upload"),
            sa.Column("source_url", sa.String(length=1000), nullable=True),
            sa.Column("source_metadata_json", sa.JSON(), nullable=True),
            sa.Column("content_hash", sa.String(length=64), nullable=False),
            sa.Column("file_path", sa.String(length=500), nullable=True),
            sa.Column("mime_type", sa.String(length=100), nullable=True),
            sa.Column("width", sa.Integer(), nullable=True),
            sa.Column("height", sa.Integer(), nullable=True),
            sa.Column("duration_ms", sa.Integer(), nullable=True),
            sa.Column("rights_status", sa.String(length=30), nullable=True),
            sa.Column("public_use_allowed", sa.Boolean(), nullable=True),
            sa.Column("model_use_allowed", sa.Boolean(), nullable=True),
            sa.Column("commercial_use_allowed", sa.Boolean(), nullable=True),
            sa.Column("attribution_text", sa.Text(), nullable=True),
            sa.Column("provider_key", sa.String(length=100), nullable=True),
            sa.Column("provider_version", sa.String(length=50), nullable=True),
            sa.Column("prompt_text", sa.Text(), nullable=True),
            sa.Column("metadata_json", sa.JSON(), nullable=True),
            sa.Column("created_by", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("material_id", "revision_no", name="uq_material_revision_no"),
        )
        op.create_index("ix_material_revision_content_hash", "material_revision", ["content_hash"])

    if not _has_table(bind, "discoverability_profile_version"):
        op.create_table(
            "discoverability_profile_version",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("profile_key", sa.String(length=150), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("channel", sa.String(length=30), nullable=False),
            sa.Column("content_form", sa.String(length=50), nullable=True),
            sa.Column("config_json", sa.JSON(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
            sa.Column("checksum", sa.String(length=64), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("profile_key", "version", name="uq_discoverability_profile_version"),
        )

    if not _has_table(bind, "discoverability_report"):
        op.create_table(
            "discoverability_report",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("topic_id", sa.Integer(), nullable=True),
            sa.Column("mother_revision_id", sa.Integer(), nullable=True),
            sa.Column("draft_id", sa.Integer(), nullable=True),
            sa.Column("stage", sa.String(length=10), nullable=False),
            sa.Column("channel", sa.String(length=30), nullable=False),
            sa.Column("content_form", sa.String(length=50), nullable=True),
            sa.Column("profile_version_id", sa.Integer(), nullable=True),
            sa.Column("input_hash", sa.String(length=64), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="incomplete"),
            sa.Column("report_json", sa.JSON(), nullable=True),
            sa.Column("model_provider", sa.String(length=50), nullable=True),
            sa.Column("model_name", sa.String(length=100), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_discoverability_report_stage", "discoverability_report", ["stage", "channel", "created_at"])

    dm_cols = _columns("draft_media")
    with op.batch_alter_table("draft_media") as batch:
        if "material_revision_id" not in dm_cols:
            batch.add_column(sa.Column("material_revision_id", sa.Integer(), nullable=True))
        if "placement_json" not in dm_cols:
            batch.add_column(sa.Column("placement_json", sa.JSON(), nullable=True))
        if "alt_text" not in dm_cols:
            batch.add_column(sa.Column("alt_text", sa.Text(), nullable=True))
        if "caption" not in dm_cols:
            batch.add_column(sa.Column("caption", sa.Text(), nullable=True))
    if "material_revision_id" not in {fk["name"] for fk in sa.inspect(bind).get_foreign_keys("draft_media")}:
        with op.batch_alter_table("draft_media") as batch:
            batch.create_foreign_key("fk_draft_media_material_revision", "material_revision", ["material_revision_id"], ["id"])


def downgrade() -> None:
    # Additive：素材与 SEO 报告历史不回滚删除
    pass
