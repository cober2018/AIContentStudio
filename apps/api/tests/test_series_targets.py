"""Persona editorial series, distribution targets and per-account v5 delivery (v2 Batch A)."""



from app.models import (
    ContentUnit,
    DeliveryTarget,
    FactPack,
    FactPackItem,
    User,
)
from app.seed import seed_v1_channel_profiles

HEADERS = {"X-Studio-User": "series-ops@studio.local"}


def _admin(db):
    user = db.query(User).filter_by(email=HEADERS["X-Studio-User"]).one()
    user.role = "admin"
    db.commit()


def _platform_account(client, db, persona_id: int, name: str, channel: str, handle: str) -> dict:
    _admin(db)
    created = client.post(f"/api/v1/content-personas/{persona_id}/channel-accounts", json={
        "name": name, "platform_channel": channel, "platform_account_id": handle,
    }, headers=HEADERS)
    assert created.status_code == 201, created.text
    return created.json()


def _editorial_series(client, persona_id: int, name="技术拆解") -> dict:
    created = client.post(f"/api/v1/content-personas/{persona_id}/series", json={"name": name}, headers=HEADERS)
    assert created.status_code == 201, created.text
    return created.json()


def test_editorial_series_needs_no_account_and_units_can_use_it(client, db_session):
    persona = client.post("/api/v1/content-personas", json={"name": "作者"}, headers=HEADERS).json()
    series = _editorial_series(client, persona["id"])
    assert series["scope"] == "persona_editorial" and series["account_id"] is None and series["persona_id"] == persona["id"]
    assert client.get(f"/api/v1/content-personas/{persona['id']}/series", headers=HEADERS).json()[0]["id"] == series["id"]
    effective = client.get(
        f"/api/v1/content-identities/effective?persona_id={persona['id']}&series_id={series['id']}", headers=HEADERS)
    assert effective.status_code == 200, effective.text
    assert effective.json()["series_id"] == series["id"] and effective.json()["account_id"] is None
    project = client.post("/api/v1/content-projects", json={"title": "栏目项目"}, headers=HEADERS).json()
    unit = client.post(f"/api/v1/content-projects/{project['id']}/units", json={
        "title": "栏目稿件", "persona_id": persona["id"], "series_id": series["id"], "modality": "text",
    }, headers=HEADERS)
    assert unit.status_code == 201, unit.text
    assert unit.json()["series_id"] == series["id"] and unit.json()["account_id"] is None
    snapshot = db_session.get(type(db_session.get(ContentUnit, unit.json()["id"])), unit.json()["id"])
    assert snapshot.identity_snapshot_id is not None
    # 同名栏目不自动合并：再建一个同名 editorial 也是独立行。
    second = _editorial_series(client, persona["id"])
    assert second["id"] != series["id"]


def test_legacy_series_keeps_account_scoped_rules(client):
    persona = client.post("/api/v1/content-personas", json={"name": "旧作者"}, headers=HEADERS).json()
    account = client.post(f"/api/v1/content-personas/{persona['id']}/accounts", json={"name": "旧账号"}, headers=HEADERS).json()
    legacy = client.post(f"/api/v1/content-accounts/{account['id']}/series", json={"name": "旧栏目"}, headers=HEADERS)
    assert legacy.status_code == 201, legacy.text
    assert legacy.json()["scope"] == "account_legacy" and legacy.json()["account_id"] == account["id"]
    no_account = client.get(
        f"/api/v1/content-identities/effective?persona_id={persona['id']}&series_id={legacy.json()['id']}", headers=HEADERS)
    assert no_account.status_code == 422
    # editorial 投放绑定不适用于 legacy 栏目。
    blocked = client.post(f"/api/v1/content-series/{legacy.json()['id']}/targets",
                          json={"account_id": account["id"], "content_form": "article"}, headers=HEADERS)
    assert blocked.status_code == 422 and "series_scope_unsupported" in blocked.text


