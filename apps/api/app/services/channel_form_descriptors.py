"""Public, value-free projections of registered canonical form contracts."""

from copy import deepcopy

MODERN_ARTICLE_SCHEMAS = frozenset({
    "toutiao.article.v1", "baijia.article.v1", "zhihu.article.v1", "zhihu.answer.v1",
    "bilibili.article.v1", "sohu.article.v1", "penguin.article.v1", "netease.article.v1", "x.articles.v1",
})
ARTICLE_BLOCK_FIELDS = {
    "heading": {"id", "order", "kind", "text", "level"},
    "paragraph": {"id", "order", "kind", "text"},
    "quote": {"id", "order", "kind", "text"},
    "list": {"id", "order", "kind", "ordered", "items"},
    "callout": {"id", "order", "kind", "text", "tone"},
    "code": {"id", "order", "kind", "text", "language"},
    "divider": {"id", "order", "kind"},
    "image": {"id", "order", "kind", "image_ref_key", "text", "alt_text"},
    "direct_answer": {"id", "order", "kind", "text"},
}
TEXT_LIMITS = {"title": 200, "summary": 2000, "block_text": 10000, "image_text": 2000,
               "language": 40, "tag": 100, "question": 2000, "url": 2000, "context": 10000,
               "long_post": 25000, "weibo": 2000, "description": 2000, "caption": 500}
CALLOUT_TONES = ("note", "info", "warning")


def _field(path, kind, label=None, *, required=False, readonly=False, default=None, **constraints):
    if kind == "media_ref":
        constraints = {"min_length": 1, "max_length": 100,
                       "pattern": "^[A-Za-z0-9][A-Za-z0-9_-]{0,99}$", **constraints}
    return {"path": path, "type": kind, "label": label or path.rsplit(".", 1)[-1],
            "required": required, "readonly": readonly, "default": default, **constraints}


def _text(path, bound, label=None, *, required=False, default=""):
    return _field(path, "string", label, required=required, default=default,
                  min_length=1 if required else 0, max_length=bound, normalization="NFC/newline")


def _ordered_fields(path, maximum):
    return {"id": _field(f"{path}.id", "string", "稳定标识", required=True, readonly=True,
                         pattern="^[A-Za-z0-9][A-Za-z0-9_-]{0,99}$", min_length=1, max_length=100),
            "order": _field(f"{path}.order", "integer", "顺序", required=True, readonly=True,
                            minimum=0, maximum=maximum - 1, contiguous=True)}


def _list(path, fields, maximum, *, minimum=0, label=None, variants=None):
    item = _field(f"{path}[]", "object", required=True, fields=list(fields.values()), additional_fields=False)
    if variants is not None:
        item.update(discriminator="kind", variants=variants)
    return _field(path, "list", label, required=minimum > 0, default=[], min_items=minimum,
                  max_items=maximum, ordered=True, unique_ids=True, item=item)


def _blocks(schema):
    modern = schema in MODERN_ARTICLE_SCHEMAS
    maximum = 250 if modern else 200
    kinds = set(ARTICLE_BLOCK_FIELDS) - {"direct_answer"} if modern else {"heading", "paragraph", "quote", "list"}
    if schema == "wechat.article.v1":
        kinds.add("image")
    if schema == "zhihu.answer.v1":
        kinds.add("direct_answer")
    variants = {}
    for kind in sorted(kinds):
        fields = _ordered_fields("blocks[]", maximum)
        fields["kind"] = _field("blocks[].kind", "string", "段落类型", required=True, default=kind, enum=[kind])
        if kind == "image":
            fields.update(image_ref_key=_field("blocks[].image_ref_key", "media_ref", "图片", required=True,
                                              role="inline_image", exact_slot=True),
                          text=_text("blocks[].text", 2000, "图说"), alt_text=_text("blocks[].alt_text", 2000, "替代文字"))
        elif kind == "list" and modern:
            fields["ordered"] = _field("blocks[].ordered", "boolean", "有序列表", default=False)
            children = _ordered_fields("blocks[].items[]", 250)
            children["text"] = _text("blocks[].items[].text", 10000, "条目", required=True)
            fields["items"] = _list("blocks[].items", children, 250, minimum=1, label="列表项")
        elif kind != "divider":
            fields["text"] = _text("blocks[].text", 10000, "直接回答" if kind == "direct_answer" else "正文", required=True)
        if modern and kind == "heading":
            fields["level"] = _field("blocks[].level", "integer", "标题层级", default=2, minimum=1, maximum=6)
        if kind == "callout":
            fields["tone"] = _field("blocks[].tone", "string", "提示类型", default="note", enum=list(CALLOUT_TONES))
        if kind == "code":
            fields["language"] = _text("blocks[].language", 40, "代码语言")
        variants[kind] = fields
    result = _list("blocks", {}, maximum, minimum=1, label="正文段落", variants=variants)
    result["item"]["global_unique_ids"] = True
    if schema == "zhihu.answer.v1":
        result["first_kind"] = "direct_answer"
        result["kind_counts"] = {"direct_answer": {"min": 1, "max": 1}}
    return result


