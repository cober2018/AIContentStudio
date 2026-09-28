"""Master-only freeze never fabricates Draft/Topic lineage."""

import pytest
from test_f6a_modality_adapters import HEADERS, _draft_render, _unit

from app.models import ContentAsset, FactPackItem, ProjectEvent, utcnow


def _ready(client, db):
    _, path = _unit(client, db, "text")
    master = client.post(path, json={"idempotency_key": "text", "payload": {"markdown": "独立手工成品"}}, headers=HEADERS).json()
    client.post(f"{path}/{master['id']}/checks", headers=HEADERS)
    return path, master


def _freeze(client, path, master, **overrides):
    return client.post(path.replace("master-revisions", "candidates/freeze"), json={"content_master_revision_id": master["id"], "expected_payload_hash": master["payload_hash"], **overrides}, headers=HEADERS)


def test_manual_text_freeze_uses_full_v4_and_repeats_one_candidate_event(client, db_session):
    path, master = _ready(client, db_session)
    response = _freeze(client, path, master)
    assert response.status_code == 201, response.text
    asset = db_session.get(ContentAsset, response.json()["id"])
    assert asset.draft_id is None and asset.topic_brief_id is None and asset.mother_revision_id is None
    assert asset.workflow_run_id is None
    assert asset.candidate_manifest_json["identity"]["checksum"]
    assert asset.candidate_manifest_json["content_master"]["id"] == master["id"]
    assert asset.final_body == "独立手工成品"
    assert _freeze(client, path, master).json()["id"] == asset.id
    assert db_session.query(ProjectEvent).filter_by(event_type="candidate.frozen").count() == 1


@pytest.mark.parametrize("problem", ["hash", "missing_hash", "brief", "latest", "evidence", "latest_check"])
def test_freeze_fails_closed_on_changed_inputs(client, db_session, problem):
    from app.models import ContentMasterCheckRun

    path, master = _ready(client, db_session)
    overrides = {}
    if problem == "hash":
        overrides["expected_payload_hash"] = "0" * 64
    elif problem == "missing_hash":
        overrides["expected_payload_hash"] = None
    elif problem == "brief":
        client.post(f"/api/v1/content-projects/{path.split('/')[4]}/brief/revisions", json={"expected_revision": 1, "objective": "已更改"}, headers=HEADERS)
    elif problem == "latest":
        client.post(path, json={"idempotency_key": "new", "expected_revision": 1, "payload": master["payload"]}, headers=HEADERS)
    elif problem == "evidence":
        db_session.query(FactPackItem).one().public_use_revoked_at = utcnow()
        db_session.commit()
    else:
        check = db_session.query(ContentMasterCheckRun).filter_by(master_revision_id=master["id"], check_kind="rights").one()
        db_session.add(ContentMasterCheckRun(master_revision_id=master["id"], check_kind="rights", profile_key=check.profile_key, profile_version=check.profile_version, input_hash=check.input_hash, status="blocker", report_json={"reasons": ["new_blocker"]}))
        db_session.commit()
    response = _freeze(client, path, master, **overrides)
    assert response.status_code == (422 if problem == "missing_hash" else 409), response.text
    assert db_session.query(ContentAsset).count() == 0


@pytest.mark.parametrize("modality", ["graphic", "video"])
def test_verified_manual_render_freezes_without_legacy_fallback(client, db_session, tmp_path, modality):
    path, body, readiness, _ = _draft_render(client, db_session, tmp_path, modality)
    master = client.post(path, json={**body, "idempotency_key": "confirm", "expected_revision": 1, "render_attestation": {"confirmed": True, "render_input_hash": readiness["render_input_hash"]}}, headers=HEADERS).json()
    client.post(f"{path}/{master['id']}/checks", headers=HEADERS)
    response = _freeze(client, path, master)
    assert response.status_code == 201, response.text
    assert response.json()["manifest"]["render"]["origin"] == "manual"
    assert response.json()["artifact_kind"] == ("image" if modality == "graphic" else "video")
    assert db_session.get(ContentAsset, response.json()["id"]).final_body is None


