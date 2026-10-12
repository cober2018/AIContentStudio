"""Add creative intent, external execution and capability history."""

import re

import sqlalchemy as sa

from alembic import op

revision = "aco000000001"
down_revision = "f8a000000001"
branch_labels = None
depends_on = None


_NEW_TABLES = (
    "creative_execution_package", "creative_execution", "creative_execution_output",
    "capability_artifact", "capability_artifact_revision", "capability_use",
)
_INTENT_TABLES = (
    ("content_master_revision", "ck_master_creative_intent_hash"),
    ("channel_variant_revision", "ck_variant_creative_intent_hash"),
)
_CURRENT_FK = "fk_capability_artifact_current_revision"


def _ref(name, target, nullable=False):
    return sa.Column(name, sa.Integer(), sa.ForeignKey(target, ondelete="RESTRICT"), nullable=nullable)


def _string(name, length, nullable=False):
    return sa.Column(name, sa.String(length), nullable=nullable)


def _json(name):
    return sa.Column(name, sa.JSON(), nullable=False)


def _time(name, nullable=False):
    return sa.Column(name, sa.DateTime(timezone=True), nullable=nullable)


def _actor_time():
    return [_string("created_by", 255, nullable=True), _time("created_at")]


def _normalize(sql):
    # Preserve literal whitespace when checking schemas made by the legacy initial migration.
    return re.sub(r"('(?:''|[^'])*')|\s+", lambda match: match.group(1) or "", sql)


def _ensure_table(name, columns, checks, uniques=(), indexes=()):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if name not in inspector.get_table_names():
        op.create_table(
            name, *columns,
            *(sa.CheckConstraint(sql, name=key) for key, sql in checks.items()),
            *(sa.UniqueConstraint(*fields, name=key) for key, fields in uniques),
        )
    else:
        # Initial revision uses current metadata.create_all; do not accept an incomplete existing shape.
        actual = {item["name"]: item for item in inspector.get_columns(name)}
        expected = {column.name: column for column in columns}
        if set(actual) != set(expected) or any(
            actual[key]["nullable"] != column.nullable
            or actual[key]["type"].compile(dialect=bind.dialect) != column.type.compile(dialect=bind.dialect)
            for key, column in expected.items()
        ) or inspector.get_pk_constraint(name)["constrained_columns"] != ["id"]:
            raise RuntimeError(f"creative orchestration schema mismatch: {name}")
        actual_checks = {item["name"]: item["sqltext"] for item in inspector.get_check_constraints(name)}
        if set(actual_checks) != set(checks) or (
            bind.dialect.name == "sqlite"
            and any(_normalize(actual_checks[key]) != _normalize(sql) for key, sql in checks.items())
        ):
            raise RuntimeError(f"creative orchestration check mismatch: {name}")
        actual_uniques = {item["name"]: tuple(item["column_names"])
                          for item in inspector.get_unique_constraints(name)}
        if actual_uniques != dict(uniques):
            raise RuntimeError(f"creative orchestration unique mismatch: {name}")
        actual_refs = {
            (tuple(item["constrained_columns"]), item["referred_table"], tuple(item["referred_columns"]),
             item.get("options", {}).get("ondelete"))
            for item in inspector.get_foreign_keys(name)
            if item["name"] != _CURRENT_FK
        }
        expected_refs = {
            ((column.name,), fk.target_fullname.split(".")[0], (fk.target_fullname.split(".")[1],), fk.ondelete)
            for column in columns for fk in column.foreign_keys
        }
        if actual_refs != expected_refs:
            raise RuntimeError(f"creative orchestration foreign key mismatch: {name}")
    actual_indexes = {item["name"]: item for item in sa.inspect(bind).get_indexes(name)}
    for key, fields in indexes:
        if key not in actual_indexes:
            op.create_index(key, name, fields)
        elif tuple(actual_indexes[key]["column_names"]) != fields or actual_indexes[key]["unique"]:
            raise RuntimeError(f"creative orchestration index mismatch: {name}")


