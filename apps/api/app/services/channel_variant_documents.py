"""Bounded, deterministic durable payloads for published channel variants."""

import hashlib
import json
import re
import unicodedata

from .channel_form_descriptors import ARTICLE_BLOCK_FIELDS, CALLOUT_TONES, MODERN_ARTICLE_SCHEMAS, TEXT_LIMITS


class VariantDocumentError(ValueError):
    def __init__(self, reason: str, path: str = ""):
        super().__init__(reason)
        self.code = reason
        self.path = path


_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,99}$")
_HASH = re.compile(r"^[0-9a-f]{64}$")

# Long-form text targets. They share one document shape and do not inherit WeChat's cover or official HTML.
ARTICLE_SCHEMAS = frozenset({
    "toutiao.article.v1",
    "baijia.article.v1",
    "zhihu.article.v1",
    "zhihu.answer.v1",
    "bilibili.article.v1",
    "sohu.article.v1",
    "penguin.article.v1",
    "netease.article.v1",
    "xueqiu.quant_research.v1",
    "xueqiu.market_recap.v1",
    "juejin.tech_article.v1",
    "x.articles.v1",
})
# x.single stays at 280. Weibo uses the long-post bound, not a remote publish claim.
SINGLE_TEXT_SCHEMAS = frozenset({"x.single.v1", "weibo.single.v1", "x.long_post.v1"})
_SINGLE_TEXT_LIMITS = {"x.single.v1": 280, "weibo.single.v1": 2000, "x.long_post.v1": TEXT_LIMITS["long_post"]}


def _fail(reason: str, path: str = "") -> None:
    raise VariantDocumentError(reason, path)


def _object(value: object, allowed: set[str]) -> dict:
    if not isinstance(value, dict):
        _fail("object_required")
    if set(value) - allowed:
        _fail("unknown_fields")
    return value


def _text(value: object, limit: int, *, required: bool = False) -> str:
    if not isinstance(value, str):
        _fail("text_required")
    normalized = unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n"))
    if len(normalized) > limit or (required and not normalized.strip()):
        _fail("text_bound")
    if any(ord(character) < 32 and character not in "\n\t" for character in normalized):
        _fail("control_character")
    try:
        normalized.encode("utf-8", errors="strict")
    except UnicodeEncodeError:
        _fail("invalid_unicode")
    return normalized


def _id(value: object) -> str:
    if not isinstance(value, str) or _ID.fullmatch(value) is None:
        _fail("invalid_id")
    return value


def _ordered(value: object, limit: int) -> list[dict]:
    if not isinstance(value, list) or not 1 <= len(value) <= limit:
        _fail("collection_bound")
    result = []
    seen = set()
    for index, raw in enumerate(value):
        if not isinstance(raw, dict):
            _fail("object_required")
        item_id = _id(raw.get("id"))
        if item_id in seen:
            _fail("duplicate_id")
        seen.add(item_id)
        if type(raw.get("order")) is not int or raw["order"] != index:
            _fail("order_mismatch")
        result.append(raw)
    return result


def _asset_keys(refs: object) -> set[str]:
    if not isinstance(refs, list) or len(refs) > 250:
        _fail("asset_refs_invalid")
    keys = set()
    for raw in refs:
        if not isinstance(raw, dict):
            _fail("asset_refs_invalid")
        key = _id(raw.get("slot_key"))
        revision_id = raw.get("material_revision_id")
        if key in keys or type(revision_id) is not int or revision_id <= 0 or not isinstance(raw.get("content_hash_snapshot"), str) or _HASH.fullmatch(raw["content_hash_snapshot"]) is None:
            _fail("asset_refs_invalid")
        keys.add(key)
    return keys


