"""Prompt 组装与 Draft 正文渲染。"""

import json
from pathlib import Path

from ...models import Channel

PROMPT_DIR = Path(__file__).resolve().parents[2] / "llm" / "prompts"


def compose_prompt(
    channel: str,
    topic_brief_text: str,
    facts: list[dict],
    brand_voice_text: str,
    domain_knowledge_block: str = "",
) -> str:
    template_path = PROMPT_DIR / f"{channel}.txt"
    template = template_path.read_text(encoding="utf-8")
    # wechat 模板注入 wewrite 风格块（style.yaml 缺失时为空串，模板不破）
    if "{style_block}" in template:
        from ..writing_pipeline import style_prompt_block

        template = template.replace("{style_block}", style_prompt_block())
    # 领域知识块（方法论 + 涉及指标的口径卡）；知识文档缺席时为空串，模板不破
    template = template.replace("{domain_knowledge_block}", domain_knowledge_block)
    # 模板内含 JSON 示例的花括号，不能用 str.format，只能做占位符替换
    return (
        template.replace("{topic_brief}", topic_brief_text)
        .replace("{fact_pack}", json.dumps(facts, ensure_ascii=False, indent=1))
        .replace("{brand_voice}", brand_voice_text)
    )


def topic_brief_text(topic) -> str:
    parts = [
        f"标题：{topic.title}",
        f"受众：{topic.audience or '-'}",
        f"目标：{topic.goal or '-'}",
        f"角度：{topic.angle or '-'}",
        f"核心结论：{topic.core_thesis or '-'}",
        f"必须包含：{'、'.join(topic.must_include_json or []) or '-'}",
        f"禁止出现：{'、'.join(topic.forbidden_json or []) or '-'}",
        f"CTA：{topic.cta or '-'}",
    ]
    return "\n".join(parts)


def brand_voice_text(brand_voice) -> str:
    if brand_voice is None:
        return "（未配置，使用默认客观风格）"
    return "\n".join(
        [
            f"名称：{brand_voice.name} v{brand_voice.version}",
            f"语气规则：{'；'.join(brand_voice.tone_rules or [])}",
            f"偏好用词：{'、'.join(brand_voice.preferred_words or [])}",
            f"禁用词：{'、'.join(brand_voice.forbidden_words or [])}",
        ]
    )


def render_body(channel: str, structured: dict) -> str:
    renderer = {
        Channel.douyin.value: _render_douyin,
        Channel.xiaohongshu.value: _render_xiaohongshu,
        Channel.wechat.value: _render_wechat,
    }[channel]
    return renderer(structured)


def _render_douyin(s: dict) -> str:
    lines = [f"# {s.get('title', '')}", "", f"**Hook**：{s.get('hook', '')}", "", "## 口播脚本", "", s.get("spoken_script", ""), "", "## 分镜"]
    for scene in s.get("scenes", []):
        fact_ids = ", ".join(scene.get("fact_ids", [])) or "-"
        lines.append(f"{scene.get('index')}. {scene.get('script', '')}")
        lines.append(f"   - 字幕：{scene.get('on_screen_text', '')}")
        lines.append(f"   - B-roll：{scene.get('broll_prompt', '')}")
        lines.append(f"   - 引用事实：{fact_ids}")
    lines += ["", f"**风险提示**：{s.get('risk_note', '')}", f"**预估时长**：{s.get('estimated_length_seconds', '-')} 秒（估算仅供参考）"]
    return "\n".join(lines)


def _render_xiaohongshu(s: dict) -> str:
    titles = s.get("titles", [])
    lines = [f"# {titles[0] if titles else ''}", ""]
    if len(titles) > 1:
        lines.append(f"标题候选：{' / '.join(titles)}")
        lines.append("")
    lines.append(f"**封面文案**：{s.get('cover_text', '')}")
    lines += ["", "## 正文", "", s.get("body", ""), "", "## 卡片"]
    for card in s.get("cards", []):
        lines.append(f"{card.get('index')}. {card.get('text', '')}")
    lines += ["", "## 图片 Prompt"]
    lines.extend(f"- {p}" for p in s.get("image_prompts", []))
    lines += ["", f"**Tags**：{' '.join('#' + t for t in s.get('tags', []))}"]
    return "\n".join(lines)


def _render_wechat(s: dict) -> str:
    titles = s.get("titles", [])
    lines = [
        f"# {titles[0] if titles else ''}",
        "",
        f"> 摘要：{s.get('summary', '')}",
        "",
        s.get("intro", ""),
        "",
    ]
    for section in s.get("sections", []):
        lines += [f"## {section.get('heading', '')}", "", section.get("body", ""), ""]
    lines += [
        f"**风险提示**：{s.get('risk_note', '')}",
        "",
        s.get("ending", ""),
        "",
        "## 数据来源",
    ]
    lines.extend(f"- {src}" for src in s.get("sources", []))
    lines.extend(f"- {p}" for p in s.get("image_suggestions", []))
    return "\n".join(lines)
