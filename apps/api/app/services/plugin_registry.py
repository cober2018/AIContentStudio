"""技能与插件登记（设置页「技能与插件」数据源）。

V1 范围：
- 自动发现本机 Agent skills（~/.agents/skills、~/.zcode/skills 下带 SKILL.md 的目录），
  读 frontmatter 的 name/description；
- MCP server 手工登记（name + url + enabled），连通性检测留 V2；
- dsh（DeepSeek Harness，:3080）状态探测（未带 token ping，401 = 存活且要求鉴权）。

登记用途：工作流节点 / 场景路由引用技能时的可见清单；启用集存 system_settings.plugins。
"""

import re
from pathlib import Path
from typing import Any

import httpx

SKILL_DIRS = (Path.home() / ".agents" / "skills", Path.home() / ".zcode" / "skills")
_FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---", re.DOTALL)
_FIELD = re.compile(r"^(name|description):\s*(.+)$", re.MULTILINE)


def scan_skills(dirs: list[Path] | tuple[Path, ...] = SKILL_DIRS) -> list[dict[str, Any]]:
    """扫描 skill 目录：每个含 SKILL.md 的子目录记为一条（name/description 来自 frontmatter）。"""
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
            meta = {}
            match = _FRONTMATTER.search(text)
            if match:
                for key, value in _FIELD.findall(match.group(1)):
                    meta[key] = value.strip().strip('"').strip("'")
            name = meta.get("name") or skill_md.parent.name
            entry = {
                "name": name,
                "description": (meta.get("description") or "")[:200],
                "path": str(skill_md.parent),
                "source": "local",
            }
            # 同名 skill 以先扫描到的为准（.agents 优先）
            found.setdefault(name, entry)
    return sorted(found.values(), key=lambda x: x["name"])


def dsh_status(base_url: str = "http://localhost:3080") -> dict[str, Any]:
    """dsh 存活探测：401 = 在线且要求鉴权（正常）；连接失败 = 未启动。"""
    try:
        resp = httpx.get(base_url, timeout=2.5)
        return {"url": base_url, "reachable": True, "status_code": resp.status_code}
    except httpx.HTTPError:
        return {"url": base_url, "reachable": False, "status_code": None}
