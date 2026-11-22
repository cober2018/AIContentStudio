"""效果复盘·角色表现。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models import User
from ..services.content_identity import owned_entity
from ..services.persona_performance import persona_timeline, personas_overview

router = APIRouter(prefix="/api/v1", tags=["learning"])


@router.get("/learning/personas")
def list_personas(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {"items": personas_overview(db, user)}


@router.get("/learning/personas/{persona_id}/timeline")
def get_timeline(persona_id: int, days: int = Query(default=90, ge=0, le=3650),
                 db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """0 天表示不限时间。"""
    owned_entity(db, user, "persona", persona_id)
    return persona_timeline(db, user, persona_id, days)
