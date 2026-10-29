"""FastAPI 入口。"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings, validate_production_settings
from .db import SessionLocal, init_db, schema_head_matches
from .observability import TraceMiddleware
from .routers import (
    capability_memory,
    channel_variants,
    channels,
    connectors,
    content_identities,
    content_masters,
    content_projects,
    creation_recipe_learning,
    creative_mcp,
    creative_orchestration,
    delivery,
    edit_agent,
    external,
    fact_packs,
    facts,
    form_assistance,
    health,
    home,
    learning,
    material_library,
    material_match,
    materials,
    obsidian_knowledge,
    opportunities,
    performance_history,
    product_settings,
    project_assets,
    project_evidence,
    project_read_models,
    project_review,
    settings,
    sources,
    stage_integrations,
    system_library,
    templates,
    users,
)
from .routers.templates import sync_prompt_versions_from_files

# 结构化访问日志走 studio.request；第三方库日志保持简洁
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[logging.StreamHandler()],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    validate_production_settings(settings)
    if settings.app_env != "production":
        init_db()
    with SessionLocal() as db:
        if settings.app_env == "production" and not schema_head_matches(db, settings.required_schema_head):
            raise RuntimeError("production_schema_head_mismatch")
        if settings.app_env != "production":
            sync_prompt_versions_from_files(db)
        # 修复历史数据：同渠道多个 published 模板只保留最高版本
        from .routers.templates import normalize_template_publication

        demoted = normalize_template_publication(db) if settings.app_env != "production" else 0
        if demoted:
            import logging

            logging.getLogger(__name__).info("已下线 %d 个同渠道旧生效模板", demoted)
        # 运行时配置覆盖（前端设置页写入）加载进进程缓存
        from . import runtime_config

        runtime_config.load_from_db(db)
        from .services import model_registration

        model_registration.migrate_to_single_source(db)
        model_registration.sync_cli_files()
        from .services.storage_locations import ensure_default

        ensure_default(db)
        from .services.project_folders import ensure_library_dirs

        ensure_library_dirs()
        # V1 PRD 2.0：媒体 provider（asset_provider 等）注册；不联网、不发布
        from .services.content_harness.providers import bootstrap_media_providers

        bootstrap_media_providers()
        from .services.minimax_cli_provider import register_if_enabled

        register_if_enabled()
        # V1 PRD 2.0：基础 discoverability profiles（幂等）
        from .services import discoverability as disco

        if settings.app_env != "production":
            disco.seed_default_profiles(db)
            db.commit()
    # 兜底维护（僵尸 running 回收/retention/WAL checkpoint），beat 不可用时的默认执行者
    from .services import maintenance

    maintenance.start()
    try:
        yield
    finally:
        maintenance.stop()


app = FastAPI(title="AI Content Studio API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (
    sources,
    capability_memory,
    facts,
    fact_packs,
    form_assistance,
    delivery,
    material_library,
    material_match,
    edit_agent,
    materials,
    templates,
    channels,
    channel_variants,
    users,
    connectors,
    settings,
    content_identities,
    content_projects,
    creation_recipe_learning,
    stage_integrations,
    content_masters,
    learning,
    creative_orchestration,
    creative_mcp,
    opportunities,
    home,
    performance_history,
    product_settings,
    system_library,
    project_evidence,
    project_assets,
    project_read_models,
    project_review,
    obsidian_knowledge,
    health,
    external,
):
    app.include_router(router.router)

# trace_id + 访问日志 + 指标采集（放在 CORS 之后注册，实际处于最外层）
app.add_middleware(TraceMiddleware)
