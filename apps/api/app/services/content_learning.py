"""Owner-scoped learning decisions and explicit, versioned Memory promotion."""

import copy
import hashlib
import json
import unicodedata
from datetime import UTC, datetime
from functools import wraps

from fastapi import HTTPException
from sqlalchemy import func, or_, select, update
from sqlalchemy.exc import DBAPIError, IntegrityError

from ..models import (
    ContentInsight,
    ContentMemoryEntry,
    ContentMemoryRevision,
    DeliveryFeedback,
    DeliveryTarget,
    LearningCandidate,
    LearningCandidateEvidence,
    PerformanceObservation,
    PublishedContentRecord,
    utcnow,
)
from . import content_identity
from .project_authorization import authorize_project_target


def database_conflict(exc):
    driver = exc.orig
    state = getattr(driver, "sqlstate", None) or getattr(driver, "pgcode", None)
    if state in {"40P01", "40001", "55P03"}:
        return True
    sqlite_code = getattr(driver, "sqlite_errorcode", None)
    return isinstance(sqlite_code, int) and (sqlite_code & 0xFF) in {5, 6}


def atomic_write(operation):
    @wraps(operation)
    def write(db, *args, **kwargs):
        try:
            return operation(db, *args, **kwargs)
        except HTTPException:
            db.rollback()
            raise
        except DBAPIError as exc:
            db.rollback()
            if database_conflict(exc):
                raise HTTPException(409, "数据库并发冲突，请刷新后重试") from exc
            raise

    return write


