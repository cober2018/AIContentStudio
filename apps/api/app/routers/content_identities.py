"""Persistent Brand/Persona/Account/Series identity APIs."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_editor
from ..models import BrandVoiceVersion, ContentAccount, ContentBrand, ContentPersona, ContentSeries, IdentitySnapshot, User
from ..services import content_identity as identity

router = APIRouter(prefix="/api/v1", tags=["content-identities"])


class NameIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class RevisionIn(BaseModel):
    expected_revision: int = Field(ge=0)
    profile: identity.IdentityProfile


def _entity_json(db: Session, kind: str, row) -> dict:
    current = identity.current_revision(db, kind, row.id)
    data = {"id": row.id, "name": row.name, "status": row.status, "current_revision": current.revision_no if current else 0}
    if kind == "brand":
        data["owner_user_id"] = row.owner_user_id
    else:
        data[{"persona": "brand_id", "account": "persona_id", "series": "account_id"}[kind]] = getattr(row, {"persona": "brand_id", "account": "persona_id", "series": "account_id"}[kind])
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
    return [_entity_json(db, "brand", row) for row in db.scalars(select(ContentBrand).where(ContentBrand.owner_user_id == user.id).order_by(ContentBrand.id)).all()]


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


@router.get("/content-brands/{brand_id}/personas")
def brand_personas(brand_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    identity.owned_entity(db, user, "brand", brand_id)
    return [_entity_json(db, "persona", row) for row in db.scalars(select(ContentPersona).where(ContentPersona.brand_id == brand_id, ContentPersona.owner_user_id == user.id).order_by(ContentPersona.id)).all()]


@router.post("/content-brands/{brand_id}/personas", status_code=201)
def create_brand_persona(payload: NameIn, brand_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    identity.owned_entity(db, user, "brand", brand_id, mutable=True)
    return _create(db, "persona", ContentPersona(owner_user_id=user.id, brand_id=brand_id, name=payload.name))


@router.get("/content-personas/{persona_id}")
def get_persona(persona_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _entity_json(db, "persona", identity.owned_entity(db, user, "persona", persona_id))


@router.patch("/content-personas/{persona_id}")
def rename_persona(payload: NameIn, persona_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return _rename(db, user, "persona", persona_id, payload.name)


@router.delete("/content-personas/{persona_id}", status_code=204)
def archive_persona(persona_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    _archive(db, user, "persona", persona_id)


@router.get("/content-personas/{persona_id}/accounts")
def persona_accounts(persona_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    identity.owned_entity(db, user, "persona", persona_id)
    return [_entity_json(db, "account", row) for row in db.scalars(select(ContentAccount).where(ContentAccount.persona_id == persona_id).order_by(ContentAccount.id)).all()]


@router.post("/content-personas/{persona_id}/accounts", status_code=201)
def create_account(payload: NameIn, persona_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    identity.owned_entity(db, user, "persona", persona_id, mutable=True)
    return _create(db, "account", ContentAccount(persona_id=persona_id, name=payload.name))


@router.get("/content-accounts/{account_id}")
def get_account(account_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _entity_json(db, "account", identity.owned_entity(db, user, "account", account_id))


@router.patch("/content-accounts/{account_id}")
def rename_account(payload: NameIn, account_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return _rename(db, user, "account", account_id, payload.name)


@router.delete("/content-accounts/{account_id}", status_code=204)
def archive_account(account_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    _archive(db, user, "account", account_id)


@router.get("/content-accounts/{account_id}/series")
def account_series(account_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    identity.owned_entity(db, user, "account", account_id)
    return [_entity_json(db, "series", row) for row in db.scalars(select(ContentSeries).where(ContentSeries.account_id == account_id).order_by(ContentSeries.id)).all()]


@router.post("/content-accounts/{account_id}/series", status_code=201)
def create_series(payload: NameIn, account_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    identity.owned_entity(db, user, "account", account_id, mutable=True)
    return _create(db, "series", ContentSeries(account_id=account_id, name=payload.name))


@router.get("/content-series/{series_id}")
def get_series(series_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _entity_json(db, "series", identity.owned_entity(db, user, "series", series_id))


@router.patch("/content-series/{series_id}")
def rename_series(payload: NameIn, series_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return _rename(db, user, "series", series_id, payload.name)


@router.delete("/content-series/{series_id}", status_code=204)
def archive_series(series_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    _archive(db, user, "series", series_id)


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


@router.get("/identity-snapshots/{snapshot_id}")
def get_snapshot(snapshot_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.get(IdentitySnapshot, snapshot_id)
    if row is None or row.owner_user_id != user.id:
        raise HTTPException(404, "身份快照不存在")
    return identity.snapshot_json(row)


@router.get("/content-identities/brand-voices")
def published_voices(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return [{"id": row.id, "name": row.name, "version": row.version} for row in db.scalars(select(BrandVoiceVersion).where(BrandVoiceVersion.status == "published").order_by(BrandVoiceVersion.name, BrandVoiceVersion.version.desc())).all()]
