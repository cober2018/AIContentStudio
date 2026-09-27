"""掘金技术规则（V1 PRD 2.0 / capability: v1-platform-artifacts — Juejin）。"""

import pytest

from app.models import ContentJob, Draft, FactPack, TopicBrief, User
from app.services.content_harness.rules import RuleContext, evaluate_rule_set, worst_status


@pytest.fixture
def draft(db_session):
    db_session.add(User(email="editor@studio.local", name="E", role="editor"))
    pack = FactPack(name="tech包", version=1, status="frozen", checksum="f" * 64)
    db_session.add(pack)
    db_session.flush()
    topic = TopicBrief(title="tech", fact_pack_id=pack.id, fact_pack_version=1)
    db_session.add(topic)
    db_session.flush()
    job = ContentJob(topic_brief_id=topic.id, channel="juejin", content_form="tech_article", status="succeeded")
    db_session.add(job)
    db_session.flush()
    row = Draft(content_job_id=job.id, revision_no=1, title="t", body="正文")
    db_session.add(row)
    db_session.commit()
    return row


def test_no_code_passes(db_session, draft):
    results = evaluate_rule_set(db_session, ["rule.tech.code_provenance"], RuleContext(draft=draft, channel="juejin", content_form="tech_article"))
    assert worst_status(results) == "pass"


def test_code_without_verified_marker_warns(db_session, draft):
    draft.body = "```python\nprint('hi')\n```"
    results = evaluate_rule_set(db_session, ["rule.tech.code_provenance"], RuleContext(draft=draft, channel="juejin", content_form="tech_article"))
    assert worst_status(results) == "warning"


def test_verified_runnable_without_provenance_blocks(db_session, draft):
    """无依据代码不得被标记为 verified runnable（blocking）。"""
    draft.body = "```python\nprint('hi')\n```\n以上代码 verified-runnable。"
    results = evaluate_rule_set(db_session, ["rule.tech.code_provenance"], RuleContext(draft=draft, channel="juejin", content_form="tech_article"))
    assert worst_status(results) == "blocker"

    draft.structured_json = {"code_provenance": {"repo": "https://github.com/x/y", "commit": "abc"}}
    results2 = evaluate_rule_set(db_session, ["rule.tech.code_provenance"], RuleContext(draft=draft, channel="juejin", content_form="tech_article"))
    assert worst_status(results2) in {"pass", "warning"}
