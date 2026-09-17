"""身份与 RBAC（STU-010）。

V1 本地开发用 header 身份（X-Studio-User 传 email，自动建号），
生产接入标准身份框架时只替换 get_current_user，权限矩阵不变。
"""

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from .db import get_db
from .models import User

ROLE_ADMIN = "admin"
ROLE_EDITOR = "editor"
ROLE_REVIEWER = "reviewer"
ROLE_VIEWER = "viewer"


def get_current_user(
    db: Session = Depends(get_db),
    x_studio_user: str | None = Header(default=None, alias="X-Studio-User"),
) -> User:
    email = (x_studio_user or "admin@studio.local").strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        user = User(email=email, name=email.split("@")[0], role=ROLE_EDITOR)
        db.add(user)
        db.commit()
        db.refresh(user)
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "用户已停用")
    return user


def require_role(*allowed_roles: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"需要角色 {list(allowed_roles)}，当前角色 {user.role}",
            )
        return user

    return checker


# 常用组合
require_admin = require_role(ROLE_ADMIN)
require_editor = require_role(ROLE_ADMIN, ROLE_EDITOR)
require_editor_or_reviewer = require_role(ROLE_ADMIN, ROLE_EDITOR, ROLE_REVIEWER)
