"""身份与 RBAC（STU-010）。

V1 本地开发用 header 身份（X-Studio-User 传 email，自动建号），
生产接入标准身份框架时只替换 get_current_user，权限矩阵不变。
"""

import base64
import hashlib
import hmac
import json
import math
import re
import time

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from .db import get_db
from .models import User

ROLE_ADMIN = "admin"
ROLE_EDITOR = "editor"
ROLE_REVIEWER = "reviewer"
ROLE_VIEWER = "viewer"


def _b64(value: str) -> bytes:
    if not value or not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        raise ValueError("jwt_encoding_invalid")
    return base64.b64decode(value + "=" * (-len(value) % 4), altchars=b"-_", validate=True)


def _jwt_object(raw: bytes) -> dict:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("jwt_duplicate_claim")
            result[key] = value
        return result

    result = json.loads(raw, object_pairs_hook=pairs)
    if not isinstance(result, dict):
        raise TypeError("jwt_object_required")
    return result


def _production_claims(token: str, settings) -> dict:
    parts = token.split(".") if isinstance(token, str) and len(token) <= 8192 else []
    if len(parts) != 3:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "production_auth_invalid")
    try:
        header = _jwt_object(_b64(parts[0]))
        claims = _jwt_object(_b64(parts[1]))
        signature = _b64(parts[2])
    except (ValueError, TypeError, json.JSONDecodeError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "production_auth_invalid") from None
    if (header.get("alg") != "HS256" or "crit" in header or header.get("b64") is False
            or not hmac.compare_digest(
        signature, hmac.new(settings.auth_hmac_secret.encode(), f"{parts[0]}.{parts[1]}".encode(), hashlib.sha256).digest()
    )):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "production_auth_invalid")
    if claims.get("iss") != settings.auth_issuer:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "production_auth_invalid")
    audience = claims.get("aud")
    if not (audience == settings.auth_audience or isinstance(audience, list) and settings.auth_audience in audience):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "production_auth_invalid")
    now = time.time()
    if (type(claims.get("exp")) not in {int, float} or not 0 < claims["exp"] <= 2**53
            or not math.isfinite(claims["exp"]) or claims["exp"] <= now):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "production_auth_expired")
    if "nbf" in claims and (type(claims["nbf"]) not in {int, float} or not 0 <= claims["nbf"] <= 2**53
            or not math.isfinite(claims["nbf"]) or claims["nbf"] > now + 30):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "production_auth_not_active")
    if not isinstance(claims.get("sub"), str) or not claims["sub"] or len(claims["sub"]) > 500:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "production_auth_invalid")
    return claims


def get_current_user(
    db: Session = Depends(get_db),
    x_studio_user: str | None = Header(default=None, alias="X-Studio-User"),
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> User:
    return _current_user(db, x_studio_user, authorization, provision=True)


def get_existing_user(
    db: Session = Depends(get_db),
    x_studio_user: str | None = Header(default=None, alias="X-Studio-User"),
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> User:
    # Pure previews must not create an identity while authorizing a read.
    return _current_user(db, x_studio_user, authorization, provision=False)


def _current_user(db, x_studio_user, authorization, *, provision):
    from .config import get_settings, validate_production_settings

    settings = get_settings()
    if settings.app_env == "production":
        validate_production_settings(settings)
        if not isinstance(authorization, str) or not authorization.startswith("Bearer "):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "production_auth_required")
        claims = _production_claims(authorization[7:].strip(), settings)
        matches = db.query(User).filter(User.identity_issuer == claims["iss"], User.identity_subject == claims["sub"]).limit(2).all()
        if not matches:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "production_identity_unknown")
        if len(matches) != 1:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "production_identity_ambiguous")
        user = matches[0]
    else:
        email = (x_studio_user or "admin@studio.local").strip().lower()
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            if not provision:
                raise HTTPException(status.HTTP_403_FORBIDDEN, "local_identity_unknown")
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
