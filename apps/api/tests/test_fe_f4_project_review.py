"""Project-first review and distribution contracts."""


from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
PNG = b"\x89PNG\r\n\x1a\n" + b"m2" * 8

from app.models import (
    ContentAsset,
    DeliveryAttempt,
    DeliveryTarget,
    Review,
)


def test_candidate_review_and_target_schema_support_project_flow(db_session):
    inspector = inspect(db_session.bind)
    asset = {column["name"]: column for column in inspector.get_columns("content_asset")}
    review = {column["name"]: column for column in inspector.get_columns("review")}
    target = {column["name"]: column for column in inspector.get_columns("delivery_target")}

    assert {"project_id", "content_unit_id", "identity_snapshot_id", "workflow_run_id", "candidate_hash"} <= set(asset)
    assert all(asset[name]["nullable"] for name in ("fact_pack_id", "fact_pack_version", "approved_revision"))
    assert {"content_asset_id"} <= set(review)
    assert review["revision_no"]["nullable"]
    assert target["content_account_id"]["nullable"]
    assert not target["authorization_account_key"]["nullable"]
    unique = {constraint["name"]: tuple(constraint["column_names"]) for constraint in inspector.get_unique_constraints("delivery_target")}
    assert "authorization_account_key" in unique["uq_delivery_target_authorization"]
    assert "account_ref" not in unique["uq_delivery_target_authorization"]
    asset_unique = {constraint["name"]: tuple(constraint["column_names"]) for constraint in inspector.get_unique_constraints("content_asset")}
    assert asset_unique["uq_project_candidate_hash"] == ("project_id", "content_unit_id", "candidate_hash")


def test_project_bound_raw_delivery_ids_do_not_disclose_to_other_owner(client, db_session):
    alice = {"X-Studio-User": "owner@studio.local"}
    bob = {"X-Studio-User": "stranger@studio.local"}
    persona_id = client.post("/api/v1/content-personas", json={"name": "作者"}, headers=alice).json()["id"]
    project_id = client.post("/api/v1/content-projects", json={"title": "私有项目"}, headers=alice).json()["id"]
    unit_id = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "稿件", "persona_id": persona_id, "modality": "text"}, headers=alice).json()["id"]
    asset = ContentAsset(project_id=project_id, content_unit_id=unit_id, channel="wechat", title="稿件", final_body="正文", status="approved", candidate_hash="a" * 64, approved_candidate_hash="a" * 64, candidate_manifest_json={"schema_version": 3})
    db_session.add(asset)
    db_session.flush()
    target = DeliveryTarget(content_asset_id=asset.id, channel="wechat", content_form="article", account_ref="owner", action="copy_package", authorization_version="v1", approved_candidate_hash="a" * 64, status="target_authorized")
    db_session.add(target)
    db_session.commit()

    assert client.get(f"/api/v1/delivery-targets/{target.id}", headers=bob).status_code == 404
    assert client.post(f"/api/v1/delivery-targets/{target.id}/execute", headers=bob).status_code == 404
    assert client.post(f"/api/v1/delivery-targets/{target.id}/reconcile", json={"resolution": "delivered", "note": "platform checked"}, headers=bob).status_code == 404
    assert client.post(f"/api/v1/delivery-targets/{target.id}/receipt", json={"status": "human_confirmed"}, headers=bob).status_code == 404
    assert client.get(f"/api/v1/delivery-targets/{target.id}/package.zip", headers=bob).status_code == 404
    assert client.get(f"/api/v1/assets/{asset.id}/delivery-targets", headers=bob).status_code == 404
    assert client.get(f"/api/v1/delivery-targets/{target.id}", headers=alice).status_code == 200
    target.status = "reconciliation_needed"
    db_session.add(DeliveryAttempt(target_id=target.id, attempt_no=1, idempotency_key="u" * 64, status="unknown"))
    db_session.commit()
    assert client.post(f"/api/v1/delivery-targets/{target.id}/receipt", json={"status": "human_confirmed"}, headers=alice).status_code == 409
    assert client.get(f"/api/v1/delivery-targets/{target.id}", headers=alice).json()["status"] == "reconciliation_needed"
    reconciled = client.post(f"/api/v1/delivery-targets/{target.id}/reconcile", json={"resolution": "delivered", "note": "platform checked"}, headers=alice)
    assert reconciled.status_code == 200
    assert db_session.query(DeliveryAttempt).filter_by(target_id=target.id).one().response_metadata_json["reconciled"] == "delivered"