def checksum(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def bound_snapshot(value):
    if len(json.dumps(value, ensure_ascii=False, default=str)) > 200000:
        raise HTTPException(422, "证据快照超过 200000 字符，请缩小证据范围")
    return value


def document(row):
    # ORM metadata is the persisted snapshot contract; relationships are never traversed.
    return {
        column.name.removesuffix("_json"): (
            (value if value.tzinfo else value.replace(tzinfo=UTC)).isoformat()
            if isinstance(value, datetime)
            else copy.deepcopy(value)
        )
        for column in row.__table__.columns
        for value in [getattr(row, column.name)]
    }


def positive_id(entity_id):
    if not isinstance(entity_id, int) or isinstance(entity_id, bool) or entity_id <= 0:
        raise HTTPException(422, "引用 ID 必须是正整数")
    return entity_id


def owned(db, model, entity_id, user):
    positive_id(entity_id)
    row = db.get(model, entity_id)
    if row is None or row.owner_user_id != user.id:
        raise HTTPException(404, "记录不存在")
    return row


def resolve_scope(db, user, scope_type="owner", scope_id=None, *, mutable=False):
    if not isinstance(scope_type, str) or scope_type not in {"owner", *content_identity.REVISION_MODELS}:
        raise HTTPException(422, "身份范围类型无效")
    if scope_id is not None:
        positive_id(scope_id)
    if scope_type == "owner":
        if scope_id is not None and scope_id != user.id:
            raise HTTPException(404, "范围不存在")
        return {"scope_type": "owner", "scope_id": user.id, "label": user.email, "ancestors": []}
    if scope_type not in content_identity.REVISION_MODELS or scope_id is None:
        raise HTTPException(422, "身份范围无效")
    entity = content_identity.owned_entity(db, user, scope_type, scope_id, mutable=mutable)
    members = [(scope_type, entity)]
    if scope_type != "brand":
        account = entity if scope_type == "account" else None
        if scope_type == "series":
            account = content_identity.owned_entity(db, user, "account", entity.account_id, mutable=mutable)
        persona_id = entity.id if scope_type == "persona" else account.persona_id
        resolved = content_identity.hierarchy(
            db,
            user,
            persona_id=persona_id,
            account_id=account.id if account else None,
            series_id=entity.id if scope_type == "series" else None,
            mutable=mutable,
        )
        members = list(resolved.members())
    if mutable:
        for kind, row in members:
            model = content_identity.REVISION_MODELS[kind][0]
            # PostgreSQL locks destination rows; SQLite already holds the candidate write lock.
            db.scalar(
                select(model).where(model.id == row.id).with_for_update().execution_options(populate_existing=True)
            )
            content_identity.owned_entity(db, user, kind, row.id, mutable=True)
    labels = [{"scope_type": kind, "scope_id": row.id, "label": row.name} for kind, row in members]
    return {
        "scope_type": scope_type,
        "scope_id": entity.id,
        "label": entity.name,
        "ancestors": [{"scope_type": "owner", "scope_id": user.id, "label": user.email}] + labels[:-1],
        **{kind + "_id": row.id for kind, row in members},
    }


def scope_origins(db, user, context):
    result = []
    if isinstance(context, dict):
        if "scope_type" in context:
            result.append(resolve_scope(db, user, context["scope_type"], context.get("scope_id")))
        for kind in content_identity.REVISION_MODELS:
            if context.get(kind + "_id"):
                result.append(resolve_scope(db, user, kind, context[kind + "_id"]))
        for child in context.values():
            if isinstance(child, (dict, list)):
                result.extend(scope_origins(db, user, child))
    elif isinstance(context, list):
        for child in context:
            result.extend(scope_origins(db, user, child))
    return result


def validate_context(db, user, value):
    """Validate embedded scope/cohort references before persisting client context."""
    if isinstance(value, list):
        for child in value:
            validate_context(db, user, child)
    elif isinstance(value, dict):
        if value.get("owner_user_id") is not None:
            positive_id(value["owner_user_id"])
            if value["owner_user_id"] != user.id:
                raise HTTPException(404, "范围不存在")
        resolved = []
        if "scope_type" in value or "scope_id" in value:
            resolved.append(resolve_scope(db, user, value.get("scope_type", "owner"), value.get("scope_id")))
        for kind in content_identity.REVISION_MODELS:
            entity_id = value.get(kind + "_id")
            if entity_id is not None:
                if not isinstance(entity_id, int) or isinstance(entity_id, bool) or entity_id <= 0:
                    raise HTTPException(422, "身份引用无效")
                resolved.append(resolve_scope(db, user, kind, entity_id))
        for scope in resolved:
            for kind in content_identity.REVISION_MODELS:
                if kind + "_id" in value and kind + "_id" in scope and value[kind + "_id"] != scope[kind + "_id"]:
                    raise HTTPException(422, "身份层级不匹配")
        if "evidence_type" in value and "entity_id" in value:
            reference(db, user, value["evidence_type"], value["entity_id"])
        for key, model in (("published_content_id", PublishedContentRecord), ("insight_id", ContentInsight)):
            if value.get(key) is not None:
                owned(db, model, value[key], user)
        if value.get("performance_observation_id") is not None:
            reference(db, user, "performance_observation", value["performance_observation_id"])
        if value.get("delivery_feedback_id") is not None:
            reference(db, user, "delivery_feedback", value["delivery_feedback_id"])
        for key, kind in (
            ("published_content_ids", "published_content"),
            ("performance_observation_ids", "performance_observation"),
            ("insight_ids", "insight"),
            ("delivery_feedback_ids", "delivery_feedback"),
        ):
            if key in value:
                if not isinstance(value[key], list):
                    raise HTTPException(422, "引用必须是 ID 列表")
                for entity_id in value[key]:
                    reference(db, user, kind, entity_id)
        for kind in content_identity.REVISION_MODELS:
            key = kind + "_ids"
            if key in value:
                if not isinstance(value[key], list):
                    raise HTTPException(422, "身份引用必须是 ID 列表")
                for entity_id in value[key]:
                    resolve_scope(db, user, kind, entity_id)
        for child in value.values():
            if isinstance(child, (dict, list)):
                validate_context(db, user, child)


def reference(db, user, evidence_type, entity_id):
    positive_id(entity_id)
    if evidence_type == "published_content":
        row = owned(db, PublishedContentRecord, entity_id, user)
    elif evidence_type == "insight":
        row = owned(db, ContentInsight, entity_id, user)
    elif evidence_type == "performance_observation":
        row = db.get(PerformanceObservation, entity_id)
        if row is None:
            raise HTTPException(404, "证据不存在")
        owned(db, PublishedContentRecord, row.published_content_id, user)
    elif evidence_type == "delivery_feedback":
        row = db.get(DeliveryFeedback, entity_id)
        target = db.get(DeliveryTarget, row.target_id) if row else None
        if target is None:
            raise HTTPException(404, "证据不存在")
        authorize_project_target(db, target, user)
        if target.authorized_by != user.email:
            raise HTTPException(404, "证据不存在")
    else:
        raise HTTPException(422, "证据类型无效")
    return bound_snapshot(document(row))


def published_samples(snapshot, evidence_type, seen=None):
    seen = seen or set()
    if evidence_type == "published_content":
        return {snapshot["id"]}
    if evidence_type == "performance_observation":
        return {snapshot["published_content_id"]}
    if evidence_type == "insight":
        result = set()
        for ref in snapshot.get("supporting_refs", []):
            identity = (ref["evidence_type"], ref["entity_id"])
            if identity in seen:
                continue
            seen.add(identity)
            if ref.get("snapshot"):
                result |= published_samples(ref["snapshot"], ref["evidence_type"], seen)
        return result
    return set()


def walk_evidence(refs, seen=None):
    if seen is None:
        seen = set()
    for ref in refs:
        identity = (ref["evidence_type"], ref["entity_id"])
        if identity in seen:
            continue
        seen.add(identity)
        yield ref
        if ref["evidence_type"] == "insight":
            snapshot = ref["snapshot"]
            yield from walk_evidence(snapshot.get("supporting_refs", []) + snapshot.get("contradicting_refs", []), seen)


def freeze_ref(db, user, ref):
    value = dict(ref)
    value["snapshot"] = reference(db, user, ref["evidence_type"], ref["entity_id"])
    value["snapshot_checksum"] = checksum(value["snapshot"])
    return value


@atomic_write
def save_insight(db, user, data):
    if (
        data["analysis_source"] != "manual"
        or data.get("provider_key") is not None
        or data.get("provider_version") is not None
    ):
        raise HTTPException(422, "人工分析不能冒充自动分析来源")
    validate_context(db, user, data["scope"])
    validate_context(db, user, data["cohort"])
    if data.get("supersedes_id"):
        owned(db, ContentInsight, data["supersedes_id"], user)
    if not data["supporting_refs"] and not data["contradicting_refs"]:
        raise HTTPException(422, "Insight 需要真实证据引用")
    support = [freeze_ref(db, user, ref) for ref in data["supporting_refs"]]
    contradict = [freeze_ref(db, user, ref) for ref in data["contradicting_refs"]]
    samples = set()
    observations, metrics = set(), set()
    for ref in walk_evidence(support + contradict):
        if ref["evidence_type"] == "published_content":
            samples.add(ref["entity_id"])
        if ref["evidence_type"] == "performance_observation":
            samples.add(ref["snapshot"]["published_content_id"])
            observations.add(ref["entity_id"])
            if (
                ref["snapshot"].get("metric_namespace")
                and ref["snapshot"].get("metric_key")
                and ref["snapshot"].get("numeric_value") is not None
            ):
                metrics.add(ref["entity_id"])
    coverage = {
        "published_content_count": len(samples),
        "observation_count": len(observations),
        "metrics": "known" if metrics else "unknown",
        "source_coverage": {
            str(pid): document(owned(db, PublishedContentRecord, pid, user))["coverage"] for pid in sorted(samples)
        },
    }
    if data.get("coverage") and data["coverage"] != coverage:
        raise HTTPException(422, "coverage 必须与实际证据一致")
    frozen_scope = {**data["scope"], "origins": scope_origins(db, user, data["scope"])}
    payload = bound_snapshot(
        {
            **data,
            "scope": frozen_scope,
            "supporting_refs": support,
            "contradicting_refs": contradict,
            "coverage": coverage,
        }
    )
    row = ContentInsight(
        owner_user_id=user.id,
        insight_type=data["insight_type"],
        statement=data["statement"],
        scope_json=frozen_scope,
        cohort_json=data["cohort"],
        coverage_json=coverage,
        supporting_refs_json=support,
        contradicting_refs_json=contradict,
        limitations_json=data["limitations"],
        confidence=data["confidence"],
        analysis_source="manual",
        checksum=checksum(payload),
        supersedes_id=data.get("supersedes_id"),
        created_by=user.email,
    )
    db.add(row)
    commit(db)
    return document(row)


def commit(db):
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "并发保存冲突，请刷新后重试") from exc


