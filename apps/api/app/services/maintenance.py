"""进程内周期维护：僵尸 running 回收、保留清理、SQLite WAL checkpoint。

Celery beat 在默认部署（task_queue_enabled=false）不会运行，retention 清理因此
从未执行；崩溃/异常留下的 running 状态也无人回收。本模块在 API 进程内用一条
守护线程兜底，周期可配（maintenance_interval_seconds=0 关闭）。

只回收「running」：queued 是合法的排队积压，provider 任务的 unknown 按
「不确定结果不重试」的既有口径永远不动。
"""

import logging
import threading
import time
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import SessionLocal
from ..models import AuditLog, WorkflowRun, WorkflowStep, utcnow

logger = logging.getLogger(__name__)

_FIRST_CYCLE_DELAY_SECONDS = 30
_AUDIT_ID_LIMIT = 50

_stop = threading.Event()
_thread: threading.Thread | None = None


def reap_stale_running(db: Session, *, stale_seconds: int) -> dict:
    """把超过阈值的 running WorkflowRun/WorkflowStep 置为 failed。

    阈值需大于任何合法执行时长（媒体 305s 上限等），
    默认 1800s；只做状态收口，不删除任何业务数据。
    """
    if stale_seconds <= 0:
        return {"disabled": True}
    cutoff = utcnow() - timedelta(seconds=stale_seconds)
    reaped: dict[str, list[int]] = {}

    steps = db.scalars(
        select(WorkflowStep).where(
            WorkflowStep.status == "running",
            WorkflowStep.started_at.is_not(None),
            WorkflowStep.started_at < cutoff,
        )
    ).all()
    for step in steps:
        step.status = "failed"
        step.finished_at = utcnow()
        step.error = step.error or f"reaped:stale_running_after_{stale_seconds}s"
    if steps:
        reaped["workflow_steps"] = [step.id for step in steps]

    runs = db.scalars(
        select(WorkflowRun).where(
            WorkflowRun.status == "running",
            WorkflowRun.started_at.is_not(None),
            WorkflowRun.started_at < cutoff,
        )
    ).all()
    for run in runs:
        run.status = "failed"
        run.finished_at = utcnow()
        run.error = run.error or f"reaped:stale_running_after_{stale_seconds}s"
    if runs:
        reaped["workflow_runs"] = [run.id for run in runs]

    if not reaped:
        return {}
    db.add(AuditLog(
        event="maintenance.stale_running_reaped",
        actor="system:maintenance",
        entity_type="maintenance",
        detail_json={key: value[:_AUDIT_ID_LIMIT] for key, value in reaped.items()},
    ))
    db.commit()
    logger.warning("reaped stale running state: %s", reaped)
    return reaped


def _wal_checkpoint() -> str:
    if not get_settings().database_url.startswith("sqlite"):
        return "skipped"
    from ..db import engine

    with engine.connect() as conn:
        row = conn.exec_driver_sql("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
    # (busy, log, checkpointed)；busy=0 表示完成截断
    return "truncated" if row and row[0] == 0 else "busy_or_deferred"


def run_maintenance_cycle() -> dict:
    from . import retention

    stats: dict = {}
    started = time.perf_counter()
    with SessionLocal() as db:
        try:
            stats["reaped"] = reap_stale_running(db, stale_seconds=get_settings().stale_running_seconds)
        except Exception:
            db.rollback()
            logger.exception("stale running reap failed")
        try:
            stats["retention"] = retention.run_retention(db)
        except Exception:
            db.rollback()
            logger.exception("retention sweep failed")
    try:
        stats["wal_checkpoint"] = _wal_checkpoint()
    except Exception:
        logger.exception("wal checkpoint failed")
    from ..observability import log_operation

    log_operation("maintenance_cycle", status="ok", duration=time.perf_counter() - started)
    return stats


def _loop(interval: int) -> None:
    if _stop.wait(_FIRST_CYCLE_DELAY_SECONDS):
        return
    while True:
        cycle_started = time.perf_counter()
        try:
            run_maintenance_cycle()
        except Exception:
            logger.exception("maintenance cycle crashed")
        remaining = max(interval - (time.perf_counter() - cycle_started), 1.0)
        if _stop.wait(remaining):
            return


def start() -> None:
    """启动维护线程（幂等）；maintenance_interval_seconds<=0 时为空操作。"""
    global _thread
    interval = get_settings().maintenance_interval_seconds
    if interval <= 0:
        return
    if _thread is not None and _thread.is_alive():
        return
    _stop.clear()
    _thread = threading.Thread(target=_loop, args=(interval,), name="studio-maintenance", daemon=True)
    _thread.start()


def stop() -> None:
    _stop.set()
    thread = _thread
    if thread is not None and thread.is_alive():
        thread.join(timeout=5)
