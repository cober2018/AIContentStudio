"""URL Import 安全抓取：防 SSRF（执行计划 STU-024 / STU-161）。"""

import ipaddress
import json
import logging
import re
import socket
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from threading import BoundedSemaphore
from types import MappingProxyType
from urllib.parse import urlparse

import httpx
from httpcore import ConnectTimeout, ReadTimeout, WriteError, WriteTimeout
from httpcore._backends.base import NetworkStream
from httpcore._backends.sync import SyncBackend
from httpcore._exceptions import map_exceptions

from ..config import get_settings

MAX_REDIRECTS = 3


@dataclass(frozen=True)
class OutboundLimits:
    timeout_seconds: float
    request_bytes: int
    response_bytes: int


OUTBOUND_HTTP_POLICIES = MappingProxyType({
    "fetch": OutboundLimits(10, 1_000_000, 5 * 1024 * 1024),
    "connector": OutboundLimits(10, 1_000_000, 1_000_000),
    "model_discovery": OutboundLimits(10, 1_000_000, 2_000_000),
    "model_generation": OutboundLimits(120, 1_000_000, 2_000_000),
    "image": OutboundLimits(25, 1_000_000, 8 * 1024 * 1024),
    "commons": OutboundLimits(15, 0, 5_000_000),
    "wechat": OutboundLimits(25, 11 * 1024 * 1024, 1_048_576),
    "minimax_download": OutboundLimits(120, 0, 30 * 1024 * 1024),
    "dsh": OutboundLimits(2.5, 0, 0),
})
MAX_OUTBOUND_TIMEOUT_SECONDS = OUTBOUND_HTTP_POLICIES["fetch"].timeout_seconds
MAX_OUTBOUND_REQUEST_BYTES = OUTBOUND_HTTP_POLICIES["fetch"].request_bytes
MAX_OUTBOUND_RESPONSE_BYTES = OUTBOUND_HTTP_POLICIES["fetch"].response_bytes
_DNS_POOL = ThreadPoolExecutor(max_workers=2, thread_name_prefix="fetch-dns")
_DNS_SLOTS = BoundedSemaphore(2)
_OUTBOUND_DEADLINE = ContextVar("outbound_deadline", default=None)


class _PrivateOutboundLogs(logging.Filter):
    def filter(self, _record):
        return _OUTBOUND_DEADLINE.get() is None


for _logger in ("httpx", "httpcore.connection", "httpcore.http11", "httpcore.http2", "httpcore.proxy"):
    logging.getLogger(_logger).addFilter(_PrivateOutboundLogs())


@contextmanager
def outbound_scope(deadline: float):
    previous = _OUTBOUND_DEADLINE.get()
    token = _OUTBOUND_DEADLINE.set(min(previous, deadline) if previous is not None else deadline)
    try:
        yield
    finally:
        _OUTBOUND_DEADLINE.reset(token)


def _remaining_timeout(deadline, timeout, error=ConnectTimeout):
    if deadline is None:
        return timeout
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise error("outbound_deadline")
    return remaining if timeout is None else min(remaining, timeout)


class _DeadlineStream(NetworkStream):
    def __init__(self, stream, deadline):
        self.stream, self.deadline = stream, deadline

    def read(self, max_bytes, timeout=None):
        result = self.stream.read(max_bytes, timeout=_remaining_timeout(self.deadline, timeout, ReadTimeout))
        _remaining_timeout(self.deadline, None, ReadTimeout)
        return result

    def write(self, buffer, timeout=None):
        # SyncStream's send loop resets an idle timeout; bound each actual send instead.
        sock = self.stream.get_extra_info("socket")
        if sock is None:
            self.stream.write(buffer, timeout=_remaining_timeout(self.deadline, timeout, WriteTimeout))
            _remaining_timeout(self.deadline, None, WriteTimeout)
            return
        with map_exceptions({socket.timeout: WriteTimeout, OSError: WriteError}):
            pending = memoryview(buffer)
            while pending:
                sock.settimeout(_remaining_timeout(self.deadline, timeout, WriteTimeout))
                count = sock.send(pending[:65536])
                if not count:
                    raise WriteError("outbound_write_closed")
                pending = pending[count:]
                _remaining_timeout(self.deadline, None, WriteTimeout)

    def start_tls(self, ssl_context, server_hostname=None, timeout=None):
        stream = self.stream.start_tls(ssl_context, server_hostname=server_hostname,
                                      timeout=_remaining_timeout(self.deadline, timeout))
        try:
            _remaining_timeout(self.deadline, None)
        except ConnectTimeout:
            stream.close()
            raise
        return _DeadlineStream(stream, self.deadline)

    def close(self):
        self.stream.close()

    def get_extra_info(self, info):
        return self.stream.get_extra_info(info)