def lock_candidate(db, user, candidate_id, expected_revision=None):
    row = owned(db, LearningCandidate, candidate_id, user)
    stmt = update(LearningCandidate).where(LearningCandidate.id == row.id, LearningCandidate.owner_user_id == user.id)
    if expected_revision is not None:
        stmt = stmt.where(LearningCandidate.revision_no == expected_revision)
        values = {"revision_no": LearningCandidate.revision_no + 1}
    else:
        values = {"revision_no": LearningCandidate.revision_no}
    # Real UPDATE takes a row/write lock on both PostgreSQL and SQLite.
    result = db.execute(stmt.values(**values).execution_options(synchronize_session=False))
    if result.rowcount != 1:
        raise HTTPException(409, "学习候选版本已更新")
    db.refresh(row)
    return row


def evidence_rows(db, candidate_id):
    return db.scalars(
        select(LearningCandidateEvidence)
        .where(LearningCandidateEvidence.learning_candidate_id == candidate_id)
        .order_by(LearningCandidateEvidence.id)
    ).all()


def candidate_detail(db, row):
    result = {
        **document(row),
        "evidence": [document(e) for e in evidence_rows(db, row.id)],
        "promoted_memory_id": db.scalar(
            select(ContentMemoryEntry.id).where(ContentMemoryEntry.source_learning_candidate_id == row.id)
        ),
    }
    if row.status == "accepted" and "promotable_claim" not in row.validation_summary_json:
        try:
            frozen = trusted_frozen_decision(row)
            claim = promotable_claim(frozen)
        except HTTPException:
            # Invalid historical decisions remain readable, but cannot offer a promotion.
            return result
        result["validation_summary"]["promotable_claim"] = claim
        result["validation_summary_projection"] = {
            "derived_fields": ["promotable_claim"],
            "source_checksum": frozen["checksum"],
        }
    return result


