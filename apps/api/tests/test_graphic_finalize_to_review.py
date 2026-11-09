"""图文定稿后平台自动出图、冻结候选；定稿状态不变。"""

import hashlib
import io

import pytest
from PIL import Image
from sqlalchemy import select

from app.models import ContentAsset, FactPack, FactPackItem, Material, MaterialRevision, ProjectMaterialReference, User
from app.services import article_chain
from app.services.local_graphic_renderer import LocalGraphicRenderer
from app.services.multiplatform_profiles import DECLARED_TARGETS, apply_profiles, dry_run_profiles

HEADERS = {"X-Studio-User": "graphic-review@studio.local"}


@pytest.fixture
def renderer(monkeypatch):
    calls = []

    def render(self, request):
        from app.services.content_harness.providers import MediaRenderOutput

        canvas = next(item for item in request["payload"]["canvases"] if item["id"] == request["canvas_id"])
        calls.append(canvas["id"])
        buffer = io.BytesIO()
        Image.new("RGB", (canvas["width"], canvas["height"]), (len(calls) * 40, 10, 10)).save(buffer, "PNG")
        return MediaRenderOutput("succeeded", buffer.getvalue(), "image/png", request["render_input_hash"], request["canvas_id"])

    monkeypatch.setattr(LocalGraphicRenderer, "runtime_fingerprint", lambda self: "a" * 64)
    monkeypatch.setattr(LocalGraphicRenderer, "render_master", render)
    return calls


def _work(client, db, tmp_path):
    plan = dry_run_profiles(db, sorted({item[0] for item in DECLARED_TARGETS}))
    apply_profiles(db, plan, expected_plan_hash=plan["plan_hash"])
    persona = client.post("/api/v1/content-personas", json={"name": "阿军"}, headers=HEADERS).json()["id"]
    project = client.post("/api/v1/content-projects", json={"title": "退休贴图"}, headers=HEADERS).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project}/units", json={
        "title": "退休小事", "persona_id": persona, "modality": "graphic", "channel_id": "wechat"}, headers=HEADERS).json()["id"]
    assert client.post(f"/api/v1/content-projects/{project}/brief/revisions", json={
        "objective": "退休生活建议", "expected_revision": 0}, headers=HEADERS).status_code == 201
    pack = FactPack(name="观点", version=1, status="frozen", checksum="c" * 64)
    db.add(pack)
    db.flush()
    db.add(FactPackItem(fact_pack_id=pack.id, evidence_kind="author_opinion", snapshot_json={"statement": "观点"},
                        snapshot_checksum="d" * 64, public_use_allowed=True, model_use_allowed=True))
    db.commit()
    assert client.post(f"/api/v1/content-projects/{project}/fact-boundary", json={
        "fact_pack_id": pack.id, "expected_revision": 0}, headers=HEADERS).status_code == 201
    buffer = io.BytesIO()
    Image.new("RGB", (64, 48), (200, 180, 160)).save(buffer, "PNG")
    content = buffer.getvalue()
    file = tmp_path / "photo.png"
    file.write_bytes(content)
    material = Material(title="配图", kind="image", status="active")
    db.add(material)
    db.flush()
    revision = MaterialRevision(material_id=material.id, content_hash=hashlib.sha256(content).hexdigest(), file_path=str(file),
                                mime_type="image/png", status="active", public_use_allowed=True, rights_status="cleared")
    db.add(revision)
    db.flush()
    db.add(ProjectMaterialReference(project_id=project, material_revision_id=revision.id, origin="system_library", status="active"))
    db.commit()
    canvases = [{"id": key, "order": index, "width": 1080, "height": 1440, "background": {"color": "#FCF8F2"}, "layers": [
        {"id": "photo", "order": 0, "type": "image", "x": 60, "y": 60, "width": 960, "height": 720, "material_revision_id": revision.id, "fit": "cover"},
        {"id": "head", "order": 1, "type": "text", "x": 60, "y": 830, "width": 960, "height": 80,
         "runs": [{"text": f"第{index + 1}件小事", "style": {"font_size": 58, "color": "#262D35"}}]},
    ]} for index, key in enumerate(("cover", "tip1"))]
    user = db.scalar(select(User).where(User.email == HEADERS["X-Studio-User"]))
    article_chain.set_writer(db, user, project, unit, "external")
    article_chain.save_draft(db, user, project, unit, {"title": "退休后过得踏实", "canvases": canvases}, None)
    return project, unit, user, revision


def _candidates(db, unit):
    return db.scalars(select(ContentAsset).where(ContentAsset.content_unit_id == unit)).all()


def _submit_third_party_reviews(db, user, project, unit):
    from app.services import third_party_review

    for item in third_party_review.pending_tasks(db, user, project, unit)["items"]:
        third_party_review.submit(db, user, project, unit, item["master_id"], item["purpose"], item["input_hash"], "test-third-party-model", [])


