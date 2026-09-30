"""Actual service scope gates; contract fixtures never certify an external vendor."""

import sqlite3
import threading
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from test_f7_media_renderers import decision, stage

from app.models import CapabilityVerification, ContentMasterRevision, MaterialRevision, User
from app.services import media_renderers, provider_media

pytest_plugins = ["test_f7_media_renderers"]


def verify(client, preview, **changes):
    return client.post("/api/v1/settings/media-renderer-verifications", json={"stage_id": preview["stage_id"],
        "confirmed": True, "expected_input_hash": preview["input_hash"], "expected_output_hash": preview["content_hash"], **changes})


def execute(client, setup, **changes):
    return client.post(f"{setup['path']}/{setup['master']['id']}/media-render-outputs",
        json={**setup["body"], "output_mime": "image/png", **changes})


def test_real_stage_records_scope_without_rerender_or_business_write(client, db_session, setup):
    preview = stage(client, setup).json()
    response = verify(client, preview)
    assert response.status_code == 201, response.text
    event = db_session.get(CapabilityVerification, response.json()["verification_id"])
    assert event.scope_json["payload_schema"] == "graphic.master.v2"
    assert event.scope_json["output_mime"] == "image/png"
    assert event.evidence_json["input_hash"] == preview["input_hash"]
    assert event.evidence_json["output_hash"] == preview["content_hash"]
    assert setup["renderer"].calls == 1
    assert db_session.query(MaterialRevision).count() == 0
    assert db_session.query(ContentMasterRevision).count() == 1
    assert "private-result" not in str(event.evidence_json)


@pytest.mark.parametrize("problem", ["unconfirmed", "input", "output", "corrupt", "runtime", "master", "foreign", "viewer", "expired"])
def test_stage_verification_rejects_invalid_evidence(client, db_session, setup, problem):
    preview = stage(client, setup).json()
    changes = {}
    if problem == "unconfirmed":
        changes["confirmed"] = False
    elif problem in {"input", "output"}:
        changes[f"expected_{problem}_hash"] = "c" * 64
    elif problem == "corrupt":
        provider_media._cache[preview["stage_id"]].content = b"not a PNG"
    elif problem == "runtime":
        setup["renderer"].fingerprint = "d" * 64
    elif problem == "master":
        master = db_session.get(ContentMasterRevision, setup["master"]["id"])
        master.payload_json = {**master.payload_json, "title": "tampered"}
        db_session.commit()
    elif problem in {"foreign", "viewer"}:
        db_session.add(User(email="other@studio.local", name="Other", role="admin" if problem == "foreign" else "viewer"))
        db_session.commit()
    elif problem == "expired":
        provider_media._cache[preview["stage_id"]].expires = 0
    body = {"stage_id": preview["stage_id"], "confirmed": True,
        "expected_input_hash": preview["input_hash"], "expected_output_hash": preview["content_hash"], **changes}
    response = client.post("/api/v1/settings/media-renderer-verifications", json=body,
        headers={"X-Studio-User": "other@studio.local"} if problem in {"foreign", "viewer"} else {})
    assert response.status_code == (404 if problem in {"foreign", "expired"} else 403 if problem == "viewer" else 422 if problem == "unconfirmed" else 409), response.text
    assert db_session.query(CapabilityVerification).count() == 0
    assert setup["renderer"].calls == 1


def test_editor_executes_and_accepts_only_after_exact_verification(client, db_session, setup):
    assert execute(client, setup).status_code == 409
    assert setup["renderer"].calls == 0
    preview = stage(client, setup).json()
    assert verify(client, preview).status_code == 201
    user = db_session.scalar(select(User).where(User.email == "admin@studio.local"))
    user.role = "editor"
    db_session.commit()
    output = execute(client, setup)
    assert output.status_code == 200, output.text
    accepted = client.post(f"/api/v1/provider-media/{output.json()['stage_id']}/accept", json=decision())
    assert accepted.status_code == 201, accepted.text
    assert setup["renderer"].calls == 2
    assert db_session.query(MaterialRevision).count() == 1
    assert db_session.query(ContentMasterRevision).count() == 1


@pytest.mark.parametrize("problem", ["runtime", "expiry", "revocation", "mime"])
def test_changed_scope_blocks_before_renderer_call(client, db_session, setup, problem):
    preview = stage(client, setup).json()
    record = verify(client, preview)
    assert record.status_code == 201, record.text
    changes = {}
    if problem == "runtime":
        setup["renderer"].fingerprint = "f" * 64
    elif problem == "expiry":
        event = db_session.get(CapabilityVerification, record.json()["verification_id"])
        event.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        db_session.commit()
    elif problem == "mime":
        changes["output_mime"] = "image/jpeg"
    else:
        provider_media._cache.clear()
        revoked = client.post(f"/api/v1/settings/media-renderer-verifications/{record.json()['verification_id']}/revoke")
        assert revoked.status_code == 201, revoked.text
        assert db_session.get(CapabilityVerification, record.json()["verification_id"]).result == "verified"
    response = execute(client, setup, **changes)
    assert response.status_code == 409, response.text
    assert setup["renderer"].calls == 1
    assert db_session.query(MaterialRevision).count() == 0


def test_revocation_after_output_blocks_acceptance(client, db_session, setup):
    preview = stage(client, setup).json()
    record = verify(client, preview)
    assert record.status_code == 201, record.text
    output = execute(client, setup)
    assert output.status_code == 200, output.text
    assert client.post(f"/api/v1/settings/media-renderer-verifications/{record.json()['verification_id']}/revoke").status_code == 201
    accepted = client.post(f"/api/v1/provider-media/{output.json()['stage_id']}/accept", json=decision())
    assert accepted.status_code == 409, accepted.text
    assert db_session.query(MaterialRevision).count() == 0


