"""Connector 映射协议 v2（stages）测试：宽表 → 精选事实。

覆盖 DreamO 数据服务接入所需能力：aggregate / expand(*_json 二次解析) / join(名单汇总、
分布计数) / item + filter/sort_by/limit/derived，offset 分页，raw_keep_fields 瘦身。
"""

import json

import pytest

from app.services import connector_service
from app.services.connector_service import ConnectorError

ADMIN = {"X-Studio-User": "admin@studio.local"}
EDITOR = {"X-Studio-User": "editor@studio.local"}


@pytest.fixture
def seed_admin(db_session):
    from app.models import User

    db_session.add(User(email="admin@studio.local", name="Admin", role="admin"))
    db_session.commit()


def _sentiment_row(**over):
    row = {
        "trade_date": "2026-09-18",
        "emotion_total_score": 0.18,
        "emotion_total_max": 5.0,
        "emotion_state": "none",
        "emotion_state_label": "未形成底部共振",
        "emotion_confidence": 1.0,
        "resonance_label_text": None,
        "resonance_triggered": 0,
        "valuation_bucket_label": "中性",
        "valuation_confidence": 1.0,
        "derivatives_score": 0.38,
        "breadth_score": 0.0,
        "microstructure_score": 0.0,
        "crowding_liquidity_score": 0.44,
        "erp_regime_label": "估值风险补偿中性",
        "erp_filter_score": None,
        "indicators_json": json.dumps(
            {
                "smart_money": {"score": 0.02, "signal": 0, "level": "中性观察"},
                "option_panic": {"signal": 1, "level": "偏谨慎", "unavailable": "no_data"},
            },
            ensure_ascii=False,
        ),
    }
    row.update(over)
    return row


def _mapping(stages):
    return {"items_path": "data.rows", "as_of_field": "trade_date", "stages": stages}


def test_v2_aggregate_and_expand():
    mapping = _mapping(
        [
            {
                "mode": "aggregate",
                "facts": [
                    {
                        "statement": "A股市场情绪总分 {emotion_total_score}（满分 {emotion_total_max}），市场状态：{emotion_state_label}",
                        "value": "{emotion_total_score}",
                        "subject": "市场情绪",
                        "predicate": "情绪总分",
                        "when_present": ["emotion_total_score", "emotion_state_label"],
                    },
                    {
                        "statement": "底部共振：{resonance_label_text}",
                        "value": "{emotion_confidence}",
                        "when": {"resonance_triggered": 1},
                        "when_present": ["resonance_label_text"],
                    },
                    {
                        "statement": "ERP 区间：{erp_regime_label}",
                        "value": "{erp_filter_score}",
                        "when_present": ["erp_regime_label", "erp_filter_score"],
                    },
                ],
            },
            {
                "mode": "expand",
                "expand_field": "indicators_json",
                "key_into": "indicator",
                "facts": [
                    {
                        "statement": "情绪指标 {indicator} 得分 {score}（{level}）",
                        "value": "{score}",
                        "subject": "{indicator}",
                        "when_present": ["score", "level"],
                    }
                ],
            },
        ]
    )
    facts = connector_service.map_response_to_facts_v2([_sentiment_row()], mapping, None)
    statements = [f.statement for f in facts]
    assert any("情绪总分 0.18" in s and "未形成底部共振" in s for s in statements)
    # when 条件不满足（resonance_triggered=0）与 when_present 缺失（erp_filter_score=None）都被跳过
    assert len(facts) == 2
    # expand：缺 score 的 unavailable 指标被跳过，dict key 成为 {indicator} 字段
    assert "情绪指标 smart_money 得分 0.02（中性观察）" in statements
    assert all("option_panic" not in s for s in statements)
    assert facts[0].as_of == "2026-09-18"


def test_v2_join_count_and_names():
    rows = [
        {"sector_name": "银行", "lifecycle_phase": "neutral", "rrg_v3_quadrant": "leading", "rrg_v3_rs_z": 1.2, "sector_return": 0.01},
        {"sector_name": "电子", "lifecycle_phase": "turning_up", "rrg_v3_quadrant": "leading", "rrg_v3_rs_z": 2.5, "sector_return": 0.03},
        {"sector_name": "煤炭", "lifecycle_phase": "turning_down", "rrg_v3_quadrant": "lagging", "rrg_v3_rs_z": -1.0, "sector_return": -0.02},
    ]
    mapping = _mapping(
        [
            {
                "mode": "join",
                "count_by": "lifecycle_phase",
                "facts": [
                    {"statement": "行业生命周期分布：{__counts__}", "value": "{__count__}",
                     "subject": "行业结构", "predicate": "生命周期分布"}
                ],
            },
            {
                "mode": "join",
                "filter": {"rrg_v3_quadrant": "leading"},
                "sort_by": "-rrg_v3_rs_z",
                "join_field": "sector_name",
                "limit": 10,
                "facts": [
                    {"statement": "RRG 领先行业：{__joined__}（共 {__count__} 个）", "value": "{__count__}",
                     "subject": "行业结构", "predicate": "RRG领先行业"}
                ],
            },
        ]
    )
    facts = connector_service.map_response_to_facts_v2(rows, mapping, "2026-09-18")
    assert facts[0].statement == "行业生命周期分布：neutral=1 turning_up=1 turning_down=1"
    assert facts[0].value == 3
    # 排序生效（rs_z 降序）、join 用顿号、计数正确
    assert facts[1].statement == "RRG 领先行业：电子、银行（共 2 个）"
    assert facts[1].as_of == "2026-09-18"


