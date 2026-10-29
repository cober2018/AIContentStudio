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
    if request.schema_hint == "creation_recipe.tuning.v1":
        base, allowed = context.get("base_config", {}), context.get("tunable_schema", {})
        if "candidate_count" in allowed:
            value = base.get("candidate_count", 1)
            patch = {"candidate_count": 3 if value != 3 else 2}
        elif "instruction" in allowed:
            patch = {"instruction": f"{base.get('instruction', '')}\n明确展示可选择的结果；等待人工确认。"}
        else:
            raise ValueError("Mock tuner has no declared field")
        return {"config_patch": patch, "explanation": "隔离Mock建议，仅验证可调字段和显式保存链路，不代表AI学习质量。"}
    if request.schema_hint == "stage.master.proposal.v1":
        count = context.get("candidate_count", 1)
        if type(count) is not int or not 1 <= count <= 5:
            raise ValueError("invalid Mock Stage candidate count")
        modality = context.get("modality", "text")
        length = context.get("length", "medium")
        repeats = {"short": 1, "medium": 2, "long": 3}[length]
        candidates = []
        for index in range(1, count + 1):
            title = f"隔离 Mock 候选 {index}"
            body = f"这是第 {index} 个隔离验收候选，仅用于验证阶段调节、人工编辑与采用链路，不代表真实模型生成质量。"
            body = "\n\n".join([body] * repeats)
            if request.purpose != "generate":
                body = f"阶段用途：{request.purpose}。\n\n{body}"
            if modality == "text":
                from ..text_documents import convert_legacy_text

                payload = convert_legacy_text({"title": title, "markdown": f"# {title}\n\n{body}"})["payload"]
            elif modality == "graphic":
                payload = {"title": title, "canvases": [{
                    "id": "canvas-1", "order": 0, "width": 1080, "height": 1440,
                    "background": {"color": "#ffffff"},
                    "layers": [{"id": "text-1", "order": 0, "type": "text", "x": 80, "y": 80,
                                "width": 920, "height": 1200,
                                "runs": [{"text": body, "style": {"font_size": 36, "color": "#111111"}}]}],
                }]}
            elif modality == "video":
                duration = {"short": 5000, "medium": 15000, "long": 30000}[length]
                payload = {
                    "title": title, "aspect_ratio": [9, 16],
                    "script": {"blocks": [{"id": "script-1", "order": 0, "text": body}]},
                    "shots": [{"id": "shot-1", "order": 0, "label": "待绑定素材的镜头计划",
                               "purpose": request.purpose, "duration_ms": duration, "script_block_id": "script-1"}],
                    "timeline": {"duration_ms": duration, "tracks": [{
                        "id": "video-1", "order": 0, "kind": "video",
                        "items": [{"id": "item-1", "order": 0, "shot_id": "shot-1",
                                   "start_ms": 0, "end_ms": duration}],
                    }]},
                    "voice": {"mode": "none"}, "subtitles": {"cues": []}, "overlays": [],
                    "music": {}, "cover": {},
                }
            else:
                raise ValueError("invalid Mock Stage modality")
            candidates.append({"payload_schema": f"{modality}.master.v2", "payload": payload,
                               "asset_refs": [], "evidence_refs": []})
        return {"candidates": candidates}
    if request.schema_hint == "stage.creative.method.v1":
        schema = context.get("output_schema", "content.outline.v1")
        count = max(1, min(int(context.get("candidate_count", 1)), 5))
        candidates = []
        for index in range(1, count + 1):
            summary = f"隔离 Mock {schema} 候选 {index}"
            content = {
                "title": summary,
                "sections": [{"id": "section-1", "order": 0, "heading": "下一步", "purpose": "保留事实边界",
                              "points": ["等待人工确认"], "open_questions": ["尚未提供可引用的来源"]}],
            }
            if schema == "research.brief.v1":
                content = {"question": summary, "known": [], "unknowns": ["尚未提供可引用的来源"],
                           "time_boundary": "没有可核验的时间边界"}
            elif schema == "article.plan.v1":
                content = {"title": summary, "angle": "先看清限制", "reader_stake": "需要知道能不能用",
                           "known": [], "unknowns": ["尚未提供可引用的来源"], "sections": content["sections"]}
            elif schema == "creative.angles.v1":
                content = {"angle": summary, "reader_stake": "需要看清限制", "question": "下一步如何选择",
                           "support": "只使用已提供的材料", "limits": "不把缺失来源写成事实"}
            elif schema == "creative.title-hook.v1":
                content = {"title": summary, "hook": "先看清限制，再决定要不要展开。", "reason": "标题不承诺正文没有的事实"}
            elif schema == "video.script.v1":
                content = {"title": summary, "beats": [{"id": "beat-1", "order": 0, "narration": "这是隔离口播，不代表成片。",
                    "visual": "待准备画面", "asset_requirements": [], "unknowns": ["没有可引用的画面素材"]}]}
            elif schema == "graphic.visual-direction.v1":
                content = {"intent": summary, "hierarchy": ["标题", "具体观察"],
                    "visual_language": "隔离合同样例，不代表真实视觉质量", "image_requirements": []}
            elif schema == "graphic.card-plan.v1":
                content = {"title": summary, "aspect_ratio": "3:4", "cards": [{
                    "id": "cover", "order": 0, "role": "cover", "title": "隔离卡片计划",
                    "body": "只验证语义计划与确定性排版合同。", "visual_type": "none"}]}
            elif schema == "text.spoken-adaptation.v1":
                content = {"script": "这是隔离口语稿合同样例，不代表真实音频质量。", "pronunciation_notes": [],
                    "source_summary": summary, "warnings": ["mock_output_not_quality_evidence"]}
            elif schema == "video.shot-plan.v1":
                content = {"title": summary, "shots": [{"id": "shot-1", "order": 0,
                    "script": "隔离脚本", "visual": "待准备画面", "asset_requirements": [], "duration_seconds": 5}]}
            candidates.append({"id": f"method-{index:02d}", "summary": summary, "content": content,
                               "references": [], "warnings": ["mock_output_not_quality_evidence"]})
        return {"schema": schema, "candidates": candidates}
    if request.purpose == "text_master_edit":
        return _build_text_master_edit(context)
    topic = context.get("topic", {})
    facts: list[dict[str, Any]] = context.get("facts", [])
    brand = context.get("brand_voice", {})
    channel = request.channel or "douyin"

    if request.purpose == "suggest_topics":
        return _build_topic_suggestions(facts, context.get("count", 3))

    from ..content_harness.channel_methods import mock_shape, mock_unfact_kind

    builders = {
        "spoken_script": _build_douyin,
        "image_note": _build_xiaohongshu,
        "article": _build_wechat,
    }
    output = builders[mock_shape(channel)](topic, facts, brand)

    if inject_unfact and facts:
        kind = mock_unfact_kind(channel)
        if kind:
            _inject_unfact(output, kind)
    return output


