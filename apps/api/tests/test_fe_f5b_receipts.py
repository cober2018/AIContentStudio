"""Receipt entry points materialize publication history in the same transaction."""

from datetime import UTC, datetime

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import (
    AuditLog,
    ContentAsset,
    ContentPersona,
    ContentProject,
    ContentUnit,
    DeliveryAttempt,
    DeliveryReceipt,
    DeliveryTarget,
    PublishedContentRecord,
    User,
)
from app.services import published_history

EDITOR = {"X-Studio-User": "editor@studio.local"}
CONFIRM = {"status": "human_confirmed", "evidence_ref": "manual-publication-proof"}
ATTESTED = {
    **CONFIRM,
    "published_at": "2025-03-04T15:00:00+08:00",
    "publication_time_evidence": "Platform page shows 2025-03-04 15:00 +08:00",
}


@pytest.fixture(params=["generic"])
def receipt_env(request, db_session):
    user = User(email=EDITOR["X-Studio-User"], name="Editor", role="editor")
    other = User(email="foreign@studio.local", name="Foreign", role="editor")
    db_session.add_all([user, other])
    db_session.flush()
    asset = ContentAsset(channel="wechat", title="Frozen title", final_body="Frozen body",
                         candidate_hash="c" * 64, approved_candidate_hash="c" * 64)
    db_session.add(asset)
    db_session.flush()
    target = DeliveryTarget(content_asset_id=asset.id, channel="wechat", content_form="article",
                            account_ref="owned-account", authorization_version="v1",
                            approved_candidate_hash="c" * 64, authorized_by=user.email,
                            status="awaiting_manual_receipt",
                            action="copy_package")
    db_session.add(target)
    db_session.commit()
    path = f"/api/v1/delivery-targets/{target.id}/receipt"
    return request.param, user, asset, target, path


def histories(db):
    return db.scalars(select(PublishedContentRecord)).all()


def receipts(db):
    return db.scalars(select(DeliveryReceipt)).all()


def test_receipt_creates_one_history_without_fabricated_date(client, db_session, receipt_env):
    _, user, asset, target, path = receipt_env
    for _ in range(2):
        response = client.post(path, headers=EDITOR, json=CONFIRM)
        assert response.status_code == 200, response.text
    assert len(receipts(db_session)) == len(histories(db_session)) == 1
    receipt, row = receipts(db_session)[0], histories(db_session)[0]
    assert (row.owner_user_id, row.content_asset_id, row.delivery_target_id, row.delivery_receipt_id) == (
        user.id, asset.id, target.id, receipt.id,
    )
    assert row.content_hash == target.approved_candidate_hash
    assert row.published_at is None
    assert row.content_snapshot_json["publication_time_source"] == "unknown"
    assert datetime.fromisoformat(row.content_snapshot_json["confirmation_time"]).replace(tzinfo=UTC) == receipt.delivered_at.replace(tzinfo=UTC)


@pytest.mark.parametrize("status", ["failed", "reconciliation_needed"])
def test_unconfirmed_receipt_does_not_publish(client, db_session, receipt_env, status):
    *_, path = receipt_env
    response = client.post(path, headers=EDITOR, json={"status": status})
    assert response.status_code == 200, response.text
    assert len(receipts(db_session)) == 1
    assert histories(db_session) == []


def test_unresolved_unknown_never_publishes(client, db_session, receipt_env):
    kind, _, _, target, path = receipt_env
    db_session.add(DeliveryAttempt(target_id=target.id, attempt_no=1, idempotency_key="unknown-attempt",
                                   status="unknown", response_metadata_json={}))
    db_session.commit()
    for _ in range(2):
        response = client.post(path, headers=EDITOR, json=CONFIRM)
        assert response.status_code == (409 if kind == "generic" else 200), response.text
    assert len(receipts(db_session)) == (0 if kind == "generic" else 1)
    assert histories(db_session) == []


def test_unprovable_legacy_candidate_keeps_receipt(client, db_session, receipt_env):
    _, _, asset, _, path = receipt_env
    asset.candidate_hash = asset.approved_candidate_hash = None
    db_session.commit()
    response = client.post(path, headers=EDITOR, json=CONFIRM)
    assert response.status_code == 200, response.text
    assert len(receipts(db_session)) == 1
    assert histories(db_session) == []


