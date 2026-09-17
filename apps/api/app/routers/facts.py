"""Fact API（STU-032~034）。"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_editor
from ..models import AuditLog, Fact, FactStatus, User
from ..services.factpack_service import detect_conflicts

router = APIRouter(prefix="/api/v1/facts", tags=["facts"])


class FactUpdateIn(BaseModel):
    statement: str | None = None
    subject: str | None = None
    predicate: str | None = None
    value: float | str | None = None
    unit: str | None = None
    as_of: str | None = None
    note: str | None = None
    status: FactStatus | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)


class BulkStatusIn(BaseModel):
    fact_ids: list[int]
    action: str  # confirm / reject


def _serialize(f: Fact) -> dict:
    return {
        "id": f.id,
        "ref": f"F{f.id:03d}",
        "source_document_id": f.source_document_id,
        "source_title": f.source_document.title,
        "statement": f.statement,
        "fact_type": f.fact_type,
        "subject": f.subject,
        "predicate": f.predicate,
        "value": (f.value_json or {}).get("value") if f.value_json else None,
        "unit": f.unit,
        "as_of": f.as_of,
        "confidence": f.confidence,
        "status": f.status,
        "note": f.note,
        "source_locator": f.source_locator_json,
        "revision": f.revision,
    }


@router.get("")
def list_facts(
    source_id: int | None = None,
    status: str | None = None,
    subject: str | None = None,
    fact_type: str | None = None,
    as_of: str | None = None,
    conflict_only: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Fact).order_by(Fact.id)
    if source_id:
        stmt = stmt.where(Fact.source_document_id == source_id)
    if status:
        stmt = stmt.where(Fact.status == status)
    if fact_type:
        stmt = stmt.where(Fact.fact_type == fact_type)
    if as_of:
        stmt = stmt.where(Fact.as_of == as_of)
    if subject:
        stmt = stmt.where(Fact.subject.ilike(f"%{subject}%"))
    if conflict_only:
        stmt = stmt.where(Fact.status == FactStatus.conflict.value)
    return [_serialize(f) for f in db.scalars(stmt)]


@router.patch("/{fact_id}")
def update_fact(
    fact_id: int,
    payload: FactUpdateIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_editor),
):
    fact = db.get(Fact, fact_id)
    if not fact:
        raise HTTPException(404, "Fact 不存在")

    changed = False
    if payload.statement is not None:
        fact.statement = payload.statement
        changed = True
    if payload.subject is not None:
        fact.subject = payload.subject
        changed = True
    if payload.predicate is not None:
        fact.predicate = payload.predicate
        changed = True
    if payload.value is not None:
        fact.value_json = {"value": payload.value}
        changed = True
    if payload.unit is not None:
        fact.unit = payload.unit
        changed = True
    if payload.as_of is not None:
        fact.as_of = payload.as_of
        changed = True
    if payload.note is not None:
        fact.note = payload.note
    if payload.confidence is not None:
        fact.confidence = payload.confidence
    if changed:
        fact.revision += 1
        fact.updated_by = user.email
        if fact.status == FactStatus.confirmed.value:
            # confirmed 事实内容变更后需要重算冲突
            detect_conflicts(db)
    db.commit()
    return _serialize(fact)


@router.post("/{fact_id}/confirm")
def confirm_fact(fact_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    fact = db.get(Fact, fact_id)
    if not fact:
        raise HTTPException(404, "Fact 不存在")
    if fact.status == FactStatus.rejected.value:
        raise HTTPException(409, "已拒绝的 Fact 不能直接确认，请先编辑")
    fact.status = FactStatus.confirmed.value
    fact.updated_by = user.email
    detect_conflicts(db)
    db.add(AuditLog(event="fact.confirmed", actor=user.email, entity_type="fact", entity_id=str(fact_id)))
    db.commit()
    return _serialize(fact)


@router.post("/{fact_id}/reject")
def reject_fact(fact_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    fact = db.get(Fact, fact_id)
    if not fact:
        raise HTTPException(404, "Fact 不存在")
    fact.status = FactStatus.rejected.value
    fact.updated_by = user.email
    db.add(AuditLog(event="fact.rejected", actor=user.email, entity_type="fact", entity_id=str(fact_id)))
    db.commit()
    return _serialize(fact)


@router.post("/bulk-status")
def bulk_status(payload: BulkStatusIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    if payload.action not in {"confirm", "reject"}:
        raise HTTPException(400, "action 仅支持 confirm / reject")
    facts = [db.get(Fact, fid) for fid in payload.fact_ids]
    missing = [fid for fid, f in zip(payload.fact_ids, facts, strict=True) if f is None]
    if missing:
        raise HTTPException(404, f"Fact 不存在: {missing}")
    target = FactStatus.confirmed.value if payload.action == "confirm" else FactStatus.rejected.value
    for f in facts:
        f.status = target  # type: ignore[union-attr]
        f.updated_by = user.email  # type: ignore[union-attr]
    if payload.action == "confirm":
        detect_conflicts(db)
    db.commit()
    return {"updated": len(payload.fact_ids)}
