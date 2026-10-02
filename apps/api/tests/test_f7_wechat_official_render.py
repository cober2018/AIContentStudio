"""Official representation is frozen before approval, never guessed at dispatch."""

from copy import deepcopy

import pytest


@pytest.mark.parametrize("content,allowed", [("a" * 2047, True), ("a" * 2048, False),
                                            ("中" * 682, True), ("中" * 683, False), ("", False)],
                         ids=["2047-ascii", "2048-ascii", "2046-utf8", "2049-utf8", "empty"])
def test_short_draft_actual_body_uses_strict_utf8_bytes(content, allowed):
    from app.services import wechat_official_render as render

    original = content
    if allowed:
        assert render.validate_short_draft_body(content) == len(content.encode("utf-8"))
    else:
        with pytest.raises(ValueError, match="official_experiment_body_limit"):
            render.validate_short_draft_body(content)
    assert content == original


def test_short_draft_preupload_bound_accounts_for_escaped_remote_url():
    from app.services import wechat_official_render as render

    content, assets = _article()
    frozen = render.build_article_render(content, assets, [])
    before = deepcopy(frozen)
    assert render.validate_short_draft_render_bound(frozen) < 2048
    assert frozen == before
    content, assets = _inline_article()
    frozen = render.build_article_render(content, assets, [])
    with pytest.raises(ValueError, match="official_experiment_body_limit"):
        render.validate_short_draft_render_bound(frozen)


def _article():
    content = {"title": "已批准标题", "blocks": [
        {"id": "b1", "order": 0, "kind": "heading", "text": "标题 <script>"},
        {"id": "b2", "order": 1, "kind": "paragraph", "text": "原文 & 数据\n第二行"},
    ], "citations": [], "declarations": [{"id": "d1", "kind": "disclosure", "text": "明确声明"}]}
    assets = [{"material_revision_id": 7, "content_hash_snapshot": "a" * 64, "role": "cover", "slot_key": "cover",
               "sort_order": 0, "placement": {"usage": "cover"}, "rights_snapshot": {"public_use_allowed": True}}]
    return content, assets


def test_official_render_is_deterministic_escaped_and_does_not_mutate_variant():
    from app.services.wechat_official_render import build_article_render, validate_article_render

    content, assets = _article()
    original = deepcopy(content)
    render = build_article_render(content, assets, [])
    assert render["status"] == "local_ready"
    assert render["schema"] == "wechat.official.article.v1"
    assert render["title"] == content["title"]
    assert render["digest"] == "" and render["author"] == ""
    assert "<script>" not in render["html_template"]
    assert "&lt;script&gt;" in render["html_template"] and "原文 &amp; 数据<br>第二行" in render["html_template"]
    assert "明确声明" in render["html_template"]
    assert render["asset_slots"][0]["material_revision_id"] == 7
    assert render["asset_slots"][0]["content_hash"] == "a" * 64
    assert build_article_render({key: content[key] for key in reversed(content)}, assets, []) == render
    assert content == original
    validate_article_render(render, content, assets, [])
    for field in ("title", "html_template", "digest", "render_hash"):
        changed = deepcopy(render)
        changed[field] = "changed"
        with pytest.raises(ValueError, match="official_render_mismatch"):
            validate_article_render(changed, content, assets, [])


def test_official_unavailable_render_preserves_local_article_without_truncating():
    from app.services.wechat_official_render import build_article_render

    content, assets = _article()
    content["title"] = "长" * 33
    render = build_article_render(content, assets, [])
    assert render["status"] == "unavailable"
    assert render["title"] == content["title"]
    assert "title_limit" in render["reasons"]
    render = build_article_render(_article()[0], [], [])
    assert "cover_required" in render["reasons"]


def test_v5_optional_official_render_rejects_tampering_without_upgrading_history():
    from test_f6e_candidate_manifest_v5 import _inputs

    from app.services.candidates_v5 import build_manifest_v5
    from app.services.channel_adapters import TextChannelAdapter
    from app.services.channel_variant_documents import payload_hash
    from app.services.wechat_official_render import build_article_render

    inputs = _inputs()
    content, assets = _article()
    adapter = TextChannelAdapter("wechat", "article")
    inputs["target"].update(channel="wechat", content_form="article", adapter={"key": "wechat.article", "version": "1"})
    inputs["variant"]["payload_schema"] = "wechat.article.v1"
    inputs["content"] = content
    inputs["assets"] = assets
    inputs["variant"]["payload_hash"] = payload_hash("wechat.article.v1", content, asset_refs=assets)
    inputs["declarations"] = content["declarations"]
    inputs["render"] = adapter.package_projection(content, asset_refs=assets)
    from app.services.candidates import candidate_hash

    for check in inputs["checks"]:
        check["adapter_hash"] = candidate_hash(inputs["target"]["adapter"])
        if check["kind"] == "variant_package":
            check["report"]["projection_hash"] = candidate_hash(inputs["render"])
    legacy = build_manifest_v5(inputs)
    assert "official_render" not in legacy
    inputs["official_render"] = build_article_render(content, assets, [])
    frozen = build_manifest_v5(inputs)
    assert frozen["content"] == legacy["content"] and frozen["checks"] == legacy["checks"]
    assert candidate_hash(frozen) != candidate_hash(legacy)
    assert build_manifest_v5({key: value for key, value in frozen.items() if key != "schema_version"}) == frozen
    inputs["official_render"]["html_template"] += "changed"
    with pytest.raises(ValueError, match="official_render_mismatch"):
        build_manifest_v5(inputs)