@atomic_write
def create_candidate(db, user, data):
    validate_context(db, user, data["scope"])
    if data.get("created_from_insight_id"):
        owned(db, ContentInsight, data["created_from_insight_id"], user)
    row = LearningCandidate(
        owner_user_id=user.id,
        category=data["category"],
        title=data["title"],
        proposition=data["proposition"],
        rationale=data["rationale"],
        scope_json=data["scope"],
        confidence=data["confidence"],
        created_from_insight_id=data.get("created_from_insight_id"),
        created_by=user.email,
    )
    db.add(row)
    commit(db)
    return candidate_detail(db, row)


def collecting(row):
    if row.status != "collecting":
        raise HTTPException(409, "只有收集证据中的候选可修改")


@atomic_write
def patch_candidate(db, user, candidate_id, data):
    row = lock_candidate(db, user, candidate_id, data.pop("expected_revision"))
    collecting(row)
    validate_context(db, user, data.get("scope", {}))
    for key, value in data.items():
        setattr(row, "scope_json" if key == "scope" else key, value)
    commit(db)
    return candidate_detail(db, row)


@atomic_write
def add_evidence(db, user, candidate_id, data):
    row = lock_candidate(db, user, candidate_id, data.pop("expected_revision"))
    collecting(row)
    snapshot = reference(db, user, data["evidence_type"], data["entity_id"])
    evidence = LearningCandidateEvidence(
        learning_candidate_id=row.id,
        **data,
        snapshot_json=snapshot,
        snapshot_checksum=checksum(snapshot),
        created_by=user.email,
    )
    db.add(evidence)
    commit(db)
    return document(evidence)


@atomic_write
def submit(db, user, candidate_id, expected_revision):
    row = lock_candidate(db, user, candidate_id, expected_revision)
    collecting(row)
    if not evidence_rows(db, row.id):
        raise HTTPException(422, "请先添加证据")
    row.status = "ready_for_review"
    commit(db)
    return candidate_detail(db, row)


