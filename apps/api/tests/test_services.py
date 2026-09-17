"""服务层单测：解析器 / SSRF 校验 / Checker / 校验和 / 导出。"""

import pytest

from app.models import Fact
from app.services.exports import export_srt, export_txt
from app.services.factchecker import run_deterministic_check
from app.services.factpack_service import fact_checksum
from app.services.parsers import CsvParser, JsonParser, MarkdownParser, TextParser, get_parser
from app.services.url_fetch import UnsafeUrlError, _validate_target

# ---------- Parsers（STU-023） ----------


def test_text_parser_blocks():
    doc = TextParser().parse("第一段。\n\n第二段 上涨1.2%。".encode())
    assert len(doc.blocks) == 2
    assert doc.blocks[1].locator == {"block": 1}


def test_markdown_parser_heading():
    doc = MarkdownParser().parse("# 标题\n\n正文".encode())
    assert doc.blocks[0].type == "heading"


def test_csv_parser_rows():
    csv_bytes = "指标,数值,单位\n成交额,1.1,万亿\n涨幅,1.2,%\n".encode()
    doc = CsvParser().parse(csv_bytes)
    assert doc.metadata["columns"] == ["指标", "数值", "单位"]
    assert len(doc.blocks) == 2
    assert "指标=成交额" in doc.blocks[0].text
    assert "数值=1.1" in doc.blocks[0].text


def test_json_parser_paths():
    doc = JsonParser().parse('{"指数": {"涨幅": 1.2}}'.encode())
    assert doc.blocks[0].text == "指数.涨幅 = 1.2"


def test_get_parser_dispatch():
    assert isinstance(get_parser("text/csv", ".csv"), CsvParser)
    assert isinstance(get_parser("application/pdf", ".pdf"), get_parser("application/pdf", ".pdf").__class__)
    assert isinstance(get_parser("text/markdown", ".md"), MarkdownParser)


# ---------- SSRF（STU-161） ----------


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "http://127.0.0.1/x",
        "http://10.0.0.1/x",
        "http://169.254.169.254/meta",
        "ftp://example.com/x",
    ],
)
def test_unsafe_urls_rejected(url):
    with pytest.raises((UnsafeUrlError, OSError)):
        _validate_target(url)


def test_ssrf_allow_private_dev_flag(monkeypatch):
    """fake-ip 代理环境豁免开关：开启后跳过 IP 检查，但 scheme 校验仍然生效。"""
    from app.config import get_settings

    monkeypatch.setenv("SSRF_ALLOW_PRIVATE", "true")
    get_settings.cache_clear()
    try:
        _validate_target("http://10.0.0.1/x")  # 不再抛 UnsafeUrlError
        with pytest.raises(UnsafeUrlError):
            _validate_target("ftp://example.com/x")
    finally:
        get_settings.cache_clear()


# ---------- Deterministic Checker（STU-091） ----------

FACTS = [
    {"id": "F001", "statement": "指数上涨1.2%", "value": 1.2, "unit": "%", "as_of": "2026-09-15"},
    {"id": "F002", "statement": "成交额达到1.1万亿", "value": 1.1, "unit": "万亿", "as_of": "2026-09-15"},
]
TOPIC_TEXT = "标题：今天的市场复盘 受众：普通投资者"


def test_checker_pass_supported_numbers():
    result = run_deterministic_check("指数上涨1.2%，成交额1.1万亿。", FACTS, TOPIC_TEXT, [])
    assert result.result == "pass", result.to_json()


def test_checker_blocks_unsupported_number():
    result = run_deterministic_check("板块资金净流入达到87.3%。", FACTS, TOPIC_TEXT, [])
    assert result.result == "blocker"
    assert result.issues[0].category == "number"
    assert "87.3" in result.issues[0].reason


def test_checker_blocks_risk_words():
    result = run_deterministic_check("这只股票保证收益，指数上涨1.2%。", FACTS, TOPIC_TEXT, [])
    assert any(i.category == "risk_word" and i.severity == "blocker" for i in result.issues)


