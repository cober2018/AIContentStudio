"""Worker 任务：每个任务自建 DB session（worker 进程独立于 FastAPI 生命周期）。"""

import logging
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..models import ConnectorEndpoint, User
from ..services import connector_service
from .celery_app import celery_app

logger = logging.getLogger(__name__)


def _telemetry_from(payload: dict | None) -> dict:
    value = (payload or {}).get("_telemetry")
    return value if isinstance(value, dict) else {}


@celery_app.task(name="app.tasks.worker_tasks.retention_sweep")
def retention_sweep() -> dict:
    from ..services.retention import run_retention

    with SessionLocal() as db:
        return run_retention(db)


def _run_pull(db: Session, endpoint_id: int, actor_email: str) -> None:
    from ..observability import correlation_scope, log_operation

    started = time.perf_counter()
    error = None
    endpoint = db.get(ConnectorEndpoint, endpoint_id)
    user = db.query(User).filter(User.email == actor_email).first()
    if user is None:
        # 定时拉取的 actor（"scheduler"）不是真实登录用户：兜底建系统账号，调度链路不该因此断
        user = User(email=actor_email, name="系统调度", role="editor")
        db.add(user)
        db.commit()
    if not endpoint:
        logger.error("拉取任务取消：endpoint=%s user=%s 缺失", endpoint_id, actor_email)
        return
    with correlation_scope(operation="connector_pull", actor=actor_email, endpoint_id=endpoint_id):
        try:
            connector_service.pull_endpoint(db, endpoint, user)
        except connector_service.ConnectorError as exc:
            error = exc
            connector_service.record_pull_failure(db, endpoint, str(exc))
        except Exception as exc:  # noqa: BLE001 网络等未知失败同样回写 endpoint
            error = exc
            connector_service.record_pull_failure(db, endpoint, str(exc))
        finally:
            log_operation("worker_connector_pull", status=endpoint.last_pull_status or "unknown", duration=time.perf_counter() - started, error=error)


def _advance_workflow_run(db: Session, run_id: int) -> str:
    """R2-B1：异步模式下推进 WorkflowRun（主生产入口经 Content Harness）。"""
    from ..models import WorkflowRun
    from ..services import workflow_engine

    run = db.get(WorkflowRun, run_id)
    if not run:
        return "unknown"
    from ..observability import correlation_scope, log_operation

    started = time.perf_counter()
    telemetry = _telemetry_from(run.context_json)
    error = None
    user = db.query(User).filter(User.email == "workflow@studio.local").first()
    if user is None:
        user = User(email="workflow@studio.local", name="工作流执行", role="editor")
        db.add(user)
        db.commit()
    from .. import runtime_config

    runtime_config.load_from_db(db)
    with correlation_scope(
        trace_id=telemetry.get("trace_id"), operation="workflow", run_id=run.id, unit_id=run.content_unit_id,
    ):
        try:
            run = workflow_engine.advance(db, run, user)
            return run.status
        except Exception as exc:  # noqa: BLE001 Worker failures must remain opaque at the task boundary.
            from ..observability import safe_error_category

            error = exc
            category = safe_error_category(exc)
            logger.error("workflow run %s 推进失败：%s", run_id, category)
            # 立即收口 running 状态：advance 在执行前已把 run/step 置 running 并提交，
            # 异常穿透会让它们悬挂到 30 分钟后的维护回收器才被处理
            db.rollback()
            try:
                from ..models import WorkflowStep, utcnow

                run = db.get(WorkflowRun, run_id)
                if run is not None and run.status == "running":
                    run.status = "failed"
                    run.finished_at = utcnow()
                    run.error = f"worker_error:{category}"
                    for step in db.scalars(select(WorkflowStep).where(
                            WorkflowStep.run_id == run_id, WorkflowStep.status == "running")).all():
                        step.status = "failed"
                        step.finished_at = utcnow()
                        step.error = step.error or f"worker_error:{category}"
                    db.commit()
            except Exception:
                db.rollback()
                logger.exception("workflow run %s 异常后状态收口失败", run_id)
            return f"error:{category}"
        finally:
            log_operation("worker_workflow", status=run.status, duration=time.perf_counter() - started, error=error)


@celery_app.task(name="app.tasks.worker_tasks.advance_workflow_run")
def advance_workflow_run(run_id: int) -> dict:
    with SessionLocal() as db:
        status = _advance_workflow_run(db, run_id)
        return {"run_id": run_id, "status": status}


