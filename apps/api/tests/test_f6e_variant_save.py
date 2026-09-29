"""First F6E append-only Text Variant save keeps exact source/profile and per-series CAS."""

from types import SimpleNamespace

from sqlalchemy import select

from app.models import ChannelTemplateVersion, ChannelVariantRevision, ProjectEvent
from app.seed import seed_v1_channel_profiles
from app.services.channel_variants import _variant_context


def _source(client, db_session):
    seed_v1_channel_profiles(db_session)
    db_session.commit()
    headers = {"X-Studio-User": "variant-save@studio.local"}
    persona = client.post("/api/v1/content-personas", json={"name": "作者"}, headers=headers).json()["id"]
    project = client.post("/api/v1/content-projects", json={"title": "渠道适配"}, headers=headers).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project}/units", json={"title": "源稿", "persona_id": persona, "modality": "text", "channel_id": "wechat"}, headers=headers).json()["id"]
    source_payload = {"title": "原稿", "document": {"schema": "studio.text.document.v1", "blocks": [{"id": "b1", "type": "paragraph", "content": [{"text": "有来源的原文", "marks": []}]}], "citations": []}}
    path = f"/api/v1/content-projects/{project}/units/{unit}/master-revisions"
    response = client.post(path, json={"idempotency_key": "source-master", "payload_schema": "text.master.v2", "content_form": "article", "payload": source_payload}, headers=headers)
    assert response.status_code == 200, response.text
    return project, unit, response.json(), headers


def test_text_variant_save_is_append_only_idempotent_and_series_scoped(client, db_session):
    project, unit, master, headers = _source(client, db_session)
    path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    body = {
        "variant_key": "x.single.primary", "expected_revision": 0, "source_master_revision_id": master["id"],
        "expected_source_payload_hash": master["payload_hash"], "expected_source_context_hash": master["context_hash"],
        "channel_id": "x", "content_form": "single", "idempotency_key": "variant-save-1", "payload": {"text": "有来源的原文"},
    }
    first = client.post(path, json=body, headers=headers)
    assert first.status_code == 201, first.text
    assert first.json()["revision_no"] == 1
    assert first.json()["source_master_revision_id"] == master["id"]
    assert first.json()["payload_schema"] == "x.single.v1"
    assert first.json()["profile_template_version_id"] is not None
    replay = client.post(path, json=body, headers=headers)
    assert replay.status_code == 201
    assert replay.json()["id"] == first.json()["id"]
    changed = client.post(path, json={**body, "payload": {"text": "另一个版本"}}, headers=headers)
    assert changed.status_code == 409
    stale = client.post(path, json={**body, "idempotency_key": "variant-save-2", "payload": {"text": "另一个版本"}}, headers=headers)
    assert stale.status_code == 409
    assert client.get(path, headers=headers).json()["items"][0]["id"] == first.json()["id"]
    current_master = client.get(f"/api/v1/content-projects/{project}/units/{unit}/master-revisions/current", headers=headers).json()
    assert current_master["id"] == master["id"]
    assert current_master["payload_hash"] == master["payload_hash"]
    assert client.post(path, json={**body, "idempotency_key": "foreign-write"}, headers={"X-Studio-User": "other@studio.local"}).status_code == 404


def test_variant_context_hash_freezes_exact_profile_version_not_only_profile_row_id():
    master = SimpleNamespace(id=1, payload_hash="a" * 64, context_hash="b" * 64)
    capability = {"artifact_kind": "text", "profile_version_id": 7, "profile_version": 100, "profile_hash": "c" * 64, "adapter_key": "x.single", "adapter_version": "1"}
    first = _variant_context(master, None, None, "x", "single", capability, "d" * 64)
    newer = _variant_context(master, None, None, "x", "single", {**capability, "profile_version": 101}, "d" * 64)
    assert first != newer