@atomic_write
def decide(db, user, candidate_id, data):
    row = lock_candidate(db, user, candidate_id, data["expected_revision"])
    if row.status != "ready_for_review":
        raise HTTPException(409, "只有待验证候选可作决定")
    if data["decision"] == "collecting":
        row.status = "collecting"
        commit(db)
        return candidate_detail(db, row)
    if data["validation_method"] in {"rule", "experiment"}:
        raise HTTPException(409, {"status": "capability_unavailable", "reason": "没有已验证的规则或实验执行器"})
    summary = data["validation_summary"]

    def contains_text(value):
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, (dict, list)):
            return any(contains_text(child) for child in (value.values() if isinstance(value, dict) else value))
        return False

    if not contains_text(summary):
        raise HTTPException(422, "验证摘要不能为空")
    validate_context(db, user, summary)
    snapshots, samples = [], set()
    for evidence in evidence_rows(db, row.id):
        # Reauthorize live ownership, but preserve the exact bound historical payload.
        reference(db, user, evidence.evidence_type, evidence.entity_id)
        snapshot = document(evidence)
        if not snapshot["snapshot"] or checksum(snapshot["snapshot"]) != snapshot["snapshot_checksum"]:
            raise HTTPException(409, "证据快照校验失败")
        snapshots.append(snapshot)
        if evidence.role == "support":
            samples |= published_samples(snapshot["snapshot"], evidence.evidence_type)
    if data["decision"] == "accepted" and not any(e["role"] == "support" for e in snapshots):
        raise HTTPException(422, "接受需要至少一项支持证据")
    definition = summary.get("sample_definition")
    if data["validation_method"] == "multi_sample" and (
        len(samples) < 2 or not isinstance(definition, str) or not definition.strip()
    ):
        raise HTTPException(422, "多样本验证需要独立内容样本及样本定义")
    now = utcnow()
    frozen = {
        "candidate_id": row.id,
        "proposition": row.proposition,
        "scope": copy.deepcopy(row.scope_json),
        "scope_origins": scope_origins(db, user, row.scope_json),
        "evidence": snapshots,
        "validation_method": data["validation_method"],
        "summary": summary,
        "independent_sample_ids": sorted(samples),
        "sample_count": len(samples),
        "limitations": ["single_sample"] if len(samples) < 2 else [],
        "decision": data["decision"],
        "actor": user.email,
        "decided_at": now.isoformat(),
    }
    if data["decision"] == "accepted":
        frozen["promotable_claim"] = promotable_claim(frozen)
    bound_snapshot(frozen)
    frozen["checksum"] = checksum(frozen)
    row.status = data["decision"]
    row.validation_method = data["validation_method"]
    row.validation_summary_json = frozen
    row.decided_by, row.decided_at = user.email, now
    commit(db)
    return candidate_detail(db, row)


@atomic_write
def archive_candidate(db, user, candidate_id, expected_revision):
    row = lock_candidate(db, user, candidate_id, expected_revision)
    if row.status not in {"accepted", "rejected"}:
        raise HTTPException(409, "只有已接受或已拒绝候选可归档")
    row.status = "archived"
    commit(db)


def accepted_source(db, user, candidate_id):
    row = lock_candidate(db, user, candidate_id)
    if row.status != "accepted":
        raise HTTPException(409, "内容记忆必须来自已接受候选")
    return row, trusted_frozen_decision(row)


def trusted_frozen_decision(row):
    frozen = copy.deepcopy(row.validation_summary_json)
    digest = frozen.pop("checksum", None)
    if (
        not digest
        or checksum(frozen) != digest
        or frozen.get("decision") != "accepted"
        or not any(e.get("role") == "support" for e in frozen.get("evidence", []))
    ):
        raise HTTPException(409, "候选缺少可信的冻结验证记录")
    frozen["checksum"] = digest
    return frozen


def memory_revisions(db, memory_id):
    return (
        select(ContentMemoryRevision)
        .where(ContentMemoryRevision.memory_entry_id == memory_id)
        .order_by(ContentMemoryRevision.revision_no.desc())
    )


def memory_detail(db, row):
    current = db.scalar(memory_revisions(db, row.id).limit(1))
    scope_id = getattr(row, row.scope_type + "_id", None) if row.scope_type != "owner" else row.owner_user_id
    initial = db.scalar(
        select(ContentMemoryRevision).where(
            ContentMemoryRevision.memory_entry_id == row.id, ContentMemoryRevision.revision_no == 1
        )
    )
    destination = initial.evidence_snapshot_json.get("destination_scope", {}) if initial else {}
    return {
        **document(row),
        "scope_id": scope_id,
        "scope_origin": {**copy.deepcopy(destination), "relationship": "exact"},
        "current_revision": document(current) if current else None,
    }


