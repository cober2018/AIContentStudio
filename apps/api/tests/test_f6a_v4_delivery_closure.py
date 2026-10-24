"""Real Master-only approval and local ZIP, with frozen provenance and live gates."""

import io
import json
import zipfile
from copy import deepcopy
from pathlib import Path

import pytest
from fastapi import HTTPException
from test_f6a_modality_adapters import HEADERS, _draft_render, _render_material, _unit

from app.models import (
    ContentAsset,
    ContentMasterCheckRun,
    ContentMasterRevision,
    DeliveryAttempt,
    DeliveryTarget,
    FactPackItem,
    Review,
    utcnow,
)


def _candidate(client, db, tmp_path):
    project, path = _unit(client, db, "text")
    material = _render_material(db, project, tmp_path, "graphic")
    saved = client.post(path, json={"idempotency_key": "closure", "payload": {"title": "独立内容", "markdown": "不经过Draft的成品正文"}, "asset_refs": [{"material_revision_id": material.id, "content_hash": material.content_hash, "role": "inline", "placement": {"after": "intro"}}]}, headers=HEADERS)
    assert saved.status_code == 200, saved.text
    master = saved.json()
    checked = client.post(f"{path}/{master['id']}/checks", headers=HEADERS)
    assert all(check["status"] == "pass" for check in checked.json()["items"])
    frozen = client.post(path.replace("master-revisions", "candidates/freeze"), json={"content_master_revision_id": master["id"], "expected_payload_hash": master["payload_hash"]}, headers=HEADERS)
    assert frozen.status_code == 201, frozen.text
    candidate = frozen.json()
    base = f"{path.replace('master-revisions', 'candidates')}/{candidate['id']}"
    return path, base, master, candidate, material


def _approve(client, base, candidate):
    return client.post(f"{base}/approve", json={"candidate_hash": candidate["candidate_hash"]}, headers=HEADERS)


def _authorize(client, base, *, action="copy_package", version="v1"):
    return client.post(f"{base}/delivery-authorizations", json={"channel": "wechat", "content_form": "article", "account_ref": "manual-account", "authorization_version": version, "action": action}, headers=HEADERS)


@pytest.mark.parametrize("action", ["copy_package", "manual_handoff"])
def test_no_draft_master_approves_authorizes_and_builds_exact_zip(client, db_session, tmp_path, action):
    path, base, master, candidate, material = _candidate(client, db_session, tmp_path)
    original = deepcopy(db_session.get(ContentMasterRevision, master["id"]).__dict__)
    approved = _approve(client, base, candidate)
    assert approved.status_code == 200, approved.text
    authorized = _authorize(client, base, action=action)
    assert authorized.status_code == 201, authorized.text
    target_id = authorized.json()["id"]
    response = client.get(f"/api/v1/delivery-targets/{target_id}/package.zip", headers=HEADERS)
    assert response.status_code == 200, response.text
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["schema_version"] == 4
        assert manifest["candidate"]["hash"] == candidate["candidate_hash"]
        assert manifest["content_master"]["id"] == master["id"]
        assert archive.read("content.md").decode() == master["payload"]["markdown"]
        assert "publish-guide.md" in archive.namelist()
        media_names = [name for name in archive.namelist() if name.startswith("media/")]
        assert len(media_names) == 1
        assert archive.read(media_names[0]) == Path(material.file_path).read_bytes()
    asset = db_session.get(ContentAsset, candidate["id"])
    assert asset.workflow_run_id is None
    assert asset.candidate_hash == candidate["candidate_hash"] and asset.candidate_manifest_json == candidate["manifest"]
    review = db_session.query(Review).one()
    assert review.content_asset_id == asset.id and review.candidate_hash == asset.candidate_hash
    assert review.revision_no == master["revision_no"]
    assert db_session.get(DeliveryTarget, target_id).approved_candidate_hash == asset.approved_candidate_hash
    unchanged = client.get(f"{path}/{master['id']}", headers=HEADERS).json()
    assert unchanged == master
    db_session.refresh(db_session.get(ContentMasterRevision, master["id"]))
    assert all(getattr(db_session.get(ContentMasterRevision, master["id"]), key) == value for key, value in original.items() if key != "_sa_instance_state")
    assert db_session.query(DeliveryAttempt).count() == 0


