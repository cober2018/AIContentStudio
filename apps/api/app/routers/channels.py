"""Channel Registry API（§6.3/§8.2）：前端渠道/内容形态唯一来源，取代本地常量。"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_admin
from ..models import User
from ..services.content_harness import channel_methods, channel_registry

router = APIRouter(prefix="/api/v1/channels", tags=["channels"])


@router.get("")
def list_channels(catalog: bool = Query(False), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """列出全部可用渠道与 content forms（profile 来源 + legacy 兜底）；catalog=true 时连同待接入的目标渠道。"""
    return channel_registry.list_channel_catalog(db) if catalog else channel_registry.list_channels(db)


@router.get("/plugins")
def list_channel_plugins(user: User = Depends(get_current_user)):
    """已安装的渠道方法，以及当前是插上还是拔出。不能从这里上传代码。"""
    return channel_methods.plugin_catalog()


@router.post("/plugins/{channel_key}/plug")
def plug_channel_plugin(channel_key: str, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    return channel_methods.set_plugged(db, channel_key, True, user.email)


@router.post("/plugins/{channel_key}/unplug")
def unplug_channel_plugin(channel_key: str, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    return channel_methods.set_plugged(db, channel_key, False, user.email)


@router.get("/{channel_key}")
def get_channel(channel_key: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if channel_key in channel_registry.RETIRED_CHANNELS:
        raise HTTPException(404, channel_registry.RETIRED_CHANNELS[channel_key])
    if channel_methods.is_unplugged(channel_key):
        raise HTTPException(404, channel_methods.unplugged_message(channel_key))
    spec = channel_registry.resolve_channel(db, channel_key)
    if spec is None:
        raise HTTPException(404, f"未知渠道: {channel_key}")
    return spec.to_dict()
