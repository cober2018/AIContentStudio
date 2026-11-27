"""一份本体、四种形态：勾形态、本体定稿后开工、派生记血缘、一致性检查、本体改版、补勾、导入已发表文章。"""

import pytest
from fastapi import HTTPException

from app.models import ContentMasterRevision, ContentProject, ContentUnit, User
from app.services import article_chain, topic_forms, video_chain


def _body_doc(conclusion="两个因子在样本里无法区分", table="样本 2018-2025 年，IC 均值 0.031 与 0.029"):
    return {"title": "两个因子能分出好坏吗", "document": {"schema": "studio.text.document.v1", "blocks": [
        {"id": "h1", "type": "heading", "level": 2, "content": [{"text": "问题"}]},
        {"id": "p1", "type": "paragraph", "content": [{"text": "两个几乎一样的因子，哪个更好？"}]},
        {"id": "h2", "type": "heading", "level": 2, "content": [{"text": "结论"}]},
        {"id": "p2", "type": "paragraph", "content": [{"text": conclusion}]},
        {"id": "h3", "type": "heading", "level": 2, "content": [{"text": "结果表"}]},
        {"id": "p3", "type": "paragraph", "content": [{"text": table}]},
    ]}}


def _graphic(text):
    return {"title": "图卡", "canvases": [{"id": "c1", "order": 0, "width": 1080, "height": 1440, "background": {"color": "#FCF8F2"},
                                         "layers": [{"id": "t1", "order": 0, "type": "text", "x": 80, "y": 80, "width": 900, "height": 200,
                                                     "runs": [{"text": text, "style": {"font_size": 48, "color": "#262D35"}}]}]}]}


def _video(aspect, line="两个因子在样本里无法区分"):
    return {"title": "短片", "aspect_ratio": aspect, "script": {"blocks": [{"id": "opening", "order": 0, "text": line}]},
            "shots": [{"id": "shot-1", "order": 0, "label": "开场", "duration_ms": 4_000, "script_block_id": "opening", "transition": "cut"}],
            "timeline": {"duration_ms": 4_000, "tracks": [{"id": "visual", "order": 0, "kind": "video",
                                                           "items": [{"id": "item-1", "order": 0, "shot_id": "shot-1", "start_ms": 0, "end_ms": 4_000}]}]},
            "voice": {"mode": "none"}, "subtitles": {"cues": []}, "overlays": [], "music": {}, "cover": {}}


@pytest.fixture
def setup(client, db_session):
    persona = client.post("/api/v1/content-personas", json={"name": "量化研究专家"}).json()["id"]
    project = client.post("/api/v1/content-projects", json={"title": "两个因子", "objective": "讲清能否区分"}).json()["id"]
    user = db_session.query(User).filter_by(email="admin@studio.local").one()
    return user, persona, project


def _units(db, project_id):
    return {unit.form: unit for unit in db.query(ContentUnit).filter_by(project_id=project_id).all()}


def _finalize(client, db, user, project_id, body_id, doc=None):
    article_chain.save_draft(db, user, project_id, body_id, doc or _body_doc(), "本体")
    result = client.post(f"/api/v1/content-projects/{project_id}/units/{body_id}/article-chain/decision",
                         json={"decision": "approve", "notes": []})
    assert result.status_code == 200, result.text


