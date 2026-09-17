"""对象存储层测试：开关关闭返回 None；开启时上传并返回预签名 URL（mock 客户端）。"""

from app.services import storage_service


def test_export_returns_none_when_disabled(monkeypatch):
    from app.config import get_settings

    monkeypatch.delenv("MINIO_ENABLED", raising=False)
    get_settings.cache_clear()
    try:
        assert storage_service.export_to_storage("k.md", "content") is None
    finally:
        get_settings.cache_clear()


def test_export_uploads_and_returns_presigned_url(monkeypatch):
    from app.config import get_settings

    monkeypatch.setenv("MINIO_ENABLED", "true")
    get_settings.cache_clear()
    try:
        uploaded = {}

        class FakeClient:
            def put_object(self, bucket, key, stream, length, content_type=None):
                uploaded["bucket"], uploaded["key"], uploaded["length"] = bucket, key, length

            def presigned_get_object(self, bucket, key, expires=None):
                return f"https://fake/{bucket}/{key}"

        monkeypatch.setattr(storage_service, "_get_client", lambda: FakeClient())
        url = storage_service.export_to_storage("a/asset-1.md", "# hi")
        assert url == "https://fake/content-studio-assets/a/asset-1.md"
        assert uploaded["length"] == 4

        # 上传异常不阻断：返回 None
        def broken(*a, **kw):
            raise RuntimeError("s3 down")

        monkeypatch.setattr(storage_service, "_get_client", lambda: broken())
        assert storage_service.export_to_storage("k", "v") is None
    finally:
        get_settings.cache_clear()
