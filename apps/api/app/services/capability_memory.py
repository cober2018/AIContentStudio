"""Owner-scoped immutable methods, explicit reuse and evidence-backed capture."""

import copy
from functools import wraps

from fastapi import HTTPException
from sqlalchemy import func, inspect, select, update
from sqlalchemy.exc import DBAPIError, IntegrityError

from ..models import (
    CapabilityArtifact,
    CapabilityArtifactRevision,
    CapabilityUse,
    ChannelVariantRevision,
    ContentMasterRevision,
    ContentProject,
    CreativeBriefRevision,
    CreativeExecution,
    IdentitySnapshot,
    LearningCandidate,
    ProjectFactBoundaryRevision,
    User,
    utcnow,
)
from . import content_identity, content_learning, content_masters, creative_executions
from .capability_contracts import (
    IDENTIFIER,
    KINDS,
    OUTCOMES,
    SCOPES,
    STATUSES,
    artifact,
    canonical,
    digest,
    error,
    fields,
    positive_id,
    render,
    text,
)
from .content_harness.channel_registry import resolve_channel
from .content_masters import owned_unit

TABLES = ("capability_artifact", "capability_artifact_revision", "capability_use")


def _ready(db):
    inspector = inspect(db.connection())
    if not all(inspector.has_table(table) for table in TABLES):
        raise error("capability_memory_unavailable", 503)


def _active(user):
    if not user.is_active:
        raise error("capability_user_unavailable", 403)


def _write(operation):
    @wraps(operation)
    def atomic(db, user, *args, **kwargs):
        try:
            _ready(db)
            identity = inspect(user).identity
            owner_id = identity[0] if identity else user.id
            if db.new or db.deleted or any(db.is_modified(row) for row in db.dirty):
                raise error("capability_separate_transaction_required", 409)
            # Owner UPDATE serializes dedupe even before any artifact exists, across processes.
            with db.no_autoflush:
                changed = db.execute(update(User).where(
                    User.id == owner_id, User.is_active.is_(True), User.role.in_(("admin", "editor")),
                ).values(id=User.id).execution_options(synchronize_session=False))
            if changed.rowcount != 1:
                raise error("capability_editor_required", 403)
            db.expire_all()
            result = operation(db, user, *args, **kwargs)
            db.commit()
            return result
        except IntegrityError:
            db.rollback()
            raise error("capability_revision_conflict", 409) from None
        except DBAPIError as exc:
            db.rollback()
            if content_learning.database_conflict(exc):
                raise error("capability_database_conflict", 409) from None
            raise
        except BaseException:
            db.rollback()
            raise
    return atomic


def _owned(db, user, artifact_id):
    _active(user)
    row = db.scalar(select(CapabilityArtifact).where(
        CapabilityArtifact.id == positive_id(artifact_id), CapabilityArtifact.owner_user_id == user.id,
    ).execution_options(populate_existing=True))
    if row is None:
        raise error("capability_not_found", 404)
    return row


def _scope(db, user, kind, value, *, mutable=False):
    if type(kind) is not str or kind not in SCOPES or type(value) is not dict:
        raise error("capability_scope_invalid")
    if kind == "owner":
        fields(value, {"id"})
        if positive_id(value.get("id", user.id)) != user.id:
            raise error("capability_scope_not_found", 404)
        return {"id": user.id}
    if kind in {"persona", "account", "series"}:
        fields(value, {"id"})
        entity_id = positive_id(value.get("id"))
        content_learning.resolve_scope(db, user, kind, entity_id, mutable=mutable)
        return {"id": entity_id}
    if kind == "project":
        fields(value, {"id"})
        project = db.get(ContentProject, positive_id(value.get("id")))
        if project is None or project.owner_user_id != user.id:
            raise error("capability_scope_not_found", 404)
        if mutable:
            project = db.scalar(select(ContentProject).where(ContentProject.id == project.id)
                .with_for_update().execution_options(populate_existing=True))
            if project.status == "archived":
                raise error("capability_scope_archived", 409)
        return {"id": project.id}
    if kind == "channel":
        fields(value, {"channel_id"})
        channel = text(value.get("channel_id"), 100, required=True)
        if resolve_channel(db, channel) is None:
            raise error("capability_channel_invalid")
        return {"channel_id": channel}
    fields(value, {"executor_kind", "executor_key", "executor_version"})
    result = {}
    for key, maximum in (("executor_kind", 30), ("executor_key", 150), ("executor_version", 50)):
        result[key] = text(value.get(key), maximum, required=True)
        if not IDENTIFIER.fullmatch(result[key]):
            raise error("capability_executor_invalid")
    return result


