"""Explicit Stage decisions, reusable methods and versioned Recipe selection."""

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_existing_user
from ..models import User
from ..services import creation_recipe_learning as learning
from ..services import stage_feedback
from ..services.stage_contracts import StageContractError
from ..services.stage_invocations import StageInvocationError
from .content_projects import StagePreviewRoute

router = APIRouter(prefix="/api/v1/content-projects/{project_id}/units/{unit_id}/creation-recipe",
                   tags=["creation-recipe"], route_class=StagePreviewRoute)
read_router = APIRouter(tags=["creation-recipe"])


def _call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except StageInvocationError as exc:
        raise HTTPException(exc.status_code, {"code": exc.code}) from None
    except (StageContractError, ValueError):
        raise HTTPException(422, {"code": "recipe_input_invalid"}) from None


@read_router.get("/methods")
def methods(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(get_existing_user)):
    return _call(learning.method_inventory, db, project_id, unit_id, user)


@read_router.get("/options")
def options(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(get_existing_user)):
    return _call(learning.recipe_options, db, project_id, unit_id, user)


@read_router.get("/stages/{node_id}/history")
def history(project_id: int, unit_id: int, node_id: str, run_id: int,
            db: Session = Depends(get_db), user: User = Depends(get_existing_user)):
    return _call(stage_feedback.history, db, project_id, unit_id, node_id, user, run_id=run_id)


@router.post("/adopt-recipe")
def adopt_recipe(project_id: int, unit_id: int, payload: dict = Body(...),
                 db: Session = Depends(get_db), user: User = Depends(get_existing_user)):
    return _call(learning.adopt_recipe, db, project_id, unit_id, user, payload)


@router.post("/stages/{node_id}/feedback")
def feedback(project_id: int, unit_id: int, node_id: str, payload: dict = Body(...),
             db: Session = Depends(get_db), user: User = Depends(get_existing_user)):
    return _call(stage_feedback.submit_feedback, db, project_id, unit_id, node_id, user, payload)


@router.post("/stages/{node_id}/improvement-preview")
def improvement_preview(project_id: int, unit_id: int, node_id: str, payload: dict = Body(...),
                        db: Session = Depends(get_db), user: User = Depends(get_existing_user)):
    return _call(learning.improvement_preview, db, project_id, unit_id, node_id, user, payload)


@router.post("/stages/{node_id}/save-adjustment")
def save_adjustment(project_id: int, unit_id: int, node_id: str, payload: dict = Body(...),
                    db: Session = Depends(get_db), user: User = Depends(get_existing_user)):
    return _call(learning.save_adjustment, db, project_id, unit_id, node_id, user, payload)


@router.post("/stages/{node_id}/apply-method-preview")
def apply_method_preview(project_id: int, unit_id: int, node_id: str, payload: dict = Body(...),
                         db: Session = Depends(get_db), user: User = Depends(get_existing_user)):
    return _call(learning.apply_method_preview, db, project_id, unit_id, node_id, user, payload)


@router.post("/stages/{node_id}/apply-method")
def apply_method(project_id: int, unit_id: int, node_id: str, payload: dict = Body(...),
                 db: Session = Depends(get_db), user: User = Depends(get_existing_user)):
    return _call(learning.apply_method, db, project_id, unit_id, node_id, user, payload)


@router.post("/stages/{node_id}/tuning-suggestion")
def tuning_suggestion(project_id: int, unit_id: int, node_id: str, payload: dict = Body(...),
                      db: Session = Depends(get_db), user: User = Depends(get_existing_user)):
    from ..services.stage_tuning import tuning_suggestion as suggest

    return _call(suggest, db, project_id, unit_id, node_id, user, payload)


router.include_router(read_router)
