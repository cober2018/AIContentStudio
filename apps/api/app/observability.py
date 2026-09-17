"""可观测性（EPIC-17）：/health 探针、/metrics Prometheus 文本指标、trace_id 结构化日志。"""

import json
import logging
import time
import uuid

from sqlalchemy import text

logger = logging.getLogger("studio.request")

# 进程内计数器：足够 V1 单进程部署；多副本时由外部聚合或换 prometheus_client
_METRICS: dict[str, float] = {}
START_TIME = time.time()


def observe(method: str, path: str, status: int, duration: float) -> None:
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


async def trace_middleware(request, call_next):
    """BaseHTTPMiddleware dispatch：trace_id 注入响应头，输出结构化访问日志。"""
    trace_id = uuid.uuid4().hex[:12]
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    path = request.url.path
    if path != "/metrics":  # 指标端点自身不计量，避免自增噪声
        observe(request.method, path, response.status_code, duration)
    # 结构化访问日志：一行一条 JSON，trace_id 与响应头可对账
    logger.info(
        json.dumps(
            {
                "event": "http_request",
                "trace_id": trace_id,
                "method": request.method,
                "path": path,
                "status": response.status_code,
                "duration_ms": round(duration * 1000, 1),
            },
            ensure_ascii=False,
        )
    )
    response.headers["x-trace-id"] = trace_id
    return response


def check_health(db) -> dict:
    """深探针：DB ping 失败返回 503 语义（由路由决定状态码）。"""
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
        error = None
    except Exception as exc:  # noqa: BLE001 探针必须吞掉异常返回结构化状态
        db_ok = False
        error = str(exc)[:200]
    from .config import get_settings

    settings = get_settings()
    return {
        "status": "ok" if db_ok else "degraded",
        "db": db_ok,
        "error": error,
        "provider": settings.llm_provider,
        "queue_enabled": settings.task_queue_enabled,
        "version": "0.1.0",
    }
