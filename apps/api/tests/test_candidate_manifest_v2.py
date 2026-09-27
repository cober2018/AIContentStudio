"""Candidate Manifest v2（V1 PRD 2.0 / capability: versioned-article-candidate 升级）。

覆盖：canonical hash stable；placement/SEO 变化 → hash 变化；stale check 阻止批准；
schema v2 批准路径（非 M1 内容）；legacy M1（mother revision）仍走 v1 可读。
"""

import pytest

from app.models import ContentJob, Draft, FactPack, MotherRevision, TopicBrief, User
from app.services import checks as checks_service
from app.services.candidates import (
    build_manifest,
    build_manifest_v2,
    candidate_hash,
    draft_input_hash,
)
from app.services.generation.renderers import render_body

EDITOR = {"X-Studio-User": "editor@studio.local"}
PNG = b"\x89PNG\r\n\x1a\n" + b"m2" * 8


@pytest.fixture
def env(db_session):
    db_session.add(User(email="editor@studio.local", name="E", role="editor"))
    db_session.add(User(email="reviewer@studio.local", name="R", role="reviewer"))
    pack = FactPack(name="cand包", version=1, status="frozen", checksum="9" * 64)
    db_session.add(pack)
    db_session.flush()
    topic = TopicBrief(title="候选测试", fact_pack_id=pack.id, fact_pack_version=1)
    db_session.add(topic)
    db_session.flush()
    job = ContentJob(topic_brief_id=topic.id, channel="wechat", content_form="article", status="succeeded")
    db_session.add(job)
    db_session.flush()
    structured = {
        "titles": ["标题"],
        "summary": "摘要",
        "sections": [{"heading": "H", "body": "B"}],
        "risk_note": "风险",
        "ending": "结尾",
        "sources": ["s1"],
        "claim_fact_map": [],
        "declarations": [],
    }
    draft = Draft(
        content_job_id=job.id, revision_no=1, title="标题",
        body=render_body("wechat", structured), structured_json=structured,
        input_hash=draft_input_hash("标题", render_body("wechat", structured), None),
    )
    db_session.add(draft)
    db_session.commit()
    return db_session, topic, draft


def _ready_checks(db, draft):
    checks_service.run_rule_set(db, draft, rule_keys=["rule.platform.required_fields"])
    if draft.media:
        checks_service.run_rule_set(db, draft, rule_keys=["rule.media.required", "rule.media.public_rights", "rule.media.order"])
    db.commit()


def _approve(client, draft_id):
    return client.post(f"/api/v1/reviews/drafts/{draft_id}/approve", json={"comment": "ok"}, headers={"X-Studio-User": "reviewer@studio.local"})


def _submit(client, draft_id):
    return client.post(f"/api/v1/drafts/{draft_id}/submit-review", headers=EDITOR)


def test_manifest_v2_hash_stable_and_changes_with_content(env):
    """同一输入 hash 稳定；placement/SEO metadata 变化 → hash 变化。"""
    db, _topic, draft = env
    _ready_checks(db, draft)
    m1 = build_manifest_v2(db, draft)
    h1 = candidate_hash(m1)
    m2 = build_manifest_v2(db, draft)
    assert candidate_hash(m2) == h1  # stable

    # SEO metadata 变化（structured tags）
    draft.structured_json = {**(draft.structured_json or {}), "tags": ["量化"]}
    db.commit()
    h3 = candidate_hash(build_manifest_v2(db, draft))
    assert h3 != h1

    # placement 变化（attachment 角色变更）——无媒体时用 document 层变化
    draft.document_json = {"schema_version": 1, "blocks": [{"id": "p1", "type": "paragraph", "text": "x"}]}
    db.commit()
    h4 = candidate_hash(build_manifest_v2(db, draft))
    assert h4 != h3


