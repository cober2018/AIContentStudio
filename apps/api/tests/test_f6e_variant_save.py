"""First F6E append-only Text Variant save keeps exact source/profile and per-series CAS."""

import hashlib
from types import SimpleNamespace

from sqlalchemy import select

from app.models import (
    ChannelTemplateVersion,
    ChannelVariantCheckRun,
    ChannelVariantRevision,
    FactPack,
    FactPackItem,
    Material,
    MaterialRevision,
    ProjectEvent,
    ProjectMaterialReference,
)
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
    first_checks_path = f"{path}/{single.json()['id']}/checks"
    assert client.post(first_checks_path, headers=headers).json()["items"][0]["status"] == "pass"
    thread = client.post(path, json={**common, "variant_key": "thread-primary", "content_form": "thread", "payload": {"posts": [{"id": "p1", "order": 0, "text": "推文"}]}, "idempotency_key": "thread-1"}, headers=headers)
    assert thread.status_code == 201, thread.text
    second = client.post(path, json={**common, "variant_key": "single-primary", "expected_revision": 1, "payload": {"text": "单条修订"}, "idempotency_key": "single-2"}, headers=headers)
    assert second.status_code == 201, second.text
    assert second.json()["parent_revision_id"] == single.json()["id"]
    assert second.json()["revision_no"] == 2
    assert client.get(first_checks_path, headers=headers).json()["items"][0]["status"] == "stale"
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


def test_text_variant_citation_binds_exact_frozen_boundary_and_rolls_back_invalid_ref(client, db_session):
    project, unit, master, headers = _source(client, db_session)
    pack = FactPack(name="可核对事实", version=1, status="frozen", checksum="p" * 64)
    db_session.add(pack)
    db_session.flush()
    item = FactPackItem(fact_pack_id=pack.id, evidence_kind="fact", snapshot_json={"statement": "有来源"}, snapshot_checksum="a" * 64, public_use_allowed=True)
    db_session.add(item)
    db_session.commit()
    boundary = client.post(f"/api/v1/content-projects/{project}/fact-boundary", json={"fact_pack_id": pack.id, "expected_revision": 0}, headers=headers)
    assert boundary.status_code == 201, boundary.text
    source_path = f"/api/v1/content-projects/{project}/units/{unit}/master-revisions"
    second_source = client.post(source_path, json={
        "idempotency_key": "source-with-boundary", "expected_revision": 1, "payload_schema": "text.master.v2",
        "payload": master["payload"],
    }, headers=headers)
    assert second_source.status_code == 200, second_source.text
    source = second_source.json()
    path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    evidence = {"fact_pack_item_id": item.id, "snapshot_checksum": item.snapshot_checksum, "role": "claim", "content_locator_json": {"location_id": "single", "start": 0, "end": 2}, "sort_order": 0}
    body = {
        "variant_key": "x-single-cited", "expected_revision": 0, "source_master_revision_id": source["id"],
        "expected_source_payload_hash": source["payload_hash"], "expected_source_context_hash": source["context_hash"],
        "channel_id": "x", "content_form": "single", "idempotency_key": "cited-1",
        "payload": {"text": "有来源的原文", "citations": [{"id": "c1", "location_id": "single", "fact_pack_item_id": item.id, "snapshot_checksum": item.snapshot_checksum, "locator": {"start": 0, "end": 2}}]},
        "evidence_refs": [evidence],
    }
    invalid = client.post(path, json={**body, "idempotency_key": "cited-bad", "evidence_refs": [{**evidence, "snapshot_checksum": "x" * 64}]}, headers=headers)
    assert invalid.status_code == 422, invalid.text
    assert client.get(path, headers=headers).json()["items"] == []
    accepted = client.post(path, json=body, headers=headers)
    assert accepted.status_code == 201, accepted.text
    assert accepted.json()["evidence"][0]["fact_pack_item_id"] == item.id
    assert accepted.json()["evidence"][0]["locator"] == evidence["content_locator_json"]
    assert client.post(path, json=body, headers=headers).json()["id"] == accepted.json()["id"]
    checks_path = f"{path}/{accepted.json()['id']}/checks"
    checked = client.post(checks_path, headers=headers).json()
    assert checked["items"][0]["status"] == "pass"
    citation_check = next(entry for entry in checked["items"] if entry["check_kind"] == "variant_evidence")
    assert citation_check["status"] == "incomplete"
    assert "citation_semantics_unverified" in citation_check["report"]["reasons"]
    item.public_use_allowed = False
    db_session.commit()
    revoked_checks = client.get(checks_path, headers=headers)
    assert revoked_checks.status_code == 200, revoked_checks.text
    assert revoked_checks.json()["items"][0]["status"] == "stale"
    assert "evidence_changed" in revoked_checks.json()["drift_reasons"]
    item.public_use_allowed = True
    db_session.commit()
    oversized_role = client.post(path, json={**body, "variant_key": "x-single-bad-role", "idempotency_key": "cited-bad-role", "evidence_refs": [{**evidence, "role": "r" * 41}]}, headers=headers)
    assert oversized_role.status_code == 422, oversized_role.text


