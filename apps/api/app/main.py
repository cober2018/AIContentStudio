"""FastAPI 入口。"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import init_db
from .observability import trace_middleware
from .routers import (
    assets,
    connectors,
    dashboard,
    fact_packs,
    facts,
    generate,
    health,
    reviews,
    sources,
    templates,
    topics,
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
    init_db()
    from .db import SessionLocal

    with SessionLocal() as db:
        sync_prompt_versions_from_files(db)
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
    templates,
    dashboard,
    users,
    connectors,
    health,
):
    app.include_router(router.router)

# trace_id + 访问日志 + 指标采集（放在 CORS 之后注册，实际处于最外层）
from starlette.middleware.base import BaseHTTPMiddleware

app.add_middleware(BaseHTTPMiddleware, dispatch=trace_middleware)
