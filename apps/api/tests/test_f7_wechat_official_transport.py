"""Official HTTP fixtures never obtain tokens or touch a real account."""

import hashlib
import io
import json
import time
from copy import deepcopy

import pytest


def _experiment_scope():
    return {"account_id": 10, "appid": "wx0123456789abcdef", "candidate_id": 20,
            "candidate_hash": "b" * 64, "target_id": 30, "attempt_id": 40,
            "runtime_fingerprint": "a" * 64, "actor": "owner@example.com",
            "action": "auto_draft", "channel": "wechat", "content_form": "article"}


def test_short_experiment_authority_is_exact_signed_expiring_not_general(monkeypatch):
    from app.services import wechat_official as official

    monkeypatch.setenv("AICS_WECHAT_RUNTIME_IDENTITY_KEY", "k" * 32)
    scope = _experiment_scope()
    now = int(time.time())
    authority = official.sign_short_draft_authority(scope, expires_at=now + 120, now=now)
    assert official.check_short_draft_authority(authority, scope, now=now)
    assert official.remote_contract_ready() is False
    assert not official.check_short_draft_authority(authority, scope, now=now + 120)
    for key, value in {"account_id": 11, "appid": "wx" + "f" * 16, "candidate_id": 21,
                       "candidate_hash": "c" * 64, "target_id": 31, "attempt_id": 41,
                       "runtime_fingerprint": "d" * 64, "actor": "foreign@example.com",
                       "action": "manual_handoff", "channel": "x", "content_form": "single"}.items():
        assert not official.check_short_draft_authority(authority, {**scope, key: value}, now=now)
        forged = deepcopy(authority)
        forged["scope"][key] = value
        assert not official.check_short_draft_authority(forged, {**scope, key: value}, now=now)
    monkeypatch.setenv("AICS_WECHAT_RUNTIME_IDENTITY_KEY", "r" * 32)
    assert not official.check_short_draft_authority(authority, scope, now=now)


@pytest.mark.parametrize("mutation", [{"account_id": True}, {"attempt_id": 0}, {"action": "publish"},
                                      {"channel": "x"}, {"candidate_hash": "bad"}, {"extra": "untrusted"}])
def test_short_experiment_invalid_scope_cannot_be_signed(monkeypatch, mutation):
    from app.services import wechat_official as official

    monkeypatch.setenv("AICS_WECHAT_RUNTIME_IDENTITY_KEY", "k" * 32)
    now = int(time.time())
    with pytest.raises(ValueError, match="official_experiment_authority_invalid"):
        official.sign_short_draft_authority({**_experiment_scope(), **mutation}, expires_at=now + 120, now=now)


def test_short_experiment_authority_requires_key_and_bounded_expiry(monkeypatch):
    from app.services import wechat_official as official

    now = int(time.time())
    monkeypatch.delenv("AICS_WECHAT_RUNTIME_IDENTITY_KEY", raising=False)
    with pytest.raises(ValueError, match="official_experiment_authority_invalid"):
        official.sign_short_draft_authority(_experiment_scope(), expires_at=now + 120, now=now)
    monkeypatch.setenv("AICS_WECHAT_RUNTIME_IDENTITY_KEY", "k" * 32)
    for expiry in [now, now - 1, now + 901, True]:
        with pytest.raises(ValueError, match="official_experiment_authority_invalid"):
            official.sign_short_draft_authority(_experiment_scope(), expires_at=expiry, now=now)


def test_short_experiment_transport_exact_runtime_token_body_and_single_create(module, runtime, wire, monkeypatch):
    from app.services import wechat_official as official

    calls, replies, Response = wire
    monkeypatch.setattr(official, "remote_contract_ready", lambda: False)
    monkeypatch.setenv("AICS_WECHAT_RUNTIME_IDENTITY_KEY", "k" * 32)
    scope = _experiment_scope()
    authority = official.sign_short_draft_authority(scope, expires_at=int(time.time()) + 120)
    client = module.OfficialTransport(experiment_authority=authority, experiment_scope=scope)
    replies.extend([Response({"access_token": "token-a", "expires_in": 7200}), Response({"media_id": "draft-id"})])
    assert client.token(runtime) == "token-a"
    with pytest.raises(module.OfficialTransportError, match="official_experiment_scope_invalid"):
        client.upload_cover("foreign-token", b"\x89PNG\r\n\x1a\nbytes", "image/png")
    with pytest.raises(module.OfficialTransportError, match="official_experiment_body_limit"):
        client.create_draft("token-a", {"title": "标题", "author": "", "digest": "", "content": "中" * 683, "thumb_media_id": "cover-id"})
    assert len(calls) == 1
    article = {"title": "标题", "author": "", "digest": "", "content": "<p>测试</p>", "thumb_media_id": "cover-id"}
    assert client.create_draft("token-a", article) == "draft-id"
    with pytest.raises(module.OfficialTransportError, match="official_experiment_create_claimed"):
        client.create_draft("token-a", article)
    assert len(calls) == 2
    assert official.remote_contract_ready() is False


