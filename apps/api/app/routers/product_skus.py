"""SKU assets reuse the existing project, material and production contracts."""
import hashlib
import json
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import or_, select, update
from sqlalchemy.exc import IntegrityError

from ..db import get_db
from ..deps import get_current_user, require_editor
from ..models import (
    ContentMasterRevision,
    ContentProject,
    ContentUnit,
    MaterialRevision,
    ProductionProfileRevision,
    ProductSku,
    ProductSkuPlan,
    ProductSkuReference,
    ProductSkuRevision,
    ProductSkuWork,
)
from ..services.project_brief import ProductContext, validate_product_context

router = APIRouter(tags=["product-skus"])


class Feedback(BaseModel):
    model_config = ConfigDict(extra="forbid")
    location: str = Field(max_length=200)
    note: str = Field(max_length=4000)
    scope: Literal["work", "sku", "category", "style", "general"] = "work"


class SharedReference(BaseModel):
    model_config = ConfigDict(extra="forbid")
    material_revision_id: int = Field(gt=0)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    role: Literal["product", "person", "scene"]


class ProductionSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    shared_references: list[SharedReference] = Field(default_factory=list, max_length=30)
    production_stages: dict | None = None
    video_creative_profile: dict | None = None
    audio_creative_profile: dict | None = None
    model_profile_ref: str | None = Field(default=None, max_length=100)
    voice_id: str | None = Field(default=None, max_length=200)
    work_type: Literal["showcase", "scene", "ugc"] = "scene"
    creation_mode: Literal["original", "reference"] = "original"
    speech_mode: Literal["voiceover", "lip_sync", "none", "mixed"] = "voiceover"
    reference_notes: str = Field(default="", max_length=4000)
    visual_style: str = Field(default="", max_length=4000)
    continuity_notes: str = Field(default="", max_length=4000)
    comparison_notes: str = Field(default="", max_length=4000)
    dialogue: str = Field(default="", max_length=12000)
    dialogue_language: str = Field(default="中文", max_length=100)
    music_direction: str = Field(default="不使用配乐", max_length=2000)
    ae_packaging: bool = False
    target_duration_seconds: int | None = Field(default=None, gt=0, le=3600)
    estimated_voice_duration_seconds: float | None = Field(default=None, gt=0, le=3600, allow_inf_nan=False)
    feedback: Feedback | None = None


class SkuIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_key: str = Field(min_length=1, max_length=100)
    external_code: str = Field(default="", max_length=300)
    product: ProductContext
    primary_image_revision_id: int | None = Field(default=None, gt=0)
    primary_image_kind: Literal["primary", "reference"] = "primary"


class SkuUpdate(SkuIn):
    expected_revision: int = Field(ge=1)


class ProfileIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=0)
    settings: ProductionSettings


class WorkIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    launch_key: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_.:-]+$")
    expected_revision: int = Field(ge=1)
    persona_id: int | None = Field(default=None, gt=0)
    channel: str | None = Field(default=None, min_length=1, max_length=100)
    title: str | None = Field(default=None, max_length=300)
    objective: str = Field(default="基于已提供商品资料规划视频，未知事实待补。", min_length=1, max_length=3000)
    plan_id: int | None = Field(default=None, gt=0)


class PlanIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    include_methods: bool = True
    include_sound: bool = True
    name: str = Field(min_length=1, max_length=200)
    plan_key: str = Field(default_factory=lambda: uuid.uuid4().hex, max_length=100)
    expected_revision: int = Field(default=0, ge=0)
    settings: ProductionSettings
    source_unit_id: int | None = Field(default=None, gt=0)


class ReferenceIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    master_id: int = Field(gt=0)
    master_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def owned_sku(db, user, sku_id):
    row = db.get(ProductSku, sku_id)
    if not row or row.owner_user_id != user.id:
        raise HTTPException(404, "商品不存在")
    return row


