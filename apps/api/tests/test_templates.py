"""模板中心删除功能测试：引用保护 / 已发布 Prompt 不可删 / RBAC。"""

import pytest

from app.models import (
    BrandVoiceVersion,
    ChannelTemplateVersion,
    ContentJob,
    FactPack,
    PromptVersion,
    TopicBrief,
)

ADMIN = {"X-Studio-User": "admin@studio.local"}
EDITOR = {"X-Studio-User": "editor@studio.local"}


@pytest.fixture
def seed_users(db_session):
    """内存库无种子用户：admin 不会自动建号（默认角色是 editor），需显式种入。"""
    from app.models import User

    db_session.add(User(email="admin@studio.local", name="Admin", role="admin"))
    db_session.add(User(email="editor@studio.local", name="Editor", role="editor"))
    db_session.commit()


@pytest.fixture
def bv(db_session) -> BrandVoiceVersion:
    row = BrandVoiceVersion(name="测试风格", version=1, status="draft")
    db_session.add(row)
    db_session.commit()
    return row


@pytest.fixture
def ct(db_session) -> ChannelTemplateVersion:
    row = ChannelTemplateVersion(channel="douyin", version=99, name="测试模板", status="draft")
    db_session.add(row)
    db_session.commit()
    return row


def test_delete_brand_voice_without_reference(client, seed_users, bv):
    resp = client.delete(f"/api/v1/templates/brand-voices/{bv.id}", headers=ADMIN)
    assert resp.status_code == 200
    assert resp.json()["deleted"] is True
    ids = [x["id"] for x in client.get("/api/v1/templates/brand-voices", headers=ADMIN).json()]
    assert bv.id not in ids


def test_delete_brand_voice_referenced_by_topic(client, seed_users, db_session, bv):
    fp = FactPack(name="fp", version=1)
    db_session.add(fp)
    db_session.flush()
    db_session.add(
        TopicBrief(
            title="选题",
            fact_pack_id=fp.id,
            fact_pack_version=1,
            brand_voice_version_id=bv.id,
        )
    )
    db_session.commit()
    resp = client.delete(f"/api/v1/templates/brand-voices/{bv.id}", headers=ADMIN)
    assert resp.status_code == 409
    assert "引用" in resp.json()["detail"]


def test_delete_channel_template_without_reference(client, seed_users, ct):
    resp = client.delete(f"/api/v1/templates/channel-templates/{ct.id}", headers=ADMIN)
    assert resp.status_code == 200
    ids = [x["id"] for x in client.get("/api/v1/templates/channel-templates", headers=ADMIN).json()]
    assert ct.id not in ids


def test_delete_channel_template_referenced_by_job(client, seed_users, db_session, ct):
    fp = FactPack(name="fp", version=1)
    db_session.add(fp)
    db_session.flush()
    tb = TopicBrief(title="选题", fact_pack_id=fp.id, fact_pack_version=1)
    db_session.add(tb)
    db_session.flush()
    db_session.add(
        ContentJob(topic_brief_id=tb.id, channel="douyin", template_version_id=ct.id)
    )
    db_session.commit()
    resp = client.delete(f"/api/v1/templates/channel-templates/{ct.id}", headers=ADMIN)
    assert resp.status_code == 409
    assert "引用" in resp.json()["detail"]


def test_delete_prompt_published_blocked_draft_ok(client, seed_users, db_session):
    published = PromptVersion(
        channel="douyin", version=1, name="已发布", template_text="...", status="published"
    )
    draft = PromptVersion(channel="douyin", version=2, name="草稿", template_text="...", status="draft")
    db_session.add_all([published, draft])
    db_session.commit()
    resp = client.delete(f"/api/v1/templates/prompts/{published.id}", headers=ADMIN)
    assert resp.status_code == 409
    assert "同步" in resp.json()["detail"]
    resp = client.delete(f"/api/v1/templates/prompts/{draft.id}", headers=ADMIN)
    assert resp.status_code == 200


def test_delete_template_requires_admin(client, seed_users, bv, ct):
    assert client.delete(f"/api/v1/templates/brand-voices/{bv.id}", headers=EDITOR).status_code == 403
    assert client.delete(f"/api/v1/templates/channel-templates/{ct.id}", headers=EDITOR).status_code == 403


def test_delete_missing_returns_404(client, seed_users):
    assert client.delete("/api/v1/templates/brand-voices/9999", headers=ADMIN).status_code == 404
    assert client.delete("/api/v1/templates/channel-templates/9999", headers=ADMIN).status_code == 404
    assert client.delete("/api/v1/templates/prompts/9999", headers=ADMIN).status_code == 404


