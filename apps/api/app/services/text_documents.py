"""Studio-owned Text v2 schema and deterministic projections, independent of TipTap."""

import hashlib
import json
import re
import unicodedata
from urllib.parse import urlsplit

DOCUMENT_SCHEMA = "studio.text.document.v1"
TEXT_PAYLOAD_SCHEMA = "text.master.v2"
TEXT_BLOCKS = {"heading", "paragraph", "quote", "callout"}
LIST_BLOCKS = {"bullet_list", "ordered_list"}
MEDIA_BLOCKS = {"image", "chart"}
MARK_ORDER = {"bold": 0, "italic": 1, "code": 2, "link": 3}


class TextDocumentError(ValueError):
    pass


def _fail(reason: str) -> None:
    raise TextDocumentError(reason)


def _object(value: object, allowed: set[str]) -> dict:
    if not isinstance(value, dict) or set(value) - allowed:
        _fail("invalid_or_unknown_document_fields")
    return value


def _string(value: object, limit: int, *, nonempty: bool = False) -> str:
    if not isinstance(value, str) or len(value) > limit or (nonempty and not value.strip()):
        _fail("invalid_document_string")
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeEncodeError:
        _fail("invalid_unicode_scalar")
    if any(ord(character) < 32 and character not in "\n\r\t" for character in value):
        _fail("document_control_character")
    return value


def _id(value: object) -> str:
    result = _string(value, 150, nonempty=True)
    if any(ord(char) < 32 for char in result):
        _fail("invalid_document_id")
    return result


def _positive(value: object) -> int:
    if type(value) is not int or value <= 0:
        _fail("invalid_exact_reference")
    return value


def _array(value: object, limit: int) -> list:
    if not isinstance(value, list) or len(value) > limit:
        _fail("document_collection_bound")
    return value


def _bounds(value: object) -> None:
    # Keep the shared outer bound; the document schema adds stricter field limits.
    from .production_modalities import validate_json_bounds

    try:
        errors = validate_json_bounds(value)
    except (UnicodeEncodeError, RecursionError, OverflowError):
        _fail("invalid_document_json")
    if errors:
        _fail(errors[0])


def _runs(value: object) -> list[dict]:
    normalized = []
    for item in _array(value, 1000):
        item = _object(item, {"text", "marks"})
        text = _string(item.get("text"), 20_000)
        marks, seen = [], set()
        for mark in _array(item.get("marks", []), 4):
            mark = _object(mark, {"type", "href"})
            kind = mark.get("type")
            if not isinstance(kind, str) or kind not in MARK_ORDER or kind in seen:
                _fail("invalid_or_duplicate_mark")
            seen.add(kind)
            canonical = {"type": kind}
            if kind == "link":
                href = _string(mark.get("href"), 1000, nonempty=True)
                try:
                    url = urlsplit(href)
                except ValueError:
                    _fail("invalid_link")
                if url.scheme.lower() not in {"http", "https"} or not url.hostname or any(c.isspace() or ord(c) < 32 for c in href):
                    _fail("invalid_link")
                canonical["href"] = href
            elif "href" in mark:
                _fail("mark_href_not_allowed")
            marks.append(canonical)
        marks.sort(key=lambda m: MARK_ORDER[m["type"]])
        if "code" in seen and any(c in text for c in "\r\n"):
            _fail("inline_code_newline_requires_code_block")
        if normalized and normalized[-1]["marks"] == marks:
            if len(normalized[-1]["text"]) + len(text) > 20_000:
                _fail("inline_text_bound")
            normalized[-1]["text"] += text
        elif text:
            normalized.append({"text": text, "marks": marks})
    return normalized


