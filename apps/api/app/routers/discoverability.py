"""Discoverability API（§6.20）：Pre/Post SEO 报告与建议应用。"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_editor
from ..models import DiscoverabilityReport, Draft, TopicBrief, User
from ..services import discoverability as disco

router = APIRouter(prefix="/api/v1", tags=["discoverability"])


class ApplyIn(BaseModel):
    title: str | None = None
    title_index: int | None = None


@router.post("/topics/{topic_id}/discoverability/pre")
def run_pre(topic_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    topic = db.get(TopicBrief, topic_id)
    if not topic:
        raise HTTPException(404, "Topic 不存在")
    try:
        row = disco.run_pre_topic(db, topic, user)
    except Exception as exc:
        raise HTTPException(502, f"Discoverability Pre 执行失败: {str(exc)[:200]}") from exc
    db.commit()
    return disco.serialize(row)


@router.get("/topics/{topic_id}/discoverability")
def list_topic_reports(topic_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return [disco.serialize(r) for r in disco.reports_for(db, topic_id=topic_id)]


@router.post("/drafts/{draft_id}/discoverability/post")
def run_post(draft_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    draft = db.get(Draft, draft_id)
    if not draft:
        raise HTTPException(404, "Draft 不存在")
    try:
        row = disco.run_post_draft(db, draft, user)
    except Exception as exc:
        raise HTTPException(502, f"Discoverability Post 执行失败: {str(exc)[:200]}") from exc
    db.commit()
    return disco.serialize(row)


@router.get("/drafts/{draft_id}/discoverability")
def list_draft_reports(draft_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return [disco.serialize(r) for r in disco.reports_for(db, draft_id=draft_id)]


@router.post("/drafts/{draft_id}/discoverability/{report_id}/apply")
def apply_suggestion(draft_id: int, report_id: int, payload: ApplyIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    draft = db.get(Draft, draft_id)
    report = db.get(DiscoverabilityReport, report_id)
    if not draft or not report or report.draft_id not in {None, draft_id}:
        raise HTTPException(404, "Draft 或报告不存在")
    try:
        result = disco.apply_suggestion(db, draft, report, payload.model_dump(), user)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    db.commit()
    return result