def test_short_experiment_transport_rejects_wrong_runtime_before_dns(module, runtime, monkeypatch):
    from app.services import wechat_official as official

    monkeypatch.setenv("AICS_WECHAT_RUNTIME_IDENTITY_KEY", "k" * 32)
    monkeypatch.setattr(module.socket, "getaddrinfo", lambda *a, **kw: pytest.fail("foreign runtime reached DNS"))
    scope = _experiment_scope()
    authority = official.sign_short_draft_authority(scope, expires_at=int(time.time()) + 120)
    client = module.OfficialTransport(experiment_authority=authority, experiment_scope=scope)
    foreign = official.AccountRuntime(11, runtime.appid, runtime.fingerprint, runtime.secret)
    with pytest.raises(module.OfficialTransportError, match="official_experiment_scope_invalid"):
        client.token(foreign)


def test_short_experiment_expiry_blocks_cached_token(module, runtime, wire, monkeypatch):
    from app.services import wechat_official as official

    calls, replies, Response = wire
    monkeypatch.setattr(official, "remote_contract_ready", lambda: False)
    monkeypatch.setenv("AICS_WECHAT_RUNTIME_IDENTITY_KEY", "k" * 32)
    now = int(time.time())
    authority = official.sign_short_draft_authority(_experiment_scope(), expires_at=now + 120, now=now)
    client = module.OfficialTransport(experiment_authority=authority, experiment_scope=_experiment_scope())
    replies.append(Response({"access_token": "token-a", "expires_in": 7200}))
    assert client.token(runtime) == "token-a"
    monkeypatch.setattr(official.time, "time", lambda: now + 120)
    with pytest.raises(module.OfficialTransportError, match="official_experiment_scope_invalid"):
        client.token(runtime)
    assert len(calls) == 1


def test_short_experiment_unconfirmed_create_cannot_repeat(module, runtime, wire, monkeypatch):
    from app.services import wechat_official as official

    calls, replies, Response = wire
    monkeypatch.setattr(official, "remote_contract_ready", lambda: False)
    monkeypatch.setenv("AICS_WECHAT_RUNTIME_IDENTITY_KEY", "k" * 32)
    authority = official.sign_short_draft_authority(_experiment_scope(), expires_at=int(time.time()) + 120)
    client = module.OfficialTransport(experiment_authority=authority, experiment_scope=_experiment_scope())
    replies.extend([Response({"access_token": "token-a", "expires_in": 7200}), Response({})])
    client.token(runtime)
    article = {"title": "标题", "author": "", "digest": "", "content": "<p>测试</p>", "thumb_media_id": "cover-id"}
    with pytest.raises(module.OfficialTransportError, match="official_response_unconfirmed"):
        client.create_draft("token-a", article)
    with pytest.raises(module.OfficialTransportError, match="official_experiment_create_claimed"):
        client.create_draft("token-a", article)
    assert len(calls) == 2


@pytest.mark.parametrize("delay_phase", ["dns", "tls"])
def test_short_experiment_expiry_during_connection_prevents_http(module, runtime, wire, monkeypatch, delay_phase):
    from app.services import wechat_official as official

    calls, replies, Response = wire
    replies.append(Response({"access_token": "token-a", "expires_in": 7200}))
    monkeypatch.setattr(official, "remote_contract_ready", lambda: False)
    monkeypatch.setenv("AICS_WECHAT_RUNTIME_IDENTITY_KEY", "k" * 32)
    now = int(time.time())
    clock = [now]
    authority = official.sign_short_draft_authority(_experiment_scope(), expires_at=now + 120, now=now)
    client = module.OfficialTransport(experiment_authority=authority, experiment_scope=_experiment_scope())
    monkeypatch.setattr(official.time, "time", lambda: clock[0])
    base_address = module._address
    base_connection = module._connection

    def address(deadline):
        result = base_address(deadline)
        if delay_phase == "dns":
            clock[0] = now + 120
        return result

    def connection(addr, deadline):
        result = base_connection(addr, deadline)

        def connect():
            if delay_phase == "tls":
                clock[0] = now + 120

        result.connect = connect
        return result

    monkeypatch.setattr(module, "_address", address)
    monkeypatch.setattr(module, "_connection", connection)
    with pytest.raises(module.OfficialTransportError, match="official_experiment_scope_invalid") as caught:
        client.token(runtime)
    assert caught.value.dispatched is False
    assert calls == []