def _inline_article():
    content, assets = _article()
    content["blocks"].insert(1, {"id": "img1", "order": 1, "kind": "image", "image_ref_key": "img1", "text": "图注 & 原文", "alt_text": "图片 <说明>"})
    content["blocks"][2]["order"] = 2
    assets.append({"material_revision_id": 8, "content_hash_snapshot": "b" * 64, "role": "inline_image", "slot_key": "img1",
                   "sort_order": 1, "placement": {"usage": "inline", "block_id": "img1"}})
    return content, assets


def test_inline_render_freezes_exact_block_order_and_resource_placeholder():
    from app.services.wechat_official_render import build_article_render, validate_article_render

    content, assets = _inline_article()
    original = deepcopy(content)
    render = build_article_render(content, assets, [])
    assert render["status"] == "local_ready"
    assert render["asset_slots"][1] == {"slot_key": "img1", "usage": "inline", "block_id": "img1", "material_revision_id": 8, "content_hash": "b" * 64}
    assert '<img src="aics-resource:img1" alt="图片 &lt;说明&gt;">' in render["html_template"]
    assert render["html_template"].index('data-block-id="b1"') < render["html_template"].index('data-block-id="img1"') < render["html_template"].index('data-block-id="b2"')
    assert "图注 &amp; 原文" in render["html_template"] and content == original
    validate_article_render(render, content, assets, [])
    metadata = {7: {"filename": "原始封面.png", "mime_type": "image/png"},
                8: {"filename": "原始正文图.png", "mime_type": "image/png"}}
    current = build_article_render(content, assets, [], asset_metadata=metadata)
    assert current["renderer_version"] == "2" and current["status"] == "local_ready"
    assert current["asset_slots"][1]["filename"] == "原始正文图.png"
    assert current["render_hash"] != render["render_hash"]
    validate_article_render(current, content, assets, [])
    assert build_article_render(content, assets, [], asset_metadata={})["status"] == "unavailable"
    for invalid in ('bad".png', "../cover.png", "bad\r\nheader.png", "bad\\path.png", "x" * 256):
        changed = {**metadata, 7: {"filename": invalid, "mime_type": "image/png"}}
        assert build_article_render(content, assets, [], asset_metadata=changed)["status"] == "unavailable"


@pytest.mark.parametrize("mutation", ["missing", "orphan", "duplicate", "placement", "order", "role", "external"])
def test_inline_contract_rejects_unprovable_mapping(mutation):
    from app.services.channel_variant_documents import VariantDocumentError, canonical_payload

    content, assets = _inline_article()
    if mutation == "missing":
        assets.pop()
    elif mutation == "orphan":
        content["blocks"].pop(1)
        content["blocks"][1]["order"] = 1
    elif mutation == "duplicate":
        duplicate = deepcopy(content["blocks"][1])
        duplicate.update(id="img2", order=3)
        content["blocks"].append(duplicate)
    elif mutation == "placement":
        assets[1]["placement"]["block_id"] = "other"
    elif mutation == "order":
        assets[1]["sort_order"] = 2
    elif mutation == "role":
        assets[1]["role"] = "cover"
    else:
        content["blocks"][1]["image_ref_key"] = "https://external.invalid/img"
    with pytest.raises(VariantDocumentError):
        canonical_payload("wechat.article.v1", content, asset_refs=assets)


def test_text_adapter_maps_only_proven_source_image_blocks_and_exact_refs():
    from app.services.channel_adapters import AdapterUnavailable, TextChannelAdapter

    content, assets = _inline_article()
    source = {"title": content["title"], "document": {"schema": "studio.text.document.v1", "citations": [], "blocks": [
        {"id": "b1", "type": "paragraph", "content": [{"text": "前文", "marks": []}]},
        {"id": "img1", "type": "image", "material_revision_id": 8, "caption": "图注 & 原文", "alt_text": "图片 <说明>"},
        {"id": "b2", "type": "paragraph", "content": [{"text": "后文", "marks": []}]},
    ]}}
    adapter = TextChannelAdapter("wechat", "article")
    mapped = adapter.adapt(source, asset_refs=assets, evidence_refs=[])
    assert mapped["blocks"][1] == content["blocks"][1]
    assert [block["id"] for block in mapped["blocks"]] == ["b1", "img1", "b2"]
    assert adapter.package_projection(mapped, asset_refs=assets)["text"] == content["title"] + "\n\n前文\n\n图注 & 原文\n\n后文"
    bad = deepcopy(assets)
    bad[1]["material_revision_id"] = 9
    with pytest.raises(AdapterUnavailable):
        adapter.adapt(source, asset_refs=bad, evidence_refs=[])
    with pytest.raises(AdapterUnavailable):
        TextChannelAdapter("x", "single").adapt(source, asset_refs=assets, evidence_refs=[])


def test_inline_only_preview_uses_contiguous_asset_order_and_missing_cover_remains_unavailable():
    from app.services.wechat_official_render import build_article_render

    content, assets = _inline_article()
    assets = assets[1:]
    assets[0]["sort_order"] = 0
    render = build_article_render(content, assets, [])
    assert render["reasons"] == ["cover_required"]
    assert render["status"] == "unavailable"
    assert render["asset_slots"][0]["usage"] == "inline"
