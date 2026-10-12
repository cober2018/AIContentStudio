"""Project-first review and distribution contracts."""

import io
import json
import zipfile

import pytest
from fastapi import HTTPException
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from test_candidate_manifest_v2 import PNG, _ready_checks
from test_candidate_manifest_v2 import env as draft_env  # noqa: F401

from app.models import (
    ContentAsset,
    DeliveryAttempt,
    DeliveryTarget,
    Draft,
    FactPackItem,
    ProjectEvent,
    ProjectFactBoundaryRevision,
    ProjectWorkflowOutput,
    Review,
    Workflow,
    WorkflowRun,
    utcnow,
)


def test_candidate_review_and_target_schema_support_project_flow(db_session):
    inspector = inspect(db_session.bind)
    asset = {column["name"]: column for column in inspector.get_columns("content_asset")}
    review = {column["name"]: column for column in inspector.get_columns("review")}
    target = {column["name"]: column for column in inspector.get_columns("delivery_target")}

    assert {"project_id", "content_unit_id", "identity_snapshot_id", "workflow_run_id", "candidate_hash"} <= set(asset)
    assert all(asset[name]["nullable"] for name in ("draft_id", "topic_brief_id", "fact_pack_id", "fact_pack_version", "approved_revision"))
    assert {"content_asset_id"} <= set(review)
    assert review["draft_id"]["nullable"] and review["revision_no"]["nullable"]
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
    assert client.get(f"/api/v1/assets/{asset.id}", headers=bob).status_code == 404
    assert client.get(f"/api/v1/assets/{asset.id}/media", headers=bob).status_code == 404
    assert client.get(f"/api/v1/assets/{asset.id}/cover.svg").status_code == 404
    assert client.get(f"/api/v1/assets/{asset.id}/media/1/raw").status_code == 404
    assert all(row["id"] != asset.id for row in client.get("/api/v1/assets", headers=bob).json())
    assert client.post(f"/api/v1/assets/{asset.id}/media", json={"kind": "cover"}, headers=alice).status_code == 409
    assert client.post(f"/api/v1/assets/{asset.id}/export", json={"fmt": "md"}, headers=alice).status_code == 409
    assert client.get(f"/api/v1/article-handoff/assets/{asset.id}/targets", headers=bob).status_code == 404
    assert client.post(f"/api/v1/article-handoff/targets/{target.id}/package", headers=bob).status_code == 404
    assert client.post(f"/api/v1/article-handoff/targets/{target.id}/receipt", json={"status": "human_confirmed"}, headers=bob).status_code == 404
    assert client.post(f"/api/v1/article-handoff/targets/{target.id}/feedback", json={"body": "x"}, headers=bob).status_code == 404
    assert client.post(f"/api/v1/article-handoff/targets/{target.id}/package", headers=alice).status_code == 409
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


def test_freeze_without_verified_project_output_is_typed_blocker(client, db_session):
    alice = {"X-Studio-User": "freeze-owner@studio.local"}
    persona_id = client.post("/api/v1/content-personas", json={"name": "作者"}, headers=alice).json()["id"]
    project_id = client.post("/api/v1/content-projects", json={"title": "待冻结"}, headers=alice).json()["id"]
    unit_id = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "文章", "persona_id": persona_id, "modality": "text"}, headers=alice).json()["id"]
    response = client.post(f"/api/v1/content-projects/{project_id}/units/{unit_id}/candidates/freeze", json={"project_output_id": 999}, headers=alice)
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "unsupported_source"
    assert db_session.query(ContentAsset).count() == 0