def _block(value: object) -> dict:
    if not isinstance(value, dict) or not isinstance(value.get("type"), str):
        _fail("invalid_document_block")
    kind = value["type"]
    extra = {"heading": {"level"}, "quote": {"attribution"}, "callout": {"tone"}}.get(kind, set())
    if kind in TEXT_BLOCKS:
        item = _object(value, {"id", "type", "content"} | extra)
        result = {"id": _id(item.get("id")), "type": kind, "content": _runs(item.get("content"))}
        if kind == "heading":
            if type(item.get("level")) is not int or not 1 <= item["level"] <= 4:
                _fail("invalid_heading_level")
            result["level"] = item["level"]
        if kind == "quote" and "attribution" in item:
            result["attribution"] = _string(item["attribution"], 1000)
        if kind == "callout":
            if not isinstance(item.get("tone"), str) or item["tone"] not in {"info", "note", "warning"}:
                _fail("invalid_callout_tone")
            result["tone"] = item["tone"]
        return result
    if kind in LIST_BLOCKS:
        item = _object(value, {"id", "type", "items"})
        items, seen = [], set()
        for entry in _array(item.get("items"), 1000):
            entry = _object(entry, {"id", "content"})
            item_id = _id(entry.get("id"))
            if item_id in seen:
                _fail("duplicate_list_item_id")
            seen.add(item_id)
            items.append({"id": item_id, "content": _runs(entry.get("content"))})
        if not items:
            _fail("empty_list")
        return {"id": _id(item.get("id")), "type": kind, "items": items}
    if kind == "code":
        item = _object(value, {"id", "type", "code", "language"})
        language = _string(item.get("language", ""), 50)
        if not re.fullmatch(r"[a-zA-Z0-9_+-]*", language):
            _fail("invalid_code_language")
        return {"id": _id(item.get("id")), "type": kind, "code": _string(item.get("code"), 200_000), "language": language}
    if kind in MEDIA_BLOCKS:
        item = _object(value, {"id", "type", "material_revision_id", "alt_text", "caption"})
        result = {"id": _id(item.get("id")), "type": kind, "material_revision_id": _positive(item.get("material_revision_id"))}
        for field in ("alt_text", "caption"):
            if field in item:
                result[field] = _string(item[field], 2000)
        return result
    if kind == "divider":
        item = _object(value, {"id", "type"})
        return {"id": _id(item.get("id")), "type": kind}
    _fail("unsupported_document_block")


def _target_text(document: dict, locator: dict) -> str:
    block = next((b for b in document["blocks"] if b["id"] == locator.get("block_id")), None)
    if block is None:
        _fail("citation_block_missing")
    if block["type"] in TEXT_BLOCKS and locator.get("list_item_id") is None:
        return "".join(run["text"] for run in block["content"])
    if block["type"] in LIST_BLOCKS and isinstance(locator.get("list_item_id"), str):
        item = next((i for i in block["items"] if i["id"] == locator["list_item_id"]), None)
        if item:
            return "".join(run["text"] for run in item["content"])
    _fail("citation_target_not_text")


def locator_text(document: dict, locator: dict) -> str:
    text = _target_text(document, locator)
    start, end = locator.get("start"), locator.get("end")
    if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(text):
        _fail("citation_range_invalid")
    return text[start:end]


def canonical_document(value: object) -> dict:
    _bounds(value)
    item = _object(value, {"schema", "blocks", "citations"})
    if item.get("schema") != DOCUMENT_SCHEMA:
        _fail("unsupported_text_document_schema")
    result = {"schema": DOCUMENT_SCHEMA, "blocks": [_block(b) for b in _array(item.get("blocks"), 1000)], "citations": []}
    ids = [b["id"] for b in result["blocks"]]
    if len(ids) != len(set(ids)):
        _fail("duplicate_block_id")
    seen = set()
    for use in _array(item.get("citations", []), 250):
        use = _object(use, {"id", "block_id", "list_item_id", "start", "end", "fact_pack_item_id", "selected_text_hash", "label"})
        citation_id = _id(use.get("id"))
        if citation_id in seen:
            _fail("duplicate_citation_id")
        seen.add(citation_id)
        canonical = {"id": citation_id, "block_id": _id(use.get("block_id")), "start": use.get("start"), "end": use.get("end"), "fact_pack_item_id": _positive(use.get("fact_pack_item_id"))}
        if "list_item_id" in use:
            canonical["list_item_id"] = _id(use["list_item_id"])
        selected = locator_text(result, canonical)
        checksum = hashlib.sha256(selected.encode()).hexdigest()
        if use.get("selected_text_hash") != checksum:
            _fail("citation_selected_text_changed")
        canonical["selected_text_hash"] = checksum
        if "label" in use:
            canonical["label"] = _string(use["label"], 200)
        result["citations"].append(canonical)
    _bounds(result)
    return result


def canonical_payload(value: object) -> dict:
    _bounds(value)
    item = _object(value, {"title", "document"})
    return {"title": _string(item.get("title", ""), 500), "document": canonical_document(item.get("document"))}


