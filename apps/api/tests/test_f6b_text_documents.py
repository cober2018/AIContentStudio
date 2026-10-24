"""Portable text documents: pure contracts, not editor-engine JSON."""

import hashlib
import importlib
import importlib.util
import json
from copy import deepcopy

import pytest


def service():
    assert importlib.util.find_spec("app.services.text_documents"), "F6B document service missing"
    return importlib.import_module("app.services.text_documents")


def run(text, marks=None):
    return {"text": text, "marks": marks or []}


def doc(blocks=None, citations=None):
    return {"schema": "studio.text.document.v1", "blocks": blocks or [], "citations": citations or []}


def paragraph(text="中文😀正文", block_id="p1"):
    return {"id": block_id, "type": "paragraph", "content": [run(text)]}


def test_legacy_converter_is_deterministic_and_markdown_is_authoritative():
    original = {"title": "旧稿", "markdown": "## 标题\n\n正文😀 **强调**\n\n- 第一条\n- 第二条", "document": {"type": "doc", "content": [{"text": "矛盾正文"}]}}
    before = deepcopy(original)
    converted = service().convert_legacy_text(original)
    assert original == before
    assert converted == service().convert_legacy_text(original)
    assert converted["payload"]["document"]["schema"] == "studio.text.document.v1"
    assert [b["type"] for b in converted["payload"]["document"]["blocks"]] == ["heading", "paragraph", "bullet_list"]
    assert "矛盾正文" not in service().plain_text(converted["payload"]["document"])
    assert converted["warnings"] == [{"code": "legacy_document_not_equivalent"}]
    assert "markdown" not in converted["payload"]
    assert converted["payload"]["document"]["blocks"][0]["level"] == 2


def test_converter_normalizes_title_repeat_empty_sections_and_heading_jumps():
    title = "审查者的认知界限"
    markdown = f"# {title}\n\n### 先看粒度\n\n小步提交更容易审。\n\n### 再看上下文\n\n上下文再大也不能代替人看过的差异。"
    converted = service().convert_legacy_text({"title": title, "markdown": markdown})
    blocks = converted["payload"]["document"]["blocks"]
    assert [block["type"] for block in blocks] == ["heading", "paragraph", "heading", "paragraph"]
    assert [block["level"] for block in blocks if block["type"] == "heading"] == [2, 2]
    assert title not in service().plain_text(converted["payload"]["document"])
    assert blocks[-1]["type"] != "heading"
    assert all(blocks[index + 1]["type"] != "heading" for index, block in enumerate(blocks[:-1]) if block["type"] == "heading")
    jumped = service().convert_legacy_text({"title": "别的标题", "markdown": "# 总览\n\n正文\n\n#### 细节\n\n继续"})
    assert [block["level"] for block in jumped["payload"]["document"]["blocks"] if block["type"] == "heading"] == [2, 3]
    assert service().plain_text(jumped["payload"]["document"]) == "总览\n正文\n细节\n继续"
    trailing = service().convert_legacy_text({"title": "别的标题", "markdown": "正文\n\n## 没有下文"})
    assert [block["type"] for block in trailing["payload"]["document"]["blocks"]] == ["paragraph"]
    listed = service().convert_legacy_text({"title": "小步修改", "markdown": "# 标题\n\n- 先看**差异**，再看 [依据](https://example.com/a)。\n"})
    listed_blocks = listed["payload"]["document"]["blocks"]
    assert listed_blocks[0]["type"] == "heading" and listed_blocks[0]["level"] == 2
    assert "差异" in service().plain_text(listed["payload"]["document"])


@pytest.mark.parametrize("markdown", ["<script>不执行</script>", "| a | b |\n| -- | -- |", "##### 五级标题", "  - 嵌套列表", "![远程](https://example.com/x.png)", "```bad language\n原文\n```", "```python\n未闭合"])
def test_converter_preserves_unsupported_source_as_literal_with_warning(markdown):
    converted = service().convert_legacy_text({"markdown": markdown})
    assert service().plain_text(converted["payload"]["document"]) == markdown
    assert converted["warnings"]