def owned_unit(db, user, project_id, unit_id, mutable=False):
    project, unit = db.get(ContentProject, project_id), db.get(ContentUnit, unit_id)
    if not project or project.owner_user_id != user.id or not unit or unit.project_id != project_id:
        raise HTTPException(404, "作品不存在")
    if mutable and (project.status == "archived" or unit.lifecycle_readonly):
        raise HTTPException(409, "已归档作品不可修改")
    return unit


def validate_settings(db, user, settings, project_id=None):
    from ..models import ProjectMaterialReference
    from ..services.studio_creative_catalog import validate_production_stages
    try:
        if settings.get("production_stages") is not None:
            validate_production_stages(settings["production_stages"])
        from ..services.content_identity import CreativeProfile
        for field in ("video_creative_profile", "audio_creative_profile"):
            if settings.get(field) is not None:
                parsed = CreativeProfile.model_validate(settings[field]).model_dump(mode="json", by_alias=True)
                if parsed["schema"] != f"persona.creative.{field.split('_')[0]}.v1":
                    raise ValueError("creative_profile_modality_mismatch")
                settings[field] = parsed
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None
    for ref in settings.get("shared_references", []):
        revision = db.get(MaterialRevision, ref["material_revision_id"])
        if not revision or not revision.material or revision.material.status != "active" or revision.status in {"revoked", "archived"} or revision.content_hash != ref["content_hash"]:
            raise HTTPException(409, "共用参考素材不可用，请重新选择")
        visible = project_id and db.scalar(select(ProjectMaterialReference.id).where(ProjectMaterialReference.project_id == project_id,
            ProjectMaterialReference.material_revision_id == revision.id, ProjectMaterialReference.status == "active"))
        if revision.created_by != user.email and not visible:
            raise HTTPException(403, "共用参考需要本人素材或本项目明确引用")


def latest_profile(db, unit_id):
    return db.scalar(select(ProductionProfileRevision).where(ProductionProfileRevision.unit_id == unit_id)
        .order_by(ProductionProfileRevision.revision.desc()).limit(1))


def sku_revision(db, row):
    return db.scalar(select(ProductSkuRevision).where(ProductSkuRevision.sku_id == row.id,
        ProductSkuRevision.revision == row.revision))


def image_revision(db, data):
    if data.primary_image_revision_id is None:
        return None
    ref = next((r for r in data.product.material_refs if r.material_revision_id == data.primary_image_revision_id), None)
    revision = db.get(MaterialRevision, data.primary_image_revision_id)
    if not ref or not revision or not revision.material or revision.material.kind != "image" or not (revision.mime_type or "").startswith("image/"):
        raise HTTPException(422, "主图必须绑定本商品已选择的精确图片版本")
    if revision.material.status != "active" or revision.status in {"revoked", "archived"} or revision.content_hash != ref.content_hash:
        raise HTTPException(409, "图片版本不可用，请重新选择")
    if "ai_scene" in ref.categories and data.primary_image_kind == "primary":
        raise HTTPException(422, "AI情境图不能作为商品原始主图")
    return revision


def sku_json(db, row):
    rev = sku_revision(db, row)
    return {"id": row.id, "code": row.code, "revision": row.revision, "revision_id": rev.id,
        "external_code": rev.external_code, "product": rev.product_json,
        "primary_image_revision_id": rev.primary_image_revision_id, "primary_image_kind": rev.primary_image_kind,
        "image_url": f"/api/v1/product-skus/{row.id}/image?revision={rev.revision}" if rev.primary_image_revision_id else None,
        "default_plan_id": row.default_plan_id}


def commit(db):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "记录已被其他请求更新，请重新读取；本地输入保留") from None


