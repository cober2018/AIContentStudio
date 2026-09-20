"""运行时配置覆盖：DB system_settings 表的值优先于环境变量。

进程内持有一份缓存：API 进程在启动与每次写入时刷新；Celery worker 在执行
LLM 任务前刷新。读取热路径（get_provider 等）只查缓存，不碰 DB。
"""

import threading

_LOCK = threading.Lock()
_OVERRIDES: dict[str, dict] = {}

KEY_LLM = "llm"
KEY_MODELS = "models"  # {"profiles": {name: {...}}, "routes": {purpose: profile_name}}
KEY_PLUGINS = "plugins"  # {"skill_dirs": [...], "skills_enabled": [...], "mcp": [{name, url, enabled}]}
KEY_DSH = "dsh"
KEY_IMAGE = "image"  # {"enabled","provider","model","base_url","api_key","size"}  # {"default_provider","default_model","fallback_provider","timeout_sec","max_retries","output_dir"}


def load_from_db(db) -> None:
    """用 DB 中的覆盖行整体刷新进程缓存（启动 / 写入后 / worker 任务前调用）。"""
    from .models import SystemSetting

    rows = db.query(SystemSetting).all()
    with _LOCK:
        _OVERRIDES.clear()
        for row in rows:
            _OVERRIDES[row.key] = dict(row.value or {})


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
