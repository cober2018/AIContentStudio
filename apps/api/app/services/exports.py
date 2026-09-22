"""导出服务（STU-121~123）：Markdown / TXT / JSON / SRT / HTML（公众号微信兼容风）。"""

import html
import json
import re

from ..models import Channel, ContentAsset

_MD_MARKERS = re.compile(r"^[#>]+\s*|\*\*|\*|^-\s", re.MULTILINE)

# 中文字幕估算速度：每秒约 4 字（SRT 无真实时间轴时必须标记 estimated，不假装精确）
SRT_CHARS_PER_SECOND = 4.0


def export_markdown(asset: ContentAsset) -> str:
    return asset.final_body


def export_txt(asset: ContentAsset) -> str:
    text = _MD_MARKERS.sub("", asset.final_body)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def export_json(asset: ContentAsset) -> str:
    payload = {
        "metadata": {
            "asset_id": asset.id,
            "channel": asset.channel,
            "title": asset.title,
            "approved_revision": asset.approved_revision,
            "reviewer": asset.reviewer,
            "created_at": asset.created_at.isoformat() if asset.created_at else None,
        },
        "content": asset.structured_json,
        "final_body": asset.final_body,
        "fact_citations": _extract_citations(asset),
        "provenance": {
            "fact_pack": {
                "id": asset.fact_pack_id,
                "version": asset.fact_pack_version,
                "checksum": asset.fact_pack_checksum,
            },
            "model": {"provider": asset.model_provider, "model": asset.model_name},
            "prompt_version": asset.prompt_version,
            "template_version_id": asset.template_version_id,
        },
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def export_srt(asset: ContentAsset) -> str:
    if asset.channel != Channel.douyin.value:
        raise ValueError("SRT 导出仅支持抖音口播稿")
    structured = asset.structured_json or {}
    script = structured.get("spoken_script") or ""
    sentences = [s.strip() for s in re.split(r"[。！？!?；;\n]+", script) if s.strip()]
    entries = []
    cursor_ms = 0
    for idx, sentence in enumerate(sentences, start=1):
        duration_ms = int(len(sentence) / SRT_CHARS_PER_SECOND * 1000)
        entries.append(f"{idx}\n{_format_srt_time(cursor_ms)} --> {_format_srt_time(cursor_ms + duration_ms)}\n{sentence}\n")
        cursor_ms += duration_ms + 200  # 句间留 200ms 停顿
    header = (
        f"NOTE 生成自 AI Content Studio；时间轴为按 {SRT_CHARS_PER_SECOND:.0f} 字/秒估算（estimated），"
        "非真实音频时间，接入 TTS 后替换。\n\n"
    )
    return header + "\n".join(entries)


def _format_srt_time(ms: int) -> str:
    hours, rem = divmod(ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    seconds, millis = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def _extract_citations(asset: ContentAsset) -> list[dict]:
    structured = asset.structured_json or {}
    citations = []
    for claim in structured.get("claim_fact_map", []) or []:
        citations.append({"text": claim.get("text"), "fact_ids": claim.get("fact_ids", [])})
    for scene in structured.get("scenes", []) or []:
        if scene.get("fact_ids"):
            citations.append({"text": scene.get("script", "")[:80], "fact_ids": scene.get("fact_ids", [])})
    return citations


# ---------- HTML（公众号微信兼容风：全内联样式，无外部依赖的简易 MD 渲染） ----------

_INLINE_RE = re.compile(r"(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)")


def _inline_md(text: str) -> str:
    """行内 Markdown（粗体/斜体/代码）→ HTML，其余字符转义。"""
    parts = _INLINE_RE.split(text)
    out = []
    for part in parts:
        if part.startswith("**") and part.endswith("**"):
            out.append(f'<strong style="font-weight:600;color:#1f2937;">{html.escape(part[2:-2])}</strong>')
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            out.append(f"<em>{html.escape(part[1:-1])}</em>")
        elif part.startswith("`") and part.endswith("`"):
            out.append(
                f'<code style="background:#f3f4f6;padding:1px 5px;border-radius:3px;font-size:0.9em;">'
                f"{html.escape(part[1:-1])}</code>"
            )
        else:
            out.append(html.escape(part))
    return "".join(out)


def _md_to_html(md: str) -> str:
    """V1 简易渲染：标题/列表/引用/分隔线/段落。表格与图片走占位提示（公众号编辑器内再补）。"""
    lines = md.split("\n")
    out: list[str] = []
    in_list: str | None = None  # ul / ol
    H_STYLE = {
        "#": 'font-size:20px;font-weight:700;color:#111827;line-height:1.4;margin:24px 0 12px;',
        "##": 'font-size:18px;font-weight:700;color:#111827;border-left:4px solid #6366f1;padding-left:10px;line-height:1.4;margin:22px 0 10px;',
        "###": 'font-size:16px;font-weight:600;color:#374151;margin:18px 0 8px;',
    }

    def close_list():
        nonlocal in_list
        if in_list:
            out.append(f"</{in_list}>")
            in_list = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            close_list()
            continue
        if stripped in ("---", "***", "___"):
            close_list()
            out.append('<hr style="border:none;border-top:1px solid #e5e7eb;margin:20px 0;"/>')
            continue
        heading = re.match(r"^(#{1,3})\s+(.*)$", stripped)
        if heading:
            close_list()
            level = heading.group(1)
            out.append(f"<h{len(level)} style=\"{H_STYLE[level]}\">{_inline_md(heading.group(2))}</h{len(level)}>")
            continue
        if stripped.startswith(">"):
            close_list()
            out.append(
                '<blockquote style="border-left:3px solid #d1d5db;background:#f9fafb;'
                'padding:8px 12px;margin:10px 0;color:#6b7280;font-size:14px;">'
                f"{_inline_md(stripped.lstrip('> ').strip())}</blockquote>"
            )
            continue
        ul = re.match(r"^[-*]\s+(.*)$", stripped)
        ol = re.match(r"^\d+[.、]\s+(.*)$", stripped)
        if ul:
            if in_list != "ul":
                close_list()
                out.append('<ul style="padding-left:22px;margin:8px 0;">')
                in_list = "ul"
            out.append(
                '<li style="margin:4px 0;line-height:1.8;color:#374151;font-size:15px;">'
                f"{_inline_md(ul.group(1))}</li>"
            )
            continue
        if ol:
            if in_list != "ol":
                close_list()
                out.append('<ol style="padding-left:22px;margin:8px 0;">')
                in_list = "ol"
            out.append(
                '<li style="margin:4px 0;line-height:1.8;color:#374151;font-size:15px;">'
                f"{_inline_md(ol.group(1))}</li>"
            )
            continue
        close_list()
        out.append(
            f'<p style="margin:10px 0;line-height:1.85;color:#374151;font-size:15px;letter-spacing:0.3px;">'
            f"{_inline_md(stripped)}</p>"
        )
    close_list()
    return "\n".join(out)


def render_wechat_html(title_text: str, body_markdown: str, footer_text: str = "") -> str:
    """Render immutable handoff content without consulting a mutable asset row."""
    body = _md_to_html(body_markdown)
    title = html.escape(title_text)
    footer = (
        '<p style="margin-top:28px;padding-top:12px;border-top:1px solid #e5e7eb;'
        'font-size:12px;color:#9ca3af;">本文由 AI Content Studio 生成，经事实校验与人工审核。'
        f"{html.escape(footer_text)}</p>"
    )
    return (
        '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">\n'
        f"<title>{title}</title>\n</head>\n"
        '<body style="margin:0;padding:0;background:#ffffff;">\n'
        '<article style="max-width:677px;margin:0 auto;padding:24px 16px;'
        'font-family:-apple-system,BlinkMacSystemFont,\'PingFang SC\',\'Microsoft YaHei\',sans-serif;">\n'
        f'<h1 style="font-size:22px;font-weight:700;color:#111827;line-height:1.5;margin:0 0 8px;">{title}</h1>\n'
        f"{body}\n{footer}\n</article>\n</body>\n</html>\n"
    )


def export_html(asset: ContentAsset) -> str:
    footer = f"事实包 v{asset.fact_pack_version}（checksum {asset.fact_pack_checksum or '-'}）"
    return render_wechat_html(asset.title, asset.final_body, footer)


EXPORTERS = {
    "md": export_markdown,
    "txt": export_txt,
    "json": export_json,
    "srt": export_srt,
    "html": export_html,
}

CHANNEL_ALLOWED_FORMATS = {
    Channel.douyin.value: ["md", "txt", "json", "srt"],
    Channel.xiaohongshu.value: ["md", "txt", "json"],
    Channel.wechat.value: ["md", "html", "txt", "json"],
}
