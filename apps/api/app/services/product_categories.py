"""Product categories: like personas, each carries its own directive, script styles, hooks, look and camera plan."""
import copy
import json
import re
from functools import cache
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ProductCategory, ProductCategoryRevision, User

CATALOG = Path(__file__).resolve().parent.parent / "product_catalog"
STYLES = {"drama": "情景短剧", "reversal": "反转剧场", "interview": "街头采访", "story": "剧情故事",
          "unboxing": "开箱测评", "product-pov": "物品拟人", "comparison": "对比测评",
          "talking-head": "达人口播", "pain-point": "痛点种草", "scene": "场景安利"}
STYLE_FORMS = {"剧情形": ["drama", "reversal", "interview", "story"], "物品形": ["unboxing", "product-pov", "comparison"],
               "口播形": ["talking-head", "pain-point"], "场景形": ["scene"]}
# Drama-type styles have several speaking roles, so voiceover gives each role its own voice.
DIALOGUE_STYLES = {"drama", "reversal", "interview", "story"}
SHOT_TYPES = ("hook", "pain_point", "product_reveal", "demo", "social_proof", "cta")
DIRECTIVE_FIELDS = ("focus", "selling_points", "audience", "tone")
_KEY = re.compile(r"^[a-z0-9][a-z0-9-]{0,59}$")


def style_ref(style: str) -> str:
    return f"studio.product.style.{style}@1"


@cache
def builtin() -> tuple[dict, ...]:
    return tuple(json.loads((CATALOG / "categories.json").read_text(encoding="utf-8")))


def _fail(status: int, code: str, message: str):
    raise HTTPException(status, {"code": code, "message": message})


def validate_profile(value) -> dict:
    from . import product_motion

    if type(value) is not dict or set(value) - {"directive", "styles", "default_style", "hooks", "look", "camera_plan", "production_stages"}:
        _fail(422, "product_category_invalid", "品类设置格式不对")
    directive = value.get("directive") or {}
    if (type(directive) is not dict or set(directive) - {*DIRECTIVE_FIELDS, "banned_words"}
            or any(type(directive.get(key, "")) is not str or len(directive.get(key, "")) > 2000 for key in DIRECTIVE_FIELDS)
            or type(directive.get("banned_words", [])) is not list or len(directive.get("banned_words", [])) > 60
            or any(type(word) is not str or not 0 < len(word) <= 30 for word in directive.get("banned_words", []))):
        _fail(422, "product_category_directive_invalid", "品类要点格式不对")
    styles = value.get("styles") or []
    if type(styles) is not list or not styles or set(styles) - STYLES.keys() or len(set(styles)) != len(styles):
        _fail(422, "product_category_styles_invalid", "可用脚本风格至少选一个，且只能从 10 种风格里选")
    if value.get("default_style") not in styles:
        _fail(422, "product_category_default_style_invalid", "默认风格必须在可用风格里")
    hooks = value.get("hooks") or []
    if type(hooks) is not list or len(hooks) > 16 or any(type(hook) is not str or not 0 < len(hook) <= 40 for hook in hooks):
        _fail(422, "product_category_hooks_invalid", "推荐开头格式不对")
    motion = product_motion.catalog()
    if value.get("look") not in {item["id"] for item in motion["looks"]}:
        _fail(422, "product_category_look_invalid", "默认光线色调不在平台列表里")
    plan = value.get("camera_plan") or {}
    cameras = {item["id"] for item in motion["camera"]}
    if type(plan) is not dict or set(plan) - set(SHOT_TYPES) or set(plan.values()) - cameras:
        _fail(422, "product_category_camera_invalid", "运镜计划只能用平台运镜库里的运镜")
    if value.get("production_stages") is not None:
        from .studio_creative_catalog import validate_production_stages

        try:
            validate_production_stages(value["production_stages"])
        except ValueError:
            _fail(422, "product_category_stages_invalid", "各阶段 skill 设置不对")
    return copy.deepcopy(value)


def _profile_of(item: dict) -> dict:
    return {key: item[key] for key in ("directive", "styles", "default_style", "hooks", "look", "camera_plan")}