@pytest.fixture
def module():
    from app.services import wechat_official_transport

    return wechat_official_transport


@pytest.fixture
def runtime():
    from app.services.wechat_official import AccountRuntime

    return AccountRuntime(10, "wx0123456789abcdef", "a" * 64, "s" * 32)


@pytest.fixture
def wire(module, monkeypatch):
    from app.services import wechat_official

    monkeypatch.setattr(wechat_official, "remote_contract_ready", lambda: True)
    monkeypatch.setattr(module.socket, "getaddrinfo", lambda *a, **kw: [(2, 1, 6, "", ("8.8.8.8", 443))])
    calls, replies = [], []

    class Response:
        status = 200

        def __init__(self, body, headers=None):
            self.body = io.BytesIO(json.dumps(body).encode())
            self.headers = headers or {"Content-Type": "application/json"}

        def getheader(self, key, default=None):
            return next((v for k, v in self.headers.items() if k.lower() == key.lower()), default)

        def getheaders(self):
            return list(self.headers.items())

        def read(self, amount):
            return self.body.read(amount)

    class Connection:
        def connect(self):
            pass

        def request(self, method, path, body=None, headers=None):
            calls.append({"method": method, "path": path, "body": body, "headers": headers})

        def getresponse(self):
            item = replies.pop(0)
            if isinstance(item, Exception):
                raise item
            return item

        def close(self):
            pass

    def connection(address, deadline):
        assert address[4] == ("8.8.8.8", 443)
        return Connection()

    monkeypatch.setattr(module, "_connection", connection)
    return calls, replies, Response


def test_transport_remote_gate_blocks_before_dns_and_cached_token(module, runtime, monkeypatch):
    monkeypatch.setattr(module.socket, "getaddrinfo", lambda *a, **k: pytest.fail("closed gate reached DNS"))
    client = module.OfficialTransport()
    client.cache.put(runtime, "cached-token", expires_in=7200)
    with pytest.raises(module.OfficialTransportError, match="official_contract_unresolved") as caught:
        client.token(runtime)
    assert caught.value.dispatched is False


def test_official_endpoints_exact_bytes_and_safe_readback(module, runtime, wire):
    calls, replies, Response = wire
    replies.extend([Response({"access_token": "token-a", "expires_in": 7200, "secret_echo": "NEVER_RETURN"}),
                    Response({"media_id": "cover-id"}), Response({"url": "https://mmbiz.qpic.cn/path/0?wx_fmt=png"}),
                    Response({"media_id": "draft-id"}), Response({"news_item": [{"title": "原文", "author": "", "digest": "", "content": "<p>原文</p>", "thumb_media_id": "cover-id", "url": "SECRET_PREVIEW"}]})])
    client = module.OfficialTransport()
    token = client.token(runtime)
    assert client.token(runtime) == token and len(calls) == 1
    image = b"\x89PNG\r\n\x1a\nexact-bytes"
    assert client.upload_cover(token, image, "image/png", "原始封面.png") == "cover-id"
    assert client.upload_inline(token, image, "image/png", "原始正文图.png") == "https://mmbiz.qpic.cn/path/0?wx_fmt=png"
    article = {"title": "原文", "author": "", "digest": "", "content": "<p>原文</p>", "thumb_media_id": "cover-id"}
    assert client.create_draft(token, article) == "draft-id"
    assert client.read_draft(token, "draft-id") == article
    assert [call["path"].split("?")[0] for call in calls] == ["/cgi-bin/token", "/cgi-bin/material/add_material", "/cgi-bin/media/uploadimg", "/cgi-bin/draft/add", "/cgi-bin/draft/get"]
    assert [call["method"] for call in calls] == ["GET", "POST", "POST", "POST", "POST"]
    assert "grant_type=client_credential" in calls[0]["path"]
    assert f"appid={runtime.appid}" in calls[0]["path"]
    assert f"secret={runtime.secret}" in calls[0]["path"]
    assert calls[0]["body"] is None
    assert image in calls[1]["body"] and image in calls[2]["body"]
    assert 'filename="原始封面.png"'.encode() in calls[1]["body"]
    assert 'filename="原始正文图.png"'.encode() in calls[2]["body"]
    assert "type=image" in calls[1]["path"]
    assert json.loads(calls[3]["body"])["articles"] == [{"article_type": "news", **article, "show_cover_pic": 0}]
    assert calls[3]["headers"]["Content-Type"] == "application/json; charset=utf-8"


