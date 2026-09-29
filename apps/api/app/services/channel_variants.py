"""Project-owned immutable ChannelVariant history reads."""

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import (
    ChannelVariantAssetRef,
    ChannelVariantCheckRun,
    ChannelVariantEvidenceRef,
    ChannelVariantRevision,
    User,
)
from .content_masters import owned_unit


def _serialize(db: Session, row: ChannelVariantRevision) -> dict:
    assets = db.scalars(
        select(ChannelVariantAssetRef)
        .where(ChannelVariantAssetRef.variant_revision_id == row.id)
        .order_by(ChannelVariantAssetRef.sort_order, ChannelVariantAssetRef.id)
    ).all()
    evidence = db.scalars(
        select(ChannelVariantEvidenceRef)
        .where(ChannelVariantEvidenceRef.variant_revision_id == row.id)
        .order_by(ChannelVariantEvidenceRef.sort_order, ChannelVariantEvidenceRef.id)
    ).all()
    checks = db.scalars(
        select(ChannelVariantCheckRun)
        .where(ChannelVariantCheckRun.variant_revision_id == row.id)
        .order_by(ChannelVariantCheckRun.created_at.desc(), ChannelVariantCheckRun.id.desc())
    ).all()
    return {
        "id": row.id,
        "project_id": row.project_id,
        "content_unit_id": row.content_unit_id,
        "variant_key": row.variant_key,
        "revision_no": row.revision_no,
        "parent_revision_id": row.parent_revision_id,
        "source_master_revision_id": row.source_master_revision_id,
        "source_master_payload_hash": row.source_master_payload_hash,
        "source_master_context_hash": row.source_master_context_hash,
        "source_channel_id": row.source_channel_id,
        "source_content_form": row.source_content_form,
        "identity_snapshot_id": row.identity_snapshot_id,
        "channel_id": row.channel_id,
        "content_form": row.content_form,
        "artifact_kind": row.artifact_kind,
        "profile_template_version_id": row.profile_template_version_id,
        "profile_key": row.profile_key,
        "profile_version": row.profile_version,
        "profile_hash": row.profile_hash,
        "adapter_key": row.adapter_key,
        "adapter_version": row.adapter_version,
        "rule_hash": row.rule_hash,
        "payload_schema": row.payload_schema,
        "payload": row.payload_json,
        "payload_hash": row.payload_hash,
        "context_hash": row.context_hash,
        "source_kind": row.source_kind,
        "edit_summary": row.edit_summary_json,
        "llm_provenance": row.llm_provenance_json,
        "idempotency_key": row.idempotency_key,
        "created_by": row.created_by,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "assets": [
            {"id": item.id, "material_revision_id": item.material_revision_id, "role": item.role, "slot_key": item.slot_key, "sort_order": item.sort_order, "placement": item.placement_json, "rights_snapshot": item.rights_snapshot_json, "content_hash": item.content_hash_snapshot}
            for item in assets
        ],
        "evidence": [
            {"id": item.id, "fact_pack_item_id": item.fact_pack_item_id, "role": item.role, "locator": item.content_locator_json, "sort_order": item.sort_order, "snapshot_checksum": item.snapshot_checksum}
            for item in evidence
        ],
        "checks": [
            {"id": item.id, "check_kind": item.check_kind, "input_hash": item.input_hash, "profile_hash": item.profile_hash, "adapter_hash": item.adapter_hash, "rule_hash": item.rule_hash, "status": item.status, "report": item.report_json, "created_at": item.created_at.isoformat() if item.created_at else None}
            for item in checks
        ],
    }


def list_revisions(db: Session, project_id: int, unit_id: int, user: User, *, variant_key: str | None = None, limit: int = 50, offset: int = 0) -> list[dict]:
    owned_unit(db, project_id, unit_id, user)
    statement = select(ChannelVariantRevision).where(ChannelVariantRevision.project_id == project_id, ChannelVariantRevision.content_unit_id == unit_id)
    if variant_key is not None:
        statement = statement.where(ChannelVariantRevision.variant_key == variant_key)
    rows = db.scalars(statement.order_by(ChannelVariantRevision.created_at.desc(), ChannelVariantRevision.id.desc()).offset(offset).limit(limit)).all()
    return [_serialize(db, row) for row in rows]


def current_revision(db: Session, project_id: int, unit_id: int, variant_key: str, user: User) -> dict | None:
    owned_unit(db, project_id, unit_id, user)
    row = db.scalar(
        select(ChannelVariantRevision)
        .where(ChannelVariantRevision.project_id == project_id, ChannelVariantRevision.content_unit_id == unit_id, ChannelVariantRevision.variant_key == variant_key)
        .order_by(ChannelVariantRevision.revision_no.desc())
        .limit(1)
    )
    return _serialize(db, row) if row else None


def get_revision(db: Session, project_id: int, unit_id: int, variant_id: int, user: User) -> dict:
    owned_unit(db, project_id, unit_id, user)
    row = db.get(ChannelVariantRevision, variant_id)
    if row is None or row.project_id != project_id or row.content_unit_id != unit_id:
        raise HTTPException(404, "ChannelVariant版本不存在")
    return _serialize(db, row)
