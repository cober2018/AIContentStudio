"""Deterministic Video v2 checks stored by the existing Master check runtime."""

from sqlalchemy.orm import Session

from ..models import ContentMasterRevision, IdentitySnapshot
from .content_harness.channel_registry import ChannelRegistryError, resolve_content_form
from .text_master_checks import _semantic_review
from .video_documents import VideoDocumentError, canonical_payload, profile_reasons, validate_references


def _document(master: ContentMasterRevision, projection: dict) -> tuple[dict | None, list[str]]:
    try:
        document = canonical_payload(master.payload_json)
        assets = [
            {key: ref[key] for key in ("material_revision_id", "content_hash", "role", "slot_key", "sort_order", "placement")}
            for ref in projection["assets"]
        ]
        validate_references(document, assets, projection["evidence"])
    except VideoDocumentError as exc:
        return None, [str(exc)]
    return document, []


def _platform(db: Session, master: ContentMasterRevision, document: dict) -> tuple[str, dict]:
    try:
        form = resolve_content_form(db, master.channel_id, master.content_form)
    except (ChannelRegistryError, TypeError, ValueError):
        return "incomplete", {"reasons": ["video_profile_unavailable"], "coverage": {"deterministic": "unavailable"}}
    unsupported = [key for key in form.rule_sets if key not in {"rule.media.required", "rule.media.public_rights", "rule.media.order"}]
    if unsupported:
        return "incomplete", {"reasons": ["video_rule_executor_unavailable"], "unsupported_rule_keys": unsupported, "coverage": {"deterministic": "partial"}}
    reasons = profile_reasons(form, document)
    unavailable = {"video_profile_unavailable", "video_profile_rules_invalid", "video_profile_rule_unavailable"}
    status = "incomplete" if any(reason in unavailable for reason in reasons) else "blocker" if reasons else "pass"
    return status, {"reasons": reasons, "channel": form.channel, "content_form": form.content_form, "profile_version_id": form.profile_version_id, "coverage": {"deterministic": "unavailable" if status == "incomplete" else "complete"}}


def _identity(db: Session, master: ContentMasterRevision, document: dict, requirement: dict) -> tuple[str, dict]:
    product = (getattr(master, "edit_summary_json", None) or {}).get("product_context_snapshot")
    if product is not None:
        body = "\n".join([block["text"] for block in document["script"]["blocks"]] + [cue["text"] for cue in document["subtitles"]["cues"]] + [item["text"] for item in document["overlays"]])
        dimensions = ("purchase_reason", "product_evidence", "product_consistency", "shot_continuity", "sound_clarity", "truthful_cta")
        issues, coverage = _semantic_review("identity_review", text=body, context={"production_domain": "product", "product": product, "review_dimensions": dimensions, "rule": "仅依SKU资料评审购买理由与证据；AI情境不能证明性能，禁止虚构体验/优惠/实测"}, configured=requirement["metadata"]["semantic"]["configured"], critic_dimensions=dimensions)
        coverage.update({"visual_semantics": "unavailable", "audio_semantics": "unavailable", "deterministic": "existing_structure_rights_evidence_checks"})
        return ("blocker" if any(issue["severity"] == "blocker" for issue in issues) else "warning"), {"reasons": [], "production_domain": "product", "product_context_checksum": product["checksum"], "issues": issues, "coverage": coverage, "human_review_required": True}
    snapshot = db.get(IdentitySnapshot, master.identity_snapshot_id) if master.identity_snapshot_id else None
    if snapshot is None:
        return "incomplete", {"reasons": ["identity_snapshot_missing"], "coverage": {"semantic": "unavailable", "visual_semantics": "unavailable", "audio_semantics": "unavailable"}}
    profile = snapshot.effective_profile_json or {}
    if not isinstance(profile, dict) or not profile:
        return "incomplete", {"reasons": ["identity_profile_invalid"], "coverage": {"semantic": "unavailable", "visual_semantics": "unavailable", "audio_semantics": "unavailable"}}
    style = profile.get("expression_style") if isinstance(profile.get("expression_style"), dict) else {}
    forbidden = style.get("forbidden_phrases", [])
    if not isinstance(forbidden, list) or any(not isinstance(term, str) for term in forbidden):
        return "incomplete", {"reasons": ["identity_rule_invalid"], "coverage": {"semantic": "unavailable", "visual_semantics": "unavailable", "audio_semantics": "unavailable"}}
    text_parts = [block["text"] for block in document["script"]["blocks"]]
    text_parts.extend(cue["text"] for cue in document["subtitles"]["cues"])
    text_parts.extend(overlay["text"] for overlay in document["overlays"])
    body = "\n".join(text_parts)
    issues = [{"severity": "blocker", "span": term[:120], "reason": "explicit_identity_forbidden_phrase", "source": "deterministic"} for term in forbidden if term and term in body]
    if body.strip():
        semantic, coverage = _semantic_review("identity_review", text=body, context={"identity": profile, "checksum": snapshot.checksum}, configured=requirement["metadata"]["semantic"]["configured"])
    else:
        semantic, coverage = [], {"semantic": "unavailable", "reason": "video_text_missing"}
    issues.extend(semantic)
    coverage.update({"deterministic": "explicit_phrases_only", "text_segment_count": len(text_parts), "visual_semantics": "unavailable", "audio_semantics": "unavailable"})
    return ("blocker" if any(issue["severity"] == "blocker" for issue in issues) else "warning"), {"reasons": [], "identity_snapshot_id": snapshot.id, "identity_checksum": snapshot.checksum, "issues": issues, "coverage": coverage}


def run_video_checks(db: Session, master: ContentMasterRevision, projection: dict, requirements: dict[str, dict]) -> dict[str, tuple[str, dict]]:
    document, errors = _document(master, projection)
    if errors:
        failure = ("blocker", {"reasons": errors, "coverage": {"deterministic": "complete"}})
        return {"video_structure": failure, "video_timeline": failure, "video_identity": failure, "video_platform": failure}

    script_blocks = document["script"]["blocks"]
    shots = document["shots"]
    structure_reasons = []
    if not any(block["text"].strip() for block in script_blocks):
        structure_reasons.append("video_script_missing")
    if not shots:
        structure_reasons.append("video_shots_missing")
    timeline = document["timeline"]
    placed_shot_ids = {
        item["shot_id"]
        for track in timeline["tracks"] if track["kind"] == "video"
        for item in track["items"] if "shot_id" in item
    }
    timeline_reasons = []
    if timeline["duration_ms"] == 0 or not any(track["items"] for track in timeline["tracks"] if track["kind"] == "video"):
        timeline_reasons.append("video_visual_timeline_missing")
    if any(shot["id"] not in placed_shot_ids for shot in shots):
        timeline_reasons.append("video_shot_unplaced")
    return {
        "video_structure": (
            "incomplete" if structure_reasons else "pass",
            {"reasons": structure_reasons, "coverage": {"deterministic": "complete"}, "script_block_count": len(script_blocks), "shot_count": len(shots)},
        ),
        "video_timeline": (
            "incomplete" if timeline_reasons else "pass",
            {"reasons": timeline_reasons, "coverage": {"deterministic": "complete"}, "duration_ms": timeline["duration_ms"], "placed_shot_count": len(placed_shot_ids)},
        ),
        "video_platform": _platform(db, master, document),
        "video_identity": _identity(db, master, document, requirements["video_identity"]),
    }
