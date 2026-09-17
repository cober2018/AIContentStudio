"""外部内容入库 API（dsh/Agent skills → Studio 汇聚协议）。"""

import json

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_editor
from ..models import AuditLog, ExternalContent, User

router = APIRouter(prefix="/api/v1", tags=["external"])

CHANNELS = {"douyin", "xiaohongshu", "wechat", "other"}
ORIGINS = {"dsh", "antigravity", "manual"}
STATUSES = {"draft", "published", "archived"}


class IngestIn(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    body: str = Field(min_length=1)
    channel: str = "other"
    origin: str = "dsh"
    origin_ref: str | None = Field(default=None, max_length=500)
    tags: list[str] | None = None
    metadata: dict | None = None


class ExternalUpdateIn(BaseModel):
    title: str | None = None
    body: str | None = None
    status: str | None = None
    tags: list[str] | None = None


def _serialize(c: ExternalContent) -> dict:
    return {
        "id": c.id,
        "title": c.title,
        "channel": c.channel,
        "origin": c.origin,
        "origin_ref": c.origin_ref,
        "status": c.status,
        "tags": c.tags or [],
        "metadata": c.metadata_json or {},
        "created_by": c.created_by,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


@router.post("/assets/ingest", status_code=201)
def ingest(payload: IngestIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    """外部产出入库。同 (origin, origin_ref) 重复上报返回已有记录（幂等，200）。"""
    if payload.channel not in CHANNELS:
        raise HTTPException(400, f"channel 只允许 {sorted(CHANNELS)}")
    if payload.origin not in ORIGINS:
        raise HTTPException(400, f"origin 只允许 {sorted(ORIGINS)}")

    if payload.origin_ref:
        existing = db.scalar(
            select(ExternalContent).where(
                ExternalContent.origin == payload.origin,
                ExternalContent.origin_ref == payload.origin_ref,
            )
        )
        if existing:
            return Response(
                content=json.dumps({**_serialize(existing), "deduplicated": True}, ensure_ascii=False),
                status_code=200,
                media_type="application/json",
            )

    content = ExternalContent(
        title=payload.title,
        body=payload.body,
        channel=payload.channel,
        origin=payload.origin,
        origin_ref=payload.origin_ref,
        tags=payload.tags,
        metadata_json=payload.metadata,
        created_by=user.email,
    )
    db.add(content)
    db.add(AuditLog(event="external.ingested", actor=user.email, entity_type="external_content",
                    detail_json={"origin": payload.origin, "origin_ref": payload.origin_ref}))
    db.commit()
    return _serialize(content)


@router.get("/external-contents")
def list_external(
    status: str | None = None,
    channel: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(ExternalContent).order_by(ExternalContent.id.desc())
    if status:
        stmt = stmt.where(ExternalContent.status == status)
    if channel:
        stmt = stmt.where(ExternalContent.channel == channel)
    return [_serialize(c) for c in db.scalars(stmt)]


@router.get("/external-contents/{content_id}")
def get_external(content_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    content = db.get(ExternalContent, content_id)
    if not content:
        raise HTTPException(404, "内容不存在")
    data = _serialize(content)
    data["body"] = content.body
    return data


@router.patch("/external-contents/{content_id}")
def update_external(
    content_id: int,
    payload: ExternalUpdateIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_editor),
):
    content = db.get(ExternalContent, content_id)
    if not content:
        raise HTTPException(404, "内容不存在")
    if payload.status and payload.status not in STATUSES:
        raise HTTPException(400, f"status 只允许 {sorted(STATUSES)}")
    if payload.title is not None:
        content.title = payload.title
    if payload.body is not None:
        content.body = payload.body
    if payload.status is not None:
        content.status = payload.status
    if payload.tags is not None:
        content.tags = payload.tags
    db.commit()
    return _serialize(content)
