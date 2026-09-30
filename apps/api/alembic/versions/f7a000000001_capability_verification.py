"""FE-F7 safe capability registration and scoped verification history."""

import sqlalchemy as sa

from alembic import op

revision = "f7a000000001"
down_revision = "f6e000000001"
branch_labels = None
depends_on = None


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def upgrade() -> None:
    if "capability_registration" not in _tables():
        op.create_table(
            "capability_registration",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("kind", sa.String(50), nullable=False),
            sa.Column("key", sa.String(150), nullable=False),
            sa.Column("version", sa.String(50), nullable=False),
            sa.Column("status", sa.String(20), nullable=False),
            sa.Column("config_fingerprint", sa.String(64), nullable=False),
            sa.Column("data_source_plugin_key", sa.String(100)),
            sa.Column("endpoint_id", sa.Integer(), sa.ForeignKey("connector_endpoint.id", ondelete="RESTRICT")),
            sa.Column("created_by", sa.String(255)),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("kind", "key", "version", name="uq_capability_registration_identity"),
            sa.CheckConstraint("kind IN ('node','rule','renderer','publisher','asset_provider','material_search','skill_runtime',"
                               "'model_provider','tool_provider','data_connector','search_provider','image_provider',"
                               "'video_provider','tts_provider','asr_provider','channel_adapter','browser_automation')",
                               name="ck_capability_registration_kind"),
            sa.CheckConstraint("length(kind) > 0 AND length(key) > 0 AND length(version) > 0", name="ck_capability_registration_identity_nonempty"),
            sa.CheckConstraint("status IN ('configured', 'disabled')", name="ck_capability_registration_status"),
            sa.CheckConstraint("length(config_fingerprint) = 64", name="ck_capability_registration_fingerprint"),
            sa.CheckConstraint(
                "(kind = 'data_connector' AND data_source_plugin_key IS NOT NULL AND endpoint_id IS NOT NULL) "
                "OR (kind != 'data_connector' AND data_source_plugin_key IS NULL AND endpoint_id IS NULL)",
                name="ck_capability_registration_data_mapping",
            ),
        )
    if "capability_verification" not in _tables():
        op.create_table(
            "capability_verification",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("registration_id", sa.Integer(), sa.ForeignKey("capability_registration.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("config_fingerprint", sa.String(64), nullable=False),
            sa.Column("scope_kind", sa.String(50), nullable=False),
            sa.Column("scope_json", sa.JSON(), nullable=False),
            sa.Column("result", sa.String(20), nullable=False),
            sa.Column("verified_by", sa.String(255)),
            sa.Column("verified_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True)),
            sa.Column("evidence_json", sa.JSON(), nullable=False),
            sa.CheckConstraint("result IN ('verified', 'failed', 'revoked')", name="ck_capability_verification_result"),
            sa.CheckConstraint("scope_kind IN ('publisher_action', 'data_source_endpoint')", name="ck_capability_verification_scope_kind"),
            sa.CheckConstraint("length(config_fingerprint) = 64", name="ck_capability_verification_fingerprint"),
        )
    indexes = {item["name"] for item in sa.inspect(op.get_bind()).get_indexes("capability_verification")}
    if "ix_capability_verification_registration_id" not in indexes:
        op.create_index("ix_capability_verification_registration_id", "capability_verification", ["registration_id"])
    if "ix_capability_verification_registration_scope_id" not in indexes:
        op.create_index("ix_capability_verification_registration_scope_id", "capability_verification",
                        ["registration_id", "scope_kind", "id"])


def downgrade() -> None:
    if "capability_verification" in _tables():
        retained = op.get_bind().execute(sa.text("SELECT 1 FROM capability_verification LIMIT 1")).first()
        if retained:
            raise RuntimeError("refusing downgrade: retained CapabilityVerification history")
        op.drop_table("capability_verification")
    if "capability_registration" in _tables():
        op.drop_table("capability_registration")
