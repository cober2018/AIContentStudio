"""Review & Publish Center（V1 PRD 2.0 / capability: unified-review-publish-center）。

覆盖：projection 聚合（不建第二份状态）；readiness 投影；批准后 candidate/delivery 可见。
"""

import pytest

from app.models import ContentJob, Draft, FactPack, TopicBrief, User
from app.services.candidates import build_manifest_v2, candidate_hash, draft_input_hash

EDITOR = {"X-Studio-User": "editor@studio.local"}
REVIEWER = {"X-Studio-User": "reviewer@studio.local"}


@pytest.fixture
def env(db_session):
    db_session.add(User(email="editor@studio.local", name="E", role="editor"))
    db_session.add(User(email="reviewer@studio.local", name="R", role="reviewer"))
    pack = FactPack(name="center包", version=1, status="frozen", checksum="q" * 64)
    db_session.add(pack)
    db_session.flush()
    topic = TopicBrief(
        title="中心测试", fact_pack_id=pack.id, fact_pack_version=1,
        targets_json=[{"channel": "wechat", "content_form": "article"}],
        channels=["wechat"],
    )
    db_session.add(topic)
    db_session.flush()
    job = ContentJob(topic_brief_id=topic.id, channel="wechat", content_form="article", status="succeeded")
    db_session.add(job)
    db_session.flush()
    draft = Draft(content_job_id=job.id, revision_no=1, title="中心稿", body="正文", input_hash=draft_input_hash("中心稿", "正文", None))
    db_session.add(draft)
    db_session.commit()
    return db_session, topic, draft


def _client(db):
    from fastapi.testclient import TestClient

    from app.db import get_db
    from app.main import app

    def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    return TestClient(app)


def test_projection_before_approval(env):
    db, topic, draft = env
    data = _client(db).get(f"/api/v1/review-center/topics/{topic.id}", headers=EDITOR).json()
    assert data["topic"]["id"] == topic.id
    assert len(data["targets"]) == 1
    target = data["targets"][0]
    assert target["channel"] == "wechat"
    assert target["draft"]["id"] == draft.id
    assert target["candidate"] is None
    assert target["readiness"]["evidence"] == "ready"
    assert target["readiness"]["delivery"] == "awaiting_approval"


def test_projection_after_approval_with_delivery(env):
    db, topic, draft = env
    client = _client(db)
    from app.services import checks as checks_service
    from app.services import factchecker

    checks_service.run_rule_set(db, draft, rule_keys=["rule.platform.required_fields"])
    result = factchecker.run_fact_check(draft.body, [], "topic", forbidden_words=[], source_text="")
    draft.fact_check_json = result.to_json() | {"input_hash": draft.input_hash}
    draft.candidate_readiness = "ready"
    db.commit()
    manifest = build_manifest_v2(db, draft)
    from app.models import ContentAsset

    asset = ContentAsset(
        draft_id=draft.id, topic_brief_id=topic.id, channel="wechat", title=draft.title,
        final_body=draft.body, fact_pack_id=1, fact_pack_version=1, approved_revision=1,
        approved_candidate_hash=candidate_hash(manifest), candidate_manifest_json=manifest,
        artifact_kind="text", content_form="article",
    )
    db.add(asset)
    db.commit()

    data = client.get(f"/api/v1/review-center/topics/{topic.id}", headers=EDITOR).json()
    target = data["targets"][0]
    assert target["candidate"]["manifest_schema"] == 2
    assert target["readiness"]["content"] == "ready"
    assert target["readiness"]["delivery"] == "not_authorized"

    # 授权交付后投影更新（不建第二份状态：读的就是 DeliveryTarget）
    t = client.post(
        f"/api/v1/assets/{asset.id}/delivery-targets",
        json={"channel": "wechat", "content_form": "article", "account_ref": "acct", "authorization_version": "v1", "action": "copy_package"},
        headers=EDITOR,
    )
    assert t.status_code == 201
    data2 = client.get(f"/api/v1/review-center/topics/{topic.id}", headers=EDITOR).json()
    assert data2["targets"][0]["readiness"]["delivery"] == "authorized"
    assert data2["targets"][0]["delivery"][0]["publisher_key"] == "publisher.copy"
