"""Channel Registry（V1 PRD 2.0 D3）：渠道/内容形态唯一入口。

覆盖：profile publish → 新渠道无需改 models.Channel；duplicate content form；
legacy 渠道兼容与默认形态；未知渠道拒绝；targets 归一化。
"""

import pytest

from app.models import Channel, ChannelTemplateVersion, FactPack, User

ADMIN = {"X-Studio-User": "admin@studio.local"}
EDITOR = {"X-Studio-User": "editor@studio.local"}

ZHIHU_PROFILE = {
    "content_forms": {
        "article": {
            "artifact_kind": "text",
            "default_workflow_key": "workflow.zhihu.article",
            "renderer_key": "renderer.zhihu.article",
            "rule_sets": ["rules.common.article"],
        },
        "answer": {
            "artifact_kind": "text",
            "default_workflow_key": "workflow.zhihu.answer",
        },
    }
}


@pytest.fixture
def seed_users(db_session):
    db_session.add(User(email="admin@studio.local", name="Admin", role="admin"))
    db_session.add(User(email="editor@studio.local", name="Editor", role="editor"))
    db_session.commit()


@pytest.fixture
def frozen_pack(db_session) -> FactPack:
    from app.models import FactPackStatus

    pack = FactPack(name="registry 测试包", version=1, status=FactPackStatus.frozen.value, checksum="c" * 64)
    db_session.add(pack)
    db_session.commit()
    return pack


def _publish(client, db_session, channel: str, profile: dict, version: int = 1):
    """建 draft profile 模板并发布，返回模板行 id。"""
    row = ChannelTemplateVersion(
        channel=channel, version=version, name=f"{channel} Profile", status="draft",
        profile_schema_version=1, profile_json=profile,
    )
    db_session.add(row)
    db_session.commit()
    resp = client.post(
        f"/api/v1/templates/channel-templates/{row.id}/status", json={"status": "published"}, headers=ADMIN
    )
    assert resp.status_code == 200
    return row.id


def test_new_channel_via_profile_without_enum(client, seed_users, db_session):
    """发布新渠道 profile 后：/channels 可见、topic 可选，全程无需改 models.Channel。"""
    assert "zhihu" not in {c.value for c in Channel}  # 前置：enum 未动
    _publish(client, db_session, "zhihu", ZHIHU_PROFILE)

    channels = {c["channel"]: c for c in client.get("/api/v1/channels", headers=EDITOR).json()}
    assert "zhihu" in channels
    forms = {f["content_form"] for f in channels["zhihu"]["content_forms"]}
    assert forms == {"article", "answer"}
    assert "zhihu" not in {c.value for c in Channel}  # 后置：仍无需 enum

    detail = client.get("/api/v1/channels/zhihu", headers=EDITOR).json()
    assert detail["content_forms"][0]["workflow_key"] == "workflow.zhihu.article"


def test_duplicate_content_form_rejected(client, seed_users, db_session):
    """profile 校验：content form 非法 artifact_kind / 空 content_forms 被拒。"""
    row = ChannelTemplateVersion(
        channel="zhihu", version=1, name="坏 Profile", status="draft",
        profile_json={"content_forms": {"article": {"artifact_kind": "hologram"}}},
    )
    db_session.add(row)
    db_session.commit()
    resp = client.post(f"/api/v1/templates/channel-templates/{row.id}/status", json={"status": "published"}, headers=ADMIN)
    assert resp.status_code == 422

    empty = ChannelTemplateVersion(
        channel="zhihu", version=2, name="空 Profile", status="draft", profile_json={"content_forms": {}}
    )
    db_session.add(empty)
    db_session.commit()
    resp2 = client.post(f"/api/v1/templates/channel-templates/{empty.id}/status", json={"status": "published"}, headers=ADMIN)
    assert resp2.status_code == 422


def test_legacy_channels_still_valid_with_default_forms(client, seed_users):
    """legacy 三渠道经兜底可用；已下线的 x_thread 不再出现在渠道列表。"""
    channels = {c["channel"]: c for c in client.get("/api/v1/channels", headers=EDITOR).json()}
    assert {"douyin", "xiaohongshu", "wechat"} <= set(channels)
    assert "x_thread" not in channels
    default_form = {ch: forms["content_forms"][0]["content_form"] for ch, forms in channels.items()}
    assert default_form["wechat"] == "article"
    assert default_form["douyin"] == "spoken_script"
    assert default_form["xiaohongshu"] == "image_note"
    kinds = {ch: forms["content_forms"][0]["artifact_kind"] for ch, forms in channels.items()}
    assert kinds["douyin"] == "script"
    assert kinds["wechat"] == "text"


