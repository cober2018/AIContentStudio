"""Add owner-scoped recoverable form assistance without rewriting existing content."""
import sqlalchemy as sa

from alembic import op

revision = "formassist000001"
down_revision = "catchup000001"
branch_labels = None
depends_on = None


def upgrade():
    if "form_assistance_session" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table("form_assistance_session",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("content_project.id", ondelete="RESTRICT")),
        sa.Column("unit_id", sa.Integer(), sa.ForeignKey("content_unit.id", ondelete="RESTRICT")),
        sa.Column("request_key", sa.String(100), nullable=False),
        sa.Column("surface", sa.String(30), nullable=False),
        sa.Column("mode", sa.String(20), nullable=False),
        sa.Column("context_hash", sa.String(64), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("context_json", sa.JSON(), nullable=False),
        sa.Column("state_json", sa.JSON(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("llm_run_id", sa.Integer(), sa.ForeignKey("llm_run.id", ondelete="RESTRICT")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("owner_user_id", "request_key", name="uq_form_assistance_owner_request"))
    op.create_index("ix_form_assistance_session_owner_user_id", "form_assistance_session", ["owner_user_id"])
    op.create_index("ix_form_assistance_session_project_id", "form_assistance_session", ["project_id"])


def downgrade():
    if op.get_bind().execute(sa.text("SELECT COUNT(*) FROM form_assistance_session")).scalar():
        raise RuntimeError("destructive_downgrade_blocked: retain form assistance history")
    op.drop_table("form_assistance_session")
