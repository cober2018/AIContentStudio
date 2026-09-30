"""URL Import 安全抓取：防 SSRF（执行计划 STU-024 / STU-161）。"""

import ipaddress
import socket
from urllib.parse import urlparse

import httpx

from ..config import get_settings

MAX_REDIRECTS = 3


class UnsafeUrlError(ValueError):
    pass


def _validate_target(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise UnsafeUrlError("仅允许 http/https 协议")
    if not parsed.hostname:
        raise UnsafeUrlError("URL 缺少主机名")

    # 开发代理 fake-ip 场景的显式豁免（见 config.ssrf_allow_private 注释）
    if get_settings().ssrf_allow_private:
        return

    try:
        addr_infos = socket.getaddrinfo(parsed.hostname, None)
    except socket.gaierror as exc:
        raise UnsafeUrlError(f"域名解析失败: {parsed.hostname}") from exc

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
    current_url = url
    redirect_count = 0

    with httpx.Client(timeout=settings.url_fetch_timeout_seconds, follow_redirects=False) as client:
        while True:
            _validate_target(current_url)
            resp = client.request(method.upper(), current_url, headers=headers, json=json_body)
            if resp.status_code in {301, 302, 303, 307, 308}:
                redirect_count += 1
                if redirect_count > MAX_REDIRECTS:
                    raise UnsafeUrlError("重定向次数超限")
                current_url = str(httpx.URL(current_url).join(resp.headers["location"]))
                continue
            resp.raise_for_status()
            if len(resp.content) > settings.url_fetch_max_bytes:
                raise UnsafeUrlError(f"响应超过大小限制 {settings.url_fetch_max_bytes} 字节")
            return resp.content, resp.headers.get("content-type", "text/html").split(";")[0].strip()


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
    current_url = url
    redirect_count = 0
    with httpx.Client(timeout=min(settings.url_fetch_timeout_seconds, 10), follow_redirects=False) as client:
        while True:
            _validate_target(current_url)
            with client.stream(method.upper(), current_url, headers=headers, json=json_body) as resp:
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
                chunks: list[bytes] = []
                total = 0
                for chunk in resp.iter_bytes():
                    total += len(chunk)
                    if total > limit:
                        raise UnsafeUrlError(f"响应超过大小限制 {limit} 字节")
                    chunks.append(chunk)
                return b"".join(chunks), resp.headers.get("content-type", "text/html").split(";")[0].strip()
