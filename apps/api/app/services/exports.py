"""导出服务（STU-121~123）：Markdown / TXT / JSON / SRT。"""

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


EXPORTERS = {
    "md": export_markdown,
    "txt": export_txt,
    "json": export_json,
    "srt": export_srt,
}

CHANNEL_ALLOWED_FORMATS = {
    Channel.douyin.value: ["md", "txt", "json", "srt"],
    Channel.xiaohongshu.value: ["md", "txt", "json"],
    Channel.wechat.value: ["md", "txt", "json"],
}