@pytest.mark.parametrize("phase", ["approval", "authorization", "package"])
@pytest.mark.parametrize("problem", ["rights", "evidence", "bytes", "tampered_manifest"])
def test_live_failure_blocks_all_v4_actions_without_mutating_history(client, db_session, tmp_path, phase, problem):
    _, base, _, candidate, material = _candidate(client, db_session, tmp_path)
    target_id = None
    if phase != "approval":
        approved = _approve(client, base, candidate)
        assert approved.status_code == 200, approved.text
    if phase == "package":
        target = _authorize(client, base)
        assert target.status_code == 201, target.text
        target_id = target.json()["id"]
    if problem == "rights":
        material.public_use_allowed = False
    elif problem == "evidence":
        db_session.query(FactPackItem).one().public_use_revoked_at = utcnow()
    elif problem == "bytes":
        Path(material.file_path).write_bytes(b"not frozen bytes")
    else:
        asset = db_session.get(ContentAsset, candidate["id"])
        changed = deepcopy(asset.candidate_manifest_json)
        changed["content"]["markdown"] = "篡改正文"
        asset.candidate_manifest_json = changed
    db_session.commit()
    response = _approve(client, base, candidate) if phase == "approval" else _authorize(client, base) if phase == "authorization" else client.get(f"/api/v1/delivery-targets/{target_id}/package.zip", headers=HEADERS)
    assert response.status_code == 409, response.text
    assert db_session.query(DeliveryAttempt).count() == 0
    if phase == "authorization":
        assert db_session.query(DeliveryTarget).count() == 0
    if target_id:
        assert db_session.get(DeliveryTarget, target_id).status == "target_authorized"


def test_new_master_blocks_new_authorization_but_preserves_existing_frozen_package(client, db_session, tmp_path):
    path, base, master, candidate, _ = _candidate(client, db_session, tmp_path)
    assert _approve(client, base, candidate).status_code == 200
    target = _authorize(client, base)
    assert target.status_code == 201, target.text
    new = client.post(path, json={"idempotency_key": "next", "expected_revision": 1, "payload": {"markdown": "新版正文"}}, headers=HEADERS)
    assert new.status_code == 200, new.text
    assert _authorize(client, base, version="v2").status_code == 409
    response = client.get(f"/api/v1/delivery-targets/{target.json()['id']}/package.zip", headers=HEADERS)
    assert response.status_code == 200, response.text
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert archive.read("content.md").decode() == master["payload"]["markdown"]


def test_shared_validator_exists_and_rejects_unknown_schema(client, db_session, tmp_path):
    from app.services.production_validation import validate_live_v4_candidate

    _, _, _, candidate, _ = _candidate(client, db_session, tmp_path)
    manifest = validate_live_v4_candidate(db_session, db_session.get(ContentAsset, candidate["id"]))
    assert manifest["schema_version"] == 4
    asset = db_session.get(ContentAsset, candidate["id"])
    changed = deepcopy(asset.candidate_manifest_json)
    changed["schema_version"] = 3
    asset.candidate_manifest_json = changed
    with pytest.raises(HTTPException) as exc:
        validate_live_v4_candidate(db_session, asset)
    assert exc.value.status_code == 409


