"""Official Delivery uses real local lineage and isolated transport only."""

import hashlib
import json
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from test_f6e_freeze_v5 import HEADERS, _approval_payload, _ready_source

from app.models import (
    CapabilityRegistration,
    ContentAccount,
    ContentAsset,
    ContentPersona,
    ContentUnit,
    DeliveryAttempt,
    DeliveryReceipt,
    DeliveryTarget,
    Material,
    MaterialRevision,
    ProjectEvent,
    ProjectMaterialReference,
    PublishedContentRecord,
    SystemSetting,
    User,
)
from app.services import capability_integrations, wechat_official


@pytest.fixture
def ready(client, db_session, tmp_path, monkeypatch, request):
    project, unit, master = _ready_source(client, db_session, neutral=True,
        fact_pack_name=getattr(request, "fact_pack_name", "真实事实边界"))
    owner = db_session.scalar(select(User).where(User.email == HEADERS["X-Studio-User"]))
    account_identity = getattr(request, "platform_account_id", "wx" + "a" * 16)
    account = ContentAccount(persona_id=db_session.get(ContentUnit, unit).persona_id, name="公众号A",
                             platform_channel="wechat", platform_account_id=account_identity)
    db_session.add(account)
    db_session.flush()
    ref = f"AICS_WECHAT_ACCOUNT_{account.id}_APPSECRET"
    monkeypatch.setenv(ref, "a" * 32)
    monkeypatch.setenv(ref + "_VERSION", "v1")
    monkeypatch.setenv("AICS_WECHAT_RUNTIME_IDENTITY_KEY", "k" * 32)
    db_session.add(SystemSetting(key=f"wechat.official.account.{account.id}", value={
        "revision": 1, "enabled": True, "credential_ref": ref, "credential_version": "v1",
        "platform_account_id": account.platform_account_id}))
    data = b"\x89PNG\r\n\x1a\nexact-approved-bytes"
    path = tmp_path / "cover.png"
    path.write_bytes(data)
    material = Material(title="cover", kind="image", status="active")
    db_session.add(material)
    db_session.flush()
    revision = MaterialRevision(material_id=material.id, content_hash=hashlib.sha256(data).hexdigest(),
        file_path=str(path), mime_type="image/png", status="active", public_use_allowed=True, rights_status="cleared",
        metadata_json={"filename": "原始封面.png"})
    db_session.add(revision)
    db_session.flush()
    db_session.add(ProjectMaterialReference(project_id=project, material_revision_id=revision.id, origin="system_library", status="active"))
    blocks = [{"id": "b1", "order": 0, "kind": "paragraph", "text": "这是观点"}]
    asset_refs = [{"material_revision_id": revision.id, "content_hash_snapshot": revision.content_hash,
                   "role": "cover", "slot_key": "cover", "sort_order": 0, "placement": {"usage": "cover"}}]
    inline = None
    inline_data = b"\x89PNG\r\n\x1a\nexact-inline-approved-bytes"
    if getattr(request, "param", None) == "inline":
        inline_path = tmp_path / "inline.png"
        inline_path.write_bytes(inline_data)
        inline_material = Material(title="inline", kind="image", status="active")
        db_session.add(inline_material)
        db_session.flush()
        inline = MaterialRevision(material_id=inline_material.id, content_hash=hashlib.sha256(inline_data).hexdigest(),
            file_path=str(inline_path), mime_type="image/png", status="active", public_use_allowed=True, rights_status="cleared",
            metadata_json={"filename": "原始正文图.png"})
        db_session.add(inline)
        db_session.flush()
        db_session.add(ProjectMaterialReference(project_id=project, material_revision_id=inline.id, origin="system_library", status="active"))
        blocks.append({"id": "img1", "order": 1, "kind": "image", "image_ref_key": "img1", "text": "批准的图注", "alt_text": "批准的图片"})
        asset_refs.append({"material_revision_id": inline.id, "content_hash_snapshot": inline.content_hash,
            "role": "inline_image", "slot_key": "img1", "sort_order": 1, "placement": {"usage": "inline", "block_id": "img1"}})
    db_session.commit()
    variants = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    if inline:
        master_path = f"/api/v1/content-projects/{project}/units/{unit}/master-revisions"
        payload = {**master["payload"], "document": {**master["payload"]["document"], "blocks": [
            *master["payload"]["document"]["blocks"], {"id": "img1", "type": "image",
                "material_revision_id": inline.id, "caption": "批准的图注", "alt_text": "批准的图片"}]}}
        source = client.post(master_path, json={"expected_revision": 1, "parent_revision_id": master["id"],
            "idempotency_key": "delivery-inline-source", "payload_schema": "text.master.v2", "payload": payload,
            "asset_refs": [{"material_revision_id": ref.id, "content_hash": ref.content_hash,
                "role": "cover" if index == 0 else "inline", "slot_key": "cover" if index == 0 else "img1",
                "sort_order": index, "placement": {"usage": "cover"} if index == 0 else {"block_id": "img1"}}
                for index, ref in enumerate([revision, inline])]}, headers=HEADERS)
        assert source.status_code == 200, source.text
        master = source.json()
        assert client.post(f"{master_path}/{master['id']}/checks", headers=HEADERS).status_code == 200
        preview = client.post(f"{variants}/adapt-preview", json={"source_master_revision_id": master["id"],
            "expected_source_payload_hash": master["payload_hash"], "expected_source_context_hash": master["context_hash"],
            "channel_id": "wechat", "content_form": "article"}, headers=HEADERS)
        assert preview.status_code == 200, preview.text
        blocks, asset_refs = preview.json()["payload"]["blocks"], preview.json()["asset_refs"]
    variant = client.post(variants, json={"variant_key": "wechat.article.primary", "expected_revision": 0,
        "source_master_revision_id": master["id"], "expected_source_payload_hash": master["payload_hash"],
        "expected_source_context_hash": master["context_hash"], "channel_id": "wechat", "content_form": "article",
        "idempotency_key": "official-delivery", "source_kind": "deterministic_adapt",
        "payload": {"title": "有来源的观点", "blocks": blocks}, "asset_refs": asset_refs}, headers=HEADERS)
    assert variant.status_code == 201, variant.text
    checks = client.post(f"{variants}/{variant.json()['id']}/checks", headers=HEADERS).json()
    assert checks["ready"], json.dumps(checks, ensure_ascii=False)
    candidates = f"/api/v1/content-projects/{project}/units/{unit}/candidates"
    frozen = client.post(f"{candidates}/freeze", json={"channel_variant_revision_id": variant.json()["id"],
        "expected_payload_hash": variant.json()["payload_hash"]}, headers=HEADERS)
    assert frozen.status_code == 201, frozen.text
    candidate = frozen.json()
    assert client.post(f"{candidates}/{candidate['id']}/approve", json=_approval_payload(candidate), headers=HEADERS).status_code == 200
    short_experiment = getattr(request, "param", None) == "short"
    if short_experiment:
        owner.role = "admin"
    if not short_experiment:
        monkeypatch.setattr(wechat_official, "remote_contract_ready", lambda: True)
    registration = db_session.scalar(select(CapabilityRegistration).where(
        CapabilityRegistration.kind == "publisher", CapabilityRegistration.key == wechat_official.KEY,
        CapabilityRegistration.version == "1"))
    if registration is None:
        registration = CapabilityRegistration(kind="publisher", key=wechat_official.KEY, version="1", status="configured",
                                               config_fingerprint=wechat_official.implementation_fingerprint())
        db_session.add(registration)
    db_session.flush()
    scope = {"channel": "wechat", "content_form": "article", "action": "auto_draft", "content_account_id": account.id,
        "account_ref": account.platform_account_id, "publisher_key": wechat_official.KEY, "publisher_version": "1"}
    if not short_experiment:
        capability_integrations.append_verification(db_session, registration, scope_kind="publisher_action", scope=scope,
            result="verified", actor=owner.email, evidence={"kind": "human_readback", "reference_hash": "e" * 64})
    db_session.commit()
    auth_url = f"{candidates}/{candidate['id']}/delivery-authorizations"
    auth = {"channel": "wechat", "content_form": "article", "action": "auto_draft", "content_account_id": account.id,
            "account_ref": account.platform_account_id, "authorization_version": "v1"}
    return {"auth_url": auth_url, "auth": auth, "account": account, "owner": owner, "revision": revision,
            "candidate": candidate, "data": data, "inline": inline, "inline_data": inline_data,
            "registration": registration, "scope": scope, "short_experiment": short_experiment}


