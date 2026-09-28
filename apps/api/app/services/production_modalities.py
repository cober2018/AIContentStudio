"""Small, explicit modality registry for Production Core."""

import hashlib
import json
from dataclasses import dataclass

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ContentMasterAssetRef, ContentMasterEvidenceRef, ContentMasterRevision, MaterialRevision
from .content_harness.channel_registry import ChannelRegistryError, resolve_content_form
from .materials import read_bytes_checked, sniff_mime


@dataclass(frozen=True)
class ModalityDescriptor:
    modality: str
    payload_schema: str
    required_checks: tuple[str, ...]
    candidate_freeze_available: bool
    unavailable_reason: str | None = None


def _validate_text(payload: dict) -> list[str]:
    if not isinstance(payload, dict):
        return ["payload_not_object"]
    if payload.get("markdown") is not None and not isinstance(payload["markdown"], str):
        return ["markdown_must_be_string"]
    if payload.get("document") is not None and not isinstance(payload["document"], dict):
        return ["document_must_be_object"]
    if payload.get("structured") is not None and not isinstance(payload["structured"], dict):
        return ["structured_must_be_object"]
    return []


def _validate_graphic(payload: dict) -> list[str]:
    if not isinstance(payload, dict) or not isinstance(payload.get("canvases", []), list):
        return ["canvases_must_be_array"]
    return _stable_items(payload.get("canvases", []), "canvases")


def _validate_video(payload: dict) -> list[str]:
    if not isinstance(payload, dict) or not isinstance(payload.get("shots", []), list):
        return ["shots_must_be_array"]
    return _stable_items(payload.get("shots", []), "shots")


def _stable_items(items: list, field: str) -> list[str]:
    seen = set()
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"] or len(item["id"]) > 150:
            return [f"{field}_stable_id_required"]
        if item["id"] in seen:
            return [f"{field}_duplicate_id"]
        seen.add(item["id"])
        if "order" in item and (type(item["order"]) is not int or item["order"] < 0):
            return [f"{field}_invalid_order"]
    return []


DESCRIPTORS = {
    "text": ModalityDescriptor("text", "text.master.v1", ("master_schema", "evidence", "rights", "render"), True),
    "graphic": ModalityDescriptor("graphic", "graphic.master.v1", ("master_schema", "evidence", "rights", "render"), False, "final_render_required"),
    "video": ModalityDescriptor("video", "video.master.v1", ("master_schema", "evidence", "rights", "render"), False, "final_render_required"),
}


VALIDATORS = {"text": _validate_text, "graphic": _validate_graphic, "video": _validate_video}


def _canonical_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def render_input_hash(db: Session, master: ContentMasterRevision) -> str:
    payload = {key: value for key, value in master.payload_json.items() if key != "render_asset_ref"}
    assets = db.scalars(select(ContentMasterAssetRef).where(ContentMasterAssetRef.master_revision_id == master.id, ContentMasterAssetRef.role != "render_output").order_by(ContentMasterAssetRef.sort_order, ContentMasterAssetRef.id)).all()
    evidence = db.scalars(select(ContentMasterEvidenceRef).where(ContentMasterEvidenceRef.master_revision_id == master.id).order_by(ContentMasterEvidenceRef.sort_order, ContentMasterEvidenceRef.id)).all()
    # Final outputs and revision IDs are excluded to avoid a render-hash cycle.
    return _canonical_hash({"project_id": master.project_id, "unit_id": master.content_unit_id, "schema": master.payload_schema, "context_hash": master.context_hash, "payload": payload, "assets": [{"material_revision_id": item.material_revision_id, "content_hash": item.content_hash_snapshot, "role": item.role, "slot_key": item.slot_key, "sort_order": item.sort_order, "placement": item.placement_json, "rights": item.rights_snapshot_json} for item in assets], "evidence": [{"fact_pack_item_id": item.fact_pack_item_id, "checksum": item.snapshot_checksum, "role": item.role, "sort_order": item.sort_order, "locator": item.content_locator_json} for item in evidence]})