def _narrower(db, user, old_kind, old_scope, new_kind, new_scope):
    if old_kind == new_kind:
        return old_scope == new_scope
    if old_kind == "owner":
        return True
    if new_kind in {"account", "series"}:
        ancestry = content_learning.resolve_scope(db, user, new_kind, new_scope["id"])
        return old_kind in {"persona", "account"} and ancestry.get(old_kind + "_id") == old_scope.get("id")
    # A project can contain siblings and channels; it is not an implicit Identity child.
    return False


def _context(db, user, data, *, mutable=False):
    project_id, unit_id = data.get("project_id"), data.get("unit_id")
    execution = None
    if data.get("execution_id") is not None:
        execution = db.get(CreativeExecution, positive_id(data["execution_id"]))
        if execution is None or execution.owner_user_id != user.id:
            raise error("capability_execution_not_found", 404)
        project_id = project_id if project_id is not None else execution.project_id
        unit_id = unit_id if unit_id is not None else execution.content_unit_id
        if (execution.project_id, execution.content_unit_id) != (project_id, unit_id):
            raise error("capability_execution_context_mismatch", 404)
    context = {"owner": {"id": user.id}}
    if project_id is None and unit_id is None:
        return context
    project, unit = owned_unit(db, positive_id(project_id), positive_id(unit_id), user, mutate=mutable)
    context["project"] = {"id": project.id}
    if unit.channel_id:
        context["channel"] = _scope(db, user, "channel", {"channel_id": unit.channel_id})
    snapshot = db.get(IdentitySnapshot, unit.identity_snapshot_id) if unit.identity_snapshot_id else None
    if snapshot is not None:
        if snapshot.owner_user_id != user.id or (snapshot.persona_id, snapshot.account_id, snapshot.series_id) != (
            unit.persona_id, unit.account_id, unit.series_id,
        ):
            raise error("capability_identity_context_mismatch", 409)
        content_identity.hierarchy(db, user, persona_id=snapshot.persona_id,
            account_id=snapshot.account_id, series_id=snapshot.series_id, mutable=mutable)
        for kind in ("persona", "account", "series"):
            entity_id = getattr(snapshot, kind + "_id")
            if entity_id is not None:
                context[kind] = _scope(db, user, kind, {"id": entity_id}, mutable=mutable)
    elif unit.identity_snapshot_id is not None:
        raise error("capability_identity_context_missing", 409)
    if execution:
        context["executor"] = _scope(db, user, "executor", {key: getattr(execution, key)
            for key in ("executor_kind", "executor_key", "executor_version")})
    return context


def _validate_revision(revision):
    frozen = revision.metadata_json
    if type(frozen) is not dict:
        raise error("capability_revision_integrity", 409)
    try:
        _content, _schema, content_hash = artifact(frozen.get("kind"), revision.content_json, revision.args_schema_json)
        canonical({"content": revision.content_json, "args_schema": revision.args_schema_json, "metadata": frozen})
    except HTTPException:
        raise error("capability_revision_integrity", 409) from None
    if content_hash != revision.content_hash:
        raise error("capability_revision_integrity", 409)


def _revision(db, row):
    revision = db.get(CapabilityArtifactRevision, row.current_revision_id)
    if revision is None or revision.artifact_id != row.id:
        raise error("capability_revision_integrity", 409)
    _validate_revision(revision)
    frozen = revision.metadata_json
    if any(frozen.get(key) != value for key, value in (
        ("kind", row.kind), ("name", row.name), ("status", row.status),
        ("scope_type", row.scope_type), ("scope", row.scope_json),
    )):
        raise error("capability_revision_integrity", 409)
    return revision


def _revision_json(revision):
    _validate_revision(revision)
    return {"id": revision.id, "revision_no": revision.revision_no,
        "content": copy.deepcopy(revision.content_json), "args_schema": copy.deepcopy(revision.args_schema_json),
        "content_hash": revision.content_hash, "metadata": copy.deepcopy(revision.metadata_json),
        "source_execution_id": revision.source_execution_id,
        "source_learning_candidate_id": revision.source_learning_candidate_id,
        "created_at": revision.created_at.isoformat()}