@celery_app.task(name="app.tasks.worker_tasks.pull_connector_endpoint")
def pull_connector_endpoint(endpoint_id: int, actor_email: str) -> dict:
    with SessionLocal() as db:
        _run_pull(db, endpoint_id, actor_email)
        endpoint = db.get(ConnectorEndpoint, endpoint_id)
        return {"endpoint_id": endpoint_id, "status": endpoint.last_pull_status if endpoint else "unknown"}


@celery_app.task(name="app.tasks.worker_tasks.scan_connector_schedules")
def scan_connector_schedules() -> dict:
    """beat 每分钟触发：找到达到 interval_minutes 间隔的 endpoint，分发给 ingestion 队列。"""
    from datetime import UTC, datetime

    def _aware(dt: datetime) -> datetime:
        # SQLite 可能读回 naive datetime，统一按 UTC 处理
        return dt if dt.tzinfo else dt.replace(tzinfo=UTC)

    with SessionLocal() as db:
        now = datetime.now(UTC)
        due_ids: list[int] = []
        for endpoint in db.query(ConnectorEndpoint).all():
            if not endpoint.interval_minutes or endpoint.interval_minutes <= 0:
                continue
            if not endpoint.connector or not endpoint.connector.is_active:
                continue
            if endpoint.last_pull_at is None or (
                now - _aware(endpoint.last_pull_at)
            ).total_seconds() >= endpoint.interval_minutes * 60:
                due_ids.append(endpoint.id)
        for endpoint_id in due_ids:
            pull_connector_endpoint.delay(endpoint_id, "scheduler")
        return {"scanned_at": now.isoformat(), "dispatched": due_ids}


# ---------- 供 API 路由调用的分发封装（同步/异步双模式） ----------


def dispatch_pull(endpoint_id: int, actor_email: str) -> str:
    """异步模式入 ingestion 队列；同步模式不该走这里（路由直接调 pull_endpoint）。"""
    pull_connector_endpoint.delay(endpoint_id, actor_email)
    return "queued"


@celery_app.task(name="app.tasks.worker_tasks.scan_persona_discovery")
def scan_persona_discovery():
    from ..models import DiscoverySource, SystemSetting, utcnow
    from ..services.discovery_runtime import schedule_due

    with SessionLocal() as db:
        from ..models import PersonaResearchRun
        from ..services.discovery_catchup import prerequisite, scan

        jobs = scan(db)
        ids = schedule_due(db)
        for run_id in ids:
            run = db.get(PersonaResearchRun, run_id)
            if run.kind != "daily" or prerequisite(db, run):
                process_persona_research.apply_async(args=[run_id], queue="llm")
        validations = db.scalars(select(DiscoverySource.id).where(
            DiscoverySource.evidence_json["management"]["validation"]["state"].as_string().in_(["pending", "running"]),
            DiscoverySource.next_due_at <= utcnow(),
            (DiscoverySource.lease_until.is_(None)) | (DiscoverySource.lease_until < utcnow())).limit(20)).all()
        for source_id in validations:
            validate_discovery_source.apply_async(args=[source_id], queue="ingestion")
        for receipt_id in jobs:
            collect_discovery_catchup.apply_async(args=[receipt_id], queue="ingestion")
        row = db.get(SystemSetting, "discovery.heartbeat")
        if row is None:
            row = SystemSetting(key="discovery.heartbeat")
            db.add(row)
        row.value = {"last_scan_at": utcnow().isoformat(), "origin": "celery_beat", "queued_runs": len(ids)}
        db.commit()
        return {"runs": len(ids), "sources": len(jobs), "validations": len(validations)}


@celery_app.task(name="app.tasks.worker_tasks.process_persona_research")
def process_persona_research(run_id):
    from .. import runtime_config
    from ..services.daily_opportunities import execute_research

    with SessionLocal() as db:
        runtime_config.load_from_db(db)
        return execute_research(db, run_id, execution_origin="celery_worker", task_id=process_persona_research.request.id)


@celery_app.task(name="app.tasks.worker_tasks.collect_discovery_source")
def collect_discovery_source(source_id):
    from ..services.discovery_ingestion import collect_source

    with SessionLocal() as db:
        return collect_source(db, source_id)


@celery_app.task(name="app.tasks.worker_tasks.validate_discovery_source")
def validate_discovery_source(source_id):
    from ..services.discovery_sources import validate_source

    with SessionLocal() as db:
        return validate_source(db, source_id)


@celery_app.task(name="app.tasks.worker_tasks.collect_discovery_catchup")
def collect_discovery_catchup(receipt_id):
    from ..services.discovery_catchup import step

    with SessionLocal() as db:
        return step(db, receipt_id)
