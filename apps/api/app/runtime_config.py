"""运行时配置覆盖：DB system_settings 表的值优先于环境变量。

进程内持有一份缓存：API 进程在启动与每次写入时刷新；Celery worker 在执行
LLM 任务前刷新。读取热路径（get_provider 等）只查缓存，不碰 DB。
"""

import re
import threading
from contextlib import contextmanager
from urllib.parse import parse_qsl, urlsplit

_LOCK = threading.RLock()
_OVERRIDES: dict[str, dict] = {}

KEY_LLM = "llm"
KEY_MODELS = "models"  # {"profiles": {name: {...}}, "routes": {purpose: profile_name}}
KEY_PLUGINS = "plugins"  # {"skill_dirs": [...], "skills_enabled": [...], "mcp": [{name, url, enabled}]}
KEY_DSH = "dsh"
KEY_IMAGE = "image"  # {"enabled","provider","model","base_url","api_key","size"}  # {"default_provider","default_model","fallback_provider","timeout_sec","max_retries","output_dir"}
KEY_DELIVERY = "delivery"  # 历史配置保留读取；allow_unverified_auto_draft 不再授权远端效果


@contextmanager
def configuration_guard():
    """Serialize process-cache changes with runtime revalidation and durable acceptance."""
    with _LOCK:
        yield


def load_from_db(db) -> None:
    """用 DB 中的覆盖行整体刷新进程缓存（启动 / 写入后 / worker 任务前调用）。"""
    from .models import SystemSetting

    rows = db.query(SystemSetting).all()
    validate_production_secret_policy(rows)
    with _LOCK:
        _OVERRIDES.clear()
        for row in rows:
            _OVERRIDES[row.key] = dict(row.value or {})


_SECRET_FIELDS = {"apikey", "accesskey", "secretkey", "secret", "clientsecret", "appsecret", "password", "passwd", "token", "accesstoken", "refreshtoken", "authorization", "cookie", "signature"}


def _secret_field(name: str) -> bool:
    normalized = re.sub(r"[^a-z]", "", name.lower())
    return (normalized in _SECRET_FIELDS
            or normalized.endswith(("apikey", "password", "secret", "token", "authorization", "cookie", "signature"))
            or normalized in {"sig", "xamzcredential", "xgoogcredential", "ossaccesskeyid", "keypairid"})


def contains_plaintext_secret(value, *, depth: int = 0) -> bool:
    """Inspect stored configuration without returning any value or user-defined key."""
    if depth > 20:
        return True
    if isinstance(value, dict):
        for name, item in value.items():
            if _secret_field(str(name)) and item:
                return True
            if contains_plaintext_secret(item, depth=depth + 1):
                return True
    elif isinstance(value, list):
        return any(contains_plaintext_secret(item, depth=depth + 1) for item in value)
    elif isinstance(value, str) and "://" in value:
        try:
            url = urlsplit(value)
            if url.username is not None or url.password is not None:
                return True
            if any(_secret_field(name) for name, _ in parse_qsl(url.query, keep_blank_values=True)):
                return True
        except ValueError:
            return True
    return False


def validate_production_secret_policy(rows) -> None:
    from .config import get_settings

    if get_settings().app_env == "production" and any(contains_plaintext_secret(row.value) for row in rows):
        raise RuntimeError("production_plaintext_secret_override")


def validate_persisted_configuration(value) -> None:
    from fastapi import HTTPException

    from .config import get_settings

    if get_settings().app_env == "production" and contains_plaintext_secret(value):
        raise HTTPException(422, "production_secret_reference_required")


def set_runtime(key: str, value: dict) -> None:
    with _LOCK:
        _OVERRIDES[key] = dict(value)


def clear_runtime(key: str) -> None:
    with _LOCK:
        _OVERRIDES.pop(key, None)


def get_runtime(key: str) -> dict | None:
    with _LOCK:
        value = _OVERRIDES.get(key)
        return dict(value) if value is not None else None


def clear_all() -> None:
    with _LOCK:
        _OVERRIDES.clear()