@pytest.fixture
def wire(monkeypatch, db_session, ready):
    from app.services import wechat_official_transport

    calls = []
    article = {}

    class Transport:
        def __init__(self, **kwargs):
            if ready["short_experiment"]:
                assert wechat_official.check_short_draft_authority(kwargs["experiment_authority"], kwargs["experiment_scope"])

        def token(self, runtime):
            attempts = db_session.scalars(select(DeliveryAttempt)).all()
            assert len(attempts) == 1 and attempts[0].status == "running"
            assert attempts[0].response_metadata_json["in_flight"] in {"token", "readback_token"}
            calls.append("token")
            return "secret-token-not-history"

        def upload_cover(self, token, content, mime, filename):
            assert token == "secret-token-not-history" and content == ready["data"] and mime == "image/png"
            assert filename == "原始封面.png"
            calls.append("cover")
            return "exact-cover-id"

        def create_draft(self, token, value):
            article.update(value)
            calls.append("create")
            return "exact-draft-id"

        def read_draft(self, token, draft_id):
            assert draft_id == "exact-draft-id"
            calls.append("read")
            return dict(article)

    monkeypatch.setattr(wechat_official_transport, "OfficialTransport", Transport)
    return calls, Transport, article


def _authorize(client, ready):
    response = client.post(ready["auth_url"], json=ready["auth"], headers=HEADERS)
    assert response.status_code == 201, response.text
    assert response.json()["publisher_key"] == wechat_official.KEY
    return response.json()["id"]


def _experiment_request(ready):
    return {"account_id": ready["account"].id, "appid": ready["account"].platform_account_id,
            "candidate_id": ready["candidate"]["id"], "candidate_hash": ready["candidate"]["candidate_hash"],
            "actor": ready["owner"].email, "expires_at": int(time.time()) + 120}


def _prepare_experiment(db, ready, authority=None):
    from app.routers.delivery import GenericTargetIn
    from app.services import wechat_official_delivery

    return wechat_official_delivery.prepare_short_draft_experiment(db,
        db.get(ContentAsset, ready["candidate"]["id"]), GenericTargetIn(**ready["auth"]), ready["owner"],
        authority=authority or _experiment_request(ready))


def _move_to_explicit_readback(db, target_id, attempt_id):
    target = db.get(DeliveryTarget, target_id)
    attempt = db.get(DeliveryAttempt, attempt_id)
    target.status = "reconciliation_needed"
    attempt.status = "unknown"
    attempt.finished_at = None
    db.commit()