def test_text_variant_citation_revoked_before_commit_rolls_back_variant_and_event(client, db_session, monkeypatch):
    from app.services import channel_variants as service

    project, unit, master, headers = _source(client, db_session)
    pack = FactPack(name="待撤权事实", version=1, status="frozen", checksum="b" * 64)
    db_session.add(pack)
    db_session.flush()
    item = FactPackItem(fact_pack_id=pack.id, evidence_kind="fact", snapshot_json={"statement": "有来源"}, snapshot_checksum="a" * 64, public_use_allowed=True)
    db_session.add(item)
    db_session.commit()
    assert client.post(f"/api/v1/content-projects/{project}/fact-boundary", json={"fact_pack_id": pack.id, "expected_revision": 0}, headers=headers).status_code == 201
    source = client.post(f"/api/v1/content-projects/{project}/units/{unit}/master-revisions", json={
        "idempotency_key": "source-boundary-race", "expected_revision": 1, "payload_schema": "text.master.v2", "payload": master["payload"],
    }, headers=headers).json()
    original_record = service.record_project_event

    def revoke_on_event(db, **kwargs):
        result = original_record(db, **kwargs)
        db.get(FactPackItem, item.id).public_use_allowed = False
        db.flush()
        return result

    monkeypatch.setattr(service, "record_project_event", revoke_on_event)
    path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    response = client.post(path, json={
        "variant_key": "x-single-race", "expected_revision": 0, "source_master_revision_id": source["id"],
        "expected_source_payload_hash": source["payload_hash"], "expected_source_context_hash": source["context_hash"],
        "channel_id": "x", "content_form": "single", "idempotency_key": "cited-race",
        "payload": {"text": "有来源的原文", "citations": [{"id": "c1", "location_id": "single", "fact_pack_item_id": item.id, "snapshot_checksum": item.snapshot_checksum, "locator": {"start": 0, "end": 2}}]},
        "evidence_refs": [{"fact_pack_item_id": item.id, "snapshot_checksum": item.snapshot_checksum, "role": "claim", "content_locator_json": {"location_id": "single", "start": 0, "end": 2}}],
    }, headers=headers)
    assert response.status_code == 409, response.text
    assert db_session.scalars(select(ChannelVariantRevision)).all() == []
    assert db_session.scalars(select(ProjectEvent).where(ProjectEvent.event_type == "channel_variant.saved")).all() == []
    db_session.expire(item)
    assert item.public_use_allowed is True


