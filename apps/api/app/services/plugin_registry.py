"""技能与插件登记（设置页「技能与插件」数据源）。

V1 范围：
- 自动发现本机 Agent skills（~/.agents/skills、~/.zcode/skills、~/.codex/skills 下带 SKILL.md 的目录），
  读 frontmatter 的 name/description，以及 V1 PRD 2.0（D16）扩展元数据
  version/license/kind/capabilities（缺省 unversioned/unknown/skill/[]）；
- MCP server 手工登记（name + url + enabled），连通性检测留 V2；
- dsh（DeepSeek Harness，:3080）状态探测（未带 token ping，401 = 存活且要求鉴权）。

登记用途：工作流节点 / 场景路由引用技能时的可见清单；启用集存 system_settings.plugins。
不读取 Skill body 当系统指令（D16：只消费 frontmatter 元数据）。
"""

import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import httpx

from .url_fetch import OUTBOUND_HTTP_POLICIES, outbound_scope, pinned_transport

# Preserve older agent-directory precedence while including the catalog used by
# the current local Codex runtime.
SKILL_DIRS = (
    Path.home() / ".agents" / "skills",
    Path.home() / ".zcode" / "skills",
    Path.home() / ".codex" / "skills",
)
_FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---", re.DOTALL)
# D16：frontmatter 元数据键；capabilities 为逗号分隔列表
_FIELD = re.compile(r"^(name|description|version|license|kind|capabilities):\s*(.+)$", re.MULTILINE)
_DEFAULTS = {"version": "unversioned", "license": "unknown", "kind": "skill"}


def scan_skills(dirs: list[Path] | tuple[Path, ...] = SKILL_DIRS) -> list[dict[str, Any]]:
    """扫描 skill 目录：每个含 SKILL.md 的子目录记为一条（元数据来自 frontmatter，缺省见 _DEFAULTS）。"""
    found: dict[str, dict[str, Any]] = {}
    for raw in dirs:
        base = Path(str(raw)).expanduser()
        if not base.is_dir():
            continue
        for skill_md in sorted(base.glob("*/SKILL.md")):
            try:
                text = skill_md.read_text(encoding="utf-8", errors="replace")[:4000]
            except OSError:
                continue
            meta: dict[str, Any] = {}
            match = _FRONTMATTER.search(text)
            if match:
                for key, value in _FIELD.findall(match.group(1)):
                    value = value.strip().strip('"').strip("'")
                    if key == "capabilities":
                        meta[key] = [c.strip() for c in value.split(",") if c.strip()]
                    else:
                        meta[key] = value
            name = meta.get("name") or skill_md.parent.name
            entry = {
                "name": name,
                "description": (meta.get("description") or "")[:200],
                # D16 扩展：version/license/kind/capabilities（缺省值保证旧 skill 可登记）
                "version": meta.get("version") or _DEFAULTS["version"],
                "license": meta.get("license") or _DEFAULTS["license"],
                "kind": meta.get("kind") or _DEFAULTS["kind"],
                "capabilities": meta.get("capabilities") or [],
                "path": str(skill_md.parent),
                "source": "local",
            }
            # 同名 skill 以先扫描到的为准（.agents 优先）
            found.setdefault(name, entry)
    return sorted(found.values(), key=lambda x: x["name"])


def skill_descriptor(name: str, dirs: list[Path] | tuple[Path, ...] = SKILL_DIRS) -> dict[str, Any] | None:
    """按 name 取单个 skill 描述符（未安装返回 None）。"""
    return next((s for s in scan_skills(dirs) if s["name"] == name), None)


def dsh_status(base_url: str = "http://localhost:3080") -> dict[str, Any]:
    """dsh 存活探测：401 = 在线且要求鉴权（正常）；连接失败 = 未启动。"""
    try:
        parsed = urlsplit(base_url)
        port = parsed.port
    except (TypeError, ValueError):
        return {"url": "http://localhost:3080", "reachable": False, "status_code": None}
    if (parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
            or port != 3080 or parsed.username is not None or parsed.password is not None
            or parsed.query or parsed.fragment):
        return {"url": "http://localhost:3080", "reachable": False, "status_code": None}
    try:
        deadline = time.monotonic() + OUTBOUND_HTTP_POLICIES["dsh"].timeout_seconds
        with (outbound_scope(deadline),
              httpx.Client(timeout=OUTBOUND_HTTP_POLICIES["dsh"].timeout_seconds,
                           transport=pinned_transport(base_url, allow_http=True, allow_private=True),
                           follow_redirects=False, trust_env=False) as client,
              client.stream("GET", base_url) as resp):
            return {"url": base_url, "reachable": True, "status_code": resp.status_code}
    except (httpx.HTTPError, ValueError):
        return {"url": base_url, "reachable": False, "status_code": None}