def test_converter_maps_only_exact_media_hints_and_unique_claim_text():
    assets = [{"material_revision_id": 7, "content_hash": "a" * 64, "role": "inline", "sort_order": 0}]
    evidence = [{"fact_pack_item_id": 8, "snapshot_checksum": "s" * 64, "locator": {"text": "中文😀事实"}, "role": "claim"}]
    source = {"markdown": "中文😀事实", "document": {"schema_version": 1, "blocks": [{"type": "paragraph", "text": "中文😀事实"}, {"type": "image", "material_revision_id": 7, "alt": "配图"}]}}
    converted = service().convert_legacy_text(source, asset_refs=assets, evidence_refs=evidence)
    assert converted["warnings"] == []
    assert converted["payload"]["document"]["blocks"][1]["material_revision_id"] == 7
    use = converted["payload"]["document"]["citations"][0]
    assert (use["start"], use["end"]) == (0, len("中文😀事实"))
    assert service().validate_references(converted["payload"], converted["asset_refs"], converted["evidence_refs"]) == {"unused_asset_ids": []}
    ambiguous = service().convert_legacy_text({"markdown": "中文😀事实\n\n中文😀事实"}, evidence_refs=evidence)
    assert ambiguous["evidence_refs"] == []
    assert ambiguous["warnings"] == [{"code": "unmapped_evidence_locator", "reference_index": 0}]


def test_converter_does_not_trust_unmatched_media_or_document_without_body():
    source = {"markdown": "正文", "document": {"schema_version": 1, "blocks": [{"type": "paragraph", "text": "正文"}, {"type": "image", "material_revision_id": 999}]}}
    converted = service().convert_legacy_text(source)
    assert converted["warnings"] == [{"code": "unmapped_media_hint", "hint_index": 1}]
    assert [b["type"] for b in converted["payload"]["document"]["blocks"]] == ["paragraph"]
    with pytest.raises(service().TextDocumentError, match="legacy_body_required"):
        service().convert_legacy_text({"document": source["document"]})


def test_converter_overlapping_claims_are_ambiguous_and_unicode_separators_survive():
    evidence = [{"fact_pack_item_id": 8, "snapshot_checksum": "s" * 64, "locator": {"text": "aa"}}]
    result = service().convert_legacy_text({"markdown": "aaa"}, evidence_refs=evidence)
    assert result["evidence_refs"] == []
    text = "第一行\u2028第二行\u2029第三行"
    assert service().plain_text(service().convert_legacy_text({"markdown": text})["payload"]["document"]) == text


def test_converter_flat_list_continuation_keeps_unknown_indent_literal():
    result = service().convert_legacy_text({"markdown": "- 第一条\n  延续正文\n- 第二条"})
    assert "延续正文" in service().plain_text(result["payload"]["document"])
    assert result["warnings"]


@pytest.mark.parametrize("text", ["abc ** def ** ghi", "\\*字面星号\\*", "***嵌套强调***", "`双``反引号`", "a*（文字）*b", "[**重要**](https://example.com)", "[a\\*b](https://example.com)"])
def test_converter_ambiguous_inline_syntax_is_literal_not_reinterpreted(text):
    converted = service().convert_legacy_text({"markdown": text})
    assert service().plain_text(converted["payload"]["document"]) == text
    assert converted["warnings"] == [{"code": "unsupported_inline_preserved"}]


def test_converter_supported_code_span_uses_commonmark_space_rule():
    converted = service().convert_legacy_text({"markdown": "` a ` 与 `   `"})
    assert service().plain_text(converted["payload"]["document"]) == "a 与    "
    assert converted["warnings"] == []


def test_converter_layout_equivalence_cannot_strip_authoritative_indent():
    body = "    缩进代码"
    result = service().convert_legacy_text({"markdown": body, "document": {"schema_version": 1, "blocks": [{"type": "paragraph", "text": body.strip()}]}})
    assert service().plain_text(result["payload"]["document"]) == body
    assert {w["code"] for w in result["warnings"]} == {"legacy_document_not_equivalent", "unsupported_block_preserved"}


@pytest.mark.parametrize("body", ["## 标题 ##", "> 引用\n延续", "a &amp; b", "a  \nb", "标题\n---", "标题\n===", "+ 第一项\n+ 第二项"])
def test_converter_nontrivial_markdown_layout_always_reports_loss(body):
    result = service().convert_legacy_text({"markdown": body})
    assert result["warnings"]