def test_freeze_commit_context_change_rolls_back_candidate_and_event(client, db_session):
    from sqlalchemy import event

    from app.models import CreativeBriefRevision

    path, master = _ready(client, db_session)
    injected = False

    def change_context(session, flush_context, instances):
        nonlocal injected
        if not injected and any(isinstance(row, ContentAsset) for row in session.new):
            injected = True
            prior = session.query(CreativeBriefRevision).one()
            session.add(CreativeBriefRevision(project_id=prior.project_id, revision_no=2, objective="并发新上下文", checksum="c" * 64))

    event.listen(db_session, "before_flush", change_context)
    try:
        response = _freeze(client, path, master)
    finally:
        event.remove(db_session, "before_flush", change_context)
    assert response.status_code == 409, response.text
    assert db_session.query(ContentAsset).count() == 0
    assert db_session.query(ProjectEvent).filter_by(event_type="candidate.frozen").count() == 0


def test_v4_freeze_denies_foreign_owner_and_archived_unit(client, db_session):
    from app.models import ContentUnit

    path, master = _ready(client, db_session)
    response = client.post(path.replace("master-revisions", "candidates/freeze"), json={"content_master_revision_id": master["id"], "expected_payload_hash": master["payload_hash"]}, headers={"X-Studio-User": "foreign@studio.local"})
    assert response.status_code == 404, response.text
    db_session.get(ContentUnit, int(path.split("/")[6])).status = "archived"
    db_session.commit()
    assert _freeze(client, path, master).status_code == 409


def test_changed_evidence_snapshot_cannot_be_cleared_by_rerunning_checks(client, db_session):
    _, path = _unit(client, db_session, "text")
    item = db_session.query(FactPackItem).one()
    master = client.post(path, json={"idempotency_key": "evidence", "payload": {"markdown": "观点"}, "evidence_refs": [{"fact_pack_item_id": item.id, "snapshot_checksum": item.snapshot_checksum}]}, headers=HEADERS).json()
    item.snapshot_checksum = "changed" * 9
    db_session.commit()
    checks = client.post(f"{path}/{master['id']}/checks", headers=HEADERS).json()["items"]
    assert next(check for check in checks if check["check_kind"] == "evidence")["status"] == "blocker"
    assert _freeze(client, path, master).status_code == 409


def test_new_master_freeze_preserves_prior_candidate(client, db_session):
    from copy import deepcopy

    path, first = _ready(client, db_session)
    frozen = _freeze(client, path, first).json()
    snapshot = deepcopy(frozen["manifest"])
    second = client.post(path, json={"idempotency_key": "new-master", "expected_revision": 1, "payload": {"markdown": "下一版"}}, headers=HEADERS).json()
    client.post(f"{path}/{second['id']}/checks", headers=HEADERS)
    next_candidate = _freeze(client, path, second).json()
    assert next_candidate["id"] != frozen["id"]
    assert db_session.get(ContentAsset, frozen["id"]).candidate_manifest_json == snapshot
    assert db_session.get(ContentAsset, frozen["id"]).candidate_hash == frozen["candidate_hash"]
    assert _freeze(client, path, first).status_code == 409


def test_two_sessions_freeze_identical_master_once(client, db_session, tmp_path):
    import sqlite3
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session

    from app.models import User
    from app.services.project_review import freeze_master_candidate

    path, master = _ready(client, db_session)
    db_session.commit()
    database = tmp_path / "freeze-race.db"
    raw = db_session.get_bind().raw_connection()
    with sqlite3.connect(database) as destination:
        raw.driver_connection.backup(destination)
    raw.close()
    engine = create_engine(f"sqlite:///{database}", connect_args={"timeout": 5})
    barrier = Barrier(2)

    def freeze(_):
        with Session(engine) as session:
            user = session.query(User).filter_by(email=HEADERS["X-Studio-User"]).one()
            barrier.wait(timeout=5)
            return freeze_master_candidate(session, int(path.split('/')[4]), int(path.split('/')[6]), master['id'], user, expected_payload_hash=master['payload_hash']).id

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            ids = list(pool.map(freeze, [1, 2]))
        assert ids[0] == ids[1]
        with Session(engine) as session:
            assert session.scalar(text("SELECT count(*) FROM content_asset")) == 1
            assert session.scalar(text("SELECT count(*) FROM project_event WHERE event_type = 'candidate.frozen'")) == 1
    finally:
        engine.dispose()
