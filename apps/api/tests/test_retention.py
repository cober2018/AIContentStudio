"""数据保留策略测试：llm_run 大字段瘦身 / 审计与工作流过期删除 / 新数据不动。"""

from datetime import UTC, datetime, timedelta

from app.models import AuditLog, LLMRun, WorkflowRun, WorkflowStep
from app.services.retention import run_retention


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
