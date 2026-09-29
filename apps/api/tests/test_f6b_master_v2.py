"""Text v2 uses the existing immutable Master API, with no implicit upgrade."""

from copy import deepcopy

import pytest
from test_f6a_modality_adapters import HEADERS, _render_material, _unit
from test_f6b_text_documents import citation, doc, paragraph, run


def payload(text="中文😀正文"):
    return {"title": "文字主版本", "document": doc([paragraph(text)])}


def _v1(client, path, key="legacy-source"):
    response = client.post(path, json={"idempotency_key": key, "payload": {"title": "旧稿", "markdown": "## 标题\n\n正文😀 **强调**"}}, headers=HEADERS)
    assert response.status_code == 200, response.text
    return response.json()


def _upgrade_request(source, preview, key="upgrade"):
    return {"idempotency_key": key, "expected_revision": source["revision_no"], "expected_payload_hash": source["payload_hash"], "expected_context_hash": preview["current_context_hash"]}


def test_explicit_upgrade_is_append_only_preview_does_not_save_and_replay_precedes_context(client, db_session):
    project, path = _unit(client, db_session, "text")
    source = _v1(client, path)
    preview = client.get(f"{path}/{source['id']}/text-v2-upgrade-preview", headers=HEADERS)
    assert preview.status_code == 200, preview.text
    preview = preview.json()
    assert len(client.get(path, headers=HEADERS).json()["items"]) == 1
    body = _upgrade_request(source, preview)
    response = client.post(f"{path}/{source['id']}/text-v2-upgrade", json=body, headers=HEADERS)
    assert response.status_code == 200, response.text
    child = response.json()
    assert child["payload_schema"] == "text.master.v2"
    assert child["parent_revision_id"] == source["id"]
    assert child["payload"] == preview["payload"]
    assert child["edit_summary"]["upgrade_source"]["payload_hash"] == source["payload_hash"]
    assert client.get(f"{path}/{source['id']}", headers=HEADERS).json() == source
    client.post(f"/api/v1/content-projects/{project}/brief/revisions", json={"expected_revision": 1, "objective": "新上下文"}, headers=HEADERS)
    replay = client.post(f"{path}/{source['id']}/text-v2-upgrade", json=body, headers=HEADERS)
    assert replay.status_code == 200, replay.text
    assert replay.json()["id"] == child["id"]
    assert len(client.get(path, headers=HEADERS).json()["items"]) == 2
    mismatch = client.post(f"{path}/{source['id']}/text-v2-upgrade", json={**body, "expected_revision": 99}, headers=HEADERS)
    assert mismatch.status_code == 409


@pytest.mark.parametrize("field", ["expected_revision", "expected_payload_hash", "expected_context_hash"])
def test_upgrade_conflicts_create_no_revision(client, db_session, field):
    _, path = _unit(client, db_session, "text")
    source = _v1(client, path)
    preview = client.get(f"{path}/{source['id']}/text-v2-upgrade-preview", headers=HEADERS).json()
    body = _upgrade_request(source, preview)
    body[field] = 99 if field == "expected_revision" else "0" * 64
    response = client.post(f"{path}/{source['id']}/text-v2-upgrade", json=body, headers=HEADERS)
    assert response.status_code == 409, response.text
    assert len(client.get(path, headers=HEADERS).json()["items"]) == 1


def test_upgrade_historical_source_preview_allowed_but_commit_rejected(client, db_session):
    _, path = _unit(client, db_session, "text")
    source = _v1(client, path)
    next_response = client.post(path, json={"expected_revision": 1, "idempotency_key": "next-v1", "payload": {"markdown": "另一个版本"}}, headers=HEADERS)
    assert next_response.status_code == 200
    preview = client.get(f"{path}/{source['id']}/text-v2-upgrade-preview", headers=HEADERS)
    assert preview.status_code == 200, preview.text
    response = client.post(f"{path}/{source['id']}/text-v2-upgrade", json=_upgrade_request(source, preview.json()), headers=HEADERS)
    assert response.status_code == 409, response.text
    assert len(client.get(path, headers=HEADERS).json()["items"]) == 2


