"""系统配置管理（前端设置页 API，EPIC-13 扩展）。

- GET    /api/v1/settings          生效配置总览（Secret 一律脱敏；登录即可看）
- PUT    /api/v1/settings/llm      写入默认 LLM 覆盖（admin；优先于 .env）
- DELETE /api/v1/settings/llm      清除默认覆盖，回落环境变量（admin）
- POST   /api/v1/settings/llm/test 连通性验证（admin）
- PUT    /api/v1/settings/models   多模型 Profiles + 场景路由（admin）
- PUT    /api/v1/settings/plugins  技能启用集 + MCP 登记（admin）
"""

import asyncio
import time
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import runtime_config
from ..db import get_db
from ..deps import get_current_user, require_admin
from ..services.generation.providers import (
    ROUTE_KEYS,
    GenerateRequest,
    OpenAICompatibleProvider,
    effective_llm_config,
)
from ..services.system_settings import (
    build_settings_view,
    clear_llm_override,
    save_llm_override,
    save_models,
    save_plugins,
)

router = APIRouter(tags=["settings"])


class LLMSettingsUpdate(BaseModel):
    provider: Literal["mock", "openai_compatible"]
    base_url: str = ""
    model: str = ""
    api_key: str = ""  # 留空 = 保持当前生效值不变化
    mock_inject_unfact_number: bool = False


class ModelProfile(BaseModel):
    name: str
    provider: Literal["mock", "openai_compatible"]
    base_url: str = ""
    model: str = ""
    api_key: str = ""  # 留空 = 保持该 Profile 已存值
    enabled: bool = True


class ModelsUpdate(BaseModel):
    profiles: list[ModelProfile]
    routes: dict[str, str] = {}


class PluginsUpdate(BaseModel):
    skill_dirs: list[str] = []
    skills_enabled: list[str] = []
    mcp: list[dict[str, Any]] = []


class ImageGenUpdate(BaseModel):
    enabled: bool = False
    provider: Literal["minimax", "gemini", "openai", "doubao", "dashscope", "replicate", "openrouter", "jimeng"] = "minimax"
    model: str = ""
    base_url: str = ""
    api_key: str = ""  # 留空 = 保持已存值
    size: str = "1344x768"


class DshConfigUpdate(BaseModel):
    default_provider: str = "minimax"
    default_model: str = "MiniMax-M3"
    fallback_provider: str = "deepseek"
    fallback_model: str = "deepseek-chat"
    timeout_sec: int = 300
    max_retries: int = 1
    output_dir: str = ".wewrite-scratch"
    apply_to_dsh: bool = False  # true 时把默认模型写回 ~/.dsh/settings.yaml（自动备份）


@router.get("/api/v1/settings")
def get_settings_view(user=Depends(get_current_user)):
    return build_settings_view()


@router.put("/api/v1/settings/llm")
def put_llm_settings(
    payload: LLMSettingsUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
):
    # 覆盖存完整快照：未填的 api_key 沿用当前生效值，避免已配置密钥被意外清空
    merged = {
        "provider": payload.provider,
        "base_url": payload.base_url.strip(),
        "model": payload.model.strip(),
        "api_key": payload.api_key or effective_llm_config()["api_key"],
        "mock_inject_unfact_number": payload.mock_inject_unfact_number,
    }
    if payload.provider == "openai_compatible":
        missing = [k for k in ("base_url", "model", "api_key") if not merged[k]]
        if missing:
            raise HTTPException(422, f"openai_compatible 需要配置: {', '.join(missing)}")
    save_llm_override(db, merged, updated_by=user.email)
    db.commit()
    return build_settings_view()["llm"]


@router.delete("/api/v1/settings/llm")
def delete_llm_settings(
    db: Session = Depends(get_db),
    user=Depends(require_admin),
):
    clear_llm_override(db)
    db.commit()
    return build_settings_view()["llm"]


@router.post("/api/v1/settings/llm/test")
def test_llm_settings(
    payload: LLMSettingsUpdate | None = None,
    user=Depends(require_admin),
):
    """连通性验证：payload 缺省字段回落当前生效配置；不发真实业务请求。"""
    effective = effective_llm_config()
    body = payload.model_dump() if payload else {}
    provider_name = body.get("provider") or effective["provider"]
    config = {
        "provider": provider_name,
        "base_url": (body.get("base_url") or "").strip() or effective["base_url"],
        "model": (body.get("model") or "").strip() or effective["model"],
        "api_key": body.get("api_key") or effective["api_key"],
    }
    started = time.monotonic()
    if provider_name == "mock":
        return {"ok": True, "provider": "mock", "latency_ms": 0, "reply": "mock provider 恒可用"}
    try:
        provider = OpenAICompatibleProvider(config["base_url"], config["api_key"], config["model"])
        request = GenerateRequest(
            purpose="settings_test",
            channel=None,
            system_prompt="你是连通性探针。只回复两个字：正常",
            user_prompt="ping",
        )
        reply = asyncio.run(provider.generate_text(request))
    except Exception as exc:  # noqa: BLE001 测试端点把任何失败转成结构化结果
        return {
            "ok": False,
            "provider": provider_name,
            "latency_ms": int((time.monotonic() - started) * 1000),
            "error": str(exc)[:300],
        }
    return {
        "ok": True,
        "provider": provider_name,
        "model": config["model"],
        "latency_ms": int((time.monotonic() - started) * 1000),
        "reply": reply[:120],
    }


