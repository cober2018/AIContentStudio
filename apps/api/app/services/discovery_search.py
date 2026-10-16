"""Background search using the same provider endpoints as the configured MCPs."""

from __future__ import annotations

import json
import os
import pwd
import re
import selectors
import shutil
import subprocess
import time
import tomllib
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from ..config import get_settings
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


def credentials(provider: str, source: str = "environment") -> tuple[str, str]:
    if provider not in {"minimax", "tavily"}:
        raise SearchUnavailable("search_provider_unavailable")
    name = "MINIMAX_API_KEY" if provider == "minimax" else "TAVILY_API_KEY"
    key = os.getenv(name, "")
    host = os.getenv("MINIMAX_API_HOST", "https://api.minimaxi.com") if provider == "minimax" else "https://api.tavily.com"
    if source == "codex_mcp":
        if get_settings().app_env == "production":
            raise SearchUnavailable("local_mcp_credentials_not_allowed_in_production")
        path = Path(pwd.getpwuid(os.getuid()).pw_dir) / ".codex" / "config.toml"
        try:
            if path.stat().st_size > 1024 * 1024:
                raise ValueError("config_size")
            servers = tomllib.loads(path.read_text()).get("mcp_servers", {})
            server = servers.get("MiniMax" if provider == "minimax" else "tavily", {})
            if not server.get("enabled", True):
                raise ValueError("disabled")
            env = server.get("env", {})
            key = env.get(name) or key
            if provider == "minimax":
                host = env.get("MINIMAX_API_HOST") or host
        except (OSError, ValueError, TypeError):
            raise SearchUnavailable("search_credentials_unavailable") from None
    elif source != "environment":
        raise SearchUnavailable("search_credentials_unavailable")
    allowed = {"https://api.minimax.io", "https://api.minimaxi.com"} if provider == "minimax" else {"https://api.tavily.com"}
    if host.rstrip("/") not in allowed or not isinstance(key, str) or not key:
        raise SearchUnavailable("search_unavailable")
    return host.rstrip("/"), key


def available(provider: str, source: str) -> bool:
    try:
        credentials(provider, source)
        return not (provider == "minimax" and source == "codex_mcp" and not shutil.which("uvx"))
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


def search(query: str, *, provider: str, credential_source: str, limit: int = 5) -> list[dict]:
    if not isinstance(query, str) or not 2 <= len(query.strip()) <= 500:
        raise ValueError("search_query_invalid")
    host, key = credentials(provider, credential_source)
    if provider == "minimax":
        path, payload = "/v1/coding_plan/search", {"q": query}
        headers = {"Authorization": f"Bearer {key}", "MM-API-Source": "Minimax-MCP"}
    else:
        path, payload = "/search", {"query": query, "max_results": min(10, max(1, limit)), "search_depth": "basic"}
        headers = {"Authorization": f"Bearer {key}"}
    try:
        if provider == "minimax" and credential_source == "codex_mcp":
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