@pytest.mark.parametrize("phase", ["approval", "authorization", "package"])
@pytest.mark.parametrize("section", ["content_master", "identity", "render", "checks", "schema_version"])
def test_rehashed_forgery_cannot_bypass_exact_master_provenance(client, db_session, tmp_path, phase, section):
    from app.services.candidates import candidate_hash

    _, base, _, candidate, _ = _candidate(client, db_session, tmp_path)
    if phase != "approval":
        assert _approve(client, base, candidate).status_code == 200
    target = _authorize(client, base).json() if phase == "package" else None
    asset = db_session.get(ContentAsset, candidate["id"])
    changed = deepcopy(asset.candidate_manifest_json)
    if section == "schema_version":
        changed[section] = 3
    elif section == "checks":
        changed[section][0]["report"] = {"forged": True}
    else:
        key = "payload_hash" if section == "content_master" else "checksum" if section == "identity" else "content_hash"
        changed[section][key] = "forged"
    asset.candidate_manifest_json = changed
    asset.candidate_hash = candidate_hash(changed)
    if phase != "approval":
        asset.approved_candidate_hash = asset.candidate_hash
        db_session.query(Review).one().candidate_hash = asset.candidate_hash
    if target:
        db_session.get(DeliveryTarget, target["id"]).approved_candidate_hash = asset.candidate_hash
    db_session.commit()
    candidate["candidate_hash"] = asset.candidate_hash
    response = _approve(client, base, candidate) if phase == "approval" else _authorize(client, base) if phase == "authorization" else client.get(f"/api/v1/delivery-targets/{target['id']}/package.zip", headers=HEADERS)
    assert response.status_code == 409, response.text
    assert db_session.query(DeliveryAttempt).count() == 0


def test_existing_authorization_packages_frozen_context_after_new_brief(client, db_session, tmp_path):
    path, base, master, candidate, _ = _candidate(client, db_session, tmp_path)
    assert _approve(client, base, candidate).status_code == 200
    target = _authorize(client, base).json()
    new_brief = client.post(f"{path.split('/units/')[0]}/brief/revisions", json={"objective": "新目标", "expected_revision": 1}, headers=HEADERS)
    assert new_brief.status_code == 201, new_brief.text
    assert _approve(client, base, candidate).status_code == 409
    assert _authorize(client, base, version="v2").status_code == 409
    response = client.get(f"/api/v1/delivery-targets/{target['id']}/package.zip", headers=HEADERS)
    assert response.status_code == 200, response.text
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["brief"]["id"] == candidate["manifest"]["brief"]["id"]
        assert archive.read("content.md").decode() == master["payload"]["markdown"]


def test_approval_and_authorization_retries_do_not_duplicate_decisions(client, db_session, tmp_path):
    _, base, _, candidate, _ = _candidate(client, db_session, tmp_path)
    assert _approve(client, base, candidate).status_code == 200
    assert _approve(client, base, candidate).status_code == 200
    first = _authorize(client, base)
    second = _authorize(client, base)
    assert first.status_code == second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert db_session.query(Review).count() == db_session.query(DeliveryTarget).count() == 1


def test_changes_request_preserves_master_and_candidate(client, db_session, tmp_path):
    path, base, master, candidate, _ = _candidate(client, db_session, tmp_path)
    response = client.post(f"{base}/request-changes", json={"candidate_hash": candidate["candidate_hash"], "comment": "调整表达"}, headers=HEADERS)
    assert response.status_code == 200, response.text
    assert client.get(f"{path}/{master['id']}", headers=HEADERS).json() == master
    assert db_session.get(ContentAsset, candidate["id"]).candidate_manifest_json == candidate["manifest"]
    assert db_session.query(Review).one().decision == "changes_requested"
    assert db_session.query(DeliveryTarget).count() == 0