def test_converter_repeated_exact_legacy_media_is_not_a_second_asset():
    ref = {"material_revision_id": 7, "content_hash": "a" * 64, "role": "cover", "sort_order": 0}
    source = {"markdown": "正文", "document": {"schema_version": 1, "blocks": [{"type": "image", "material_revision_id": 7}, {"type": "paragraph", "text": "正文"}, {"type": "image", "material_revision_id": 7}]}}
    result = service().convert_legacy_text(source, asset_refs=[ref, {**ref, "role": "inline", "sort_order": 1}])
    assert result["asset_refs"] == [ref]
    assert len([b for b in result["payload"]["document"]["blocks"] if b["type"] == "image"]) == 2
    assert result["warnings"] == [{"code": "duplicate_legacy_asset_normalized", "material_revision_id": 7}]
    with pytest.raises(service().TextDocumentError, match="conflicting_legacy_asset_hash"):
        service().convert_legacy_text(source, asset_refs=[ref, {**ref, "content_hash": "b" * 64}])


@pytest.mark.parametrize("marker", ["9" * 4301, "1234567890", "٩"], ids=["python-limit", "commonmark-limit", "non-ascii"])
def test_converter_unsupported_numeric_list_marker_is_bounded_literal(marker):
    body = marker + ". 项目"
    result = service().convert_legacy_text({"markdown": body})
    assert service().plain_text(result["payload"]["document"]) == body
    assert result["warnings"] == [{"code": "unsupported_block_preserved"}]


@pytest.mark.parametrize("block", [
    paragraph(),
    {"id": "h1", "type": "heading", "level": 2, "content": [run("标题")]},
    {"id": "q1", "type": "quote", "content": [run("引用")], "attribution": "作者"},
    {"id": "l1", "type": "bullet_list", "items": [{"id": "i1", "content": [run("一条")]}]},
    {"id": "l2", "type": "ordered_list", "items": [{"id": "i2", "content": [run("一条")]}]},
    {"id": "c1", "type": "callout", "tone": "note", "content": [run("注意")]},
    {"id": "code", "type": "code", "language": "python", "code": "print(1)"},
    {"id": "img", "type": "image", "material_revision_id": 5, "alt_text": "图片", "caption": "说明"},
    {"id": "chart", "type": "chart", "material_revision_id": 6, "alt_text": "图表"},
    {"id": "hr", "type": "divider"},
])
def test_each_supported_block_round_trips_without_mutation(block):
    original = doc([block])
    before = deepcopy(original)
    result = service().canonical_document(original)
    assert original == before
    assert result["blocks"][0]["id"] == block["id"]
    assert service().canonical_document(result) == result


@pytest.mark.parametrize("invalid", [
    {"schema": "prosemirror", "blocks": [], "citations": []},
    {**doc(), "file_path": "/private/content"},
    doc([paragraph(), paragraph()]),
    doc([{**paragraph(), "id": ""}]),
    doc([{**paragraph(), "type": "unsupported"}]),
    doc([{**paragraph(), "attrs": {}}]),
    doc([{**paragraph(), "content": [run("x", [{"type": "strike"}])]}]),
    doc([{**paragraph(), "content": [run("x", [{"type": "link", "href": "javascript:alert(1)"}])]}]),
    doc([{**paragraph(), "content": [run("\ud800")]}]),
    doc([{**paragraph(), "content": [run("x" * 20001)]}]),
    doc([{**paragraph(), "id": "b" * 151}]),
    doc([{"id": "h", "type": "heading", "level": True, "content": []}]),
    doc([{"id": "h", "type": "heading", "level": 5, "content": []}]),
    doc([{"id": "l", "type": "bullet_list", "items": []}]),
    doc([{"id": "l", "type": "bullet_list", "items": [{"id": "i", "content": []}, {"id": "i", "content": []}]}]),
    doc([{"id": "i", "type": "image", "material_revision_id": True}]),
    doc([{"id": "c", "type": "callout", "tone": "unknown", "content": []}]),
    doc([paragraph("x", str(i)) for i in range(1001)]),
])
def test_invalid_documents_fail_closed(invalid):
    module = service()
    with pytest.raises(module.TextDocumentError):
        module.canonical_document(invalid)


