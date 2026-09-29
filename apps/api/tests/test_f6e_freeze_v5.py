"""A ready post-adaptation Variant is the sole source of a v5 Candidate."""

from sqlalchemy import select

from app.models import ContentAsset, FactPack, FactPackItem, ProjectEvent, utcnow
from app.seed import seed_v1_channel_profiles

HEADERS = {"X-Studio-User": "v5-freeze@studio.local"}


def _ready_source(client, db):
    seed_v1_channel_profiles(db)
    db.commit()
    persona = client.post("/api/v1/content-personas", json={"name": "作者"}, headers=HEADERS).json()["id"]
    project = client.post("/api/v1/content-projects", json={"title": "渠道成品"}, headers=HEADERS).json()["id"]
    unit_response = client.post(f"/api/v1/content-projects/{project}/units", json={
        "title": "源稿", "persona_id": persona, "modality": "text", "channel_id": "x",
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
    db.add(FactPackItem(fact_pack_id=pack.id, evidence_kind="author_opinion",
                        snapshot_json={"statement": "这是观点"}, snapshot_checksum="d" * 64,
                        public_use_allowed=True, model_use_allowed=True))
    db.commit()
    boundary = client.post(f"/api/v1/content-projects/{project}/fact-boundary", json={
        "fact_pack_id": pack.id, "expected_revision": 0,
    }, headers=HEADERS)
    assert boundary.status_code == 201, boundary.text
    master_path = f"/api/v1/content-projects/{project}/units/{unit}/master-revisions"
    master = client.post(master_path, json={
        "idempotency_key": "v5-source", "payload_schema": "text.master.v2", "content_form": "single",
        "payload": {"title": "有来源的观点", "document": {"schema": "studio.text.document.v1", "blocks": [
            {"id": "b1", "type": "paragraph", "content": [{"text": "这是观点", "marks": []}]},
        ], "citations": []}},
    }, headers=HEADERS)
    assert master.status_code == 200, master.text
    checks = client.post(f"{master_path}/{master.json()['id']}/checks", headers=HEADERS)
    assert checks.status_code == 200, checks.text
    return project, unit, master.json()


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
