"""财务/技术领域规则（D13/§3.8）：确定性检查，不用 LLM。

雪球（quant/market_recap）：as_of 必须存在、禁止收益保证表述；
掘金（tech_article）：代码必须有 provenance 声明，未声明不得标 verified runnable。
"""

from __future__ import annotations

import re
from typing import Any

# 收益保证类禁止表述（雪球等财经形态）
FINANCE_FORBIDDEN_PATTERNS = [
    r"保证[收本]?收益", r"稳赚", r"必涨", r"包赚", r"零风险.{0,6}(收益|回报)", r"确定(性)?获得.{0,6}收益",
]
# 代码可信标注模式（掘金）
VERIFIED_RUNNABLE_PATTERN = re.compile(r"verified[-_ ]?runnable", re.IGNORECASE)


def rules_for_form(content_form: str | None) -> list[str]:
    form = content_form or ""
    if form in {"quant_research", "market_recap", "quant"}:
        return ["rule.finance.as_of", "rule.finance.no_return_guarantee"]
    if form in {"tech_article", "tech"}:
        return ["rule.tech.code_provenance"]
    return []


class FinanceAsOfRule:
    key = "rule.finance.as_of"
    version = "1"

    def evaluate(self, db, ctx: dict) -> Any:
        from .contracts import RuleResult

        draft = ctx["draft"]
        structured = draft.structured_json or {}
        has_as_of = bool(structured.get("as_of")) or bool(re.search(r"截至\s*\d{4}[-/年]\d{1,2}", draft.body or ""))
        return RuleResult(
            key=self.key, version=self.version,
            status="blocker" if not has_as_of else "pass",
            details={"as_of_declared": has_as_of},
        )


class FinanceNoReturnGuaranteeRule:
    key = "rule.finance.no_return_guarantee"
    version = "1"

    def evaluate(self, db, ctx: dict) -> Any:
        from .contracts import RuleResult

        draft = ctx["draft"]
        text = draft.body or ""
        hits = sorted({m.group(0) for pattern in FINANCE_FORBIDDEN_PATTERNS for m in re.finditer(pattern, text)})
        return RuleResult(
            key=self.key, version=self.version,
            status="blocker" if hits else "pass",
            details={"forbidden_hits": hits},
        )


class TechCodeProvenanceRule:
    key = "rule.tech.code_provenance"
    version = "1"

    def evaluate(self, db, ctx: dict) -> Any:
        from .contracts import RuleResult

        draft = ctx["draft"]
        structured = draft.structured_json or {}
        has_code = "```" in (draft.body or "")
        if not has_code:
            return RuleResult(key=self.key, version=self.version, status="pass", details={"has_code": False})
        provenance = structured.get("code_provenance") or {}
        declared = bool(provenance) or ("来源" in (draft.body or "") and "仓库" in (draft.body or ""))
        verified_marker = bool(VERIFIED_RUNNABLE_PATTERN.search(draft.body or "")) or bool(
            structured.get("verified_runnable")
        )
        if verified_marker and not declared:
            return RuleResult(
                key=self.key, version=self.version, status="blocker",
                details={"verified_runnable_without_provenance": True},
            )
        return RuleResult(
            key=self.key, version=self.version,
            status="warning" if not declared else "pass",
            details={"has_code": True, "provenance_declared": declared, "verified_runnable": verified_marker},
        )


def bootstrap_domain_rules(registry) -> None:
    for rule in (FinanceAsOfRule(), FinanceNoReturnGuaranteeRule(), TechCodeProvenanceRule()):
        if rule.key not in {d.key for d in registry.list("rule")}:
            registry.register("rule", rule.key, rule.version, rule)