class ProductionModalityAdapter:
    version = "1"
    required_check_kinds = ("master_schema", "evidence", "rights", "render")
    modality: str
    allowed_artifact_kinds: tuple[str, ...]

    @property
    def payload_schema(self) -> str:
        return f"{self.modality}.master.v1"

    def validate_payload(self, payload: dict) -> list[str]:
        return validate_payload(self.modality, payload)

    def build_preview(self, master: ContentMasterRevision) -> dict:
        return {"modality": self.modality, "title": master.payload_json.get("title"), "payload_schema": self.payload_schema}

    def build_render_snapshot(self, db: Session, master: ContentMasterRevision) -> dict:
        raise NotImplementedError

    def freeze_availability(self, db: Session, master: ContentMasterRevision) -> dict:
        reasons = self.validate_payload(master.payload_json)
        if master.channel_id is None or master.content_form is None:
            reasons.append("channel_form_missing")
        else:
            try:
                form = resolve_content_form(db, master.channel_id, master.content_form)
                if form.artifact_kind not in self.allowed_artifact_kinds:
                    reasons.append("unsupported_channel_modality")
            except ChannelRegistryError:
                reasons.append("channel_form_unavailable")
        render = self.build_render_snapshot(db, master)
        if render["status"] != "ready":
            reasons.extend(render["reasons"])
        return {"available": not reasons, "reasons": list(dict.fromkeys(reasons)), "adapter_version": self.version}

    def build_package_projection(self, db: Session, master: ContentMasterRevision) -> dict:
        raise NotImplementedError


class TextMasterAdapter(ProductionModalityAdapter):
    modality = "text"
    allowed_artifact_kinds = ("text", "script")

    def build_preview(self, master: ContentMasterRevision) -> dict:
        return {**super().build_preview(master), "markdown": (master.payload_json.get("markdown") or "")[:20_000], "truncated": len(master.payload_json.get("markdown") or "") > 20_000}

    def build_render_snapshot(self, db: Session, master: ContentMasterRevision) -> dict:
        reasons = validate_payload(self.modality, master.payload_json, for_freeze=True)
        if reasons:
            return {"status": "incomplete", "reasons": reasons}
        markdown = master.payload_json["markdown"]
        return {"status": "ready", "origin": "deterministic", "renderer_key": "text.markdown.v1", "renderer_version": self.version, "render_input_hash": render_input_hash(db, master), "content_hash": hashlib.sha256(markdown.encode()).hexdigest(), "body_markdown": markdown, "reasons": []}

    def build_package_projection(self, db: Session, master: ContentMasterRevision) -> dict:
        available = self.freeze_availability(db, master)
        if not available["available"]:
            raise HTTPException(409, {"code": "modality_package_unavailable", "reasons": available["reasons"]})
        render = self.build_render_snapshot(db, master)
        return {"text_files": [{"name": "content.md", "content": render["body_markdown"]}], "material_outputs": []}


class MediaMasterAdapter(ProductionModalityAdapter):
    material_kind: str
    mime_prefix: str

    def build_render_snapshot(self, db: Session, master: ContentMasterRevision) -> dict:
        errors = self.validate_payload(master.payload_json)
        if errors:
            return {"status": "incomplete", "reasons": errors}
        attestation = (master.edit_summary_json or {}).get("render_attestation") or {}
        inputs_hash = render_input_hash(db, master)
        if attestation.get("origin") != "manual" or attestation.get("confirmed") is not True or not attestation.get("attested_by"):
            return {"status": "incomplete", "reasons": ["render_attestation_missing"]}
        if attestation.get("render_input_hash") != inputs_hash:
            return {"status": "incomplete", "reasons": ["render_input_changed"]}
        declaration = master.payload_json.get("render_asset_ref")
        declarations = declaration if isinstance(declaration, list) else [declaration] if isinstance(declaration, dict) else []
        if not declarations or any(not isinstance(item, dict) for item in declarations):
            return {"status": "incomplete", "reasons": ["final_render_required"]}
        if self.modality == "graphic":
            canvas_ids = [item.get("id") for item in master.payload_json.get("canvases", [])]
            output_ids = [item.get("canvas_id") for item in declarations]
            if not canvas_ids or len(output_ids) != len(canvas_ids) or set(output_ids) != set(canvas_ids):
                return {"status": "incomplete", "reasons": ["render_canvas_coverage_missing"]}
        else:
            if not master.payload_json.get("shots") or not master.payload_json.get("script"):
                return {"status": "incomplete", "reasons": ["video_content_missing"]}
            if len(declarations) != 1:
                return {"status": "incomplete", "reasons": ["video_final_render_must_be_single"]}
        refs = {item.material_revision_id: item for item in db.scalars(select(ContentMasterAssetRef).where(ContentMasterAssetRef.master_revision_id == master.id, ContentMasterAssetRef.role == "render_output")).all()}
        outputs = []
        seen = set()
        for declaration in declarations:
            revision_id = declaration.get("material_revision_id")
            if type(revision_id) is not int or revision_id in seen or revision_id not in refs:
                return {"status": "incomplete", "reasons": ["render_asset_ref_invalid"]}
            seen.add(revision_id)
            revision = db.get(MaterialRevision, revision_id)
            if revision is None or revision.content_hash != refs[revision_id].content_hash_snapshot or revision.status in {"revoked", "archived"} or revision.material.status != "active" or revision.material.kind != self.material_kind or revision.public_use_allowed is not True:
                return {"status": "incomplete", "reasons": ["render_asset_rights_or_kind_invalid"]}
            try:
                content = read_bytes_checked(db, revision, require_public=True)
            except (HTTPException, OSError):
                return {"status": "incomplete", "reasons": ["render_bytes_unverified"]}
            if not revision.mime_type or not revision.mime_type.startswith(self.mime_prefix) or sniff_mime(content, None) != revision.mime_type:
                return {"status": "incomplete", "reasons": ["render_mime_invalid"]}
            outputs.append({"material_revision_id": revision.id, "content_hash": revision.content_hash, "mime_type": revision.mime_type, "canvas_id": declaration.get("canvas_id"), "rights_snapshot": refs[revision_id].rights_snapshot_json})
        bindings = [{key: output[key] for key in ("material_revision_id", "content_hash", "canvas_id")} for output in outputs]
        if bindings != attestation.get("outputs"):
            return {"status": "incomplete", "reasons": ["render_output_binding_changed"]}
        return {"status": "ready", "origin": "manual", "attested_by": attestation["attested_by"], "render_input_hash": inputs_hash, "outputs": outputs, "reasons": []}

    def build_package_projection(self, db: Session, master: ContentMasterRevision) -> dict:
        available = self.freeze_availability(db, master)
        if not available["available"]:
            raise HTTPException(409, {"code": "modality_package_unavailable", "reasons": available["reasons"]})
        render = self.build_render_snapshot(db, master)
        suffixes = {"image/png": ".png", "image/jpeg": ".jpg", "image/gif": ".gif", "image/webp": ".webp", "video/mp4": ".mp4"}
        if any(output["mime_type"] not in suffixes for output in render["outputs"]):
            raise HTTPException(409, {"code": "modality_package_unavailable", "reasons": ["render_format_unsupported"]})
        return {"text_files": [], "material_outputs": [{**output, "name": f"render-{index + 1}{suffixes[output['mime_type']]}"} for index, output in enumerate(render["outputs"])]}


