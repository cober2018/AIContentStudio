"""数据保留策略：分级清理无界增长表，库体积可控（防"杂乱数据拖垮系统"）。

- llm_run：调用记录永久保留（审计），但 raw_output / parsed 超过 N 天的清空大字段
- audit_log：超过 90 天删除；未处理的项目素材孤儿字节候选例外
- workflow_run / workflow_step：终态超过 30 天删除（steps 先删）
- export_record：超过 90 天删除
清理只按主键范围批量删，SQLite WAL 下安全；每类限量分批，避免长事务。
"""

import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import delete, select

from ..models import (
    AssetMedia,
    AuditLog,
    ContentAsset,
    ContentJob,
    ContentMasterRevision,
    DataSnapshot,
    DraftMedia,
    ExportRecord,
    LLMRun,
    MaterialRevision,
    ProjectWorkflowOutput,
    WorkflowRun,
    WorkflowStep,
    WorkflowStepAttempt,
)

logger = logging.getLogger(__name__)

DEFAULTS = {
    "llm_run_payload_days": 30,   # 超期清空大字段（行保留）
    "audit_log_days": 90,
    "material_orphan_grace_days": 1,
    "workflow_run_days": 30,
    "export_record_days": 90,
    "batch": 500,
}


def _cutoff(days: int) -> datetime:
    return datetime.now(UTC) - timedelta(days=days)


def _process_material_orphan_candidates(db, *, cutoff: datetime, batch: int) -> dict:
    from .material_byte_lock import locked_hash
    from .material_storage import provider

    rows = db.scalars(select(AuditLog).where(AuditLog.event == "material.upload_orphan_candidate", AuditLog.created_at < cutoff).order_by(AuditLog.id).limit(batch)).all()
    removed = referenced = invalid = 0
    storage = provider()
    for row in rows:
        detail = row.detail_json or {}
        raw_path = detail.get("file_path")
        content_hash = detail.get("content_hash")
        relative = Path(raw_path) if isinstance(raw_path, str) else Path()
        safe = (
            isinstance(content_hash, str) and len(content_hash) == 64
            and relative.parts[:2] == ("material", content_hash[:2])
            and relative.name.startswith(content_hash + ".")
            and relative.as_posix().startswith("material/")
        )
        if not safe:
            invalid += 1
            row.event = "material.upload_orphan_resolved"
            row.detail_json = {**detail, "cleanup_status": "invalid_path_not_deleted"}
            db.commit()
            continue
        with locked_hash(content_hash):
            path_value = str(relative)
            in_use = any((
                db.scalar(select(MaterialRevision.id).where(MaterialRevision.file_path == path_value).limit(1)),
                db.scalar(select(DraftMedia.id).where(DraftMedia.file_path == path_value).limit(1)),
                db.scalar(select(AssetMedia.id).where(AssetMedia.file_path == path_value).limit(1)),
            ))
            if in_use:
                referenced += 1
                row.detail_json = {**detail, "cleanup_status": "retained_referenced"}
            else:
                try:
                    storage.delete_if_unreferenced(relative.as_posix(), expected_hash=content_hash)
                except Exception:  # noqa: BLE001 Cleanup leaves unresolved evidence on any storage failure.
                    logger.warning("material_orphan_cleanup_failed audit_id=%s", row.id)
                    continue
                removed += 1
                row.detail_json = {**detail, "cleanup_status": "removed_or_missing"}
        row.event = "material.upload_orphan_resolved"
        db.commit()
    return {"material_orphan_bytes_removed": removed, "material_orphan_referenced": referenced, "material_orphan_invalid": invalid}


def run_retention(db, cfg: dict | None = None) -> dict:
    """执行一轮清理；cfg 覆盖 DEFAULTS（配置化留给后续，当前用默认档位）。"""
    c = {**DEFAULTS, **(cfg or {})}
    stats = {}

    # Resolve orphan bytes before taking any database write locks.
    stats.update(_process_material_orphan_candidates(db, cutoff=_cutoff(c["material_orphan_grace_days"]), batch=c["batch"]))

    # 1) llm_run 大字段瘦身（行保留：审计线索 id/purpose/status/model 不动）
    cutoff = _cutoff(c["llm_run_payload_days"])
    rows = db.scalars(
        select(LLMRun.id).where(LLMRun.created_at < cutoff, LLMRun.raw_output.is_not(None)).limit(c["batch"])
    ).all()
    for rid in rows:
        run = db.get(LLMRun, rid)
        run.raw_output = None
        # Validated AI receipts remain live provenance for immutable Masters and Variants.
        if run.purpose not in {"text_master_edit", "channel_variant_adapt"}:
            run.parsed_output_json = None
    stats["llm_run_payloads_cleared"] = len(rows)

    # 2) audit_log: unresolved byte candidates survive normal log expiry.
    res = db.execute(delete(AuditLog).where(AuditLog.created_at < _cutoff(c["audit_log_days"]), AuditLog.event != "material.upload_orphan_candidate"))
    stats["audit_log_deleted"] = res.rowcount

    # Immutable project/output/attempt lineage must survive the legacy sweep.
    old_runs = db.scalars(
        select(WorkflowRun.id)
        .where(WorkflowRun.finished_at.is_not(None), WorkflowRun.finished_at < _cutoff(c["workflow_run_days"]))
        .where(WorkflowRun.content_unit_id.is_(None))
        .where(~select(WorkflowStepAttempt.id).where(WorkflowStepAttempt.run_id == WorkflowRun.id).exists())
        .where(~select(ContentAsset.id).where(ContentAsset.workflow_run_id == WorkflowRun.id).exists())
        .where(~select(ContentJob.id).where(ContentJob.workflow_run_id == WorkflowRun.id).exists())
        .where(~select(ContentMasterRevision.id).where(ContentMasterRevision.origin_workflow_run_id == WorkflowRun.id).exists())
        .where(~select(DataSnapshot.id).where(DataSnapshot.run_id == WorkflowRun.id).exists())
        .where(~select(ProjectWorkflowOutput.id).where(ProjectWorkflowOutput.run_id == WorkflowRun.id).exists())
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
