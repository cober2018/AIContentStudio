"""渠道方法是插件：主流程按注册表调用，摘掉插件后该渠道不再有专用行为。"""

import inspect

import pytest
from fastapi import HTTPException

from app.services.content_harness import channel_methods
from app.services.content_harness.renderers import resolve_renderer_key
from app.services.delivery import resolve_publisher


def test_main_dispatch_does_not_name_channels():
    for function in (
        resolve_renderer_key,
        resolve_publisher,
    ):
        source = inspect.getsource(function)
        for name in ("wechat", "xiaohongshu", "douyin", "x_thread"):
            assert name not in source, f"{function.__name__} still names {name}"


def test_registered_methods_keep_current_behavior():
    assert resolve_renderer_key("wechat", "article") == "renderer.wechat.article"
    assert resolve_renderer_key("x", "thread") == "renderer.x.thread"
    assert resolve_renderer_key("x", "single") == "renderer.generic.markdown"
    assert resolve_renderer_key("x_thread", None) == "renderer.x.thread"
    assert resolve_renderer_key("xiaohongshu", "image_note") == "renderer.xhs.cards"
    assert resolve_renderer_key("zhihu", "article") == "renderer.generic.markdown"
    assert channel_methods.retired_message("x_thread") == "渠道 x_thread 已下线，请使用渠道 x 的 single 或 thread"
    assert channel_methods.get("x_thread").selectable is False
    publisher, key, version = resolve_publisher("wechat", "article", "auto_draft")
    assert (key, version) == ("publisher.wechat.wewrite", "1")
    assert publisher is not None
    with pytest.raises(HTTPException) as error:
        resolve_publisher("xiaohongshu", "image_note", "auto_draft")
    assert error.value.status_code == 422


def test_removing_the_plugin_removes_the_channel_method():
    saved = dict(channel_methods._PLUGINS)
    try:
        del channel_methods._PLUGINS["wechat"]
        assert resolve_renderer_key("wechat", "article") == "renderer.generic.markdown"
        with pytest.raises(HTTPException):
            resolve_publisher("wechat", "article", "auto_draft")
    finally:
        channel_methods._PLUGINS.clear()
        channel_methods._PLUGINS.update(saved)


def test_unplug_hides_the_channel_and_hot_plug_restores_it(client, db_session):
    from app import runtime_config
    from app.models import User
    from app.services.content_harness import channel_registry
    from app.services.content_harness.channel_registry import ChannelRegistryError

    db_session.add(User(email="admin@studio.local", name="Admin", role="admin"))
    db_session.add(User(email="editor@studio.local", name="Editor", role="editor"))
    db_session.commit()
    admin = {"X-Studio-User": "admin@studio.local"}
    editor = {"X-Studio-User": "editor@studio.local"}
    saved = runtime_config.get_runtime(runtime_config.KEY_CHANNEL_PLUGINS)
    try:
        listed = client.get("/api/v1/channels/plugins", headers=editor)
        assert listed.status_code == 200
        catalog = {item["key"]: item for item in listed.json()["items"]}
        assert catalog["wechat"]["plugged"] is True
        assert catalog["x_thread"]["selectable"] is False
        assert "wechat" in channel_registry.list_channel_keys(db_session)

        denied = client.post("/api/v1/channels/plugins/wechat/unplug", headers=editor)
        assert denied.status_code == 403
        unknown = client.post("/api/v1/channels/plugins/toutiao/unplug", headers=admin)
        assert unknown.status_code == 404

        unplugged = client.post("/api/v1/channels/plugins/wechat/unplug", headers=admin)
        assert unplugged.status_code == 200
        assert unplugged.json()["plugged"] is False
        channels = {item["channel"] for item in client.get("/api/v1/channels", headers=editor).json()}
        assert "wechat" not in channels
        assert "douyin" in channels and "xiaohongshu" in channels
        missing = client.get("/api/v1/channels/wechat", headers=editor)
        assert missing.status_code == 404
        assert "已拔出" in missing.json()["detail"]
        assert channel_registry.resolve_content_form(db_session, "wechat", "article").content_form == "article"
        with pytest.raises(ChannelRegistryError, match="已拔出"):
            channel_registry.normalize_targets(db_session, channels=["wechat"])
        assert resolve_renderer_key("wechat", "article") == "renderer.generic.markdown"
        with pytest.raises(HTTPException):
            resolve_publisher("wechat", "article", "auto_draft")
        retired = client.get("/api/v1/channels/x_thread", headers=editor)
        assert retired.status_code == 404
        assert "已下线" in retired.json()["detail"]

        restored = client.post("/api/v1/channels/plugins/wechat/plug", headers=admin)
        assert restored.status_code == 200
        assert restored.json()["plugged"] is True
        assert "wechat" in {item["channel"] for item in client.get("/api/v1/channels", headers=editor).json()}
        assert resolve_renderer_key("wechat", "article") == "renderer.wechat.article"

        client.post("/api/v1/channels/plugins/x_thread/unplug", headers=admin)
        assert resolve_renderer_key("x_thread", None) == "renderer.generic.markdown"
        client.post("/api/v1/channels/plugins/x_thread/plug", headers=admin)
        assert resolve_renderer_key("x_thread", None) == "renderer.x.thread"
        assert "x_thread" not in {item["channel"] for item in client.get("/api/v1/channels", headers=editor).json()}
        still_retired = client.get("/api/v1/channels/x_thread", headers=editor)
        assert still_retired.status_code == 404
        assert "已下线" in still_retired.json()["detail"]
    finally:
        if saved is None:
            runtime_config.clear_runtime(runtime_config.KEY_CHANNEL_PLUGINS)
        else:
            runtime_config.set_runtime(runtime_config.KEY_CHANNEL_PLUGINS, saved)