@pytest.mark.parametrize("ready", ["short"], indirect=True)
@pytest.mark.parametrize("code,expected", [
    ("official_network_unavailable", "official_network_unavailable"),
    ("official_api_rejected", "official_api_rejected"),
    ("secret-token-and-provider-response", "official_error_unclassified"),
])
def test_upload_unknown_preserves_only_bounded_diagnostics(client, db_session, ready, wire, monkeypatch, code, expected):
    from app.services import wechat_official_delivery, wechat_official_transport

    def fail_upload(*args):
        wire[0].append("cover")
        raise wechat_official_transport.OfficialTransportError(code, dispatched=True)

    monkeypatch.setattr(wire[1], "upload_cover", fail_upload)
    target_id, attempt_id, claim = _prepare_experiment(db_session, ready)
    result = wechat_official_delivery.execute_prepared(db_session, target_id, attempt_id, claim, ready["owner"])
    assert result["status"] == "unknown" and result["target_status"] == "reconciliation_needed"
    attempt = db_session.get(DeliveryAttempt, attempt_id, populate_existing=True)
    metadata = attempt.response_metadata_json
    assert metadata["failure_diagnostic"] == {"code": expected, "dispatch_hint": True}
    assert metadata["completed_steps"] == ["token"] and metadata["in_flight"] == "asset_0"
    assert attempt.remote_id is None and wire[0] == ["token", "cover"]
    assert "secret-token-and-provider-response" not in json.dumps(metadata)
    with pytest.raises(HTTPException):
        wechat_official_delivery.execute_prepared(db_session, target_id, attempt_id, claim, ready["owner"])
    assert wire[0] == ["token", "cover"]


@pytest.mark.parametrize("ready", ["short"], indirect=True)
def test_short_experiment_product_claim_without_general_verification(client, db_session, ready, wire):
    from app.services import wechat_official_delivery

    denied = client.post(ready["auth_url"], json=ready["auth"], headers=HEADERS)
    assert denied.status_code == 409
    target_id, attempt_id, claim = _prepare_experiment(db_session, ready)
    target = db_session.get(DeliveryTarget, target_id)
    attempt = db_session.get(DeliveryAttempt, attempt_id)
    assert target.capability_snapshot_json["verified"] is False
    assert target.capability_snapshot_json["remote_verified"] is False
    assert attempt.status == "prepared" and wire[0] == []
    assert wechat_official.remote_contract_ready() is False
    result = wechat_official_delivery.execute_prepared(db_session, target_id, attempt_id, claim, ready["owner"])
    assert result["status"] == "succeeded" and wire[0] == ["token", "cover", "create"]
    assert db_session.scalars(select(PublishedContentRecord)).all() == []
    assert db_session.scalars(select(DeliveryReceipt)).all() == []
    denied = client.post(ready["auth_url"], json={**ready["auth"], "authorization_version": "ordinary-2"}, headers=HEADERS)
    assert denied.status_code == 409


@pytest.mark.parametrize("ready", ["short"], indirect=True)
@pytest.mark.parametrize("mutation", ["expired", "tampered", "disabled", "revoked", "rotated", "actor", "other_attempt"])
def test_short_experiment_claim_live_mismatch_zero_dispatch(client, db_session, ready, wire, monkeypatch, mutation):
    from app.services import wechat_official_delivery

    target_id, attempt_id, claim = _prepare_experiment(db_session, ready)
    target = db_session.get(DeliveryTarget, target_id)
    if mutation == "expired":
        fixed_now = target.capability_snapshot_json["short_draft_authority"]["expires_at"]
        monkeypatch.setattr(wechat_official.time, "time", lambda: fixed_now)
    elif mutation in {"tampered", "other_attempt"}:
        import copy

        snapshot = copy.deepcopy(target.capability_snapshot_json)
        proof = snapshot["short_draft_authority"]
        if mutation == "tampered":
            proof["signature"] = "0" * 64
        else:
            proof["scope"]["attempt_id"] += 1
        target.capability_snapshot_json = snapshot
    elif mutation == "disabled":
        ready["registration"].status = "disabled"
    elif mutation == "revoked":
        capability_integrations.append_verification(db_session, ready["registration"],
            scope_kind="publisher_action", scope=ready["scope"], result="revoked", actor=ready["owner"].email,
            evidence={"kind": "revocation", "reason_code": "operator_revoked"})
    elif mutation == "rotated":
        monkeypatch.setenv(f"AICS_WECHAT_ACCOUNT_{ready['account'].id}_APPSECRET_VERSION", "v2")
    else:
        target.authorized_by = "other@studio.local"
    db_session.commit()
    with pytest.raises(HTTPException):
        wechat_official_delivery.execute_prepared(db_session, target_id, attempt_id, claim, ready["owner"])
    db_session.rollback()
    assert wire[0] == []
    assert db_session.get(DeliveryAttempt, attempt_id).status == "prepared"


@pytest.mark.parametrize("ready", ["short"], indirect=True)
def test_short_experiment_unknown_has_no_second_attempt(client, db_session, ready, wire, monkeypatch):
    from app.services import wechat_official_delivery
    from app.services.wechat_official_transport import OfficialTransportError

    target_id, attempt_id, claim = _prepare_experiment(db_session, ready)
    monkeypatch.setattr(wire[1], "create_draft", lambda *args: (_ for _ in ()).throw(
        OfficialTransportError("official_response_unconfirmed", dispatched=True)))
    result = wechat_official_delivery.execute_prepared(db_session, target_id, attempt_id, claim, ready["owner"])
    assert result["status"] == "unknown" and result["remote_id"] is None
    before = list(wire[0])
    with pytest.raises(HTTPException):
        wechat_official_delivery.prepare(db_session, target_id, ready["owner"])
    db_session.rollback()
    with pytest.raises(HTTPException):
        _prepare_experiment(db_session, ready)
    db_session.rollback()
    assert wire[0] == before
    assert len(db_session.scalars(select(DeliveryAttempt)).all()) == 1


@pytest.mark.parametrize("ready", ["short"], indirect=True)
def test_short_experiment_invalid_authority_rolls_back_target_and_attempt(client, db_session, ready, wire):
    authority = {**_experiment_request(ready), "actor": "foreign@studio.local"}
    with pytest.raises(HTTPException):
        _prepare_experiment(db_session, ready, authority)
    db_session.rollback()
    assert db_session.scalars(select(DeliveryTarget)).all() == []
    assert db_session.scalars(select(DeliveryAttempt)).all() == []
    assert wire[0] == []


