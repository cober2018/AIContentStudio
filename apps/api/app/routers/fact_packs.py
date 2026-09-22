"""FactPack API（STU-040~044）：创建、增删 item、冻结、克隆。"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_editor
from ..models import (
    AuditLog,
    ContentAsset,
    DeliveryTarget,
    DeliveryTargetStatus,
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
    fact_id: int | None = None
    evidence_kind: str = "fact"
    snapshot: dict | None = None
    # Existing internal-only workflows stay usable; neither external-model nor
    # public-delivery permission is ever inferred from these defaults.
    public_use_allowed: bool = False
    model_use_allowed: bool = False
    note: str | None = None
    sort_order: int = 0


class FactPackItemUpdateIn(BaseModel):
    evidence_kind: str | None = None
    snapshot: dict | None = None
    public_use_allowed: bool | None = None
    model_use_allowed: bool | None = None
    note: str | None = None
    sort_order: int | None = None


class PublicUseRevocationIn(BaseModel):
    note: str = Field(min_length=1, max_length=1000)


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
                "evidence_kind": item.evidence_kind,
                "snapshot_checksum": item.snapshot_checksum,
                "snapshot": item.snapshot_json,
                "ref": f"F{item.fact_id:03d}" if item.fact_id is not None else f"E{item.id:03d}",
                "statement": (item.snapshot_json or {}).get("statement") or (item.fact.statement if item.fact else None),
                "subject": (item.snapshot_json or {}).get("subject") or (item.fact.subject if item.fact else None),
                "predicate": (item.snapshot_json or {}).get("predicate") or (item.fact.predicate if item.fact else None),
                "value": (item.snapshot_json or {}).get("value") if item.snapshot_json else ((item.fact.value_json or {}).get("value") if item.fact else None),
                "unit": (item.snapshot_json or {}).get("unit") or (item.fact.unit if item.fact else None),
                "as_of": (item.snapshot_json or {}).get("as_of") or (item.fact.as_of if item.fact else None),
                "confidence": (item.snapshot_json or {}).get("confidence") or (item.fact.confidence if item.fact else None),
                "status": item.fact.status if item.fact else "legacy_untyped",
                "source_document_id": (item.snapshot_json or {}).get("source_id") or (item.fact.source_document_id if item.fact else None),
                "public_use_allowed": item.public_use_allowed,
                "public_use_revoked_at": item.public_use_revoked_at.isoformat() if item.public_use_revoked_at else None,
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
        db.add(FactPackItem(
            fact_pack_id=pack.id,
            fact_id=fact_id,
            sort_order=sort_order,
            evidence_kind="fact",
            public_use_allowed=False,
            model_use_allowed=False,
        ))
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
    if payload.evidence_kind not in {"fact", "event", "third_party_quote", "author_opinion"}:
        raise HTTPException(422, "evidence_kind 不受支持")
    fact = db.get(Fact, payload.fact_id) if payload.fact_id is not None else None
    if payload.evidence_kind in {"fact", "event"}:
        if not fact:
            raise HTTPException(404, "Fact 不存在")
        if fact.status not in {FactStatus.confirmed.value}:
            raise HTTPException(409, f"仅 confirmed 事实可加入 FactPack（当前 {fact.status}）")
        exists = db.scalars(
            select(FactPackItem).where(FactPackItem.fact_pack_id == pack_id, FactPackItem.fact_id == payload.fact_id)
        ).first()
        if exists:
            raise HTTPException(409, "该 Fact 已在 FactPack 中")
    elif not payload.snapshot:
        raise HTTPException(422, "引述或作者观点必须提供 snapshot")
    row = FactPackItem(
        fact_pack_id=pack_id,
        fact_id=payload.fact_id,
        evidence_kind=payload.evidence_kind,
        snapshot_json=payload.snapshot,
        public_use_allowed=payload.public_use_allowed,
        model_use_allowed=payload.model_use_allowed,
        note=payload.note,
        sort_order=payload.sort_order,
        fact=fact,
    )
    try:
        factpack_service.evidence_snapshot(row)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    db.add(row)
    db.commit()
    return _serialize(db.get(FactPack, pack_id), with_items=True)


@router.patch("/{pack_id}/items/{item_id}")
def update_item(
    pack_id: int,
    item_id: int,
    payload: FactPackItemUpdateIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_editor),
):
    pack = db.get(FactPack, pack_id)
    item = db.get(FactPackItem, item_id)
    if not pack or not item or item.fact_pack_id != pack_id:
        raise HTTPException(404, "Item 不存在")
    _require_draft(pack)
    for field in ("evidence_kind", "public_use_allowed", "model_use_allowed", "note", "sort_order"):
        value = getattr(payload, field)
        if value is not None:
            setattr(item, field, value)
    if payload.snapshot is not None:
        item.snapshot_json = payload.snapshot
    try:
        factpack_service.evidence_snapshot(item)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    db.commit()
    return _serialize(pack, with_items=True)


@router.post("/{pack_id}/items/{item_id}/revoke-public-use")
def revoke_item_public_use(
    pack_id: int,
    item_id: int,
    payload: PublicUseRevocationIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_editor),
):
    pack = db.get(FactPack, pack_id)
    item = db.get(FactPackItem, item_id)
    if not pack or not item or item.fact_pack_id != pack_id:
        raise HTTPException(404, "Item 不存在")
    if pack.status != FactPackStatus.frozen.value:
        raise HTTPException(409, "只有冻结证据包的公开权限撤销会影响交付目标")
    if not item.public_use_revoked_at:
        item.public_use_revoked_at = utcnow()
        item.public_use_revocation_note = payload.note
        asset_ids = list(db.scalars(select(ContentAsset.id).where(
            ContentAsset.fact_pack_id == pack_id,
            ContentAsset.mother_revision_id.is_not(None),
        )))
        targets = db.scalars(select(DeliveryTarget).where(
            DeliveryTarget.content_asset_id.in_(asset_ids),
            DeliveryTarget.status.not_in({DeliveryTargetStatus.human_confirmed.value, DeliveryTargetStatus.canceled.value}),
        )).all() if asset_ids else []
        for target in targets:
            target.status = DeliveryTargetStatus.blocked.value
            db.add(AuditLog(event="delivery_target.blocked", actor=user.email, entity_type="delivery_target", entity_id=str(target.id), detail_json={"reason": "evidence_public_use_revoked", "fact_pack_item_id": item.id}))
        db.add(AuditLog(event="fact_pack_item.public_use_revoked", actor=user.email, entity_type="fact_pack_item", entity_id=str(item.id), detail_json={"blocked_targets": len(targets), "note": payload.note}))
        db.commit()
    return _serialize(pack, with_items=True)


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
    facts = [item.fact for item in pack.items if item.fact is not None]
    conflicted = [f.id for f in facts if f.status == FactStatus.conflict.value]
    if conflicted:
        raise HTTPException(400, f"存在未解决冲突: {conflicted}")
    not_confirmed = [f.id for f in facts if f.status != FactStatus.confirmed.value]
    if not_confirmed:
        raise HTTPException(400, f"存在非 confirmed 事实: {not_confirmed}")

    pack.status = FactPackStatus.frozen.value
    pack.frozen_at = utcnow()
    for item in pack.items:
        try:
            item.snapshot_json = factpack_service.evidence_snapshot(item)
        except ValueError as exc:
            raise HTTPException(422, f"证据项 {item.id}: {exc}") from exc
        item.snapshot_checksum = factpack_service.snapshot_checksum(item.snapshot_json)
        item.snapshot_version = 1
    pack.checksum = factpack_service.pack_snapshot_checksum(pack.items)
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
        db.add(FactPackItem(
            fact_pack_id=clone.id,
            fact_id=item.fact_id,
            note=item.note,
            sort_order=item.sort_order,
            evidence_kind=item.evidence_kind,
            snapshot_json=dict(item.snapshot_json or {}),
            public_use_allowed=item.public_use_allowed,
            model_use_allowed=item.model_use_allowed,
        ))
    db.add(AuditLog(event="fact_pack.cloned", actor=user.email, entity_type="fact_pack", entity_id=str(clone.id),
                    detail_json={"parent_id": pack.id, "parent_version": pack.version}))
    db.commit()
    return _serialize(clone, with_items=True)