def proposal_response_schema(candidate_count: int) -> dict:
    """Expose the existing editable truth to models, not an editor-specific JSON dialect."""
    if type(candidate_count) is not int or not 1 <= candidate_count <= 5:
        _fail("invalid_proposal_candidate_count")

    def obj(properties, required):
        return {"type": "object", "additionalProperties": False, "properties": properties, "required": required}

    def array(items, maximum=256, minimum=0):
        return {"type": "array", "items": items, "minItems": minimum, "maxItems": maximum}

    def string(maximum, minimum=0):
        return {"type": "string", "minLength": minimum, "maxLength": maximum}

    identifier, positive = string(150, 1), {"type": "integer", "minimum": 1}
    checksum = {"type": "string", "pattern": "^[a-f0-9]{64}$"}
    reference = lambda name: {"$ref": f"#/$defs/{name}"}
    content = array(reference("run"))
    blocks = []
    for kind in sorted(TEXT_BLOCKS):
        fields = {"id": identifier, "type": {"const": kind}, "content": content}
        required = ["id", "type", "content"]
        if kind == "heading":
            fields["level"] = {"type": "integer", "minimum": 1, "maximum": 4}
            required.append("level")
        elif kind == "quote":
            fields["attribution"] = string(1000)
        elif kind == "callout":
            fields["tone"] = {"enum": ["info", "note", "warning"]}
            required.append("tone")
        blocks.append(obj(fields, required))
    for kind in sorted(LIST_BLOCKS):
        blocks.append(obj({"id": identifier, "type": {"const": kind},
            "items": array(reference("list_item"), minimum=1)},
            ["id", "type", "items"]))
    for kind in sorted(MEDIA_BLOCKS):
        blocks.append(obj({"id": identifier, "type": {"const": kind}, "material_revision_id": positive,
            "alt_text": string(2000), "caption": string(2000)}, ["id", "type", "material_revision_id"]))
    blocks.extend([
        obj({"id": identifier, "type": {"const": "code"}, "code": string(200_000),
            "language": {**string(50), "pattern": "^[a-zA-Z0-9_+-]*$"}}, ["id", "type", "code"]),
        obj({"id": identifier, "type": {"const": "divider"}}, ["id", "type"]),
    ])
    range_fields = {"block_id": identifier, "list_item_id": identifier,
        "start": {"type": "integer", "minimum": 0}, "end": positive, "selected_text_hash": checksum}
    range_required = ["block_id", "start", "end", "selected_text_hash"]
    order = {"type": "integer", "minimum": 0, "maximum": 2147483647}
    defs = {
        "plain_mark": obj({"type": {"enum": ["bold", "italic", "code"]}}, ["type"]),
        "link_mark": obj({"type": {"const": "link"}, "href": {**string(1000, 1), "pattern": "^https?://"}},
            ["type", "href"]),
        "mark": {"oneOf": [reference("plain_mark"), reference("link_mark")]},
        "run": obj({"text": string(20_000), "marks": array(reference("mark"), 4)}, ["text"]),
        "list_item": obj({"id": identifier, "content": content}, ["id", "content"]),
        "block": {"oneOf": [reference(f"block_{index}") for index in range(len(blocks))]},
        **{f"block_{index}": block for index, block in enumerate(blocks)},
        "citation": obj({"id": identifier, **range_fields, "fact_pack_item_id": positive, "label": string(200)},
            ["id", "fact_pack_item_id", *range_required]),
        "citation_selection": obj({"id": identifier, "block_id": identifier, "list_item_id": identifier,
            "quote": string(20_000, 1), "fact_pack_item_id": positive, "label": string(200)},
            ["id", "block_id", "quote", "fact_pack_item_id"]),
        "asset_ref": obj({"material_revision_id": positive, "content_hash": checksum,
            "role": string(40, 1), "slot_key": {"type": ["string", "null"], "maxLength": 100},
            "sort_order": order, "placement": {"type": "object"}}, ["material_revision_id", "content_hash"]),
        "evidence_ref": obj({"fact_pack_item_id": positive, "snapshot_checksum": checksum,
            "role": string(40, 1), "sort_order": order, "locator": reference("locator")},
            ["fact_pack_item_id", "snapshot_checksum", "locator"]),
        "locator": obj({"citation_id": identifier, **range_fields}, ["citation_id", *range_required]),
        "document": obj({"schema": {"const": DOCUMENT_SCHEMA}, "blocks": array(reference("block")),
            "citations": array(reference("citation"), 250)}, ["schema", "blocks"]),
        "payload": obj({"title": string(500), "document": reference("document")}, ["title", "document"]),
    }
    candidate = obj({"payload_schema": {"const": TEXT_PAYLOAD_SCHEMA}, "payload": reference("payload"),
        "asset_refs": array(reference("asset_ref"), 250), "evidence_refs": array(reference("evidence_ref"), 250),
        "citation_selections": array(reference("citation_selection"), 250)},
        ["payload_schema", "payload"])
    defs["candidate"] = candidate
    return {**obj({"schema": {"const": "stage.master.proposal.v1"},
        "candidates": array(reference("candidate"), candidate_count, candidate_count)}, ["candidates"]), "$defs": defs}