def _detail(db, row):
    revision = _revision(db, row)
    count, last_used = db.execute(select(func.count(CapabilityUse.id), func.max(CapabilityUse.used_at))
        .join(CapabilityArtifactRevision, CapabilityUse.artifact_revision_id == CapabilityArtifactRevision.id)
        .where(CapabilityArtifactRevision.artifact_id == row.id,
            CapabilityUse.owner_user_id == row.owner_user_id)).one()
    return {"id": row.id, "kind": row.kind, "name": row.name, "status": row.status,
        "scope_type": row.scope_type, "scope": copy.deepcopy(row.scope_json), "source_kind": "capability_memory",
        "current_revision": _revision_json(revision),
        "usage": {"use_count": count, "last_used": last_used.isoformat() if last_used else None}}


def _append(db, user, row, content, schema, content_hash, *, previous=None, provenance=None,
            execution_id=None, learning_id=None):
    metadata = {"kind": row.kind, "name": row.name, "status": row.status,
        "scope_type": row.scope_type, "scope": copy.deepcopy(row.scope_json),
        "provenance": copy.deepcopy(previous.metadata_json.get("provenance", {}) if previous else provenance or {})}
    canonical({"content": content, "args_schema": schema, "metadata": metadata})
    revision = CapabilityArtifactRevision(artifact_id=row.id,
        revision_no=previous.revision_no + 1 if previous else 1,
        content_json=copy.deepcopy(content), args_schema_json=copy.deepcopy(schema), content_hash=content_hash,
        metadata_json=canonical(metadata), source_execution_id=previous.source_execution_id if previous else execution_id,
        source_learning_candidate_id=previous.source_learning_candidate_id if previous else learning_id,
        created_by=user.email)
    db.add(revision)
    db.flush([revision])
    return revision


def _create(db, user, data, *, scope_type=None, scope=None, provenance=None, execution_id=None, learning_id=None,
            dedupe=False, candidate_only=False):
    kind = data.get("kind")
    content, schema, content_hash = artifact(kind, data.get("content"), data.get("args_schema", {}))
    name = text(data.get("name"), 255, required=True).strip()
    scope_type = scope_type or data.get("scope_type", "owner")
    scope = _scope(db, user, scope_type, scope if scope is not None else data.get("scope", {}), mutable=True)
    if dedupe:
        rows = db.scalars(select(CapabilityArtifact).join(CapabilityArtifactRevision,
            CapabilityArtifact.current_revision_id == CapabilityArtifactRevision.id).where(
                CapabilityArtifact.owner_user_id == user.id, CapabilityArtifact.kind == kind,
                CapabilityArtifact.scope_type == scope_type, CapabilityArtifactRevision.content_hash == content_hash,
                CapabilityArtifactRevision.source_execution_id == execution_id,
                CapabilityArtifactRevision.source_learning_candidate_id == learning_id,
                CapabilityArtifact.status.in_(("candidate",) if candidate_only else ("candidate", "saved", "pinned")),
            ).order_by(CapabilityArtifact.id)).all()
        for row in rows:
            current = _revision(db, row)
            if row.scope_json == scope and current.metadata_json.get("provenance", {}) == (provenance or {}):
                return _detail(db, row)
    row = CapabilityArtifact(owner_user_id=user.id, kind=kind, status="candidate", name=name,
        scope_type=scope_type, scope_json=scope)
    db.add(row)
    db.flush()
    revision = _append(db, user, row, content, schema, content_hash,
        provenance=provenance, execution_id=execution_id, learning_id=learning_id)
    row.current_revision_id = revision.id
    db.flush()
    return _detail(db, row)


@_write
def create_artifact(db, user, data):
    fields(data, {"kind", "name", "content", "args_schema", "scope_type", "scope"})
    return _create(db, user, data)


def get_artifact(db, user, artifact_id):
    _ready(db)
    return _detail(db, _owned(db, user, artifact_id))


def revisions(db, user, artifact_id):
    _ready(db)
    row = _owned(db, user, artifact_id)
    return {"items": [_revision_json(revision) for revision in db.scalars(
        select(CapabilityArtifactRevision).where(CapabilityArtifactRevision.artifact_id == row.id)
        .order_by(CapabilityArtifactRevision.revision_no.desc())).all()]}


