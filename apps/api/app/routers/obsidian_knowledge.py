"""Explicit local knowledge access through authorized project pages."""

from typing import Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_admin, require_editor
from ..models import User
from ..services import obsidian_knowledge as knowledge
from .content_projects import mutable_project, owned_project

router = APIRouter(prefix="/api/v1", tags=["obsidian-knowledge"])


class ConnectionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    root_path: str = Field(min_length=1, max_length=1000)
    folders: list[str] = Field(default_factory=list, max_length=30)
    enabled: bool = True
    expected_revision: int = Field(ge=0)


class SelectionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_document_id: int | None = Field(default=None, ge=1)
    source_checksum: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    note_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    path: str = Field(default="", max_length=1500)
    title: str | None = Field(default=None, max_length=500)
    excerpt: str = Field(default="", max_length=4000)
    purposes: list[Literal["professional", "style"]] = Field(min_length=1, max_length=2)
    persona_id: int | None = Field(default=None, ge=1)
    unit_id: int | None = Field(default=None, ge=1)
    modalities: list[Literal["text", "graphic", "video"]] = Field(default_factory=lambda: ["text"], min_length=1, max_length=3)
    model_use_allowed: bool = False
    connection_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    connection_revision: int | None = Field(default=None, ge=1)


class KnowledgeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=0)
    items: list[SelectionIn] = Field(max_length=5)


@router.get("/obsidian/connection")
def connection(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return knowledge.connection_view(db, user)


@router.put("/obsidian/connection")
def configure(payload: ConnectionIn, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    return knowledge.save_connection(db, user, payload.model_dump())


@router.get("/content-projects/{project_id}/knowledge/notes")
def search(project_id: int, q: str = Query(default="", max_length=200), limit: int = Query(default=20, ge=1, le=20),
           db: Session = Depends(get_db), user: User = Depends(require_editor)):
    mutable_project(db, project_id, user)
    return knowledge.search_notes(db, q, limit)


@router.get("/content-projects/{project_id}/knowledge/note")
def preview(project_id: int, path: str = Query(min_length=1, max_length=1500),
            db: Session = Depends(get_db), user: User = Depends(require_editor)):
    mutable_project(db, project_id, user)
    return knowledge.read_note(db, path)


@router.get("/content-projects/{project_id}/knowledge")
def current(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    owned_project(db, project_id, user)
    return knowledge.context_view(db, project_id)


@router.put("/content-projects/{project_id}/knowledge")
def select_knowledge(project_id: int, payload: KnowledgeIn, db: Session = Depends(get_db),
                     user: User = Depends(require_editor)):
    return knowledge.save_context(db, project_id, user, payload.model_dump())
