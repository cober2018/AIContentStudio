"""Review API（STU-110~112）：队列、退回、批准（含 FactCheck Gate）。"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_editor_or_reviewer
from ..models import (
    AuditLog,
    ContentAsset,
    Draft,
    DraftStatus,
    Review,
    User,
)

router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])


class DecisionIn(BaseModel):
    comment: str | None = None


def _serialize_queue_item(draft: Draft) -> dict:
    job = draft.content_job
    fc = draft.fact_check_json or {}
    return {
        "draft_id": draft.id,
        "revision_no": draft.revision_no,
        "title": draft.title,
        "topic_id": job.topic_brief_id,
        "topic_title": job.topic_brief.title,
        "channel": job.channel,
        "status": draft.status,
        "submitter": draft.created_by,
        "fact_check_result": fc.get("result"),
        "fact_check_stats": fc.get("stats"),
        "fact_check_issues": fc.get("issues"),
        "last_modified": draft.created_at.isoformat() if draft.created_at else None,
        "reviewer": draft.reviews[-1].reviewer_id if draft.reviews else None,
    }


def _get_latest_draft_for_job(db: Session, job_id: int) -> Draft | None:
    return db.scalars(
        select(Draft).where(Draft.content_job_id == job_id).order_by(Draft.revision_no.desc()).limit(1)
    ).first()


@router.get("/queue")
def review_queue(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    drafts = db.scalars(
        select(Draft)
        .where(Draft.status.in_([DraftStatus.ready_for_review.value, DraftStatus.changes_requested.value]))
        .order_by(Draft.created_at.desc())
    )
    return [_serialize_queue_item(d) for d in drafts]


@router.get("/history")
def review_history(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    drafts = db.scalars(
        select(Draft)
        .where(Draft.status.in_([DraftStatus.approved.value, DraftStatus.exported.value]))
        .order_by(Draft.created_at.desc())
    )
    return [_serialize_queue_item(d) for d in drafts]


@router.post("/drafts/{draft_id}/request-changes")
def request_changes(
    draft_id: int,
    payload: DecisionIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_editor_or_reviewer),
):
    draft = db.get(Draft, draft_id)
    if not draft:
        raise HTTPException(404, "Draft 不存在")
    if draft.status not in {DraftStatus.ready_for_review.value, DraftStatus.changes_requested.value}:
        raise HTTPException(409, f"当前状态 {draft.status} 不可退回")

    db.add(Review(draft_id=draft.id, revision_no=draft.revision_no, reviewer_id=user.email,
                  decision="changes_requested", comment=payload.comment))
    draft.status = DraftStatus.changes_requested.value
    db.add(AuditLog(event="review.changes_requested", actor=user.email, entity_type="draft", entity_id=str(draft.id),
                    detail_json={"comment": payload.comment}))
    db.commit()
    return _serialize_queue_item(draft)


@router.post("/drafts/{draft_id}/approve", status_code=201)
def approve(
    draft_id: int,
    payload: DecisionIn | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_editor_or_reviewer),
):
    """批准 Gate（STU-094/112）：blocker=0、FactPack frozen、revision 未被并发编辑。"""
    draft = db.get(Draft, draft_id)
    if not draft:
        raise HTTPException(404, "Draft 不存在")
    if draft.status not in {DraftStatus.ready_for_review.value, DraftStatus.changes_requested.value}:
        raise HTTPException(409, f"当前状态 {draft.status} 不可批准")

    fc = draft.fact_check_json
    if not fc:
        raise HTTPException(409, "尚未执行 FactCheck，不能批准")
    if fc.get("result") == "blocker":
        raise HTTPException(409, f"存在 {fc.get('stats', {}).get('blockers', '?')} 个 blocker，未解决不能批准")

    job = draft.content_job
    topic = job.topic_brief
    pack = topic.fact_pack
    if pack.status != "frozen":
        raise HTTPException(409, "FactPack 非 frozen 状态，不能批准")

    latest = db.scalars(
        select(Draft.revision_no).where(Draft.content_job_id == job.id).order_by(Draft.revision_no.desc()).limit(1)
    ).first()
    if latest != draft.revision_no:
        raise HTTPException(409, "审核期间稿件已被编辑（有更新的 revision），请重新查看最新版本")

    existing_review = db.scalars(
        select(Review).where(Review.draft_id == draft.id).order_by(Review.id.desc()).limit(1)
    ).first()
    if existing_review and existing_review.revision_no != draft.revision_no:
        raise HTTPException(409, "稿件在审核开启后被修改，需基于最新 revision 重新提交")

    db.add(Review(draft_id=draft.id, revision_no=draft.revision_no, reviewer_id=user.email,
                  decision="approved", comment=payload.comment if payload else None))
    draft.status = DraftStatus.approved.value

    asset = ContentAsset(
        draft_id=draft.id,
        topic_brief_id=topic.id,
        channel=job.channel,
        title=draft.title,
        final_body=draft.body,
        structured_json=draft.structured_json,
        fact_pack_id=pack.id,
        fact_pack_version=pack.version,
        fact_pack_checksum=pack.checksum,
        brand_voice_version_id=topic.brand_voice_version_id,
        template_version_id=job.template_version_id,
        model_provider=job.model_provider,
        model_name=job.model_name,
        prompt_version=job.prompt_version,
        reviewer=user.email,
        approved_revision=draft.revision_no,
    )
    db.add(asset)
    db.add(AuditLog(event="review.approved", actor=user.email, entity_type="draft", entity_id=str(draft.id),
                    detail_json={"asset_id": None, "revision": draft.revision_no}))
    db.commit()
    db.refresh(asset)
    return {"draft_id": draft.id, "asset_id": asset.id, "status": draft.status}
