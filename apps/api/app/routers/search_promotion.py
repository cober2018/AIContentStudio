"""搜索推广工作台：人确认资料、审成稿；问题库、开项目和中间生产由 AI 通过 MCP 完成，页面也可手动修改。"""
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_editor, require_editor_or_reviewer
from ..models import User
from ..services import search_promotion as service
from ..services import search_runner as runner

router = APIRouter(prefix="/api/v1/search-promotion", tags=["search-promotion"])


class CategoryIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    top_key: Literal["physical", "digital", "service", "org"]
    name: str


class CategoryPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = None
    status: Literal["active", "disabled"] | None = None


class SubjectUpdate(service.SubjectIn):
    expected_revision: int = Field(ge=0)


class ConfirmIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision_no: int = Field(ge=1)


class StatusIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["active", "archived"]


class ProjectsIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[service.ProjectItem] = Field(min_length=1, max_length=service.BATCH_LIMIT)
    force: bool = False


class DraftIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=200)
    links: list[str] = Field(default_factory=list, max_length=10)
    note: str = Field(default="", max_length=2000)
    subject_id: int | None = Field(default=None, ge=1)


class StartIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    count: int = Field(default=3, ge=1, le=service.BATCH_LIMIT)
    forms: list[str] = Field(default_factory=lambda: ["text"], min_length=1, max_length=3)
    tone: str = Field(default="专业中立科普", max_length=100)
    reader_level: str = Field(default="小白", max_length=50)
    platforms: list[str] = Field(default_factory=lambda: list(service.DEFAULT_PLATFORMS), min_length=1, max_length=7)


class DecisionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    candidate_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    comment: str = Field(default="", max_length=2000)


@router.get("/categories")
def categories(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.list_categories(db, user)


@router.post("/categories", status_code=201)
def create_category(payload: CategoryIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return service.create_category(db, user, payload.top_key, payload.name)


@router.patch("/categories/{category_id}")
def update_category(category_id: int, payload: CategoryPatch, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return service.update_category(db, user, category_id, payload.name, payload.status)


@router.get("/subjects")
def subjects(include_archived: bool = False, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.list_subjects(db, user, include_archived)


@router.post("/subjects", status_code=201)
def create_subject(payload: service.SubjectIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return service.save_subject(db, user, None, payload, origin="human")


@router.get("/subjects/{subject_id}")
def get_subject(subject_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.get_subject(db, user, subject_id)


@router.put("/subjects/{subject_id}")
def update_subject(subject_id: int, payload: SubjectUpdate, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    data = service.SubjectIn.model_validate(payload.model_dump(exclude={"expected_revision"}))
    return service.save_subject(db, user, subject_id, data, origin="human", expected_revision=payload.expected_revision)


@router.post("/subjects/{subject_id}/confirm")
def confirm_subject(subject_id: int, payload: ConfirmIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return service.confirm_subject(db, user, subject_id, payload.revision_no)


@router.post("/subjects/{subject_id}/status")
def subject_status(subject_id: int, payload: StatusIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return service.set_subject_status(db, user, subject_id, payload.status)


@router.put("/subjects/{subject_id}/library")
def save_library(subject_id: int, payload: service.LibraryIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return service.save_library(db, user, subject_id, payload, origin="human")


@router.post("/subjects/{subject_id}/projects", status_code=201)
def open_projects(subject_id: int, payload: ProjectsIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return service.open_projects(db, user, subject_id, payload.items, force=payload.force)


@router.get("/projects/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.get_project(db, user, project_id)


@router.get("/works/{unit_id}")
def work_info(unit_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.work_info(db, user, unit_id)


@router.get("/review")
def review_queue(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.review_queue(db, user)


@router.get("/delivered")
def delivered(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.delivered(db, user)


@router.post("/candidates/{candidate_id}/approve")
def approve(candidate_id: int, payload: DecisionIn, db: Session = Depends(get_db), user: User = Depends(require_editor_or_reviewer)):
    return service.approve_version(db, user, candidate_id, payload.candidate_hash)


@router.post("/candidates/{candidate_id}/request-changes")
def request_changes(candidate_id: int, payload: DecisionIn, db: Session = Depends(get_db), user: User = Depends(require_editor_or_reviewer)):
    return service.request_changes(db, user, candidate_id, payload.candidate_hash, payload.comment)


@router.post("/drafts", status_code=202)
def draft_subject(payload: DraftIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return runner.draft_subject(db, user, payload.name, payload.links, payload.note, payload.subject_id)


@router.post("/subjects/{subject_id}/start", status_code=202)
def start(subject_id: int, payload: StartIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return runner.start(db, user, subject_id, payload.model_dump())


@router.get("/runs")
def runs(subject_id: int | None = None, project_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return runner.list_runs(db, user, subject_id=subject_id, project_id=project_id)


@router.post("/runs/{run_id}/retry", status_code=202)
def retry(run_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return runner.retry(db, user, run_id)


@router.post("/projects/{project_id}/continue", status_code=202)
def continue_project(project_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return runner.continue_project(db, user, project_id)