@pytest.mark.parametrize("ready", ["short"], indirect=True)
def test_short_experiment_explicit_known_id_readback_never_creates(client, db_session, ready, wire, monkeypatch):
    from app.services import wechat_official_delivery

    target_id, attempt_id, claim = _prepare_experiment(db_session, ready)
    assert wechat_official_delivery.execute_prepared(db_session, target_id, attempt_id, claim, ready["owner"])["status"] == "succeeded"
    _move_to_explicit_readback(db_session, target_id, attempt_id)
    result = wechat_official_delivery.readback(db_session, target_id, attempt_id, ready["owner"])
    assert result["status"] == "succeeded"
    assert wire[0] == ["token", "cover", "create", "token", "read"]


@pytest.mark.parametrize("ready", ["inline"], indirect=True)
def test_short_experiment_preupload_bound_refuses_before_target_or_token(client, db_session, ready, wire, monkeypatch):
    monkeypatch.setattr(wechat_official, "remote_contract_ready", lambda: False)
    ready["owner"].role = "admin"
    db_session.commit()
    with pytest.raises(HTTPException) as raised:
        _prepare_experiment(db_session, ready)
    assert raised.value.detail == "official_experiment_body_limit"
    db_session.rollback()
    assert wire[0] == []
    assert db_session.scalars(select(DeliveryTarget)).all() == []
    assert db_session.scalars(select(DeliveryAttempt)).all() == []


@pytest.mark.parametrize("ready", ["short"], indirect=True)
def test_short_experiment_signing_failure_is_atomic(client, db_session, ready, wire, monkeypatch):
    monkeypatch.setattr(wechat_official, "sign_short_draft_authority",
        lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("signing_failed")))
    with pytest.raises(HTTPException):
        _prepare_experiment(db_session, ready)
    db_session.rollback()
    assert db_session.scalars(select(DeliveryTarget)).all() == []
    assert db_session.scalars(select(DeliveryAttempt)).all() == []
    assert wire[0] == []


@pytest.mark.parametrize("ready", ["short"], indirect=True)
def test_short_experiment_started_worker_not_reclaimed(client, db_session, ready, wire):
    from app.services import wechat_official_delivery

    target_id, attempt_id, claim = _prepare_experiment(db_session, ready)
    attempt = db_session.get(DeliveryAttempt, attempt_id)
    attempt.response_metadata_json = {**attempt.response_metadata_json, "execution_started": True}
    db_session.commit()
    with pytest.raises(HTTPException) as raised:
        wechat_official_delivery.execute_prepared(db_session, target_id, attempt_id, claim, ready["owner"])
    assert raised.value.detail == "official_execution_claimed"
    db_session.rollback()
    assert wire[0] == [] and attempt.status == "prepared"


def test_prepared_claim_survives_rotation_without_first_dispatch(client, db_session, ready, wire, monkeypatch):
    from app.services import wechat_official_delivery

    target = _authorize(client, ready)
    attempt_id, claim = wechat_official_delivery.prepare(db_session, target, ready["owner"])
    before = dict(db_session.get(DeliveryAttempt, attempt_id).response_metadata_json)
    setting = db_session.scalar(select(SystemSetting).where(SystemSetting.key == f"wechat.official.account.{ready['account'].id}"))
    setting.value = {**setting.value, "revision": 2, "credential_version": "v2"}
    monkeypatch.setenv(setting.value["credential_ref"] + "_VERSION", "v2")
    db_session.commit()
    with pytest.raises(HTTPException) as raised:
        wechat_official_delivery._step(db_session, target, attempt_id, claim, ready["owner"], "token",
            lambda *args: wire[1]().token(None), lambda *args: None)
    assert raised.value.status_code == 409 and raised.value.detail == "official_publisher_unverified"
    db_session.rollback()
    attempt = db_session.get(DeliveryAttempt, attempt_id, populate_existing=True)
    assert attempt.status == "prepared" and attempt.response_metadata_json == before
    assert len(db_session.scalars(select(DeliveryAttempt)).all()) == 1 and wire[0] == []


@pytest.mark.parametrize("other_owner", [False, True])
def test_owned_candidate_cannot_authorize_other_persona_account(client, db_session, ready, wire, other_owner):
    owner = ready["owner"]
    if other_owner:
        owner = User(email="foreign-account@studio.local", name="其他用户", role="admin")
        db_session.add(owner)
        db_session.flush()
    persona = ContentPersona(owner_user_id=owner.id, name="其他角色")
    db_session.add(persona)
    db_session.flush()
    account = ContentAccount(persona_id=persona.id, name="其他角色账号", platform_channel="wechat", platform_account_id="wx" + "b" * 16)
    db_session.add(account)
    db_session.commit()
    response = client.post(ready["auth_url"], json={**ready["auth"], "content_account_id": account.id,
        "account_ref": account.platform_account_id}, headers=HEADERS)
    assert response.status_code == 404, response.text
    from app.models import DeliveryTarget

    assert not db_session.scalars(select(DeliveryTarget)).all()
    assert not db_session.scalars(select(DeliveryAttempt)).all() and wire[0] == []


