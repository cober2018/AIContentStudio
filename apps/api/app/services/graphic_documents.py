"""Canonical, editor-independent Graphic Master v2 document contract."""

import hashlib
import json
import math
import re


class GraphicDocumentError(ValueError):
    pass


_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,99}$")
_COLOR = re.compile(r"^#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?$")
_MAX_CANVASES = 24
_MAX_LAYERS = 128
_MAX_RUNS = 100
_MAX_TEXT = 10_000


def _fail(code: str) -> None:
    raise GraphicDocumentError(code)


def _object(value: object, allowed: set[str], code: str) -> dict:
    if not isinstance(value, dict):
        _fail(code)
    if set(value) - allowed:
        _fail("graphic_field_unknown")
    return value


def _id(value: object, code: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        _fail(code)
    return value


def _number(value: object, *, minimum: float, maximum: float, code: str) -> int | float:
    if type(value) not in (int, float) or not math.isfinite(value) or not minimum <= value <= maximum:
        _fail(code)
    return value


def _order(value: object, code: str) -> int:
    if type(value) is not int or value < 0:
        _fail(code)
    return value


def _color(value: object, code: str) -> str:
    if not isinstance(value, str) or not _COLOR.fullmatch(value):
        _fail(code)
    return value.lower()


def _ordered(items: object, *, limit: int, kind: str) -> list[dict]:
    if not isinstance(items, list) or len(items) > limit:
        _fail(f"graphic_{kind}_count_invalid")
    ids: set[str] = set()
    orders: set[int] = set()
    for item in items:
        if not isinstance(item, dict):
            _fail(f"graphic_{kind}_invalid")
        item_id = _id(item.get("id"), f"graphic_{kind}_id_invalid")
        if item_id in ids:
            _fail(f"graphic_{kind}_duplicate_id")
        ids.add(item_id)
        order = _order(item.get("order"), f"graphic_{kind}_order_invalid")
        if order in orders:
            _fail(f"graphic_{kind}_order_invalid")
        orders.add(order)
    if orders != set(range(len(items))):
        _fail(f"graphic_{kind}_order_invalid")
    return sorted(items, key=lambda item: item["order"])


def _style(raw: object) -> dict:
    if isinstance(raw, dict) and set(raw) - {"font_size", "color", "weight", "italic", "align"}:
        _fail("graphic_style_invalid")
    value = _object(raw, {"font_size", "color", "weight", "italic", "align"}, "graphic_style_invalid")
    size = _number(value.get("font_size"), minimum=1, maximum=256, code="graphic_style_invalid")
    color = _color(value.get("color"), "graphic_style_invalid")
    weight = value.get("weight", 400)
    if type(weight) is not int or weight not in range(100, 1000, 100):
        _fail("graphic_style_invalid")
    italic = value.get("italic", False)
    align = value.get("align", "left")
    if type(italic) is not bool or not isinstance(align, str) or align not in {"left", "center", "right"}:
        _fail("graphic_style_invalid")
    return {"font_size": size, "color": color, "weight": weight, "italic": italic, "align": align}


def _layer(raw: dict) -> dict:
    kind = raw.get("type")
    if not isinstance(kind, str) or kind not in {"text", "image", "chart", "shape"}:
        _fail("graphic_layer_type_invalid")
    common = {"id", "order", "type", "x", "y", "width", "height", "rotation", "opacity", "visible", "locked"}
    specific = {
        "text": {"runs", "claims"},
        "image": {"material_revision_id", "fit", "crop", "focal"},
        "chart": {"material_revision_id", "fit", "crop", "focal"},
        "shape": {"shape", "fill", "stroke", "stroke_width"},
    }
    _object(raw, common | specific[kind], "graphic_layer_invalid")
    result = {
        "id": _id(raw.get("id"), "graphic_layer_id_invalid"),
        "order": _order(raw.get("order"), "graphic_layer_order_invalid"),
        "type": kind,
        "x": _number(raw.get("x"), minimum=-8192, maximum=8192, code="graphic_geometry_invalid"),
        "y": _number(raw.get("y"), minimum=-8192, maximum=8192, code="graphic_geometry_invalid"),
        "width": _number(raw.get("width"), minimum=1, maximum=8192, code="graphic_geometry_invalid"),
        "height": _number(raw.get("height"), minimum=1, maximum=8192, code="graphic_geometry_invalid"),
        "rotation": _number(raw.get("rotation", 0), minimum=-360, maximum=360, code="graphic_geometry_invalid"),
        "opacity": _number(raw.get("opacity", 1), minimum=0, maximum=1, code="graphic_geometry_invalid"),
    }
    for flag, default in (("visible", True), ("locked", False)):
        value = raw.get(flag, default)
        if type(value) is not bool:
            _fail("graphic_layer_flag_invalid")
        result[flag] = value
    if kind == "text":
        runs = raw.get("runs")
        if not isinstance(runs, list) or not 1 <= len(runs) <= _MAX_RUNS:
            _fail("graphic_text_runs_invalid")
        total = 0
        normalized = []
        for raw_run in runs:
            run = _object(raw_run, {"text", "style"}, "graphic_text_run_invalid")
            content = run.get("text")
            if not isinstance(content, str):
                _fail("graphic_text_run_invalid")
            total += len(content)
            normalized.append({"text": content, "style": _style(run.get("style"))})
        if total > _MAX_TEXT:
            _fail("graphic_text_too_long")
        result["runs"] = normalized
        claims = raw.get("claims", [])
        if not isinstance(claims, list) or len(claims) > 100:
            _fail("graphic_claim_count_invalid")
        normalized_claims = []
        seen_claims = set()
        for raw_claim in claims:
            claim = _object(raw_claim, {"fact_pack_item_id", "snapshot_checksum", "start", "end"}, "graphic_claim_invalid")
            fact_id = claim.get("fact_pack_item_id")
            checksum = claim.get("snapshot_checksum")
            start, end = claim.get("start"), claim.get("end")
            if type(fact_id) is not int or fact_id <= 0 or not isinstance(checksum, str) or len(checksum) != 64:
                _fail("graphic_claim_invalid")
            if type(start) is not int or type(end) is not int or not 0 <= start < end <= total:
                _fail("graphic_claim_range_invalid")
            key = (fact_id, checksum, start, end)
            if key in seen_claims:
                _fail("graphic_claim_duplicate")
            seen_claims.add(key)
            normalized_claims.append({"fact_pack_item_id": fact_id, "snapshot_checksum": checksum, "start": start, "end": end})
        result["claims"] = sorted(normalized_claims, key=lambda item: (item["start"], item["end"], item["fact_pack_item_id"]))
    elif kind in {"image", "chart"}:
        revision_id = raw.get("material_revision_id")
        if type(revision_id) is not int or revision_id <= 0:
            _fail("graphic_media_revision_invalid")
        fit = raw.get("fit", "cover")
        if not isinstance(fit, str) or fit not in {"cover", "contain", "fill"}:
            _fail("graphic_media_fit_invalid")
        result.update({"material_revision_id": revision_id, "fit": fit})
        for field in ("crop", "focal"):
            if field in raw:
                value = _object(raw[field], {"x", "y", "width", "height"} if field == "crop" else {"x", "y"}, "graphic_media_placement_invalid")
                required = ("x", "y", "width", "height") if field == "crop" else ("x", "y")
                result[field] = {key: _number(value.get(key), minimum=0, maximum=1, code="graphic_media_placement_invalid") for key in required}
                if field == "crop" and (result[field]["width"] == 0 or result[field]["height"] == 0 or result[field]["x"] + result[field]["width"] > 1 or result[field]["y"] + result[field]["height"] > 1):
                    _fail("graphic_media_placement_invalid")
    else:
        shape = raw.get("shape")
        if not isinstance(shape, str) or shape not in {"rectangle", "ellipse", "line"}:
            _fail("graphic_shape_invalid")
        result["shape"] = shape
        result["fill"] = _color(raw.get("fill", "#00000000"), "graphic_shape_invalid")
        if "stroke" in raw:
            result["stroke"] = _color(raw["stroke"], "graphic_shape_invalid")
        result["stroke_width"] = _number(raw.get("stroke_width", 0), minimum=0, maximum=100, code="graphic_shape_invalid")
    return result


def canonical_payload(raw: object) -> dict:
    payload = _object(raw, {"title", "canvases", "render_asset_ref"}, "graphic_payload_invalid")
    title = payload.get("title", "")
    if not isinstance(title, str) or len(title) > 500:
        _fail("graphic_title_invalid")
    canvases = _ordered(payload.get("canvases"), limit=_MAX_CANVASES, kind="canvas")
    if not canvases:
        _fail("graphic_canvas_required")
    normalized = []
    all_ids = {item["id"] for item in canvases}
    variants = {item["id"]: item.get("variant_of_canvas_id") for item in canvases}
    for canvas_id in all_ids:
        seen = {canvas_id}
        source_id = variants[canvas_id]
        while source_id is not None:
            if not isinstance(source_id, str) or source_id not in all_ids or source_id in seen:
                _fail("graphic_variant_source_invalid")
            seen.add(source_id)
            source_id = variants[source_id]
    for index, raw_canvas in enumerate(canvases):
        canvas = _object(raw_canvas, {"id", "order", "width", "height", "background", "layers", "variant_of_canvas_id", "role"}, "graphic_canvas_invalid")
        variant = canvas.get("variant_of_canvas_id")
        background = _object(canvas.get("background"), {"color"}, "graphic_background_invalid")
        layers = _ordered(canvas.get("layers"), limit=_MAX_LAYERS, kind="layer")
        output = {
            "id": canvas["id"],
            "order": index,
            "width": _number(canvas.get("width"), minimum=1, maximum=8192, code="graphic_canvas_size_invalid"),
            "height": _number(canvas.get("height"), minimum=1, maximum=8192, code="graphic_canvas_size_invalid"),
            "background": {"color": _color(background.get("color"), "graphic_background_invalid")},
            "layers": [_layer(layer) for layer in layers],
        }
        if variant is not None:
            output["variant_of_canvas_id"] = variant
        if "role" in canvas:
            if canvas["role"] not in ("cover", "body"):
                _fail("graphic_canvas_role_invalid")
            output["role"] = canvas["role"]
        normalized.append(output)
    result = {"title": title, "canvases": normalized}
    if "render_asset_ref" in payload:
        declarations = payload["render_asset_ref"]
        if not isinstance(declarations, list) or len(declarations) > _MAX_CANVASES:
            _fail("graphic_render_ref_invalid")
        result["render_asset_ref"] = [
            {"canvas_id": _id(item.get("canvas_id"), "graphic_render_ref_invalid"), "material_revision_id": item.get("material_revision_id")}
            for item in declarations
            if isinstance(item, dict) and set(item) == {"canvas_id", "material_revision_id"} and type(item.get("material_revision_id")) is int and item["material_revision_id"] > 0
        ]
        if len(result["render_asset_ref"]) != len(declarations):
            _fail("graphic_render_ref_invalid")
    encoded = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    if len(encoded) > 2_000_000:
        _fail("graphic_payload_too_large")
    return result


def document_hash(payload: object) -> str:
    canonical = canonical_payload(payload)
    return hashlib.sha256(json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def validate_references(payload: object, asset_refs: object, evidence_refs: object) -> None:
    document = canonical_payload(payload)
    if not isinstance(asset_refs, list) or not isinstance(evidence_refs, list):
        _fail("graphic_reference_invalid")
    expected = {
        (canvas["id"], layer["id"]): layer["material_revision_id"]
        for canvas in document["canvases"]
        for layer in canvas["layers"]
        if layer["type"] in {"image", "chart"}
    }
    actual = {}
    for ref in asset_refs:
        if not isinstance(ref, dict):
            _fail("graphic_reference_invalid")
        if ref.get("role") == "render_output":
            continue
        placement = ref.get("placement")
        if not isinstance(placement, dict) or set(placement) != {"canvas_id", "layer_id"}:
            _fail("graphic_asset_placement_mismatch")
        key = (placement["canvas_id"], placement["layer_id"])
        if any(not isinstance(value, str) for value in key) or key in actual or ref.get("role") != "graphic_layer" or ref.get("slot_key") != key[1] or ref.get("material_revision_id") != expected.get(key):
            _fail("graphic_asset_placement_mismatch")
        actual[key] = ref["material_revision_id"]
    if actual != expected:
        _fail("graphic_asset_placement_mismatch")
    expected_evidence = {
        (canvas["id"], layer["id"], claim["start"], claim["end"], claim["fact_pack_item_id"], claim["snapshot_checksum"])
        for canvas in document["canvases"]
        for layer in canvas["layers"]
        if layer["type"] == "text"
        for claim in layer["claims"]
    }
    actual_evidence = set()
    for ref in evidence_refs:
        if not isinstance(ref, dict) or not isinstance(ref.get("locator"), dict) or set(ref["locator"]) != {"canvas_id", "layer_id", "start", "end"} or ref.get("role") != "claim":
            _fail("graphic_evidence_locator_mismatch")
        locator = ref["locator"]
        if not isinstance(locator["canvas_id"], str) or not isinstance(locator["layer_id"], str) or type(locator["start"]) is not int or type(locator["end"]) is not int or type(ref.get("fact_pack_item_id")) is not int or not isinstance(ref.get("snapshot_checksum"), str):
            _fail("graphic_evidence_locator_mismatch")
        key = (locator["canvas_id"], locator["layer_id"], locator["start"], locator["end"], ref.get("fact_pack_item_id"), ref.get("snapshot_checksum"))
        if key not in expected_evidence or key in actual_evidence:
            _fail("graphic_evidence_locator_mismatch")
        actual_evidence.add(key)
    if actual_evidence != expected_evidence:
        _fail("graphic_evidence_locator_mismatch")


def convert_legacy_graphic(payload: object, *, asset_refs: list[dict], evidence_refs: list[dict]) -> dict:
    if not isinstance(payload, dict):
        _fail("graphic_payload_invalid")
    old_render = "render_asset_ref" in payload or any(ref.get("role") == "render_output" for ref in asset_refs)
    content = {key: value for key, value in payload.items() if key != "render_asset_ref"}
    canonical = canonical_payload(content)
    content_refs = [ref for ref in asset_refs if ref.get("role") != "render_output"]
    validate_references(canonical, content_refs, evidence_refs)
    return {
        "payload": canonical,
        "asset_refs": content_refs,
        "evidence_refs": evidence_refs,
        "warnings": [{"code": "legacy_render_requires_new_attestation"}] if old_render else [],
        "document_hash": document_hash(canonical),
    }
