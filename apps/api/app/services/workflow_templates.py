"""内置工作流模板：数据源一条线，生成后按渠道分叉（抖音口播 / 小红书 / 公众号各自独立）。"""

from typing import Any

CHANNEL_META = {
    "douyin": {"label": "抖音口播", "formats": ["txt", "srt"]},
    "xiaohongshu": {"label": "小红书图文", "formats": ["md", "txt"]},
    "wechat": {"label": "公众号文章", "formats": ["md", "html"]},
}


def _node(node_id: str, node_type: str, label: str, params: dict | None = None, x: float = 0, y: float = 0) -> dict:
    return {"id": node_id, "type": node_type, "label": label, "params": params or {}, "layout": {"x": x, "y": y}}


def build_daily_suggest(params: dict | None = None) -> dict:
    """每日舆情 → 荐题：拉取 → 抽取 → 打包冻结 → AI 荐题 →【人工采纳】。"""
    p = params or {}
    return {
        "nodes": [
            _node("pull", "connector_pull", "拉取监测数据", {"endpoint_id": p.get("endpoint_id")}, 0, 0),
            _node("extract", "extract_facts", "抽取候选事实", {"auto_confirm": False}, 260, 0),
            _node("confirm", "confirm_facts", "人工确认事实", {}, 520, 0),
            _node("freeze", "factpack_freeze", "打包并冻结 FactPack", {}, 780, 0),
            _node("suggest", "suggest_topics", "AI 荐题", {"count": p.get("count", 3)}, 1040, 0),
            _node("adopt", "adopt_topic", "人工采纳选题", {}, 1300, 0),
        ],
        "edges": [
            {"from": "pull", "to": "extract"},
            {"from": "extract", "to": "confirm"},
            {"from": "confirm", "to": "freeze"},
            {"from": "freeze", "to": "suggest"},
            {"from": "suggest", "to": "adopt"},
        ],
    }


def build_gen_export(params: dict | None = None) -> dict:
    """生成 → 出库：共享一个 Topic，按渠道分叉（生成 → 校验 →【人工批准】→ 导出），公众号线接草稿箱。"""
    p = params or {}
    channels = p.get("channels") or ["douyin", "xiaohongshu", "wechat"]
    nodes: list[dict] = []
    edges: list[dict] = []
    for i, ch in enumerate(channels):
        meta = CHANNEL_META.get(ch, {"label": ch, "formats": ["md"]})
        y = i * 170
        nodes.append(_node(f"gen_{ch}", "generate", f"生成 · {meta['label']}", {"channel": ch}, 0, y))
        nodes.append(_node(f"humanize_{ch}", "humanize_polish", f"去AI味 · {meta['label']}", {"channel": ch}, 230, y))
        nodes.append(_node(f"censor_{ch}", "content_censor", f"合规审查 · {meta['label']}", {"channel": ch}, 460, y))
        nodes.append(_node(f"check_{ch}", "fact_check", f"事实校验 · {meta['label']}", {"channel": ch}, 690, y))
        nodes.append(_node(f"approve_{ch}", "approve", f"人工批准 · {meta['label']}", {"channel": ch}, 920, y))
        nodes.append(
            _node(f"export_{ch}", "export", f"导出 · {meta['label']}", {"channel": ch, "formats": meta["formats"]}, 1150, y)
        )
        edges += [
            {"from": f"gen_{ch}", "to": f"humanize_{ch}"},
            {"from": f"humanize_{ch}", "to": f"censor_{ch}"},
            {"from": f"censor_{ch}", "to": f"check_{ch}"},
            {"from": f"check_{ch}", "to": f"approve_{ch}"},
            {"from": f"approve_{ch}", "to": f"export_{ch}"},
        ]
        if ch == "wechat" and p.get("publish_wechat", True):
            nodes.append(_node("cover_wechat", "generate_cover", "AI 封面 · 公众号", {"channel": "wechat"}, 1380, y))
            nodes.append(_node("publish_wechat", "publish_wechat", "公众号草稿箱", {"channel": "wechat"}, 1610, y))
            edges += [
                {"from": "approve_wechat", "to": "cover_wechat"},
                {"from": "cover_wechat", "to": "publish_wechat"},
                {"from": "publish_wechat", "to": "export_wechat"},
            ]
            # 发布后导出（封面已入链）
            edges = [e for e in edges if not (e["from"] == "approve_wechat" and e["to"] == "export_wechat")]
    return {"nodes": nodes, "edges": edges}


TEMPLATES = {
    "daily_suggest": {
        "name": "每日舆情 → 荐题",
        "description": "拉取监测数据 → 抽取候选 → 人工确认事实 → 打包冻结 → AI 荐题 → 人工采纳",
        "builder": build_daily_suggest,
        "params_schema": [
            {"key": "endpoint_id", "label": "监测数据端点", "type": "endpoint", "required": True},
            {"key": "count", "label": "荐题候选数", "type": "number", "default": 3},
        ],
    },
    "gen_export": {
        "name": "生成 → 出库（按渠道分叉）",
        "description": "共享一个选题，抖音/小红书/公众号各自一条线：生成 → 事实校验 → 人工批准 → 导出；公众号线接草稿箱",
        "builder": build_gen_export,
        "params_schema": [
            {"key": "channels", "label": "渠道线", "type": "channels", "default": ["douyin", "xiaohongshu", "wechat"]},
            {"key": "publish_wechat", "label": "公众号线接草稿箱", "type": "boolean", "default": True},
        ],
    },
}


def build_definition(template_key: str, params: dict | None = None) -> dict[str, Any]:
    template = TEMPLATES.get(template_key)
    if not template:
        raise ValueError(f"未知模板: {template_key}")
    return template["builder"](params or {})