def test_malformed_variant_evidence_ref_returns_domain_error_without_write(client, db_session):
    project, unit, master, headers = _source(client, db_session)
    pack = FactPack(name="畸形引用测试", version=1, status="frozen", checksum="b" * 64)
    db_session.add(pack)
    db_session.commit()
    assert client.post(f"/api/v1/content-projects/{project}/fact-boundary", json={"fact_pack_id": pack.id, "expected_revision": 0}, headers=headers).status_code == 201
    source = client.post(f"/api/v1/content-projects/{project}/units/{unit}/master-revisions", json={
        "idempotency_key": "malformed-ref-source", "expected_revision": 1, "payload_schema": "text.master.v2", "payload": master["payload"],
    }, headers=headers).json()
    path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    response = client.post(path, json={
        "variant_key": "bad-citation", "expected_revision": 0, "source_master_revision_id": source["id"],
        "expected_source_payload_hash": source["payload_hash"], "expected_source_context_hash": source["context_hash"],
        "channel_id": "x", "content_form": "single", "idempotency_key": "bad-citation",
        "payload": {"text": "文字"}, "evidence_refs": [{"fact_pack_item_id": [], "snapshot_checksum": "a" * 64, "content_locator_json": {"location_id": "single", "start": 0, "end": 1}}],
    }, headers=headers)
    assert response.status_code == 422, response.text
    assert client.get(path, headers=headers).json()["items"] == []


def test_adapt_preview_uses_exact_current_master_profile_and_does_not_write(client, db_session):
    project, unit, master, headers = _source(client, db_session)
    path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants/adapt-preview"
    body = {
        "source_master_revision_id": master["id"], "expected_source_payload_hash": master["payload_hash"],
        "expected_source_context_hash": master["context_hash"], "channel_id": "x", "content_form": "single",
    }
    preview = client.post(path, json=body, headers=headers)
    assert preview.status_code == 200, preview.text
    assert preview.json()["payload_schema"] == "x.single.v1"
    assert preview.json()["payload"]["text"] == "有来源的原文"
    assert preview.json()["source_master_revision_id"] == master["id"]
    assert preview.json()["profile_template_version_id"] is not None
    assert client.get(f"/api/v1/content-projects/{project}/units/{unit}/channel-variants", headers=headers).json()["items"] == []
    assert client.post(path, json={**body, "expected_source_payload_hash": "f" * 64}, headers=headers).status_code == 409
    unavailable = client.post(path, json={**body, "channel_id": "xiaohongshu", "content_form": "image_note"}, headers=headers)
    assert unavailable.status_code == 422
    assert unavailable.json()["detail"]["code"] == "variant_adapter_unavailable"
    assert client.post(path, json=body, headers={"X-Studio-User": "foreign-preview@studio.local"}).status_code == 404


def test_variant_schema_check_is_append_only_bound_to_payload_and_does_not_imply_ready(client, db_session):
    project, unit, master, headers = _source(client, db_session)
    path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    variant = client.post(path, json={
        "variant_key": "single-checks", "expected_revision": 0, "source_master_revision_id": master["id"],
        "expected_source_payload_hash": master["payload_hash"], "expected_source_context_hash": master["context_hash"],
        "channel_id": "x", "content_form": "single", "idempotency_key": "single-checks-1", "payload": {"text": "有来源的原文"},
    }, headers=headers)
    assert variant.status_code == 201, variant.text
    checks_path = f"{path}/{variant.json()['id']}/checks"
    before = client.get(checks_path, headers=headers)
    assert before.status_code == 200, before.text
    assert {item["check_kind"]: item["status"] for item in before.json()["items"]}["variant_schema"] == "incomplete"
    assert before.json()["ready"] is False
    first = client.post(checks_path, headers=headers)
    assert first.status_code == 200, first.text
    schema = next(item for item in first.json()["items"] if item["check_kind"] == "variant_schema")
    assert schema["status"] == "pass"
    assert schema["is_current"] is True
    assert first.json()["ready"] is False
    assert len(db_session.scalars(select(ChannelVariantCheckRun)).all()) == 5
    assert client.get(checks_path, headers={"X-Studio-User": "foreign-check@studio.local"}).status_code == 404
    assert client.post(checks_path, headers={"X-Studio-User": "foreign-check@studio.local"}).status_code == 404


