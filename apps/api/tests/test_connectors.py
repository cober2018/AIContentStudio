"""External Connector 测试（EPIC-18）：配置 CRUD、鉴权注入、JSON 映射、拉取落库。"""

import json

import pytest

from app.services import connector_service
from app.services.connector_service import ConnectorError


@pytest.fixture
def seed_admin(db_session):
    """内存库无种子用户：admin 不会自动建号（默认角色是 editor），需显式种入。"""
    from app.models import User

    db_session.add(User(email="admin@studio.local", name="Admin", role="admin"))
    db_session.commit()

ADMIN = {"X-Studio-User": "admin@studio.local"}
EDITOR = {"X-Studio-User": "editor@studio.local"}
VIEWER = {"X-Studio-User": "viewer@studio.local"}

API_JSON = {
    "code": 0,
    "data": {
        "trade_date": "2026-09-17",
        "rows": [
            {"index_name": "沪深300", "pct_change": 1.2},
            {"index_name": "中证500", "pct_change": -0.8},
        ],
    },
}

CONNECTOR_BODY = {
    "name": "量化平台",
    "base_url": "https://api.quant.example.com",
    "auth_style": "bearer",
    "api_key_env": "QUANT_API_KEY",
}

ENDPOINT_BODY = {
    "name": "每日市场复盘",
    "path": "/api/v1/market/daily",
    "params": {"date": "{today}"},
    "title_template": "{today} 市场复盘",
    "as_of_path": "data.trade_date",
    "fact_mapping": {
        "items_path": "data.rows",
        "statement": "{index_name} 当日涨跌幅 {pct_change}%",
        "fields": {"value": "{pct_change}", "subject": "{index_name}", "unit": "%", "predicate": "涨跌幅"},
    },
}


def _setup_connector_and_endpoint(client, monkeypatch, api_json=API_JSON, captured=None):
    """建 connector + endpoint，并 mock safe_fetch 返回固定 JSON（不真发网络）。"""
    monkeypatch.setenv("QUANT_API_KEY", "test-secret")
    resp = client.post("/api/v1/connectors", json=CONNECTOR_BODY, headers=ADMIN)
    assert resp.status_code == 201, resp.text
    connector_id = resp.json()["id"]

    resp = client.post(f"/api/v1/connectors/{connector_id}/endpoints", json=ENDPOINT_BODY, headers=ADMIN)
    assert resp.status_code == 201, resp.text
    endpoint_id = resp.json()["id"]

    def fake_fetch(url, headers=None, **kwargs):
        if captured is not None:
            captured["url"] = url
            captured["headers"] = headers or {}
        return json.dumps(api_json, ensure_ascii=False).encode(), "application/json"

    monkeypatch.setattr(connector_service, "safe_fetch", fake_fetch)
    return connector_id, endpoint_id


def test_connector_crud_and_rbac(client, db_session, seed_admin):
    from app.models import User

    db_session.add(User(email="viewer@studio.local", name="Viewer", role="viewer"))
    db_session.commit()
    resp = client.post("/api/v1/connectors", json=CONNECTOR_BODY, headers=VIEWER)
    assert resp.status_code == 403

    resp = client.post("/api/v1/connectors", json=CONNECTOR_BODY, headers=ADMIN)
    assert resp.status_code == 201
    cid = resp.json()["id"]
    assert resp.json()["base_url"] == "https://api.quant.example.com"

    # auth_style != none 但缺 api_key_env → 400
    bad = {**CONNECTOR_BODY, "api_key_env": None}
    assert client.post("/api/v1/connectors", json=bad, headers=ADMIN).status_code == 400
    # header 鉴权缺 header 名 → 400
    bad2 = {**CONNECTOR_BODY, "auth_style": "header", "auth_header_name": None}
    assert client.post("/api/v1/connectors", json=bad2, headers=ADMIN).status_code == 400

    listing = client.get("/api/v1/connectors", headers=EDITOR).json()
    assert any(c["id"] == cid for c in listing)

    detail = client.get(f"/api/v1/connectors/{cid}", headers=EDITOR).json()
    assert detail["endpoints"] == []

    assert client.delete(f"/api/v1/connectors/{cid}", headers=ADMIN).status_code == 204
    assert client.get(f"/api/v1/connectors/{cid}", headers=ADMIN).status_code == 404


def test_endpoint_requires_mapping_fields(client, seed_admin):
    resp = client.post("/api/v1/connectors", json=CONNECTOR_BODY, headers=ADMIN)
    cid = resp.json()["id"]
    bad = {**ENDPOINT_BODY, "fact_mapping": {"items_path": "data"}}
    resp = client.post(f"/api/v1/connectors/{cid}/endpoints", json=bad, headers=ADMIN)
    assert resp.status_code == 400