@pytest.mark.parametrize("phase", ["approval", "authorization"])
def test_commit_boundary_revalidation_rolls_back_late_revocation(client, db_session, tmp_path, monkeypatch, phase):
    from app.services import project_events, project_review

    _, base, _, candidate, material = _candidate(client, db_session, tmp_path)
    if phase == "authorization":
        assert _approve(client, base, candidate).status_code == 200
    original = project_events.record_project_event

    def revoke_after_event(db, **kwargs):
        result = original(db, **kwargs)
        if kwargs["event_type"] in {"content.approved", "delivery.authorized"}:
            db.get(type(material), material.id).public_use_allowed = False
        return result

    monkeypatch.setattr(project_events, "record_project_event", revoke_after_event)
    monkeypatch.setattr(project_review, "record_project_event", revoke_after_event)
    response = _approve(client, base, candidate) if phase == "approval" else _authorize(client, base)
    assert response.status_code == 409, response.text
    assert db_session.query(DeliveryTarget).count() == 0
    assert db_session.query(Review).count() == (1 if phase == "authorization" else 0)
    assert db_session.get(type(material), material.id).public_use_allowed is True


def test_v4_cannot_enter_unverified_publisher_adapter(client, db_session, tmp_path):
    from app.services.delivery import validate_live_candidate_payload

    _, base, _, candidate, _ = _candidate(client, db_session, tmp_path)
    assert _approve(client, base, candidate).status_code == 200
    response = _authorize(client, base, action="auto_draft")
    assert response.status_code == 422, response.text
    with pytest.raises(HTTPException) as exc:
        validate_live_candidate_payload(db_session, db_session.get(ContentAsset, candidate["id"]))
    assert "capability_unavailable" in str(exc.value.detail)
    assert db_session.query(DeliveryAttempt).count() == db_session.query(DeliveryTarget).count() == 0


@pytest.mark.parametrize("modality", ["graphic", "video"])
def test_existing_manual_render_adapter_packages_only_exact_bytes(client, db_session, tmp_path, modality):
    path, body, readiness, material = _draft_render(client, db_session, tmp_path, modality)
    response = client.post(path, json={**body, "idempotency_key": "confirmed", "expected_revision": 1, "render_attestation": {"confirmed": True, "render_input_hash": readiness["render_input_hash"]}}, headers=HEADERS)
    master = response.json()
    assert response.status_code == 200, response.text
    checks = client.post(f"{path}/{master['id']}/checks", headers=HEADERS)
    assert all(check["status"] == "pass" for check in checks.json()["items"])
    frozen = client.post(path.replace("master-revisions", "candidates/freeze"), json={"content_master_revision_id": master["id"], "expected_payload_hash": master["payload_hash"]}, headers=HEADERS)
    assert frozen.status_code == 201, frozen.text
    candidate = frozen.json()
    base = f"{path.replace('master-revisions', 'candidates')}/{candidate['id']}"
    assert _approve(client, base, candidate).status_code == 200
    target = client.post(f"{base}/delivery-authorizations", json={"channel": f"fixture_{modality}", "content_form": "final", "account_ref": "manual", "authorization_version": "v1", "action": "copy_package"}, headers=HEADERS)
    assert target.status_code == 201, target.text
    response = client.get(f"/api/v1/delivery-targets/{target.json()['id']}/package.zip", headers=HEADERS)
    assert response.status_code == 200, response.text
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        name = "render-1.png" if modality == "graphic" else "render-1.mp4"
        assert archive.read(name) == Path(material.file_path).read_bytes()
        assert "content.md" not in archive.namelist()
        assert json.loads(archive.read("manifest.json"))["render"]["origin"] == "manual"
    assert db_session.query(DeliveryAttempt).count() == 0