class DeadlineBackend(SyncBackend):
    def __init__(self, deadline=None):
        self.deadline = deadline if deadline is not None else _OUTBOUND_DEADLINE.get()

    def connect_tcp(self, host, port, timeout=None, local_address=None, socket_options=None):
        stream = super().connect_tcp(host, port, timeout=_remaining_timeout(self.deadline, timeout),
                                     local_address=local_address, socket_options=socket_options)
        if self.deadline is None:
            return stream
        try:
            _remaining_timeout(self.deadline, None)
        except ConnectTimeout:
            stream.close()
            raise
        return _DeadlineStream(stream, self.deadline)


class UnsafeUrlError(ValueError):
    pass


def enforce_outbound_host(url: str) -> None:
    raw = getattr(get_settings(), "outbound_allowed_hosts", "")
    if not raw:
        return
    if not isinstance(raw, str) or len(raw) > 5000:
        raise UnsafeUrlError("outbound_host_policy_invalid")
    entries = [item.strip().lower() for item in raw.split(",")]
    if not 0 < len(entries) <= 100 or any(not entry for entry in entries):
        raise UnsafeUrlError("outbound_host_policy_invalid")
    for entry in entries:
        try:
            ipaddress.ip_address(entry)
        except ValueError:
            if (len(entry) > 253 or not re.fullmatch(r"[a-z0-9.-]+", entry)
                    or any(not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
                           for label in entry.split("."))):
                raise UnsafeUrlError("outbound_host_policy_invalid") from None
    try:
        host = urlparse(url).hostname
    except ValueError:
        raise UnsafeUrlError("outbound_host_forbidden") from None
    if host is None or host.lower() not in entries:
        raise UnsafeUrlError("outbound_host_forbidden")


def resolve_addresses(host: str, port: int, *, timeout: float = 4):
    if not _DNS_SLOTS.acquire(blocking=False):
        raise UnsafeUrlError("来源网络解析繁忙")
    try:
        future = _DNS_POOL.submit(socket.getaddrinfo, host, port, type=socket.SOCK_STREAM)
    except Exception:
        _DNS_SLOTS.release()
        raise
    future.add_done_callback(lambda _: _DNS_SLOTS.release())
    try:
        return future.result(timeout=_remaining_timeout(_OUTBOUND_DEADLINE.get(), timeout))
    except (OSError, FutureTimeout, ConnectTimeout):
        raise UnsafeUrlError("来源网络地址不可用") from None


