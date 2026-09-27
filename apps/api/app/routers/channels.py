"""Channel Registry API（§6.3/§8.2）：前端渠道/内容形态唯一来源，取代本地常量。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models import User
from ..services.content_harness import channel_registry

router = APIRouter(prefix="/api/v1/channels", tags=["channels"])


@router.get("")
def list_channels(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """列出全部可用渠道与 content forms（profile 来源 + legacy 兜底）。"""
    return channel_registry.list_channels(db)


@router.get("/{channel_key}")
def get_channel(channel_key: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    spec = channel_registry.resolve_channel(db, channel_key)
    if spec is None:
        raise HTTPException(404, f"未知渠道: {channel_key}")
    return spec.to_dict()
