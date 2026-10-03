"""Single-shot official HTTP with no URL logs, retries, proxies or account fallback."""

from __future__ import annotations

import http.client
import io
import ipaddress
import json
import re
import secrets
import socket
import ssl
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from copy import deepcopy
from threading import BoundedSemaphore
from urllib.parse import urlencode

from . import wechat_official
from .url_fetch import OUTBOUND_HTTP_POLICIES, enforce_outbound_host

HOST = "api.weixin.qq.com"
MAX_RESPONSE_BYTES = OUTBOUND_HTTP_POLICIES["wechat"].response_bytes
MAX_JSON_REQUEST_BYTES = 1_048_576
MAX_HEADER_BYTES = 65_536
STEP_TIMEOUT = OUTBOUND_HTTP_POLICIES["wechat"].timeout_seconds
_DNS_POOL = ThreadPoolExecutor(max_workers=2, thread_name_prefix="official-dns")
_DNS_SLOTS = BoundedSemaphore(2)
_TOKEN = re.compile(r"[A-Za-z0-9_.-]{1,2048}")
_REMOTE_ID = re.compile(r"[A-Za-z0-9_-]{1,128}")
_PATHS = {"token": "/cgi-bin/token", "cover": "/cgi-bin/material/add_material",
          "inline": "/cgi-bin/media/uploadimg", "create": "/cgi-bin/draft/add", "read": "/cgi-bin/draft/get"}
_ARTICLE_FIELDS = {"title": 32, "author": 16, "digest": 120, "content": MAX_RESPONSE_BYTES, "thumb_media_id": 128}
_ERROR_CODES = {"official_contract_unresolved", "official_request_invalid", "official_response_unconfirmed",
                "official_network_unavailable", "official_api_rejected", "official_asset_unsupported",
                "official_experiment_scope_invalid", "official_experiment_body_limit",
                "official_experiment_create_claimed"}
_DIAGNOSTIC_VALUES = {
    "phase": {"dns", "connect", "send", "response_headers", "response_body", "response_json", "response_contract"},
    "reason": {"io_failure", "deadline", "tls", "protocol", "http_status", "header_limit", "content_type",
               "content_encoding", "body_limit", "invalid_json", "invalid_response", "api_rejected"},
    "response_type": {"json", "text", "html", "missing", "other"},
}


class OfficialTransportError(ValueError):
    def __init__(self, code: str, *, dispatched: bool = False, phase=None, reason=None,
                 http_status=None, response_type=None):
        self.code, self.dispatched = code, dispatched
        self.phase, self.reason = phase, reason
        self.http_status, self.response_type = http_status, response_type
        super().__init__(code)


def failure_diagnostic(error):
    # Filter again at persistence: exception attributes need not originate in this transport.
    result = {"code": "official_error_unclassified", "dispatch_hint": None}
    if not isinstance(error, OfficialTransportError):
        return result
    if type(error.code) is str and error.code in _ERROR_CODES:
        result["code"] = error.code
    if type(error.dispatched) is bool:
        result["dispatch_hint"] = error.dispatched
    for key, allowed in _DIAGNOSTIC_VALUES.items():
        value = getattr(error, key, None)
        if type(value) is str and value in allowed:
            result[key] = value
    status = getattr(error, "http_status", None)
    if type(status) is int and 100 <= status <= 599:
        result["http_status"] = status
    return result


def _remaining(deadline: float) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("official_deadline")
    return remaining


def _address(deadline: float):
    enforce_outbound_host("https://" + HOST)
    if not _DNS_SLOTS.acquire(blocking=False):
        raise OSError("official_dns_capacity")
    try:
        future = _DNS_POOL.submit(socket.getaddrinfo, HOST, 443, type=socket.SOCK_STREAM)
    except Exception:
        _DNS_SLOTS.release()
        raise
    future.add_done_callback(lambda _: _DNS_SLOTS.release())
    addresses = future.result(timeout=_remaining(deadline))
    _remaining(deadline)
    if not addresses or any(
        not ipaddress.ip_address(row[4][0]).is_global or ipaddress.ip_address(row[4][0]).is_multicast
        or row[4][1] != 443 or row[0] not in (socket.AF_INET, socket.AF_INET6) for row in addresses
    ):
        raise OSError("official_dns_invalid")
    return addresses[0]