def test_upgrade_is_project_owned_and_archived_read_only(client, db_session):
    project, path = _unit(client, db_session, "text")
    source = _v1(client, path)
    preview = client.get(f"{path}/{source['id']}/text-v2-upgrade-preview", headers=HEADERS).json()
    assert client.get(f"{path}/{source['id']}/text-v2-upgrade-preview", headers={"X-Studio-User": "foreign@studio.local"}).status_code == 404
    assert client.delete(f"/api/v1/content-projects/{project}", headers=HEADERS).status_code == 204
    assert client.get(f"{path}/{source['id']}/text-v2-upgrade-preview", headers=HEADERS).status_code == 200
    assert client.post(f"{path}/{source['id']}/text-v2-upgrade", json=_upgrade_request(source, preview), headers=HEADERS).status_code == 409


def test_upgrade_reserved_provenance_cannot_be_supplied_to_generic_save(client, db_session):
    _, path = _unit(client, db_session, "text")
    body = {"idempotency_key": "spoof", "payload_schema": "text.master.v2", "payload": payload(), "edit_summary": {"upgrade_source": {"master_id": 999}}}
    response = client.post(path, json=body, headers=HEADERS)
    assert response.status_code == 422


def test_upgrade_cannot_refresh_stale_parent_implicitly(client, db_session):
    project, path = _unit(client, db_session, "text")
    source = _v1(client, path)
    assert client.post(f"/api/v1/content-projects/{project}/brief/revisions", json={"expected_revision": 1, "objective": "新 Brief"}, headers=HEADERS).status_code == 201
    preview = client.get(f"{path}/{source['id']}/text-v2-upgrade-preview", headers=HEADERS)
    assert preview.status_code == 200, preview.text
    response = client.post(f"{path}/{source['id']}/text-v2-upgrade", json=_upgrade_request(source, preview.json()), headers=HEADERS)
    assert response.status_code == 409, response.text
    assert response.json()["detail"]["code"] == "stale_upgrade_source"
    assert len(client.get(path, headers=HEADERS).json()["items"]) == 1


def test_upgrade_preview_long_numeric_marker_cannot_raise_internal_error(client, db_session):
    _, path = _unit(client, db_session, "text")
    source = client.post(path, json={"idempotency_key": "long-number", "payload": {"markdown": "9" * 4301 + ". 项目"}}, headers=HEADERS).json()
    preview = client.get(f"{path}/{source['id']}/text-v2-upgrade-preview", headers=HEADERS)
    assert preview.status_code == 200, preview.text
    assert preview.json()["warnings"] == [{"code": "unsupported_block_preserved"}]
    assert len(client.get(path, headers=HEADERS).json()["items"]) == 1


def test_save_v2_canonical_revision_and_idempotent_replay(client, db_session):
    _, path = _unit(client, db_session, "text")
    body = {"idempotency_key": "v2-manual", "payload_schema": "text.master.v2", "payload": payload()}
    response = client.post(path, json=body, headers=HEADERS)
    assert response.status_code == 200, response.text
    saved = response.json()
    assert saved["payload_schema"] == "text.master.v2"
    assert "markdown" not in saved["payload"]
    assert client.get(f"{path}/{saved['id']}", headers=HEADERS).json()["payload"] == saved["payload"]
    next_body = {**body, "expected_revision": 1, "idempotency_key": "v2-next", "payload": payload("新正文")}
    assert client.post(path, json=next_body, headers=HEADERS).status_code == 200
    assert client.post(path, json=body, headers=HEADERS).json()["id"] == saved["id"]
    assert len(client.get(path, headers=HEADERS).json()["items"]) == 2
    changed_replay = client.post(path, json={**body, "payload": payload("变更重试")}, headers=HEADERS)
    assert changed_replay.status_code == 409
    assert client.get(f"{path}/{saved['id']}", headers=HEADERS).json()["payload"] == saved["payload"]


def test_new_structured_document_uses_v2_default_but_legacy_markdown_stays_v1(client, db_session):
    _, path = _unit(client, db_session, "text")
    response = client.post(path, json={"idempotency_key": "default", "payload": payload()}, headers=HEADERS)
    assert response.status_code == 200, response.text
    assert response.json()["payload_schema"] == "text.master.v2"
    _, legacy = _unit(client, db_session, "text", suffix="legacy")
    response = client.post(legacy, json={"idempotency_key": "legacy", "payload": {"markdown": "旧正文"}}, headers=HEADERS)
    assert response.status_code == 200, response.text
    assert response.json()["payload_schema"] == "text.master.v1"


