"""A ready post-adaptation Variant is the sole source of a v5 Candidate."""

import hashlib
import io
import json
import sqlite3
import threading
import zipfile
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.models import (
    CapabilityRegistration,
    ContentAccount,
    ContentAsset,
    ContentMasterCheckRun,
    ContentProject,
    ContentUnit,
    DeliveryAttempt,
    DeliveryTarget,
    FactPack,
    FactPackItem,
    LLMRun,
    Material,
    MaterialRevision,
    PerformanceObservation,
    ProjectEvent,
    ProjectMaterialReference,
    PublishedContentRecord,
    Review,
    User,
    utcnow,
)
from app.seed import seed_v1_channel_profiles
from app.services import capability_integrations
from app.services.content_harness.contracts import PublisherResult
from app.services.content_harness.publishers.wechat_wewrite import WechatWewritePublisher

HEADERS = {"X-Studio-User": "v5-freeze@studio.local"}


def _approval_payload(candidate):
    warnings = candidate["manifest"]["source_master"].get("warning_checks", [])
    return {"candidate_hash": candidate["candidate_hash"],
            "warning_dispositions": {f"{row['id']}:{row['input_hash']}": "编辑已核对该提示"
                                     for row in warnings}}


def _ready_source(client, db, *, neutral=False, cited=False):
    seed_v1_channel_profiles(db)
    db.commit()
    persona = client.post("/api/v1/content-personas", json={"name": "作者"}, headers=HEADERS).json()["id"]
    project = client.post("/api/v1/content-projects", json={"title": "渠道成品"}, headers=HEADERS).json()["id"]
    unit_response = client.post(f"/api/v1/content-projects/{project}/units", json={
        "title": "源稿", "persona_id": persona, "modality": "text", "channel_id": None if neutral else "x",
    }, headers=HEADERS)
    assert unit_response.status_code == 201, unit_response.text
    unit = unit_response.json()["id"]
    brief = client.post(f"/api/v1/content-projects/{project}/brief/revisions", json={
        "objective": "准确表达观点", "expected_revision": 0,
    }, headers=HEADERS)
    assert brief.status_code == 201, brief.text
    pack = FactPack(name="真实事实边界", version=1, status="frozen", checksum="c" * 64)
    db.add(pack)
    db.flush()
    item = FactPackItem(fact_pack_id=pack.id, evidence_kind="author_opinion",
                        snapshot_json={"statement": "这是观点"}, snapshot_checksum="d" * 64,
                        public_use_allowed=True, model_use_allowed=True)
    db.add(item)
    db.flush()
    db.commit()
    boundary = client.post(f"/api/v1/content-projects/{project}/fact-boundary", json={
        "fact_pack_id": pack.id, "expected_revision": 0,
    }, headers=HEADERS)
    assert boundary.status_code == 201, boundary.text
    master_path = f"/api/v1/content-projects/{project}/units/{unit}/master-revisions"
    citation = {"id": "c1", "block_id": "b1", "start": 0, "end": 4, "fact_pack_item_id": item.id,
                "selected_text_hash": hashlib.sha256("这是观点".encode()).hexdigest()}
    master = client.post(master_path, json={
        "idempotency_key": "v5-source", "payload_schema": "text.master.v2",
        **({} if neutral else {"content_form": "single"}),
        "payload": {"title": "有来源的观点", "document": {"schema": "studio.text.document.v1", "blocks": [
            {"id": "b1", "type": "paragraph", "content": [{"text": "这是观点", "marks": []}]},
        ], "citations": [citation] if cited else []}},
        **({"evidence_refs": [{"fact_pack_item_id": item.id, "snapshot_checksum": item.snapshot_checksum,
                                 "locator": {"citation_id": "c1", "block_id": "b1", "start": 0, "end": 4,
                                             "selected_text_hash": citation["selected_text_hash"]}}]} if cited else {}),
    }, headers=HEADERS)
    assert master.status_code == 200, master.text
    checks = client.post(f"{master_path}/{master.json()['id']}/checks", headers=HEADERS)
    assert checks.status_code == 200, checks.text
    return project, unit, master.json()


def test_neutral_text_master_is_source_only_and_can_freeze_v5_variant(client, db_session):
    project, unit, master = _ready_source(client, db_session, neutral=True)
    assert master["channel_id"] is None and master["content_form"] is None
    direct = client.post(f"/api/v1/content-projects/{project}/units/{unit}/candidates/freeze", json={
        "content_master_revision_id": master["id"], "expected_payload_hash": master["payload_hash"],
    }, headers=HEADERS)
    assert direct.status_code in (409, 422), direct.text
    assert not db_session.scalars(select(ContentAsset)).all()
    variant = _ready_variant(client, project, unit, master)
    frozen = client.post(f"/api/v1/content-projects/{project}/units/{unit}/candidates/freeze", json={
        "channel_variant_revision_id": variant["id"], "expected_payload_hash": variant["payload_hash"],
    }, headers=HEADERS)
    assert frozen.status_code == 201, frozen.text
    assert frozen.json()["manifest"]["source_master"]["channel"] is None
    assert frozen.json()["manifest"]["target"]["channel"] == "x"


def _ready_variant(client, project, unit, master, *, key="x.single.primary", form="single"):
    path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    payload = {"text": "这是观点"} if form == "single" else {"posts": [{"id": "b1", "order": 0, "text": "这是观点"}]}
    saved = client.post(path, json={
        "variant_key": key, "expected_revision": 0, "source_master_revision_id": master["id"],
        "expected_source_payload_hash": master["payload_hash"], "expected_source_context_hash": master["context_hash"],
        "channel_id": "x", "content_form": form, "idempotency_key": key, "source_kind": "deterministic_adapt",
        "payload": payload,
    }, headers=HEADERS)
    assert saved.status_code == 201, saved.text
    checks = client.post(f"{path}/{saved.json()['id']}/checks", headers=HEADERS)
    assert checks.status_code == 200, checks.text
    assert checks.json()["ready"] is True, checks.json()
    return saved.json()


def test_concurrent_v5_freeze_reuses_one_exact_candidate(client, db_session, tmp_path):
    from app.services.project_review import freeze_variant_candidate

    project, unit, master = _ready_source(client, db_session, neutral=True)
    variant = _ready_variant(client, project, unit, master)
    user_id = db_session.scalar(select(User.id).where(User.email == HEADERS["X-Studio-User"]))
    db_session.commit()
    db_file = tmp_path / "v5-freeze-race.db"
    with sqlite3.connect(db_file) as target:
        db_session.connection().connection.driver_connection.backup(target)
        target.execute("PRAGMA journal_mode=WAL")
    db_session.rollback()
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False, "timeout": 5})
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    start = threading.Barrier(2, timeout=5)

    def freeze():
        with factory() as session:
            user = session.get(User, user_id)
            start.wait()
            return freeze_variant_candidate(session, project, unit, variant["id"], user,
                                            expected_payload_hash=variant["payload_hash"]).id

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            ids = [future.result(timeout=12) for future in (pool.submit(freeze), pool.submit(freeze))]
        assert ids[0] == ids[1]
        with factory() as session:
            candidates = session.scalars(select(ContentAsset).where(
                ContentAsset.project_id == project, ContentAsset.channel_variant_revision_id == variant["id"])).all()
            events = session.scalars(select(ProjectEvent).where(
                ProjectEvent.project_id == project, ProjectEvent.event_type == "candidate.frozen")).all()
            assert len(candidates) == len(events) == 1
            assert candidates[0].id == ids[0] and events[0].entity_id == str(ids[0])
    finally:
        engine.dispose()


