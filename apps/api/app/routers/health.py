"""健康探针与指标端点（EPIC-17）。"""

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from ..db import get_db
from ..observability import check_health, render_metrics

router = APIRouter(tags=["ops"])


@router.get("/api/v1/health")
def health(db: Session = Depends(get_db)):
    result = check_health(db)
    return result


@router.get("/metrics")
def metrics():
    """Prometheus 文本格式（0.0.4）。"""
    return Response(content=render_metrics(), media_type="text/plain; version=0.0.4; charset=utf-8")
