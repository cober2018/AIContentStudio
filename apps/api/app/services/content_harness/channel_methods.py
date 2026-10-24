"""渠道方法插件。

主流程只按渠道键取出这里注册的方法。拿掉一个渠道，是取消它的注册，
而不是到生成、渲染、交付或审批主函数里删一段条件。

插拔状态写在系统设置里，每次取方法都读这份状态。拔出后该方法不再参与，
插上后同一进程立即恢复，不用改主程序，也不用重启。

没有注册方法的渠道走通用行为：通用 Markdown、复制包，不提供远端草稿。
`x_thread` 仍注册，但不可选；它只给历史稿件保留读取方法。插上也不会把它变回可选渠道。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class ChannelMethods:
    key: str
    selectable: bool = True
    retired_message: str | None = None
    renderer_key: str | None = None
    renderer_forms: frozenset[str | None] | None = None
    require_cover: bool = False
    auto_draft_publisher: tuple[str, str] | None = None
    official_publisher: tuple[str, str] | None = None
    official_scope: Callable[[dict], bool] | None = None
    prepare_variant_auto_draft: Callable[[dict], dict] | None = None
    metadata_echo: bool = False
    text_cover_form: str | None = None
    workflow_label: str | None = None
    mock_shape: str | None = None
    mock_unfact: str | None = None
    length_guidance: dict | None = None


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


def echoes_metadata_channel(channel: object) -> bool:
    if not isinstance(channel, str):
        return False
    plugin = get(channel)
    return bool(plugin and plugin.metadata_echo)


def allows_text_cover(channel: str, content_form: str) -> bool:
    plugin = get(channel)
    return bool(plugin and plugin.text_cover_form == content_form)


def matches_official_scope(scope: dict) -> bool:
    if not isinstance(scope, dict):
        return False
    channel = scope.get("channel")
    plugin = get(channel) if isinstance(channel, str) else None
    return bool(plugin and plugin.official_scope and plugin.official_scope(scope))


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


def _method_labels(plugin: ChannelMethods) -> list[str]:
    labels: list[str] = []
    if plugin.renderer_key:
        labels.append("专用渲染")
    if plugin.require_cover:
        labels.append("封面检查")
    if plugin.auto_draft_publisher or plugin.official_publisher:
        labels.append("草稿方法")
    if plugin.metadata_echo:
        labels.append("交付回执标注")
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


def _register_builtin_channels() -> None:
    register(ChannelMethods(
        key="douyin",
        metadata_echo=True,
        workflow_label="抖音口播",
        mock_shape="spoken_script",
        mock_unfact="scenes",
        length_guidance={"seconds": "45-90", "chars": "300-600"},
    ))
    register(ChannelMethods(
        key="xiaohongshu",
        renderer_key="renderer.xhs.cards",
        metadata_echo=True,
        workflow_label="小红书图文",
        mock_shape="image_note",
        mock_unfact="body",
        length_guidance={"body_chars": "300-800"},
    ))
    register(ChannelMethods(
        key="wechat",
        renderer_key="renderer.wechat.article",
        require_cover=True,
        auto_draft_publisher=("publisher.wechat.wewrite", "1"),
        official_publisher=("publisher.wechat.official", "1"),
        official_scope=_wechat_official_scope,
        prepare_variant_auto_draft=_prepare_wechat_auto_draft,
        metadata_echo=True,
        text_cover_form="article",
        workflow_label="公众号文章",
        mock_shape="article",
        mock_unfact="sections",
        length_guidance={"body_chars": "1500-3000"},
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
    ))


_register_builtin_channels()
