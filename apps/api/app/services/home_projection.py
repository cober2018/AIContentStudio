"""Bounded Home composition; responsible domains remain the status truth."""

from datetime import UTC, datetime
from urllib.parse import quote

from sqlalchemy import case, func, inspect, select
from sqlalchemy.orm import Session

from ..models import (
    ContentOpportunity,
    ContentOpportunityAssessmentRevision,
    ContentProject,
    ContentUnit,
    CreativeExecution,
    LearningCandidate,
    OpportunityProjectConversion,
    ProjectEvent,
    User,
    Workflow,
    WorkflowRun,
    WorkflowStep,
)
from .content_harness.registry import RegistryError, registry
from .opportunities import opportunity_list_json
from .project_overview import project_overviews

DECISION_ORDER = {
    "unknown": 0,
    "blocked": 1,
    "stale": 2,
    "waiting_human": 3,
    "approval": 4,
    "authorization": 5,
    "identity_unready": 6,
    "learning_validation": 7,
    "recipe_stage": 8,
}
PRIORITY_ORDER = {"high": 0, "normal": 1, "low": 2}
SENSITIVITY_ORDER = {"high": 0, "medium": 1, "low": 2, "timeless": 3}


def recipe_stage_actions(db: Session, project_ids: list[int]) -> list[dict]:
    if not project_ids:
        return []
    latest_run = select(func.max(WorkflowRun.id)).where(
        WorkflowRun.content_unit_id == ContentUnit.id,
        WorkflowRun.workflow_id == ContentUnit.pinned_workflow_id,
    ).correlate(ContentUnit).scalar_subquery()
    rows = db.execute(select(
        ContentUnit, Workflow.definition_json, Workflow.version, Workflow.checksum,
        WorkflowRun.id.label("run_id"), WorkflowRun.status.label("run_status"),
        WorkflowRun.identity_snapshot_id.label("run_identity"),
        WorkflowRun.workflow_version.label("run_version"), WorkflowRun.definition_checksum.label("run_checksum"),
    ).select_from(ContentUnit).join(Workflow, Workflow.id == ContentUnit.pinned_workflow_id).outerjoin(
        WorkflowRun, WorkflowRun.id == latest_run,
    ).where(ContentUnit.project_id.in_(project_ids), ContentUnit.status != "archived")
      .order_by(ContentUnit.id)).all()
    run_ids = [row.run_id for row in rows if row.run_id is not None]
    steps = {}
    if run_ids:
        for row in db.execute(select(
            WorkflowStep.run_id, WorkflowStep.node_id, WorkflowStep.status,
            WorkflowStep.plugin_key, WorkflowStep.plugin_version,
        ).where(WorkflowStep.run_id.in_(run_ids))).all():
            steps.setdefault(row.run_id, {})[row.node_id] = row
    actions = []
    contracts = {}
    for row in rows:
        unit, definition, version, checksum = row[:4]
        if row.run_id is not None and (row.run_status in {"canceled", "cancelled", "archived", "succeeded"}
                or row.run_identity != unit.identity_snapshot_id
                or row.run_version != version or row.run_checksum != checksum):
            continue
        nodes = {node["id"]: node for node in definition.get("nodes", [])}
        dependencies = {}
        for edge in definition.get("edges", []):
            dependencies.setdefault(edge["to"], []).append(edge["from"])
        run_steps = steps.get(row.run_id, {})
        choices = []
        for position, node_id in enumerate(definition.get("visual_order") or list(nodes)):
            node = nodes.get(node_id)
            if not node or node.get("enabled") is False:
                continue
            identity = (node.get("plugin"), str(node.get("plugin_version") or "1"))
            if identity not in contracts:
                try:
                    descriptor = registry.descriptor("node", *identity)
                    contracts[identity] = descriptor.stage_contract.to_dict() if descriptor.stage_contract else None
                except RegistryError:
                    contracts[identity] = None
            contract = contracts[identity]
            if not contract or node.get("stage_schema") != contract["stage_schema"]:
                continue
            step = run_steps.get(node_id)
            if row.run_id is not None and step is None:
                continue
            if step and (step.plugin_key, step.plugin_version) != identity:
                continue
            status = step.status if step else "pending"
            code = {"unknown": "unknown", "blocked": "blocked", "failed": "blocked", "stale": "stale",
                    "waiting_input": "waiting_human", "waiting_human": "waiting_human"}.get(status)
            if code is None:
                if status != "pending" or any(
                    source not in nodes or (nodes[source].get("enabled") is not False
                    and (source not in run_steps or run_steps[source].status not in {"succeeded", "skipped"}))
                    for source in dependencies.get(node_id, [])
                ):
                    continue
                code = "recipe_stage"
            label = node.get("label") or contract["title"] or node_id
            action = {"code": code, "project_id": unit.project_id, "unit_id": unit.id, "run_id": row.run_id,
                      "node_id": node_id, "entity_kind": "recipe_stage",
                      "label": {"unknown": "核对阶段未知结果（禁止自动重试）", "blocked": "处理阶段阻断",
                                "stale": "重新确认过期阶段", "waiting_human": "审阅阶段结果",
                                "recipe_stage": "继续创作阶段"}[code] + f"：{label}",
                      "href": f"/projects/{unit.project_id}/units/{unit.id}/production?stage={quote(node_id, safe='')}"}
            choices.append((DECISION_ORDER[code], position, action))
        if choices:
            actions.append(min(choices, key=lambda item: item[:2])[2])
    return actions


