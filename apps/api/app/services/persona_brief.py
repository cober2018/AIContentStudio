"""The persona part of a third-party model's brief: who the work speaks as, whether it has a portrait, and the persona's own method when it set one."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import CapabilityArtifact, CapabilityArtifactRevision, ContentBrand, ContentPersona, User

PROFILE_FIELDS = {"positioning": "定位", "target_audience": "目标受众", "content_domains": "内容领域", "expression_style": "表达风格",
                  "visual_language": "视觉语言", "content_boundaries": "内容边界", "risk_boundaries": "风险边界",
                  "public_fact_policy": "公开事实规则"}
CREATIVE_FIELD = {"text": "text_creative_profile", "graphic": "graphic_creative_profile", "video": "video_creative_profile"}
EXTRA_TEXT = 4000

RULES = [
    "角色资料是这条作品的出发点：选角度、取舍内容、说话方式都按 persona.profile；表达风格里的「不能出现的词」一个都不能出现；内容边界和风险边界内的不写。",
    "persona.portrait 为 true：角色有形象照，生成画面里的人物照它来；为 false：生成画面里不出现人物（只拍商品和场景，拿东西只出现手部），要人物出镜的镜头写成实拍，或请用户先给角色补形象照。",
    "persona.speech_samples 有样本：口播 / 旁白照这些真人逐字稿的说话方式写（句子长短、口头语、怎么称呼观众、怎么转话题），不照搬里面的内容、事实和经历；unavailable 有值说明这次没读到。",
    "persona.method 有值：按它的主方法 skill 写（用 get_craft_skill 读 method.skill.read），并照它的风格预设、质量标准、额外要求和附加方法；没有值就按 platform_skills 的默认选法。",
]


def _extras(db: Session, revision_ids: list) -> list[dict]:
    """Extra methods and reference styles picked for the persona, with their text so the model can follow them."""
    items = []
    for revision_id in revision_ids[:8]:
        revision = db.get(CapabilityArtifactRevision, revision_id) if isinstance(revision_id, int) else None
        artifact = db.get(CapabilityArtifact, revision.artifact_id) if revision else None
        if revision is None or artifact is None:
            continue
        content = revision.content_json or {}
        text = content.get("text") or content.get("description") or content.get("instruction") or ""
        items.append({"name": artifact.name, "kind": artifact.kind, "text": str(text)[:EXTRA_TEXT]})
    return items


def _method(db: Session, profile: dict | None) -> dict | None:
    from .studio_creative_catalog import PRESETS, QUALITY, SKILLS

    if not isinstance(profile, dict) or not profile.get("skill_ref"):
        return None
    skill = SKILLS.get(profile["skill_ref"]) or {}
    preset = PRESETS.get(profile.get("style_preset_ref") or "")
    quality = QUALITY.get(profile.get("quality_profile_ref") or "")
    return {
        "skill": {"ref": profile["skill_ref"], "purpose": skill.get("purpose"), "read": f'get_craft_skill(skill="{profile["skill_ref"]}")'},
        "style_preset": None if preset is None else {"ref": preset["ref"], "settings": preset["config"]},
        "quality_profile": None if quality is None else {"ref": quality["ref"], "checks": quality["checks"]},
        "stage_instruction": profile.get("stage_instruction"),
        "parameters": profile.get("parameters") or {},
        "extras": _extras(db, profile.get("capability_memory_revision_ids") or []),
    }


def _speech_samples(db: Session, unit, folder) -> dict | None:
    # Product works borrow only the persona's voice and identity, not how the persona talks.
    if not folder or unit.production_domain == "product":
        return None
    from .obsidian_knowledge import speech_samples

    return speech_samples(db, folder)


def persona_brief(db: Session, user: User, unit) -> dict | None:
    from . import content_identity, craft_skills, voiceover

    if unit.persona_id is None:
        return None
    try:
        identity = content_identity.effective(db, user, persona_id=unit.persona_id, account_id=unit.account_id, series_id=unit.series_id)
    except HTTPException:
        # A persona this user cannot read leaves the brief without it rather than failing the whole brief.
        return None
    merged = identity.get("effective_profile") or {}
    persona = db.get(ContentPersona, unit.persona_id)
    brand = db.get(ContentBrand, persona.brand_id) if persona and persona.brand_id else None
    # Product works borrow only the persona's identity and voice; their script follows the product system's own skills.
    with_method = unit.production_domain != "product" and craft_skills.writing_skills_on(db, unit.id)
    return {
        "name": persona.name if persona else None, "brand": brand.name if brand else None,
        "voice": voiceover.settings_for(db, unit)["preset_name"],
        "portrait": any(content_identity.usable_portrait(db, item) for item in merged.get("portrait_material_revision_ids") or []),
        "profile": {label: merged[key] for key, label in PROFILE_FIELDS.items() if merged.get(key) not in (None, "", [], {})},
        "method": _method(db, merged.get(CREATIVE_FIELD.get(unit.modality, ""))) if with_method else None,
        "speech_samples": _speech_samples(db, unit, merged.get("speech_sample_folder")),
        "rules": RULES,
    }


def persona_skill_refs(db: Session, user: User, unit) -> set[str]:
    """Skill refs the persona's own setup names, readable even when an older version than the newest."""
    brief = persona_brief(db, user, unit) or {}
    method = brief.get("method") or {}
    return {method["skill"]["ref"]} if method.get("skill") else set()
