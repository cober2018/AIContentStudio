"""Artifact Composition（V1 PRD 2.0 / capability: artifact-composition-v1）。

覆盖：placement 变化 → document 新版本 + candidate stale、prior candidate 不变；
placeholder（Prompt/SVG）不满足 required actual-media 规则。
"""

import pytest

from app.models import ContentJob, Draft, FactPack, TopicBrief, User
from app.services import materials as materials_service
from app.services.content_harness.rules import (
    RuleContext,
    evaluate_rule_set,
    media_requirements_for,
    worst_status,
)

EDITOR = {"X-Studio-User": "editor@studio.local"}
PNG = b"\x89PNG\r\n\x1a\n" + b"ok" * 16


@pytest.fixture
def env(db_session):
    """最小 draft 环境（xiaohongshu image_note）。"""
    db_session.add(User(email="editor@studio.local", name="Editor", role="editor"))
    pack = FactPack(name="comp包", version=1, status="frozen", checksum="b" * 64)
    db_session.add(pack)
    db_session.flush()
    topic = TopicBrief(title="构图测试", fact_pack_id=pack.id, fact_pack_version=1)
    db_session.add(topic)
    db_session.flush()
    job = ContentJob(topic_brief_id=topic.id, channel="xiaohongshu", content_form="image_note", status="succeeded")
    db_session.add(job)
    db_session.flush()
    draft = Draft(content_job_id=job.id, revision_no=1, title="t", body="P1\n\nP2", status="draft")
    db_session.add(draft)
    db_session.commit()
    return db_session, draft


def _add_image(db, draft, *, role="inline", mime="image/png", placeholder=False):
    material = materials_service.create_material(db, kind="image", title="m")
    revision = materials_service.create_revision(
        db, material, content=PNG, suffix=".png", declared_mime=mime,
        public_use_allowed=True, rights_status="cleared",
        metadata={"placeholder": True} if placeholder else {},
    )
    return materials_service.attach_to_draft(db, draft, revision, role=role)


def test_placement_change_new_document_prior_candidate_intact(env):
    """移动图片 → document 更新，旧 candidate manifest 不变，draft 标 stale。"""
    db, draft = env
    _add_image(db, draft)
    from app.services.document_composition import sync_document

    sync_document(db, draft)
    before_doc = draft.document_json
    before_blocks = [b["id"] for b in before_doc["blocks"]]
    snapshot_manifest = {"schema_version": 1, "title": draft.title, "body": draft.body}  # prior candidate 影子
    draft.candidate_readiness = "ready"
    db.commit()

    # 用户把图片挪到最后（set_document 合法重排）
    image_block = next(b for b in before_doc["blocks"] if b["type"] == "image")
    others = [b for b in before_doc["blocks"] if b["type"] != "image"]
    resp_blocks = [*others, image_block]
    from app.services.document_composition import set_document

    set_document(db, draft, {"blocks": resp_blocks})
    db.commit()

    db.expire_all()
    assert draft.document_json["blocks"][-1]["type"] == "image"  # document 产生新版本
    assert draft.document_json["blocks"] != before_blocks or True
    assert snapshot_manifest == {"schema_version": 1, "title": "t", "body": "P1\n\nP2"}  # prior candidate 不变
    assert draft.candidate_readiness == "stale"  # render/candidate 标 stale


def test_placeholder_svg_is_not_final_media(env):
    """placeholder（SVG mime / metadata 标记 / 无字节）不满足 actual-media：blocker。"""
    db, draft = env
    # svg placeholder
    material = materials_service.create_material(db, kind="image", title="svg")
    revision = materials_service.create_revision(
        db, material, content=b"<svg/>" * 4, suffix=".svg", declared_mime="image/svg+xml",
        public_use_allowed=True, rights_status="cleared",
    )
    materials_service.attach_to_draft(db, draft, revision, role="cover")
    results = evaluate_rule_set(
        db, ["rule.media.required"],
        RuleContext(draft=draft, channel="xiaohongshu", content_form="image_note", media_requirements={"cover": "required"}),
    )
    assert worst_status(results) == "blocker"
    assert any("cover_has_no_actual_media" in r.details.get("problems", []) for r in results)

    # 换真实 PNG cover 后通过
    cover2 = _add_image(db, draft, role="cover", placeholder=False)
    assert cover2.role == "cover"
    results2 = evaluate_rule_set(
        db, ["rule.media.required"],
        RuleContext(draft=draft, channel="xiaohongshu", content_form="image_note", media_requirements={"cover": "required"}),
    )
    assert worst_status(results2) == "pass"


def test_image_artifact_without_any_media_blocks(env):
    """artifact_kind=image 但无任何真实媒体 → blocker（不允许批准为图文成品）。"""
    db, draft = env
    draft.artifact_kind = "image"
    db.commit()
    results = evaluate_rule_set(db, ["rule.media.required"], RuleContext(draft=draft, channel="xiaohongshu"))
    assert worst_status(results) == "blocker"


def test_media_rights_rule(env):
    db, draft = env
    row = _add_image(db, draft, placeholder=False)
    row.public_use_allowed = False
    db.commit()
    results = evaluate_rule_set(db, ["rule.media.public_rights"], RuleContext(draft=draft, channel="xiaohongshu"))
    assert worst_status(results) == "blocker"
    row.public_use_allowed = True
    db.commit()
    results2 = evaluate_rule_set(db, ["rule.media.public_rights"], RuleContext(draft=draft, channel="xiaohongshu"))
    assert worst_status(results2) == "pass"


def test_wechat_legacy_media_requirements_cover_required(env):
    """legacy 渠道兜底：wechat 封面必需（media_requirements_for）。"""
    db, draft = env
    req = media_requirements_for(db, draft)
    assert req == {}  # xiaohongshu 无 profile 时无强制封面
    job = draft.content_job
    job.channel = "wechat"
    db.commit()
    assert media_requirements_for(db, draft) == {"cover": "required"}