def test_mark_normalization_and_hash_are_deterministic():
    module = service()
    a = doc([{**paragraph(), "content": [run("text", [{"type": "italic"}, {"type": "bold"}])]}])
    b = doc([{**paragraph(), "content": [run("text", [{"type": "bold"}, {"type": "italic"}])]}])
    assert module.document_hash(a) == module.document_hash(b)
    reordered = json.loads(json.dumps(a, sort_keys=True))
    assert module.document_hash(a) == module.document_hash(reordered)
    assert module.canonical_document(a)["blocks"][0]["content"][0]["marks"] == [{"type": "bold"}, {"type": "italic"}]


def citation(block="p1", start=2, end=3, text="😀", citation_id="c1", item=None):
    return {"id": citation_id, "block_id": block, "start": start, "end": end,
            "fact_pack_item_id": 8, "selected_text_hash": hashlib.sha256(text.encode()).hexdigest(),
            **({"list_item_id": item} if item else {})}


def test_unicode_list_and_repeated_item_locators_are_separate_uses():
    module = service()
    source = doc([paragraph(), {"id": "list", "type": "bullet_list", "items": [{"id": "i", "content": [run("😀证据")]}]}],
                 [citation(), citation("list", 0, 1, "😀", "c2", "i")])
    result = module.canonical_document(source)
    assert len(result["citations"]) == 2
    assert module.locator_text(result, {"block_id": "p1", "start": 2, "end": 3}) == "😀"
    assert module.locator_text(result, {"block_id": "list", "list_item_id": "i", "start": 0, "end": 1}) == "😀"
    assert module.plain_text(result) == "中文😀正文\n😀证据"


@pytest.mark.parametrize("change", [
    {"block_id": "missing"}, {"start": -1}, {"end": 99}, {"start": True},
    {"end": 2}, {"selected_text_hash": "0" * 64}, {"fact_pack_item_id": True},
    {"list_item_id": "not-a-list"}, {"id": ""},
])
def test_citation_validation_includes_selected_text_not_only_range(change):
    module = service()
    with pytest.raises(module.TextDocumentError):
        module.canonical_document(doc([paragraph()], [{**citation(), **change}]))


def test_duplicate_citation_and_wrong_list_item_fail():
    module = service()
    with pytest.raises(module.TextDocumentError):
        module.canonical_document(doc([paragraph()], [citation(), citation()]))
    with pytest.raises(module.TextDocumentError):
        module.canonical_document(doc([{"id": "list", "type": "bullet_list", "items": [{"id": "i", "content": [run("😀")]}]}], [citation("list", 0, 1, item="wrong")]))


def test_single_editable_truth_rejects_markdown_editor_json_and_unknown_envelope():
    module = service()
    payload = {"title": "标题", "document": doc([paragraph()])}
    assert module.canonical_payload(payload) == payload
    for field in ("markdown", "structured", "prosemirror", "file_path"):
        with pytest.raises(module.TextDocumentError):
            module.canonical_payload({**payload, field: "second truth"})


def test_reference_uses_match_citations_and_detect_unused_assets():
    module = service()
    payload = {"title": "", "document": doc([paragraph(), {"id": "img", "type": "image", "material_revision_id": 5}], [citation()])}
    locator = {"citation_id": "c1", **{k: v for k, v in citation().items() if k not in {"id", "fact_pack_item_id"}}}
    assets = [{"material_revision_id": 5, "content_hash": "a" * 64}, {"material_revision_id": 6, "content_hash": "b" * 64}]
    evidence = [{"fact_pack_item_id": 8, "snapshot_checksum": "c" * 64, "locator": locator}]
    assert module.validate_references(payload, assets, evidence) == {"unused_asset_ids": [6]}
    with pytest.raises(module.TextDocumentError):
        module.validate_references(payload, [], evidence)
    with pytest.raises(module.TextDocumentError):
        module.validate_references(payload, assets, [{**evidence[0], "locator": {}}])
    with pytest.raises(module.TextDocumentError):
        module.validate_references(payload, assets, evidence + evidence)