def test_v2_approve_happy_path_and_structure(env):
    db, _topic, draft = env
    _ready_checks(db, draft)
    # fact check 绑定当前输入
    from app.services import factchecker

    result = factchecker.run_fact_check(draft.body, [], "topic", forbidden_words=[], source_text="")
    draft.fact_check_json = result.to_json() | {"input_hash": draft.input_hash}
    # R2-B2：公众号封面必需（media_requirements 强制，publisher 不再造 placeholder）
    from app.services import materials as materials_service

    material = materials_service.create_material(db, kind="image", title="封面")
    revision = materials_service.create_revision(
        db, material, content=PNG, suffix=".png", declared_mime="image/png",
        public_use_allowed=True, rights_status="cleared",
    )
    materials_service.attach_to_draft(db, draft, revision, role="cover")
    db.commit()

    r = _submit(_client(db), draft.id)
    assert r.status_code in (200, 201), r.json()
    r2 = _approve(_client(db), draft.id)
    assert r2.status_code == 201, r2.json()
    assert r2.json()["manifest_schema"] == 2

    from app.models import ContentAsset

    asset = db.query(ContentAsset).filter_by(draft_id=draft.id).order_by(ContentAsset.id.desc()).first()
    manifest = asset.candidate_manifest_json
    assert manifest["schema_version"] == 2
    assert manifest["channel"] == "wechat"
    assert manifest["content_form"] == "article"
    assert manifest["render"]["renderer_key"] == "renderer.wechat.article"
    assert manifest["render"]["payload"]["html"]
    assert len(asset.approved_candidate_hash) == 64
    assert asset.artifact_kind == "text"
    assert asset.content_form == "article"
    # hash 与实际交付 payload 一致（render 在 manifest 内）
    assert candidate_hash(manifest) == asset.approved_candidate_hash


def test_stale_fact_check_blocks_v2_approve(env):
    """stale check 阻止 approve：fact check input_hash 与当前输入不一致。"""
    db, _topic, draft = env
    _ready_checks(db, draft)
    from app.services import factchecker

    result = factchecker.run_fact_check(draft.body, [], "topic", forbidden_words=[], source_text="")
    draft.fact_check_json = result.to_json() | {"input_hash": "stale" + "0" * 60}
    db.commit()
    _submit(_client(db), draft.id)
    r = _approve(_client(db), draft.id)
    assert r.status_code == 409
    assert any("fact_check_not_bound" in str(x) for x in r.json()["detail"]["reasons"])


def test_media_rights_incomplete_blocks_v2_approve(env):
    db, _topic, draft = env
    from app.services import materials as materials_service

    material = materials_service.create_material(db, kind="image", title="封面")
    revision = materials_service.create_revision(
        db, material, content=PNG, suffix=".png", declared_mime="image/png",
        public_use_allowed=False, rights_status="cleared",  # 未授权公开
    )
    materials_service.attach_to_draft(db, draft, revision, role="cover")
    db.commit()
    _submit(_client(db), draft.id)
    r = _approve(_client(db), draft.id)
    assert r.status_code == 409
    detail = r.json()["detail"]
    reasons = str(detail["reasons"]) if isinstance(detail, dict) else str(detail)
    assert "media_rights_incomplete" in reasons or "media_not_actual" in reasons or "不可批准" in reasons


def test_legacy_v1_mother_flow_still_v1(env):
    """M1（mother revision）内容仍走 schema v1 manifest，v1 可读。"""
    db, topic, _draft = env
    revision = MotherRevision(
        topic_brief_id=topic.id, revision_no=1, title="母稿", body_markdown="母稿正文",
        evidence_checksum=topic.fact_pack.checksum, body_hash="0" * 64,
    )
    db.add(revision)
    db.flush()
    job2 = ContentJob(topic_brief_id=topic.id, channel="wechat", content_form="article", status="succeeded")
    db.add(job2)
    db.flush()
    from app.models import DraftStatus

    m1_draft = Draft(
        content_job_id=job2.id, revision_no=1, title="母稿改写", body="改写正文",
        mother_revision_id=revision.id, evidence_checksum=revision.evidence_checksum,
        input_hash="i" * 64, status=DraftStatus.ready_for_review.value,
    )
    db.add(m1_draft)
    db.commit()
    manifest = build_manifest(m1_draft)
    assert manifest["schema_version"] == 1  # v1 builder 保留


def _client(db):
    from fastapi.testclient import TestClient

    from app.db import get_db
    from app.main import app

    def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    return TestClient(app)