# ---------- 单一生效：发布新版本自动下线同范围旧版本 ----------


def _published_channels(client, channel: str) -> list[int]:
    return [
        t["version"]
        for t in client.get("/api/v1/templates/channel-templates", headers=ADMIN).json()
        if t["channel"] == channel and t["status"] == "published"
    ]


def test_publish_template_demotes_previous_published(client, seed_users, db_session):
    v1 = ChannelTemplateVersion(channel="douyin", version=1, name="旧", status="published")
    v2 = ChannelTemplateVersion(channel="douyin", version=2, name="新", status="draft")
    other = ChannelTemplateVersion(channel="wechat", version=1, name="别渠道", status="published")
    db_session.add_all([v1, v2, other])
    db_session.commit()
    resp = client.post(f"/api/v1/templates/channel-templates/{v2.id}/status", headers=ADMIN, json={"status": "published"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "published"
    # API 与测试共享 session：update(synchronize_session=False) 后需过期缓存再断言
    db_session.expire_all()
    # 同渠道只剩 v2 生效；v1 自动下线；其他渠道不受影响
    assert _published_channels(client, "douyin") == [2]
    v1_row = db_session.query(ChannelTemplateVersion).filter_by(id=v1.id).first()
    assert v1_row.status == "archived"
    assert _published_channels(client, "wechat") == [1]


def test_publish_brand_voice_demotes_same_name_only(client, seed_users, db_session):
    v1 = BrandVoiceVersion(name="风格A", version=1, status="published")
    v2 = BrandVoiceVersion(name="风格A", version=2, status="draft")
    keep = BrandVoiceVersion(name="风格B", version=1, status="published")
    db_session.add_all([v1, v2, keep])
    db_session.commit()
    resp = client.post(f"/api/v1/templates/brand-voices/{v2.id}/status", headers=ADMIN, json={"status": "published"})
    assert resp.status_code == 200
    db_session.expire_all()
    rows = {b["name"] + str(b["version"]): b["status"] for b in client.get("/api/v1/templates/brand-voices", headers=ADMIN).json()}
    assert rows["风格A2"] == "published"
    assert rows["风格A1"] == "archived"
    assert rows["风格B1"] == "published"  # 同名才下线，其他 Voice 不受影响


def test_publish_prompt_demotes_same_channel(client, seed_users, db_session):
    v1 = PromptVersion(channel="douyin", version=1, name="旧", template_text="a", status="published")
    v2 = PromptVersion(channel="douyin", version=2, name="新", template_text="b", status="draft")
    db_session.add_all([v1, v2])
    db_session.commit()
    resp = client.post(f"/api/v1/templates/prompts/{v2.id}/status", headers=ADMIN, json={"status": "published"})
    assert resp.status_code == 200
    db_session.expire_all()
    statuses = {p["version"]: p["status"] for p in client.get("/api/v1/templates/prompts", headers=ADMIN).json() if p["channel"] == "douyin"}
    assert statuses == {1: "archived", 2: "published"}


def test_normalize_keeps_only_latest_published(client, seed_users, db_session):
    from app.routers.templates import normalize_template_publication

    db_session.add_all(
        [
            ChannelTemplateVersion(channel="xiaohongshu", version=1, name="v1", status="published"),
            ChannelTemplateVersion(channel="xiaohongshu", version=3, name="v3", status="published"),
        ]
    )
    db_session.commit()
    assert normalize_template_publication(db_session) == 1
    assert _published_channels(client, "xiaohongshu") == [3]


# ---------- 不可更改铁律：模板中心任何内容（含克隆草稿）都没有编辑入口 ----------


def test_template_content_has_no_mutation_endpoint(client, seed_users, bv, ct):
    """克隆草稿也不可编辑：不存在内容更新端点，PATCH/PUT 一律 405。"""
    assert client.patch(f"/api/v1/templates/channel-templates/{ct.id}", headers=ADMIN, json={"name": "改"}).status_code == 405
    assert client.put(f"/api/v1/templates/channel-templates/{ct.id}", headers=ADMIN, json={"name": "改"}).status_code == 405
    assert client.patch(f"/api/v1/templates/brand-voices/{bv.id}", headers=ADMIN, json={"name": "改"}).status_code == 405
    assert client.put("/api/v1/templates/prompts/1", headers=ADMIN, json={"template_text": "改"}).status_code == 405