def test_series_targets_binding_contracts(client, db_session):
    persona = client.post("/api/v1/content-personas", json={"name": "绑定作者"}, headers=HEADERS).json()
    series = _editorial_series(client, persona["id"])
    red_a = _platform_account(client, db_session, persona["id"], "小红书A", "xiaohongshu", "handleA")
    red_b = _platform_account(client, db_session, persona["id"], "小红书B", "xiaohongshu", "handleB")

    first = client.post(f"/api/v1/content-series/{series['id']}/targets",
                        json={"account_id": red_a["id"], "content_form": "image_note"}, headers=HEADERS)
    assert first.status_code == 201, first.text
    assert first.json()["enabled"] is True and first.json()["version"] == 1
    # 同平台第二个账号是独立绑定行，不会被 platform_channel 折叠。
    second = client.post(f"/api/v1/content-series/{series['id']}/targets",
                         json={"account_id": red_b["id"], "content_form": "image_note"}, headers=HEADERS)
    assert second.status_code == 201, second.text
    assert first.json()["id"] != second.json()["id"]
    duplicate = client.post(f"/api/v1/content-series/{series['id']}/targets",
                            json={"account_id": red_a["id"], "content_form": "image_note"}, headers=HEADERS)
    assert duplicate.status_code == 409

    other_persona = client.post("/api/v1/content-personas", json={"name": "别人"}, headers=HEADERS).json()
    foreign = client.post(f"/api/v1/content-personas/{other_persona['id']}/accounts", json={"name": "外号"}, headers=HEADERS).json()
    cross = client.post(f"/api/v1/content-series/{series['id']}/targets",
                        json={"account_id": foreign["id"], "content_form": "image_note"}, headers=HEADERS)
    assert cross.status_code == 422 and "series_target_persona_mismatch" in cross.text

    unbound = client.post(f"/api/v1/content-personas/{persona['id']}/accounts", json={"name": "无平台"}, headers=HEADERS).json()
    missing = client.post(f"/api/v1/content-series/{series['id']}/targets",
                          json={"account_id": unbound["id"], "content_form": "image_note"}, headers=HEADERS)
    assert missing.status_code == 422 and "series_target_account_unbound" in missing.text

    bad_form = client.post(f"/api/v1/content-series/{series['id']}/targets",
                           json={"account_id": red_a["id"], "content_form": "long_video"}, headers=HEADERS)
    assert bad_form.status_code == 422

    listing = client.get(f"/api/v1/content-series/{series['id']}/targets", headers=HEADERS)
    assert {row["account_id"] for row in listing.json()} == {red_a["id"], red_b["id"]}

    stale = client.patch(f"/api/v1/content-series/{series['id']}/targets/{first.json()['id']}",
                         json={"enabled": False, "expected_version": 99}, headers=HEADERS)
    assert stale.status_code == 409
    disable = client.patch(f"/api/v1/content-series/{series['id']}/targets/{first.json()['id']}",
                           json={"enabled": False, "expected_version": 1}, headers=HEADERS)
    assert disable.status_code == 200 and disable.json()["enabled"] is False and disable.json()["version"] == 2
    assert client.delete(f"/api/v1/content-series/{series['id']}/targets/{second.json()['id']}", headers=HEADERS).status_code == 204
    assert client.get(f"/api/v1/content-series/{series['id']}/targets", headers=HEADERS).json() == [disable.json()]


def _approval_payload(candidate):
    warnings = candidate["manifest"]["source_master"].get("warning_checks", [])
    return {"candidate_hash": candidate["candidate_hash"],
            "warning_dispositions": {f"{row['id']}:{row['input_hash']}": "编辑已核对该提示"
                                     for row in warnings}}


