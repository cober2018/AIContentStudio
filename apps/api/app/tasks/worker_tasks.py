"""Worker 任务：每个任务自建 DB session（worker 进程独立于 FastAPI 生命周期）。"""

import logging

from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..models import ConnectorEndpoint, ContentJob, User
from ..services import connector_service
from ..services.generation import orchestrator
from .celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.worker_tasks.retention_sweep")
def retention_sweep() -> dict:
    from ..services.retention import run_retention

    with SessionLocal() as db:
        return run_retention(db)


def _run_generation(db: Session, job_id: int) -> None:
    job = db.get(ContentJob, job_id)
    if not job:
        logger.error("生成任务取消：ContentJob %s 不存在", job_id)
        return
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
    except LLMError:
        from ..models import JobStatus, utcnow

        job.status = JobStatus.failed.value
        job.error = "queued_model_selection_unavailable"
        job.finished_at = utcnow()
    except orchestrator.GenerationError:
        pass  # job.status/error 已由 orchestrator 落库
    db.commit()


def _run_pull(db: Session, endpoint_id: int, actor_email: str) -> None:
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
    try:
        connector_service.pull_endpoint(db, endpoint, user)
    except connector_service.ConnectorError as exc:
        connector_service.record_pull_failure(db, endpoint, str(exc))
    except Exception as exc:  # noqa: BLE001 网络等未知失败同样回写 endpoint
        connector_service.record_pull_failure(db, endpoint, str(exc))


@celery_app.task(name="app.tasks.worker_tasks.run_generation_job")
def run_generation_job(job_id: int) -> dict:
    with SessionLocal() as db:
        _run_generation(db, job_id)
        job = db.get(ContentJob, job_id)
        return {"job_id": job_id, "status": job.status if job else "unknown"}


def _advance_workflow_run(db: Session, run_id: int) -> str:
    """R2-B1：异步模式下推进 WorkflowRun（主生产入口经 Content Harness）。"""
    from ..models import WorkflowRun
    from ..services import workflow_engine

    run = db.get(WorkflowRun, run_id)
    if not run:
        return "unknown"
    user = db.query(User).filter(User.email == "workflow@studio.local").first()
    if user is None:
        user = User(email="workflow@studio.local", name="工作流执行", role="editor")
        db.add(user)
        db.commit()
    from .. import runtime_config

    runtime_config.load_from_db(db)
    try:
        run = workflow_engine.advance(db, run, user)
        return run.status
    except Exception as exc:
        logger.exception("workflow run %s 推进异常", run_id)
        return f"error: {exc}"[:100]


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
    """按开关决定同步执行或入队。返回最终/预期的 job 状态。"""
    from ..config import get_settings
    from ..models import JobStatus

    if get_settings().task_queue_enabled:
        run_generation_job.delay(job_id)
        return JobStatus.queued.value
    _run_generation(db, job_id)
    job = db.get(ContentJob, job_id)
    return job.status if job else JobStatus.failed.value


def dispatch_pull(endpoint_id: int, actor_email: str) -> str:
    """异步模式入 ingestion 队列；同步模式不该走这里（路由直接调 pull_endpoint）。"""
    pull_connector_endpoint.delay(endpoint_id, actor_email)
    return "queued"