def test_project_account_identity_is_distinct_from_account_ref(client, db_session, monkeypatch):
    from app.services.candidates import candidate_hash

    alice = {"X-Studio-User": "account-owner@studio.local"}
    persona_id = client.post("/api/v1/content-personas", json={"name": "作者"}, headers=alice).json()["id"]
    first_account = client.post(f"/api/v1/content-personas/{persona_id}/accounts", json={"name": "甲号"}, headers=alice).json()["id"]
    second_account = client.post(f"/api/v1/content-personas/{persona_id}/accounts", json={"name": "乙号"}, headers=alice).json()["id"]
    project_id = client.post("/api/v1/content-projects", json={"title": "账号授权"}, headers=alice).json()["id"]
    unit_id = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "稿件", "persona_id": persona_id, "modality": "text", "channel_id": "wechat"}, headers=alice).json()["id"]
    manifest = {"schema_version": 3}
    frozen_hash = candidate_hash(manifest)
    asset = ContentAsset(project_id=project_id, content_unit_id=unit_id, channel="wechat", content_form="article", title="稿件", final_body="正文", status="approved", candidate_hash=frozen_hash, approved_candidate_hash=frozen_hash, candidate_manifest_json=manifest)
    db_session.add(asset)
    db_session.flush()
    db_session.add(Review(content_asset_id=asset.id, decision="approved", reviewer_id="account-owner@studio.local", candidate_hash=frozen_hash))
    db_session.commit()

    base = {"channel": "wechat", "content_form": "article", "account_ref": "shared-alias", "authorization_version": "v1", "action": "copy_package"}
    first = client.post(f"/api/v1/assets/{asset.id}/delivery-targets", json={**base, "content_account_id": first_account}, headers=alice)
    second = client.post(f"/api/v1/assets/{asset.id}/delivery-targets", json={**base, "content_account_id": second_account}, headers=alice)
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert first.json()["id"] != second.json()["id"]
    assert first.json()["content_account_id"] == first_account
    assert second.json()["content_account_id"] == second_account
    repeated = client.post(f"/api/v1/assets/{asset.id}/delivery-targets", json={**base, "content_account_id": first_account}, headers=alice)
    assert repeated.json()["id"] == first.json()["id"]
    original_scalars = db_session.scalars
    race = {"missed": False}

    class EmptyResult:
        def first(self):
            return None

    def first_lookup_misses(statement, *args, **kwargs):
        if "delivery_target.authorization_account_key" in str(statement) and not race["missed"]:
            race["missed"] = True
            return EmptyResult()
        return original_scalars(statement, *args, **kwargs)

    def duplicate_flush(*args, **kwargs):
        raise IntegrityError("INSERT delivery_target", {}, Exception("duplicate authorization"))

    with monkeypatch.context() as patcher:
        patcher.setattr(db_session, "scalars", first_lookup_misses)
        patcher.setattr(db_session, "flush", duplicate_flush)
        concurrent = client.post(f"/api/v1/assets/{asset.id}/delivery-targets", json={**base, "content_account_id": first_account}, headers=alice)
    assert race["missed"] and concurrent.status_code == 201 and concurrent.json()["id"] == first.json()["id"]
    changed_ref = client.post(f"/api/v1/assets/{asset.id}/delivery-targets", json={**base, "account_ref": "new-alias", "content_account_id": first_account}, headers=alice)
    assert changed_ref.status_code == 409


def test_review_projection_only_uses_current_candidate_targets(client, db_session):
    from app.services.candidates import candidate_hash

    owner = {"X-Studio-User": "projection-owner@studio.local"}
    stranger = {"X-Studio-User": "projection-stranger@studio.local"}
    persona_id = client.post("/api/v1/content-personas", json={"name": "作者"}, headers=owner).json()["id"]
    project_id = client.post("/api/v1/content-projects", json={"title": "投影项目"}, headers=owner).json()["id"]
    unit_id = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "稿件", "persona_id": persona_id, "modality": "text"}, headers=owner).json()["id"]
    old_manifest = {"schema_version": 3, "content": {"title": "旧稿"}}
    new_manifest = {"schema_version": 3, "content": {"title": "新稿"}}
    old_hash = candidate_hash(old_manifest)
    new_hash = candidate_hash(new_manifest)
    old = ContentAsset(project_id=project_id, content_unit_id=unit_id, channel="wechat", title="旧稿", final_body="旧", status="approved", candidate_hash=old_hash, approved_candidate_hash=old_hash, candidate_manifest_json=old_manifest)
    new = ContentAsset(project_id=project_id, content_unit_id=unit_id, channel="wechat", title="新稿", final_body="新", status="frozen", candidate_hash=new_hash, candidate_manifest_json=new_manifest)
    db_session.add_all([old, new])
    db_session.flush()
    db_session.add(Review(content_asset_id=old.id, decision="approved", reviewer_id="projection-owner@studio.local", candidate_hash=old_hash))
    db_session.add(DeliveryTarget(content_asset_id=old.id, channel="wechat", content_form="article", account_ref="owner", action="copy_package", authorization_version="v1", approved_candidate_hash=old_hash, status="reconciliation_needed"))
    db_session.commit()
    path = f"/api/v1/review-center/projects/{project_id}/units/{unit_id}"
    assert client.get(path, headers=stranger).status_code == 404
    current = client.get(path, headers=owner)
    assert current.status_code == 200, current.text
    assert current.json()["current_candidate"]["id"] == new.id
    assert current.json()["summary"] == "blocked"
    assert current.json()["history"][0]["id"] == old.id
    assert client.get(f"/api/v1/review-center/projects/{project_id}/units/{unit_id}/candidates/{old.id}", headers=owner).status_code == 200
    historical_authorization = client.post(f"/api/v1/assets/{old.id}/delivery-targets", json={
        "channel": "wechat", "content_form": "article", "account_ref": "owner",
        "authorization_version": "v2", "action": "copy_package",
    }, headers=owner)
    assert historical_authorization.status_code == 409
    assert client.post(f"/api/v1/content-projects/{project_id}/units/{unit_id}/candidates/{old.id}/approve", json={"candidate_hash": old_hash}, headers=owner).status_code == 409
    assert client.post(f"/api/v1/content-projects/{project_id}/units/{unit_id}/candidates/{old.id}/request-changes", json={"candidate_hash": old_hash}, headers=owner).status_code == 409
    db_session.add(DeliveryTarget(content_asset_id=new.id, channel="wechat", content_form="article", account_ref="owner", action="copy_package", authorization_version="v1", approved_candidate_hash=new_hash, status="reconciliation_needed"))
    db_session.commit()
    assert client.get(path, headers=owner).json()["summary"] == "unknown"


