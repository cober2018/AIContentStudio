"""FE-F3A project-core persistence and lifecycle contracts."""

import pytest
from sqlalchemy import inspect, select

from app.models import ContentProject, ProjectEvent


def test_project_core_tables_exist(db_session):
    tables = set(inspect(db_session.bind).get_table_names())
    assert {
        "creative_brief_revision",
        "project_source_binding",
        "project_fact_boundary_revision",
        "project_material_reference",
        "project_event",
    } <= tables


def test_project_create_and_archive_preserve_history(client, db_session):
    headers = {"X-Studio-User": "alice@studio.local"}
    created = client.post("/api/v1/content-projects", json={"title": "FE-F3A"}, headers=headers)
    assert created.status_code == 201
    project_id = created.json()["id"]
    endpoint = f"/api/v1/content-projects/{project_id}"
    assert client.patch(endpoint, json={"status": "archived"}, headers=headers).status_code == 422
    assert client.delete(endpoint, headers=headers).status_code == 204
    assert client.delete(endpoint, headers=headers).status_code == 204
    assert client.get(endpoint, headers=headers).json()["status"] == "archived"
    assert db_session.get(ContentProject, project_id) is not None
    assert client.patch(endpoint, json={"title": "should fail"}, headers=headers).status_code == 409
    events = db_session.scalars(select(ProjectEvent).where(ProjectEvent.project_id == project_id).order_by(ProjectEvent.id)).all()
    assert [event.event_type for event in events] == ["project.created", "project.archived"]


def test_project_unit_changes_record_activity_without_erasing_history(client, db_session):
    headers = {"X-Studio-User": "alice@studio.local"}
    persona = client.post("/api/v1/content-personas", json={"name": "作者"}, headers=headers).json()["id"]
    project_id = client.post("/api/v1/content-projects", json={"title": "活动项目"}, headers=headers).json()["id"]
    endpoint = f"/api/v1/content-projects/{project_id}"
    assert client.patch(endpoint, json={"title": "活动项目 2"}, headers=headers).status_code == 200
    unit = client.post(f"{endpoint}/units", json={"title": "文章", "persona_id": persona, "modality": "text"}, headers=headers)
    assert unit.status_code == 201
    unit_endpoint = f"{endpoint}/units/{unit.json()['id']}"
    assert client.patch(unit_endpoint, json={"status": "archived"}, headers=headers).status_code == 422
    assert client.patch(unit_endpoint, json={"title": "文章 2"}, headers=headers).status_code == 200
    assert client.delete(unit_endpoint, headers=headers).status_code == 204
    assert client.delete(endpoint, headers=headers).status_code == 204
    events = db_session.scalars(select(ProjectEvent).where(ProjectEvent.project_id == project_id).order_by(ProjectEvent.id)).all()
    assert [event.event_type for event in events] == [
        "project.created", "project.updated", "unit.created", "unit.updated", "unit.deleted", "project.archived"
    ]


