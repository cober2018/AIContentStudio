"""FE-F6A additive production Master revisions and immutable references."""

import sqlalchemy as sa

from alembic import op

revision = "f6a000000001"
down_revision = "f5c000000001"
branch_labels = None
depends_on = None


def _columns(table: str) -> dict[str, dict]:
    return {column["name"]: column for column in sa.inspect(op.get_bind()).get_columns(table)}


def _add_column(table: str, column: sa.Column) -> None:
    if column.name in _columns(table):
        return
    if op.get_bind().dialect.name == "sqlite" and column.foreign_keys:
        with op.batch_alter_table(table) as batch:
            batch.add_column(column)
    else:
        op.add_column(table, column)


def _index(table: str, name: str, columns: list[str]) -> None:
    if name not in {item["name"] for item in sa.inspect(op.get_bind()).get_indexes(table)}:
        op.create_index(name, table, columns)


def _drop_index(table: str, name: str) -> None:
    if name in {item["name"] for item in sa.inspect(op.get_bind()).get_indexes(table)}:
        op.drop_index(name, table_name=table)


def upgrade() -> None:
    bind = op.get_bind()
    existing = set(sa.inspect(bind).get_table_names())
    if "content_master_revision" not in existing:
        op.create_table(
            "content_master_revision",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), sa.ForeignKey("content_project.id"), nullable=False),
            sa.Column("content_unit_id", sa.Integer(), sa.ForeignKey("content_unit.id"), nullable=False),
            sa.Column("revision_no", sa.Integer(), nullable=False),
            sa.Column("parent_revision_id", sa.Integer(), sa.ForeignKey("content_master_revision.id")),
            sa.Column("modality", sa.String(20), nullable=False),
            sa.Column("channel_id", sa.String(100)),
            sa.Column("content_form", sa.String(100)),
            sa.Column("payload_schema", sa.String(100), nullable=False),
            sa.Column("payload_json", sa.JSON(), nullable=False),
            sa.Column("payload_hash", sa.String(64), nullable=False),
            sa.Column("context_hash", sa.String(64), nullable=False),
            sa.Column("identity_snapshot_id", sa.Integer(), sa.ForeignKey("identity_snapshot.id")),
            sa.Column("creative_brief_revision_id", sa.Integer(), sa.ForeignKey("creative_brief_revision.id")),
            sa.Column("fact_boundary_revision_id", sa.Integer(), sa.ForeignKey("project_fact_boundary_revision.id")),
            sa.Column("origin_workflow_run_id", sa.Integer(), sa.ForeignKey("workflow_run.id")),
            sa.Column("origin_project_output_id", sa.Integer(), sa.ForeignKey("project_workflow_output.id")),
            sa.Column("source_kind", sa.String(30), nullable=False),
            sa.Column("edit_summary_json", sa.JSON(), nullable=False),
            sa.Column("idempotency_key", sa.String(150), nullable=False),
            sa.Column("request_fingerprint", sa.String(64), nullable=False),
            sa.Column("created_by", sa.String(255)),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("content_unit_id", "revision_no", name="uq_master_unit_revision"),
            sa.UniqueConstraint("content_unit_id", "idempotency_key", name="uq_master_unit_idempotency"),
        )
    if "content_master_asset_ref" not in existing:
        op.create_table(
            "content_master_asset_ref",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("master_revision_id", sa.Integer(), sa.ForeignKey("content_master_revision.id"), nullable=False),
            sa.Column("material_revision_id", sa.Integer(), sa.ForeignKey("material_revision.id"), nullable=False),
            sa.Column("role", sa.String(40), nullable=False),
            sa.Column("slot_key", sa.String(100)),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("placement_json", sa.JSON(), nullable=False),
            sa.Column("rights_snapshot_json", sa.JSON(), nullable=False),
            sa.Column("content_hash_snapshot", sa.String(64), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    if "content_master_evidence_ref" not in existing:
        op.create_table(
            "content_master_evidence_ref",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("master_revision_id", sa.Integer(), sa.ForeignKey("content_master_revision.id"), nullable=False),
            sa.Column("fact_pack_item_id", sa.Integer(), sa.ForeignKey("fact_pack_item.id"), nullable=False),
            sa.Column("role", sa.String(40), nullable=False),
            sa.Column("content_locator_json", sa.JSON(), nullable=False),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("snapshot_checksum", sa.String(64), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    if "content_master_check_run" not in existing:
        op.create_table(
            "content_master_check_run",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("master_revision_id", sa.Integer(), sa.ForeignKey("content_master_revision.id"), nullable=False),
            sa.Column("check_kind", sa.String(40), nullable=False),
            sa.Column("profile_key", sa.String(100)),
            sa.Column("profile_version", sa.String(50)),
            sa.Column("input_hash", sa.String(64), nullable=False),
            sa.Column("status", sa.String(20), nullable=False),
            sa.Column("report_json", sa.JSON(), nullable=False),
            sa.Column("provider_key", sa.String(100)),
            sa.Column("provider_version", sa.String(100)),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )

    _add_column("content_asset", sa.Column("content_master_revision_id", sa.Integer(), sa.ForeignKey("content_master_revision.id", name="fk_content_asset_master_revision_id")))
    if not _columns("content_asset")["final_body"]["nullable"]:
        with op.batch_alter_table("content_asset") as batch:
            batch.alter_column("final_body", existing_type=sa.Text(), nullable=True)
    _index("content_asset", "ix_content_asset_content_master_revision_id", ["content_master_revision_id"])
    _index("content_master_revision", "ix_master_project_unit_created", ["project_id", "content_unit_id", "created_at"])
    _index("content_master_asset_ref", "ix_master_asset_ref_master_order", ["master_revision_id", "sort_order"])
    _index("content_master_evidence_ref", "ix_master_evidence_ref_master_order", ["master_revision_id", "sort_order"])
    _index("content_master_check_run", "ix_master_check_master_kind_created", ["master_revision_id", "check_kind", "created_at"])


def downgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    history_tables = ("content_master_check_run", "content_master_evidence_ref", "content_master_asset_ref", "content_master_revision")
    for table in history_tables:
        if table in tables and bind.scalar(sa.select(sa.func.count()).select_from(sa.table(table))):
            raise RuntimeError("FE-F6A downgrade refused: retained Master history; no schema changes made")
    asset_columns = _columns("content_asset")
    assets = sa.table("content_asset", sa.column("final_body"), sa.column("content_master_revision_id"))
    incompatible = assets.c.final_body.is_(None)
    if "content_master_revision_id" in asset_columns:
        incompatible = sa.or_(incompatible, assets.c.content_master_revision_id.is_not(None))
    if bind.scalar(sa.select(sa.func.count()).select_from(assets).where(incompatible)):
        raise RuntimeError("FE-F6A downgrade refused: incompatible Candidate history; no schema changes made")
    if "content_master_revision_id" in _columns("content_asset"):
        _drop_index("content_asset", "ix_content_asset_content_master_revision_id")
        with op.batch_alter_table("content_asset") as batch:
            batch.drop_column("content_master_revision_id")
    if _columns("content_asset")["final_body"]["nullable"]:
        with op.batch_alter_table("content_asset") as batch:
            batch.alter_column("final_body", existing_type=sa.Text(), nullable=False)
    for table in history_tables:
        if table in set(sa.inspect(op.get_bind()).get_table_names()):
            op.drop_table(table)
