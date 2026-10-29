"""系统配置管理（前端设置页 API，EPIC-13 扩展）。

- GET    /api/v1/settings          完整运行环境总览（admin；含本地 inventory）
- PUT    /api/v1/settings/plugins  技能启用集 + MCP 登记（admin）
- GET    /api/v1/settings/mcp      平台 MCP 接入：状态、连接方式、能力清单（admin；不含令牌）
- POST   /api/v1/settings/mcp/check 平台 MCP 自检（admin；不联网、不含令牌）
"""

import asyncio
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_admin
from ..services.system_settings import (
    build_settings_view,
    save_plugins,
)

router = APIRouter(tags=["settings"])


class CapabilityConfigurationUpdate(BaseModel):
    model_config = {"extra": "forbid"}
    expected_revision: int = Field(strict=True, ge=0)
    configuration: dict[str, Any]


class CapabilityPlanIn(BaseModel):
    model_config = {"extra": "forbid"}
    capability: str = Field(max_length=30)
    selected_profile: str = Field(pattern=r"^[A-Za-z0-9_.-]{1,100}$")
    parameters: dict[str, int] = {}
    explicit_plugin: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_.-]{1,100}$")
    explicit_profile: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_.-]{1,100}$")


class VoiceCatalogUpdate(BaseModel):
    model_config = {"extra": "forbid"}
    expected_revision: int = Field(strict=True, ge=0)
    items: list[dict[str, Any]] = Field(default_factory=list, max_length=2000)


@router.get("/api/v1/settings/model-capabilities")
def get_model_capabilities(db: Session = Depends(get_db), user=Depends(get_current_user)):
    from ..services import model_capability_routing

    return model_capability_routing.configuration_view(db)


@router.put("/api/v1/settings/model-capabilities")
def put_model_capabilities(payload: CapabilityConfigurationUpdate, db: Session = Depends(get_db), user=Depends(require_admin)):
    from ..services import model_capability_routing

    return model_capability_routing.save_configuration(db, payload.configuration, expected_revision=payload.expected_revision, actor=user.email)