def _expected(db, user, artifact_id, data):
    row = _owned(db, user, artifact_id)
    previous = _revision(db, row)
    if positive_id(data.get("expected_revision")) != previous.revision_no:
        raise error("capability_revision_conflict", 409)
    return row, previous


def _advance(db, row, previous, revision):
    changed = db.execute(update(CapabilityArtifact).where(CapabilityArtifact.id == row.id,
        CapabilityArtifact.owner_user_id == row.owner_user_id,
        CapabilityArtifact.current_revision_id == previous.id).values(current_revision_id=revision.id,
            kind=row.kind, name=row.name, status=row.status, scope_type=row.scope_type,
            scope_json=row.scope_json, updated_at=utcnow(), archived_at=row.archived_at,
            deprecated_at=row.deprecated_at).execution_options(synchronize_session=False))
    if changed.rowcount != 1:
        raise error("capability_revision_conflict", 409)
    db.refresh(row)
    return _detail(db, row)


@_write
def update_revision(db, user, artifact_id, data):
    fields(data, {"expected_revision", "content", "args_schema"})
    row, previous = _expected(db, user, artifact_id, data)
    if row.status in {"archived", "deprecated"}:
        raise error("capability_archived_read_only", 409)
    _scope(db, user, row.scope_type, row.scope_json, mutable=True)
    content, schema, content_hash = artifact(row.kind, data.get("content"), data.get("args_schema", {}))
    revision = _append(db, user, row, content, schema, content_hash, previous=previous)
    return _advance(db, row, previous, revision)


@_write
def lifecycle(db, user, artifact_id, data):
    fields(data, {"expected_revision", "status", "scope_type", "scope", "confirm_scope_broadening", "name"})
    row, previous = _expected(db, user, artifact_id, data)
    status = data.get("status")
    if type(status) is not str or status not in STATUSES:
        raise error("capability_status_invalid")
    kind = data.get("scope_type", row.scope_type)
    if kind != row.scope_type and "scope" not in data:
        raise error("capability_scope_required")
    scope = _scope(db, user, kind, data.get("scope", row.scope_json), mutable=status not in {"archived", "deprecated"})
    if (kind, scope) != (row.scope_type, row.scope_json) and not _narrower(
        db, user, row.scope_type, row.scope_json, kind, scope,
    ) and data.get("confirm_scope_broadening") is not True:
        raise error("capability_scope_confirmation_required", 409)
    if "confirm_scope_broadening" in data and type(data["confirm_scope_broadening"]) is not bool:
        raise error("capability_scope_confirmation_invalid")
    name = text(data.get("name", row.name), 255, required=True).strip()
    if (status, kind, scope, name) == (row.status, row.scope_type, row.scope_json, row.name):
        return _detail(db, row)
    row.status, row.scope_type, row.scope_json, row.name = status, kind, scope, name
    row.archived_at = utcnow() if status == "archived" else None
    row.deprecated_at = utcnow() if status == "deprecated" else None
    # Keep dirty root metadata out of autoflush until the previous pointer wins CAS.
    with db.no_autoflush:
        revision = _append(db, user, row, previous.content_json, previous.args_schema_json,
            previous.content_hash, previous=previous)
        return _advance(db, row, previous, revision)


def _page(data, *, discovery=False):
    limit, offset = data.get("limit", 20 if discovery else 50), data.get("offset", 0)
    if type(limit) is not int or not 1 <= limit <= 100 or type(offset) is not int or offset < 0:
        raise error("capability_pagination_invalid")
    return min(limit, 20) if discovery else limit, offset


