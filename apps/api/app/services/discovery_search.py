"""Background search; the vendor is the 选题搜索 use in 设置 → AI 与模型."""

from __future__ import annotations

import json
import os
import re
import selectors
import shutil
import subprocess
import time
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .url_fetch import safe_fetch


class SearchUnavailable(RuntimeError):
    def __init__(self, code, *, dispatched=False):
        self.dispatched = dispatched
        super().__init__(code)


def canonical_url(value: str) -> str:
    if not isinstance(value, str) or len(value) > 1000:
        raise ValueError("invalid_source_url")
    parsed = urlsplit(value)
    if (parsed.scheme not in {"https", "http"} or not parsed.hostname or parsed.username
            or parsed.password or parsed.port not in {None, 80, 443}):
        raise ValueError("invalid_source_url")
    query = [(k, v) for k, v in parse_qsl(parsed.query) if not k.lower().startswith("utm_")
             and k.lower() not in {"fbclid", "gclid"}]
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path or "/",
                       urlencode(sorted(query)), ""))


def credentials(provider: str) -> tuple[str, str]:
    """Search keys come only from 设置 → AI 与模型: MiniMax from its card, Tavily from its registered vendor."""
    from .. import runtime_config
    from . import minimax_cli_provider as minimax

    if provider == "minimax":
        host = "https://api.minimax.io" if minimax.chat_base_url().startswith("https://api.minimax.io") else "https://api.minimaxi.com"
        key = minimax.shared_key()
    elif provider == "tavily":
        vendor = ((runtime_config.get_runtime(runtime_config.KEY_MODELS) or {}).get("providers") or {}).get("tavily") or {}
        host, key = "https://api.tavily.com", vendor.get("api_key") if vendor.get("enabled", True) else ""
    else:
        raise SearchUnavailable("search_provider_unavailable")
    if not isinstance(key, str) or not key:
        raise SearchUnavailable("search_unavailable")
    return host, key


def available(provider: str) -> bool:
    try:
        credentials(provider)
        return True
    except SearchUnavailable:
        return False


def _minimax_mcp(query: str, host: str, key: str) -> dict:
    executable = shutil.which("uvx")
    if not executable:
        raise SearchUnavailable("search_mcp_runtime_unavailable")
    env = {name: os.environ[name] for name in ("PATH", "HOME", "USER", "TMPDIR", "SSL_CERT_FILE") if name in os.environ}
    env.update(MINIMAX_API_KEY=key, MINIMAX_API_HOST=host)
    try:
        process = subprocess.Popen([executable, "--offline", "minimax-coding-plan-mcp", "-y"],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.DEVNULL, env=env)
    except OSError:
        raise SearchUnavailable("search_mcp_runtime_unavailable") from None
    dispatched = False
    deadline = time.monotonic() + 45
    pending = bytearray()
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)

    def send(message):
        process.stdin.write(json.dumps(message).encode() + b"\n")
        process.stdin.flush()

    def receive(request_id):
        total = 0
        while time.monotonic() < deadline:
            while b"\n" in pending:
                line, _, rest = pending.partition(b"\n")
                pending[:] = rest
                try:
                    message = json.loads(line)
                except (ValueError, UnicodeError):
                    continue
                if isinstance(message, dict) and message.get("id") == request_id:
                    if message.get("error"):
                        raise SearchUnavailable("search_mcp_rejected", dispatched=dispatched)
                    return message.get("result", {})
            for event, _ in selector.select(min(.2, max(0, deadline - time.monotonic()))):
                data = os.read(event.fileobj.fileno(), 65536)
                if not data:
                    raise SearchUnavailable("search_mcp_closed", dispatched=dispatched)
                pending.extend(data)
                total += len(data)
                if total > 1_000_000:
                    raise SearchUnavailable("search_response_too_large", dispatched=dispatched)
        raise SearchUnavailable("search_mcp_timeout", dispatched=dispatched)

    try:
        send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2024-11-05", "capabilities": {},
            "clientInfo": {"name": "AIContentStudio-discovery", "version": "1"}}})
        receive(1)
        send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        send({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
              "params": {"name": "web_search", "arguments": {"query": query}}})
        dispatched = True
        result = receive(2)
        if result.get("isError"):
            raise SearchUnavailable("search_mcp_rejected", dispatched=dispatched)
        for block in result.get("content", []):
            if block.get("type") == "text":
                try:
                    data = json.loads(block["text"])
                except (ValueError, TypeError):
                    continue
                if isinstance(data, dict) and "organic" in data:
                    return data
        raise SearchUnavailable("search_response_invalid", dispatched=dispatched)
    except (OSError, BrokenPipeError):
        raise SearchUnavailable("search_mcp_runtime_unavailable", dispatched=dispatched) from None
    finally:
        selector.close()
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        for stream in (process.stdin, process.stdout):
            stream.close()


def search(query: str, *, provider: str, limit: int = 5) -> list[dict]:
    if not isinstance(query, str) or not 2 <= len(query.strip()) <= 500:
        raise ValueError("search_query_invalid")
    host, key = credentials(provider)
    if provider == "minimax":
        path, payload = "/v1/coding_plan/search", {"q": query}
        headers = {"Authorization": f"Bearer {key}", "MM-API-Source": "Minimax-MCP"}
    else:
        path, payload = "/search", {"query": query, "max_results": min(10, max(1, limit)), "search_depth": "basic"}
        headers = {"Authorization": f"Bearer {key}"}
    try:
        if provider == "minimax" and shutil.which("uvx"):
            # The local MiniMax MCP reaches the endpoint where pinned fetch rejects proxy-resolved addresses.
            data = _minimax_mcp(query, host, key)
        else:
            body, _ = safe_fetch(host + path, headers=headers, method="POST", json_body=payload)
            data = json.loads(body)
    except SearchUnavailable:
        raise
    except Exception:  # noqa: BLE001 Do not propagate request metadata or credentials.
        # Provider exceptions can include credential-bearing request metadata.
        raise SearchUnavailable("search_request_failed", dispatched=True) from None
    if not isinstance(data, dict):
        raise SearchUnavailable("search_response_invalid")
    if provider == "minimax" and data.get("base_resp", {}).get("status_code") != 0:
        raise SearchUnavailable("search_provider_rejected")
    rows = data.get("organic" if provider == "minimax" else "results")
    if not isinstance(rows, list):
        raise SearchUnavailable("search_response_invalid")
    result = []
    for row in rows[:min(10, max(1, limit))]:
        if not isinstance(row, dict):
            continue
        try:
            url = canonical_url(row.get("link") or row.get("url"))
        except (ValueError, TypeError):
            continue
        title = re.sub(r"\s+", " ", str(row.get("title") or "")).strip()[:300]
        if title:
            result.append({"url": url, "title": title,
                           "snippet": str(row.get("snippet") or row.get("content") or "")[:2500],
                           "date": str(row.get("date") or row.get("published_date") or "")[:100],
                           "provider": provider})
    return result
