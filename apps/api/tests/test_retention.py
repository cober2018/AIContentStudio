"""数据保留策略测试：llm_run 大字段瘦身 / 审计与工作流过期删除 / 新数据不动。"""

import threading
from datetime import UTC, datetime, timedelta

from app.models import AuditLog, LLMRun, WorkflowRun, WorkflowStep
from app.services import asset_media
from app.services.material_byte_lock import locked_hash
from app.services.materials import store_bytes
from app.services.retention import run_retention
from app.tasks.celery_app import celery_app
from app.tasks.worker_tasks import retention_sweep


def _old(days):
    return datetime.now(UTC) - timedelta(days=days)


def test_retention_llm_run_payload_cleared_row_kept(db_session):
    old_run = LLMRun(provider="p", model="m", purpose="generate", raw_output="x" * 1000,
                     parsed_output_json={"a": 1}, status="succeeded", created_at=_old(40))
    new_run = LLMRun(provider="p", model="m", purpose="generate", raw_output="y" * 100,
                     status="succeeded", created_at=_old(1))
    db_session.add_all([old_run, new_run])
    db_session.commit()
    stats = run_retention(db_session)
    assert stats["llm_run_payloads_cleared"] == 1
    db_session.expire_all()
    assert db_session.get(LLMRun, old_run.id).raw_output is None  # 大字段清空
    assert db_session.get(LLMRun, old_run.id).status == "succeeded"  # 行保留（审计线索）
    assert db_session.get(LLMRun, new_run.id).raw_output == "y" * 100  # 新数据不动


def test_retention_audit_and_workflow(db_session):
    db_session.add(AuditLog(event="e", entity_type="t", created_at=_old(100)))
    db_session.add(AuditLog(event="e2", entity_type="t", created_at=_old(1)))
    run = WorkflowRun(workflow_id=1, status="succeeded", finished_at=_old(40))
    db_session.add(run)
    db_session.flush()
    db_session.add(WorkflowStep(run_id=run.id, node_id="n", node_type="generate", params_json={}, status="succeeded"))
    live = WorkflowRun(workflow_id=1, status="waiting_input")  # 未终态不删
    db_session.add(live)
    db_session.commit()
    rid, lid = run.id, live.id
    stats = run_retention(db_session)
    assert stats["audit_log_deleted"] >= 1
    assert stats["workflow_runs_deleted"] == 1
    assert db_session.get(WorkflowRun, rid) is None
    assert db_session.get(WorkflowRun, lid) is not None


def test_unprocessed_material_byte_candidate_survives_audit_expiry(db_session):
    candidate = AuditLog(event="material.upload_orphan_candidate", entity_type="material_bytes", entity_id="a" * 50, detail_json={"file_path": "material/aa/" + "a" * 64 + ".png", "content_hash": "a" * 64}, created_at=_old(100))
    db_session.add(candidate)
    db_session.commit()
    run_retention(db_session, {"batch": 0})
    assert db_session.get(AuditLog, candidate.id) is not None


def test_retention_task_is_registered_for_beat():
    scheduled = celery_app.conf.beat_schedule["retention-sweep"]["task"]
    assert scheduled == retention_sweep.name
    assert scheduled in celery_app.tasks


def test_material_writer_holds_hash_lock_until_commit(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(asset_media, "MEDIA_ROOT", tmp_path)
    _, content_hash = store_bytes(db_session, b"same material", subdir="material", suffix=".bin")
    attempted = threading.Event()
    acquired = threading.Event()

    def cleanup_waiter():
        attempted.set()
        with locked_hash(content_hash):
            acquired.set()

    thread = threading.Thread(target=cleanup_waiter, daemon=True)
    thread.start()
    try:
        assert attempted.wait(1)
        assert not acquired.wait(0.1)
    finally:
        db_session.commit()
        thread.join(timeout=1)
    assert acquired.is_set()