def resolve_proposal_citations(value: dict, selections: list, evidence_catalog: list) -> tuple[dict, list]:
    """Models select words; the service proves locators and hashes without repairing invalid citations."""
    _bounds(selections)
    payload = canonical_payload(value)
    document = payload["document"]
    if document["citations"]:
        _fail("mixed_proposal_citation_forms")
    supplied = {item["item_id"]: item["checksum"] for item in evidence_catalog}
    refs = []
    for index, raw in enumerate(_array(selections, 250)):
        item = _object(raw, {"id", "block_id", "list_item_id", "quote", "fact_pack_item_id", "label"})
        citation_id, block_id = _id(item.get("id")), _id(item.get("block_id"))
        fact_id = _positive(item.get("fact_pack_item_id"))
        checksum = supplied.get(fact_id)
        if not isinstance(checksum, str) or not re.fullmatch(r"[a-f0-9]{64}", checksum):
            _fail("foreign_proposal_citation")
        locator = {"block_id": block_id}
        if "list_item_id" in item:
            locator["list_item_id"] = _id(item["list_item_id"])
        quote = _string(item.get("quote"), 20_000, nonempty=True)
        text = _target_text(document, locator)
        start = text.find(quote)
        if start < 0 or text.find(quote, start + 1) >= 0:
            _fail("missing_or_ambiguous_proposal_citation")
        locator.update(start=start, end=start + len(quote), selected_text_hash=hashlib.sha256(quote.encode()).hexdigest())
        citation = {"id": citation_id, **locator, "fact_pack_item_id": fact_id}
        if "label" in item:
            citation["label"] = _string(item["label"], 200)
        document["citations"].append(citation)
        refs.append({"fact_pack_item_id": fact_id, "snapshot_checksum": checksum, "role": "claim",
                     "sort_order": index, "locator": {"citation_id": citation_id, **locator}})
    return canonical_payload(payload), refs


def _heading_text(block: dict) -> str:
    return "".join(run["text"] for run in block.get("content") or [] if isinstance(run, dict) and isinstance(run.get("text"), str))


def normalize_text_structure(blocks: list, title: str = "") -> list:
    """Apply the editorial heading rule without rewriting prose or inventing blocks.

    A leading heading that repeats the title is removed. A heading with no body
    of its own (it is last, or the next block is also a heading) is removed.
    Remaining headings start at level 2 and never skip a level.
    """
    title_text = title.strip() if isinstance(title, str) else ""
    pending = list(blocks)
    if (pending and isinstance(pending[0], dict) and pending[0].get("type") == "heading"
            and title_text and _heading_text(pending[0]).strip() == title_text):
        pending = pending[1:]
    kept = []
    for index, block in enumerate(pending):
        if isinstance(block, dict) and block.get("type") == "heading":
            nxt = pending[index + 1] if index + 1 < len(pending) else None
            if nxt is None or (isinstance(nxt, dict) and nxt.get("type") == "heading"):
                continue
        kept.append(block)
    levels = [block["level"] for block in kept if isinstance(block, dict) and block.get("type") == "heading" and type(block.get("level")) is int and 1 <= block["level"] <= 4]
    if not levels:
        return kept
    delta = 2 - min(levels)
    previous = 1
    result = []
    for block in kept:
        if isinstance(block, dict) and block.get("type") == "heading" and type(block.get("level")) is int and 1 <= block["level"] <= 4:
            level = block["level"] + delta
            if level > previous + 1:
                level = previous + 1
            if level < 2:
                level = 2
            if level > 4:
                level = 4
            previous = level
            if level != block["level"]:
                block = {**block, "level": level}
        result.append(block)
    return result


