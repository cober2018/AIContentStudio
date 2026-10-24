"""Settings view of the platform MCP: what it is, how to connect and what it can do; never the token."""

from __future__ import annotations

import os
import re
import stat
import sys
from pathlib import Path

from sqlalchemy.orm import Session

from ..models import User
from .system_settings import build_settings_view

SERVER_NAME = "aicontentstudio-creative"
ENDPOINT = "/api/v1/creative-mcp"
API_ROOT = Path(__file__).resolve().parents[2]
BRIDGE = API_ROOT / "scripts" / "creative_mcp_stdio.py"
RUNTIME_ENV = API_ROOT / "scripts" / "startup" / "runtime.env"
GROUPS = {
    "stages": ("生产阶段与决定", {"get_stages", "start_run", "preview_stage", "run_stage", "get_stage_result", "get_stage_decision"}),
    "materials": ("找素材", {"start_material_match", "get_material_match", "get_shot_slots"}),
    "executions": ("执行包与回传", {"get_package", "get_execution", "claim_execution", "start_execution", "materialize_inputs",
                                  "report_progress", "report_blocker", "report_checkpoint", "submit_output", "mark_unknown",
                                  "reconcile_unknown", "request_human_review"}),
    "context": ("读取上下文与方法", {"get_context", "find_capabilities", "use_capability"}),
    "video": ("做视频（导演稿 → 小样 → 成片）", {"get_video_brief", "save_director_draft", "get_video_decision", "set_shot_materials",
                                        "accept_material_candidate", "generate_video_image", "generate_video_voiceover", "prepare_video_edit", "file_as_common"}),
}
# Registry descriptions are written for models; these are the same facts for the person maintaining the setup.
SUMMARIES = {
    "get_stages": "看作品的各个生产步骤、状态和当前运行，附平台审阅链接",
    "start_run": "为作品开一次新的运行（比如上一次卡在未知状态）",
    "preview_stage": "检查某一步能不能跑，拿到这一步的精确配置指纹",
    "run_stage": "跑一步，生成候选；候选留在平台等你决定",
    "get_stage_result": "读一步的候选摘要、质量检查和审阅链接",
    "get_stage_decision": "读你在平台上的决定和意见；可等待最多 25 秒",
    "start_material_match": "按文案或分镜找素材（自己的素材库优先，再搜免费图库）",
    "get_material_match": "读找素材的结果，以及你采用或否掉了哪些",
    "get_shot_slots": "读视频每个镜头的素材槽位：旁白、画面、搜索词、首帧生图和图生视频两条提示词、缺/有候选/已选",
    "get_context": "读作品、简报和事实边界的当前信息",
    "find_capabilities": "查可用的已保存方法",
    "use_capability": "加载一个方法，或某个执行包的生产方法",
    "get_package": "读一个冻结的执行包及其授权输入",
    "get_execution": "读执行状态和已暂存的产出",
    "claim_execution": "认领一个已准备好的执行",
    "start_execution": "开始已认领的执行",
    "materialize_inputs": "把授权的输入文件放到本地工作目录",
    "report_progress": "报告进度",
    "report_blocker": "报告卡住的原因",
    "report_checkpoint": "记录一个检查点",
    "submit_output": "回传一个产出文件（只暂存，不采用）",
    "mark_unknown": "标记结果不确定，不重发",
    "reconcile_unknown": "核对不确定的结果",
    "request_human_review": "请你审阅已就绪的结果",
    "get_video_brief": "读做视频要用的一切：简报、事实、原文、配音设置、素材库和当前导演稿",
    "save_director_draft": "存导演稿（含每个镜头的素材需求），然后等你在页面上看",
    "get_video_decision": "读你对导演稿 / 小样 / 成片的决定和修改意见",
    "set_shot_materials": "导演稿采用后，给每个镜头定素材",
    "accept_material_candidate": "把搜到的一条图库素材收进素材库和本项目",
    "file_as_common": "把本项目里通用的素材（特效、转场、常用 BGM / 音效）移到 Mac 本地的通用素材库",
    "generate_video_image": "用平台生图工具生成一张画面，放进项目文件夹",
    "generate_video_voiceover": "按你的 MiniMax 设置生成配音，并按配音对齐镜头时长",
    "prepare_video_edit": "记下哪些镜头用 AE，开剪辑任务：先小样，小样通过后排版出成片",
}
CANNOT = ["接受或带修改接受阶段结果", "拒绝或记录反馈", "采用素材、绑定到镜头", "批准候选、冻结 Master", "发布或交付到渠道"]
LOOP = ["get_stages / preview_stage 查看要做哪一步", "run_stage 生成候选", "把 review_url 发给你，你在平台上看图并决定",
        "get_stage_decision 读你的决定（每次最多等 25 秒）", "通过就继续下一步；不通过按你的意见重做"]


