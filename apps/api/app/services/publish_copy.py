"""发布文案：每个作品一份通用文案；视频和图文的格式不同。"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import ContentUnit, User

# Kept under the key product works used first, so their saved copy stays valid.
COPY_KEY = "product_publish_copy"
FIELDS = {"video": ("title", "hashtags", "cover_text", "interaction", "description"),
          "graphic": ("title", "lead", "hashtags", "interaction")}
LIMITS = {"product": {"title": 15, "cover_text": 8, "interaction": 60, "description": 50},
          "video": {"title": 30, "cover_text": 12, "interaction": 60, "description": 300},
          "graphic": {"title": 30, "lead": 120, "interaction": 60}}
NAMES = {"title": "标题", "cover_text": "封面字", "interaction": "互动引导", "description": "简介", "lead": "导语"}
SKILLS = {"product": "studio.product.publish-copy", "video": "studio.persona.publish-copy", "graphic": "studio.persona.graphic-copy"}


def _fail(status: int, code: str, message: str):
    raise HTTPException(status, {"code": code, "message": message})


def kind(db: Session, unit: ContentUnit) -> str:
    """product (product video), video (persona video) or graphic."""
    from .product_video import work

    if unit.modality == "graphic":
        return "graphic"
    if unit.modality != "video":
        _fail(409, "publish_copy_modality_unsupported", "发布文案只给视频和图文作品")
    return "product" if work(db, unit.id) else "video"


def _store(db: Session) -> dict:
    from .product_video import _setting

    return _setting(db, COPY_KEY)


def stored(db: Session, unit_id: int) -> dict | None:
    return _store(db).get(str(unit_id))


def get(db: Session, user: User, project_id: int, unit_id: int) -> dict:
    from .content_masters import owned_unit

    _project, unit = owned_unit(db, project_id, unit_id, user)
    which = kind(db, unit)
    return {"format": "graphic" if which == "graphic" else "video", "limits": LIMITS[which], "skill": SKILLS[which],
            "copy": stored(db, unit_id)}


def save(db: Session, user: User, project_id: int, unit_id: int, value: dict) -> dict:
    from .content_masters import owned_unit
    from .product_video import _put

    _project, unit = owned_unit(db, project_id, unit_id, user)
    which = kind(db, unit)
    fields = FIELDS["graphic" if which == "graphic" else "video"]
    if type(value) is not dict:
        _fail(422, "publish_copy_invalid", "发布文案格式不对")
    # Older product copy named a channel; one copy now serves every platform, so it is accepted and dropped.
    given = {key: item for key, item in value.items() if key != "channel" and item not in ("", [], None)}
    extra = set(given) - set(fields)
    if extra:
        names = "、".join(NAMES.get(key, key) for key in sorted(extra))
        _fail(422, "publish_copy_format_mismatch", f"{'图文' if which == 'graphic' else '视频'}文案没有{names}")
    for key, limit in LIMITS[which].items():
        if type(value.get(key, "")) is not str or len(value.get(key, "")) > limit:
            _fail(422, "publish_copy_too_long", f"{NAMES[key]}不能超过 {limit} 个字")
    tags = value.get("hashtags", [])
    if type(tags) is not list or len(tags) > 5 or any(type(tag) is not str or not 0 < len(tag) <= 30 for tag in tags):
        _fail(422, "publish_copy_hashtags_invalid", "话题最多 5 个，每个不超过 30 个字")
    store = _store(db)
    store[str(unit_id)] = {key: value.get(key, [] if key == "hashtags" else "") for key in fields}
    _put(db, COPY_KEY, store, user.email)
    db.commit()
    if unit.modality == "video" and unit.status in {"finalized", "published"}:
        _refreeze(db, user, unit)
    return store[str(unit_id)]


def _refreeze(db: Session, user: User, unit: ContentUnit) -> None:
    """A finalized video's delivery candidate carries its copy, so new copy means a new candidate to approve."""
    from sqlalchemy import select

    from ..models import ContentAsset
    from .finished_video import SCHEMA, send_to_review

    latest = db.scalar(select(ContentAsset).where(ContentAsset.content_unit_id == unit.id, ContentAsset.channel_variant_revision_id.is_(None))
                       .order_by(ContentAsset.id.desc()).limit(1))
    manifest = (latest.candidate_manifest_json or {}) if latest else {}
    if manifest.get("schema_version") == SCHEMA:
        send_to_review(db, user, unit.project_id, unit.id, manifest["execution_id"])


def text(copy: dict | None) -> str | None:
    """The copy as the 发布文案.txt put into delivery packages."""
    if not copy:
        return None
    lines = [f"标题：{copy.get('title', '')}"]
    if "lead" in copy:
        lines.append(f"导语：{copy.get('lead', '')}")
    lines.append(f"话题：{' '.join(copy.get('hashtags') or [])}")
    if "cover_text" in copy:
        lines.append(f"封面字：{copy.get('cover_text', '')}")
    lines.append(f"互动引导：{copy.get('interaction', '')}")
    if copy.get("description"):
        lines += ["", copy["description"]]
    return "\n".join(lines) + "\n"