def convert_legacy_text(source: dict, *, asset_refs: list | None = None, evidence_refs: list | None = None) -> dict:
    """Convert proven legacy inputs without trusting layout JSON as editable truth."""
    _bounds(source)
    if not isinstance(source.get("markdown"), str):
        _fail("legacy_body_required")
    body = _string(source["markdown"], 500_000)
    assets = _array(asset_refs or [], 250)
    evidence = _array(evidence_refs or [], 250)
    _bounds(assets)
    _bounds(evidence)
    warnings, blocks = [], []

    def warn(code: str, **fields) -> None:
        value = {"code": code, **fields}
        if value not in warnings:
            warnings.append(value)

    unique_assets = {}
    for ref in assets:
        revision_id = _positive(ref.get("material_revision_id"))
        if revision_id in unique_assets:
            if ref.get("content_hash") != unique_assets[revision_id].get("content_hash"):
                _fail("conflicting_legacy_asset_hash")
            warn("duplicate_legacy_asset_normalized", material_revision_id=revision_id)
        else:
            unique_assets[revision_id] = ref
    assets = list(unique_assets.values())

    def inline(text: str) -> list:
        # Unsupported/nested markup stays literal, rather than guessing its meaning.
        if re.search(r"&(?:#[xX]?[0-9a-fA-F]+|[a-zA-Z]+);| {2,}\n|\r|~~", text):
            warn("unsupported_inline_preserved")
            return [{"text": text, "marks": []}]
        pattern = r"(\*\*([^*\n]+)\*\*|\*([^*\n]+)\*|`([^`\n]+)`|\[([^\[\]\n]+)\]\((https?://[^\s()]+)\))"
        result, offset = [], 0
        uncertain = False
        for match in re.finditer(pattern, text):
            if match.start() > offset:
                literal = text[offset:match.start()]
                if re.search(r"[*`_\[\]\\]", literal):
                    uncertain = True
                result.append({"text": literal, "marks": []})
            value = next(v for v in match.groups()[1:5] if v is not None)
            kind = "bold" if match.group(2) is not None else "italic" if match.group(3) is not None else "code" if match.group(4) is not None else "link"
            before = text[match.start() - 1] if match.start() else " "
            after = text[match.end()] if match.end() < len(text) else " "
            if kind in {"bold", "italic"}:
                punct = lambda character: unicodedata.category(character)[0] in "PS"
                left = not value[0].isspace() and (not punct(value[0]) or before.isspace() or punct(before))
                right = not value[-1].isspace() and (not punct(value[-1]) or after.isspace() or punct(after))
                if not left or not right or re.search(r"[*`_\[\]\\]", value):
                    uncertain = True
            if kind == "code":
                if before == "`" or after == "`":
                    uncertain = True
                if value.startswith(" ") and value.endswith(" ") and value.strip(" "):
                    value = value[1:-1]
            mark = {"type": kind}
            if kind == "link":
                mark["href"] = match.group(6)
                if re.search(r"[*`_\[\]\\]", value):
                    uncertain = True
            result.append({"text": value, "marks": [mark]})
            offset = match.end()
        literal = text[offset:]
        if literal:
            if re.search(r"[*`_\[\]\\]", literal):
                uncertain = True
            result.append({"text": literal, "marks": []})
        if uncertain:
            warn("unsupported_inline_preserved")
            return [{"text": text, "marks": []}]
        return result

    def append(kind: str, **fields) -> None:
        blocks.append({"id": f"legacy-b{len(blocks) + 1}", "type": kind, **fields})
        if len(blocks) > 1000:
            _fail("document_collection_bound")

    def parse(markdown: str) -> None:
        lines, index = markdown.split("\n"), 0
        while index < len(lines):
            line = lines[index]
            if not line.strip():
                index += 1
                continue
            fence = re.fullmatch(r"(`{3,}|~{3,})([a-zA-Z0-9_+-]*)", line)
            if fence:
                end = next((n for n in range(index + 1, len(lines)) if re.fullmatch(re.escape(fence[1][0]) + "{" + str(len(fence[1])) + ",}\\s*", lines[n])), None)
                if end is not None:
                    append("code", code="\n".join(lines[index + 1:end]), language=fence[2])
                    index = end + 1
                    continue
                warn("unclosed_code_preserved")
                append("paragraph", content=[{"text": "\n".join(lines[index:]), "marks": []}])
                break
            if re.fullmatch(r"#{1,4} .+", line):
                prefix, text = line.split(" ", 1)
                if re.search(r"\s#+\s*$", text):
                    warn("unsupported_block_preserved")
                    append("paragraph", content=[{"text": line, "marks": []}])
                else:
                    append("heading", level=len(prefix), content=inline(text))
                index += 1
                continue
            if re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", line):
                append("divider")
                index += 1
                continue
            list_match = re.fullmatch(r"(- |\* |[0-9]{1,9}\. )(.+)", line)
            if list_match:
                ordered = list_match[1][0].isdigit()
                entries, start = [], index
                while index < len(lines):
                    entry = re.fullmatch(r"([0-9]{1,9}\. )(.+)" if ordered else r"([-*] )(.+)", lines[index])
                    if not entry:
                        break
                    if ordered and int(entry[1].split(".")[0]) != len(entries) + 1:
                        warn("ordered_list_numbering_normalized")
                    if not ordered and entry[1] != list_match[1]:
                        warn("list_marker_normalized")
                    entries.append({"id": f"legacy-i{index - start + 1}", "content": inline(entry[2])})
                    index += 1
                append("ordered_list" if ordered else "bullet_list", items=entries)
                if index < len(lines) and lines[index].strip() and not re.match(r"^(#{1,4} |[-*] |\d+\. |> |`{3,}|~{3,})", lines[index]):
                    warn("legacy_container_layout_normalized")
                continue
            if line.startswith("> ") and not line.startswith("> >"):
                quotes = []
                while index < len(lines) and lines[index].startswith("> ") and not lines[index].startswith("> >"):
                    quotes.append(lines[index][2:])
                    index += 1
                append("quote", content=inline("\n".join(quotes)))
                if index < len(lines) and lines[index].strip() and not re.match(r"^(#{1,4} |[-*] |\d+\. |> |`{3,}|~{3,})", lines[index]):
                    warn("legacy_container_layout_normalized")
                continue
            start = index
            index += 1
            while index < len(lines) and lines[index].strip() and not re.match(r"^(#{1,4} |[-*] |\d+\. |> |`{3,}|~{3,})", lines[index]):
                index += 1
            text = "\n".join(lines[start:index])
            if re.search(r"(^|\n)(?:\s{2,}\S|#{5,}|[|]|`{3,}|~{3,}|\+ |\d+\. |[=-]{2,}[ \t]*(?:\n|$))|[<>]|!\[", text):
                warn("unsupported_block_preserved")
                append("paragraph", content=[{"text": text, "marks": []}])
            else:
                append("paragraph", content=inline(text))

    layout = source.get("document")
    hints = layout.get("blocks") if isinstance(layout, dict) and layout.get("schema_version") == 1 else None
    paragraphs = [chunk for chunk in re.split(r"\n[ \t]*\n", body) if chunk.strip()]
    equivalent = isinstance(hints, list) and all(isinstance(b, dict) and b.get("type") in {"paragraph", "image", "chart"} for b in hints) and [b.get("text") for b in hints if b.get("type") == "paragraph"] == paragraphs
    declared = {item.get("material_revision_id"): item for item in assets}
    if equivalent:
        for number, hint in enumerate(hints):
            if hint["type"] == "paragraph":
                parse(hint["text"])
            elif type(hint.get("material_revision_id")) is int and hint["material_revision_id"] in declared:
                append(hint["type"], material_revision_id=hint["material_revision_id"], alt_text=hint.get("alt", ""), caption=hint.get("caption", ""))
            else:
                warn("unmapped_media_hint", hint_index=number)
    else:
        if layout:
            warn("legacy_document_not_equivalent")
        parse(body)
    blocks = normalize_text_structure(blocks, source["title"] if isinstance(source.get("title"), str) else "")
    document = canonical_document({"schema": DOCUMENT_SCHEMA, "blocks": blocks, "citations": []})
    mapped = []
    for number, ref in enumerate(evidence):
        locator = ref.get("locator") or {}
        selected = locator.get("text")
        matches = []
        if isinstance(selected, str) and selected:
            for segment in text_map(document)["segments"]:
                if segment["block_type"] not in TEXT_BLOCKS | LIST_BLOCKS:
                    continue
                for match in re.finditer("(?=" + re.escape(selected) + ")", segment["text"]):
                    matches.append({"block_id": segment["block_id"], **({"list_item_id": segment["list_item_id"]} if segment.get("list_item_id") else {}), "start": match.start(), "end": match.start() + len(selected)})
                    if len(matches) > 1:
                        break
                if len(matches) > 1:
                    break
        if len(matches) != 1:
            warn("unmapped_evidence_locator", reference_index=number)
            continue
        citation = {"id": f"legacy-c{number + 1}", **matches[0], "fact_pack_item_id": ref.get("fact_pack_item_id"), "selected_text_hash": hashlib.sha256(selected.encode()).hexdigest()}
        document["citations"].append(citation)
        mapped.append({**ref, "locator": {"citation_id": citation["id"], **matches[0], "selected_text_hash": citation["selected_text_hash"]}})
    payload = canonical_payload({"title": source.get("title", ""), "document": document})
    unused = validate_references(payload, assets, mapped)["unused_asset_ids"]
    if unused:
        warn("unused_legacy_assets", material_revision_ids=unused)
    return {"payload": payload, "asset_refs": assets, "evidence_refs": mapped, "warnings": warnings, "document_hash": document_hash(payload["document"])}


