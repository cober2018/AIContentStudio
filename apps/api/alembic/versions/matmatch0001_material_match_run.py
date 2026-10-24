"""Saved script and storyboard material match runs."""
import sqlalchemy as sa
from alembic import op

revision = "matmatch0001"
down_revision = "matlib0001"
branch_labels = None
depends_on = None


def upgrade():
    # Local bootstrap may already have created the table from the current model.
    if "material_match_run" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table(
        "material_match_run",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("content_project.id")),
        sa.Column("unit_id", sa.Integer(), sa.ForeignKey("content_unit.id")),
        sa.Column("scope", sa.String(20), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("source_json", sa.JSON(), nullable=False),
        sa.Column("settings_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("cancel_requested", sa.Boolean(), nullable=False),
        sa.Column("progress_json", sa.JSON()),
        sa.Column("result_json", sa.JSON()),
        sa.Column("error_code", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("scope IN ('script','shots')", name="ck_material_match_run_scope"),
        sa.CheckConstraint("status IN ('queued','running','completed','failed','cancelled','interrupted')", name="ck_material_match_run_status"),
    )
    for column in ("owner_user_id", "project_id", "unit_id"):
        op.create_index(f"ix_material_match_run_{column}", "material_match_run", [column])


def downgrade():
    raise RuntimeError("destructive_downgrade_blocked: match runs hold reviewed material decisions")