@pytest.mark.parametrize("rotate_a", [False, True])
def test_two_accounts_share_persona_not_runtime_or_delivery_history(client, db_session, ready, monkeypatch, rotate_a):
    from app.models import DeliveryTarget
    from app.services import wechat_official_transport

    account_a = ready["account"]
    account_b = ContentAccount(persona_id=account_a.persona_id, name="公众号B",
        platform_channel="wechat", platform_account_id="wx" + "b" * 16)
    db_session.add(account_b)
    db_session.flush()
    ref_b = f"AICS_WECHAT_ACCOUNT_{account_b.id}_APPSECRET"
    monkeypatch.setenv(ref_b, "b" * 32)
    monkeypatch.setenv(ref_b + "_VERSION", "v1")
    db_session.add(SystemSetting(key=f"wechat.official.account.{account_b.id}", value={
        "revision": 1, "enabled": True, "credential_ref": ref_b, "credential_version": "v1",
        "platform_account_id": account_b.platform_account_id}))
    db_session.flush()
    scope_b = {**ready["scope"], "content_account_id": account_b.id, "account_ref": account_b.platform_account_id}
    capability_integrations.append_verification(db_session, ready["registration"], scope_kind="publisher_action",
        scope=scope_b, result="verified", actor=ready["owner"].email,
        evidence={"kind": "human_readback", "reference_hash": "f" * 64})
    db_session.commit()
    target_a = _authorize(client, ready)
    response_b = client.post(ready["auth_url"], json={**ready["auth"], "content_account_id": account_b.id,
        "account_ref": account_b.platform_account_id}, headers=HEADERS)
    assert response_b.status_code == 201, response_b.text
    target_b = response_b.json()["id"]
    assert target_a != target_b
    runtimes = {row.id: wechat_official.resolve_runtime(db_session, row.id) for row in [account_a, account_b]}
    assert runtimes[account_a.id].fingerprint != runtimes[account_b.id].fingerprint
    calls, articles = [], {}

    class Transport:
        def token(self, runtime):
            assert runtime == runtimes[runtime.account_id]
            calls.append((runtime.account_id, "token"))
            return f"fixture-token-{runtime.account_id}"

        def upload_cover(self, token, data, mime, filename):
            account_id = int(token.removeprefix("fixture-token-"))
            assert data == ready["data"] and mime == "image/png"
            assert filename == "原始封面.png"
            calls.append((account_id, "cover"))
            return f"cover-{account_id}"

        def create_draft(self, token, article):
            account_id = int(token.removeprefix("fixture-token-"))
            assert article["thumb_media_id"] == f"cover-{account_id}"
            articles[account_id] = dict(article)
            calls.append((account_id, "create"))
            return f"draft-{account_id}"

        def read_draft(self, token, draft_id):
            account_id = int(token.removeprefix("fixture-token-"))
            assert draft_id == f"draft-{account_id}"
            calls.append((account_id, "read"))
            return articles[account_id]

    monkeypatch.setattr(wechat_official_transport, "OfficialTransport", Transport)
    if rotate_a:
        monkeypatch.setenv(f"AICS_WECHAT_ACCOUNT_{account_a.id}_APPSECRET", "c" * 32)
        denied = client.post(f"/api/v1/delivery-targets/{target_a}/execute", headers=HEADERS)
        assert denied.status_code == 409, denied.text
        assert not db_session.scalars(select(DeliveryAttempt)).all() and calls == []
    for account_id, target in [(account_b.id, target_b)] + ([] if rotate_a else [(account_a.id, target_a)]):
        result = client.post(f"/api/v1/delivery-targets/{target}/execute", headers=HEADERS)
        assert result.status_code == 200 and result.json()["status"] == "succeeded", result.text
        attempt = db_session.scalar(select(DeliveryAttempt).where(DeliveryAttempt.target_id == target))
        mapping = attempt.response_metadata_json["resource_mapping"]
        assert mapping[0]["account_id"] == account_id and mapping[0]["appid"] == runtimes[account_id].appid
        assert attempt.remote_id == f"draft-{account_id}"
        assert not db_session.scalars(select(PublishedContentRecord)).all()
        receipt = client.post(f"/api/v1/delivery-targets/{target}/receipt", json={"status": "human_confirmed",
            "evidence_ref": f"fixture-draft:{account_id}"}, headers=HEADERS)
        assert receipt.status_code == 200, receipt.text
        assert db_session.get(DeliveryTarget, target, populate_existing=True).content_account_id == account_id
        saved = db_session.scalar(select(DeliveryReceipt).where(DeliveryReceipt.target_id == target))
        assert saved.approved_candidate_hash == ready["candidate"]["candidate_hash"]
        assert not db_session.scalars(select(PublishedContentRecord)).all()
    assert [item for item in calls if item[0] == account_b.id] == [(account_b.id, step) for step in ["token", "cover", "create"]]
    if rotate_a:
        assert all(account_id != account_a.id for account_id, _ in calls)


@pytest.mark.parametrize("attempt_status", ["prepared", "running"])
@pytest.mark.parametrize("path", ["package.zip", "package", "receipt"])
def test_unresolved_official_attempt_cannot_bypass_reconciliation(client, db_session, ready, attempt_status, path):
    from app.models import DeliveryTarget
    from app.services.wechat_official_delivery import prepare

    target_id = _authorize(client, ready)
    attempt_id, _claim = prepare(db_session, target_id, ready["owner"])
    attempt = db_session.get(DeliveryAttempt, attempt_id)
    attempt.status = attempt_status
    metadata = dict(attempt.response_metadata_json)
    if attempt_status == "running":
        metadata["in_flight"] = "create"
    attempt.response_metadata_json = metadata
    expected_status = "awaiting_manual_receipt" if path == "receipt" else "target_authorized"
    db_session.get(DeliveryTarget, target_id).status = expected_status
    db_session.commit()
    claim_hash = metadata["claim_hash"]
    url = f"/api/v1/delivery-targets/{target_id}/{path}"
    result = client.post(url, json={"status": "human_confirmed", "evidence_ref": "no-reconciliation"}, headers=HEADERS) if path == "receipt" else (client.post(url, headers=HEADERS) if path == "package" else client.get(url, headers=HEADERS))
    assert result.status_code == 409, result.text
    assert db_session.get(DeliveryTarget, target_id, populate_existing=True).status == expected_status
    attempt = db_session.get(DeliveryAttempt, attempt_id, populate_existing=True)
    assert attempt.status == attempt_status and attempt.response_metadata_json["claim_hash"] == claim_hash
    assert not db_session.scalars(select(DeliveryReceipt)).all()
    assert not db_session.scalars(select(PublishedContentRecord)).all()