def _ready_source(client, db, *, persona_id: int, account_id=None, series_id=None):
    seed_v1_channel_profiles(db)
    db.commit()
    persona = persona_id
    project = client.post("/api/v1/content-projects", json={"title": "多账号交付"}, headers=HEADERS).json()["id"]
    unit_response = client.post(f"/api/v1/content-projects/{project}/units", json={
        "title": "源稿", "persona_id": persona, "modality": "text", "channel_id": "x",
        "account_id": account_id, "series_id": series_id,
    }, headers=HEADERS)
    assert unit_response.status_code == 201, unit_response.text
    unit = unit_response.json()["id"]
    assert client.post(f"/api/v1/content-projects/{project}/brief/revisions", json={
        "objective": "准确表达观点", "expected_revision": 0}, headers=HEADERS).status_code == 201
    pack = FactPack(name="多账号事实", version=1, status="frozen", checksum="c" * 64)
    db.add(pack)
    db.flush()
    db.add(FactPackItem(fact_pack_id=pack.id, evidence_kind="author_opinion",
                        snapshot_json={"statement": "这是观点"}, snapshot_checksum="d" * 64,
                        public_use_allowed=True, model_use_allowed=True))
    db.commit()
    assert client.post(f"/api/v1/content-projects/{project}/fact-boundary", json={
        "fact_pack_id": pack.id, "expected_revision": 0}, headers=HEADERS).status_code == 201
    master_path = f"/api/v1/content-projects/{project}/units/{unit}/master-revisions"
    master = client.post(master_path, json={
        "idempotency_key": "series-target-source", "payload_schema": "text.master.v2", "content_form": "single",
        "payload": {"title": "有来源的观点", "document": {"schema": "studio.text.document.v1", "blocks": [
            {"id": "b1", "type": "paragraph", "content": [{"text": "这是观点", "marks": []}]}], "citations": []}},
    }, headers=HEADERS)
    assert master.status_code == 200, master.text
    assert client.post(f"{master_path}/{master.json()['id']}/checks", headers=HEADERS).status_code == 200
    return project, unit, master.json()


def _ready_variant_candidate(client, project, unit, master):
    path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    saved = client.post(path, json={
        "variant_key": "x.single.primary", "expected_revision": 0,
        "source_master_revision_id": master["id"],
        "expected_source_payload_hash": master["payload_hash"], "expected_source_context_hash": master["context_hash"],
        "channel_id": "x", "content_form": "single", "idempotency_key": "x.single.primary",
        "source_kind": "deterministic_adapt", "payload": {"text": "这是观点"},
    }, headers=HEADERS)
    assert saved.status_code == 201, saved.text
    checks = client.post(f"{path}/{saved.json()['id']}/checks", headers=HEADERS)
    assert checks.status_code == 200 and checks.json()["ready"] is True, checks.text
    frozen = client.post(f"/api/v1/content-projects/{project}/units/{unit}/candidates/freeze", json={
        "channel_variant_revision_id": saved.json()["id"], "expected_payload_hash": saved.json()["payload_hash"]}, headers=HEADERS)
    assert frozen.status_code == 201, frozen.text
    candidate = frozen.json()
    approved = client.post(
        f"/api/v1/content-projects/{project}/units/{unit}/candidates/{candidate['id']}/approve",
        json=_approval_payload(candidate), headers=HEADERS)
    assert approved.status_code == 200, approved.text
    return candidate


def _authorize(client, project, unit, candidate, **extra):
    return client.post(
        f"/api/v1/content-projects/{project}/units/{unit}/candidates/{candidate['id']}/delivery-authorizations",
        json={"channel": "x", "content_form": "single", "account_ref": "manual-x",
              "authorization_version": "v1", "action": "copy_package", **extra}, headers=HEADERS)