def test_v2_item_filter_sort_limit_derived():
    rows = [
        {"sector_name": f"行业{i}", "idx_type": "行业板块", "review_group": "focus" if i % 2 else "hold",
         "phase_confidence": i / 100, "sector_return": i / 1000}
        for i in range(10)
    ]
    mapping = _mapping(
        [
            {
                "mode": "item",
                "filter": {"idx_type": "行业板块", "review_group": "focus"},
                "sort_by": "-phase_confidence",
                "limit": 2,
                "derived": {"sector_return_pct": ["sector_return", 100]},
                "facts": [
                    {
                        "statement": "{sector_name}：涨跌 {sector_return_pct}%",
                        "value": "{sector_return_pct}",
                        "unit": "%",
                        "subject": "{sector_name}",
                        "when_present": ["sector_return_pct"],
                    }
                ],
            }
        ]
    )
    facts = connector_service.map_response_to_facts_v2(rows, mapping, None)
    assert len(facts) == 2
    assert facts[0].statement == "行业9：涨跌 0.9%"  # phase_confidence 降序后取前 2
    assert facts[1].statement == "行业7：涨跌 0.7%"
    assert facts[0].value == 0.9


def test_v2_expand_focus_event_empty_string_skipped():
    row = {"trade_date": "2026-09-18", "focus_event_json": "", "title": "x"}
    mapping = _mapping(
        [
            {
                "mode": "expand",
                "expand_field": "focus_event_json",
                "facts": [{"statement": "焦点事件：{title}", "value": "{importance}", "when_present": ["title"]}],
            }
        ]
    )
    assert connector_service.map_response_to_facts_v2([row], mapping, None) == []


def test_v2_requires_stages_and_facts():
    with pytest.raises(ConnectorError, match="stages"):
        connector_service.map_response_to_facts_v2([], {"stages": []}, None)
    with pytest.raises(ConnectorError, match="facts"):
        connector_service.map_response_to_facts_v2([{}], _mapping([{"mode": "aggregate"}]), None)


def _setup_v2_endpoint(client, monkeypatch, rows, mapping, captured=None):
    monkeypatch.setenv("QUANT_API_KEY", "test-secret")
    client.post("/api/v1/connectors", json={
        "name": "DreamO 数据服务", "base_url": "https://dreamotech.cn",
        "auth_style": "header", "auth_header_name": "X-API-Key", "api_key_env": "QUANT_API_KEY",
    }, headers=ADMIN)
    detail = client.get("/api/v1/connectors", headers=ADMIN).json()
    cid = detail[0]["id"]
    resp = client.post(f"/api/v1/connectors/{cid}/endpoints", json={
        "name": "市场情绪看板",
        "path": "/api/v1/data/apis/review-market-sentiment/records",
        "params": {"limit": 500},
        "title_template": "DreamO 市场情绪看板 {today}",
        "as_of_path": "data.rows.0.trade_date",
        "trust_level": 0.95,
        "fact_mapping": mapping,
        "pagination": {"type": "offset", "limit_param": "limit", "offset_param": "offset",
                       "page_size": 2, "offset_start": 0, "max_pages": 5},
    }, headers=ADMIN)
    assert resp.status_code == 201, resp.text
    endpoint_id = resp.json()["id"]

    def fake_fetch(url, headers=None, method="GET", json_body=None):
        if captured is not None:
            captured["urls"] = captured.get("urls", []) + [url]
            captured["headers"] = headers or {}
        offset = int(url.split("offset=")[1].split("&")[0])
        page = rows[offset: offset + 2]
        return json.dumps({"success": True, "data": {"rows": page}}, ensure_ascii=False).encode(), "application/json"

    monkeypatch.setattr(connector_service, "safe_fetch", fake_fetch)
    return cid, endpoint_id


def test_pull_v2_offset_pagination_and_raw_trim(client, monkeypatch, seed_admin):
    captured = {}
    rows = [_sentiment_row(emotion_total_score=0.10 + i * 0.01) for i in range(3)]  # 3 行 → 2 页
    mapping = _mapping(
        [
            {
                "mode": "item",
                "derived": {"emotion_pct": ["emotion_total_score", 100]},
                "facts": [
                    {"statement": "{trade_date} 情绪总分 {emotion_pct}", "value": "{emotion_pct}",
                     "when_present": ["emotion_pct"]}
                ],
            }
        ]
    )
    mapping["raw_keep_fields"] = ["trade_date", "emotion_total_score", "emotion_state_label"]
    cid, endpoint_id = _setup_v2_endpoint(client, monkeypatch, rows, mapping, captured)

    resp = client.post(f"/api/v1/endpoints/{endpoint_id}/pull", headers=EDITOR)
    assert resp.status_code == 200, resp.text
    assert resp.json()["facts"] == 3

    # offset 分页：第二页 offset=2，鉴权 header 注入
    assert "limit=2" in captured["urls"][0] and "offset=0" in captured["urls"][0]
    assert "offset=2" in captured["urls"][1]
    assert captured["headers"]["X-API-Key"] == "test-secret"

    source = client.get(f"/api/v1/sources/{resp.json()['source_id']}", headers=EDITOR).json()
    assert source["as_of"] == "2026-09-18"
    # raw_keep_fields 瘦身：原始文本只保留关注列
    raw = json.loads(source["raw_text"]) if source["raw_text"].startswith("{") else {}
    assert raw and raw["row_count"] == 3
    assert set(raw["rows"][0]) == {"trade_date", "emotion_total_score", "emotion_state_label"}
    assert any("情绪总分 12.0" in f["statement"] for f in source["facts"])

    # 指纹去重：再次拉取不新建 Source
    resp2 = client.post(f"/api/v1/endpoints/{endpoint_id}/pull", headers=EDITOR)
    assert resp2.status_code == 200
    assert resp2.json()["unchanged"] is True