def _tags():
    return _field("tags", "list", "标签", default=[], min_items=0, max_items=50,
                  unique_values=True, item=_text("tags[]", TEXT_LIMITS["tag"], required=True))


def _common():
    citations = {
        "id": _field("citations[].id", "string", required=True, readonly=True, max_length=100,
                     pattern="^[A-Za-z0-9][A-Za-z0-9_-]{0,99}$"),
        "location_id": _field("citations[].location_id", "string", "正文位置", required=True, max_length=100,
                              pattern="^[A-Za-z0-9][A-Za-z0-9_-]{0,99}$"),
        "fact_pack_item_id": _field("citations[].fact_pack_item_id", "integer", "事实项", required=True, minimum=1),
        "snapshot_checksum": _field("citations[].snapshot_checksum", "string", required=True, readonly=True,
                                    pattern="^[0-9a-f]{64}$", min_length=64, max_length=64),
        "locator": _field("citations[].locator", "object", "引用范围", required=True, additional_fields=False, fields=[
            _field("citations[].locator.start", "integer", "开始", required=True, minimum=0),
            _field("citations[].locator.end", "integer", "结束", required=True, minimum=1),
        ]),
    }
    declarations = {
        "id": _field("declarations[].id", "string", required=True, readonly=True, max_length=100,
                     pattern="^[A-Za-z0-9][A-Za-z0-9_-]{0,99}$"),
        "kind": _field("declarations[].kind", "string", "声明类型", required=True, max_length=100,
                       pattern="^[A-Za-z0-9][A-Za-z0-9_-]{0,99}$"),
        "text": _text("declarations[].text", 2000, "声明", required=True),
    }
    result = [_list("citations", citations, 250, label="引用"), _list("declarations", declarations, 50, label="声明")]
    for field in result:
        field["ordered"] = False
    result[0]["offset_unit"] = "unicode_code_point"
    result[0]["exact_evidence_ref"] = True
    return result


