"""用户 API（P01/设置页用）。V1 为 header 身份的开发模式，见 deps.py。"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models import User

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "name": user.name, "role": user.role}


@router.get("")
def list_users(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return [
        {"id": u.id, "email": u.email, "name": u.name, "role": u.role, "is_active": u.is_active}
        for u in db.scalars(select(User).order_by(User.id))
    ]
