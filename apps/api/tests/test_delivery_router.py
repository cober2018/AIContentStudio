"""Delivery Router（V1 PRD 2.0 / capability: delivery-router-v1）。

覆盖：目标授权 registry 验证/幂等；execute prepared-before-call；duplicate execute
不重复 attempt；timeout→unknown 不自动 retry；reconcile 契约；candidate mismatch；
账号变更新 target；copy package hash/media 一致；旧 workflow 直发路径对 v2 封锁。
"""


import pytest

from app.models import (
    ContentAsset,
    ContentJob,
    FactPack,
    TopicBrief,
    User,
)

EDITOR = {"X-Studio-User": "editor@studio.local"}
PNG = b"\x89PNG\r\n\x1a\n" + b"cover" * 8


def _unknown_target(env):
    from app.models import DeliveryAttempt, DeliveryTarget

    db, asset = env
    target = DeliveryTarget(content_asset_id=asset.id, channel="wechat", content_form="article",
        account_ref="acct-1", authorization_version="v1", action="auto_draft",
        authorized_by="editor@studio.local", approved_candidate_hash=asset.approved_candidate_hash,
        status="reconciliation_needed")
    db.add(target)
    db.flush()
    attempt = DeliveryAttempt(target_id=target.id, attempt_no=1, idempotency_key="d" * 64,
                              status="unknown", response_metadata_json={"draft_box": True})
    db.add(attempt)
    db.commit()
    return db, target, attempt


def test_reconcile_delivered_creates_exact_receipt_idempotently_without_publication(env):
    from sqlalchemy import select

    from app.models import AuditLog, DeliveryReceipt, PublishedContentRecord

    db, target, attempt = _unknown_target(env)
    client = _client(db)
    body = {"resolution": "delivered", "expected_attempt_id": attempt.id, "evidence_ref": "sha256:" + "e" * 64}
    endpoint = f"/api/v1/delivery-targets/{target.id}/reconcile"
    for _ in range(2):
        response = client.post(endpoint, json=body, headers=EDITOR)
        assert response.status_code == 200, response.json()
    receipts = db.scalars(select(DeliveryReceipt).where(DeliveryReceipt.target_id == target.id)).all()
    assert len(receipts) == 1
    assert receipts[0].approved_candidate_hash == target.approved_candidate_hash
    assert receipts[0].verification_method == "human_reconciliation"
    assert receipts[0].evidence_ref == body["evidence_ref"]
    assert attempt.status == "unknown"
    assert not db.scalars(select(PublishedContentRecord)).all()
    assert len(db.scalars(select(AuditLog).where(AuditLog.event == "delivery_target.reconciled")).all()) == 1


@pytest.mark.parametrize("body,status", [
    ({"resolution": "delivered"}, 422),
    ({"resolution": "not_delivered", "note": "   "}, 422),
    ({"resolution": "delivered", "evidence_ref": "https://host/?token=SECRET"}, 422),
    ({"resolution": "delivered", "note": "checked", "expected_attempt_id": 9999}, 409),
])
def test_reconcile_rejects_missing_unsafe_or_stale_evidence_without_writes(env, body, status):
    from sqlalchemy import select

    from app.models import DeliveryReceipt

    db, target, attempt = _unknown_target(env)
    response = _client(db).post(f"/api/v1/delivery-targets/{target.id}/reconcile", json=body, headers=EDITOR)
    assert response.status_code == status, response.json()
    assert "SECRET" not in response.text
    assert target.status == "reconciliation_needed"
    assert "reconciled" not in attempt.response_metadata_json
    assert not db.scalars(select(DeliveryReceipt)).all()


def test_reconcile_oversized_note_failure_does_not_echo_secret(env):
    _, target, _ = _unknown_target(env)
    response = _client(env[0]).post(f"/api/v1/delivery-targets/{target.id}/reconcile",
        json={"resolution": "delivered", "note": "PRIVATE_SECRET" * 200}, headers=EDITOR)
    assert response.status_code == 422
    assert "PRIVATE_SECRET" not in response.text