@pytest.mark.parametrize("address", ["127.0.0.1", "198.18.0.1", "169.254.1.1", "224.0.0.1", "::1"])
def test_private_or_mixed_dns_refused_before_credentials(module, runtime, wire, monkeypatch, address):
    calls, _, _ = wire
    monkeypatch.setattr(module.socket, "getaddrinfo", lambda *a, **kw: [(2, 1, 6, "", ("8.8.8.8", 443)), (2, 1, 6, "", (address, 443))])
    with pytest.raises(module.OfficialTransportError) as caught:
        module.OfficialTransport().token(runtime)
    assert caught.value.code == "official_network_unavailable" and not caught.value.dispatched
    assert calls == []


@pytest.mark.parametrize("problem", ["redirect", "compressed", "mime", "oversize", "timeout", "api-error", "malformed"])
def test_unsafe_response_no_retry_or_secret_echo(module, runtime, wire, monkeypatch, caplog, problem):
    calls, replies, Response = wire
    response = Response({"access_token": "token-a", "expires_in": 7200, "errmsg": "SECRET_ECHO"})
    if problem == "redirect":
        response.status = 302
        response.headers["Location"] = "https://attacker.invalid/?secret=SECRET_ECHO"
    elif problem == "compressed":
        response.headers["Content-Encoding"] = "gzip"
    elif problem == "mime":
        response.headers["Content-Type"] = "text/html"
    elif problem == "oversize":
        monkeypatch.setattr(module, "MAX_RESPONSE_BYTES", 20)
    elif problem == "timeout":
        response = TimeoutError("SECRET_ECHO")
    elif problem == "api-error":
        response = Response({"errcode": 40001, "errmsg": "SECRET_ECHO"})
    else:
        response.body = io.BytesIO(b'{"access_token":"token-a","access_token":"SECRET_ECHO"}')
    replies.append(response)
    with pytest.raises(module.OfficialTransportError) as caught:
        module.OfficialTransport().token(runtime)
    assert len(calls) == 1
    assert "SECRET_ECHO" not in str(caught.value) + repr(caught.value) + caplog.text
    assert caught.value.dispatched is True


def test_stream_read_deadline_enforced_after_empty_response(module, runtime, wire, monkeypatch):
    _, replies, Response = wire
    clock = [0.0]
    monkeypatch.setattr(module.time, "monotonic", lambda: clock[0])
    response = Response({})
    def read(amount):
        clock[0] = 26
        return b""
    response.read = read
    replies.append(response)
    with pytest.raises(module.OfficialTransportError, match="official_response_unconfirmed"):
        module.OfficialTransport().token(runtime)


@pytest.mark.parametrize("field,value", [("access_token", []), ("expires_in", True), ("expires_in", 1)])
def test_invalid_token_response_never_enters_cache(module, runtime, wire, field, value):
    _, replies, Response = wire
    body = {"access_token": "token-a", "expires_in": 7200, field: value}
    replies.append(Response(body))
    client = module.OfficialTransport()
    with pytest.raises(module.OfficialTransportError):
        client.token(runtime)
    assert client.cache.get(runtime) is None


def test_invalid_upload_never_transforms_or_dispatches(module, wire):
    calls, _, _ = wire
    for content, mime in [(b"<svg>bad</svg>", "image/svg+xml"), (b"bad", "image/png"), (b"\x89PNG\r\n\x1a\n" + b"x" * 1_000_000, "image/png")]:
        with pytest.raises(module.OfficialTransportError) as caught:
            module.OfficialTransport().upload_inline("token-a", content, mime)
        assert not caught.value.dispatched
    assert not calls


@pytest.mark.parametrize("url", ["https://mmbiz.qpic.cn:SENSITIVE_CANARY/path", "https://[SENSITIVE_CANARY/path"])
def test_resource_url_parser_errors_are_redacted(url):
    from app.services.wechat_official_render import remote_image_url

    with pytest.raises(ValueError) as caught:
        remote_image_url(url)
    assert str(caught.value) == "official_resource_mapping_invalid"
    assert "SENSITIVE_CANARY" not in str(caught.value)


