"""领域知识层：复盘看板方法论 + 指标字典的加载、按需裁剪与 prompt 注入。

知识来源：量化平台官方文档（DreamOAgents docs/review/，复制到 app/llm/knowledge/）：
  - 方法论.md：看盘顺序、每张图怎么读、跨图剧本、成稿模板、自检清单 → 全文注入
  - 指标字典.md：逐字段口径/公式/阈值/组合用法/误读红线 → 按本稿涉及的指标裁剪注入

设计约束：
  - 知识是解读规则，不是事实——不进 FactPack、不参与 FactCheck 数字校验；
  - 文档缺席时一切接口返回空串，生成链路行为与没有知识层时完全一致（优雅降级）；
  - 解析结构无关（按 Markdown 标题分节 + 关键词匹配），官方文档落盘后零代码改动生效；
  - mtime 缓存，替换文档后下次调用自动重载。

裁剪策略（token 经济）：
  匹配 token = 事实 statement/subject/predicate 中的中文指标术语 + 来源 raw_text 中
  出现的 API 英文字段名（raw_keep_fields 保留的宽表列名）。字典节按「节文本包含任一
  token」入选，按命中数排序、总长封顶；方法论全文注入（它是整套看盘框架，拆开失效）。
"""

import re
from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).resolve().parents[1] / "llm" / "knowledge"
METHODOLOGY_FILE = "方法论.md"
DICTIONARY_FILE = "指标字典.md"

# 注入块总长封顶（字符）：防止知识文档膨胀后打爆 prompt
_MAX_BLOCK_CHARS = 20000
_MAX_DICT_CHARS = 10000
# 误读红线节的关键词（reviewer 注入用）
_REDLINE_KEYWORDS = ("红线", "误读", "禁止", "禁用", "自检", "常见错误", "不得")

_section_re = re.compile(r"^(#{2,4})\s+(.+)$", re.MULTILINE)
_field_re = re.compile(r"\b[a-z][a-z0-9_]{4,}\b")
_chinese_re = re.compile(r"[\u4e00-\u9fa5]{2,8}")

_cache: dict[str, tuple[float, str]] = {}


def _read(path: Path) -> str:
    """mtime 缓存读取：文档替换后自动失效。"""
    if not path.is_file():
        return ""
    mtime = path.stat().st_mtime
    cached = _cache.get(path.name)
    if cached and cached[0] == mtime:
        return cached[1]
    text = path.read_text(encoding="utf-8")
    _cache[path.name] = (mtime, text)
    return text


def methodology_text() -> str:
    return _read(KNOWLEDGE_DIR / METHODOLOGY_FILE).strip()


def _split_sections(text: str) -> list[dict]:
    """按 ##/###/#### 标题把字典切成节；首节（文件头说明）单独保留。"""
    if not text.strip():
        return []
    matches = list(_section_re.finditer(text))
    if not matches:
        return [{"heading": "", "body": text.strip()}]
    sections = []
    if matches[0].start() > 0:
        head = text[: matches[0].start()].strip()
        if head:
            sections.append({"heading": "", "body": head})
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections.append({"heading": m.group(2).strip(), "body": text[m.start():end].strip()})
    return sections


def dictionary_sections() -> list[dict]:
    return _split_sections(_read(KNOWLEDGE_DIR / DICTIONARY_FILE))


def knowledge_ready() -> bool:
    return bool(methodology_text()) or bool(dictionary_sections())


def _collect_tokens(facts: list[dict], source_raws: list[str] | None) -> set[str]:
    """事实术语（中文，取 subject/predicate + statement 中的词典内片段）+ 字段名（英文）。"""
    tokens: set[str] = set()
    for f in facts or []:
        for key in ("subject", "predicate"):
            v = (f or {}).get(key)
            if v and 2 <= len(str(v)) <= 12:
                tokens.add(str(v))
    statements = "。".join(str((f or {}).get("statement", "")) for f in (facts or []))
    tokens.update(_chinese_re.findall(statements))
    for raw in source_raws or []:
        tokens.update(_field_re.findall(raw))
    # 过滤过泛的词（出现在超多节里没有区分度，匹配时也会被结构性排除，这里先去掉明显停用词）
    tokens -= {"当日", "当日涨", "数据", "平台", "口径", "亿元", "评分", "市场", "相对", "分布", "趋势"}
    return {t for t in tokens if len(t) >= 2}


def _match_sections(sections: list[dict], tokens: set[str], redline_only: bool = False) -> list[dict]:
    """节文本命中任一 token 即入选；红线模式只取含红线关键词的节。"""
    matched: list[tuple[int, dict]] = []
    for sec in sections:
        text = f"{sec['heading']}\n{sec['body']}"
        if redline_only and not any(k in text for k in _REDLINE_KEYWORDS):
            continue
        hits = sum(1 for t in tokens if t in text)
        if hits or redline_only:
            matched.append((hits, sec))
    matched.sort(key=lambda x: (-x[0],))
    return [sec for _, sec in matched]


def _join_capped(sections: list[dict], cap: int) -> str:
    out: list[str] = []
    total = 0
    for sec in sections:
        body = f"### {sec['heading']}\n{sec['body']}" if sec["heading"] else sec["body"]
        if total + len(body) > cap:
            break
        out.append(body)
        total += len(body)
    return "\n\n".join(out)


def generation_block(facts: list[dict], source_raws: list[str] | None = None) -> str:
    """生成/荐题 prompt 的领域知识块。文档缺席返回空串（调用方拼 prompt 不受影响）。"""
    methodology = methodology_text()
    sections = dictionary_sections()
    if not methodology and not sections:
        return ""

    tokens = _collect_tokens(facts, source_raws)
    dict_parts = _join_capped(_match_sections(sections, tokens), _MAX_DICT_CHARS) if sections else ""

    parts: list[str] = []
    if methodology:
        parts.append(
            "【领域知识 · 复盘看板方法论（解读数据的框架与顺序，写作时必须遵循）】\n" + methodology
        )
    if dict_parts:
        parts.append(
            "【领域知识 · 本稿涉及指标的口径卡（指标字典节选：口径/阈值/组合用法/表述红线，"
            "涉及数字与结论的表述必须与这里一致）】\n" + dict_parts
        )
    block = "\n\n".join(parts)
    return block[:_MAX_BLOCK_CHARS]


def reviewer_block(facts: list[dict], source_raws: list[str] | None = None) -> str:
    """LLM Reviewer 的误读红线块：数字正确但方向/口径/确定性写错 → warning。"""
    sections = dictionary_sections()
    if not sections:
        return ""
    tokens = _collect_tokens(facts, source_raws)
    # 红线节全给；再补充本稿涉及指标的节（其内的组合用法/阈值同样是判定依据）
    redline = _match_sections(sections, set(), redline_only=True)
    field_secs = [s for s in _match_sections(sections, tokens) if s not in redline]
    body = _join_capped(redline + field_secs, _MAX_DICT_CHARS)
    if not body:
        return ""
    return (
        "【指标解读红线（语义级审查依据：稿件数字与事实一致，但解读方向/口径/确定性违反下列规则"
        "时记 warning，与事实清单明显冲突才升 blocker）】\n" + body
    )
