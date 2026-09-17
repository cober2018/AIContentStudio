"""候选事实抽取（STU-031）。

V1 采用确定性规则抽取：句子含数字/百分比/日期/金额即成为候选 metric 事实。
LLM 抽取作为增强路径由 provider 提供，规则抽取保证无模型时主链路可用。
"""

import re
from dataclasses import dataclass, field

from .parsers import ParsedDocument

# 数字+紧邻单位。单位只认数字后紧跟的（"上涨1.2%"），不猜句子里任意位置的百分号
_NUM = re.compile(r"\d+(?:\.\d+)?")
_UNITS_BY_LENGTH = ["万亿", "个点", "美元", "港元", "％", "%", "亿", "万", "元", "点", "倍", "bp", "只", "家", "次", "天", "人", "辆", "台", "份", "条"]
_DATE = re.compile(r"\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?|\d{1,2}月\d{1,2}日")
_CJK = re.compile(r"[一-龥]")

_SENTENCE_SPLIT = re.compile(r"[。；！？\n]")


@dataclass
class CandidateFact:
    statement: str
    fact_type: str = "metric"
    subject: str | None = None
    predicate: str | None = None
    value: float | str | None = None
    unit: str | None = None
    as_of: str | None = None
    source_locator: dict = field(default_factory=dict)
    confidence: float = 0.7


def _unit_after(sentence: str, pos: int) -> str | None:
    rest = sentence[pos:]
    for unit in _UNITS_BY_LENGTH:
        if rest.startswith(unit):
            return "%" if unit == "％" else unit
    return None


def _is_date_span(sentence: str, start: int, end: int) -> bool:
    return any(m.start() <= start and end <= m.end() for m in _DATE.finditer(sentence))


def _sentence_candidates(sentence: str, locator: dict, as_of: str | None) -> list[CandidateFact]:
    candidates = []
    for match in _NUM.finditer(sentence):
        start, end = match.span()
        num_text = match.group(0)
        if _is_date_span(sentence, start, end):
            continue
        unit = _unit_after(sentence, end)
        if unit is None:
            # 裸数字与中文粘连（沪深300、第3条）多为名称或序号，不是独立指标
            before_cjk = start > 0 and _CJK.match(sentence[start - 1])
            after_cjk = end < len(sentence) and _CJK.match(sentence[end])
            if before_cjk or after_cjk:
                continue
            if num_text in {"0", "1"}:
                continue
        candidates.append(
            CandidateFact(
                statement=sentence.strip(),
                subject=_guess_subject(sentence),
                predicate=_guess_predicate(sentence),
                value=float(num_text) if "." in num_text else int(num_text),
                unit=unit,
                as_of=as_of,
                source_locator=dict(locator),
                confidence=0.75,
            )
        )
    if not candidates and _DATE.search(sentence):
        candidates.append(
            CandidateFact(
                statement=sentence.strip(),
                fact_type="event",
                subject=_guess_subject(sentence),
                predicate="日期",
                value=_DATE.search(sentence).group(0),  # type: ignore[union-attr]
                as_of=as_of,
                source_locator=dict(locator),
                confidence=0.6,
            )
        )
    return candidates


def _guess_subject(sentence: str) -> str | None:
    # 中文主语启发式：取句首到第一个动词类字符前的片段，失败则取前 12 字
    m = re.match(r"^(.{2,20}?)(?:上涨|下跌|涨|跌|达到|为|是|公布|发布|成交|收于|报|增长|下降|减少|增加)", sentence)
    return m.group(1).strip() if m else sentence[:12]


def _guess_predicate(sentence: str) -> str | None:
    for verb in ["上涨", "下跌", "涨", "跌", "成交额", "成交量", "增长", "下降", "减少", "增加", "达到", "收于", "公布"]:
        if verb in sentence:
            return verb
    return "数值"


def extract_candidate_facts(doc: ParsedDocument, as_of: str | None) -> list[CandidateFact]:
    seen: set[str] = set()
    result: list[CandidateFact] = []
    for block in doc.blocks:
        for sentence in (s.strip() for s in _SENTENCE_SPLIT.split(block.text) if len(s.strip()) >= 6):
            if sentence in seen:
                continue
            seen.add(sentence)
            result.extend(_sentence_candidates(sentence, block.locator, as_of))
    return result