def test_connection_pins_checked_address_and_original_tls_host(module, monkeypatch):
    events = []

    class Socket:
        def settimeout(self, value):
            assert 0 < value <= 25

        def connect(self, address):
            events.append(("connect", address))

        def close(self):
            events.append(("close",))

    class Context:
        check_hostname = True
        verify_mode = module.ssl.CERT_REQUIRED

        def wrap_socket(self, sock, server_hostname):
            events.append(("tls", server_hostname))
            return sock

    monkeypatch.setattr(module.socket, "socket", lambda *args: Socket())
    monkeypatch.setattr(module.ssl, "create_default_context", lambda: Context())
    monkeypatch.setattr(module.socket, "getaddrinfo", lambda *args, **kwargs: pytest.fail("second DNS resolution"))
    connection = module._PinnedConnection((2, 1, 6, "", ("8.8.8.8", 443)), module.time.monotonic() + 25)
    connection.connect()
    assert events == [("connect", ("8.8.8.8", 443)), ("tls", "api.weixin.qq.com")]
    assert connection.debuglevel == 0
    connection.close()
    assert events[-1] == ("close",)


def test_dns_capacity_is_bounded_before_resolution(module, monkeypatch):
    from threading import BoundedSemaphore

    slots = BoundedSemaphore(1)
    slots.acquire()
    monkeypatch.setattr(module, "_DNS_SLOTS", slots)
    monkeypatch.setattr(module.socket, "getaddrinfo", lambda *args, **kwargs: pytest.fail("capacity bypass"))
    with pytest.raises(OSError, match="official_dns_capacity"):
        module._address(module.time.monotonic() + 25)


def test_wire_reader_enforces_deadline_and_total_budget(module, monkeypatch):
    clock = [0.0]
    monkeypatch.setattr(module.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(module, "MAX_RESPONSE_BYTES", 1)
    monkeypatch.setattr(module, "MAX_HEADER_BYTES", 1)

    class Socket:
        def settimeout(self, value):
            assert value == 25

        def recv_into(self, buffer):
            return len(buffer)

    reader = module._DeadlineReader(Socket(), 25)
    with pytest.raises(OSError, match="official_wire_limit"):
        reader.readinto(bytearray(3))
    clock[0] = 26
    with pytest.raises(TimeoutError, match="official_deadline"):
        reader.readinto(bytearray(1))


@pytest.mark.parametrize("filename", ["wechat_official_transport.py", "wechat_official_render.py"])
def test_implementation_fingerprint_tracks_transport_and_render(monkeypatch, filename):
    from pathlib import Path

    from app.services.wechat_official import implementation_fingerprint

    original = Path.read_bytes
    before = implementation_fingerprint()
    monkeypatch.setattr(Path, "read_bytes", lambda path: original(path) + (b"changed-implementation" if path.name == filename else b""))
    assert implementation_fingerprint() != before


def test_frozen_resource_substitution_bound_to_exact_account_and_bytes(runtime):
    from test_f7_wechat_official_render import _inline_article

    from app.services.wechat_official_render import build_article_render, match_readback, prepare_article

    content, assets = _inline_article()
    render = build_article_render(content, assets, [])
    manifest = {"schema_version": 5, "content": content, "assets": assets, "evidence_refs": [], "official_render": render}
    original = deepcopy(manifest)
    mapping = [{**slot, "account_id": runtime.account_id, "appid": runtime.appid, "runtime_fingerprint": runtime.fingerprint,
                "remote_ref": "cover-id" if slot["usage"] == "cover" else "https://mmbiz.qpic.cn/path/0?wx_fmt=png"} for slot in render["asset_slots"]]
    article = prepare_article(manifest, runtime, mapping)
    assert 'src="https://mmbiz.qpic.cn/path/0?wx_fmt=png"' in article["content"]
    assert article["thumb_media_id"] == "cover-id" and manifest == original
    assert match_readback(article, article) == hashlib.sha256(json.dumps(article, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    changed = {**article, "content": article["content"] + "变更"}
    with pytest.raises(ValueError, match="official_readback_mismatch"):
        match_readback(article, changed)
    for field, value in [("account_id", 11), ("appid", "wxfedcba9876543210"), ("runtime_fingerprint", "b" * 64), ("content_hash", "c" * 64), ("remote_ref", "https://evil.invalid/?token=secret")]:
        bad = deepcopy(mapping)
        bad[1][field] = value
        with pytest.raises(ValueError):
            prepare_article(manifest, runtime, bad)
    with pytest.raises(ValueError):
        prepare_article(manifest, runtime, mapping[:-1])
    with pytest.raises(ValueError):
        prepare_article({k: v for k, v in manifest.items() if k != "official_render"}, runtime, mapping)
