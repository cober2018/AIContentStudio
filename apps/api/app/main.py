"""FastAPI 入口。"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import init_db
from .observability import trace_middleware
from .routers import (
    assets,
    article_handoff,
    connectors,
    dashboard,
    external,
    fact_packs,
    facts,
    generate,
    health,
    reviews,
    settings,
    sources,
    templates,
    topics,
    users,
    workflows,
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
    init_db()
    from .db import SessionLocal

    with SessionLocal() as db:
        sync_prompt_versions_from_files(db)
        # 修复历史数据：同渠道多个 published 模板只保留最高版本
        from .routers.templates import normalize_template_publication

        demoted = normalize_template_publication(db)
        if demoted:
            import logging

            logging.getLogger(__name__).info("已下线 %d 个同渠道旧生效模板", demoted)
        # 运行时配置覆盖（前端设置页写入）加载进进程缓存
        from . import runtime_config

        runtime_config.load_from_db(db)
        db.commit()
    yield


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
    facts,
    fact_packs,
    topics,
    generate,
    reviews,
    assets,
    article_handoff,
    templates,
    dashboard,
    users,
    connectors,
    settings,
    workflows,
    health,
    external,
):
    app.include_router(router.router)

# trace_id + 访问日志 + 指标采集（放在 CORS 之后注册，实际处于最外层）
from starlette.middleware.base import BaseHTTPMiddleware

app.add_middleware(BaseHTTPMiddleware, dispatch=trace_middleware)
