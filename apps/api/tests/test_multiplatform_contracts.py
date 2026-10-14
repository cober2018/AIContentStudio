import copy

import pytest
from sqlalchemy import select

from app.models import ChannelTemplateVersion
from app.services.channel_adapters import FIRST_BATCH, AdapterUnavailable, TextChannelAdapter, capability_for
from app.services.channel_variant_documents import VariantDocumentError, canonical_payload, payload_hash

ARTICLE_TARGETS = [
    "toutiao.article.v1", "baijia.article.v1", "zhihu.article.v1", "bilibili.article.v1",
    "sohu.article.v1", "penguin.article.v1", "netease.article.v1", "x.articles.v1",
]
ASSETS = [{"slot_key": "image1", "material_revision_id": 1, "content_hash_snapshot": "a" * 64}]


def article():
    return {"title": "标题", "summary": "概要", "tags": ["技术"], "blocks": [
        {"id": "b1", "order": 0, "kind": "heading", "text": "标题", "level": 2},
        {"id": "b2", "order": 1, "kind": "paragraph", "text": "正文"},
        {"id": "b3", "order": 2, "kind": "quote", "text": "引用"},
        {"id": "b4", "order": 3, "kind": "list", "ordered": False,
         "items": [{"id": "item1", "order": 0, "text": "条目"}]},
        {"id": "b5", "order": 4, "kind": "callout", "text": "注意", "tone": "note"},
        {"id": "b6", "order": 5, "kind": "code", "text": "print('<x>')", "language": "python"},
        {"id": "b7", "order": 6, "kind": "divider"},
        {"id": "b8", "order": 7, "kind": "image", "image_ref_key": "image1", "text": "图说", "alt_text": "图"},
    ]}


@pytest.mark.parametrize("schema", ARTICLE_TARGETS)
def test_typed_articles_roundtrip(schema):
    payload = canonical_payload(schema, article(), asset_refs=ASSETS)
    assert payload["summary"] == "概要"
    assert payload["blocks"][3]["items"][0]["id"] == "item1"
    assert canonical_payload(schema, payload, asset_refs=ASSETS) == payload


@pytest.mark.parametrize("schema", ARTICLE_TARGETS)
def test_direct_answer_never_allowed_in_articles(schema):
    payload = {"title": "标题", "blocks": [{"id": "b1", "order": 0, "kind": "direct_answer", "text": "答案"}]}
    with pytest.raises(VariantDocumentError, match="block_kind_invalid"):
        canonical_payload(schema, payload)


def test_answer_requires_confirmed_question_and_first_direct_answer():
    payload = {"title": "回答", "question": {"text": "问题？", "confirmed": True},
               "blocks": [{"id": "b1", "order": 0, "kind": "direct_answer", "text": "直接回答"}]}
    assert canonical_payload("zhihu.answer.v1", payload)["question"]["confirmed"] is True
    for change in ({"question": {"text": "问题？", "confirmed": False}},
                   {"question": {}}, {"blocks": [{"id": "b1", "order": 0, "kind": "paragraph", "text": "不是直接回答"}]},
                   {"blocks": payload["blocks"] + [{"id": "b2", "order": 1, "kind": "direct_answer", "text": "重复"}]}):
        with pytest.raises(VariantDocumentError):
            canonical_payload("zhihu.answer.v1", {**payload, **change})


def test_new_single_and_card_shapes():
    assert canonical_payload("x.long_post.v1", {"text": "连续正文"})["text"] == "连续正文"
    with pytest.raises(VariantDocumentError):
        canonical_payload("x.long_post.v1", {"posts": []})
    post = canonical_payload("weibo.single.v1", {"text": "正文", "tags": ["技术"],
        "images": [{"id": "pic1", "order": 0, "image_ref_key": "image1"}]}, asset_refs=ASSETS)
    assert post["images"][0]["id"] == "pic1"
    card = canonical_payload("bilibili.image_note.v1", {"title": "标题", "description": "说明", "tags": ["技术"],
        "cards": [{"id": "card1", "order": 0, "image_ref_key": "image1", "caption": "图说"}]}, asset_refs=ASSETS)
    assert card["description"] == "说明"
    with pytest.raises(VariantDocumentError, match="asset_ref_missing"):
        canonical_payload("bilibili.image_note.v1", card)


