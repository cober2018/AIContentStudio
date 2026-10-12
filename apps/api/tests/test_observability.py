"""可观测性测试：/health 深探针、/metrics 指标、trace_id 响应头与结构化日志。"""

import json

from sqlalchemy import text


def _approved_schema(db):
    from app.db import LOCAL_APPROVED_SCHEMA_HEAD

    # Metadata-only fixtures have no migration ledger; readiness must not pretend otherwise.
    db.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL PRIMARY KEY)"))
    db.execute(text("INSERT INTO alembic_version VALUES (:head)"), {"head": LOCAL_APPROVED_SCHEMA_HEAD})
    db.commit()


def test_health_deep_probe(client, db_session):
    _approved_schema(db_session)
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["db"] is True
    assert data["provider"] == "mock"
    assert "queue_enabled" in data


def test_health_rejects_database_without_migration_ledger(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 503
    assert resp.json()["schema"] is False
    assert "schema_head_mismatch" in resp.json()["reasons"]


def test_metrics_counts_requests(client):
    client.get("/api/v1/health")
    client.get("/api/v1/health")
    resp = client.get("/metrics")
    assert resp.status_code == 200
    body = resp.text
    assert "http_requests_total" in body
    assert 'path="/api/v1/health"' in body
    assert "process_uptime_seconds" in body
    # 指标端点自身不计数
    assert 'path="/metrics"' not in body


def test_trace_id_in_response_header_and_log(client, caplog, db_session):
    import logging

    _approved_schema(db_session)
    with caplog.at_level(logging.INFO, logger="studio.request"):
        resp = client.get("/api/v1/health")
    trace_id = resp.headers.get("x-trace-id")
    assert trace_id, "响应必须带 x-trace-id"

    log_records = [r.getMessage() for r in caplog.records if "http_request" in r.getMessage()]
    assert log_records
    entry = json.loads(log_records[-1])
    assert entry["trace_id"] == trace_id
    assert entry["path"] == "/api/v1/health"
    assert entry["status"] == 200
    assert "duration_ms" in entry
