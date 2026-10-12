"""Worker 任务：每个任务自建 DB session（worker 进程独立于 FastAPI 生命周期）。"""

import logging
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..models import ConnectorEndpoint, ContentJob, User
from ..services import connector_service
from ..services.generation import orchestrator
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


def _run_generation(db: Session, job_id: int, dispatch_id: str = "") -> None:
    job = db.get(ContentJob, job_id)
    if not job:
        logger.error("生成任务取消：ContentJob %s 不存在", job_id)
        return
    from ..models import JobStatus

    terminal = {JobStatus.succeeded.value, JobStatus.failed.value}
    if (dispatch_id and job.status in terminal
            and (job.usage_json or {}).get("_completed_dispatch_id") == dispatch_id):
        # acks_late 重投护栏：本次派发已完成并落标记，重投同 id 不再执行
        # （重复跑=重复计费/重复 Draft；regenerate 等显式新派发是新 id，不受影响）
        logger.warning("生成任务跳过：ContentJob %s 本次派发 %s 已完成", job_id, dispatch_id)
        return
    from ..observability import correlation_scope, log_operation

    telemetry = _telemetry_from(job.usage_json)
    started = time.perf_counter()
    error = None
    with correlation_scope(
        trace_id=telemetry.get("trace_id"), operation="generation", job_id=job.id, run_id=job.workflow_run_id,
    ):
        # worker 进程独立于 FastAPI 生命周期：跑 LLM 前刷新运行时配置覆盖
        from .. import runtime_config

        runtime_config.load_from_db(db)
        from ..services.generation.providers import LLMError, effective_llm_config, model_selection

        selected_profile = (job.usage_json or {}).get("selected_model_profile")
        try:
            with model_selection(selected_profile):
                if selected_profile:
                    config = effective_llm_config("generate")
                    from ..services.generation.providers import provider_model_name

                    expected_model = provider_model_name("generate")
                    if config["provider"] != job.model_provider or expected_model != job.model_name:
                        raise LLMError("queued_model_selection_changed")
                orchestrator.run_generation_for_job(db, job)
        except LLMError as exc:
            from ..models import JobStatus, utcnow

            error = exc
            job.status = JobStatus.failed.value
            job.error = "queued_model_selection_unavailable"
            job.finished_at = utcnow()
        except orchestrator.GenerationError as exc:
            error = exc
            # job.status/error 已由 orchestrator 落库
        finally:
            # 与终态同一次提交：重投看到的状态和令牌不会拆开
            if dispatch_id and job.status in terminal:
                job.usage_json = {**(job.usage_json or {}), "_completed_dispatch_id": dispatch_id}
            db.commit()
            log_operation("worker_generation", status=job.status, duration=time.perf_counter() - started, error=error)


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


@celery_app.task(name="app.tasks.worker_tasks.run_generation_job")
def run_generation_job(job_id: int, dispatch_id: str | None = None) -> dict:
    """dispatch_id 缺省兼容已入队的旧消息；旧消息没有令牌，不做重投去重。"""
    with SessionLocal() as db:
        _run_generation(db, job_id, dispatch_id or "")
        job = db.get(ContentJob, job_id)
        return {"job_id": job_id, "status": job.status if job else "unknown"}


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


def dispatch_generation(db: Session, job_id: int) -> str:
    """按开关决定同步执行或入队。返回最终/预期的 job 状态。

    每次派发生成唯一 dispatch_id：任务完成后把该 id 记入 usage_json，
    acks_late 下消息重投（同 id）会被终态护栏拦下，而 regenerate 这类
    显式新派发（新 id）正常执行。
    """
    import uuid

    from ..config import get_settings
    from ..models import JobStatus

    dispatch_id = uuid.uuid4().hex[:12]
    if get_settings().task_queue_enabled:
        from ..observability import persisted_telemetry

        job = db.get(ContentJob, job_id)
        if job is not None:
            job.usage_json = persisted_telemetry(job.usage_json)
            db.flush()
        run_generation_job.delay(job_id, dispatch_id)
        return JobStatus.queued.value
    _run_generation(db, job_id, dispatch_id)
    job = db.get(ContentJob, job_id)
    return job.status if job else JobStatus.failed.value


def dispatch_pull(endpoint_id: int, actor_email: str) -> str:
    """异步模式入 ingestion 队列；同步模式不该走这里（路由直接调 pull_endpoint）。"""
    pull_connector_endpoint.delay(endpoint_id, actor_email)
    return "queued"
