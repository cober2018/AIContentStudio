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
    video_profile = None
    if master.payload_schema == "video.master.v2" and master.channel_id and master.content_form:
        try:
            form = resolve_content_form(db, master.channel_id, master.content_form)
            video_profile = {"source": form.source, "version_id": form.profile_version_id, "artifact_kind": form.artifact_kind, "video_requirements": form.video_requirements, "media_requirements": form.media_requirements}
        except ChannelRegistryError:
            video_profile = {"unavailable": True}
    # Final outputs and revision IDs are excluded to avoid a render-hash cycle.
    return _canonical_hash({"project_id": master.project_id, "unit_id": master.content_unit_id, "schema": master.payload_schema, "context_hash": master.context_hash, "payload": payload, "assets": [{"material_revision_id": item.material_revision_id, "content_hash": item.content_hash_snapshot, "role": item.role, "slot_key": item.slot_key, "sort_order": item.sort_order, "placement": item.placement_json, "rights": item.rights_snapshot_json} for item in assets], "evidence": [{"fact_pack_item_id": item.fact_pack_item_id, "checksum": item.snapshot_checksum, "role": item.role, "sort_order": item.sort_order, "locator": item.content_locator_json} for item in evidence], **({"video_profile": video_profile} if master.payload_schema == "video.master.v2" else {})})


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


class TextMasterV2Adapter(TextMasterAdapter):
    version = "2"
    required_check_kinds = (*ProductionModalityAdapter.required_check_kinds, "text_structure", "text_fact", "text_identity", "text_platform")

    @property
    def payload_schema(self) -> str:
        return "text.master.v2"

    def validate_payload(self, payload: dict) -> list[str]:
        from .text_documents import TextDocumentError, canonical_payload

        try:
            canonical_payload(payload)
        except TextDocumentError as exc:
            return [str(exc)]
        return []

    def build_preview(self, master: ContentMasterRevision) -> dict:
        from .text_documents import TextDocumentError, canonical_payload, plain_text

        try:
            document = canonical_payload(master.payload_json)["document"]
            text = plain_text(document)
        except TextDocumentError as exc:
            return {**ProductionModalityAdapter.build_preview(self, master), "status": "invalid", "reasons": [str(exc)]}
        return {**ProductionModalityAdapter.build_preview(self, master), "plain_text": text[:20_000], "truncated": len(text) > 20_000, "block_count": len(document["blocks"]), "citation_count": len(document["citations"])}

    def build_render_snapshot(self, db: Session, master: ContentMasterRevision) -> dict:
        from .text_documents import TextDocumentError, canonical_payload, plain_text, render_markdown

        try:
            document = canonical_payload(master.payload_json)["document"]
            if not plain_text(document).strip():
                return {"status": "incomplete", "reasons": ["text_content_missing"]}
            refs = db.scalars(select(ContentMasterAssetRef).where(ContentMasterAssetRef.master_revision_id == master.id).order_by(ContentMasterAssetRef.sort_order, ContentMasterAssetRef.id)).all()
            paths = {}
            used = {}
            for block in document["blocks"]:
                if block["type"] not in {"image", "chart"}:
                    continue
                revision_id = block["material_revision_id"]
                if revision_id in used and used[revision_id] != block["type"]:
                    raise TextDocumentError("text_asset_use_kind_conflict")
                used[revision_id] = block["type"]
            for index, ref in enumerate(refs):
                if ref.material_revision_id not in used:
                    continue
                revision = db.get(MaterialRevision, ref.material_revision_id)
                expected_kind = "chart" if used[ref.material_revision_id] == "chart" else "image"
                if revision is None or revision.material.kind != expected_kind or revision.content_hash != ref.content_hash_snapshot or ref.material_revision_id in paths:
                    raise TextDocumentError("text_asset_kind_hash_or_declaration_invalid")
                data = read_bytes_checked(db, revision, require_public=True)
                suffix = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "image/gif": ".gif"}.get(revision.mime_type)
                if suffix is None or sniff_mime(data, None) != revision.mime_type:
                    raise TextDocumentError("text_asset_render_unavailable")
                paths[revision.id] = f"media/{index:02d}-{revision.id}{suffix}"
            markdown = render_markdown(document, media_paths=paths)
        except (TextDocumentError, HTTPException, OSError) as exc:
            reason = str(exc) if isinstance(exc, TextDocumentError) else "text_asset_bytes_or_rights_unavailable"
            return {"status": "incomplete", "reasons": [reason]}
        unused = sorted({ref.material_revision_id for ref in refs} - set(used))
        return {"status": "ready", "origin": "deterministic", "renderer_key": "text.studio.document.v1", "renderer_version": self.version, "render_input_hash": render_input_hash(db, master), "content_hash": hashlib.sha256(markdown.encode()).hexdigest(), "body_markdown": markdown, "unused_asset_ids": unused, "warnings": ["declared_asset_unused"] if unused else [], "reasons": []}


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


