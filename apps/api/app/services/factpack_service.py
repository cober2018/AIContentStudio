"""FactPack 冲突检测（STU-033）与版本校验和（STU-042）。"""

import hashlib
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Fact, FactStatus


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