def _search(db, user, data, *, discovery=False, context=None):
    _active(user)
    limit, offset = _page(data, discovery=discovery)
    query = select(CapabilityArtifact).where(CapabilityArtifact.owner_user_id == user.id)
    status, kind, scope_type = data.get("status"), data.get("kind"), data.get("scope_type")
    if discovery:
        query = query.where(CapabilityArtifact.status.in_(("saved", "pinned")))
    elif status is not None:
        if type(status) is not str or status not in STATUSES:
            raise error("capability_status_invalid")
        query = query.where(CapabilityArtifact.status == status)
    if kind is not None:
        if type(kind) is not str or kind not in KINDS:
            raise error("capability_kind_invalid")
        query = query.where(CapabilityArtifact.kind == kind)
    if scope_type is not None:
        if type(scope_type) is not str or scope_type not in SCOPES:
            raise error("capability_scope_invalid")
        query = query.where(CapabilityArtifact.scope_type == scope_type)
    q = text(data.get("q", ""), 500).casefold().strip()
    tag = text(data.get("tag", ""), 100).strip()
    matches = []
    for row in db.scalars(query.order_by(CapabilityArtifact.name, CapabilityArtifact.id)).all():
        if discovery and context.get(row.scope_type) != row.scope_json:
            continue
        # Revalidate ancestry rather than trusting stale root ownership after a parent change.
        _scope(db, user, row.scope_type, row.scope_json)
        revision = _revision(db, row)
        if tag and tag not in revision.content_json.get("tags", []):
            continue
        if q and q not in row.name.casefold() and q not in str(revision.content_json).casefold():
            continue
        matches.append(row)
    items = [_detail(db, row) for row in matches[offset:offset + limit]]
    if discovery:
        for item in items:
            item["matched_scope"] = {"scope_type": item["scope_type"], "scope": copy.deepcopy(item["scope"])}
    return {"items": items, "total": len(matches), "limit": limit, "offset": offset}


def list_artifacts(db, user, data):
    _ready(db)
    fields(data, {"status", "kind", "scope_type", "q", "tag", "limit", "offset"})
    return _search(db, user, data)


def discover(db, user, data):
    _ready(db)
    fields(data, {"project_id", "unit_id", "execution_id", "kind", "scope_type", "q", "tag", "limit", "offset"})
    positive_id(data.get("project_id"))
    positive_id(data.get("unit_id"))
    return _search(db, user, data, discovery=True, context=_context(db, user, data))


@_write
def use_artifact(db, user, artifact_id, data):
    fields(data, {"artifact_revision_id", "arguments", "project_id", "unit_id", "execution_id"})
    row = _owned(db, user, artifact_id)
    revision = _revision(db, row)
    if row.status not in {"saved", "pinned"}:
        raise error("capability_not_discoverable", 409)
    if positive_id(data.get("artifact_revision_id")) != revision.id:
        raise error("capability_revision_conflict", 409)
    _scope(db, user, row.scope_type, row.scope_json, mutable=True)
    context = _context(db, user, data, mutable=True)
    if context.get(row.scope_type) != row.scope_json:
        raise error("capability_scope_not_applicable", 404)
    rendered, arguments_hash = render(revision.content_json, revision.args_schema_json, data.get("arguments", {}))
    use = CapabilityUse(artifact_revision_id=revision.id, owner_user_id=user.id,
        project_id=context.get("project", {}).get("id"), execution_id=data.get("execution_id"),
        rendered_arguments_hash=arguments_hash, outcome="used", created_by=user.email)
    db.add(use)
    db.flush()
    return {"use_id": use.id, "artifact_revision_id": revision.id, "content_hash": revision.content_hash,
        "rendered_content": rendered, "rendered_arguments_hash": arguments_hash, "outcome": "used"}


def get_use(db, user, use_id):
    _ready(db)
    _active(user)
    use = db.scalar(select(CapabilityUse).where(
        CapabilityUse.id == positive_id(use_id), CapabilityUse.owner_user_id == user.id,
    ).execution_options(populate_existing=True))
    if use is None:
        raise error("capability_use_not_found", 404)
    revision = db.get(CapabilityArtifactRevision, use.artifact_revision_id, populate_existing=True)
    if revision is None:
        raise error("capability_revision_integrity", 409)
    _owned(db, user, revision.artifact_id)
    _validate_revision(revision)
    return {"use_id": use.id, "artifact_revision_id": use.artifact_revision_id, "outcome": use.outcome}


@_write
def record_outcome(db, user, use_id, data):
    fields(data, {"outcome", "expected_outcome"})
    expected, outcome = data.get("expected_outcome"), data.get("outcome")
    if type(expected) is not str or expected not in OUTCOMES or type(outcome) is not str or outcome not in OUTCOMES:
        raise error("capability_outcome_invalid")
    use = db.get(CapabilityUse, positive_id(use_id))
    if use is None or use.owner_user_id != user.id:
        raise error("capability_use_not_found", 404)
    revision = db.get(CapabilityArtifactRevision, use.artifact_revision_id)
    if revision is None:
        raise error("capability_revision_integrity", 409)
    _owned(db, user, revision.artifact_id)
    changed = db.execute(update(CapabilityUse).where(CapabilityUse.id == use.id,
        CapabilityUse.owner_user_id == user.id, CapabilityUse.outcome == expected)
        .values(outcome=outcome).execution_options(synchronize_session=False))
    if changed.rowcount != 1:
        raise error("capability_outcome_conflict", 409)
    return {"use_id": use.id, "artifact_revision_id": use.artifact_revision_id, "outcome": outcome}


