"""Celery 队列分发测试：默认同步；开关打开时分发到队列且不依赖真实 broker。"""

import pytest

from app.config import get_settings
from app.models import JobStatus


@pytest.fixture
def seed_admin(db_session):
    from app.models import User

    db_session.add(User(email="admin@studio.local", name="Admin", role="admin"))
    db_session.commit()


def _build_frozen_pack_and_topic(client, db_session):
    """搭最小链路：来源→事实→确认→pack 冻结→topic。返回 topic_id。"""
    r = client.post(
        "/api/v1/sources/text",
        json={"title": "复盘", "as_of": "2026-09-17", "content": "沪深300上涨1.2%，成交额1.1万亿。"},
        headers={"X-Studio-User": "admin@studio.local"},
    )
    source_id = r.json()["id"]
    client.post(f"/api/v1/sources/{source_id}/extract-facts", headers={"X-Studio-User": "admin@studio.local"})
    fact_ids = [f["id"] for f in client.get(f"/api/v1/sources/{source_id}", headers={"X-Studio-User": "admin@studio.local"}).json()["facts"]]
    for fid in fact_ids:
        client.post(f"/api/v1/facts/{fid}/confirm", headers={"X-Studio-User": "admin@studio.local"})
    pack = client.post(
        "/api/v1/fact-packs",
        json={"name": "队列测试包", "fact_ids": fact_ids},
        headers={"X-Studio-User": "admin@studio.local"},
    ).json()
    client.post(f"/api/v1/fact-packs/{pack['id']}/freeze", headers={"X-Studio-User": "admin@studio.local"})
    topic = client.post(
        "/api/v1/topics",
        json={"title": "队列测试选题", "fact_pack_id": pack["id"], "channels": ["douyin"]},
        headers={"X-Studio-User": "admin@studio.local"},
    ).json()
    return topic["id"]


def test_generation_sync_by_default(client, db_session, seed_admin):
    topic_id = _build_frozen_pack_and_topic(client, db_session)
    assert get_settings().task_queue_enabled is False

    resp = client.post(f"/api/v1/topics/{topic_id}/generate", headers={"X-Studio-User": "editor@studio.local"})
    assert resp.status_code == 201
    job = resp.json()["jobs"][0]
    assert job["status"] == JobStatus.succeeded.value
    assert job["draft_id"]


def test_generation_dispatches_to_queue_when_enabled(client, db_session, seed_admin, monkeypatch):
    topic_id = _build_frozen_pack_and_topic(client, db_session)
    monkeypatch.setenv("TASK_QUEUE_ENABLED", "true")
    get_settings.cache_clear()
    try:
        delayed = []
        from app.tasks import worker_tasks

        monkeypatch.setattr(worker_tasks.run_generation_job, "delay", lambda job_id: delayed.append(job_id))

        resp = client.post(f"/api/v1/topics/{topic_id}/generate", headers={"X-Studio-User": "editor@studio.local"})
        assert resp.status_code == 201
        job = resp.json()["jobs"][0]
        assert job["status"] == JobStatus.queued.value
        assert "draft_id" not in job
        assert delayed == [job["job_id"]]

        # job 落库为 queued，生成接口重复触发被 409 拒绝
        detail = client.get(f"/api/v1/content-jobs/{job['job_id']}", headers={"X-Studio-User": "editor@studio.local"}).json()
        assert detail["status"] == "queued"
        resp2 = client.post(f"/api/v1/content-jobs/{job['job_id']}/regenerate", headers={"X-Studio-User": "editor@studio.local"})
        assert resp2.status_code == 409
    finally:
        get_settings.cache_clear()


def test_worker_task_function_executes_locally(client, db_session, seed_admin):
    """task.apply() 本地执行不经过 broker：验证任务函数本身可被 worker 消费。"""
    topic_id = _build_frozen_pack_and_topic(client, db_session)
    resp = client.post(f"/api/v1/topics/{topic_id}/generate", headers={"X-Studio-User": "editor@studio.local"})
    job_id = resp.json()["jobs"][0]["job_id"]

    from app.tasks.worker_tasks import run_generation_job

    result = run_generation_job.apply(args=[job_id + 1000]).get()  # 不存在的 job 应安全返回
    assert result["status"] == "unknown"


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