def _citations(raw: object, evidence_refs: object, locations: dict[str, str]) -> list[dict]:
    if not isinstance(raw, list) or len(raw) > 250 or not isinstance(evidence_refs, list) or len(evidence_refs) > 250:
        _fail("citations_invalid")
    available = set()
    for ref in evidence_refs:
        ref = _object(ref, {"fact_pack_item_id", "snapshot_checksum", "role", "sort_order", "content_locator_json"})
        fact_id, checksum = ref.get("fact_pack_item_id"), ref.get("snapshot_checksum")
        locator = ref.get("content_locator_json")
        if type(fact_id) is not int or fact_id <= 0 or not isinstance(checksum, str) or _HASH.fullmatch(checksum) is None or not isinstance(locator, dict) or set(locator) != {"location_id", "start", "end"}:
            _fail("evidence_refs_invalid")
        role = ref.get("role", "claim")
        order = ref.get("sort_order", 0)
        if not isinstance(role, str) or not role or len(role) > 40 or _ID.fullmatch(role) is None or type(order) is not int or not 0 <= order < 250:
            _fail("evidence_refs_invalid")
        if not isinstance(locator["location_id"], str) or _ID.fullmatch(locator["location_id"]) is None or type(locator["start"]) is not int or type(locator["end"]) is not int:
            _fail("evidence_refs_invalid")
        available.add((fact_id, checksum, json.dumps(locator, sort_keys=True, separators=(",", ":"))))
    result = []
    seen = set()
    for item in raw:
        item = _object(item, {"id", "location_id", "fact_pack_item_id", "snapshot_checksum", "locator"})
        citation_id = _id(item.get("id"))
        location_id = _id(item.get("location_id"))
        if citation_id in seen or location_id not in locations:
            _fail("citation_location_invalid")
        seen.add(citation_id)
        fact_id = item.get("fact_pack_item_id")
        checksum = item.get("snapshot_checksum")
        locator = _object(item.get("locator"), {"start", "end"})
        start, end = locator.get("start"), locator.get("end")
        if type(fact_id) is not int or fact_id <= 0 or not isinstance(checksum, str) or _HASH.fullmatch(checksum) is None:
            _fail("citations_invalid")
        if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(locations[location_id]):
            _fail("citation_location_invalid")
        normalized_locator = {"start": start, "end": end}
        exact_locator = {"location_id": location_id, **normalized_locator}
        token = (fact_id, checksum, json.dumps(exact_locator, sort_keys=True, separators=(",", ":")))
        if token not in available:
            _fail("evidence_ref_missing")
        result.append({"id": citation_id, "location_id": location_id, "fact_pack_item_id": fact_id, "snapshot_checksum": checksum, "locator": normalized_locator})
    return result


def _declarations(raw: object) -> list[dict]:
    if not isinstance(raw, list) or len(raw) > 50:
        _fail("declarations_invalid")
    result = []
    seen = set()
    for item in raw:
        item = _object(item, {"id", "kind", "text"})
        declaration_id = _id(item.get("id"))
        if declaration_id in seen:
            _fail("duplicate_id")
        seen.add(declaration_id)
        result.append({"id": declaration_id, "kind": _id(item.get("kind")), "text": _text(item.get("text"), 2000, required=True)})
    return result


def validate_wechat_inline_refs(blocks: list[dict], refs: list[dict]) -> None:
    images = [block for block in blocks if block.get("kind") == "image"]
    inline = [ref for ref in refs if ref.get("role") == "inline_image"]
    if not images and not inline:
        return
    keys = [block["image_ref_key"] for block in images]
    if len(set(keys)) != len(keys) or len(inline) != len(images):
        _fail("inline_mapping_invalid")
    covers = [ref for ref in refs if ref.get("role") == "cover"]
    if len(covers) > 1 or len(refs) != len(covers) + len(inline):
        _fail("inline_mapping_invalid")
    if any(any(ref.get(key) != value for key, value in {
        "slot_key": "cover", "sort_order": 0, "placement": {"usage": "cover"},
    }.items()) for ref in covers):
        _fail("inline_mapping_invalid")
    for order, block in enumerate(images, len(covers)):
        ref = next((item for item in inline if item.get("slot_key") == block["image_ref_key"]), None)
        if (ref is None or block["image_ref_key"] == "cover" or type(ref.get("sort_order")) is not int
                or ref["sort_order"] != order or ref.get("placement") != {"usage": "inline", "block_id": block["id"]}):
            _fail("inline_mapping_invalid")


def _tags(raw: object) -> list[str]:
    if not isinstance(raw, list) or len(raw) > 50:
        _fail("collection_bound", "tags")
    result = [_text(value, TEXT_LIMITS["tag"], required=True) for value in raw]
    if len(set(result)) != len(result):
        _fail("duplicate_tag", "tags")
    return result