@_write
def capture_execution(db, user, data):
    fields(data, {"execution_id", "kind", "name", "content", "args_schema"})
    row = db.get(CreativeExecution, positive_id(data.get("execution_id")))
    if row is None or row.owner_user_id != user.id:
        raise error("capability_execution_not_found", 404)
    creative_executions._owned(db, row.project_id, row.content_unit_id, row.id, user)
    if row.state != "accepted":
        raise error("capability_execution_not_fully_accepted", 409)
    package = creative_executions._package(db, row, user, current=False)
    source = db.get(ContentMasterRevision if package.source_master_revision_id else ChannelVariantRevision,
        package.source_master_revision_id or package.source_variant_revision_id)
    if source is None or (source.project_id, source.content_unit_id) != (row.project_id, row.content_unit_id):
        raise error("capability_execution_source_not_found", 404)
    if (source.payload_hash, source.context_hash) != (package.source_payload_hash, package.source_context_hash):
        raise error("capability_execution_source_integrity", 409)
    outputs = creative_executions._outputs(db, row)
    if not creative_executions._completion(package, outputs)[1]:
        raise error("capability_execution_not_fully_accepted", 409)
    required = {role["role_id"] for role in creative_executions._roles(package) if role["required"]}
    current_outputs = creative_executions._latest(outputs).values()
    if any(output.role_id in required and output.state == "accepted" and output.material_revision_id is None
            for output in current_outputs):
        raise error("capability_execution_not_fully_accepted", 409)
    provenance = {"source_kind": "creative_execution", "execution_id": row.id,
        "execution_revision": row.revision_no, "package_id": package.id, "package_hash": package.package_hash,
        "project_id": row.project_id, "unit_id": row.content_unit_id,
        "source": {"kind": "master" if package.source_master_revision_id else "variant", "id": source.id,
            "payload_hash": package.source_payload_hash, "context_hash": package.source_context_hash},
        "accepted_outputs": [{"id": output.id, "role_id": output.role_id, "output_index": output.output_index,
            "content_hash": output.content_hash, "material_revision_id": output.material_revision_id}
            for output in current_outputs if output.state == "accepted"]}
    return _create(db, user, data, scope_type="project", scope={"id": row.project_id},
        provenance=provenance, execution_id=row.id, dedupe=True)


@_write
def capture_learning(db, user, data):
    fields(data, {"learning_candidate_id", "expected_learning_revision", "kind", "name", "content", "args_schema"})
    candidate_id = positive_id(data.get("learning_candidate_id"))
    expected = positive_id(data.get("expected_learning_revision"))
    # A no-op lock preserves the accepted Learning revision; capture is not a Learning decision.
    changed = db.execute(update(LearningCandidate).where(LearningCandidate.id == candidate_id,
        LearningCandidate.owner_user_id == user.id).values(revision_no=LearningCandidate.revision_no)
        .execution_options(synchronize_session=False))
    if changed.rowcount != 1:
        raise error("capability_learning_not_found", 404)
    row = db.get(LearningCandidate, candidate_id, populate_existing=True)
    if row.revision_no != expected:
        raise error("capability_learning_revision_conflict", 409)
    if row.status != "accepted":
        raise error("capability_learning_not_accepted", 409)
    summary = row.validation_summary_json
    if (type(summary) is not dict or type(summary.get("evidence")) is not list
            or any(type(evidence) is not dict for evidence in summary["evidence"])):
        raise error("capability_learning_integrity", 409)
    frozen = content_learning.trusted_frozen_decision(row)
    if frozen.get("candidate_id") != row.id or frozen.get("scope") != row.scope_json:
        raise error("capability_learning_integrity", 409)
    refs = []
    for evidence in frozen["evidence"]:
        if (type(evidence) is not dict or evidence.get("learning_candidate_id") != row.id
                or not evidence.get("snapshot")
                or content_learning.checksum(evidence["snapshot"]) != evidence.get("snapshot_checksum")):
            raise error("capability_learning_evidence_integrity", 409)
        content_learning.reference(db, user, evidence["evidence_type"], evidence["entity_id"])
        refs.append({"evidence_id": positive_id(evidence.get("id")), "evidence_type": evidence["evidence_type"],
            "entity_id": positive_id(evidence["entity_id"]), "role": evidence["role"],
            "snapshot_checksum": evidence["snapshot_checksum"]})
    scope_kind, scope = "owner", {"id": user.id}
    origins = content_learning.scope_origins(db, user, frozen["scope"])
    identity_ids = {kind: {origin[kind + "_id"] for origin in origins if origin.get(kind + "_id") is not None}
        for kind in ("series", "account", "persona")}
    if any(len(ids) > 1 for ids in identity_ids.values()):
        raise error("capability_learning_scope_ambiguous", 409)
    for kind in ("series", "account", "persona"):
        ids = identity_ids[kind]
        if ids:
            scope_kind, scope = kind, {"id": ids.pop()}
            ancestry = content_learning.resolve_scope(db, user, kind, scope["id"])
            if any(ids and ancestry.get(parent + "_id") not in ids for parent, ids in identity_ids.items()):
                raise error("capability_learning_scope_ambiguous", 409)
            break
    provenance = {"source_kind": "learning_candidate", "learning_candidate_id": row.id,
        "learning_revision": row.revision_no, "decision_checksum": frozen["checksum"], "evidence_refs": refs}
    return _create(db, user, data, scope_type=scope_kind, scope=scope,
        provenance=provenance, learning_id=row.id, dedupe=True)