@pytest.mark.parametrize("phase", ["approval", "authorization", "package"])
def test_latest_failed_check_cannot_use_old_frozen_pass(client, db_session, tmp_path, phase):
    _, base, master, candidate, _ = _candidate(client, db_session, tmp_path)
    if phase != "approval":
        assert _approve(client, base, candidate).status_code == 200
    target = _authorize(client, base).json() if phase == "package" else None
    old = db_session.query(ContentMasterCheckRun).filter_by(master_revision_id=master["id"], check_kind="rights").one()
    db_session.add(ContentMasterCheckRun(master_revision_id=master["id"], check_kind=old.check_kind, profile_key=old.profile_key, profile_version=old.profile_version, input_hash=old.input_hash, status="blocker", report_json={"reasons": ["new finding"]}))
    db_session.commit()
    response = _approve(client, base, candidate) if phase == "approval" else _authorize(client, base) if phase == "authorization" else client.get(f"/api/v1/delivery-targets/{target['id']}/package.zip", headers=HEADERS)
    assert response.status_code == 409, response.text
    assert db_session.query(DeliveryAttempt).count() == 0


def test_stale_context_checks_cannot_poison_already_authorized_history(client, db_session, tmp_path):
    path, base, master, candidate, _ = _candidate(client, db_session, tmp_path)
    assert _approve(client, base, candidate).status_code == 200
    target = _authorize(client, base).json()
    project = path.split("/")[4]
    client.post(f"/api/v1/content-projects/{project}/brief/revisions", json={"expected_revision": 1, "objective": "新上下文"}, headers=HEADERS)
    response = client.post(f"{path}/{master['id']}/checks", headers=HEADERS)
    assert response.status_code == 409
    old = db_session.query(ContentMasterCheckRun).filter_by(master_revision_id=master["id"], check_kind="rights").one()
    db_session.add(ContentMasterCheckRun(master_revision_id=master["id"], check_kind=old.check_kind, profile_key=old.profile_key, profile_version=old.profile_version, input_hash="a" * 64, status="stale", report_json={"reasons": ["different context"]}))
    db_session.commit()
    assert client.get(f"/api/v1/delivery-targets/{target['id']}/package.zip", headers=HEADERS).status_code == 200
    db_session.add(ContentMasterCheckRun(master_revision_id=master["id"], check_kind=old.check_kind, profile_key=old.profile_key, profile_version=old.profile_version, input_hash=old.input_hash, status="blocker", report_json={"reasons": ["same input, actual new blocker"]}))
    db_session.commit()
    assert client.get(f"/api/v1/delivery-targets/{target['id']}/package.zip", headers=HEADERS).status_code == 409


def test_raw_asset_authorization_cannot_bypass_owner_or_current_master(client, db_session, tmp_path):
    path, base, _, candidate, _ = _candidate(client, db_session, tmp_path)
    assert _approve(client, base, candidate).status_code == 200
    payload = {"channel": "wechat", "content_form": "article", "account_ref": "manual-account", "authorization_version": "v1", "action": "copy_package"}
    raw = f"/api/v1/assets/{candidate['id']}/delivery-targets"
    forbidden = client.post(raw, json=payload, headers={"X-Studio-User": "other@studio.local"})
    assert forbidden.status_code == 404, forbidden.text
    first = client.post(raw, json=payload, headers=HEADERS)
    assert first.status_code == 201, first.text
    assert first.json()["id"] == _authorize(client, base).json()["id"]
    new = client.post(path, json={"idempotency_key": "new", "expected_revision": 1, "payload": {"markdown": "新内容"}}, headers=HEADERS)
    assert new.status_code == 200, new.text
    response = client.post(raw, json={**payload, "authorization_version": "v2"}, headers=HEADERS)
    assert response.status_code == 409, response.text
    assert db_session.query(DeliveryTarget).count() == 1


def test_checks_refresh_does_not_rewrite_frozen_candidate(client, db_session, tmp_path):
    path, base, master, candidate, _ = _candidate(client, db_session, tmp_path)
    response = client.post(f"{path}/{master['id']}/checks", headers=HEADERS)
    assert response.status_code == 200
    assert _approve(client, base, candidate).status_code == 200
    assert _authorize(client, base).status_code == 201
    assert db_session.get(ContentAsset, candidate["id"]).candidate_manifest_json == candidate["manifest"]
