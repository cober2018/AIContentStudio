"""Bounded, deterministic durable payloads for the first five F6E forms."""

import hashlib
import json
import re
import unicodedata


class VariantDocumentError(ValueError):
    pass


_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,99}$")
_HASH = re.compile(r"^[0-9a-f]{64}$")


def _fail(reason: str) -> None:
    raise VariantDocumentError(reason)


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
    elif schema == "x.single.v1":
        item = _object(value, {"text"} | common)
        result = {"text": _text(item.get("text"), 280, required=True)}
        locations["single"] = result["text"]
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


def payload_hash(schema: str, value: object, *, asset_refs: object = None, evidence_refs: object = None) -> str:
    canonical = canonical_payload(schema, value, asset_refs=asset_refs, evidence_refs=evidence_refs)
    return hashlib.sha256(json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
