"""按文案 / 分镜找素材：运行只存链接与评分，采用时才下载并入库。"""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_editor
from ..models import User
from ..services import material_matching, open_media, shot_slots

router = APIRouter(prefix="/api/v1", tags=["material-match"])


class ShotIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=100)
    label: str | None = Field(default=None, max_length=120)
    text: str = Field(min_length=1, max_length=4000)


class RunIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scope: Literal["script", "shots"]
    text: str | None = Field(default=None, min_length=1, max_length=20000)
    shots: list[ShotIn] | None = Field(default=None, min_length=1, max_length=material_matching.MAX_SEGMENTS)
    title: str | None = Field(default=None, max_length=300)
    project_id: int | None = Field(default=None, gt=0)
    unit_id: int | None = Field(default=None, gt=0)
    aspect: Literal["9:16", "16:9", "3:4", "1:1", "4:3"] = "9:16"
    min_short_side: Literal[540, 720, 1080] = 720
    strict_aspect: bool = False
    providers: list[str] | None = Field(default=None, max_length=10)

    @model_validator(mode="after")
    def source_matches_scope(self):
        if (self.scope == "script") != (self.text is not None) or (self.scope == "shots") != (self.shots is not None):
            raise ValueError("script needs text and shots needs shots")
        if self.scope == "shots" and len({shot.id for shot in self.shots}) != len(self.shots):
            raise ValueError("shot ids must be unique")
        return self


class AcceptIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    segment_id: str = Field(min_length=1, max_length=100)
    candidate_id: str = Field(min_length=1, max_length=300)
    title: str | None = Field(default=None, max_length=200)
    project_id: int | None = Field(default=None, gt=0)
    note: str | None = Field(default=None, max_length=500)
    public_use_allowed: bool = False
    model_use_allowed: bool = True
    commercial_use_allowed: bool = False


class AttachIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    material_revision_id: int = Field(gt=0)


class RejectIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    note: str = Field(default="", max_length=500)


@router.get("/material-match/providers")
def match_providers(user: User = Depends(get_current_user)):
    return {"items": open_media.status()}


@router.post("/material-match-runs", status_code=202)
def start_run(payload: RunIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return material_matching.start(db, user, payload.model_dump())


@router.get("/material-match-runs")
def list_runs(project_id: Annotated[int | None, Query(gt=0)] = None, unit_id: Annotated[int | None, Query(gt=0)] = None,
              scope: Literal["script", "shots"] | None = None, limit: Annotated[int, Query(ge=1, le=100)] = 30,
              db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return material_matching.listing(db, user, project_id=project_id, unit_id=unit_id, scope=scope, limit=limit)


@router.get("/material-match-runs/{run_id}")
def read_run(run_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return material_matching.read(db, user, run_id)


@router.post("/material-match-runs/{run_id}/cancel")
def cancel_run(run_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return material_matching.cancel(db, user, run_id)


@router.post("/material-match-runs/{run_id}/resume")
def resume_run(run_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return material_matching.resume(db, user, run_id)


@router.post("/material-match-runs/{run_id}/accept", status_code=201)
def accept_candidate(run_id: int, payload: AcceptIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return material_matching.accept(db, user, run_id, payload.model_dump())


@router.post("/material-match-runs/{run_id}/segments/{segment_id}/reject")
def reject_segment(run_id: int, segment_id: str, payload: RejectIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return material_matching.reject(db, user, run_id, segment_id, payload.note)


@router.post("/material-match-runs/{run_id}/segments/{segment_id}/attach")
def attach_upload(run_id: int, segment_id: str, payload: AttachIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return material_matching.attach(db, user, run_id, segment_id, payload.material_revision_id)


class BriefIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query_zh: str | None = Field(default=None, max_length=60)
    queries_en: list[Annotated[str, Field(max_length=100)]] | None = Field(default=None, max_length=2)
    t2v_prompt: str | None = Field(default=None, max_length=1500)
    frame_prompt: str | None = Field(default=None, max_length=1000)
    prompt: str | None = Field(default=None, max_length=1000)
    footage: Literal["real", "motion"] | None = None
    gen_mode: Literal["text", "frame"] | None = None


@router.get("/content-projects/{project_id}/units/{unit_id}/shot-slots")
def read_shot_slots(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return shot_slots.view(db, user, project_id, unit_id)


@router.post("/content-projects/{project_id}/units/{unit_id}/material-autofill", status_code=202)
def start_autofill(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    from ..services import material_autofill

    return material_autofill.start(db, user, project_id, unit_id)


@router.post("/content-projects/{project_id}/units/{unit_id}/edit-handoff")
def run_edit_handoff(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    from ..services import edit_handoff

    return edit_handoff.run(db, user, project_id, unit_id)


@router.get("/content-projects/{project_id}/units/{unit_id}/edit-handoff")
def read_edit_handoff(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from ..services import edit_handoff

    return edit_handoff.status(db, user, project_id, unit_id)


@router.patch("/content-projects/{project_id}/units/{unit_id}/shot-slots/{shot_id}/brief")
def update_shot_brief(project_id: int, unit_id: int, shot_id: str, payload: BriefIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return shot_slots.update_brief(db, user, project_id, unit_id, shot_id, payload.model_dump())


@router.post("/content-projects/{project_id}/units/{unit_id}/shot-slots/{shot_id}/upload-target")
def shot_upload_target(project_id: int, unit_id: int, shot_id: str, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return shot_slots.ensure_run(db, user, project_id, unit_id, shot_id)


@router.post("/content-projects/{project_id}/units/{unit_id}/shot-slots/briefs")
def write_shot_briefs(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return shot_slots.write_briefs(db, user, project_id, unit_id)


class DetachIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    candidate_id: str = Field(min_length=1, max_length=300)


@router.post("/material-match-runs/{run_id}/segments/{segment_id}/detach")
def detach_upload(run_id: int, segment_id: str, payload: DetachIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return material_matching.detach_upload(db, user, run_id, segment_id, payload.candidate_id)