class GraphicMasterV2Adapter(GraphicMasterAdapter):
    version = "2"
    required_check_kinds = (*ProductionModalityAdapter.required_check_kinds, "graphic_structure", "graphic_fact", "graphic_identity", "graphic_platform")

    @property
    def payload_schema(self) -> str:
        return "graphic.master.v2"

    def validate_payload(self, payload: dict) -> list[str]:
        from .graphic_documents import GraphicDocumentError, canonical_payload

        try:
            canonical_payload(payload)
        except GraphicDocumentError as exc:
            return [str(exc)]
        return []

    def freeze_availability(self, db: Session, master: ContentMasterRevision) -> dict:
        from .graphic_master_checks import profile_reasons

        availability = super().freeze_availability(db, master)
        reasons = list(availability["reasons"])
        if master.channel_id and master.content_form and not self.validate_payload(master.payload_json):
            try:
                form = resolve_content_form(db, master.channel_id, master.content_form)
                reasons.extend(profile_reasons(form, master.payload_json))
            except ChannelRegistryError:
                reasons.append("graphic_profile_unavailable")
        return {**availability, "available": not reasons, "reasons": list(dict.fromkeys(reasons))}

    def build_preview(self, master: ContentMasterRevision) -> dict:
        from .graphic_documents import GraphicDocumentError, canonical_payload

        try:
            document = canonical_payload(master.payload_json)
        except GraphicDocumentError as exc:
            return {**super().build_preview(master), "status": "invalid", "reasons": [str(exc)]}
        return {**super().build_preview(master), "canvas_count": len(document["canvases"]), "canvases": [{"id": canvas["id"], "order": canvas["order"], "width": canvas["width"], "height": canvas["height"], "layer_count": len(canvas["layers"])} for canvas in document["canvases"]]}

    def build_render_snapshot(self, db: Session, master: ContentMasterRevision) -> dict:
        render = super().build_render_snapshot(db, master)
        if render["status"] != "ready":
            return render
        canvas_ids = [canvas["id"] for canvas in master.payload_json["canvases"]]
        if [output["canvas_id"] for output in render["outputs"]] != canvas_ids:
            return {"status": "incomplete", "reasons": ["render_canvas_order_mismatch"]}
        refs = {ref.material_revision_id: ref for ref in db.scalars(select(ContentMasterAssetRef).where(ContentMasterAssetRef.master_revision_id == master.id, ContentMasterAssetRef.role == "render_output")).all()}
        for index, output in enumerate(render["outputs"]):
            ref = refs[output["material_revision_id"]]
            canvas_id = canvas_ids[index]
            if ref.slot_key != canvas_id or ref.sort_order != index or ref.placement_json != {"canvas_id": canvas_id}:
                return {"status": "incomplete", "reasons": ["render_canvas_binding_mismatch"]}
        return render


class VideoMasterAdapter(MediaMasterAdapter):
    modality = "video"
    allowed_artifact_kinds = ("video",)
    material_kind = "video"
    mime_prefix = "video/"