def ensure_builtin(db: Session, user: User) -> None:
    """Built-in categories are seeded per owner once; later edits are the owner's own revisions."""
    have = set(db.scalars(select(ProductCategory.key).where(ProductCategory.owner_user_id == user.id)))
    for item in builtin():
        if item["key"] in have:
            continue
        row = ProductCategory(owner_user_id=user.id, key=item["key"], name=item["name"], revision=1)
        db.add(row)
        db.flush()
        db.add(ProductCategoryRevision(category_id=row.id, revision=1, profile_json=_profile_of(item), created_by="platform"))
    db.flush()


def _view(db: Session, row: ProductCategory) -> dict:
    current = db.scalar(select(ProductCategoryRevision).where(ProductCategoryRevision.category_id == row.id,
                                                              ProductCategoryRevision.revision == row.revision))
    return {"id": row.id, "key": row.key, "name": row.name, "status": row.status, "revision": row.revision,
            "builtin": row.key in {item["key"] for item in builtin()}, "profile": current.profile_json if current else None}


def list_categories(db: Session, user: User) -> dict:
    ensure_builtin(db, user)
    db.commit()
    rows = db.scalars(select(ProductCategory).where(ProductCategory.owner_user_id == user.id).order_by(ProductCategory.id))
    return {"items": [_view(db, row) for row in rows],
            "styles": [{"id": key, "name": name, "form": next(form for form, ids in STYLE_FORMS.items() if key in ids)} for key, name in STYLES.items()]}


def _owned(db: Session, user: User, category_id: int) -> ProductCategory:
    row = db.get(ProductCategory, category_id)
    if row is None or row.owner_user_id != user.id:
        _fail(404, "product_category_not_found", "没有这个品类")
    return row


def create(db: Session, user: User, key: str, name: str, profile: dict) -> dict:
    ensure_builtin(db, user)
    if not _KEY.fullmatch(key) or not 0 < len(name.strip()) <= 100:
        _fail(422, "product_category_key_invalid", "品类标识只能用小写字母、数字和横线，名称不能为空")
    if db.scalar(select(ProductCategory.id).where(ProductCategory.owner_user_id == user.id, ProductCategory.key == key)):
        _fail(409, "product_category_exists", "这个品类标识已存在")
    row = ProductCategory(owner_user_id=user.id, key=key, name=name.strip(), revision=1)
    db.add(row)
    db.flush()
    db.add(ProductCategoryRevision(category_id=row.id, revision=1, profile_json=validate_profile(profile), created_by=user.email))
    db.commit()
    return _view(db, row)


def update(db: Session, user: User, category_id: int, expected_revision: int, name: str | None, status: str | None, profile: dict | None) -> dict:
    row = _owned(db, user, category_id)
    if row.revision != expected_revision:
        _fail(409, "product_category_revision_conflict", "品类已被修改，请刷新后再改")
    if name is not None:
        if not 0 < len(name.strip()) <= 100:
            _fail(422, "product_category_name_invalid", "名称不能为空")
        row.name = name.strip()
    if status is not None:
        row.status = status
    if profile is not None:
        row.revision += 1
        db.add(ProductCategoryRevision(category_id=row.id, revision=row.revision, profile_json=validate_profile(profile), created_by=user.email))
    db.commit()
    return _view(db, row)


def resolve(db: Session, owner_user_id: int, key: str) -> dict | None:
    """The category's current revision, frozen into a work so later edits do not change it."""
    if not key:
        return None
    row = db.scalar(select(ProductCategory).where(ProductCategory.owner_user_id == owner_user_id, ProductCategory.key == key))
    if row is None:
        return None
    current = db.scalar(select(ProductCategoryRevision).where(ProductCategoryRevision.category_id == row.id,
                                                              ProductCategoryRevision.revision == row.revision))
    return {"key": row.key, "name": row.name, "revision": row.revision, "revision_id": current.id, "profile": current.profile_json}


_GUESS = {"beauty": ("美妆", "护肤", "化妆", "彩妆", "面膜", "口红", "香水"), "food": ("食品", "零食", "饮料", "食物", "茶", "咖啡", "生鲜"),
          "home": ("家居", "日用", "家具", "厨房", "清洁", "收纳", "床品", "沙发"), "fashion": ("服饰", "服装", "鞋", "包", "衣", "裤", "配饰"),
          "tech": ("数码", "3c", "电子", "耳机", "手机", "电脑", "相机", "家电", "电器")}


def guess_key(text: str) -> str:
    """Old SKUs only have free text; a keyword match picks the built-in category, otherwise none."""
    lowered = (text or "").lower()
    return next((key for key, words in _GUESS.items() if any(word in lowered for word in words)), "")