class _DeadlineReader(io.RawIOBase):
    def __init__(self, sock, deadline):
        self.sock, self.deadline, self.received = sock, deadline, 0

    def readable(self):
        return True

    def readinto(self, buffer):
        self.sock.settimeout(_remaining(self.deadline))
        count = self.sock.recv_into(buffer)
        _remaining(self.deadline)
        self.received += count
        if self.received > MAX_RESPONSE_BYTES + MAX_HEADER_BYTES:
            raise OSError("official_wire_limit")
        return count


class _DeadlineSocket:
    def __init__(self, sock, deadline):
        self.sock, self.deadline = sock, deadline

    def sendall(self, data):
        self.sock.settimeout(_remaining(self.deadline))
        self.sock.sendall(data)
        _remaining(self.deadline)

    def makefile(self, mode):
        if mode != "rb":
            raise OSError("official_stream_mode")
        return io.BufferedReader(_DeadlineReader(self.sock, self.deadline))

    def close(self):
        self.sock.close()


class _PinnedConnection(http.client.HTTPSConnection):
    def __init__(self, address, deadline):
        super().__init__(HOST, 443, timeout=_remaining(deadline), context=ssl.create_default_context())
        self.address, self.deadline = address, deadline
        self.set_debuglevel(0)

    def connect(self):
        family, socktype, proto, _, sockaddr = self.address
        sock = socket.socket(family, socktype, proto)
        try:
            sock.settimeout(_remaining(self.deadline))
            sock.connect(sockaddr)
            sock.settimeout(_remaining(self.deadline))
            secure = self._context.wrap_socket(sock, server_hostname=HOST)
            self.sock = _DeadlineSocket(secure, self.deadline)
        except Exception:
            sock.close()
            raise


