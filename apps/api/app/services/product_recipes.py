"""Finished-video recipes for product works, and the rule that a category does not repeat the same one back to back."""
import json
from functools import cache

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ContentMasterRevision, ProductSku, ProductSkuWork
from . import product_categories, product_motion
from .product_categories import CATALOG

GROUPS = {"product_show": "商品展示", "presenter": "真人讲解", "story": "剧情叙事", "lifestyle": "生活种草", "promo": "促销转化", "creative": "创意视觉"}
# A recipe the five latest other works of the category used is not picked again by the model.
RECENT = 5
_BRIEF = ("id", "name", "pitch", "group", "style", "needs")


def _fail(status: int, code: str, message: str):
    raise HTTPException(status, {"code": code, "message": message})


@cache
def catalog() -> tuple[dict, ...]:
    recipes = tuple(json.loads((CATALOG / "recipes.json").read_text(encoding="utf-8"))["recipes"])
    cameras = {item["id"] for item in product_motion.catalog()["camera"]}
    looks = {item["id"] for item in product_motion.catalog()["looks"]}
    for recipe in recipes:
        problems = [name for name, ok in (
            ("group", recipe["group"] in GROUPS), ("style", recipe["style"] in product_categories.STYLES),
            ("look", recipe["look"] in looks), ("camera_plan", set(recipe["camera_plan"]) <= set(product_categories.SHOT_TYPES)
                                                and set(recipe["camera_plan"].values()) <= cameras)) if not ok]
        if problems:
            raise ValueError(f"recipe {recipe['id']}: {', '.join(problems)}")
    return recipes


def get(recipe_id: str) -> dict | None:
    return next((recipe for recipe in catalog() if recipe["id"] == recipe_id), None)


def fits(recipe: dict, category_key: str | None) -> bool:
    # Recipes are tagged with the built-in categories only; a category of the user's own takes any recipe.
    builtin = {item["key"] for item in product_categories.builtin()}
    return not recipe["categories"] or category_key not in builtin or category_key in recipe["categories"]


def _category_key(link: ProductSkuWork) -> str | None:
    return ((link.settings_snapshot_json or {}).get("category") or {}).get("key")


def recent(db: Session, link: ProductSkuWork) -> list[dict]:
    """Recipes of the latest other works of the same category and owner, newest first."""
    key = _category_key(link)
    owner = db.scalar(select(ProductSku.owner_user_id).where(ProductSku.id == link.sku_id))
    found = []
    others = db.scalars(select(ProductSkuWork).join(ProductSku, ProductSku.id == ProductSkuWork.sku_id)
                        .where(ProductSku.owner_user_id == owner, ProductSkuWork.unit_id != link.unit_id)
                        .order_by(ProductSkuWork.id.desc()))
    for other in others:
        if _category_key(other) != key:
            continue
        payload = db.scalar(select(ContentMasterRevision.payload_json).where(ContentMasterRevision.content_unit_id == other.unit_id)
                            .order_by(ContentMasterRevision.revision_no.desc()).limit(1)) or {}
        chosen = (payload.get("recipe") or {}).get("id")
        if chosen:
            found.append({"recipe_id": chosen, "unit_id": other.unit_id})
        if len(found) == RECENT:
            break
    return found


def listing(db: Session, link: ProductSkuWork, group: str | None = None, recipe_id: str | None = None, chosen: str | None = None) -> dict:
    """The recipes this work may use: the chosen one first, recently used ones marked so the model passes over them."""
    if recipe_id:
        recipe = get(recipe_id)
        if recipe is None:
            _fail(404, "product_recipe_unknown", f"没有配方 {recipe_id}")
        return {"recipe": recipe, "group_name": GROUPS[recipe["group"]]}
    if group and group not in GROUPS:
        _fail(422, "product_recipe_group_invalid", "分组只能是：" + "、".join(GROUPS))
    key = _category_key(link)
    used = {item["recipe_id"]: item["unit_id"] for item in reversed(recent(db, link))}
    items = [{**{field: recipe[field] for field in _BRIEF}, **({"recently_used_by_unit": used[recipe["id"]]} if recipe["id"] in used else {})}
             for recipe in catalog() if fits(recipe, key) and (group is None or recipe["group"] == group)]
    return {"category": key, "chosen": chosen, "groups": GROUPS, "count": len(items), "recipes": items,
            "rule": f"挑一个适合这件商品和现有素材的配方，用 recipe_id 读完整配方；同品类最近 {RECENT} 条作品用过的（recently_used_by_unit）不要再用，除非用户在制作设置里选了它。"}


def check_draft(db: Session, link: ProductSkuWork, payload: dict, chosen: str | None) -> None:
    """A product 导演稿 names its recipe: one that exists, fits the category and was not just used, unless the user picked it."""
    recipe_id = (payload.get("recipe") or {}).get("id")
    if not recipe_id:
        _fail(422, "product_recipe_required", "商品作品的导演稿要写 recipe {id, reason}：先用 list_product_recipes 挑一个成片配方")
    recipe = get(recipe_id)
    if recipe is None:
        _fail(422, "product_recipe_unknown", f"没有配方 {recipe_id}")
    if recipe_id == chosen:
        return
    if chosen:
        _fail(422, "product_recipe_not_chosen", f"用户在制作设置里选了配方 {chosen}，导演稿要按它做")
    if not fits(recipe, _category_key(link)):
        _fail(422, "product_recipe_category", f"配方「{recipe['name']}」不适合这个品类，换一个")
    clash = next((item for item in recent(db, link) if item["recipe_id"] == recipe_id), None)
    if clash:
        _fail(409, "product_recipe_recent", f"配方「{recipe['name']}」作品 {clash['unit_id']} 刚用过，同品类最近 {RECENT} 条不重复，换一个")
