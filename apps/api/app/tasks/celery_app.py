"""Celery 应用与队列路由（EPIC-17）。

队列划分（执行计划 STU-170）：default / ingestion / llm / export。
仅当 settings.task_queue_enabled 时 API 才向 broker 分发；worker 单独进程部署。
"""

from celery import Celery

from ..config import get_settings

celery_app = Celery(
    "content_studio",
    broker=get_settings().celery_broker_url,
    backend="",
    include=["app.tasks.worker_tasks"],  # worker 启动时必须加载任务定义，否则消费到消息报 KeyError
)

celery_app.conf.update(
    task_default_queue="default",
    task_routes={
        "app.tasks.worker_tasks.run_generation_job": {"queue": "llm"},
        "app.tasks.worker_tasks.pull_connector_endpoint": {"queue": "ingestion"},
        "app.tasks.worker_tasks.scan_connector_schedules": {"queue": "default"},
    },
    # beat 周期触发扫描任务；任务内部按每个 endpoint 的 interval_minutes 决定是否拉取
    beat_schedule={
        "scan-connector-schedules": {
            "task": "app.tasks.worker_tasks.scan_connector_schedules",
            "schedule": 60.0,
        },
    },
    task_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    # 每个任务ack后再执行，worker 崩溃时任务不丢；prefetch=1 保证 llm 长任务不挤占
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
)
