"""数据保留策略：分级清理无界增长表，库体积可控（防"杂乱数据拖垮系统"）。

- llm_run：调用记录永久保留（审计），但 raw_output / parsed 超过 N 天的清空大字段
- audit_log：超过 90 天删除
- workflow_run / workflow_step：终态超过 30 天删除（steps 先删）
- export_record：超过 90 天删除
清理只按主键范围批量删，SQLite WAL 下安全；每类限量分批，避免长事务。
"""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select

from ..models import AuditLog, ExportRecord, LLMRun, WorkflowRun, WorkflowStep

logger = logging.getLogger(__name__)

DEFAULTS = {
    "llm_run_payload_days": 30,   # 超期清空大字段（行保留）
    "audit_log_days": 90,
    "workflow_run_days": 30,
    "export_record_days": 90,
    "batch": 500,
}


def _cutoff(days: int) -> datetime:
    return datetime.now(UTC) - timedelta(days=days)


def run_retention(db, cfg: dict | None = None) -> dict:
    """执行一轮清理；cfg 覆盖 DEFAULTS（配置化留给后续，当前用默认档位）。"""
    c = {**DEFAULTS, **(cfg or {})}
    stats = {}

    # 1) llm_run 大字段瘦身（行保留：审计线索 id/purpose/status/model 不动）
    cutoff = _cutoff(c["llm_run_payload_days"])
    rows = db.scalars(
        select(LLMRun.id).where(LLMRun.created_at < cutoff, LLMRun.raw_output.is_not(None)).limit(c["batch"])
    ).all()
    for rid in rows:
        run = db.get(LLMRun, rid)
        run.raw_output = None
        run.parsed_output_json = None
    stats["llm_run_payloads_cleared"] = len(rows)

    # 2) audit_log
    res = db.execute(delete(AuditLog).where(AuditLog.created_at < _cutoff(c["audit_log_days"])))
    stats["audit_log_deleted"] = res.rowcount

    # 3) workflow 终态运行（steps 级联删）
    old_runs = db.scalars(
        select(WorkflowRun.id)
        .where(WorkflowRun.finished_at.is_not(None), WorkflowRun.finished_at < _cutoff(c["workflow_run_days"]))
        .limit(c["batch"])
    ).all()
    if old_runs:
        db.execute(delete(WorkflowStep).where(WorkflowStep.run_id.in_(old_runs)))
        db.execute(delete(WorkflowRun).where(WorkflowRun.id.in_(old_runs)))
    stats["workflow_runs_deleted"] = len(old_runs)

    # 4) export_record
    res = db.execute(delete(ExportRecord).where(ExportRecord.created_at < _cutoff(c["export_record_days"])))
    stats["export_records_deleted"] = res.rowcount

    db.commit()
    logger.info("retention_sweep %s", stats)
    return stats
