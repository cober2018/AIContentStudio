"""Renderer Registry（V1 PRD 2.0 / D19）：平台渲染在批准前冻结。"""


from app.services.content_harness.registry import registry
from app.services.content_harness.renderers import (
    GenericMarkdownRenderer,
    WechatArticleRenderer,
    XhsCardsRenderer,
    XThreadRenderer,
    bootstrap_renderers,
    resolve_renderer_key,
)

bootstrap_renderers()


def test_all_builtin_renderers_registered():
    keys = {d.key for d in registry.list("renderer")}
    assert {"renderer.wechat.article", "renderer.x.thread", "renderer.generic.markdown", "renderer.xhs.cards"} <= keys
    # 重复注册防护（幂等 bootstrap 不报错）
    bootstrap_renderers()


def test_renderer_key_mapping():
    assert resolve_renderer_key("wechat", "article") == "renderer.wechat.article"
    assert resolve_renderer_key("x_thread", "thread") == "renderer.x.thread"
    assert resolve_renderer_key("xiaohongshu", "image_note") == "renderer.xhs.cards"
    assert resolve_renderer_key("zhihu", "article") == "renderer.generic.markdown"


def test_wechat_renderer_payload_and_hash():
    result = WechatArticleRenderer().render({"title": "T", "body_markdown": "# T\n\n正文"})
    assert result.payload["html"]  # wechat html 已生成
    assert result.payload["markdown"].startswith("# T")
    assert len(result.content_hash) == 64
    again = WechatArticleRenderer().render({"title": "T", "body_markdown": "# T\n\n正文"})
    assert again.content_hash == result.content_hash  # canonical hash stable


def test_x_thread_renderer_ordered_posts():
    result = XThreadRenderer().render({
        "title": "T",
        "thread_posts": [{"index": 1, "text": "one"}, {"index": 2, "text": "two"}],
    })
    assert result.payload["thread_posts"][1]["text"] == "two"
    assert "1. one" in result.payload["markdown"]
    assert result.warnings == []
    empty = XThreadRenderer().render({"title": "T", "thread_posts": []})
    assert "missing_thread_posts" in empty.warnings


def test_xhs_renderer_orders_media_and_warns_without_media():
    media = [
        {"draft_media_id": 2, "hash": "b", "sort_order": 1, "role": "inline"},
        {"draft_media_id": 1, "hash": "a", "sort_order": 0, "role": "cover"},
    ]
    result = XhsCardsRenderer().render({
        "title": "T", "body_markdown": "正文", "structured": {"cards": [{"text": "卡1"}, {"text": "卡2"}], "tags": ["x"]},
        "media": media,
    })
    assert [m["draft_media_id"] for m in result.payload["media"]] == [1, 2]  # sort_order 排序
    assert result.payload["cards"][0]["text"] == "卡1"
    assert result.warnings == []
    no_media = XhsCardsRenderer().render({"title": "T", "body_markdown": "", "structured": {}, "media": []})
    assert "no_actual_media" in no_media.warnings


def test_generic_renderer():
    result = GenericMarkdownRenderer().render({"title": "T", "body_markdown": "md"})
    assert result.payload == {"title": "T", "markdown": "md"}
    assert len(result.content_hash) == 64