@pytest.mark.parametrize("schema,content", [
    ("text.master.v2", {**payload(), "markdown": "第二真源"}),
    ("text.master.v2", {"title": "", "document": {"type": "doc", "content": []}}),
    ("text.master.v99", payload()),
    ("graphic.master.v1", payload()),
])
def test_v2_invalid_or_unknown_schema_creates_no_history(client, db_session, schema, content):
    _, path = _unit(client, db_session, "text")
    response = client.post(path, json={"idempotency_key": "invalid", "payload_schema": schema, "payload": content}, headers=HEADERS)
    assert response.status_code == 422, response.text
    assert client.get(path, headers=HEADERS).json()["items"] == []


def test_current_v1_requires_explicit_upgrade_and_v2_cannot_downgrade(client, db_session):
    _, path = _unit(client, db_session, "text")
    v1 = client.post(path, json={"idempotency_key": "v1", "payload": {"markdown": "历史"}}, headers=HEADERS).json()
    response = client.post(path, json={"idempotency_key": "silent-upgrade", "expected_revision": 1, "payload_schema": "text.master.v2", "payload": payload()}, headers=HEADERS)
    assert response.status_code == 409, response.text
    assert client.get(f"{path}/{v1['id']}", headers=HEADERS).json()["payload"] == {"markdown": "历史"}
    _, other = _unit(client, db_session, "text", suffix="other")
    assert client.post(other, json={"idempotency_key": "v2", "payload_schema": "text.master.v2", "payload": payload()}, headers=HEADERS).status_code == 200
    response = client.post(other, json={"idempotency_key": "downgrade", "expected_revision": 1, "payload_schema": "text.master.v1", "payload": {"markdown": "不要降级"}}, headers=HEADERS)
    assert response.status_code == 409, response.text


def test_v2_context_conflict_archive_and_unknown_ai_receipt_are_closed(client, db_session):
    project, path = _unit(client, db_session, "text")
    body = {"idempotency_key": "v2", "payload_schema": "text.master.v2", "payload": payload()}
    response = client.post(path, json=body, headers=HEADERS)
    assert response.status_code == 200, response.text
    saved = response.json()
    client.post(f"/api/v1/content-projects/{project}/brief/revisions", json={"expected_revision": 1, "objective": "新的上下文"}, headers=HEADERS)
    response = client.post(path, json={**body, "idempotency_key": "stale", "expected_revision": 1, "expected_context_hash": saved["context_hash"]}, headers=HEADERS)
    assert response.status_code == 409
    response = client.post(path, json={**body, "idempotency_key": "fake-ai", "expected_revision": 1, "edit_summary": {"ai_edits": [{"llm_run_id": 999}]}}, headers=HEADERS)
    assert response.status_code == 422
    assert len(client.get(path, headers=HEADERS).json()["items"]) == 1
    assert client.delete(f"/api/v1/content-projects/{project}", headers=HEADERS).status_code == 204
    assert client.post(path, json={**body, "expected_revision": 1, "idempotency_key": "archive"}, headers=HEADERS).status_code == 409


def test_v2_schema_reads_and_partial_semantic_checks_require_approval_disposition(client, db_session):
    project, path = _unit(client, db_session, "text")
    response = client.post(path, json={"idempotency_key": "text", "payload_schema": "text.master.v2", "payload": payload()}, headers=HEADERS)
    assert response.status_code == 200, response.text
    saved = response.json()
    ready = client.get(f"{path}/{saved['id']}/readiness", headers=HEADERS)
    assert ready.status_code == 200, ready.text
    assert ready.json()["payload_schema"] == "text.master.v2"
    assert ready.json()["render"]["status"] == "ready"
    checks = client.post(f"{path}/{saved['id']}/checks", headers=HEADERS)
    assert checks.status_code == 200, checks.text
    required = {c["check_kind"] for c in checks.json()["items"]}
    assert {"text_structure", "text_fact", "text_identity", "text_platform"} <= required
    assert client.get(f"{path}/{saved['id']}/readiness", headers=HEADERS).json()["candidate_freeze_available"]
    unit_id = saved["content_unit_id"]
    freeze = client.post(f"/api/v1/content-projects/{project}/units/{unit_id}/candidates/freeze", json={"content_master_revision_id": saved["id"], "expected_payload_hash": saved["payload_hash"]}, headers=HEADERS)
    assert freeze.status_code == 201, freeze.text
    candidate = freeze.json()
    base = f"{path.replace('master-revisions', 'candidates')}/{candidate['id']}"
    assert client.post(f"{base}/approve", json={"candidate_hash": candidate["candidate_hash"]}, headers=HEADERS).status_code == 409


