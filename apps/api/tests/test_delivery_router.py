"""Delivery Router（V1 PRD 2.0 / capability: delivery-router-v1）。

覆盖：目标授权 registry 验证/幂等；execute prepared-before-call；duplicate execute
不重复 attempt；timeout→unknown 不自动 retry；reconcile 契约；candidate mismatch；
账号变更新 target；copy package hash/media 一致；旧 workflow 直发路径对 v2 封锁。
"""




EDITOR = {"X-Studio-User": "editor@studio.local"}
PNG = b"\x89PNG\r\n\x1a\n" + b"cover" * 8


def test_wewrite_subprocess_error_does_not_return_secret(monkeypatch):
    from types import SimpleNamespace

    from app.services.content_harness.publishers.wechat_wewrite import WechatWewritePublisher

    secret = "token-super-private-123"

    def fail_run(*args, **kwargs):
        return SimpleNamespace(returncode=1, stdout="", stderr=f"Authorization: Bearer {secret}")

    from app.services.content_harness.publishers import wechat_wewrite

    monkeypatch.setattr(wechat_wewrite.subprocess, "run", fail_run)
    result = WechatWewritePublisher().deliver({
        "render": {"payload": {"title": "Approved", "markdown": "# Approved"}}, "_cover_bytes": b"cover",
    }, None, None)
    assert result.status == "failed"
    assert result.error == "publisher_execution_failed"
    assert secret not in repr(result)


def test_publisher_result_projection_rejects_nested_secret_and_unsafe_remote_id():
    from app.services.content_harness.contracts import PublisherResult
    from app.services.delivery import safe_publisher_result

    result = safe_publisher_result(PublisherResult(
        status="succeeded", remote_id="wx123\nAuthorization: Bearer secret",
        metadata={"channel": "wechat", "nested": {"token": "secret"}, "verified": True},
    ))
    assert result.status == "unknown"
    assert result.remote_id is None
    assert result.metadata == {"channel": "wechat"}
    assert "secret" not in repr(result)