@router.get("/product-skus")
def list_skus(q: str = Query(default="", max_length=300), category: str = Query(default="", max_length=300),
              offset: int = Query(default=0, ge=0), limit: int = Query(default=40, ge=1, le=100),
              db=Depends(get_db), user=Depends(get_current_user)):
    stmt = select(ProductSku).join(ProductSkuRevision, (ProductSkuRevision.sku_id == ProductSku.id) &
        (ProductSkuRevision.revision == ProductSku.revision)).where(ProductSku.owner_user_id == user.id)
    if q.strip():
        term = q.strip()
        stmt = stmt.where(or_(ProductSku.code.icontains(term, autoescape=True),
            ProductSkuRevision.external_code.icontains(term, autoescape=True),
            ProductSkuRevision.product_json["name"].as_string().icontains(term, autoescape=True)))
    if category:
        stmt = stmt.where(ProductSkuRevision.product_json["category"].as_string() == category)
    return {"items": [sku_json(db, r) for r in db.scalars(stmt.order_by(ProductSku.id.desc()).offset(offset).limit(limit))]}


@router.post("/product-skus", status_code=201)
def create_sku(payload: SkuIn, db=Depends(get_db), user=Depends(require_editor)):
    product = validate_product_context(db, payload.product, user=user)
    if not product["name"].strip() or not product["category"].strip():
        raise HTTPException(422, "请填写商品名称和品类")
    image_revision(db, payload)
    existing = db.scalar(select(ProductSku).where(ProductSku.owner_user_id == user.id, ProductSku.request_key == payload.request_key))
    if existing:
        old = sku_revision(db, existing)
        if old.product_json != product or old.external_code != payload.external_code or old.primary_image_revision_id != payload.primary_image_revision_id or old.primary_image_kind != payload.primary_image_kind:
            raise HTTPException(409, "此保存标识已用于其他商品资料")
        return sku_json(db, existing)
    row = ProductSku(owner_user_id=user.id, request_key=payload.request_key, revision=1)
    db.add(row)
    try:
        db.flush()
        row.code = f"SKU-{row.id:06d}"
        db.add(ProductSkuRevision(sku_id=row.id, revision=1, external_code=payload.external_code, product_json=product,
            primary_image_revision_id=payload.primary_image_revision_id, primary_image_kind=payload.primary_image_kind))
        commit(db)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "商品已由其他请求保存，请按原标识重试") from None
    return sku_json(db, row)


