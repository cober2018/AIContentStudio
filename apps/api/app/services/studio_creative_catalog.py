"""Product-owned creative resources.

The catalog is deliberately code-owned and read-only. It is not a second
database for skills or learned methods; Capability Memory and installed Agent
Skills remain separate inventories.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import unicodedata
from datetime import UTC, datetime, time, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

REF_RE = re.compile(r"^[a-z][a-z0-9_.-]{1,119}@[1-9][0-9]{0,5}$")
SAFE_TEXT_RE = re.compile(r"(?:api[_-]?key|secret|token|password|authorization|/Users/|/private/|/tmp/|~/)", re.IGNORECASE)
BINDING_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,99}$")
PARAMETER_SCHEMAS = {
    "instruction": {"type": "string", "maxLength": 4000},
    "candidate_count": {"type": "integer", "minimum": 1, "maximum": 5},
    "length": {"type": "string", "enum": ["short", "medium", "long"], "maxLength": 6},
    "tone": {"type": "string", "maxLength": 200},
    "density": {"type": "string", "enum": ["low", "medium", "high"], "maxLength": 6},
    "canvas_count": {"type": "integer", "minimum": 1, "maximum": 10},
    "aspect_ratio": {"type": "string", "enum": ["1:1", "4:3", "3:4", "16:9", "9:16"], "maxLength": 5},
    "template": {"type": "string", "maxLength": 100},
    "pace": {"type": "string", "enum": ["slow", "medium", "fast"], "maxLength": 6},
    "energy": {"type": "string", "maxLength": 100},
    "pause_policy": {"type": "string", "maxLength": 200},
    "voice": {"type": "string", "maxLength": 150},
    "rate": {"type": "number", "minimum": 0.5, "maximum": 2},
    "shot_count": {"type": "integer", "minimum": 1, "maximum": 100},
}
OUTPUT_SCHEMAS = {
    "studio.research.evidence-brief": ["research.brief.v1"],
    "studio.research.angle-lab": ["creative.angles.v1"],
    "studio.text.outline": ["content.outline.v1"],
    "studio.text.title-hook": ["creative.title-hook.v1"],
    "studio.text.article-plan": ["article.plan.v1"],
    "studio.graphic.visual-director": ["graphic.visual-direction.v1"],
    "studio.graphic.card-plan": ["graphic.card-plan.v1"],
    "studio.graphic.image-brief": ["graphic.visual-direction.v1"],
    "studio.audio.spoken-adapt": ["audio.spoken-adaptation.v1"],
    "studio.audio.voice-director": ["audio.voice-direction.v1"],
    "studio.video.script": ["video.script.v1"],
    "studio.video.product-script": ["video.script.v1"],
    "studio.video.product-shots": ["video.shot-plan.v1"],
    "studio.video.product-filming": ["video.shot-plan.v1"],
    "studio.video.shot-director": ["video.shot-plan.v1"],
}


def _ref(key: str, version: int = 1) -> str:
    return f"{key}@{version}"


PRODUCT_CONTEXT_SKILLS = frozenset({"studio.video.product-script", "studio.video.product-shots", "studio.video.product-filming",
                                    "studio.product.audience-need", "studio.product.purchase-reason", "studio.product.compliance-check"})


# Writing skills any work can use, kept in both systems.
SHARED_SKILLS = frozenset({"studio.research.evidence-brief", "studio.research.angle-lab", "studio.text.title-hook",
                           "studio.text.humanize", "studio.audio.spoken-adapt", "studio.video.script-review",
                           "studio.video.stock-scout", "studio.video.digital-human"})


def skill_system(key: str) -> str:
    """Persona and product works use separate skill systems; shared ones (and the craft skills) serve both."""
    return "product" if key in PRODUCT_CONTEXT_SKILLS else "shared" if key in SHARED_SKILLS else "persona"


def _resource(key: str, kind: str, modality: str, *, purpose: str, tunable_fields=(), checks=(), tools=(), applicable_fields=()):
    resource = {
        "key": key,
        "version": "1",
        "ref": _ref(key),
        "kind": kind,
        "modality": modality,
        "purpose": purpose,
        "source_kind": "studio_builtin",
        "provenance": "self_developed",
        "license": "product_owned",
        "compatible_stage_schemas": ["stage.creative.method.v1", "stage.master.propose.v1"] if key in {"studio.video.script", "studio.video.product-script"} else
            ["stage.creative.method.v3"] if key == "studio.text.article-plan" else
            ["stage.creative.method.v1"] if key in OUTPUT_SCHEMAS else
            ["stage.master.propose.v1"] if modality == "text" else
            ["stage.graphic.compose.v1"] if key == "studio.graphic.layout-compose" else
            ["media.generate.stage.v4"] if key == "studio.audio.tts" else
            ["stage.audio.qc.v1"] if key == "studio.audio.qc" else
            ["stage.professional.prepare.v2"] if key == "studio.video.director-package" else [],
        "output_schemas": ["video.script.v1", "video.master.v2"] if key in {"studio.video.script", "studio.video.product-script"} else OUTPUT_SCHEMAS.get(key, ["text.master.v2"] if modality == "text" else
            ["graphic.master.v2"] if key == "studio.graphic.layout-compose" else
            ["stage.media.result.v1"] if key == "studio.audio.tts" else
            ["stage.checks.result.v1"] if key == "studio.audio.qc" else
            ["director.video.v1"] if key == "studio.video.director-package" else []),
        "required_context": ["product_context"] if key in PRODUCT_CONTEXT_SKILLS else ["identity"],
        "requires_selected_upstream": kind == "skill" or key == "studio.graphic.layout-compose",
        "prompt_sections": ["method", "product_context" if key in PRODUCT_CONTEXT_SKILLS else "identity", "stage_instruction", "evidence", "upstream"],
        "tunable_fields": list(tunable_fields),
        "parameter_schema": {"type": "object", "additionalProperties": False,
                             "properties": {field: {**PARAMETER_SCHEMAS[field],
                                 **({"maxLength": 2000} if key == "studio.video.director-package" and field == "instruction" else {})}
                                 for field in tunable_fields}},
        "checks": list(checks),
        "tools": list(tools),
        "bounds": {"max_instruction_chars": 4000, "max_context_bytes": 128 * 1024, "max_output_bytes": 128 * 1024},
    }
    if applicable_fields:
        resource["applicable_fields"] = list(applicable_fields)
    return resource


SKILLS = {
    item["ref"]: item
    for item in (
        _resource("studio.research.evidence-brief", "skill", "research", purpose="把来源、事实和限制整理为可审阅证据简报", tunable_fields=("instruction", "candidate_count")),
        _resource("studio.research.angle-lab", "skill", "research", purpose="从证据中提出可解释的内容角度", tunable_fields=("instruction", "candidate_count")),
        _resource("studio.text.outline", "skill", "text", purpose="把接受的证据和角度组织为结构化大纲", tunable_fields=("instruction", "length")),
        _resource("studio.text.longform", "skill", "text", purpose="生成结构化长文 Master 提案", tunable_fields=("instruction", "length", "candidate_count"), checks=("text_structure", "text_fact")),
        _resource("studio.text.answer", "skill", "text", purpose="生成有证据边界的直接回答", tunable_fields=("instruction", "length"), checks=("text_fact",)),
        _resource("studio.text.social-short", "skill", "text", purpose="生成短内容表达", tunable_fields=("instruction", "length")),
        _resource("studio.text.humanize", "skill", "text", purpose="在不改变事实的前提下精修表达", tunable_fields=("instruction", "tone"), checks=("text_identity",)),
        _resource("studio.text.article-plan", "skill", "text", purpose="一次给出含角度、事实、未知和大纲的完整写作方案", tunable_fields=("instruction", "candidate_count")),
        _resource("studio.text.article-write", "skill", "text", purpose="按选定方案一次写成完整文章并给出备选标题", tunable_fields=("instruction", "length", "candidate_count"),
                  checks=("text_structure", "text_fact", "text_identity", "text_platform")),
        _resource("studio.text.title-hook", "skill", "text", purpose="生成与正文一致的标题和开头候选", tunable_fields=("instruction", "candidate_count"), checks=("text_platform",)),
        _resource("studio.graphic.visual-director", "skill", "graphic", purpose="定义视觉方向而不直接计算像素", tunable_fields=("instruction", "density")),
        _resource("studio.graphic.card-plan", "skill", "graphic", purpose="把视觉方向转为卡片语义计划", tunable_fields=("instruction", "canvas_count")),
        _resource("studio.graphic.image-brief", "skill", "graphic", purpose="为需要的图像槽位生成有边界的素材简报", tunable_fields=("instruction", "aspect_ratio")),
        _resource("studio.graphic.layout-compose", "tool", "graphic", purpose="确定性地把语义卡片计划组合为 graphic.master.v2", tunable_fields=("template", "density"), tools=("studio.graphic.layout-compose@1",)),
        _resource("studio.graphic.qc", "tool", "graphic", purpose="检查真实渲染的尺寸、边界、可读性和素材权利", checks=("graphic_canvas", "graphic_bounds", "graphic_rights"), tools=("studio.graphic.qc@1",)),
        _resource("studio.audio.spoken-adapt", "skill", "audio", purpose="在不改变事实的前提下把文字改成口语稿", tunable_fields=("instruction", "pace")),
        _resource("studio.audio.voice-director", "skill", "audio", purpose="把 Persona 声音偏好转成 TTS 方向", tunable_fields=("instruction", "energy", "pause_policy")),
        _resource("studio.audio.tts", "skill", "audio", purpose="复用 ProviderGenerationTask 执行 TTS", tunable_fields=("voice", "rate")),
        _resource("studio.audio.qc", "tool", "audio", purpose="检查真实音频字节、MIME、时长和可听性", checks=("audio_bytes", "audio_duration", "audio_loudness"), tools=("studio.audio.qc@1",)),
        _resource("studio.video.product-script", "skill", "video", purpose="依据SKU资料生成商品销售脚本", tunable_fields=("instruction", "length")),
        _resource("studio.video.product-shots", "skill", "video", purpose="规划商品连续镜头、关键帧与图生视频素材", tunable_fields=("instruction", "shot_count")),
        _resource("studio.video.product-filming", "skill", "video", purpose="将购买理由和脚本拆成手机可执行的实拍任务书", tunable_fields=("instruction", "shot_count")),
        _resource("studio.product.audience-need", "skill", "video", purpose="把商品已知事实梳理为具体受众、购买情境与最大顾虑",
                  applicable_fields=("primary_audience", "buyer_situation", "main_objection")),
        _resource("studio.product.purchase-reason", "skill", "video", purpose="围绕单一购买理由组织目标、核心表达与行动引导",
                  applicable_fields=("objective", "core_message", "cta")),
        _resource("studio.product.compliance-check", "skill", "video", purpose="定稿前逐句检查带货合规风险并给出改法"),
        _resource("studio.video.script-review", "skill", "video", purpose="四评委逐句评审口播脚本并只改说法"),
        _resource("studio.video.stock-scout", "skill", "video", purpose="为缺素材的镜头找、挑免费素材并标版权"),
        _resource("studio.video.digital-human", "skill", "video", purpose="规划数字人出镜的人物设定、表演与限制（生成功能未上线）"),
        _resource("studio.video.script", "skill", "video", purpose="生成角色化视频脚本", tunable_fields=("instruction", "length")),
        _resource("studio.video.shot-director", "skill", "video", purpose="把脚本拆为镜头和素材计划", tunable_fields=("instruction", "shot_count")),
        _resource("studio.video.director-package", "skill", "video", purpose="生成交给外部专业执行的导演包", tunable_fields=("instruction", "aspect_ratio")),
    )
}

PERSONA_METHOD_TRIAL_KEYS = ('studio.research.evidence-brief', 'studio.research.angle-lab', 'studio.text.outline', 'studio.text.title-hook', 'studio.text.longform', 'studio.text.humanize', 'studio.graphic.card-plan', 'studio.graphic.visual-director', 'studio.graphic.image-brief', 'studio.audio.spoken-adapt', 'studio.audio.voice-director', 'studio.video.script', 'studio.video.shot-director', 'studio.video.director-package')

for _trial_key in PERSONA_METHOD_TRIAL_KEYS:
    _trial_resource = copy.deepcopy(SKILLS[_ref(_trial_key)])
    _trial_resource.update(version="2", ref=_ref(_trial_key, 2))
    if "stage.creative.method.v1" in _trial_resource["compatible_stage_schemas"]:
        _trial_resource["compatible_stage_schemas"].append("stage.creative.method.v2")
    if _trial_key in {"studio.graphic.card-plan", "studio.video.shot-director"}:
        _trial_resource["output_schemas"].append(_trial_resource["output_schemas"][0].replace(".v1", ".v2"))
    SKILLS[_trial_resource["ref"]] = _trial_resource

# Material-aware video planning is a further trial version; @1/@2 stay byte-identical.
for _trial_key in ("studio.video.script", "studio.video.shot-director"):
    _trial_resource = copy.deepcopy(SKILLS[_ref(_trial_key, 2)])
    _trial_resource.update(version="3", ref=_ref(_trial_key, 3))
    SKILLS[_trial_resource["ref"]] = _trial_resource

# Commerce methods absorbed from clipforge (forms, hooks, channels, category shots); @1 stays byte-identical.
for _trial_key in ("studio.video.product-script", "studio.video.product-shots"):
    _trial_resource = copy.deepcopy(SKILLS[_ref(_trial_key)])
    _trial_resource.update(version="2", ref=_ref(_trial_key, 2))
    SKILLS[_trial_resource["ref"]] = _trial_resource


PRESETS = {
    ref: {"key": ref.split("@", 1)[0], "version": "1", "ref": ref, "kind": "style_preset", "source_kind": "studio_builtin", "provenance": "self_developed", "license": "product_owned", "config": config}
    for ref, config in {
        _ref("studio.text.deep-technical"): {"modality": "text", "voice": "evidence_led_engineering", "hype": "low", "specificity": "high"},
        _ref("studio.text.engineering-explainer"): {"modality": "text", "voice": "clear_technical", "hype": "low"},
        _ref("studio.text.observational-lifestyle"): {"modality": "text", "voice": "warm_observational", "hype": "low", "preachiness": "low"},
        _ref("studio.text.reflective-lifestyle"): {"modality": "text", "voice": "grounded_reflection", "hype": "low"},
        _ref("studio.text.concise-social"): {"modality": "text", "voice": "concise_specific", "hype": "low"},
        _ref("studio.graphic.technical-editorial"): {"modality": "graphic", "palette": "technical_editorial", "density": "medium", "image_fallback": "blocked"},
        _ref("studio.graphic.architecture-diagram"): {"modality": "graphic", "palette": "architecture", "density": "medium", "image_fallback": "shape_only"},
        _ref("studio.graphic.clean-infographic"): {"modality": "graphic", "palette": "clean", "density": "medium", "image_fallback": "shape_only"},
        _ref("studio.graphic.warm-magazine"): {"modality": "graphic", "palette": "warm_magazine", "density": "low", "image_fallback": "blocked"},
        _ref("studio.graphic.documentary-photo"): {"modality": "graphic", "palette": "documentary", "density": "low", "image_fallback": "blocked"},
        _ref("studio.graphic.lifestyle-cards"): {"modality": "graphic", "palette": "lifestyle", "density": "low", "image_fallback": "shape_only"},
        _ref("studio.graphic.product-neutral"): {"modality": "graphic", "product_consistency": "original_references", "motion": "one_action_per_shot"},
        _ref("studio.audio.calm-engineer"): {"modality": "audio", "voice": "calm_clear", "pace": "medium", "energy": "steady"},
        _ref("studio.audio.clear-explainer"): {"modality": "audio", "voice": "clear_explainer", "pace": "medium", "energy": "clear"},
        _ref("studio.audio.warm-conversational"): {"modality": "audio", "voice": "warm_conversational", "pace": "medium", "energy": "warm"},
        _ref("studio.audio.reflective-story"): {"modality": "audio", "voice": "reflective_story", "pace": "slow_medium", "energy": "gentle"},
    }.items()
}

QUALITY = {
    ref: {"key": ref.split("@", 1)[0], "version": "1", "ref": ref, "kind": "quality_profile", "source_kind": "studio_builtin", "provenance": "self_developed", "license": "product_owned", "checks": checks, "human_review_required": True}
    for ref, checks in {
        _ref("studio.quality.video.product"): ["product_evidence", "product_consistency", "shot_continuity", "sound_clarity", "purchase_reason", "truthful_cta"],
        _ref("studio.quality.text.technical"): ["text_structure", "text_fact", "text_identity", "text_anti_hype"],
        _ref("studio.quality.text.lifestyle"): ["text_structure", "text_fact_speculation", "text_identity", "text_anti_clickbait"],
        _ref("studio.quality.graphic.editorial"): ["graphic_canvas", "graphic_bounds", "graphic_readability", "graphic_rights"],
        _ref("studio.quality.graphic.lifestyle"): ["graphic_canvas", "graphic_bounds", "graphic_readability", "graphic_rights"],
        _ref("studio.quality.audio.explainer"): ["audio_bytes", "audio_duration", "audio_loudness", "audio_voice_contract"],
        _ref("studio.quality.audio.conversational"): ["audio_bytes", "audio_duration", "audio_loudness", "audio_voice_contract"],
    }.items()
}

TEXT_RULES = {
    "studio.quality.text.technical@1": {
        "blocked_phrases": ["颠覆一切", "百分之百保证", "稳赚不赔", "躺赚"],
        "warning_phrases": ["王炸", "赋能一切", "必看", "无敌"],
        "citation_required_for_numeric_claims": True,
        "critic_dimensions": ["factual_grounding", "engineering_fit", "clarity", "specificity", "tradeoffs"],
    },
    "studio.quality.text.lifestyle@1": {
        "blocked_phrases": ["不看后悔一辈子", "震惊所有人", "百分之百保证"],
        "warning_phrases": ["所有人都该", "人生的意义就是", "这才是人生", "你一定要"],
        "citation_required_for_numeric_claims": True,
        "critic_dimensions": ["factual_grounding", "naturalness", "specificity", "non_preachy", "title_alignment"],
    },
}
for _quality_ref, _rules in TEXT_RULES.items():
    QUALITY[_quality_ref]["rules"] = _rules
    QUALITY[_quality_ref]["thresholds"] = {"empty_sections": "blocker", "repeated_paragraphs": "warning",
        "numeric_claim_without_citation": "blocker", "critic": "advisory_only"}
    QUALITY[_quality_ref]["critic_contract"] = "advisory.rubric.v1"
QUALITY["studio.quality.text.lifestyle@1"]["thresholds"].update(
    fact_speculation="bounded_prediction_label_v1", title_body_alignment="bounded_numeric_detail_v1",
    generic_reflection="bounded_two_phrases_without_observation_v1")


def _frontmatter(text: str) -> tuple[dict, str]:
    parts = text.split("---", 2)
    if len(parts) != 3 or parts[0].strip():
        raise ValueError("studio_skill_frontmatter_invalid")
    metadata = {}
    for line in parts[1].strip().splitlines():
        key, separator, value = line.partition(":")
        if not separator or key in metadata or not value.strip():
            raise ValueError("studio_skill_frontmatter_invalid")
        metadata[key.strip()] = value.strip()
    return metadata, parts[2].strip()


def load_skill(ref: str) -> dict:
    """Read only a selected, product-owned package; documentation is never executable."""
    from .content_harness.registry import registry
    from .stage_contracts import canonical

    validate_ref(ref, kind="skill")
    resource = SKILLS[ref]
    root = Path(__file__).resolve().parents[1] / "studio_skills"
    directory = root / resource["key"] / ("v" + resource["version"])
    def read(name):
        path = directory / name
        if not path.is_file() or path.is_symlink() or path.resolve().parent != directory.resolve():
            raise ValueError("studio_skill_package_unavailable")
        if path.stat().st_size > 32 * 1024:
            raise ValueError("studio_skill_package_bound")
        return path.read_text(encoding="utf-8")
    metadata, instruction = _frontmatter(read("SKILL.md"))
    provenance, _ = _frontmatter(read("STUDIO-META.md"))
    try:
        contract = canonical(json.loads(read("STUDIO-CONTRACT.json")), max_bytes=32 * 1024)
    except (TypeError, ValueError):
        raise ValueError("studio_skill_contract_invalid") from None
    if metadata != {"key": resource["key"], "version": resource["version"], "source_kind": "studio_builtin"}:
        raise ValueError("studio_skill_frontmatter_invalid")
    if (provenance.get("classification") not in {"self_developed", "adapted", "method_reference", "vendored"}
            or provenance.get("license") != "product_owned" or provenance.get("vendored_code") != "none"):
        raise ValueError("studio_skill_provenance_invalid")
    if contract.get("schema") != "studio.skill.contract.v1" or any(contract.get(key) != resource[key] for key in resource):
        raise ValueError("studio_skill_contract_drift")
    if (len(instruction) < 120 or len(instruction) > 4000
            or type(contract.get("references")) is not list or len(contract["references"]) > 8
            or type(contract.get("optional_tools")) is not list or len(contract["optional_tools"]) > 8):
        raise ValueError("studio_skill_contract_invalid")
    canonical({"instruction": instruction, "provenance": provenance}, max_bytes=16 * 1024)
    for field, kind in (("style_compatibility", "style_preset"), ("quality_compatibility", "quality_profile")):
        values = contract.get(field)
        if type(values) is not list or not values or len(values) > 20:
            raise ValueError("studio_skill_contract_invalid")
        for value in values:
            validate_ref(value, kind=kind)
    from .content_harness.nodes import bootstrap_builtin_nodes
    from .content_harness.registry import RegistryKinds

    bootstrap_builtin_nodes()
    for schema in contract["compatible_stage_schemas"]:
        matches = [item for item in registry.list("node")
            if item.stage_contract is not None and item.stage_contract.to_dict()["stage_schema"] == schema]
        if len(matches) != 1:
            raise ValueError("studio_skill_stage_unavailable")
        plugin = registry.resolve("node", matches[0].key, matches[0].version)
        if not set(contract["tunable_fields"]).issubset(plugin.stage_consumed_fields):
            raise ValueError("studio_skill_parameter_not_consumed")
    unavailable_tools = []
    for optional, refs in ((False, contract["tools"]), (True, contract["optional_tools"])):
        for tool_ref in refs:
            if type(tool_ref) is not str or not REF_RE.fullmatch(tool_ref):
                raise ValueError("studio_skill_tool_ref_invalid")
            key, version = tool_ref.rsplit("@", 1)
            matches = [item for kind in RegistryKinds for item in registry.list(kind) if item.key == key and item.version == version]
            if not matches and not optional:
                raise ValueError("studio_skill_required_tool_unavailable")
            if not matches:
                unavailable_tools.append({"ref": tool_ref, "reason": "optional_tool_unregistered"})
            if matches and resource["kind"] == "tool":
                executor = registry.resolve(matches[0].kind, key, version)
                if not set(contract["tunable_fields"]).issubset(getattr(executor, "consumed_fields", ())):
                    raise ValueError("studio_skill_parameter_not_consumed")
    references = []
    for name in contract["references"]:
        if (type(name) is not str or not name.startswith("references/") or "\\" in name
                or any(part in {"", ".", ".."} for part in name.split("/"))):
            raise ValueError("studio_skill_reference_path_invalid")
        path = directory / name
        if (not path.is_file() or any(parent.is_symlink() for parent in (path, *path.parents) if parent != directory.parent)
                or not path.resolve().is_relative_to(directory.resolve()) or path.stat().st_size > 16 * 1024):
            raise ValueError("studio_skill_reference_unavailable")
        content = path.read_text(encoding="utf-8")
        canonical({"content": content}, max_bytes=20 * 1024)
        references.append({"name": name, "content": content, "hash": digest(content)})
    package = {"instruction": instruction, "contract": contract, "provenance": provenance}
    if references:
        package["references"] = references
    if unavailable_tools:
        package["unavailable_optional_tools"] = unavailable_tools
    return {**package, "package_hash": digest(package)}


def freshness_projection(boundary: dict | None, mode: str, *, now=None, max_age_hours: int = 168) -> dict:
    if mode not in {"grounded", "current", "reflection", "speculation"} or type(max_age_hours) is not int or not 1 <= max_age_hours <= 720:
        raise ValueError("creative_fact_mode_invalid")
    now = now or datetime.now(UTC)
    # A same-day as_of in the operator's timezone is not future evidence; the cutoff is the end of that local day.
    local = now.astimezone()
    local_day_end = datetime.combine(local.date(), time.max, tzinfo=local.tzinfo).astimezone(UTC)
    eligible = []
    for item in (boundary or {}).get("items", []):
        snapshot = item.get("snapshot") or {}
        if (item.get("kind") not in {"fact", "event"} or item.get("fresh_source_verified") is not True
                or type(snapshot.get("source_id")) is not int or snapshot["source_id"] <= 0):
            continue
        as_of = snapshot.get("as_of")
        try:
            observed = datetime.fromisoformat(as_of) if type(as_of) is str else None
            if observed is not None:
                observed = observed.replace(tzinfo=UTC) if observed.tzinfo is None else observed
                if now - timedelta(hours=max_age_hours) <= observed <= local_day_end:
                    eligible.append({"item_id": item["item_id"], "checksum": item["checksum"], "as_of": as_of})
        except ValueError:
            continue
    return {"mode": mode, "max_age_hours": max_age_hours, "fresh_refs": eligible,
        "ready": mode != "current" or bool(eligible), "current_facts_permitted": mode == "current" and bool(eligible),
        "reason": "fresh_current_evidence_required" if mode == "current" and not eligible else None}


def text_quality(ref: str, payload: dict) -> dict:
    from .text_documents import canonical_payload, plain_text, text_map

    validate_ref(ref, kind="quality_profile")
    if ref not in TEXT_RULES:
        raise ValueError("creative_text_quality_profile_invalid")
    payload = canonical_payload(payload)
    document, rules = payload["document"], TEXT_RULES[ref]
    body = plain_text(document)
    segments = text_map(document)["segments"]
    issues = []
    title = payload.get("title", "")
    for severity, field in (("blocker", "blocked_phrases"), ("warning", "warning_phrases")):
        for phrase in rules[field]:
            if phrase in title or phrase in body:
                issues.append({"severity": severity, "reason": "persona_phrase_rule", "span": phrase})
    seen = set()
    for segment in segments:
        text = segment["text"].strip()
        if len(text) >= 30 and text in seen:
            issues.append({"severity": "warning", "reason": "persona_repeated_paragraph", "block_id": segment["block_id"]})
        seen.add(text)
    for index, block in enumerate(document["blocks"]):
        if block["type"] == "heading" and (index + 1 == len(document["blocks"]) or document["blocks"][index + 1]["type"] == "heading"):
            issues.append({"severity": "blocker", "reason": "persona_empty_section", "block_id": block["id"]})
    numeric_claim = re.compile(r"(?:\b20\d{2}[-年/]\d{1,2}|\d+(?:\.\d+)?\s*(?:%|％|亿元|万元|秒|倍))")
    for segment in segments:
        if segment["block_type"] == "code" or not rules["citation_required_for_numeric_claims"]:
            continue
        citations = [item for item in document["citations"] if item["block_id"] == segment["block_id"]
            and item.get("list_item_id") == segment.get("list_item_id")]
        for match in numeric_claim.finditer(segment["text"]):
            if not any(item["start"] <= match.start() and item["end"] >= match.end() for item in citations):
                locator = {"block_id": segment["block_id"], "start": match.start(), "end": match.end()}
                if segment.get("list_item_id"):
                    locator["list_item_id"] = segment["list_item_id"]
                issues.append({"severity": "blocker", "reason": "persona_numeric_claim_citation_missing", **locator})
    lifestyle = ref == "studio.quality.text.lifestyle@1"
    if lifestyle:
        for segment in segments:
            if segment["block_type"] == "code":
                continue
            text = segment["text"]
            if (re.search(r"(?:未来|将来|接下来).{0,40}(?:必然|一定会|肯定会)", text)
                    and not re.search(r"(?:推测|假设|我猜|可能|设想)", text)):
                issues.append({"severity": "warning", "reason": "persona_unlabeled_prediction", "block_id": segment["block_id"]})
        title_numbers = {match.group() for match in numeric_claim.finditer(title)}
        for value in sorted(title_numbers):
            if value not in body:
                issues.append({"severity": "warning", "reason": "persona_title_detail_not_in_body", "span": value})
        generic = [phrase for phrase in ("生活就是一场", "人生的意义在于", "珍惜每一个瞬间", "做最好的自己") if phrase in body]
        if len(generic) >= 2 and not document["citations"] and not re.search(r"(?:昨天|今早|午后|走进|坐在|我看到|我听到|那家|这条街)", body):
            issues.append({"severity": "warning", "reason": "persona_generic_reflection_without_observation", "span": generic[0]})
    quality = QUALITY[ref]
    return {"status": "blocker" if any(item["severity"] == "blocker" for item in issues) else "warning" if issues else "pass",
        "quality_profile_ref": ref, "quality_profile_hash": digest(quality), "payload_hash": digest(payload),
        "issues": issues, "human_review_required": True,
        "critic_dimensions": rules["critic_dimensions"],
        "coverage": {"deterministic": "bounded_phrase_structure_citation_rules", "semantic": "not_run",
            "title_body_alignment": "bounded_numeric_detail_only" if lifestyle else "human_review_required",
            "fact_speculation": "bounded_prediction_label_rule" if lifestyle else "existing_text_fact_check",
            "factual_truth": "existing_text_fact_check"}}


def _profile(mode: str, skill: str, preset: str, quality: str, *, capability: str, recipe: str, model_binding=None):
    modality = skill.split(".")[1]
    return {
        "schema": f"persona.creative.{modality}.v1", "mode": mode, "skill_ref": _ref(skill),
        "style_preset_ref": _ref(preset), "quality_profile_ref": _ref(quality),
        "capability": capability, "model_binding": model_binding,
        "model_chain": [], "capability_memory_revision_ids": [], "installed_skill_refs": [],
        "parameters": {}, "stage_instruction": None,
        "provenance": {"blueprint_key": None, "blueprint_version": None, "default_recipe_key": recipe},
    }


BLUEPRINTS = {
    "starter.ai-tech-engineer.v1": {
        "key": "starter.ai-tech-engineer.v1", "name": "AI科技研发技术博主", "version": "1",
        "positioning": "AI Agent、软件架构与开发工具的工程实践型内容角色",
        "target_audience": ["开发者", "技术负责人", "关注 AI 工程化的人"],
        "content_domains": ["AI Agent", "软件架构", "开发工具", "工程实践"],
        "expression_style": {"voice": "engineering_first", "hype": "low", "tradeoffs": "explicit", "evidence": "required"},
        "visual_language": {"preset": "technical_editorial", "diagram_first": True, "density": "medium"},
        "content_boundaries": ["不夸大能力", "明确限制和 trade-off", "事实与推测分开"],
        "risk_boundaries": ["不伪造 benchmark", "不把未验证模型输出当事实"],
        "public_fact_policy": {"fresh_source_required_for_current_claims": True, "label_speculation": True},
        "text_creative_profile": _profile("auto", "studio.text.longform", "studio.text.deep-technical", "studio.quality.text.technical", capability="chat", recipe="persona.text.ai-tech.v1"),
        "graphic_creative_profile": _profile("auto", "studio.graphic.visual-director", "studio.graphic.architecture-diagram", "studio.quality.graphic.editorial", capability="image_generation", recipe="persona.graphic.ai-tech.v1"),
        "audio_creative_profile": _profile("auto", "studio.audio.tts", "studio.audio.calm-engineer", "studio.quality.audio.explainer", capability="tts", recipe="persona.audio.ai-tech.v1"),
        "video_creative_profile": _profile("auto", "studio.video.director-package", "studio.graphic.technical-editorial", "studio.quality.text.technical", capability="chat", recipe="persona.video.ai-tech.v1"),
    },
    "starter.lifestyle-observer.v1": {
        "key": "starter.lifestyle-observer.v1", "name": "日常生活方式博主", "version": "1",
        "positioning": "观察正在发生的有趣事情、未来变化与日常生活感受的内容角色",
        "target_audience": ["对生活变化好奇的人", "希望获得具体观察的普通读者"],
        "content_domains": ["日常生活", "新鲜变化", "个人观察", "近未来趣事"],
        "expression_style": {"voice": "warm_observational", "hype": "low", "preachiness": "low", "specificity": "high"},
        "visual_language": {"preset": "warm_magazine", "documentary": True, "density": "low"},
        "content_boundaries": ["不说教", "不制造焦虑", "事实与个人感受分开"],
        "risk_boundaries": ["当前事实必须有 fresh source", "未来内容明确标注推测"],
        "public_fact_policy": {"fresh_source_required_for_current_claims": True, "label_speculation": True},
        "text_creative_profile": _profile("auto", "studio.text.longform", "studio.text.observational-lifestyle", "studio.quality.text.lifestyle", capability="chat", recipe="persona.text.lifestyle.v1"),
        "graphic_creative_profile": _profile("auto", "studio.graphic.visual-director", "studio.graphic.warm-magazine", "studio.quality.graphic.lifestyle", capability="image_generation", recipe="persona.graphic.lifestyle.v1"),
        "audio_creative_profile": _profile("auto", "studio.audio.tts", "studio.audio.warm-conversational", "studio.quality.audio.conversational", capability="tts", recipe="persona.audio.lifestyle.v1"),
        "video_creative_profile": _profile("auto", "studio.video.director-package", "studio.graphic.warm-magazine", "studio.quality.text.lifestyle", capability="chat", recipe="persona.video.lifestyle.v1"),
    },
}


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate_ref(value: Any, *, kind: str | None = None) -> str:
    if not isinstance(value, str) or not REF_RE.fullmatch(value):
        raise ValueError("creative_resource_ref_invalid")
    pools = {"skill": SKILLS, "style_preset": PRESETS, "quality_profile": QUALITY}
    if kind and value not in pools[kind]:
        raise ValueError("creative_resource_ref_unavailable")
    if not kind and value not in set().union(SKILLS, PRESETS, QUALITY):
        raise ValueError("creative_resource_ref_unavailable")
    return value


PRODUCTION_STAGES = [
    {"id": key, "title": title, "order": index, "modalities": modalities}
    for index, (key, title, modalities) in enumerate([
        ("research", "选题与证据", ["text", "graphic", "audio", "video"]),
        ("script", "文案与脚本", ["text", "graphic", "audio", "video"]),
        ("voice", "配音与声音准备", ["audio", "video"]),
        ("storyboard", "分镜与素材", ["graphic", "video"]),
        ("sound_edit", "声音粗剪", ["audio", "video"]),
        ("picture_edit", "画面粗剪与节奏", ["video"]),
        ("subtitle_color", "字幕与校色", ["video"]),
        ("packaging", "后期包装", ["video"]),
        ("finish", "终混与导出", ["audio", "video"]),
        ("review", "质量评审与回收", ["text", "graphic", "audio", "video"]),
    ])
]


def validate_production_stages(value):
    from .stage_contracts import _validate, canonical

    if type(value) is not dict or set(value) - {item["id"] for item in PRODUCTION_STAGES}:
        raise ValueError("production_stages_invalid")
    canonical(value, max_bytes=16 * 1024)
    for stage in value.values():
        if (type(stage) is not dict or set(stage) != {"enabled", "methods"}
                or type(stage["enabled"]) is not bool or type(stage["methods"]) is not list
                or len(stage["methods"]) > 12):
            raise ValueError("production_stage_invalid")
        identifiers = set()
        for method in stage["methods"]:
            if type(method) is not dict:
                raise ValueError("production_method_invalid")
            kind = method.get("source_kind")
            if type(kind) is not str:
                raise ValueError("production_method_invalid")
            refs = {"studio_builtin": {"skill_ref"}, "capability_memory": {"artifact_id", "revision_id"},
                    "installed_agent_skill": {"skill_id", "version"}}.get(kind)
            if (refs is None or set(method) != {"id", "source_kind", "enabled", "parameters"} | refs
                    or type(method.get("enabled")) is not bool or type(method.get("parameters")) is not dict
                    or len(method["parameters"]) > 30 or not isinstance(method.get("id"), str)
                    or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,99}", method["id"])
                    or method["id"] in identifiers):
                raise ValueError("production_method_invalid")
            identifiers.add(method["id"])
            canonical(method["parameters"], max_bytes=4000)
            if kind == "studio_builtin":
                validate_ref(method["skill_ref"], kind="skill")
                _validate(method["parameters"], SKILLS[method["skill_ref"]]["parameter_schema"])
            elif kind == "capability_memory":
                if any(type(method[key]) is not int or method[key] < 1 for key in refs):
                    raise ValueError("production_method_revision_invalid")
            elif any(not isinstance(method[key], str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:@-]{0,199}", method[key]) for key in refs):
                raise ValueError("production_method_installed_invalid")
    return copy.deepcopy(value)


def validate_creative_profile(value: Any) -> dict:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) - {
        "schema", "mode", "skill_ref", "style_preset_ref", "quality_profile_ref", "capability",
        "model_binding", "model_chain", "capability_memory_revision_ids", "installed_skill_refs",
        "parameters", "stage_instruction", "provenance", "production_stages",
    }:
        raise ValueError("creative_profile_invalid")
    from fastapi import HTTPException

    from .capability_contracts import text as safe_method_text
    from .creative_intents import contains_secret_text
    from .stage_contracts import _validate, canonical

    # Validate the entire identity object before it can enter a snapshot or prompt.
    canonical(value, max_bytes=16 * 1024)

    def safe_strings(item):
        if isinstance(item, dict):
            for key, child in item.items():
                safe_method_text(key, 150)
                safe_strings(child)
        elif isinstance(item, list):
            for child in item:
                safe_strings(child)
        elif isinstance(item, str):
            scanned = unicodedata.normalize("NFKC", item)
            for _ in range(3):
                scanned = unicodedata.normalize("NFKC", unquote(scanned))
            if contains_secret_text(scanned):
                raise ValueError("creative_profile_unsafe_content")
            url_pattern = r"https?://[^\s\"'<>（）()，。；]+"
            for match in re.finditer(url_pattern, scanned, re.IGNORECASE):
                try:
                    if "\\" in match.group():
                        raise ValueError("creative_profile_unsafe_content")
                    parsed = urlsplit(match.group())
                    if not parsed.hostname or parsed.username is not None:
                        raise ValueError("creative_profile_unsafe_content")
                except ValueError:
                    raise ValueError("creative_profile_unsafe_content") from None
            # HTTP scheme colons are not Windows drives; credentials are checked above.
            safe_method_text(re.sub(r"https?:", "http", scanned, flags=re.IGNORECASE), 16 * 1024)
            local_text = re.sub(url_pattern, "[public-url]", scanned, flags=re.IGNORECASE)
            if re.search(r"(?<![A-Za-z0-9_/.-])/(?!/)[^\s\"'<>，。；）]+|\\\\[^\s\\]+\\", local_text):
                raise ValueError("creative_profile_unsafe_content")

    try:
        safe_strings(value)
    except HTTPException:
        raise ValueError("creative_profile_unsafe_content") from None
    schemas = {f"persona.creative.{modality}.v1" for modality in ("text", "graphic", "audio", "video")}
    if value.get("schema") not in schemas or value.get("mode") not in {"auto", "custom", "composed"}:
        raise ValueError("creative_profile_invalid")
    for field, kind in (("skill_ref", "skill"), ("style_preset_ref", "style_preset"), ("quality_profile_ref", "quality_profile")):
        validate_ref(value.get(field), kind=kind)
    modality = value["schema"].split(".")[2]
    if SKILLS[value["skill_ref"]]["modality"] != modality:
        raise ValueError("creative_profile_modality_mismatch")
    if PRESETS[value["style_preset_ref"]]["config"]["modality"] != ("graphic" if modality == "video" else modality):
        raise ValueError("creative_profile_preset_mismatch")
    # Video planning retains its existing script-quality profiles, not a new final-video QC.
    quality_modality = "text" if modality == "video" else modality
    if not QUALITY[value["quality_profile_ref"]]["key"].startswith(f"studio.quality.{quality_modality}.") and not (modality == "video" and value["quality_profile_ref"] == "studio.quality.video.product@1"):
        raise ValueError("creative_profile_quality_mismatch")
    if value.get("capability") not in {"chat", "image_generation", "tts", "video_generation", "asr"}:
        raise ValueError("creative_profile_capability_invalid")
    binding = value.get("model_binding")
    chain = value.get("model_chain", [])
    if value["mode"] == "auto" and binding is not None:
        raise ValueError("creative_profile_binding_invalid")
    if value["mode"] == "custom" and (not isinstance(binding, dict) or set(binding) != {"provider", "model", "profile"}):
        raise ValueError("creative_profile_custom_binding_required")
    if value["mode"] == "composed" and (binding is not None and (not isinstance(binding, dict) or set(binding) != {"provider", "model", "profile"})):
        raise ValueError("creative_profile_binding_invalid")
    if not isinstance(chain, list) or len(chain) > 8 or chain and value["mode"] != "composed":
        raise ValueError("creative_profile_chain_invalid")
    for item in ([binding] if binding is not None else []) + chain:
        if (not isinstance(item, dict) or set(item) != {"provider", "model", "profile"}
                or any(not isinstance(item[key], str) or not BINDING_ID_RE.fullmatch(item[key]) for key in item)):
            raise ValueError("creative_profile_binding_invalid")
    if chain and binding is None:
        raise ValueError("creative_profile_binding_invalid")
    memory = value.get("capability_memory_revision_ids", [])
    if not isinstance(memory, list) or len(memory) > 8 or any(type(item) is not int or item <= 0 for item in memory):
        raise ValueError("creative_profile_memory_refs_invalid")
    installed = value.get("installed_skill_refs", [])
    if (not isinstance(installed, list) or len(installed) > 8
            or any(not isinstance(item, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:@-]{0,199}", item)
                   for item in installed)):
        raise ValueError("creative_profile_installed_refs_invalid")
    if "production_stages" in value:
        validate_production_stages(value["production_stages"])
    params = value.get("parameters", {})
    if (not isinstance(params, dict) or len(params) > 32
            or set(params) - set(SKILLS[value["skill_ref"]]["tunable_fields"])):
        raise ValueError("creative_profile_parameters_invalid")
    canonical(params, max_bytes=4000)
    _validate(params, SKILLS[value["skill_ref"]]["parameter_schema"])
    if any(type(item) is str and (SAFE_TEXT_RE.search(item) or re.search(r"(?:[A-Za-z]:\\|file://|^/)", item))
           for item in params.values()):
        raise ValueError("creative_profile_parameters_invalid")
    text = value.get("stage_instruction")
    if text is not None and (not isinstance(text, str) or len(text) > 4000 or SAFE_TEXT_RE.search(text)):
        raise ValueError("creative_profile_instruction_invalid")
    provenance = value.get("provenance", {})
    if not isinstance(provenance, dict) or set(provenance) - {"blueprint_key", "blueprint_version", "default_recipe_key"}:
        raise ValueError("creative_profile_provenance_invalid")
    for key, item in provenance.items():
        pattern = r"[1-9][0-9]{0,5}" if key == "blueprint_version" else r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,149}"
        if item is not None and (not isinstance(item, str) or not re.fullmatch(pattern, item)):
            raise ValueError("creative_profile_provenance_invalid")
    return copy.deepcopy(value)


def inventory() -> dict:
    skills = copy.deepcopy(list(SKILLS.values()))
    for item in skills:
        item["system"] = skill_system(item["key"])
        connected = bool(item["compatible_stage_schemas"] or item["kind"] == "tool" and item["tools"])
        item["execution_support"] = {"status": "connected_not_probed" if connected else "partial",
            "reason": None if connected else "stage_execution_not_connected"}
    return {
        "schema": "studio.creative.inventory.v1",
        "skills": skills,
        "production_stages": copy.deepcopy(PRODUCTION_STAGES),
        "style_presets": copy.deepcopy(list(PRESETS.values())),
        "quality_profiles": copy.deepcopy(list(QUALITY.values())),
        "starter_personas": [
            {"key": item["key"], "name": item["name"], "version": item["version"], "checksum": digest(item)}
            for item in BLUEPRINTS.values()
        ],
    }


def blueprint(key: str) -> dict:
    try:
        return copy.deepcopy(BLUEPRINTS[key])
    except KeyError:
        raise ValueError("starter_blueprint_not_found") from None


def blueprint_preview(key: str) -> dict:
    item = blueprint(key)
    return {"schema": "starter.persona.preview.v1", "key": key, "version": item["version"], "name": item["name"], "checksum": digest(item), "profile": item}