def test_brief_revision_is_append_only_and_conflict_safe(client, db_session):
    alice = {"X-Studio-User": "alice@studio.local"}
    bob = {"X-Studio-User": "bob@studio.local"}
    project_id = client.post("/api/v1/content-projects", json={"title": "Brief"}, headers=alice).json()["id"]
    endpoint = f"/api/v1/content-projects/{project_id}/brief"
    assert client.patch(f"/api/v1/content-projects/{project_id}", json={"objective": "旁路目标"}, headers=alice).status_code == 422
    payload = {
        "expected_revision": 0,
        "objective": "V1 目标",
        "primary_audience": "开发者",
        "core_message": "事实先行",
        "angle": "产品说明",
        "required_evidence": ["source:1"],
        "content_constraints": ["不夸大"],
        "identity_scope": [],
        "modality_scope": ["text"],
        "channel_scope": ["wechat"],
        "cta": "了解更多",
        "references": [],
    }
    first = client.post(f"{endpoint}/revisions", json=payload, headers=alice)
    assert first.status_code == 201, first.text
    assert first.json()["revision_no"] == 1
    assert len(first.json()["checksum"]) == 64
    stale = client.post(f"{endpoint}/revisions", json=payload, headers=alice)
    assert stale.status_code == 409
    second = client.post(f"{endpoint}/revisions", json={**payload, "expected_revision": 1, "objective": "V2 目标"}, headers=alice)
    assert second.status_code == 201, second.text
    assert second.json()["revision_no"] == 2
    same_content = client.post(f"{endpoint}/revisions", json={**payload, "expected_revision": 2, "objective": "V2 目标"}, headers=alice)
    assert same_content.status_code == 201
    assert same_content.json()["revision_no"] == 3
    assert same_content.json()["checksum"] == second.json()["checksum"]
    assert client.get(endpoint, headers=alice).json()["objective"] == "V2 目标"
    assert [row["objective"] for row in client.get(f"{endpoint}/revisions", headers=alice).json()] == ["V2 目标", "V2 目标", "V1 目标"]
    assert client.get(f"{endpoint}/revisions/{first.json()['id']}", headers=alice).json()["objective"] == "V1 目标"
    assert client.get(endpoint, headers=bob).status_code == 404
    events = db_session.scalars(select(ProjectEvent).where(ProjectEvent.project_id == project_id, ProjectEvent.event_type == "brief.revision_created")).all()
    assert len(events) == 3


def test_project_source_binding_reuses_global_source_and_detach_is_reversible(client, db_session):
    alice = {"X-Studio-User": "alice@studio.local"}
    bob = {"X-Studio-User": "bob@studio.local"}
    project_id = client.post("/api/v1/content-projects", json={"title": "Evidence"}, headers=alice).json()["id"]
    source = client.post("/api/v1/sources/text", json={"title": "来源", "content": "原始文本"}, headers=alice)
    assert source.status_code == 201, source.text
    source_id = source.json()["id"]
    endpoint = f"/api/v1/content-projects/{project_id}/sources"
    first = client.post(endpoint, json={"source_document_id": source_id}, headers=alice)
    assert first.status_code == 201, first.text
    assert client.post(endpoint, json={"source_document_id": source_id}, headers=alice).json()["id"] == first.json()["id"]
    assert len(db_session.scalars(select(ProjectEvent).where(ProjectEvent.project_id == project_id, ProjectEvent.event_type == "source.attached")).all()) == 1
    assert len(client.get(endpoint, headers=alice).json()) == 1
    assert client.delete(f"{endpoint}/{source_id}", headers=alice).status_code == 204
    assert client.get(endpoint, headers=alice).json() == []
    assert client.get(f"/api/v1/sources/{source_id}", headers=alice).status_code == 200
    assert client.post(endpoint, json={"source_document_id": source_id}, headers=alice).json()["id"] == first.json()["id"]
    assert client.get(endpoint, headers=bob).status_code == 404


def test_fact_boundary_rejects_draft_and_keeps_prior_revision(client, db_session):
    from app.models import FactPack, FactPackStatus

    headers = {"X-Studio-User": "alice@studio.local"}
    project_id = client.post("/api/v1/content-projects", json={"title": "Boundary"}, headers=headers).json()["id"]
    draft = FactPack(name="draft boundary", version=1)
    frozen = FactPack(name="frozen boundary", version=1, status=FactPackStatus.frozen.value, checksum="a" * 64)
    db_session.add_all([draft, frozen])
    db_session.commit()
    endpoint = f"/api/v1/content-projects/{project_id}/fact-boundary"
    assert client.post(endpoint, json={"fact_pack_id": draft.id, "expected_revision": 0}, headers=headers).status_code in {409, 422}
    first = client.post(endpoint, json={"fact_pack_id": frozen.id, "expected_revision": 0}, headers=headers)
    assert first.status_code == 201, first.text
    assert first.json()["revision_no"] == 1
    assert client.post(endpoint, json={"fact_pack_id": frozen.id, "expected_revision": 0}, headers=headers).status_code == 409
    assert client.get(endpoint, headers=headers).json()["fact_pack_checksum"] == "a" * 64
    assert len(client.get(f"{endpoint}/revisions", headers=headers).json()) == 1