def test_reconcile_hashes_legacy_note_and_rejects_conflicting_retry(env):
    from sqlalchemy import select

    from app.models import AuditLog

    db, target, attempt = _unknown_target(env)
    client = _client(db)
    endpoint = f"/api/v1/delivery-targets/{target.id}/reconcile"
    body = {"resolution": "not_delivered", "note": "verified token=PRIVATE_SECRET no draft"}
    assert client.post(endpoint, json=body, headers=EDITOR).status_code == 200
    assert client.post(endpoint, json=body, headers=EDITOR).status_code == 200
    assert target.status == "target_authorized"
    assert "PRIVATE_SECRET" not in str(attempt.response_metadata_json)
    audit = db.scalar(select(AuditLog).where(AuditLog.event == "delivery_target.reconciled"))
    assert "PRIVATE_SECRET" not in str(audit.detail_json)
    assert client.post(endpoint, json={**body, "resolution": "delivered"}, headers=EDITOR).status_code == 409


def _client(db):
    from fastapi.testclient import TestClient

    from app.db import get_db
    from app.main import app

    def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    return TestClient(app)


@pytest.fixture
def env(db_session):
    db_session.add(User(email="editor@studio.local", name="E", role="editor"))
    pack = FactPack(name="deli包", version=1, status="frozen", checksum="7" * 64)
    db_session.add(pack)
    db_session.flush()
    topic = TopicBrief(title="交付测试", fact_pack_id=pack.id, fact_pack_version=1)
    db_session.add(topic)
    db_session.flush()
    job = ContentJob(topic_brief_id=topic.id, channel="wechat", content_form="article", status="succeeded")
    db_session.add(job)
    db_session.flush()
    manifest = {
        "schema_version": 2,
        "artifact_kind": "text",
        "content_form": "article",
        "channel": "wechat",
        "content": {"title": "交付标题", "body_markdown": "# 交付标题\n\n正文", "document": None, "structured": {}, "thread_posts": None},
        "media": [
            {
                "draft_media_id": None, "material_revision_id": None, "hash": "h0", "role": "cover",
                "sort_order": 0, "placement": {}, "alt_text": None, "caption": None,
                "rights": {"rights_status": "cleared", "public_use_allowed": True, "revoked": False},
            }
        ],
        "checks": [{"id": 1, "kind": "fact", "input_hash": "i" * 64, "status": "pass"}],
        "discoverability": None,
        "render": {
            "renderer_key": "renderer.wechat.article", "renderer_version": "1",
            "content_hash": "r" * 64,
            "payload": {"title": "交付标题", "markdown": "# 交付标题\n\n正文", "html": "<h1>交付标题</h1>", "digest": "交付标题"},
            "warnings": [],
        },
        "execution": {"workflow_key": None, "workflow_version": None, "workflow_checksum": None, "plugins": []},
        "declarations": [],
        "citations": [],
        "input_hash": "i" * 64,
        "revision_no": 1,
    }
    asset = ContentAsset(
        draft_id=1, topic_brief_id=topic.id, channel="wechat", title="交付标题", final_body="正文",
        fact_pack_id=pack.id, fact_pack_version=1, approved_revision=1,
        approved_candidate_hash="c" * 64, candidate_manifest_json=manifest,
        artifact_kind="text", content_form="article",
    )
    db_session.add(asset)
    db_session.commit()
    return db_session, asset


def test_target_authorization_validates_registry_and_idempotent(env):
    db, asset = env
    client = _client(db)
    body = {"channel": "wechat", "content_form": "article", "account_ref": "acct-1", "authorization_version": "v1", "action": "copy_package"}
    r1 = client.post(f"/api/v1/assets/{asset.id}/delivery-targets", json=body, headers=EDITOR)
    assert r1.status_code == 201, r1.json()
    t1 = r1.json()
    assert t1["publisher_key"] == "publisher.copy"
    r2 = client.post(f"/api/v1/assets/{asset.id}/delivery-targets", json=body, headers=EDITOR)
    assert r2.json()["id"] == t1["id"]  # 幂等

    # 未知渠道 400；未注册 auto_draft 渠道 422
    bad = client.post(f"/api/v1/assets/{asset.id}/delivery-targets", json={**body, "channel": "mars"}, headers=EDITOR)
    assert bad.status_code == 400
    noauto = client.post(
        f"/api/v1/assets/{asset.id}/delivery-targets",
        json={**body, "channel": "xiaohongshu", "content_form": "image_note", "action": "auto_draft"}, headers=EDITOR,
    )
    assert noauto.status_code == 422
    assert "capability_unavailable" in noauto.json()["detail"]

    # 账号变化 → 新 target
    other = client.post(
        f"/api/v1/assets/{asset.id}/delivery-targets", json={**body, "account_ref": "acct-2"}, headers=EDITOR
    )
    assert other.json()["id"] != t1["id"]