def test_ticked_forms_wait_for_the_body_then_start(client, db_session, setup):
    user, persona, project = setup
    view = client.post(f"/api/v1/content-projects/{project}/forms",
                       json={"persona_id": persona, "forms": ["long_article", "graphic_cards"]}).json()
    units = _units(db_session, project)
    assert set(units) == {"body", "graphic_cards"} and not view["started"]
    graphic = units["graphic_cards"]
    # Before the body is final the form work has no brief and cannot be saved.
    with pytest.raises(HTTPException) as early:
        article_chain.brief(db_session, user, project, graphic.id)
    assert early.value.detail["code"] == "body_not_final"
    article_chain.save_draft(db_session, user, project, units["body"].id, _body_doc(), "本体")
    assert article_chain._state(db_session, units["body"].id)["state"] == "draft_review"
    # The user ticks 竖版 at the 本体待你看 step, then makes the body final.
    client.put(f"/api/v1/content-projects/{project}/forms", json={"forms": ["long_article", "graphic_cards", "video_portrait"]})
    client.post(f"/api/v1/content-projects/{project}/units/{units['body'].id}/article-chain/decision", json={"decision": "approve", "notes": []})
    view = client.get(f"/api/v1/content-projects/{project}/forms").json()
    assert view["started"] and {item["form"] for item in view["works"]} == {"graphic_cards", "video_portrait"}
    assert view["long_article"]["channel_id"] == "wechat"
    brief = article_chain.brief(db_session, user, project, graphic.id)
    assert brief["source_texts"] == [] and brief["form"]["body"]["revision_no"] == 1
    assert [part["kind"] for part in brief["form"]["body"]["sections"]] == ["question", "conclusion", "results"]
    assert brief["form"]["writing_standard"]["skill"] == "craft-writing"
    pending = topic_forms.pending(db_session, user)["items"]
    assert {item["form"] for item in pending} == {"graphic_cards", "video_portrait"}
    saved = article_chain.save_draft(db_session, user, project, graphic.id, _graphic("IC 均值 0.031 与 0.029：无法区分"), None)
    body_master = topic_forms.final_body(db_session, units["body"].id)
    assert db_session.get(ContentMasterRevision, saved["master_id"]).source_body_revision_id == body_master.id


def test_derived_drafts_must_agree_with_the_body(client, db_session, setup):
    user, persona, project = setup
    client.post(f"/api/v1/content-projects/{project}/forms", json={"persona_id": persona, "forms": ["graphic_cards", "video_landscape"]})
    units = _units(db_session, project)
    _finalize(client, db_session, user, project, units["body"].id)
    with pytest.raises(HTTPException) as number:
        article_chain.save_draft(db_session, user, project, units["graphic_cards"].id, _graphic("年化 12% 的因子"), None)
    assert number.value.detail["code"] == "form_body_mismatch" and "12" in number.value.detail["problems"][0]
    with pytest.raises(HTTPException) as stronger:
        article_chain.save_draft(db_session, user, project, units["graphic_cards"].id, _graphic("B 明显更好"), None)
    assert "结论比本体强" in stronger.value.detail["problems"][0]
    with pytest.raises(HTTPException) as aspect:
        video_chain.save_draft(db_session, user, project, units["video_landscape"].id, _video([9, 16]), None)
    assert aspect.value.detail["code"] == "form_aspect_mismatch"
    saved = video_chain.save_draft(db_session, user, project, units["video_landscape"].id, _video([16, 9]), None)
    assert db_session.get(ContentMasterRevision, saved["master_id"]).source_body_revision_id is not None


def test_a_new_body_revision_marks_derived_works_and_redo_uses_it(client, db_session, setup):
    user, persona, project = setup
    client.post(f"/api/v1/content-projects/{project}/forms", json={"persona_id": persona, "forms": ["graphic_cards"]})
    units = _units(db_session, project)
    body = units["body"]
    _finalize(client, db_session, user, project, body.id)
    article_chain.save_draft(db_session, user, project, units["graphic_cards"].id, _graphic("无法区分"), None)
    # Reopen the final body with a note, write revision 2 with a changed table, make it final again.
    reopened = client.post(f"/api/v1/content-projects/{project}/units/{body.id}/article-chain/decision",
                           json={"decision": "changes", "notes": [{"note": "结果表加 2026 年"}]})
    assert reopened.status_code == 200, reopened.text
    _finalize(client, db_session, user, project, body.id, _body_doc(table="样本 2018-2026 年，IC 均值 0.030 与 0.029"))
    work = next(item for item in client.get(f"/api/v1/content-projects/{project}/forms").json()["works"])
    assert work["stale"] == {"from_revision_no": 1, "to_revision_no": 2, "changed_sections": ["结果表"]}
    assert work["body_revision_no"] == 1  # nothing was redone automatically
    fresh = client.post(f"/api/v1/content-projects/{project}/units/{work['unit_id']}/form-redo").json()
    again = client.post(f"/api/v1/content-projects/{project}/units/{work['unit_id']}/form-redo")
    assert again.status_code == 409
    old = next(item for item in client.get(f"/api/v1/content-projects/{project}/forms").json()["works"] if item["unit_id"] == work["unit_id"])
    assert old["redone_by"] == fresh["unit_id"]
    saved = article_chain.save_draft(db_session, user, project, fresh["unit_id"], _graphic("2026 年也无法区分"), None)
    used = db_session.get(ContentMasterRevision, db_session.get(ContentMasterRevision, saved["master_id"]).source_body_revision_id)
    assert used.revision_no == 2


