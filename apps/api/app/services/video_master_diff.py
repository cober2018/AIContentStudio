"""Stable-ID comparison of canonical Video Master documents."""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import ContentMasterRevision, User
from .content_masters import _hash, _serialize, owned_unit
from .video_documents import VideoDocumentError, canonical_payload


def _changes(before: list[dict], after: list[dict], fields: tuple[str, ...], *, scope: dict | None = None) -> list[dict]:
    prior = {item["id"]: (index, item) for index, item in enumerate(before)}
    latest = {item["id"]: (index, item) for index, item in enumerate(after)}
    scope = scope or {}
    result = []
    for item_id, (index, item) in prior.items():
        if item_id not in latest:
            result.append({**scope, "id": item_id, "kind": "remove", "from_index": index, "before": item})
    for item_id, (index, item) in latest.items():
        if item_id not in prior:
            result.append({**scope, "id": item_id, "kind": "add", "to_index": index, "after": item})
            continue
        old_index, old_item = prior[item_id]
        changed = (["move"] if old_index != index else []) + [field for field in fields if old_item.get(field) != item.get(field)]
        if changed:
            result.append({**scope, "id": item_id, "kind": "modify" if changed != ["move"] else "move", "changes": changed, "from_index": old_index, "to_index": index, "before": old_item, "after": item})
    return result


def _value(before: dict, after: dict, key: str) -> dict:
    return {"changed": before.get(key) != after.get(key), "before": before.get(key), "after": after.get(key)}


def diff_video_documents(before_payload: dict, after_payload: dict) -> dict:
    before, after = canonical_payload(before_payload), canonical_payload(after_payload)
    old_tracks = {track["id"]: track for track in before["timeline"]["tracks"]}
    new_tracks = {track["id"]: track for track in after["timeline"]["tracks"]}
    items = []
    for track_id in dict.fromkeys((*old_tracks, *new_tracks)):
        old = old_tracks.get(track_id, {"items": []})
        new = new_tracks.get(track_id, {"items": []})
        items.extend(_changes(old["items"], new["items"], ("shot_id", "material_revision_id", "start_ms", "end_ms", "trim_start_ms", "trim_end_ms", "volume"), scope={"track_id": track_id}))
    return {
        "title": _value(before, after, "title"),
        "aspect_ratio": _value(before, after, "aspect_ratio"),
        "script": _changes(before["script"]["blocks"], after["script"]["blocks"], ("text",)),
        "shots": _changes(before["shots"], after["shots"], ("label", "purpose", "duration_ms", "script_block_id", "source_material_revision_id", "framing", "transition")),
        "timeline_duration_ms": _value(before["timeline"], after["timeline"], "duration_ms"),
        "timeline_tracks": _changes(before["timeline"]["tracks"], after["timeline"]["tracks"], ("kind",)),
        "timeline_items": items,
        "voice": _value(before, after, "voice"),
        "subtitles": _changes(before["subtitles"]["cues"], after["subtitles"]["cues"], ("text", "start_ms", "end_ms")),
        "overlays": _changes(before["overlays"], after["overlays"], ("text", "start_ms", "end_ms", "x", "y")),
        "music": _value(before, after, "music"),
        "cover": _value(before, after, "cover"),
        "render_asset_ref": _value(before, after, "render_asset_ref"),
    }


def structured_video_diff(db: Session, *, project_id: int, unit_id: int, from_master_id: int, to_master_id: int, user: User) -> dict:
    owned_unit(db, project_id, unit_id, user)
    before = db.get(ContentMasterRevision, from_master_id)
    after = db.get(ContentMasterRevision, to_master_id)
    if before is None or after is None or any(row.project_id != project_id or row.content_unit_id != unit_id for row in (before, after)):
        raise HTTPException(404, "Master版本不存在")
    if before.payload_schema != "video.master.v2" or after.payload_schema != "video.master.v2":
        raise HTTPException(409, {"code": "video_master_not_comparable"})
    try:
        if any(canonical_payload(row.payload_json) != row.payload_json or _hash(row.payload_json) != row.payload_hash for row in (before, after)):
            raise VideoDocumentError("video_master_payload_integrity_invalid")
        diff = diff_video_documents(before.payload_json, after.payload_json)
    except VideoDocumentError as exc:
        raise HTTPException(409, {"code": "video_master_not_comparable", "reason": str(exc)}) from exc
    old_refs, new_refs = _serialize(db, before), _serialize(db, after)
    old_assets = [{key: value for key, value in ref.items() if key != "id"} for ref in old_refs["assets"]]
    new_assets = [{key: value for key, value in ref.items() if key != "id"} for ref in new_refs["assets"]]
    old_evidence = [{key: value for key, value in ref.items() if key != "id"} for ref in old_refs["evidence"]]
    new_evidence = [{key: value for key, value in ref.items() if key != "id"} for ref in new_refs["evidence"]]
    old_render = (before.edit_summary_json or {}).get("render_attestation")
    new_render = (after.edit_summary_json or {}).get("render_attestation")
    return {
        "from_master_id": before.id,
        "to_master_id": after.id,
        "from_schema": before.payload_schema,
        "to_schema": after.payload_schema,
        **diff,
        "assets": {"changed": old_assets != new_assets, "before": old_assets, "after": new_assets},
        "evidence": {"changed": old_evidence != new_evidence, "before": old_evidence, "after": new_evidence},
        "render": {"changed": old_render != new_render, "before": old_render, "after": new_render},
        "context": {"changed": before.context_hash != after.context_hash, "before": before.context_hash, "after": after.context_hash},
        "payload": {"before_hash": before.payload_hash, "after_hash": after.payload_hash},
    }
