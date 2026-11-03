"""网上搜素材：搜索记录只存链接，用户勾选的图才下载入库。"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_admin, require_editor
from ..models import User
from ..services import web_material_search

router = APIRouter(prefix="/api/v1", tags=["web-material-search"])


class SearchIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(min_length=2, max_length=120)
    sku_id: int | None = Field(default=None, gt=0)
    project_id: int | None = Field(default=None, gt=0)
    unit_id: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def _target(self):
        if not (self.sku_id or self.project_id or self.unit_id):
            raise ValueError("sku_id or project_id required")
        return self


class AcceptIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    image_ids: list[str] = Field(min_length=1, max_length=20)


class SitesIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sites: list[str] = Field(max_length=50)


@router.post("/web-material-searches", status_code=202)
def start(payload: SearchIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return web_material_search.start(db, user, **payload.model_dump())


@router.get("/web-material-searches/latest")
def latest(sku_id: Annotated[int | None, Query(gt=0)] = None, project_id: Annotated[int | None, Query(gt=0)] = None,
           db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {"search": web_material_search.latest(db, user, sku_id=sku_id, project_id=project_id)}


@router.get("/web-material-searches/{search_id}")
def read(search_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return web_material_search.read(db, user, search_id)


@router.get("/web-material-searches/{search_id}/images/{image_id}")
def preview(search_id: int, image_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    content, mime = web_material_search.preview(db, user, search_id, image_id)
    return Response(content=content, media_type=mime, headers={"Cache-Control": "private, max-age=3600"})


@router.post("/web-material-searches/{search_id}/accept", status_code=201)
def accept(search_id: int, payload: AcceptIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return web_material_search.accept(db, user, search_id, payload.image_ids)


@router.post("/web-material-searches/{search_id}/pages/{page_id}/source", status_code=201)
def save_source(search_id: int, page_id: str, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return web_material_search.save_source(db, user, search_id, page_id)


@router.get("/settings/web-material-sites")
def get_sites(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {"sites": web_material_search.sites(db)}


@router.put("/settings/web-material-sites")
def put_sites(payload: SitesIn, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    return web_material_search.put_sites(db, user, payload.sites)