def test_explicit_publication_date_is_preserved_and_idempotent(client, db_session, receipt_env):
    *_, path = receipt_env
    for _ in range(2):
        response = client.post(path, headers=EDITOR, json=ATTESTED)
        assert response.status_code == 200, response.text
    assert len(receipts(db_session)) == len(histories(db_session)) == 1
    row = histories(db_session)[0]
    assert row.published_at.replace(tzinfo=UTC) == datetime(2025, 3, 4, 7, tzinfo=UTC)
    assert ATTESTED["publication_time_evidence"] in str(row.content_snapshot_json)
    assert row.published_at.replace(tzinfo=UTC) != receipts(db_session)[0].delivered_at.replace(tzinfo=UTC)


@pytest.mark.parametrize("change", [
    {"published_at": "2025-03-04T15:00:00"},
    {"publication_time_evidence": None},
    {"publication_time_evidence": "   "},
    {"status": "failed"},
    {"status": "reconciliation_needed"},
    {"published_at": None},
])
def test_publication_time_requires_confirmed_aware_attestation(client, db_session, receipt_env, change):
    *_, path = receipt_env
    response = client.post(path, headers=EDITOR, json={**ATTESTED, **change})
    assert response.status_code == 422, response.text
    assert receipts(db_session) == histories(db_session) == []


@pytest.mark.parametrize("change", [
    {"published_at": "2025-03-05T15:00:00+08:00"},
    {"publication_time_evidence": "A different time attestation"},
])
def test_publication_time_and_evidence_participate_in_idempotency(client, db_session, receipt_env, change):
    *_, target, path = receipt_env
    assert client.post(path, headers=EDITOR, json=ATTESTED).status_code == 200
    response = client.post(path, headers=EDITOR, json={**ATTESTED, **change})
    assert response.status_code == 409, response.text
    assert len(receipts(db_session)) == len(histories(db_session)) == 1
    assert target.status == "human_confirmed"


def test_foreign_target_cannot_record_or_reuse_receipt(client, db_session, receipt_env):
    *_, path = receipt_env
    foreign = {"X-Studio-User": "foreign@studio.local"}
    for confirmed in (False, True):
        if confirmed:
            assert client.post(path, headers=EDITOR, json=CONFIRM).status_code == 200
        response = client.post(path, headers=foreign, json=CONFIRM)
        assert response.status_code in {403, 404}, response.text
    assert len(receipts(db_session)) == len(histories(db_session)) == 1


def test_foreign_existing_history_cannot_be_reused(client, db_session, receipt_env):
    *_, path = receipt_env
    assert client.post(path, headers=EDITOR, json=CONFIRM).status_code == 200
    row = histories(db_session)[0]
    row.owner_user_id = db_session.scalar(select(User.id).where(User.email == "foreign@studio.local"))
    db_session.commit()
    response = client.post(path, headers=EDITOR, json=CONFIRM)
    assert response.status_code == 404, response.text
    assert len(receipts(db_session)) == len(histories(db_session)) == 1


@pytest.mark.parametrize("integrity_failure", [False, True])
def test_history_failure_rolls_back_receipt_and_target(client, db_session, receipt_env, monkeypatch, integrity_failure):
    *_, target, path = receipt_env
    sync = published_history.sync_receipt

    def fail_after_history(db, user, receipt, **kwargs):
        sync(db, user, receipt, **kwargs)
        if integrity_failure:
            raise IntegrityError("INSERT publication", {}, Exception("Injected constraint failure"))
        raise HTTPException(409, "Injected publication failure")

    monkeypatch.setattr(published_history, "sync_receipt", fail_after_history)
    response = client.post(path, headers=EDITOR, json=CONFIRM)
    assert response.status_code == 409, response.text
    assert receipts(db_session) == histories(db_session) == []
    db_session.refresh(target)
    assert target.status == "awaiting_manual_receipt"
    assert db_session.scalars(select(AuditLog).where(AuditLog.event == "delivery_receipt.recorded")).all() == []


def test_project_mutation_boundary_precedes_receipt_repair(client, db_session, receipt_env):
    kind, user, asset, _, path = receipt_env
    project = ContentProject(owner_user_id=user.id, title="Project")
    persona = ContentPersona(owner_user_id=user.id, name="Persona")
    db_session.add_all([project, persona])
    db_session.flush()
    unit = ContentUnit(project_id=project.id, persona_id=persona.id, modality="text", title="Unit")
    db_session.add(unit)
    db_session.flush()
    asset.project_id, asset.content_unit_id = project.id, unit.id
    db_session.commit()
    assert client.post(path, headers=EDITOR, json=CONFIRM).status_code == 200
    db_session.delete(histories(db_session)[0])
    project.status = "archived"
    db_session.commit()
    response = client.post(path, headers=EDITOR, json=CONFIRM)
    assert response.status_code == 409, response.text
    assert len(receipts(db_session)) == 1
    assert histories(db_session) == []