def test_copy_package_zip_hash_and_media_consistency(env):
    db, asset = env
    client = _client(db)
    # 给 manifest 注入真实素材（material revision）
    from app.services import materials as materials_service

    material = materials_service.create_material(db, kind="image", title="封面")
    revision = materials_service.create_revision(db, material, content=PNG, suffix=".png", declared_mime="image/png", public_use_allowed=True, rights_status="cleared")
    manifest = asset.candidate_manifest_json
    manifest["media"][0]["material_revision_id"] = revision.id
    manifest["media"][0]["hash"] = revision.content_hash
    asset.candidate_manifest_json = manifest
    db.commit()

    target = client.post(
        f"/api/v1/assets/{asset.id}/delivery-targets",
        json={"channel": "wechat", "content_form": "article", "account_ref": "a", "authorization_version": "v1", "action": "copy_package"},
        headers=EDITOR,
    ).json()
    preview = client.post(f"/api/v1/delivery-targets/{target['id']}/package", headers=EDITOR)
    assert preview.status_code == 200
    assert preview.json()["manifest"]["schema_version"] == 2
    zip_resp = client.get(f"/api/v1/delivery-targets/{target['id']}/package.zip", headers=EDITOR)
    assert zip_resp.status_code == 200
    assert zip_resp.content[:2] == b"PK"

    # 撤权后不能再交付

    materials_service.revoke_public_use(db, revision, "版权存疑")
    db.commit()
    blocked = client.get(f"/api/v1/delivery-targets/{target['id']}/package.zip", headers=EDITOR)
    assert blocked.status_code in {403, 409}


def _allow_unverified_auto_draft(monkeypatch):
    """仅让旧交付流程测试越过新 F7 验证闸门；真实放行另测。"""
    from app.services import delivery

    monkeypatch.setattr(delivery, "publisher_target_verified", lambda *args: True)


def test_legacy_unverified_flag_cannot_start_remote_attempt(env, monkeypatch):
    db, asset = env
    client = _client(db)
    from app import runtime_config

    monkeypatch.setattr(runtime_config, "get_runtime", lambda key: {"allow_unverified_auto_draft": True})
    _inject_cover(db, asset)
    target = client.post(
        f"/api/v1/assets/{asset.id}/delivery-targets",
        json={"channel": "wechat", "content_form": "article", "account_ref": "wx-acct", "authorization_version": "v1", "action": "auto_draft"},
        headers=EDITOR,
    )
    assert target.status_code == 201
    result = client.post(f"/api/v1/delivery-targets/{target.json()['id']}/execute", headers=EDITOR)
    assert result.status_code == 409
    assert "publisher_unverified" in result.text
    detail = client.get(f"/api/v1/delivery-targets/{target.json()['id']}", headers=EDITOR).json()
    assert detail["attempts"] == []


def test_wewrite_subprocess_error_does_not_return_secret(monkeypatch):
    from types import SimpleNamespace

    from app.services.content_harness.publishers.wechat_wewrite import WechatWewritePublisher

    secret = "token-super-private-123"

    def fail_run(*args, **kwargs):
        return SimpleNamespace(returncode=1, stdout="", stderr=f"Authorization: Bearer {secret}")

    from app.services.content_harness.publishers import wechat_wewrite

    monkeypatch.setattr(wechat_wewrite.subprocess, "run", fail_run)
    result = WechatWewritePublisher().deliver({
        "render": {"payload": {"title": "Approved", "markdown": "# Approved"}}, "_cover_bytes": b"cover",
    }, None, None)
    assert result.status == "failed"
    assert result.error == "publisher_execution_failed"
    assert secret not in repr(result)


def test_publisher_result_projection_rejects_nested_secret_and_unsafe_remote_id():
    from app.services.content_harness.contracts import PublisherResult
    from app.services.delivery import safe_publisher_result

    result = safe_publisher_result(PublisherResult(
        status="succeeded", remote_id="wx123\nAuthorization: Bearer secret",
        metadata={"channel": "wechat", "nested": {"token": "secret"}, "verified": True},
    ))
    assert result.status == "unknown"
    assert result.remote_id is None
    assert result.metadata == {"channel": "wechat"}
    assert "secret" not in repr(result)


