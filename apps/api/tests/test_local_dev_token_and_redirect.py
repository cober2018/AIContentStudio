"""本机口令与跨主机下载跳转。"""

import httpx
import pytest

from app.config import get_settings
from app.services import url_fetch


def test_local_dev_token_required_when_configured(client, monkeypatch):
    monkeypatch.setenv("LOCAL_DEV_TOKEN", "s3cret-token")
    get_settings.cache_clear()
    try:
        denied = client.get("/api/v1/users/me", headers={"X-Studio-User": "admin@studio.local"})
        allowed = client.get(
            "/api/v1/users/me",
            headers={"X-Studio-User": "admin@studio.local", "X-Studio-Local-Token": "s3cret-token"},
        )
        assert denied.status_code == 401
        assert allowed.status_code == 200
        assert allowed.json()["email"] == "admin@studio.local"
    finally:
        monkeypatch.delenv("LOCAL_DEV_TOKEN", raising=False)
        get_settings.cache_clear()


def test_safe_fetch_strips_credentials_when_redirect_leaves_the_host(monkeypatch):
    seen = []

    def handler(request):
        seen.append((str(request.url), request.headers.get("authorization")))
        if request.url.host == "example.org":
            return httpx.Response(302, headers={"location": "https://cdn.example/file.mp4?sig=1"})
        return httpx.Response(200, content=b"ok-video")

    real_client = httpx.Client
    monkeypatch.setattr(url_fetch.httpx, "Client", lambda **kwargs: real_client(**(kwargs | {"transport": httpx.MockTransport(handler)})))
    monkeypatch.setattr(url_fetch, "pinned_transport", lambda *args, **kwargs: None)
    monkeypatch.setattr(url_fetch, "_validate_target", lambda url: None)
    body, _mime = url_fetch.safe_fetch("https://example.org/content", headers={"Authorization": "Bearer secret"})
    assert body == b"ok-video"
    assert seen == [
        ("https://example.org/content", "Bearer secret"),
        ("https://cdn.example/file.mp4?sig=1", None),
    ]


def test_safe_fetch_refuses_https_downgrade_on_redirect(monkeypatch):
    calls = []

    def handler(request):
        calls.append(str(request.url))
        return httpx.Response(302, headers={"location": "http://cdn.example/file.mp4"})

    real_client = httpx.Client
    monkeypatch.setattr(url_fetch.httpx, "Client", lambda **kwargs: real_client(**(kwargs | {"transport": httpx.MockTransport(handler)})))
    monkeypatch.setattr(url_fetch, "pinned_transport", lambda *args, **kwargs: None)
    monkeypatch.setattr(url_fetch, "_validate_target", lambda url: None)
    with pytest.raises(url_fetch.UnsafeUrlError, match="https"):
        url_fetch.safe_fetch("https://example.org/content", headers={"Authorization": "Bearer secret"})
    assert calls == ["https://example.org/content"]