@pytest.mark.parametrize(("channel", "form"), [("wechat", "article"), ("x", "thread"), ("x", "single")])
def test_v5_text_packages_freeze_exact_inherited_citation(client, db_session, tmp_path, channel, form):
    project, unit, master = _ready_source(client, db_session, neutral=True, cited=True)
    variants = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    intent = {"source_master_revision_id": master["id"], "expected_source_payload_hash": master["payload_hash"],
              "expected_source_context_hash": master["context_hash"], "channel_id": channel, "content_form": form}
    cover = None
    if channel == "wechat":
        content = b"\x89PNG\r\n\x1a\nverified cited cover"
        file = tmp_path / "cover.png"
        file.write_bytes(content)
        material = Material(title="引文封面", kind="image", status="active")
        db_session.add(material)
        db_session.flush()
        cover = MaterialRevision(material_id=material.id, content_hash=hashlib.sha256(content).hexdigest(),
                                 file_path=str(file), mime_type="image/png", status="active",
                                 public_use_allowed=True, rights_status="cleared")
        db_session.add(cover)
        db_session.flush()
        db_session.add(ProjectMaterialReference(project_id=project, material_revision_id=cover.id,
                                                origin="system_library", status="active"))
        db_session.commit()
    preview = client.post(f"{variants}/adapt-preview", json=intent, headers=HEADERS)
    assert preview.status_code == 200, preview.text
    proposed = preview.json()
    assert proposed["evidence_refs"][0]["fact_pack_item_id"] == proposed["payload"]["citations"][0]["fact_pack_item_id"]
    asset_refs = ([{"material_revision_id": cover.id, "content_hash_snapshot": cover.content_hash,
                    "role": "cover", "slot_key": "cover", "sort_order": 0, "placement": {"usage": "cover"}}]
                  if cover else proposed["asset_refs"])
    saved = client.post(variants, json={**intent, "variant_key": f"{channel}.{form}.cited",
        "expected_revision": 0, "idempotency_key": f"{channel}.{form}.cited", "source_kind": "deterministic_adapt",
        "payload": proposed["payload"], "asset_refs": asset_refs, "evidence_refs": proposed["evidence_refs"]}, headers=HEADERS)
    assert saved.status_code == 201, saved.text
    checked = client.post(f"{variants}/{saved.json()['id']}/checks", headers=HEADERS)
    assert checked.status_code == 200 and checked.json()["ready"] is True, checked.text
    candidates = f"/api/v1/content-projects/{project}/units/{unit}/candidates"
    frozen = client.post(f"{candidates}/freeze", json={"channel_variant_revision_id": saved.json()["id"],
        "expected_payload_hash": saved.json()["payload_hash"]}, headers=HEADERS)
    assert frozen.status_code == 201, frozen.text
    candidate = frozen.json()
    assert candidate["manifest"]["citations"] == proposed["payload"]["citations"]
    assert candidate["manifest"]["evidence_refs"][0]["content_locator_json"] == proposed["evidence_refs"][0]["content_locator_json"]
    approved = client.post(f"{candidates}/{candidate['id']}/approve", json=_approval_payload(candidate), headers=HEADERS)
    assert approved.status_code == 200, approved.text
    target = client.post(f"{candidates}/{candidate['id']}/delivery-authorizations", json={
        "channel": channel, "content_form": form, "account_ref": f"manual-{channel}",
        "authorization_version": "v1", "action": "copy_package"}, headers=HEADERS)
    assert target.status_code == 201, target.text
    downloaded = client.get(f"/api/v1/delivery-targets/{target.json()['id']}/package.zip", headers=HEADERS)
    assert downloaded.status_code == 200, downloaded.text
    with zipfile.ZipFile(io.BytesIO(downloaded.content)) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["schema_version"] == 5 and manifest["remote_call"] is False
        assert manifest["citations"] == proposed["payload"]["citations"]
        assert manifest["evidence_refs"][0]["content_locator_json"] == proposed["evidence_refs"][0]["content_locator_json"]
        assert "这是观点" in archive.read("content.md").decode()
        if cover:
            assert archive.read(manifest["media"][0]["name"]) == (tmp_path / "cover.png").read_bytes()


def test_v5_text_declaration_preserves_exact_evidence_and_package(client, db_session):
    project, unit, master = _ready_source(client, db_session, neutral=True, cited=True)
    variants = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    intent = {"source_master_revision_id": master["id"], "expected_source_payload_hash": master["payload_hash"],
              "expected_source_context_hash": master["context_hash"], "channel_id": "x", "content_form": "single"}
    preview = client.post(f"{variants}/adapt-preview", json=intent, headers=HEADERS)
    assert preview.status_code == 200, preview.text
    declaration = {"id": "d1", "kind": "ai_assistance", "text": "本文使用 AI 辅助整理"}
    payload = {**preview.json()["payload"], "declarations": [declaration]}
    saved = client.post(variants, json={**intent, "variant_key": "x.single.declared", "expected_revision": 0,
        "idempotency_key": "x.single.declared", "source_kind": "manual_edit", "payload": payload,
        "evidence_refs": preview.json()["evidence_refs"]}, headers=HEADERS)
    assert saved.status_code == 201, saved.text
    checked = client.post(f"{variants}/{saved.json()['id']}/checks", headers=HEADERS)
    assert checked.status_code == 200 and checked.json()["ready"] is True, checked.text
    assert checked.json()["items"][-1]["status"] == "pass"
    candidates = f"/api/v1/content-projects/{project}/units/{unit}/candidates"
    frozen = client.post(f"{candidates}/freeze", json={"channel_variant_revision_id": saved.json()["id"],
        "expected_payload_hash": saved.json()["payload_hash"]}, headers=HEADERS)
    assert frozen.status_code == 201, frozen.text
    candidate = frozen.json()
    assert candidate["manifest"]["declarations"] == [declaration]
    approved = client.post(f"{candidates}/{candidate['id']}/approve", json=_approval_payload(candidate), headers=HEADERS)
    assert approved.status_code == 200, approved.text
    target = client.post(f"{candidates}/{candidate['id']}/delivery-authorizations", json={
        "channel": "x", "content_form": "single", "account_ref": "manual-x", "authorization_version": "v1",
        "action": "copy_package"}, headers=HEADERS)
    assert target.status_code == 201, target.text
    downloaded = client.get(f"/api/v1/delivery-targets/{target.json()['id']}/package.zip", headers=HEADERS)
    assert downloaded.status_code == 200, downloaded.text
    with zipfile.ZipFile(io.BytesIO(downloaded.content)) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["declarations"] == [declaration]
        assert manifest["citations"] == payload["citations"]
        assert manifest["evidence_refs"][0]["content_locator_json"] == preview.json()["evidence_refs"][0]["content_locator_json"]


def test_v5_freeze_uses_only_exact_current_variant_and_is_idempotent(client, db_session):
    project, unit, master = _ready_source(client, db_session)
    variant = _ready_variant(client, project, unit, master)
    path = f"/api/v1/content-projects/{project}/units/{unit}/candidates/freeze"
    body = {"channel_variant_revision_id": variant["id"], "expected_payload_hash": variant["payload_hash"]}
    first = client.post(path, json=body, headers=HEADERS)
    assert first.status_code == 201, first.text
    candidate = db_session.get(ContentAsset, first.json()["id"])
    assert candidate.channel_variant_revision_id == variant["id"]
    assert candidate.candidate_manifest_json["schema_version"] == 5
    assert candidate.candidate_manifest_json["target"]["content_form"] == "single"
    assert all(getattr(candidate, field) is None for field in (
        "draft_id", "topic_brief_id", "mother_revision_id", "content_master_revision_id", "workflow_run_id"))
    assert candidate.channel == "x" and candidate.content_form == "single" and candidate.artifact_kind == "text"
    assert candidate.status == "frozen" and candidate.approved_candidate_hash is None
    repeat = client.post(path, json=body, headers=HEADERS)
    assert repeat.status_code == 201 and repeat.json()["id"] == candidate.id
    assert db_session.scalars(select(ContentAsset)).all() == [candidate]
    assert len(db_session.scalars(select(ProjectEvent).where(ProjectEvent.event_type == "candidate.frozen")).all()) == 1


def test_v5_source_warning_requires_exact_approval_disposition_and_stays_verified_at_package(client, db_session):
    project, unit, master = _ready_source(client, db_session)
    variant = _ready_variant(client, project, unit, master)
    source_warnings = db_session.scalars(select(ContentMasterCheckRun).where(
        ContentMasterCheckRun.master_revision_id == master["id"],
        ContentMasterCheckRun.status == "warning")).all()
    assert {row.check_kind for row in source_warnings} >= {"text_fact", "text_identity"}
    checks = client.get(f"/api/v1/content-projects/{project}/units/{unit}/channel-variants/{variant['id']}/checks",
                        headers=HEADERS)
    assert checks.status_code == 200 and checks.json()["ready"] is True, checks.text

    candidates = f"/api/v1/content-projects/{project}/units/{unit}/candidates"
    frozen = client.post(f"{candidates}/freeze", json={
        "channel_variant_revision_id": variant["id"], "expected_payload_hash": variant["payload_hash"]}, headers=HEADERS)
    assert frozen.status_code == 201, frozen.text
    candidate = frozen.json()
    frozen_warnings = candidate["manifest"]["source_master"]["warning_checks"]
    assert {row["kind"] for row in frozen_warnings} >= {"text_fact", "text_identity"}
    approval_url = f"{candidates}/{candidate['id']}/approve"
    missing = client.post(approval_url, json={"candidate_hash": candidate["candidate_hash"]}, headers=HEADERS)
    assert missing.status_code == 409, missing.text
    assert db_session.scalars(select(Review).where(Review.content_asset_id == candidate["id"])).all() == []
    dispositions = {f"{row['id']}:{row['input_hash']}": "编辑已核对该提示" for row in frozen_warnings}
    wrong = client.post(approval_url, json={"candidate_hash": candidate["candidate_hash"],
                                               "warning_dispositions": {"wrong:hash": "已核对"}}, headers=HEADERS)
    assert wrong.status_code == 409, wrong.text
    approved = client.post(approval_url, json={"candidate_hash": candidate["candidate_hash"],
                                                  "warning_dispositions": dispositions}, headers=HEADERS)
    assert approved.status_code == 200, approved.text
    authorized = client.post(f"{candidates}/{candidate['id']}/delivery-authorizations", json={
        "channel": "x", "content_form": "single", "account_ref": "manual-x",
        "authorization_version": "v1", "action": "copy_package"}, headers=HEADERS)
    assert authorized.status_code == 201, authorized.text
    package_url = f"/api/v1/delivery-targets/{authorized.json()['id']}/package.zip"
    assert client.get(package_url, headers=HEADERS).status_code == 200
    review = db_session.scalar(select(Review).where(Review.content_asset_id == candidate["id"],
                                                  Review.decision == "approved"))
    review.warning_dispositions_json = None
    db_session.commit()
    assert client.get(package_url, headers=HEADERS).status_code == 409
    review.warning_dispositions_json = dispositions
    warning = source_warnings[0]
    db_session.add(ContentMasterCheckRun(master_revision_id=master["id"], check_kind=warning.check_kind,
        profile_key=warning.profile_key, profile_version=warning.profile_version, input_hash=warning.input_hash,
        status="blocker", report_json={"reasons": ["new_safety_blocker"]}))
    db_session.commit()
    assert client.get(package_url, headers=HEADERS).status_code == 409