def test_retired_x_thread_is_not_selectable(client, seed_users, frozen_pack):
    """旧键不能再被列出、查询或写成新选题。"""
    listed = client.get("/api/v1/channels", headers=EDITOR)
    assert listed.status_code == 200
    assert "x_thread" not in {item["channel"] for item in listed.json()}
    detail = client.get("/api/v1/channels/x_thread", headers=EDITOR)
    assert detail.status_code == 404
    assert "已下线" in detail.json()["detail"]
    created = client.post(
        "/api/v1/topics",
        json={"title": "旧渠道", "fact_pack_id": frozen_pack.id, "channels": ["x_thread"]},
        headers=EDITOR,
    )
    assert created.status_code == 400
    assert "已下线" in created.json()["detail"]


def test_exact_video_profile_projects_video_requirements(db_session):
    from app.services.content_harness.channel_registry import resolve_content_form

    rules = {"max_duration_ms": 90_000, "allowed_aspect_ratios": [[9, 16]], "subtitle_required": True}
    db_session.add(ChannelTemplateVersion(
        channel="video_profile_fixture", version=1, name="Video Profile", status="published",
        profile_json={"content_forms": {"short": {"artifact_kind": "video", "video_requirements": rules}}},
    ))
    db_session.commit()
    form = resolve_content_form(db_session, "video_profile_fixture", "short")
    assert form.video_requirements == rules
    assert form.to_dict()["video_requirements"] == rules


def test_unknown_channel_rejected_on_topic(client, seed_users, frozen_pack):
    """未注册渠道建 Topic 被拒（400），且不进入 channels。"""
    resp = client.post(
        "/api/v1/topics",
        json={"title": "t", "fact_pack_id": frozen_pack.id, "channels": ["toutiao"]},
        headers=EDITOR,
    )
    assert resp.status_code == 400
    assert "toutiao" in resp.json()["detail"]


def test_topic_targets_truth_and_channels_compat(client, seed_users, db_session, frozen_pack):
    """targets_json 为真源（zhihu article+answer 并存），channels 写去重兼容值。"""
    row = ChannelTemplateVersion(
        channel="zhihu", version=1, name="知乎 Profile", status="draft",
        profile_json=ZHIHU_PROFILE,
    )
    db_session.add(row)
    db_session.commit()
    client.post(f"/api/v1/templates/channel-templates/{row.id}/status", json={"status": "published"}, headers=ADMIN)

    resp = client.post(
        "/api/v1/topics",
        json={
            "title": "知乎双形态",
            "fact_pack_id": frozen_pack.id,
            "targets": [{"channel": "zhihu", "content_form": "article"}, {"channel": "zhihu", "content_form": "answer"}],
        },
        headers=EDITOR,
    )
    assert resp.status_code == 201, resp.json()
    body = resp.json()
    assert {(t["channel"], t["content_form"]) for t in body["targets"]} == {("zhihu", "article"), ("zhihu", "answer")}
    assert body["channels"] == ["zhihu"]

    # 重复 target 去重
    resp2 = client.post(
        "/api/v1/topics",
        json={
            "title": "去重",
            "fact_pack_id": frozen_pack.id,
            "targets": [{"channel": "wechat"}, {"channel": "wechat"}],
        },
        headers=EDITOR,
    )
    assert resp2.status_code == 201
    assert len(resp2.json()["targets"]) == 1


def test_legacy_channels_payload_still_accepted(client, seed_users, frozen_pack):
    """旧客户端只传 channels 仍可用（默认形态映射）。"""
    resp = client.post(
        "/api/v1/topics",
        json={"title": "旧语义", "fact_pack_id": frozen_pack.id, "channels": ["wechat", "douyin"]},
        headers=EDITOR,
    )
    assert resp.status_code == 201
    targets = {(t["channel"], t["content_form"]) for t in resp.json()["targets"]}
    assert targets == {("wechat", "article"), ("douyin", "spoken_script")}
