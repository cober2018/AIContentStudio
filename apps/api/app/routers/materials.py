"""Material Library API（§6.15）：全局素材复用与权利链路。

- search/generate 无 provider 时返回 422 capability_unavailable，不返回假数据；
- 已批准候选引用的素材不可删除/变更（替换=新 Revision）；
"""

import hashlib
import json
from http.cookies import SimpleCookie
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response, UploadFile
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, ConfigDict, Field, StrictFloat, StrictInt, StrictStr, field_validator
from sqlalchemy import String, cast, or_, select
from sqlalchemy.orm import Session, selectinload

from ..db import get_db
from ..deps import get_current_user, require_admin, require_editor
from ..models import (
    AuditLog,
    Material,
    MaterialRevision,
    MaterialSource,
    User,
    utcnow,
)
from ..services import materials as materials_service
from ..services.content_harness.providers import CapabilityUnavailable
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
    license_code: Literal["CC0", "PDM", "CC-BY-4.0", "CC-BY", "provider_terms", "owned"]
    license_evidence_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    public_use_allowed: bool
    model_use_allowed: bool
    commercial_use_allowed: bool
    attribution_text: str | None = Field(default=None, max_length=1000)


class GenerationTaskIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    idempotency_key: str = Field(pattern=r"^[A-Za-z0-9_.-]{1,100}$")
    capability: Literal["image_generation", "video_generation", "tts"]
    selected_profile: str = Field(pattern=r"^[A-Za-z0-9_.-]{1,100}$")
    explicit_plugin: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_.-]{1,100}$")
    configuration_mode: Literal["auto", "custom"] = "auto"
    prompt: str = Field(min_length=1, max_length=2000)
    project_id: int | None = Field(default=None, ge=1)
    source_revision_ids: list[int] = Field(default_factory=list, max_length=4)
    parameters: dict[Literal["items", "pixels", "seconds", "tokens", "timeout_seconds", "aspect_ratio", "voice_id", "rate"], StrictInt | StrictFloat | StrictStr] = Field(default_factory=dict, max_length=8)

    @field_validator("parameters")
    @classmethod
    def bounded_parameters(cls, value, info):
        from ..services.model_capability_routing import tts_parameters

        numeric = {"items", "pixels", "seconds", "tokens", "timeout_seconds"}
        if any(type(value[key]) is not int for key in numeric.intersection(value)):
            raise ValueError("generation_parameters_invalid")
        try:
            spoken = tts_parameters(value, capability=info.data.get("capability"))
        except (TypeError, ValueError):
            raise ValueError("generation_parameters_invalid") from None
        return {**value, **spoken} if spoken is not None else value


class GenerationRevisionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(strict=True, ge=1)


class GenerationAcceptIn(ProviderAcceptIn):
    expected_revision: int = Field(strict=True, ge=1)
    candidate_index: int = Field(default=0, strict=True, ge=0, le=3)