@pytest.mark.parametrize("invalidate", [False, True])
def test_v5_model_variant_freezes_only_verified_safe_receipt(client, db_session, monkeypatch, invalidate):
    from app.services import channel_variants as service
    from app.services.generation.providers import GenerateResult

    project, unit, master = _ready_source(client, db_session)
    class Provider:
        name = "test-provider"
        model = "test-model"

        async def generate_json(self, request):
            return GenerateResult(data={"payload": {"text": "这是观点"}}, raw_output="private provider output", usage={})

    monkeypatch.setattr(service, "get_provider", lambda purpose: Provider())
    path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    source = {"source_master_revision_id": master["id"], "expected_source_payload_hash": master["payload_hash"],
              "expected_source_context_hash": master["context_hash"], "channel_id": "x", "content_form": "single"}
    suggested = client.post(f"{path}/model-suggestions", json=source, headers=HEADERS)
    assert suggested.status_code == 200, suggested.text
    saved = client.post(path, json={**source, "variant_key": "x.single.model", "expected_revision": 0,
        "idempotency_key": "model-1", "source_kind": "model_assisted", "payload": suggested.json()["payload"],
        "llm_provenance": {"llm_run_id": suggested.json()["llm_run_id"]}}, headers=HEADERS)
    assert saved.status_code == 201, saved.text
    checks = client.post(f"{path}/{saved.json()['id']}/checks", headers=HEADERS)
    assert checks.status_code == 200 and checks.json()["ready"] is True, checks.text
    run = db_session.get(LLMRun, suggested.json()["llm_run_id"])
    if invalidate:
        run.status = "failed"
        db_session.commit()
    frozen = client.post(f"/api/v1/content-projects/{project}/units/{unit}/candidates/freeze", json={
        "channel_variant_revision_id": saved.json()["id"], "expected_payload_hash": saved.json()["payload_hash"]}, headers=HEADERS)
    if invalidate:
        assert frozen.status_code == 409, frozen.text
        assert not db_session.scalars(select(ContentAsset)).all()
    else:
        assert frozen.status_code == 201, frozen.text
        receipt = frozen.json()["manifest"]["production"]["llm_provenance"]
        assert set(receipt) == {"llm_run_id", "provider", "model", "prompt_version", "purpose",
                                "input_hash", "accepted_output_hash", "status"}
        assert "private provider output" not in frozen.text


def test_v5_freeze_series_independence_and_fail_closed_inputs(client, db_session):
    project, unit, master = _ready_source(client, db_session)
    single = _ready_variant(client, project, unit, master)
    thread = _ready_variant(client, project, unit, master, key="x.thread.primary", form="thread")
    path = f"/api/v1/content-projects/{project}/units/{unit}/candidates/freeze"
    for variant in (single, thread):
        frozen = client.post(path, json={"channel_variant_revision_id": variant["id"],
                                         "expected_payload_hash": variant["payload_hash"]}, headers=HEADERS)
        assert frozen.status_code == 201, frozen.text
        assert frozen.json()["content_form"] == variant["content_form"]
    assert len(db_session.scalars(select(ContentAsset)).all()) == 2
    invalid = (
        {"channel_variant_revision_id": single["id"]},
        {"channel_variant_revision_id": single["id"], "expected_payload_hash": "0" * 64},
        {"channel_variant_revision_id": single["id"], "content_master_revision_id": master["id"],
         "expected_payload_hash": single["payload_hash"]},
        {"channel_variant_revision_id": 999999, "expected_payload_hash": single["payload_hash"]},
    )
    for payload in invalid:
        response = client.post(path, json=payload, headers=HEADERS)
        assert response.status_code in (404, 409, 422), response.text
    assert len(db_session.scalars(select(ContentAsset)).all()) == 2
    assert not db_session.scalars(select(Review)).all()
    assert not db_session.scalars(select(DeliveryTarget)).all()
    assert all(row.candidate_manifest_json["schema_version"] == 5 for row in db_session.scalars(select(ContentAsset)).all())


def test_v5_project_versions_keep_each_channel_series_current(client, db_session):
    project, unit, master = _ready_source(client, db_session)
    variants = (_ready_variant(client, project, unit, master),
                _ready_variant(client, project, unit, master, key="x.thread.primary", form="thread"))
    frozen = []
    for variant in variants:
        response = client.post(f"/api/v1/content-projects/{project}/units/{unit}/candidates/freeze", json={
            "channel_variant_revision_id": variant["id"], "expected_payload_hash": variant["payload_hash"],
        }, headers=HEADERS)
        assert response.status_code == 201, response.text
        frozen.append(response.json())
    versions = client.get(f"/api/v1/content-projects/{project}/versions", headers=HEADERS)
    assert versions.status_code == 200, versions.text
    candidates = {int(row["id"]): row for row in versions.json()["candidates"]}
    assert all(candidates[row["id"]]["current"] is True for row in frozen)
    revisions = {row["variantKey"]: row for row in versions.json()["channelVariants"]}
    assert set(revisions) == {"x.single.primary", "x.thread.primary"}
    assert all(row["current"] is True for row in revisions.values())
    assert {row["sourceMasterRevisionId"] for row in revisions.values()} == {master["id"]}


def test_v5_overview_preserves_unknown_from_other_current_series(client, db_session):
    project, unit, master = _ready_source(client, db_session)
    single = _ready_variant(client, project, unit, master)
    first = client.post(f"/api/v1/content-projects/{project}/units/{unit}/candidates/freeze", json={
        "channel_variant_revision_id": single["id"], "expected_payload_hash": single["payload_hash"],
    }, headers=HEADERS)
    assert first.status_code == 201, first.text
    db_session.add(DeliveryTarget(content_asset_id=first.json()["id"], channel="x", content_form="single",
                                  action="copy_package", account_ref="manual", authorization_version="v1",
                                  approved_candidate_hash=first.json()["candidate_hash"], authorized_by=HEADERS["X-Studio-User"],
                                  authorized_at=utcnow(), requested_at=utcnow(), status="reconciliation_needed"))
    db_session.commit()
    thread = _ready_variant(client, project, unit, master, key="x.thread.primary", form="thread")
    second = client.post(f"/api/v1/content-projects/{project}/units/{unit}/candidates/freeze", json={
        "channel_variant_revision_id": thread["id"], "expected_payload_hash": thread["payload_hash"],
    }, headers=HEADERS)
    assert second.status_code == 201, second.text
    overview = client.get(f"/api/v1/content-projects/{project}/overview", headers=HEADERS)
    assert overview.status_code == 200, overview.text
    assert overview.json()["nextAction"]["code"] == "delivery.reconcile"
    review_unit = overview.json()["review"]["units"][0]
    assert {row["variantKey"] for row in review_unit["variantSeries"]} == {"x.single.primary", "x.thread.primary"}
    from app.services.project_overview import project_overviews

    bulk = project_overviews(db_session, [project], summary_only=True)[project]
    assert bulk["nextAction"]["code"] == "delivery.reconcile"
    assert {row["variantKey"] for row in bulk["review"]["units"][0]["variantSeries"]} == {
        "x.single.primary", "x.thread.primary"}


def test_v5_review_projection_keeps_pending_series_after_other_series_approved(client, db_session):
    project, unit, master = _ready_source(client, db_session)
    single = _ready_variant(client, project, unit, master)
    thread = _ready_variant(client, project, unit, master, key="x.thread.primary", form="thread")
    frozen = []
    for variant in (single, thread):
        response = client.post(f"/api/v1/content-projects/{project}/units/{unit}/candidates/freeze", json={
            "channel_variant_revision_id": variant["id"], "expected_payload_hash": variant["payload_hash"],
        }, headers=HEADERS)
        assert response.status_code == 201, response.text
        frozen.append(response.json())
    approved = client.post(f"/api/v1/content-projects/{project}/units/{unit}/candidates/{frozen[1]['id']}/approve",
                           json=_approval_payload(frozen[1]), headers=HEADERS)
    assert approved.status_code == 200, approved.text
    review = client.get(f"/api/v1/review-center/projects/{project}/units/{unit}", headers=HEADERS)
    assert review.status_code == 200, review.text
    body = review.json()
    assert body["summary"] == "waiting_review"
    assert body["dimensions"]["approval"]["status"] == "waiting_review"
    assert {row["variantKey"]: row["approvalStatus"] for row in body["variantSeries"]} == {
        "x.single.primary": "waiting_review", "x.thread.primary": "approved",
    }


def test_v5_project_read_models_mark_variant_stale_after_source_master_advances(client, db_session):
    project, unit, master = _ready_source(client, db_session)
    variant = _ready_variant(client, project, unit, master)
    frozen = client.post(f"/api/v1/content-projects/{project}/units/{unit}/candidates/freeze", json={
        "channel_variant_revision_id": variant["id"], "expected_payload_hash": variant["payload_hash"],
    }, headers=HEADERS)
    assert frozen.status_code == 201, frozen.text
    save = client.post(f"/api/v1/content-projects/{project}/units/{unit}/master-revisions", json={
        "idempotency_key": "source-updated", "expected_revision": 1,
        "payload": {"title": "更新观点", "document": {"schema": "studio.text.document.v1", "blocks": [
            {"id": "b1", "type": "paragraph", "content": [{"text": "更新观点", "marks": []}]},
        ], "citations": []}},
    }, headers=HEADERS)
    assert save.status_code == 200, save.text
    versions = client.get(f"/api/v1/content-projects/{project}/versions", headers=HEADERS)
    assert versions.status_code == 200, versions.text
    row = next(row for row in versions.json()["channelVariants"] if row["id"] == str(variant["id"]))
    assert row["current"] is False
    assert row["status"] == "stale"
    candidate = next(row for row in versions.json()["candidates"] if row["id"] == str(frozen.json()["id"]))
    assert candidate["current"] is False
    overview = client.get(f"/api/v1/content-projects/{project}/overview", headers=HEADERS)
    assert overview.status_code == 200, overview.text
    series = overview.json()["review"]["units"][0]["variantSeries"][0]
    assert series["status"] == "stale"
    assert {risk["code"] for risk in overview.json()["risks"]} >= {"variant_stale"}


