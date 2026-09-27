"""Project Overview, Versions and Activity read APIs."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models import ProjectEvent, User
from ..services.project_overview import project_overview
from ..services.project_versions import project_versions
from .content_projects import owned_project

router = APIRouter(prefix="/api/v1/content-projects", tags=["content-project-read-models"])


@router.get("/{project_id}/overview")
def get_project_overview(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    owned_project(db, project_id, user)
    return project_overview(db, project_id)


@router.get("/{project_id}/versions")
def get_project_versions(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    owned_project(db, project_id, user)
    return project_versions(db, project_id)


@router.get("/{project_id}/activity")
def get_project_activity(project_id: int, before_id: int | None = None, limit: int = Query(default=30, ge=1, le=100), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    owned_project(db, project_id, user)
    stmt = select(ProjectEvent).where(ProjectEvent.project_id == project_id)
    if before_id is not None:
        stmt = stmt.where(ProjectEvent.id < before_id)
    rows = db.scalars(stmt.order_by(ProjectEvent.id.desc()).limit(limit + 1)).all()
    page = rows[:limit]
    return {"items": [{"id": row.id, "event_type": row.event_type, "entity_type": row.entity_type, "entity_id": row.entity_id, "actor": row.actor, "payload": row.payload_json, "schema_version": row.schema_version, "created_at": row.created_at.isoformat() if row.created_at else None} for row in page], "next_before_id": page[-1].id if len(rows) > limit and page else None}
