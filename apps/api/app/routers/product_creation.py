"""Product-driven entry; ordinary projects own every downstream artifact."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select

from ..db import get_db
from ..deps import get_current_user, require_editor
from ..models import ProductCreationLaunch
from ..services import product_creation as service
from ..services.project_brief import ProductContext

router = APIRouter(prefix="/content-projects", tags=["product-creation"])


class ProductLaunchIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    launch_key: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_.:-]+$")
    title: str | None = Field(default=None, max_length=300)
    objective: str = Field(min_length=1, max_length=3000)
    persona_id: int = Field(gt=0)
    primary_audience: str | None = Field(default=None, max_length=2000)
    channel: str = Field(min_length=1, max_length=100)
    modality: Literal["text", "graphic", "video"] = "video"
    cta: str | None = Field(default=None, max_length=2000)
    workflow_id: int | None = Field(default=None, gt=0)
    product_context: ProductContext
    production_stages: dict | None = None
    source_ids: list[int] = Field(default_factory=list, max_length=30)
    material_revision_ids: list[int] = Field(default_factory=list, max_length=30)

    @model_validator(mode="after")
    def validate_methods(self):
        if self.production_stages is not None:
            from ..services.studio_creative_catalog import validate_production_stages

            validate_production_stages(self.production_stages)
        return self



@router.post("/from-product", status_code=201)
def start_product(payload: ProductLaunchIn, db=Depends(get_db), user=Depends(require_editor)):
    try:
        launch = service.save_launch(db, user, payload)
        return service.resume_launch(db, user, launch)
    except (HTTPException, ValueError) as exc:
        db.rollback()
        existing = db.scalar(select(ProductCreationLaunch).where(ProductCreationLaunch.owner_user_id == user.id,
            ProductCreationLaunch.launch_key == payload.launch_key))
        raise HTTPException(exc.status_code if isinstance(exc, HTTPException) else 422, detail={"code": "product_creation_input_rejected",
            "message": str(exc.detail) if isinstance(exc, HTTPException) else str(exc), "project_created": existing is not None,
            "launch": service.launch_json(existing) if existing else None}) from None


@router.get("/{project_id}/product-launch")
def read_product_launch(project_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    row = db.scalar(select(ProductCreationLaunch).where(ProductCreationLaunch.project_id == project_id,
                                                       ProductCreationLaunch.owner_user_id == user.id))
    return service.launch_json(row) if row else None


@router.post("/{project_id}/product-launch/resume")
def resume_product(project_id: int, db=Depends(get_db), user=Depends(require_editor)):
    row = db.scalar(select(ProductCreationLaunch).where(ProductCreationLaunch.project_id == project_id,
                                                       ProductCreationLaunch.owner_user_id == user.id))
    if not row:
        raise HTTPException(404, "商品创作记录不存在")
    return service.resume_launch(db, user, row)


@router.post("/{project_id}/product-research")
def research_product(project_id: int, db=Depends(get_db), user=Depends(require_editor)):
    from ..services.discovery_runtime import settings
    from ..services.discovery_search import SearchUnavailable, search
    from ..services.project_brief import current_brief
    from ..services.project_events import record_project_event

    launch = db.scalar(select(ProductCreationLaunch).where(ProductCreationLaunch.project_id == project_id,
                                                          ProductCreationLaunch.owner_user_id == user.id))
    if not launch:
        raise HTTPException(404, "商品项目不存在")
    from ..models import ContentProject
    project = db.get(ContentProject, project_id)
    if project.status == "archived":
        raise HTTPException(409, "已归档项目不可研究")
    brief = current_brief(db, project_id)
    product = brief.product_context_json if brief else None
    if not product:
        raise HTTPException(409, "请先保存商品资料")
    config = settings(db, user.id)
    # Private descriptions, source bodies and media never become search queries.
    query = f"{product['name']} {product.get('variant', '')} 官方说明 使用场景"[:500]
    try:
        results = search(query, provider=config["search_provider"], credential_source=config["credential_source"], limit=5)
    except SearchUnavailable as exc:
        raise HTTPException(503, str(exc)) from None
    record_project_event(db, project_id=project_id, event_type="product.research_completed", actor=user.email,
        entity_type="product_creation_launch", entity_id=launch.id,
        payload={"provider": config["search_provider"], "query": query, "urls": [r["url"] for r in results],
                 "brief_revision_id": brief.id})
    db.commit()
    return {"results": results, "note": "公开搜索线索；导入、确认和冻结沿用来源与证据流程"}