def upgrade():
    for table, check in _INTENT_TABLES:
        inspector = sa.inspect(op.get_bind())
        columns = {item["name"]: item for item in inspector.get_columns(table)}
        if "creative_intent_json" not in columns:
            op.add_column(table, sa.Column("creative_intent_json", sa.JSON(none_as_null=True), nullable=True))
        elif not columns["creative_intent_json"]["nullable"] or not isinstance(
            columns["creative_intent_json"]["type"], sa.JSON
        ):
            raise RuntimeError(f"creative intent schema mismatch: {table}")
        predicate = "creative_intent_hash IS NULL OR length(creative_intent_hash) = 64"
        if "creative_intent_hash" not in columns:
            # SQLite accepts a column CHECK on ADD COLUMN; no historical table rebuild is needed.
            op.add_column(table, sa.Column("creative_intent_hash", sa.String(64),
                                          sa.CheckConstraint(predicate, name=check), nullable=True))
        else:
            column = columns["creative_intent_hash"]
            checks = {item["name"]: item["sqltext"] for item in inspector.get_check_constraints(table)}
            if (not column["nullable"] or not isinstance(column["type"], sa.String)
                    or column["type"].length != 64 or check not in checks
                    or op.get_bind().dialect.name == "sqlite" and _normalize(checks[check]) != _normalize(predicate)):
                raise RuntimeError(f"creative intent schema mismatch: {table}")

    _ensure_table("creative_execution_package", [
        sa.Column("id", sa.Integer(), primary_key=True),
        _ref("owner_user_id", "user.id"), _ref("project_id", "content_project.id"),
        _ref("content_unit_id", "content_unit.id"),
        _ref("source_master_revision_id", "content_master_revision.id", nullable=True),
        _ref("source_variant_revision_id", "channel_variant_revision.id", nullable=True),
        _string("package_schema", 100), _json("package_json"), _string("package_hash", 64),
        _string("source_payload_hash", 64), _string("source_context_hash", 64),
        _string("creative_intent_hash", 64, nullable=True), *_actor_time(),
    ], {
        "ck_creative_package_one_source":
            "(source_master_revision_id IS NOT NULL AND source_variant_revision_id IS NULL) OR "
            "(source_master_revision_id IS NULL AND source_variant_revision_id IS NOT NULL)",
        "ck_creative_package_schema": "package_schema IN ('creative.execution.v1','director.video.v1')",
        "ck_creative_package_hashes": "length(package_hash) = 64 AND length(source_payload_hash) = 64 "
            "AND length(source_context_hash) = 64",
        "ck_creative_package_intent_hash": "creative_intent_hash IS NULL OR length(creative_intent_hash) = 64",
        "ck_creative_package_actor": "created_by IS NULL OR length(created_by) <= 255",
    }, indexes=(
        ("ix_creative_package_owner_hash", ("owner_user_id", "package_hash")),
        ("ix_creative_package_project_unit", ("project_id", "content_unit_id", "created_at")),
        ("ix_creative_package_master", ("source_master_revision_id",)),
        ("ix_creative_package_variant", ("source_variant_revision_id",)),
    ))
    _ensure_table("creative_execution", [
        sa.Column("id", sa.Integer(), primary_key=True),
        _ref("owner_user_id", "user.id"), _ref("project_id", "content_project.id"),
        _ref("content_unit_id", "content_unit.id"), _ref("package_id", "creative_execution_package.id"),
        _string("idempotency_key", 150), _string("request_fingerprint", 64),
        _string("executor_kind", 30), _string("executor_key", 150), _string("executor_version", 50),
        _string("state", 30), sa.Column("revision_no", sa.Integer(), nullable=False),
        _string("dispatch_certainty", 30), _string("safe_reason", 100, nullable=True),
        _json("checkpoint_json"), _json("recovery_json"), _json("materialized_inputs_json"),
        _ref("retry_of_id", "creative_execution.id", nullable=True), *_actor_time(), _time("updated_at"),
    ], {
        "ck_creative_execution_state": "state IN ('prepared','claimed','in_progress','failed_before_dispatch','blocked',"
            "'unknown','result_ready','accepted','rejected','cancelled','superseded')",
        "ck_creative_execution_dispatch":
            "dispatch_certainty IN ('not_dispatched','possibly_dispatched','confirmed_dispatched')",
        "ck_creative_execution_predispatch": "state != 'failed_before_dispatch' OR dispatch_certainty = 'not_dispatched'",
        "ck_creative_execution_revision": "revision_no > 0",
        "ck_creative_execution_key": "length(idempotency_key) BETWEEN 1 AND 150",
        "ck_creative_execution_fingerprint": "length(request_fingerprint) = 64",
        "ck_creative_execution_executor": "length(executor_kind) BETWEEN 1 AND 30 "
            "AND length(executor_key) BETWEEN 1 AND 150 AND length(executor_version) BETWEEN 1 AND 50",
        "ck_creative_execution_reason": "safe_reason IS NULL OR length(safe_reason) BETWEEN 1 AND 100",
        "ck_creative_execution_retry": "retry_of_id IS NULL OR retry_of_id != id",
        "ck_creative_execution_actor": "created_by IS NULL OR length(created_by) <= 255",
    }, uniques=(("uq_creative_execution_owner_key", ("owner_user_id", "idempotency_key")),), indexes=(
        ("ix_creative_execution_owner_state", ("owner_user_id", "state", "updated_at")),
        ("ix_creative_execution_project_unit_state", ("project_id", "content_unit_id", "state")),
        ("ix_creative_execution_package", ("package_id",)),
        ("ix_creative_execution_retry", ("retry_of_id",)),
    ))
    _ensure_table("creative_execution_output", [
        sa.Column("id", sa.Integer(), primary_key=True), _ref("execution_id", "creative_execution.id"),
        _string("role_id", 100), _string("kind", 20),
        sa.Column("output_index", sa.Integer(), nullable=False), sa.Column("attempt_no", sa.Integer(), nullable=False),
        _string("staging_key", 500), _string("mime_type", 100), _string("content_hash", 64),
        sa.Column("size_bytes", sa.Integer(), nullable=False), _json("metadata_json"), _string("state", 20),
        _ref("material_revision_id", "material_revision.id", nullable=True), *_actor_time(),
        _string("decided_by", 255, nullable=True), _time("decided_at", nullable=True),
    ], {
        "ck_creative_output_slot": "output_index > 0 AND attempt_no > 0",
        "ck_creative_output_kind": "kind IN ('image','chart','screenshot','video','audio','brand','other')",
        "ck_creative_output_state": "state IN ('staged','accepted','rejected')",
        "ck_creative_output_role": "length(role_id) BETWEEN 1 AND 100",
        "ck_creative_output_storage": "length(staging_key) BETWEEN 1 AND 500 AND length(mime_type) BETWEEN 1 AND 100",
        "ck_creative_output_hash": "length(content_hash) = 64",
        "ck_creative_output_size": "size_bytes > 0",
        "ck_creative_output_accepted_ref": "state != 'accepted' OR material_revision_id IS NOT NULL",
        "ck_creative_output_actors": "(created_by IS NULL OR length(created_by) <= 255) "
            "AND (decided_by IS NULL OR length(decided_by) <= 255)",
    }, uniques=(("uq_creative_output_attempt", ("execution_id", "role_id", "output_index", "attempt_no")),), indexes=(
        ("ix_creative_output_execution_state", ("execution_id", "state")),
        ("ix_creative_output_material", ("material_revision_id",)),
    ))
    _ensure_table("capability_artifact", [
        sa.Column("id", sa.Integer(), primary_key=True), _ref("owner_user_id", "user.id"),
        _string("kind", 30), _string("status", 20), _string("scope_type", 30), _json("scope_json"),
        _string("name", 255), sa.Column("current_revision_id", sa.Integer(), nullable=True),
        _time("created_at"), _time("updated_at"), _time("archived_at", nullable=True), _time("deprecated_at", nullable=True),
    ], {
        "ck_capability_artifact_kind":
            "kind IN ('prompt_skill','recipe','creative_pattern','preference','execution_template','tool')",
        "ck_capability_artifact_status": "status IN ('candidate','saved','pinned','archived','deprecated')",
        "ck_capability_artifact_scope": "scope_type IN ('owner','persona','account','series','project','channel','executor')",
        "ck_capability_artifact_name": "length(name) BETWEEN 1 AND 255",
    }, indexes=(
        ("ix_capability_artifact_owner_scope_status", ("owner_user_id", "scope_type", "status", "kind")),
        ("ix_capability_artifact_current", ("current_revision_id",)),
    ))
    _ensure_table("capability_artifact_revision", [
        sa.Column("id", sa.Integer(), primary_key=True), _ref("artifact_id", "capability_artifact.id"),
        sa.Column("revision_no", sa.Integer(), nullable=False), _json("content_json"),
        _json("args_schema_json"), _json("metadata_json"), _string("content_hash", 64),
        _ref("source_execution_id", "creative_execution.id", nullable=True),
        _ref("source_learning_candidate_id", "learning_candidate.id", nullable=True), *_actor_time(),
    ], {
        "ck_capability_artifact_revision_no": "revision_no > 0",
        "ck_capability_artifact_revision_hash": "length(content_hash) = 64",
        "ck_capability_artifact_revision_actor": "created_by IS NULL OR length(created_by) <= 255",
    }, uniques=(("uq_capability_artifact_revision", ("artifact_id", "revision_no")),), indexes=(
        ("ix_capability_artifact_revision_hash", ("artifact_id", "content_hash")),
        ("ix_capability_artifact_revision_execution", ("source_execution_id",)),
        ("ix_capability_artifact_revision_learning", ("source_learning_candidate_id",)),
    ))
    current_refs = [item for item in sa.inspect(op.get_bind()).get_foreign_keys("capability_artifact")
                    if item["constrained_columns"] == ["current_revision_id"]]
    if not current_refs:
        # SQLite cannot ALTER ADD a circular FK; both tables exist before the batch rebuild.
        with op.batch_alter_table("capability_artifact") as batch:
            batch.create_foreign_key(_CURRENT_FK, "capability_artifact_revision", ["current_revision_id"], ["id"],
                                     ondelete="RESTRICT")
    elif len(current_refs) != 1 or (
        current_refs[0]["name"] != _CURRENT_FK
        or current_refs[0]["referred_table"] != "capability_artifact_revision"
        or current_refs[0]["referred_columns"] != ["id"]
        or current_refs[0].get("options", {}).get("ondelete") != "RESTRICT"
    ):
        raise RuntimeError("creative orchestration current revision foreign key mismatch")
    _ensure_table("capability_use", [
        sa.Column("id", sa.Integer(), primary_key=True), _ref("artifact_revision_id", "capability_artifact_revision.id"),
        _ref("owner_user_id", "user.id"), _ref("project_id", "content_project.id", nullable=True),
        _ref("execution_id", "creative_execution.id", nullable=True), _string("rendered_arguments_hash", 64),
        _string("outcome", 20), _time("used_at"), _string("created_by", 255, nullable=True),
    ], {
        "ck_capability_use_outcome": "outcome IN ('used','accepted','rejected','unknown')",
        "ck_capability_use_arguments_hash": "length(rendered_arguments_hash) = 64",
        "ck_capability_use_actor": "created_by IS NULL OR length(created_by) <= 255",
    }, indexes=(
        ("ix_capability_use_revision_time", ("artifact_revision_id", "used_at")),
        ("ix_capability_use_owner_project_time", ("owner_user_id", "project_id", "used_at")),
        ("ix_capability_use_execution", ("execution_id",)),
    ))


def downgrade():
    bind = op.get_bind()
    # Complete every history check before the first schema mutation, including unused packages/candidates.
    for table in _NEW_TABLES:
        if bind.execute(sa.text(f"SELECT 1 FROM {table} LIMIT 1")).first():
            raise RuntimeError("refusing downgrade: retained creative execution or capability history")
    for table, _check in _INTENT_TABLES:
        if bind.execute(sa.text(f"SELECT 1 FROM {table} WHERE creative_intent_json IS NOT NULL "
                                "OR creative_intent_hash IS NOT NULL LIMIT 1")).first():
            raise RuntimeError("refusing downgrade: retained creative intent history")
    op.drop_table("capability_use")
    with op.batch_alter_table("capability_artifact") as batch:
        batch.drop_constraint(_CURRENT_FK, type_="foreignkey")
    for table in ("capability_artifact_revision", "capability_artifact", "creative_execution_output",
                  "creative_execution", "creative_execution_package"):
        op.drop_table(table)
    for table, check in _INTENT_TABLES:
        with op.batch_alter_table(table) as batch:
            batch.drop_constraint(check, type_="check")
            batch.drop_column("creative_intent_hash")
            batch.drop_column("creative_intent_json")
