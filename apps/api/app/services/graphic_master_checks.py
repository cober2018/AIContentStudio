"""Exact published Graphic profile and schema-specific check rules."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ContentMasterRevision, FactPackItem, IdentitySnapshot, ProjectFactBoundaryRevision
from .content_harness.channel_registry import ChannelRegistryError, ContentFormSpec, resolve_content_form
from .graphic_documents import GraphicDocumentError, canonical_payload, validate_references
from .text_master_checks import _semantic_review


def profile_reasons(form: ContentFormSpec, document: dict) -> list[str]:
    if form.source != "profile" or form.artifact_kind != "image" or form.profile_version_id is None:
        return ["graphic_profile_unavailable"]
    rules = form.graphic_requirements
    if not isinstance(rules, dict) or set(rules) - {"min_canvases", "max_canvases", "allowed_dimensions", "cover_required", "presets"}:
        return ["graphic_profile_rules_invalid"]
    minimum = rules.get("min_canvases")
    maximum = rules.get("max_canvases")
    if any(type(value) is not int or not 1 <= value <= 24 for value in (minimum, maximum) if value is not None) or (minimum is not None and maximum is not None and minimum > maximum):
        return ["graphic_profile_rules_invalid"]
    dimensions = rules.get("allowed_dimensions")
    if dimensions is not None and (not isinstance(dimensions, list) or not dimensions or len(dimensions) > 50 or any(not isinstance(pair, list) or len(pair) != 2 or any(type(value) is not int or not 1 <= value <= 8192 for value in pair) for pair in dimensions)):
        return ["graphic_profile_rules_invalid"]
    if "cover_required" in rules and type(rules["cover_required"]) is not bool:
        return ["graphic_profile_rules_invalid"]
    presets = rules.get("presets")
    if presets is not None and (not isinstance(presets, list) or len(presets) > 50 or any(not isinstance(item, dict) or set(item) != {"key", "label", "width", "height"} or not isinstance(item["key"], str) or not item["key"] or not isinstance(item["label"], str) or not item["label"] or any(type(item[field]) is not int or not 1 <= item[field] <= 8192 for field in ("width", "height")) for item in presets)):
        return ["graphic_profile_rules_invalid"]
    media_rules = form.media_requirements
    if not isinstance(media_rules, dict) or any(value not in {"required", "optional"} for value in media_rules.values()):
        return ["graphic_profile_rules_invalid"]
    if set(media_rules) - {"cover", "inline"}:
        return ["graphic_profile_rule_unavailable"]
    canvases = document["canvases"]
    reasons = []
    if minimum is not None and len(canvases) < minimum:
        reasons.append("graphic_canvas_count_below_profile_minimum")
    if maximum is not None and len(canvases) > maximum:
        reasons.append("graphic_canvas_count_above_profile_maximum")
    if dimensions is not None and any([canvas["width"], canvas["height"]] not in dimensions for canvas in canvases):
        reasons.append("graphic_dimensions_not_allowed")
    if (rules.get("cover_required") is True or form.media_requirements.get("cover") == "required") and canvases[0].get("role") != "cover":
        reasons.append("graphic_cover_required")
    if media_rules.get("inline") == "required" and not any(layer["type"] in {"image", "chart"} and layer["visible"] for canvas in canvases for layer in canvas["layers"]):
        reasons.append("graphic_inline_media_required")
    return reasons


def _visible_text(document: dict) -> tuple[str, list[dict]]:
    layers = [
        {"canvas_id": canvas["id"], "layer_id": layer["id"], "text": "".join(run["text"] for run in layer["runs"])}
        for canvas in document["canvases"]
        for layer in canvas["layers"]
        if layer["type"] == "text" and layer["visible"]
    ]
    return "\n".join(item["text"] for item in layers), layers


def _structure(master: ContentMasterRevision, projection: dict, requirement: dict | None = None) -> tuple[str, dict]:
    try:
        document = canonical_payload(master.payload_json)
        validate_references(document, projection["assets"], projection["evidence"])
    except GraphicDocumentError as exc:
        return "blocker", {"reasons": [str(exc)], "coverage": {"deterministic": "complete"}}
    visible = [layer for canvas in document["canvases"] for layer in canvas["layers"] if layer["visible"]]
    if not visible:
        return "incomplete", {"reasons": ["graphic_visible_layer_missing"], "coverage": {"deterministic": "complete"}, "canvas_count": len(document["canvases"])}
    persona = (requirement or {}).get("metadata", {}).get("persona_quality")
    if persona:
        from .graphic_composition import geometry_quality, photo_requirement, requires_photo
        from .studio_creative_catalog import PRESETS, QUALITY, digest

        ref = persona["ref"]
        if (ref not in {"studio.quality.graphic.editorial@1", "studio.quality.graphic.lifestyle@1"}
                or digest(QUALITY[ref]) != persona["hash"]
                or persona.get("style_preset_ref") not in PRESETS
                or digest(PRESETS[persona["style_preset_ref"]]) != persona.get("style_preset_hash")):
            return "incomplete", {"reasons": ["graphic_persona_quality_unavailable"], "coverage": {"deterministic": "partial"}}
        report = geometry_quality(document)
        preset = PRESETS.get(persona.get("style_preset_ref"), {}).get("config", {})
        if "photo_requirement" in persona and persona["photo_requirement"] != photo_requirement(preset):
            return "incomplete", {"reasons": ["graphic_persona_quality_unavailable"], "coverage": {"deterministic": "partial"}}
        for canvas in document["canvases"]:
            if requires_photo(preset, canvas["role"]) and not any(layer["type"] == "image" and layer["visible"] for layer in canvas["layers"]):
                report["issues"].append({"severity": "blocker", "reason": "graphic_requested_photo_missing", "canvas_id": canvas["id"]})
        report["status"] = "blocker" if any(item["severity"] == "blocker" for item in report["issues"]) else "warning" if report["issues"] else "pass"
        return report["status"], {"reasons": [], "persona_quality": {**persona, "report": report},
            "coverage": {**report["coverage"], "live_bytes_rights": "separate_required_render_rights_checks"},
            "canvas_count": len(document["canvases"]), "visible_layer_count": len(visible)}
    return "pass", {"reasons": [], "coverage": {"deterministic": "complete"}, "canvas_count": len(document["canvases"]), "visible_layer_count": len(visible)}


def _fact(db: Session, master: ContentMasterRevision, requirement: dict) -> tuple[str, dict]:
    boundary = db.get(ProjectFactBoundaryRevision, master.fact_boundary_revision_id) if master.fact_boundary_revision_id else None
    if boundary is None:
        return "incomplete", {"reasons": ["fact_boundary_missing"], "coverage": {"semantic": "unavailable"}}
    document = canonical_payload(master.payload_json)
    body, text_layers = _visible_text(document)
    if not body.strip():
        return "warning", {"reasons": ["graphic_visual_semantics_unverified"], "coverage": {"deterministic": "exact_claim_refs_only", "semantic": "unavailable", "reason": "visible_text_missing"}, "text_layer_count": len(text_layers)}
    items = db.scalars(select(FactPackItem).where(FactPackItem.fact_pack_id == boundary.fact_pack_id).order_by(FactPackItem.id)).all()
    excluded = [item.id for item in items if item.model_use_allowed is not True or item.public_use_revoked_at is not None]
    invalid = [item.id for item in items if not isinstance(item.snapshot_json, dict)]
    if excluded or invalid:
        issues, coverage = [], {"semantic": "unavailable", "reason": "model_use_excluded" if excluded else "fact_snapshot_invalid"}
    else:
        context = {"facts": [{"id": item.id, "statement": str((item.snapshot_json or {}).get("statement") or "")[:400]} for item in items[:50]]}
        issues, coverage = _semantic_review("fact_review", text=body, context=context, configured=requirement["metadata"]["semantic"]["configured"])
        if len(items) > 50:
            coverage.update({"semantic": "partial" if coverage["semantic"] == "verified" else coverage["semantic"], "reason": "fact_input_truncated"})
    coverage.update({"deterministic": "exact_claim_refs_only", "model_use_excluded_item_ids": excluded, "invalid_snapshot_item_ids": invalid, "fact_count": len(items), "text_layer_count": len(text_layers)})
    status = "blocker" if any(issue["severity"] == "blocker" for issue in issues) else "warning" if issues or coverage["semantic"] != "verified" else "pass"
    return status, {"reasons": [], "issues": issues, "coverage": coverage}


def _identity(db: Session, master: ContentMasterRevision, requirement: dict) -> tuple[str, dict]:
    snapshot = db.get(IdentitySnapshot, master.identity_snapshot_id) if master.identity_snapshot_id else None
    if snapshot is None:
        return "incomplete", {"reasons": ["identity_snapshot_missing"], "coverage": {"semantic": "unavailable"}}
    document = canonical_payload(master.payload_json)
    body, text_layers = _visible_text(document)
    profile = snapshot.effective_profile_json or {}
    if not isinstance(profile, dict):
        return "incomplete", {"reasons": ["identity_profile_invalid"], "coverage": {"semantic": "unavailable"}}
    style = profile.get("expression_style") if isinstance(profile.get("expression_style"), dict) else {}
    forbidden = style.get("forbidden_phrases", [])
    if not isinstance(forbidden, list) or any(not isinstance(term, str) for term in forbidden):
        return "incomplete", {"reasons": ["identity_rule_invalid"], "coverage": {"semantic": "unavailable"}}
    issues = [{"severity": "blocker", "span": term[:120], "reason": "explicit_identity_forbidden_phrase", "source": "deterministic"} for term in forbidden if term and term in body]
    if not body.strip() or not profile:
        semantic, coverage = [], {"semantic": "unavailable", "reason": "visible_text_missing" if not body.strip() else "identity_scope_missing"}
    else:
        semantic, coverage = _semantic_review("identity_review", text=body, context={"identity": profile, "checksum": snapshot.checksum}, configured=requirement["metadata"]["semantic"]["configured"])
    issues.extend(semantic)
    coverage.update({"deterministic": "explicit_phrases_only", "text_layer_count": len(text_layers), "visual_semantics": "unavailable"})
    status = "blocker" if any(issue["severity"] == "blocker" for issue in issues) else "warning"
    return status, {"reasons": [], "identity_snapshot_id": snapshot.id, "identity_checksum": snapshot.checksum, "issues": issues, "coverage": coverage}


def _platform(db: Session, master: ContentMasterRevision) -> tuple[str, dict]:
    try:
        form = resolve_content_form(db, master.channel_id, master.content_form)
    except (ChannelRegistryError, TypeError, ValueError):
        return "incomplete", {"reasons": ["graphic_profile_unavailable"], "coverage": {"deterministic": "unavailable"}}
    unsupported = [key for key in form.rule_sets if key not in {"rule.media.required", "rule.media.public_rights", "rule.media.order"}]
    if unsupported:
        return "incomplete", {"reasons": ["graphic_rule_executor_unavailable"], "unsupported_rule_keys": unsupported, "coverage": {"deterministic": "partial"}}
    reasons = profile_reasons(form, canonical_payload(master.payload_json))
    state = "incomplete" if any(reason in {"graphic_profile_unavailable", "graphic_profile_rules_invalid", "graphic_profile_rule_unavailable"} for reason in reasons) else "blocker" if reasons else "pass"
    return state, {"reasons": reasons, "channel": form.channel, "content_form": form.content_form, "profile_version_id": form.profile_version_id, "coverage": {"deterministic": "complete" if state != "incomplete" else "unavailable"}}


def run_graphic_checks(db: Session, master: ContentMasterRevision, projection: dict, requirements: dict[str, dict]) -> dict[str, tuple[str, dict]]:
    handlers = {
        "graphic_structure": lambda requirement: _structure(master, projection, requirement),
        "graphic_fact": lambda requirement: _fact(db, master, requirement),
        "graphic_identity": lambda requirement: _identity(db, master, requirement),
        "graphic_platform": lambda _: _platform(db, master),
    }
    return {kind: handlers[kind](requirement) for kind, requirement in requirements.items() if kind in handlers}