def test_approve_renders_then_waits_for_check_before_freezing(client, db_session, tmp_path, renderer):
    project, unit, user, _ = _work(client, db_session, tmp_path)
    state = article_chain.decide(db_session, user, project, unit, "approve", [])
    assert renderer == ["cover", "tip1"], state.get("review")
    assert state["state"] == "final_review" and not state.get("locked")
    assert [item["canvas_id"] for item in state["renders"]] == ["cover", "tip1"] and _candidates(db_session, unit) == []
    done = article_chain.decide(db_session, user, project, unit, "accept", [])
    assert done["state"] == "done" and done["locked"] is True and done["review"]["state"] == "failed", done["review"]
    _submit_third_party_reviews(db_session, user, project, unit)
    done = article_chain.send_to_review(db_session, user, project, unit)
    assert done["review"]["state"] == "sent", done["review"]
    asset = db_session.get(ContentAsset, done["review"]["candidate_id"])
    assert (asset.channel, asset.content_form, asset.status) == ("wechat", "image_message", "frozen")
    # A retry on a sent piece reuses the render and the frozen candidate.
    again = article_chain.send_to_review(db_session, user, project, unit)
    assert renderer == ["cover", "tip1"] and again["review"]["candidate_id"] == asset.id and again["locked"] is True


def test_notes_on_rendered_images_send_the_piece_back_to_the_model(client, db_session, tmp_path, renderer):
    project, unit, user, _ = _work(client, db_session, tmp_path)
    article_chain.decide(db_session, user, project, unit, "approve", [])
    back = article_chain.decide(db_session, user, project, unit, "changes", [{"note": "去掉图上的AI标记"}])
    assert back["state"] == "draft_changes" and not back.get("locked") and _candidates(db_session, unit) == []
    payload = article_chain.brief(db_session, user, project, unit)["current_master"]["payload"]
    payload.pop("render_asset_ref", None)
    saved = article_chain.save_draft(db_session, user, project, unit, payload, "按意见改")
    assert saved["state"]["state"] == "draft_review"


def test_save_is_refused_while_images_wait_for_check(client, db_session, tmp_path, renderer):
    from fastapi import HTTPException

    project, unit, user, _ = _work(client, db_session, tmp_path)
    article_chain.decide(db_session, user, project, unit, "approve", [])
    with pytest.raises(HTTPException) as refused:
        article_chain.save_draft(db_session, user, project, unit, {"title": "x", "canvases": []}, None)
    assert refused.value.detail["code"] == "article_chain_waiting_render_check"


def test_non_public_image_blocks_render_but_keeps_approval(client, db_session, tmp_path, renderer):
    project, unit, user, revision = _work(client, db_session, tmp_path)
    revision.public_use_allowed = False
    db_session.commit()
    state = article_chain.decide(db_session, user, project, unit, "approve", [])
    assert renderer == []
    assert state["state"] == "rendering"
    assert state["review"]["state"] == "failed" and f"素材 {revision.id}" in state["review"]["message"]


def test_facts_changed_after_acceptance_bring_new_images_to_check(client, db_session, tmp_path, renderer):
    project, unit, user, _ = _work(client, db_session, tmp_path)
    article_chain.decide(db_session, user, project, unit, "approve", [])
    article_chain.decide(db_session, user, project, unit, "accept", [])
    _submit_third_party_reviews(db_session, user, project, unit)
    first = article_chain.send_to_review(db_session, user, project, unit)
    assert first["review"]["state"] == "sent"
    pack = FactPack(name="新事实", version=1, status="frozen", checksum="e" * 64)
    db_session.add(pack)
    db_session.flush()
    db_session.add(FactPackItem(fact_pack_id=pack.id, evidence_kind="author_opinion", snapshot_json={"statement": "新观点"},
                                snapshot_checksum="f" * 64, public_use_allowed=True, model_use_allowed=True))
    db_session.commit()
    assert client.post(f"/api/v1/content-projects/{project}/fact-boundary", json={
        "fact_pack_id": pack.id, "expected_revision": 1}, headers=HEADERS).status_code == 201
    again = article_chain.send_to_review(db_session, user, project, unit)
    assert again["state"] == "final_review" and again["master_id"] != first["master_id"]
    assert renderer == ["cover", "tip1", "cover", "tip1"]
    article_chain.decide(db_session, user, project, unit, "accept", [])
    _submit_third_party_reviews(db_session, user, project, unit)
    sent = article_chain.send_to_review(db_session, user, project, unit)
    assert sent["review"]["state"] == "sent" and sent["review"]["candidate_id"] != first["review"]["candidate_id"]


def test_platform_written_piece_waits_for_approval_and_renders(client, db_session, tmp_path, renderer):
    project, unit, user, _ = _work(client, db_session, tmp_path)
    article_chain.set_writer(db_session, user, project, unit, "platform")
    waiting = article_chain.state(db_session, user, project, unit)
    assert waiting["state"] == "draft_review"
    rendered = article_chain.decide(db_session, user, project, unit, "approve", [])
    assert rendered["state"] == "final_review" and renderer == ["cover", "tip1"]
    back = article_chain.decide(db_session, user, project, unit, "changes", [{"note": "换背景"}])
    assert back["state"] == "draft_changes" and back["label"] == "按你的意见在创作流程里重写"
