"""Staleness: a rerun marks the workflow steps below it stale."""

from __future__ import annotations

from sqlalchemy.orm import Session


def mark_workflow_downstream_stale(db: Session, run, node_id: str, reason: str) -> int:
    """D28：workflow 下游节点标 stale（Phase 6）。engine 的 rerun 变更检测统一走这里。"""
    from ...services.workflow_engine import _definition_of, _downstream, _steps

    downstream = set(_downstream(_definition_of(db, run), node_id))
    count = 0
    for step in _steps(db, run):
        if step.node_id in downstream and step.status in {"succeeded", "failed", "skipped"}:
            step.status = "stale"
            step.stale_reason = reason
            count += 1
    return count
