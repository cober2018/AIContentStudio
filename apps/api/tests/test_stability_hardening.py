"""稳定性加固回归：provider 调用槽位可恢复 + 僵尸 running 状态回收。"""

import threading
import time
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.models import (
    AuditLog,
    Workflow,
    WorkflowRun,
    WorkflowStep,
    utcnow,
)
from app.services import provider_calls
from app.services.maintenance import reap_stale_running


def _wait_until(predicate, timeout: float = 2.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.02)
    raise AssertionError("condition not met in time")


def test_provider_timeout_releases_slot_for_later_calls():
    """挂死的调用超时后不得永久占用槽位（历史缺陷：两次挂死即全站外呼瘫痪）。"""
    release = threading.Event()

    def hung(_request):
        release.wait(10)
        return "late"

    with pytest.raises(TimeoutError):
        provider_calls.call(hung, {}, timeout_seconds=0.2)
    assert provider_calls.abandoned_calls() == 1
    # 槽位已归还：挂死调用不拖累后续调用
    assert provider_calls.call(lambda request: "ok", {}) == "ok"

    release.set()
    _wait_until(lambda: provider_calls.abandoned_calls() == 0)


def test_provider_capacity_bound_still_enforced():
    release1, release2 = threading.Event(), threading.Event()
    failures: list[BaseException] = []

    def run(release):
        try:
            provider_calls.call(lambda request: release.wait(5), {}, timeout_seconds=5)
        except BaseException as exc:  # noqa: BLE001 记录线程内异常供断言
            failures.append(exc)

    thread1 = threading.Thread(target=run, args=(release1,), daemon=True)
    thread2 = threading.Thread(target=run, args=(release2,), daemon=True)
    thread1.start()
    thread2.start()
    try:
        _wait_until(lambda: provider_calls.abandoned_calls() >= 0 and thread1.is_alive() and thread2.is_alive())
        # 两个槽位被占满时，第三个调用必须立即拒绝而不是排队
        with pytest.raises(provider_calls.ProviderCapacityError):
            provider_calls.call(lambda request: "never", {})
    finally:
        release1.set()
        release2.set()
        thread1.join(timeout=2)
        thread2.join(timeout=2)
    assert failures == []


def test_provider_worker_exception_propagates():
    def boom(_request):
        raise RuntimeError("provider exploded")

    with pytest.raises(RuntimeError, match="provider exploded"):
        provider_calls.call(boom, {})


def test_reap_stale_running_fails_only_stale_rows(db_session):
    workflow = Workflow(name="reap-flow", definition_json={"nodes": [], "edges": []})
    db_session.add(workflow)
    db_session.flush()

    stale_run = WorkflowRun(workflow_id=workflow.id, status="running", started_at=utcnow() - timedelta(hours=2))
    fresh_run = WorkflowRun(workflow_id=workflow.id, status="running", started_at=utcnow())
    done_run = WorkflowRun(workflow_id=workflow.id, status="succeeded", started_at=utcnow() - timedelta(hours=3))
    db_session.add_all([stale_run, fresh_run, done_run])
    db_session.flush()
    stale_step = WorkflowStep(run_id=stale_run.id, node_id="n1", node_type="generate", status="running",
                              started_at=utcnow() - timedelta(hours=2))
    fresh_step = WorkflowStep(run_id=fresh_run.id, node_id="n2", node_type="generate", status="running",
                              started_at=utcnow())
    db_session.add_all([stale_step, fresh_step])
    db_session.commit()

    stats = reap_stale_running(db_session, stale_seconds=1800)

    assert stats["workflow_runs"] == [stale_run.id]
    assert stats["workflow_steps"] == [stale_step.id]

    reaped_run = db_session.get(WorkflowRun, stale_run.id)
    assert reaped_run.status == "failed" and reaped_run.finished_at is not None
    assert "reaped:stale_running" in reaped_run.error
    assert db_session.get(WorkflowRun, fresh_run.id).status == "running"
    assert db_session.get(WorkflowRun, done_run.id).status == "succeeded"
    assert db_session.get(WorkflowStep, stale_step.id).status == "failed"
    assert db_session.get(WorkflowStep, fresh_step.id).status == "running"

    audit = db_session.scalars(
        select(AuditLog).where(AuditLog.event == "maintenance.stale_running_reaped")
    ).one()
    assert audit.actor == "system:maintenance"
    assert audit.detail_json["workflow_runs"] == [stale_run.id]


def test_reap_disabled_keeps_everything(db_session):
    workflow = Workflow(name="reap-off", definition_json={"nodes": [], "edges": []})
    db_session.add(workflow)
    db_session.flush()
    db_session.add(WorkflowRun(workflow_id=workflow.id, status="running",
                               started_at=utcnow() - timedelta(days=30)))
    db_session.commit()

    assert reap_stale_running(db_session, stale_seconds=0) == {"disabled": True}
    db_session.expire_all()
    assert db_session.query(WorkflowRun).one().status == "running"
