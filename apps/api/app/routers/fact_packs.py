"""FactPack API（STU-040~044）：创建、增删 item、冻结、克隆。"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_editor
from ..models import (
    AuditLog,
    Fact,
    FactPack,
    FactPackItem,
    FactPackStatus,
    FactStatus,
    User,
    utcnow,
)
from ..services import factpack_service

router = APIRouter(prefix="/api/v1/fact-packs", tags=["fact-packs"])


class FactPackCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    description: str | None = None
    fact_ids: list[int] = Field(default_factory=list)


class FactPackItemIn(BaseModel):
    fact_id: int
    note: str | None = None
    sort_order: int = 0


def _serialize(pack: FactPack, with_items: bool = False) -> dict:
    data = {
        "id": pack.id,
        "name": pack.name,
        "description": pack.description,
        "version": pack.version,
        "status": pack.status,
        "parent_id": pack.parent_id,
        "checksum": pack.checksum,
        "frozen_at": pack.frozen_at.isoformat() if pack.frozen_at else None,
        "item_count": len(pack.items),
        "created_at": pack.created_at.isoformat() if pack.created_at else None,
    }
    if with_items:
        data["items"] = [
            {
                "item_id": item.id,
                "fact_id": item.fact_id,
                "ref": f"F{item.fact_id:03d}",
                "statement": item.fact.statement,
                "subject": item.fact.subject,
                "predicate": item.fact.predicate,
                "value": (item.fact.value_json or {}).get("value") if item.fact.value_json else None,
                "unit": item.fact.unit,
                "as_of": item.fact.as_of,
                "confidence": item.fact.confidence,
                "status": item.fact.status,
                "source_document_id": item.fact.source_document_id,
                "note": item.note,
                "sort_order": item.sort_order,
            }
            for item in pack.items
        ]
    return data


def _require_draft(pack: FactPack) -> None:
    if pack.status != FactPackStatus.draft.value:
        raise HTTPException(409, f"FactPack 已 {pack.status}，冻结版本不可修改，请 Clone 新版本")


@router.post("", status_code=201)
def create_fact_pack(
    payload: FactPackCreateIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_editor),
):
    max_version = (
        db.scalars(
            select(FactPack.version).where(FactPack.name == payload.name).order_by(FactPack.version.desc()).limit(1)
        ).first()
        or 0
    )
    pack = FactPack(
        name=payload.name,
        description=payload.description,
        version=max_version + 1,
        created_by=user.email,
    )
    db.add(pack)
    db.flush()
    for sort_order, fact_id in enumerate(payload.fact_ids):
        fact = db.get(Fact, fact_id)
        if not fact:
            raise HTTPException(404, f"Fact {fact_id} 不存在")
        db.add(FactPackItem(fact_pack_id=pack.id, fact_id=fact_id, sort_order=sort_order))
    db.commit()
    return _serialize(pack, with_items=True)


@router.get("")
def list_fact_packs(
    status: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(FactPack).order_by(FactPack.created_at.desc())
    if status:
        stmt = stmt.where(FactPack.status == status)
    return [_serialize(p) for p in db.scalars(stmt)]


@router.get("/{pack_id}")
def get_fact_pack(pack_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    pack = db.get(FactPack, pack_id)
    if not pack:
        raise HTTPException(404, "FactPack 不存在")
    return _serialize(pack, with_items=True)


@router.post("/{pack_id}/items", status_code=201)
def add_item(
    pack_id: int,
    payload: FactPackItemIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_editor),
):
    pack = db.get(FactPack, pack_id)
    if not pack:
        raise HTTPException(404, "FactPack 不存在")
    _require_draft(pack)
    fact = db.get(Fact, payload.fact_id)
    if not fact:
        raise HTTPException(404, "Fact 不存在")
    if fact.status not in {FactStatus.confirmed.value}:
        raise HTTPException(409, f"仅 confirmed 事实可加入 FactPack（当前 {fact.status}）")
    exists = db.scalars(
        select(FactPackItem).where(FactPackItem.fact_pack_id == pack_id, FactPackItem.fact_id == payload.fact_id)
    ).first()
    if exists:
        raise HTTPException(409, "该 Fact 已在 FactPack 中")
    db.add(FactPackItem(fact_pack_id=pack_id, fact_id=payload.fact_id, note=payload.note,
                        sort_order=payload.sort_order))
    db.commit()
    return _serialize(db.get(FactPack, pack_id), with_items=True)


@router.delete("/{pack_id}/items/{fact_id}")
def remove_item(
    pack_id: int,
    fact_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_editor),
):
    pack = db.get(FactPack, pack_id)
    if not pack:
        raise HTTPException(404, "FactPack 不存在")
    _require_draft(pack)
    item = db.scalars(
        select(FactPackItem).where(FactPackItem.fact_pack_id == pack_id, FactPackItem.fact_id == fact_id)
    ).first()
    if not item:
        raise HTTPException(404, "Item 不存在")
    db.delete(item)
    db.commit()
    return _serialize(db.get(FactPack, pack_id), with_items=True)


@router.post("/{pack_id}/freeze")
def freeze_fact_pack(pack_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    pack = db.get(FactPack, pack_id)
    if not pack:
        raise HTTPException(404, "FactPack 不存在")
    if pack.status == FactPackStatus.frozen.value:
        raise HTTPException(409, "FactPack 已冻结")
    if pack.status == FactPackStatus.archived.value:
        raise HTTPException(409, "FactPack 已归档，请 Clone")

    # 事务内校验（STU-042）：冲突优先于状态提示，便于定位根因
    if not pack.items:
        raise HTTPException(400, "FactPack 至少需要 1 个 Fact")
    facts = [item.fact for item in pack.items]
    conflicted = [f.id for f in facts if f.status == FactStatus.conflict.value]
    if conflicted:
        raise HTTPException(400, f"存在未解决冲突: {conflicted}")
    not_confirmed = [f.id for f in facts if f.status != FactStatus.confirmed.value]
    if not_confirmed:
        raise HTTPException(400, f"存在非 confirmed 事实: {not_confirmed}")

    pack.status = FactPackStatus.frozen.value
    pack.frozen_at = utcnow()
    pack.checksum = factpack_service.fact_checksum(facts)
    db.add(AuditLog(event="fact_pack.frozen", actor=user.email, entity_type="fact_pack", entity_id=str(pack.id),
                    detail_json={"version": pack.version, "checksum": pack.checksum}))
    db.commit()
    return _serialize(pack, with_items=True)


@router.post("/{pack_id}/clone", status_code=201)
def clone_fact_pack(pack_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    pack = db.get(FactPack, pack_id)
    if not pack:
        raise HTTPException(404, "FactPack 不存在")

    max_version = (
        db.scalars(
            select(FactPack.version).where(FactPack.name == pack.name).order_by(FactPack.version.desc()).limit(1)
        ).first()
        or pack.version
    )
    clone = FactPack(
        name=pack.name,
        description=pack.description,
        version=max_version + 1,
        parent_id=pack.id,
        created_by=user.email,
    )
    db.add(clone)
    db.flush()
    for item in pack.items:
        db.add(FactPackItem(fact_pack_id=clone.id, fact_id=item.fact_id, note=item.note,
                            sort_order=item.sort_order))
    db.add(AuditLog(event="fact_pack.cloned", actor=user.email, entity_type="fact_pack", entity_id=str(clone.id),
                    detail_json={"parent_id": pack.id, "parent_version": pack.version}))
    db.commit()
    return _serialize(clone, with_items=True)
