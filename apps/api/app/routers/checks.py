"""统一检查 API（§6.18）：DraftCheckRun 的读取与手动触发。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_editor_or_reviewer
from ..models import CheckKind, Draft, User
from ..services import checks as checks_service
from ..services.project_authorization import authorize_project_draft

router = APIRouter(prefix="/api/v1/drafts", tags=["checks"])

_RUNNABLE_KINDS = {
    "platform": "rule",
    "media": "rule",
    "rights": "rule",
    "seo": "seo",
    "domain": "domain",
    "safety": "rule",
}


@router.get("/{draft_id}/checks")
def list_checks(draft_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    draft = db.get(Draft, draft_id)
    if not draft:
        raise HTTPException(404, "Draft 不存在")
    authorize_project_draft(db, draft, user)
    return [
        {
            "id": row.id,
            "check_kind": row.check_kind,
            "profile_key": row.profile_key,
            "profile_version": row.profile_version,
            "input_hash": row.input_hash,
            "status": row.status,
            "report": row.report_json,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in checks_service.current_checks(db, draft)
    ]


@router.post("/{draft_id}/checks/{kind}")
def run_check(kind: str, draft_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor_or_reviewer)):
    draft = db.get(Draft, draft_id)
    if not draft:
        raise HTTPException(404, "Draft 不存在")
    authorize_project_draft(db, draft, user, mutate=True)
    if kind not in _RUNNABLE_KINDS:
        raise HTTPException(422, f"kind 只支持 {sorted(_RUNNABLE_KINDS)}（fact 走 POST /drafts/{draft_id}/fact-check）")
    if kind not in {k.value for k in CheckKind}:
        raise HTTPException(422, f"未知检查类型: {kind}")

    if _RUNNABLE_KINDS[kind] == "seo":
        runs = [checks_service.run_seo_check(db, draft)]
    elif _RUNNABLE_KINDS[kind] == "domain":
        runs = checks_service.run_domain_checks(db, draft)
        if not runs:
            raise HTTPException(422, "该内容形态没有配置领域规则")
    else:
        rules_for_kind = {
            "platform": ["rule.platform.required_fields"],
            "media": ["rule.media.required", "rule.media.order"],
            "rights": ["rule.media.public_rights"],
            "safety": ["rule.platform.required_fields"],
        }
        runs = checks_service.run_rule_set(db, draft, rule_keys=rules_for_kind[kind])
    db.commit()
    return [
        {"id": r.id, "check_kind": r.check_kind, "status": r.status, "report": r.report_json, "input_hash": r.input_hash}
        for r in runs
    ]
