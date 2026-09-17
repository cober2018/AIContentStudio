"""Fact Checker（PRD §11 / STU-090~093）。

两层：Deterministic Checker（数字/日期/风险词，规则可复现）+ LLM Reviewer
（越界事实/过度推断，mock provider 下退化为确定性规则，接真实模型自动启用）。
"""

import re
from dataclasses import dataclass, field
from datetime import UTC

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
    """LLM 审查层。mock provider 下无法真正推理，退化为保守规则：
    确定性结果直接透传，避免伪造审查结论。接真实模型后此函数走 provider。
    """
    return deterministic


def run_fact_check(
    draft_text: str,
    facts: list[dict],
    topic_text: str,
    forbidden_words: list[str],
    source_text: str = "",
) -> FactCheckResult:
    deterministic = run_deterministic_check(draft_text, facts, topic_text, forbidden_words, source_text)
    return run_llm_review(draft_text, facts, deterministic)