def append_memory_revision(db, user, entry, data, source, previous=None, destination_scope=None):
    source = {
        "candidate": copy.deepcopy(source),
        "destination_scope": copy.deepcopy(
            previous.evidence_snapshot_json["destination_scope"] if previous else destination_scope
        ),
    }
    payload = {
        "statement": data["statement"],
        "applicability": data["applicability"],
        "limitations": data["limitations"],
        "source_learning_candidate_id": data["source_learning_candidate_id"],
        "evidence_snapshot": source,
    }
    row = ContentMemoryRevision(
        memory_entry_id=entry.id,
        revision_no=previous.revision_no + 1 if previous else 1,
        parent_revision_id=previous.id if previous else None,
        statement=data["statement"],
        applicability_json=data["applicability"],
        limitations_json=data["limitations"],
        source_learning_candidate_id=data["source_learning_candidate_id"],
        evidence_snapshot_json=copy.deepcopy(source),
        checksum=checksum(payload),
        created_by=user.email,
    )
    db.add(row)
    return row


def normalized_claim(statement):
    return " ".join(unicodedata.normalize("NFKC", statement).split())


def promotable_claim(frozen):
    identity_keys = {"scope_type", "scope_id", "origins", "owner_user_id"} | {
        kind + "_id" for kind in content_identity.REVISION_MODELS
    }
    required_applicability = {key: value for key, value in frozen["scope"].items() if key not in identity_keys}
    validated_applicability = frozen["summary"].get("applicability", {})
    if not isinstance(validated_applicability, dict):
        raise HTTPException(409, "冻结验证记录中的适用条件格式无效")
    applicability = copy.deepcopy(required_applicability)
    for key, value in validated_applicability.items():
        if key in applicability and applicability[key] != value:
            raise HTTPException(409, "候选范围与冻结验证适用条件冲突")
        applicability[key] = copy.deepcopy(value)
    limitation_sets = [frozen.get("limitations", []), frozen["summary"].get("limitations", [])]
    for evidence in walk_evidence(frozen["evidence"]):
        if evidence["evidence_type"] == "insight":
            limitation_sets.append(evidence["snapshot"].get("limitations", []))
    result, seen = [], set()
    for limitations in limitation_sets:
        if not isinstance(limitations, list) or any(not isinstance(value, str) for value in limitations):
            raise HTTPException(409, "冻结验证记录中的局限格式无效")
        for value in limitations:
            key = normalized_claim(value)
            if key not in seen:
                seen.add(key)
                result.append(value)
    return {"statement": frozen["proposition"], "applicability": applicability, "limitations": result}


def memory_claim_gate(frozen, data, destination, previous=None):
    claim = promotable_claim(frozen)
    # Exact normalization is auditable; a different claim requires its own accepted proposition.
    if normalized_claim(data["statement"]) != normalized_claim(claim["statement"]):
        raise HTTPException(409, "记忆声明必须与来源候选的冻结命题一致；新声明需要匹配的新接受候选")
    destination_refs = {(destination["scope_type"], destination["scope_id"])} | {
        (scope["scope_type"], scope["scope_id"]) for scope in destination["ancestors"]
    }
    for origin in frozen.get("scope_origins", []):
        required_refs = [origin, *origin.get("ancestors", [])]
        if any((scope["scope_type"], scope["scope_id"]) not in destination_refs for scope in required_refs):
            raise HTTPException(409, "记忆目标超出了来源候选的已验证身份范围")
    restrictions = [claim["applicability"]]
    limitation_sets = [claim["limitations"]]
    if previous:
        restrictions.append(previous.applicability_json)
        limitation_sets.append(previous.limitations_json)
    for restriction in restrictions:
        if any(
            key not in data["applicability"] or data["applicability"][key] != value
            for key, value in restriction.items()
        ):
            raise HTTPException(409, "记忆适用条件必须保留已验证范围及此前限制")
    for limitations in limitation_sets:
        if not {normalized_claim(value) for value in limitations}.issubset(
            {normalized_claim(value) for value in data["limitations"]}
        ):
            raise HTTPException(409, "记忆不得删除已验证或此前保存的局限")