def test_project_boundary_clone_freeze_and_bind_keeps_old_history(client):
    headers = {"X-Studio-User": "alice@studio.local"}
    project_id = client.post("/api/v1/content-projects", json={"title": "Boundary Flow"}, headers=headers).json()["id"]
    pack = client.post("/api/v1/fact-packs", json={"name": "project evidence"}, headers=headers)
    assert pack.status_code == 201
    pack_id = pack.json()["id"]
    item = client.post(f"/api/v1/fact-packs/{pack_id}/items", json={"evidence_kind": "author_opinion", "snapshot": {"excerpt": "观点", "attribution": "作者", "source_locator": "段落 1"}}, headers=headers)
    assert item.status_code == 201, item.text
    assert client.post(f"/api/v1/fact-packs/{pack_id}/freeze", headers=headers).status_code == 200
    endpoint = f"/api/v1/content-projects/{project_id}/fact-boundary"
    first = client.post(endpoint, json={"fact_pack_id": pack_id, "expected_revision": 0}, headers=headers)
    assert first.status_code == 201
    clone = client.post(f"{endpoint}/clone", headers=headers)
    assert clone.status_code == 201, clone.text
    clone_id = clone.json()["id"]
    assert clone.json()["parent_id"] == pack_id
    assert clone.json()["status"] == "draft"
    edited = client.post(f"/api/v1/fact-packs/{clone_id}/items", json={"evidence_kind": "author_opinion", "snapshot": {"excerpt": "新增观点", "attribution": "作者", "source_locator": "段落 2"}}, headers=headers)
    assert edited.status_code == 201, edited.text
    advanced = client.post(f"{endpoint}/{clone_id}/freeze-and-bind", json={"expected_revision": 1}, headers=headers)
    assert advanced.status_code == 201, advanced.text
    assert advanced.json()["revision_no"] == 2
    assert advanced.json()["fact_pack_id"] == clone_id
    revisions = client.get(f"{endpoint}/revisions", headers=headers).json()
    assert [row["fact_pack_id"] for row in revisions] == [clone_id, pack_id]
    assert revisions[0]["fact_pack_checksum"] != revisions[1]["fact_pack_checksum"]
    assert client.get(f"/api/v1/fact-packs/{pack_id}", headers=headers).json()["item_count"] == 1


def test_explicit_material_reference_is_unified_and_detachable(client, db_session):
    from test_material_library import PNG

    headers = {"X-Studio-User": "alice@studio.local"}
    project_id = client.post("/api/v1/content-projects", json={"title": "Assets"}, headers=headers).json()["id"]
    material = client.post("/api/v1/materials/upload", data={"kind": "image", "title": "图"}, files={"file": ("image.png", PNG, "image/png")}, headers=headers)
    assert material.status_code == 201, material.text
    revision_id = material.json()["revisions"][0]["id"]
    endpoint = f"/api/v1/content-projects/{project_id}/materials/references"
    first = client.post(endpoint, json={"material_revision_id": revision_id}, headers=headers)
    assert first.status_code == 201, first.text
    assert client.post(endpoint, json={"material_revision_id": revision_id}, headers=headers).json()["id"] == first.json()["id"]
    assert len(db_session.scalars(select(ProjectEvent).where(ProjectEvent.project_id == project_id, ProjectEvent.event_type == "asset.attached")).all()) == 1
    shared = client.get(f"/api/v1/content-projects/{project_id}/shared-assets", headers=headers)
    assert shared.status_code == 200
    assert shared.json()[0]["material_revision_id"] == revision_id
    assert shared.json()[0]["source_type"] == "system_reference"
    assert shared.json()[0]["provenance"]["source_kind"] == "upload"
    assert client.delete(f"{endpoint}/{first.json()['id']}", headers=headers).status_code == 204
    assert client.get(f"/api/v1/content-projects/{project_id}/shared-assets", headers=headers).json() == []
    assert client.get(f"/api/v1/materials/{material.json()['id']}", headers=headers).status_code == 200