@router.put("/api/v1/settings/models")
def put_models_settings(
    payload: ModelsUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
):
    """多模型 Profiles + 场景路由。api_key 留空沿用该 Profile 已存值；路由指向的 Profile 必须存在。"""
    existing = (runtime_config.get_runtime(runtime_config.KEY_MODELS) or {}).get("profiles") or {}
    profiles: dict[str, dict] = {}
    for p in payload.profiles:
        name = p.name.strip()
        if not name:
            raise HTTPException(422, "Profile 名称不能为空")
        if name in profiles:
            raise HTTPException(422, f"Profile 名称重复: {name}")
        merged = {
            "provider": p.provider,
            "base_url": p.base_url.strip(),
            "model": p.model.strip(),
            # 留空沿用已存值：先查本次提交里的旧值，再回落已存覆盖
            "api_key": p.api_key or (profiles.get(name, {}).get("api_key")) or existing.get(name, {}).get("api_key", ""),
            "enabled": p.enabled,
        }
        if p.provider == "openai_compatible" and p.enabled:
            missing = [k for k in ("base_url", "model", "api_key") if not merged[k]]
            if missing:
                raise HTTPException(422, f"Profile「{name}」缺少: {', '.join(missing)}")
        profiles[name] = merged
    routes = {k: v.strip() for k, v in payload.routes.items() if k in ROUTE_KEYS}
    for purpose, target in routes.items():
        if target and target not in profiles:
            raise HTTPException(422, f"场景 {purpose} 路由指向不存在的 Profile: {target}")
    save_models(db, {"profiles": profiles, "routes": routes}, updated_by=user.email)
    db.commit()
    return build_settings_view()["models"]


@router.put("/api/v1/settings/plugins")
def put_plugins_settings(
    payload: PluginsUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
):
    from pathlib import Path

    skill_dirs: list[str] = []
    for d in payload.skill_dirs:
        expanded = str(Path(d.strip()).expanduser())
        if not expanded or not Path(expanded).is_dir():
            raise HTTPException(422, f"扫描目录不存在: {d}")
        skill_dirs.append(expanded)
    known = {s["name"] for s in build_settings_view()["plugins"]["skills"]}
    unknown = [n for n in payload.skills_enabled if n not in known]
    if unknown:
        raise HTTPException(422, f"未知技能: {', '.join(unknown[:5])}")
    mcp = []
    for m in payload.mcp:
        name = str(m.get("name", "")).strip()
        url = str(m.get("url", "")).strip()
        if not name or not url.startswith(("http://", "https://")):
            raise HTTPException(422, f"MCP 登记需要 name 与 http(s) URL: {name or '(空)'}")
        mcp.append({"name": name, "url": url, "enabled": bool(m.get("enabled", True))})
    save_plugins(
        db, {"skill_dirs": skill_dirs, "skills_enabled": payload.skills_enabled, "mcp": mcp},
        updated_by=user.email,
    )
    db.commit()
    return build_settings_view()["plugins"]


@router.put("/api/v1/settings/image")
def put_image_settings(
    payload: ImageGenUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
):
    """AI 生图开关：provider 可切（minimax / gemini / openai / ...），保存即同步 wewrite CLI 配置。"""
    from ..services.system_settings import save_image

    existing = (runtime_config.get_runtime(runtime_config.KEY_IMAGE) or {}).get("api_key", "")
    value = {
        "enabled": payload.enabled,
        "provider": payload.provider,
        "model": payload.model.strip(),
        "base_url": payload.base_url.strip(),
        "api_key": payload.api_key or existing,
        "size": payload.size.strip() or "1344x768",
    }
    if payload.enabled and not value["api_key"]:
        raise HTTPException(422, "启用生图需要 API Key（MiniMax/Gemini 均用各自平台 Key）")
    save_image(db, value, updated_by=user.email)
    db.commit()
    return build_settings_view()["image"]


@router.put("/api/v1/settings/dsh")
def put_dsh_settings(
    payload: DshConfigUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
):
    from ..services.dsh_integration import apply_default_model
    from ..services.system_settings import save_dsh

    value = {
        "default_provider": payload.default_provider.strip() or "minimax",
        "default_model": payload.default_model.strip(),
        "fallback_provider": payload.fallback_provider.strip(),
        "fallback_model": payload.fallback_model.strip(),
        "timeout_sec": max(30, min(3600, payload.timeout_sec)),
        "max_retries": max(0, min(5, payload.max_retries)),
        "output_dir": payload.output_dir.strip() or ".wewrite-scratch",
    }
    result: dict[str, Any] = {}
    if payload.apply_to_dsh:
        result = apply_default_model(value["default_provider"], value["default_model"])
        if not result.get("ok"):
            raise HTTPException(422, result.get("error", "写回 dsh 设置失败"))
    save_dsh(db, value, updated_by=user.email)
    db.commit()
    view = build_settings_view()["dsh"]
    view["last_apply"] = result
    return view
