"""Persistent Brand/Persona/Account/Series identity APIs."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, get_existing_user, require_admin, require_editor
from ..models import (
    BrandVoiceVersion,
    ContentAccount,
    ContentBrand,
    ContentPersona,
    ContentSeries,
    IdentitySnapshot,
    User,
)
from ..services import content_identity as identity
from ..services import creative_configuration, series_targets, starter_personas
from ..services.studio_creative_catalog import inventory
from . import CapabilityInputRoute

router = APIRouter(prefix="/api/v1", tags=["content-identities"], route_class=CapabilityInputRoute)


class NameIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class RevisionIn(BaseModel):
    expected_revision: int = Field(ge=0)
    profile: identity.IdentityProfile


class PlatformBindingIn(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    platform_channel: str = Field(pattern=r"^wechat$")
    platform_account_id: str = Field(pattern=r"^wx[0-9a-f]{16}$")


class ChannelAccountIn(BaseModel):
    """浏览器最后一公里用的公开身份。不能带密码、密钥或其他额外字段。"""

    model_config = ConfigDict(extra="forbid", strict=True)
    name: str = Field(min_length=1, max_length=200)
    platform_channel: str = Field(min_length=1, max_length=50)
    platform_account_id: str = Field(min_length=1, max_length=64)


class PublisherConnectionIn(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    expected_revision: int = Field(ge=0)
    enabled: bool
    credential_version: str = Field(pattern=r"^[A-Za-z0-9_.-]{1,64}$")


class CreativeStagePreviewIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    persona_id: int = Field(gt=0)
    account_id: int | None = Field(default=None, gt=0)
    series_id: int | None = Field(default=None, gt=0)
    modality: str = Field(pattern=r"^(text|graphic|audio|video)$")
    stage: str | None = Field(default=None, max_length=120)
    override: dict | None = None
    profile_override: identity.CreativeProfile | None = None


class StarterPreviewIn(BaseModel):
    blueprint_key: str = Field(pattern=r"^starter\.[a-z0-9-]+\.v[0-9]+$")


class StarterApplyIn(StarterPreviewIn):
    model_config = ConfigDict(extra="forbid")


class StarterForkIn(StarterApplyIn):
    name: str = Field(min_length=1, max_length=200)
    expected_profile_checksum: str = Field(pattern=r"^[a-f0-9]{64}$")


def _current_revision_nos(db: Session, kind: str, entity_ids: list[int]) -> dict[int, int]:
    """列表页批量取每实体最新 revision_no，替代逐实体查询的 N+1。"""
    if not entity_ids:
        return {}
    _, revision_model, foreign_key = identity.REVISION_MODELS[kind]
    return dict(db.execute(
        select(getattr(revision_model, foreign_key), func.max(revision_model.revision_no))
        .where(getattr(revision_model, foreign_key).in_(entity_ids))
        .group_by(getattr(revision_model, foreign_key))
    ).all())


def _entity_json(db: Session, kind: str, row, *, current_revision_no: int | None = None) -> dict:
    if current_revision_no is None:
        current = identity.current_revision(db, kind, row.id)
        current_revision_no = current.revision_no if current else 0
    data = {"id": row.id, "name": row.name, "status": row.status, "current_revision": current_revision_no}
    if kind == "brand":
        data["owner_user_id"] = row.owner_user_id
    else:
        data[{"persona": "brand_id", "account": "persona_id", "series": "account_id"}[kind]] = getattr(row, {"persona": "brand_id", "account": "persona_id", "series": "account_id"}[kind])
    if kind == "account":
        data.update(platform_channel=row.platform_channel, platform_account_id=row.platform_account_id,
                    platform_binding_state="bound_unverified" if row.platform_account_id else "unbound")
    if kind == "series":
        data.update(scope=getattr(row, "scope", "account_legacy"), persona_id=getattr(row, "persona_id", None))
    return data


def _revision_json(row) -> dict:
    return {"id": row.id, "revision_no": row.revision_no, "profile": row.profile_json, "checksum": row.checksum, "created_by": row.created_by, "created_at": row.created_at.isoformat() if row.created_at else None}


def _create(db: Session, kind: str, row) -> dict:
    db.add(row)
    db.commit()
    db.refresh(row)
    return _entity_json(db, kind, row)


def _rename(db: Session, user: User, kind: str, entity_id: int, name: str) -> dict:
    row = identity.owned_entity(db, user, kind, entity_id, mutable=True)
    row.name = name
    db.commit()
    return _entity_json(db, kind, row)


def _archive(db: Session, user: User, kind: str, entity_id: int) -> None:
    row = identity.owned_entity(db, user, kind, entity_id)
    if row.status != "archived":
        row.status = "archived"
        db.commit()


def _revisions(db: Session, user: User, kind: str, entity_id: int) -> list[dict]:
    identity.owned_entity(db, user, kind, entity_id)
    return [_revision_json(row) for row in identity.revisions(db, kind, entity_id)]


def _revision_detail(db: Session, user: User, kind: str, entity_id: int, revision_id: int) -> dict:
    identity.owned_entity(db, user, kind, entity_id)
    _, revision_model, foreign_key = identity.REVISION_MODELS[kind]
    row = db.get(revision_model, revision_id)
    if row is None or getattr(row, foreign_key) != entity_id:
        raise HTTPException(404, "身份版本不存在")
    return _revision_json(row)


def _save(db: Session, user: User, kind: str, entity_id: int, payload: RevisionIn) -> dict:
    row = identity.save_revision(db, user, kind, entity_id, expected_revision=payload.expected_revision, profile=payload.profile)
    return _revision_json(row)


@router.get("/content-brands")
def list_brands(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(ContentBrand).where(ContentBrand.owner_user_id == user.id).order_by(ContentBrand.id)).all()
    revision_nos = _current_revision_nos(db, "brand", [row.id for row in rows])
    return [_entity_json(db, "brand", row, current_revision_no=revision_nos.get(row.id, 0)) for row in rows]


@router.post("/content-brands", status_code=201)
def create_brand(payload: NameIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return _create(db, "brand", ContentBrand(owner_user_id=user.id, name=payload.name))


@router.get("/content-brands/{brand_id}")
def get_brand(brand_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _entity_json(db, "brand", identity.owned_entity(db, user, "brand", brand_id))


@router.patch("/content-brands/{brand_id}")
def rename_brand(payload: NameIn, brand_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return _rename(db, user, "brand", brand_id, payload.name)


@router.delete("/content-brands/{brand_id}", status_code=204)
def archive_brand(brand_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    _archive(db, user, "brand", brand_id)


@router.delete("/content-brands/{brand_id}/permanent")
def delete_brand(brand_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    """Delete a brand that has nothing under it; brands still holding personas are refused with their names."""
    from ..models import ContentBrand, ContentBrandRevision, IdentitySnapshot, ContentMemoryEntry

    brand = identity.owned_entity(db, user, "brand", brand_id)
    personas = db.scalars(select(ContentPersona).where(ContentPersona.brand_id == brand_id, ContentPersona.owner_user_id == user.id)).all()
    if personas:
        names = "、".join(f"{row.name}{'（已归档）' if row.status == 'archived' else ''}" for row in personas[:20])
        raise HTTPException(409, {"code": "brand_has_personas", "message": f"品牌下还有角色：{names}。先把它们移到别的品牌或删除，再删品牌。"})
    # Production snapshots and brand memory point at the brand; keeping it archived keeps old works traceable.
    if (db.scalar(select(IdentitySnapshot.id).where(IdentitySnapshot.brand_id == brand_id).limit(1)) is not None
            or db.scalar(select(ContentMemoryEntry.id).where(ContentMemoryEntry.brand_id == brand_id).limit(1)) is not None):
        _archive(db, user, "brand", brand_id)
        return {"deleted": False, "archived": True, "message": "已从目录删除；有作品的历史记录引用它，保留只读记录。"}
    for revision in db.scalars(select(ContentBrandRevision).where(ContentBrandRevision.brand_id == brand_id)).all():
        db.delete(revision)
    db.delete(db.get(ContentBrand, brand.id))
    db.commit()
    return {"deleted": True, "archived": False, "message": "品牌已删除。"}


@router.get("/content-brands/{brand_id}/personas")
def brand_personas(brand_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    identity.owned_entity(db, user, "brand", brand_id)
    rows = db.scalars(select(ContentPersona).where(ContentPersona.brand_id == brand_id, ContentPersona.owner_user_id == user.id).order_by(ContentPersona.id)).all()
    revision_nos = _current_revision_nos(db, "persona", [row.id for row in rows])
    return [_entity_json(db, "persona", row, current_revision_no=revision_nos.get(row.id, 0)) for row in rows]


@router.post("/content-brands/{brand_id}/personas", status_code=201)
def create_brand_persona(payload: NameIn, brand_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    identity.owned_entity(db, user, "brand", brand_id, mutable=True)
    return _create(db, "persona", ContentPersona(owner_user_id=user.id, brand_id=brand_id, name=payload.name))


@router.get("/content-personas/{persona_id}")
def get_persona(persona_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _entity_json(db, "persona", identity.owned_entity(db, user, "persona", persona_id))


@router.get("/content-personas/{persona_id}/portraits")
def persona_portraits(persona_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """The portraits of the current revision with their material ids, so the page can show them."""
    from ..models import MaterialRevision

    identity.owned_entity(db, user, "persona", persona_id)
    current = identity.current_revision(db, "persona", persona_id)
    items = []
    for revision_id in ((current.profile_json if current else None) or {}).get("portrait_material_revision_ids") or []:
        row = db.get(MaterialRevision, revision_id)
        items.append({"material_revision_id": revision_id, "material_id": row.material_id if row else None,
                      "usable": identity.usable_portrait(db, revision_id)})
    return {"items": items}


@router.patch("/content-personas/{persona_id}")
def rename_persona(payload: NameIn, persona_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return _rename(db, user, "persona", persona_id, payload.name)


@router.delete("/content-personas/{persona_id}", status_code=204)
def archive_persona(persona_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    _archive(db, user, "persona", persona_id)


@router.get("/content-personas/{persona_id}/accounts")
def persona_accounts(persona_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    identity.owned_entity(db, user, "persona", persona_id)
    rows = db.scalars(select(ContentAccount).where(ContentAccount.persona_id == persona_id).order_by(ContentAccount.id)).all()
    revision_nos = _current_revision_nos(db, "account", [row.id for row in rows])
    return [_entity_json(db, "account", row, current_revision_no=revision_nos.get(row.id, 0)) for row in rows]


@router.post("/content-personas/{persona_id}/accounts", status_code=201)
def create_account(payload: NameIn, persona_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    identity.owned_entity(db, user, "persona", persona_id, mutable=True)
    return _create(db, "account", ContentAccount(persona_id=persona_id, name=payload.name))


@router.post("/content-personas/{persona_id}/channel-accounts", status_code=201)
def create_channel_account(persona_id: int, payload: dict, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    try:
        body = ChannelAccountIn.model_validate(payload)
    except ValidationError:
        raise HTTPException(422, "platform_account_public_id_invalid") from None
    row = identity.register_public_channel_account(
        db, user, persona_id, name=body.name, channel=body.platform_channel, platform_account_id=body.platform_account_id,
    )
    return _entity_json(db, "account", row)


@router.get("/content-accounts/{account_id}")
def get_account(account_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _entity_json(db, "account", identity.owned_entity(db, user, "account", account_id))


@router.patch("/content-accounts/{account_id}")
def rename_account(payload: NameIn, account_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return _rename(db, user, "account", account_id, payload.name)


@router.put("/content-accounts/{account_id}/platform-binding")
def bind_account(account_id: int, payload: dict, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    try:
        binding = PlatformBindingIn.model_validate(payload)
    except ValidationError:
        raise HTTPException(422, "platform_binding_invalid") from None
    row = identity.bind_platform_account(db, user, account_id, channel=binding.platform_channel, platform_account_id=binding.platform_account_id)
    return _entity_json(db, "account", row)


@router.get("/content-accounts/{account_id}/publisher-connection")
def get_publisher_connection(account_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return identity.publisher_connection(db, user, account_id)


@router.put("/content-accounts/{account_id}/publisher-connection")
def save_publisher_connection(account_id: int, payload: dict, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    try:
        config = PublisherConnectionIn.model_validate(payload)
    except ValidationError:
        raise HTTPException(422, "publisher_connection_invalid") from None
    return identity.save_publisher_connection(db, user, account_id, **config.model_dump())


@router.delete("/content-accounts/{account_id}", status_code=204)
def archive_account(account_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    _archive(db, user, "account", account_id)


@router.get("/content-accounts/{account_id}/series")
def account_series(account_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    identity.owned_entity(db, user, "account", account_id)
    rows = db.scalars(select(ContentSeries).where(ContentSeries.account_id == account_id).order_by(ContentSeries.id)).all()
    revision_nos = _current_revision_nos(db, "series", [row.id for row in rows])
    return [_entity_json(db, "series", row, current_revision_no=revision_nos.get(row.id, 0)) for row in rows]


@router.post("/content-accounts/{account_id}/series", status_code=201)
def create_series(payload: NameIn, account_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    identity.owned_entity(db, user, "account", account_id, mutable=True)
    return _create(db, "series", ContentSeries(account_id=account_id, name=payload.name))


@router.get("/content-personas/{persona_id}/series")
def persona_editorial_series(persona_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    identity.owned_entity(db, user, "persona", persona_id)
    rows = db.scalars(select(ContentSeries).where(ContentSeries.persona_id == persona_id, ContentSeries.scope == "persona_editorial").order_by(ContentSeries.id)).all()
    revision_nos = _current_revision_nos(db, "series", [row.id for row in rows])
    return [_entity_json(db, "series", row, current_revision_no=revision_nos.get(row.id, 0)) for row in rows]


@router.post("/content-personas/{persona_id}/series", status_code=201)
def create_editorial_series(payload: NameIn, persona_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    row = identity.create_editorial_series(db, user, persona_id, name=payload.name)
    return _entity_json(db, "series", row)


@router.get("/content-series/{series_id}")
def get_series(series_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _entity_json(db, "series", identity.owned_entity(db, user, "series", series_id))


@router.patch("/content-series/{series_id}")
def rename_series(payload: NameIn, series_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return _rename(db, user, "series", series_id, payload.name)


@router.delete("/content-series/{series_id}", status_code=204)
def archive_series(series_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    _archive(db, user, "series", series_id)


class SeriesTargetIn(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    account_id: int = Field(gt=0)
    content_form: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9_]+$")


class SeriesTargetPatchIn(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    enabled: bool
    expected_version: int = Field(ge=1)


@router.get("/content-series/{series_id}/targets")
def list_series_targets(series_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return series_targets.list_targets(db, user, series_id)


@router.post("/content-series/{series_id}/targets", status_code=201)
def bind_series_target(series_id: int, payload: SeriesTargetIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return series_targets.bind_target(db, user, series_id, account_id=payload.account_id, content_form=payload.content_form)


@router.patch("/content-series/{series_id}/targets/{target_id}")
def update_series_target(series_id: int, target_id: int, payload: SeriesTargetPatchIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return series_targets.update_target(db, user, series_id, target_id, expected_version=payload.expected_version, enabled=payload.enabled)


@router.delete("/content-series/{series_id}/targets/{target_id}", status_code=204)
def unbind_series_target(series_id: int, target_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    series_targets.unbind_target(db, user, series_id, target_id)


def _register_revisions(kind: str, path: str) -> None:
    # The four entity kinds have the same revision contract and authorization behavior.
    async def list_rows(entity_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
        return _revisions(db, user, kind, entity_id)

    async def read_row(entity_id: int, revision_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
        return _revision_detail(db, user, kind, entity_id, revision_id)

    async def create_row(payload: RevisionIn, entity_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
        return _save(db, user, kind, entity_id, payload)

    router.add_api_route(path + "/revisions", list_rows, methods=["GET"], name=f"list_{kind}_revisions")
    router.add_api_route(path + "/revisions/{revision_id}", read_row, methods=["GET"], name=f"get_{kind}_revision")
    router.add_api_route(path + "/revisions", create_row, methods=["POST"], status_code=201, name=f"create_{kind}_revision")


for _kind, _path in (
    ("brand", "/content-brands/{entity_id}"),
    ("persona", "/content-personas/{entity_id}"),
    ("account", "/content-accounts/{entity_id}"),
    ("series", "/content-series/{entity_id}"),
):
    _register_revisions(_kind, _path)


@router.get("/content-identities/effective")
def effective_identity(persona_id: int, account_id: int | None = None, series_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return identity.effective(db, user, persona_id=persona_id, account_id=account_id, series_id=series_id)


@router.get("/content-identities/creative-catalog")
def creative_catalog(user: User = Depends(get_existing_user)):
    return inventory()


@router.post("/content-identities/creative-preview")
def creative_preview(payload: CreativeStagePreviewIn, db: Session = Depends(get_db), user: User = Depends(get_existing_user)):
    values = payload.model_dump(by_alias=True)
    if payload.profile_override is not None and "production_stages" not in payload.profile_override.model_fields_set:
        values["profile_override"].pop("production_stages", None)
    return creative_configuration.resolve(db, user, **values,
        has_profile_override="profile_override" in payload.model_fields_set)


@router.post("/content-identities/starter-preview")
def starter_preview(payload: StarterPreviewIn, user: User = Depends(get_existing_user)):
    try:
        return starter_personas.preview(payload.blueprint_key)
    except ValueError:
        raise HTTPException(404, "starter_blueprint_not_found") from None


@router.post("/content-identities/starter-apply", status_code=201)
def starter_apply(payload: StarterApplyIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return starter_personas.apply(db, user, payload.blueprint_key)


@router.post("/content-identities/starter-fork", status_code=201)
def starter_fork(payload: StarterForkIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return starter_personas.fork(db, user, payload.blueprint_key, name=payload.name,
        expected_profile_checksum=payload.expected_profile_checksum)


@router.get("/content-identities/starter-readiness")
def starter_readiness(persona_id: int = Query(gt=0), account_id: int | None = Query(default=None, gt=0),
        series_id: int | None = Query(default=None, gt=0), db: Session = Depends(get_db),
        user: User = Depends(get_existing_user)):
    return starter_personas.readiness(db, user, persona_id=persona_id, account_id=account_id, series_id=series_id)


@router.get("/identity-snapshots/{snapshot_id}")
def get_snapshot(snapshot_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.get(IdentitySnapshot, snapshot_id)
    if row is None or row.owner_user_id != user.id:
        raise HTTPException(404, "身份快照不存在")
    return identity.snapshot_json(row)


@router.get("/content-identities/brand-voices")
def published_voices(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return [{"id": row.id, "name": row.name, "version": row.version} for row in db.scalars(select(BrandVoiceVersion).where(BrandVoiceVersion.status == "published").order_by(BrandVoiceVersion.name, BrandVoiceVersion.version.desc())).all()]

@router.get("/content-accounts")
def owned_accounts(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from sqlalchemy import or_
    from ..models import ContentPersona
    rows = db.scalars(select(ContentAccount).where(or_(ContentAccount.owner_user_id == user.id,
        (ContentAccount.owner_user_id.is_(None)) & ContentAccount.persona_id.in_(select(ContentPersona.id).where(ContentPersona.owner_user_id == user.id))))
        .order_by(ContentAccount.id)).all()
    return [_entity_json(db, "account", row) for row in rows]


@router.post("/content-accounts/channel-accounts", status_code=201)
def create_independent_channel_account(payload: ChannelAccountIn, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    row = identity.register_public_channel_account(db, user, None, name=payload.name,
        channel=payload.platform_channel, platform_account_id=payload.platform_account_id)
    return _entity_json(db, "account", row)