def test_adding_a_form_after_the_body_is_final_and_started_forms_stay(client, db_session, setup):
    user, persona, project = setup
    client.post(f"/api/v1/content-projects/{project}/forms", json={"persona_id": persona, "forms": ["video_landscape"]})
    units = _units(db_session, project)
    _finalize(client, db_session, user, project, units["body"].id)
    video_chain.save_draft(db_session, user, project, units["video_landscape"].id, _video([16, 9]), None)
    assert client.put(f"/api/v1/content-projects/{project}/forms", json={"forms": ["video_portrait"]}).status_code == 409
    view = client.put(f"/api/v1/content-projects/{project}/forms", json={"forms": ["video_landscape", "video_portrait"]}).json()
    portrait = next(item for item in view["works"] if item["form"] == "video_portrait")
    brief = video_chain.brief(db_session, user, project, portrait["unit_id"])
    assert brief["form"]["form"]["aspect_ratio"] == [9, 16] and brief["form"]["body"]["revision_no"] == 1


def test_published_article_becomes_a_final_body_at_once(client, db_session, setup):
    user, persona, project = setup
    view = client.post(f"/api/v1/content-projects/{project}/forms", json={
        "persona_id": persona, "forms": ["video_landscape", "video_portrait"], "body_source": "published_article",
        "article": {"title": "两个因子能分出好坏吗", "url": "https://mp.weixin.qq.com/s/abc",
                    "text": "# 两个因子能分出好坏吗\n\n## 问题\n哪个更好？\n\n![K线](https://img.example/k.png)\n\n## 结论\n无法区分\n\n| 因子 | IC |\n|---|---|\n| A | 0.031 |"}}).json()
    assert view["started"] and view["import"]["url"] == "https://mp.weixin.qq.com/s/abc"
    assert view["import"]["images"] == [{"alt": "K线", "src": "https://img.example/k.png"}]
    assert view["body"]["state"] == "done" and view["body"]["final_revision_no"] == 1
    portrait = next(item for item in view["works"] if item["form"] == "video_portrait")
    saved = video_chain.save_draft(db_session, user, project, portrait["unit_id"], _video([9, 16], "A 的 IC 是 0.031，和 B 无法区分"), None)
    assert db_session.get(ContentMasterRevision, saved["master_id"]).source_body_revision_id is not None


def test_persona_default_forms(client, db_session, setup):
    _user, persona, _project = setup
    assert client.get(f"/api/v1/content-personas/{persona}/default-forms").json()["forms"] == ["long_article"]
    client.put(f"/api/v1/content-personas/{persona}/default-forms", json={"forms": ["video_landscape", "long_article", "graphic_cards"]})
    assert client.get(f"/api/v1/content-personas/{persona}/default-forms").json()["forms"] == ["long_article", "graphic_cards", "video_landscape"]


def test_platform_limits_only_warn():
    from app.services.platform_limits import check

    copy = {"title": "两个几乎一样的因子到底能不能分出好坏", "hashtags": ["量化"], "description": ""}
    assert check("bilibili", copy) == []
    warned = check("wechat_channels", copy)
    assert warned and warned[0]["field"] == "title" and "视频号短标题最多 16 字" in warned[0]["message"]


def test_writing_standard_is_one_shared_skill(client, db_session, setup):
    user, persona, project = setup
    client.post(f"/api/v1/content-projects/{project}/forms", json={"persona_id": persona, "forms": ["graphic_cards", "video_portrait"]})
    units = _units(db_session, project)
    _finalize(client, db_session, user, project, units["body"].id)
    graphic = article_chain.brief(db_session, user, project, units["graphic_cards"].id)["form"]["writing_standard"]
    video = video_chain.brief(db_session, user, project, units["video_portrait"].id)["form"]["writing_standard"]
    assert graphic["version"] == video["version"] and graphic["skill"] == "craft-writing"
    assert db_session.get(ContentProject, project).form_plan_json["forms"] == ["graphic_cards", "video_portrait"]
