"""Fact Checker（PRD §11 / STU-090~093）。

两层：Deterministic Checker（数字/日期/风险词，规则可复现）+ LLM Reviewer
（越界事实/过度推断，mock provider 下退化为确定性规则，接真实模型自动启用）。
"""

import re
from dataclasses import dataclass, field
from datetime import UTC

from .generation.providers import GenerateRequest

RISK_BLOCKER_WORDS = ["保证收益", "稳赚", "必涨", "一定上涨", "包赚", "零风险", "无风险", "稳赚不赔"]
RISK_WARNING_WORDS = ["大概率", "肯定会", "绝对", "必然"]
# 标准金融术语中的“无风险”不是收益承诺
_RISK_TERM_MASK = re.compile(r"无风险(?:利率|收益率)")

# 结构性数字白名单：行首列表编号、第X、Fact 编号、版本号、时长/字数等元信息
# 注意不能用 \b：中文字符同属 \w，“3分钟读懂”里“钟”后是“读”，\b 永不成立
_STRUCTURAL_NUMBER = re.compile(r"^(?:\d+[.、)])|第\d+|^F\d{3}|\bv\d+|\d+\s*(?:秒|分钟|字)(?!\d)|F\d{3}")
_NUMBER_TOKEN = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)(?![\w.%])|(\d+(?:\.\d+)?)\s*([%％])")
_FULL_DATE = re.compile(r"\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?")
_YEAR_MONTH = re.compile(r"\d{4}[-/年]\d{1,2}(?![\d/月])")
_TODAY_WORDS = re.compile(r"今天|今日|当前|最新")
# 指数类名称常直接来自事实主体，仅机构类后缀值得告警；时间指示词前缀不算实体
_ENTITY_SUFFIX = re.compile(r"([一-龥A-Za-z]{2,12}(?:公司|集团|股份|证券|银行|基金))")
_DEICTIC_PREFIX = ("今日", "今天", "昨日", "明日", "当前", "本周", "上周")
# 贪婪捕获会把“关注基金”“是选基金”这类动宾短语带进候选，剥掉动词性前缀再判断
_VERB_PREFIXES = (
    "是", "关注", "看懂", "读懂", "看", "选", "选购", "买", "卖", "投", "投资",
    "讲", "聊", "谈", "学", "懂", "用", "做", "买", "拿", "到", "在", "给", "让",
)
_SUFFIX_WORDS = ("公司", "集团", "股份", "证券", "银行", "基金")


def _strip_verb_prefix(name: str) -> str:
    changed = True
    while changed:
        changed = False
        for verb in _VERB_PREFIXES:
            if name.startswith(verb) and len(name) - len(verb) >= 2:
                name = name[len(verb):]
                changed = True
    return name


@dataclass
class CheckIssue:
    severity: str  # blocker / warning
    category: str  # number / date / risk_word / forbidden / entity / llm
    span: str
    reason: str
    fact_ids: list[str] = field(default_factory=list)
    suggestion: str | None = None


@dataclass
class FactCheckResult:
    result: str  # pass / warning / blocker
    issues: list[CheckIssue] = field(default_factory=list)
    stats: dict = field(default_factory=dict)

    def to_json(self) -> dict:
        return {
            "result": self.result,
            "stats": self.stats,
            "issues": [
                {
                    "severity": i.severity,
                    "category": i.category,
                    "span": i.span,
                    "reason": i.reason,
                    "fact_ids": i.fact_ids,
                    "suggestion": i.suggestion,
                }
                for i in self.issues
            ],
        }


def _fact_values(facts: list[dict]) -> list[float]:
    values = []
    for f in facts:
        v = f.get("value")
        if isinstance(v, (int, float)):
            values.append(float(v))
    return values


def _fact_texts(facts: list[dict]) -> str:
    return " ".join(f.get("statement", "") for f in facts)


def _number_supported(num: float, raw_digits: str, facts: list[dict], topic_text: str) -> bool:
    fact_values = _fact_values(facts)
    if any(abs(num - v) < 1e-9 for v in fact_values):
        return True
    if raw_digits in _fact_texts(facts) or raw_digits in topic_text:
        return True
    # Fact 总数这类派生计数
    if num == len(facts):
        return True
    # 年份：与事实 as_of 同年即可
    if 1990 <= num <= 2100:
        as_of_years = {str(f.get("as_of") or "")[:4] for f in facts}
        as_of_years.discard("")
        if str(int(num)) in as_of_years:
            return True
    return False


