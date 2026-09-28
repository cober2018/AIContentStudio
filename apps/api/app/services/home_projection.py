"""Bounded Home composition; responsible domains remain the status truth."""

from datetime import UTC, datetime

from sqlalchemy import case, select
from sqlalchemy.orm import Session

from ..models import (
    ContentOpportunity,
    ContentOpportunityAssessmentRevision,
    ContentProject,
    LearningCandidate,
    OpportunityProjectConversion,
    ProjectEvent,
    User,
)
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
}
PRIORITY_ORDER = {"high": 0, "normal": 1, "low": 2}
SENSITIVITY_ORDER = {"high": 0, "medium": 1, "low": 2, "timeless": 3}


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
    for offset in range(0, len(projects), 100):
        batch = projects[offset : offset + 100]
        overviews = project_overviews(db, [project.id for project in batch], summary_only=True)
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
        "capabilities": {"schedule": False, "opportunity_analysis": False},
        "generated_at": now.isoformat(),
        "incomplete": False,
        "section_errors": [],
    }