def test_x_single_variant_checks_record_projection_without_claiming_zip_or_source_readiness(client, db_session):
    project, unit, master, headers = _source(client, db_session)
    path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    saved = client.post(path, json={
        "variant_key": "x-check-coverage", "expected_revision": 0, "source_master_revision_id": master["id"],
        "expected_source_payload_hash": master["payload_hash"], "expected_source_context_hash": master["context_hash"],
        "channel_id": "x", "content_form": "single", "idempotency_key": "x-check-coverage-1",
        "source_kind": "deterministic_adapt", "payload": {"text": "有来源的原文"},
    }, headers=headers)
    assert saved.status_code == 201, saved.text
    checks = client.post(f"{path}/{saved.json()['id']}/checks", headers=headers)
    assert checks.status_code == 200, checks.text
    by_kind = {item["check_kind"]: item for item in checks.json()["items"]}
    assert {kind: by_kind[kind]["status"] for kind in ("variant_schema", "variant_profile", "variant_evidence", "variant_rights")} == {
        "variant_schema": "pass", "variant_profile": "pass", "variant_evidence": "pass", "variant_rights": "pass",
    }
    assert by_kind["variant_profile"]["report"]["coverage"]["remote_publisher"] == "unverified"
    assert by_kind["variant_package"]["status"] == "pass"
    assert by_kind["variant_package"]["report"]["coverage"] == "projection_only"
    assert by_kind["variant_package"]["report"]["local_zip"] == "not_generated"
    assert by_kind["variant_package"]["report"]["remote_effect"] == "unverified"
    assert checks.json()["source_gate"]["status"] == "incomplete"
    assert "evidence_missing" in checks.json()["source_gate"]["reasons"]
    assert checks.json()["ready"] is False
    assert len(db_session.scalars(select(ChannelVariantCheckRun)).all()) == 5


def test_wechat_article_missing_required_cover_blocks_profile_check(client, db_session):
    project, unit, master, headers = _source(client, db_session)
    path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    saved = client.post(path, json={
        "variant_key": "wechat-no-cover", "expected_revision": 0, "source_master_revision_id": master["id"],
        "expected_source_payload_hash": master["payload_hash"], "expected_source_context_hash": master["context_hash"],
        "channel_id": "wechat", "content_form": "article", "idempotency_key": "wechat-no-cover-1",
        "payload": {"title": "原稿", "blocks": [{"id": "b1", "order": 0, "kind": "paragraph", "text": "有来源的原文"}]},
    }, headers=headers)
    assert saved.status_code == 201, saved.text
    checks = client.post(f"{path}/{saved.json()['id']}/checks", headers=headers)
    assert checks.status_code == 200, checks.text
    profile = next(item for item in checks.json()["items"] if item["check_kind"] == "variant_profile")
    assert profile["status"] == "blocker"
    assert "cover_required" in profile["report"]["reasons"]
    package = next(item for item in checks.json()["items"] if item["check_kind"] == "variant_package")
    assert package["status"] == "incomplete"
    assert "prerequisite_unready:variant_profile" in package["report"]["reasons"]
    assert checks.json()["ready"] is False