def check_numbers(text: str, facts: list[dict], topic_text: str) -> list[CheckIssue]:
    issues = []
    fact_texts = _fact_texts(facts)
    # 日期（含年月）先掩码，避免 2026-09-17 被拆成 09/17 两个"无来源数字"
    masked = _FULL_DATE.sub(lambda m: " " * len(m.group(0)), text)
    masked = _YEAR_MONTH.sub(lambda m: " " * len(m.group(0)), masked)
    for match in _NUMBER_TOKEN.finditer(masked):
        raw = match.group(1) or match.group(2)
        unit = match.group(3)
        span_text = text[max(0, match.start() - 25) : min(len(text), match.end() + 25)].replace("\n", " ")
        if _STRUCTURAL_NUMBER.search(span_text):
            continue
        num = float(raw)
        if _number_supported(num, raw, facts, topic_text):
            continue
        issues.append(
            CheckIssue(
                severity="blocker",
                category="number",
                span=span_text.strip(),
                reason=f"数字 {raw}{unit or ''} 未获得任何 Fact 支持，且不属于结构性数字",
                suggestion=f"请核对来源，或将其替换为 FactPack 中的事实：{fact_texts[:80]}...",
            )
        )
    return issues


def check_dates(text: str, facts: list[dict]) -> list[CheckIssue]:
    issues = []
    valid_dates = {f.get("as_of") for f in facts if f.get("as_of")}
    for match in _FULL_DATE.finditer(text):
        found = re.sub(r"[年月/]", "-", match.group(0)).replace("日", "")
        parts = [int(p) for p in found.split("-")]
        normalized = f"{parts[0]:04d}-{parts[1]:02d}-{parts[2]:02d}"
        if normalized not in valid_dates:
            issues.append(
                CheckIssue(
                    severity="blocker",
                    category="date",
                    span=match.group(0),
                    reason=f"日期 {normalized} 不在 FactPack 任何事实的 as_of 范围内",
                    suggestion=f"允许的日期：{sorted(valid_dates)}",
                )
            )
    if _TODAY_WORDS.search(text) and valid_dates:
        from datetime import datetime

        today = datetime.now(UTC).date().isoformat()
        if today not in valid_dates:
            issues.append(
                CheckIssue(
                    severity="warning",
                    category="date",
                    span="今天/当前",
                    reason=f"稿件使用『今天/当前』表述，但 FactPack 事实日期为 {sorted(valid_dates)}，非当日",
                    suggestion="改为明确日期，或刷新 FactPack",
                )
            )
    return issues


def check_risk_words(text: str, forbidden_words: list[str]) -> list[CheckIssue]:
    issues = []
    # “无风险利率/无风险收益率”是标准金融术语（夏普比率等），不是收益承诺
    masked = _RISK_TERM_MASK.sub(lambda m: " " * len(m.group(0)), text)
    for word in RISK_BLOCKER_WORDS:
        if word in masked:
            issues.append(
                CheckIssue(
                    severity="blocker",
                    category="risk_word",
                    span=word,
                    reason=f"出现风险词『{word}』，属于确定性投资承诺类表述",
                    suggestion="改为客观描述或加风险限定",
                )
            )
    for word in RISK_WARNING_WORDS:
        if word in text:
            issues.append(
                CheckIssue(
                    severity="warning",
                    category="risk_word",
                    span=word,
                    reason=f"出现确定性倾向词『{word}』",
                )
            )
    for word in forbidden_words:
        if word and word in text:
            issues.append(
                CheckIssue(
                    severity="blocker",
                    category="forbidden",
                    span=word,
                    reason=f"命中 Topic 禁止表述『{word}』",
                )
            )
    return issues


def check_entities(text: str, facts: list[dict], source_text: str) -> list[CheckIssue]:
    """朴素实体检查：公司/机构类名词未出现在任何事实或来源中则告警。"""
    issues = []
    known = _fact_texts(facts) + " " + source_text
    for match in {_strip_verb_prefix(m) for m in _ENTITY_SUFFIX.findall(text)}:
        if match.startswith(_DEICTIC_PREFIX):
            continue
        if match in _SUFFIX_WORDS:
            continue  # 剥掉动词前缀后只剩后缀词本身（如“关注基金”→“基金”），无实体含义
        if match not in known:
            issues.append(
                CheckIssue(
                    severity="warning",
                    category="entity",
                    span=match,
                    reason=f"实体『{match}』未出现在 FactPack 或 Source 中，可能为模型引入的新实体",
                )
            )
    return issues


def run_deterministic_check(
    draft_text: str,
    facts: list[dict],
    topic_text: str,
    forbidden_words: list[str],
    source_text: str = "",
) -> FactCheckResult:
    issues = (
        check_numbers(draft_text, facts, topic_text)
        + check_dates(draft_text, facts)
        + check_risk_words(draft_text, forbidden_words)
        + check_entities(draft_text, facts, source_text)
    )
    blockers = [i for i in issues if i.severity == "blocker"]
    warnings = [i for i in issues if i.severity == "warning"]
    result = "blocker" if blockers else ("warning" if warnings else "pass")
    return FactCheckResult(
        result=result,
        issues=issues,
        stats={"blockers": len(blockers), "warnings": len(warnings)},
    )