def _question(raw: object) -> dict:
    item = _object(raw, {"text", "url", "context", "confirmed"})
    if item.get("confirmed") is not True:
        _fail("question_confirmation_required", "question.confirmed")
    result = {"text": _text(item.get("text"), TEXT_LIMITS["question"], required=True), "confirmed": True}
    for key in ("url", "context"):
        if key in item:
            result[key] = _text(item[key], TEXT_LIMITS[key])
    if result.get("url"):
        from urllib.parse import urlsplit

        try:
            url = urlsplit(result["url"])
            if url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password:
                _fail("question_url_invalid", "question.url")
        except ValueError as exc:
            if isinstance(exc, VariantDocumentError):
                raise
            _fail("question_url_invalid", "question.url")
    return result


def _article_blocks(value: object, schema: str, asset_keys: set[str], locations: dict[str, str]) -> list[dict]:
    blocks = _ordered(value, 250)
    identifiers = {block["id"] for block in blocks}
    result = []
    direct_count = 0
    for raw in blocks:
        kind = raw.get("kind")
        if not isinstance(kind, str) or kind not in ARTICLE_BLOCK_FIELDS or kind == "direct_answer" and schema != "zhihu.answer.v1":
            _fail("block_kind_invalid", f"blocks[{raw['order']}].kind")
        raw = _object(raw, ARTICLE_BLOCK_FIELDS[kind])
        block = {"id": raw["id"], "order": raw["order"], "kind": kind}
        if kind == "list":
            ordered = raw.get("ordered", False)
            if type(ordered) is not bool:
                _fail("boolean_required", f"blocks[{raw['order']}].ordered")
            items = []
            for item in _ordered(raw.get("items"), 250):
                item = _object(item, {"id", "order", "text"})
                if item["id"] in identifiers:
                    _fail("duplicate_id", f"blocks[{raw['order']}].items")
                identifiers.add(item["id"])
                normalized = {"id": item["id"], "order": item["order"],
                              "text": _text(item.get("text"), TEXT_LIMITS["block_text"], required=True)}
                locations[item["id"]] = normalized["text"]
                items.append(normalized)
            block.update(ordered=ordered, items=items)
        elif kind == "image":
            key = _id(raw.get("image_ref_key"))
            if key not in asset_keys:
                _fail("asset_ref_missing", f"blocks[{raw['order']}].image_ref_key")
            block.update(image_ref_key=key, text=_text(raw.get("text", ""), TEXT_LIMITS["image_text"]),
                         alt_text=_text(raw.get("alt_text", ""), TEXT_LIMITS["image_text"]))
            locations[block["id"]] = block["text"]
        elif kind != "divider":
            block["text"] = _text(raw.get("text"), TEXT_LIMITS["block_text"], required=True)
            locations[block["id"]] = block["text"]
        if kind == "heading":
            level = raw.get("level", 2)
            if type(level) is not int or not 1 <= level <= 6:
                _fail("heading_level_invalid", f"blocks[{raw['order']}].level")
            block["level"] = level
        elif kind == "callout":
            tone = raw.get("tone", "note")
            if not isinstance(tone, str) or tone not in CALLOUT_TONES:
                _fail("callout_tone_invalid", f"blocks[{raw['order']}].tone")
            block["tone"] = tone
        elif kind == "code":
            block["language"] = _text(raw.get("language", ""), TEXT_LIMITS["language"])
        elif kind == "direct_answer":
            direct_count += 1
        result.append(block)
    if schema == "zhihu.answer.v1" and (direct_count != 1 or result[0]["kind"] != "direct_answer"):
        _fail("direct_answer_required", "blocks")
    return result


