"""健康探针与指标端点（EPIC-17）。"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_db
from ..deps import get_current_user, require_role
from ..models import AuditLog, User
from ..observability import check_health, render_metrics, safe_telemetry

router = APIRouter(tags=["ops"])


@router.get("/api/v1/health")
def health(db: Session = Depends(get_db)):
    """Backward-compatible readiness alias."""
    result = check_health(db)
    return JSONResponse(result, status_code=200 if result["ready"] else 503)


@router.get("/api/v1/health/ready")
def readiness(db: Session = Depends(get_db)):
    result = check_health(db)
    return JSONResponse(result, status_code=200 if result["ready"] else 503)


@router.get("/api/v1/health/live")
def liveness():
    return {"status": "alive"}


@router.get("/metrics")
def metrics(user: User = Depends(get_current_user)):
    """Prometheus 文本格式（0.0.4）。"""
    if get_settings().app_env == "production" and user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "需要管理员角色")
    return Response(content=render_metrics(), media_type="text/plain; version=0.0.4; charset=utf-8")


@router.get("/api/v1/ops/audit")
def audit_query(
    event: str | None = Query(default=None, max_length=100),
    entity_type: str | None = Query(default=None, max_length=50),
    entity_id: str | None = Query(default=None, max_length=50),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """Bounded admin debug view; never returns raw audit detail payloads."""
    stmt = select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)
    if event:
        stmt = stmt.where(AuditLog.event == event)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    rows = db.scalars(stmt).all()
    return {
        "items": [
            {
                "id": row.id,
                "event": row.event,
                "actor": row.actor,
                "entity_type": row.entity_type,
                "entity_id": row.entity_id,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "telemetry": safe_telemetry((row.detail_json or {}).get("_telemetry")) if isinstance(row.detail_json, dict) else {},
            }
            for row in rows
        ],
        "limit": limit,
        "filters": {"event": event, "entity_type": entity_type, "entity_id": entity_id},
    }
