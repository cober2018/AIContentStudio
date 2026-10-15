"""Connect stdio MCP clients to the existing loopback creative MCP."""

from __future__ import annotations

import argparse
import http.client
import json
import os
import re
import shlex
import stat
import sys
from pathlib import Path

MAX_BYTES = 2 * 1024 * 1024


def load_token(path: Path) -> str:
    info = path.stat()
    if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
        raise ValueError("private_runtime_required")
    for line in path.read_text().splitlines():
        fields = shlex.split(line, comments=True)
        if fields and fields[0] == "export":
            fields = fields[1:]
        if len(fields) == 1 and fields[0].startswith("AICS_CREATIVE_MCP_TOKEN="):
            token = fields[0].split("=", 1)[1]
            if re.fullmatch(r"[A-Za-z0-9._~+/-]{32,512}", token):
                return token
    raise ValueError("creative_mcp_token_unavailable")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-env", required=True, type=Path)
    args = parser.parse_args()
    try:
        token = load_token(args.runtime_env)
    except (OSError, ValueError):
        print("Creative MCP requires the existing private runtime configuration.", file=sys.stderr)
        raise SystemExit(1) from None
    while raw := sys.stdin.buffer.readline(MAX_BYTES + 1):
        message = None
        connection = None
        try:
            if len(raw) > MAX_BYTES:
                raise ValueError("request_too_large")
            message = json.loads(raw)
            if not isinstance(message, dict):
                raise TypeError("request_invalid")
            # A fixed destination keeps the credential confined to its existing service.
            connection = http.client.HTTPConnection("127.0.0.1", 8000, timeout=330)
            connection.request("POST", "/api/v1/creative-mcp", body=raw, headers={
                "Authorization": f"Bearer {token}", "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream", "MCP-Protocol-Version": "2025-11-25",
            })
            response = connection.getresponse()
            body = response.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                raise ValueError("response_too_large")
            if body:
                result = json.loads(body)
                if not isinstance(result, dict):
                    raise ValueError("response_invalid")
                print(json.dumps(result, ensure_ascii=False), flush=True)
        except (OSError, TypeError, ValueError, http.client.HTTPException):
            if not isinstance(message, dict) or "id" in message:
                print(json.dumps({"jsonrpc": "2.0", "id": message.get("id") if isinstance(message, dict) else None,
                    "error": {"code": -32000, "message": "creative_mcp_transport_unavailable",
                              "data": {"read_execution_before_retry": True}}}), flush=True)
        finally:
            if connection is not None:
                connection.close()
        if len(raw) > MAX_BYTES:
            break


if __name__ == "__main__":
    main()
