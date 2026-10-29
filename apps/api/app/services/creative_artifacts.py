"""Bounded semantic outputs for non-Master creative stages."""

from copy import deepcopy

from .stage_contracts import IDENTIFIER, _validate, canonical


def text(limit=2000):
    return {"type": "string", "minLength": 1, "maxLength": limit}


def array(item, maximum=24, minimum=0):
    return {"type": "array", "items": item, "minItems": minimum, "maxItems": maximum}


def obj(properties, required):
    return {"type": "object", "additionalProperties": False, "properties": properties, "required": required}


CLAIM = obj({"target": text(100), "quote": text(2000),
    "fact_pack_item_id": {"type": "integer", "minimum": 1, "maximum": 2147483647}},
    ["target", "quote", "fact_pack_item_id"])
KNOWN = obj({"statement": text(1000),
    "kind": {"type": "string", "enum": ["fact", "inference"], "maxLength": 9},
    "as_of": text(80),
    "fact_pack_item_id": {"type": "integer", "minimum": 1, "maximum": 2147483647}},
    ["statement", "kind"])
SECTION = obj({"id": text(60), "order": {"type": "integer", "minimum": 0, "maximum": 30},
    "heading": text(200), "purpose": text(500),
    "points": array(text(500), maximum=8, minimum=1),
    "open_questions": array(text(500), maximum=6)},
    ["id", "order", "heading", "purpose", "points", "open_questions"])
BEAT = obj({"id": text(60), "order": {"type": "integer", "minimum": 0, "maximum": 30},
    "narration": text(2000), "visual": text(1000),
    "asset_requirements": {**array(text(500), maximum=8), "default": []},
    "unknowns": {**array(text(500), maximum=8), "default": []}},
    ["id", "order", "narration", "visual", "asset_requirements", "unknowns"])
CARD = obj({"id": text(60), "order": {"type": "integer", "minimum": 0, "maximum": 9},
    "role": {"type": "string", "enum": ["cover", "body"], "maxLength": 5},
    "title": text(120), "body": {"type": "string", "maxLength": 1200},
    "bullets": array(text(240), maximum=6),
    "visual_type": {"type": "string", "enum": ["none", "image", "chart", "diagram"], "maxLength": 7},
    "material_revision_id": {"type": "integer", "minimum": 1, "maximum": 2147483647},
    "diagram_nodes": array(text(80), maximum=4, minimum=2),
    "claims": array(CLAIM, maximum=20)}, ["id", "order", "role", "title", "body", "visual_type"])
ARTIFACT_SCHEMAS = {
    "research.brief.v1": obj({"question": text(500), "known": array(KNOWN, 24),
        "unknowns": array(text(500), 24, 1), "time_boundary": text(500)},
        ["question", "known", "unknowns", "time_boundary"]),
    "creative.angles.v1": obj({"angle": text(500), "reader_stake": text(500), "question": text(500),
        "support": text(1000), "limits": text(1000)},
        ["angle", "reader_stake", "question", "support", "limits"]),
    "creative.title-hook.v1": obj({"title": text(200), "hook": text(500), "reason": text(500)},
        ["title", "hook", "reason"]),
    "content.outline.v1": obj({"title": text(500), "sections": array(SECTION, 12, 1)},
        ["title", "sections"]),
    "video.script.v1": obj({"title": text(500), "beats": array(BEAT, 12, 1)}, ["title", "beats"]),
    # One complete writing plan: angle, the facts it stands on, what stays open, and the outline.
    "article.plan.v1": obj({"title": text(500), "angle": text(500), "reader_stake": text(500),
        "known": array(KNOWN, 24), "unknowns": array(text(500), 24), "sections": array(SECTION, 12, 1)},
        ["title", "angle", "reader_stake", "known", "unknowns", "sections"]),
    "graphic.visual-direction.v1": obj({"intent": text(), "hierarchy": array(text(300), 12, 1),
        "visual_language": text(), "image_requirements": array(text(500), 24),
        "constraints": array(text(500), 24)}, ["intent", "hierarchy", "visual_language", "image_requirements"]),
    "graphic.card-plan.v1": obj({"title": text(500),
        "aspect_ratio": {"type": "string", "enum": ["1:1", "4:3", "3:4", "16:9", "9:16"], "maxLength": 5},
        "cards": array(CARD, 10, 1)}, ["title", "aspect_ratio", "cards"]),
    "text.spoken-adaptation.v1": obj({"script": text(24000), "pronunciation_notes": array(text(500), 40),
        "source_summary": text(1000), "warnings": array(text(500), 20)}, ["script", "pronunciation_notes", "source_summary"]),
    "video.shot-plan.v1": obj({"title": text(500), "shots": array(obj({"id": text(100),
        "order": {"type": "integer", "minimum": 0, "maximum": 99}, "script": {"type": "string", "maxLength": 2000},
        "purpose": text(1000), "framing": {"type": "string", "enum": ["wide", "medium", "close", "custom"], "maxLength": 6},
        "filming": obj({"scene_id": text(100), "filming_order": {"type": "integer", "minimum": 0, "maximum": 299},
            "raw_duration_ms": {"type": "integer", "minimum": 1, "maximum": 28800000},
            **{key: text(2000) for key in ("subject", "action", "camera_position", "angle", "focus", "evidence_requirement", "audio_note")}}, []),
        "visual": text(1000), "asset_requirements": {**array(text(500), 20), "default": []},
        "duration_seconds": {"type": "number", "minimum": 0.1, "maximum": 600}},
        ["id", "order", "script", "visual", "asset_requirements", "duration_seconds"]), 100, 1)}, ["title", "shots"]),
}


