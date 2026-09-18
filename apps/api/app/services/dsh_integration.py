"""dsh（DeepSeek Harness）执行层集成：设置快照 + Studio 侧稳定性配置。

- snapshot：只读解析 ~/.dsh/settings.yaml（providers / 默认模型路由）与 env.local 密钥
  配置状态（只报「是否已配置」，绝不回显密钥值）；
- studio 侧配置存 system_settings.dsh：调用 dsh 时的稳定性约定（默认模型、备选、超时、
  重试、产出目录），供后续内容工作流消费；
- apply_default_model：把 Studio 侧选定的默认模型一键写回 dsh 用户设置（自动备份原文件；
  结构不符合预期时拒绝，让用户手动改）。
"""

import os
import re
import time
from pathlib import Path
from typing import Any

import yaml

DSH_HOME = Path.home() / ".dsh"
SETTINGS_PATH = DSH_HOME / "settings.yaml"
ENV_LOCAL_PATH = DSH_HOME / "env.local"
DEFAULT_STUDIO_CONFIG = {
    "default_provider": "minimax",
    "default_model": "MiniMax-M3",
    "fallback_provider": "deepseek",
    "fallback_model": "deepseek-chat",
    "timeout_sec": 300,
    "max_retries": 1,
    "output_dir": ".wewrite-scratch",
}


def _env_key_status() -> dict[str, bool]:
    """env.local 中各 API key 是否非空（只回布尔，不回值；同时看进程环境）。"""
    status: dict[str, bool] = {}
    text = ""
    try:
        text = ENV_LOCAL_PATH.read_text(encoding="utf-8")
    except OSError:
        pass
    for match in re.finditer(r"^export\s+([A-Z_]+)=(.*)$", text, re.MULTILINE):
        name, raw = match.group(1), match.group(2).strip().strip('"').strip("'")
        if "KEY" in name or "TOKEN" in name:
            status[name] = bool(raw)
    for name, value in status.items():
        status[name] = value or bool(os.environ.get(name))
    return status


def snapshot() -> dict[str, Any]:
    """dsh 用户设置只读快照。文件缺失/损坏时返回 configured=False 的兜底结构。"""
    data: dict = {}
    parsed = False
    try:
        data = yaml.safe_load(SETTINGS_PATH.read_text(encoding="utf-8")) or {}
        parsed = True
    except (OSError, yaml.YAMLError):
        pass
    providers = {}
    for name, p in (data.get("llm-pi-ai", {}).get("providers") or {}).items():
        if isinstance(p, dict):
            providers[name] = {
                "api": p.get("api"),
                "base_url": p.get("baseURL"),
                "api_key_env": p.get("apiKeyEnv"),
                "models": [m.get("id") for m in (p.get("models") or []) if isinstance(m, dict)],
            }
    default = data.get("agent-default-model") or {}
    return {
        "configured": parsed,
        "settings_path": str(SETTINGS_PATH),
        "providers": providers,
        "default_model": {"provider": default.get("provider"), "model": default.get("model")},
        "env_keys": _env_key_status(),
    }


def apply_default_model(provider: str, model: str, *, dsh_home: Path = DSH_HOME) -> dict[str, Any]:
    """把默认模型路由写回 settings.yaml（先备份）。注释用文本级替换保留；结构不符时拒绝。"""
    settings_path = dsh_home / "settings.yaml"
    try:
        text = settings_path.read_text(encoding="utf-8")
    except OSError as exc:
        return {"ok": False, "error": f"读取 {settings_path} 失败: {exc}"}
    block = re.search(r"^agent-default-model:\s*$", text, re.MULTILINE)
    if not block or "provider:" not in text[block.end():block.end() + 200]:
        return {"ok": False, "error": "settings.yaml 中未找到 agent-default-model 块，请手动修改"}
    backup = settings_path.with_name(f"settings.yaml.bak-{time.strftime('%Y%m%d-%H%M%S')}")
    backup.write_text(text, encoding="utf-8")
    updated = text
    updated = re.sub(
        r"(agent-default-model:\s*\n\s+provider: )[^\s#]+", rf"\g<1>{provider}", updated, count=1
    )
    updated = re.sub(
        r"(agent-default-model:\s*\n\s+provider: [^\s#]+\s*\n\s+model: )[^\s#]+",
        rf"\g<1>{model}",
        updated,
        count=1,
    )
    settings_path.write_text(updated, encoding="utf-8")
    return {"ok": True, "backup": str(backup), "default_model": {"provider": provider, "model": model}}


def studio_view(stored: dict | None = None) -> dict[str, Any]:
    config = {**DEFAULT_STUDIO_CONFIG, **(stored or {})}
    return {"config": config, "snapshot": snapshot()}