def _inject_cover(db, asset):
    """给 manifest 注入带真实字节的 cover 素材（R2-B3：publisher 不再造 placeholder）。

    R3-3：同步重算批准 hash——模拟「带真实封面的批准候选」（否则完整性 Gate 会正确拦截）。
    必须在创建 DeliveryTarget 之前调用（authorize 冻结 asset.approved_candidate_hash）。
    """
    from app.services import materials as materials_service
    from app.services.candidates import candidate_hash

    material = materials_service.create_material(db, kind="image", title="交付封面")
    revision = materials_service.create_revision(db, material, content=PNG, suffix=".png", declared_mime="image/png", public_use_allowed=True, rights_status="cleared")
    manifest = asset.candidate_manifest_json
    manifest["media"][0]["material_revision_id"] = revision.id
    manifest["media"][0]["hash"] = revision.content_hash
    asset.candidate_manifest_json = manifest
    asset.approved_candidate_hash = candidate_hash(manifest)
    db.commit()
    return revision


def test_wechat_auto_draft_prepared_before_call_and_idempotent(env, monkeypatch):
    """prepared 先落库；成功后 remote_id 保存；duplicate execute 不重复 attempt。"""
    db, asset = env
    client = _client(db)
    _allow_unverified_auto_draft(monkeypatch)
    calls = []

    def fake_run(cmd, capture_output, text, timeout, check):
        calls.append(cmd)

        class P:
            returncode = 0
            stdout = "Draft created! media_id: wx_draft_123"
            stderr = ""

        return P()

    from app.services.content_harness.publishers import wechat_wewrite

    monkeypatch.setattr(wechat_wewrite.subprocess, "run", fake_run)

    _inject_cover(db, asset)
    target = client.post(
        f"/api/v1/assets/{asset.id}/delivery-targets",
        json={"channel": "wechat", "content_form": "article", "account_ref": "wx-acct", "authorization_version": "v1", "action": "auto_draft"},
        headers=EDITOR,
    ).json()
    assert target["publisher_key"] == "publisher.wechat.wewrite"
    assert target["capability"]["verified"] is False  # unverified 如实呈现

    r1 = client.post(f"/api/v1/delivery-targets/{target['id']}/execute", headers=EDITOR)
    assert r1.status_code == 200, r1.json()
    body = r1.json()
    assert body["status"] == "succeeded"
    assert body["remote_id"] == "wx_draft_123"
    assert body["target_status"] == "awaiting_manual_receipt"
    assert len(calls) == 1
    # wewrite 只拿批准 payload（标题不得被临时改写）
    assert "--title" in calls[0] and "交付标题" in calls[0]

    r2 = client.post(f"/api/v1/delivery-targets/{target['id']}/execute", headers=EDITOR)
    assert r2.status_code == 409  # 已 succeeded：不可重复远端调用
    detail = client.get(f"/api/v1/delivery-targets/{target['id']}", headers=EDITOR).json()
    assert len(detail["attempts"]) == 1


def test_timeout_unknown_no_auto_retry_reconcile_contract(env, monkeypatch):
    """timeout → attempt=unknown + target=reconciliation_needed；不自动重发；reconcile 后可重新执行。"""
    db, asset = env
    client = _client(db)
    _allow_unverified_auto_draft(monkeypatch)

    import subprocess

    from app.services.content_harness.publishers import wechat_wewrite

    def fake_timeout(cmd, capture_output, text, timeout, check):
        raise subprocess.TimeoutExpired(cmd="wewrite", timeout=180)

    monkeypatch.setattr(wechat_wewrite.subprocess, "run", fake_timeout)

    _inject_cover(db, asset)
    target = client.post(
        f"/api/v1/assets/{asset.id}/delivery-targets",
        json={"channel": "wechat", "content_form": "article", "account_ref": "wx-acct", "authorization_version": "v1", "action": "auto_draft"},
        headers=EDITOR,
    ).json()
    r1 = client.post(f"/api/v1/delivery-targets/{target['id']}/execute", headers=EDITOR)
    assert r1.json()["status"] == "unknown"
    assert r1.json()["target_status"] == "reconciliation_needed"

    # unknown 状态下不可自动重发
    r2 = client.post(f"/api/v1/delivery-targets/{target['id']}/execute", headers=EDITOR)
    assert r2.status_code == 409

    # 对账：未送达 → 回到 target_authorized，可重新 execute（人工契约）
    rec = client.post(
        f"/api/v1/delivery-targets/{target['id']}/reconcile",
        json={"resolution": "not_delivered", "note": "平台侧无草稿"},
        headers=EDITOR,
    )
    assert rec.status_code == 200
    assert rec.json()["status"] == "target_authorized"

    def fake_ok(cmd, capture_output, text, timeout, check):
        class P:
            returncode = 0
            stdout = "Draft created! media_id: wx_retry_1"
            stderr = ""

        return P()

    monkeypatch.setattr(wechat_wewrite.subprocess, "run", fake_ok)
    r3 = client.post(f"/api/v1/delivery-targets/{target['id']}/execute", headers=EDITOR)
    assert r3.status_code == 200
    assert r3.json()["attempt_no"] == 2  # 新 attempt，历史可审计


