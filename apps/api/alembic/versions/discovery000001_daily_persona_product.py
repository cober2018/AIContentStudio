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
    # 与全链守卫一致：有发现/产品数据才拒绝；空库才回退本版本的表与列
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    for table in ("discovery_source", "persona_source_subscription", "discovery_item",
                  "discovery_event", "persona_research_run", "product_creation_launch"):
        if table in tables and bind.execute(sa.text(f"SELECT COUNT(*) FROM {table}")).scalar():
            raise RuntimeError("destructive_downgrade_blocked: pause discovery instead; retain provenance and product revisions")
    opp_columns = {column["name"] for column in sa.inspect(bind).get_columns("content_opportunity")}
    # 这版加上的每一列只要有值就不能丢。之前只看 persona_id / research_run_id，
    # business_date、event_key 等有值时仍会把列删掉。
    provenance = [name for name in (
        "persona_id", "persona_revision_id", "research_run_id", "business_date", "event_key", "angle_key",
    ) if name in opp_columns]
    if provenance and bind.execute(sa.text(
            "SELECT COUNT(*) FROM content_opportunity WHERE "
            + " OR ".join(f"{name} IS NOT NULL" for name in provenance))).scalar():
        raise RuntimeError("destructive_downgrade_blocked: pause discovery instead; retain provenance and product revisions")
    if "product_context_json" in {column["name"] for column in sa.inspect(bind).get_columns("creative_brief_revision")}             and bind.execute(sa.text("SELECT COUNT(*) FROM creative_brief_revision WHERE product_context_json IS NOT NULL")).scalar():
        raise RuntimeError("destructive_downgrade_blocked: pause discovery instead; retain provenance and product revisions")
    # 全空：先删所有引用待删列的索引（batch recreate 不会自动剔除），batch 删列
    # （此时新表还在，batch recreate 反射 FK 时目标表必须存在），最后 drop 新表
    dropping = {"persona_id", "persona_revision_id", "research_run_id", "business_date", "event_key", "angle_key"} & opp_columns
    for index in sa.inspect(bind).get_indexes("content_opportunity"):
        if set(index["column_names"]) & dropping:
            op.drop_index(index["name"], table_name="content_opportunity")
    with op.batch_alter_table("content_opportunity") as batch:
        for name in dropping:
            batch.drop_column(name)
    if "product_context_json" in {column["name"] for column in sa.inspect(bind).get_columns("creative_brief_revision")}:
        with op.batch_alter_table("creative_brief_revision") as batch:
            batch.drop_column("product_context_json")
    for table in ("product_creation_launch", "persona_research_run", "discovery_event",
                  "discovery_item", "persona_source_subscription", "discovery_source"):
        if table in tables:
            bind.execute(sa.text(f"DROP TABLE {table}"))
