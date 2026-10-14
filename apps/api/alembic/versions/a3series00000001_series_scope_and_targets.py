"""Persona-owned editorial series and explicit series distribution targets.

按 ADR（complete-multiplatform-content-handoff/docs/ADR_SERIES_ACCOUNT_MODEL.md）的最小增量迁移：
- content_series 增加 scope/persona_id，account_id 可空化；存量行由 server_default 回填为 account_legacy，零重写。
- 新增 series_account_target 投放绑定关系（唯一键 series+account+form）。
- downgrade fail-closed：存在 persona_editorial 栏目或投放绑定时拒绝破坏性回退。

SQLite 约束/FK 不能 ALTER，全部在 batch_alter_table 重建块内完成；
对经 create_all 建出的库（列/表已存在）幂等跳过。
"""

import sqlalchemy as sa

from alembic import op

revision = "a3series00000001"
down_revision = "idx000000001"
branch_labels = None
depends_on = None

SCOPE_CHECK = (
    "(scope = 'account_legacy' AND account_id IS NOT NULL AND persona_id IS NULL) "
    "OR (scope = 'persona_editorial' AND persona_id IS NOT NULL AND account_id IS NULL)"
)


def _columns(bind, table):
    return {row["name"] for row in sa.inspect(bind).get_columns(table)}


def _tables(bind):
    return set(sa.inspect(bind).get_table_names())


def _persona_fk_name(bind):
    for fk in sa.inspect(bind).get_foreign_keys("content_series"):
        if fk.get("referred_table") == "content_persona" and fk.get("constrained_columns") == ["persona_id"]:
            return fk.get("name")
    return None


def _indexes(bind, table):
    return {row["name"] for row in sa.inspect(bind).get_indexes(table)}


def upgrade():
    bind = op.get_bind()
    if "series_account_target" not in _tables(bind):
        op.create_table(
            "series_account_target",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("series_id", sa.Integer(), sa.ForeignKey("content_series.id"), nullable=False, index=True),
            sa.Column("account_id", sa.Integer(), sa.ForeignKey("content_account.id"), nullable=False, index=True),
            sa.Column("content_form", sa.String(length=100), nullable=False),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_by", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("series_id", "account_id", "content_form", name="uq_series_account_target"),
            sa.CheckConstraint("length(content_form) BETWEEN 1 AND 100", name="ck_series_target_form_length"),
        )
    if "content_series" not in _tables(bind):
        return
    columns = _columns(bind, "content_series")
    if "scope" in columns and "persona_id" in columns:
        return
    with op.batch_alter_table("content_series") as batch:
        if "scope" not in columns:
            batch.add_column(sa.Column("scope", sa.String(length=20), nullable=False, server_default="account_legacy"))
        if "persona_id" not in columns:
            batch.add_column(sa.Column("persona_id", sa.Integer(), nullable=True))
        batch.alter_column("account_id", existing_type=sa.Integer(), nullable=True)
        if _persona_fk_name(bind) is None:
            batch.create_foreign_key("fk_content_series_persona", "content_persona", ["persona_id"], ["id"])
        checks = {row["name"] for row in sa.inspect(bind).get_check_constraints("content_series")}
        if "ck_content_series_scope" not in checks:
            batch.create_check_constraint("ck_content_series_scope", SCOPE_CHECK)
    # 模型 persona_id index=True；alembic 路径补齐同名索引（create_all 库已有则跳过）。
    if "ix_content_series_persona_id" not in _indexes(bind, "content_series"):
        op.create_index("ix_content_series_persona_id", "content_series", ["persona_id"])


def downgrade():
    bind = op.get_bind()
    editorial = bind.execute(sa.text("SELECT COUNT(*) FROM content_series WHERE scope = 'persona_editorial'")).scalar()
    targets = 0
    if "series_account_target" in _tables(bind):
        targets = bind.execute(sa.text("SELECT COUNT(*) FROM series_account_target")).scalar()
    if (editorial or 0) > 0 or (targets or 0) > 0:
        # 新模式已有真实记录时拒绝破坏性回退，宁可失败也不丢数据。
        raise RuntimeError("destructive_downgrade_blocked: persona_editorial series or distribution targets exist")
    if "series_account_target" in _tables(bind):
        op.drop_table("series_account_target")
    if "content_series" not in _tables(bind):
        return
    columns = _columns(bind, "content_series")
    if "scope" not in columns and "persona_id" not in columns:
        return
    checks = {row["name"] for row in sa.inspect(bind).get_check_constraints("content_series")}
    persona_fk = _persona_fk_name(bind)
    # persona_id 的索引必须先于列删除，否则 batch 重建会在无列状态下复制索引失败。
    if "persona_id" in columns and "ix_content_series_persona_id" in _indexes(bind, "content_series"):
        op.drop_index("ix_content_series_persona_id", table_name="content_series")
    with op.batch_alter_table("content_series") as batch:
        # create_all 建出的库约束名可能不同或缺名，按实况发现，存在才删。
        if "ck_content_series_scope" in checks:
            batch.drop_constraint("ck_content_series_scope", type_="check")
        if persona_fk:
            batch.drop_constraint(persona_fk, type_="foreignkey")
        if "persona_id" in columns:
            batch.drop_column("persona_id")
        if "scope" in columns:
            batch.drop_column("scope")
        batch.alter_column("account_id", existing_type=sa.Integer(), nullable=False)
