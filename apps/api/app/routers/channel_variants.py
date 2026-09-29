"""Project-scoped immutable ChannelVariant read API."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models import User
from ..services.channel_variants import current_revision, get_revision, list_revisions

router = APIRouter(prefix="/api/v1", tags=["channel-variants"])


@router.get("/content-projects/{project_id}/units/{unit_id}/channel-variants")
def list_channel_variants(project_id: int, unit_id: int, variant_key: str | None = Query(default=None, max_length=120), limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {"items": list_revisions(db, project_id, unit_id, user, variant_key=variant_key, limit=limit, offset=offset), "limit": limit, "offset": offset}


@router.get("/content-projects/{project_id}/units/{unit_id}/channel-variants/current")
def get_current_channel_variant(project_id: int, unit_id: int, variant_key: str = Query(min_length=1, max_length=120), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return current_revision(db, project_id, unit_id, variant_key, user)


@router.get("/content-projects/{project_id}/units/{unit_id}/channel-variants/{variant_id}")
def get_channel_variant(project_id: int, unit_id: int, variant_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_revision(db, project_id, unit_id, variant_id, user)
