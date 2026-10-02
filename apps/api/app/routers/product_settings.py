"""Safe Settings inventory and explicit scoped operator verification."""

from datetime import UTC, datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_admin
from ..models import AuditLog, CapabilityRegistration, User
from ..services import capability_integrations, content_identity, product_settings
from ..services.content_harness.publishers import bootstrap_publishers
from ..services.content_harness.registry import registry
from . import CapabilityInputRoute

router = APIRouter(prefix="/api/v1/settings", tags=["product-settings"], route_class=CapabilityInputRoute)


class PublisherVerificationIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    channel: Literal["wechat"]
    content_form: Literal["article"]
    action: Literal["auto_draft"]
    content_account_id: int = Field(ge=1)
    account_ref: str = Field(pattern=r"^[A-Za-z0-9_.:@-]{1,150}$")
    publisher_key: Literal["publisher.wechat.wewrite", "publisher.wechat.official"]
    publisher_version: Literal["1"]
    result: Literal["verified", "revoked"]
    reference_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    confirm_readback: bool = False
    validity_hours: int = Field(default=24, ge=1, le=24)


class RendererProbeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: int = Field(ge=1)
    unit_id: int = Field(ge=1)
    master_id: int = Field(ge=1)
    renderer_key: str = Field(pattern=r"^[A-Za-z0-9_.-]{1,150}$")
    renderer_version: str = Field(pattern=r"^[A-Za-z0-9_.-]{1,50}$")
    expected_payload_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_context_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    result: Literal["verified", "revoked"] = "verified"


@router.post("/renderer-probes", status_code=201)
def renderer_probe(payload: RendererProbeIn, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    from ..services import renderer_capabilities

    return renderer_capabilities.probe(db, user, payload.model_dump())


@router.get("/capabilities")
def capabilities(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return product_settings.capability_inventory(db, user)


class MediaRendererVerificationIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stage_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    confirmed: bool
    expected_input_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_output_hash: str = Field(pattern=r"^[a-f0-9]{64}$")


@router.post("/media-renderer-verifications", status_code=201)
def verify_media_renderer(payload: MediaRendererVerificationIn, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    from ..services.media_renderers import verify_stage

    return verify_stage(db, user, payload.model_dump())


@router.post("/media-renderer-verifications/{verification_id}/revoke", status_code=201)
def revoke_media_renderer(verification_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    from ..services.media_renderers import revoke

    return revoke(db, user, verification_id)


@router.post("/publisher-verifications", status_code=201)
def verify_publisher(payload: PublisherVerificationIn, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    account = content_identity.owned_entity(db, user, "account", payload.content_account_id, mutable=True)
    if not payload.confirm_readback:
        raise HTTPException(422, "publisher_readback_confirmation_required")
    bootstrap_publishers()
    registry.resolve("publisher", payload.publisher_key, payload.publisher_version)
    scope = {key: getattr(payload, key) for key in (
        "channel", "content_form", "action", "content_account_id", "account_ref", "publisher_key", "publisher_version",
    )}
    registration = db.scalar(select(CapabilityRegistration).where(
        CapabilityRegistration.kind == "publisher", CapabilityRegistration.key == payload.publisher_key,
        CapabilityRegistration.version == payload.publisher_version,
    ))
    official = payload.publisher_key == "publisher.wechat.official"
    if official:
        from ..services import wechat_official

        if account.platform_channel != "wechat" or account.platform_account_id != payload.account_ref:
            raise HTTPException(409, "official_account_scope_mismatch")
        if payload.result == "verified" and not wechat_official.remote_contract_ready():
            raise HTTPException(409, "official_contract_unresolved")
        fingerprint = wechat_official.scope_fingerprint(db, scope) if payload.result == "verified" else None
        registration_fingerprint = wechat_official.implementation_fingerprint()
    else:
        fingerprint = capability_integrations.publisher_runtime_fingerprint(payload.publisher_key, payload.publisher_version)
        registration_fingerprint = fingerprint
    if payload.result == "verified":
        if fingerprint is None:
            raise HTTPException(409, "publisher_runtime_unavailable")
        if registration is None:
            registration = CapabilityRegistration(kind="publisher", key=payload.publisher_key,
                                                   version=payload.publisher_version, status="configured",
                                                   config_fingerprint=registration_fingerprint, created_by=user.email)
            db.add(registration)
            db.flush()
        else:
            registration.config_fingerprint = registration_fingerprint
            registration.status = "configured"
    elif registration is None:
        raise HTTPException(404, "publisher_verification_not_found")
    evidence = {"kind": "human_readback", "reference_hash": payload.reference_hash} if payload.result == "verified" else {"kind": "revocation"}
    try:
        event = capability_integrations.append_verification(db, registration, scope_kind="publisher_action", scope=scope,
                                                            result=payload.result, actor=user.email, evidence=evidence,
                                                            expires_at=datetime.now(UTC) + timedelta(hours=payload.validity_hours) if payload.result == "verified" else None)
    except ValueError:
        db.rollback()
        raise HTTPException(409, "publisher_verification_conflict") from None
    db.add(AuditLog(event="publisher.verification_recorded", actor=user.email,
                    entity_type="capability_verification", entity_id=str(event.id),
                    detail_json={"registration_id": registration.id, "scope": scope, "result": payload.result}))
    db.commit()
    return {"verification_id": event.id, "registration_id": registration.id, "result": event.result,
            "scope": scope, "expires_at": event.expires_at.isoformat() if event.expires_at else None}


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