def test_v3_manual_package_adapter_does_not_require_legacy_draft_ids(client, draft_env):  # noqa: F811
    from app.services import materials as materials_service
    from app.services.candidates import candidate_hash

    db, topic, _draft = draft_env
    owner = {"X-Studio-User": "editor@studio.local"}
    persona_id = client.post("/api/v1/content-personas", json={"name": "作者"}, headers=owner).json()["id"]
    project_id = client.post("/api/v1/content-projects", json={"title": "无旧稿包"}, headers=owner).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "内容", "persona_id": persona_id, "modality": "text", "channel_id": "wechat"}, headers=owner).json()
    boundary = ProjectFactBoundaryRevision(project_id=project_id, revision_no=1, fact_pack_id=topic.fact_pack_id, fact_pack_version=topic.fact_pack_version, fact_pack_checksum=topic.fact_pack.checksum)
    db.add(boundary)
    db.flush()
    material = materials_service.create_material(db, kind="image", title="独立封面")
    revision = materials_service.create_revision(db, material, content=PNG, suffix=".png", declared_mime="image/png", public_use_allowed=True, rights_status="cleared")
    manifest = {
        "schema_version": 3,
        "project": {"id": project_id, "unit_id": unit["id"]},
        "identity": {"snapshot_id": unit["identity_snapshot_id"]},
        "evidence": {"boundary_id": boundary.id},
        "production": {"run_id": 1},
        "content": {"title": "独立内容", "body_markdown": "可发布正文"},
        "render": {"payload": {"markdown": "可发布正文"}, "content_hash": "r" * 64},
        "media": [{"material_revision_id": revision.id, "hash": revision.content_hash, "role": "cover", "sort_order": 0, "rights": {"public_use_allowed": True}}],
    }
    frozen_hash = candidate_hash(manifest)
    asset = ContentAsset(project_id=project_id, content_unit_id=unit["id"], identity_snapshot_id=unit["identity_snapshot_id"], channel="wechat", content_form="article", title="独立内容", final_body="可发布正文", status="approved", candidate_hash=frozen_hash, approved_candidate_hash=frozen_hash, candidate_manifest_json=manifest)
    db.add(asset)
    db.flush()
    target = DeliveryTarget(content_asset_id=asset.id, channel="wechat", content_form="article", account_ref="manual", action="manual_handoff", authorization_version="v1", approved_candidate_hash=frozen_hash, authorized_by="editor@studio.local", status="target_authorized")
    db.add(target)
    db.commit()
    assert asset.draft_id is None and asset.topic_brief_id is None and asset.fact_pack_id is None
    response = client.get(f"/api/v1/delivery-targets/{target.id}/package.zip", headers=owner)
    assert response.status_code == 200, response.text
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert json.loads(archive.read("manifest.json"))["schema_version"] == 3
        assert archive.read("content.md").decode() == "可发布正文"
        assert archive.read(f"media/00-{revision.id}.png") == PNG
    receipt = client.post(f"/api/v1/delivery-targets/{target.id}/receipt", json={"status": "human_confirmed"}, headers=owner)
    assert receipt.status_code == 200 and receipt.json()["status"] == "human_confirmed"


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


def test_freeze_source_never_substitutes_newer_draft_for_old_workflow_output(client, draft_env):  # noqa: F811
    from app.models import ContentUnit
    from app.services.project_review import _source

    db, _topic, draft = draft_env
    owner = {"X-Studio-User": "editor@studio.local"}
    persona_id = client.post("/api/v1/content-personas", json={"name": "作者"}, headers=owner).json()["id"]
    project_id = client.post("/api/v1/content-projects", json={"title": "输出血缘"}, headers=owner).json()["id"]
    unit_id = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "文章", "persona_id": persona_id, "modality": "text"}, headers=owner).json()["id"]
    workflow = Workflow(name="输出血缘", workflow_key="lineage.test", version=1, status="published", checksum="w" * 64, definition_json={"nodes": [], "edges": []})
    db.add(workflow)
    db.flush()
    run = WorkflowRun(workflow_id=workflow.id, content_unit_id=unit_id, identity_snapshot_id=db.get(ContentUnit, unit_id).identity_snapshot_id, status="succeeded", context_json={}, params_json={}, workflow_key="test", workflow_version=1, definition_checksum="w" * 64)
    db.add(run)
    db.flush()
    draft.content_job.workflow_run_id = run.id
    output = ProjectWorkflowOutput(project_id=project_id, unit_id=unit_id, run_id=run.id, node_id="generate", output_kind="draft", entity_id=draft.id)
    newer = Draft(content_job_id=draft.content_job_id, revision_no=2, title="新稿", body="新稿正文", input_hash="n" * 64)
    db.add_all([output, newer])
    db.commit()
    with pytest.raises(HTTPException) as caught:
        _source(db, db.get(ContentUnit, unit_id), output.id)
    assert caught.value.detail["code"] == "stale_source"


