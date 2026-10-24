"""Deterministic card composition; proposals are not rendered media."""

import math

from .creative_artifacts import validate_artifact
from .graphic_documents import canonical_payload, validate_references
from .stage_contracts import canonical, digest

DIMENSIONS = {"1:1": (1080, 1080), "4:3": (1440, 1080), "3:4": (1080, 1440),
              "16:9": (1920, 1080), "9:16": (1080, 1920)}
PALETTES = {
    "technical_editorial": ("#101827", "#f5f7fa", "#60a5fa"),
    "architecture": ("#101827", "#f5f7fa", "#6ee7b7"),
    "clean": ("#f6f8fb", "#172033", "#2563eb"),
    "warm_magazine": ("#fff6e9", "#392d27", "#b85c38"),
    "documentary": ("#f8f4ec", "#302d2a", "#816c4f"),
    "lifestyle": ("#fff4e8", "#443328", "#b66545"),
}


def photo_requirement(preset):
    if preset.get("palette") == "documentary":
        return "every_card"
    return "cover" if preset.get("palette") == "warm_magazine" else "none"


def requires_photo(preset, role):
    requirement = photo_requirement(preset)
    return requirement == "every_card" or (requirement == "cover" and role == "cover")


def _text_height(text, width, size):
    # Same estimate as geometry_quality, so a fitted card never fails its own overflow check.
    return (math.ceil(len(text) / max(1, width // size)) + text.count("\n")) * size * 1.4


def _node_height(labels, width, size):
    return max(math.ceil(len(label) / max(1, (width - 32) // size)) for label in labels) * size * 1.4 + 32


def compose(plan, *, preset_ref, asset_catalog=(), evidence_catalog=(), template="editorial", density=None):
    from .studio_creative_catalog import PRESETS, validate_ref

    validate_ref(preset_ref, kind="style_preset")
    preset = PRESETS[preset_ref]["config"]
    if preset.get("modality") != "graphic" or template not in {"editorial", "split", "cards"}:
        raise ValueError("graphic_composition_preset_invalid")
    density = density or preset["density"]
    if density not in {"low", "medium", "high"}:
        raise ValueError("graphic_composition_density_invalid")
    plan_schema = "graphic.card-plan.v2" if any("visual_structure" in card for card in plan.get("cards", [])) else "graphic.card-plan.v1"
    plan = validate_artifact(plan_schema, plan)
    width, height = DIMENSIONS[plan["aspect_ratio"]]
    background, foreground, accent = PALETTES[preset["palette"]]
    supplied_assets = {item["material_revision_id"]: item for item in asset_catalog}
    if any(item["content_hash"] != supplied_assets[item["material_revision_id"]]["content_hash"] for item in asset_catalog):
        raise ValueError("graphic_composition_conflicting_asset_hash")
    supplied_evidence = {item["item_id"]: item["checksum"] for item in evidence_catalog}
    canvases, asset_refs, evidence_refs = [], [], []
    for card in plan["cards"]:
        cid, layers = card["id"], []
        evidence_start = len(evidence_refs)
        margin = 72
        content_width = width - 2 * margin
        visual = card["visual_type"]
        visual_height = round(height * (0.32 if template == "split" else 0.28))
        labels = card["diagram_nodes"] if visual == "diagram" else []
        gap = 36
        node_width = (content_width - gap * (len(labels) - 1)) / len(labels) if labels else 0
        bullet_gap = 32 if template == "cards" else 24
        base_title, title_cap = (60, 120) if card["role"] == "cover" else (48, 84)
        base_body = {"low": 38, "medium": 34, "high": 30}[density]
        # Caps are for medium density and follow the density ratio, otherwise short cards would hit the same caps at every density.
        ratio = base_body / 34
        def sizes(scale, _base_title=base_title, _title_cap=title_cap, _base_body=base_body, _ratio=ratio):
            return (min(round(_base_title * scale), round(_title_cap * _ratio)), min(round(_base_body * scale), round(56 * _ratio)),
                min(round(28 * scale), round(40 * _ratio)))
        def stack(title_size, body_size, label_size, _card=card, _visual=visual, _visual_height=visual_height,
                  _labels=labels, _node_width=node_width, _width=content_width, _bullet_gap=bullet_gap):
            total = 32 + _text_height(_card["title"], _width, title_size) + 28
            if _visual in {"image", "chart"}:
                total += _visual_height + 28
            if _labels:
                total += _node_height(_labels, _node_width, label_size) + 28
            if _card["body"]:
                total += _text_height(_card["body"], _width, body_size) + 24
            return total + sum(_text_height("• " + bullet, _width, body_size) + _bullet_gap for bullet in _card.get("bullets", []))
        # Largest scale that leaves breathing room; base sizes are the floor so dense cards behave exactly as before.
        safe = height - 2 * margin
        title_size, body_size, label_size = next((sizes(step / 20) for step in range(50, 20, -1)
            if stack(*sizes(step / 20)) <= safe * .9), sizes(1))
        top = margin + round(max(0, safe - stack(title_size, body_size, label_size)) * .45)
        def layer(kind, lid, x, y, w, h, *, _layers=layers, **content):
            value = {"id": lid, "type": kind, "order": len(_layers), "x": x, "y": y,
                "width": w, "height": h, **content}
            _layers.append(value)
            return value
        def write(lid, value, y, size, box_height, target, *, x=None, box_width=None,
                  _card=card, _cid=cid, _margin=margin, _width=content_width, _layer=layer):
            claims = []
            for claim in _card.get("claims", []):
                if claim["target"] != target:
                    continue
                quote = claim["quote"]
                start = value.find(quote)
                if start < 0 or value.find(quote, start + 1) >= 0 or claim["fact_pack_item_id"] not in supplied_evidence:
                    raise ValueError("graphic_composition_claim_unproven")
                item = {"fact_pack_item_id": claim["fact_pack_item_id"],
                    "snapshot_checksum": supplied_evidence[claim["fact_pack_item_id"]], "start": start, "end": start + len(quote)}
                claims.append(item)
                evidence_refs.append({"fact_pack_item_id": item["fact_pack_item_id"],
                    "snapshot_checksum": item["snapshot_checksum"], "role": "claim", "sort_order": len(evidence_refs),
                    "locator": {"canvas_id": _cid, "layer_id": lid, "start": item["start"], "end": item["end"]}})
            _layer("text", lid, _margin if x is None else x, y, _width if box_width is None else box_width, box_height, claims=claims,
                runs=[{"text": value, "style": {"font_size": size, "color": foreground, "weight": 400, "align": "left"}}])
        layer("shape", f"{cid}-accent", margin, top, 88, 8, shape="rectangle", fill=accent)
        title_height = _text_height(card["title"], content_width, title_size)
        write(f"{cid}-title", card["title"], top + 32, title_size, title_height, "title")
        cursor = top + 32 + title_height + 28
        if requires_photo(preset, card["role"]) and visual != "image":
            raise ValueError("graphic_composition_requested_photo_missing")
        if visual in {"image", "chart"}:
            revision = supplied_assets.get(card["material_revision_id"])
            if revision is None:
                raise ValueError("graphic_composition_asset_not_supplied")
            if revision.get("kind") is not None and revision["kind"] != visual:
                raise ValueError("graphic_composition_asset_kind_mismatch")
            lid = f"{cid}-visual"
            layer(visual, lid, margin, cursor, content_width, visual_height,
                material_revision_id=revision["material_revision_id"], fit="contain")
            asset_refs.append({"material_revision_id": revision["material_revision_id"], "content_hash": revision["content_hash"],
                "role": "graphic_layer", "slot_key": lid, "sort_order": len(asset_refs),
                "placement": {"canvas_id": cid, "layer_id": lid}})
            cursor += visual_height + 28
        elif visual == "diagram" and preset.get("image_fallback") != "shape_only":
            raise ValueError("graphic_composition_shape_fallback_unavailable")
        if visual == "diagram":
            box_width, size = node_width, label_size
            box_height = _node_height(labels, box_width, size)
            for index, label in enumerate(labels):
                x = margin + index * (box_width + gap)
                layer("shape", f"{cid}-node-{index}-box", x, cursor, box_width, box_height,
                    shape="rectangle", fill=background, stroke=accent, stroke_width=2)
                write(f"{cid}-node-{index}", label, cursor + 16, size, box_height - 32,
                    f"diagram-{index}", x=x + 16, box_width=box_width - 32)
                if index + 1 < len(labels) and card.get("visual_structure", "sequence") == "sequence":
                    layer("shape", f"{cid}-link-{index}", x + box_width, cursor + box_height / 2,
                        gap, 2, shape="rectangle", fill=accent)
            cursor += box_height + 28
        if card["body"]:
            box = _text_height(card["body"], content_width, body_size)
            write(f"{cid}-body", card["body"], cursor, body_size, box, "body")
            cursor += box + 24
        for index, bullet in enumerate(card.get("bullets", [])):
            value = "• " + bullet
            box = _text_height(value, content_width, body_size)
            write(f"{cid}-bullet-{index}", value, cursor, body_size, box, f"bullet-{index}")
            cursor += box + bullet_gap
        valid_targets = {"title", *(("body",) if card["body"] else ()), *(f"bullet-{i}" for i in range(len(card.get("bullets", [])))),
            *(f"diagram-{i}" for i in range(len(card.get("diagram_nodes", []))))}
        if any(claim["target"] not in valid_targets for claim in card.get("claims", [])):
            raise ValueError("graphic_composition_claim_target_invalid")
        if len(evidence_refs) - evidence_start != len(card.get("claims", [])):
            raise ValueError("graphic_composition_claim_unmapped")
        if cursor > height - margin:
            raise ValueError("graphic_composition_text_overflow")
        canvases.append({"id": cid, "order": card["order"], "role": card["role"], "width": width, "height": height,
            "background": {"color": background}, "layers": layers})
    payload = canonical_payload({"title": plan["title"], "canvases": canvases})
    validate_references(payload, asset_refs, evidence_refs)
    report = geometry_quality(payload)
    if report["status"] == "blocker":
        raise ValueError("graphic_composition_layout_blocked")
    return canonical({"payload_schema": "graphic.master.v2", "payload": payload, "asset_refs": asset_refs,
        "evidence_refs": evidence_refs, "composition": {"tool": "studio.graphic.layout-compose@1", "plan_hash": digest(plan),
            "preset_ref": preset_ref, "preset_hash": digest(PRESETS[preset_ref]),
            **({"plan_schema": plan_schema, "page_purposes": [{"id": card["id"], "purpose": card["purpose"], "visual_structure": card["visual_structure"]} for card in plan["cards"]]} if plan_schema.endswith(".v2") else {}),
            "photo_requirement": photo_requirement(preset), "template": template, "density": density},
        "quality": report})


def _luminance(color):
    rgb = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return sum(weight * (v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4)
        for weight, v in zip((.2126, .7152, .0722), rgb))


def build_proposal(resolved):
    from .stage_master_proposals import _candidate, _validate_supplied_refs
    from .studio_creative_catalog import load_skill

    if (resolved.get("node", {}).get("plugin") != "stage.graphic.compose"
            or resolved.get("context", {}).get("modality") != "graphic" or resolved.get("model") is not None):
        raise ValueError("graphic_composition_stage_invalid")
    method = resolved.get("method") or {}
    if method.get("skill_ref") != "studio.graphic.layout-compose@1":
        raise ValueError("graphic_composition_method_invalid")
    package = load_skill(method["skill_ref"])
    if method.get("package_hash") != package["package_hash"]:
        raise ValueError("graphic_composition_tool_changed")
    plans = [value for value in resolved.get("upstream", {}).values()
        if value.get("output_schema") in {"graphic.card-plan.v1", "graphic.card-plan.v2"} and value.get("selected_content") is not None]
    if len(plans) != 1:
        raise ValueError("graphic_composition_one_accepted_plan_required")
    context = resolved["context"]
    sources = [context, context.get("master") or {}, *resolved.get("upstream", {}).values()]
    assets = [*[item for source in sources for item in source.get("asset_refs", [])], *context.get("shared_asset_refs", [])]
    config = resolved["effective_config"]
    preset = config.get("preset_ref") or (resolved.get("creative_configuration") or {}).get("profile", {}).get("style_preset_ref")
    result = compose(plans[0]["selected_content"], preset_ref=preset, asset_catalog=assets,
        evidence_catalog=(context.get("boundary") or {}).get("items", []),
        template=config.get("template", "editorial"), density=config.get("density"))
    candidate = _candidate(result, 1, "graphic", resolved)
    _validate_supplied_refs(candidate, resolved)
    output = canonical({"schema": "stage.master.proposal.v1", "candidates": [candidate], "candidate_count": 1,
        "llm_run_id": None, "model": None, "input_hash": digest({"resolution_hash": resolved["resolution_hash"],
            "accepted_plan_hash": plans[0]["accepted_hash"], "tool_package_hash": package["package_hash"]}),
        "prompt_hash": resolved["prompt_hash"], "composition": result["composition"], "quality": result["quality"]})
    output["proposal_hash"] = digest(output)
    return output


def geometry_quality(payload):
    document = canonical_payload(payload)
    issues = []
    if len(document["canvases"]) > 10 or document["canvases"][0].get("role") != "cover" or any(canvas.get("role") != "body" for canvas in document["canvases"][1:]):
        issues.append({"severity": "blocker", "reason": "graphic_studio_canvas_contract"})
    for canvas in document["canvases"]:
        texts = [layer for layer in canvas["layers"] if layer["type"] == "text" and layer["visible"]]
        for layer in canvas["layers"]:
            if not layer["visible"]:
                continue
            location = {"canvas_id": canvas["id"], "layer_id": layer["id"]}
            if layer["x"] < 24 or layer["y"] < 24 or layer["x"] + layer["width"] > canvas["width"] - 24 or layer["y"] + layer["height"] > canvas["height"] - 24:
                issues.append({"severity": "blocker", "reason": "graphic_minimum_margin", **location})
            if layer["type"] == "text":
                total = "".join(run["text"] for run in layer["runs"])
                size = max(run["style"]["font_size"] for run in layer["runs"])
                estimated = math.ceil(len(total) / max(1, layer["width"] // size)) + total.count("\n")
                if estimated * size * 1.4 > layer["height"] + 1:
                    issues.append({"severity": "blocker", "reason": "graphic_estimated_text_overflow", **location})
                if size < 24:
                    issues.append({"severity": "warning", "reason": "graphic_small_type", **location})
                for run in layer["runs"]:
                    fg, bg = run["style"]["color"], canvas["background"]["color"]
                    if len(fg) != 7 or len(bg) != 7 or layer["rotation"] or layer["opacity"] != 1:
                        issues.append({"severity": "warning", "reason": "graphic_contrast_unmeasured", **location})
                        continue
                    bright, dark = sorted((_luminance(fg), _luminance(bg)), reverse=True)
                    if (bright + .05) / (dark + .05) < 4.5:
                        issues.append({"severity": "blocker", "reason": "graphic_low_contrast", **location})
        for index, left in enumerate(texts):
            for right in texts[index + 1:]:
                if (not left["rotation"] and not right["rotation"] and left["x"] < right["x"] + right["width"]
                        and right["x"] < left["x"] + left["width"] and left["y"] < right["y"] + right["height"]
                        and right["y"] < left["y"] + left["height"]):
                    issues.append({"severity": "blocker", "reason": "graphic_text_overlap", "canvas_id": canvas["id"],
                        "layer_id": left["id"], "other_layer_id": right["id"]})
    return {"schema": "studio.graphic.geometry-qc.v1", "payload_hash": digest(document),
        "status": "blocker" if any(i["severity"] == "blocker" for i in issues) else "warning" if issues else "pass",
        "issues": issues, "coverage": {"geometry": "axis_aligned", "text_fit": "estimated", "bytes": "not_rendered",
            "contrast": "text_vs_solid_canvas_only", "aesthetic_quality": "human_review_required"}, "human_review_required": True}


class GraphicComposer:
    key = "studio.graphic.layout-compose"
    version = "1"
    consumed_fields = frozenset({"template", "density"})
    execute = staticmethod(compose)


class GraphicQC:
    key = "studio.graphic.qc"
    version = "1"
    consumed_fields = frozenset()
    execute = staticmethod(geometry_quality)


def bootstrap():
    from .content_harness.registry import registry
    for executor in (GraphicComposer(), GraphicQC()):
        if (executor.key, executor.version) not in {(item.key, item.version) for item in registry.list("tool_provider")}:
            registry.register("tool_provider", executor.key, executor.version, executor, label=executor.key)
