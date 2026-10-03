"""Add local durable generation tasks without applying the unapproved F8 draft."""

import re

import sqlalchemy as sa

from alembic import op

revision = "f7d000000001"
down_revision = "f7c000000001"
branch_labels = None
depends_on = None


_STATES = ("prepared", "submitting", "running", "unknown", "result_ready", "accepted", "failed", "cancelled")
_CHECKS = {
    "ck_generation_state": "state IN (" + ",".join(f"'{state}'" for state in _STATES) + ")",
    "ck_generation_revision": "revision > 0",
    "ck_generation_queries": "query_count >= 0 AND query_count <= 120",
    "ck_generation_size": "result_size IS NULL OR (result_size > 0 AND result_size <= 31457280)",
    "ck_generation_accepted_ref": "state != 'accepted' OR accepted_material_revision_id IS NOT NULL",
}


def _normalize_check(value):
    # Literal whitespace changes the predicate, unlike SQL formatting spaces.
    return re.sub(r"('(?:''|[^'])*'|\"(?:\"\"|[^\"])*\")|\s+",
                  lambda match: match.group(1) or "", value)


def _plain_index(item):
    # Partial/include/operator-class indexes are not the required whole-table index.
    return all(value is None or value is False
               or isinstance(value, (list, dict)) and not value
               or key == "postgresql_using" and value == "btree"
               for key, value in item.get("dialect_options", {}).items())


def _check_definitions(dialect):
    checks = dict(_CHECKS)
    if dialect == "postgresql":
        # PostgreSQL introspection renders IN as ANY and removes redundant
        # parentheses. Match that exact form, not arbitrary same-name checks.
        checks["ck_generation_state"] = "state::text = ANY (ARRAY[" + ",".join(
            f"'{state}'::character varying" for state in _STATES) + "]::text[])"
        checks["ck_generation_size"] = "result_size IS NULL OR result_size > 0 AND result_size <= 31457280"
        checks["ck_generation_accepted_ref"] = "state::text <> 'accepted'::text OR accepted_material_revision_id IS NOT NULL"
    return {name: _normalize_check(value) for name, value in checks.items()}


def upgrade():
    columns = [
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("content_project.id")),
        sa.Column("workflow_step_attempt_id", sa.Integer(), sa.ForeignKey("workflow_step_attempt.id")),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("query_count", sa.Integer(), nullable=False),
        sa.Column("result_size", sa.Integer()),
        sa.Column("accepted_material_revision_id", sa.Integer(), sa.ForeignKey("material_revision.id")),
    ]
    for name, length in (
        ("idempotency_key", 100), ("request_hash", 64), ("state", 20), ("plan_hash", 64),
        ("provider_kind", 30), ("provider_key", 150), ("provider_version", 50),
        ("model_id", 100), ("protocol_version", 50), ("runtime_hash", 64),
        ("credential_epoch", 64), ("input_hash", 64), ("receipt_key_id", 100), ("receipt_signature", 64),
    ):
        columns.append(sa.Column(name, sa.String(length), nullable=False))
    for name, length in (
        ("provider_job_id", 200), ("provider_file_id", 200), ("result_storage_key", 300),
        ("result_mime", 100), ("result_hash", 64), ("result_signature", 64),
        ("acceptance_hash", 64), ("lease_token", 32), ("reason_code", 100),
    ):
        columns.append(sa.Column(name, sa.String(length)))
    columns.extend(sa.Column(name, sa.JSON(), nullable=False) for name in ("request_json", "plan_json", "source_refs_json"))
    columns.extend(sa.Column(name, sa.DateTime(timezone=True), nullable=False) for name in ("created_at", "updated_at"))
    columns.append(sa.Column("lease_expires_at", sa.DateTime(timezone=True)))
    inspector = sa.inspect(op.get_bind())
    if "provider_generation_task" in inspector.get_table_names():
        # The historical initial migration uses today's metadata.create_all.
        # Skip only an exact existing shape, never silently accept an older one.
        actual = {item["name"]: item for item in inspector.get_columns("provider_generation_task")}
        expected = {column.name: column for column in columns}
        dialect = op.get_bind().dialect
        if (set(actual) != set(expected) or any(
                actual[name]["nullable"] != column.nullable
                or actual[name]["type"].compile(dialect=dialect) != column.type.compile(dialect=dialect)
                for name, column in expected.items())
                or inspector.get_pk_constraint("provider_generation_task")["constrained_columns"] != ["id"]):
            raise RuntimeError("generation task schema mismatch")
        foreign_keys = {
            (tuple(item["constrained_columns"]), item["referred_table"], tuple(item["referred_columns"]))
            for item in inspector.get_foreign_keys("provider_generation_task")
        }
        expected_foreign_keys = {
            (("owner_user_id",), "user", ("id",)),
            (("project_id",), "content_project", ("id",)),
            (("workflow_step_attempt_id",), "workflow_step_attempt", ("id",)),
            (("accepted_material_revision_id",), "material_revision", ("id",)),
        }
        if foreign_keys != expected_foreign_keys:
            raise RuntimeError("generation task schema mismatch")
        check_items = inspector.get_check_constraints("provider_generation_task")
        if any(any(item.get("dialect_options", {}).values()) for item in check_items):
            raise RuntimeError("generation task schema mismatch")
        checks = {item["name"]: _normalize_check(item["sqltext"]) for item in check_items}
        uniques = {item["name"]: item["column_names"]
                   for item in inspector.get_unique_constraints("provider_generation_task")}
        indexes = {item["name"]: (item["column_names"], bool(item["unique"]), _plain_index(item))
                   for item in inspector.get_indexes("provider_generation_task")}
        if (any(checks.get(name) != value for name, value in _check_definitions(dialect.name).items())
                or uniques.get("uq_generation_owner_key") != ["owner_user_id", "idempotency_key"]
                or indexes.get("ix_generation_owner_state") != (["owner_user_id", "state"], False, True)
                or indexes.get("ix_generation_project_state") != (["project_id", "state"], False, True)):
            raise RuntimeError("generation task schema mismatch")
        return
    op.create_table(
        "provider_generation_task", *columns,
        sa.UniqueConstraint("owner_user_id", "idempotency_key", name="uq_generation_owner_key"),
        *(sa.CheckConstraint(value, name=name) for name, value in _CHECKS.items()),
    )
    op.create_index("ix_generation_owner_state", "provider_generation_task", ["owner_user_id", "state"])
    op.create_index("ix_generation_project_state", "provider_generation_task", ["project_id", "state"])


def downgrade():
    # Unknown/running and accepted history must not disappear during rollback.
    if op.get_bind().execute(sa.text("SELECT 1 FROM provider_generation_task LIMIT 1")).first():
        raise RuntimeError("refusing downgrade: retained generation tasks")
    op.drop_table("provider_generation_task")
