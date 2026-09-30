"""Material Library API（§6.15）：全局素材复用、权利链路、Draft use/placement。

- search/generate 无 provider 时返回 422 capability_unavailable，不返回假数据；
- 已批准候选引用的素材不可删除/变更（替换=新 Revision）；
- 旧 DraftMedia（无 material_revision_id）保持可读。
"""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_editor
from ..models import (
    AuditLog,
    ContentAsset,
    Draft,
    DraftMedia,
    DraftStatus,
    Material,
    MaterialRevision,
    User,
    utcnow,
)
from ..services import document_composition
from ..services import materials as materials_service
from ..services.content_harness.providers import CapabilityUnavailable
from ..services.project_authorization import authorize_project_draft
from . import CapabilityInputRoute

router = APIRouter(prefix="/api/v1", tags=["materials"], route_class=CapabilityInputRoute)

ROLES = {"cover", "inline", "attachment"}


class ProviderStageIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider_kind: Literal["image_provider", "video_provider", "tts_provider"]
    provider_key: str = Field(pattern=r"^[A-Za-z0-9_.-]{1,150}$")
    provider_version: str = Field(pattern=r"^[A-Za-z0-9_.-]{1,50}$")
    prompt: str = Field(min_length=1, max_length=2000)
    project_id: int | None = Field(default=None, ge=1)
    source_revision_ids: list[int] = Field(default_factory=list, max_length=4)


class ProviderAcceptIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    confirmed: bool
    title: str = Field(min_length=1, max_length=200)
    license_code: Literal["CC0", "CC-BY-4.0", "provider_terms", "owned"]
    license_evidence_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    public_use_allowed: bool
    model_use_allowed: bool
    commercial_use_allowed: bool
    attribution_text: str | None = Field(default=None, max_length=1000)


class ProviderSearchIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider_key: str = Field(pattern=r"^[A-Za-z0-9_.-]{1,150}$")
    provider_version: str = Field(pattern=r"^[A-Za-z0-9_.-]{1,50}$")
    query: str = Field(min_length=1, max_length=300)
    limit: int = Field(default=10, ge=1, le=10)


class SearchStageIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: int | None = Field(default=None, ge=1)


@router.post("/provider-search")
def search_provider_media(payload: ProviderSearchIn, user: User = Depends(require_editor)):
    from ..services import material_search

    return material_search.search(user, key=payload.provider_key, version=payload.provider_version, query=payload.query, limit=payload.limit)


