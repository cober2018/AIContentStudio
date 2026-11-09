"""Warning approval follows the writing model's verdict on the exact check and input hash."""

import pytest
from test_f6a_freeze_v4 import _freeze, _ready
from test_f6a_modality_adapters import HEADERS
from test_f6a_v4_delivery_closure import _authorize

from app.models import ContentMasterCheckRun, Review
from app.services import warning_judgment


def _judge(client, path, check_id):
    return client.post(path.replace("master-revisions", f"checks/{check_id}/judge"), headers=HEADERS)


def test_warning_freezes_but_approval_needs_model_accept(client, db_session, monkeypatch):
    path, master = _ready(client, db_session)
    prior = db_session.query(ContentMasterCheckRun).filter_by(master_revision_id=master["id"], check_kind="master_schema").one()
    warning = ContentMasterCheckRun(master_revision_id=master["id"], check_kind=prior.check_kind, profile_key=prior.profile_key, profile_version=prior.profile_version, input_hash=prior.input_hash, status="warning", report_json={"reasons": ["explicit_editorial_warning"]})
    db_session.add(warning)
    db_session.commit()
    readiness = client.get(f"{path}/{master['id']}/readiness", headers=HEADERS).json()
    assert readiness["candidate_freeze_available"] is True
    frozen = _freeze(client, path, master)
    assert frozen.status_code == 201, frozen.text
    candidate = frozen.json()
    base = f"{path.replace('master-revisions', 'candidates')}/{candidate['id']}"
    decision = {"candidate_hash": candidate["candidate_hash"]}
    unjudged = client.post(f"{base}/approve", json=decision, headers=HEADERS)
    assert unjudged.status_code == 409 and unjudged.json()["detail"]["code"] == "warning_judgment_required"
    monkeypatch.setattr(warning_judgment, "_platform_judge", lambda request, model: ("done", "reject", "事实说法没有来源", model))
    assert _judge(client, path, warning.id).json()["verdict"] == "reject"
    assert client.post(f"{base}/approve", json=decision, headers=HEADERS).status_code == 409
    assert _judge(client, path, warning.id).status_code == 409
    db_session.query(warning_judgment.CheckWarningJudgment).delete()
    db_session.commit()
    monkeypatch.undo()
    monkeypatch.setattr(warning_judgment, "_platform_judge", lambda request, model: ("done", "accept", "内容没有这类问题", model))
    assert _judge(client, path, warning.id).json()["verdict"] == "accept"
    approved = client.post(f"{base}/approve", json=decision, headers=HEADERS)
    assert approved.status_code == 200, approved.text
    assert db_session.query(Review).one().warning_dispositions_json == {f"{warning.id}:{warning.input_hash}": "模型判断可以接受（平台模型）：内容没有这类问题"}
    assert warning.status == "warning"
    authorized = _authorize(client, base)
    assert authorized.status_code == 201, authorized.text
    assert client.get(f"/api/v1/delivery-targets/{authorized.json()['id']}/package.zip", headers=HEADERS).status_code == 200
    second = client.post(path, json={"idempotency_key": "new", "expected_revision": 1, "payload": master["payload"]}, headers=HEADERS).json()
    assert all(row["id"] is None for row in client.get(f"{path}/{second['id']}/checks/current", headers=HEADERS).json()["items"])


@pytest.mark.parametrize("phase", ["approval", "authorization", "package"])
def test_new_warning_result_never_reuses_old_disposition(client, db_session, phase):
    path, master = _ready(client, db_session)
    prior = db_session.query(ContentMasterCheckRun).filter_by(master_revision_id=master["id"], check_kind="master_schema").one()
    first = ContentMasterCheckRun(master_revision_id=master["id"], check_kind=prior.check_kind, profile_key=prior.profile_key, profile_version=prior.profile_version, input_hash=prior.input_hash, status="warning", report_json={"reasons": ["first finding"]})
    db_session.add(first)
    db_session.commit()
    candidate = _freeze(client, path, master).json()
    base = f"{path.replace('master-revisions', 'candidates')}/{candidate['id']}"
    old_decision = {"candidate_hash": candidate["candidate_hash"]}
    _judge(client, path, first.id)
    if phase != "approval":
        assert client.post(f"{base}/approve", json=old_decision, headers=HEADERS).status_code == 200
    target = _authorize(client, base).json() if phase == "package" else None
    second = ContentMasterCheckRun(master_revision_id=master["id"], check_kind=prior.check_kind, profile_key=prior.profile_key, profile_version=prior.profile_version, input_hash=prior.input_hash, status="warning", report_json={"reasons": ["different finding"]})
    db_session.add(second)
    db_session.commit()
    response = client.post(f"{base}/approve", json=old_decision, headers=HEADERS) if phase == "approval" else _authorize(client, base) if phase == "authorization" else client.get(f"/api/v1/delivery-targets/{target['id']}/package.zip", headers=HEADERS)
    assert response.status_code == 409, response.text
    refreshed = _freeze(client, path, master).json()
    assert refreshed["id"] != candidate["id"]
    refreshed_base = f"{path.replace('master-revisions', 'candidates')}/{refreshed['id']}"
    decision = {"candidate_hash": refreshed["candidate_hash"]}
    assert client.post(f"{refreshed_base}/approve", json=decision, headers=HEADERS).status_code == 409
    _judge(client, path, second.id)
    assert client.post(f"{refreshed_base}/approve", json=decision, headers=HEADERS).status_code == 200
