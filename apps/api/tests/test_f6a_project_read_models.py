"""Production projections expose immutable Masters without another state store."""

import pytest
from test_f6a_freeze_v4 import _freeze, _ready
from test_f6a_modality_adapters import HEADERS, _draft_render, _unit

from app.models import ContentAsset, DeliveryTarget
from app.services.project_review_projection import candidate_diff


@pytest.mark.parametrize("modality", ["text", "graphic", "video"])
def test_review_preview_and_diff_are_modality_aware(client, db_session, tmp_path, modality):
    if modality == "text":
        path, master = _ready(client, db_session)
    else:
        path, body, readiness, _ = _draft_render(client, db_session, tmp_path, modality)
        master = client.post(path, json={**body, "idempotency_key": "confirm", "expected_revision": 1, "render_attestation": {"confirmed": True, "render_input_hash": readiness["render_input_hash"]}}, headers=HEADERS).json()
        client.post(f"{path}/{master['id']}/checks", headers=HEADERS)
    frozen = _freeze(client, path, master).json()
    project, unit = path.split("/")[4], path.split("/")[6]
    url = f"/api/v1/review-center/projects/{project}/units/{unit}/candidates/{frozen['id']}"
    preview = client.get(url, headers=HEADERS).json()["preview"]
    assert preview["modality"] == modality
    assert preview["render"]["status"] == "ready"
    if modality == "text":
        assert preview["markdown"] == master["payload"]["markdown"]
    elif modality == "graphic":
        assert preview["canvas_count"] == 1
    else:
        assert preview["shot_count"] == 1
    if modality != "text":
        render_id = frozen["manifest"]["render"]["outputs"][0]["material_revision_id"]
        response = client.get(f"{url}/renders/{render_id}", headers=HEADERS)
        assert response.status_code == 200, response.text
        assert response.headers["x-content-type-options"] == "nosniff"
        assert client.get(f"{url}/renders/{render_id + 1000}", headers=HEADERS).status_code == 404
        assert client.get(f"{url}/renders/{render_id}", headers={"X-Studio-User": "foreign-preview@studio.local"}).status_code == 404
    diff = client.get(f"{url}/diff", headers=HEADERS).json()
    assert (diff["text"] is not None) == (modality == "text")
    assert "content_master" in diff["changed_sections"]


def test_versions_show_real_master_history_and_frozen_context(client, db_session):
    path, first = _ready(client, db_session)
    second = client.post(path, json={"idempotency_key": "second", "expected_revision": 1, "payload": {"markdown": "第二版"}}, headers=HEADERS).json()
    project = path.split("/")[4]
    versions = client.get(f"/api/v1/content-projects/{project}/versions", headers=HEADERS).json()["contentMasters"]
    assert [row["id"] for row in versions] == [str(second["id"]), str(first["id"])]
    assert [row["current"] for row in versions] == [True, False]
    assert versions[0]["payloadHash"] == second["payload_hash"]
    assert versions[0]["contextHash"] == second["context_hash"]
    assert versions[0]["identitySnapshotId"] == second["identity_snapshot_id"]
    assert versions[0]["briefRevisionId"] == second["creative_brief_revision_id"]
    assert versions[0]["boundaryRevisionId"] == second["fact_boundary_revision_id"]


@pytest.mark.parametrize("state", ["incomplete", "stale", "check_blocked", "render_unready"])
def test_overview_projects_master_risks_with_unit_action(client, db_session, state):
    project, path = _unit(client, db_session, "graphic" if state == "render_unready" else "text")
    master = client.post(path, json={"idempotency_key": "risk", "payload": {"canvases": []} if state == "render_unready" else {"markdown": "正文"}}, headers=HEADERS).json()
    if state == "stale":
        client.post(f"/api/v1/content-projects/{project}/brief/revisions", json={"expected_revision": 1, "objective": "新方向"}, headers=HEADERS)
    elif state == "check_blocked":
        from app.models import FactPackItem
        db_session.query(FactPackItem).one().public_use_allowed = False
        db_session.commit()
        client.post(f"{path}/{master['id']}/checks", headers=HEADERS)
    overview = client.get(f"/api/v1/content-projects/{project}/overview", headers=HEADERS).json()
    assert f"master_{state}" in {risk["code"] for risk in overview["risks"]}
    assert overview["nextAction"]["href"] == f"/projects/{project}/units/{path.split('/')[6]}/production"


def test_unknown_delivery_precedes_master_stale_risk(client, db_session):
    path, master = _ready(client, db_session)
    frozen = _freeze(client, path, master).json()
    from app.models import utcnow
    db_session.add(DeliveryTarget(content_asset_id=frozen["id"], channel="wechat", content_form="article", action="copy_package", account_ref="manual", authorization_version="v1", approved_candidate_hash=frozen["candidate_hash"], authorized_by=HEADERS["X-Studio-User"], authorized_at=utcnow(), requested_at=utcnow(), status="reconciliation_needed"))
    db_session.commit()
    project = path.split("/")[4]
    client.post(f"/api/v1/content-projects/{project}/brief/revisions", json={"expected_revision": 1, "objective": "新方向"}, headers=HEADERS)
    overview = client.get(f"/api/v1/content-projects/{project}/overview", headers=HEADERS).json()
    assert overview["nextAction"]["code"] == "delivery.reconcile"
    assert "master_stale" in {risk["code"] for risk in overview["risks"]}


def test_legacy_diff_remains_textual():
    asset = ContentAsset(id=1, candidate_manifest_json={"schema_version": 3, "content": {"body_markdown": "历史正文"}})
    assert candidate_diff(None, asset)["text"]["after_chars"] == 4


@pytest.mark.parametrize("modality", ["text", "graphic", "video"])
def test_v3_preview_retains_frozen_body_for_every_unit_modality(modality):
    from app.services.project_review_projection import candidate_preview

    asset = ContentAsset(id=1, title="旧候选", candidate_manifest_json={"schema_version": 3, "project": {"modality": modality}, "content": {"body_markdown": "旧冻结正文"}})
    preview = candidate_preview(asset)
    assert preview["markdown"] == "旧冻结正文"
    assert preview["modality"] == "text"
    assert preview["source_modality"] == modality