@pytest.mark.parametrize("ready", ["inline"], indirect=True)
@pytest.mark.parametrize("mutation", ["none", "revoke", "bytes"])
def test_inline_delivery_preserves_exact_bytes_and_fixed_slots(client, db_session, ready, wire, monkeypatch, mutation):
    from pathlib import Path

    calls, Transport, article = wire
    target = _authorize(client, ready)
    frozen = json.dumps(ready["candidate"]["manifest"], sort_keys=True)
    original_cover = Transport.upload_cover

    def cover(self, token, data, mime, filename):
        result = original_cover(self, token, data, mime, filename)
        if mutation == "revoke":
            ready["inline"].public_use_allowed = False
            db_session.commit()
        elif mutation == "bytes":
            Path(ready["inline"].file_path).write_bytes(b"changed-after-approval")
        return result

    def inline(self, token, data, mime, filename):
        assert token == "secret-token-not-history"
        assert data == ready["inline_data"] and mime == "image/png"
        assert filename == "原始正文图.png"
        calls.append("inline")
        return "https://mmbiz.qpic.cn/exact-approved-inline"

    monkeypatch.setattr(Transport, "upload_cover", cover)
    monkeypatch.setattr(Transport, "upload_inline", inline, raising=False)
    response = client.post(f"/api/v1/delivery-targets/{target}/execute", headers=HEADERS)
    assert response.status_code == 200, response.text
    attempt = db_session.scalar(select(DeliveryAttempt))
    mapping = attempt.response_metadata_json["resource_mapping"]
    assert mapping[0]["material_revision_id"] == ready["revision"].id
    if mutation == "none":
        assert response.json()["status"] == "succeeded"
        assert calls == ["token", "cover", "inline", "create"]
        assert mapping[1]["material_revision_id"] == ready["inline"].id
        assert mapping[1]["content_hash"] == hashlib.sha256(ready["inline_data"]).hexdigest()
        assert 'src="https://mmbiz.qpic.cn/exact-approved-inline"' in article["content"]
        assert "aics-resource:" not in article["content"] and "批准的图注" in article["content"]
    else:
        assert response.json()["status"] == "unknown"
        assert calls == ["token", "cover"] and len(mapping) == 1
    assert json.dumps(db_session.get(ContentAsset, ready["candidate"]["id"]).candidate_manifest_json, sort_keys=True) == frozen
    assert not db_session.scalars(select(PublishedContentRecord)).all()


def test_frozen_candidate_to_official_draft_no_publication(client, db_session, ready, wire):
    calls, _, _ = wire
    target = _authorize(client, ready)
    before = json.dumps(ready["candidate"]["manifest"], sort_keys=True)
    response = client.post(f"/api/v1/delivery-targets/{target}/execute", headers=HEADERS)
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "succeeded" and response.json()["target_status"] == "awaiting_manual_receipt"
    assert calls == ["token", "cover", "create"]
    attempt = db_session.scalar(select(DeliveryAttempt))
    assert attempt.remote_id == "exact-draft-id" and attempt.response_metadata_json["create_confirmed"]
    assert "secret-token-not-history" not in json.dumps(attempt.response_metadata_json)
    assert json.dumps(db_session.get(ContentAsset, ready["candidate"]["id"]).candidate_manifest_json, sort_keys=True) == before
    assert not db_session.scalars(select(PublishedContentRecord)).all()
    assert not db_session.scalars(select(DeliveryReceipt)).all()
    events = db_session.scalars(select(ProjectEvent).where(ProjectEvent.event_type.in_(
        ["delivery.prepared", "delivery.succeeded"]))).all()
    assert {row.event_type for row in events} == {"delivery.prepared", "delivery.succeeded"}
    assert client.post(f"/api/v1/delivery-targets/{target}/execute", headers=HEADERS).status_code == 409
    assert calls == ["token", "cover", "create"]


def test_foreign_owner_and_revoked_material_refuse_before_attempt(client, db_session, ready, wire):
    foreign = client.post(ready["auth_url"], json=ready["auth"], headers={"X-Studio-User": "other-owner@studio.local"})
    assert foreign.status_code == 404
    ready["revision"].public_use_allowed = False
    db_session.commit()
    denied = client.post(ready["auth_url"], json=ready["auth"], headers=HEADERS)
    assert denied.status_code in (409, 422)
    assert not db_session.scalars(select(DeliveryAttempt)).all() and wire[0] == []


@pytest.mark.parametrize("step", ["create"])
def test_ambiguous_result_keeps_partial_metadata_and_never_recreates(client, db_session, ready, wire, monkeypatch, step):
    calls, Transport, _ = wire
    from app.services.wechat_official_transport import OfficialTransportError

    def fail(*args):
        calls.append(step)
        raise OfficialTransportError("official_response_unconfirmed", dispatched=True)

    monkeypatch.setattr(Transport, "create_draft" if step == "create" else "read_draft", fail)
    target = _authorize(client, ready)
    result = client.post(f"/api/v1/delivery-targets/{target}/execute", headers=HEADERS)
    assert result.status_code == 200, result.text
    assert result.json()["status"] == "unknown"
    attempt = db_session.scalar(select(DeliveryAttempt))
    assert attempt.response_metadata_json["resource_mapping"][0]["remote_ref"] == "exact-cover-id"
    assert attempt.remote_id == ("exact-draft-id" if step == "read" else None)
    assert client.post(f"/api/v1/delivery-targets/{target}/execute", headers=HEADERS).status_code == 409
    assert calls.count("create") == 1


def test_rotate_after_cover_blocks_create_but_preserves_upload(client, db_session, ready, wire, monkeypatch):
    calls, Transport, _ = wire
    original = Transport.upload_cover

    def rotate(self, *args):
        result = original(self, *args)
        monkeypatch.setenv(f"AICS_WECHAT_ACCOUNT_{ready['account'].id}_APPSECRET", "b" * 32)
        return result

    monkeypatch.setattr(Transport, "upload_cover", rotate)
    target = _authorize(client, ready)
    response = client.post(f"/api/v1/delivery-targets/{target}/execute", headers=HEADERS)
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "unknown" and calls == ["token", "cover"]
    attempt = db_session.scalar(select(DeliveryAttempt))
    assert attempt.response_metadata_json["resource_mapping"][0]["remote_ref"] == "exact-cover-id"