def test_v2_normalization_happens_before_hash_and_replay(client, db_session):
    _, path = _unit(client, db_session, "text")
    source = payload("x")
    source["document"]["blocks"][0]["content"] = [run("x", [{"type": "italic"}, {"type": "bold"}])]
    body = {"payload_schema": "text.master.v2", "idempotency_key": "normalize", "payload": source}
    response = client.post(path, json=body, headers=HEADERS)
    assert response.status_code == 200, response.text
    saved = response.json()
    normalized = deepcopy(body)
    normalized["payload"]["document"]["blocks"][0]["content"][0]["marks"].reverse()
    assert client.post(path, json=normalized, headers=HEADERS).json()["id"] == saved["id"]


def test_v2_dangling_citation_ref_rejected_before_commit(client, db_session):
    _, path = _unit(client, db_session, "text")
    source = payload()
    source["document"]["citations"] = [citation()]
    response = client.post(path, json={"idempotency_key": "dangling", "payload_schema": "text.master.v2", "payload": source}, headers=HEADERS)
    assert response.status_code == 422
    assert client.get(path, headers=HEADERS).json()["items"] == []


def test_v2_asset_kind_and_visibility_are_atomic(client, db_session, tmp_path):
    project, path = _unit(client, db_session, "text")
    video = _render_material(db_session, project, tmp_path, "video")
    source = payload()
    source["document"]["blocks"].append({"id": "image", "type": "image", "material_revision_id": video.id})
    body = {"idempotency_key": "wrong-kind", "payload_schema": "text.master.v2", "payload": source, "asset_refs": [{"material_revision_id": video.id, "content_hash": video.content_hash}]}
    response = client.post(path, json=body, headers=HEADERS)
    assert response.status_code == 422, response.text
    assert client.get(path, headers=HEADERS).json()["items"] == []
    other, _ = _unit(client, db_session, "text", suffix="foreign")
    image = _render_material(db_session, other, tmp_path, "graphic", name="foreign-image")
    source["document"]["blocks"][-1]["material_revision_id"] = image.id
    response = client.post(path, json={**body, "asset_refs": [{"material_revision_id": image.id, "content_hash": image.content_hash}]}, headers=HEADERS)
    assert response.status_code == 422
    assert client.get(path, headers=HEADERS).json()["items"] == []


@pytest.mark.parametrize("kind", ["image", "chart"])
def test_v2_asset_render_and_live_revocation_preserve_history(client, db_session, tmp_path, kind):
    from app.models import MaterialRevision

    project, path = _unit(client, db_session, "text")
    image = _render_material(db_session, project, tmp_path, "graphic")
    image.material.kind = kind
    db_session.commit()
    unused = _render_material(db_session, project, tmp_path, "graphic", name="unused")
    source = payload()
    source["document"]["blocks"].append({"id": "image", "type": kind, "material_revision_id": image.id, "alt_text": "图"})
    body = {"idempotency_key": "image", "payload_schema": "text.master.v2", "payload": source, "asset_refs": [{"material_revision_id": item.id, "content_hash": item.content_hash} for item in (unused, image)]}
    response = client.post(path, json=body, headers=HEADERS)
    assert response.status_code == 200, response.text
    saved = response.json()
    render = client.get(f"{path}/{saved['id']}/readiness", headers=HEADERS).json()["render"]
    assert render["status"] == "ready"
    assert f"media/01-{image.id}.png" in render["body_markdown"]
    assert render["unused_asset_ids"] == [unused.id]
    assert f"{unused.id}.png" not in render["body_markdown"]
    from app.models import ContentMasterRevision
    from app.services.production_modalities import adapter_for

    projection = adapter_for("text", "text.master.v2").build_package_projection(db_session, db_session.get(ContentMasterRevision, saved["id"]))
    assert projection["text_files"] == [{"name": "content.md", "content": render["body_markdown"]}]
    removed = client.post(path, json={"idempotency_key": "remove-asset", "expected_revision": 1, "payload_schema": "text.master.v2", "payload": payload()}, headers=HEADERS)
    assert removed.status_code == 200, removed.text
    assert removed.json()["assets"] == []
    assert len(client.get(f"{path}/{saved['id']}", headers=HEADERS).json()["assets"]) == 2
    assert db_session.get(MaterialRevision, image.id) is not None
    db_session.get(MaterialRevision, image.id).public_use_allowed = False
    db_session.commit()
    assert client.get(f"{path}/{saved['id']}/readiness", headers=HEADERS).json()["render"]["status"] == "incomplete"
    assert client.get(f"{path}/{saved['id']}", headers=HEADERS).json()["payload"] == saved["payload"]