def canonical_payload(schema: str, value: object, *, asset_refs: object = None, evidence_refs: object = None) -> dict:
    asset_keys = _asset_keys([] if asset_refs is None else asset_refs)
    evidence = [] if evidence_refs is None else evidence_refs
    common = {"citations", "declarations"}
    locations: dict[str, str] = {}
    if schema == "wechat.article.v1":
        item = _object(value, {"title", "blocks", "html_template", "digest", "author"} | common)
        blocks = []
        for raw in _ordered(item.get("blocks"), 200):
            if raw.get("kind") == "image":
                raw = _object(raw, {"id", "order", "kind", "image_ref_key", "text", "alt_text"})
                key = _id(raw.get("image_ref_key"))
                if key not in asset_keys:
                    _fail("asset_ref_missing")
                block = {"id": raw["id"], "order": raw["order"], "kind": "image", "image_ref_key": key,
                         "text": _text(raw.get("text", ""), 2000), "alt_text": _text(raw.get("alt_text", ""), 2000)}
                locations[block["id"]] = block["text"]
                blocks.append(block)
                continue
            raw = _object(raw, {"id", "order", "kind", "text"})
            if not isinstance(raw.get("kind"), str) or raw["kind"] not in {"heading", "paragraph", "quote", "list"}:
                _fail("block_kind_invalid")
            block = {"id": raw["id"], "order": raw["order"], "kind": raw["kind"], "text": _text(raw.get("text"), 10000, required=True)}
            locations[block["id"]] = block["text"]
            blocks.append(block)
        validate_wechat_inline_refs(blocks, [] if asset_refs is None else asset_refs)
        result = {"title": _text(item.get("title"), 200, required=True), "blocks": blocks}
        if "html_template" in item:
            from .wechat_official_render import original_html_blocks

            try:
                if original_html_blocks(item["html_template"]) != blocks or item.get("declarations", []) or item.get("citations", []):
                    _fail("official_html_content_mismatch")
            except ValueError as exc:
                _fail(str(exc))
            result.update(html_template=item["html_template"], digest=_text(item.get("digest", ""), 120),
                          author=_text(item.get("author", ""), 16))
        elif "digest" in item or "author" in item:
            _fail("official_html_required")
    elif schema == "x.thread.v1":
        item = _object(value, {"posts"} | common)
        posts = []
        for raw in _ordered(item.get("posts"), 25):
            raw = _object(raw, {"id", "order", "text"})
            post = {"id": raw["id"], "order": raw["order"], "text": _text(raw.get("text"), 280, required=True)}
            locations[post["id"]] = post["text"]
            posts.append(post)
        result = {"posts": posts}
    elif schema in SINGLE_TEXT_SCHEMAS:
        item = _object(value, {"text", "tags", "images"} | common if schema == "weibo.single.v1" else {"text"} | common)
        result = {"text": _text(item.get("text"), _SINGLE_TEXT_LIMITS[schema], required=True)}
        locations["single"] = result["text"]
        if schema == "weibo.single.v1":
            images = item.get("images", [])
            if not isinstance(images, list):
                _fail("collection_bound", "images")
            result.update(tags=_tags(item.get("tags", [])), images=[])
            image_keys = set()
            for raw in _ordered(images, 250) if images else []:
                raw = _object(raw, {"id", "order", "image_ref_key"})
                key = _id(raw.get("image_ref_key"))
                if key not in asset_keys:
                    _fail("asset_ref_missing", f"images[{raw['order']}].image_ref_key")
                if key in image_keys:
                    _fail("duplicate_image_ref", "images")
                image_keys.add(key)
                result["images"].append({"id": raw["id"], "order": raw["order"], "image_ref_key": key})
    elif schema in MODERN_ARTICLE_SCHEMAS:
        item = _object(value, {"title", "summary", "blocks", "tags"} | common | ({"question"} if schema == "zhihu.answer.v1" else set()))
        if schema == "zhihu.answer.v1":
            if "question" not in item:
                _fail("question_confirmation_required", "question")
            question = _question(item["question"])
        result = {"title": _text(item.get("title"), TEXT_LIMITS["title"], required=True),
                  "summary": _text(item.get("summary", ""), TEXT_LIMITS["summary"]),
                  "blocks": _article_blocks(item.get("blocks"), schema, asset_keys, locations),
                  "tags": _tags(item.get("tags", []))}
        if schema == "zhihu.answer.v1":
            result["question"] = question
    elif schema in ARTICLE_SCHEMAS:
        item = _object(value, {"title", "blocks"} | common)
        blocks = []
        for raw in _ordered(item.get("blocks"), 200):
            raw = _object(raw, {"id", "order", "kind", "text"})
            if not isinstance(raw.get("kind"), str) or raw["kind"] not in {"heading", "paragraph", "quote", "list"}:
                _fail("block_kind_invalid")
            block = {"id": raw["id"], "order": raw["order"], "kind": raw["kind"], "text": _text(raw.get("text"), 10000, required=True)}
            locations[block["id"]] = block["text"]
            blocks.append(block)
        result = {"title": _text(item.get("title"), 200, required=True), "blocks": blocks}
    elif schema == "xiaohongshu.image_note.v1":
        item = _object(value, {"title", "cards"} | common)
        cards = []
        for raw in _ordered(item.get("cards"), 20):
            raw = _object(raw, {"id", "order", "image_ref_key", "caption"})
            key = _id(raw.get("image_ref_key"))
            if key not in asset_keys:
                _fail("asset_ref_missing")
            card = {"id": raw["id"], "order": raw["order"], "image_ref_key": key, "caption": _text(raw.get("caption", ""), 500)}
            locations[card["id"]] = card["caption"]
            cards.append(card)
        result = {"title": _text(item.get("title"), 200, required=True), "cards": cards}
    elif schema == "bilibili.image_note.v1":
        item = _object(value, {"title", "description", "tags", "cards"} | common)
        cards = []
        keys = set()
        for raw in _ordered(item.get("cards"), 250):
            raw = _object(raw, {"id", "order", "image_ref_key", "caption"})
            key = _id(raw.get("image_ref_key"))
            if key not in asset_keys:
                _fail("asset_ref_missing", f"cards[{raw['order']}].image_ref_key")
            if key in keys:
                _fail("duplicate_image_ref", "cards")
            keys.add(key)
            card = {"id": raw["id"], "order": raw["order"], "image_ref_key": key,
                    "caption": _text(raw.get("caption", ""), TEXT_LIMITS["caption"])}
            locations[card["id"]] = card["caption"]
            cards.append(card)
        result = {"title": _text(item.get("title"), TEXT_LIMITS["title"], required=True),
                  "description": _text(item.get("description", ""), TEXT_LIMITS["description"]),
                  "tags": _tags(item.get("tags", [])), "cards": cards}
    elif schema == "douyin.spoken_script.v1":
        item = _object(value, {"scenes", "estimated_srt"} | common)
        scenes = []
        for raw in _ordered(item.get("scenes"), 120):
            raw = _object(raw, {"id", "order", "script", "voice_text", "b_roll_ref_keys"})
            refs = raw.get("b_roll_ref_keys", [])
            if not isinstance(refs, list) or len(refs) > 20:
                _fail("asset_refs_invalid")
            keys = [_id(key) for key in refs]
            if len(keys) != len(set(keys)):
                _fail("asset_refs_invalid")
            if any(key not in asset_keys for key in keys):
                _fail("asset_ref_missing")
            scene = {"id": raw["id"], "order": raw["order"], "script": _text(raw.get("script"), 10000, required=True), "voice_text": _text(raw.get("voice_text"), 10000, required=True), "b_roll_ref_keys": keys}
            locations[scene["id"]] = scene["script"]
            scenes.append(scene)
        result = {"scenes": scenes}
        if "estimated_srt" in item:
            srt = _object(item["estimated_srt"], {"estimated", "text"})
            if srt.get("estimated") is not True:
                _fail("srt_must_be_estimated")
            result["estimated_srt"] = {"estimated": True, "text": _text(srt.get("text"), 20000)}
    else:
        _fail("unsupported_variant_schema")
    result["citations"] = _citations(item.get("citations", []), evidence, locations)
    result["declarations"] = _declarations(item.get("declarations", []))
    encoded = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    if len(encoded) > 2_000_000:
        _fail("payload_too_large")
    return result


def collection_key(schema: str) -> str | None:
    if schema == "wechat.article.v1" or schema in ARTICLE_SCHEMAS:
        return "blocks"
    if schema == "x.thread.v1":
        return "posts"
    if schema in {"xiaohongshu.image_note.v1", "bilibili.image_note.v1"}:
        return "cards"
    if schema == "douyin.spoken_script.v1":
        return "scenes"
    return None


def payload_hash(schema: str, value: object, *, asset_refs: object = None, evidence_refs: object = None) -> str:
    canonical = canonical_payload(schema, value, asset_refs=asset_refs, evidence_refs=evidence_refs)
    return hashlib.sha256(json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
