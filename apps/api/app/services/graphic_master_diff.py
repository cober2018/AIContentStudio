"""Bounded structured comparison of canonical Graphic documents."""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import ContentMasterRevision, User
from .content_masters import _serialize, owned_unit
from .graphic_documents import GraphicDocumentError, canonical_payload, convert_legacy_graphic


def _ordered_changes(before: list[dict], after: list[dict], *, key: str, scope: dict | None = None) -> list[dict]:
    prior = {item[key]: item for item in before}
    latest = {item[key]: item for item in after}
    before_order = [item[key] for item in before]
    after_order = [item[key] for item in after]
    scope = scope or {}
    is_canvas = "canvas_id" not in scope
    result = []
    for item_id in before_order:
        if item_id not in latest:
            result.append({**scope, f"{key}": item_id, "kind": "remove", "from_index": before_order.index(item_id)})
    for item_id in after_order:
        if item_id not in prior:
            result.append({**scope, f"{key}": item_id, "kind": "add", "to_index": after_order.index(item_id)})
            continue
        old, new = prior[item_id], latest[item_id]
        changes = []
        if before_order.index(item_id) != after_order.index(item_id):
            changes.append("move")
        if any(old.get(field) != new.get(field) for field in (("width", "height") if is_canvas else ("x", "y", "width", "height"))):
            changes.append("resize")
        if is_canvas:
            if old.get("background") != new.get("background") or old.get("role") != new.get("role") or old.get("variant_of_canvas_id") != new.get("variant_of_canvas_id"):
                changes.append("modify")
        else:
            if old.get("runs") != new.get("runs"):
                changes.append("text")
            if old.get("material_revision_id") != new.get("material_revision_id"):
                changes.append("asset")
            if old.get("claims") != new.get("claims"):
                changes.append("evidence")
            if any(old.get(field) != new.get(field) for field in ("type", "visible", "locked", "fit", "shape", "style")):
                changes.append("modify")
        if changes:
            result.append({**scope, f"{key}": item_id, "kind": changes[-1], "changes": changes, "from_index": before_order.index(item_id), "to_index": after_order.index(item_id)})
    return result


def diff_graphic_documents(before_payload: dict, after_payload: dict) -> dict:
    before = canonical_payload(before_payload)
    after = canonical_payload(after_payload)
    before_canvases, after_canvases = before["canvases"], after["canvases"]
    before_map = {item["id"]: item for item in before_canvases}
    after_map = {item["id"]: item for item in after_canvases}
    canvas_changes = _ordered_changes(before_canvases, after_canvases, key="id")
    canvas_changes = [{"canvas_id": item.pop("id"), **item} for item in canvas_changes]
    layer_changes = []
    for canvas_id in [item["id"] for item in after_canvases if item["id"] in before_map]:
        changes = _ordered_changes(before_map[canvas_id]["layers"], after_map[canvas_id]["layers"], key="id", scope={"canvas_id": canvas_id})
        layer_changes.extend({"layer_id": item.pop("id"), **item} for item in changes)
    before_locations = {}
    after_locations = {}
    for locations, canvases in ((before_locations, before_canvases), (after_locations, after_canvases)):
        for canvas in canvases:
            for index, layer in enumerate(canvas["layers"]):
                locations.setdefault(layer["id"], []).append((canvas["id"], index, layer))
    for layer_id, origins in before_locations.items():
        destinations = after_locations.get(layer_id, [])
        if len(origins) != 1 or len(destinations) != 1 or origins[0][0] == destinations[0][0]:
            continue
        source_canvas, source_index, source_layer = origins[0]
        target_canvas, target_index, target_layer = destinations[0]
        layer_changes = [item for item in layer_changes if not (item["layer_id"] == layer_id and item["kind"] in {"remove", "add"} and item["canvas_id"] in {source_canvas, target_canvas})]
        kinds = ["move"] + (["modify"] if source_layer != target_layer else [])
        layer_changes.append({"layer_id": layer_id, "kind": "move", "changes": kinds, "from_canvas_id": source_canvas, "to_canvas_id": target_canvas, "from_index": source_index, "to_index": target_index})
    return {"canvases": canvas_changes, "layers": layer_changes, "title": {"changed": before.get("title") != after.get("title"), "before": before.get("title"), "after": after.get("title")}}


def _master_payload(db: Session, master: ContentMasterRevision) -> dict:
    try:
        if master.payload_schema == "graphic.master.v2":
            return canonical_payload(master.payload_json)
        if master.payload_schema == "graphic.master.v1":
            refs = _serialize(db, master)
            return convert_legacy_graphic(master.payload_json, asset_refs=refs["assets"], evidence_refs=refs["evidence"])["payload"]
    except GraphicDocumentError as exc:
        raise HTTPException(409, {"code": "graphic_master_not_comparable", "reason": str(exc)}) from exc
    raise HTTPException(409, {"code": "unsupported_graphic_master_schema"})


def _semantic_refs(rows: list[dict]) -> list[dict]:
    return [{key: value for key, value in row.items() if key != "id"} for row in rows]


def structured_graphic_diff(db: Session, *, project_id: int, unit_id: int, from_master_id: int, to_master_id: int, user: User) -> dict:
    owned_unit(db, project_id, unit_id, user)
    before = db.get(ContentMasterRevision, from_master_id)
    after = db.get(ContentMasterRevision, to_master_id)
    if before is None or after is None or any(row.project_id != project_id or row.content_unit_id != unit_id for row in (before, after)):
        raise HTTPException(404, "Master版本不存在")
    diff = diff_graphic_documents(_master_payload(db, before), _master_payload(db, after))
    before_refs, after_refs = _serialize(db, before), _serialize(db, after)
    before_assets, after_assets = _semantic_refs(before_refs["assets"]), _semantic_refs(after_refs["assets"])
    before_evidence, after_evidence = _semantic_refs(before_refs["evidence"]), _semantic_refs(after_refs["evidence"])
    old_render = (before.edit_summary_json or {}).get("render_attestation")
    new_render = (after.edit_summary_json or {}).get("render_attestation")
    return {
        "from_master_id": before.id,
        "to_master_id": after.id,
        "from_schema": before.payload_schema,
        "to_schema": after.payload_schema,
        **diff,
        "assets": {"changed": before_assets != after_assets, "before": before_assets, "after": after_assets},
        "evidence": {"changed": before_evidence != after_evidence, "before": before_evidence, "after": after_evidence},
        "render": {"changed": old_render != new_render, "before": old_render, "after": new_render},
        "context": {"changed": before.context_hash != after.context_hash, "before": before.context_hash, "after": after.context_hash},
        "payload": {"before_hash": before.payload_hash, "after_hash": after.payload_hash},
    }