def test_project_material_upload_creates_reference(client):
    from test_material_library import PNG

    headers = {"X-Studio-User": "alice@studio.local"}
    project_id = client.post("/api/v1/content-projects", json={"title": "Upload"}, headers=headers).json()["id"]
    response = client.post(f"/api/v1/content-projects/{project_id}/materials/upload", data={"kind": "image", "title": "封面"}, files={"file": ("cover.png", PNG, "image/png")}, headers=headers)
    assert response.status_code == 201, response.text
    assert response.json()["source_type"] == "project_upload"
    shared = client.get(f"/api/v1/content-projects/{project_id}/shared-assets", headers=headers).json()
    assert len(shared) == 1
    assert shared[0]["material_revision_id"] == response.json()["material_revision_id"]


def test_project_upload_db_failure_rolls_back_without_deleting_shared_bytes(client, db_session, monkeypatch, tmp_path):
    from datetime import UTC, datetime, timedelta

    from test_material_library import PNG

    from app.models import AuditLog, Material, MaterialRevision, ProjectMaterialReference
    from app.routers import project_assets
    from app.services import asset_media
    from app.services.retention import run_retention

    monkeypatch.setattr(asset_media, "MEDIA_ROOT", tmp_path)
    headers = {"X-Studio-User": "alice@studio.local"}
    project_id = client.post("/api/v1/content-projects", json={"title": "Upload rollback"}, headers=headers).json()["id"]
    existing = client.post("/api/v1/materials/upload", data={"kind": "image", "title": "shared"}, files={"file": ("cover.png", PNG, "image/png")}, headers=headers)
    assert existing.status_code == 201, existing.text
    existing_revision = db_session.get(MaterialRevision, existing.json()["revisions"][0]["id"])
    shared_path = tmp_path / existing_revision.file_path
    assert shared_path.is_file()
    material_count = len(db_session.scalars(select(Material)).all())
    revision_count = len(db_session.scalars(select(MaterialRevision)).all())

    def reject_event(*args, **kwargs):
        raise RuntimeError("injected event failure")

    monkeypatch.setattr(project_assets, "record_project_event", reject_event)
    with pytest.raises(RuntimeError, match="injected event failure"):
        client.post(f"/api/v1/content-projects/{project_id}/materials/upload", data={"kind": "image", "title": "rollback"}, files={"file": ("cover.png", PNG, "image/png")}, headers=headers)
    assert len(db_session.scalars(select(Material)).all()) == material_count
    assert len(db_session.scalars(select(MaterialRevision)).all()) == revision_count
    assert db_session.scalars(select(ProjectMaterialReference).where(ProjectMaterialReference.project_id == project_id)).all() == []
    assert shared_path.is_file()
    assert db_session.scalars(select(AuditLog).where(AuditLog.event == "material.upload_orphan_candidate")).all() == []

    unique_content = PNG + b"failed-new-byte-object"
    with pytest.raises(RuntimeError, match="injected event failure"):
        client.post(f"/api/v1/content-projects/{project_id}/materials/upload", data={"kind": "image", "title": "new rollback"}, files={"file": ("new.png", unique_content, "image/png")}, headers=headers)
    candidate = db_session.scalar(select(AuditLog).where(AuditLog.event == "material.upload_orphan_candidate"))
    assert candidate is not None
    assert len(candidate.entity_id) <= 50
    assert candidate.detail_json["project_id"] == project_id
    new_path = tmp_path / candidate.detail_json["file_path"]
    assert new_path.read_bytes() == unique_content
    assert db_session.scalars(select(MaterialRevision).where(MaterialRevision.file_path == candidate.detail_json["file_path"])).all() == []
    candidate.created_at = datetime.now(UTC) - timedelta(days=2)
    db_session.commit()
    stats = run_retention(db_session, {"material_orphan_grace_days": 1})
    assert stats["material_orphan_bytes_removed"] == 1
    assert not new_path.exists()
    assert db_session.get(AuditLog, candidate.id).event == "material.upload_orphan_resolved"

    shared_candidate = AuditLog(event="material.upload_orphan_candidate", actor="test", entity_type="material_bytes", entity_id=existing_revision.content_hash[:50], detail_json={"file_path": existing_revision.file_path, "content_hash": existing_revision.content_hash}, created_at=datetime.now(UTC) - timedelta(days=2))
    db_session.add(shared_candidate)
    db_session.commit()
    stats = run_retention(db_session, {"material_orphan_grace_days": 1})
    assert stats["material_orphan_referenced"] == 1
    assert shared_path.is_file()
    assert db_session.get(AuditLog, shared_candidate.id).event == "material.upload_orphan_resolved"