def test_pull_maps_json_to_facts(client, monkeypatch, seed_admin):
    captured = {}
    connector_id, _ = _setup_connector_and_endpoint(client, monkeypatch, captured=captured)
    detail = client.get(f"/api/v1/connectors/{connector_id}", headers=ADMIN).json()
    endpoint_id = detail["endpoints"][0]["id"]

    resp = client.post(f"/api/v1/endpoints/{endpoint_id}/pull", headers=EDITOR)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["facts"] == 2

    # 鉴权 header 注入 + {today} 占位符替换
    assert captured["headers"]["Authorization"] == "Bearer test-secret"
    assert "date=20" in captured["url"]

    # Source 与 Fact 落库正确
    source = client.get(f"/api/v1/sources/{body['source_id']}", headers=EDITOR).json()
    assert source["source_type"] == "connector"
    assert source["as_of"] == "2026-09-17"
    assert source["title"] .startswith("20") and source["title"].endswith("市场复盘")
    statements = [f["statement"] for f in source["facts"]]
    assert "沪深300 当日涨跌幅 1.2%" in statements
    assert "中证500 当日涨跌幅 -0.8%" in statements
    fact = next(f for f in source["facts"] if "沪深300" in f["statement"])
    assert fact["value"] == 1.2 and fact["unit"] == "%"
    assert fact["status"] == "candidate"
    assert fact["as_of"] == "2026-09-17"
    assert fact["subject"] == "沪深300"

    # 拉取状态回写
    refreshed = client.get(f"/api/v1/connectors/{detail['id']}", headers=ADMIN).json()
    assert refreshed["endpoints"][0]["last_pull_status"] == "ok"


def test_pull_missing_env_key_reports_clearly(client, monkeypatch, seed_admin):
    monkeypatch.delenv("QUANT_API_KEY", raising=False)
    monkeypatch.setattr(connector_service, "safe_fetch", lambda url, headers=None, **kw: (b"{}", "application/json"))
    resp = client.post("/api/v1/connectors", json=CONNECTOR_BODY, headers=ADMIN)
    detail = client.get(f"/api/v1/connectors/{resp.json()['id']}", headers=ADMIN).json()
    endpoint_id = detail["endpoints"][0]["id"] if detail["endpoints"] else None
    # endpoint 未创建时先建
    if endpoint_id is None:
        r = client.post(f"/api/v1/connectors/{resp.json()['id']}/endpoints", json=ENDPOINT_BODY, headers=ADMIN)
        endpoint_id = r.json()["id"]
    resp = client.post(f"/api/v1/endpoints/{endpoint_id}/pull", headers=EDITOR)
    assert resp.status_code == 400
    assert "QUANT_API_KEY" in resp.json()["detail"]


def test_pull_bad_mapping_path(client, monkeypatch, seed_admin):
    _setup_connector_and_endpoint(client, monkeypatch, api_json={"data": {"rows": [{"name": "x"}]}})
    listing = client.get("/api/v1/connectors", headers=ADMIN).json()
    detail = client.get(f"/api/v1/connectors/{listing[0]['id']}", headers=ADMIN).json()
    endpoint_id = detail["endpoints"][0]["id"]

    resp = client.post(f"/api/v1/endpoints/{endpoint_id}/pull", headers=EDITOR)
    assert resp.status_code == 400
    assert "不存在" in resp.json()["detail"]
    # 失败留痕
    refreshed = client.get(f"/api/v1/connectors/{listing[0]['id']}", headers=ADMIN).json()
    assert refreshed["endpoints"][0]["last_pull_status"] == "failed"


def test_map_response_single_object(client):
    payload = {"name": "上证指数", "close": 3200.5, "date": "2026-09-17"}
    mapping = {"statement": "{name} 收盘 {close}点", "fields": {"value": "{close}", "unit": "点"}}
    facts = connector_service.map_response_to_facts(payload, mapping, "2026-09-17")
    assert len(facts) == 1
    assert facts[0].statement == "上证指数 收盘 3200.5点"
    assert facts[0].value == 3200.5
    assert facts[0].unit == "点"


def test_map_response_missing_statement_template():
    try:
        connector_service.map_response_to_facts({"a": 1}, {"fields": {"value": "{a}"}}, None)
        raise AssertionError("应抛 ConnectorError")
    except ConnectorError as exc:
        assert "statement" in str(exc)


