"""领域知识层测试：加载/裁剪/红线提取/优雅降级/prompt 注入。"""

import pytest

from app.services import domain_knowledge
from app.services.generation import renderers

METHODOLOGY = """# 复盘看板方法论

## 看盘顺序
先看市场情绪，再看行业生命周期，最后看 RRG。

## 底部共振框架
情绪总分极低 + 多指标共振 = 底部区域信号，不是利空。

## 自检清单
- 反向指标不得按字面解读。
"""

DICTIONARY = """# 指标字典

## crowding_percentile_60d 拥挤度分位
字段：crowding_percentile_60d。90% 以上 = 交易拥挤，属追高风险预警；
禁止写成"资金追捧利好"。

## lifecycle_phase 生命周期阶段
字段：lifecycle_phase。accelerating/turning_up/turning_down/declining/neutral。
turning_up 是阶段判定带置信度，禁止写成"即将大涨"。

## emotion_total_score 情绪总分
字段：emotion_total_score。底部检测框架，低分是反向信号。
误读红线：不得把低分写成市场情绪崩溃建议清仓。

## 与本稿无关的指标
字段：unrelated_metric_xyz。这一节不应被注入。
"""

FACTS = [
    {
        "id": "F001",
        "statement": "电子：生命周期 turning_up（置信度 0.78），拥挤度60日分位 65.0%",
        "subject": "电子",
        "predicate": "当日涨跌幅",
        "value": 2.81,
        "as_of": "2026-09-18",
        "source_id": 1,
    },
    {
        "id": "F002",
        "statement": "A股市场情绪总分 0.1835（满分 5.0）",
        "subject": "市场情绪",
        "predicate": "情绪总分",
        "value": 0.1835,
        "as_of": "2026-09-18",
        "source_id": 2,
    },
]

RAW = '{"rows": [{"lifecycle_phase": "turning_up", "crowding_percentile_60d": 0.65}]}'


@pytest.fixture
def knowledge_docs(tmp_path, monkeypatch):
    (tmp_path / "方法论.md").write_text(METHODOLOGY, encoding="utf-8")
    (tmp_path / "指标字典.md").write_text(DICTIONARY, encoding="utf-8")
    monkeypatch.setattr(domain_knowledge, "KNOWLEDGE_DIR", tmp_path)
    domain_knowledge._cache.clear()
    yield tmp_path
    domain_knowledge._cache.clear()


def test_graceful_degradation_when_docs_absent(tmp_path, monkeypatch):
    monkeypatch.setattr(domain_knowledge, "KNOWLEDGE_DIR", tmp_path)
    domain_knowledge._cache.clear()
    assert domain_knowledge.methodology_text() == ""
    assert domain_knowledge.generation_block(FACTS, [RAW]) == ""
    assert domain_knowledge.reviewer_block(FACTS) == ""
    assert domain_knowledge.knowledge_ready() is False


def test_generation_block_injects_methodology_and_matched_sections(knowledge_docs):
    block = domain_knowledge.generation_block(FACTS, [RAW])
    assert "看盘顺序" in block  # 方法论全文
    assert "底部共振框架" in block
    assert "crowding_percentile_60d" in block  # 字段名命中 → 拥挤度节入选
    assert "lifecycle_phase" in block  # raw_text 字段名命中
    assert "unrelated_metric_xyz" not in block  # 无关节被裁掉


def test_generation_block_matches_chinese_terms_without_raw(knowledge_docs):
    """没有 source raw 时，statement/predicate 中的中文术语仍能命中字典节。"""
    block = domain_knowledge.generation_block(FACTS, None)
    assert "情绪总分" in block
    assert "unrelated_metric_xyz" not in block


def test_reviewer_block_redline_sections(knowledge_docs):
    block = domain_knowledge.reviewer_block(FACTS, [RAW])
    assert "误读红线" in block or "红线" in block
    assert "清仓" in block  # 情绪节含红线文案，入选
    assert "禁止写成" in block  # 拥挤度/生命周期节的红线
    assert "看盘顺序" not in block  # 方法论不进 reviewer（只按红线审）


def test_compose_prompt_placeholder_replaced(knowledge_docs):
    brief = renderers.topic_brief_text(type("T", (), {
        "title": "t", "audience": "a", "goal": "g", "angle": "an",
        "core_thesis": "c", "must_include_json": [], "forbidden_json": [], "cta": "ct",
    })())
    prompt_with = renderers.compose_prompt(
        "douyin", brief, FACTS, "voice", domain_knowledge_block="【领域知识】测试块"
    )
    assert "【领域知识】测试块" in prompt_with
    assert "{domain_knowledge_block}" not in prompt_with
    # 空知识块：占位符消失，模板不破
    prompt_without = renderers.compose_prompt("douyin", brief, FACTS, "voice")
    assert "{domain_knowledge_block}" not in prompt_without
    assert "FactPack" in prompt_without


def test_block_size_cap(knowledge_docs, monkeypatch):
    monkeypatch.setattr(domain_knowledge, "_MAX_DICT_CHARS", 200)
    block = domain_knowledge.generation_block(FACTS, [RAW])
    assert len(block) <= domain_knowledge._MAX_BLOCK_CHARS
    # 字典部分被截断，方法论保留在开头
    assert "看盘顺序" in block
