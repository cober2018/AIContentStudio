"""Read-only safe Settings projections; mutation gates stay in existing routers."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models import User
from ..services import product_settings

router = APIRouter(prefix="/api/v1/settings", tags=["product-settings"])


@router.get("/product")
def product(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return product_settings.product_view(db, user)


@router.get("/data-sources")
def data_sources(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return product_settings.data_sources_section(db, user, limit, offset)


@router.get("/channels")
def channels(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return product_settings.channels_section(db, user)


@router.get("/rules")
def rules(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return product_settings.rules_section(db, user, limit, offset)


@router.get("/team")
def team(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return product_settings.team_section(db, user)
