"""Project-scoped immutable ChannelVariant read API."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_editor
from ..models import User
from ..services.channel_variants import (
    current_revision,
    get_revision,
    get_variant_checks,
    list_revisions,
    revision_diff,
    run_variant_checks,
    save_revision,
    variant_capabilities,
)
from ..services.creative_intents import CreativeIntentError, canonical_intent
from . import CapabilityInputRoute

router = APIRouter(prefix="/api/v1", tags=["channel-variants"], route_class=CapabilityInputRoute)


class VariantRevisionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    variant_key: str = Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    expected_revision: int = Field(ge=0)
    source_master_revision_id: int = Field(ge=1)
    expected_source_payload_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_source_context_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_profile_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    channel_id: str = Field(min_length=1, max_length=100)
    content_form: str = Field(min_length=1, max_length=100)
    idempotency_key: str = Field(min_length=1, max_length=150)
    payload: dict
    source_kind: str = Field(default="manual_edit", pattern="^(manual_edit|deterministic_adapt|model_assisted)$")
    edit_summary: dict = Field(default_factory=dict)
    asset_refs: list[dict] = Field(default_factory=list, max_length=250)
    evidence_refs: list[dict] = Field(default_factory=list, max_length=250)
    llm_provenance: dict | None = None
    creative_intent: dict | None = None
    target_account_id: int | None = Field(default=None, ge=1)
    expected_target_context_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")

    @field_validator("creative_intent", mode="before")
    @classmethod
    def validate_creative_intent(cls, value):
        try:
            return canonical_intent(value)[0]
        except CreativeIntentError as exc:
            raise HTTPException(422, {"code": str(exc)}) from None


class VariantAdaptPreviewIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_master_revision_id: int = Field(ge=1)
    expected_source_payload_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_source_context_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    channel_id: str = Field(min_length=1, max_length=100)
    content_form: str = Field(min_length=1, max_length=100)
    target_account_id: int | None = Field(default=None, ge=1)
    question: dict | None = None


@router.post("/content-projects/{project_id}/units/{unit_id}/channel-variants/adapt-preview", dependencies=[Depends(require_editor)])
def preview_channel_adaptation(project_id: int, unit_id: int, body: VariantAdaptPreviewIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from ..services.channel_variants import adapt_preview

    return adapt_preview(db, project_id=project_id, unit_id=unit_id, user=user, payload=body.model_dump())


@router.post("/content-projects/{project_id}/units/{unit_id}/channel-variants/model-suggestions", dependencies=[Depends(require_editor)])
async def suggest_channel_adaptation(project_id: int, unit_id: int, body: VariantAdaptPreviewIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from ..services.channel_variants import suggest_adaptation

    return await suggest_adaptation(db, project_id=project_id, unit_id=unit_id, user=user, payload=body.model_dump())


@router.post("/content-projects/{project_id}/units/{unit_id}/channel-variants", status_code=201, dependencies=[Depends(require_editor)])
def create_channel_variant(project_id: int, unit_id: int, body: VariantRevisionIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    payload = body.model_dump()
    # Keep existing default fields in the idempotency fingerprint for old clients.
    if "creative_intent" not in body.model_fields_set:
        payload.pop("creative_intent")
    if "expected_profile_hash" not in body.model_fields_set:
        payload.pop("expected_profile_hash")
    for field in ("target_account_id", "expected_target_context_hash"):
        if field not in body.model_fields_set:
            payload.pop(field)
    return save_revision(db, project_id=project_id, unit_id=unit_id, user=user, payload=payload)


@router.get("/content-projects/{project_id}/units/{unit_id}/channel-variants")
def list_channel_variants(project_id: int, unit_id: int, variant_key: str | None = Query(default=None, max_length=120), limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {"items": list_revisions(db, project_id, unit_id, user, variant_key=variant_key, limit=limit, offset=offset), "limit": limit, "offset": offset}


@router.get("/content-projects/{project_id}/units/{unit_id}/channel-variants/current")
def get_current_channel_variant(project_id: int, unit_id: int, variant_key: str = Query(min_length=1, max_length=120), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return current_revision(db, project_id, unit_id, variant_key, user)


@router.get("/content-projects/{project_id}/units/{unit_id}/channel-variants/capabilities")
def get_channel_variant_capabilities(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return variant_capabilities(db, project_id, unit_id, user)


@router.get("/content-projects/{project_id}/units/{unit_id}/channel-variants/{variant_id}")
def get_channel_variant(project_id: int, unit_id: int, variant_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_revision(db, project_id, unit_id, variant_id, user)


@router.get("/content-projects/{project_id}/units/{unit_id}/channel-variants/{variant_id}/diff")
def get_channel_variant_diff(project_id: int, unit_id: int, variant_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return revision_diff(db, project_id, unit_id, variant_id, user)


@router.get("/content-projects/{project_id}/units/{unit_id}/channel-variants/{variant_id}/checks")
def get_channel_variant_checks(project_id: int, unit_id: int, variant_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_variant_checks(db, project_id, unit_id, variant_id, user)


@router.post("/content-projects/{project_id}/units/{unit_id}/channel-variants/{variant_id}/checks", dependencies=[Depends(require_editor)])
def run_channel_variant_checks(project_id: int, unit_id: int, variant_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return run_variant_checks(db, project_id, unit_id, variant_id, user)
