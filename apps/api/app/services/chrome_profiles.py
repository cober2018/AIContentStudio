"""Which local Chrome profile each persona's platform accounts open in.

The studio never holds platform cookies or passwords. Each Chrome profile keeps its own
logins, so one profile per persona lets the user stay logged in to every persona's
accounts at once. Only profile names are read from Chrome.
"""

import json
import subprocess
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import ContentPersona, SystemSetting, User
from . import content_identity

KEY = "persona_chrome_profiles"
LOCAL_STATE = Path.home() / "Library/Application Support/Google/Chrome/Local State"
CHROME_APP = Path("/Applications/Google Chrome.app")


def _fail(status: int, code: str, message: str):
    raise HTTPException(status, {"code": code, "message": message})


def local_profiles() -> list[dict]:
    try:
        cache = json.loads(LOCAL_STATE.read_text(encoding="utf-8")).get("profile", {}).get("info_cache", {})
    except (OSError, ValueError):
        return []
    return [{"dir": key, "name": (value or {}).get("name") or key} for key, value in sorted(cache.items())]


def _stored(db: Session) -> dict[str, str]:
    row = db.get(SystemSetting, KEY)
    personas = (row.value or {}).get("personas") if row else None
    return dict(personas) if isinstance(personas, dict) else {}


def view(db: Session) -> dict:
    return {"available": CHROME_APP.exists(), "profiles": local_profiles(), "personas": _stored(db)}


def set_persona(db: Session, user: User, persona_id: int, profile_dir: str | None) -> dict:
    content_identity.owned_entity(db, user, "persona", persona_id, mutable=True)
    current = _stored(db)
    if profile_dir:
        if profile_dir not in {item["dir"] for item in local_profiles()}:
            _fail(422, "chrome_profile_missing", "本机 Chrome 里没有这个个人资料")
        # Two personas in one profile would log each other out of the same platform.
        holder = next((key for key, value in current.items() if value == profile_dir and key != str(persona_id)), None)
        if holder is not None:
            other = db.get(ContentPersona, int(holder))
            _fail(409, "chrome_profile_taken", f"这个个人资料已经给角色「{other.name if other else holder}」用了")
        current[str(persona_id)] = profile_dir
    else:
        current.pop(str(persona_id), None)
    row = db.get(SystemSetting, KEY) or SystemSetting(key=KEY)
    row.value, row.updated_by = {"personas": current}, user.email
    db.add(row)
    db.commit()
    return view(db)


def open_account_link(db: Session, user: User, account_id: int, url: str) -> dict:
    account = content_identity.owned_entity(db, user, "account", account_id)
    allowed = {item["url"] for item in content_identity.creator_links(account.platform_channel)} | ({account.home_url} if account.home_url else set())
    if url not in allowed:
        _fail(422, "account_link_not_allowed", "只能打开这个账号自己的入口或主页")
    profile_dir = _stored(db).get(str(account.persona_id)) if account.persona_id is not None else None
    if not profile_dir:
        _fail(409, "chrome_profile_unset", "这个账号的角色还没选 Chrome 个人资料")
    if not CHROME_APP.exists():
        _fail(503, "chrome_unavailable", "本机没有找到 Google Chrome")
    subprocess.run(["open", "-na", str(CHROME_APP), "--args", f"--profile-directory={profile_dir}", url], check=False, timeout=10)
    return {"opened": True, "profile_dir": profile_dir}
