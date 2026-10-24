"""素材库：预览缩略图、播放流与素材合集。预览是按内容哈希缓存的派生图，不产生素材版本。"""

import base64
import hashlib
import hmac
import json
import os
import time
from contextlib import ExitStack
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_editor
from ..models import AuditLog, Material, MaterialCollection, MaterialCollectionItem, MaterialRevision, User, utcnow
from ..services import material_previews as previews

router = APIRouter(prefix="/api/v1", tags=["material-library"])
_STREAM_KEY = os.urandom(32)
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]


def _revision(db: Session, material_id: int, revision_id: int) -> MaterialRevision:
    row = db.get(MaterialRevision, revision_id)
    if row is None or row.material_id != material_id:
        raise HTTPException(404, {"code": "material_revision_not_found"})
    return row


@router.get("/materials/{material_id}/revisions/{revision_id}/thumbnail")
def material_thumbnail(material_id: int, revision_id: int, variant: Literal["thumb", "strip"] = "thumb",
                             db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    revision = _revision(db, material_id, revision_id)
    content, mime = previews.derivative(db, revision, variant)
    # Keyed by revision, whose bytes never change, so the browser may keep it.
    return Response(content=content, media_type=mime, headers={"Cache-Control": "private, max-age=604800, immutable"})


def _stream_path(material_id: int, revision_id: int) -> str:
    return f"/api/v1/materials/{material_id}/revisions/{revision_id}/stream"


@router.post("/materials/{material_id}/revisions/{revision_id}/stream-session")
def material_stream_session(material_id: int, revision_id: int, request: Request, response: Response,
                            db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    revision = _revision(db, material_id, revision_id)
    if previews.media_kind(revision) is None:
        raise HTTPException(422, {"code": "material_stream_unsupported"})
    with previews.source_path(db, revision):
        pass
    payload = base64.urlsafe_b64encode(json.dumps([user.id, revision.id, revision.content_hash, int(time.time()) + 1800],
                                                  separators=(",", ":")).encode()).decode()
    token = payload + "." + hmac.new(_STREAM_KEY, payload.encode(), hashlib.sha256).hexdigest()
    path = _stream_path(material_id, revision_id)
    # A media element cannot send the studio header, so a cookie scoped to this one URL carries the session.
    response.set_cookie("material_stream", token, max_age=1800, path=path, httponly=True, samesite="strict",
                        secure=request.url.scheme == "https")
    response.headers["Cache-Control"] = "no-store"
    return {"url": path, "expires_in": 1800, "mime_type": revision.mime_type}


@router.get("/materials/{material_id}/revisions/{revision_id}/stream")
def material_stream(material_id: int, revision_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        token, signature = request.cookies.get("material_stream", "").rsplit(".", 1)
        if not hmac.compare_digest(signature, hmac.new(_STREAM_KEY, token.encode(), hashlib.sha256).hexdigest()):
            raise ValueError()
        owner, signed_revision, digest, expiry = json.loads(base64.urlsafe_b64decode(token))
        user = db.get(User, owner)
        if signed_revision != revision_id or expiry < time.time() or user is None or not user.is_active:
            raise ValueError()
    except (ValueError, TypeError, KeyError):
        raise HTTPException(401, {"code": "material_stream_session_required"}) from None
    revision = _revision(db, material_id, revision_id)
    if revision.content_hash != digest:
        raise HTTPException(409, {"code": "material_stream_hash_mismatch"})
    stack = ExitStack()
    try:
        path = stack.enter_context(previews.source_path(db, revision))
        size, start, end = previews.ranged(path, request.headers.get("range"))
        source = stack.enter_context(open(path, "rb"))
        source.seek(start)

        def chunks():
            try:
                remaining = end - start + 1
                while remaining:
                    chunk = source.read(min(previews.CHUNK, remaining))
                    if not chunk:
                        return
                    remaining -= len(chunk)
                    yield chunk
            finally:
                stack.close()

        headers = {"Accept-Ranges": "bytes", "Content-Length": str(end - start + 1), "Cache-Control": "no-store",
                   "X-Content-Type-Options": "nosniff"}
        if request.headers.get("range"):
            headers["Content-Range"] = f"bytes {start}-{end}/{size}"
        return StreamingResponse(chunks(), status_code=206 if request.headers.get("range") else 200,
                                 media_type=revision.mime_type or "application/octet-stream", headers=headers)
    except BaseException:
        stack.close()
        raise


class CollectionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Name
    description: str | None = Field(default=None, max_length=5000)


class CollectionEdit(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(gt=0)
    name: Name | None = None
    description: str | None = Field(default=None, max_length=5000)


class CollectionItemIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(gt=0)
    material_id: int = Field(gt=0)
    note: str | None = Field(default=None, max_length=2000)


def _collection_json(db: Session, row: MaterialCollection) -> dict:
    count = db.scalar(select(func.count()).where(MaterialCollectionItem.collection_id == row.id))
    return {"id": row.id, "name": row.name, "description": row.description, "status": row.status, "revision": row.revision,
            "item_count": count, "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None}


def _owned(db: Session, collection_id: int, user: User, expected_revision: int | None = None) -> MaterialCollection:
    row = db.get(MaterialCollection, collection_id)
    if row is None or row.owner_user_id != user.id:
        raise HTTPException(404, {"code": "material_collection_not_found"})
    if expected_revision is not None:
        if row.status != "active":
            raise HTTPException(409, {"code": "material_collection_archived"})
        if row.revision != expected_revision:
            raise HTTPException(409, {"code": "material_collection_revision_conflict"})
    return row


def _touch(db: Session, row: MaterialCollection, user: User, event: str, detail: dict) -> dict:
    row.revision += 1
    row.updated_at = utcnow()
    db.add(AuditLog(event=event, actor=user.email, entity_type="material_collection", entity_id=str(row.id), detail_json=detail))
    db.commit()
    return _collection_json(db, row)


@router.get("/material-collections")
def list_collections(status: Literal["active", "archived"] = "active", db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(MaterialCollection).where(MaterialCollection.owner_user_id == user.id, MaterialCollection.status == status)
                      .order_by(MaterialCollection.updated_at.desc())).all()
    return {"items": [_collection_json(db, row) for row in rows]}


@router.post("/material-collections", status_code=201)
def create_collection(payload: CollectionIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    row = MaterialCollection(owner_user_id=user.id, name=payload.name, description=payload.description, created_by=user.email)
    db.add(row)
    db.flush()
    db.add(AuditLog(event="material_collection.created", actor=user.email, entity_type="material_collection", entity_id=str(row.id),
                    detail_json={"name": row.name}))
    db.commit()
    return _collection_json(db, row)


@router.patch("/material-collections/{collection_id}")
def edit_collection(collection_id: int, payload: CollectionEdit, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    row = _owned(db, collection_id, user, payload.expected_revision)
    changes = payload.model_dump(exclude_unset=True, exclude={"expected_revision"})
    if not changes or ("name" in changes and changes["name"] is None):
        raise HTTPException(422, {"code": "material_collection_edit_invalid"})
    for key, value in changes.items():
        setattr(row, key, value)
    return _touch(db, row, user, "material_collection.edited", {"fields": sorted(changes)})


@router.delete("/material-collections/{collection_id}")
def archive_collection(collection_id: int, expected_revision: Annotated[int, Query(gt=0)], db: Session = Depends(get_db),
                       user: User = Depends(require_editor)):
    row = _owned(db, collection_id, user, expected_revision)
    row.status = "archived"
    return _touch(db, row, user, "material_collection.archived", {})


@router.post("/material-collections/{collection_id}/items", status_code=201)
def add_collection_item(collection_id: int, payload: CollectionItemIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    row = _owned(db, collection_id, user, payload.expected_revision)
    material = db.get(Material, payload.material_id)
    if material is None or material.status != "active":
        raise HTTPException(404, {"code": "material_not_found"})
    db.add(MaterialCollectionItem(collection_id=row.id, material_id=material.id, note=payload.note, added_by=user.email))
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, {"code": "material_collection_item_exists"}) from None
    return _touch(db, row, user, "material_collection.item_added", {"material_id": material.id})


@router.delete("/material-collections/{collection_id}/items/{material_id}")
def remove_collection_item(collection_id: int, material_id: int, expected_revision: Annotated[int, Query(gt=0)],
                           db: Session = Depends(get_db), user: User = Depends(require_editor)):
    row = _owned(db, collection_id, user, expected_revision)
    item = db.scalar(select(MaterialCollectionItem).where(MaterialCollectionItem.collection_id == row.id,
                                                          MaterialCollectionItem.material_id == material_id))
    if item is None:
        raise HTTPException(404, {"code": "material_collection_item_not_found"})
    db.delete(item)
    return _touch(db, row, user, "material_collection.item_removed", {"material_id": material_id})


@router.get("/materials/{material_id}/collections")
def material_collections(material_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(MaterialCollection).join(MaterialCollectionItem, MaterialCollectionItem.collection_id == MaterialCollection.id)
                      .where(MaterialCollectionItem.material_id == material_id, MaterialCollection.owner_user_id == user.id,
                             MaterialCollection.status == "active")).all()
    return {"items": [_collection_json(db, row) for row in rows]}