def test_viewer_cannot_execute_or_revoke(client, db_session, setup):
    user = db_session.scalar(select(User).where(User.email == "admin@studio.local"))
    user.role = "viewer"
    db_session.commit()
    assert execute(client, setup).status_code == 403
    assert client.post("/api/v1/settings/media-renderer-verifications/1/revoke").status_code == 403
    assert setup["renderer"].calls == 0


def test_accept_does_not_hold_global_cache_lock_when_entering_database(client, monkeypatch, setup):
    preview = stage(client, setup).json()
    original = media_renderers._current
    def current(*args, **kwargs):
        assert not provider_media._lock._is_owned()
        return original(*args, **kwargs)
    monkeypatch.setattr(media_renderers, "_current", current)
    response = client.post(f"/api/v1/provider-media/{preview['stage_id']}/accept", json=decision())
    assert response.status_code == 201, response.text


def test_stage_releases_database_locks_before_global_cache_write(client, db_session, monkeypatch, setup):
    original = provider_media.stage_output
    def output(*args, **kwargs):
        assert not db_session.in_transaction()
        return original(*args, **kwargs)
    monkeypatch.setattr(provider_media, "stage_output", output)
    assert stage(client, setup).status_code == 200


def test_editor_cannot_accept_admin_probe_or_forge_execution_mode(client, db_session, setup):
    preview = stage(client, setup).json()
    user = db_session.scalar(select(User).where(User.email == "admin@studio.local"))
    user.role = "editor"
    db_session.commit()
    assert client.post(f"/api/v1/provider-media/{preview['stage_id']}/accept", json=decision()).status_code == 403
    assert execute(client, setup, execution_mode="verified").status_code == 422
    assert db_session.query(MaterialRevision).count() == 0


def test_revocation_during_render_blocks_staging(client, db_session, setup):
    preview = stage(client, setup).json()
    record = verify(client, preview)
    assert record.status_code == 201, record.text
    def revoke_scope():
        response = client.post(f"/api/v1/settings/media-renderer-verifications/{record.json()['verification_id']}/revoke")
        assert response.status_code == 201, response.text
    setup["renderer"].mutate = revoke_scope
    before = set(provider_media._cache)
    assert execute(client, setup).status_code == 409
    assert set(provider_media._cache) == before
    assert db_session.query(MaterialRevision).count() == 0


def test_two_connections_revocation_precedes_accept_without_holding_cache_lock(client, db_session, monkeypatch, setup, tmp_path):
    preview = stage(client, setup).json()
    record = verify(client, preview)
    assert record.status_code == 201, record.text
    output = execute(client, setup)
    assert output.status_code == 200, output.text
    db_session.rollback()
    connection = db_session.bind.raw_connection()
    destination = sqlite3.connect(tmp_path / "revocation.sqlite")
    try:
        connection.driver_connection.backup(destination)
    finally:
        destination.close()
        connection.close()
    engine = create_engine(f"sqlite:///{tmp_path / 'revocation.sqlite'}", connect_args={"check_same_thread": False, "timeout": 5})
    locked, accept_started, release = threading.Event(), threading.Event(), threading.Event()
    results, failures = [], []
    original = media_renderers._lock_registration
    def registration_lock(*args):
        original(*args)
        if threading.current_thread().name == "scope-revoker":
            locked.set()
            assert release.wait(5)
    monkeypatch.setattr(media_renderers, "_lock_registration", registration_lock)
    original_owned = media_renderers.content_masters.owned_unit
    def owned(*args, **kwargs):
        if threading.current_thread().name == "scope-accepter":
            accept_started.set()
        return original_owned(*args, **kwargs)
    monkeypatch.setattr(media_renderers.content_masters, "owned_unit", owned)
    def revoker():
        try:
            with Session(engine) as db:
                user = db.scalar(select(User).where(User.email == "admin@studio.local"))
                media_renderers.revoke(db, user, record.json()["verification_id"])
                results.append("revoked")
        except Exception as error:  # noqa: BLE001 Worker failures must reach the main-thread assertion.
            failures.append(error)
    def accepter():
        from fastapi import HTTPException
        try:
            with Session(engine) as db:
                user = db.scalar(select(User).where(User.email == "admin@studio.local"))
                try:
                    provider_media.accept(db, user, output.json()["stage_id"], decision())
                    results.append("unexpected_accept")
                except HTTPException as error:
                    results.append(error.detail)
        except Exception as error:  # noqa: BLE001 Worker failures must reach the main-thread assertion.
            failures.append(error)
    first = threading.Thread(target=revoker, name="scope-revoker")
    second = threading.Thread(target=accepter, name="scope-accepter")
    first.start()
    try:
        assert locked.wait(5)
        second.start()
        assert accept_started.wait(5)
        cache_available = provider_media._lock.acquire(timeout=1)
        assert cache_available
        provider_media._lock.release()
    finally:
        release.set()
        first.join(6)
        if second.ident is not None:
            second.join(6)
    assert not first.is_alive() and not second.is_alive()
    assert failures == []
    assert sorted(results) == ["media_renderer_scope_unverified", "revoked"]
    with Session(engine) as db:
        assert db.query(MaterialRevision).count() == 0
        assert db.get(CapabilityVerification, record.json()["verification_id"]).result == "verified"
    engine.dispose()