@atomic_write
def promote(db, user, candidate_id, data):
    _, frozen = accepted_source(db, user, candidate_id)
    scope = resolve_scope(db, user, data["scope_type"], data.get("scope_id"), mutable=True)
    memory_claim_gate(frozen, data, scope)
    validate_context(db, user, data["applicability"])
    payload = {**data, "source_learning_candidate_id": candidate_id}
    payload["scope_id"] = scope["scope_id"]
    digest = checksum(payload)
    existing = db.scalar(
        select(ContentMemoryEntry)
        .where(
            ContentMemoryEntry.owner_user_id == user.id,
            or_(
                ContentMemoryEntry.source_learning_candidate_id == candidate_id,
                ContentMemoryEntry.promotion_idempotency_key == data["idempotency_key"],
            ),
        )
        .with_for_update()
    )
    if existing:
        if (
            existing.source_learning_candidate_id != candidate_id
            or existing.promotion_checksum != digest
            or existing.promotion_idempotency_key != data["idempotency_key"]
        ):
            raise HTTPException(409, "候选已提升或幂等请求内容不一致")
        result = memory_detail(db, existing)
        db.rollback()
        return result
    entry = ContentMemoryEntry(
        owner_user_id=user.id,
        scope_type=data["scope_type"],
        memory_type=data["memory_type"],
        source_learning_candidate_id=candidate_id,
        promotion_idempotency_key=data["idempotency_key"],
        promotion_checksum=digest,
        **{key: value for key, value in scope.items() if key in {"brand_id", "persona_id", "account_id", "series_id"}},
    )
    db.add(entry)
    try:
        db.flush()
        append_memory_revision(
            db, user, entry, {**data, "source_learning_candidate_id": candidate_id}, frozen, destination_scope=scope
        )
        commit(db)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "并发提升冲突，请重试相同请求") from exc
    return memory_detail(db, entry)


@atomic_write
def revise_memory(db, user, memory_id, data):
    entry = owned(db, ContentMemoryEntry, memory_id, user)
    # Every path that needs these locks acquires candidate -> identity -> memory.
    _, frozen = accepted_source(db, user, data["source_learning_candidate_id"])
    scope_id = getattr(entry, entry.scope_type + "_id", None)
    scope = resolve_scope(db, user, entry.scope_type, scope_id, mutable=True)
    # The no-op write serializes archive and revision saves before reading the tip.
    db.execute(
        update(ContentMemoryEntry).where(ContentMemoryEntry.id == entry.id).values(status=ContentMemoryEntry.status)
    )
    db.refresh(entry)
    if entry.status != "active":
        raise HTTPException(409, "已归档内容记忆只可查看")
    previous = db.scalar(memory_revisions(db, entry.id).limit(1))
    if data["expected_revision"] != (previous.revision_no if previous else 0):
        raise HTTPException(409, "内容记忆版本已更新")
    memory_claim_gate(frozen, data, scope, previous)
    validate_context(db, user, data["applicability"])
    row = append_memory_revision(db, user, entry, data, frozen, previous)
    commit(db)
    return document(row)


@atomic_write
def archive_memory(db, user, memory_id):
    entry = owned(db, ContentMemoryEntry, memory_id, user)
    db.execute(update(ContentMemoryEntry).where(ContentMemoryEntry.id == entry.id).values(status="archived"))
    commit(db)


def page(db, stmt, limit, offset, serializer=document):
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
    return {
        "items": [serializer(row) for row in db.scalars(stmt.limit(limit).offset(offset))],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


def list_memory(db, user, limit, offset, scope_type=None, scope_id=None, include_ancestors=False, status="active"):
    stmt = select(ContentMemoryEntry).where(ContentMemoryEntry.owner_user_id == user.id)
    origins = {}
    if scope_type:
        scope = resolve_scope(db, user, scope_type, scope_id)
        selections = [scope] + (scope["ancestors"] if include_ancestors else [])
        clauses = []
        for selection in selections:
            kind, entity_id = selection["scope_type"], selection["scope_id"]
            clause = ContentMemoryEntry.scope_type == kind
            if kind != "owner":
                clause = clause & (getattr(ContentMemoryEntry, kind + "_id") == entity_id)
            clauses.append(clause)
            origins[(kind, entity_id)] = {
                "scope_type": kind,
                "scope_id": entity_id,
                "label": selection["label"],
                "relationship": "exact" if kind == scope_type and entity_id == scope["scope_id"] else "ancestor",
            }
        stmt = stmt.where(or_(*clauses))
    elif scope_id is not None:
        raise HTTPException(422, "scope_id 需要 scope_type")
    if status:
        stmt = stmt.where(ContentMemoryEntry.status == status)

    def serialize(row):
        detail = memory_detail(db, row)
        origin = origins.get((row.scope_type, detail["scope_id"]))
        if origin:
            detail["scope_origin"]["relationship"] = origin["relationship"]
        return detail

    return page(db, stmt.order_by(ContentMemoryEntry.id.desc()), limit, offset, serialize)
