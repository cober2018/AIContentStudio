"""系统配置展示服务（前端设置页数据源）。

职责：把「环境变量 + system_settings 运行时覆盖」合并成生效配置视图；
所有 Secret 字段一律脱敏回显，任何接口都不返回明文密钥。
"""

import re
from urllib.parse import parse_qsl, unquote, urlsplit

from sqlalchemy.engine import make_url

from ..config import get_settings
from ..models import SystemSetting
from .plugin_registry import SKILL_DIRS as DEFAULT_SKILL_DIRS
from .plugin_registry import scan_skills as discover_local_skills


def discover_default_skill_dirs() -> tuple:
    return DEFAULT_SKILL_DIRS


def mask_secret(value: str | None) -> dict:
    """密钥脱敏视图：只回显是否配置 + 掩码（前 3 后 4），永不返回明文。"""
    if not value:
        return {"configured": False, "masked": ""}
    masked = f"{value[:3]}••••{value[-4:]}" if len(value) > 8 else "••••"
    return {"configured": True, "masked": masked}


def mask_url(url: str) -> str:
    """连接串脱敏：隐藏密码，其余（方言/host/库名）保留用于展示。"""
    try:
        return make_url(url).render_as_string(hide_password=True)
    except Exception:  # noqa: BLE001 展示用途，解析失败就整体打码
        return "••••"


def display_provider_url(value: str | None) -> tuple[str, bool]:
    """Keep editable clean URLs intact; omit unsafe ones rather than invent a mask URL."""
    if not value:
        return "", False
    if not isinstance(value, str) or any(ord(c) <= 32 for c in value) or "\\" in value:
        return "", True
    credential_name = r"api[_-]?key|access[_-]?key|token|secret|password|passwd|pwd|credential|authorization|auth|bearer|signature|sig"
    try:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username is not None or parsed.password is not None or parsed.fragment:
            return "", True
        if parsed.port == 0:
            return "", True
        decoded_path = unquote(parsed.path)
        if re.search(rf"(?:^|[/;])(?:{credential_name})(?:[/;=]|$)|(?:^|/)sk-[^/]+", decoded_path, re.IGNORECASE):
            return "", True
        # Unknown query names are not evidence of safety, even without a secret keyword.
        for name, query_value in parse_qsl(parsed.query.replace(";", "&"), keep_blank_values=True, strict_parsing=True):
            if name.lower() not in {"version", "api-version"} or not re.fullmatch(r"[vV]?[0-9][a-zA-Z0-9._-]{0,63}", query_value):
                return "", True
        return value, False
    except ValueError:
        return "", True


def build_settings_view() -> dict:
    settings = get_settings()
    return {
        "plugins": plugins_view(),
        "database": {
            "url": mask_url(settings.database_url),
            "driver": make_url(settings.database_url).drivername,
        },
        "queue": {
            "enabled": settings.task_queue_enabled,
            "broker": mask_url(settings.celery_broker_url),
            "queues": ["default", "llm", "ingestion", "export"],
        },
        "storage": {
            "enabled": settings.minio_enabled,
            "endpoint": settings.minio_endpoint,
            "bucket": settings.minio_bucket,
            "secure": settings.minio_secure,
            "access_key": mask_secret(settings.minio_access_key),
            "url_expiry_hours": settings.minio_url_expiry_hours,
        },
        "security": {
            "ssrf_allow_private": settings.ssrf_allow_private,
            "url_fetch_timeout_seconds": settings.url_fetch_timeout_seconds,
            "url_fetch_max_bytes": settings.url_fetch_max_bytes,
            "upload_max_bytes": settings.upload_max_bytes,
        },
        "app": {"version": "0.1.0"},
    }


def plugins_view() -> dict:
    from .. import runtime_config

    stored = runtime_config.get_runtime(runtime_config.KEY_PLUGINS) or {}
    custom_dirs = [str(d) for d in (stored.get("skill_dirs") or [])]
    scan_dirs = list(discover_default_skill_dirs()) + custom_dirs  # 并集：默认目录始终生效
    return {
        "skill_dirs": custom_dirs,
        "skills_enabled": list(stored.get("skills_enabled") or []),
        "mcp": list(stored.get("mcp") or []),
        "skills": discover_local_skills(scan_dirs),
        "dsh": {"url": "http://localhost:3080", "reachable": False, "status_code": None, "status": "not_probed"},
    }


def save_plugins(db, value: dict, updated_by: str | None) -> None:
    from .. import runtime_config

    runtime_config.validate_persisted_configuration(value)
    row = db.get(SystemSetting, runtime_config.KEY_PLUGINS)
    if row is None:
        row = SystemSetting(key=runtime_config.KEY_PLUGINS)
        db.add(row)
    row.value = value
    row.updated_by = updated_by
    db.flush()
    runtime_config.set_runtime(runtime_config.KEY_PLUGINS, value)