def test_matrix_suggestions_are_bounded_read_only_and_explain_capability(client, db_session):
    project, _, _ = _ready_source(client, db_session)
    before_units = client.get(f"/api/v1/content-projects/{project}", headers=HEADERS).json()["units"]
    before_events = len(db_session.scalars(select(ProjectEvent).where(ProjectEvent.project_id == project)).all())
    response = client.get(f"/api/v1/content-projects/{project}/matrix/suggestions?limit=2", headers=HEADERS)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["persisted"] is False and body["schedule"] is False
    assert len(body["items"]) <= 2
    assert body["items"]
    assert all(item["reason"] and item["capability"]["configured"] for item in body["items"])
    assert all(item["historyCoverage"] == "unknown" and item["confidence"] == "unknown" for item in body["items"])
    assert all(item["estimatedCost"] == "unknown" and item["estimatedValue"] == "unknown"
               and item["unknowns"] for item in body["items"])
    assert client.get(f"/api/v1/content-projects/{project}/matrix/suggestions?limit=2", headers=HEADERS).json() == body
    assert client.get(f"/api/v1/content-projects/{project}", headers=HEADERS).json()["units"] == before_units
    assert len(db_session.scalars(select(ProjectEvent).where(ProjectEvent.project_id == project)).all()) == before_events
    assert client.get(f"/api/v1/content-projects/{project}/matrix/suggestions?limit=1000", headers=HEADERS).status_code == 422
    assert client.get(f"/api/v1/content-projects/{project}/matrix/suggestions", headers={"X-Studio-User": "foreign-matrix@studio.local"}).status_code == 404


def test_matrix_without_brief_identity_scope_uses_selected_project_identity(client, db_session):
    project, unit, _ = _ready_source(client, db_session)
    selected_persona = db_session.get(ContentUnit, unit).persona_id
    other = client.post("/api/v1/content-personas", json={"name": "项目外作者"}, headers=HEADERS)
    assert other.status_code == 201, other.text
    response = client.get(f"/api/v1/content-projects/{project}/matrix/suggestions", headers=HEADERS)
    assert response.status_code == 200, response.text
    assert response.json()["items"]
    assert {item["personaId"] for item in response.json()["items"]} == {selected_persona}


def test_matrix_suggestions_respect_brief_identity_modality_and_channel_scope(client, db_session):
    project, _, _ = _ready_source(client, db_session)
    persona = client.post("/api/v1/content-personas", json={"name": "第二作者"}, headers=HEADERS)
    assert persona.status_code == 201, persona.text
    brief = client.post(f"/api/v1/content-projects/{project}/brief/revisions", json={
        "expected_revision": 1, "objective": "图文计划", "identity_scope": [{"persona_id": persona.json()["id"]}],
        "modality_scope": ["text"], "channel_scope": ["wechat"],
    }, headers=HEADERS)
    assert brief.status_code == 201, brief.text
    response = client.get(f"/api/v1/content-projects/{project}/matrix/suggestions", headers=HEADERS)
    assert response.status_code == 200, response.text
    assert len(response.json()["items"]) == 1
    item = response.json()["items"][0]
    assert (item["personaId"], item["modality"], item["channel"], item["contentForm"]) == (
        persona.json()["id"], "text", "wechat", "article")
    assert item["briefRevisionId"] == brief.json()["id"]


def test_matrix_history_uses_only_same_form_metric_coverage_without_cross_channel_score(client, db_session):
    project, _, _ = _ready_source(client, db_session)
    owner = db_session.scalar(select(User).where(User.email == HEADERS["X-Studio-User"]))
    record = PublishedContentRecord(owner_user_id=owner.id, origin="external_import", channel="wechat",
                                    content_form="article", status="active")
    db_session.add(record)
    db_session.flush()
    db_session.add(PerformanceObservation(published_content_id=record.id, observation_kind="metric",
                                          metric_namespace="wechat", metric_key="reads", numeric_value=120,
                                          observed_at=utcnow()))
    db_session.commit()
    response = client.get(f"/api/v1/content-projects/{project}/matrix/suggestions", headers=HEADERS)
    assert response.status_code == 200, response.text
    wechat = next(item for item in response.json()["items"] if item["channel"] == "wechat")
    assert wechat["historyCoverage"] == "known"
    assert wechat["historicalMetrics"] == [{"namespace": "wechat", "key": "reads", "sampleCount": 1}]
    assert wechat["estimatedValue"] == "unknown" and wechat["confidence"] == "unknown"


def test_v5_freeze_rejects_stale_variant_with_no_candidate_or_event(client, db_session):
    project, unit, master = _ready_source(client, db_session)
    old = _ready_variant(client, project, unit, master)
    path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    newer = client.post(path, json={
        "variant_key": "x.single.primary", "expected_revision": 1, "source_master_revision_id": master["id"],
        "expected_source_payload_hash": master["payload_hash"], "expected_source_context_hash": master["context_hash"],
        "channel_id": "x", "content_form": "single", "idempotency_key": "x.single.new",
        "source_kind": "manual_edit", "payload": {"text": "另一条观点"},
    }, headers=HEADERS)
    assert newer.status_code == 201, newer.text
    frozen = client.post(f"/api/v1/content-projects/{project}/units/{unit}/candidates/freeze", json={
        "channel_variant_revision_id": old["id"], "expected_payload_hash": old["payload_hash"],
    }, headers=HEADERS)
    assert frozen.status_code == 409, frozen.text
    assert not db_session.scalars(select(ContentAsset)).all()
    assert not db_session.scalars(select(ProjectEvent).where(ProjectEvent.event_type == "candidate.frozen")).all()


def test_v5_freeze_rechecks_live_evidence_after_checks(client, db_session):
    project, unit, master = _ready_source(client, db_session)
    variant = _ready_variant(client, project, unit, master)
    item = db_session.scalar(select(FactPackItem))
    item.public_use_revoked_at = utcnow()
    db_session.commit()
    response = client.post(f"/api/v1/content-projects/{project}/units/{unit}/candidates/freeze", json={
        "channel_variant_revision_id": variant["id"], "expected_payload_hash": variant["payload_hash"],
    }, headers=HEADERS)
    assert response.status_code == 409, response.text
    assert not db_session.scalars(select(ContentAsset)).all()


def test_v5_candidate_read_rejects_legacy_source_pointer_contamination(client, db_session):
    project, unit, master = _ready_source(client, db_session)
    variant = _ready_variant(client, project, unit, master)
    frozen = client.post(f"/api/v1/content-projects/{project}/units/{unit}/candidates/freeze", json={
        "channel_variant_revision_id": variant["id"], "expected_payload_hash": variant["payload_hash"],
    }, headers=HEADERS)
    assert frozen.status_code == 201, frozen.text
    candidate = db_session.get(ContentAsset, frozen.json()["id"])
    candidate.content_master_revision_id = master["id"]
    db_session.commit()
    read = client.get(f"/api/v1/content-projects/{project}/units/{unit}/candidates/{candidate.id}", headers=HEADERS)
    assert read.status_code == 409, read.text


def test_v5_candidates_in_different_series_can_be_approved_in_reverse_order(client, db_session):
    project, unit, master = _ready_source(client, db_session)
    single = _ready_variant(client, project, unit, master)
    thread = _ready_variant(client, project, unit, master, key="x.thread.primary", form="thread")
    freeze_path = f"/api/v1/content-projects/{project}/units/{unit}/candidates/freeze"
    frozen = []
    for variant in (single, thread):
        response = client.post(freeze_path, json={"channel_variant_revision_id": variant["id"],
                                                 "expected_payload_hash": variant["payload_hash"]}, headers=HEADERS)
        assert response.status_code == 201, response.text
        frozen.append(response.json())
    for candidate in frozen:
        response = client.post(
            f"/api/v1/content-projects/{project}/units/{unit}/candidates/{candidate['id']}/approve",
            json=_approval_payload(candidate), headers=HEADERS,
        )
        assert response.status_code == 200, response.text
        assert response.json()["status"] == "approved"
    assert len(db_session.scalars(select(Review).where(Review.decision == "approved")).all()) == 2


