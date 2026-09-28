"""Read-only project review projection over existing persisted facts."""

from difflib import SequenceMatcher

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ContentAsset, ContentProject, ContentUnit, DeliveryTarget, Draft, Review, WorkflowRun
from .candidates import candidate_hash
from .project_evidence import current_boundary
from .project_projection_context import ProjectProjectionContext


def candidate_rows(db: Session, unit_id: int) -> list[ContentAsset]:
    return db.scalars(select(ContentAsset).where(ContentAsset.content_unit_id == unit_id).order_by(ContentAsset.id.desc())).all()


def unit_projection(db: Session, unit: ContentUnit, *, context: ProjectProjectionContext | None = None) -> dict:
    candidates = context.candidates.get(unit.id, []) if context is not None else candidate_rows(db, unit.id)
    current = candidates[0] if candidates else None
    targets = (context.targets.get(current.id, []) if context is not None else db.scalars(select(DeliveryTarget).where(DeliveryTarget.content_asset_id == current.id).order_by(DeliveryTarget.id.desc())).all()) if current else []
    reviews = (context.reviews.get(current.id, []) if context is not None else db.scalars(select(Review).where(Review.content_asset_id == current.id).order_by(Review.id.desc())).all()) if current else []
    run = context.runs.get(unit.id) if context is not None else db.scalar(select(WorkflowRun).where(WorkflowRun.content_unit_id == unit.id).order_by(WorkflowRun.id.desc()).limit(1))

    def attempts(target):
        return context.attempts.get(target.id, []) if context is not None else target.attempts

    def receipts(target):
        return context.receipts.get(target.id, []) if context is not None else target.receipts

    live_db = context.live_reads(unit.project_id) if context is not None else db
    dimensions: dict[str, dict] = {}

    def dimension(name: str, status: str, reasons: list[str] | None = None) -> None:
        dimensions[name] = {"status": status, "reasons": reasons or []}

    dimension("content", "ready" if current else "blocked", [] if current else ["candidate_missing"])
    dimension("identity", "ready" if unit.identity_snapshot_id else "blocked", [] if unit.identity_snapshot_id else ["identity_unready"])
    boundary = context.boundaries.get(unit.project_id) if context is not None else current_boundary(db, unit.project_id)
    evidence = (current.candidate_manifest_json or {}).get("evidence", {}) if current else {}
    evidence_stale = bool(current and evidence.get("boundary_id") and boundary and evidence["boundary_id"] != boundary.id)
    from .project_review import live_evidence_reasons

    evidence_reasons = live_evidence_reasons(live_db, unit.project_id, current.candidate_manifest_json or {}) if current else ([] if boundary else ["evidence_unready"])
    dimension("evidence", "stale" if evidence_stale else ("blocked" if evidence_reasons else "ready"), evidence_reasons)
    media_reasons: list[str] = []
    if current:
        from .delivery import _live_media_rights

        for media in (current.candidate_manifest_json or {}).get("media", []):
            if _live_media_rights(live_db, media) is not True:
                media_reasons.append(f"media_rights_unready:{media.get('material_revision_id') or media.get('draft_media_id')}")
    dimension("media", "blocked" if media_reasons else "ready", media_reasons)
    checksum_ok = bool(current and current.candidate_hash and candidate_hash(current.candidate_manifest_json or {}) == current.candidate_hash)
    dimension("checks", "ready" if checksum_ok else "blocked", [] if checksum_ok else ["candidate_integrity_unready"])
    stale_revision = False
    if current and current.draft_id:
        draft = context.drafts.get(current.draft_id) if context is not None else db.get(Draft, current.draft_id)
        if draft:
            latest = context.draft_revisions.get(draft.content_job_id) if context is not None else db.scalar(select(Draft.revision_no).where(Draft.content_job_id == draft.content_job_id).order_by(Draft.revision_no.desc()).limit(1))
            stale_revision = latest != draft.revision_no
    dimension("candidate", "stale" if stale_revision else ("ready" if current else "blocked"), ["newer_draft_revision"] if stale_revision else ([] if current else ["freeze_required"]))
    approved = bool(current and current.status in {"approved", "exported"} and current.candidate_hash == current.approved_candidate_hash and any(row.decision == "approved" and row.candidate_hash == current.candidate_hash for row in reviews))
    dimension("approval", "approved" if approved else "waiting_review" if current else "blocked", [] if approved or current else ["candidate_missing"])
    dimension("delivery", "ready" if targets else "blocked", [] if targets else ["authorization_missing"])
    unknown = any(target.status == "reconciliation_needed" or any(attempt.status == "unknown" and (attempt.response_metadata_json or {}).get("reconciled") is None for attempt in attempts(target)) for target in targets)
    if unknown:
        summary = "unknown"
    elif any(target.status == "blocked" for target in targets) or media_reasons or (evidence_reasons and not evidence_stale) or (not checksum_ok and current is not None):
        summary = "blocked"
    elif evidence_stale or stale_revision or (run and run.status == "stale" and current is None):
        summary = "stale"
    elif current and not approved:
        summary = "waiting_review"
    elif current and not targets:
        summary = "approved"
    elif targets and all(target.status == "human_confirmed" for target in targets):
        summary = "delivered"
    elif targets:
        summary = "delivery_ready"
    elif not unit.identity_snapshot_id or boundary is None:
        summary = "blocked"
    else:
        summary = "ready"
    return {
        "unit_id": unit.id, "project_id": unit.project_id, "title": unit.title, "modality": unit.modality,
        "persona_id": unit.persona_id, "account_id": unit.account_id, "channel_id": unit.channel_id,
        "identity_snapshot_id": unit.identity_snapshot_id,
        "unit_status": unit.status, "summary": summary, "dimensions": dimensions,
        "current_candidate": {"id": current.id, "hash": current.candidate_hash, "status": current.status, "title": current.title} if current else None,
        "history": [{"id": row.id, "hash": row.candidate_hash, "status": row.status, "title": row.title} for row in candidates[1:]],
        "reviews": [{"id": row.id, "decision": row.decision, "candidate_hash": row.candidate_hash, "comment": row.comment} for row in reviews],
        "targets": [{"id": target.id, "status": target.status, "action": target.action, "account_ref": target.account_ref,
                     "content_account_id": target.content_account_id,
                     "attempts": [] if context is not None and context.summary_only else [{"id": attempt.id, "status": attempt.status, "remote_id": attempt.remote_id, "error": attempt.error} for attempt in attempts(target)],
                     "receipts": [{"id": receipt.id, "status": receipt.status, "evidence_ref": receipt.evidence_ref, "note": receipt.note} for receipt in receipts(target)]} for target in targets],
    }


def project_projection(db: Session, project: ContentProject) -> dict:
    units = db.scalars(select(ContentUnit).where(ContentUnit.project_id == project.id).order_by(ContentUnit.id)).all()
    return {"project_id": project.id, "title": project.title, "status": project.status, "units": [unit_projection(db, unit) for unit in units]}


def candidate_diff(previous: ContentAsset | None, current: ContentAsset) -> dict:
    prior = previous.candidate_manifest_json or {} if previous else {}
    latest = current.candidate_manifest_json or {}
    sections = ("content", "media", "evidence", "identity", "production", "checks", "render", "channel")
    changed = {name: {"changed": prior.get(name) != latest.get(name)} for name in sections}
    before = str((prior.get("content") or {}).get("body_markdown") or "")[:2000]
    after = str((latest.get("content") or {}).get("body_markdown") or "")[:2000]
    return {"from_candidate_id": previous.id if previous else None, "to_candidate_id": current.id,
            "changed_sections": changed, "text": {"before_chars": len(before), "after_chars": len(after),
                                                 "similarity": round(SequenceMatcher(None, before, after).ratio(), 4)}}