def test_overview_versions_and_activity_derive_from_persisted_project_state(client, db_session):
    from app.models import FactPack, FactPackStatus

    headers = {"X-Studio-User": "alice@studio.local"}
    project_id = client.post("/api/v1/content-projects", json={"title": "Read models"}, headers=headers).json()["id"]
    base = f"/api/v1/content-projects/{project_id}"
    assert client.get(f"{base}/overview", headers=headers).json()["stage"] == "brief_needed"
    assert client.post(f"{base}/brief/revisions", json={"expected_revision": 0, "objective": "目标"}, headers=headers).status_code == 201
    assert client.get(f"{base}/overview", headers=headers).json()["stage"] == "evidence_needed"
    pack = FactPack(name="read model pack", version=1, status=FactPackStatus.frozen.value, checksum="b" * 64)
    db_session.add(pack)
    db_session.commit()
    assert client.post(f"{base}/fact-boundary", json={"fact_pack_id": pack.id, "expected_revision": 0}, headers=headers).status_code == 201
    assert client.get(f"{base}/overview", headers=headers).json()["stage"] == "matrix_needed"
    persona = client.post("/api/v1/content-personas", json={"name": "作者"}, headers=headers).json()["id"]
    assert client.post(f"{base}/units", json={"title": "文章", "persona_id": persona, "modality": "text"}, headers=headers).status_code == 201
    overview = client.get(f"{base}/overview", headers=headers).json()
    assert overview["activeUnitCount"] == 1
    assert overview["modalityCounts"]["text"] == 1
    versions = client.get(f"{base}/versions", headers=headers)
    assert versions.status_code == 200
    assert len(versions.json()["brief"]) == 1
    assert len(versions.json()["factBoundary"]) == 1
    activity = client.get(f"{base}/activity?limit=2", headers=headers)
    assert activity.status_code == 200
    assert len(activity.json()["items"]) == 2
    assert activity.json()["next_before_id"] is not None
    older = client.get(f"{base}/activity?limit=2&before_id={activity.json()['next_before_id']}", headers=headers)
    assert older.status_code == 200
    assert all(item["id"] < activity.json()["next_before_id"] for item in older.json()["items"])


