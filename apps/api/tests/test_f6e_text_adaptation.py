"""Deterministic Text v2 adaptation is lossless for its supported subset."""

import hashlib

import pytest

from app.services.channel_adapters import AdapterUnavailable, TextChannelAdapter


def _text_payload(*paragraphs: str) -> dict:
    return {
        "title": "源文章",
        "document": {
            "schema": "studio.text.document.v1",
            "blocks": [{"id": f"b{index}", "type": "paragraph", "content": [{"text": value, "marks": []}]} for index, value in enumerate(paragraphs)],
            "citations": [],
        },
    }


@pytest.mark.parametrize(
    ("channel", "form", "expected_schema", "expected_field"),
    [
        ("wechat", "article", "wechat.article.v1", "blocks"),
        ("x", "thread", "x.thread.v1", "posts"),
        ("x", "single", "x.single.v1", "text"),
    ],
)
def test_simple_text_source_adapts_to_canonical_target(channel, form, expected_schema, expected_field):
    adapter = TextChannelAdapter(channel, form)
    result = adapter.adapt(_text_payload("原文"), asset_refs=[], evidence_refs=[])
    assert adapter.contract.payload_schema == expected_schema
    assert expected_field in result
    assert "原文" in str(result)
    assert adapter.canonicalize(result) == result
    rendered = adapter.render(result)
    assert rendered["artifact_kind"] == "text"
    assert "原文" in rendered["text"]
    if form == "article":
        assert rendered["text"].startswith("源文章\n\n")


def test_adaptation_rejects_unmapped_citations_or_assets_and_overlong_single():
    adapter = TextChannelAdapter("x", "single")
    source = _text_payload("原文")
    source["document"]["citations"] = [{"id": "c1", "block_id": "b0", "start": 0, "end": 2, "fact_pack_item_id": 1, "selected_text_hash": hashlib.sha256("原文".encode()).hexdigest()}]
    with pytest.raises(AdapterUnavailable, match="source_citations_require_explicit_mapping"):
        adapter.adapt(source, asset_refs=[], evidence_refs=[])
    with pytest.raises(AdapterUnavailable, match="source_refs_require_explicit_mapping"):
        adapter.adapt(_text_payload("原文"), asset_refs=[{"material_revision_id": 1}], evidence_refs=[])
    with pytest.raises(AdapterUnavailable, match="adapted_payload_invalid"):
        adapter.adapt(_text_payload("很" * 281), asset_refs=[], evidence_refs=[])


@pytest.mark.parametrize(("channel", "form", "location"),
                         [("wechat", "article", "b0"), ("x", "thread", "b0"), ("x", "single", "single")])
def test_exact_source_citation_survives_deterministic_adaptation(channel, form, location):
    adapter = TextChannelAdapter(channel, form)
    source = _text_payload("有来源的原文")
    source["document"]["citations"] = [{"id": "c1", "block_id": "b0", "start": 0, "end": 3,
        "fact_pack_item_id": 7, "selected_text_hash": hashlib.sha256("有来源".encode()).hexdigest()}]
    ref = {"fact_pack_item_id": 7, "snapshot_checksum": "a" * 64, "role": "claim", "sort_order": 0,
           "content_locator_json": {"location_id": location, "start": 0, "end": 3}}
    result = adapter.adapt(source, asset_refs=[], evidence_refs=[ref])
    assert result["citations"] == [{"id": "c1", "location_id": location, "fact_pack_item_id": 7,
                                    "snapshot_checksum": "a" * 64, "locator": {"start": 0, "end": 3}}]
    assert adapter.canonicalize(result, evidence_refs=[ref]) == result
    with pytest.raises(AdapterUnavailable, match="source_citations_require_explicit_mapping"):
        adapter.adapt(source, asset_refs=[], evidence_refs=[{**ref, "content_locator_json": {"location_id": location, "start": 1, "end": 3}}])