def _configured() -> tuple[bool, bool, int | None]:
    token = os.environ.get("AICS_CREATIVE_MCP_TOKEN", "")
    owner = os.environ.get("AICS_CREATIVE_MCP_OWNER_USER_ID", "")
    owner_id = int(owner) if re.fullmatch(r"[1-9][0-9]{0,15}", owner) else None
    return bool(re.fullmatch(r"[A-Za-z0-9._~+/-]{32,512}", token)), owner_id is not None, owner_id


def _tools() -> list[dict]:
    from .creative_mcp import TOOLS

    items = []
    for name, (_, description, readonly) in TOOLS.items():
        group = next((key for key, (_, names) in GROUPS.items() if name in names), "other")
        items.append({"name": name, "description": description, "summary": SUMMARIES.get(name), "read_only": readonly, "group": group})
    return items


def view(db: Session) -> dict:
    token_ok, owner_ok, owner_id = _configured()
    owner = db.get(User, owner_id) if owner_id else None
    python = API_ROOT / ".venv" / "bin" / "python"
    python = str(python if python.exists() else Path(sys.executable))
    args = [str(BRIDGE), "--runtime-env", str(RUNTIME_ENV)]
    # The plugins PUT replaces skills and MCP together, so the page needs the current values to save MCP alone.
    plugins = build_settings_view()["plugins"]
    return {
        "server_name": SERVER_NAME, "enabled": token_ok and owner_ok, "token_configured": token_ok,
        "owner": {"id": owner.id, "email": owner.email, "role": owner.role, "active": owner.is_active} if owner else None,
        "endpoint": ENDPOINT, "loopback_only": True, "bridge": str(BRIDGE), "runtime_env": str(RUNTIME_ENV),
        "config_keys": ["AICS_CREATIVE_MCP_TOKEN", "AICS_CREATIVE_MCP_OWNER_USER_ID"],
        "clients": {
            "codex": "\n".join([f"[mcp_servers.{SERVER_NAME}]", "startup_timeout_sec = 15", "tool_timeout_sec = 360",
                                f'command = "{python}"', "args = [" + ", ".join(f'"{item}"' for item in args) + "]"]),
            "claude_code": f"claude mcp add {SERVER_NAME} -s local -- {python} " + " ".join(args),
        },
        "groups": [{"key": key, "label": label} for key, (label, _) in GROUPS.items()] + [{"key": "other", "label": "其他"}],
        "tools": _tools(), "cannot": CANNOT, "loop": LOOP,
        "external": {key: plugins[key] for key in ("mcp", "skill_dirs", "skills_enabled")},
    }


def check(db: Session) -> dict:
    token_ok, owner_ok, owner_id = _configured()
    owner = db.get(User, owner_id) if owner_id else None
    owner_reason = ("creative_mcp_owner_unavailable" if owner is None or not owner.is_active
                    else "creative_mcp_owner_role" if owner.role not in {"editor", "admin"} else None)
    try:
        mode = stat.S_IMODE(RUNTIME_ENV.stat().st_mode)
        private = not mode & 0o077
    except OSError:
        private = None
    try:
        count = len(_tools())
    except Exception:  # noqa: BLE001 A broken registry is a failed check, not a page error.
        count = 0
    checks = [
        {"key": "token", "label": "访问令牌已配置", "ok": token_ok, "reason": None if token_ok else "creative_mcp_token_unavailable"},
        {"key": "owner", "label": "代理账号可用（启用的编辑或管理员）", "ok": owner_reason is None, "reason": owner_reason},
        {"key": "runtime_env", "label": "运行配置文件只有本人可读", "ok": private is True,
         "reason": None if private else "runtime_env_missing" if private is None else "runtime_env_not_private"},
        {"key": "bridge", "label": "本地连接脚本存在", "ok": BRIDGE.is_file(), "reason": None if BRIDGE.is_file() else "bridge_missing"},
        {"key": "tools", "label": "工具清单可加载", "ok": count > 0, "reason": None if count else "tool_registry_unavailable", "count": count},
    ]
    return {"ok": all(item["ok"] for item in checks), "checks": checks}