def _json_request_body(json_body: dict | None) -> bytes | None:
    if json_body is None:
        return None
    try:
        body = json.dumps(json_body, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as exc:
        raise UnsafeUrlError("请求体不是有效 JSON") from exc
    if len(body) > MAX_OUTBOUND_REQUEST_BYTES:
        raise UnsafeUrlError("请求体超过大小限制")
    return body


class _PinnedBackend(DeadlineBackend):
    def __init__(self, host: str, port: int, address: str, deadline=None):
        super().__init__(deadline)
        self.host, self.port, self.address = host, port, address

    def connect_tcp(self, host, port, timeout=None, local_address=None, socket_options=None):
        if (host, port) != (self.host, self.port):
            raise OSError("fetch_target_mismatch")
        # Only TCP is rewritten; TLS certificate/SNI and HTTP Host retain the URL hostname.
        return super().connect_tcp(self.address, port, timeout=timeout,
                                   local_address=local_address, socket_options=socket_options)


def pinned_transport(url: str, *, allow_http: bool = False, allow_private: bool = False) -> httpx.HTTPTransport:
    enforce_outbound_host(url)
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ({"http", "https"} if allow_http else {"https"}) or not parsed.hostname or parsed.username or parsed.password:
            raise UnsafeUrlError("仅允许无凭据 HTTP(S) 来源")
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        addresses = resolve_addresses(parsed.hostname, port)
        if not addresses or (not allow_private and any(
            not ipaddress.ip_address(info[4][0]).is_global
            or ipaddress.ip_address(info[4][0]).is_multicast
            for info in addresses
        )):
            raise UnsafeUrlError("禁止访问内网/保留地址")
    except (OSError, ValueError) as exc:
        raise UnsafeUrlError("来源网络地址不可用") from exc
    transport = httpx.HTTPTransport(retries=0, trust_env=False)
    transport._pool._network_backend = _PinnedBackend(parsed.hostname, port, addresses[0][4][0])
    return transport


def _validate_target(url: str) -> None:
    enforce_outbound_host(url)
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise UnsafeUrlError("仅允许 http/https 协议")
    if not parsed.hostname:
        raise UnsafeUrlError("URL 缺少主机名")
    if parsed.username is not None or parsed.password is not None:
        raise UnsafeUrlError("URL 不允许包含凭据")

    # 开发代理 fake-ip 场景的显式豁免（见 config.ssrf_allow_private 注释）
    if get_settings().app_env != "production" and get_settings().ssrf_allow_private:
        return

    try:
        addr_infos = resolve_addresses(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
    except (OSError, ValueError) as exc:
        raise UnsafeUrlError("来源网络地址不可用") from exc

    for info in addr_infos:
        ip = ipaddress.ip_address(info[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            raise UnsafeUrlError("禁止访问内网/保留地址")


def safe_fetch(
    url: str,
    headers: dict[str, str] | None = None,
    method: str = "GET",
    json_body: dict | None = None,
) -> tuple[bytes, str]:
    """返回 (响应体, mime_type)。重定向逐跳重新校验目标，防止跳转到内网。"""

    settings = get_settings()
    limit = min(settings.url_fetch_max_bytes, MAX_OUTBOUND_RESPONSE_BYTES)
    timeout = min(settings.url_fetch_timeout_seconds, MAX_OUTBOUND_TIMEOUT_SECONDS)
    if limit < 1 or timeout <= 0:
        raise UnsafeUrlError("响应读取限制无效")
    request_body = _json_request_body(json_body)
    current_url = url
    redirect_count = 0
    deadline = time.monotonic() + timeout
    request_headers = {key: value for key, value in (headers or {}).items() if key.lower() != "accept-encoding"}
    request_headers["Accept-Encoding"] = "identity"
    while True:
        with outbound_scope(deadline):
            _validate_target(current_url)
            transport = pinned_transport(current_url, allow_http=True,
                                         allow_private=settings.app_env != "production" and settings.ssrf_allow_private)
        with (outbound_scope(deadline),
              httpx.Client(timeout=timeout, follow_redirects=False, trust_env=False, transport=transport) as client):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise UnsafeUrlError("响应超过总读取时限")
            if request_body is not None:
                request_headers["Content-Type"] = "application/json"
            with client.stream(method.upper(), current_url, headers=request_headers, content=request_body, timeout=remaining) as resp:
                if resp.status_code in {301, 302, 303, 307, 308}:
                    redirect_count += 1
                    if redirect_count > MAX_REDIRECTS:
                        raise UnsafeUrlError("重定向次数超限")
                    redirected = httpx.URL(current_url).join(resp.headers["location"])
                    original = httpx.URL(url)
                    current = httpx.URL(current_url)
                    if ((redirected.scheme, redirected.host, redirected.port) != (current.scheme, current.host, current.port)
                            and (headers or json_body is not None or original.query
                                 or current.query or redirected.query
                                 or method.upper() not in {"GET", "HEAD"})):
                        raise UnsafeUrlError("带凭据或正文的请求不允许跨域重定向")
                    current_url = str(redirected)
                    continue
                resp.raise_for_status()
                if resp.headers.get("content-encoding", "identity").strip().lower() != "identity":
                    raise UnsafeUrlError("不允许压缩响应")
                chunks: list[bytes] = []
                total = 0
                for chunk in resp.iter_bytes():
                    if time.monotonic() >= deadline:
                        raise UnsafeUrlError("响应超过总读取时限")
                    total += len(chunk)
                    if total > limit:
                        raise UnsafeUrlError(f"响应超过大小限制 {limit} 字节")
                    chunks.append(chunk)
                if time.monotonic() >= deadline:
                    raise UnsafeUrlError("响应超过总读取时限")
                return b"".join(chunks), resp.headers.get("content-type", "text/html").split(";")[0].strip()


def bounded_safe_fetch(
    url: str,
    headers: dict[str, str] | None = None,
    method: str = "GET",
    json_body: dict | None = None,
    *,
    max_bytes: int = 1_000_000,
) -> tuple[bytes, str]:
    """F7 external capability fetch with an in-flight body limit and per-hop URL validation."""
    settings = get_settings()
    limit = min(max_bytes, settings.url_fetch_max_bytes, 1_000_000)
    if limit < 1:
        raise UnsafeUrlError("响应大小限制无效")
    request_body = _json_request_body(json_body)
    current_url = url
    redirect_count = 0
    timeout = min(settings.url_fetch_timeout_seconds, MAX_OUTBOUND_TIMEOUT_SECONDS)
    deadline = time.monotonic() + timeout
    request_headers = {key: value for key, value in (headers or {}).items() if key.lower() != "accept-encoding"}
    request_headers["Accept-Encoding"] = "identity"
    while True:
        with (outbound_scope(deadline),
              httpx.Client(timeout=timeout, follow_redirects=False, trust_env=False,
                           transport=pinned_transport(current_url)) as client):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise UnsafeUrlError("响应超过总读取时限")
            if request_body is not None:
                request_headers["Content-Type"] = "application/json"
            with client.stream(method.upper(), current_url, headers=request_headers, content=request_body, timeout=remaining) as resp:
                if time.monotonic() >= deadline:
                    raise UnsafeUrlError("响应超过总读取时限")
                if resp.status_code in {301, 302, 303, 307, 308}:
                    redirect_count += 1
                    if redirect_count > MAX_REDIRECTS:
                        raise UnsafeUrlError("重定向次数超限")
                    redirected = httpx.URL(current_url).join(resp.headers["location"])
                    original = httpx.URL(url)
                    if (redirected.scheme, redirected.host, redirected.port) != (original.scheme, original.host, original.port):
                        raise UnsafeUrlError("重定向目标不属于已验证来源")
                    current_url = str(redirected)
                    continue
                resp.raise_for_status()
                if resp.headers.get("content-encoding", "identity").strip().lower() != "identity":
                    raise UnsafeUrlError("不允许压缩响应")
                chunks: list[bytes] = []
                total = 0
                for chunk in resp.iter_bytes():
                    if time.monotonic() >= deadline:
                        raise UnsafeUrlError("响应超过总读取时限")
                    total += len(chunk)
                    if total > limit:
                        raise UnsafeUrlError(f"响应超过大小限制 {limit} 字节")
                    chunks.append(chunk)
                if time.monotonic() >= deadline:
                    raise UnsafeUrlError("响应超过总读取时限")
                return b"".join(chunks), resp.headers.get("content-type", "text/html").split(";")[0].strip()