def test_overview_risk_precedes_waiting_and_archived_units_leave_active_counts(client, db_session):
    from app.models import ContentUnit

    headers = {"X-Studio-User": "alice@studio.local"}
    project_id = client.post("/api/v1/content-projects", json={"title": "Stages"}, headers=headers).json()["id"]
    base = f"/api/v1/content-projects/{project_id}"
    assert client.post(f"{base}/brief/revisions", json={"expected_revision": 0, "objective": "目标"}, headers=headers).status_code == 201
    # Reuse a frozen pack through the public API rather than fabricating a boundary row.
    pack = client.post("/api/v1/fact-packs", json={"name": "stages"}, headers=headers).json()
    assert client.post(f"/api/v1/fact-packs/{pack['id']}/items", json={"evidence_kind": "author_opinion", "snapshot": {"excerpt": "观点", "attribution": "作者", "source_locator": "段落 1"}}, headers=headers).status_code == 201
    assert client.post(f"/api/v1/fact-packs/{pack['id']}/freeze", headers=headers).status_code == 200
    assert client.post(f"{base}/fact-boundary", json={"fact_pack_id": pack["id"], "expected_revision": 0}, headers=headers).status_code == 201
    persona = client.post("/api/v1/content-personas", json={"name": "作者"}, headers=headers).json()["id"]
    blocked = client.post(f"{base}/units", json={"title": "受阻", "persona_id": persona, "modality": "text"}, headers=headers).json()["id"]
    waiting = client.post(f"{base}/units", json={"title": "等待", "persona_id": persona, "modality": "graphic"}, headers=headers).json()["id"]
    assert client.patch(f"{base}/units/{blocked}", json={"status": "blocked"}, headers=headers).status_code == 200
    assert client.patch(f"{base}/units/{waiting}", json={"status": "waiting_human"}, headers=headers).status_code == 200
    overview = client.get(f"{base}/overview", headers=headers).json()
    assert overview["stage"] == "attention_required"
    assert {risk["code"] for risk in overview["risks"]} == {"unit_blocked", "identity_unready"}
    assert overview["modalityCounts"] == {"text": 1, "graphic": 1, "video": 0}
    assert overview["personas"] == [{"id": persona, "name": "作者", "unitCount": 2}]
    db_session.get(ContentUnit, blocked).status = "archived"
    db_session.commit()
    after = client.get(f"{base}/overview", headers=headers).json()
    assert after["activeUnitCount"] == 1
    assert after["archivedUnitCount"] == 1
    assert after["modalityCounts"]["text"] == 0
    assert after["stage"] == "attention_required"
    assert after["nextAction"]["code"] == "identity.rebind"
    assert after["pendingDecisions"][0]["code"] == "unit_waiting_human"
    for status in ("stale", "unknown"):
        assert client.patch(f"{base}/units/{waiting}", json={"status": status}, headers=headers).status_code == 200
        risk_view = client.get(f"{base}/overview", headers=headers).json()
        assert risk_view["stage"] == "attention_required"
        assert {risk["code"] for risk in risk_view["risks"]} == {f"unit_{status}", "identity_unready"}


def test_archived_project_keeps_historic_run_readable_and_blocks_legacy_mutation(client):
    from test_fe_f2_workflows import _definition

    headers = {"X-Studio-User": "alice@studio.local"}
    persona_id = client.post("/api/v1/content-personas", json={"name": "作者"}, headers=headers).json()["id"]
    project_id = client.post("/api/v1/content-projects", json={"title": "Archive"}, headers=headers).json()["id"]
    unit_id = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "文章", "persona_id": persona_id, "modality": "text"}, headers=headers).json()["id"]
    base = f"/api/v1/content-projects/{project_id}/units/{unit_id}"
    assert client.post(f"{base}/workflow-override", json={"expected_revision": 0, "definition": _definition()}, headers=headers).status_code == 201
    run = client.post(f"{base}/runs", json={"params": {}}, headers=headers)
    assert run.status_code == 201, run.text
    run_id = run.json()["id"]
    before = client.get(f"/api/v1/workflow-runs/{run_id}", headers=headers).json()
    assert client.post(f"/api/v1/content-projects/{project_id}/brief/revisions", json={"expected_revision": 0, "objective": "运行后新任务书"}, headers=headers).status_code == 201
    source_id = client.post("/api/v1/sources/text", json={"title": "运行后来源", "content": "新来源"}, headers=headers).json()["id"]
    assert client.post(f"/api/v1/content-projects/{project_id}/sources", json={"source_document_id": source_id}, headers=headers).status_code == 201
    pack = client.post("/api/v1/fact-packs", json={"name": "run history boundary"}, headers=headers).json()
    assert client.post(f"/api/v1/fact-packs/{pack['id']}/items", json={"evidence_kind": "author_opinion", "snapshot": {"excerpt": "观点", "attribution": "作者", "source_locator": "段落 1"}}, headers=headers).status_code == 201
    assert client.post(f"/api/v1/fact-packs/{pack['id']}/freeze", headers=headers).status_code == 200
    assert client.post(f"/api/v1/content-projects/{project_id}/fact-boundary", json={"fact_pack_id": pack["id"], "expected_revision": 0}, headers=headers).status_code == 201
    from test_material_library import PNG

    material = client.post("/api/v1/materials/upload", data={"kind": "image", "title": "历史后素材"}, files={"file": ("image.png", PNG, "image/png")}, headers=headers)
    assert material.status_code == 201
    assert client.post(f"/api/v1/content-projects/{project_id}/materials/references", json={"material_revision_id": material.json()["revisions"][0]["id"]}, headers=headers).status_code == 201
    after = client.get(f"/api/v1/workflow-runs/{run_id}", headers=headers).json()
    assert after["definition_checksum"] == before["definition_checksum"]
    assert after["steps"] == before["steps"]
    assert client.delete(f"/api/v1/content-projects/{project_id}", headers=headers).status_code == 204
    assert client.get(f"/api/v1/workflow-runs/{run_id}", headers=headers).status_code == 200
    assert client.post(f"/api/v1/workflow-runs/{run_id}/nodes/a/rerun", headers=headers).status_code == 409
    assert client.post(f"{base}/runs", json={"params": {}}, headers=headers).status_code == 409
    assert client.patch(base, json={"title": "不可修改"}, headers=headers).status_code == 409


