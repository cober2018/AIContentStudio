"""Rule Registry（D13）：代码级确定性规则，不用 LLM。

RuleSet 以 key 引用（Channel Profile / Workflow config）；本模块内置首批规则：
fact 绑定、媒体必需/权利/顺序、平台必备字段。财务/技术/SEO 规则在 Phase 3 扩充。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from sqlalchemy.orm import Session

from ...models import Draft
from .contracts import RuleResult
from .registry import registry


class Rule(Protocol):
    key: str
    version: str

    def evaluate(self, db: Session, ctx: dict[str, Any]) -> RuleResult: ...


@dataclass
class RuleContext:
    """规则求值上下文：draft + 解析后的 ContentFormSpec dict + profile media_requirements。"""

    draft: Draft
    channel: str = ""
    content_form: str = ""
    media_requirements: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "draft": self.draft,
            "channel": self.channel,
            "content_form": self.content_form,
            "media_requirements": self.media_requirements,
        }


def _has_real_bytes(media) -> bool:
    """真实媒体判定（D10/D11）：字节在 DraftMedia 或其 MaterialRevision 上，且不是 SVG placeholder。"""
    if (media.metadata_json or {}).get("placeholder"):
        return False
    mime = (media.mime_type or "").lower()
    if "svg" in mime:
        return False
    if media.file_path:
        return True
    revision = media.material_revision
    return bool(revision and revision.file_path and "svg" not in (revision.mime_type or "").lower())


def effective_media_rights(media) -> str | None:
    """统一权利判定（R4-B3）：DraftMedia use 行 + MaterialRevision 全局状态同时检查。

    返回 None = 权利完整；否则返回问题来源：
    - "use_revoked"：本稿 use 行被撤权（public_use_allowed/revoked_at）；
    - "use_unauthorized"：use 行未显式授权公开使用；
    - "no_rights_status"：use 行缺 rights_status；
    - "revision_revoked"：素材库全局撤权（revision status=revoked / public_use_allowed=False）。

    Rule（rule.media.public_rights）、Candidate readiness、Delivery live gate 共用，
    保证「全局撤权的素材在任何一层都进不了 Approved Candidate」。
    """
    if media.public_use_revoked_at is not None:
        return "use_revoked"
    if media.public_use_allowed is not True:
        return "use_unauthorized"
    if not media.rights_status:
        return "no_rights_status"
    revision = media.material_revision
    if revision is not None and (revision.status == "revoked" or revision.public_use_allowed is not True):
        return "revision_revoked"
    return None


# ---------- 内置规则 ----------


class FactBoundRule:
    key = "rule.fact.bound"
    version = "1"

    def evaluate(self, db: Session, ctx: dict) -> RuleResult:
        draft: Draft = ctx["draft"]
        structured = draft.structured_json or {}
        pack = draft.content_job.topic_brief.fact_pack
        pack_ids = {f"E{item.id:03d}" for item in pack.items} | {f"F{item.fact_id:03d}" for item in pack.items if item.fact_id}
        used: list[str] = []
        for scene in structured.get("scenes", []) or []:
            used.extend(scene.get("fact_ids", []) or [])
        for claim in structured.get("claim_fact_map", []) or []:
            used.extend(claim.get("fact_ids", []) or [])
        invalid = [fid for fid in used if fid not in pack_ids]
        status = "blocker" if invalid else "pass"
        return RuleResult(key=self.key, version=self.version, status=status, details={"invalid_fact_ids": invalid})


class MediaRequiredRule:
    """profile.media_requirements: {"cover": "required", "inline": "optional"}；placeholder 不算成品。"""

    key = "rule.media.required"
    version = "1"

    def evaluate(self, db: Session, ctx: dict) -> RuleResult:
        draft: Draft = ctx["draft"]
        requirements = ctx.get("media_requirements") or {}
        problems: list[str] = []
        if requirements.get("cover") == "required":
            covers = [m for m in draft.media if m.role == "cover"]
            if not covers:
                problems.append("missing_cover")
            elif not any(_has_real_bytes(m) for m in covers):
                problems.append("cover_has_no_actual_media")
        if requirements.get("inline") == "required" and not any(_has_real_bytes(m) for m in draft.media if m.role == "inline"):
            problems.append("missing_actual_inline_media")
        # 通用：声称 image artifact 的稿子必须有真实媒体（placeholder/Prompt 不算）
        if (draft.artifact_kind or "text") == "image" and not any(_has_real_bytes(m) for m in draft.media):
            problems.append("image_artifact_without_actual_media")
        status = "blocker" if problems else "pass"
        return RuleResult(key=self.key, version=self.version, status=status, details={"problems": problems})


class MediaPublicRightsRule:
    key = "rule.media.public_rights"
    version = "1"

    def evaluate(self, db: Session, ctx: dict) -> RuleResult:
        draft: Draft = ctx["draft"]
        bad = [
            {"media_id": m.id, "reason": reason}
            for m in draft.media
            if (reason := effective_media_rights(m)) is not None
        ]
        return RuleResult(
            key=self.key, version=self.version,
            status="blocker" if bad else "pass",
            details={"media_without_public_rights": [b["media_id"] for b in bad], "reasons": {b["media_id"]: b["reason"] for b in bad}},
        )


class MediaOrderRule:
    key = "rule.media.order"
    version = "1"

    def evaluate(self, db: Session, ctx: dict) -> RuleResult:
        draft: Draft = ctx["draft"]
        orders = sorted(m.sort_order for m in draft.media)
        contiguous = orders == list(range(len(orders)))
        return RuleResult(
            key=self.key, version=self.version,
            status="warning" if (orders and not contiguous) else "pass",
            details={"sort_orders": orders},
        )


class PlatformRequiredFieldsRule:
    """平台必备字段：thread 形态必须有推串边界；structured 声明的必备键必须存在。"""

    key = "rule.platform.required_fields"
    version = "1"

    def evaluate(self, db: Session, ctx: dict) -> RuleResult:
        draft: Draft = ctx["draft"]
        form = ctx.get("content_form") or ""
        problems: list[str] = []
        if form == "thread" and not draft.thread_posts_json:
            problems.append("missing_thread_boundaries")
        if form == "article" and not (draft.title or "").strip():
            problems.append("missing_title")
        status = "blocker" if problems else "pass"
        return RuleResult(key=self.key, version=self.version, status=status, details={"problems": problems})


_BUILTIN_RULES = [
    FactBoundRule(),
    MediaRequiredRule(),
    MediaPublicRightsRule(),
    MediaOrderRule(),
    PlatformRequiredFieldsRule(),
]

_registered = False


def bootstrap_rules() -> None:
    global _registered
    if _registered:
        return
    for rule in _BUILTIN_RULES:
        if rule.key not in {d.key for d in registry.list("rule")}:
            registry.register("rule", rule.key, rule.version, rule)
    from .domain_rules import bootstrap_domain_rules
    from .seo_rules import SeoRequiredFieldsRule

    if SeoRequiredFieldsRule.key not in {d.key for d in registry.list("rule")}:
        registry.register("rule", SeoRequiredFieldsRule.key, SeoRequiredFieldsRule.version, SeoRequiredFieldsRule())
    bootstrap_domain_rules(registry)
    _registered = True


def evaluate_rule_set(db: Session, rule_keys: list[str], ctx: RuleContext) -> list[RuleResult]:
    """按 key 列表求值 RuleSet；未知 key 记 incomplete（不静默跳过）。"""
    bootstrap_rules()
    results: list[RuleResult] = []
    payload = ctx.as_dict()
    for key in rule_keys or []:
        try:
            rule = registry.resolve("rule", key, None)
            results.append(rule.evaluate(db, payload))
        except Exception as exc:  # noqa: BLE001
            results.append(RuleResult(key=key, version="?", status="incomplete", details={"error": str(exc)[:200]}))
    return results


def worst_status(results: list[RuleResult]) -> str:
    order = {"blocker": 0, "incomplete": 1, "warning": 2, "pass": 3}
    if not results:
        return "incomplete"
    return min(results, key=lambda r: order.get(r.status, 1)).status


def rules_for_draft(db: Session, draft: Draft, *, form_spec: dict | None = None) -> list[str]:
    """draft 所属渠道形态的默认 RuleSet（profile 优先，legacy 兜底）。"""
    if form_spec and form_spec.get("rule_sets"):
        return list(form_spec["rule_sets"])
    return ["rule.fact.bound", "rule.media.required", "rule.media.public_rights", "rule.media.order", "rule.platform.required_fields"]


def media_requirements_for(db: Session, draft: Draft) -> dict:
    """从 Channel Profile 读 media_requirements；没有 profile 时用渠道方法插件的兜底。"""
    from .channel_registry import ChannelRegistryError, resolve_content_form

    job = draft.content_job
    for form in ((getattr(draft, "content_form", None) or job.content_form), None):
        try:
            spec = resolve_content_form(db, job.channel, form)
        except ChannelRegistryError:
            continue
        except Exception:  # noqa: BLE001 渠道已下线等场景
            return {}
        if spec.source in {"profile", "legacy_template"}:
            return spec.media_requirements
        break  # legacy_default：走渠道方法插件的兜底
    from .channel_methods import legacy_media_requirements

    return legacy_media_requirements(job.channel)