def document_hash(document: dict) -> str:
    return hashlib.sha256(json.dumps(canonical_document(document), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def plain_text(document: dict) -> str:
    return text_map(document)["text"]


def text_map(document: dict) -> dict:
    blocks = canonical_document(document)["blocks"]
    segments, offset = [], 0
    for block in blocks:
        parts = []
        if block["type"] in TEXT_BLOCKS:
            parts.append({"text": "".join(r["text"] for r in block["content"])})
        elif block["type"] in LIST_BLOCKS:
            parts.extend({"text": "".join(r["text"] for r in item["content"]), "list_item_id": item["id"]} for item in block["items"])
        elif block["type"] == "code":
            parts.append({"text": block["code"]})
        for part in parts:
            start = offset + (1 if segments else 0)
            offset = start + len(part["text"])
            segments.append({"block_id": block["id"], "block_type": block["type"], **part, "start": start, "end": offset})
    return {"text": "\n".join(part["text"] for part in segments), "segments": segments, "offset_unit": "unicode_code_point"}


def validate_references(payload: dict, assets: list[dict], evidence: list[dict]) -> dict:
    document = canonical_payload(payload)["document"]
    _bounds({"assets": assets, "evidence": evidence})
    asset_ids, declarations = set(), {}
    for ref in _array(assets, 250):
        if not isinstance(ref, dict):
            _fail("invalid_asset_reference")
        revision_id = _positive(ref.get("material_revision_id"))
        if revision_id in declarations:
            _fail("duplicate_asset_declaration")
        declarations[revision_id] = ref
        if not isinstance(ref.get("content_hash"), str) or len(ref["content_hash"]) != 64:
            _fail("invalid_asset_hash")
    for block in document["blocks"]:
        if block["type"] in MEDIA_BLOCKS:
            revision_id = block["material_revision_id"]
            if revision_id not in declarations:
                _fail("undeclared_document_asset")
            asset_ids.add(revision_id)
    uses = {}
    for ref in _array(evidence, 250):
        if not isinstance(ref, dict) or not isinstance(ref.get("locator"), dict):
            _fail("invalid_evidence_use")
        _positive(ref.get("fact_pack_item_id"))
        if any(type(ref["locator"].get(key)) is not int for key in ("start", "end")):
            _fail("invalid_evidence_range_type")
        use_id = ref["locator"].get("citation_id")
        if not isinstance(use_id, str) or use_id in uses:
            _fail("duplicate_or_invalid_evidence_use")
        uses[use_id] = ref
    for citation in document["citations"]:
        ref = uses.pop(citation["id"], None)
        locator = {"citation_id": citation["id"], **{k: citation[k] for k in ("block_id", "start", "end", "selected_text_hash")}}
        if "list_item_id" in citation:
            locator["list_item_id"] = citation["list_item_id"]
        if ref is None or ref.get("fact_pack_item_id") != citation["fact_pack_item_id"] or ref["locator"] != locator or not isinstance(ref.get("snapshot_checksum"), str) or len(ref["snapshot_checksum"]) != 64:
            _fail("citation_evidence_mismatch")
    if uses:
        _fail("unused_evidence_locator")
    return {"unused_asset_ids": sorted(set(declarations) - asset_ids)}


def _escape(text: str) -> str:
    return re.sub(r"([\\`*_{}\[\]<>!#|~+.&-])", r"\\\1", text)


def _formatted(text: str, marks: list[dict], *, html_emphasis: bool = False) -> str:
    code = any(m["type"] == "code" for m in marks)
    leading, trailing = "", ""
    if not code and any(m["type"] in {"bold", "italic"} for m in marks):
        core = text.strip()
        if not core:
            return text
        leading = text[:len(text) - len(text.lstrip())]
        trailing = text[len(text.rstrip()):]
        text = core
    # CommonMark emphasis cannot flank some punctuation without changing the text.
    html_emphasis = html_emphasis or bool(text and any(unicodedata.category(char)[0] in {"P", "S"} for char in (text[0], text[-1])))
    if code:
        delimiter = "`" * (max((len(x) for x in re.findall(r"`+", text)), default=0) + 1)
        padding = " " if text.strip(" ") and (text.startswith(("`", " ")) or text.endswith(("`", " "))) else ""
        rendered = delimiter + padding + text + padding + delimiter
    else:
        rendered = _escape(text)
    for mark in marks:
        if mark["type"] == "bold":
            rendered = f"<strong>{rendered}</strong>" if html_emphasis else f"**{rendered}**"
        elif mark["type"] == "italic":
            rendered = f"<em>{rendered}</em>" if html_emphasis else f"*{rendered}*"
        elif mark["type"] == "link":
            href = mark["href"].replace("&", "&amp;").replace("(", "%28").replace(")", "%29").replace("<", "%3C").replace(">", "%3E").replace('"', "%22").replace("\\", "%5C")
            rendered = f"[{rendered}]({href})"
    return leading + rendered + trailing


def _inline(runs: list[dict], citations: list[tuple[dict, int]]) -> str:
    markers = {}
    for citation, label in citations:
        markers.setdefault(citation["end"], []).append(f"\\[{label}\\]")
    pieces, offset = [], 0
    for index, run in enumerate(runs):
        neighbors = [runs[i] for i in (index - 1, index + 1) if 0 <= i < len(runs)]
        adjacent_emphasis = any(any(mark["type"] in {"bold", "italic"} for mark in other["marks"]) for other in neighbors)
        end = offset + len(run["text"])
        cursor = offset
        for stop in sorted(position for position in markers if offset < position <= end):
            pieces.append(_formatted(run["text"][cursor - offset:stop - offset], run["marks"], html_emphasis=adjacent_emphasis))
            pieces.extend(markers[stop])
            cursor = stop
        if cursor < end:
            pieces.append(_formatted(run["text"][cursor - offset:], run["marks"], html_emphasis=adjacent_emphasis))
        offset = end
    return "".join(pieces)


def render_markdown(document: dict, *, media_paths: dict[int, str] | None = None) -> str:
    document = canonical_document(document)
    media_paths = media_paths or {}
    paragraphs = []
    for block in document["blocks"]:
        kind = block["type"]
        citations = [(c, index + 1) for index, c in enumerate(document["citations"]) if c["block_id"] == block["id"]]
        if kind in TEXT_BLOCKS:
            body = _inline(block["content"], citations)
            if kind == "heading":
                body = "#" * block["level"] + " " + body
            elif kind in {"quote", "callout"}:
                if kind == "callout":
                    body = f"[{block['tone'].upper()}]\n" + body
                if block.get("attribution"):
                    body += "\n— " + _escape(block["attribution"])
                body = "\n".join("> " + line for line in body.split("\n"))
            paragraphs.append(body)
        elif kind in LIST_BLOCKS:
            rows = []
            for index, item in enumerate(block["items"]):
                body = _inline(item["content"], [(c, n) for c, n in citations if c.get("list_item_id") == item["id"]])
                prefix = "- " if kind == "bullet_list" else f"{index + 1}. "
                rows.append(prefix + body.replace("\n", "\n" + " " * len(prefix)))
            paragraphs.append("\n".join(rows))
        elif kind == "code":
            fence = "`" * max(3, max((len(x) for x in re.findall(r"`+", block["code"])), default=0) + 1)
            paragraphs.append(f"{fence}{block['language']}\n{block['code']}\n{fence}")
        elif kind in MEDIA_BLOCKS:
            revision_id = block["material_revision_id"]
            path = media_paths.get(revision_id)
            if not isinstance(path, str) or not re.fullmatch(rf"media/[0-9]{{2,3}}-{revision_id}\.(png|jpg|webp|gif)", path):
                _fail("render_media_mapping_missing_or_invalid")
            body = f"![{_escape(block.get('alt_text', ''))}]({path})"
            if block.get("caption"):
                body += "\n\n" + _escape(block["caption"])
            paragraphs.append(body)
        elif kind == "divider":
            paragraphs.append("---")
    return "\n\n".join(paragraphs)