def test_profile_demoted_before_variant_commit_rolls_back_row_and_event(client, db_session, monkeypatch):
    from app.services import channel_variants as service

    project, unit, master, headers = _source(client, db_session)
    profile = db_session.scalar(select(ChannelTemplateVersion).where(ChannelTemplateVersion.channel == "x"))
    original_record = service.record_project_event

    def demote_on_event(db, **kwargs):
        result = original_record(db, **kwargs)
        db.get(ChannelTemplateVersion, profile.id).status = "archived"
        return result

    monkeypatch.setattr(service, "record_project_event", demote_on_event)
    path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    response = client.post(path, json={
        "variant_key": "x.single.primary", "expected_revision": 0, "source_master_revision_id": master["id"],
        "expected_source_payload_hash": master["payload_hash"], "expected_source_context_hash": master["context_hash"],
        "channel_id": "x", "content_form": "single", "idempotency_key": "profile-race", "payload": {"text": "内容"},
    }, headers=headers)
    assert response.status_code == 409, response.text
    assert db_session.scalars(select(ChannelVariantRevision)).all() == []
    assert db_session.scalars(select(ProjectEvent).where(ProjectEvent.event_type == "channel_variant.saved")).all() == []
    db_session.expire(profile)
    assert profile.status == "published"


def test_variant_series_have_independent_heads_and_cannot_retarget(client, db_session):
    project, unit, master, headers = _source(client, db_session)
    path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    common = {
        "expected_revision": 0, "source_master_revision_id": master["id"],
        "expected_source_payload_hash": master["payload_hash"], "expected_source_context_hash": master["context_hash"],
        "channel_id": "x", "content_form": "single", "payload": {"text": "单条"},
    }
    single = client.post(path, json={**common, "variant_key": "single-primary", "idempotency_key": "single-1"}, headers=headers)
    assert single.status_code == 201, single.text
    thread = client.post(path, json={**common, "variant_key": "thread-primary", "content_form": "thread", "payload": {"posts": [{"id": "p1", "order": 0, "text": "推文"}]}, "idempotency_key": "thread-1"}, headers=headers)
    assert thread.status_code == 201, thread.text
    second = client.post(path, json={**common, "variant_key": "single-primary", "expected_revision": 1, "payload": {"text": "单条修订"}, "idempotency_key": "single-2"}, headers=headers)
    assert second.status_code == 201, second.text
    assert second.json()["parent_revision_id"] == single.json()["id"]
    assert second.json()["revision_no"] == 2
    current_single = client.get(f"{path}/current", params={"variant_key": "single-primary"}, headers=headers).json()
    current_thread = client.get(f"{path}/current", params={"variant_key": "thread-primary"}, headers=headers).json()
    assert current_single["id"] == second.json()["id"]
    assert current_thread["id"] == thread.json()["id"]
    retarget = client.post(path, json={**common, "variant_key": "single-primary", "expected_revision": 2, "content_form": "thread", "payload": {"posts": [{"id": "p1", "order": 0, "text": "换目标"}]}, "idempotency_key": "bad-retarget"}, headers=headers)
    assert retarget.status_code == 409
    assert client.get(f"{path}/current", params={"variant_key": "single-primary"}, headers=headers).json()["id"] == second.json()["id"]


def test_unsupported_source_target_has_typed_no_write_result(client, db_session):
    project, unit, master, headers = _source(client, db_session)
    path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    response = client.post(path, json={
        "variant_key": "image-note", "expected_revision": 0, "source_master_revision_id": master["id"],
        "expected_source_payload_hash": master["payload_hash"], "expected_source_context_hash": master["context_hash"],
        "channel_id": "xiaohongshu", "content_form": "image_note", "idempotency_key": "unsupported",
        "payload": {"title": "图文", "cards": [{"id": "c1", "order": 0, "image_ref_key": "cover", "caption": "图文"}]},
    }, headers=headers)
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "variant_adapter_unavailable"
    assert client.get(path, headers=headers).json()["items"] == []