def test_wechat_article_cover_is_exact_project_visible_media_and_revocation_blocks_save(client, db_session, tmp_path):
    project, unit, master, headers = _source(client, db_session)
    content = b"\x89PNG\r\n\x1a\nwechat cover bytes"
    file = tmp_path / "wechat-cover.png"
    file.write_bytes(content)
    material = Material(title="公众号封面", kind="image", status="active")
    db_session.add(material)
    db_session.flush()
    revision = MaterialRevision(material_id=material.id, content_hash=hashlib.sha256(content).hexdigest(), file_path=str(file),
                                mime_type="image/png", status="active", public_use_allowed=True, rights_status="cleared")
    db_session.add(revision)
    db_session.flush()
    db_session.add(ProjectMaterialReference(project_id=project, material_revision_id=revision.id, origin="system_library", status="active"))
    db_session.commit()
    path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    cover = {"material_revision_id": revision.id, "content_hash_snapshot": revision.content_hash,
             "role": "cover", "slot_key": "cover", "sort_order": 0, "placement": {"usage": "cover"}}
    body = {
        "variant_key": "wechat-with-cover", "expected_revision": 0, "source_master_revision_id": master["id"],
        "expected_source_payload_hash": master["payload_hash"], "expected_source_context_hash": master["context_hash"],
        "channel_id": "wechat", "content_form": "article", "idempotency_key": "wechat-cover-1",
        "source_kind": "deterministic_adapt",
        "payload": {"title": "原稿", "blocks": [{"id": "b1", "order": 0, "kind": "paragraph", "text": "有来源的原文"}]},
        "asset_refs": [cover],
    }
    invalid = client.post(path, json={**body, "idempotency_key": "wrong-cover", "asset_refs": [{**cover, "content_hash_snapshot": "f" * 64}]}, headers=headers)
    assert invalid.status_code == 422, invalid.text
    assert client.get(path, headers=headers).json()["items"] == []
    saved = client.post(path, json=body, headers=headers)
    assert saved.status_code == 201, saved.text
    assert saved.json()["assets"][0]["material_revision_id"] == revision.id
    checks = client.post(f"{path}/{saved.json()['id']}/checks", headers=headers)
    assert checks.status_code == 200, checks.text
    statuses = {item["check_kind"]: item["status"] for item in checks.json()["items"]}
    assert statuses["variant_profile"] == "pass"
    assert statuses["variant_evidence"] == "pass"
    assert statuses["variant_rights"] == "pass"
    assert statuses["variant_package"] == "pass"
    project_ref = db_session.scalar(select(ProjectMaterialReference).where(
        ProjectMaterialReference.project_id == project, ProjectMaterialReference.material_revision_id == revision.id,
    ))
    project_ref.status = "detached"
    db_session.commit()
    unshared = client.post(path, json={**body, "variant_key": "wechat-unshared", "idempotency_key": "wechat-unshared-1"}, headers=headers)
    assert unshared.status_code == 422, unshared.text
    project_ref.status = "active"
    db_session.commit()
    revision.public_use_allowed = False
    db_session.commit()
    assert "assets_or_render_changed" in client.get(f"{path}/{saved.json()['id']}/checks", headers=headers).json()["drift_reasons"]
    denied = client.post(path, json={**body, "variant_key": "wechat-revoked", "idempotency_key": "wechat-revoked-1"}, headers=headers)
    assert denied.status_code == 422, denied.text


def test_wechat_preview_inherits_exact_source_master_cover_without_copying_bytes(client, db_session, tmp_path):
    project, unit, master, headers = _source(client, db_session)
    content = b"\x89PNG\r\n\x1a\nsource cover bytes"
    file = tmp_path / "source-cover.png"
    file.write_bytes(content)
    material = Material(title="源稿封面", kind="image", status="active")
    db_session.add(material)
    db_session.flush()
    revision = MaterialRevision(material_id=material.id, content_hash=hashlib.sha256(content).hexdigest(), file_path=str(file),
                                mime_type="image/png", status="active", public_use_allowed=True, rights_status="cleared")
    db_session.add(revision)
    db_session.flush()
    db_session.add(ProjectMaterialReference(project_id=project, material_revision_id=revision.id, origin="system_library", status="active"))
    db_session.commit()
    master_path = f"/api/v1/content-projects/{project}/units/{unit}/master-revisions"
    newer = client.post(master_path, json={
        "idempotency_key": "master-with-cover", "expected_revision": 1, "payload_schema": "text.master.v2", "payload": master["payload"],
        "asset_refs": [{"material_revision_id": revision.id, "content_hash": revision.content_hash, "role": "cover",
                        "slot_key": "cover", "sort_order": 0, "placement": {"usage": "cover"}}],
    }, headers=headers)
    assert newer.status_code == 200, newer.text
    source = newer.json()
    path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    intent = {"source_master_revision_id": source["id"], "expected_source_payload_hash": source["payload_hash"],
              "expected_source_context_hash": source["context_hash"], "channel_id": "wechat", "content_form": "article"}
    preview = client.post(f"{path}/adapt-preview", json=intent, headers=headers)
    assert preview.status_code == 200, preview.text
    assert preview.json()["asset_refs"] == [{"material_revision_id": revision.id, "content_hash_snapshot": revision.content_hash,
                                              "role": "cover", "slot_key": "cover", "sort_order": 0, "placement": {"usage": "cover"}}]
    dropped = client.post(path, json={**intent, "variant_key": "inherited-cover", "expected_revision": 0,
                                       "idempotency_key": "drop-cover", "source_kind": "deterministic_adapt",
                                       "payload": preview.json()["payload"], "asset_refs": []}, headers=headers)
    assert dropped.status_code == 422, dropped.text
    saved = client.post(path, json={**intent, "variant_key": "inherited-cover", "expected_revision": 0,
                                     "idempotency_key": "inherited-cover-1", "source_kind": "deterministic_adapt",
                                     "payload": preview.json()["payload"], "asset_refs": preview.json()["asset_refs"]}, headers=headers)
    assert saved.status_code == 201, saved.text
    assert saved.json()["assets"][0]["material_revision_id"] == revision.id