def run_llm_review(draft_text: str, facts: list[dict], deterministic: FactCheckResult) -> FactCheckResult:
    """LLM 审查层（真实 provider）：越界事实/过度推断 + 实体抽取，替代朴素规则。

    mock provider 或调用失败时透传确定性结果，绝不伪造审查结论。
    """
    if not _llm_provider_ready():
        return deterministic

    facts_brief = "；".join(f"{f.get('id', '')}:{f.get('statement', '')}" for f in facts[:50])
    # 指标误读红线：数字对但方向/口径/确定性写错（如把底部共振低分写成利空）→ warning
    from .domain_knowledge import reviewer_block

    redline = reviewer_block(facts)
    prompt = (
        "你是金融内容事实合规审查员。对照事实清单审查稿件。\n"
        f"【事实清单】{facts_brief or '（空）'}\n"
        + (f"{redline}\n" if redline else "")
        + f"【稿件】\n{draft_text[:4000]}\n\n"
        "输出 JSON：\n"
        '{"issues": [{"severity": "warning|blocker", "span": "原文片段", '
        '"reason": "为何越界或过度推断", "suggestion": "修改建议"}], '
        '"entities": ["稿件中出现的机构类实体（公司/银行/券商/基金等专有名词，无则空数组）"]}\n'
        "severity=blocker 仅用于稿件内容与事实清单明显冲突；推测性表述与指标解读红线违规用 warning。"
    )
    request = GenerateRequest(
        purpose="fact_review",
        channel=None,
        system_prompt="你是严格的内容事实审查员，只输出 JSON，不输出其他内容。",
        user_prompt=prompt,
        schema_hint='{"issues": [], "entities": []}',
    )
    try:
        result = _run_llm_request(request)
    except Exception:  # noqa: BLE001 审查层任何异常都降级，不阻塞 factcheck 主流程
        return deterministic
    if result is None:
        return deterministic

    merged_issues = list(deterministic.issues)
    known = _fact_texts(facts)
    for issue in result.data.get("issues", []) or []:
        if not isinstance(issue, dict) or not issue.get("reason"):
            continue
        merged_issues.append(
            CheckIssue(
                severity=issue.get("severity") if issue.get("severity") in {"blocker", "warning"} else "warning",
                category="llm",
                span=str(issue.get("span", ""))[:100],
                reason=f"[LLM 审查] {issue['reason']}",
                suggestion=issue.get("suggestion"),
            )
        )
    # LLM 实体抽取成功时覆盖朴素规则实体结果
    llm_entities = result.data.get("entities")
    if isinstance(llm_entities, list):
        merged_issues = [i for i in merged_issues if i.category != "entity"]
        for entity in llm_entities:
            entity = str(entity).strip()
            if entity and entity not in known and not entity.startswith(_DEICTIC_PREFIX):
                merged_issues.append(
                    CheckIssue(
                        severity="warning",
                        category="entity",
                        span=entity,
                        reason=f"实体『{entity}』未出现在 FactPack 中，可能为模型引入的新实体（LLM 抽取）",
                    )
                )

    blockers = [i for i in merged_issues if i.severity == "blocker"]
    warnings = [i for i in merged_issues if i.severity == "warning"]
    return FactCheckResult(
        result="blocker" if blockers else ("warning" if warnings else "pass"),
        issues=merged_issues,
        stats={"blockers": len(blockers), "warnings": len(warnings)},
    )


def _llm_provider_ready() -> bool:
    from ..config import get_settings

    return get_settings().llm_provider == "openai_compatible"


def _run_llm_request(request: GenerateRequest):
    """LLM 调用统一入口：任何失败都降级返回 None（审查层不阻塞主流程）。"""
    import asyncio
    import logging

    from .generation.providers import get_provider

    logger = logging.getLogger(__name__)
    try:
        provider = get_provider("fact_check")
        return asyncio.run(provider.generate_json(request))
    except Exception as exc:  # noqa: BLE001 LLM 层失败只降级告警
        logger.warning("LLM review 调用失败，退回确定性结果: %s", exc)
        return None


def run_fact_check(
    draft_text: str,
    facts: list[dict],
    topic_text: str,
    forbidden_words: list[str],
    source_text: str = "",
) -> FactCheckResult:
    deterministic = run_deterministic_check(draft_text, facts, topic_text, forbidden_words, source_text)
    return run_llm_review(draft_text, facts, deterministic)
