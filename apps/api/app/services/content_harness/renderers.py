"""Renderer Registry（D19/§6.10 拆职责）：平台渲染输出在批准前冻结。

render(candidate_source) -> RenderResult(renderer_key, version, payload, content_hash, warnings)。
Publisher 不做实质格式变换（Phase 5）。legacy 三渠道 render 仍在
generation/renderers.py 供旧生成链使用；新受控链一律走本 registry。
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Protocol

from .contracts import RenderResult
from .registry import registry


class RendererPlugin(Protocol):
    key: str
    version: str

    def render(self, source: dict[str, Any]) -> RenderResult: ...


def _hash_payload(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()


class WechatArticleRenderer:
    """公众号文章：markdown + wechat html（复用 exports.render_wechat_html）。"""

    key = "renderer.wechat.article"
    version = "1"

    def render(self, source: dict) -> RenderResult:
        from ...services.exports import render_wechat_html

        title = source.get("title") or ""
        body = source.get("body_markdown") or ""
        payload = {
            "title": title,
            "markdown": body,
            "html": render_wechat_html(title, body, "已批准候选渲染"),
            "digest": (source.get("structured") or {}).get("summary") or title[:54],
        }
        return RenderResult(
            renderer_key=self.key, version=self.version, payload=payload,
            content_hash=_hash_payload(payload), warnings=[],
        )


class XThreadRenderer:
    """X Thread：有序推串 JSON + markdown。"""

    key = "renderer.x.thread"
    version = "1"

    def render(self, source: dict) -> RenderResult:
        posts = source.get("thread_posts") or []
        payload = {
            "title": source.get("title") or "",
            "thread_posts": posts,
            "markdown": "\n\n".join(f"{p.get('index', i + 1)}. {p.get('text', '')}" for i, p in enumerate(posts)),
        }
        warnings = [] if posts else ["missing_thread_posts"]
        return RenderResult(renderer_key=self.key, version=self.version, payload=payload, content_hash=_hash_payload(payload), warnings=warnings)


class GenericMarkdownRenderer:
    """通用 markdown copy renderer（无 verified publisher 平台的兜底格式）。"""

    key = "renderer.generic.markdown"
    version = "1"

    def render(self, source: dict) -> RenderResult:
        payload = {"title": source.get("title") or "", "markdown": source.get("body_markdown") or ""}
        return RenderResult(renderer_key=self.key, version=self.version, payload=payload, content_hash=_hash_payload(payload), warnings=[])


class XhsCardsRenderer:
    """小红书卡片 manifest：有序卡片 + 真实图片清单（含 placement/rights）。"""

    key = "renderer.xhs.cards"
    version = "1"

    def render(self, source: dict) -> RenderResult:
        structured = source.get("structured") or {}
        media = source.get("media") or []
        cards = [{"index": i + 1, "text": c.get("text", "")} for i, c in enumerate(structured.get("cards") or [])]
        payload = {
            "title": source.get("title") or "",
            "body_markdown": source.get("body_markdown") or "",
            "tags": structured.get("tags") or [],
            "cards": cards,
            "media": [
                {
                    "draft_media_id": m.get("draft_media_id"),
                    "material_revision_id": m.get("material_revision_id"),
                    "hash": m.get("hash"),
                    "sort_order": m.get("sort_order"),
                    "role": m.get("role"),
                }
                for m in sorted(media, key=lambda x: x.get("sort_order") or 0)
            ],
        }
        warnings = []
        if not payload["media"]:
            warnings.append("no_actual_media")
        return RenderResult(renderer_key=self.key, version=self.version, payload=payload, content_hash=_hash_payload(payload), warnings=warnings)


_BOOTSTRAPPED = False


def bootstrap_renderers() -> None:
    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return
    for plugin in (WechatArticleRenderer(), XThreadRenderer(), GenericMarkdownRenderer(), XhsCardsRenderer()):
        if plugin.key not in {d.key for d in registry.list("renderer")}:
            registry.register("renderer", plugin.key, plugin.version, plugin, label=plugin.key)
    _BOOTSTRAPPED = True


def resolve_renderer_key(channel: str, content_form: str | None) -> str:
    """渠道×形态 → renderer key（profile 未定义时的静态映射；profile 可覆盖）。"""
    if channel == "wechat":
        return "renderer.wechat.article"
    if channel in {"x", "x_thread"} and content_form in {None, "thread"}:
        return "renderer.x.thread"
    if channel == "x_thread":
        return "renderer.x.thread"
    if channel == "xiaohongshu":
        return "renderer.xhs.cards"
    return "renderer.generic.markdown"


def render_for(db, draft, *, media: list[dict] | None = None) -> RenderResult:
    """对 draft 求渲染（批准前冻结）。media 为 manifest v2 media 结构（可空）。

    R2-M9：renderer 由 Channel Profile 的 renderer_key 驱动（Profile→Renderer 插件架构）；
    profile 未声明时才退回静态渠道映射。
    """
    bootstrap_renderers()
    job = draft.content_job
    content_form = getattr(draft, "content_form", None) or job.content_form
    key = None
    try:
        from .channel_registry import resolve_content_form

        spec = resolve_content_form(db, job.channel, content_form)
        if spec.source == "profile" and spec.renderer_key:
            key = spec.renderer_key
    except Exception:  # noqa: BLE001 渠道解析失败：走静态兜底
        key = None
    if not key:
        key = resolve_renderer_key(job.channel, content_form)
    try:
        plugin = registry.resolve("renderer", key, None)
    except Exception:  # noqa: BLE001 profile 声明了未注册的 renderer：如实降级并记 warning
        plugin = registry.resolve("renderer", "renderer.generic.markdown", "1")
        source = {
            "title": draft.title,
            "body_markdown": draft.body,
            "structured": draft.structured_json or {},
            "thread_posts": draft.thread_posts_json or [],
            "media": media or [],
        }
        result = plugin.render(source)
        return RenderResult(
            renderer_key=result.renderer_key, version=result.version, payload=result.payload,
            content_hash=result.content_hash, warnings=[f"renderer_unregistered:{key}"],
        )
    source = {
        "title": draft.title,
        "body_markdown": draft.body,
        "structured": draft.structured_json or {},
        "thread_posts": draft.thread_posts_json or [],
        "media": media or [],
    }
    return plugin.render(source)
