"""Staleness 服务（V1 PRD 2.0 / D28）。"""

import pytest

from app.models import ContentAsset, ContentJob, Draft, DraftMedia, FactPack, TopicBrief
from app.services.content_harness import staleness


@pytest.fixture
def draft(db_session):
    pack = FactPack(name="stale包", version=1, status="frozen", checksum="s" * 64)
    db_session.add(pack)
    db_session.flush()
    topic = TopicBrief(title="stale", fact_pack_id=pack.id, fact_pack_version=1)
    db_session.add(topic)
    db_session.flush()
    job = ContentJob(topic_brief_id=topic.id, channel="wechat", status="succeeded")
    db_session.add(job)
    db_session.flush()
    row = Draft(content_job_id=job.id, revision_no=1, title="t", body="b", candidate_readiness="ready", fact_check_json={"result": "pass"})
    db_session.add(row)
    db_session.commit()
    return row


def test_mark_draft_changed_invalidates_candidate_and_fact_check(db_session, draft):
    staleness.mark_draft_changed(db_session, draft)
    assert draft.candidate_readiness == "stale"
    assert draft.fact_check_json is None


def test_mark_media_changed(db_session, draft):
    staleness.mark_media_changed(db_session, draft, reason="reorder")
    assert draft.candidate_readiness == "stale"


def test_invalidate_candidate_never_mutates_manifest(db_session, draft):
    """R3-6：Immutable Candidate——失效只写审计，历史 manifest/批准 hash 保持原样。"""
    asset = ContentAsset(
        draft_id=draft.id, topic_brief_id=1, channel="wechat", title="t", final_body="b",
        fact_pack_id=1, fact_pack_version=1, approved_revision=1, approved_candidate_hash="h" * 64,
        candidate_manifest_json={"schema_version": 2, "media": []},
    )
    db_session.add(asset)
    db_session.commit()
    before = asset.candidate_manifest_json
    count = staleness.invalidate_candidate(db_session, draft.id, reason="body_changed")
    db_session.commit()
    assert count == 1
    assert asset.candidate_manifest_json == before  # manifest 未被改写
    assert asset.approved_candidate_hash == "h" * 64
    from app.models import AuditLog

    logs = db_session.query(AuditLog).filter_by(event="candidate.invalidated", entity_id=str(asset.id)).all()
    assert len(logs) == 1 and logs[0].detail_json["reason"] == "body_changed"


def test_mark_material_rights_revoked_affects_uses(db_session, draft):
    use = DraftMedia(draft_id=draft.id, content_hash="c" * 64, role="inline", material_revision_id=99)
    db_session.add(use)
    db_session.commit()
    affected = staleness.mark_material_rights_revoked(db_session, 99, "版权问题")
    assert draft.id in affected
    assert draft.candidate_readiness == "stale"