def test_project_core_history_is_readable_after_archive_and_private_to_owner(client):
    from test_material_library import PNG

    alice = {"X-Studio-User": "alice@studio.local"}
    bob = {"X-Studio-User": "bob@studio.local"}
    project_id = client.post("/api/v1/content-projects", json={"title": "Private history"}, headers=alice).json()["id"]
    base = f"/api/v1/content-projects/{project_id}"
    assert client.post(f"{base}/brief/revisions", json={"expected_revision": 0, "objective": "历史目标"}, headers=alice).status_code == 201
    source_id = client.post("/api/v1/sources/text", json={"title": "原始来源", "content": "事实"}, headers=alice).json()["id"]
    assert client.post(f"{base}/sources", json={"source_document_id": source_id}, headers=alice).status_code == 201
    pack = client.post("/api/v1/fact-packs", json={"name": "historical boundary"}, headers=alice).json()
    assert client.post(f"/api/v1/fact-packs/{pack['id']}/items", json={"evidence_kind": "author_opinion", "snapshot": {"excerpt": "观点", "attribution": "作者", "source_locator": "段落 1"}}, headers=alice).status_code == 201
    assert client.post(f"/api/v1/fact-packs/{pack['id']}/freeze", headers=alice).status_code == 200
    assert client.post(f"{base}/fact-boundary", json={"fact_pack_id": pack["id"], "expected_revision": 0}, headers=alice).status_code == 201
    uploaded = client.post(f"{base}/materials/upload", data={"kind": "image"}, files={"file": ("cover.png", PNG, "image/png")}, headers=alice)
    assert uploaded.status_code == 201
    assert client.delete(f"{base}/sources/{source_id}", headers=alice).status_code == 204
    assert client.get(f"{base}/fact-boundary", headers=alice).json()["fact_pack_id"] == pack["id"]
    assert client.delete(base, headers=alice).status_code == 204
    for path in ("/brief", "/brief/revisions", "/fact-boundary", "/fact-boundary/revisions", "/shared-assets", "/versions", "/activity", "/overview"):
        assert client.get(f"{base}{path}", headers=alice).status_code == 200
        assert client.get(f"{base}{path}", headers=bob).status_code == 404
    assert client.get(f"{base}/brief", headers=alice).json()["objective"] == "历史目标"
    assert client.get(f"{base}/shared-assets", headers=alice).json()[0]["material_revision_id"] == uploaded.json()["material_revision_id"]
    assert client.post(f"{base}/brief/revisions", json={"expected_revision": 1, "objective": "不可修改"}, headers=alice).status_code == 409
    assert client.post(f"{base}/sources", json={"source_document_id": source_id}, headers=alice).status_code == 409
    assert client.post(f"{base}/fact-boundary", json={"fact_pack_id": pack["id"], "expected_revision": 1}, headers=alice).status_code == 409
    assert client.post(f"{base}/materials/references", json={"material_revision_id": uploaded.json()["material_revision_id"]}, headers=alice).status_code == 409
