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
CARD = obj({"id": text(60), "order": {"type": "integer", "minimum": 0, "maximum": 9},
    "role": {"type": "string", "enum": ["cover", "body"], "maxLength": 5},
    "title": text(120), "body": {"type": "string", "maxLength": 1200},
    "bullets": array(text(240), maximum=6),
    "visual_type": {"type": "string", "enum": ["none", "image", "chart", "diagram"], "maxLength": 7},
    "material_revision_id": {"type": "integer", "minimum": 1, "maximum": 2147483647},
    "diagram_nodes": array(text(80), maximum=4, minimum=2),
    "claims": array(CLAIM, maximum=20)}, ["id", "order", "role", "title", "body", "visual_type"])
ARTIFACT_SCHEMAS = {
    "graphic.visual-direction.v1": obj({"intent": text(), "hierarchy": array(text(300), 12, 1),
        "visual_language": text(), "image_requirements": array(text(500), 24),
        "constraints": array(text(500), 24)}, ["intent", "hierarchy", "visual_language", "image_requirements"]),
    "graphic.card-plan.v1": obj({"title": text(500),
        "aspect_ratio": {"type": "string", "enum": ["1:1", "4:3", "3:4", "16:9", "9:16"], "maxLength": 5},
        "cards": array(CARD, 10, 1)}, ["title", "aspect_ratio", "cards"]),
    "audio.spoken-adaptation.v1": obj({"script": text(24000), "pronunciation_notes": array(text(500), 40),
        "source_summary": text(1000), "warnings": array(text(500), 20)}, ["script", "pronunciation_notes", "source_summary"]),
    "audio.voice-direction.v1": obj({"voice_character": text(500),
        "pace": {"type": "string", "enum": ["slow", "medium", "fast"], "maxLength": 6},
        "energy": text(100), "pause_policy": text(500), "pronunciation_notes": array(text(500), 40),
        "rate": {"type": "number", "minimum": 0.5, "maximum": 2}},
        ["voice_character", "pace", "energy", "pause_policy", "pronunciation_notes", "rate"]),
    "video.shot-plan.v1": obj({"title": text(500), "shots": array(obj({"id": text(100),
        "order": {"type": "integer", "minimum": 0, "maximum": 99}, "script": text(2000),
        "visual": text(1000), "asset_requirements": array(text(500), 20),
        "duration_seconds": {"type": "number", "minimum": 0.1, "maximum": 600}},
        ["id", "order", "script", "visual", "asset_requirements", "duration_seconds"]), 100, 1)}, ["title", "shots"]),
}


def validate_artifact(schema, content):
    result = canonical(content, max_bytes=64 * 1024)
    if schema not in ARTIFACT_SCHEMAS:
        return result
    _validate(result, ARTIFACT_SCHEMAS[schema])
    ordered = result.get("cards", result.get("shots", []))
    if ordered:
        ids = [item["id"] for item in ordered]
        if len(set(ids)) != len(ids) or any(not IDENTIFIER.fullmatch(value) for value in ids):
            raise ValueError("creative_artifact_identifier_invalid")
        if {item["order"] for item in ordered} != set(range(len(ordered))):
            raise ValueError("creative_artifact_order_invalid")
        key = "cards" if "cards" in result else "shots"
        result[key] = sorted(ordered, key=lambda item: item["order"])
    if schema == "graphic.card-plan.v1":
        if result["cards"][0]["role"] != "cover" or any(item["role"] != "body" for item in result["cards"][1:]):
            raise ValueError("creative_card_cover_required")
        for card in result["cards"]:
            needs_asset = card["visual_type"] in {"image", "chart"}
            if needs_asset != ("material_revision_id" in card):
                raise ValueError("creative_card_exact_visual_required")
            if (card["visual_type"] == "diagram") != ("diagram_nodes" in card):
                raise ValueError("creative_card_diagram_plan_required")
    return deepcopy(result)


def required_references(schema, content):
    required = set()
    if schema == "graphic.card-plan.v1":
        for card in content["cards"]:
            if "material_revision_id" in card:
                required.add(("material_revision", card["material_revision_id"]))
            for claim in card.get("claims", []):
                required.add(("fact_pack_item", claim["fact_pack_item_id"]))
    return required
