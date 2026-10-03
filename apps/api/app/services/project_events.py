"""Stable, transactional project activity records."""

from sqlalchemy.orm import Session

from ..models import ProjectEvent

EVENT_TYPES = frozenset({
    "project.created", "project.updated", "project.archived",
    "brief.revision_created", "source.attached", "source.detached",
    "fact_boundary.bound", "fact_boundary.draft_cloned", "fact_boundary.frozen_bound",
    "unit.created", "unit.updated", "unit.replaced", "unit.archived", "unit.deleted",
    "workflow.override_saved", "workflow.role_default_saved",
    "data.snapshot_created", "data.snapshot_changed",
    "asset.attached", "asset.detached", "asset.workflow_generated",
    "draft.generated", "candidate.associated",
    "candidate.frozen", "content.approved", "content.changes_requested",
    "delivery.authorized", "delivery.prepared", "delivery.succeeded", "delivery.failed", "delivery.unknown",
    "delivery.reconciled", "delivery.receipt_recorded", "delivery.publication_confirmed",
    "project.created_from_opportunity",
    "content_master.saved",
    "content_master.generated",
    "channel_variant.saved",
})


def record_project_event(
    db: Session,
    *,
    project_id: int,
    event_type: str,
    actor: str | None,
    entity_type: str | None = None,
    entity_id: str | int | None = None,
    payload: dict | None = None,
) -> ProjectEvent:
    if event_type not in EVENT_TYPES:
        raise ValueError(f"未注册的项目事件类型：{event_type}")
    from ..observability import current_correlation

    event_payload = dict(payload or {})
    telemetry = current_correlation()
    if telemetry:
        event_payload.setdefault("_telemetry", telemetry)
    event = ProjectEvent(
        project_id=project_id,
        event_type=event_type,
        actor=actor,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        payload_json=event_payload,
        schema_version=1,
    )
    db.add(event)
    return event
