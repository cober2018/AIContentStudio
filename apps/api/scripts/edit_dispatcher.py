"""Start one queued rough-cut edit with a local assistant (run by launchd every minute).

launchd never overlaps runs of the same job, so at most one edit session runs at a time.
The session claims, edits and submits through the platform MCP; this script only starts it and
reports how the start ended. A task is never started twice by itself.
"""
from __future__ import annotations

import http.client
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API = Path(__file__).resolve().parents[1]
RUNTIME_ENV = API / "scripts" / "startup" / "runtime.env"
LOGS = Path.home() / "AIContentStudio" / "edit-logs"
TIMEOUT = 90 * 60

sys.path.insert(0, str(API / "scripts"))
from creative_mcp_stdio import load_token  # noqa: E402

PROMPT = """你是这台 Mac 上的剪辑助手，现在没有人在旁边，按下面做完就结束。

任务：剪辑任务 execution={execution_id}（project={project_id}，unit={unit_id}，package_hash={package_hash}）。

1. 先读 .codex/skills/video-production-handoff/SKILL.md、.codex/skills/craft-resolve/SKILL.md、.codex/skills/craft-ae/SKILL.md，按它们的流程做。
2. 用平台 MCP（aics）领取并开始这个任务，读取导演包。导演包是唯一依据，不要自己改文案或换素材。
3. 达芬奇（resolve MCP）负责全部镜头的剪辑、调色和声音；导演包里标了 AE 的镜头，按 craft-ae 用 AE（aerender）制作后放进达芬奇时间线。
4. 渲染粗剪，按任务的输出合同把成片和工程文件通过 MCP 回传。不要接受自己的结果，等用户审片。
5. 达芬奇或 AE 打不开、素材读不到、或任何做不下去的情况：用 MCP 报告阻塞原因（一句中文大白话），然后结束。可能已经发出去的操作不要重试。
"""


def _call(method: str, path: str, token: str, body: dict | None = None) -> dict:
    connection = http.client.HTTPConnection("127.0.0.1", 8000, timeout=60)
    try:
        connection.request(method, path, body=json.dumps(body) if body is not None else None,
                           headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
        response = connection.getresponse()
        data = json.loads(response.read() or b"{}")
        if response.status >= 400:
            raise RuntimeError(f"{path} → {response.status} {data}")
        return data
    finally:
        connection.close()


def _mcp_config(path: Path) -> None:
    servers = {
        "aics": {"type": "stdio", "command": str(API / ".venv" / "bin" / "python"),
                 "args": [str(API / "scripts" / "creative_mcp_stdio.py"), "--runtime-env", str(RUNTIME_ENV)]},
        "resolve": {"type": "stdio", "command": "/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Applications/ResolveMCP", "args": []},
    }
    path.write_text(json.dumps({"mcpServers": servers}, ensure_ascii=False))
    path.chmod(0o600)


def _command(assistant: str, prompt: str, config: Path) -> list[str]:
    if assistant == "codex":
        return [shutil.which("codex") or "codex", "exec", "--full-auto", prompt]
    return [shutil.which("claude") or str(Path.home() / ".local/bin/claude"), "-p", prompt,
            "--mcp-config", str(config), "--strict-mcp-config", "--permission-mode", "acceptEdits",
            "--allowedTools", "mcp__aics,mcp__resolve,Bash,Read,Write,Edit,Glob,Grep"]


def main() -> int:
    token = load_token(RUNTIME_ENV)
    task = _call("GET", "/api/v1/edit-agent/next", token).get("task")
    if not task:
        return 0
    execution_id = task["execution_id"]
    LOGS.mkdir(parents=True, exist_ok=True)
    log = LOGS / f"execution-{execution_id}.log"
    config = LOGS / ".mcp-config.json"
    _mcp_config(config)
    _call("POST", f"/api/v1/edit-agent/tasks/{execution_id}/report", token, {"state": "launched", "log": str(log)})
    prompt = PROMPT.format(**{key: task.get(key) for key in ("execution_id", "project_id", "unit_id", "package_hash")})
    try:
        with log.open("ab") as output:
            done = subprocess.run(_command(task["assistant"], prompt, config), cwd=ROOT, stdout=output, stderr=subprocess.STDOUT,
                                  stdin=subprocess.DEVNULL, timeout=TIMEOUT, env={**os.environ})
        state, reason = ("finished", "") if done.returncode == 0 else ("failed", f"助手异常退出（{done.returncode}），详见日志")
    except subprocess.TimeoutExpired:
        state, reason = "failed", "剪辑超过 90 分钟没结束，已停止，详见日志"
    except OSError as exc:
        state, reason = "failed", f"助手没能启动：{exc}"
    _call("POST", f"/api/v1/edit-agent/tasks/{execution_id}/report", token, {"state": state, "reason": reason, "log": str(log)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
