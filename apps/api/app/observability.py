"""可观测性（EPIC-17）：/health 探针、/metrics Prometheus 文本指标、trace_id 结构化日志。"""

import json
import logging
import queue
import re
import threading
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

from sqlalchemy import text

logger = logging.getLogger("studio.request")

# 进程内计数器：足够 V1 单进程部署；多副本时由外部聚合或换 prometheus_client
_METRICS: dict[str, float] = {}
START_TIME = time.time()

_CORRELATION: ContextVar[dict[str, object] | None] = ContextVar("studio_correlation", default=None)
_CORRELATION_KEYS = frozenset({
    "trace_id", "actor", "project_id", "unit_id", "run_id", "attempt_id",
    "job_id", "master_revision_id", "variant_revision_id", "candidate_id",
    "target_id", "endpoint_id", "capability_key", "capability_version", "operation",
})
_HTTP_METHODS = frozenset({"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "TRACE", "CONNECT"})


def _bounded_value(key: str, value: object) -> object | None:
    if key.endswith("_id") and key != "trace_id":
        return value if type(value) is int and 0 <= value <= 2**63 - 1 else None
    if not isinstance(value, str) or value.lower().startswith(("sk-", "bearer")):
        return None
    patterns = {
        "trace_id": r"[A-Za-z0-9_-]{1,64}",
        "actor": r"[A-Za-z0-9][A-Za-z0-9_.+-]{0,127}@[A-Za-z0-9.-]{1,125}",
        "operation": r"[a-z][a-z0-9_-]{0,79}",
        "capability_key": r"[a-z][a-z0-9_-]*(?:\.[a-z][a-z0-9_-]*){1,8}",
        "capability_version": r"[A-Za-z0-9_-]{1,32}(?:\.[0-9]{1,16}){0,3}",
    }
    if len(value) <= 255 and key in patterns and re.fullmatch(patterns[key], value):
        return value
    return None


def safe_telemetry(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        return {}
    return {key: bounded for key, item in value.items()
            if key in _CORRELATION_KEYS and (bounded := _bounded_value(key, item)) is not None}


def current_correlation() -> dict[str, object]:
    """Return only bounded correlation metadata, never request content or secrets."""
    return safe_telemetry(_CORRELATION.get())


def persisted_telemetry(payload: dict | None) -> dict:
    """Attach safe worker handoff metadata to an existing JSON context."""
    result = dict(payload or {})
    telemetry = current_correlation()
    if telemetry:
        result["_telemetry"] = telemetry
    return result


@contextmanager
def correlation_scope(trace_id: str | None = None, **fields: object) -> Iterator[dict[str, object]]:
    """Temporarily extend correlation metadata across sync and worker boundaries."""
    merged = current_correlation()
    if trace_id is not None:
        fields["trace_id"] = trace_id
    for key, value in fields.items():
        if key not in _CORRELATION_KEYS:
            continue
        bounded = _bounded_value(key, value)
        if bounded is not None:
            merged[key] = bounded
    token = _CORRELATION.set(merged)
    try:
        yield merged
    finally:
        _CORRELATION.reset(token)


def safe_error_category(exc: BaseException) -> str:
    """Map an exception to a stable category without persisting provider details."""
    name = type(exc).__name__.lower()
    if isinstance(exc, TimeoutError) or "timeout" in name:
        return "timeout"
    if "integrity" in name or "operational" in name or "database" in name:
        return "database_error"
    if isinstance(exc, (ValueError, TypeError)):
        return "validation_error"
    if any(token in name for token in ("llm", "provider", "connector", "publisher")):
        return "external_capability_error"
    return "internal_error"


def log_operation(event: str, *, status: str, duration: float, error: BaseException | None = None, **fields: object) -> None:
    """Emit bounded operation telemetry; details stay in durable business records."""
    payload = {"event": event, **current_correlation(), "status": status, "duration_ms": round(duration * 1000, 1)}
    if error is not None:
        payload["error_category"] = safe_error_category(error)
    for key, value in fields.items():
        if key not in _CORRELATION_KEYS:
            continue
        bounded = _bounded_value(key, value)
        if bounded is not None:
            payload[key] = bounded
    logger.info(json.dumps(payload, ensure_ascii=False, sort_keys=True))


_probe_thread: threading.Thread | None = None


def _bounded_worker_ping(celery_app, timeout: float = 1.0):
    """Keep broker control retries from blocking a readiness request."""
    # 单飞：上一探测线程还活着（broker 挂起时 kombu 重试不返回）就不再新起，
    # 否则高频 readiness 探测会持续积累滞留线程。
    global _probe_thread
    previous = _probe_thread
    if previous is not None and previous.is_alive():
        return None
    result: queue.Queue = queue.Queue(maxsize=1)

    def probe() -> None:
        try:
            replies = celery_app.control.inspect(timeout=timeout).ping()
            result.put((True, replies))
        except Exception:  # noqa: BLE001 Worker diagnostics stay opaque.
            try:
                result.put_nowait((False, None))
            except queue.Full:
                pass

    # Kombu's control broadcast publishes with its own retry behavior. A
    # daemon thread gives the caller a hard upper bound if the broker drops
    # between the connection check and ping.
    thread = threading.Thread(target=probe, name="readiness-worker-ping", daemon=True)
    _probe_thread = thread
    thread.start()
    thread.join(timeout + 0.25)
    if thread.is_alive():
        return None
    try:
        succeeded, replies = result.get_nowait()
    except queue.Empty:
        return None
    return replies if succeeded else None


def observe(method: str, path: str, status: int, duration: float) -> None:
    method = method if method in _HTTP_METHODS else "OTHER"
    key = f'http_requests_total{{method="{method}",path="{path}",status="{status}"}}'
    _METRICS[key] = _METRICS.get(key, 0) + 1
    latency_key = f'http_request_duration_seconds_sum{{path="{path}"}}'
    _METRICS[latency_key] = _METRICS.get(latency_key, 0.0) + duration
    count_key = f'http_request_duration_seconds_count{{path="{path}"}}'
    _METRICS[count_key] = _METRICS.get(count_key, 0) + 1


def render_metrics() -> str:
    lines = [
        "# HELP http_requests_total Total HTTP requests",
        "# TYPE http_requests_total counter",
        "# HELP http_request_duration_seconds_sum Cumulative request latency",
        "# TYPE http_request_duration_seconds_sum counter",
        "# HELP http_request_duration_seconds_count Request count for latency",
        "# TYPE http_request_duration_seconds_count counter",
        "# HELP process_uptime_seconds Process uptime",
        "# TYPE process_uptime_seconds gauge",
    ]
    lines.extend(f"{key} {value}" for key, value in sorted(_METRICS.items()))
    lines.append(f'process_uptime_seconds {time.time() - START_TIME:.1f}')
    return "\n".join(lines) + "\n"


class TraceMiddleware:
    """纯 ASGI 中间件：trace_id 注入响应头，输出结构化访问日志。

    不用 BaseHTTPMiddleware：它会为每个响应引入额外的 task 切换与流缓冲，
    大文件下载端点（素材 raw / 交付包 zip）的内存与延迟会被放大；
    纯 ASGI 包一层 send 即可保留全部既有语义。
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        trace_id = uuid.uuid4().hex[:12]
        start = time.perf_counter()
        started: dict[str, int | None] = {"status": None}

        async def send_with_trace(message):
            if message["type"] == "http.response.start":
                started["status"] = message["status"]
                from starlette.datastructures import MutableHeaders

                MutableHeaders(scope=message).append("x-trace-id", trace_id)
            await send(message)

        with correlation_scope(trace_id=trace_id, operation="http_request"):
            try:
                await self.app(scope, receive, send_with_trace)
            finally:
                status = started["status"]
                if status is not None:
                    duration = time.perf_counter() - start
                    route = scope.get("route")
                    # Unmatched URLs can contain arbitrary private strings, not merely IDs.
                    path = getattr(route, "path", None) or "__unmatched__"
                    if path != "/metrics":  # 指标端点自身不计量，避免自增噪声
                        observe(scope.get("method", "?"), path, status, duration)
                    # 结构化访问日志：一行一条 JSON，trace_id 与响应头可对账
                    logger.info(
                        json.dumps(
                            {
                                "event": "http_request",
                                **current_correlation(),
                                "method": scope.get("method", "?"),
                                "path": path,
                                "status": status,
                                "duration_ms": round(duration * 1000, 1),
                            },
                            ensure_ascii=False,
                        )
                    )


def check_health(db) -> dict:
    """Truthful readiness probe; diagnostics are bounded safe reason codes."""
    from .config import get_settings, validate_production_settings

    settings = get_settings()
    reasons = []
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:  # noqa: BLE001 探针必须吞掉异常返回结构化状态
        db_ok = False
        reasons.append("database_unavailable")
    schema_ok = True
    from .db import LOCAL_APPROVED_SCHEMA_HEAD, schema_head_matches

    expected_head = settings.required_schema_head or (LOCAL_APPROVED_SCHEMA_HEAD if settings.app_env == "development" else "")
    if expected_head and db_ok:
        schema_ok = schema_head_matches(db, expected_head)
        if not schema_ok:
            reasons.append("schema_head_mismatch")
    elif expected_head:
        schema_ok = False
    auth_ok = True
    if settings.app_env == "production":
        try:
            validate_production_settings(settings)
        except RuntimeError:
            auth_ok = False
            reasons.append("production_configuration_invalid")
    storage_ok = True
    if settings.app_env == "production":
        storage_ok = bool(settings.material_storage_backend == "minio" and settings.minio_enabled
                          and settings.minio_endpoint and settings.minio_access_key
                          and settings.minio_secret_key and settings.minio_bucket)
        if not storage_ok:
            reasons.append("storage_configuration_invalid")
    if storage_ok:
        try:
            from .services.material_storage import provider

            storage_ok = provider().probe()
        except Exception:  # noqa: BLE001 Readiness exposes no storage endpoint or credential.
            storage_ok = False
        if not storage_ok:
            reasons.append("storage_unavailable")
    queue_ok = True
    worker_ok = True
    if settings.task_queue_enabled:
        try:
            from .tasks.celery_app import celery_app

            with celery_app.connection_for_read(connect_timeout=2) as connection:
                connection.ensure_connection(max_retries=0)
        except Exception:  # noqa: BLE001 Readiness must not expose broker details.
            queue_ok = False
            reasons.append("queue_unavailable")
        if queue_ok:
            try:
                replies = _bounded_worker_ping(celery_app, timeout=1)
                worker_ok = isinstance(replies, dict) and any(
                    isinstance(reply, dict) and reply.get("ok") == "pong"
                    for reply in replies.values()
                )
            except Exception:  # noqa: BLE001 Worker errors can contain credential-bearing broker URLs.
                worker_ok = False
            if not worker_ok:
                reasons.append("worker_unavailable")
        else:
            worker_ok = False
    from .services.generation.providers import effective_llm_config

    secret_ok = True
    if settings.app_env == "production" and db_ok:
        try:
            from .models import SystemSetting
            from .runtime_config import validate_production_secret_policy

            validate_production_secret_policy(db.query(SystemSetting).all())
        except Exception:  # noqa: BLE001 Readiness exposes only a bounded policy reason.
            secret_ok = False
            reasons.append("secret_policy_unavailable")
    try:
        provider_name = effective_llm_config()["provider"]
        if provider_name not in {"mock", "openai_compatible", "anthropic", "minimax"}:
            provider_name = "unavailable"
    except Exception:  # noqa: BLE001 Optional provider configuration never crashes core readiness.
        provider_name = "unavailable"
    ready = db_ok and schema_ok and auth_ok and storage_ok and queue_ok and worker_ok and secret_ok
    return {
        "status": "ok" if ready else "degraded",
        "ready": ready,
        "db": db_ok,
        "schema": schema_ok,
        "auth": auth_ok,
        "storage": storage_ok,
        "queue": queue_ok,
        "worker": worker_ok,
        "secrets": secret_ok,
        "reasons": reasons,
        "provider": provider_name,
        "optional_capabilities": {"llm": {"provider": provider_name, "required": False, "status": "unavailable" if provider_name == "unavailable" else "not_probed"}},
        "queue_enabled": settings.task_queue_enabled,
        "version": "0.1.0",
    }