def form_descriptor_for(schema: str, channel_id: str | None = None, content_form: str | None = None) -> dict:
    from .channel_variant_documents import ARTICLE_SCHEMAS

    fields = []
    roles = []
    if schema == "wechat.article.v1" or schema in ARTICLE_SCHEMAS:
        fields = [_text("title", 200, "标题", required=True)]
        if schema in MODERN_ARTICLE_SCHEMAS:
            fields += [_text("summary", 2000, "概要"), _tags()]
        if schema == "zhihu.answer.v1":
            fields.append(_field("question", "object", "已确认的问题", required=True, additional_fields=False, fields=[
                _text("question.text", 2000, "问题", required=True), _text("question.url", 2000, "问题链接"),
                _text("question.context", 10000, "问题背景"),
                _field("question.confirmed", "boolean", "确认问题", required=True, default=False, enum=[True]),
            ]))
        fields.append(_blocks(schema))
        if schema == "wechat.article.v1":
            fields += [_field("html_template", "string", "公众号原版 HTML", readonly=True, default=None,
                              encoding="wechat_official_html.v1", max_length=2_000_000),
                       _text("digest", 120, "摘要"), _text("author", 16, "作者")]
            roles.append({"role": "cover", "required": False, "max_items": 1})
        roles.append({"role": "inline_image", "required": False, "exact_slot": True, "placement": "block_id"})
    elif schema == "x.thread.v1":
        items = _ordered_fields("posts[]", 25)
        items["text"] = _text("posts[].text", 280, "推文", required=True)
        fields = [_list("posts", items, 25, minimum=1, label="推串")]
    elif schema in {"x.single.v1", "weibo.single.v1", "x.long_post.v1"}:
        limit = {"x.single.v1": 280, "weibo.single.v1": 2000, "x.long_post.v1": 25000}[schema]
        fields = [_text("text", limit, "正文", required=True)]
        if schema == "weibo.single.v1":
            items = _ordered_fields("images[]", 250)
            items["image_ref_key"] = _field("images[].image_ref_key", "media_ref", "图片", required=True,
                                            role="post_image", exact_slot=True)
            fields += [_tags(), _list("images", items, 250, label="配图")]
            roles.append({"role": "post_image", "required": False, "exact_slot": True, "placement": "image_id"})
    elif schema in {"xiaohongshu.image_note.v1", "bilibili.image_note.v1"}:
        limit = 20 if schema.startswith("xiaohongshu") else 250
        items = _ordered_fields("cards[]", limit)
        items.update(image_ref_key=_field("cards[].image_ref_key", "media_ref", "成品图片", required=True,
                                          role="card_image", exact_slot=True), caption=_text("cards[].caption", 500, "图说"))
        fields = [_text("title", 200, "标题", required=True)]
        if schema.startswith("bilibili"):
            fields += [_text("description", 2000, "说明"), _tags()]
        fields.append(_list("cards", items, limit, minimum=1, label="图卡"))
        roles.append({"role": "card_image", "required": True, "exact_render": True, "exact_slot": True,
                      "dimension_source": "published_profile_and_render_attestation"})
    elif schema == "douyin.spoken_script.v1":
        items = _ordered_fields("scenes[]", 120)
        items.update(script=_text("scenes[].script", 10000, "脚本", required=True),
                     voice_text=_text("scenes[].voice_text", 10000, "口播", required=True),
                     b_roll_ref_keys=_field("scenes[].b_roll_ref_keys", "list", "B-roll", default=[], min_items=0,
                                            max_items=20, unique_values=True,
                                            item=_field("scenes[].b_roll_ref_keys[]", "media_ref", required=True,
                                                        exact_slot=True, role="b_roll")))
        fields = [_list("scenes", items, 120, minimum=1, label="分镜"),
                  _field("estimated_srt", "object", "估算字幕", additional_fields=False, fields=[
                      _field("estimated_srt.estimated", "boolean", required=True, readonly=True, default=True, enum=[True]),
                      _text("estimated_srt.text", 20000, "SRT"),
                  ])]
        roles.append({"role": "b_roll", "required": False, "exact_slot": True})
    else:
        raise ValueError("unsupported_variant_schema")
    errors = {
        "unknown_fields": {"path": "", "message": "含不支持的字段"},
        "text_bound": {"path": "", "message": "文字为空或超过技术长度限制"},
        "text_required": {"path": "", "message": "字段必须是文字"},
        "invalid_id": {"path": "", "message": "稳定标识格式不正确"},
        "duplicate_id": {"path": "", "message": "稳定标识重复"},
        "order_mismatch": {"path": "", "message": "顺序必须从零连续排列"},
        "collection_bound": {"path": "", "message": "列表数量不符合技术限制"},
        "block_kind_invalid": {"path": "blocks[].kind", "message": "不支持该段落类型"},
        "asset_ref_missing": {"path": "", "message": "缺少精确素材引用"},
        "citation_location_invalid": {"path": "citations", "message": "引用位置或范围不匹配"},
        "evidence_ref_missing": {"path": "citations", "message": "缺少精确事实引用"},
        "question_confirmation_required": {"path": "question.confirmed", "message": "请确认问题"},
        "direct_answer_required": {"path": "blocks", "message": "首段必须是唯一直接回答"},
        "payload_too_large": {"path": "", "message": "正文超过技术大小限制"},
        "object_required": {"path": "", "message": "字段必须是结构对象"},
        "control_character": {"path": "", "message": "文字含不允许的控制字符"},
        "invalid_unicode": {"path": "", "message": "文字含无效字符"},
        "asset_refs_invalid": {"path": "asset_refs", "message": "素材引用格式或数量不正确"},
        "citations_invalid": {"path": "citations", "message": "引用格式或数量不正确"},
        "evidence_refs_invalid": {"path": "evidence_refs", "message": "事实引用格式或数量不正确"},
        "declarations_invalid": {"path": "declarations", "message": "声明格式或数量不正确"},
        "boolean_required": {"path": "blocks[].ordered", "message": "字段必须为是或否"},
        "heading_level_invalid": {"path": "blocks[].level", "message": "标题层级必须为一到六"},
        "callout_tone_invalid": {"path": "blocks[].tone", "message": "不支持该提示类型"},
        "question_url_invalid": {"path": "question.url", "message": "问题链接格式不正确"},
        "duplicate_tag": {"path": "tags", "message": "标签重复"},
        "duplicate_image_ref": {"path": "", "message": "图片引用重复"},
        "inline_mapping_invalid": {"path": "blocks", "message": "图片与段落位置不匹配"},
        "official_html_content_mismatch": {"path": "html_template", "message": "原版 HTML 与段落不匹配"},
        "official_html_required": {"path": "html_template", "message": "需要公众号原版 HTML"},
        "srt_must_be_estimated": {"path": "estimated_srt.estimated", "message": "字幕必须标为估算"},
    }
    result = {"descriptor_version": 1, "channel_id": channel_id or schema.split(".")[0],
              "content_form": content_form or schema.split(".")[1], "schema_id": schema, "schema_version": "1",
              "fields": fields + _common(), "media_roles": roles, "error_mapping": errors,
              "technical_limits": {"canonical_bytes": 2_000_000, "platform_verified": False},
              "additional_fields": False}
    return deepcopy(result)
