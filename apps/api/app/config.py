from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./content_studio.db"

    llm_provider: str = "mock"  # mock | openai_compatible
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""

    # Mock provider 用：注入 FactPack 外数字，验证 FactCheck blocker 链路（执行计划 §22 用例 11）
    mock_inject_unfact_number: bool = False

    url_fetch_timeout_seconds: int = 10
    url_fetch_max_bytes: int = 5 * 1024 * 1024
    # 仅限本机开发：代理 fake-ip 模式（如 Clash）下所有域名解析到 198.18.0.0/15，
    # 连接实际由代理转发；此时按解析 IP 判内网会误杀全部外网请求。生产必须保持 false。
    ssrf_allow_private: bool = False

    # Celery：默认 false 时生成/拉取在请求内同步执行（mock 毫秒级、测试零依赖）；
    # 置 true 后分发到 Redis 队列，由 worker 异步消费，API 只返回 queued 状态。
    task_queue_enabled: bool = False
    celery_broker_url: str = "redis://localhost:6379/0"

    # 对象存储（S3 兼容，如 MinIO）：默认关闭，导出内容内联返回；开启后导出产物另传存储并返回预签名 URL
    minio_enabled: bool = False
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = ""
    minio_secret_key: str = ""
    minio_bucket: str = "content-studio-assets"
    minio_secure: bool = False
    minio_url_expiry_hours: int = 24

    upload_max_bytes: int = 20 * 1024 * 1024

    # local_git Connector 允许读取的本地目录前缀（CSV，如 /Users/me/Project）；空 = 功能关闭。
    # 开发文档作为数据源（repo docs / CHANGELOG / git log），只读不执行。
    # 存 str 而非 tuple：pydantic-settings 对复杂类型会先走 JSON 解析，裸路径 CSV 会炸
    local_docs_allowlist: str = ""

    @property
    def local_docs_allowlist_dirs(self) -> tuple[str, ...]:
        import os

        return tuple(
            os.path.expanduser(p.strip()) for p in (self.local_docs_allowlist or "").split(",") if p.strip()
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