def _connection(address, deadline):
    return _PinnedConnection(address, deadline)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def _json(body):
    try:
        encoded = json.dumps(body, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()
    except (ValueError, TypeError, RecursionError):
        raise OfficialTransportError("official_request_invalid") from None
    if len(encoded) > MAX_JSON_REQUEST_BYTES:
        raise OfficialTransportError("official_request_invalid")
    return encoded


def _enabled():
    if not wechat_official.remote_contract_ready():
        raise OfficialTransportError("official_contract_unresolved")


def _token(value):
    if not isinstance(value, str) or _TOKEN.fullmatch(value) is None:
        raise OfficialTransportError("official_request_invalid")
    return value


def _remote_id(value, *, dispatched=False):
    if not isinstance(value, str) or _REMOTE_ID.fullmatch(value) is None:
        raise OfficialTransportError("official_response_unconfirmed" if dispatched else "official_request_invalid",
                                     dispatched=dispatched, phase="response_contract" if dispatched else None,
                                     reason="invalid_response" if dispatched else None)
    return value


def _article(value, *, dispatched=False):
    if (not isinstance(value, dict) or set(value) != set(_ARTICLE_FIELDS)
            or any(not isinstance(value[key], str) or len(value[key]) > limit for key, limit in _ARTICLE_FIELDS.items())
            or not value["title"] or not value["content"]):
        raise OfficialTransportError("official_response_unconfirmed" if dispatched else "official_request_invalid",
                                     dispatched=dispatched, phase="response_contract" if dispatched else None,
                                     reason="invalid_response" if dispatched else None)
    _remote_id(value["thumb_media_id"], dispatched=dispatched)
    return dict(value)


class OfficialTransport:
    def __init__(self, *, experiment_authority=None, experiment_scope=None):
        self.cache = wechat_official.TokenCache()
        self._experiment = experiment_authority is not None or experiment_scope is not None
        self._authority = deepcopy(experiment_authority)
        self._scope = deepcopy(experiment_scope)
        self._bound_token = None
        self._create_claimed = False

    def _enabled(self):
        if self._experiment:
            if not wechat_official.check_draft_authority(self._authority, self._scope):
                raise OfficialTransportError("official_experiment_scope_invalid")
        else:
            _enabled()

    def _check_token(self, token):
        self._enabled()
        if self._experiment and (self._bound_token is None or token != self._bound_token):
            raise OfficialTransportError("official_experiment_scope_invalid")

    def _request(self, operation, body, content_type="application/json", token=None, *, method="POST", query=None):
        self._enabled()
        if operation != "token":
            self._check_token(token)
        if (operation not in _PATHS or (body is not None and not isinstance(body, bytes))
                or len(body or b"") > OUTBOUND_HTTP_POLICIES["wechat"].request_bytes):
            raise OfficialTransportError("official_request_invalid")
        query = dict(query or {})
        if operation != "token":
            query["access_token"] = _token(token)
        if operation == "cover":
            query["type"] = "image"
        path = _PATHS[operation] + ("?" + urlencode(query) if query else "")
        deadline, dispatched, connection = time.monotonic() + STEP_TIMEOUT, False, None
        phase, reason, status, response_type = "dns", "io_failure", None, None
        try:
            address = _address(deadline)
            self._enabled()
            phase = "connect"
            connection = _connection(address, deadline)
            connection.connect()
            _remaining(deadline)
            # DNS/TLS may consume the remaining authority lifetime without sending any HTTP bytes.
            self._enabled()
            dispatched = True
            headers = {"Host": HOST, "Accept-Encoding": "identity", "Connection": "close"}
            if body is not None:
                headers["Content-Length"] = str(len(body))
            if content_type is not None:
                headers["Content-Type"] = content_type
            phase = "send"
            connection.request(method, path, body=body, headers=headers)
            phase = "response_headers"
            response = connection.getresponse()
            _remaining(deadline)
            status = response.status
            mime = response.getheader("Content-Type", "").split(";")[0].strip().lower()
            response_type = {"application/json": "json", "text/plain": "text", "text/html": "html", "": "missing"}.get(mime, "other")
            if status != 200:
                reason = "http_status"
                raise ValueError("official_http_invalid")
            if sum(len(k) + len(v) + 4 for k, v in response.getheaders()) > MAX_HEADER_BYTES:
                reason = "header_limit"
                raise ValueError("official_http_invalid")
            # WeChat may label JSON as text/plain; both still use the same strict parser below.
            if mime not in {"application/json", "text/plain"}:
                reason = "content_type"
                raise ValueError("official_http_invalid")
            if response.getheader("Content-Encoding", "identity").strip().lower() != "identity":
                reason = "content_encoding"
                raise ValueError("official_http_invalid")
            phase = "response_body"
            chunks, size = [], 0
            while True:
                _remaining(deadline)
                chunk = response.read(min(65_536, MAX_RESPONSE_BYTES - size + 1))
                _remaining(deadline)
                size += len(chunk)
                if size > MAX_RESPONSE_BYTES:
                    reason = "body_limit"
                    raise ValueError("official_response_limit")
                if not chunk:
                    break
                chunks.append(chunk)
            phase, reason = "response_json", "invalid_json"
            result = json.loads(b"".join(chunks), object_pairs_hook=_unique_object,
                                parse_constant=lambda _: (_ for _ in ()).throw(ValueError("invalid_json_constant")))
            phase, reason = "response_contract", "invalid_response"
            if not isinstance(result, dict) or ("errcode" in result and type(result["errcode"]) is not int):
                raise ValueError("official_response_invalid")
            if result.get("errcode", 0) != 0:
                raise OfficialTransportError("official_api_rejected", dispatched=dispatched, phase=phase,
                                             reason="api_rejected", http_status=status, response_type=response_type)
            return result
        except OfficialTransportError:
            raise
        except (OSError, ValueError, TypeError, RecursionError, http.client.HTTPException, FutureTimeout) as error:
            if isinstance(error, (TimeoutError, FutureTimeout)):
                reason = "deadline"
            elif isinstance(error, ssl.SSLError):
                reason = "tls"
            elif isinstance(error, http.client.HTTPException):
                reason = "protocol"
            raise OfficialTransportError("official_response_unconfirmed" if dispatched else "official_network_unavailable",
                                         dispatched=dispatched, phase=phase, reason=reason,
                                         http_status=status, response_type=response_type) from None
        finally:
            if connection is not None:
                try:
                    connection.close()
                except OSError:
                    pass

    def token(self, runtime):
        self._enabled()
        if self._experiment and (
            runtime.account_id != self._scope["account_id"]
            or runtime.appid != self._scope["appid"]
            or runtime.fingerprint != self._scope["runtime_fingerprint"]
        ):
            raise OfficialTransportError("official_experiment_scope_invalid")
        if (type(runtime.account_id) is not int or runtime.account_id <= 0
                or not re.fullmatch(r"wx[0-9a-f]{16}", runtime.appid)
                or not re.fullmatch(r"[A-Za-z0-9_-]{32,128}", runtime.secret)):
            raise OfficialTransportError("official_request_invalid")
        cached = self.cache.get(runtime)
        if cached:
            self._bound_token = cached
            return cached
        result = self._request("token", None, content_type=None, method="GET", query={
            "grant_type": "client_credential", "appid": runtime.appid, "secret": runtime.secret,
        })
        token, expires = result.get("access_token"), result.get("expires_in")
        if not isinstance(token, str) or _TOKEN.fullmatch(token) is None or type(expires) is not int or not 60 <= expires <= 7200:
            raise OfficialTransportError("official_response_unconfirmed", dispatched=True,
                                         phase="response_contract", reason="invalid_response")
        self.cache.put(runtime, token, expires_in=expires)
        self._bound_token = token
        return token

    def _upload(self, operation, token, content, mime, filename=None):
        self._check_token(token)
        signature = {"image/png": b"\x89PNG\r\n\x1a\n", "image/jpeg": b"\xff\xd8\xff"}.get(mime)
        limit = 1_000_000 if operation == "inline" else 10 * 1024 * 1024
        if not isinstance(content, bytes) or not signature or not content.startswith(signature) or not len(signature) < len(content) < limit:
            raise OfficialTransportError("official_asset_unsupported")
        if filename is None:
            filename = "media.png" if mime == "image/png" else "media.jpg"
        from .wechat_official_render import validate_upload_filename

        try:
            validate_upload_filename(filename)
        except ValueError:
            raise OfficialTransportError("official_request_invalid")
        boundary = "aics" + secrets.token_hex(24)
        prefix = (f'--{boundary}\r\nContent-Disposition: form-data; name="media"; filename="{filename}"\r\n'
                  f'Content-Type: {mime}\r\n\r\n').encode()
        return self._request(operation, prefix + content + f"\r\n--{boundary}--\r\n".encode(),
                             f"multipart/form-data; boundary={boundary}", token)

    def upload_cover(self, token, content, mime, filename=None):
        return _remote_id(self._upload("cover", token, content, mime, filename).get("media_id"), dispatched=True)

    def upload_inline(self, token, content, mime, filename=None):
        from .wechat_official_render import remote_image_url

        value = self._upload("inline", token, content, mime, filename).get("url")
        try:
            return remote_image_url(value)
        except ValueError:
            raise OfficialTransportError("official_response_unconfirmed", dispatched=True,
                                         phase="response_contract", reason="invalid_response") from None

    def create_draft(self, token, article):
        self._check_token(token)
        article = _article(article)
        if self._experiment:
            from .wechat_official_render import validate_html_draft_body, validate_short_draft_body

            try:
                validator = validate_html_draft_body if self._authority["schema"] == "wechat.html-draft.authority.v1" else validate_short_draft_body
                validator(article["content"])
            except ValueError:
                raise OfficialTransportError("official_experiment_body_limit") from None
            if self._create_claimed:
                raise OfficialTransportError("official_experiment_create_claimed")
        body = {"articles": [{"article_type": "news", **article, "show_cover_pic": 0}]}
        encoded = _json(body)
        # A lost response must never become permission to create a second draft.
        self._create_claimed = True
        return _remote_id(self._request("create", encoded, "application/json; charset=utf-8", token=token)
                           .get("media_id"), dispatched=True)

    def read_draft(self, token, draft_id):
        self._check_token(token)
        result = self._request("read", _json({"media_id": _remote_id(draft_id)}), token=token)
        items = result.get("news_item")
        if not isinstance(items, list) or len(items) != 1 or not isinstance(items[0], dict) or items[0].get("article_type", "news") != "news":
            raise OfficialTransportError("official_response_unconfirmed", dispatched=True,
                                         phase="response_contract", reason="invalid_response")
        return _article({key: items[0].get(key) for key in _ARTICLE_FIELDS}, dispatched=True)
