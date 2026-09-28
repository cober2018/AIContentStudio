"""Add FE-F5B performance and validated learning resources."""

import sqlalchemy as sa

from alembic import op

revision = "f5b000000001"
down_revision = "f5a000000001"
branch_labels = None
depends_on = None


def upgrade():
    # Fresh initial migrations may already create current metadata tables.
    existing = set(sa.inspect(op.get_bind()).get_table_names())
    if "published_content_record" not in existing:
        op.create_table(
            "published_content_record",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
            sa.Column("origin", sa.String(30), nullable=False),
            sa.Column("external_key", sa.String(300), nullable=True),
            sa.Column("content_asset_id", sa.Integer(), sa.ForeignKey("content_asset.id"), nullable=True),
            sa.Column("delivery_target_id", sa.Integer(), sa.ForeignKey("delivery_target.id"), nullable=True),
            sa.Column("delivery_receipt_id", sa.Integer(), sa.ForeignKey("delivery_receipt.id"), nullable=True),
            sa.Column("content_account_id", sa.Integer(), sa.ForeignKey("content_account.id"), nullable=True),
            sa.Column("identity_snapshot_id", sa.Integer(), sa.ForeignKey("identity_snapshot.id"), nullable=True),
            sa.Column("channel", sa.String(30), nullable=False),
            sa.Column("content_form", sa.String(50), nullable=True),
            sa.Column("account_ref_snapshot", sa.String(255), nullable=True),
            sa.Column("title", sa.String(500), nullable=True),
            sa.Column("canonical_url", sa.String(2000), nullable=True),
            sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("content_hash", sa.String(64), nullable=True),
            sa.Column("content_snapshot_json", sa.JSON(), nullable=False),
            sa.Column("coverage_json", sa.JSON(), nullable=False),
            sa.Column("confidence", sa.Float(), nullable=True),
            sa.Column("status", sa.String(20), nullable=False),
            sa.Column("created_by", sa.String(255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("delivery_receipt_id", name="uq_published_receipt"),
            sa.UniqueConstraint("owner_user_id", "channel", "external_key", name="uq_published_external"),
            sa.CheckConstraint("origin IN ('studio','external_import')", name="ck_published_origin"),
            sa.CheckConstraint("status IN ('active','archived')", name="ck_published_status"),
        )
    if "ix_published_content_record_owner_user_id" not in {
        i["name"] for i in sa.inspect(op.get_bind()).get_indexes("published_content_record")
    }:
        op.create_index("ix_published_content_record_owner_user_id", "published_content_record", ["owner_user_id"])
    if "ix_published_content_record_channel" not in {
        i["name"] for i in sa.inspect(op.get_bind()).get_indexes("published_content_record")
    }:
        op.create_index("ix_published_content_record_channel", "published_content_record", ["channel"])
    if "ix_published_content_record_published_at" not in {
        i["name"] for i in sa.inspect(op.get_bind()).get_indexes("published_content_record")
    }:
        op.create_index("ix_published_content_record_published_at", "published_content_record", ["published_at"])
    if "performance_observation" not in existing:
        op.create_table(
            "performance_observation",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "published_content_id", sa.Integer(), sa.ForeignKey("published_content_record.id"), nullable=False
            ),
            sa.Column("observation_kind", sa.String(30), nullable=False),
            sa.Column("metric_namespace", sa.String(100), nullable=True),
            sa.Column("metric_key", sa.String(100), nullable=True),
            sa.Column("numeric_value", sa.Float(), nullable=True),
            sa.Column("text_value", sa.Text(), nullable=True),
            sa.Column("unit", sa.String(50), nullable=True),
            sa.Column("period_start", sa.DateTime(timezone=True), nullable=True),
            sa.Column("period_end", sa.DateTime(timezone=True), nullable=True),
            sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("source_type", sa.String(30), nullable=False),
            sa.Column("source_ref", sa.String(300), nullable=True),
            sa.Column("source_checksum", sa.String(64), nullable=True),
            sa.Column("confidence", sa.Float(), nullable=True),
            sa.Column("payload_json", sa.JSON(), nullable=False),
            sa.Column("supersedes_id", sa.Integer(), sa.ForeignKey("performance_observation.id"), nullable=True),
            sa.Column("created_by", sa.String(255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("supersedes_id", name="uq_observation_correction_tip"),
            sa.CheckConstraint(
                "observation_kind IN ('metric','feedback','editorial','correction')", name="ck_observation_kind"
            ),
        )
    if "ix_performance_observation_published_content_id" not in {
        i["name"] for i in sa.inspect(op.get_bind()).get_indexes("performance_observation")
    }:
        op.create_index(
            "ix_performance_observation_published_content_id", "performance_observation", ["published_content_id"]
        )
    if "content_insight" not in existing:
        op.create_table(
            "content_insight",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
            sa.Column("insight_type", sa.String(30), nullable=False),
            sa.Column("statement", sa.Text(), nullable=False),
            sa.Column("scope_json", sa.JSON(), nullable=False),
            sa.Column("cohort_json", sa.JSON(), nullable=False),
            sa.Column("coverage_json", sa.JSON(), nullable=False),
            sa.Column("supporting_refs_json", sa.JSON(), nullable=False),
            sa.Column("contradicting_refs_json", sa.JSON(), nullable=False),
            sa.Column("limitations_json", sa.JSON(), nullable=False),
            sa.Column("confidence", sa.Float(), nullable=True),
            sa.Column("analysis_source", sa.String(30), nullable=False),
            sa.Column("provider_key", sa.String(150), nullable=True),
            sa.Column("provider_version", sa.String(50), nullable=True),
            sa.Column("checksum", sa.String(64), nullable=False),
            sa.Column("supersedes_id", sa.Integer(), sa.ForeignKey("content_insight.id"), nullable=True),
            sa.Column("created_by", sa.String(255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    if "ix_content_insight_owner_user_id" not in {
        i["name"] for i in sa.inspect(op.get_bind()).get_indexes("content_insight")
    }:
        op.create_index("ix_content_insight_owner_user_id", "content_insight", ["owner_user_id"])
    if "learning_candidate" not in existing:
        op.create_table(
            "learning_candidate",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
            sa.Column("category", sa.String(30), nullable=False),
            sa.Column("title", sa.String(500), nullable=False),
            sa.Column("proposition", sa.Text(), nullable=False),
            sa.Column("rationale", sa.Text(), nullable=False),
            sa.Column("scope_json", sa.JSON(), nullable=False),
            sa.Column("status", sa.String(30), nullable=False),
            sa.Column("revision_no", sa.Integer(), nullable=False),
            sa.Column("confidence", sa.Float(), nullable=True),
            sa.Column("validation_method", sa.String(30), nullable=True),
            sa.Column("validation_summary_json", sa.JSON(), nullable=False),
            sa.Column("created_from_insight_id", sa.Integer(), sa.ForeignKey("content_insight.id"), nullable=True),
            sa.Column("created_by", sa.String(255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("decided_by", sa.String(255), nullable=True),
            sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
            sa.CheckConstraint(
                "status IN ('collecting','ready_for_review','accepted','rejected','archived')",
                name="ck_learning_candidate_status",
            ),
            sa.CheckConstraint(
                "category IN ('identity','audience','channel','format','topic','workflow')",
                name="ck_learning_candidate_category",
            ),
        )
    if "ix_learning_candidate_owner_user_id" not in {
        i["name"] for i in sa.inspect(op.get_bind()).get_indexes("learning_candidate")
    }:
        op.create_index("ix_learning_candidate_owner_user_id", "learning_candidate", ["owner_user_id"])
    if "ix_learning_candidate_status" not in {
        i["name"] for i in sa.inspect(op.get_bind()).get_indexes("learning_candidate")
    }:
        op.create_index("ix_learning_candidate_status", "learning_candidate", ["status"])
    if "learning_candidate_evidence" not in existing:
        op.create_table(
            "learning_candidate_evidence",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("learning_candidate_id", sa.Integer(), sa.ForeignKey("learning_candidate.id"), nullable=False),
            sa.Column("evidence_type", sa.String(40), nullable=False),
            sa.Column("entity_id", sa.Integer(), nullable=False),
            sa.Column("role", sa.String(20), nullable=False),
            sa.Column("snapshot_checksum", sa.String(64), nullable=True),
            sa.Column("snapshot_json", sa.JSON(), nullable=False),
            sa.Column("note", sa.Text(), nullable=True),
            sa.Column("created_by", sa.String(255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint(
                "learning_candidate_id", "evidence_type", "entity_id", "role", name="uq_learning_evidence"
            ),
            sa.CheckConstraint("role IN ('support','contradict','context')", name="ck_learning_evidence_role"),
        )
    if "ix_learning_candidate_evidence_learning_candidate_id" not in {
        i["name"] for i in sa.inspect(op.get_bind()).get_indexes("learning_candidate_evidence")
    }:
        op.create_index(
            "ix_learning_candidate_evidence_learning_candidate_id",
            "learning_candidate_evidence",
            ["learning_candidate_id"],
        )
    if "content_memory_entry" not in existing:
        op.create_table(
            "content_memory_entry",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
            sa.Column("scope_type", sa.String(30), nullable=False),
            sa.Column("brand_id", sa.Integer(), sa.ForeignKey("content_brand.id"), nullable=True),
            sa.Column("persona_id", sa.Integer(), sa.ForeignKey("content_persona.id"), nullable=True),
            sa.Column("account_id", sa.Integer(), sa.ForeignKey("content_account.id"), nullable=True),
            sa.Column("series_id", sa.Integer(), sa.ForeignKey("content_series.id"), nullable=True),
            sa.Column("memory_type", sa.String(40), nullable=False),
            sa.Column("status", sa.String(20), nullable=False),
            sa.Column(
                "source_learning_candidate_id", sa.Integer(), sa.ForeignKey("learning_candidate.id"), nullable=False
            ),
            sa.Column("promotion_idempotency_key", sa.String(100), nullable=False),
            sa.Column("promotion_checksum", sa.String(64), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("source_learning_candidate_id", name="uq_memory_promoted_candidate"),
            sa.UniqueConstraint("owner_user_id", "promotion_idempotency_key", name="uq_memory_promotion_key"),
            sa.CheckConstraint("scope_type IN ('owner','brand','persona','account','series')", name="ck_memory_scope"),
            sa.CheckConstraint("status IN ('active','archived')", name="ck_memory_status"),
        )
    if "ix_content_memory_entry_owner_user_id" not in {
        i["name"] for i in sa.inspect(op.get_bind()).get_indexes("content_memory_entry")
    }:
        op.create_index("ix_content_memory_entry_owner_user_id", "content_memory_entry", ["owner_user_id"])
    if "content_memory_revision" not in existing:
        op.create_table(
            "content_memory_revision",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("memory_entry_id", sa.Integer(), sa.ForeignKey("content_memory_entry.id"), nullable=False),
            sa.Column("revision_no", sa.Integer(), nullable=False),
            sa.Column("parent_revision_id", sa.Integer(), sa.ForeignKey("content_memory_revision.id"), nullable=True),
            sa.Column("statement", sa.Text(), nullable=False),
            sa.Column("applicability_json", sa.JSON(), nullable=False),
            sa.Column("limitations_json", sa.JSON(), nullable=False),
            sa.Column(
                "source_learning_candidate_id", sa.Integer(), sa.ForeignKey("learning_candidate.id"), nullable=False
            ),
            sa.Column("evidence_snapshot_json", sa.JSON(), nullable=False),
            sa.Column("checksum", sa.String(64), nullable=False),
            sa.Column("created_by", sa.String(255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("memory_entry_id", "revision_no", name="uq_memory_revision"),
        )
    if "ix_content_memory_revision_memory_entry_id" not in {
        i["name"] for i in sa.inspect(op.get_bind()).get_indexes("content_memory_revision")
    }:
        op.create_index("ix_content_memory_revision_memory_entry_id", "content_memory_revision", ["memory_entry_id"])


def downgrade():
    op.drop_table("content_memory_revision")
    op.drop_table("content_memory_entry")
    op.drop_table("learning_candidate_evidence")
    op.drop_table("learning_candidate")
    op.drop_table("content_insight")
    op.drop_table("performance_observation")
    op.drop_table("published_content_record")