PREFERENCE_EDIT_FIELDS = {"master_revision_id", "revision_no", "payload_hash", "context_hash",
    "parent_revision_id", "parent_payload_hash", "parent_context_hash"}


def _preference_edit(db, user, project, unit, row):
    if row is None or (row.project_id, row.content_unit_id) != (project.id, unit.id):
        raise error("capability_preference_edit_not_found", 404)
    if row.source_kind != "user_edit" or row.created_by != user.email or row.parent_revision_id is None:
        raise error("capability_preference_human_edit_required", 409)
    parent = db.get(ContentMasterRevision, row.parent_revision_id, populate_existing=True)
    if (parent is None or (parent.project_id, parent.content_unit_id) != (project.id, unit.id)
            or row.revision_no != parent.revision_no + 1 or row.payload_schema != parent.payload_schema
            or row.modality != parent.modality or row.modality != unit.modality):
        raise error("capability_preference_parent_integrity", 409)
    for revision in (row, parent):
        try:
            if type(revision.payload_json) is not dict or content_masters._hash(revision.payload_json) != revision.payload_hash:
                raise error("capability_preference_edit_integrity", 409)
            for cls, entity_id in ((IdentitySnapshot, revision.identity_snapshot_id),
                    (CreativeBriefRevision, revision.creative_brief_revision_id),
                    (ProjectFactBoundaryRevision, revision.fact_boundary_revision_id)):
                if entity_id is not None:
                    context_row = db.get(cls, entity_id, populate_existing=True)
                    if context_row is None or (isinstance(context_row, IdentitySnapshot)
                            and context_row.owner_user_id != user.id) or (not isinstance(context_row, IdentitySnapshot)
                            and context_row.project_id != project.id):
                        raise error("capability_preference_edit_integrity", 409)
            if content_masters._hash(content_masters.frozen_context(db, revision)) != revision.context_hash:
                raise error("capability_preference_edit_integrity", 409)
        except (TypeError, ValueError, RecursionError):
            raise error("capability_preference_edit_integrity", 409) from None
    summary = row.edit_summary_json
    if type(summary) is not dict:
        raise error("capability_preference_edit_integrity", 409)
    if "ai_edits" in summary or "ai_provenance" in summary:
        from .text_master_ai import verify_ai_edits

        try:
            if row.payload_schema != "text.master.v2" or "ai_edits" not in summary:
                raise error("capability_preference_edit_integrity", 409)
            verified = verify_ai_edits(db, project_id=project.id, unit_id=unit.id, actor=user.email,
                base=parent, document=row.payload_json["document"], ai_edits=summary["ai_edits"])
            if verified != summary.get("ai_provenance"):
                raise error("capability_preference_edit_integrity", 409)
        except (HTTPException, KeyError, TypeError, ValueError):
            raise error("capability_preference_edit_integrity", 409) from None
    # Final output binding and attestation are delivery evidence, not editing preferences.
    content = {key: value for key, value in row.payload_json.items() if key != "render_asset_ref"}
    previous_content = {key: value for key, value in parent.payload_json.items() if key != "render_asset_ref"}
    if content_masters._hash(content) == content_masters._hash(previous_content):
        raise error("capability_preference_content_change_required", 409)
    return {"master_revision_id": row.id, "revision_no": row.revision_no,
        "payload_hash": row.payload_hash, "context_hash": row.context_hash,
        "parent_revision_id": parent.id, "parent_payload_hash": parent.payload_hash,
        "parent_context_hash": parent.context_hash, "actor_user_id": user.id,
        "payload_schema": row.payload_schema, "created_at": row.created_at.isoformat()}


