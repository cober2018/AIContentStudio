"""渠道方法插件。

主流程只按渠道键取出这里注册的方法。拿掉一个渠道，是取消它的注册，
而不是到生成、渲染、交付或审批主函数里删一段条件。

插拔状态写在系统设置里，每次取方法都读这份状态。拔出后该方法不再参与，
插上后同一进程立即恢复，不用改主程序，也不用重启。

没有注册方法的渠道走通用行为：通用 Markdown、复制包，不提供远端草稿。
`x_thread` 仍注册，但不可选；它只给历史稿件保留读取方法。插上也不会把它变回可选渠道。
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class ChannelMethods:
    key: str
    selectable: bool = True
    retired_message: str | None = None
    renderer_key: str | None = None
    renderer_forms: frozenset[str | None] | None = None
    prompt_channel: str | None = None
    numbered_thread_body: bool = False
    require_cover: bool = False
    require_thread_posts: bool = False
    legacy_media: dict | None = None
    auto_draft_publisher: tuple[str, str] | None = None
    official_publisher: tuple[str, str] | None = None
    official_scope: Callable[[dict], bool] | None = None
    prepare_variant_auto_draft: Callable[[dict], dict] | None = None
    metadata_echo: bool = False
    m1_handoff: bool = False
    m1_content_form: str | None = None
    text_cover_form: str | None = None
    legacy_workflow: bool = False
    workflow_label: str | None = None
    workflow_formats: tuple[str, ...] = ()
    legacy_publish_extension: Callable[[dict, float], dict | None] | None = None
    template_params: tuple[dict, ...] = ()
    mock_shape: str | None = None
    mock_unfact: str | None = None
    length_guidance: dict | None = None
    m1_package: Callable[..., dict] | None = None


_PLUGINS: dict[str, ChannelMethods] = {}


def register(plugin: ChannelMethods) -> None:
    if plugin.key in _PLUGINS:
        raise RuntimeError(f"channel method 重复注册: {plugin.key}")
    _PLUGINS[plugin.key] = plugin


def unplugged_set() -> frozenset[str]:
    """已拔出的已安装渠道。没写过设置时全部视为插上。"""
    from ...runtime_config import KEY_CHANNEL_PLUGINS, get_runtime

    raw = get_runtime(KEY_CHANNEL_PLUGINS) or {}
    values = raw.get("unplugged") if isinstance(raw, dict) else None
    if not isinstance(values, list):
        return frozenset()
    return frozenset(item for item in values if isinstance(item, str) and item in _PLUGINS)


def unplugged_message(channel: str) -> str:
    return f"渠道 {channel} 已拔出。主程序和其他渠道继续运行；更新这个方法后可以重新插上。"


def is_unplugged(channel: str | None) -> bool:
    return bool(channel) and channel in unplugged_set()


def get(channel: str | None) -> ChannelMethods | None:
    if not channel or channel in unplugged_set():
        return None
    return _PLUGINS.get(channel)


def retired_message(channel: str | None) -> str | None:
    plugin = _PLUGINS.get(channel) if channel else None
    if plugin and not plugin.selectable and plugin.retired_message:
        return plugin.retired_message
    return None


def retired_map() -> dict[str, str]:
    return {
        plugin.key: plugin.retired_message
        for plugin in _PLUGINS.values()
        if not plugin.selectable and plugin.retired_message
    }


def renderer_key_for(channel: str, content_form: str | None) -> str:
    plugin = get(channel)
    if plugin and plugin.renderer_key and (plugin.renderer_forms is None or content_form in plugin.renderer_forms):
        return plugin.renderer_key
    return "renderer.generic.markdown"


def generation_prompt_channel(channel: str) -> str:
    plugin = get(channel)
    if plugin and plugin.prompt_channel:
        return plugin.prompt_channel
    return channel


def numbered_thread_body(channel: str) -> bool:
    plugin = get(channel)
    return bool(plugin and plugin.numbered_thread_body)


def readiness_gaps(channel: str, *, has_cover: bool, has_thread_posts: bool) -> list[str]:
    plugin = get(channel)
    if plugin is None:
        return []
    gaps: list[str] = []
    if plugin.require_cover and not has_cover:
        gaps.append("missing_required_cover")
    if plugin.require_thread_posts and not has_thread_posts:
        gaps.append("missing_thread_boundaries")
    return gaps


def legacy_media_requirements(channel: str) -> dict:
    plugin = get(channel)
    if plugin and plugin.legacy_media:
        return dict(plugin.legacy_media)
    return {}


def echoes_metadata_channel(channel: object) -> bool:
    if not isinstance(channel, str):
        return False
    plugin = get(channel)
    return bool(plugin and plugin.metadata_echo)


def m1_rejection(channel: str, *, content_form: str | None = None) -> str | None:
    installed = _PLUGINS.get(channel)
    if installed and not installed.selectable:
        return installed.retired_message
    if channel in unplugged_set():
        return unplugged_message(channel)
    plugin = get(channel)
    if plugin is None or not plugin.m1_handoff:
        return "M1 只支持公众号"
    if content_form is not None and content_form != plugin.m1_content_form:
        return f"{plugin.key} 的 M1 content_form 必须是 {plugin.m1_content_form}"
    return None


def allows_text_cover(channel: str, content_form: str) -> bool:
    plugin = get(channel)
    return bool(plugin and plugin.text_cover_form == content_form)


def matches_official_scope(scope: dict) -> bool:
    if not isinstance(scope, dict):
        return False
    channel = scope.get("channel")
    plugin = get(channel) if isinstance(channel, str) else None
    return bool(plugin and plugin.official_scope and plugin.official_scope(scope))


def workflow_meta(channel: str) -> dict:
    plugin = get(channel)
    if plugin and plugin.workflow_label:
        return {"label": plugin.workflow_label, "formats": list(plugin.workflow_formats)}
    return {"label": channel, "formats": ["md"]}


def legacy_workflow_channels() -> list[str]:
    unplugged = unplugged_set()
    return [plugin.key for plugin in _PLUGINS.values() if plugin.legacy_workflow and plugin.key not in unplugged]


def legacy_template_params() -> list[dict]:
    unplugged = unplugged_set()
    params: list[dict] = []
    for plugin in _PLUGINS.values():
        if plugin.key in unplugged:
            continue
        params.extend(plugin.template_params)
    return params


def length_guidance_for(channel: str) -> dict:
    plugin = get(channel)
    if plugin and plugin.length_guidance:
        return dict(plugin.length_guidance)
    return {"body_chars": "1500-3000"}


def mock_shape(channel: str) -> str:
    plugin = get(channel)
    return plugin.mock_shape if plugin and plugin.mock_shape else "article"


def mock_unfact_kind(channel: str) -> str | None:
    plugin = get(channel)
    return plugin.mock_unfact if plugin else None


def m1_package_content(channel: str, *, title: str, body: str, thread_posts: list, note: str) -> dict:
    plugin = get(channel)
    if plugin and plugin.m1_package:
        return plugin.m1_package(title=title, body=body, thread_posts=thread_posts, note=note)
    return {
        "markdown": body,
        "json": json.dumps(
            {"title": title, "thread_posts": thread_posts},
            ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ),
        "title": title,
    }


def _method_labels(plugin: ChannelMethods) -> list[str]:
    labels: list[str] = []
    if plugin.renderer_key:
        labels.append("专用渲染")
    if plugin.require_cover or plugin.legacy_media:
        labels.append("封面检查")
    if plugin.auto_draft_publisher or plugin.official_publisher:
        labels.append("草稿方法")
    if plugin.m1_handoff:
        labels.append("旧母稿交接")
    if plugin.legacy_workflow:
        labels.append("旧工作流")
    if plugin.metadata_echo:
        labels.append("交付回执标注")
    if plugin.require_thread_posts or plugin.numbered_thread_body or plugin.prompt_channel:
        labels.append("历史读取")
    if not plugin.selectable:
        labels.append("不可作为新渠道")
    return labels


def _label(plugin: ChannelMethods) -> str:
    if plugin.workflow_label:
        return plugin.workflow_label
    from .channel_registry import CHANNEL_LABELS

    return CHANNEL_LABELS.get(plugin.key, plugin.key)


def describe(plugin: ChannelMethods) -> dict:
    plugged = plugin.key not in unplugged_set()
    return {
        "key": plugin.key,
        "label": _label(plugin),
        "plugged": plugged,
        "selectable": plugin.selectable,
        "historical_only": not plugin.selectable,
        "methods": _method_labels(plugin),
    }


def plugin_catalog() -> dict:
    return {
        "items": [describe(plugin) for plugin in _PLUGINS.values()],
        "note": (
            "拔出只停用已经安装的渠道方法，不删除稿件、模板或图片，也不改主程序。"
            "插上立即生效，不用重启。这里不能上传代码；新的渠道方法要随程序更新出现在这张表里。"
            "已下线的历史方法即使插上，也不会回到可选渠道。草稿方法不是已验证的远端发布。"
        ),
    }


def set_plugged(db, channel: str, plugged: bool, actor: str | None) -> dict:
    """把一个已安装的渠道方法插上或拔出。未知键拒绝，不接受代码。"""
    from fastapi import HTTPException

    from ...models import AuditLog, SystemSetting
    from ...runtime_config import KEY_CHANNEL_PLUGINS, set_runtime, validate_persisted_configuration

    plugin = _PLUGINS.get(channel)
    if plugin is None:
        raise HTTPException(404, "没有安装这个渠道方法")
    current = set(unplugged_set())
    if plugged:
        current.discard(channel)
    else:
        current.add(channel)
    value = {"unplugged": sorted(current)}
    validate_persisted_configuration(value)
    row = db.get(SystemSetting, KEY_CHANNEL_PLUGINS)
    if row is None:
        db.add(SystemSetting(key=KEY_CHANNEL_PLUGINS, value=value, updated_by=actor))
    else:
        row.value = value
        row.updated_by = actor
    db.add(AuditLog(
        event="channel_plugin.plugged" if plugged else "channel_plugin.unplugged",
        actor=actor,
        entity_type="channel_plugin",
        entity_id=channel,
        detail_json={"plugged": plugged},
    ))
    db.commit()
    set_runtime(KEY_CHANNEL_PLUGINS, value)
    return describe(plugin)


def _wechat_official_scope(scope: dict) -> bool:
    return (
        scope.get("publisher_key") == "publisher.wechat.official"
        and scope.get("publisher_version") == "1"
        and scope.get("channel") == "wechat"
        and scope.get("content_form") == "article"
        and scope.get("action") == "auto_draft"
    )


def _prepare_wechat_auto_draft(manifest: dict) -> dict:
    from ..delivery import project_v5_wewrite_payload

    return project_v5_wewrite_payload(manifest)


def _wechat_m1_package(*, title: str, body: str, thread_posts: list, note: str) -> dict:
    from ..exports import render_wechat_html

    return {
        "markdown": body,
        "html": render_wechat_html(title, body, note),
        "title": title,
    }


def _wechat_publish_extension(params: dict, y: float) -> dict | None:
    if not params.get("publish_wechat", False):
        return None
    from ..workflow_templates import _node

    return {
        "nodes": [
            _node("cover_wechat", "generate_cover", "AI 封面 · 公众号", {"channel": "wechat"}, 1380, y),
            _node(
                "publish_wechat",
                "publish_wechat",
                "公众号草稿箱（遗留能力，显式启用）",
                {"channel": "wechat", "legacy_remote_publish": True},
                1610,
                y,
            ),
        ],
        "edges": [
            {"from": "approve_wechat", "to": "cover_wechat"},
            {"from": "cover_wechat", "to": "publish_wechat"},
            {"from": "publish_wechat", "to": "export_wechat"},
        ],
        "drop_edge": {"from": "approve_wechat", "to": "export_wechat"},
    }


def _register_builtin_channels() -> None:
    register(ChannelMethods(
        key="douyin",
        metadata_echo=True,
        legacy_workflow=True,
        workflow_label="抖音口播",
        workflow_formats=("txt", "srt"),
        mock_shape="spoken_script",
        mock_unfact="scenes",
        length_guidance={"seconds": "45-90", "chars": "300-600"},
    ))
    register(ChannelMethods(
        key="xiaohongshu",
        renderer_key="renderer.xhs.cards",
        metadata_echo=True,
        legacy_workflow=True,
        workflow_label="小红书图文",
        workflow_formats=("md", "txt"),
        mock_shape="image_note",
        mock_unfact="body",
        length_guidance={"body_chars": "300-800"},
    ))
    register(ChannelMethods(
        key="wechat",
        renderer_key="renderer.wechat.article",
        require_cover=True,
        legacy_media={"cover": "required"},
        auto_draft_publisher=("publisher.wechat.wewrite", "1"),
        official_publisher=("publisher.wechat.official", "1"),
        official_scope=_wechat_official_scope,
        prepare_variant_auto_draft=_prepare_wechat_auto_draft,
        metadata_echo=True,
        m1_handoff=True,
        m1_content_form="wechat_article",
        text_cover_form="article",
        legacy_workflow=True,
        workflow_label="公众号文章",
        workflow_formats=("md", "html"),
        legacy_publish_extension=_wechat_publish_extension,
        template_params=({"key": "publish_wechat", "label": "显式启用遗留公众号草稿能力", "type": "boolean", "default": False},),
        mock_shape="article",
        mock_unfact="sections",
        length_guidance={"body_chars": "1500-3000"},
        m1_package=_wechat_m1_package,
    ))
    register(ChannelMethods(
        key="x",
        renderer_key="renderer.x.thread",
        renderer_forms=frozenset({None, "thread"}),
        metadata_echo=True,
    ))
    register(ChannelMethods(
        key="x_thread",
        selectable=False,
        retired_message="渠道 x_thread 已下线，请使用渠道 x 的 single 或 thread",
        renderer_key="renderer.x.thread",
        prompt_channel="wechat",
        numbered_thread_body=True,
        require_thread_posts=True,
    ))


_register_builtin_channels()