def test_v5_three_text_series_freeze_then_approve_and_authorize_in_reverse_order(client, db_session, tmp_path):
    project, unit, master = _ready_source(client, db_session, neutral=True)
    single = _ready_variant(client, project, unit, master)
    thread = _ready_variant(client, project, unit, master, key="x.thread.primary", form="thread")
    content = b"\x89PNG\r\n\x1a\nthree-series cover"
    file = tmp_path / "cover.png"
    file.write_bytes(content)
    material = Material(title="封面", kind="image", status="active")
    db_session.add(material)
    db_session.flush()
    cover = MaterialRevision(material_id=material.id, content_hash=hashlib.sha256(content).hexdigest(),
                             file_path=str(file), mime_type="image/png", status="active",
                             public_use_allowed=True, rights_status="cleared")
    db_session.add(cover)
    db_session.flush()
    db_session.add(ProjectMaterialReference(project_id=project, material_revision_id=cover.id,
                                            origin="system_library", status="active"))
    db_session.commit()
    variants = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    wechat = client.post(variants, json={"variant_key": "wechat.article.primary", "expected_revision": 0,
        "source_master_revision_id": master["id"], "expected_source_payload_hash": master["payload_hash"],
        "expected_source_context_hash": master["context_hash"], "channel_id": "wechat", "content_form": "article",
        "idempotency_key": "wechat.article.primary", "source_kind": "deterministic_adapt",
        "payload": {"title": "有来源的观点", "blocks": [{"id": "b1", "order": 0, "kind": "paragraph", "text": "这是观点"}]},
        "asset_refs": [{"material_revision_id": cover.id, "content_hash_snapshot": cover.content_hash,
                        "role": "cover", "slot_key": "cover", "sort_order": 0, "placement": {"usage": "cover"}}]}, headers=HEADERS)
    assert wechat.status_code == 201, wechat.text
    checked = client.post(f"{variants}/{wechat.json()['id']}/checks", headers=HEADERS)
    assert checked.status_code == 200 and checked.json()["ready"] is True, checked.text
    candidates = f"/api/v1/content-projects/{project}/units/{unit}/candidates"
    frozen = []
    for variant in (wechat.json(), thread, single):
        response = client.post(f"{candidates}/freeze", json={"channel_variant_revision_id": variant["id"],
            "expected_payload_hash": variant["payload_hash"]}, headers=HEADERS)
        assert response.status_code == 201, response.text
        frozen.append(response.json())
    targets = {}
    for candidate in reversed(frozen):
        approved = client.post(f"{candidates}/{candidate['id']}/approve", json=_approval_payload(candidate), headers=HEADERS)
        assert approved.status_code == 200, approved.text
        target = client.post(f"{candidates}/{candidate['id']}/delivery-authorizations", json={
            "channel": candidate["channel"], "content_form": candidate["content_form"],
            "account_ref": f"manual-{candidate['content_form']}", "authorization_version": "v1",
            "action": "copy_package"}, headers=HEADERS)
        assert target.status_code == 201, target.text
        targets[candidate["content_form"]] = target.json()
        assert client.get(f"/api/v1/delivery-targets/{target.json()['id']}/package.zip", headers=HEADERS).status_code == 200
    assert len(db_session.scalars(select(Review).where(Review.decision == "approved")).all()) == 3
    assert len(db_session.scalars(select(DeliveryTarget)).all()) == 3
    advanced = client.post(variants, json={"variant_key": "x.single.primary", "expected_revision": 1,
        "source_master_revision_id": master["id"], "expected_source_payload_hash": master["payload_hash"],
        "expected_source_context_hash": master["context_hash"], "channel_id": "x", "content_form": "single",
        "idempotency_key": "x.single.advanced", "source_kind": "manual_edit", "payload": {"text": "新版本观点"}}, headers=HEADERS)
    assert advanced.status_code == 201, advanced.text
    old_single = frozen[2]
    denied = client.post(f"{candidates}/{old_single['id']}/delivery-authorizations", json={
        "channel": "x", "content_form": "single", "account_ref": "manual-single",
        "authorization_version": "v2", "action": "copy_package"}, headers=HEADERS)
    assert denied.status_code == 409, denied.text
    for candidate in frozen[:2]:
        allowed = client.post(f"{candidates}/{candidate['id']}/delivery-authorizations", json={
            "channel": candidate["channel"], "content_form": candidate["content_form"],
            "account_ref": f"manual-{candidate['content_form']}", "authorization_version": "v2",
            "action": "copy_package"}, headers=HEADERS)
        assert allowed.status_code == 201, allowed.text
    assert client.get(f"/api/v1/delivery-targets/{targets['single']['id']}/package.zip", headers=HEADERS).status_code == 200


def test_v5_approval_rejects_candidate_after_its_series_advances(client, db_session):
    project, unit, master = _ready_source(client, db_session)
    old = _ready_variant(client, project, unit, master)
    freeze_path = f"/api/v1/content-projects/{project}/units/{unit}/candidates/freeze"
    frozen = client.post(freeze_path, json={"channel_variant_revision_id": old["id"],
                                            "expected_payload_hash": old["payload_hash"]}, headers=HEADERS)
    assert frozen.status_code == 201, frozen.text
    path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    newer = client.post(path, json={
        "variant_key": "x.single.primary", "expected_revision": 1, "source_master_revision_id": master["id"],
        "expected_source_payload_hash": master["payload_hash"], "expected_source_context_hash": master["context_hash"],
        "channel_id": "x", "content_form": "single", "idempotency_key": "x.single.new",
        "source_kind": "manual_edit", "payload": {"text": "另一条观点"},
    }, headers=HEADERS)
    assert newer.status_code == 201, newer.text
    decision = client.post(f"/api/v1/content-projects/{project}/units/{unit}/candidates/{frozen.json()['id']}/approve",
                           json={"candidate_hash": frozen.json()["candidate_hash"]}, headers=HEADERS)
    assert decision.status_code == 409, decision.text
    assert db_session.get(ContentAsset, frozen.json()["id"]).status == "frozen"
    assert not db_session.scalars(select(Review)).all()


@pytest.mark.parametrize("legacy_field", [
    "draft_id", "topic_brief_id", "mother_revision_id", "content_master_revision_id", "workflow_run_id",
])
def test_v5_approval_rejects_each_legacy_pointer(client, db_session, legacy_field):
    project, unit, master = _ready_source(client, db_session)
    variant = _ready_variant(client, project, unit, master)
    frozen = client.post(f"/api/v1/content-projects/{project}/units/{unit}/candidates/freeze", json={
        "channel_variant_revision_id": variant["id"], "expected_payload_hash": variant["payload_hash"],
    }, headers=HEADERS)
    assert frozen.status_code == 201, frozen.text
    asset = db_session.get(ContentAsset, frozen.json()["id"])
    setattr(asset, legacy_field, master["id"])
    db_session.commit()
    decision = client.post(f"/api/v1/content-projects/{project}/units/{unit}/candidates/{asset.id}/approve",
                           json={"candidate_hash": frozen.json()["candidate_hash"]}, headers=HEADERS)
    assert decision.status_code == 409, decision.text
    assert asset.status == "frozen" and not db_session.scalars(select(Review)).all()


def test_v5_approval_rechecks_revoked_evidence_without_mutating_frozen_candidate(client, db_session):
    project, unit, master = _ready_source(client, db_session)
    variant = _ready_variant(client, project, unit, master)
    frozen = client.post(f"/api/v1/content-projects/{project}/units/{unit}/candidates/freeze", json={
        "channel_variant_revision_id": variant["id"], "expected_payload_hash": variant["payload_hash"],
    }, headers=HEADERS)
    assert frozen.status_code == 201, frozen.text
    item = db_session.scalar(select(FactPackItem))
    item.public_use_revoked_at = utcnow()
    db_session.commit()
    decision = client.post(f"/api/v1/content-projects/{project}/units/{unit}/candidates/{frozen.json()['id']}/approve",
                           json={"candidate_hash": frozen.json()["candidate_hash"]}, headers=HEADERS)
    assert decision.status_code == 409, decision.text
    asset = db_session.get(ContentAsset, frozen.json()["id"])
    assert asset.status == "frozen" and asset.approved_candidate_hash is None


def test_v5_approved_series_can_authorize_separate_local_targets_in_any_order(client, db_session):
    project, unit, master = _ready_source(client, db_session)
    variants = (_ready_variant(client, project, unit, master),
                _ready_variant(client, project, unit, master, key="x.thread.primary", form="thread"))
    candidates = []
    for variant in variants:
        frozen = client.post(f"/api/v1/content-projects/{project}/units/{unit}/candidates/freeze", json={
            "channel_variant_revision_id": variant["id"], "expected_payload_hash": variant["payload_hash"],
        }, headers=HEADERS)
        assert frozen.status_code == 201, frozen.text
        candidate = frozen.json()
        approved = client.post(f"/api/v1/content-projects/{project}/units/{unit}/candidates/{candidate['id']}/approve",
                               json=_approval_payload(candidate), headers=HEADERS)
        assert approved.status_code == 200, approved.text
        candidates.append(candidate)
    targets = []
    for candidate in candidates:
        target = client.post(
            f"/api/v1/content-projects/{project}/units/{unit}/candidates/{candidate['id']}/delivery-authorizations",
            json={"channel": "x", "content_form": candidate["content_form"], "account_ref": "manual-x",
                  "authorization_version": "v1", "action": "copy_package"}, headers=HEADERS,
        )
        assert target.status_code == 201, target.text
        targets.append(target.json())
    assert len(db_session.scalars(select(DeliveryTarget)).all()) == 2
    for candidate, target in zip(candidates, targets, strict=True):
        download = client.get(f"/api/v1/delivery-targets/{target['id']}/package.zip", headers=HEADERS)
        assert download.status_code == 200, download.text
        with zipfile.ZipFile(io.BytesIO(download.content)) as archive:
            manifest = json.loads(archive.read("manifest.json"))
            assert manifest["schema_version"] == 5
            assert manifest["candidate"]["hash"] == candidate["candidate_hash"]
            assert manifest["target"]["content_form"] == candidate["content_form"]
            assert archive.read("content.md").decode() == candidate["manifest"]["render"]["text"]
            assert "publish-guide.md" in archive.namelist()