def test_renderer_supports_all_blocks_safe_markdown_and_exact_media_paths():
    module = service()
    source = doc([
        {"id": "h", "type": "heading", "level": 2, "content": [run("标题")]},
        paragraph("<script> *文字*"),
        {"id": "q", "type": "quote", "content": [run("引用")], "attribution": "作者"},
        {"id": "l", "type": "bullet_list", "items": [{"id": "i", "content": [run("条目")]}]},
        {"id": "o", "type": "ordered_list", "items": [{"id": "i", "content": [run("顺序")]}]},
        {"id": "c", "type": "callout", "tone": "warning", "content": [run("注意")]},
        {"id": "code", "type": "code", "language": "py", "code": "```\nprint(1)"},
        {"id": "img", "type": "image", "material_revision_id": 5, "alt_text": "图]片"},
        {"id": "chart", "type": "chart", "material_revision_id": 6, "caption": "图表"},
        {"id": "hr", "type": "divider"},
    ])
    media = {5: "media/00-5.png", 6: "media/01-6.png"}
    rendered = module.render_markdown(source, media_paths=media)
    assert rendered.startswith("## 标题\n\n")
    assert "<script>" not in rendered and "\\*文字\\*" in rendered
    assert "- 条目" in rendered and "1. 顺序" in rendered
    assert "````py\n```\nprint(1)\n````" in rendered
    assert "media/00-5.png" in rendered and "media/01-6.png" in rendered
    assert module.render_markdown(source, media_paths=media) == rendered
    with pytest.raises(module.TextDocumentError):
        module.render_markdown(source)
    with pytest.raises(module.TextDocumentError):
        module.render_markdown(source, media_paths={5: "/private/file", 6: media[6]})


def test_renderer_marks_escape_code_and_citation_labels_without_evidence_text():
    module = service()
    source = doc([paragraph(), {"id": "m", "type": "paragraph", "content": [
        run("strong", [{"type": "bold"}]), run("x`y", [{"type": "code"}]),
        run("link", [{"type": "link", "href": "https://example.com/a(b)"}]),
    ]}], [citation()])
    output = module.render_markdown(source)
    assert "**strong**" in output and "``x`y``" in output
    assert "https://example.com/a%28b%29" in output
    assert "\\[1\\]" in output
    assert "FactPack" not in output and "selected_text_hash" not in output


@pytest.mark.parametrize("modality,schema", [("text", "text.master.v1"), ("text", "text.master.v2"), ("graphic", "graphic.master.v1"), ("video", "video.master.v1")])
def test_adapter_registry_dispatches_exact_persisted_schema(modality, schema):
    from app.services import production_modalities as adapters

    assert "payload_schema" in __import__("inspect").signature(adapters.adapter_for).parameters
    assert adapters.adapter_for(modality, schema).payload_schema == schema
    assert schema in adapters.supported_payload_schemas(modality)


def test_v2_adapter_default_and_renderer_are_real_without_draft(db_session):
    from app.models import ContentMasterRevision
    from app.services import production_modalities as adapters

    assert hasattr(adapters, "default_payload_schema"), "exact-schema registry missing"
    assert adapters.default_payload_schema("text") == "text.master.v2"
    adapter = adapters.adapter_for("text", "text.master.v2")
    payload = {"title": "标题", "document": doc([paragraph()])}
    master = ContentMasterRevision(id=1, project_id=1, content_unit_id=1, modality="text", payload_schema="text.master.v2", payload_json=payload, context_hash="a" * 64)
    assert adapter.validate_payload(payload) == []
    rendered = adapter.build_render_snapshot(db_session, master)
    assert rendered["status"] == "ready"
    assert rendered["body_markdown"] == "中文😀正文"
    assert rendered["content_hash"] == hashlib.sha256(rendered["body_markdown"].encode()).hexdigest()
    assert adapter.build_render_snapshot(db_session, master) == rendered
    master.payload_json = {"title": "", "document": doc()}
    assert adapter.build_render_snapshot(db_session, master)["status"] == "incomplete"


@pytest.mark.parametrize("modality,schema", [("text", "text.master.v3"), ("text", "graphic.master.v1"), ("other", "text.master.v2")])
def test_unknown_adapter_schema_is_rejected(modality, schema):
    from fastapi import HTTPException

    from app.services import production_modalities as adapters

    assert "payload_schema" in __import__("inspect").signature(adapters.adapter_for).parameters
    with pytest.raises(HTTPException) as error:
        adapters.adapter_for(modality, schema)
    assert error.value.status_code == 422


