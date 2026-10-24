"""Product-owned configuration shares execution contracts without inheriting identity."""
from copy import deepcopy

from fastapi import HTTPException
from sqlalchemy import select

from ..models import ContentProject, ProductSkuWork, User
from .discovery_runtime import digest
from .production_profiles import profile_snapshot
from .project_brief import current_brief


def is_product(unit):
    return getattr(unit, "production_domain", "persona") == "product"


def effective_settings(db, unit):
    if not is_product(unit):
        return {}
    saved = profile_snapshot(db, unit.id)
    if saved:
        return deepcopy(saved["settings"])
    work = db.scalar(select(ProductSkuWork).where(ProductSkuWork.unit_id == unit.id))
    return deepcopy(work.settings_snapshot_json or {}) if work else {}


def default_creative_profile(modality):
    from .content_identity import CreativeProfile
    from .studio_creative_catalog import _profile

    refs = {
        "text": ("studio.text.longform", "studio.text.concise-social", "studio.quality.text.technical", "chat"),
        "graphic": ("studio.graphic.visual-director", "studio.graphic.clean-infographic", "studio.quality.graphic.editorial", "image_generation"),
        "video": ("studio.video.director-package", "studio.graphic.product-neutral", "studio.quality.video.product", "chat"),
        "audio": ("studio.audio.tts", "studio.audio.clear-explainer", "studio.quality.audio.explainer", "tts"),
    }
    skill, preset, quality, capability = refs[modality]
    value = _profile("auto", skill, preset, quality, capability=capability, recipe=f"product.{modality}.v1")
    return CreativeProfile.model_validate(value).model_dump(mode="json", by_alias=True)


def effective_profile(db, unit):
    if not is_product(unit):
        return {}
    settings = effective_settings(db, unit)
    profile = {key: deepcopy(value) for key, value in settings.items()
               if key.endswith("_creative_profile") and value is not None}
    key = f"{unit.modality}_creative_profile"
    if key not in profile:
        profile[key] = default_creative_profile(unit.modality)
    if settings.get("voice_id") and "audio_creative_profile" not in profile:
        profile["audio_creative_profile"] = default_creative_profile("audio")
    if settings.get("voice_id") and "audio_creative_profile" in profile:
        audio = profile["audio_creative_profile"]
        audio["parameters"] = {**audio.get("parameters", {}), "voice": settings["voice_id"]}
    brief = current_brief(db, unit.project_id)
    brief_stages = (brief.product_context_json or {}).get("production_stages") if brief else None
    work_stages = settings.get("production_stages")
    if work_stages is None:
        work_stages = profile[key].get("production_stages")
    if brief_stages is not None or work_stages is not None:
        stages = {**(brief_stages or {}), **(work_stages or {})}
        profile[key]["production_stages"] = deepcopy(stages)
        profile["product_production_stages"] = deepcopy(stages)
    if settings.get("product_production_methods"):
        profile["product_production_methods"] = deepcopy(settings["product_production_methods"])
    return profile


def context_snapshot(db, unit, user=None):
    if not is_product(unit):
        return None
    project = db.get(ContentProject, unit.project_id)
    if not project or (user is not None and project.owner_user_id != user.id):
        raise HTTPException(404, "商品作品不存在")
    brief = current_brief(db, unit.project_id)
    work = db.scalar(select(ProductSkuWork).where(ProductSkuWork.unit_id == unit.id))
    profiles = effective_profile(db, unit)
    stages = profiles.get("product_production_stages")
    if stages is not None:
        from .creative_configuration import freeze_production_stages
        settings = effective_settings(db, unit)
        frozen = profiles.get("product_production_methods", {}).get(unit.modality)
        if stages != (settings.get("production_stages") or (settings.get(f"{unit.modality}_creative_profile") or {}).get("production_stages")):
            frozen = None
        profiles["product_production_methods"] = {unit.modality: freeze_production_stages(db,
            user or db.get(User, project.owner_user_id), unit, stages, origin="product_configuration", frozen_manifest=frozen)}
    value = {"production_domain": "product", "product_context": deepcopy(brief.product_context_json or {}) if brief else {},
             "production_profile": profile_snapshot(db, unit.id), "creative_profiles": profiles,
             "sku": {"sku_id": work.sku_id, "sku_revision_id": work.sku_revision_id, "plan_id": work.plan_id} if work else None}
    return {**value, "checksum": digest(value)}


get_product_context = context_snapshot


def prompt_snapshot(snapshot):
    # The current stage supplies its own frozen methods; all-stage history stays in the hashed context.
    return {key: deepcopy(snapshot[key]) for key in ("production_domain", "checksum", "product_context", "sku")
            if key in snapshot}
