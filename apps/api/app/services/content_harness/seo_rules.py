"""SEO 确定性规则（D13/§3.7）：不依赖 LLM 的必备字段检查。

LLM Discoverability Report 是独立阶段（discoverability.py）；这里只查结构字段。
"""

from __future__ import annotations

from typing import Any


def evaluate_seo_fields(draft) -> dict[str, Any]:
    """post 阶段结构字段：标题非空、structured 内 seo 标签/描述声明（有则查形）。"""
    problems: list[str] = []
    warnings: list[str] = []
    if not (draft.title or "").strip():
        problems.append("missing_title")
    structured = draft.structured_json or {}
    tags = structured.get("tags") or structured.get("seo_tags")
    if tags is not None and not isinstance(tags, list):
        warnings.append("tags_not_list")
    description = structured.get("description") or structured.get("summary")
    if description is not None and not str(description).strip():
        warnings.append("empty_description")
    status = "blocker" if problems else ("warning" if warnings else "pass")
    return {"status": status, "problems": problems, "warnings": warnings}


def rules_for_form(content_form: str | None) -> list[str]:
    """SEO 形态规则：全部形态走必填字段规则。"""
    return ["rule.seo.required_fields"]


class SeoRequiredFieldsRule:
    key = "rule.seo.required_fields"
    version = "1"

    def evaluate(self, db, ctx: dict) -> dict:
        from .contracts import RuleResult

        outcome = evaluate_seo_fields(ctx["draft"])
        return RuleResult(key=self.key, version=self.version, status=outcome["status"], details=outcome)
