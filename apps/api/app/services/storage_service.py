"""对象存储（MinIO/S3 兼容）：开关式启用，未启用时导出走 DB 内联返回（V1 默认）。"""

import logging

from ..config import get_settings

logger = logging.getLogger(__name__)

_client = None


class StorageError(RuntimeError):
    pass


def storage_enabled() -> bool:
    return get_settings().minio_enabled


def _get_client():
    global _client
    if _client is None:
        try:
            from minio import Minio
        except ImportError as exc:
            raise StorageError("minio SDK 未安装（pip install minio）") from exc
        settings = get_settings()
        _client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        if not _client.bucket_exists(settings.minio_bucket):
            _client.make_bucket(settings.minio_bucket)
    return _client


def put_object(key: str, content: bytes, content_type: str = "text/plain; charset=utf-8") -> str:
    """上传对象并返回预签名下载 URL。"""
    settings = get_settings()
    client = _get_client()
    import io

    client.put_object(
        settings.minio_bucket, key, io.BytesIO(content), len(content), content_type=content_type
    )
    return presigned_get_url(key)


def presigned_get_url(key: str, expires_hours: int | None = None) -> str:
    from datetime import timedelta

    settings = get_settings()
    url = _get_client().presigned_get_object(
        settings.minio_bucket, key, expires=timedelta(hours=expires_hours or settings.minio_url_expiry_hours)
    )
    return url


def export_to_storage(key: str, content: str) -> str | None:
    """导出产物上传；失败只告警不阻断导出（本地仍有 content 返回）。"""
    if not storage_enabled():
        return None
    try:
        return put_object(key, content.encode("utf-8"))
    except Exception as exc:  # noqa: BLE001 存储故障不阻断导出主流程
        logger.warning("导出产物上传对象存储失败 key=%s: %s", key, exc)
        return None
