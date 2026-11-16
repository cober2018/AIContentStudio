"""CT-002: model-confirmed receipts are told apart from human ones, and identity stays owner-scoped."""

from sqlalchemy import select
from test_f6a_modality_adapters import HEADERS
from test_f6a_v4_delivery_closure import _approve, _authorize, _candidate

from app.models import PublishedContentRecord, User
from app.services import browser_publish


def _authorized_target(client, db_session, tmp_path):
    _, base, _, candidate, _ = _candidate(client, db_session, tmp_path)
    assert _approve(client, base, candidate).status_code == 200
    authorized = _authorize(client, base)
    assert authorized.status_code == 201, authorized.text
    return authorized.json()["id"]


def _record(db_session, target_id):
    return db_session.scalar(select(PublishedContentRecord).where(PublishedContentRecord.delivery_target_id == target_id))


def _history(client):
    response = client.get("/api/v1/published-content", headers=HEADERS)
    assert response.status_code == 200, response.text
    return response.json()


def test_model_publish_without_link_is_pending_until_link_added(client, db_session, tmp_path):
    target_id = _authorized_target(client, db_session, tmp_path)
    screenshot = tmp_path / "published.png"
    screenshot.write_bytes(b"png")
    user = db_session.scalar(select(User).where(User.email == HEADERS["X-Studio-User"]))

    browser_publish.record_published(db_session, user, target_id, str(screenshot), "", "", "test-model")
    record = _record(db_session, target_id)
    assert record is not None
    listed = _history(client)
    item = next(row for row in listed["items"] if row["id"] == record.id)
    assert (item["confirmed_by"], item["publication_verified"], item["pending_link"]) == ("model", False, True)
    assert (listed["verified_total"], listed["pending_link_total"]) == (0, 1)
    receipts = client.get(f"/api/v1/delivery-targets/{target_id}", headers=HEADERS).json()["receipts"]
    assert receipts[-1]["verification_method"] == "third_party_model_browser"

    browser_publish.record_link(db_session, user, target_id, "https://www.douyin.com/video/1")
    listed = _history(client)
    item = next(row for row in listed["items"] if row["id"] == record.id)
    assert (item["confirmed_by"], item["publication_verified"], item["pending_link"]) == ("model", True, False)
    assert (listed["verified_total"], listed["pending_link_total"]) == (1, 0)


def test_human_receipt_counts_as_verified_even_without_platform_url(client, db_session, tmp_path):
    target_id = _authorized_target(client, db_session, tmp_path)
    saved = client.post(f"/api/v1/delivery-targets/{target_id}/receipt", headers=HEADERS,
                        json={"status": "human_confirmed", "evidence_ref": "后台截图已存档"})
    assert saved.status_code == 200, saved.text
    record = _record(db_session, target_id)
    assert record is not None
    item = next(row for row in _history(client)["items"] if row["id"] == record.id)
    assert (item["confirmed_by"], item["publication_verified"], item["pending_link"]) == ("human", True, False)


def test_external_import_has_no_verification_verdict(client, db_session):
    imported = client.post("/api/v1/published-content/import", headers=HEADERS, json={"records": [{
        "external_key": "old-1", "channel": "douyin", "content_form": "video", "title": "旧作品",
        "canonical_url": "https://www.douyin.com/video/9", "content_snapshot": {}}]})
    assert imported.status_code == 201, imported.text
    listed = _history(client)
    assert (listed["items"][0]["confirmed_by"], listed["items"][0]["publication_verified"]) == (None, None)
    assert (listed["verified_total"], listed["pending_link_total"]) == (0, 0)


def test_brand_tone_rules_stay_out_of_persona_expression_style(client, db_session):
    headers = {"X-Studio-User": "tone@studio.test"}
    brand = client.post("/api/v1/content-brands", headers=headers, json={"name": "品牌"}).json()
    persona = client.post(f"/api/v1/content-brands/{brand['id']}/personas", headers=headers, json={"name": "角色"}).json()
    brand_rules = ["品牌口吻：克制"]
    persona_style = {"tone": "口语、短句"}
    for root, entity_id, profile in (("content-brands", brand["id"], {"tone_rules": brand_rules}),
                                     ("content-personas", persona["id"], {"expression_style": persona_style})):
        saved = client.post(f"/api/v1/{root}/{entity_id}/revisions", headers=headers,
                            json={"expected_revision": 0, "profile": profile})
        assert saved.status_code == 201, saved.text
    effective = client.get(f"/api/v1/content-identities/effective?persona_id={persona['id']}", headers=headers).json()
    profile = effective["effective_profile"]
    assert profile["expression_style"] == persona_style
    assert profile["brand"]["tone_rules"] == brand_rules
    assert "tone_rules" not in profile
    assert effective["field_origins"]["expression_style"] == "persona"


def test_other_user_cannot_reach_brand_account_or_published_records(client, db_session, tmp_path):
    owner = {"X-Studio-User": "owner@studio.test"}
    other = {"X-Studio-User": "intruder@studio.test"}
    brand = client.post("/api/v1/content-brands", headers=owner, json={"name": "品牌"}).json()
    persona = client.post(f"/api/v1/content-brands/{brand['id']}/personas", headers=owner, json={"name": "角色"}).json()
    db_session.scalar(select(User).where(User.email == owner["X-Studio-User"])).role = "admin"
    db_session.commit()
    account = client.post(f"/api/v1/content-personas/{persona['id']}/channel-accounts", headers=owner,
                          json={"name": "账号", "platform_channel": "wechat", "platform_account_id": "wx0123456789abcdef"}).json()
    target_id = _authorized_target(client, db_session, tmp_path)
    assert client.post(f"/api/v1/delivery-targets/{target_id}/receipt", headers=HEADERS,
                       json={"status": "human_confirmed", "evidence_ref": "https://mp.weixin.qq.com/s/x"}).status_code == 200
    record = _record(db_session, target_id)

    assert client.get(f"/api/v1/content-brands/{brand['id']}", headers=other).status_code == 404
    assert client.get(f"/api/v1/content-accounts/{account['id']}", headers=other).status_code == 404
    assert client.get(f"/api/v1/content-identities/effective?persona_id={persona['id']}", headers=other).status_code == 404
    assert client.get(f"/api/v1/published-content?content_account_id={account['id']}", headers=other).status_code == 404
    assert client.get(f"/api/v1/published-content/{record.id}", headers=other).status_code == 404
    listed = client.get("/api/v1/published-content", headers=other).json()
    assert (listed["total"], listed["verified_total"], listed["pending_link_total"]) == (0, 0, 0)