def test_v2_repeated_evidence_uses_round_trip_and_edited_selection_rejects(client, db_session):
    from sqlalchemy import select

    from app.models import FactPackItem

    _, path = _unit(client, db_session, "text")
    item = db_session.scalar(select(FactPackItem))
    source = payload()
    first = {**citation(), "fact_pack_item_id": item.id}
    second = {**first, "id": "c2"}
    source["document"]["citations"] = [first, second]
    refs = [{"fact_pack_item_id": item.id, "snapshot_checksum": item.snapshot_checksum, "locator": {"citation_id": c["id"], **{key: c[key] for key in ("block_id", "start", "end", "selected_text_hash")}}} for c in (first, second)]
    body = {"idempotency_key": "citations", "payload_schema": "text.master.v2", "payload": source, "evidence_refs": refs}
    response = client.post(path, json=body, headers=HEADERS)
    assert response.status_code == 200, response.text
    saved = response.json()
    assert len(saved["evidence"]) == 2
    assert {ref["locator"]["citation_id"] for ref in saved["evidence"]} == {"c1", "c2"}
    changed = deepcopy(body)
    changed.update(idempotency_key="edited", expected_revision=1)
    changed["payload"]["document"]["blocks"][0]["content"][0]["text"] = "中文😞正文"
    assert client.post(path, json=changed, headers=HEADERS).status_code == 422
    assert len(client.get(path, headers=HEADERS).json()["items"]) == 1


def test_v2_adapter_revalidates_each_asset_use_not_only_last_block(client, db_session, tmp_path):
    from app.models import ContentMasterRevision
    from app.services.production_modalities import adapter_for

    project, path = _unit(client, db_session, "text")
    image = _render_material(db_session, project, tmp_path, "graphic")
    source = payload()
    source["document"]["blocks"].append({"id": "image", "type": "image", "material_revision_id": image.id})
    saved = client.post(path, json={"idempotency_key": "image", "payload_schema": "text.master.v2", "payload": source, "asset_refs": [{"material_revision_id": image.id, "content_hash": image.content_hash}]}, headers=HEADERS).json()
    master = db_session.get(ContentMasterRevision, saved["id"])
    master.payload_json = deepcopy(master.payload_json)
    master.payload_json["document"]["blocks"].insert(0, {"id": "bad-chart", "type": "chart", "material_revision_id": image.id})
    assert adapter_for("text", "text.master.v2").build_render_snapshot(db_session, master)["status"] == "incomplete"


def test_v2_foreign_reader_and_viewer_cannot_mutate(client, db_session):
    from sqlalchemy import select

    from app.models import User

    _, path = _unit(client, db_session, "text")
    saved = client.post(path, json={"idempotency_key": "base", "payload_schema": "text.master.v2", "payload": payload()}, headers=HEADERS).json()
    other = {"X-Studio-User": "unrelated@studio.local"}
    assert client.get(f"{path}/{saved['id']}", headers=other).status_code == 404
    assert client.post(path, json={"idempotency_key": "foreign", "payload_schema": "text.master.v2", "payload": payload()}, headers=other).status_code == 404
    db_session.scalar(select(User).where(User.email == HEADERS["X-Studio-User"])).role = "viewer"
    db_session.commit()
    assert client.post(path, json={"idempotency_key": "viewer", "payload_schema": "text.master.v2", "payload": payload()}, headers=HEADERS).status_code == 403


