"""V1 PRD 2.0 Content Harness — Migration A（additive）。

覆盖（开发 OpenSpec §5 Migration A）：
- channel_template_version: + profile_schema_version / profile_json（Channel Profile 载体）
- topic_brief: + targets_json / product_ref / business_line
- workflow: + workflow_key/version/parent_id/status/schema_version/checksum + unique(workflow_key, version)
- workflow_run: + topic_id/channel/content_form/workflow_key/workflow_version/definition_checksum
- workflow_step: + plugin_key/plugin_version/input_hash/output_hash/stale_reason/attempt_no
- draft: + artifact_kind/content_form/document_schema_version/document_json（按渠道 backfill）
- content_job: + content_form/artifact_kind/workflow_run_id/channel_profile_version_id
- draft_check_run: 新表（Phase 3 起写入）

不变量：不修改旧 candidate hash；历史 Workflow 回填 schema_version=1、
workflow_key='legacy.workflow.<id>'（原文按 template_key 回填会同 key 撞 unique，
以 id 兜底保证约束可满足，见 change design.md deviation 注记）。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1harness00001"
down_revision: Union[str, Sequence[str], None] = "g31415926535"
branch_labels = None
depends_on = None


def _columns(table: str) -> dict[str, dict]:
    return {item["name"]: item for item in sa.inspect(op.get_bind()).get_columns(table)}


def _has_table(engine, table: str) -> bool:
    return table in set(sa.inspect(engine).get_table_names())


def _add_columns(batch, columns: list[sa.Column], existing: dict[str, dict]) -> None:
    for col in columns:
        if col.name not in existing:
            batch.add_column(col)


CONTENT_FORM_CASE = (
    "CASE channel WHEN 'wechat' THEN 'article' WHEN 'xiaohongshu' THEN 'image_note' "
    "WHEN 'douyin' THEN 'spoken_script' WHEN 'x_thread' THEN 'thread' ELSE NULL END"
)
# draft 经 content_job 关联映射 content_form（CASE 放在关联子查询 SELECT 内）
DRAFT_CONTENT_FORM_SUBQUERY = (
    f"(SELECT {CONTENT_FORM_CASE} FROM content_job WHERE content_job.id = draft.content_job_id)"
)


def upgrade() -> None:
    bind = op.get_bind()

    # ---- channel_template_version：Channel Profile 字段 ----
    ct_cols = _columns("channel_template_version")
    with op.batch_alter_table("channel_template_version") as batch:
        _add_columns(
            batch,
            [
                sa.Column("profile_schema_version", sa.Integer(), nullable=False, server_default="1"),
                sa.Column("profile_json", sa.JSON(), nullable=True),
            ],
            ct_cols,
        )

    # ---- topic_brief：targets 真源 ----
    if _has_table(bind, "topic_brief"):  # fresh installs no longer create the old-version tables
        tb_cols = _columns("topic_brief")
        with op.batch_alter_table("topic_brief") as batch:
            _add_columns(
                batch,
                [
                    sa.Column("targets_json", sa.JSON(), nullable=True),
                    sa.Column("product_ref", sa.String(length=100), nullable=True),
                    sa.Column("business_line", sa.String(length=100), nullable=True),
                ],
                tb_cols,
            )

    # ---- workflow：版本化 Definition ----
    wf_cols = _columns("workflow")
    wf_unique = next(
        (u for u in sa.inspect(bind).get_unique_constraints("workflow") if u.get("name") == "uq_workflow_key_version"),
        None,
    )
    with op.batch_alter_table("workflow") as batch:
        _add_columns(
            batch,
            [
                sa.Column("workflow_key", sa.String(length=120), nullable=True),
                sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
                sa.Column("parent_id", sa.Integer(), nullable=True),
                sa.Column("status", sa.String(length=20), nullable=True, server_default="draft"),
                sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
                sa.Column("checksum", sa.String(length=64), nullable=True),
            ],
            wf_cols,
        )
        if "fk_workflow_parent_id" not in {fk["name"] for fk in sa.inspect(bind).get_foreign_keys("workflow")}:
            batch.create_foreign_key("fk_workflow_parent_id", "workflow", ["parent_id"], ["id"])
        if wf_unique is None:
            batch.create_unique_constraint("uq_workflow_key_version", ["workflow_key", "version"])
    # 历史行回填：workflow_key 用 id 兜底（同 template_key 多实例会撞 unique）；enabled→status
    bind.execute(sa.text("UPDATE workflow SET workflow_key = 'legacy.workflow.' || id WHERE workflow_key IS NULL"))
    bind.execute(
        sa.text(
            "UPDATE workflow SET status = CASE WHEN enabled THEN 'published' ELSE 'archived' END WHERE status IS NULL"
        )
    )

    # ---- workflow_run：冻结 definition 身份 ----
    run_cols = _columns("workflow_run")
    with op.batch_alter_table("workflow_run") as batch:
        _add_columns(
            batch,
            [
                sa.Column("topic_id", sa.Integer(), nullable=True),
                sa.Column("channel", sa.String(length=30), nullable=True),
                sa.Column("content_form", sa.String(length=50), nullable=True),
                sa.Column("workflow_key", sa.String(length=120), nullable=True),
                sa.Column("workflow_version", sa.Integer(), nullable=True),
                sa.Column("definition_checksum", sa.String(length=64), nullable=True),
            ],
            run_cols,
        )

    # ---- workflow_step：plugin 版本与 hash ----
    step_cols = _columns("workflow_step")
    with op.batch_alter_table("workflow_step") as batch:
        _add_columns(
            batch,
            [
                sa.Column("plugin_key", sa.String(length=150), nullable=True),
                sa.Column("plugin_version", sa.String(length=50), nullable=True),
                sa.Column("input_hash", sa.String(length=64), nullable=True),
                sa.Column("output_hash", sa.String(length=64), nullable=True),
                sa.Column("stale_reason", sa.Text(), nullable=True),
                sa.Column("attempt_no", sa.Integer(), nullable=False, server_default="0"),
            ],
            step_cols,
        )

    # ---- content_job：content_form / artifact_kind / run 关联 ----
    if _has_table(bind, "content_job"):  # fresh installs no longer create the old-version tables
        job_cols = _columns("content_job")
        with op.batch_alter_table("content_job") as batch:
            _add_columns(
                batch,
                [
                    sa.Column("content_form", sa.String(length=50), nullable=True),
                    sa.Column("artifact_kind", sa.String(length=20), nullable=True),
                    sa.Column("workflow_run_id", sa.Integer(), nullable=True),
                    sa.Column("channel_profile_version_id", sa.Integer(), nullable=True),
                ],
                job_cols,
            )
        bind.execute(sa.text(f"UPDATE content_job SET content_form = ({CONTENT_FORM_CASE}) WHERE content_form IS NULL"))
        bind.execute(
            sa.text("UPDATE content_job SET artifact_kind = 'script' WHERE channel = 'douyin' AND artifact_kind IS NULL")
        )
        bind.execute(sa.text("UPDATE content_job SET artifact_kind = 'text' WHERE artifact_kind IS NULL"))

    # ---- draft：Artifact / Document（channel 经 content_job 映射 backfill）----
    if _has_table(bind, "draft"):  # fresh installs no longer create the old-version tables
        draft_cols = _columns("draft")
        with op.batch_alter_table("draft") as batch:
            _add_columns(
                batch,
                [
                    sa.Column("artifact_kind", sa.String(length=20), nullable=False, server_default="text"),
                    sa.Column("content_form", sa.String(length=50), nullable=True),
                    sa.Column("document_schema_version", sa.Integer(), nullable=False, server_default="1"),
                    sa.Column("document_json", sa.JSON(), nullable=True),
                ],
                draft_cols,
            )
        bind.execute(
            sa.text(
                "UPDATE draft SET artifact_kind = 'script' WHERE artifact_kind = 'text' AND content_job_id IN "
                "(SELECT id FROM content_job WHERE channel = 'douyin')"
            )
        )
        bind.execute(
            sa.text(
                f"UPDATE draft SET content_form = {DRAFT_CONTENT_FORM_SUBQUERY} "
                "WHERE content_form IS NULL AND EXISTS (SELECT 1 FROM content_job WHERE content_job.id = draft.content_job_id)"
            )
        )

    # ---- draft_check_run：通用检查记录（Phase 3 起写入）----
    if not _has_table(bind, "draft_check_run") and _has_table(bind, "draft"):
        op.create_table(
            "draft_check_run",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("draft_id", sa.Integer(), sa.ForeignKey("draft.id"), nullable=False),
            sa.Column("check_kind", sa.String(length=30), nullable=False),
            sa.Column("profile_key", sa.String(length=150), nullable=True),
            sa.Column("profile_version", sa.String(length=50), nullable=True),
            sa.Column("input_hash", sa.String(length=64), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("report_json", sa.JSON(), nullable=True),
            sa.Column("provider_key", sa.String(length=100), nullable=True),
            sa.Column("provider_version", sa.String(length=50), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index(
            "ix_draft_check_run_draft_kind_time",
            "draft_check_run",
            ["draft_id", "check_kind", "created_at"],
        )


def downgrade() -> None:
    # Additive：M1/V1 历史与派生状态不回滚删除（与 e27182818284 同策略）
    pass
