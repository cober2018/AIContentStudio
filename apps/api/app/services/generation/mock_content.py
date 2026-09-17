"""Mock 结构化输出：确定性生成，数字全部来自 FactPack，保证 FactCheck 可闭环验证。

inject_unfact=True 时注入一个 FactPack 外的数字，用于验证 Deterministic Checker
能产生 blocker 并阻止 approve（执行计划 §22 用例 11-13）。
"""

from typing import Any

from .providers import GenerateRequest

UNFACT_NUMBER = 87.3


def _fmt_value(fact: dict[str, Any]) -> str:
    value = fact.get("value")
    unit = fact.get("unit") or ""
    if unit == "%":
        return f"{value}%"
    return f"{value}{unit}"


def _fact_lines(facts: list[dict[str, Any]]) -> list[str]:
    return [f"{f['statement']}（截至 {f.get('as_of') or '未知日期'}）" for f in facts]


def _injected_statement(facts: list[dict[str, Any]]) -> str:
    return f"值得注意的是，板块资金净流入达到 {UNFACT_NUMBER}%，创近期新高。"


def build_structured_output(request: GenerateRequest, inject_unfact: bool) -> dict[str, Any]:
    context = request.context or {}
    topic = context.get("topic", {})
    facts: list[dict[str, Any]] = context.get("facts", [])
    brand = context.get("brand_voice", {})
    channel = request.channel or "douyin"

    builders = {
        "douyin": _build_douyin,
        "xiaohongshu": _build_xiaohongshu,
        "wechat": _build_wechat,
    }
    builder = builders.get(channel, _build_douyin)
    output = builder(topic, facts, brand)

    if inject_unfact and facts:
        _inject_unfact(output, channel)
    return output


def _topic_title(topic: dict[str, Any]) -> str:
    return topic.get("title") or "今日内容"


def _build_douyin(topic: dict, facts: list[dict], brand: dict) -> dict[str, Any]:
    core = topic.get("core_thesis") or _topic_title(topic)
    fact_lines = _fact_lines(facts)
    scene_facts = facts[:4] if facts else []

    scenes = [
        {
            "index": 1,
            "script": f"先说背景：{topic.get('angle') or core}。{fact_lines[0] if fact_lines else ''}",
            "fact_ids": [scene_facts[0]["id"]] if scene_facts else [],
            "on_screen_text": core[:20],
            "broll_prompt": "数据大屏动画，字幕逐条浮现",
        },
        {
            "index": 2,
            "script": f"核心观点：{core}。{fact_lines[1] if len(fact_lines) > 1 else ''}",
            "fact_ids": [scene_facts[1]["id"]] if len(scene_facts) > 1 else [],
            "on_screen_text": "为什么值得关注",
            "broll_prompt": "趋势曲线上升镜头",
        },
        {
            "index": 3,
            "script": f"证据来了：{fact_lines[2] if len(fact_lines) > 2 else ''}。这些数字都来自公开数据。",
            "fact_ids": [scene_facts[2]["id"]] if len(scene_facts) > 2 else [],
            "on_screen_text": "数据说话",
            "broll_prompt": "表格数据特写",
        },
        {
            "index": 4,
            "script": "当然也要提示风险：市场存在不确定性，以上不构成投资建议。",
            "fact_ids": [],
            "on_screen_text": "风险提示",
            "broll_prompt": "风险提示字幕页",
        },
    ]

    spoken = f"今天聊聊这个话题。{core}。" + " ".join(s["script"] for s in scenes)
    if topic.get("cta"):
        spoken += f" {topic['cta']}"

    return {
        "title": _topic_title(topic),
        "hook": f"今天有一个变化值得注意：{core}",
        "spoken_script": spoken,
        "scenes": scenes,
        "risk_note": "市场有风险，内容不构成投资建议。",
        "estimated_length_seconds": max(30, len(spoken) // 4),
        "claim_fact_map": [
            {"text": f["statement"], "fact_ids": [f["id"]]} for f in scene_facts
        ],
    }


def _build_xiaohongshu(topic: dict, facts: list[dict], brand: dict) -> dict[str, Any]:
    core = topic.get("core_thesis") or _topic_title(topic)
    fact_lines = _fact_lines(facts)
    used = facts[:5]
    body_parts = [f"{topic.get('angle') or core}\n"]
    body_parts.extend(f"- {line}" for line in fact_lines)
    if topic.get("cta"):
        body_parts.append(f"\n{topic['cta']}")
    body = "\n".join(body_parts)

    return {
        "titles": [f"{core[:15]}｜数据一次看懂", f"3 分钟读懂：{core[:12]}"],
        "cover_text": core[:12],
        "body": body,
        "cards": [{"index": i + 1, "text": line} for i, line in enumerate(fact_lines[:4])],
        "image_prompts": ["简洁数据图表风格封面，浅色底，大字标题", "趋势折线图卡片，标注来源与日期"],
        "tags": ["数据复盘", "财经科普", "理性看市场"],
        "claim_fact_map": [{"text": f["statement"], "fact_ids": [f["id"]]} for f in used],
    }


def _build_wechat(topic: dict, facts: list[dict], brand: dict) -> dict[str, Any]:
    core = topic.get("core_thesis") or _topic_title(topic)
    fact_lines = _fact_lines(facts)
    used = facts[:6]
    sections = [
        {"heading": "发生了什么", "body": "\n\n".join(fact_lines[:3]) or core},
        {"heading": "怎么理解", "body": f"{topic.get('angle') or core}。综合以上数据，可以更完整地看待当前情况。"},
        {"heading": "需要注意什么", "body": "数据只是截面，任何单一指标都不能代表全貌。"},
    ]
    ending = topic.get("cta") or "关注我们，每周用数据看懂市场。"
    sources = [f"{f['statement']}（来源：{f.get('source_title', 'Source')}，截至 {f.get('as_of') or '未知'}）" for f in used]

    return {
        "titles": [_topic_title(topic)],
        "summary": core,
        "intro": f"本期我们用 FactPack 中的 {len(facts)} 条事实，复盘这个话题。",
        "sections": sections,
        "risk_note": "本文仅为信息整理，不构成任何投资建议。",
        "ending": ending,
        "image_suggestions": ["开头放全景图", "每节配一张数据图，标注来源日期"],
        "claim_fact_map": [{"text": f["statement"], "fact_ids": [f["id"]]} for f in used],
        "sources": sources,
    }


def _inject_unfact(output: dict[str, Any], channel: str) -> None:
    statement = _injected_statement([])
    if channel == "douyin" and output.get("scenes"):
        output["scenes"].append(
            {
                "index": len(output["scenes"]) + 1,
                "script": statement,
                "fact_ids": [],
                "on_screen_text": "资金流向",
                "broll_prompt": "资金流向动画",
            }
        )
        output["spoken_script"] += " " + statement
    elif channel == "xiaohongshu":
        output["body"] += f"\n- {statement}"
    elif channel == "wechat" and output.get("sections"):
        output["sections"][0]["body"] += "\n\n" + statement