def test_v2_invalid_unicode_in_metadata_is_an_atomic_client_error(client, db_session):
    import json

    _, path = _unit(client, db_session, "text")
    body = {"idempotency_key": "surrogate", "payload_schema": "text.master.v2", "payload": payload(), "edit_summary": {"note": "\ud800"}}
    response = client.post(path, content=json.dumps(body, ensure_ascii=True), headers={**HEADERS, "Content-Type": "application/json"})
    assert response.status_code == 422, response.text
    assert client.get(path, headers=HEADERS).json()["items"] == []


def test_v2_stale_revision_and_forged_origin_create_no_partial_rows(client, db_session):
    from sqlalchemy import func, select

    from app.models import ContentMasterAssetRef, ContentMasterEvidenceRef, ContentMasterRevision, ProjectEvent

    _, path = _unit(client, db_session, "text")
    body = {"idempotency_key": "first", "payload_schema": "text.master.v2", "payload": payload()}
    assert client.post(path, json=body, headers=HEADERS).status_code == 200
    counts = {model: db_session.scalar(select(func.count()).select_from(model)) for model in (ContentMasterRevision, ContentMasterAssetRef, ContentMasterEvidenceRef, ProjectEvent)}
    assert client.post(path, json={**body, "idempotency_key": "conflict"}, headers=HEADERS).status_code == 409
    assert client.post(path, json={**body, "idempotency_key": "forged", "expected_revision": 1, "source_kind": "explicit_upgrade"}, headers=HEADERS).status_code == 422
    assert counts == {model: db_session.scalar(select(func.count()).select_from(model)) for model in counts}


def test_empty_v2_document_saves_draft_without_claiming_render_ready(client, db_session):
    _, path = _unit(client, db_session, "text")
    response = client.post(path, json={"idempotency_key": "empty", "payload_schema": "text.master.v2", "payload": {"title": "", "document": doc()}}, headers=HEADERS)
    assert response.status_code == 200, response.text
    readiness = client.get(f"{path}/{response.json()['id']}/readiness", headers=HEADERS).json()
    assert readiness["render"]["status"] == "incomplete"
    assert not readiness["candidate_freeze_available"]


def test_v2_evidence_boundary_change_does_not_retarget_history(client, db_session):
    from sqlalchemy import select

    from app.models import FactPack, FactPackItem

    project, path = _unit(client, db_session, "text")
    item = db_session.scalar(select(FactPackItem))
    c = {**citation(), "fact_pack_item_id": item.id}
    source = payload()
    source["document"]["citations"] = [c]
    body = {"idempotency_key": "boundary", "payload_schema": "text.master.v2", "payload": source, "evidence_refs": [{"fact_pack_item_id": item.id, "snapshot_checksum": item.snapshot_checksum, "locator": {"citation_id": c["id"], **{key: c[key] for key in ("block_id", "start", "end", "selected_text_hash")}}}]}
    saved = client.post(path, json=body, headers=HEADERS).json()
    pack = FactPack(name="另一边界", version=1, status="frozen", checksum="n" * 64)
    db_session.add(pack)
    db_session.flush()
    db_session.add(FactPackItem(fact_pack_id=pack.id, evidence_kind="author_opinion", snapshot_json={"statement": "其他观点"}, snapshot_checksum="o" * 64, public_use_allowed=True))
    db_session.commit()
    response = client.post(f"/api/v1/content-projects/{project}/fact-boundary", json={"fact_pack_id": pack.id, "expected_revision": 1}, headers=HEADERS)
    assert response.status_code == 201, response.text
    changed = {**body, "idempotency_key": "wrong-boundary", "expected_revision": 1}
    assert client.post(path, json={**changed, "expected_context_hash": saved["context_hash"]}, headers=HEADERS).status_code == 409
    assert client.post(path, json=changed, headers=HEADERS).status_code == 422
    history = client.get(f"{path}/{saved['id']}", headers=HEADERS).json()
    assert history["payload"] == saved["payload"] and history["evidence"] == saved["evidence"]
    assert history["readiness"]["state"] == "stale"