@router.get("/product-skus/{sku_id}")
def read_sku(sku_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    return sku_json(db, owned_sku(db, user, sku_id))


@router.put("/product-skus/{sku_id}")
def update_sku(sku_id: int, payload: SkuUpdate, db=Depends(get_db), user=Depends(require_editor)):
    row = owned_sku(db, user, sku_id)
    product = validate_product_context(db, payload.product, user=user)
    if not product["name"].strip() or not product["category"].strip():
        raise HTTPException(422, "请填写商品名称和品类")
    image_revision(db, payload)
    changed = db.execute(update(ProductSku).where(ProductSku.id == row.id, ProductSku.revision == payload.expected_revision)
        .values(revision=payload.expected_revision + 1))
    if not changed.rowcount:
        db.rollback()
        raise HTTPException(409, "商品资料已变化，请核对后重新保存")
    db.add(ProductSkuRevision(sku_id=row.id, revision=payload.expected_revision + 1, external_code=payload.external_code,
        product_json=product, primary_image_revision_id=payload.primary_image_revision_id, primary_image_kind=payload.primary_image_kind))
    commit(db)
    db.refresh(row)
    return sku_json(db, row)


@router.get("/product-skus/{sku_id}/image")
def read_image(sku_id: int, revision: int | None = Query(default=None, ge=1), db=Depends(get_db), user=Depends(get_current_user)):
    row = owned_sku(db, user, sku_id)
    rev = db.scalar(select(ProductSkuRevision).where(ProductSkuRevision.sku_id == row.id, ProductSkuRevision.revision == (revision or row.revision)))
    if not rev or not rev.primary_image_revision_id:
        raise HTTPException(404, "商品尚无主图")
    payload = SkuIn(request_key=row.request_key, product=rev.product_json,
        primary_image_revision_id=rev.primary_image_revision_id, primary_image_kind=rev.primary_image_kind)
    image = image_revision(db, payload)
    from ..services.materials import read_bytes_checked
    return Response(read_bytes_checked(db, image), media_type=image.mime_type, headers={"Cache-Control": "private, no-store"})


@router.get("/content-projects/{project_id}/units/{unit_id}/production-profile")
def read_profile(project_id: int, unit_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    owned_unit(db, user, project_id, unit_id)
    row = latest_profile(db, unit_id)
    link = db.scalar(select(ProductSkuWork).where(ProductSkuWork.unit_id == unit_id))
    return {"revision": row.revision if row else 0, "settings": {key: value for key, value in row.settings_json.items() if key in ProductionSettings.model_fields} if row else {},
        "sku_id": link.sku_id if link else None, "sku_revision_id": link.sku_revision_id if link else None,
        "plan_id": link.plan_id if link else None}


@router.put("/content-projects/{project_id}/units/{unit_id}/production-profile")
def save_profile(project_id: int, unit_id: int, payload: ProfileIn, db=Depends(get_db), user=Depends(require_editor)):
    owned_unit(db, user, project_id, unit_id, True)
    current = latest_profile(db, unit_id)
    if (current.revision if current else 0) != payload.expected_revision:
        raise HTTPException(409, "制作配置已变化，请核对后重新保存")
    settings = payload.settings.model_dump(mode="json")
    validate_settings(db, user, settings, project_id)
    unit = db.get(ContentUnit, unit_id)
    stages = settings.get("production_stages")
    if stages is None:
        stages = (settings.get("video_creative_profile") or {}).get("production_stages")
    if unit.production_domain == "product" and stages is not None:
        from ..services.creative_configuration import freeze_production_stages
        settings["product_production_methods"] = {"video": freeze_production_stages(db, user, unit, stages, origin="work_profile")}
    row = ProductionProfileRevision(unit_id=unit_id, revision=payload.expected_revision + 1,
        settings_json=settings, settings_hash=digest(settings), created_by=user.email)
    db.add(row)
    commit(db)
    return {"revision": row.revision, "settings": row.settings_json}


@router.post("/product-skus/{sku_id}/works", status_code=201)
def create_work(sku_id: int, payload: WorkIn, db=Depends(get_db), user=Depends(require_editor)):
    sku = owned_sku(db, user, sku_id)
    from ..models import ProductCreationLaunch
    launch_key = f"sku.{sku_id}.{payload.launch_key}"
    if len(launch_key) > 100:
        raise HTTPException(422, "发起标识过长")
    previous = db.scalar(select(ProductCreationLaunch).where(ProductCreationLaunch.owner_user_id == user.id, ProductCreationLaunch.launch_key == launch_key))
    if previous:
        existing_link = db.scalar(select(ProductSkuWork).where(ProductSkuWork.unit_id == previous.unit_id))
        if existing_link:
            old_revision = db.get(ProductSkuRevision, existing_link.sku_revision_id)
            old_project, old_unit = db.get(ContentProject, previous.project_id), db.get(ContentUnit, previous.unit_id)
            if (old_revision.revision != payload.expected_revision or ("persona_id" in payload.model_fields_set and old_unit.persona_id is not None and old_unit.persona_id != payload.persona_id)
                    or ("channel" in payload.model_fields_set and old_unit.channel_id != payload.channel) or old_project.objective != payload.objective
                    or (payload.title is not None and old_unit.title != payload.title)
                    or (payload.plan_id is not None and existing_link.plan_id != payload.plan_id)):
                raise HTTPException(409, "原发起标识已用于不同作品设置，请继续原作品或重新创建")
            from ..services.product_creation import launch_json
            return {**launch_json(previous), "href": f"/projects/{previous.project_id}/units/{previous.unit_id}/production?workstep=goal", "sku_id": sku.id}
    if payload.channel:
        from ..services.content_harness.channel_registry import resolve_channel
        channel = resolve_channel(db, payload.channel)
        if not channel or not any(form.artifact_kind == "video" for form in channel.content_forms):
            raise HTTPException(422, "此渠道未配置视频成片，请先制作，交付时再选渠道")
    if sku.revision != payload.expected_revision:
        raise HTTPException(409, "商品资料版本已变化，请重新读取")
    revision = sku_revision(db, sku)
    plan_id = payload.plan_id if payload.plan_id is not None else sku.default_plan_id
    plan = db.get(ProductSkuPlan, plan_id) if plan_id else None
    if plan_id and (not plan or plan.sku_id != sku.id):
        raise HTTPException(422, "创作方案不属于此商品")
    from ..services.product_creation import launch_json, save_launch
    from .product_creation import ProductLaunchIn
    product = ProductContext.model_validate(revision.product_json)
    # This intake saves a draft; generation is an explicit subsequent action.
    defaults = get_product_defaults(db, user)
    selected_settings = {**defaults.get("settings", {}), **(plan.settings_json if plan else {})}
    settings = ProductionSettings.model_validate(selected_settings).model_dump(mode="json")
    source_link = db.scalar(select(ProductSkuWork).where(ProductSkuWork.unit_id == plan.source_unit_id)) if plan and plan.source_unit_id else None
    source_project = source_link.project_id if source_link else None
    if source_link:
        owned_unit(db, user, source_link.project_id, source_link.unit_id)
    validate_settings(db, user, settings, source_project)
    body = ProductLaunchIn(launch_key=launch_key, persona_id=payload.persona_id, channel=payload.channel,
        production_stages=settings.get("production_stages"), creative_profile=settings.get("video_creative_profile"),
        audio_creative_profile=settings.get("audio_creative_profile"), fetch_product_url=False,
        title=payload.title, objective=payload.objective, primary_audience="", product_context=product,
        source_ids=[s.source_id for s in product.source_refs], material_revision_ids=[r.material_revision_id for r in product.material_refs])
    launch = save_launch(db, user, body)
    from ..models import ProjectMaterialReference
    attached = {ref.material_revision_id for ref in product.material_refs}
    for ref in settings.get("shared_references", []):
        if ref["material_revision_id"] not in attached:
            db.add(ProjectMaterialReference(project_id=launch.project_id, material_revision_id=ref["material_revision_id"],
                origin="system_reference", attached_by=user.email))
            attached.add(ref["material_revision_id"])
    db.add(ProductSkuWork(sku_id=sku.id, sku_revision_id=revision.id, project_id=launch.project_id,
        unit_id=launch.unit_id, plan_id=plan.id if plan else None, settings_snapshot_json=settings))
    current = latest_profile(db, launch.unit_id)
    if current:
        settings = {**current.settings_json, **{key: value for key, value in settings.items() if value is not None}}
    db.add(ProductionProfileRevision(unit_id=launch.unit_id, revision=(current.revision + 1) if current else 1,
        settings_json=settings, settings_hash=digest(settings), created_by=user.email))
    commit(db)
    return {**launch_json(launch), "href": f"/projects/{launch.project_id}/units/{launch.unit_id}/production?workstep=goal", "sku_id": sku.id}


@router.get("/product-skus/{sku_id}/works")
def list_works(sku_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    owned_sku(db, user, sku_id)
    items = []
    for link in db.scalars(select(ProductSkuWork).where(ProductSkuWork.sku_id == sku_id).order_by(ProductSkuWork.id.desc())):
        project, unit = db.get(ContentProject, link.project_id), db.get(ContentUnit, link.unit_id)
        if project.owner_user_id == user.id:
            items.append({"project_id": project.id, "unit_id": unit.id, "title": unit.title, "status": unit.status,
                "sku_revision_id": link.sku_revision_id, "plan_id": link.plan_id,
                "href": f"/projects/{project.id}/units/{unit.id}/production"})
    return {"items": items}


@router.get("/product-skus/{sku_id}/plans")
def list_plans(sku_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    owned_sku(db, user, sku_id)
    return {"items": [{"id": p.id, "name": p.name, "plan_key": p.plan_key, "revision": p.revision,
        "settings": p.settings_json, "source_unit_id": p.source_unit_id} for p in db.scalars(
        select(ProductSkuPlan).where(ProductSkuPlan.sku_id == sku_id).order_by(ProductSkuPlan.id.desc()))]}


@router.post("/product-skus/{sku_id}/plans", status_code=201)
def save_plan(sku_id: int, payload: PlanIn, db=Depends(get_db), user=Depends(require_editor)):
    owned_sku(db, user, sku_id)
    if payload.source_unit_id:
        link = db.scalar(select(ProductSkuWork).where(ProductSkuWork.unit_id == payload.source_unit_id, ProductSkuWork.sku_id == sku_id))
        if not link:
            raise HTTPException(422, "来源作品不属于此商品")
        owned_unit(db, user, link.project_id, link.unit_id)
    previous = db.scalar(select(ProductSkuPlan).where(ProductSkuPlan.sku_id == sku_id, ProductSkuPlan.plan_key == payload.plan_key)
        .order_by(ProductSkuPlan.revision.desc()).limit(1))
    if (previous.revision if previous else 0) != payload.expected_revision:
        raise HTTPException(409, "方案版本已变化，请重新读取")
    # Feedback stays task-local and never becomes reusable policy automatically.
    settings = payload.settings.model_dump(mode="json", exclude={"feedback", "comparison_notes"})
    if payload.source_unit_id:
        from ..services.product_context import effective_settings
        unit = db.get(ContentUnit, payload.source_unit_id)
        source_settings = effective_settings(db, unit)
        creative = source_settings.get("video_creative_profile")
        if payload.include_methods:
            inherited = {
                "video_creative_profile": creative,
                "production_stages": source_settings.get("production_stages") or (creative or {}).get("production_stages"),
                "model_profile_ref": source_settings.get("model_profile_ref") or ((creative or {}).get("model_binding") or {}).get("profile"),
            }
            for key, value in inherited.items():
                if settings.get(key) is None and value is not None:
                    settings[key] = value
        if payload.include_sound:
            for key in ("audio_creative_profile", "voice_id"):
                inherited = source_settings.get(key)
                if settings.get(key) is None and inherited is not None:
                    settings[key] = inherited
    validate_settings(db, user, settings, link.project_id if payload.source_unit_id else None)
    row = ProductSkuPlan(sku_id=sku_id, plan_key=payload.plan_key, revision=payload.expected_revision + 1,
        name=payload.name, settings_json=settings, source_unit_id=payload.source_unit_id)
    db.add(row)
    commit(db)
    return {"id": row.id, "revision": row.revision, "name": row.name, "settings": settings}


@router.put("/product-skus/{sku_id}/default-plan/{plan_id}")
def set_default(sku_id: int, plan_id: int, db=Depends(get_db), user=Depends(require_editor)):
    row = owned_sku(db, user, sku_id)
    plan = db.get(ProductSkuPlan, plan_id)
    if not plan or plan.sku_id != row.id:
        raise HTTPException(422, "方案不属于此商品")
    row.default_plan_id = plan.id
    commit(db)
    return sku_json(db, row)


@router.get("/product-skus/{sku_id}/references")
def list_references(sku_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    owned_sku(db, user, sku_id)
    return {"items": [{"id": r.id, "master_id": r.master_id, "master_hash": r.master_hash,
        "profile_revision_id": r.profile_revision_id,
        "href": f"/projects/{db.get(ContentMasterRevision, r.master_id).project_id}/units/{db.get(ContentMasterRevision, r.master_id).content_unit_id}/production?workstep=review&master={r.master_id}"} for r in db.scalars(select(ProductSkuReference).where(ProductSkuReference.sku_id == sku_id))]}


@router.post("/product-skus/{sku_id}/references", status_code=201)
def save_reference(sku_id: int, payload: ReferenceIn, db=Depends(get_db), user=Depends(require_editor)):
    owned_sku(db, user, sku_id)
    master = db.get(ContentMasterRevision, payload.master_id)
    if not master or master.payload_hash != payload.master_hash:
        raise HTTPException(409, "请读取已保存的精确作品版本")
    owned_unit(db, user, master.project_id, master.content_unit_id)
    link = db.scalar(select(ProductSkuWork).where(ProductSkuWork.sku_id == sku_id, ProductSkuWork.unit_id == master.content_unit_id))
    if not link:
        raise HTTPException(422, "参考作品不属于此商品")
    row = db.scalar(select(ProductSkuReference).where(ProductSkuReference.sku_id == sku_id, ProductSkuReference.master_id == master.id))
    if not row:
        profile = db.scalar(select(ProductionProfileRevision).where(ProductionProfileRevision.unit_id == master.content_unit_id,
            ProductionProfileRevision.created_at <= master.created_at).order_by(ProductionProfileRevision.revision.desc()).limit(1))
        row = ProductSkuReference(sku_id=sku_id, master_id=master.id, master_hash=master.payload_hash,
            profile_revision_id=profile.id if profile else None)
        db.add(row)
        commit(db)
    return {"id": row.id, "master_id": row.master_id, "master_hash": row.master_hash}


@router.get("/production-workspaces")
def workspace_rows(workspace: Literal["product", "persona"], db=Depends(get_db), user=Depends(get_current_user)):
    items = []
    for project in db.scalars(select(ContentProject).where(ContentProject.owner_user_id == user.id).order_by(ContentProject.id.desc())):
        units = list(db.scalars(select(ContentUnit).where(ContentUnit.project_id == project.id)))
        selected = [u for u in units if u.production_domain == workspace and u.lifecycle != "deleted"]
        if selected:
            items.append({"id": project.id, "title": project.title, "objective": project.objective, "status": project.status,
                "units": [{"id":u.id,"project_id":project.id,"title":u.title,"status":u.status,"lifecycle":u.lifecycle,"persona_id":u.persona_id,
                    "account_id":u.account_id,"series_id":u.series_id,"modality":u.modality,"channel_id":u.channel_id,
                    "production_domain":u.production_domain, "identity_snapshot_id":u.identity_snapshot_id,
                    "identity_state":"not_applicable" if u.production_domain == "product" else "resolved" if u.identity_snapshot_id else "unresolved",
                    "pinned_workflow_id":u.pinned_workflow_id} for u in selected]})
    return {"items": items}

class ProductDefaultsIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=0)
    settings: ProductionSettings


@router.get("/product-production-defaults")
def get_product_defaults(db=Depends(get_db), user=Depends(get_current_user)):
    from ..models import SystemSetting
    row = db.get(SystemSetting, f"product.production_defaults.{user.id}")
    return row.value if row else {"settings": {}, "revision": 0}


@router.put("/product-production-defaults")
def save_product_defaults(payload: ProductDefaultsIn, db=Depends(get_db), user=Depends(require_editor)):
    from ..models import SystemSetting
    key = f"product.production_defaults.{user.id}"
    current = db.get(SystemSetting, key)
    value = current.value if current else {"revision": 0, "settings": {}}
    if value["revision"] != payload.expected_revision:
        raise HTTPException(409, "商品默认配置已变化，请重新读取")
    settings = payload.settings.model_dump(mode="json", exclude_unset=True)
    validate_settings(db, user, settings)
    if settings.get("shared_references") or settings.get("feedback"):
        raise HTTPException(422, "商品基础默认不保存单次素材或反馈，请存到SKU方案")
    updated = {"revision": value["revision"] + 1, "settings": settings}
    if current:
        result = db.execute(update(SystemSetting).where(SystemSetting.key == key, SystemSetting.value == value)
            .values(value=updated, updated_by=user.email).execution_options(synchronize_session=False))
        if result.rowcount != 1:
            db.rollback()
            raise HTTPException(409, "商品默认配置已变化，请重新读取")
    else:
        db.add(SystemSetting(key=key, value=updated, updated_by=user.email))
    commit(db)
    return updated
