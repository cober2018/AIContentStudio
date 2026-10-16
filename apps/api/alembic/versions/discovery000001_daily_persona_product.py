"""Add discovery and product inputs without rewriting historical content."""

import sqlalchemy as sa

from alembic import op

revision = "discovery000001"
down_revision = "obsidian000001"
branch_labels = None
depends_on = None


def upgrade():
    from app.models import (
        DiscoveryEvent,
        DiscoveryItem,
        DiscoverySource,
        PersonaResearchRun,
        PersonaSourceSubscription,
        ProductCreationLaunch,
    )

    bind = op.get_bind()
    for model in (DiscoverySource, PersonaSourceSubscription, DiscoveryItem,
                  DiscoveryEvent, PersonaResearchRun, ProductCreationLaunch):
        model.__table__.create(bind, checkfirst=True)
    existing = {c["name"] for c in sa.inspect(bind).get_columns("content_opportunity")}
    columns = [
        sa.Column("persona_id", sa.Integer()), sa.Column("persona_revision_id", sa.Integer()),
        sa.Column("research_run_id", sa.Integer()), sa.Column("business_date", sa.String(10)),
        sa.Column("event_key", sa.String(100)), sa.Column("angle_key", sa.String(64)),
    ]
    for column in columns:
        if column.name not in existing:
            op.add_column("content_opportunity", column)
    indexes = {i["name"] for i in sa.inspect(bind).get_indexes("content_opportunity")}
    if "uq_opportunity_discovery_angle" not in indexes:
        op.create_index("uq_opportunity_discovery_angle", "content_opportunity",
                        ["owner_user_id", "persona_id", "event_key", "angle_key"], unique=True)
    if "product_context_json" not in {c["name"] for c in sa.inspect(bind).get_columns("creative_brief_revision")}:
        op.add_column("creative_brief_revision", sa.Column("product_context_json", sa.JSON(), nullable=True))


def downgrade():
    raise RuntimeError("destructive_downgrade_blocked: pause discovery instead; retain provenance and product revisions")