def test_global_list_location_ids_and_citations():
    payload = article()
    payload["blocks"][3]["items"][0]["id"] = "b1"
    with pytest.raises(VariantDocumentError, match="duplicate_id"):
        canonical_payload("toutiao.article.v1", payload, asset_refs=ASSETS)
    payload = article()
    payload["citations"] = [{"id": "cite1", "location_id": "item1", "fact_pack_item_id": 1,
                            "snapshot_checksum": "b" * 64, "locator": {"start": 0, "end": 2}}]
    evidence = [{"fact_pack_item_id": 1, "snapshot_checksum": "b" * 64,
                 "content_locator_json": {"location_id": "item1", "start": 0, "end": 2}}]
    assert canonical_payload("toutiao.article.v1", payload, asset_refs=ASSETS, evidence_refs=evidence)["citations"]


def test_catalog_and_descriptors_are_safe_and_complete(db_session):
    from app.services.channel_form_descriptors import form_descriptor_for
    assert {("bilibili", "image_note"), ("x", "long_post"), ("x", "articles")} <= set(FIRST_BATCH)
    for target, contract in FIRST_BATCH.items():
        descriptor = form_descriptor_for(contract.payload_schema, *target)
        assert descriptor["schema_id"] == contract.payload_schema
        assert descriptor["descriptor_version"] == 1
        assert descriptor["fields"]
        assert descriptor["technical_limits"]["canonical_bytes"] == 2_000_000
        assert capability_for(db_session, next(iter(contract.accepted_master_schemas)), *target)["form_descriptor"] == descriptor
    answer = form_descriptor_for("zhihu.answer.v1", "zhihu", "answer")
    block = next(field for field in answer["fields"] if field["path"] == "blocks")
    assert "direct_answer" in block["item"]["variants"]
    assert set(block["item"]["variants"]["direct_answer"]) == {"id", "order", "kind", "text"}


def test_descriptor_retains_original_script_text_bounds():
    from app.services.channel_form_descriptors import form_descriptor_for
    descriptor = form_descriptor_for("douyin.spoken_script.v1")
    scenes = next(field for field in descriptor["fields"] if field["path"] == "scenes")
    for path in ("scenes[].script", "scenes[].voice_text"):
        field = next(field for field in scenes["item"]["fields"] if field["path"] == path)
        assert field["max_length"] == 10000


def test_new_text_adapters_preserve_structure_and_require_question():
    source = {"title": "标题", "document": {"schema": "studio.text.document.v1", "blocks": [
        {"id": "b1", "type": "paragraph", "content": [{"text": "正文", "marks": []}]},
        {"id": "b2", "type": "bullet_list", "items": [{"id": "item1", "content": [{"text": "条目", "marks": []}]}]},
    ], "citations": []}}
    target = TextChannelAdapter("toutiao", "article").adapt(source, asset_refs=[], evidence_refs=[])
    assert target["blocks"][1]["kind"] == "list"
    assert "条目" in TextChannelAdapter("toutiao", "article").render(target)["text"]
    answer = TextChannelAdapter("zhihu", "answer")
    with pytest.raises(AdapterUnavailable, match="question_confirmation_required"):
        answer.adapt(source, asset_refs=[], evidence_refs=[])
    source["_target_question"] = {"text": "问题？", "confirmed": True}
    result = answer.adapt(source, asset_refs=[], evidence_refs=[])
    assert result["blocks"][0]["kind"] == "direct_answer"
    assert result["question"]["confirmed"] is True


@pytest.mark.parametrize("schema,payload,expected", [
    ("wechat.article.v1", {"title": "标题", "blocks": [{"id": "b1", "order": 0, "kind": "paragraph", "text": "正文"}]}, "e9a5e75e66f62a1f821e7f24ba3de666ff1922183febb2938d540773c615e560"),
    ("x.single.v1", {"text": "正文"}, "db2ba54ce3e00261619a206ba62533a088013eaba4614a01ecc3bd18f74abb8f"),
    ("x.thread.v1", {"posts": [{"id": "p1", "order": 0, "text": "正文"}]}, "f033c767109301e95ec2fd2036424c2ee1de37fc8a17e6dda1e72c93d0e0975c"),
    ("xiaohongshu.image_note.v1", {"title": "标题", "cards": [{"id": "c1", "order": 0, "image_ref_key": "c1", "caption": "正文"}]}, "cb9320659f5de282417c0c93f5fb8ed17536e79175c2f9809c58d8eb370411d6"),
    ("douyin.spoken_script.v1", {"scenes": [{"id": "s1", "order": 0, "script": "正文", "voice_text": "正文", "b_roll_ref_keys": []}]}, "cdddd6fd04bb98a5f3e7a291cbc4f57ff8cf80e74de60d6c492cb31fdc919449"),
])
def test_original_five_hashes_are_unchanged(schema, payload, expected):
    refs = [{"slot_key": "c1", "material_revision_id": 1, "content_hash_snapshot": "a" * 64}] if schema.startswith("xiaohongshu") else []
    assert payload_hash(schema, payload, asset_refs=refs) == expected