def _setup_post_pagination_endpoint(client, monkeypatch, pages):
    """两页数据 + POST + page 分页的 endpoint；safe_fetch 记录每次请求。"""
    captured = {"calls": []}

    def fake_fetch(url, headers=None, method="GET", json_body=None):
        captured["calls"].append({"url": url, "method": method, "body": dict(json_body)})
        rows = pages.get(int(json_body["page"]), [])
        return json.dumps({"data": {"rows": rows}}, ensure_ascii=False).encode(), "application/json"

    monkeypatch.setenv("QUANT_API_KEY", "test-secret")
    resp = client.post("/api/v1/connectors", json=CONNECTOR_BODY, headers=ADMIN)
    connector_id = resp.json()["id"]
    resp = client.post(
        f"/api/v1/connectors/{connector_id}/endpoints",
        json={
            "name": "分页复盘",
            "path": "/api/v1/market/daily",
            "method": "POST",
            "body_template": {"date": "{today}", "page": 0},
            "title_template": "{today} 分页拉取",
            "fact_mapping": {
                "items_path": "data.rows",
                "statement": "{index_name} 涨跌 {pct_change}%",
                "fields": {"value": "{pct_change}", "subject": "{index_name}", "unit": "%"},
            },
            "pagination": {"type": "page", "page_param": "page", "page_start": 1, "max_pages": 5},
        },
        headers=ADMIN,
    )
    assert resp.status_code == 201, resp.text
    endpoint_id = resp.json()["id"]
    monkeypatch.setattr(connector_service, "safe_fetch", fake_fetch)
    return connector_id, endpoint_id, captured


def test_pull_post_pagination(client, monkeypatch, seed_admin):
    pages = {
        1: [{"index_name": "沪深300", "pct_change": 1.2}],
        2: [{"index_name": "中证500", "pct_change": -0.8}],
        3: [],  # 空页停止
    }
    _connector_id, endpoint_id, captured = _setup_post_pagination_endpoint(client, monkeypatch, pages)

    resp = client.post(f"/api/v1/endpoints/{endpoint_id}/pull", headers=EDITOR)
    assert resp.status_code == 200, resp.text
    assert resp.json()["facts"] == 2

    # POST 请求 + 分页参数递增 + {today} 占位符替换
    methods = [c["method"] for c in captured["calls"]]
    assert methods == ["POST", "POST", "POST"]
    bodies = [c["body"] for c in captured["calls"]]
    assert [b["page"] for b in bodies] == ["1", "2", "3"]
    assert all(b["date"].startswith("20") for b in bodies)

    source = client.get(f"/api/v1/sources/{resp.json()['source_id']}", headers=EDITOR).json()
    assert len(source["facts"]) == 2


def test_pull_post_requires_body_template(client, seed_admin):
    resp = client.post("/api/v1/connectors", json=CONNECTOR_BODY, headers=ADMIN)
    cid = resp.json()["id"]
    bad = {**ENDPOINT_BODY, "method": "POST"}
    resp = client.post(f"/api/v1/connectors/{cid}/endpoints", json=bad, headers=ADMIN)
    assert resp.status_code == 400


def test_pull_cursor_pagination(client, monkeypatch, seed_admin):
    """cursor 分页：从响应 next_cursor 取游标，缺失即停。"""
    captured = {"calls": []}
    cursor_state = {"n": 0}

    def fake_fetch(url, headers=None, method="GET", json_body=None):
        cursor_state["n"] += 1
        captured["calls"].append(url)
        if cursor_state["n"] == 1:
            payload = {"rows": [{"index_name": "上证指数", "pct_change": 0.5}], "next_cursor": "abc123"}
        else:
            payload = {"rows": [{"index_name": "深证成指", "pct_change": 0.9}]}
        return json.dumps(payload, ensure_ascii=False).encode(), "application/json"

    monkeypatch.setenv("QUANT_API_KEY", "test-secret")
    resp = client.post("/api/v1/connectors", json=CONNECTOR_BODY, headers=ADMIN)
    cid = resp.json()["id"]
    resp = client.post(
        f"/api/v1/connectors/{cid}/endpoints",
        json={
            "name": "游标拉取",
            "path": "/api/v1/market/daily",
            "title_template": "游标数据",
            "fact_mapping": {
                "items_path": "rows",
                "statement": "{index_name} 涨跌 {pct_change}%",
                "fields": {"value": "{pct_change}", "unit": "%"},
            },
            "pagination": {"type": "cursor", "cursor_param": "cursor", "cursor_path": "next_cursor", "max_pages": 5},
        },
        headers=ADMIN,
    )
    endpoint_id = resp.json()["id"]
    monkeypatch.setattr(connector_service, "safe_fetch", fake_fetch)

    resp = client.post(f"/api/v1/endpoints/{endpoint_id}/pull", headers=EDITOR)
    assert resp.status_code == 200, resp.text
    assert resp.json()["facts"] == 2
    # 第二次请求带上了第一页返回的游标
    assert "cursor=abc123" in captured["calls"][1]
