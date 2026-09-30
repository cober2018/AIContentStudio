"""FE-F6E additive ChannelVariant history and v5 Candidate source link."""

import sqlalchemy as sa

from alembic import op

revision = "f6e000000001"
down_revision = "f6a000000001"
branch_labels = None
depends_on = None


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _columns(table: str) -> set[str]:
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table)}


def _index(table: str, name: str, columns: list[str]) -> None:
    if name not in {item["name"] for item in sa.inspect(op.get_bind()).get_indexes(table)}:
        op.create_index(name, table, columns)


def upgrade() -> None:
    if "channel_variant_revision" not in _tables():
        op.create_table(
            "channel_variant_revision",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), sa.ForeignKey("content_project.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("content_unit_id", sa.Integer(), sa.ForeignKey("content_unit.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("variant_key", sa.String(120), nullable=False),
            sa.Column("revision_no", sa.Integer(), nullable=False),
            sa.Column("parent_revision_id", sa.Integer(), sa.ForeignKey("channel_variant_revision.id", ondelete="RESTRICT")),
            sa.Column("source_master_revision_id", sa.Integer(), sa.ForeignKey("content_master_revision.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("source_master_payload_hash", sa.String(64), nullable=False),
            sa.Column("source_master_context_hash", sa.String(64), nullable=False),
            sa.Column("source_channel_id", sa.String(100)),
            sa.Column("source_content_form", sa.String(100)),
            sa.Column("identity_snapshot_id", sa.Integer(), sa.ForeignKey("identity_snapshot.id", ondelete="RESTRICT")),
            sa.Column("channel_id", sa.String(100), nullable=False),
            sa.Column("content_form", sa.String(100), nullable=False),
            sa.Column("artifact_kind", sa.String(20), nullable=False),
            sa.Column("profile_template_version_id", sa.Integer(), sa.ForeignKey("channel_template_version.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("profile_key", sa.String(150), nullable=False),
            sa.Column("profile_version", sa.String(50), nullable=False),
            sa.Column("profile_hash", sa.String(64), nullable=False),
            sa.Column("adapter_key", sa.String(150), nullable=False),
            sa.Column("adapter_version", sa.String(50), nullable=False),
            sa.Column("rule_hash", sa.String(64), nullable=False),
            sa.Column("payload_schema", sa.String(100), nullable=False),
            sa.Column("payload_json", sa.JSON(), nullable=False),
            sa.Column("payload_hash", sa.String(64), nullable=False),
            sa.Column("context_hash", sa.String(64), nullable=False),
            sa.Column("source_kind", sa.String(40), nullable=False),
            sa.Column("edit_summary_json", sa.JSON(), nullable=False),
            sa.Column("llm_provenance_json", sa.JSON()),
            sa.Column("idempotency_key", sa.String(150), nullable=False),
            sa.Column("request_fingerprint", sa.String(64), nullable=False),
            sa.Column("created_by", sa.String(255)),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("content_unit_id", "variant_key", "revision_no", name="uq_variant_series_revision"),
            sa.UniqueConstraint("content_unit_id", "variant_key", "idempotency_key", name="uq_variant_series_idempotency"),
            sa.CheckConstraint("revision_no > 0", name="ck_variant_revision_positive"),
            sa.CheckConstraint("length(variant_key) BETWEEN 1 AND 120", name="ck_variant_key_length"),
            sa.CheckConstraint("artifact_kind IN ('text', 'image', 'script')", name="ck_variant_artifact_kind"),
            sa.CheckConstraint("source_kind IN ('manual_edit', 'deterministic_adapt', 'model_assisted')", name="ck_variant_source_kind"),
            sa.CheckConstraint("length(payload_hash) = 64 AND length(context_hash) = 64", name="ck_variant_hash_lengths"),
        )
    if "channel_variant_asset_ref" not in _tables():
        op.create_table(
            "channel_variant_asset_ref",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("variant_revision_id", sa.Integer(), sa.ForeignKey("channel_variant_revision.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("material_revision_id", sa.Integer(), sa.ForeignKey("material_revision.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("role", sa.String(40), nullable=False),
            sa.Column("slot_key", sa.String(100)),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("placement_json", sa.JSON(), nullable=False),
            sa.Column("rights_snapshot_json", sa.JSON(), nullable=False),
            sa.Column("content_hash_snapshot", sa.String(64), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.CheckConstraint("sort_order >= 0", name="ck_variant_asset_order_nonnegative"),
        )
    if "channel_variant_evidence_ref" not in _tables():
        op.create_table(
            "channel_variant_evidence_ref",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("variant_revision_id", sa.Integer(), sa.ForeignKey("channel_variant_revision.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("fact_pack_item_id", sa.Integer(), sa.ForeignKey("fact_pack_item.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("role", sa.String(40), nullable=False),
            sa.Column("content_locator_json", sa.JSON(), nullable=False),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("snapshot_checksum", sa.String(64), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.CheckConstraint("sort_order >= 0", name="ck_variant_evidence_order_nonnegative"),
        )
    if "channel_variant_check_run" not in _tables():
        op.create_table(
            "channel_variant_check_run",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("variant_revision_id", sa.Integer(), sa.ForeignKey("channel_variant_revision.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("check_kind", sa.String(40), nullable=False),
            sa.Column("input_hash", sa.String(64), nullable=False),
            sa.Column("profile_hash", sa.String(64), nullable=False),
            sa.Column("adapter_hash", sa.String(64), nullable=False),
            sa.Column("rule_hash", sa.String(64), nullable=False),
            sa.Column("status", sa.String(20), nullable=False),
            sa.Column("report_json", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )

    if "channel_variant_revision_id" not in _columns("content_asset"):
        column = sa.Column(
            "channel_variant_revision_id",
            sa.Integer(),
            sa.ForeignKey("channel_variant_revision.id", name="fk_content_asset_variant_revision_id", ondelete="RESTRICT"),
        )
        if op.get_bind().dialect.name == "sqlite":
            with op.batch_alter_table("content_asset") as batch:
                batch.add_column(column)
        else:
            op.add_column("content_asset", column)

    for table, name, columns in (
        ("channel_variant_revision", "ix_channel_variant_revision_project_id", ["project_id"]),
        ("channel_variant_revision", "ix_channel_variant_revision_content_unit_id", ["content_unit_id"]),
        ("channel_variant_revision", "ix_channel_variant_revision_source_master_revision_id", ["source_master_revision_id"]),
        ("channel_variant_revision", "ix_channel_variant_revision_payload_hash", ["payload_hash"]),
        ("channel_variant_revision", "ix_channel_variant_revision_context_hash", ["context_hash"]),
        ("channel_variant_revision", "ix_variant_project_unit_target", ["project_id", "content_unit_id", "channel_id", "content_form"]),
        ("channel_variant_asset_ref", "ix_channel_variant_asset_ref_variant_revision_id", ["variant_revision_id"]),
        ("channel_variant_asset_ref", "ix_variant_asset_ref_order", ["variant_revision_id", "sort_order"]),
        ("channel_variant_evidence_ref", "ix_channel_variant_evidence_ref_variant_revision_id", ["variant_revision_id"]),
        ("channel_variant_evidence_ref", "ix_variant_evidence_ref_order", ["variant_revision_id", "sort_order"]),
        ("channel_variant_check_run", "ix_channel_variant_check_run_variant_revision_id", ["variant_revision_id"]),
        ("channel_variant_check_run", "ix_channel_variant_check_run_input_hash", ["input_hash"]),
        ("channel_variant_check_run", "ix_variant_check_kind_created", ["variant_revision_id", "check_kind", "created_at"]),
        ("content_asset", "ix_content_asset_channel_variant_revision_id", ["channel_variant_revision_id"]),
    ):
        _index(table, name, columns)


def downgrade() -> None:
    bind = op.get_bind()
    for table in (
        "channel_variant_check_run",
        "channel_variant_evidence_ref",
        "channel_variant_asset_ref",
        "channel_variant_revision",
    ):
        if table in _tables() and bind.scalar(sa.select(sa.func.count()).select_from(sa.table(table))):
            raise RuntimeError("FE-F6E downgrade refused: retained Variant history; no schema changes made")
    if "channel_variant_revision_id" in _columns("content_asset"):
        candidate = sa.table("content_asset", sa.column("channel_variant_revision_id"), sa.column("candidate_manifest_json", sa.JSON()))
        if bind.scalar(
            sa.select(sa.func.count()).select_from(candidate).where(
                sa.or_(
                    candidate.c.channel_variant_revision_id.is_not(None),
                    candidate.c.candidate_manifest_json["schema_version"].as_integer() == 5,
                )
            )
        ):
            raise RuntimeError("FE-F6E downgrade refused: retained v5 Candidate history; no schema changes made")
        index = "ix_content_asset_channel_variant_revision_id"
        if index in {item["name"] for item in sa.inspect(bind).get_indexes("content_asset")}:
            op.drop_index(index, table_name="content_asset")
        with op.batch_alter_table("content_asset") as batch:
            batch.drop_column("channel_variant_revision_id")
    for table in (
        "channel_variant_check_run",
        "channel_variant_evidence_ref",
        "channel_variant_asset_ref",
        "channel_variant_revision",
    ):
        if table in _tables():
            op.drop_table(table)
