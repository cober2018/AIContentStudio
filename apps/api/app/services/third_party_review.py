"""第三方写作的事实 / 身份复核：平台不调用模型，把请求挂起，由第三方模型经 MCP 领取并交回结果。

写作方式是第三方模型时，复核结果必须来自第三方模型，不能退回到平台配置的模型；
结果按稿子内容的 input_hash 对应，改过的稿子不会沿用旧结论。
"""

import hashlib
import json

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ContentMasterRevision, ThirdPartyReviewTask, User, utcnow

_SEVERITIES = {"warning", "blocker"}


def is_third_party(db: Session, unit_id: int) -> bool:
    from . import article_chain

    return article_chain._record(db, unit_id).get("writer") == "external"


def request_hash(purpose: str, text: str, context: dict) -> str:
    payload = json.dumps({"purpose": purpose, "text": text, "context": context}, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def resolve(db: Session, master: ContentMasterRevision, purpose: str, text: str, context: dict) -> tuple[list[dict], dict]:
    digest = request_hash(purpose, text, context)
    row = _task(db, master.id, purpose, digest)
    if row is None:
        row = ThirdPartyReviewTask(master_revision_id=master.id, purpose=purpose, input_hash=digest, status="pending",
                                   request_json={"text": text, "context": context})
        db.add(row)
        db.flush()
    if row.status == "submitted":
        return [dict(issue) for issue in row.issues_json or []], {"semantic": "verified", "reason": None, "provider": "third_party",
                                                                 "model": row.model_label, "review_task_id": row.id}
    return [], {"semantic": "unavailable", "reason": "third_party_review_pending", "review_task_id": row.id}


def pending_tasks(db: Session, user: User, project_id: int, unit_id: int) -> dict:
    from .content_masters import owned_unit

    owned_unit(db, project_id, unit_id, user)
    latest = db.scalar(select(ContentMasterRevision.id).where(ContentMasterRevision.content_unit_id == unit_id)
                       .order_by(ContentMasterRevision.id.desc()).limit(1))
    rows = db.scalars(select(ThirdPartyReviewTask).where(ThirdPartyReviewTask.master_revision_id == latest,
                                                         ThirdPartyReviewTask.status == "pending").order_by(ThirdPartyReviewTask.id)).all() if latest else []
    from .warning_judgment import pending as pending_judgments

    return {"writer_is_third_party": is_third_party(db, unit_id),
            "items": [{"master_id": row.master_revision_id, "purpose": row.purpose, "input_hash": row.input_hash, "request": row.request_json}
                      for row in rows],
            "warning_judgments": pending_judgments(db, latest) if latest else []}


def submit(db: Session, user: User, project_id: int, unit_id: int, master_id: int, purpose: str, input_hash: str, model: str, issues: list[dict]) -> dict:
    from .content_masters import run_checks

    master = db.get(ContentMasterRevision, master_id)
    if master is None or master.project_id != project_id or master.content_unit_id != unit_id:
        raise HTTPException(404, "Master版本不存在")
    if not is_third_party(db, unit_id):
        raise HTTPException(409, {"code": "review_writer_platform", "message": "写作方式是平台模型，不接受第三方复核"})
    row = _task(db, master_id, purpose, input_hash)
    if row is None or row.status != "pending":
        raise HTTPException(409, {"code": "review_task_not_pending", "message": "这项复核不在等待中，请重新领取"})
    checked = _validated_issues(issues)
    row.issues_json = checked
    row.model_label = model.strip()[:120]
    row.status = "submitted"
    row.submitted_at = utcnow()
    review_task_id = row.id
    db.commit()
    return {"review_task_id": review_task_id, "checks": run_checks(db, project_id, unit_id, master_id, user)}


def _task(db: Session, master_id: int, purpose: str, digest: str) -> ThirdPartyReviewTask | None:
    return db.scalar(select(ThirdPartyReviewTask).where(ThirdPartyReviewTask.master_revision_id == master_id,
                                                        ThirdPartyReviewTask.purpose == purpose,
                                                        ThirdPartyReviewTask.input_hash == digest))


def _validated_issues(issues: list[dict]) -> list[dict]:
    if not isinstance(issues, list) or len(issues) > 50:
        raise HTTPException(422, {"code": "review_issues_invalid", "message": "issues 必须是最多 50 条的列表"})
    checked = []
    for item in issues:
        if not isinstance(item, dict) or item.get("severity") not in _SEVERITIES or not isinstance(item.get("reason"), str) or not item["reason"].strip():
            raise HTTPException(422, {"code": "review_issues_invalid", "message": "每条问题需要 severity（warning 或 blocker）和 reason"})
        checked.append({"severity": item["severity"], "span": str(item.get("span") or "")[:120], "reason": item["reason"][:500], "source": "semantic"})
    return checked