def test_real_contract_gate_refuses_authorization_without_attempt(client, db_session, ready, wire, monkeypatch):
    monkeypatch.setattr(wechat_official, "remote_contract_ready", lambda: False)
    response = client.post(ready["auth_url"], json=ready["auth"], headers=HEADERS)
    assert response.status_code in (409, 422)
    assert not db_session.scalars(select(DeliveryAttempt)).all() and wire[0] == []


def test_prepared_or_crashed_claim_cannot_be_reclaimed(client, db_session, ready, wire):
    from fastapi import HTTPException

    from app.services import wechat_official_delivery as service

    target = _authorize(client, ready)
    attempt_id, claim = service.prepare(db_session, target, ready["owner"])
    assert db_session.get(DeliveryAttempt, attempt_id).status == "prepared"
    with pytest.raises(HTTPException, match="official_execution_claimed"):
        service.prepare(db_session, target, ready["owner"])

    class Crash(BaseException):
        pass

    def crash(*args):
        raise Crash()

    with pytest.raises(Crash):
        service._step(db_session, target, attempt_id, claim, ready["owner"], "create", crash, lambda *args: None)
    db_session.rollback()
    assert db_session.get(DeliveryAttempt, attempt_id).response_metadata_json["in_flight"] == "create"
    assert client.post(f"/api/v1/delivery-targets/{target}/execute", headers=HEADERS).status_code == 409
    assert wire[0] == []
    wrong = client.post(f"/api/v1/delivery-targets/{target}/reconcile", json={
        "resolution": "not_delivered", "expected_attempt_id": attempt_id + 1, "evidence_ref": "sha256:" + "a" * 64}, headers=HEADERS)
    assert wrong.status_code == 409
    reconciled = client.post(f"/api/v1/delivery-targets/{target}/reconcile", json={
        "resolution": "not_delivered", "expected_attempt_id": attempt_id, "evidence_ref": "sha256:" + "a" * 64}, headers=HEADERS)
    assert reconciled.status_code == 200, reconciled.text
    assert db_session.get(DeliveryAttempt, attempt_id).status == "unknown"
    with pytest.raises(HTTPException):
        service._claimed(db_session, target, attempt_id, claim, ready["owner"])
    db_session.rollback()
    second, _ = service.prepare(db_session, target, ready["owner"])
    assert db_session.get(DeliveryAttempt, second).attempt_no == 2


def test_explicit_not_delivered_reconciliation_allows_new_number_not_auto_retry(client, db_session, ready, wire, monkeypatch):
    calls, Transport, _ = wire
    from app.services.wechat_official_transport import OfficialTransportError
    monkeypatch.setattr(Transport, "create_draft", lambda *args: (_ for _ in ()).throw(
        OfficialTransportError("official_response_unconfirmed", dispatched=True)))
    target = _authorize(client, ready)
    first = client.post(f"/api/v1/delivery-targets/{target}/execute", headers=HEADERS)
    assert first.status_code == 200 and first.json()["status"] == "unknown"
    result = client.post(f"/api/v1/delivery-targets/{target}/reconcile", json={"resolution": "not_delivered",
        "expected_attempt_id": first.json()["attempt_id"], "evidence_ref": "sha256:" + "a" * 64}, headers=HEADERS)
    assert result.status_code == 200, result.text
    from app.services.wechat_official_delivery import prepare
    attempt_id, _ = prepare(db_session, target, ready["owner"])
    assert db_session.get(DeliveryAttempt, attempt_id).attempt_no == 2
    assert calls == ["token", "cover"]


def test_authorize_and_prepare_lock_source_before_registration(client, db_session, ready):
    from sqlalchemy import event

    from app.services.wechat_official_delivery import prepare

    statements = []
    def capture(connection, cursor, statement, parameters, context, executemany):
        statements.append(statement.lower())
    engine = db_session.get_bind()
    event.listen(engine, "before_cursor_execute", capture)
    try:
        target = _authorize(client, ready)
        assert next(i for i, row in enumerate(statements) if "from channel_template_version" in row) < next(
            i for i, row in enumerate(statements) if "from capability_registration" in row)
        statements.clear()
        prepare(db_session, target, ready["owner"])
        assert next(i for i, row in enumerate(statements) if "from channel_template_version" in row) < next(
            i for i, row in enumerate(statements) if "from capability_registration" in row)
    finally:
        event.remove(engine, "before_cursor_execute", capture)


def test_revocation_after_cover_refuses_next_external_step(client, db_session, ready, wire, monkeypatch):
    calls, Transport, _ = wire
    original = Transport.upload_cover

    def revoke(self, *args):
        result = original(self, *args)
        capability_integrations.append_verification(db_session, ready["registration"], scope_kind="publisher_action",
            scope=ready["scope"], result="revoked", actor=ready["owner"].email, evidence={"kind": "revocation"})
        return result

    monkeypatch.setattr(Transport, "upload_cover", revoke)
    target = _authorize(client, ready)
    response = client.post(f"/api/v1/delivery-targets/{target}/execute", headers=HEADERS)
    assert response.status_code == 200 and response.json()["status"] == "unknown", response.text
    assert calls == ["token", "cover"]


def test_readback_mismatch_keeps_remote_id_without_publication(client, db_session, ready, wire, monkeypatch):
    _, Transport, article = wire
    monkeypatch.setattr(Transport, "read_draft", lambda *args: {**article, "content": "platform changed text"})
    target = _authorize(client, ready)
    response = client.post(f"/api/v1/delivery-targets/{target}/execute", headers=HEADERS)
    assert response.status_code == 200 and response.json()["status"] == "succeeded", response.text
    attempt = db_session.scalar(select(DeliveryAttempt))
    _move_to_explicit_readback(db_session, target, attempt.id)
    response = client.post(f"/api/v1/delivery-targets/{target}/official-readback",
                           json={"expected_attempt_id": attempt.id}, headers=HEADERS)
    assert response.status_code == 200 and response.json()["status"] == "unknown", response.text
    assert response.json()["remote_id"] == "exact-draft-id"
    assert not db_session.scalars(select(PublishedContentRecord)).all()