def preference_edits(db, user, data):
    _ready(db)
    _active(user)
    fields(data, {"project_id", "unit_id", "limit", "offset"})
    project, unit = owned_unit(db, positive_id(data.get("project_id")), positive_id(data.get("unit_id")), user)
    limit, offset = _page(data)
    rows = db.scalars(select(ContentMasterRevision).where(ContentMasterRevision.project_id == project.id,
        ContentMasterRevision.content_unit_id == unit.id).order_by(ContentMasterRevision.revision_no.desc())
        .offset(offset).limit(limit).execution_options(populate_existing=True)).all()
    items = []
    for row in rows:
        try:
            items.append(_preference_edit(db, user, project, unit, row))
        except HTTPException:
            continue
    return {"items": items, "limit": limit, "offset": offset,
        "next_offset": offset + len(rows) if len(rows) == limit else None}


@_write
def capture_preference(db, user, data):
    fields(data, {"project_id", "unit_id", "name", "preference", "edits"})
    project, unit = owned_unit(db, positive_id(data.get("project_id")), positive_id(data.get("unit_id")), user, mutate=True)
    selected = data.get("edits")
    if type(selected) is not list or not 2 <= len(selected) <= 20:
        raise error("capability_preference_repeated_edits_required")
    edits, seen = [], set()
    for reference in selected:
        fields(reference, PREFERENCE_EDIT_FIELDS)
        revision_id = positive_id(reference.get("master_revision_id"))
        if revision_id in seen:
            raise error("capability_preference_distinct_edits_required")
        seen.add(revision_id)
        row = db.get(ContentMasterRevision, revision_id, populate_existing=True)
        edit = _preference_edit(db, user, project, unit, row)
        if any(reference.get(key) != edit[key] or type(reference.get(key)) is not type(edit[key])
                for key in PREFERENCE_EDIT_FIELDS):
            raise error("capability_preference_source_conflict", 409)
        edits.append(edit)
    edits.sort(key=lambda edit: edit["revision_no"])
    provenance = {"source_kind": "accepted_content_edits", "project_id": project.id, "unit_id": unit.id,
        "edits": [{key: value for key, value in edit.items() if key != "created_at"} for edit in edits]}
    return _create(db, user, {"kind": "preference", "name": data.get("name"),
        "content": {"text": text(data.get("preference"), 2048, required=True).strip()}},
        scope_type="project", scope={"id": project.id}, provenance=provenance, dedupe=True, candidate_only=True)


def export_artifact(db, user, artifact_id):
    detail = get_artifact(db, user, artifact_id)
    revision = detail["current_revision"]
    return canonical({"schema": "capability.memory.export.v1", "kind": detail["kind"], "name": detail["name"],
        "content": revision["content"], "args_schema": revision["args_schema"]})


@_write
def import_artifact(db, user, data):
    fields(data, {"schema", "kind", "name", "content", "args_schema"})
    if data.get("schema") != "capability.memory.export.v1":
        raise error("capability_import_schema_invalid")
    canonical(data)
    return _create(db, user, data, scope_type="owner", scope={"id": user.id},
        provenance={"source_kind": "explicit_import"})


def installed_skills(db, user):
    from .plugin_registry import scan_skills

    _active(user)
    items = []
    for skill in scan_skills():
        try:
            item = canonical({key: skill[key] for key in ("name", "description", "version", "license", "kind", "capabilities")})
        except HTTPException:
            # External metadata is optional inventory; omit unsafe entries without echoing their content.
            pass
        else:
            item["id"] = digest({"path": skill["path"], "name": skill["name"]})
            item["source_kind"] = "installed_agent_skill"
            items.append(item)
    return {"items": items}