@router.post("/provider-search/{candidate_id}/stage")
def stage_search_media(candidate_id: str, payload: SearchStageIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    from ..services import material_search

    return material_search.stage(db, user, candidate_id, payload.project_id)


@router.post("/provider-media/stage")
def stage_provider_media(payload: ProviderStageIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    from ..services import provider_media

    return provider_media.stage(db, user, payload.model_dump())


@router.get("/provider-media/{stage_id}/raw")
def preview_provider_media(stage_id: str, user: User = Depends(get_current_user)):
    from ..services import provider_media

    content, mime = provider_media.preview_bytes(stage_id, user)
    return Response(content=content, media_type=mime, headers={"Cache-Control": "private, no-store"})


@router.post("/provider-media/{stage_id}/accept", status_code=201)
def accept_provider_media(stage_id: str, payload: ProviderAcceptIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    from ..services import provider_media

    return provider_media.accept(db, user, stage_id, payload.model_dump())


class MaterialAttachIn(BaseModel):
    material_revision_id: int
    role: str = "inline"
    sort_order: int | None = None
    alt_text: str | None = None
    caption: str | None = None
    placement: dict | None = None


class MaterialPatchIn(BaseModel):
    role: str | None = None
    sort_order: int | None = None
    alt_text: str | None = None
    caption: str | None = None
    placement: dict | None = None


class RevocationIn(BaseModel):
    note: str = Field(min_length=1, max_length=1000)


class SearchIn(BaseModel):
    query: str = Field(min_length=1, max_length=300)
    limit: int = Field(default=10, ge=1, le=10)


class GenerateIn(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000)
    title: str | None = None
    draft_id: int | None = None
    role: str = "inline"


class DocumentIn(BaseModel):
    blocks: list[dict]


def _revision_json(row: MaterialRevision) -> dict:
    return {
        "id": row.id,
        "material_id": row.material_id,
        "revision_no": row.revision_no,
        "parent_revision_id": row.parent_revision_id,
        "status": row.status,
        "source_kind": row.source_kind,
        "source_url": row.source_url,
        "content_hash": row.content_hash,
        "mime_type": row.mime_type,
        "rights_status": row.rights_status,
        "public_use_allowed": row.public_use_allowed,
        "model_use_allowed": row.model_use_allowed,
        "commercial_use_allowed": row.commercial_use_allowed,
        "attribution_text": row.attribution_text,
        "provider_key": row.provider_key,
        "prompt_text": row.prompt_text,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def _material_json(row: Material, *, with_revisions: bool = False) -> dict:
    data = {
        "id": row.id,
        "kind": row.kind,
        "title": row.title,
        "tags": row.tags_json or [],
        "status": row.status,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "latest_revision": _revision_json(row.revisions[-1]) if row.revisions else None,
    }
    if with_revisions:
        data["revisions"] = [_revision_json(r) for r in row.revisions]
    return data


def _media_json(row: DraftMedia) -> dict:
    return {
        "id": row.id,
        "draft_id": row.draft_id,
        "content_hash": row.content_hash,
        "role": row.role,
        "sort_order": row.sort_order,
        "mime_type": row.mime_type,
        "rights_status": row.rights_status,
        "public_use_allowed": row.public_use_allowed,
        "material_revision_id": row.material_revision_id,
        "placement": row.placement_json or {},
        "alt_text": row.alt_text,
        "caption": row.caption,
        "metadata": row.metadata_json or {},
    }


def _get_revision(db: Session, material_id: int, revision_id: int) -> MaterialRevision:
    row = db.get(MaterialRevision, revision_id)
    if not row or row.material_id != material_id:
        raise HTTPException(404, "素材版本不存在")
    return row


def _own_media(db: Session, draft_id: int, media_id: int) -> tuple[Draft, DraftMedia]:
    draft = db.get(Draft, draft_id)
    row = db.get(DraftMedia, media_id)
    if not draft or not row or row.draft_id != draft_id:
        raise HTTPException(404, "素材 use 不存在")
    return draft, row


# ---------- Material ----------


@router.get("/materials")
def list_materials(
    kind: str | None = None,
    status: str = "active",
    q: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Material).order_by(Material.id.desc())
    if status:
        stmt = stmt.where(Material.status == status)
    if kind:
        stmt = stmt.where(Material.kind == kind)
    if q:
        stmt = stmt.where(Material.title.contains(q))
    return [_material_json(m) for m in db.scalars(stmt.limit(200))]


@router.post("/materials/upload", status_code=201)
async def upload_material(
    file: UploadFile,
    kind: str = "image",
    title: str | None = None,
    source_kind: str = "upload",
    rights_status: str = "cleared",
    public_use_allowed: bool = False,
    model_use_allowed: bool = False,
    attribution_text: str | None = None,
    source_url: str | None = None,
    tags: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_editor),
):
    content = await file.read()
    suffix = (file.filename or "").rsplit(".", 1)[-1].lower()[:5]
    mime = materials_service.validate_upload(content, file.content_type)
    material = materials_service.create_material(
        db, kind=kind, title=title or file.filename or f"material-{utcnow().timestamp():.0f}",
        tags=[t for t in (tags or "").split(",") if t], created_by=user.email,
    )
    revision = materials_service.create_revision(
        db, material,
        content=content, suffix=f".{suffix}" if suffix else "",
        declared_mime=mime, source_kind=source_kind, source_url=source_url,
        rights_status=rights_status, public_use_allowed=public_use_allowed,
        model_use_allowed=model_use_allowed, attribution_text=attribution_text,
        metadata={"filename": file.filename},
        created_by=user.email,
    )
    db.add(AuditLog(event="material.uploaded", actor=user.email, entity_type="material", entity_id=str(material.id), detail_json={"hash": revision.content_hash, "source_kind": source_kind}))
    db.commit()
    return _material_json(material, with_revisions=True)


@router.get("/materials/{material_id}")
def get_material(material_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.get(Material, material_id)
    if not row:
        raise HTTPException(404, "素材不存在")
    data = _material_json(row, with_revisions=True)
    data["usage"] = materials_service.find_usage(db, material_id)
    return data


@router.get("/materials/{material_id}/revisions")
def list_material_revisions(material_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.get(Material, material_id)
    if not row:
        raise HTTPException(404, "素材不存在")
    return [_revision_json(r) for r in row.revisions]


@router.post("/materials/{material_id}/revisions/{revision_id}/revoke-public-use")
def revoke_material_public_use(
    material_id: int,
    revision_id: int,
    payload: RevocationIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_editor),
):
    revision = _get_revision(db, material_id, revision_id)
    result = materials_service.revoke_public_use(db, revision, payload.note)
    db.add(AuditLog(event="material.public_use_revoked", actor=user.email, entity_type="material_revision", entity_id=str(revision.id), detail_json={"note": payload.note, "affected_drafts": result["affected_drafts"]}))
    db.commit()
    return {**result, "revision": _revision_json(revision)}


@router.get("/materials/{material_id}/revisions/{revision_id}/raw")
def material_raw(material_id: int, revision_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """鉴权 raw 端点（§15.1）：不复用无 Header 的 <img> 模式，前端走 blob。"""
    revision = _get_revision(db, material_id, revision_id)
    content = materials_service.read_bytes_checked(db, revision)
    from fastapi import Response

    return Response(content=content, media_type=revision.mime_type or "application/octet-stream")


@router.post("/materials/search")
def search_materials(payload: SearchIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        from ..services.content_harness.providers import resolve_material_search

        provider = resolve_material_search()
    except CapabilityUnavailable as exc:
        raise HTTPException(422, f"capability_unavailable: {exc}") from exc
    from ..services import material_search

    return material_search.search(user, key=provider.key, version=provider.version, query=payload.query, limit=payload.limit)["items"]


@router.post("/materials/generate")
def generate_material(
    payload: GenerateIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_editor),
):
    """Generation now returns a private preview; acceptance is a separate action."""

    draft = db.get(Draft, payload.draft_id) if payload.draft_id else None
    if payload.draft_id and draft is None:
        raise HTTPException(404, "Draft 不存在")
    if draft is not None:
        authorize_project_draft(db, draft, user, mutate=True)

    from .. import runtime_config
    from ..services.content_harness.providers import bootstrap_media_providers, resolve_asset_provider

    bootstrap_media_providers()
    image_cfg = runtime_config.get_runtime(runtime_config.KEY_IMAGE) or {}
    if not image_cfg.get("enabled"):
        raise HTTPException(422, "capability_unavailable: AI 生图未启用（设置 → 模型服务 → AI 生图）")
    try:
        if image_cfg.get("provider") == "openai":
            from ..services.content_harness.providers import registry
            provider = registry.resolve("image_provider", "image.openai", "1")
        else:
            provider = resolve_asset_provider()
    except CapabilityUnavailable as exc:
        raise HTTPException(422, f"capability_unavailable: {exc}") from exc

    from ..services import provider_media

    return provider_media.stage(db, user, {"provider_kind": "image_provider", "provider_key": provider.key,
                                          "provider_version": provider.version, "prompt": payload.prompt,
                                          "project_id": None, "source_revision_ids": []})


# ---------- Draft × Material（Use/Placement）----------


@router.get("/drafts/{draft_id}/materials")
def list_draft_materials(draft_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    draft = db.get(Draft, draft_id)
    if not draft:
        raise HTTPException(404, "Draft 不存在")
    authorize_project_draft(db, draft, user)
    return [_media_json(m) for m in draft.media]


@router.post("/drafts/{draft_id}/materials", status_code=201)
def attach_material(
    draft_id: int,
    payload: MaterialAttachIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_editor),
):
    """引用已有 MaterialRevision 挂到稿件（Use）。上传走 /materials/upload。"""
    draft = db.get(Draft, draft_id)
    if not draft:
        raise HTTPException(404, "Draft 不存在")
    authorize_project_draft(db, draft, user, mutate=True)
    if payload.role not in ROLES:
        raise HTTPException(422, "role 不受支持")
    revision = db.get(MaterialRevision, payload.material_revision_id)
    if not revision:
        raise HTTPException(404, "素材版本不存在")
    use = materials_service.attach_to_draft(
        db, draft, revision,
        role=payload.role,
        sort_order=payload.sort_order,
        alt_text=payload.alt_text,
        caption=payload.caption,
        placement=payload.placement,
    )
    document_composition.sync_document(db, draft)
    db.add(AuditLog(event="material.attached", actor=user.email, entity_type="draft", entity_id=str(draft.id), detail_json={"draft_media_id": use.id, "material_revision_id": revision.id}))
    db.commit()
    db.refresh(use)
    return _media_json(use)


@router.post("/drafts/{draft_id}/materials/upload", status_code=201)
async def upload_draft_material(
    draft_id: int,
    file: UploadFile,
    role: str = "inline",
    rights_status: str = "cleared",
    public_use_allowed: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(require_editor),
):
    """上传即入库：Material + MaterialRevision + DraftMedia(use)（D9 新流程）。"""
    draft = db.get(Draft, draft_id)
    if not draft:
        raise HTTPException(404, "Draft 不存在")
    authorize_project_draft(db, draft, user, mutate=True)
    if role not in ROLES:
        raise HTTPException(422, "role 不受支持")
    content = await file.read()
    mime = materials_service.validate_upload(content, file.content_type)
    material = materials_service.create_material(
        db, kind="image", title=file.filename or "draft-upload", created_by=user.email
    )
    suffix = (file.filename or "").rsplit(".", 1)[-1].lower()[:5]
    revision = materials_service.create_revision(
        db, material, content=content, suffix=f".{suffix}" if suffix else "",
        declared_mime=mime, rights_status=rights_status, public_use_allowed=public_use_allowed,
        metadata={"filename": file.filename, "first_draft_id": draft_id}, created_by=user.email,
    )
    use = materials_service.attach_to_draft(db, draft, revision, role=role)
    document_composition.sync_document(db, draft)
    db.add(AuditLog(event="material.attached", actor=user.email, entity_type="draft", entity_id=str(draft.id), detail_json={"draft_media_id": use.id, "material_revision_id": revision.id, "via": "upload"}))
    db.commit()
    db.refresh(use)
    return _media_json(use)


@router.patch("/drafts/{draft_id}/materials/{media_id}")
def patch_draft_material(
    draft_id: int,
    media_id: int,
    payload: MaterialPatchIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_editor),
):
    draft, row = _own_media(db, draft_id, media_id)
    authorize_project_draft(db, draft, user, mutate=True)
    if draft.status == DraftStatus.approved.value:
        raise HTTPException(409, "已批准稿件的素材不可修改")
    if payload.role is not None:
        if payload.role not in ROLES:
            raise HTTPException(422, "role 不受支持")
        row.role = payload.role
    if payload.sort_order is not None:
        row.sort_order = payload.sort_order
    if payload.alt_text is not None:
        row.alt_text = payload.alt_text
    if payload.caption is not None:
        row.caption = payload.caption
    if payload.placement is not None:
        row.placement_json = payload.placement
    document_composition.sync_document(db, draft)
    materials_service.staleness.mark_media_changed(db, draft, reason="draft_material_patched")
    db.commit()
    return _media_json(row)


@router.delete("/drafts/{draft_id}/materials/{media_id}")
def delete_draft_material(draft_id: int, media_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    draft, row = _own_media(db, draft_id, media_id)
    authorize_project_draft(db, draft, user, mutate=True)
    referenced_v1 = db.scalars(
        select(ContentAsset).where(ContentAsset.draft_id == draft.id, ContentAsset.approved_candidate_hash.is_not(None))
    ).first()
    approved_revision_ids = materials_service._approved_revision_ids(db)
    if draft.status == DraftStatus.approved.value or referenced_v1 or row.material_revision_id in approved_revision_ids:
        raise HTTPException(409, "素材已被批准候选引用，不能删除")
    db.delete(row)
    document_composition.sync_document(db, draft)
    materials_service.staleness.mark_media_changed(db, draft, reason="draft_material_deleted")
    db.commit()
    return {"deleted": True, "id": media_id}


# ---------- Document composition ----------


@router.get("/drafts/{draft_id}/document")
def get_document(draft_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    draft = db.get(Draft, draft_id)
    if not draft:
        raise HTTPException(404, "Draft 不存在")
    authorize_project_draft(db, draft, user)
    return {
        "draft_id": draft.id,
        "document_schema_version": draft.document_schema_version,
        "document": draft.document_json or document_composition.build_document_from_body(draft.body, list(draft.media)),
    }


@router.put("/drafts/{draft_id}/document")
def set_document(draft_id: int, payload: DocumentIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    draft = db.get(Draft, draft_id)
    if not draft:
        raise HTTPException(404, "Draft 不存在")
    authorize_project_draft(db, draft, user, mutate=True)
    try:
        document = document_composition.set_document(db, draft, {"blocks": payload.blocks})
    except (TypeError, ValueError) as exc:
        raise HTTPException(422, str(exc)) from exc
    db.commit()
    return {"draft_id": draft.id, "document": document}


@router.post("/drafts/{draft_id}/document/rebuild")
def rebuild_document(draft_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    draft = db.get(Draft, draft_id)
    if not draft:
        raise HTTPException(404, "Draft 不存在")
    authorize_project_draft(db, draft, user, mutate=True)
    document_composition.sync_document(db, draft)
    db.commit()
    return {"draft_id": draft.id, "document": draft.document_json}
