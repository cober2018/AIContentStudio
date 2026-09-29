"""Project-scoped immutable ChannelVariant read API."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_editor
from ..models import User
from ..services.channel_variants import current_revision, get_revision, list_revisions, save_revision

router = APIRouter(prefix="/api/v1", tags=["channel-variants"])


class VariantRevisionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    variant_key: str = Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    expected_revision: int = Field(ge=0)
    source_master_revision_id: int = Field(ge=1)
    expected_source_payload_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_source_context_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    channel_id: str = Field(min_length=1, max_length=100)
    content_form: str = Field(min_length=1, max_length=100)
    idempotency_key: str = Field(min_length=1, max_length=150)
    payload: dict
    source_kind: str = Field(default="manual_edit", pattern="^(manual_edit|deterministic_adapt)$")
    edit_summary: dict = Field(default_factory=dict)
    asset_refs: list[dict] = Field(default_factory=list, max_length=250)
    evidence_refs: list[dict] = Field(default_factory=list, max_length=250)
    llm_provenance: dict | None = None


@router.post("/content-projects/{project_id}/units/{unit_id}/channel-variants", status_code=201, dependencies=[Depends(require_editor)])
def create_channel_variant(project_id: int, unit_id: int, body: VariantRevisionIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return save_revision(db, project_id=project_id, unit_id=unit_id, user=user, payload=body.model_dump())


@router.get("/content-projects/{project_id}/units/{unit_id}/channel-variants")
def list_channel_variants(project_id: int, unit_id: int, variant_key: str | None = Query(default=None, max_length=120), limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {"items": list_revisions(db, project_id, unit_id, user, variant_key=variant_key, limit=limit, offset=offset), "limit": limit, "offset": offset}


@router.get("/content-projects/{project_id}/units/{unit_id}/channel-variants/current")
def get_current_channel_variant(project_id: int, unit_id: int, variant_key: str = Query(min_length=1, max_length=120), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return current_revision(db, project_id, unit_id, variant_key, user)


@router.get("/content-projects/{project_id}/units/{unit_id}/channel-variants/{variant_id}")
def get_channel_variant(project_id: int, unit_id: int, variant_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_revision(db, project_id, unit_id, variant_id, user)
