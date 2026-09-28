"""Home and project origin read projections."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models import User
from ..services.home_projection import home_projection, project_origin
from .content_projects import owned_project

router = APIRouter(prefix="/api/v1", tags=["home"])


@router.get("/home")
def get_home(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return home_projection(db, user)


@router.get("/content-projects/{project_id}/origin")
def get_project_origin(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    owned_project(db, project_id, user)
    return project_origin(db, project_id)