class VideoMasterV2Adapter(VideoMasterAdapter):
    version = "2"

    @property
    def payload_schema(self) -> str:
        return "video.master.v2"

    def validate_payload(self, payload: dict) -> list[str]:
        from .video_documents import VideoDocumentError, canonical_payload

        try:
            canonical_payload(payload)
        except VideoDocumentError as exc:
            return [str(exc)]
        return []

    def freeze_availability(self, db: Session, master: ContentMasterRevision) -> dict:
        from .video_documents import profile_reasons

        availability = super().freeze_availability(db, master)
        reasons = list(availability["reasons"])
        if master.channel_id and master.content_form and not self.validate_payload(master.payload_json):
            try:
                form = resolve_content_form(db, master.channel_id, master.content_form)
                reasons.extend(profile_reasons(form, master.payload_json))
            except ChannelRegistryError:
                reasons.append("video_profile_unavailable")
        return {**availability, "available": not reasons, "reasons": list(dict.fromkeys(reasons))}

    def build_preview(self, master: ContentMasterRevision) -> dict:
        from .video_documents import VideoDocumentError, canonical_payload

        try:
            document = canonical_payload(master.payload_json)
        except VideoDocumentError as exc:
            return {**super().build_preview(master), "status": "invalid", "reasons": [str(exc)]}
        return {**super().build_preview(master), "shot_count": len(document["shots"]), "duration_ms": document["timeline"]["duration_ms"]}


ADAPTERS = {(adapter.modality, adapter.payload_schema): adapter for adapter in (TextMasterAdapter(), TextMasterV2Adapter(), GraphicMasterAdapter(), GraphicMasterV2Adapter(), VideoMasterAdapter(), VideoMasterV2Adapter())}


def default_payload_schema(modality: str) -> str:
    if modality not in DESCRIPTORS:
        raise HTTPException(422, {"code": "unsupported_modality"})
    return "text.master.v2" if modality == "text" else DESCRIPTORS[modality].payload_schema


def supported_payload_schemas(modality: str) -> tuple[str, ...]:
    default_payload_schema(modality)
    return tuple(schema for kind, schema in ADAPTERS if kind == modality)


def adapter_for(modality: str, payload_schema: str | None = None) -> ProductionModalityAdapter:
    schema = payload_schema or default_payload_schema(modality)
    adapter = ADAPTERS.get((modality, schema))
    if adapter is None:
        raise HTTPException(422, {"code": "unsupported_payload_schema", "modality": modality, "payload_schema": schema})
    return adapter


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
    elif isinstance(payload.get("title"), str) and len(payload["title"]) > 500:
        errors.append("title_too_long")
    if modality == "text" and declaration is not None:
        errors.append("text_render_asset_unsupported")
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
            if isinstance(item, dict) and any(key in {"file_path", "local_path", "storage_path", "absolute_path", "render_url", "storage_url"} for key in item):
                return ["infrastructure_location_forbidden"]
            stack.extend((child, depth + 1) for child in (item.values() if isinstance(item, dict) else item))
    try:
        canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    except (TypeError, ValueError):
        return ["payload_invalid_json"]
    return ["payload_too_large"] if len(canonical) > 2_000_000 else []


def validate_master_references(payload: dict, assets: list[dict], evidence: list[dict]) -> list[str]:
    asset_ids = {row.get("material_revision_id") for row in assets if type(row.get("material_revision_id")) is int}
    evidence_ids = {row.get("fact_pack_item_id") for row in evidence if type(row.get("fact_pack_item_id")) is int}
    for rows, id_key, hash_key in ((assets, "material_revision_id", "content_hash"), (evidence, "fact_pack_item_id", "snapshot_checksum")):
        for row in rows:
            if type(row.get(id_key)) is not int or row[id_key] <= 0 or not isinstance(row.get(hash_key), str) or not 1 <= len(row[hash_key]) <= 64:
                return ["invalid_exact_reference"]
            if not isinstance(row.get("role", "other"), str) or not 1 <= len(row.get("role", "other")) <= 40:
                return ["invalid_reference_role"]
            if row.get("slot_key") is not None and (not isinstance(row["slot_key"], str) or len(row["slot_key"]) > 100):
                return ["invalid_reference_slot"]
            if type(row.get("sort_order", 0)) is not int or not 0 <= row.get("sort_order", 0) <= 2147483647:
                return ["invalid_reference_order"]
            if not isinstance(row.get("placement", {}), dict) or not isinstance(row.get("locator", {}), dict):
                return ["invalid_reference_location"]
    stack = [payload]
    while stack:
        value = stack.pop()
        if isinstance(value, dict):
            for key, ids in (("material_revision_id", asset_ids), ("fact_pack_item_id", evidence_ids)):
                if key in value and (type(value[key]) is not int or value[key] not in ids):
                    return ["undeclared_embedded_reference"]
            stack.extend(value.values())
        elif isinstance(value, list):
            stack.extend(value)
    return []
