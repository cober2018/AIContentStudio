"""测试夹具：内存 SQLite + 依赖覆盖 + Mock Provider。"""

import os

os.environ["LLM_PROVIDER"] = "mock"
os.environ["MOCK_INJECT_UNFACT_NUMBER"] = "false"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.db import Base, get_db
from app.services.generation.providers import _providers


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    from app.main import app

    app.dependency_overrides[get_db] = override_get_db
    # 不用 with：避免触发 lifespan 在模块级引擎上建库文件
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def inject_unfact(monkeypatch):
    """打开 mock 注入 FactPack 外数字的开关，测试 FactCheck blocker 链路。"""
    monkeypatch.setenv("MOCK_INJECT_UNFACT_NUMBER", "true")
    get_settings.cache_clear()
    _providers.clear()
    yield
    monkeypatch.setenv("MOCK_INJECT_UNFACT_NUMBER", "false")
    get_settings.cache_clear()
    _providers.clear()
