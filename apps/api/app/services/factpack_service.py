"""FactPack 冲突检测（STU-033）与版本校验和（STU-042）。"""

import hashlib
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import EvidenceKind, Fact, FactPackItem, FactStatus


def conflict_key(fact: Fact) -> tuple:
    return (fact.subject or "", fact.predicate or "", fact.as_of or "", fact.unit or "")


def values_equal(a, b) -> bool:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) < 1e-9
    return a == b


def detect_conflicts(db: Session, fact_ids: list[int] | None = None) -> int:
    """同 key 不同 value 的 confirmed 事实互相标 conflict。返回冲突事实数。

    幂等：每次全量重算，被解决冲突的事实状态会被恢复为 confirmed。
    """
    stmt = select(Fact).where(Fact.status == FactStatus.confirmed.value)
    if fact_ids is not None:
        stmt = stmt.where(Fact.id.in_(fact_ids))

    facts = list(db.scalars(stmt))
    groups: dict[tuple, list[Fact]] = {}
    for fact in facts:
        groups.setdefault(conflict_key(fact), []).append(fact)

    conflicted_ids: set[int] = set()
    for group in groups.values():
        values = [f.value_json.get("value") if f.value_json else None for f in group]
        if len(values) > 1 and not all(values_equal(values[0], v) for v in values[1:]):
            conflicted_ids.update(f.id for f in group)

    changed = 0
    for fact in facts:
        target = FactStatus.conflict.value if fact.id in conflicted_ids else FactStatus.confirmed.value
        if fact.status != target:
            fact.status = target
            changed += 1
    return changed


def fact_checksum(facts: list[Fact]) -> str:
    """按 fact 内容排序计算 checksum，冻结后不可变验证依据。"""
    payload = sorted(
        [
            {
                "statement": f.statement,
                "subject": f.subject,
                "predicate": f.predicate,
                "value": f.value_json,
                "unit": f.unit,
                "as_of": f.as_of,
            }
            for f in facts
        ],
        key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True),
    )
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def evidence_snapshot(item: FactPackItem) -> dict:
    """Normalize and validate the immutable payload used by every M1 reader."""
    kind = item.evidence_kind
    if kind == EvidenceKind.legacy_untyped.value:
        raise ValueError("legacy_untyped 证据必须先完成分类，不能进入新的 M1 冻结边界")
    if kind not in {value.value for value in EvidenceKind}:
        raise ValueError(f"未知 evidence_kind: {kind}")
    fact = item.fact
    supplied = dict(item.snapshot_json or {})
    if kind in {EvidenceKind.fact.value, EvidenceKind.event.value}:
        if fact is None:
            raise ValueError(f"{kind} 证据必须绑定 Fact")
        source = fact.source_document
        snapshot = {
            "schema_version": 1,
            "evidence_kind": kind,
            "statement": fact.statement,
            "subject": fact.subject,
            "predicate": fact.predicate,
            "value": (fact.value_json or {}).get("value") if fact.value_json else None,
            "value_json": fact.value_json,
            "unit": fact.unit,
            "as_of": fact.as_of,
            "valid_from": fact.valid_from,
            "valid_to": fact.valid_to,
            "confidence": fact.confidence,
            "source_id": fact.source_document_id,
            "source_title": source.title if source else None,
            "source_url": source.source_url if source else None,
            "source_locator": fact.source_locator_json,
        }
    else:
        excerpt = supplied.get("excerpt") or supplied.get("statement")
        attribution = supplied.get("attribution")
        source_locator = supplied.get("source_locator")
        if not excerpt or not attribution or not source_locator:
            raise ValueError(f"{kind} 证据必须包含 excerpt、attribution 和 source_locator")
        snapshot = {
            "schema_version": 1,
            "evidence_kind": kind,
            "excerpt": excerpt,
            "statement": supplied.get("statement") or excerpt,
            "attribution": attribution,
            "source_title": supplied.get("source_title"),
            "source_url": supplied.get("source_url"),
            "source_locator": source_locator,
            "as_of": supplied.get("as_of"),
        }
    if item.public_use_allowed is None or item.model_use_allowed is None:
        raise ValueError("必须分别确认公开传播权限与外部模型使用权限")
    snapshot.update({
        "public_use_allowed": item.public_use_allowed,
        "model_use_allowed": item.model_use_allowed,
    })
    return snapshot


def legacy_fact_snapshot(fact: Fact, *, evidence_kind: str = "fact") -> dict:
    """Compatibility helper for old callers; new freezes use evidence_snapshot(item)."""
    source = fact.source_document
    return {
        "schema_version": 1,
        "evidence_kind": evidence_kind,
        "statement": fact.statement,
        "subject": fact.subject,
        "predicate": fact.predicate,
        "value": (fact.value_json or {}).get("value") if fact.value_json else None,
        "value_json": fact.value_json,
        "unit": fact.unit,
        "as_of": fact.as_of,
        "valid_from": fact.valid_from,
        "valid_to": fact.valid_to,
        "confidence": fact.confidence,
        "source_id": fact.source_document_id,
        "source_title": source.title if source else None,
        "source_url": source.source_url if source else None,
        "source_locator": fact.source_locator_json,
        "public_use_allowed": False,
        "model_use_allowed": False,
    }


def snapshot_checksum(snapshot: dict) -> str:
    canonical = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def pack_snapshot_checksum(items: list[FactPackItem]) -> str:
    payload = [
        {"sort_order": item.sort_order, "snapshot_checksum": item.snapshot_checksum}
        for item in sorted(items, key=lambda row: (row.sort_order, row.id or 0))
    ]
    return snapshot_checksum({"schema_version": 1, "items": payload})