def creative_decisions(db: Session, user: User) -> tuple[list[dict], bool]:
    # An unupgraded local database is unavailable, not a successful empty queue.
    if not inspect(db.get_bind()).has_table(CreativeExecution.__tablename__):
        return [], False
    rows = db.scalars(select(CreativeExecution).join(
        ContentProject, ContentProject.id == CreativeExecution.project_id,
    ).join(ContentUnit, ContentUnit.id == CreativeExecution.content_unit_id).where(
        CreativeExecution.owner_user_id == user.id, ContentProject.owner_user_id == user.id,
        ContentUnit.project_id == ContentProject.id, ContentProject.status != "archived",
        ContentUnit.status != "archived", CreativeExecution.state.in_(["unknown", "blocked", "result_ready"]),
    ).order_by(case({"unknown": 0, "blocked": 1, "result_ready": 2}, value=CreativeExecution.state),
               CreativeExecution.id).limit(100)).all()
    decisions = []
    for row in rows:
        uncertain = row.state == "unknown" or row.dispatch_certainty == "possibly_dispatched"
        code = "unknown" if uncertain else "blocked" if row.state == "blocked" else "waiting_human"
        label = "核对创意执行未知结果（禁止自动重试）" if uncertain else (
            "补交被拒绝的必需成果" if row.safe_reason == "needs_output_replacement" else "解决创意执行阻断"
        ) if code == "blocked" else "人工接受创意执行成果（不会自动改正文）"
        decisions.append({"code": code, "project_id": row.project_id, "unit_id": row.content_unit_id,
                          "run_id": None, "entity_id": row.id, "entity_kind": "creative_execution",
                          "creative_execution_id": row.id, "label": label,
                          "href": f"/projects/{row.project_id}/units/{row.content_unit_id}/production?panel=execution&execution={row.id}"})
    return decisions, True


def project_origin(db: Session, project_id: int) -> dict | None:
    conversion = db.scalar(
        select(OpportunityProjectConversion).where(OpportunityProjectConversion.project_id == project_id)
    )
    if conversion is None:
        return None
    opportunity = db.get(ContentOpportunity, conversion.opportunity_id)
    return {
        "opportunity_id": conversion.opportunity_id,
        "title": (conversion.conversion_snapshot_json or {}).get("title"),
        "status": opportunity.status if opportunity else "unknown",
        "assessment_revision_id": conversion.assessment_revision_id,
        "snapshot": conversion.conversion_snapshot_json,
    }


def compose_decisions(project_id: int, overview: dict) -> list[dict]:
    decisions = {}

    def add(code: str, unit_id: int | None, label: str, href: str, run_id: int | None = None):
        key = (code, project_id, unit_id)
        decisions[key] = {
            "code": code,
            "project_id": project_id,
            "unit_id": unit_id,
            "run_id": run_id,
            "label": label,
            "href": href,
        }

    production = lambda unit_id: f"/projects/{project_id}/units/{unit_id}/production"
    for risk in overview.get("risks", []):
        raw = risk["code"]
        code = (
            "identity_unready"
            if raw == "identity_unready"
            else "unknown"
            if "unknown" in raw
            else "stale"
            if "stale" in raw
            else "blocked"
        )
        unit_id = risk.get("unit_id")
        add(
            code,
            unit_id,
            {
                "identity_unready": "完善内容身份",
                "unknown": "核对未知结果",
                "stale": "刷新过期产物",
                "blocked": "处理生产阻断",
            }[code],
            f"/projects/{project_id}?tab=matrix" if code == "identity_unready" else production(unit_id),
            risk.get("run_id"),
        )
    for pending in overview.get("pendingDecisions", []):
        add(
            "waiting_human",
            pending.get("unit_id"),
            "处理人工节点",
            production(pending.get("unit_id")),
            pending.get("run_id"),
        )
    for unit in overview.get("review", {}).get("units", []):
        status = unit["summary"]
        code = {
            "unknown": "unknown",
            "blocked": "blocked",
            "stale": "stale",
            "waiting_review": "approval",
            "approved": "authorization",
        }.get(status)
        if code:
            add(
                code,
                unit["unit_id"],
                {
                    "unknown": "核对交付结果（禁止自动重发）",
                    "blocked": "解决审核阻断",
                    "stale": "核对过期候选",
                    "approval": "审批冻结候选",
                    "authorization": "授权交付目标",
                }[code],
                f"/review?project={project_id}&unit={unit['unit_id']}",
            )
    return sorted(
        decisions.values(), key=lambda item: (DECISION_ORDER[item["code"]], item["project_id"], item["unit_id"] or 0)
    )