def test_unmapped_manual_text_claim_is_not_evidence_verified(client, db_session):
    project, unit, master, headers = _source(client, db_session)
    path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    saved = client.post(path, json={
        "variant_key": "new-claim", "expected_revision": 0, "source_master_revision_id": master["id"],
        "expected_source_payload_hash": master["payload_hash"], "expected_source_context_hash": master["context_hash"],
        "channel_id": "x", "content_form": "single", "idempotency_key": "new-claim-1",
        "payload": {"text": "有来源的原文，而且新事实也成立"},
    }, headers=headers)
    assert saved.status_code == 201, saved.text
    checks = client.post(f"{path}/{saved.json()['id']}/checks", headers=headers)
    assert checks.status_code == 200, checks.text
    evidence = next(item for item in checks.json()["items"] if item["check_kind"] == "variant_evidence")
    assert evidence["status"] == "incomplete"
    assert "semantic_delta_requires_review" in evidence["report"]["reasons"]
    assert checks.json()["ready"] is False


def test_unexecutable_published_profile_rule_is_incomplete_not_a_server_error(client, db_session):
    project, unit, master, headers = _source(client, db_session)
    profile = db_session.scalar(select(ChannelTemplateVersion).where(ChannelTemplateVersion.channel == "x"))
    edited = dict(profile.profile_json)
    forms = dict(edited["content_forms"])
    forms["single"] = {**forms["single"], "rule_sets": [{"unknown": "rule"}]}
    edited["content_forms"] = forms
    profile.profile_json = edited
    db_session.commit()
    path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    saved = client.post(path, json={
        "variant_key": "unknown-rule", "expected_revision": 0, "source_master_revision_id": master["id"],
        "expected_source_payload_hash": master["payload_hash"], "expected_source_context_hash": master["context_hash"],
        "channel_id": "x", "content_form": "single", "idempotency_key": "unknown-rule-1", "payload": {"text": "有来源的原文"},
    }, headers=headers)
    assert saved.status_code == 201, saved.text
    checks = client.post(f"{path}/{saved.json()['id']}/checks", headers=headers)
    assert checks.status_code == 200, checks.text
    profile_check = next(item for item in checks.json()["items"] if item["check_kind"] == "variant_profile")
    assert profile_check["status"] == "incomplete"
    assert profile_check["report"]["coverage"]["rules"] == "unknown"


def test_variant_checks_become_stale_when_source_master_advances(client, db_session):
    project, unit, master, headers = _source(client, db_session)
    path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    saved = client.post(path, json={
        "variant_key": "source-drift", "expected_revision": 0, "source_master_revision_id": master["id"],
        "expected_source_payload_hash": master["payload_hash"], "expected_source_context_hash": master["context_hash"],
        "channel_id": "x", "content_form": "single", "idempotency_key": "source-drift-1", "payload": {"text": "有来源的原文"},
    }, headers=headers)
    assert saved.status_code == 201, saved.text
    checks_path = f"{path}/{saved.json()['id']}/checks"
    assert client.post(checks_path, headers=headers).json()["items"][0]["status"] == "pass"
    newer = client.post(f"/api/v1/content-projects/{project}/units/{unit}/master-revisions", json={
        "idempotency_key": "new-source", "expected_revision": 1, "payload_schema": "text.master.v2", "payload": master["payload"],
    }, headers=headers)
    assert newer.status_code == 200, newer.text
    projected = client.get(checks_path, headers=headers)
    assert projected.status_code == 200, projected.text
    assert projected.json()["items"][0]["status"] == "stale"
    assert projected.json()["ready"] is False