@router.get("/generation-tasks")
def list_generation_tasks(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from ..services import generation_tasks

    return generation_tasks.list_tasks(db, user)


@router.post("/generation-tasks", status_code=201)
def prepare_generation_task(payload: GenerationTaskIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    from ..services import generation_tasks

    return generation_tasks.prepare(db, user, payload.model_dump())


@router.get("/generation-tasks/{task_id}")
def read_generation_task(task_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from ..services import generation_tasks

    return generation_tasks.read(db, user, task_id)


@router.post("/generation-tasks/{task_id}/execute")
def execute_generation_task(task_id: str, payload: GenerationRevisionIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    from ..services import generation_tasks

    return generation_tasks.execute(db, user, task_id, payload.expected_revision)


@router.post("/generation-tasks/{task_id}/recover")
def recover_generation_task(task_id: str, payload: GenerationRevisionIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    from ..services import generation_tasks

    return generation_tasks.recover(db, user, task_id, payload.expected_revision)


@router.get("/generation-tasks/{task_id}/raw")
def preview_generation_task(task_id: str, candidate_index: int | None = None,
                            db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from ..services import generation_tasks

    content, mime = generation_tasks.raw(db, user, task_id, candidate_index)
    return Response(content=content, media_type=mime, headers={"Cache-Control": "private, no-store"})


@router.post("/generation-tasks/{task_id}/accept", status_code=201)
def accept_generation_task(task_id: str, payload: GenerationAcceptIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    from ..services import generation_tasks

    return generation_tasks.accept(db, user, task_id, payload.expected_revision, payload.model_dump(exclude={"expected_revision"}))


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
    role: str = "inline"
    candidate_count: int = Field(default=1, ge=1, le=4)


def _drive_location(key: str | None) -> dict | None:
    from ..services.material_external import is_external, parse_key

    if not is_external(key):
        return None
    source_id, _hash, relative = parse_key(key)
    return {"source_id": source_id, "relative_path": relative}


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
        "metadata": {key: value for key, value in (row.metadata_json or {}).items() if key in {"music", "tags", "previous_tags"}},
        "duration_ms": row.duration_ms,
        "width": row.width,
        "height": row.height,
        "drive": _drive_location(row.file_path),
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


def _get_revision(db: Session, material_id: int, revision_id: int) -> MaterialRevision:
    row = db.get(MaterialRevision, revision_id)
    if not row or row.material_id != material_id:
        raise HTTPException(404, "素材版本不存在")
    return row


# ---------- Material ----------


@router.get("/materials")
def list_materials(
    kind: str | None = None,
    status: str = "active",
    q: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # selectinload：一条批量查询取全部 revisions，避免逐行 lazy load（200 条=200 次查询）
    stmt = select(Material).options(selectinload(Material.revisions)).order_by(Material.id.desc())
    if status:
        stmt = stmt.where(Material.status == status)
    if kind:
        stmt = stmt.where(Material.kind == kind)
    if q:
        encoded_query = json.dumps(q, ensure_ascii=True)[1:-1]
        music_match = select(MaterialRevision.material_id).where(
            MaterialRevision.id == select(MaterialRevision.id).where(MaterialRevision.material_id == Material.id)
                .order_by(MaterialRevision.revision_no.desc()).limit(1).correlate(Material).scalar_subquery(),
            or_(cast(MaterialRevision.metadata_json["music"], String).contains(q, autoescape=True),
                cast(MaterialRevision.metadata_json["music"], String).contains(encoded_query, autoescape=True)),
        ).correlate(Material).exists()
        stmt = stmt.where(or_(Material.title.contains(q, autoescape=True),
            cast(Material.tags_json, String).contains(q, autoescape=True),
            cast(Material.tags_json, String).contains(encoded_query, autoescape=True), music_match))
    return [_material_json(m) for m in db.scalars(stmt.limit(200))]


@router.get("/materials/storage-diagnostics")
def material_storage_diagnostics(db: Session = Depends(get_db), user: User = Depends(require_admin)):
    from ..services.materials import storage_diagnostics

    return storage_diagnostics(db)


@router.post("/materials/upload", status_code=201)
async def upload_material(
    file: UploadFile,
    kind: str = "image",
    inspect_video: bool = False,
    title: str | None = None,
    source_kind: str = "upload",
    rights_status: str = "cleared",
    public_use_allowed: bool = True,
    model_use_allowed: bool = True,
    attribution_text: str | None = None,
    source_url: str | None = None,
    tags: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_editor),
):
    if source_kind == "external_execution":
        raise HTTPException(403, {"code": "external_execution_acceptance_required"})
    content = await file.read()

    # 校验/hash/落盘（含 flock）是重活，放线程池避免阻塞事件循环
    def _persist() -> dict:
        suffix = (file.filename or "").rsplit(".", 1)[-1].lower()[:5]
        mime = materials_service.validate_upload(content, file.content_type)
        media_info = {}
        if inspect_video:
            if kind != "video" or mime not in {"video/mp4", "video/quicktime"}:
                raise HTTPException(422, "实拍原片必须为MP4或MOV视频")
            import tempfile
            from types import SimpleNamespace

            from ..services.creative_media_stream import validate

            with tempfile.TemporaryFile() as source:
                source.write(content)
                source.seek(0)
                media_info = validate(source, mime, "video", SimpleNamespace(package_json={}))
            if not media_info.get("video_duration_ms"):
                raise HTTPException(422, "实拍原片缺少可验证的视频轨时长")
        from ..services.material_dedupe import existing_revision

        # The same bytes already in the library are reused, so a file is never listed twice.
        existing = existing_revision(db, hashlib.sha256(content).hexdigest())
        if existing is not None:
            data = _material_json(existing.material, with_revisions=True)
            data["revisions"] = [row for row in data["revisions"] if row["id"] != existing.id] + [_revision_json(existing)]
            data["reused"] = True
            return data
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
            metadata={"filename": file.filename, **({"media_probe": media_info} if media_info else {})},
            duration_ms=media_info.get("video_duration_ms"), width=media_info.get("width"), height=media_info.get("height"),
            created_by=user.email,
        )
        db.add(AuditLog(event="material.uploaded", actor=user.email, entity_type="material", entity_id=str(material.id), detail_json={"hash": revision.content_hash, "source_kind": source_kind}))
        db.commit()
        return _material_json(material, with_revisions=True)

    return await run_in_threadpool(_persist)


class MaterialSourceIn(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    label: str = Field(min_length=1, max_length=200)
    root_path: str = Field(min_length=2, max_length=1000)


class MaterialLinkIn(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    relative_path: str = Field(min_length=1, max_length=1000)
    kind: Literal["image", "video", "audio"]
    title: str | None = Field(default=None, max_length=500)
    material_id: int | None = Field(default=None, ge=1)
    source_kind: Literal["upload", "web_search", "screenshot"] = "upload"
    source_url: str | None = Field(default=None, max_length=1000)
    rights_status: str = Field(default="cleared", max_length=30)
    public_use_allowed: bool = True
    model_use_allowed: bool = True
    commercial_use_allowed: bool | None = None
    attribution_text: str | None = Field(default=None, max_length=4000)
    tags: list[str] = Field(default_factory=list, max_length=30)


def _source_json(row: MaterialSource) -> dict:
    from ..services.material_external import source_status

    return {"id": row.id, "label": row.label, "root_path": row.root_path, "volume_uuid": row.volume_uuid,
            "status": source_status(row), "created_at": row.created_at.isoformat() if row.created_at else None}


def _owned_source(db: Session, source_id: int, user: User) -> MaterialSource:
    row = db.get(MaterialSource, source_id)
    if row is None or row.owner_user_id != user.id:
        raise HTTPException(404, {"code": "material_source_not_found"})
    return row


@router.post("/material-sources", status_code=201)
def create_material_source(payload: MaterialSourceIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    from pathlib import Path

    from ..services.material_external import ExternalMaterialError, http_error, normalize_root, volume_uuid

    try:
        root = normalize_root(payload.root_path)
    except ExternalMaterialError as exc:
        raise http_error(exc) from None
    if not Path(root).is_dir() or Path(root).is_symlink():
        raise HTTPException(422, {"code": "material_source_folder_missing"})
    if db.scalar(select(MaterialSource.id).where(MaterialSource.owner_user_id == user.id, MaterialSource.root_path == root)):
        raise HTTPException(409, {"code": "material_source_exists"})
    row = MaterialSource(owner_user_id=user.id, label=payload.label, root_path=root, volume_uuid=volume_uuid(root), created_by=user.email)
    db.add(row)
    db.flush()
    db.add(AuditLog(event="material_source.created", actor=user.email, entity_type="material_source", entity_id=str(row.id),
                    detail_json={"root_path": root, "volume_uuid": row.volume_uuid}))
    db.commit()
    return _source_json(row)


@router.get("/material-folders")
def material_folders(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from ..services import project_folders

    return project_folders.tree(db)


@router.post("/materials/{material_id}/to-common", dependencies=[Depends(require_editor)])
def material_to_common(material_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from ..services import project_folders

    revision = db.scalar(select(MaterialRevision).where(MaterialRevision.material_id == material_id)
                         .order_by(MaterialRevision.revision_no.desc()).limit(1))
    if revision is None:
        raise HTTPException(404, {"code": "material_not_found"})
    result = project_folders.to_common(db, revision)
    if result["state"] == "pending":
        raise HTTPException(409, {"code": "material_move_failed", "message": result["reason"]})
    return result


@router.get("/material-sources")
def list_material_sources(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(MaterialSource).where(MaterialSource.owner_user_id == user.id).order_by(MaterialSource.id)).all()
    return {"items": [_source_json(row) for row in rows]}


@router.get("/material-sources/{source_id}/files")
def scan_material_source(source_id: int, subpath: str = "", db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from ..services.material_external import ExternalMaterialError, http_error, scan

    try:
        return scan(db, _owned_source(db, source_id, user), subpath)
    except ExternalMaterialError as exc:
        raise http_error(exc) from None


@router.post("/material-sources/{source_id}/links", status_code=201)
def link_material(source_id: int, payload: MaterialLinkIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    from ..services.material_external import ExternalMaterialError, http_error, link

    source = _owned_source(db, source_id, user)
    try:
        material, revision = link(db, source, user=user, **payload.model_dump())
    except ExternalMaterialError as exc:
        db.rollback()
        raise http_error(exc) from None
    db.commit()
    db.refresh(material)
    return {**_material_json(material, with_revisions=True), "linked_revision_id": revision.id}


@router.get("/materials/{material_id}")
def get_material(material_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.get(Material, material_id)
    if not row:
        raise HTTPException(404, "素材不存在")
    data = _material_json(row, with_revisions=True)
    data["usage"] = materials_service.find_usage(db, material_id)
    return data


class MusicMetadataIn(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    scene: list[str] = Field(default_factory=list, max_length=30)
    mood: list[str] = Field(default_factory=list, max_length=30)
    energy: list[str] = Field(default_factory=list, max_length=30)
    instruments: list[str] = Field(default_factory=list, max_length=30)
    vocal: Literal["unknown", "instrumental", "vocal"] = "unknown"
    tempo_bpm: float | None = Field(default=None, gt=0, le=1000, allow_inf_nan=False)
    loop_suitable: bool | None = None
    source: str = Field(default="", max_length=2000)
    license: str = Field(default="", max_length=2000)
    listening_status: Literal["not_listened", "partially_listened", "listened"] = "not_listened"

    @field_validator("scene", "mood", "energy", "instruments")
    @classmethod
    def labels(cls, value):
        if any(not item.strip() or len(item) > 100 for item in value):
            raise ValueError("标签不能为空且最多100字")
        return list(dict.fromkeys(item.strip() for item in value))


class MusicRevisionIn(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    expected_revision_id: int = Field(ge=1)
    tags: list[str] = Field(max_length=30)
    music: MusicMetadataIn

    @field_validator("tags")
    @classmethod
    def labels(cls, value):
        return MusicMetadataIn.labels(value)


@router.post("/materials/{material_id}/music-metadata", status_code=201)
def revise_music_metadata(material_id: int, payload: MusicRevisionIn,
                          db: Session = Depends(get_db), user: User = Depends(require_editor)):
    from sqlalchemy.exc import IntegrityError, OperationalError

    try:
        materials_service.revise_music_metadata(db, material_id, payload.expected_revision_id,
            tags=payload.tags, music=payload.music.model_dump(), actor=user.email)
        db.commit()
    except (IntegrityError, OperationalError):
        db.rollback()
        raise HTTPException(409, "素材版本写入冲突，请读取最新版本后重试") from None
    except BaseException:
        db.rollback()
        raise
    db.expire_all()
    return _material_json(db.get(Material, material_id), with_revisions=True)


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
    db.add(AuditLog(event="material.public_use_revoked", actor=user.email, entity_type="material_revision", entity_id=str(revision.id), detail_json={"note": payload.note}))
    db.commit()
    return {**result, "revision": _revision_json(revision)}


class LoudnessMasterIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_lufs: StrictFloat | StrictInt = Field(default=-16.0, ge=-30, le=-9)
    true_peak_dbtp: StrictFloat | StrictInt = Field(default=-1.5, ge=-6, le=-0.5)


@router.post("/materials/{material_id}/revisions/{revision_id}/loudness-master", status_code=201)
def master_material_loudness(
    material_id: int,
    revision_id: int,
    payload: LoudnessMasterIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_editor),
):
    from ..services.audio_mastering import master_loudness

    revision = _get_revision(db, material_id, revision_id)
    if (revision.material.kind != "audio" or revision.material.status != "active" or revision.status in {"revoked", "archived"}
            or revision.source_kind == "external_execution" or revision.mime_type not in {"audio/wav", "audio/x-wav", "audio/wave"}):
        raise HTTPException(422, {"code": "audio_mastering_source_invalid"})
    mastered, report = master_loudness(materials_service.read_bytes_checked(db, revision),
                                       target_lufs=float(payload.target_lufs), true_peak_dbtp=float(payload.true_peak_dbtp))
    # The parent's generation provenance stays on the parent; the derivative records only its lineage and processing.
    row = materials_service.create_revision(
        db, revision.material, content=mastered, suffix=".wav", declared_mime="audio/wav", source_kind=revision.source_kind,
        source_url=revision.source_url, source_metadata={"loudness_master": report, "parent_revision_id": revision.id, "parent_content_hash": revision.content_hash},
        rights_status=revision.rights_status, public_use_allowed=revision.public_use_allowed, model_use_allowed=revision.model_use_allowed,
        commercial_use_allowed=revision.commercial_use_allowed, attribution_text=revision.attribution_text,
        provider_key=revision.provider_key, provider_version=revision.provider_version, duration_ms=revision.duration_ms,
        metadata={"loudness_master": report}, created_by=user.email)
    row.parent_revision_id = revision.id
    db.add(AuditLog(event="material.loudness_mastered", actor=user.email, entity_type="material_revision", entity_id=str(row.id),
                    detail_json={"parent_revision_id": revision.id, "output": report["output"], "normalization_type": report["normalization_type"]}))
    db.commit()
    return {"revision": _revision_json(row), "report": report}


def _external_video_target(db, material_id, revision_id, user=None):
    from ..services.content_masters import local_final_use_allowed

    revision = _get_revision(db, material_id, revision_id)
    provenance = revision.source_metadata_json or {}
    keys = ("project_id", "content_unit_id", "execution_id", "output_id")
    if (revision.source_kind != "external_execution" or revision.mime_type != "video/mp4"
            or any(type(provenance.get(key)) is not int or provenance[key] < 1 for key in keys)
            or (user is not None and provenance.get("owner_user_id") != user.id)):
        raise HTTPException(404, {"code": "creative_output_not_found"})
    if (revision.status in {"revoked", "archived"} or revision.material.status != "active"
            or (revision.public_use_allowed is not True and not local_final_use_allowed(
                db, provenance["project_id"], provenance["content_unit_id"], provenance.get("owner_user_id"), revision))):
        raise HTTPException(409, {"code": "creative_output_material_rights_changed"})
    return revision, [provenance[key] for key in keys]


@router.post("/materials/{material_id}/revisions/{revision_id}/preview-session")
def material_preview_session(material_id: int, revision_id: int, request: Request, response: Response,
                             db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from .creative_orchestration import _preview_output, preview_session

    revision, target = _external_video_target(db, material_id, revision_id, user)
    _execution, output = _preview_output(db, *target, user)
    if output["state"] != "accepted" or output["material_revision_id"] != revision.id or output["content_hash"] != revision.content_hash:
        raise HTTPException(409, {"code": "creative_output_material_integrity"})
    # Reuse the execution signature and Range reader, while limiting its cookie to this exact material URL.
    session_response = Response()
    result = preview_session(*target, request, session_response, db, user)
    cookie = SimpleCookie()
    cookie.load(session_response.headers["set-cookie"])
    path = f"/api/v1/materials/{material_id}/revisions/{revision_id}/preview"
    response.set_cookie("creative_preview", cookie["creative_preview"].value, max_age=300, path=path,
                        httponly=True, samesite="strict", secure=request.url.scheme == "https")
    response.headers["Cache-Control"] = "no-store"
    return {**result, "url": path}


@router.get("/materials/{material_id}/revisions/{revision_id}/preview")
def material_preview(material_id: int, revision_id: int, request: Request, db: Session = Depends(get_db)):
    from .creative_orchestration import preview_output

    if not request.cookies.get("creative_preview"):
        raise HTTPException(401, {"code": "creative_preview_session_required"})
    _revision, target = _external_video_target(db, material_id, revision_id)
    return preview_output(*target, request, db)


@router.get("/materials/{material_id}/revisions/{revision_id}/raw")
def material_raw(material_id: int, revision_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """鉴权 raw 端点（§15.1）：不复用无 Header 的 <img> 模式，前端走 blob。"""
    revision = _get_revision(db, material_id, revision_id)
    path = materials_service.local_file_checked(db, revision)
    if path is not None:
        from fastapi.responses import FileResponse

        # Files live on this machine: stream with Range so large cuts play and seek without a size cap.
        return FileResponse(path, media_type=revision.mime_type or "application/octet-stream")
    content = materials_service.read_bytes_checked(db, revision)
    from fastapi import Response

    return Response(content=content, media_type=revision.mime_type or "application/octet-stream")


def _reveal(path) -> None:
    import subprocess
    import sys

    if sys.platform != "darwin":
        raise HTTPException(409, {"code": "reveal_unsupported", "message": "只能在 Mac 本机上打开访达"})
    subprocess.run(["open", "-R", str(path)], check=False, timeout=10)


def _located(db: Session, material_id: int, revision_id: int):
    revision = _get_revision(db, material_id, revision_id)
    path = materials_service.local_file_checked(db, revision)
    if path is None:
        raise HTTPException(409, {"code": "material_not_local", "message": "这个素材不在本机硬盘上"})
    return path


@router.get("/materials/{material_id}/revisions/{revision_id}/location")
def material_location(material_id: int, revision_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {"path": str(_located(db, material_id, revision_id))}


@router.post("/materials/{material_id}/revisions/{revision_id}/reveal")
def material_reveal(material_id: int, revision_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    path = _located(db, material_id, revision_id)
    _reveal(path)
    return {"path": str(path)}


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

    from ..services.content_harness.providers import bootstrap_media_providers, resolve_asset_provider

    bootstrap_media_providers()
    from ..services.model_registration import cover_image_config
    from ..services.openai_image_provider import _config as openai_cover_config

    if cover_image_config() is None:
        raise HTTPException(422, "capability_unavailable: 封面生图未选择模型（设置 → AI 与模型 → 用途路由）")
    try:
        if openai_cover_config() is not None:
            from ..services.content_harness.providers import registry
            provider = registry.resolve("image_provider", "image.openai", "1")
        else:
            provider = resolve_asset_provider()
    except CapabilityUnavailable as exc:
        raise HTTPException(422, f"capability_unavailable: {exc}") from exc

    if payload.candidate_count != 1:
        # Multi-candidate generation must use the durable task route.  The
        # legacy preview endpoint has no receipt or selection state to bind.
        raise HTTPException(422, "generation_task_required")

    from ..services import provider_media

    request = {"provider_kind": "image_provider", "provider_key": provider.key,
               "provider_version": provider.version, "prompt": payload.prompt,
               "project_id": None, "source_revision_ids": []}
    return provider_media.stage(db, user, request)