def test_v1_adapter_keeps_its_original_markdown_hash(db_session):
    from app.models import ContentMasterRevision
    from app.services import production_modalities as adapters

    assert "payload_schema" in __import__("inspect").signature(adapters.adapter_for).parameters
    old = ContentMasterRevision(id=1, project_id=1, content_unit_id=1, modality="text", payload_schema="text.master.v1", payload_json={"markdown": "**历史原文**"}, context_hash="a" * 64)
    adapter = adapters.adapter_for("text", old.payload_schema)
    assert adapter.required_check_kinds == ("master_schema", "evidence", "rights", "render")
    assert adapter.build_render_snapshot(db_session, old)["content_hash"] == hashlib.sha256("**历史原文**".encode()).hexdigest()


def test_renderer_preserves_entity_text_and_link_destination():
    module = service()
    source = doc([paragraph("&copy;"), {"id": "link", "type": "paragraph", "content": [run("go", [{"type": "link", "href": "https://example.com/?q=&copy;"}])]}])
    rendered = module.render_markdown(source)
    assert "\\&copy;" in rendered
    assert "q=&amp;copy;" in rendered


def test_renderer_emphasis_keeps_whitespace_outside_delimiters():
    module = service()
    source = doc([{"id": "p1", "type": "paragraph", "content": [run(" a b ", [{"type": "bold"}])]}], [citation(text=" a ", start=0, end=3)])
    assert module.render_markdown(source) == " **a** \\[1\\]**b** "


def test_inline_code_newline_is_not_silently_collapsed():
    module = service()
    with pytest.raises(module.TextDocumentError):
        module.canonical_document(doc([{"id": "p1", "type": "paragraph", "content": [run("a\nb", [{"type": "code"}])]}]))


@pytest.mark.parametrize("field,value", [("start", 2.0), ("end", 3.0)])
def test_evidence_locator_requires_exact_integer_types(field, value):
    module = service()
    c = citation()
    locator = {"citation_id": c["id"], **{key: c[key] for key in ("block_id", "start", "end", "selected_text_hash")}}
    locator[field] = value
    with pytest.raises(module.TextDocumentError):
        module.validate_references({"title": "", "document": doc([paragraph()], [c])}, [], [{"fact_pack_item_id": c["fact_pack_item_id"], "snapshot_checksum": "a" * 64, "locator": locator}])


def test_text_map_has_exact_codepoint_ranges_and_list_item_paths():
    module = service()
    assert hasattr(module, "text_map"), "canonical text map missing"
    source = doc([paragraph("a😀"), {"id": "list", "type": "bullet_list", "items": [{"id": "item", "content": [run("中文")]}]}])
    mapped = module.text_map(source)
    assert mapped["text"] == "a😀\n中文"
    assert [(part["block_id"], part.get("list_item_id"), part["start"], part["end"]) for part in mapped["segments"]] == [("p1", None, 0, 2), ("list", "item", 3, 5)]
    for part in mapped["segments"]:
        assert mapped["text"][part["start"]:part["end"]] == part["text"]


def test_citation_label_cannot_become_a_link_with_following_parentheses():
    source = doc([paragraph("A(来源)")], [citation(start=0, end=1, text="A")])
    assert service().render_markdown(source) == "A\\[1\\](来源)"


def test_inline_code_only_spaces_does_not_add_padding():
    source = doc([{"id": "p1", "type": "paragraph", "content": [run("  ", [{"type": "code"}])]}])
    assert service().render_markdown(source) == "`  `"


def test_emphasis_punctuation_and_adjacent_mark_nesting_are_lossless():
    source = doc([{"id": "p1", "type": "paragraph", "content": [run("这是"), run("重点，", [{"type": "bold"}]), run("请注意")]}])
    assert service().render_markdown(source) == "这是<strong>重点，</strong>请注意"
    source["blocks"][0]["content"] = [run("a", [{"type": "bold"}]), run("b", [{"type": "bold"}, {"type": "italic"}])]
    assert service().render_markdown(source) == "<strong>a</strong><em><strong>b</strong></em>"


def test_generated_emphasis_tags_do_not_allow_user_html():
    source = doc([{"id": "p1", "type": "paragraph", "content": [run("<script>，", [{"type": "bold"}])]}])
    output = service().render_markdown(source)
    assert output == "<strong>\\<script\\>，</strong>"
    assert "<script>" not in output
