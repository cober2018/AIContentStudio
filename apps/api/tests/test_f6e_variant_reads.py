"""F6E Variant reads remain inside the exact project/unit owner boundary."""

from app.models import ChannelTemplateVersion, ChannelVariantRevision, ContentMasterRevision


def _unit(client, email: str):
    headers = {"X-Studio-User": email}
    persona = client.post("/api/v1/content-personas", json={"name": f"{email} 身份"}, headers=headers).json()["id"]
    project = client.post("/api/v1/content-projects", json={"title": f"{email} 项目"}, headers=headers).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project}/units", json={"title": "内容", "persona_id": persona, "modality": "text"}, headers=headers).json()["id"]
    return project, unit, headers


def test_variant_history_and_current_are_project_scoped(client, db_session):
    project, unit, headers = _unit(client, "variant-owner@studio.local")
    foreign_project, foreign_unit, foreign_headers = _unit(client, "variant-foreign@studio.local")
    master = ContentMasterRevision(
        project_id=project, content_unit_id=unit, revision_no=1, modality="text", payload_schema="text.master.v2",
        payload_json={"title": "原稿"}, payload_hash="a" * 64, context_hash="b" * 64, source_kind="user_edit",
        edit_summary_json={}, idempotency_key="master-1", request_fingerprint="c" * 64,
    )
    db_session.add(master)
    profile = ChannelTemplateVersion(channel="wechat", version=100, name="公众号", status="published", profile_json={"content_forms": {"article": {"artifact_kind": "text"}}})
    db_session.add(profile)
    db_session.flush()
    variant = ChannelVariantRevision(
        project_id=project, content_unit_id=unit, variant_key="wechat.article.primary", revision_no=1,
        source_master_revision_id=master.id, source_master_payload_hash=master.payload_hash, source_master_context_hash=master.context_hash,
        channel_id="wechat", content_form="article", artifact_kind="text", profile_template_version_id=profile.id,
        profile_key="wechat/article", profile_version="100", profile_hash="d" * 64, adapter_key="wechat.article",
        adapter_version="1", rule_hash="e" * 64, payload_schema="wechat.article.v1", payload_json={"title": "适配稿"},
        payload_hash="f" * 64, context_hash="1" * 64, source_kind="manual_edit", edit_summary_json={},
        idempotency_key="variant-1", request_fingerprint="2" * 64,
    )
    db_session.add(variant)
    db_session.commit()

    base = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    response = client.get(base, headers=headers)
    assert response.status_code == 200, response.text
    assert [item["id"] for item in response.json()["items"]] == [variant.id]
    current = client.get(f"{base}/current", params={"variant_key": variant.variant_key}, headers=headers)
    assert current.status_code == 200
    assert current.json()["id"] == variant.id
    assert client.get(f"{base}/{variant.id}", headers=headers).json()["payload_hash"] == variant.payload_hash

    for path in (base, f"{base}/current?variant_key={variant.variant_key}", f"{base}/{variant.id}"):
        assert client.get(path, headers=foreign_headers).status_code == 404
    assert client.get(f"/api/v1/content-projects/{foreign_project}/units/{foreign_unit}/channel-variants/{variant.id}", headers=foreign_headers).status_code == 404