def test_registration_revocation_takes_write_lock(db_session, ready):
    from sqlalchemy import event

    seen = []
    def capture(connection, cursor, statement, parameters, context, executemany):
        seen.append(statement.lower())

    engine = db_session.get_bind()
    event.listen(engine, "before_cursor_execute", capture)
    try:
        capability_integrations.append_verification(db_session, ready["registration"], scope_kind="publisher_action",
            scope=ready["scope"], result="revoked", actor=ready["owner"].email, evidence={"kind": "revocation"})
        assert any("update capability_registration" in sql for sql in seen)
    finally:
        event.remove(engine, "before_cursor_execute", capture)


def test_independent_sqlite_connections_compete_for_one_prepared_claim(client, db_session, ready, wire, tmp_path):
    from fastapi import HTTPException
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.services.wechat_official_delivery import prepare

    target = _authorize(client, ready)
    db_session.commit()
    destination = tmp_path / "execution-race.sqlite"
    raw = db_session.get_bind().raw_connection()
    copy = sqlite3.connect(destination)
    try:
        raw.driver_connection.backup(copy)
    finally:
        copy.close()
        raw.close()
    engine = create_engine(f"sqlite:///{destination}", connect_args={"timeout": 5})
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    barrier = threading.Barrier(2)
    owner_id = ready["owner"].id

    def compete():
        with factory() as session:
            user = session.get(User, owner_id)
            barrier.wait(timeout=5)
            try:
                attempt_id, _ = prepare(session, target, user)
                return ("prepared", attempt_id)
            except HTTPException as exc:
                assert exc.status_code == 409
                return ("blocked", None)

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(compete) for _ in range(2)]
            results = [future.result(timeout=10) for future in futures]
        assert sorted(row[0] for row in results) == ["blocked", "prepared"]
        with factory() as session:
            attempts = session.scalars(select(DeliveryAttempt)).all()
            assert len(attempts) == 1 and attempts[0].status == "prepared"
        assert wire[0] == []
    finally:
        engine.dispose()


def test_explicit_known_id_readback_never_recreates_draft(client, db_session, ready, wire, monkeypatch):
    calls, Transport, article = wire

    target = _authorize(client, ready)
    result = client.post(f"/api/v1/delivery-targets/{target}/execute", headers=HEADERS)
    assert result.status_code == 200 and result.json()["status"] == "succeeded", result.text
    attempt = db_session.scalar(select(DeliveryAttempt))
    _move_to_explicit_readback(db_session, target, attempt.id)
    monkeypatch.setattr(Transport, "token", lambda *args: "readback-token")
    def read(*args):
        calls.append("explicit_read")
        assert args[-1] == "exact-draft-id"
        return dict(article)
    monkeypatch.setattr(Transport, "read_draft", read)
    path = f"/api/v1/delivery-targets/{target}/official-readback"
    wrong = client.post(path, json={"expected_attempt_id": attempt.id + 1}, headers=HEADERS)
    assert wrong.status_code == 409, wrong.text
    response = client.post(path, json={"expected_attempt_id": attempt.id}, headers=HEADERS)
    assert response.status_code == 200 and response.json()["status"] == "succeeded", response.text
    assert response.json()["error"] is None
    assert calls.count("create") == 1 and calls.count("explicit_read") == 1
    assert not db_session.scalars(select(PublishedContentRecord)).all()


def test_explicit_readback_failure_retains_safe_diagnostic_without_create(client, db_session, ready, wire, monkeypatch):
    from app.services.wechat_official_transport import OfficialTransportError

    def fail_read(*args):
        raise OfficialTransportError("official_network_unavailable", dispatched=False)

    target = _authorize(client, ready)
    assert client.post(f"/api/v1/delivery-targets/{target}/execute", headers=HEADERS).json()["status"] == "succeeded"
    attempt = db_session.scalar(select(DeliveryAttempt))
    _move_to_explicit_readback(db_session, target, attempt.id)
    monkeypatch.setattr(wire[1], "read_draft", fail_read)
    response = client.post(f"/api/v1/delivery-targets/{target}/official-readback",
                          json={"expected_attempt_id": attempt.id}, headers=HEADERS)
    assert response.status_code == 200 and response.json()["status"] == "unknown"
    db_session.refresh(attempt)
    assert attempt.response_metadata_json["failure_diagnostic"] == {
        "code": "official_network_unavailable", "dispatch_hint": False}
    assert attempt.remote_id == "exact-draft-id" and wire[0].count("create") == 1


def test_historical_candidate_missing_render_refuses_official_without_enrichment(client, db_session, ready, wire):
    from app.services.candidates import candidate_hash

    asset = db_session.get(ContentAsset, ready["candidate"]["id"])
    manifest = dict(asset.candidate_manifest_json)
    manifest.pop("official_render")
    asset.candidate_manifest_json = manifest
    asset.candidate_hash = asset.approved_candidate_hash = candidate_hash(manifest)
    from app.models import Review
    review = db_session.scalar(select(Review).where(Review.content_asset_id == asset.id))
    review.candidate_hash = asset.candidate_hash
    db_session.commit()
    response = client.post(ready["auth_url"], json=ready["auth"], headers=HEADERS)
    assert response.status_code == 409 and response.json()["detail"] == "official_render_required", response.text
    assert "official_render" not in db_session.get(ContentAsset, asset.id).candidate_manifest_json
    assert not db_session.scalars(select(DeliveryAttempt)).all() and wire[0] == []