def test_candidate_mismatch_blocks_execute(env):
    db, asset = env
    client = _client(db)
    target = client.post(
        f"/api/v1/assets/{asset.id}/delivery-targets",
        json={"channel": "wechat", "content_form": "article", "account_ref": "a", "authorization_version": "v1", "action": "copy_package"},
        headers=EDITOR,
    ).json()
    # 目标授权后资产候选被替换（hash 不一致）
    asset.approved_candidate_hash = "new" + "0" * 60
    db.commit()
    r = client.post(f"/api/v1/delivery-targets/{target['id']}/execute", headers=EDITOR)
    assert r.status_code == 409
    assert "不一致" in r.json()["detail"]


def test_v2_content_blocked_from_legacy_workflow_publish(env):
    """schema v2 候选禁止经旧 workflow_engine 直接发布（D24/5.8）。"""
    db, asset = env
    from app.models import Workflow
    from app.services import workflow_engine

    user = db.query(User).filter_by(email="editor@studio.local").first()
    wf = Workflow(
        name="legacy publish", template_key="gen_export",
        definition_json={"nodes": [{"id": "p", "type": "publish_wechat", "label": "p", "params": {"channel": "wechat", "legacy_remote_publish": True}, "layout": {"x": 0, "y": 0}}], "edges": []},
    )
    db.add(wf)
    db.flush()
    # 把 asset 挂到 context
    from app.models import WorkflowRun

    run = WorkflowRun(workflow_id=wf.id, params_json={}, context_json={"assets": {"wechat": asset.id}})
    db.add(run)
    db.commit()
    from app.models import WorkflowStep

    step = WorkflowStep(run_id=run.id, node_id="p", node_type="publish_wechat", label="p", params_json={"channel": "wechat", "legacy_remote_publish": True}, plugin_key="builtin.publish_wechat", plugin_version="1")
    db.add(step)
    db.commit()
    import pytest as _pytest

    handler = workflow_engine._h_publish_wechat
    with _pytest.raises(ValueError, match="Delivery Router"):
        handler(db, run, step, user)


def test_receipt_and_feedback_on_generic_target(env):
    db, asset = env
    client = _client(db)
    target = client.post(
        f"/api/v1/assets/{asset.id}/delivery-targets",
        json={"channel": "wechat", "content_form": "article", "account_ref": "a", "authorization_version": "v1", "action": "copy_package"},
        headers=EDITOR,
    ).json()
    # 未生成包前不可回填
    early = client.post(f"/api/v1/delivery-targets/{target['id']}/receipt", json={"status": "human_confirmed"}, headers=EDITOR)
    assert early.status_code == 409
    # 生成包 → awaiting_manual_receipt → 回填
    client.post(f"/api/v1/delivery-targets/{target['id']}/package", headers=EDITOR)
    ok = client.post(
        f"/api/v1/delivery-targets/{target['id']}/receipt",
        json={"status": "human_confirmed", "evidence_ref": "https://mp.weixin.qq.com/x", "verification_method": "link_checked"},
        headers=EDITOR,
    )
    assert ok.status_code == 200
    assert ok.json()["status"] == "human_confirmed"
    fb = client.post(f"/api/v1/delivery-targets/{target['id']}/feedback", json={"kind": "performance", "body": "阅读量上升"}, headers=EDITOR)
    assert fb.status_code == 201
