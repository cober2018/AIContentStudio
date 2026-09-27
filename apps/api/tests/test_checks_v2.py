"""统一检查体系（V1 PRD 2.0 / capability: unified-check-runs）。

覆盖：FactCheck 双写（fact_check_json + DraftCheckRun）；规则集 → check runs；
incomplete 不是 pass；输入变化 stale；mandatory 未完成不允许批准前置语义。
"""

import pytest

from app.models import (
    ContentJob,
    Draft,
    FactPack,
    TopicBrief,
    User,
)
from app.services import checks as checks_service

EDITOR = {"X-Studio-User": "editor@studio.local"}
PNG = b"\x89PNG\r\n\x1a\n" + b"img" * 8


@pytest.fixture
def draft(db_session):
    db_session.add(User(email="editor@studio.local", name="E", role="editor"))
    pack = FactPack(name="checks包", version=1, status="frozen", checksum="c" * 64)
    db_session.add(pack)
    db_session.flush()
    topic = TopicBrief(title="checks", fact_pack_id=pack.id, fact_pack_version=1)
    db_session.add(topic)
    db_session.flush()
    job = ContentJob(topic_brief_id=topic.id, channel="wechat", content_form="article", status="succeeded")
    db_session.add(job)
    db_session.flush()
    row = Draft(content_job_id=job.id, revision_no=1, title="标题", body="正文")
    db_session.add(row)
    db_session.commit()
    return row


def test_fact_check_dual_write(client, db_session, inject_unfact, draft):
    """run_fact_check：fact_check_json 继续写 + 镜像 DraftCheckRun(kind=fact)。"""
    from app.services.candidates import draft_input_hash

    draft.input_hash = draft_input_hash(draft.title, draft.body, None)
    db_session.commit()
    resp = client.post(f"/api/v1/drafts/{draft.id}/fact-check", headers=EDITOR)
    assert resp.status_code == 200, resp.json()
    db_session.expire_all()
    assert draft.fact_check_json is not None  # 兼容字段仍在
    checks = checks_service.current_checks(db_session, draft)
    kinds = {c.check_kind for c in checks}
    assert "fact" in kinds
    fact_run = next(c for c in checks if c.check_kind == "fact")
    assert fact_run.input_hash == draft.input_hash
    assert fact_run.status in {"pass", "warning", "blocker"}


def test_rule_set_writes_platform_media_rights_checks(db_session, draft):
    runs = checks_service.run_rule_set(db_session, draft)
    db_session.commit()
    kinds = {r.check_kind for r in runs}
    assert {"platform", "media", "rights"} <= kinds
    # wechat cover 必需（legacy 兜底）→ media blocker
    media_run = next(r for r in runs if r.check_kind == "media")
    assert media_run.status == "blocker"
    assert "missing_cover" in media_run.report_json["rules"][0]["details"]["problems"]


def test_missing_mandatory_and_incomplete_is_not_pass(db_session, draft):
    """未运行的 mandatory 检查 = missing；incomplete 状态不算 pass。"""
    assert checks_service.missing_mandatory_kinds(db_session, draft) == ["fact", "platform"]
    checks_service.record_check_run(
        db_session, draft, check_kind="platform", status="incomplete", report={}, input_hash=None
    )
    db_session.commit()
    assert "platform" in checks_service.missing_mandatory_kinds(db_session, draft)


def test_checks_stale_after_input_change(db_session, draft):
    """输入变化后旧 check run 标 stale；Review Gate 不把旧 pass 当当前有效。"""
    from app.services.candidates import draft_input_hash

    draft.input_hash = draft_input_hash(draft.title, draft.body, None)
    run = checks_service.record_check_run(
        db_session, draft, check_kind="fact", status="pass", report={}, input_hash=draft.input_hash
    )
    db_session.commit()
    assert checks_service.checks_current_for_input(db_session, draft) is True

    # 输入变化
    draft.body = draft.body + "（新增段落）"
    draft.input_hash = draft_input_hash(draft.title, draft.body, None)
    db_session.commit()
    assert checks_service.checks_current_for_input(db_session, draft) is False
    checks_service.mark_all_stale(db_session, draft, reason="body_changed")
    db_session.commit()
    db_session.expire_all()
    assert run.status == "stale"


def test_checks_api_list_and_run(client, db_session, draft):
    listing = client.get(f"/api/v1/drafts/{draft.id}/checks", headers=EDITOR)
    assert listing.status_code == 200
    run_resp = client.post(f"/api/v1/drafts/{draft.id}/checks/platform", headers=EDITOR)
    assert run_resp.status_code == 200, run_resp.json()
    body = run_resp.json()
    assert body[0]["check_kind"] == "platform"

    seo = client.post(f"/api/v1/drafts/{draft.id}/checks/seo", headers=EDITOR)
    assert seo.status_code == 200

    bad = client.post(f"/api/v1/drafts/{draft.id}/checks/nonsense", headers=EDITOR)
    assert bad.status_code == 422


def test_seo_check_reads_structured_fields(db_session, draft):
    run = checks_service.run_seo_check(db_session, draft)
    db_session.commit()
    assert run.status in {"pass", "warning"}
    draft.title = ""
    run2 = checks_service.run_seo_check(db_session, draft)
    db_session.commit()
    assert run2.status == "blocker"
    assert "missing_title" in run2.report_json["problems"]