def home_projection(db: Session, user: User, limit: int = 20) -> dict:
    now = datetime.now(UTC)
    sensitivity = (
        select(ContentOpportunityAssessmentRevision.assessment_json["time_sensitivity"].as_string())
        .where(ContentOpportunityAssessmentRevision.opportunity_id == ContentOpportunity.id)
        .order_by(ContentOpportunityAssessmentRevision.revision_no.desc())
        .limit(1)
        .scalar_subquery()
    )
    rows = db.scalars(
        select(ContentOpportunity)
        .where(
            ContentOpportunity.owner_user_id == user.id,
            ContentOpportunity.status.in_(["new", "watching", "qualified"]),
            (ContentOpportunity.relevant_until.is_(None)) | (ContentOpportunity.relevant_until >= now),
        )
        .order_by(
            case(PRIORITY_ORDER, value=ContentOpportunity.priority, else_=1),
            case(SENSITIVITY_ORDER, value=sensitivity, else_=3),
            ContentOpportunity.relevant_until.is_(None),
            ContentOpportunity.relevant_until.asc(),
            ContentOpportunity.updated_at.desc(),
            ContentOpportunity.id.asc(),
        )
        .limit(limit)
    ).all()
    projects = db.scalars(
        select(ContentProject)
        .where(ContentProject.owner_user_id == user.id, ContentProject.status != "archived")
        .order_by(ContentProject.updated_at.desc(), ContentProject.id.desc())
    ).all()
    origins = (
        {
            row.project_id: {"opportunity_id": row.opportunity_id, "assessment_revision_id": row.assessment_revision_id}
            for row in db.scalars(
                select(OpportunityProjectConversion).where(
                    OpportunityProjectConversion.project_id.in_([project.id for project in projects[:limit]])
                )
            )
        }
        if projects
        else {}
    )
    cards = []
    decisions = []
    recipe_stages = []
    for offset in range(0, len(projects), 100):
        batch = projects[offset : offset + 100]
        overviews = project_overviews(db, [project.id for project in batch], summary_only=True)
        batch_stages = recipe_stage_actions(db, [project.id for project in batch])
        recipe_stages.extend(batch_stages)
        for index, project in enumerate(batch, start=offset):
            overview = overviews[project.id]
            if index < limit:
                cards.append(
                    {
                        "id": project.id,
                        "title": project.title,
                        "updated_at": project.updated_at.isoformat(),
                        "overview": {key: value for key, value in overview.items() if key != "review"},
                        "origin": origins.get(project.id),
                    }
                )
            decisions.extend(compose_decisions(project.id, overview))
        decisions.extend(batch_stages)
    candidates = db.scalars(
        select(LearningCandidate)
        .where(LearningCandidate.owner_user_id == user.id, LearningCandidate.status == "ready_for_review")
        .order_by(LearningCandidate.created_at, LearningCandidate.id)
        .limit(100)
    ).all()
    decisions.extend(
        {
            "code": "learning_validation",
            "project_id": None,
            "unit_id": None,
            "run_id": None,
            "entity_id": candidate.id,
            "learning_candidate_id": candidate.id,
            "label": f"验证学习候选：{candidate.title}",
            "href": f"/learning?tab=candidates&candidate={candidate.id}",
        }
        for candidate in candidates
    )
    execution_decisions, execution_available = creative_decisions(db, user)
    decisions.extend(execution_decisions)
    decisions.sort(
        key=lambda item: (
            DECISION_ORDER[item["code"]],
            item["project_id"] or 0,
            item["unit_id"] or 0,
            item.get("entity_id", 0),
        )
    )
    activity = db.scalars(
        select(ProjectEvent)
        .join(ContentProject, ContentProject.id == ProjectEvent.project_id)
        .where(ContentProject.owner_user_id == user.id)
        .order_by(ProjectEvent.created_at.desc(), ProjectEvent.id.desc())
        .limit(limit)
    ).all()
    return {
        "opportunities": opportunity_list_json(db, rows),
        "projects": cards,
        "decisions": decisions[:100],
        "recipe_stages": sorted(recipe_stages, key=lambda item: (
            DECISION_ORDER[item["code"]], item["project_id"], item["unit_id"],
        )),
        "identity_alerts": [item for item in decisions if item["code"] == "identity_unready"][:limit],
        "recent_activity": [
            {
                "id": event.id,
                "project_id": event.project_id,
                "event_type": event.event_type,
                "created_at": event.created_at.isoformat(),
            }
            for event in activity
        ],
        "upcoming": [],
        "capabilities": {"schedule": False, "opportunity_analysis": False, "creative_execution": execution_available},
        "generated_at": now.isoformat(),
        "incomplete": not execution_available,
        "section_errors": [] if execution_available else [{"section": "creative_execution", "code": "schema_unavailable", "message": "创意执行数据结构尚未启用，不能确认待处理成果。"}],
    }
