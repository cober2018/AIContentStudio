"""本体与形态：建项目时勾形态、本体定稿后补勾、本体更新后重做，以及角色的默认勾选。"""

from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_editor
from ..models import User
from ..services import topic_forms

router = APIRouter(prefix="/api/v1", tags=["topic-forms"])

Form = Literal["long_article", "graphic_cards", "video_landscape", "video_portrait"]


class ArticleIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(default="", max_length=500)
    text: str = Field(min_length=1, max_length=200_000)
    url: str | None = Field(default=None, max_length=2000)
    published_record_id: int | None = None
    published_at: str | None = Field(default=None, max_length=40)


class PlanIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    persona_id: int
    forms: list[Form] = Field(min_length=1, max_length=4)
    body_source: Literal["new", "published_article"] = "new"
    writer: Literal["external", "platform"] = "external"
    article: ArticleIn | None = None


class FormsIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    forms: list[Form] = Field(min_length=1, max_length=4)


@router.get("/content-projects/{project_id}/forms")
def get_forms(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return topic_forms.view(db, user, project_id)


@router.post("/content-projects/{project_id}/forms", status_code=201)
def plan_forms(payload: PlanIn, project_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return topic_forms.create(db, user, project_id, persona_id=payload.persona_id, forms=payload.forms, body_source=payload.body_source,
                              writer=payload.writer, article=payload.article.model_dump() if payload.article else None)


@router.put("/content-projects/{project_id}/forms")
def change_forms(payload: FormsIn, project_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return topic_forms.set_forms(db, user, project_id, payload.forms)


@router.post("/content-projects/{project_id}/units/{unit_id}/form-redo", status_code=201)
def redo_form(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return topic_forms.redo(db, user, project_id, unit_id)


@router.get("/content-personas/{persona_id}/default-forms")
def get_default_forms(persona_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from ..services.content_identity import owned_entity

    owned_entity(db, user, "persona", persona_id)
    return {"persona_id": persona_id, "forms": topic_forms.persona_defaults(db, persona_id)}


@router.put("/content-personas/{persona_id}/default-forms")
def put_default_forms(payload: FormsIn, persona_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return topic_forms.set_persona_defaults(db, user, persona_id, payload.forms)
