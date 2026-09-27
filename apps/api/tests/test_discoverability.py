"""Discoverability（V1 PRD 2.0 / capability: discoverability-optimization）。

覆盖：Pre/Post 报告生成（mock LLM 容忍 incomplete）；报告独立于 prompt；
apply 建议产生新 Draft Revision 且 downstream stale；profiles 幂等 seeding。
"""

import pytest

from app.models import (
    ContentJob,
    DiscoverabilityReport,
    Draft,
    FactPack,
    TopicBrief,
    User,
)
from app.services import checks as checks_service
from app.services import discoverability as disco

EDITOR = {"X-Studio-User": "editor@studio.local"}


@pytest.fixture
def env(db_session):
    db_session.add(User(email="editor@studio.local", name="E", role="editor"))
    pack = FactPack(name="seo包", version=1, status="frozen", checksum="d" * 64)
    db_session.add(pack)
    db_session.flush()
    topic = TopicBrief(title="量化数据 Grip：三个信号", fact_pack_id=pack.id, fact_pack_version=1, goal="科普")
    db_session.add(topic)
    db_session.flush()
    job = ContentJob(topic_brief_id=topic.id, channel="wechat", content_form="article", status="succeeded")
    db_session.add(job)
    db_session.flush()
    draft = Draft(content_job_id=job.id, revision_no=1, title="原标题", body="第一段\n\n第二段")
    db_session.add(draft)
    db_session.commit()
    return db_session, topic, draft


def test_seed_default_profiles_idempotent(db_session):
    assert disco.seed_default_profiles(db_session) >= 1
    assert disco.seed_default_profiles(db_session) == 0  # 幂等


def test_pre_and_post_reports_created(env, client):
    _db, topic, draft = env
    pre = client.post(f"/api/v1/topics/{topic.id}/discoverability/pre", headers=EDITOR)
    assert pre.status_code == 200, pre.json()
    # mock provider 不返回 SEO 结构 → incomplete（不是假装 ready）
    assert pre.json()["status"] == "incomplete"

    post = client.post(f"/api/v1/drafts/{draft.id}/discoverability/post", headers=EDITOR)
    assert post.status_code == 200
    listing = client.get(f"/api/v1/drafts/{draft.id}/discoverability", headers=EDITOR)
    assert len(listing.json()) == 1
    assert listing.json()[0]["stage"] == "post"


def test_apply_suggestion_creates_new_revision_and_stale(env):
    """SEO 建议不自动改稿：apply → 新 revision，旧稿/下游不漂移。"""
    db, topic, draft = env
    report = DiscoverabilityReport(
        topic_id=topic.id, draft_id=draft.id, stage="post", channel="wechat", content_form="article",
        input_hash="x" * 64, status="ready",
        report_json={"title_suggestions": ["SEO 标题 A", "SEO 标题 B"], "issues": []},
    )
    db.add(report)
    db.commit()
    old_id = draft.id

    resp = client = None
    from fastapi.testclient import TestClient

    from app.db import get_db
    from app.main import app

    def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    client = TestClient(app)

    resp = client.post(
        f"/api/v1/drafts/{draft.id}/discoverability/{report.id}/apply",
        json={"title_index": 0},
        headers=EDITOR,
    )
    assert resp.status_code == 200, resp.json()
    body = resp.json()
    assert body["new_draft_id"] != old_id
    assert body["applied_title"] == "SEO 标题 A"

    db.expire_all()
    new_draft = db.get(Draft, body["new_draft_id"])
    assert new_draft.revision_no == draft.revision_no + 1
    assert new_draft.candidate_readiness == "stale"  # downstream stale
    assert new_draft.body == draft.body  # 正文未变（只应用标题）

    # 越界拒绝
    bad = client.post(
        f"/api/v1/drafts/{draft.id}/discoverability/{report.id}/apply",
        json={"title_index": 9},
        headers=EDITOR,
    )
    assert bad.status_code == 422


def test_seo_check_runs_alongside_report(env):
    """确定性 SEO 字段检查与 LLM 报告是两条线（check run + report）。"""
    db, _topic, draft = env
    run = checks_service.run_seo_check(db, draft)
    db.commit()
    assert run.check_kind == "seo"
    assert run.status in {"pass", "warning"}