def test_variant_checks_become_stale_when_exact_profile_is_demoted(client, db_session):
    project, unit, master, headers = _source(client, db_session)
    path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    saved = client.post(path, json={
        "variant_key": "profile-drift", "expected_revision": 0, "source_master_revision_id": master["id"],
        "expected_source_payload_hash": master["payload_hash"], "expected_source_context_hash": master["context_hash"],
        "channel_id": "x", "content_form": "single", "idempotency_key": "profile-drift-1", "payload": {"text": "有来源的原文"},
    }, headers=headers)
    assert saved.status_code == 201, saved.text
    checks_path = f"{path}/{saved.json()['id']}/checks"
    assert client.post(checks_path, headers=headers).json()["items"][0]["status"] == "pass"
    profile = db_session.get(ChannelTemplateVersion, saved.json()["profile_template_version_id"])
    profile.status = "archived"
    db_session.commit()
    projected = client.get(checks_path, headers=headers)
    assert projected.status_code == 200, projected.text
    assert projected.json()["items"][0]["status"] == "stale"
    assert projected.json()["ready"] is False


def test_variant_later_corrupt_payload_check_blocks_earlier_pass(client, db_session):
    project, unit, master, headers = _source(client, db_session)
    path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    variant = client.post(path, json={
        "variant_key": "single-checks", "expected_revision": 0, "source_master_revision_id": master["id"],
        "expected_source_payload_hash": master["payload_hash"], "expected_source_context_hash": master["context_hash"],
        "channel_id": "x", "content_form": "single", "idempotency_key": "single-checks-1", "payload": {"text": "有来源的原文"},
    }, headers=headers).json()
    checks_path = f"{path}/{variant['id']}/checks"
    first = client.post(checks_path, headers=headers).json()
    old = next(item for item in first["items"] if item["check_kind"] == "variant_schema")
    row = db_session.get(ChannelVariantRevision, variant["id"])
    row.payload_json = {"text": "被篡改"}
    db_session.commit()
    stale = client.get(checks_path, headers=headers).json()
    stale_schema = next(item for item in stale["items"] if item["check_kind"] == "variant_schema")
    assert stale_schema["status"] == "stale"
    assert stale["ready"] is False
    second = client.post(checks_path, headers=headers)
    assert second.status_code == 200, second.text
    latest = next(item for item in second.json()["items"] if item["check_kind"] == "variant_schema")
    assert latest["status"] == "blocker"
    assert latest["input_hash"] != old["input_hash"]
    assert latest["id"] != old["id"]
    assert second.json()["ready"] is False
    assert len(db_session.scalars(select(ChannelVariantCheckRun)).all()) == 10


def test_later_variant_check_blocker_for_same_input_outranks_old_pass(client, db_session):
    project, unit, master, headers = _source(client, db_session)
    path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    variant = client.post(path, json={
        "variant_key": "single-checks", "expected_revision": 0, "source_master_revision_id": master["id"],
        "expected_source_payload_hash": master["payload_hash"], "expected_source_context_hash": master["context_hash"],
        "channel_id": "x", "content_form": "single", "idempotency_key": "single-checks-1", "payload": {"text": "有来源的原文"},
    }, headers=headers).json()
    checks_path = f"{path}/{variant['id']}/checks"
    first = client.post(checks_path, headers=headers).json()
    old = next(item for item in first["items"] if item["check_kind"] == "variant_schema")
    stored = db_session.get(ChannelVariantCheckRun, old["id"])
    db_session.add(ChannelVariantCheckRun(
        variant_revision_id=variant["id"], check_kind="variant_schema", input_hash=stored.input_hash,
        profile_hash=stored.profile_hash, adapter_hash=stored.adapter_hash, rule_hash=stored.rule_hash,
        status="blocker", report_json={"reasons": ["later_blocker"]},
    ))
    db_session.commit()
    current = client.get(checks_path, headers=headers).json()
    latest = next(item for item in current["items"] if item["check_kind"] == "variant_schema")
    assert latest["status"] == "blocker"
    assert latest["report"]["reasons"] == ["later_blocker"]
    assert latest["id"] != old["id"]
    assert current["ready"] is False
