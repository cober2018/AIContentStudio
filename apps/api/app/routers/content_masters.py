"""Project-scoped Content Master revision API."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_editor
from ..models import User
from ..services.content_masters import (
    current_checks,
    get_revision,
    list_checks,
    list_revisions,
    run_checks,
    save_revision,
)

router = APIRouter(prefix="/api/v1", tags=["content-masters"])


class MasterRevisionIn(BaseModel):
    expected_revision: int = Field(default=0, ge=0)
    idempotency_key: str = Field(min_length=1, max_length=150)
    modality: str | None = None
    payload_schema: str | None = None
    payload: dict
    content_form: str | None = Field(default=None, max_length=100)
    parent_revision_id: int | None = None
    source_kind: str = Field(default="user_edit", max_length=30)
    edit_summary: dict = Field(default_factory=dict)
    asset_refs: list[dict] = Field(default_factory=list, max_length=250)
    evidence_refs: list[dict] = Field(default_factory=list, max_length=250)


class MasterSeedIn(BaseModel):
    expected_revision: int = Field(default=0, ge=0)
    idempotency_key: str = Field(min_length=1, max_length=150)
    project_output_id: int


@router.get("/content-projects/{project_id}/units/{unit_id}/master-revisions")
def get_master_revisions(project_id: int, unit_id: int, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {"items": list_revisions(db, project_id, unit_id, user, limit=limit, offset=offset), "limit": limit, "offset": offset}


@router.get("/content-projects/{project_id}/units/{unit_id}/master-revisions/current")
def get_current_master(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    items = list_revisions(db, project_id, unit_id, user, limit=1)
    return items[0] if items else None


@router.get("/content-projects/{project_id}/units/{unit_id}/master-revisions/{master_id}")
def get_master_revision(project_id: int, unit_id: int, master_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_revision(db, project_id, unit_id, master_id, user)


@router.post("/content-projects/{project_id}/units/{unit_id}/master-revisions", dependencies=[Depends(require_editor)])
def create_master_revision(project_id: int, unit_id: int, body: MasterRevisionIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return save_revision(db, project_id=project_id, unit_id=unit_id, user=user, payload=body.model_dump())


@router.get("/content-projects/{project_id}/units/{unit_id}/master-revisions/{master_id}/checks")
def get_master_checks(project_id: int, unit_id: int, master_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {"items": list_checks(db, project_id, unit_id, master_id, user)}


@router.post("/content-projects/{project_id}/units/{unit_id}/master-revisions/{master_id}/checks", dependencies=[Depends(require_editor)])
def execute_master_checks(project_id: int, unit_id: int, master_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {"items": run_checks(db, project_id, unit_id, master_id, user)}


@router.get("/content-projects/{project_id}/units/{unit_id}/master-revisions/{master_id}/checks/current")
def get_current_master_checks(project_id: int, unit_id: int, master_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {"items": current_checks(db, project_id, unit_id, master_id, user)}


@router.post("/content-projects/{project_id}/units/{unit_id}/master-revisions/from-output")
def seed_master_from_output(project_id: int, unit_id: int, body: MasterSeedIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    from ..services.content_masters import seed_from_output

    return seed_from_output(db, project_id=project_id, unit_id=unit_id, user=user, output_id=body.project_output_id, idempotency_key=body.idempotency_key, expected_revision=body.expected_revision)
