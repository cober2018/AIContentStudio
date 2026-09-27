"""Deterministic project overview derived from persisted state."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ContentPersona, ContentUnit, IdentitySnapshot, WorkflowRun, WorkflowStep
from .project_brief import current_brief
from .project_evidence import current_boundary


def project_overview(db: Session, project_id: int) -> dict:
    brief = current_brief(db, project_id)
    boundary = current_boundary(db, project_id)
    units = db.scalars(select(ContentUnit).where(ContentUnit.project_id == project_id).order_by(ContentUnit.id)).all()
    active = [unit for unit in units if unit.status != "archived"]
    modality_counts = {key: sum(unit.modality == key for unit in active) for key in ("text", "graphic", "video")}
    personas = []
    for persona_id in sorted({unit.persona_id for unit in active}):
        persona = db.get(ContentPersona, persona_id)
        personas.append({"id": persona_id, "name": persona.name if persona else None, "unitCount": sum(unit.persona_id == persona_id for unit in active)})
    risks: list[dict] = []
    pending: list[dict] = []
    latest_runs: list[WorkflowRun] = []
    for unit in active:
        snapshot = db.get(IdentitySnapshot, unit.identity_snapshot_id) if unit.identity_snapshot_id else None
        if snapshot is None or not snapshot.effective_profile_json:
            risks.append({"code": "identity_unready", "unit_id": unit.id, "reason": "legacy_identity" if snapshot is None else "incomplete_profile"})
        if unit.status in {"blocked", "stale", "unknown", "failed"}:
            risks.append({"code": f"unit_{unit.status}", "unit_id": unit.id})
        if unit.status in {"waiting_human", "waiting_input"}:
            pending.append({"code": "unit_waiting_human", "unit_id": unit.id})
        run = db.scalar(select(WorkflowRun).where(WorkflowRun.content_unit_id == unit.id).order_by(WorkflowRun.id.desc()).limit(1))
        if run:
            latest_runs.append(run)
            if run.status in {"blocked", "stale", "unknown", "failed"}:
                risks.append({"code": f"run_{run.status}", "unit_id": unit.id, "run_id": run.id})
            step_statuses = set(db.scalars(select(WorkflowStep.status).where(WorkflowStep.run_id == run.id, WorkflowStep.status.in_(["stale", "failed", "waiting_input"]))).all())
            for status in sorted(step_statuses & {"stale", "failed"}):
                risks.append({"code": f"step_{status}", "unit_id": unit.id, "run_id": run.id})
            if "waiting_input" in step_statuses:
                pending.append({"code": "step_waiting_human", "unit_id": unit.id, "run_id": run.id})
            if run.status in {"waiting_input", "waiting_human"}:
                pending.append({"code": "run_waiting_human", "unit_id": unit.id, "run_id": run.id})
    if brief is None:
        stage, next_action = "brief_needed", {"code": "brief.create", "label": "填写项目简报", "href": f"/projects/{project_id}?tab=brief"}
    elif boundary is None:
        stage, next_action = "evidence_needed", {"code": "evidence.bind", "label": "建立事实边界", "href": f"/projects/{project_id}?tab=evidence"}
    elif not active:
        stage, next_action = "matrix_needed", {"code": "matrix.create_unit", "label": "添加内容单元", "href": f"/projects/{project_id}?tab=matrix"}
    elif risks:
        only_identity = all(risk["code"] == "identity_unready" for risk in risks)
        stage, next_action = "attention_required", {"code": "identity.rebind" if only_identity else "production.resolve_risk", "label": "完善或重绑内容身份" if only_identity else "处理生产风险", "href": f"/projects/{project_id}?tab=matrix"}
    elif pending:
        stage, next_action = "waiting_human", {"code": "production.complete_human", "label": "处理人工节点", "href": f"/projects/{project_id}?tab=matrix"}
    elif all(unit.status in {"ready", "approved"} for unit in active):
        stage, next_action = "review_ready", None
    else:
        stage, next_action = "production", {"code": "production.continue", "label": "继续生产", "href": f"/projects/{project_id}?tab=matrix"}
    return {"stage": stage, "activeUnitCount": len(active), "archivedUnitCount": len(units) - len(active), "modalityCounts": modality_counts, "personas": personas, "brief": {"ready": brief is not None, "revision": brief.revision_no if brief else None}, "factBoundary": {"ready": boundary is not None, "revision": boundary.revision_no if boundary else None, "factPackId": boundary.fact_pack_id if boundary else None, "factPackVersion": boundary.fact_pack_version if boundary else None, "checksum": boundary.fact_pack_checksum if boundary else None}, "risks": risks, "pendingDecisions": pending, "nextAction": next_action}
