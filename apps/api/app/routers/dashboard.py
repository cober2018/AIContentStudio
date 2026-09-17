"""总览 Dashboard API（P01）。"""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models import (
    ContentAsset,
    ContentJob,
    Draft,
    DraftStatus,
    ExportRecord,
    Fact,
    FactPack,
    FactStatus,
    TopicBrief,
    User,
)

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("")
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    week_ago = datetime.now(UTC) - timedelta(days=7)

    week_drafts = db.scalar(
        select(func.count(Draft.id)).where(Draft.created_at >= week_ago)
    ) or 0
    pending_review = db.scalar(
        select(func.count(Draft.id)).where(
            Draft.status.in_([DraftStatus.ready_for_review.value, DraftStatus.changes_requested.value])
        )
    ) or 0
    fact_conflicts = db.scalar(
        select(func.count(Fact.id)).where(Fact.status == FactStatus.conflict.value)
    ) or 0
    exported_count = db.scalar(select(func.count(ExportRecord.id))) or 0

    recent_jobs = db.scalars(
        select(ContentJob).order_by(ContentJob.created_at.desc()).limit(10)
    ).all()
    today_flow = [
        {
            "job_id": job.id,
            "topic_id": job.topic_brief_id,
            "topic_title": job.topic_brief.title,
            "channel": job.channel,
            "status": job.status,
            "draft_id": job.drafts[-1].id if job.drafts else None,
            "draft_status": job.drafts[-1].status if job.drafts else None,
            "updated_at": (job.finished_at or job.created_at).isoformat() if (job.finished_at or job.created_at) else None,
        }
        for job in recent_jobs
    ]

    recent_packs = [
        {
            "id": p.id,
            "name": p.name,
            "version": p.version,
            "status": p.status,
            "fact_count": len(p.items),
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in db.scalars(select(FactPack).order_by(FactPack.created_at.desc()).limit(5))
    ]
    recent_exports = [
        {"id": e.id, "asset_id": e.asset_id, "fmt": e.fmt, "created_at": e.created_at.isoformat() if e.created_at else None}
        for e in db.scalars(select(ExportRecord).order_by(ExportRecord.created_at.desc()).limit(5))
    ]
    failed_jobs = [
        {"id": j.id, "topic": j.topic_brief.title, "channel": j.channel, "error": j.error}
        for j in db.scalars(select(ContentJob).where(ContentJob.status == "failed").limit(5))
    ]
    topics_count = db.scalar(select(func.count(TopicBrief.id))) or 0
    assets_count = db.scalar(select(func.count(ContentAsset.id))) or 0

    return {
        "stats": {
            "week_drafts": week_drafts,
            "pending_review": pending_review,
            "fact_conflicts": fact_conflicts,
            "exported_count": exported_count,
            "topics": topics_count,
            "assets": assets_count,
        },
        "today_flow": today_flow,
        "recent_fact_packs": recent_packs,
        "recent_exports": recent_exports,
        "failed_jobs": failed_jobs,
    }
