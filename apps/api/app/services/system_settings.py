"""系统配置展示服务（前端设置页数据源）。

职责：把「环境变量 + system_settings 运行时覆盖」合并成生效配置视图；
所有 Secret 字段一律脱敏回显，任何接口都不返回明文密钥。
"""

from sqlalchemy.engine import make_url

from .. import runtime_config
from ..config import get_settings
from ..models import SystemSetting
from .plugin_registry import SKILL_DIRS as DEFAULT_SKILL_DIRS
from .plugin_registry import dsh_status
from .plugin_registry import scan_skills as discover_local_skills
from .writing_pipeline import WEWRITE_HOME


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


def llm_view() -> dict:
    from ..services.generation.providers import effective_llm_config

    config = effective_llm_config()
    override = runtime_config.get_runtime(runtime_config.KEY_LLM) or {}
    return {
        "provider": config["provider"],
        "base_url": config["base_url"],
        "model": config["model"],
        "api_key": mask_secret(config["api_key"]),
        "mock_inject_unfact_number": bool(config.get("mock_inject_unfact_number", False)),
        "overridden": bool(override),
    }


def build_settings_view() -> dict:
    settings = get_settings()
    return {
        "llm": llm_view(),
        "models": models_view(),
        "plugins": plugins_view(),
        "dsh": dsh_view(),
        "image": image_view(),
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


def save_llm_override(db, value: dict, updated_by: str | None) -> None:
    """写入覆盖行 + 刷新进程缓存 + 失效 provider 缓存。"""
    from ..services.generation.providers import reset_provider_cache

    row = db.get(SystemSetting, runtime_config.KEY_LLM)
    if row is None:
        row = SystemSetting(key=runtime_config.KEY_LLM)
        db.add(row)
    row.value = value
    row.updated_by = updated_by
    db.flush()
    runtime_config.set_runtime(runtime_config.KEY_LLM, value)
    reset_provider_cache()


def models_view() -> dict:
    """多模型配置档 + 场景路由视图（Secret 一律脱敏）。"""
    from .. import runtime_config
    from ..services.generation.providers import ROUTE_KEYS

    models = runtime_config.get_runtime(runtime_config.KEY_MODELS) or {}
    profiles_out = {}
    for name, p in (models.get("profiles") or {}).items():
        profiles_out[name] = {
            "provider": p.get("provider", "mock"),
            "base_url": p.get("base_url", ""),
            "model": p.get("model", ""),
            "api_key": mask_secret(p.get("api_key")),
            "enabled": bool(p.get("enabled", True)),
        }
    routes = {k: (models.get("routes") or {}).get(k, "") for k in ROUTE_KEYS}
    return {"profiles": profiles_out, "routes": routes}


def save_models(db, value: dict, updated_by: str | None) -> None:
    """写入 models 覆盖（profiles + routes）并失效 provider 缓存。"""
    from .. import runtime_config
    from ..services.generation.providers import reset_provider_cache

    row = db.get(SystemSetting, runtime_config.KEY_MODELS)
    if row is None:
        row = SystemSetting(key=runtime_config.KEY_MODELS)
        db.add(row)
    row.value = value
    row.updated_by = updated_by
    db.flush()
    runtime_config.set_runtime(runtime_config.KEY_MODELS, value)
    reset_provider_cache()


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
        "dsh": dsh_status(),
    }


def save_plugins(db, value: dict, updated_by: str | None) -> None:
    from .. import runtime_config

    row = db.get(SystemSetting, runtime_config.KEY_PLUGINS)
    if row is None:
        row = SystemSetting(key=runtime_config.KEY_PLUGINS)
        db.add(row)
    row.value = value
    row.updated_by = updated_by
    db.flush()
    runtime_config.set_runtime(runtime_config.KEY_PLUGINS, value)


IMAGE_PROVIDERS = ("minimax", "gemini", "openai", "doubao", "dashscope", "replicate", "openrouter", "jimeng")


def image_view() -> dict:
    from .. import runtime_config

    stored = runtime_config.get_runtime(runtime_config.KEY_IMAGE) or {}
    return {
        "enabled": bool(stored.get("enabled", False)),
        "provider": stored.get("provider", "minimax"),
        "model": stored.get("model", ""),
        "base_url": stored.get("base_url", ""),
        "size": stored.get("size", "1344x768"),
        "api_key": mask_secret(stored.get("api_key")),
        "providers_available": list(IMAGE_PROVIDERS),
    }


def save_image(db, value: dict, updated_by: str | None) -> None:
    """保存生图开关并把 provider 同步进 ~/.wewrite/config.yaml（wewrite image-gen CLI 消费）。"""
    import yaml

    from .. import runtime_config

    row = db.get(SystemSetting, runtime_config.KEY_IMAGE)
    if row is None:
        row = SystemSetting(key=runtime_config.KEY_IMAGE)
        db.add(row)
    row.value = value
    row.updated_by = updated_by
    db.flush()
    runtime_config.set_runtime(runtime_config.KEY_IMAGE, value)

    cfg_path = WEWRITE_HOME / "config.yaml"
    try:
        cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        cfg = {}
    if value.get("enabled") and value.get("api_key"):
        entry = {
            "provider": value["provider"],
            "api_key": value["api_key"],
            "model": value.get("model") or None,
        }
        if value.get("base_url"):
            entry["base_url"] = value["base_url"]
        cfg["image"] = {"providers": [entry]}
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        cfg_path.write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")


def dsh_view() -> dict:
    from .. import runtime_config
    from .dsh_integration import studio_view

    stored = runtime_config.get_runtime(runtime_config.KEY_DSH)
    return studio_view(stored)


def save_dsh(db, value: dict, updated_by: str | None) -> None:
    from .. import runtime_config

    row = db.get(SystemSetting, runtime_config.KEY_DSH)
    if row is None:
        row = SystemSetting(key=runtime_config.KEY_DSH)
        db.add(row)
    row.value = value
    row.updated_by = updated_by
    db.flush()
    runtime_config.set_runtime(runtime_config.KEY_DSH, value)


def clear_llm_override(db) -> None:
    from ..services.generation.providers import reset_provider_cache

    row = db.get(SystemSetting, runtime_config.KEY_LLM)
    if row is not None:
        db.delete(row)
        db.flush()
    runtime_config.clear_runtime(runtime_config.KEY_LLM)
    reset_provider_cache()
