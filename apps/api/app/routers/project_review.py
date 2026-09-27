"""Project-first Candidate and Review APIs."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_editor, require_editor_or_reviewer
from ..models import ContentAsset, ContentProject, User
from ..services import project_review as review_service
from ..services import project_review_projection as projection
from ..services import delivery as delivery_service
from ..services.project_authorization import authorize_project_asset
from .content_projects import owned_project, owned_unit
from .delivery import GenericTargetIn, _target_json

router = APIRouter(prefix="/api/v1", tags=["project-review"])


@router.get("/review-center/projects")
def review_projects(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    projects = db.scalars(select(ContentProject).where(ContentProject.owner_user_id == user.id).order_by(ContentProject.id.desc())).all()
    return [projection.project_projection(db, project) for project in projects]


@router.get("/review-center/projects/{project_id}")
def review_project(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return projection.project_projection(db, owned_project(db, project_id, user))


@router.get("/review-center/projects/{project_id}/units/{unit_id}")
def review_unit(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return projection.unit_projection(db, owned_unit(db, project_id, unit_id, user))


@router.get("/review-center/projects/{project_id}/units/{unit_id}/candidates")
def review_candidates(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    owned_unit(db, project_id, unit_id, user)
    return [_candidate_json(asset) for asset in projection.candidate_rows(db, unit_id)]


@router.get("/review-center/projects/{project_id}/units/{unit_id}/candidates/{candidate_id}")
def review_candidate(project_id: int, unit_id: int, candidate_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    asset = review_service._candidate(db, project_id, unit_id, candidate_id, user, mutate=False)
    return _candidate_json(asset, include_manifest=True)


@router.get("/review-center/projects/{project_id}/units/{unit_id}/candidates/{candidate_id}/diff")
def review_candidate_diff(project_id: int, unit_id: int, candidate_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    current = review_service._candidate(db, project_id, unit_id, candidate_id, user, mutate=False)
    previous = db.scalar(select(ContentAsset).where(ContentAsset.content_unit_id == unit_id, ContentAsset.id < candidate_id).order_by(ContentAsset.id.desc()).limit(1))
    return projection.candidate_diff(previous, current)


class FreezeIn(BaseModel):
    project_output_id: int


class CandidateDecisionIn(BaseModel):
    candidate_hash: str = Field(min_length=64, max_length=64)
    comment: str | None = None


def _candidate_json(asset: ContentAsset, *, include_manifest: bool = False) -> dict:
    data = {
        "id": asset.id, "project_id": asset.project_id, "unit_id": asset.content_unit_id,
        "identity_snapshot_id": asset.identity_snapshot_id, "workflow_run_id": asset.workflow_run_id,
        "draft_id": asset.draft_id, "title": asset.title, "channel": asset.channel,
        "content_form": asset.content_form, "status": asset.status,
        "candidate_hash": asset.candidate_hash, "approved_candidate_hash": asset.approved_candidate_hash,
        "created_at": asset.created_at.isoformat() if asset.created_at else None,
    }
    if include_manifest:
        data["manifest"] = asset.candidate_manifest_json
    return data


@router.post("/content-projects/{project_id}/units/{unit_id}/candidates/freeze", status_code=201)
def freeze(project_id: int, unit_id: int, payload: FreezeIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return _candidate_json(review_service.freeze_candidate(db, project_id, unit_id, payload.project_output_id, user), include_manifest=True)


@router.get("/content-projects/{project_id}/units/{unit_id}/candidates")
def list_candidates(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    owned_unit(db, project_id, unit_id, user)
    rows = db.scalars(select(ContentAsset).where(ContentAsset.project_id == project_id, ContentAsset.content_unit_id == unit_id).order_by(ContentAsset.id.desc())).all()
    return [_candidate_json(asset) for asset in rows]


@router.get("/content-projects/{project_id}/units/{unit_id}/candidates/{candidate_id}")
def get_candidate(project_id: int, unit_id: int, candidate_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    asset = review_service._candidate(db, project_id, unit_id, candidate_id, user, mutate=False)
    authorize_project_asset(db, asset, user)
    return _candidate_json(asset, include_manifest=True)


@router.post("/content-projects/{project_id}/units/{unit_id}/candidates/{candidate_id}/approve")
def approve(project_id: int, unit_id: int, candidate_id: int, payload: CandidateDecisionIn, db: Session = Depends(get_db), user: User = Depends(require_editor_or_reviewer)):
    return _candidate_json(review_service.decide_candidate(db, project_id, unit_id, candidate_id, payload.candidate_hash, "approved", payload.comment, user), include_manifest=True)


@router.post("/content-projects/{project_id}/units/{unit_id}/candidates/{candidate_id}/request-changes")
def request_changes(project_id: int, unit_id: int, candidate_id: int, payload: CandidateDecisionIn, db: Session = Depends(get_db), user: User = Depends(require_editor_or_reviewer)):
    return _candidate_json(review_service.decide_candidate(db, project_id, unit_id, candidate_id, payload.candidate_hash, "changes_requested", payload.comment, user), include_manifest=True)


@router.post("/content-projects/{project_id}/units/{unit_id}/candidates/{candidate_id}/delivery-authorizations", status_code=201)
def authorize_delivery(project_id: int, unit_id: int, candidate_id: int, payload: GenericTargetIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    asset = review_service._candidate(db, project_id, unit_id, candidate_id, user, mutate=True)
    return _target_json(delivery_service.authorize_target(db, asset, payload, user))
