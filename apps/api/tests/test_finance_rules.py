"""财务/技术领域规则（V1 PRD 2.0 / capability: v1-platform-artifacts）。

雪球 quant/market_recap：as_of + no-return-guarantee mandatory；
掘金 tech_article：verified runnable 必须有 provenance。
"""

import pytest

from app.models import ContentJob, Draft, FactPack, TopicBrief, User
from app.services import checks as checks_service
from app.services.content_harness.domain_rules import rules_for_form
from app.services.content_harness.rules import RuleContext, evaluate_rule_set, worst_status


@pytest.fixture
def make_draft(db_session):
    db_session.add(User(email="editor@studio.local", name="E", role="editor"))
    pack = FactPack(name="规则包", version=1, status="frozen", checksum="e" * 64)
    db_session.add(pack)
    db_session.flush()
    topic = TopicBrief(title="规则测试", fact_pack_id=pack.id, fact_pack_version=1)
    db_session.add(topic)
    db_session.flush()

    def _make(channel: str, content_form: str) -> Draft:
        job = ContentJob(topic_brief_id=topic.id, channel=channel, content_form=content_form, status="succeeded")
        db_session.add(job)
        db_session.flush()
        draft = Draft(content_job_id=job.id, revision_no=1, title="t", body="正文")
        db_session.add(draft)
        db_session.commit()
        return draft

    return _make


def test_rules_for_form_mapping():
    assert set(rules_for_form("quant_research")) == {"rule.finance.as_of", "rule.finance.no_return_guarantee"}
    assert set(rules_for_form("market_recap")) == {"rule.finance.as_of", "rule.finance.no_return_guarantee"}
    assert rules_for_form("tech_article") == ["rule.tech.code_provenance"]
    assert rules_for_form("article") == []


def test_xueqiu_as_of_mandatory(db_session, make_draft):
    draft = make_draft("xueqiu", "market_recap")
    results = evaluate_rule_set(db_session, ["rule.finance.as_of"], RuleContext(draft=draft, channel="xueqiu", content_form="market_recap"))
    assert worst_status(results) == "blocker"  # 无 as_of

    draft.body = "截至 2026-09-20，该指数上涨 1.2%。"
    results2 = evaluate_rule_set(db_session, ["rule.finance.as_of"], RuleContext(draft=draft, channel="xueqiu", content_form="market_recap"))
    assert worst_status(results2) == "pass"


def test_xueqiu_no_return_guarantee_blocker(db_session, make_draft):
    draft = make_draft("xueqiu", "quant_research")
    draft.body = "该策略稳赚不赔，保证收益 20%。"
    results = evaluate_rule_set(db_session, ["rule.finance.no_return_guarantee"], RuleContext(draft=draft, channel="xueqiu", content_form="quant_research"))
    assert worst_status(results) == "blocker"
    assert results[0].details["forbidden_hits"]

    draft.body = "该策略年化区间 -5% 到 8%，不构成投资建议。"
    results2 = evaluate_rule_set(db_session, ["rule.finance.no_return_guarantee"], RuleContext(draft=draft, channel="xueqiu", content_form="quant_research"))
    assert worst_status(results2) == "pass"


def test_xueqiu_rules_block_approval_path_via_checks(db_session, make_draft):
    """财务 RuleSet 未完成时不可批准：mandatory domain check blocker。"""
    draft = make_draft("xueqiu", "quant_research")
    runs = checks_service.run_domain_checks(db_session, draft, content_form="quant_research")
    db_session.commit()
    kinds = {r.check_kind: r for r in runs}
    assert kinds["domain"].status == "blocker"
    # incomplete/blocker 的 mandatory 检查 = missing
    assert "domain" in checks_service.missing_mandatory_kinds(db_session, draft, required=["fact", "platform", "domain"])