def test_checker_blocks_forbidden_words():
    result = run_deterministic_check("指数上涨1.2%，内部消息值得关注。", FACTS, TOPIC_TEXT, ["内部消息"])
    assert any(i.category == "forbidden" for i in result.issues)


def test_checker_blocks_unknown_date():
    result = run_deterministic_check("2026-09-01指数上涨1.2%。", FACTS, TOPIC_TEXT, [])
    assert any(i.category == "date" and i.severity == "blocker" for i in result.issues)


def test_checker_allows_structural_numbers():
    body = "# 复盘\n\n1. 第一点的说明，指数上涨1.2%。\n2. 引用 F001。"
    result = run_deterministic_check(body, FACTS, TOPIC_TEXT, [])
    assert result.result == "pass", result.to_json()


def test_checker_structural_number_next_to_cjk():
    """\\b 在中文旁不成立：时长数字后紧跟中文不得误报（Golden G007 回归）。"""
    result = run_deterministic_check("3分钟读懂市场主线，指数上涨1.2%。", FACTS, TOPIC_TEXT, [])
    assert result.result == "pass", result.to_json()


def test_checker_allows_risk_free_rate_term():
    """无风险利率是标准术语不是收益承诺（Golden G022 回归）。"""
    result = run_deterministic_check("按无风险利率1.5%计算，指数上涨1.2%。", FACTS, TOPIC_TEXT, [])
    assert not any(i.category == "risk_word" for i in result.issues)
    result2 = run_deterministic_check("该产品无风险，稳赚不赔。", FACTS, TOPIC_TEXT, [])
    assert any(i.category == "risk_word" and i.severity == "blocker" for i in result2.issues)


def test_checker_entity_verb_prefix_stripped():
    """动宾短语里的机构后缀词不算新实体（Golden G021/G022 回归）。"""
    result = run_deterministic_check("是选基金的重要指标，指数上涨1.2%。", FACTS, TOPIC_TEXT, [])
    assert not any(i.category == "entity" for i in result.issues)
    result2 = run_deterministic_check("中金证券今日发布新品，指数上涨1.2%。", FACTS, TOPIC_TEXT, [])
    assert any(i.category == "entity" for i in result2.issues)


def test_checker_fact_count_derived_number():
    result = run_deterministic_check("我们用2条事实复盘。", FACTS, TOPIC_TEXT, [])
    assert result.result == "pass", result.to_json()


# ---------- Checksum（STU-042） ----------


def _fact(fid, value, statement="s"):
    return Fact(id=fid, statement=statement, subject="X", predicate="涨", value_json={"value": value},
                unit="%", as_of="2026-09-15")


def test_checksum_order_independent():
    a = fact_checksum([_fact(1, 1.2), _fact(2, 3.4)])
    b = fact_checksum([_fact(2, 3.4), _fact(1, 1.2)])
    assert a == b


def test_checksum_changes_with_content():
    a = fact_checksum([_fact(1, 1.2)])
    b = fact_checksum([_fact(1, 1.3)])
    assert a != b


# ---------- Exports（STU-121~123） ----------


class _Asset:
    id = 7
    channel = "douyin"
    title = "t"
    final_body = "# 标题\n\n**Hook**：开场\n"
    structured_json = {"spoken_script": "第一句。第二句！"}
    fact_pack_id = 1
    fact_pack_version = 1
    fact_pack_checksum = "x"
    approved_revision = 1
    reviewer = "r@x"
    created_at = None
    model_provider = "mock"
    model_name = "m"
    prompt_version = None
    template_version_id = None


def test_srt_marks_estimated():
    content = export_srt(_Asset())
    assert content.startswith("NOTE")
    assert "estimated" in content
    assert "00:00:00,000 --> " in content


def test_txt_strips_markdown():
    assert "Hook：开场" in export_txt(_Asset())
    assert "#" not in export_txt(_Asset())