def _build_text_master_edit(context: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic provider candidate; the service still validates/applies it."""
    operation = context.get("operation")
    selection = context.get("selection") or {}
    selected = str(context.get("selected_text") or "")
    if operation == "restructure":
        return {"patch": {"kind": "replace_blocks", "from_block_id": selection.get("from_block_id"), "to_block_id": selection.get("to_block_id"), "blocks": context.get("selected_blocks") or []}}
    if operation == "shorten":
        replacement = selected[: max(1, len(selected) // 2)]
    elif operation == "expand":
        replacement = f"{selected}。补充说明：这部分内容需要结合上下文理解。"
    elif operation == "tone":
        replacement = f"换个角度看，{selected}"
    else:
        replacement = f"{selected}（改写建议）"
    return {"patch": {"kind": "replace_text", "block_id": selection.get("block_id"), "list_item_id": selection.get("list_item_id"), "start": selection.get("start"), "end": selection.get("end"), "replacement": [{"text": replacement, "marks": []}]}}


def _build_topic_suggestions(facts: list[dict[str, Any]], count: int) -> dict[str, Any]:
    """选题发现 mock：确定性三角度，素材全部来自给定 facts，不引入外部数字。"""
    count = max(1, min(int(count or 3), 5))
    angles = [
        ("风险防守视角", "先把压力讲清楚，再谈机会", "帮助观众识别风险、稳住仓位"),
        ("结构性机会视角", "聚焦仍强的主线与数据交叉验证", "帮观众抓住结构性方向"),
        ("数据深读视角", "把看板数字翻译成普通人的决策语言", "让观众看懂数据背后的含义"),
    ]
    fact_lines = _fact_lines(facts)
    suggestions = []
    for i in range(min(count, len(angles))):
        label, angle, goal = angles[i]
        headline = fact_lines[i] if i < len(fact_lines) else (fact_lines[0] if fact_lines else "今日市场数据")
        suggestions.append(
            {
                "title": f"{label}：{headline[:26]}",
                "audience": "关注A股与宏观的个人投资者",
                "goal": goal,
                "angle": angle,
                "core_thesis": f"基于已确认事实展开：{headline[:40]}",
                "must_include": [line[:14] for line in fact_lines[:3]],
                "forbidden": ["保证收益", "一定上涨", "稳赚"],
                "cta": "关注获取每日量化复盘",
                "rationale": f"覆盖事实 {min(i + 1, len(fact_lines))} 条中的核心条目，适合{label}叙事。",
            }
        )
    return {"suggestions": suggestions}


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


def _inject_unfact(output: dict[str, Any], kind: str) -> None:
    statement = _injected_statement([])
    if kind == "scenes" and output.get("scenes"):
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
    elif kind == "body":
        output["body"] += f"\n- {statement}"
    elif kind == "sections" and output.get("sections"):
        output["sections"][0]["body"] += "\n\n" + statement
