"""Celery 队列：到期的数据接入端点被定时扫描并分发。"""

import pytest


@pytest.fixture
def seed_admin(db_session):
    from app.models import User

    db_session.add(User(email="admin@studio.local", name="Admin", role="admin"))
    db_session.commit()


def test_scan_connector_schedules_dispatches_due(client, db_session, seed_admin, monkeypatch):
    """interval 到期的 endpoint 被扫描任务分发；未到期/未配置的不分发。"""
    from datetime import UTC, datetime, timedelta

    from app.models import Connector, ConnectorEndpoint

    db_session.add_all(
        [
            Connector(id=1, name="c", base_url="https://api.example.com", auth_style="none", is_active=True),
            ConnectorEndpoint(id=11, connector_id=1, name="到期", path="/a", title_template="t",
                              fact_mapping_json={"statement": "{v}", "fields": {"value": "{v}"}},
                              interval_minutes=30, last_pull_at=datetime.now(UTC) - timedelta(minutes=60)),
            ConnectorEndpoint(id=12, connector_id=1, name="未到期", path="/b", title_template="t",
                              fact_mapping_json={"statement": "{v}", "fields": {"value": "{v}"}},
                              interval_minutes=30, last_pull_at=datetime.now(UTC)),
            ConnectorEndpoint(id=13, connector_id=1, name="不定时", path="/c", title_template="t",
                              fact_mapping_json={"statement": "{v}", "fields": {"value": "{v}"}},
                              interval_minutes=None),
        ]
    )
    db_session.commit()

    delayed = []
    from app.tasks import worker_tasks

    monkeypatch.setattr(worker_tasks.pull_connector_endpoint, "delay", lambda eid, actor: delayed.append(eid))
    # 任务默认用模块级 SessionLocal（worker 进程独立 DB session）；测试指向内存库
    monkeypatch.setattr(worker_tasks, "SessionLocal", lambda: db_session)
    result = worker_tasks.scan_connector_schedules.apply().get()
    assert result["dispatched"] == [11]
    assert delayed == [11]