def test_v5_local_targets_keep_account_identity_and_unknown_reconciliation_separate(client, db_session):
    project, unit, master = _ready_source(client, db_session)
    persona = db_session.get(ContentUnit, unit).persona_id
    accounts = []
    for name in ("甲号", "乙号"):
        created = client.post(f"/api/v1/content-personas/{persona}/accounts", json={"name": name}, headers=HEADERS)
        assert created.status_code == 201, created.text
        accounts.append(created.json()["id"])
    variant = _ready_variant(client, project, unit, master)
    candidates = f"/api/v1/content-projects/{project}/units/{unit}/candidates"
    frozen = client.post(f"{candidates}/freeze", json={"channel_variant_revision_id": variant["id"],
        "expected_payload_hash": variant["payload_hash"]}, headers=HEADERS)
    assert frozen.status_code == 201, frozen.text
    candidate = frozen.json()
    approved = client.post(f"{candidates}/{candidate['id']}/approve", json=_approval_payload(candidate), headers=HEADERS)
    assert approved.status_code == 200, approved.text
    base = {"channel": "x", "content_form": "single", "account_ref": "shared-alias",
            "authorization_version": "v1", "action": "copy_package"}
    targets = []
    for account_id in accounts:
        target = client.post(f"{candidates}/{candidate['id']}/delivery-authorizations",
                             json={**base, "content_account_id": account_id}, headers=HEADERS)
        assert target.status_code == 201, target.text
        targets.append(target.json())
    assert targets[0]["id"] != targets[1]["id"]
    assert [target["content_account_id"] for target in targets] == accounts
    first = db_session.get(DeliveryTarget, targets[0]["id"])
    first.status = "reconciliation_needed"
    db_session.add(DeliveryAttempt(target_id=first.id, attempt_no=1, idempotency_key="u" * 64,
                                   status="unknown"))
    db_session.commit()
    overview = client.get(f"/api/v1/content-projects/{project}/overview", headers=HEADERS)
    assert overview.status_code == 200, overview.text
    assert overview.json()["nextAction"]["code"] == "delivery.reconcile"
    assert client.get(f"/api/v1/delivery-targets/{targets[0]['id']}", headers=HEADERS).json()["status"] == "reconciliation_needed"
    assert client.get(f"/api/v1/delivery-targets/{targets[1]['id']}", headers=HEADERS).json()["status"] == "target_authorized"
    assert client.get(f"/api/v1/delivery-targets/{targets[1]['id']}/package.zip", headers=HEADERS).status_code == 200


def test_v5_raw_ids_remain_project_scoped_and_archived_history_is_read_only(client, db_session):
    project, unit, master = _ready_source(client, db_session)
    variant = _ready_variant(client, project, unit, master)
    candidates = f"/api/v1/content-projects/{project}/units/{unit}/candidates"
    frozen = client.post(f"{candidates}/freeze", json={
        "channel_variant_revision_id": variant["id"], "expected_payload_hash": variant["payload_hash"],
    }, headers=HEADERS)
    assert frozen.status_code == 201, frozen.text
    candidate = frozen.json()
    approved = client.post(f"{candidates}/{candidate['id']}/approve", json=_approval_payload(candidate), headers=HEADERS)
    assert approved.status_code == 200, approved.text
    authorized = client.post(f"{candidates}/{candidate['id']}/delivery-authorizations", json={
        "channel": "x", "content_form": "single", "account_ref": "manual-x",
        "authorization_version": "v1", "action": "copy_package"}, headers=HEADERS)
    assert authorized.status_code == 201, authorized.text
    variant_url = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants/{variant['id']}"
    candidate_url = f"{candidates}/{candidate['id']}"
    package_url = f"/api/v1/delivery-targets/{authorized.json()['id']}/package.zip"
    foreign = {"X-Studio-User": "foreign-v5@studio.local"}
    for url in (variant_url, candidate_url, package_url):
        assert client.get(url, headers=foreign).status_code == 404
    assert client.post(f"{candidates}/freeze", json={
        "channel_variant_revision_id": variant["id"], "expected_payload_hash": variant["payload_hash"],
    }, headers=foreign).status_code == 404

    db_session.get(ContentProject, project).status = "archived"
    db_session.commit()
    assert client.get(variant_url, headers=HEADERS).status_code == 200
    assert client.get(candidate_url, headers=HEADERS).status_code == 200
    assert client.post(f"{candidates}/freeze", json={
        "channel_variant_revision_id": variant["id"], "expected_payload_hash": variant["payload_hash"],
    }, headers=HEADERS).status_code == 409
    assert client.post(f"{candidate_url}/approve", json={
        "candidate_hash": candidate["candidate_hash"]}, headers=HEADERS).status_code == 409
    assert client.post(f"{candidate_url}/delivery-authorizations", json={
        "channel": "x", "content_form": "single", "account_ref": "manual-x",
        "authorization_version": "v2", "action": "copy_package"}, headers=HEADERS).status_code == 409
    assert client.post(f"/api/v1/content-projects/{project}/units/{unit}/channel-variants/{variant['id']}/checks",
                       headers=HEADERS).status_code == 409
    assert client.get(package_url, headers=HEADERS).status_code == 409


def test_v5_existing_authorized_package_survives_new_variant_revision(client, db_session):
    project, unit, master = _ready_source(client, db_session)
    variant = _ready_variant(client, project, unit, master)
    candidate_path = f"/api/v1/content-projects/{project}/units/{unit}/candidates"
    frozen = client.post(f"{candidate_path}/freeze", json={"channel_variant_revision_id": variant["id"],
                                                          "expected_payload_hash": variant["payload_hash"]}, headers=HEADERS)
    assert frozen.status_code == 201, frozen.text
    candidate = frozen.json()
    approved = client.post(f"{candidate_path}/{candidate['id']}/approve",
                           json=_approval_payload(candidate), headers=HEADERS)
    assert approved.status_code == 200, approved.text
    target_payload = {"channel": "x", "content_form": "single", "account_ref": "manual-x",
                      "authorization_version": "v1", "action": "copy_package"}
    authorized = client.post(f"{candidate_path}/{candidate['id']}/delivery-authorizations",
                             json=target_payload, headers=HEADERS)
    assert authorized.status_code == 201, authorized.text
    newer = client.post(f"/api/v1/content-projects/{project}/units/{unit}/channel-variants", json={
        "variant_key": "x.single.primary", "expected_revision": 1, "source_master_revision_id": master["id"],
        "expected_source_payload_hash": master["payload_hash"], "expected_source_context_hash": master["context_hash"],
        "channel_id": "x", "content_form": "single", "idempotency_key": "x.single.new",
        "source_kind": "manual_edit", "payload": {"text": "另一条观点"},
    }, headers=HEADERS)
    assert newer.status_code == 201, newer.text
    denied = client.post(f"{candidate_path}/{candidate['id']}/delivery-authorizations",
                         json={**target_payload, "authorization_version": "v2"}, headers=HEADERS)
    assert denied.status_code == 409, denied.text
    package = client.get(f"/api/v1/delivery-targets/{authorized.json()['id']}/package.zip", headers=HEADERS)
    assert package.status_code == 200, package.text
    with zipfile.ZipFile(io.BytesIO(package.content)) as archive:
        assert archive.read("content.md").decode() == "这是观点"


def test_existing_v4_authorized_package_survives_v5_candidate_on_same_unit(client, db_session):
    project, unit, master = _ready_source(client, db_session)
    candidates = f"/api/v1/content-projects/{project}/units/{unit}/candidates"
    legacy = client.post(f"{candidates}/freeze", json={"content_master_revision_id": master["id"],
        "expected_payload_hash": master["payload_hash"]}, headers=HEADERS)
    assert legacy.status_code == 201, legacy.text
    old = legacy.json()
    dispositions = {f"{row['id']}:{row['input_hash']}": "编辑已核对该提示"
                    for row in old["manifest"]["checks"] if row["status"] == "warning"}
    approved_old = client.post(f"{candidates}/{old['id']}/approve", json={
        "candidate_hash": old["candidate_hash"], "warning_dispositions": dispositions}, headers=HEADERS)
    assert approved_old.status_code == 200, approved_old.text
    old_target = client.post(f"{candidates}/{old['id']}/delivery-authorizations", json={
        "channel": "x", "content_form": "single", "account_ref": "manual-x", "authorization_version": "v1",
        "action": "copy_package"}, headers=HEADERS)
    assert old_target.status_code == 201, old_target.text
    variant = _ready_variant(client, project, unit, master)
    new = client.post(f"{candidates}/freeze", json={"channel_variant_revision_id": variant["id"],
        "expected_payload_hash": variant["payload_hash"]}, headers=HEADERS)
    assert new.status_code == 201, new.text
    assert new.json()["manifest"]["schema_version"] == 5
    assert old["manifest"]["schema_version"] == 4
    assert db_session.get(ContentAsset, old["id"]).channel_variant_revision_id is None
    old_read = client.get(f"{candidates}/{old['id']}", headers=HEADERS)
    assert old_read.status_code == 200 and old_read.json()["manifest"]["schema_version"] == 4, old_read.text
    variant_rows = client.get(f"/api/v1/content-projects/{project}/units/{unit}/channel-variants", headers=HEADERS)
    assert variant_rows.status_code == 200 and len(variant_rows.json()["items"]) == 1, variant_rows.text
    historical = client.get(f"/api/v1/delivery-targets/{old_target.json()['id']}/package.zip", headers=HEADERS)
    assert historical.status_code == 200, historical.text
    with zipfile.ZipFile(io.BytesIO(historical.content)) as archive:
        assert json.loads(archive.read("manifest.json"))["schema_version"] == 4
    next_auth = client.post(f"{candidates}/{old['id']}/delivery-authorizations", json={
        "channel": "x", "content_form": "single", "account_ref": "manual-x", "authorization_version": "v2",
        "action": "copy_package"}, headers=HEADERS)
    assert next_auth.status_code == 201, next_auth.text
    review = client.get(f"/api/v1/review-center/projects/{project}/units/{unit}", headers=HEADERS)
    assert review.status_code == 200, review.text
    assert review.json()["legacy_current_candidate"]["id"] == old["id"]
    versions = client.get(f"/api/v1/content-projects/{project}/versions", headers=HEADERS)
    assert versions.status_code == 200, versions.text
    assert next(row for row in versions.json()["candidates"] if row["id"] == str(old["id"]))["current"] is True


