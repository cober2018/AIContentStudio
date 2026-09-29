"""Bounded, read-only structured diffs for Text Master history."""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import ContentMasterRevision, User
from .content_masters import _serialize, owned_unit
from .text_documents import TextDocumentError, canonical_payload, convert_legacy_text, document_hash


def _payload(master: ContentMasterRevision) -> dict:
    if master.payload_schema == "text.master.v2":
        try:
            return canonical_payload(master.payload_json)
        except TextDocumentError as exc:
            raise HTTPException(409, {"code": "master_document_invalid", "reason": str(exc)}) from exc
    if master.payload_schema == "text.master.v1":
        try:
            return convert_legacy_text(master.payload_json)["payload"]
        except TextDocumentError as exc:
            raise HTTPException(409, {"code": "legacy_master_not_comparable", "reason": str(exc)}) from exc
    raise HTTPException(409, {"code": "unsupported_text_master_schema"})


def _block_summary(block: dict) -> dict:
    return {"id": block["id"], "type": block["type"], "content_hash": document_hash({"schema": "studio.text.document.v1", "blocks": [block], "citations": []})}


def _semantic_refs(rows: list[dict]) -> list[dict]:
    # A copied exact reference receives a new database row ID on each Master revision.
    return [{key: value for key, value in row.items() if key != "id"} for row in rows]


def structured_diff(db: Session, *, project_id: int, unit_id: int, from_master_id: int, to_master_id: int, user: User) -> dict:
    owned_unit(db, project_id, unit_id, user)
    before = db.get(ContentMasterRevision, from_master_id)
    after = db.get(ContentMasterRevision, to_master_id)
    if before is None or after is None or before.project_id != project_id or after.project_id != project_id or before.content_unit_id != unit_id or after.content_unit_id != unit_id:
        raise HTTPException(404, "Master版本不存在")
    before_payload, after_payload = _payload(before), _payload(after)
    before_doc, after_doc = before_payload["document"], after_payload["document"]
    before_blocks = {block["id"]: block for block in before_doc["blocks"]}
    after_blocks = {block["id"]: block for block in after_doc["blocks"]}
    before_order = [block["id"] for block in before_doc["blocks"]]
    after_order = [block["id"] for block in after_doc["blocks"]]
    block_changes = []
    for block_id in before_order:
        if block_id not in after_blocks:
            block_changes.append({"kind": "remove", "block": _block_summary(before_blocks[block_id]), "from_index": before_order.index(block_id)})
    for block_id in after_order:
        if block_id not in before_blocks:
            block_changes.append({"kind": "add", "block": _block_summary(after_blocks[block_id]), "to_index": after_order.index(block_id)})
    for block_id in [item for item in after_order if item in before_blocks]:
        changes = []
        if before_order.index(block_id) != after_order.index(block_id):
            changes.append("move")
        if before_blocks[block_id] != after_blocks[block_id]:
            changes.append("modify")
        if changes:
            block_changes.append({"kind": changes[-1], "changes": changes, "block_id": block_id, "from_index": before_order.index(block_id), "to_index": after_order.index(block_id), "before": _block_summary(before_blocks[block_id]), "after": _block_summary(after_blocks[block_id])})
    before_refs = _serialize(db, before)
    after_refs = _serialize(db, after)
    before_assets, after_assets = _semantic_refs(before_refs["assets"]), _semantic_refs(after_refs["assets"])
    before_evidence, after_evidence = _semantic_refs(before_refs["evidence"]), _semantic_refs(after_refs["evidence"])
    before_summary, after_summary = before.edit_summary_json or {}, after.edit_summary_json or {}
    return {
        "from_master_id": before.id,
        "to_master_id": after.id,
        "from_schema": before.payload_schema,
        "to_schema": after.payload_schema,
        "title": {"changed": before_payload.get("title") != after_payload.get("title"), "before": before_payload.get("title"), "after": after_payload.get("title")},
        "blocks": block_changes,
        "assets": {"changed": before_assets != after_assets, "before": before_assets, "after": after_assets},
        "evidence": {"changed": before_evidence != after_evidence, "before": before_evidence, "after": after_evidence},
        "citations": {"changed": before_doc.get("citations", []) != after_doc.get("citations", []), "before": before_doc.get("citations", []), "after": after_doc.get("citations", [])},
        "ai_provenance": {"changed": before_summary.get("ai_provenance") != after_summary.get("ai_provenance"), "before": before_summary.get("ai_provenance"), "after": after_summary.get("ai_provenance")},
        "context": {"changed": before.context_hash != after.context_hash, "before": before.context_hash, "after": after.context_hash},
        "payload": {"before_hash": before.payload_hash, "after_hash": after.payload_hash, "document_hash_before": document_hash(before_doc), "document_hash_after": document_hash(after_doc)},
    }