@router.post("/api/v1/settings/model-capabilities/plan")
def preview_model_capability_plan(payload: CapabilityPlanIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    from ..services import model_capability_routing

    return model_capability_routing.plan(db, **payload.model_dump())


@router.put("/api/v1/settings/model-capabilities/voice-catalog")
def put_voice_catalog(payload: VoiceCatalogUpdate, db: Session = Depends(get_db), user=Depends(require_admin)):
    from ..services import model_capability_routing

    return model_capability_routing.save_voice_catalog(
        db, payload.items, expected_revision=payload.expected_revision, actor=user.email,
    )


@router.post("/api/v1/settings/model-capabilities/voice-catalog/refresh")
def refresh_voice_catalog(db: Session = Depends(get_db), user=Depends(require_admin)):
    """Explicitly refresh local voice metadata; normal reads never invoke a provider."""
    from ..services import model_capability_routing

    return model_capability_routing.refresh_voice_catalog(db, actor=user.email)


class PluginsUpdate(BaseModel):
    skill_dirs: list[str] = []
    skills_enabled: list[str] = []
    mcp: list[dict[str, Any]] = []


@router.get("/api/v1/settings/model-registration")
def get_model_registration(db: Session = Depends(get_db), user=Depends(get_current_user)):
    from ..services.model_registration import configuration_view

    return configuration_view(db)


@router.put("/api/v1/settings/model-registration")
def put_model_registration(payload: CapabilityConfigurationUpdate, db: Session = Depends(get_db), user=Depends(require_admin)):
    from ..services.model_registration import save_configuration

    return save_configuration(db, {**payload.configuration, "expected_revision": payload.expected_revision}, actor=user.email)


@router.post("/api/v1/settings/model-registration/providers/{provider_id}/models")
def discover_provider_models(provider_id: str, db: Session = Depends(get_db), user=Depends(require_admin)):
    from ..services.model_registration import discover

    return discover(db, provider_id)


class MiniMaxVendorUpdate(BaseModel):
    enabled: bool | None = None
    api_key: str | None = Field(default=None, max_length=4096)
    base_url: str | None = Field(default=None, max_length=500)
    region: str | None = Field(default=None, pattern=r"^(|global|cn)$")


@router.put("/api/v1/settings/model-registration/minimax")
def put_minimax_vendor(payload: MiniMaxVendorUpdate, db: Session = Depends(get_db), user=Depends(require_admin)):
    from ..services import minimax_cli_provider
    from ..services.model_registration import _minimax_view

    minimax_cli_provider.save_settings(db, payload.model_dump(exclude_none=True), user.email)
    minimax_cli_provider.register_if_enabled()
    db.commit()
    return {"vendor": _minimax_view()}


@router.post("/api/v1/settings/model-registration/minimax/test")
async def test_minimax_vendor(user=Depends(require_admin)):
    from ..services import minimax_cli_provider

    return await asyncio.to_thread(minimax_cli_provider.test_vendor)


@router.get("/api/v1/settings")
def get_settings_view(user=Depends(require_admin)):
    return build_settings_view()


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


@router.get("/api/v1/settings/mcp")
def get_mcp_settings(db: Session = Depends(get_db), user=Depends(require_admin)):
    from ..services import mcp_settings

    return mcp_settings.view(db)


@router.post("/api/v1/settings/mcp/check")
def check_mcp_settings(db: Session = Depends(get_db), user=Depends(require_admin)):
    from ..services import mcp_settings

    return mcp_settings.check(db)


class StorageLibraryUpdate(BaseModel):
    path: str = Field(min_length=1, max_length=1000)
    confirm: bool = False


class StorageLocalMove(BaseModel):
    path: str = Field(min_length=1, max_length=1000)


@router.get("/api/v1/settings/storage")
def get_storage_settings(db: Session = Depends(get_db), user=Depends(get_current_user)):
    from ..services import storage_locations

    return storage_locations.view(db)


@router.put("/api/v1/settings/storage/library")
def put_storage_library(payload: StorageLibraryUpdate, db: Session = Depends(get_db), user=Depends(require_admin)):
    from ..services import storage_locations

    result = storage_locations.set_library(db, payload.path, confirm=payload.confirm, user=user)
    return {**result, "storage": storage_locations.view(db)}


@router.put("/api/v1/settings/storage/common")
def put_storage_common(payload: StorageLocalMove, db: Session = Depends(get_db), user=Depends(require_admin)):
    from ..services import storage_locations

    result = storage_locations.set_common(db, payload.path, user)
    return {**result, "storage": storage_locations.view(db)}


@router.post("/api/v1/settings/storage/local/move")
def move_storage_local(payload: StorageLocalMove, user=Depends(require_admin)):
    from ..services import storage_locations

    return storage_locations.start_local_move(payload.path)


@router.get("/api/v1/settings/ae-templates")
def get_ae_templates(user=Depends(get_current_user)):
    from ..services import craft_skills

    keep = ("id", "version", "name", "category", "use", "fields", "images", "duration_ms", "alpha", "status", "installed")
    items = []
    for m in craft_skills.list_templates()["templates"]:
        aspects = ["9:16"] + sorted((m.get("variants") or {}).keys())
        items.append({**{key: m.get(key) for key in keep}, "aspects": aspects,
                      "previews": sorted(aspect.replace(":", "x") for aspect in m["preview_files"])})
    return {"items": items}


@router.get("/api/v1/settings/ae-templates/{template_id}/{version}/preview/{aspect}")
def get_ae_template_preview(template_id: str, version: str, aspect: Literal["9x16", "16x9"], user=Depends(get_current_user)):
    from fastapi.responses import FileResponse

    from ..services import craft_skills

    return FileResponse(craft_skills.preview_file(template_id, version, aspect.replace("x", ":")), media_type="video/mp4")


class OpenMediaSourceChange(BaseModel):
    enabled: bool | None = None
    api_key: str | None = Field(default=None, max_length=500)


@router.get("/api/v1/settings/open-media")
def get_open_media_settings(user=Depends(require_admin)):
    from ..services import open_media

    return {"items": open_media.settings_view()}


@router.put("/api/v1/settings/open-media")
def put_open_media_settings(payload: dict[str, OpenMediaSourceChange], db: Session = Depends(get_db), user=Depends(require_admin)):
    from ..services import open_media

    open_media.save_settings(db, {key: change.model_dump(exclude_none=True) for key, change in payload.items()}, user.email)
    db.commit()
    return {"items": open_media.settings_view()}


@router.post("/api/v1/settings/open-media/{source}/test")
async def test_open_media_source(source: str, user=Depends(require_admin)):
    from ..services import open_media

    return await asyncio.to_thread(open_media.test_source, source)