def test_v5_delivery_unlocks_cross_platform_and_same_platform_targets(client, db_session):
    seed_v1_channel_profiles(db_session)
    db_session.commit()
    persona = client.post("/api/v1/content-personas", json={"name": "解锁作者"}, headers=HEADERS).json()
    account_a = _platform_account(client, db_session, persona["id"], "X主号", "x", "mainx")
    account_b = _platform_account(client, db_session, persona["id"], "X小号", "x", "altx")
    project, unit, master = _ready_source(client, db_session, persona_id=persona["id"], account_id=account_a["id"])
    candidate = _ready_variant_candidate(client, project, unit, master)

    # 同平台 B 账号：origin 账号 A 不再是目标锁，B 拿到独立授权。
    target_b = _authorize(client, project, unit, candidate, content_account_id=account_b["id"])
    assert target_b.status_code == 201, target_b.text
    # origin 账号 A 本身也仍然可以授权。
    target_a = _authorize(client, project, unit, candidate, content_account_id=account_a["id"])
    assert target_a.status_code == 201, target_a.text
    assert target_a.json()["id"] != target_b.json()["id"]
    row_b = db_session.get(DeliveryTarget, target_b.json()["id"])
    frozen_account = row_b.capability_snapshot_json["target_account"]
    assert frozen_account["content_account_id"] == account_b["id"]
    assert frozen_account["platform_channel"] == "x"
    assert frozen_account["account_revision_id"] is None  # 无 profile 修订时显式为空，不伪造

    # 跨 Persona 的账号 fail-closed，即使同平台。
    other = client.post("/api/v1/content-personas", json={"name": "别人号"}, headers=HEADERS).json()
    foreign = _platform_account(client, db_session, other["id"], "外平台", "x", "foreignx")
    rejected = _authorize(client, project, unit, candidate, content_account_id=foreign["id"])
    assert rejected.status_code == 404

    # 账号平台必须与目标渠道一致。
    wechat_only = _platform_account(client, db_session, persona["id"], "仅微信", "wechat", "wx0123456789abcdef")
    mismatch = _authorize(client, project, unit, candidate, content_account_id=wechat_only["id"])
    assert mismatch.status_code == 422 and "平台与目标渠道不一致" in mismatch.text


def test_disabled_series_target_blocks_new_authorization(client, db_session):
    seed_v1_channel_profiles(db_session)
    db_session.commit()
    persona = client.post("/api/v1/content-personas", json={"name": "停用作者"}, headers=HEADERS).json()
    account = _platform_account(client, db_session, persona["id"], "X停用", "x", "pausx")
    series = _editorial_series(client, persona["id"], "停用栏目")
    bound = client.post(f"/api/v1/content-series/{series['id']}/targets",
                        json={"account_id": account["id"], "content_form": "single"}, headers=HEADERS)
    assert bound.status_code == 201, bound.text
    project, unit, master = _ready_source(client, db_session, persona_id=persona["id"], account_id=account["id"], series_id=series["id"])
    candidate = _ready_variant_candidate(client, project, unit, master)

    disabled = client.patch(f"/api/v1/content-series/{series['id']}/targets/{bound.json()['id']}",
                            json={"enabled": False, "expected_version": 1}, headers=HEADERS)
    assert disabled.status_code == 200
    blocked = _authorize(client, project, unit, candidate, content_account_id=account["id"])
    assert blocked.status_code == 409 and "series_target_disabled" in blocked.text

    reenabled = client.patch(f"/api/v1/content-series/{series['id']}/targets/{bound.json()['id']}",
                             json={"enabled": True, "expected_version": 2}, headers=HEADERS)
    assert reenabled.status_code == 200
    allowed = _authorize(client, project, unit, candidate, content_account_id=account["id"])
    assert allowed.status_code == 201, allowed.text


def test_missing_editorial_series_is_rejected_without_default_fallback(client):
    persona = client.post('/api/v1/content-personas', json={'name': '缺失栏目回归'}, headers=HEADERS).json()
    effective = client.get(f"/api/v1/content-identities/effective?persona_id={persona['id']}&series_id=999999", headers=HEADERS)
    assert effective.status_code == 404, effective.text
    project = client.post('/api/v1/content-projects', json={'title': '不存在的栏目'}, headers=HEADERS).json()
    response = client.post(f"/api/v1/content-projects/{project['id']}/units", json={
        'title': '不应创建', 'persona_id': persona['id'], 'series_id': 999999, 'modality': 'text'}, headers=HEADERS)
    assert response.status_code == 404, response.text
    assert client.get(f"/api/v1/content-projects/{project['id']}/units", headers=HEADERS).json() == []