# New semantic plans keep the original strict schemas and their historical hashes intact.
ARTIFACT_SCHEMAS["graphic.card-plan.v2"] = deepcopy(ARTIFACT_SCHEMAS["graphic.card-plan.v1"])
_card_v2 = ARTIFACT_SCHEMAS["graphic.card-plan.v2"]["properties"]["cards"]["items"]
_card_v2["properties"].update({
    "purpose": text(500), "content_basis": array(text(500), 8, 1), "transition": text(500),
    "visual_structure": {"type": "string", "enum": ["text", "sequence", "comparison", "groups", "image"], "maxLength": 10},
    "asset_requirements": array(text(500), 8),
})
_card_v2["required"] += ["purpose", "content_basis", "transition", "visual_structure", "asset_requirements"]
ARTIFACT_SCHEMAS["video.shot-plan.v2"] = deepcopy(ARTIFACT_SCHEMAS["video.shot-plan.v1"])
_shot_v2 = ARTIFACT_SCHEMAS["video.shot-plan.v2"]["properties"]["shots"]["items"]
_shot_v2["properties"].update({"content_basis": array(text(500), 8, 1), "reference_keys": array(text(100), 12),
    "continuity": obj({"from_previous": text(500), "to_next": text(500), "subject": text(300), "scene": text(300)},
        ["from_previous", "to_next", "subject", "scene"]),
    "sound": obj({"narration": text(1000), "ambience": text(500), "music": text(500), "uninspected": array(text(300), 8)},
        ["narration", "ambience", "music", "uninspected"]), "unknowns": array(text(500), 12)})
_shot_v2["required"] += ["purpose", "content_basis", "reference_keys", "continuity", "sound", "unknowns"]
ARTIFACT_SCHEMAS["video.shot-plan.v2"]["properties"]["reference_index"] = array(obj({
    "key": text(100), "description": text(500), "material_revision_id": {"type": "integer", "minimum": 1, "maximum": 2147483647}},
    ["key", "description", "material_revision_id"]), 100)
ARTIFACT_SCHEMAS["video.shot-plan.v2"]["required"] += ["reference_index"]


def validate_artifact(schema, content):
    result = canonical(content, max_bytes=64 * 1024)
    if schema not in ARTIFACT_SCHEMAS:
        return result
    result = _validate(result, ARTIFACT_SCHEMAS[schema])
    key = next((name for name in ("cards", "shots", "sections", "beats") if name in result), None)
    ordered = result.get(key, []) if key else []
    if ordered:
        if {item["order"] for item in ordered} == set(range(1, len(ordered) + 1)):
            for item in ordered:
                item["order"] -= 1
        prefix = {"beats": "beat", "shots": "shot", "sections": "section", "cards": "card"}[key]
        for item in ordered:
            value = item.get("id")
            if type(value) is not str or not IDENTIFIER.fullmatch(value):
                item["id"] = f"{prefix}-{item['order']}"
        ids = [item["id"] for item in ordered]
        if len(set(ids)) != len(ids) or any(not IDENTIFIER.fullmatch(value) for value in ids):
            raise ValueError("creative_artifact_identifier_invalid")
        if {item["order"] for item in ordered} != set(range(len(ordered))):
            raise ValueError("creative_artifact_order_invalid")
        result[key] = sorted(ordered, key=lambda item: item["order"])
    if schema in {"research.brief.v1", "article.plan.v1"}:
        for item in result["known"]:
            if item["kind"] == "inference" and "fact_pack_item_id" in item:
                raise ValueError("creative_brief_inference_cannot_cite")
    if schema in {"graphic.card-plan.v1", "graphic.card-plan.v2"}:
        if result["cards"][0]["role"] != "cover" or any(item["role"] != "body" for item in result["cards"][1:]):
            raise ValueError("creative_card_cover_required")
        for card in result["cards"]:
            needs_asset = card["visual_type"] in {"image", "chart"}
            if needs_asset != ("material_revision_id" in card):
                raise ValueError("creative_card_exact_visual_required")
            if (card["visual_type"] == "diagram") != ("diagram_nodes" in card):
                raise ValueError("creative_card_diagram_plan_required")
    if schema == "graphic.card-plan.v2":
        for card in result["cards"]:
            if card["visual_type"] == "diagram" and card["visual_structure"] not in {"sequence", "comparison", "groups"}:
                raise ValueError("creative_card_diagram_relation_required")
            if card["visual_type"] in {"image", "chart"} and card["visual_structure"] != "image":
                raise ValueError("creative_card_visual_structure_invalid")
    if schema == "video.shot-plan.v2":
        keys = [item["key"] for item in result["reference_index"]]
        if len(set(keys)) != len(keys) or any(not IDENTIFIER.fullmatch(key) for key in keys):
            raise ValueError("creative_shot_reference_index_invalid")
        if any(set(shot["reference_keys"]) - set(keys) for shot in result["shots"]):
            raise ValueError("creative_shot_reference_missing")
    return deepcopy(result)


def required_references(schema, content):
    required = set()
    if schema in {"research.brief.v1", "article.plan.v1"}:
        for item in content["known"]:
            if "fact_pack_item_id" in item:
                required.add(("fact_pack_item", item["fact_pack_item_id"]))
    if schema in {"graphic.card-plan.v1", "graphic.card-plan.v2"}:
        for card in content["cards"]:
            if "material_revision_id" in card:
                required.add(("material_revision", card["material_revision_id"]))
            for claim in card.get("claims", []):
                required.add(("fact_pack_item", claim["fact_pack_item_id"]))
    if schema == "video.shot-plan.v2":
        required.update(("material_revision", item["material_revision_id"]) for item in content["reference_index"])
    return required
