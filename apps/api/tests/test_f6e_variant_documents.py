"""Versioned canonical ChannelVariant payloads never accept opaque adapter JSON."""

import pytest

from app.services.channel_variant_documents import VariantDocumentError, canonical_payload, payload_hash


@pytest.mark.parametrize(
    ("schema", "payload"),
    [
        ("wechat.article.v1", {"title": "文章", "blocks": [{"id": "b1", "order": 0, "kind": "paragraph", "text": "正文"}]}),
        ("x.thread.v1", {"posts": [{"id": "p1", "order": 0, "text": "第一条"}, {"id": "p2", "order": 1, "text": "第二条"}]}),
        ("x.single.v1", {"text": "单条内容"}),
        ("xiaohongshu.image_note.v1", {"title": "图文", "cards": [{"id": "c1", "order": 0, "image_ref_key": "cover", "caption": "卡片"}]}),
        ("douyin.spoken_script.v1", {"scenes": [{"id": "s1", "order": 0, "script": "口播", "voice_text": "口播", "b_roll_ref_keys": []}]}),
    ],
)
def test_five_variant_schemas_canonicalize_deterministically(schema, payload):
    assets = [{"slot_key": "cover", "material_revision_id": 7, "content_hash_snapshot": "a" * 64}]
    first = canonical_payload(schema, payload, asset_refs=assets)
    second = canonical_payload(schema, first, asset_refs=assets)
    assert first == second
    assert payload_hash(schema, first, asset_refs=assets) == payload_hash(schema, second, asset_refs=assets)


@pytest.mark.parametrize(
    ("schema", "payload", "reason"),
    [
        ("x.single.v1", {"text": "正文", "unknown": "opaque"}, "unknown_fields"),
        ("x.thread.v1", {"posts": [{"id": "same", "order": 0, "text": "A"}, {"id": "same", "order": 1, "text": "B"}]}, "duplicate_id"),
        ("wechat.article.v1", {"title": "文章", "blocks": [{"id": "b1", "order": 1, "kind": "paragraph", "text": "正文"}]}, "order_mismatch"),
        ("xiaohongshu.image_note.v1", {"title": "图文", "cards": [{"id": "c1", "order": 0, "image_ref_key": "missing", "caption": "卡片"}]}, "asset_ref_missing"),
        ("douyin.spoken_script.v1", {"scenes": [{"id": "s1", "order": 0, "script": "口播", "voice_text": "口播", "b_roll_ref_keys": ["missing"]}]}, "asset_ref_missing"),
    ],
)
def test_invalid_or_unbound_variant_payload_fails_closed(schema, payload, reason):
    with pytest.raises(VariantDocumentError, match=reason):
        canonical_payload(schema, payload)


def test_citation_requires_exact_evidence_ref_checksum_and_locator():
    payload = {
        "text": "有证据的观点",
        "citations": [{"id": "cite1", "location_id": "single", "fact_pack_item_id": 5, "snapshot_checksum": "a" * 64, "locator": {"start": 0, "end": 3}}],
    }
    with pytest.raises(VariantDocumentError, match="evidence_ref_missing"):
        canonical_payload("x.single.v1", payload)
    evidence = [{"fact_pack_item_id": 5, "snapshot_checksum": "a" * 64, "content_locator_json": {"location_id": "single", "start": 0, "end": 3}}]
    assert canonical_payload("x.single.v1", payload, evidence_refs=evidence)["citations"][0]["id"] == "cite1"
    evidence[0]["content_locator_json"]["location_id"] = "foreign"
    with pytest.raises(VariantDocumentError, match="evidence_ref_missing"):
        canonical_payload("x.single.v1", payload, evidence_refs=evidence)
    evidence[0]["content_locator_json"]["location_id"] = "single"
    evidence[0]["snapshot_checksum"] = "b" * 64
    with pytest.raises(VariantDocumentError, match="evidence_ref_missing"):
        canonical_payload("x.single.v1", payload, evidence_refs=evidence)


def test_malformed_ref_values_fail_with_typed_error_instead_of_type_error():
    script = {"scenes": [{"id": "s1", "order": 0, "script": "内容", "voice_text": "内容", "b_roll_ref_keys": [{"bad": "key"}]}]}
    with pytest.raises(VariantDocumentError, match="invalid_id"):
        canonical_payload("douyin.spoken_script.v1", script)
    cited = {"text": "内容", "citations": [{"id": "c1", "location_id": "single", "fact_pack_item_id": 1, "snapshot_checksum": "a" * 64, "locator": {"start": 0, "end": 1}}]}
    with pytest.raises(VariantDocumentError, match="evidence_refs_invalid"):
        canonical_payload("x.single.v1", cited, evidence_refs=[{"fact_pack_item_id": {"bad": 1}, "snapshot_checksum": ["bad"], "content_locator_json": {"start": 0, "end": 1}}])
