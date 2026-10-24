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
    """公众号文章：markdown + wechat html（复用 wechat_html.render_wechat_html）。"""

    key = "renderer.wechat.article"
    version = "1"

    def render(self, source: dict) -> RenderResult:
        from ...services.wechat_html import render_wechat_html

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
    """渠道×形态 → renderer key。profile 未声明时问渠道方法插件。"""
    from .channel_methods import renderer_key_for

    return renderer_key_for(channel, content_form)