class GraphicMasterAdapter(MediaMasterAdapter):
    modality = "graphic"
    allowed_artifact_kinds = ("image",)
    material_kind = "image"
    mime_prefix = "image/"


class VideoMasterAdapter(MediaMasterAdapter):
    modality = "video"
    allowed_artifact_kinds = ("video",)
    material_kind = "video"
    mime_prefix = "video/"


ADAPTERS = {adapter.modality: adapter for adapter in (TextMasterAdapter(), GraphicMasterAdapter(), VideoMasterAdapter())}


def adapter_for(modality: str) -> ProductionModalityAdapter:
    if modality not in ADAPTERS:
        raise HTTPException(422, {"code": "unsupported_modality"})
    return ADAPTERS[modality]


def descriptor(modality: str) -> ModalityDescriptor:
    return DESCRIPTORS.get(modality) or ModalityDescriptor(modality, f"{modality}.master.v1", ("master_schema",), False, "unsupported_modality")


def validate_payload(modality: str, payload: dict, *, for_freeze: bool = False) -> list[str]:
    if not isinstance(payload, dict):
        return ["payload_not_object"]
    bounds = validate_json_bounds(payload)
    if bounds:
        return bounds
    errors = VALIDATORS.get(modality, lambda value: ["unsupported_modality"])(payload)
    declaration = payload.get("render_asset_ref")
    if declaration is not None:
        declarations = declaration if isinstance(declaration, list) else [declaration]
        if any(not isinstance(item, dict) or type(item.get("material_revision_id")) is not int or item["material_revision_id"] <= 0 or (modality == "graphic" and not isinstance(item.get("canvas_id"), str)) for item in declarations):
            errors.append("render_asset_ref_invalid")
    if payload.get("title") is not None and not isinstance(payload["title"], str):
        errors.append("title_must_be_string")
    if for_freeze and modality == "text" and not (payload.get("document") or (payload.get("markdown") or "").strip()):
        errors.append("text_content_missing")
    if for_freeze and modality == "text" and payload.get("document") and not (payload.get("markdown") or "").strip():
        errors.append("document_renderer_unavailable")
    if for_freeze and modality in {"graphic", "video"}:
        errors.append("final_render_required")
    return errors


def validate_json_bounds(value: object) -> list[str]:
    stack = [(value, 0)]
    visited = 0
    while stack:
        item, depth = stack.pop()
        visited += 1
        if depth > 32:
            return ["payload_too_deep"]
        if visited > 20_000:
            return ["payload_too_many_values"]
        if isinstance(item, (list, dict)):
            if len(item) > 1000:
                return ["payload_collection_too_large"]
            stack.extend((child, depth + 1) for child in (item.values() if isinstance(item, dict) else item))
    try:
        canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    except (TypeError, ValueError):
        return ["payload_invalid_json"]
    return ["payload_too_large"] if len(canonical) > 2_000_000 else []