def test_v5_wechat_package_uses_exact_cover_and_blocks_revoked_rights(client, db_session, tmp_path):
    project, unit, master = _ready_source(client, db_session)
    content = b"\x89PNG\r\n\x1a\nverified cover bytes"
    file = tmp_path / "cover.png"
    file.write_bytes(content)
    material = Material(title="封面", kind="image", status="active")
    db_session.add(material)
    db_session.flush()
    revision = MaterialRevision(material_id=material.id, content_hash=hashlib.sha256(content).hexdigest(),
                                file_path=str(file), mime_type="image/png", status="active",
                                public_use_allowed=True, rights_status="cleared")
    db_session.add(revision)
    db_session.flush()
    db_session.add(ProjectMaterialReference(project_id=project, material_revision_id=revision.id,
                                            origin="system_library", status="active"))
    db_session.commit()
    variants = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    saved = client.post(variants, json={
        "variant_key": "wechat.article.primary", "expected_revision": 0,
        "source_master_revision_id": master["id"], "expected_source_payload_hash": master["payload_hash"],
        "expected_source_context_hash": master["context_hash"], "channel_id": "wechat", "content_form": "article",
        "idempotency_key": "wechat.article.primary", "source_kind": "deterministic_adapt",
        "payload": {"title": "有来源的观点", "blocks": [{"id": "b1", "order": 0, "kind": "paragraph", "text": "这是观点"}]},
        "asset_refs": [{"material_revision_id": revision.id, "content_hash_snapshot": revision.content_hash,
                        "role": "cover", "slot_key": "cover", "sort_order": 0, "placement": {"usage": "cover"}}],
    }, headers=HEADERS)
    assert saved.status_code == 201, saved.text
    checks = client.post(f"{variants}/{saved.json()['id']}/checks", headers=HEADERS)
    assert checks.status_code == 200 and checks.json()["ready"] is True, checks.text
    candidates = f"/api/v1/content-projects/{project}/units/{unit}/candidates"
    frozen = client.post(f"{candidates}/freeze", json={"channel_variant_revision_id": saved.json()["id"],
                                                   "expected_payload_hash": saved.json()["payload_hash"]}, headers=HEADERS)
    assert frozen.status_code == 201, frozen.text
    candidate = frozen.json()
    approved = client.post(f"{candidates}/{candidate['id']}/approve",
                           json=_approval_payload(candidate), headers=HEADERS)
    assert approved.status_code == 200, approved.text
    target = client.post(f"{candidates}/{candidate['id']}/delivery-authorizations", json={
        "channel": "wechat", "content_form": "article", "account_ref": "manual-wechat",
        "authorization_version": "v1", "action": "copy_package",
    }, headers=HEADERS)
    assert target.status_code == 201, target.text
    package_path = f"/api/v1/delivery-targets/{target.json()['id']}/package.zip"
    package = client.get(package_path, headers=HEADERS)
    assert package.status_code == 200, package.text
    with zipfile.ZipFile(io.BytesIO(package.content)) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["schema_version"] == 5
        assert any(archive.read(name) == content for name in archive.namelist() if name.endswith(".png"))
    render_path = (f"/api/v1/review-center/projects/{project}/units/{unit}"
                   f"/candidates/{candidate['id']}/renders/{revision.id}")
    preview_media = client.get(render_path, headers=HEADERS)
    assert preview_media.status_code == 200, preview_media.text
    assert preview_media.content == content
    assert preview_media.headers["content-type"] == "image/png"
    assert preview_media.headers["cache-control"] == "private, no-store"
    unrelated = client.get(render_path.replace(f"/renders/{revision.id}", "/renders/999999"), headers=HEADERS)
    assert unrelated.status_code == 404
    revision.public_use_allowed = False
    db_session.commit()
    denied = client.get(package_path, headers=HEADERS)
    assert denied.status_code in (403, 409, 422), denied.text
    assert client.get(render_path, headers=HEADERS).status_code in (403, 409)