def test_profile_dry_run_cas_append_only_and_idempotent(db_session):
    from app.services.multiplatform_profiles import apply_profiles, dry_run_profiles
    old = ChannelTemplateVersion(channel="x", version=4, name="User X", status="published",
        profile_json={"content_forms": {"single": {"artifact_kind": "text", "audience": "user-owned"}}})
    db_session.add(old)
    db_session.commit()
    original = copy.deepcopy(old.profile_json)
    plan = dry_run_profiles(db_session, ["x", "bilibili"])
    assert len(db_session.scalars(select(ChannelTemplateVersion)).all()) == 1
    assert plan["changes"][0]["before"]["content_forms"]["single"]["audience"] == "user-owned"
    result = apply_profiles(db_session, plan, expected_plan_hash=plan["plan_hash"])
    assert len(result["created"]) == 2
    db_session.refresh(old)
    assert old.profile_json == original
    assert old.status == "archived"
    published = db_session.scalars(select(ChannelTemplateVersion).where(
        ChannelTemplateVersion.channel == "x", ChannelTemplateVersion.status == "published")).all()
    assert len(published) == 1 and published[0].id != old.id
    assert apply_profiles(db_session, plan, expected_plan_hash=plan["plan_hash"])["created"] == []
    stale = dry_run_profiles(db_session, ["x"])
    current = db_session.scalars(select(ChannelTemplateVersion).where(ChannelTemplateVersion.channel == "x").order_by(ChannelTemplateVersion.version.desc())).first()
    current.profile_json = {"content_forms": {"single": {"artifact_kind": "text", "audience": "concurrent"}}}
    db_session.commit()
    with pytest.raises(ValueError, match="profile_stale"):
        apply_profiles(db_session, stale, expected_plan_hash=stale["plan_hash"])


def test_published_profile_instructions_are_exact_safe_projection(db_session):
    from app.services.multiplatform_profiles import apply_profiles, dry_run_profiles
    plan = dry_run_profiles(db_session, ["x"])
    apply_profiles(db_session, plan, expected_plan_hash=plan["plan_hash"])
    capabilities = [capability_for(db_session, "text.master.v2", "x", form)
                    for form in ("single", "thread", "long_post", "articles")]
    assert len({capability["effective_instructions"] for capability in capabilities}) == 4
    for capability in capabilities:
        assert "profile_json" not in capability
        assert capability["effective_instructions"]


def test_profile_review_api_is_admin_only_and_read_only(client, db_session):
    from app.models import User
    db_session.add_all([User(email="admin@studio.local", name="Admin", role="admin"),
                        User(email="editor@studio.local", name="Editor", role="editor")])
    db_session.commit()
    path = "/api/v1/templates/channel-profiles"
    assert client.post(f"{path}/dry-run", json={"channels": ["x"]}, headers={"X-Studio-User": "editor@studio.local"}).status_code == 403
    response = client.post(f"{path}/dry-run", json={"channels": ["x"]}, headers={"X-Studio-User": "admin@studio.local"})
    assert response.status_code == 200
    assert db_session.scalars(select(ChannelTemplateVersion)).all() == []
    plan = response.json()
    changed = copy.deepcopy(plan)
    changed["changes"][0]["after"]["content_forms"]["single"]["artifact_kind"] = "video"
    response = client.post(f"{path}/apply", json={"plan": changed, "expected_plan_hash": plan["plan_hash"]},
                           headers={"X-Studio-User": "admin@studio.local"})
    assert response.status_code == 409
    assert db_session.scalars(select(ChannelTemplateVersion)).all() == []
