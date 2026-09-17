"""Worker 任务：每个任务自建 DB session（worker 进程独立于 FastAPI 生命周期）。"""

import logging

from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..models import ConnectorEndpoint, ContentJob, User
from ..services import connector_service
from ..services.generation import orchestrator
from .celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_generation(db: Session, job_id: int) -> None:
    job = db.get(ContentJob, job_id)
    if not job:
        logger.error("生成任务取消：ContentJob %s 不存在", job_id)
        return
    try:
        orchestrator.run_generation_for_job(db, job)
    except orchestrator.GenerationError:
        pass  # job.status/error 已由 orchestrator 落库
    db.commit()


def _run_pull(db: Session, endpoint_id: int, actor_email: str) -> None:
    endpoint = db.get(ConnectorEndpoint, endpoint_id)
    user = db.query(User).filter(User.email == actor_email).first()
    if not endpoint or not user:
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


@celery_app.task(name="app.tasks.worker_tasks.pull_connector_endpoint")
def pull_connector_endpoint(endpoint_id: int, actor_email: str) -> dict:
    with SessionLocal() as db:
        _run_pull(db, endpoint_id, actor_email)
        endpoint = db.get(ConnectorEndpoint, endpoint_id)
        return {"endpoint_id": endpoint_id, "status": endpoint.last_pull_status if endpoint else "unknown"}


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
