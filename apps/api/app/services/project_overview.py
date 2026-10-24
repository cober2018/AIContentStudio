"""Deterministic project overview derived from persisted state."""

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ContentMasterRevision, ContentPersona, ContentUnit, IdentitySnapshot, WorkflowRun, WorkflowStep
from .content_masters import master_risks
from .product_context import is_product
from .project_brief import current_brief
from .project_evidence import current_boundary
from .project_projection_context import ProjectProjectionContext
from .project_review_projection import unit_projection


def project_overviews(db: Session, project_ids: Iterable[int], *, summary_only: bool = False) -> dict[int, dict]:
    """Read authorized IDs; Home can pass batches of 100 with summary_only=True.

    Summary mode omits candidate history and attempt/receipt payloads, preserving
    current-candidate decisions and unresolved unknown delivery semantics.
    """
    context = ProjectProjectionContext(db, project_ids, summary_only=summary_only)
    return {project_id: project_overview(db, project_id, context=context) for project_id in context.project_ids}


def project_overview(db: Session, project_id: int, *, context: ProjectProjectionContext | None = None) -> dict:
    brief = context.briefs.get(project_id) if context is not None else current_brief(db, project_id)
    boundary = context.boundaries.get(project_id) if context is not None else current_boundary(db, project_id)
    units = context.units.get(project_id, []) if context is not None else db.scalars(select(ContentUnit).where(ContentUnit.project_id == project_id).order_by(ContentUnit.id)).all()
    active = [unit for unit in units if not unit.lifecycle_readonly]
    review_units = [unit_projection(db, unit, context=context) for unit in active]
    modality_counts = {key: sum(unit.modality == key for unit in active) for key in ("text", "graphic", "video")}
    personas = []
    persona_units = [unit for unit in active if not is_product(unit) and unit.persona_id is not None]
    for persona_id in sorted({unit.persona_id for unit in persona_units}):
        persona = context.personas.get(persona_id) if context is not None else db.get(ContentPersona, persona_id)
        personas.append({"id": persona_id, "name": persona.name if persona else None, "unitCount": sum(unit.persona_id == persona_id for unit in persona_units)})
    risks: list[dict] = []
    pending: list[dict] = []
    latest_runs: list[WorkflowRun] = []
    for unit in active:
        review_unit = next((row for row in review_units if row["unit_id"] == unit.id), None)
        if review_unit:
            for series in review_unit.get("variantSeries", []):
                if series["status"] in {"stale", "blocked"}:
                    risks.append({"code": f"variant_{series['status']}", "unit_id": unit.id,
                                  "variant_key": series["variantKey"], "candidate_id": series["candidateId"]})
        master = context.masters.get(unit.id) if context is not None else db.scalar(select(ContentMasterRevision).where(ContentMasterRevision.content_unit_id == unit.id).order_by(ContentMasterRevision.revision_no.desc()).limit(1))
        product_configuration_blocked = is_product(unit) and review_unit and (review_unit.get("dimensions", {}).get("identity") or {}).get("status") == "blocked"
        if master and not product_configuration_blocked:
            risks.extend(master_risks(db, master))
        snapshot = context.snapshots.get(unit.identity_snapshot_id) if context is not None else db.get(IdentitySnapshot, unit.identity_snapshot_id) if unit.identity_snapshot_id else None
        if is_product(unit) and review_unit and (review_unit.get("dimensions", {}).get("identity") or {}).get("status") == "blocked":
            risks.append({"code": "product_configuration_unavailable", "unit_id": unit.id})
        if not is_product(unit) and (snapshot is None or not snapshot.effective_profile_json):
            risks.append({"code": "identity_unready", "unit_id": unit.id, "reason": "legacy_identity" if snapshot is None else "incomplete_profile"})
        if unit.status in {"blocked", "stale", "unknown", "failed"}:
            risks.append({"code": f"unit_{unit.status}", "unit_id": unit.id})
        if unit.status in {"waiting_human", "waiting_input"}:
            pending.append({"code": "unit_waiting_human", "unit_id": unit.id})
        run = context.runs.get(unit.id) if context is not None else db.scalar(select(WorkflowRun).where(WorkflowRun.content_unit_id == unit.id).order_by(WorkflowRun.id.desc()).limit(1))
        if run:
            latest_runs.append(run)
            if run.status in {"blocked", "stale", "unknown", "failed"}:
                risks.append({"code": f"run_{run.status}", "unit_id": unit.id, "run_id": run.id})
            step_statuses = context.step_statuses.get(run.id, set()) if context is not None else set(db.scalars(select(WorkflowStep.status).where(WorkflowStep.run_id == run.id, WorkflowStep.status.in_(["stale", "failed", "waiting_input"]))).all())
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
    if stage in {"review_ready", "production"}:
        decisions = (
            ("unknown", "delivery.reconcile", "核对交付结果"),
            ("waiting_review", "content.approve", "审核冻结候选"),
            ("approved", "delivery.authorize", "授权交付目标"),
            ("delivery_ready", "delivery.complete", "完成交付并回填"),
        )
        for status, code, label in decisions:
            if any(unit["summary"] == status for unit in review_units):
                stage = "review_ready"
                next_action = {"code": code, "label": label, "href": f"/review?project={project_id}"}
                break
    master_risk = next((risk for risk in risks if risk["code"].startswith("master_")), None)
    if master_risk and stage == "attention_required":
        next_action = {"code": "production.resolve_risk", "label": "处理内容Master风险", "href": f"/projects/{project_id}/units/{master_risk['unit_id']}/production"}
    if any(unit["summary"] == "unknown" for unit in review_units):
        stage, next_action = "review_ready", {"code": "delivery.reconcile", "label": "核对交付结果", "href": f"/review?project={project_id}"}
    return {"stage": stage, "activeUnitCount": len(active), "archivedUnitCount": len(units) - len(active), "modalityCounts": modality_counts, "personas": personas, "brief": {"ready": brief is not None, "revision": brief.revision_no if brief else None}, "factBoundary": {"ready": boundary is not None, "revision": boundary.revision_no if boundary else None, "factPackId": boundary.fact_pack_id if boundary else None, "factPackVersion": boundary.fact_pack_version if boundary else None, "checksum": boundary.fact_pack_checksum if boundary else None}, "risks": risks, "pendingDecisions": pending, "nextAction": next_action, "review": {"units": review_units}}