@pytest.mark.parametrize("cover_mime,signature", [("image/png", b"\x89PNG\r\n\x1a\n"), ("image/jpeg", b"\xff\xd8\xff")])
def test_f7_v5_wechat_verified_projection_precedes_attempt_and_uses_frozen_bytes(
    client, db_session, tmp_path, monkeypatch, cover_mime, signature,
):
    project, unit, master = _ready_source(client, db_session)
    persona_id = db_session.get(ContentUnit, unit).persona_id
    account = ContentAccount(persona_id=persona_id, name="公众号账号", status="active")
    db_session.add(account)
    cover_bytes = signature + b"verified cover bytes"
    cover_path = tmp_path / "approved-cover.png"
    cover_path.write_bytes(cover_bytes)
    material = Material(title="封面", kind="image", status="active")
    db_session.add(material)
    db_session.flush()
    revision = MaterialRevision(material_id=material.id, content_hash=hashlib.sha256(cover_bytes).hexdigest(),
                                file_path=str(cover_path), mime_type=cover_mime, status="active",
                                public_use_allowed=True, rights_status="cleared")
    db_session.add(revision)
    db_session.flush()
    db_session.add(ProjectMaterialReference(project_id=project, material_revision_id=revision.id,
                                            origin="system_library", status="active"))
    db_session.commit()
    variants = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    saved = client.post(variants, json={
        "variant_key": "wechat.article.primary", "expected_revision": 0,
        "source_master_revision_id": master["id"], "expected_source_payload_hash": master["payload_hash"],
        "expected_source_context_hash": master["context_hash"], "channel_id": "wechat", "content_form": "article",
        "idempotency_key": "wechat.article.primary", "source_kind": "deterministic_adapt",
        "payload": {"title": "有来源的观点", "blocks": [{"id": "b1", "order": 0, "kind": "paragraph", "text": "这是观点"}]},
        "asset_refs": [{"material_revision_id": revision.id, "content_hash_snapshot": revision.content_hash,
                        "role": "cover", "slot_key": "cover", "sort_order": 0, "placement": {"usage": "cover"}}],
    }, headers=HEADERS)
    assert saved.status_code == 201, saved.text
    assert client.post(f"{variants}/{saved.json()['id']}/checks", headers=HEADERS).json()["ready"] is True
    candidates = f"/api/v1/content-projects/{project}/units/{unit}/candidates"
    frozen = client.post(f"{candidates}/freeze", json={"channel_variant_revision_id": saved.json()["id"],
                                                    "expected_payload_hash": saved.json()["payload_hash"]}, headers=HEADERS)
    assert frozen.status_code == 201, frozen.text
    candidate = frozen.json()
    assert client.post(f"{candidates}/{candidate['id']}/approve", json=_approval_payload(candidate), headers=HEADERS).status_code == 200
    auth_url = f"{candidates}/{candidate['id']}/delivery-authorizations"
    auth_body = {"channel": "wechat", "content_form": "article", "content_account_id": account.id,
                 "account_ref": "verified-wechat", "authorization_version": "v1", "action": "auto_draft"}
    denied = client.post(auth_url, json=auth_body, headers=HEADERS)
    assert denied.status_code in (409, 422), denied.text
    assert db_session.scalars(select(DeliveryAttempt)).all() == []
    monkeypatch.setenv("WEWRITE_CREDENTIAL_VERSION", "credential-v1")
    monkeypatch.setenv("WEWRITE_BINARY_VERSION", "binary-v1")
    fingerprint = hashlib.sha256(json.dumps({
        "publisher_key": "publisher.wechat.wewrite", "publisher_version": "1",
        "credential_version": "credential-v1", "binary_version": "binary-v1",
        "executable": "/verified/wewrite",
    }, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    monkeypatch.setattr(capability_integrations, "publisher_runtime_fingerprint", lambda *args: fingerprint)
    registration = CapabilityRegistration(kind="publisher", key="publisher.wechat.wewrite", version="1",
                                          status="configured", config_fingerprint=fingerprint)
    db_session.add(registration)
    db_session.flush()
    scope = {"channel": "wechat", "content_form": "article", "action": "auto_draft",
             "content_account_id": account.id, "account_ref": "verified-wechat",
             "publisher_key": "publisher.wechat.wewrite", "publisher_version": "1"}
    capability_integrations.append_verification(db_session, registration, scope_kind="publisher_action", scope=scope,
                                                 result="verified", actor=HEADERS["X-Studio-User"],
                                                 evidence={"kind": "human_readback", "reference_hash": "a" * 64})
    db_session.commit()
    authorized = client.post(auth_url, json=auth_body, headers=HEADERS)
    assert authorized.status_code == 201, authorized.text
    capability_integrations.append_verification(db_session, registration, scope_kind="publisher_action", scope=scope,
                                                 result="revoked", actor=HEADERS["X-Studio-User"],
                                                 evidence={"kind": "revocation"})
    db_session.commit()
    revoked_execute = client.post(f"/api/v1/delivery-targets/{authorized.json()['id']}/execute", headers=HEADERS)
    assert revoked_execute.status_code == 409, revoked_execute.text
    assert db_session.scalars(select(DeliveryAttempt)).all() == []
    capability_integrations.append_verification(db_session, registration, scope_kind="publisher_action", scope=scope,
                                                 result="verified", actor=HEADERS["X-Studio-User"],
                                                 evidence={"kind": "human_readback", "reference_hash": "b" * 64})
    db_session.commit()
    seen = []

    def fake_deliver(_publisher, manifest, _target, _attempt):
        seen.append(manifest)
        return PublisherResult(status="unknown", error="publisher_result_unconfirmed")

    monkeypatch.setattr(WechatWewritePublisher, "deliver", fake_deliver)
    executed = client.post(f"/api/v1/delivery-targets/{authorized.json()['id']}/execute", headers=HEADERS)
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "unknown"
    assert len(seen) == 1
    assert seen[0]["render"]["payload"] == {
        "title": "有来源的观点", "digest": "有来源的观点", "markdown": candidate["manifest"]["render"]["text"]}
    assert seen[0]["_cover_bytes"] == cover_bytes
    replay = client.post(f"/api/v1/delivery-targets/{authorized.json()['id']}/execute", headers=HEADERS)
    assert replay.status_code == 409, replay.text
    assert len(seen) == 1
    attempt = db_session.scalars(select(DeliveryAttempt)).all()[0]
    request_input = {"payload": seen[0]["render"]["payload"], "cover_hash": revision.content_hash}
    expected_request_hash = hashlib.sha256(("\x1f".join((json.dumps(request_input, ensure_ascii=False,
                                                                          sort_keys=True, default=str),))).encode()).hexdigest()
    assert attempt.request_hash == expected_request_hash


@pytest.mark.parametrize("legacy_field", [
    "draft_id", "topic_brief_id", "mother_revision_id", "content_master_revision_id", "workflow_run_id",
])
def test_v5_legacy_pointer_contamination_blocks_new_authorization_and_existing_package(client, db_session, legacy_field):
    project, unit, master = _ready_source(client, db_session)
    variant = _ready_variant(client, project, unit, master)
    candidates = f"/api/v1/content-projects/{project}/units/{unit}/candidates"
    frozen = client.post(f"{candidates}/freeze", json={"channel_variant_revision_id": variant["id"],
                                                   "expected_payload_hash": variant["payload_hash"]}, headers=HEADERS)
    assert frozen.status_code == 201, frozen.text
    candidate = frozen.json()
    approved = client.post(f"{candidates}/{candidate['id']}/approve",
                           json=_approval_payload(candidate), headers=HEADERS)
    assert approved.status_code == 200, approved.text
    payload = {"channel": "x", "content_form": "single", "account_ref": "manual-x",
               "authorization_version": "v1", "action": "copy_package"}
    target = client.post(f"{candidates}/{candidate['id']}/delivery-authorizations", json=payload, headers=HEADERS)
    assert target.status_code == 201, target.text
    asset = db_session.get(ContentAsset, candidate["id"])
    setattr(asset, legacy_field, master["id"])
    db_session.commit()
    denied_auth = client.post(f"{candidates}/{candidate['id']}/delivery-authorizations",
                              json={**payload, "authorization_version": "v2"}, headers=HEADERS)
    assert denied_auth.status_code == 409, denied_auth.text
    denied_package = client.get(f"/api/v1/delivery-targets/{target.json()['id']}/package.zip", headers=HEADERS)
    assert denied_package.status_code == 409, denied_package.text
    assert len(db_session.scalars(select(DeliveryTarget)).all()) == 1


def test_v5_review_reads_frozen_text_and_checks_without_mutable_master_fallback(client, db_session):
    project, unit, master = _ready_source(client, db_session)
    variant = _ready_variant(client, project, unit, master)
    frozen = client.post(f"/api/v1/content-projects/{project}/units/{unit}/candidates/freeze", json={
        "channel_variant_revision_id": variant["id"], "expected_payload_hash": variant["payload_hash"],
    }, headers=HEADERS)
    assert frozen.status_code == 201, frozen.text
    review_path = f"/api/v1/review-center/projects/{project}/units/{unit}/candidates/{frozen.json()['id']}"
    review = client.get(review_path, headers=HEADERS)
    assert review.status_code == 200, review.text
    preview = review.json()["preview"]
    assert preview["modality"] == "text"
    assert preview["markdown"] == "这是观点"
    assert preview["target"] == {"channel": "x", "content_form": "single", "artifact_kind": "text"}
    assert {row["kind"] for row in preview["checks"]} == {row["kind"] for row in frozen.json()["manifest"]["checks"]}


def test_v5_review_diff_uses_same_variant_series_and_frozen_render(client, db_session):
    project, unit, master = _ready_source(client, db_session)
    single = _ready_variant(client, project, unit, master)
    candidates = f"/api/v1/content-projects/{project}/units/{unit}/candidates"
    first = client.post(f"{candidates}/freeze", json={"channel_variant_revision_id": single["id"],
                                                  "expected_payload_hash": single["payload_hash"]}, headers=HEADERS)
    assert first.status_code == 201, first.text
    thread = _ready_variant(client, project, unit, master, key="x.thread.primary", form="thread")
    other = client.post(f"{candidates}/freeze", json={"channel_variant_revision_id": thread["id"],
                                                  "expected_payload_hash": thread["payload_hash"]}, headers=HEADERS)
    assert other.status_code == 201, other.text
    master_path = f"/api/v1/content-projects/{project}/units/{unit}/master-revisions"
    next_master = client.post(master_path, json={
        "idempotency_key": "second-source", "expected_revision": 1, "payload_schema": "text.master.v2",
        "content_form": "single", "payload": {"title": "有来源的观点", "document": {
            "schema": "studio.text.document.v1", "blocks": [
                {"id": "b1", "type": "paragraph", "content": [{"text": "第二条观点", "marks": []}]},
            ], "citations": [],
        }},
    }, headers=HEADERS)
    assert next_master.status_code == 200, next_master.text
    master = next_master.json()
    master_checks = client.post(f"{master_path}/{master['id']}/checks", headers=HEADERS)
    assert master_checks.status_code == 200, master_checks.text
    variant_path = f"/api/v1/content-projects/{project}/units/{unit}/channel-variants"
    updated = client.post(variant_path, json={
        "variant_key": "x.single.primary", "expected_revision": 1, "source_master_revision_id": master["id"],
        "expected_source_payload_hash": master["payload_hash"], "expected_source_context_hash": master["context_hash"],
        "channel_id": "x", "content_form": "single", "idempotency_key": "x.single.second",
        "source_kind": "deterministic_adapt", "payload": {"text": "第二条观点"},
    }, headers=HEADERS)
    assert updated.status_code == 201, updated.text
    checks = client.post(f"{variant_path}/{updated.json()['id']}/checks", headers=HEADERS)
    assert checks.status_code == 200 and checks.json()["ready"] is True, checks.text
    second = client.post(f"{candidates}/freeze", json={"channel_variant_revision_id": updated.json()["id"],
                                                   "expected_payload_hash": updated.json()["payload_hash"]}, headers=HEADERS)
    assert second.status_code == 201, second.text
    diff_path = f"/api/v1/review-center/projects/{project}/units/{unit}/candidates/{second.json()['id']}/diff"
    diff = client.get(diff_path, headers=HEADERS)
    assert diff.status_code == 200, diff.text
    result = diff.json()
    assert result["from_candidate_id"] == first.json()["id"]
    assert result["to_candidate_id"] == second.json()["id"]
    assert result["text"]["before_chars"] == len("这是观点")
    assert result["text"]["after_chars"] == len("第二条观点")
    assert result["text"]["similarity"] < 1
    assert result["changed_sections"]["content"]["changed"] is True


@pytest.mark.parametrize("legacy_field", [
    "draft_id", "topic_brief_id", "mother_revision_id", "content_master_revision_id", "workflow_run_id",
])
def test_v5_review_diff_rejects_legacy_source_pointer_contamination(client, db_session, legacy_field):
    project, unit, master = _ready_source(client, db_session)
    variant = _ready_variant(client, project, unit, master)
    frozen = client.post(f"/api/v1/content-projects/{project}/units/{unit}/candidates/freeze", json={
        "channel_variant_revision_id": variant["id"], "expected_payload_hash": variant["payload_hash"],
    }, headers=HEADERS)
    assert frozen.status_code == 201, frozen.text
    asset = db_session.get(ContentAsset, frozen.json()["id"])
    setattr(asset, legacy_field, master["id"])
    db_session.commit()
    response = client.get(f"/api/v1/review-center/projects/{project}/units/{unit}/candidates/{asset.id}/diff", headers=HEADERS)
    assert response.status_code == 409, response.text


def test_v5_structured_diff_identifies_order_and_content_changes_without_fake_text_similarity():
    from app.services.project_review_projection import diff_variant_rows

    before = [{"id": "a", "order": 0, "caption": "旧说明"}, {"id": "b", "order": 1, "caption": "保留"}]
    after = [{"id": "b", "order": 0, "caption": "保留"}, {"id": "a", "order": 1, "caption": "新说明"},
             {"id": "c", "order": 2, "caption": "新增"}]
    changes = diff_variant_rows(before, after)
    assert {row["id"]: row["changes"] for row in changes} == {
        "b": ["move"], "a": ["move", "modify"], "c": ["add"],
    }