def test_project_candidate_freeze_then_approve_are_separate_and_idempotent(client, draft_env):  # noqa: F811
    from app.services import checks as checks_service
    from app.services import factchecker
    from app.services import materials as materials_service

    db, topic, draft = draft_env
    editor = {"X-Studio-User": "editor@studio.local"}
    persona_id = client.post("/api/v1/content-personas", json={"name": "作者"}, headers=editor).json()["id"]
    project_id = client.post("/api/v1/content-projects", json={"title": "审核项目"}, headers=editor).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "文章", "persona_id": persona_id, "modality": "text", "channel_id": "wechat"}, headers=editor).json()
    workflow = Workflow(name="文章", workflow_key="project.review", version=1, status="published", checksum="w" * 64, definition_json={"nodes": [], "edges": []})
    db.add(workflow)
    db.flush()
    run = WorkflowRun(workflow_id=workflow.id, content_unit_id=unit["id"], identity_snapshot_id=unit["identity_snapshot_id"], status="succeeded", context_json={}, params_json={}, workflow_key=workflow.workflow_key, workflow_version=1, definition_checksum=workflow.checksum)
    db.add(run)
    db.flush()
    draft.content_job.workflow_run_id = run.id
    output = ProjectWorkflowOutput(project_id=project_id, unit_id=unit["id"], run_id=run.id, node_id="generate", output_kind="draft", entity_id=draft.id, provenance_json={})
    db.add(output)
    db.add(ProjectFactBoundaryRevision(project_id=project_id, revision_no=1, fact_pack_id=topic.fact_pack_id, fact_pack_version=topic.fact_pack_version, fact_pack_checksum=topic.fact_pack.checksum))
    material = materials_service.create_material(db, kind="image", title="封面")
    revision = materials_service.create_revision(db, material, content=PNG, suffix=".png", declared_mime="image/png", public_use_allowed=True, rights_status="cleared")
    materials_service.attach_to_draft(db, draft, revision, role="cover")
    stranger = {"X-Studio-User": "different-owner@studio.local"}
    media_id = draft.media[0].id
    assert client.get(f"/api/v1/content-jobs/{draft.content_job_id}", headers=stranger).status_code == 404
    assert client.get(f"/api/v1/drafts/{draft.id}", headers=stranger).status_code == 404
    assert client.get(f"/api/v1/article-handoff/drafts/{draft.id}/media", headers=stranger).status_code == 404
    assert client.get(f"/api/v1/article-handoff/drafts/{draft.id}/media/{media_id}/raw", headers=stranger).status_code == 404
    assert client.get(f"/api/v1/drafts/{draft.id}/checks", headers=stranger).status_code == 404
    assert client.get(f"/api/v1/drafts/{draft.id}/document", headers=stranger).status_code == 404
    assert client.delete(f"/api/v1/article-handoff/drafts/{draft.id}/media/{media_id}", headers=stranger).status_code == 404
    fact_result = factchecker.run_fact_check(draft.body, [], "topic", forbidden_words=[], source_text="")
    draft.fact_check_json = fact_result.to_json() | {"input_hash": draft.input_hash}
    db.commit()
    checks_service.run_fact_check(db, draft, draft.fact_check_json, draft.input_hash)
    _ready_checks(db, draft)

    base = f"/api/v1/content-projects/{project_id}/units/{unit['id']}/candidates"
    freeze = client.post(f"{base}/freeze", json={"project_output_id": output.id}, headers=editor)
    assert freeze.status_code == 201, freeze.text
    candidate = freeze.json()
    assert candidate["status"] == "frozen"
    assert candidate["approved_candidate_hash"] is None
    assert candidate["manifest"]["schema_version"] == 3
    assert candidate["manifest"]["identity"]["snapshot_id"] == unit["identity_snapshot_id"]
    assert candidate["manifest"]["production"]["run_id"] == run.id
    assert client.get(f"/api/v1/review-center/projects/{project_id}/units/{unit['id']}", headers=editor).json()["summary"] == "waiting_review"
    repeated = client.post(f"{base}/freeze", json={"project_output_id": output.id}, headers=editor)
    assert repeated.status_code == 201 and repeated.json()["id"] == candidate["id"]
    assert client.get(f"{base}", headers=editor).json()[0]["status"] == "frozen"
    premature = client.post(f"{base}/{candidate['id']}/delivery-authorizations", json={
        "channel": "wechat", "content_form": "article", "account_ref": "manual-account",
        "authorization_version": "v1", "action": "manual_handoff",
    }, headers=editor)
    assert premature.status_code == 409
    wrong_hash = client.post(f"{base}/{candidate['id']}/approve", json={"candidate_hash": "x" * 64}, headers=editor)
    assert wrong_hash.status_code == 409
    changes = client.post(f"{base}/{candidate['id']}/request-changes", json={"candidate_hash": candidate["candidate_hash"], "comment": "核对标题"}, headers=editor)
    assert changes.status_code == 200, changes.text
    assert changes.json()["candidate_hash"] == candidate["candidate_hash"]
    assert changes.json()["manifest"] == candidate["manifest"]
    assert db.query(Review).filter_by(content_asset_id=candidate["id"], decision="changes_requested").count() == 1
    approval = client.post(f"{base}/{candidate['id']}/approve", json={"candidate_hash": candidate["candidate_hash"]}, headers=editor)
    assert approval.status_code == 200, approval.text
    assert approval.json()["status"] == "approved"
    assert db.query(Review).filter_by(content_asset_id=candidate["id"], decision="approved").count() == 1
    late_changes = client.post(f"{base}/{candidate['id']}/request-changes", json={"candidate_hash": candidate["candidate_hash"]}, headers=editor)
    assert late_changes.status_code == 409
    account_id = client.post(f"/api/v1/content-personas/{persona_id}/accounts", json={"name": "公众号"}, headers=editor).json()["id"]
    authorization = client.post(f"{base}/{candidate['id']}/delivery-authorizations", json={
        "channel": "wechat", "content_form": "article", "account_ref": "manual-account",
        "content_account_id": account_id, "authorization_version": "v1", "action": "manual_handoff",
    }, headers=editor)
    assert authorization.status_code == 201, authorization.text
    target_id = authorization.json()["id"]
    archive_response = client.get(f"/api/v1/delivery-targets/{target_id}/package.zip", headers=editor)
    assert archive_response.status_code == 200, archive_response.text
    assert client.get(f"/api/v1/delivery-targets/{target_id}", headers=editor).json()["status"] == "awaiting_manual_receipt"
    with zipfile.ZipFile(io.BytesIO(archive_response.content)) as archive:
        package_manifest = json.loads(archive.read("manifest.json"))
        assert package_manifest["schema_version"] == 3
        assert package_manifest["candidate"]["id"] == candidate["id"]
        assert archive.read("content.md")
        assert any(name.startswith("media/") and archive.read(name) == PNG for name in archive.namelist())
    preview = client.post(f"/api/v1/delivery-targets/{target_id}/package", headers=editor)
    assert preview.status_code == 200, preview.text
    assert preview.json()["manifest"]["schema_version"] == 3
    receipt = client.post(f"/api/v1/delivery-targets/{target_id}/receipt", json={"status": "human_confirmed", "evidence_ref": "local-proof"}, headers=editor)
    assert receipt.status_code == 200, receipt.text
    assert receipt.json()["status"] == "human_confirmed"
    events = {row.event_type for row in db.query(ProjectEvent).filter_by(project_id=project_id).all()}
    assert {"candidate.frozen", "content.changes_requested", "content.approved", "delivery.authorized", "delivery.receipt_recorded"} <= events
    versions = client.get(f"/api/v1/content-projects/{project_id}/versions", headers=editor).json()
    assert versions["candidates"][0]["id"] == str(candidate["id"])
    assert versions["approvals"][0]["status"] == "approved"
    assert versions["deliveryTargets"][0]["id"] == str(target_id)
    overview = client.get(f"/api/v1/content-projects/{project_id}/overview", headers=editor).json()
    assert overview["review"]["units"][0]["summary"] == "delivered"
    db.add(FactPackItem(fact_pack_id=topic.fact_pack_id, sort_order=1, evidence_kind="fact", snapshot_checksum="z" * 64, public_use_allowed=True, public_use_revoked_at=utcnow()))
    db.commit()
    assert client.get(f"/api/v1/delivery-targets/{target_id}/package.zip", headers=editor).status_code == 409
    draft.status = "ready_for_review"
    db.commit()
    legacy = client.post(f"/api/v1/reviews/drafts/{draft.id}/approve", json={}, headers=editor)
    assert legacy.status_code == 409
    assert all(item["draft_id"] != draft.id for item in client.get("/api/v1/reviews/queue", headers=editor).json())
    assert client.delete(f"/api/v1/content-projects/{project_id}/units/{unit['id']}", headers=editor).status_code == 204
    assert client.get(f"{base}/{candidate['id']}", headers=editor).status_code == 200
    assert client.post(f"{base}/{candidate['id']}/approve", json={"candidate_hash": candidate["candidate_hash"]}, headers=editor).status_code == 409
    assert client.get(f"/api/v1/delivery-targets/{target_id}", headers=editor).status_code == 200
    assert client.post(f"/api/v1/delivery-targets/{target_id}/package", headers=editor).status_code == 409
