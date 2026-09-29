"""Explicit, source-bound Video v2 child revisions."""

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ContentMasterRevision, User
from .content_masters import _context, _hash, _serialize, owned_unit, save_revision
from .video_documents import VideoDocumentError, canonical_payload


def _parameters(operation: str, parameters: dict, source: dict, result: dict) -> None:
    if operation == "long_to_short":
        duration = parameters.get("target_duration_ms")
        if set(parameters) != {"target_duration_ms"} or type(duration) is not int or duration <= 0 or duration >= source["timeline"]["duration_ms"] or result["timeline"]["duration_ms"] != duration:
            raise HTTPException(422, {"code": "invalid_video_derivation_result"})
    elif operation == "aspect_ratio":
        ratio = parameters.get("target_aspect_ratio")
        if set(parameters) != {"target_aspect_ratio"} or ratio != result["aspect_ratio"] or ratio == source["aspect_ratio"]:
            raise HTTPException(422, {"code": "invalid_video_derivation_result"})
    else:
        shot_id = parameters.get("shot_id")
        before = {shot["id"]: shot for shot in source["shots"]}
        after = {shot["id"]: shot for shot in result["shots"]}
        if set(parameters) != {"shot_id"} or not isinstance(shot_id, str) or shot_id not in before or shot_id not in after or not after[shot_id].get("source_material_revision_id") or before[shot_id].get("source_material_revision_id") == after[shot_id]["source_material_revision_id"]:
            raise HTTPException(422, {"code": "invalid_video_derivation_result"})


def derive_video_master(db: Session, *, project_id: int, unit_id: int, master_id: int, user: User, request: dict) -> dict:
    project, unit = owned_unit(db, project_id, unit_id, user, mutate=True)
    source = db.get(ContentMasterRevision, master_id)
    if source is None or source.project_id != project_id or source.content_unit_id != unit_id:
        raise HTTPException(404, "Master版本不存在")
    if source.payload_schema != "video.master.v2" or unit.modality != "video":
        raise HTTPException(409, {"code": "video_v2_derivation_source_required"})
    fingerprint = _hash({"source_master_id": master_id, "actor": user.email, "request": request})
    existing = db.scalar(select(ContentMasterRevision).where(ContentMasterRevision.content_unit_id == unit_id, ContentMasterRevision.idempotency_key == request["idempotency_key"]))
    if existing:
        derivation = (existing.edit_summary_json or {}).get("derived_video") or {}
        if existing.source_kind != "derived_video" or derivation.get("request_hash") != fingerprint:
            raise HTTPException(409, {"code": "video_derivation_idempotency_conflict"})
        return _serialize(db, existing)
    if source.payload_hash != request["expected_payload_hash"] or _hash(source.payload_json) != source.payload_hash or source.context_hash != request["expected_context_hash"]:
        raise HTTPException(409, {"code": "video_derivation_source_conflict"})
    latest = db.scalar(select(ContentMasterRevision).where(ContentMasterRevision.content_unit_id == unit_id).order_by(ContentMasterRevision.revision_no.desc()).limit(1))
    current_context = _hash(_context(db, project, unit, content_form=source.content_form))
    if latest is None or latest.id != source.id or latest.revision_no != request["expected_revision"] or current_context != source.context_hash:
        raise HTTPException(409, {"code": "video_derivation_source_conflict"})
    if request["result_origin"] != "user_edit":
        raise HTTPException(503, {"code": "video_derivation_capability_unavailable", "operation": request["operation"]})
    if request["result_payload"] is None:
        raise HTTPException(422, {"code": "concrete_video_result_required"})
    try:
        result = canonical_payload(request["result_payload"])
        source_document = canonical_payload(source.payload_json)
    except VideoDocumentError as exc:
        raise HTTPException(422, {"code": "invalid_video_derivation_document", "reason": str(exc)}) from exc
    if result == source_document or "render_asset_ref" in result or any(ref.get("role") == "render_output" for ref in request["asset_refs"]):
        raise HTTPException(422, {"code": "concrete_unrendered_video_result_required"})
    _parameters(request["operation"], request["parameters"], source_document, result)
    derivation = {
        "source_master_id": source.id,
        "source_revision_no": source.revision_no,
        "source_payload_hash": source.payload_hash,
        "source_context_hash": source.context_hash,
        "operation": request["operation"],
        "parameters": request["parameters"],
        "result_origin": "user_edit",
        "result_payload_hash": _hash(result),
        "request_hash": fingerprint,
    }
    return save_revision(db, project_id=project_id, unit_id=unit_id, user=user, derived_source=source, payload={
        "expected_revision": request["expected_revision"],
        "expected_context_hash": request["expected_context_hash"],
        "idempotency_key": request["idempotency_key"],
        "parent_revision_id": source.id,
        "content_form": source.content_form,
        "payload_schema": "video.master.v2",
        "payload": result,
        "asset_refs": request["asset_refs"],
        "evidence_refs": request["evidence_refs"],
        "source_kind": "derived_video",
        "edit_summary": {"derived_video": derivation},
    })
