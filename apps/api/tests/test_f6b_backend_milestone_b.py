"""Backend Milestone B: server patches, receipts, structured diffs and frozen v2 projections."""

import hashlib
import io
import json
import zipfile

from test_f6a_modality_adapters import HEADERS, _unit
from test_f6b_master_v2 import _v1, payload
from test_f6b_text_documents import citation

from app.models import ContentAsset, ContentMasterRevision, FactPackItem, LLMRun
from app.services.candidates import candidate_hash
from app.services.generation.providers import GenerateResult
from app.services.project_review_projection import candidate_diff
from app.services.text_documents import canonical_document
from app.services.text_master_ai import apply_patch


def _save_v2(client, path, key="v2", text="原始正文"):
    response = client.post(path, json={"idempotency_key": key, "payload_schema": "text.master.v2", "payload": payload(text)}, headers=HEADERS)
    assert response.status_code == 200, response.text
    return response.json()


def test_text_suggestion_is_server_validated_and_does_not_write_master(client, db_session):
    _, path = _unit(client, db_session, "text")
    master = _save_v2(client, path)
    response = client.post(f"{path}/{master['id']}/text-suggestions", json={"base_payload_hash": master["payload_hash"], "working_document": master["payload"]["document"], "operation": "rewrite", "selection": {"block_id": "p1", "start": 0, "end": 2}}, headers=HEADERS)
    assert response.status_code == 200, response.text
    suggestion = response.json()
    assert suggestion["patch"]["kind"] == "replace_text"
    assert suggestion["after_document_hash"] != suggestion["before_document_hash"]
    assert suggestion["provenance"]["patch_hash"] == suggestion["patch_hash"]
    assert db_session.query(ContentMasterRevision).count() == 1
    run = db_session.get(LLMRun, suggestion["llm_run_id"])
    assert run.status == "succeeded"
    assert run.purpose == "text_master_edit"
    assert run.parsed_output_json["provenance"]["project_id"] == master["project_id"]

    saved = client.post(path, json={"expected_revision": 1, "expected_context_hash": master["context_hash"], "parent_revision_id": master["id"], "idempotency_key": "after-ai", "payload_schema": "text.master.v2", "payload": {"title": master["payload"]["title"], "document": suggestion["applied_document"]}, "edit_summary": {"ai_edits": [{"llm_run_id": suggestion["llm_run_id"]}]}}, headers=HEADERS)
    assert saved.status_code == 200, saved.text
    assert saved.json()["edit_summary"]["ai_provenance"]["edits"][0]["status"] == "verified_output_match"


def test_ai_receipt_rejects_foreign_and_broken_claims_but_allows_manual_edit(client, db_session):
    _, path = _unit(client, db_session, "text")
    master = _save_v2(client, path)
    response = client.post(f"{path}/{master['id']}/text-suggestions", json={"base_payload_hash": master["payload_hash"], "working_document": master["payload"]["document"], "operation": "shorten", "selection": {"block_id": "p1", "start": 0, "end": 2}}, headers=HEADERS)
    suggestion = response.json()
    forged = client.post(path, json={"expected_revision": 1, "parent_revision_id": master["id"], "idempotency_key": "forged", "payload_schema": "text.master.v2", "payload": master["payload"], "edit_summary": {"ai_edits": [{"llm_run_id": 999999}]}}, headers=HEADERS)
    assert forged.status_code == 422
    manual = client.post(path, json={"expected_revision": 1, "parent_revision_id": master["id"], "idempotency_key": "manual", "payload_schema": "text.master.v2", "payload": {"title": master["payload"]["title"], "document": {**master["payload"]["document"], "blocks": [{"id": "p1", "type": "paragraph", "content": [{"text": "人工修改", "marks": []}]}]}}, "edit_summary": {}}, headers=HEADERS)
    assert manual.status_code == 200, manual.text
    assert suggestion["llm_run_id"]


def test_client_cannot_spoof_verified_ai_provenance_without_receipt(client, db_session):
    _, path = _unit(client, db_session, "text")
    master = _save_v2(client, path)
    fake = {"version": "text-master-edit.v1", "edits": [{"llm_run_id": 123, "status": "verified_output_match"}]}
    response = client.post(path, json={"expected_revision": 1, "parent_revision_id": master["id"], "idempotency_key": "spoof-ai", "payload_schema": "text.master.v2", "payload": payload("人工正文"), "edit_summary": {"ai_provenance": fake}}, headers=HEADERS)
    assert response.status_code == 422, response.text
    assert db_session.query(ContentMasterRevision).count() == 1


def test_text_patch_rebases_unaffected_later_citation_offsets():
    text = "前文后文"
    document = canonical_document({"schema": "studio.text.document.v1", "blocks": [{"id": "p1", "type": "paragraph", "content": [{"text": text, "marks": []}]}], "citations": [{"id": "c1", "block_id": "p1", "start": 2, "end": 4, "fact_pack_item_id": 8, "selected_text_hash": hashlib.sha256("后文".encode()).hexdigest()}]})
    updated = apply_patch(document, {"kind": "replace_text", "block_id": "p1", "start": 0, "end": 2, "replacement": [{"text": "更长前文", "marks": []}]})
    assert updated["citations"][0]["start"] == 4
    assert updated["citations"][0]["end"] == 6


def test_ai_suggestion_uses_only_model_eligible_snapshot_evidence(client, db_session):
    _, path = _unit(client, db_session, "text")
    item = db_session.query(FactPackItem).first()
    item.model_use_allowed = True
    db_session.commit()
    master = _save_v2(client, path)
    response = client.post(f"{path}/{master['id']}/text-suggestions", json={"base_payload_hash": master["payload_hash"], "working_document": master["payload"]["document"], "operation": "expand", "selection": {"block_id": "p1", "start": 0, "end": 2}}, headers=HEADERS)
    assert response.status_code == 200, response.text
    assert response.json()["patch"]["kind"] == "replace_text"


def test_text_suggestion_supports_all_five_ops_and_rejects_stale_base(client, db_session):
    project, path = _unit(client, db_session, "text")
    master = _save_v2(client, path)
    document = master["payload"]["document"]
    for operation in ("rewrite", "expand", "shorten", "tone", "restructure"):
        selection = {"from_block_id": "p1", "to_block_id": "p1"} if operation == "restructure" else {"block_id": "p1", "start": 0, "end": 2}
        response = client.post(f"{path}/{master['id']}/text-suggestions", json={"base_payload_hash": master["payload_hash"], "working_document": document, "operation": operation, "selection": selection}, headers=HEADERS)
        assert response.status_code == 200, (operation, response.text)
        assert response.json()["patch"]["kind"] == ("replace_blocks" if operation == "restructure" else "replace_text")
    assert db_session.query(ContentMasterRevision).count() == 1
    assert client.post(f"{path}/{master['id']}/text-suggestions", json={"base_payload_hash": "0" * 64, "working_document": document, "operation": "rewrite", "selection": {"block_id": "p1", "start": 0, "end": 2}}, headers=HEADERS).status_code == 409
    assert client.post(f"{path}/{master['id']}/text-suggestions", json={"base_payload_hash": master["payload_hash"], "working_document": document, "operation": "rewrite", "selection": {"block_id": "p1", "start": 0, "end": 2}}, headers={"X-Studio-User": "foreign@studio.local"}).status_code == 404
    assert client.post(f"{path}/{master['id']}/text-suggestions", json={"base_payload_hash": master["payload_hash"], "working_document": document, "operation": "rewrite", "selection": {"block_id": "p1", "start": 0, "end": 999}}, headers=HEADERS).status_code == 422
    assert client.post(f"{path}/{master['id']}/text-suggestions", json={"base_payload_hash": master["payload_hash"], "working_document": document, "operation": "rewrite", "selection": {"block_id": "p1", "start": 0, "end": 2}, "instruction": "x" * 2001}, headers=HEADERS).status_code == 422
    assert client.post(f"/api/v1/content-projects/{project}/brief/revisions", json={"expected_revision": 1, "objective": "上下文已变化"}, headers=HEADERS).status_code == 201
    assert client.post(f"{path}/{master['id']}/text-suggestions", json={"base_payload_hash": master["payload_hash"], "working_document": document, "operation": "rewrite", "selection": {"block_id": "p1", "start": 0, "end": 2}}, headers=HEADERS).status_code == 409
    assert project


def test_provider_injection_cannot_choose_patch_target_or_claim_provenance(client, db_session, monkeypatch):
    import app.services.text_master_ai as text_ai

    _, path = _unit(client, db_session, "text")
    master = _save_v2(client, path)

    class InjectingProvider:
        name = "test-provider"
        model = "test-model"

        async def generate_json(self, request):
            return GenerateResult(data={"patch": {"kind": "replace_text", "block_id": "foreign-block", "start": 0, "end": 2, "replacement": [{"text": "指令覆盖", "marks": []}]}, "provenance": {"actor": "forged", "status": "verified_output_match"}}, raw_output="{}", usage={})

    monkeypatch.setattr(text_ai, "get_provider", lambda _purpose: InjectingProvider())
    response = client.post(f"{path}/{master['id']}/text-suggestions", json={"base_payload_hash": master["payload_hash"], "working_document": master["payload"]["document"], "operation": "rewrite", "selection": {"block_id": "p1", "start": 0, "end": 2}}, headers=HEADERS)
    assert response.status_code == 422, response.text
    assert db_session.query(ContentMasterRevision).count() == 1
    assert db_session.query(LLMRun).first().status == "failed"


def test_provider_output_uses_actual_route_and_ignores_claimed_provenance(client, db_session, monkeypatch):
    import app.services.text_master_ai as text_ai

    _, path = _unit(client, db_session, "text")
    master = _save_v2(client, path)

    class RuntimeProvider:
        name = "actual-provider"
        model = "actual-model"

        async def generate_json(self, request):
            return GenerateResult(data={"patch": {"kind": "replace_text", "block_id": "p1", "start": 0, "end": 2, "replacement": [{"text": "真实建议", "marks": []}]}, "provenance": {"actor": "forged"}}, raw_output="{}", usage={})

    monkeypatch.setattr(text_ai, "get_provider", lambda _purpose: RuntimeProvider())
    response = client.post(f"{path}/{master['id']}/text-suggestions", json={"base_payload_hash": master["payload_hash"], "working_document": master["payload"]["document"], "operation": "rewrite", "selection": {"block_id": "p1", "start": 0, "end": 2}}, headers=HEADERS)
    assert response.status_code == 200, response.text
    run = db_session.get(LLMRun, response.json()["llm_run_id"])
    assert (run.provider, run.model) == ("actual-provider", "actual-model")
    assert run.parsed_output_json["provenance"]["actor"] == HEADERS["X-Studio-User"]


def test_oversized_provider_result_is_not_saved_as_successful_receipt(client, db_session, monkeypatch):
    import app.services.text_master_ai as text_ai

    _, path = _unit(client, db_session, "text")
    master = _save_v2(client, path)

    class OversizedProvider:
        name = "test-provider"

        async def generate_json(self, request):
            return GenerateResult(data={"patch": {}}, raw_output="x" * 257_000, usage={})

    monkeypatch.setattr(text_ai, "get_provider", lambda _purpose: OversizedProvider())
    response = client.post(f"{path}/{master['id']}/text-suggestions", json={"base_payload_hash": master["payload_hash"], "working_document": master["payload"]["document"], "operation": "rewrite", "selection": {"block_id": "p1", "start": 0, "end": 2}}, headers=HEADERS)
    assert response.status_code == 422, response.text
    run = db_session.query(LLMRun).first()
    assert run.status == "failed" and run.raw_output is None
    assert db_session.query(ContentMasterRevision).count() == 1


def test_ai_receipt_rejects_failed_purged_duplicate_and_foreign_runs(client, db_session):
    _, path = _unit(client, db_session, "text")
    master = _save_v2(client, path)
    suggestion = client.post(f"{path}/{master['id']}/text-suggestions", json={"base_payload_hash": master["payload_hash"], "working_document": master["payload"]["document"], "operation": "rewrite", "selection": {"block_id": "p1", "start": 0, "end": 2}}, headers=HEADERS).json()
    run = db_session.get(LLMRun, suggestion["llm_run_id"])
    body = {"expected_revision": 1, "parent_revision_id": master["id"], "idempotency_key": "bad-ai", "payload_schema": "text.master.v2", "payload": {"title": master["payload"]["title"], "document": suggestion["applied_document"]}, "edit_summary": {"ai_edits": [{"llm_run_id": run.id}]}}
    duplicate = client.post(path, json={**body, "edit_summary": {"ai_edits": [{"llm_run_id": run.id}, {"llm_run_id": run.id}]}}, headers=HEADERS)
    assert duplicate.status_code == 422, duplicate.text
    original = run.parsed_output_json
    run.status = "failed"
    db_session.commit()
    assert client.post(path, json=body, headers=HEADERS).status_code == 422
    run.status = "succeeded"
    run.parsed_output_json = None
    db_session.commit()
    assert client.post(path, json=body, headers=HEADERS).status_code == 422
    run.parsed_output_json = original
    db_session.commit()
    other_project, other_path = _unit(client, db_session, "text", suffix="other")
    other = _save_v2(client, other_path, "other")
    foreign = client.post(other_path, json={**body, "parent_revision_id": other["id"], "payload": other["payload"], "idempotency_key": "foreign-ai"}, headers=HEADERS)
    assert foreign.status_code == 422, foreign.text
    assert other_project


def test_ai_receipts_require_continuous_chain_and_label_later_manual_edit(client, db_session):
    _, path = _unit(client, db_session, "text")
    master = _save_v2(client, path, "chain")
    first = client.post(f"{path}/{master['id']}/text-suggestions", json={"base_payload_hash": master["payload_hash"], "working_document": master["payload"]["document"], "operation": "rewrite", "selection": {"block_id": "p1", "start": 0, "end": 2}}, headers=HEADERS).json()
    second = client.post(f"{path}/{master['id']}/text-suggestions", json={"base_payload_hash": master["payload_hash"], "working_document": first["applied_document"], "operation": "tone", "selection": {"block_id": "p1", "start": 0, "end": 2}}, headers=HEADERS).json()
    saved = client.post(path, json={"expected_revision": 1, "parent_revision_id": master["id"], "idempotency_key": "chain-save", "payload_schema": "text.master.v2", "payload": {"title": master["payload"]["title"], "document": second["applied_document"]}, "edit_summary": {"ai_edits": [{"llm_run_id": first["llm_run_id"]}, {"llm_run_id": second["llm_run_id"]}]}}, headers=HEADERS)
    assert saved.status_code == 200, saved.text
    assert [item["status"] for item in saved.json()["edit_summary"]["ai_provenance"]["edits"]] == ["issued", "verified_output_match"]

    _, manual_path = _unit(client, db_session, "text", suffix="manual")
    manual_master = _save_v2(client, manual_path, "manual-chain")
    issued = client.post(f"{manual_path}/{manual_master['id']}/text-suggestions", json={"base_payload_hash": manual_master["payload_hash"], "working_document": manual_master["payload"]["document"], "operation": "rewrite", "selection": {"block_id": "p1", "start": 0, "end": 2}}, headers=HEADERS).json()
    changed = {"schema": "studio.text.document.v1", "blocks": [{"id": "p1", "type": "paragraph", "content": [{"text": "人工后续修改", "marks": []}]}], "citations": []}
    saved_manual = client.post(manual_path, json={"expected_revision": 1, "parent_revision_id": manual_master["id"], "idempotency_key": "manual-after-ai", "payload_schema": "text.master.v2", "payload": {"title": manual_master["payload"]["title"], "document": changed}, "edit_summary": {"ai_edits": [{"llm_run_id": issued["llm_run_id"]}]}}, headers=HEADERS)
    assert saved_manual.status_code == 200, saved_manual.text
    assert saved_manual.json()["edit_summary"]["ai_provenance"]["edits"][0]["status"] == "subsequently_modified"


def test_ai_receipt_broken_chain_unapplied_and_purged_history(client, db_session):
    _, path = _unit(client, db_session, "text")
    master = _save_v2(client, path)
    request = {"base_payload_hash": master["payload_hash"], "working_document": master["payload"]["document"], "operation": "rewrite", "selection": {"block_id": "p1", "start": 0, "end": 2}}
    first = client.post(f"{path}/{master['id']}/text-suggestions", json=request, headers=HEADERS).json()
    second = client.post(f"{path}/{master['id']}/text-suggestions", json={**request, "operation": "tone"}, headers=HEADERS).json()
    body = {"expected_revision": 1, "parent_revision_id": master["id"], "payload_schema": "text.master.v2", "payload": {"title": master["payload"]["title"], "document": second["applied_document"]}, "edit_summary": {"ai_edits": [{"llm_run_id": first["llm_run_id"]}, {"llm_run_id": second["llm_run_id"]}]}}
    broken = client.post(path, json={**body, "idempotency_key": "broken-chain"}, headers=HEADERS)
    assert broken.status_code == 422, broken.text
    assert broken.json()["detail"]["code"] == "broken_ai_edit_chain"
    unapplied = client.post(path, json={**body, "idempotency_key": "unapplied", "payload": master["payload"], "edit_summary": {"ai_edits": [{"llm_run_id": first["llm_run_id"]}]}}, headers=HEADERS)
    assert unapplied.status_code == 200, unapplied.text
    assert unapplied.json()["edit_summary"]["ai_provenance"]["edits"][0]["status"] == "subsequently_modified"
    receipt_id = first["llm_run_id"]
    run = db_session.get(LLMRun, receipt_id)
    run.parsed_output_json = None
    db_session.commit()
    historical = client.get(f"{path}/{unapplied.json()['id']}", headers=HEADERS)
    assert historical.status_code == 200
    assert historical.json()["edit_summary"]["ai_provenance"]["edits"][0]["llm_run_id"] == receipt_id


def test_structured_master_diff_reports_move_modify_and_context_separately(client, db_session):
    _project, path = _unit(client, db_session, "text")
    first = _save_v2(client, path, text="第一段")
    second_payload = {"title": "新标题", "document": {"schema": "studio.text.document.v1", "blocks": [{"id": "p2", "type": "paragraph", "content": [{"text": "第二段", "marks": []}]}, {"id": "p1", "type": "paragraph", "content": [{"text": "第一段修改", "marks": []}]}], "citations": []}}
    second = client.post(path, json={"expected_revision": 1, "parent_revision_id": first["id"], "idempotency_key": "diff", "payload_schema": "text.master.v2", "payload": second_payload}, headers=HEADERS).json()
    response = client.get(f"{path}/{second['id']}/diff", params={"compare_to_id": first["id"]}, headers=HEADERS)
    assert response.status_code == 200, response.text
    diff = response.json()
    assert diff["title"]["changed"] is True
    assert any(item.get("block_id") == "p1" and "move" in item.get("changes", []) and "modify" in item.get("changes", []) for item in diff["blocks"])
    assert diff["context"]["changed"] is False
    assert client.get(f"{path}/{second['id']}/diff", params={"compare_to_id": first["id"]}, headers={"X-Studio-User": "foreign@studio.local"}).status_code == 404


def test_v2_candidate_review_and_local_package_use_frozen_render(client, db_session):
    project, path = _unit(client, db_session, "text")
    master = _save_v2(client, path, "package")
    checks = client.post(f"{path}/{master['id']}/checks", headers=HEADERS)
    assert checks.status_code == 200, checks.text
    freeze = client.post(f"/api/v1/content-projects/{project}/units/{master['content_unit_id']}/candidates/freeze", json={"content_master_revision_id": master["id"], "expected_payload_hash": master["payload_hash"]}, headers=HEADERS)
    assert freeze.status_code == 201, freeze.text
    candidate = freeze.json()
    assert candidate["manifest"]["schema_version"] == 4
    assert candidate["manifest"]["content"].get("markdown") is None
    assert candidate["preview"]["markdown"] == candidate["manifest"]["render"]["body_markdown"]
    warnings = {f"{row['id']}:{row['input_hash']}": "accepted for local test" for row in candidate["manifest"]["checks"] if row["status"] == "warning"}
    approved = client.post(f"/api/v1/content-projects/{project}/units/{master['content_unit_id']}/candidates/{candidate['id']}/approve", json={"candidate_hash": candidate["candidate_hash"], "warning_dispositions": warnings}, headers=HEADERS)
    assert approved.status_code == 200, approved.text
    target = client.post(f"/api/v1/content-projects/{project}/units/{master['content_unit_id']}/candidates/{candidate['id']}/delivery-authorizations", json={"channel": "wechat", "content_form": "article", "account_ref": "test-account", "authorization_version": "v1", "action": "copy_package"}, headers=HEADERS)
    assert target.status_code == 201, target.text
    package = client.post(f"/api/v1/delivery-targets/{target.json()['id']}/package", headers=HEADERS)
    assert package.status_code == 200, package.text
    assert package.json()["content"]["markdown"] == candidate["manifest"]["render"]["body_markdown"]
    archive = client.get(f"/api/v1/delivery-targets/{target.json()['id']}/package.zip", headers=HEADERS)
    assert archive.status_code == 200, archive.text
    with zipfile.ZipFile(io.BytesIO(archive.content)) as zipped:
        assert zipped.read("content.md").decode() == candidate["manifest"]["render"]["body_markdown"]
        archived_manifest = json.loads(zipped.read("manifest.json"))
        assert archived_manifest["candidate"]["hash"] == candidate["candidate_hash"]
        assert archived_manifest["content_master"]["id"] == master["id"]
        assert "draft_id" not in archived_manifest["content_master"]


def test_v2_review_fails_closed_if_frozen_render_is_tampered(client, db_session):
    project, path = _unit(client, db_session, "text")
    master = _save_v2(client, path)
    assert client.post(f"{path}/{master['id']}/checks", headers=HEADERS).status_code == 200
    frozen = client.post(f"/api/v1/content-projects/{project}/units/{master['content_unit_id']}/candidates/freeze", json={"content_master_revision_id": master["id"], "expected_payload_hash": master["payload_hash"]}, headers=HEADERS).json()
    asset = db_session.get(ContentAsset, frozen["id"])
    manifest = dict(asset.candidate_manifest_json)
    manifest["render"] = {**manifest["render"], "body_markdown": "伪造正文"}
    asset.candidate_manifest_json = manifest
    db_session.commit()
    route = f"/api/v1/review-center/projects/{project}/units/{master['content_unit_id']}/candidates/{asset.id}"
    response = client.get(route, headers=HEADERS)
    assert response.status_code == 409, response.text


def test_v2_freeze_preserves_exact_citations_and_evidence_locators(client, db_session):
    project, path = _unit(client, db_session, "text")
    item = db_session.query(FactPackItem).first()
    source = payload("中文😀正文")
    use = {**citation(), "fact_pack_item_id": item.id}
    source["document"]["citations"] = [use]
    locator = {"citation_id": use["id"], **{key: use[key] for key in ("block_id", "start", "end", "selected_text_hash")}}
    saved = client.post(path, json={"idempotency_key": "with-citation", "payload_schema": "text.master.v2", "payload": source, "evidence_refs": [{"fact_pack_item_id": item.id, "snapshot_checksum": item.snapshot_checksum, "locator": locator}]}, headers=HEADERS)
    assert saved.status_code == 200, saved.text
    master = saved.json()
    assert client.post(f"{path}/{master['id']}/checks", headers=HEADERS).status_code == 200
    frozen = client.post(f"/api/v1/content-projects/{project}/units/{master['content_unit_id']}/candidates/freeze", json={"content_master_revision_id": master["id"], "expected_payload_hash": master["payload_hash"]}, headers=HEADERS)
    assert frozen.status_code == 201, frozen.text
    manifest = frozen.json()["manifest"]
    assert manifest["citations"] == [use]
    assert manifest["evidence_refs"][0]["snapshot_checksum"] == item.snapshot_checksum
    assert manifest["evidence_refs"][0]["locator"] == locator


def test_ai_rewrite_of_cited_text_returns_explicit_local_evidence_invalidation(client, db_session):
    _, path = _unit(client, db_session, "text")
    item = db_session.query(FactPackItem).first()
    source = payload("中文😀正文")
    use = {**citation(), "fact_pack_item_id": item.id}
    source["document"]["citations"] = [use]
    locator = {"citation_id": use["id"], **{key: use[key] for key in ("block_id", "start", "end", "selected_text_hash")}}
    response = client.post(path, json={"idempotency_key": "ai-citation-base", "payload_schema": "text.master.v2", "payload": source, "evidence_refs": [{"fact_pack_item_id": item.id, "snapshot_checksum": item.snapshot_checksum, "locator": locator}]}, headers=HEADERS)
    assert response.status_code == 200, response.text
    master = response.json()
    suggested = client.post(f"{path}/{master['id']}/text-suggestions", json={"base_payload_hash": master["payload_hash"], "working_document": master["payload"]["document"], "operation": "rewrite", "selection": {"block_id": "p1", "start": 2, "end": 3}}, headers=HEADERS)
    assert suggested.status_code == 200, suggested.text
    assert suggested.json()["applied_document"]["citations"] == []
    assert suggested.json()["suggested_evidence_refs"] == []
    assert suggested.json()["invalidated_citation_ids"] == ["c1"]
    assert db_session.query(ContentMasterRevision).count() == 1
    shifted = client.post(f"{path}/{master['id']}/text-suggestions", json={"base_payload_hash": master["payload_hash"], "working_document": master["payload"]["document"], "operation": "expand", "selection": {"block_id": "p1", "start": 0, "end": 2}}, headers=HEADERS)
    assert shifted.status_code == 200, shifted.text
    moved = shifted.json()["applied_document"]["citations"][0]
    assert shifted.json()["suggested_evidence_refs"][0]["locator"]["start"] == moved["start"]
    assert shifted.json()["suggested_evidence_refs"][0]["snapshot_checksum"] == item.snapshot_checksum
    assert shifted.json()["invalidated_citation_ids"] == []


def test_text_master_diff_ignores_new_reference_row_ids_for_same_exact_evidence(client, db_session):
    _, path = _unit(client, db_session, "text")
    item = db_session.query(FactPackItem).first()
    source = payload("中文😀正文")
    use = {**citation(), "fact_pack_item_id": item.id}
    source["document"]["citations"] = [use]
    ref = {"fact_pack_item_id": item.id, "snapshot_checksum": item.snapshot_checksum, "locator": {"citation_id": use["id"], **{key: use[key] for key in ("block_id", "start", "end", "selected_text_hash")}}}
    first = client.post(path, json={"idempotency_key": "ref-first", "payload_schema": "text.master.v2", "payload": source, "evidence_refs": [ref]}, headers=HEADERS).json()
    second = client.post(path, json={"idempotency_key": "ref-second", "expected_revision": 1, "payload_schema": "text.master.v2", "payload": source, "evidence_refs": [ref]}, headers=HEADERS).json()
    diff = client.get(f"{path}/{second['id']}/diff", params={"compare_to_id": first["id"]}, headers=HEADERS)
    assert diff.status_code == 200, diff.text
    assert diff.json()["evidence"]["changed"] is False


def test_historical_v1_to_v2_master_diff_is_read_only(client, db_session):
    _, path = _unit(client, db_session, "text")
    old = _v1(client, path)
    preview = client.get(f"{path}/{old['id']}/text-v2-upgrade-preview", headers=HEADERS).json()
    upgraded = client.post(f"{path}/{old['id']}/text-v2-upgrade", json={"idempotency_key": "diff-upgrade", "expected_revision": 1, "expected_payload_hash": old["payload_hash"], "expected_context_hash": preview["current_context_hash"]}, headers=HEADERS)
    assert upgraded.status_code == 200, upgraded.text
    result = client.get(f"{path}/{upgraded.json()['id']}/diff", params={"compare_to_id": old["id"]}, headers=HEADERS)
    assert result.status_code == 200, result.text
    assert (result.json()["from_schema"], result.json()["to_schema"]) == ("text.master.v1", "text.master.v2")
    assert len(client.get(path, headers=HEADERS).json()["items"]) == 2


def test_candidate_diff_v2_metadata_is_structured_and_v1_comparison_is_bounded():
    def frozen(asset_id, schema, blocks, body):
        manifest = {"schema_version": 4, "project": {"modality": "text"}, "content_master": {"payload_schema": schema}, "content": {"document": {"schema": "studio.text.document.v1", "blocks": blocks, "citations": []}}, "render": {"status": "ready", "body_markdown": body, "content_hash": hashlib.sha256(body.encode()).hexdigest()}}
        return ContentAsset(id=asset_id, title="历史", candidate_manifest_json=manifest, candidate_hash=candidate_hash(manifest))

    first = frozen(1, "text.master.v2", [{"id": "a", "type": "paragraph", "content": [{"text": "A", "marks": []}]}, {"id": "b", "type": "paragraph", "content": [{"text": "B", "marks": []}]}], "A\n\nB")
    second = frozen(2, "text.master.v2", [{"id": "b", "type": "paragraph", "content": [{"text": "B", "marks": []}]}, {"id": "a", "type": "paragraph", "content": [{"text": "A2", "marks": []}]}], "B\n\nA2")
    comparison = candidate_diff(first, second)
    assert comparison["structured"] == [{"kind": "move", "changes": ["move"], "block_id": "b"}, {"kind": "modify", "changes": ["move", "modify"], "block_id": "a"}]
    old = frozen(3, "text.master.v1", [], "L" * 3000)
    mixed = candidate_diff(old, second)
    assert mixed["structured"] is None
    assert mixed["text"]["before_chars"] == 2000


def test_ai_revision_flows_to_frozen_review_and_zip_without_legacy_draft(client, db_session):
    project, path = _unit(client, db_session, "text")
    base = _save_v2(client, path)
    suggestion = client.post(f"{path}/{base['id']}/text-suggestions", json={"base_payload_hash": base["payload_hash"], "working_document": base["payload"]["document"], "operation": "rewrite", "selection": {"block_id": "p1", "start": 0, "end": 2}}, headers=HEADERS).json()
    updated = client.post(path, json={"expected_revision": 1, "expected_context_hash": base["context_hash"], "parent_revision_id": base["id"], "idempotency_key": "integrated-ai", "payload_schema": "text.master.v2", "payload": {"title": base["payload"]["title"], "document": suggestion["applied_document"]}, "edit_summary": {"ai_edits": [{"llm_run_id": suggestion["llm_run_id"]}]}}, headers=HEADERS)
    assert updated.status_code == 200, updated.text
    master = updated.json()
    assert master["edit_summary"]["ai_provenance"]["edits"][0]["status"] == "verified_output_match"
    diff = client.get(f"{path}/{master['id']}/diff", params={"compare_to_id": base["id"]}, headers=HEADERS)
    assert diff.status_code == 200, diff.text
    assert diff.json()["ai_provenance"]["changed"] is True
    assert client.post(f"{path}/{master['id']}/checks", headers=HEADERS).status_code == 200
    frozen = client.post(f"/api/v1/content-projects/{project}/units/{master['content_unit_id']}/candidates/freeze", json={"content_master_revision_id": master["id"], "expected_payload_hash": master["payload_hash"]}, headers=HEADERS)
    assert frozen.status_code == 201, frozen.text
    candidate = frozen.json()
    assert candidate["manifest"]["production"]["edit_summary"]["ai_provenance"]["edits"][0]["llm_run_id"] == suggestion["llm_run_id"]
    review = client.get(f"/api/v1/review-center/projects/{project}/units/{master['content_unit_id']}/candidates/{candidate['id']}", headers=HEADERS)
    assert review.status_code == 200, review.text
    assert review.json()["preview"]["markdown"] == candidate["manifest"]["render"]["body_markdown"]
    warnings = {f"{row['id']}:{row['input_hash']}": "accepted for local test" for row in candidate["manifest"]["checks"] if row["status"] == "warning"}
    approved = client.post(f"/api/v1/content-projects/{project}/units/{master['content_unit_id']}/candidates/{candidate['id']}/approve", json={"candidate_hash": candidate["candidate_hash"], "warning_dispositions": warnings}, headers=HEADERS)
    assert approved.status_code == 200, approved.text
    target = client.post(f"/api/v1/content-projects/{project}/units/{master['content_unit_id']}/candidates/{candidate['id']}/delivery-authorizations", json={"channel": "wechat", "content_form": "article", "account_ref": "test-account", "authorization_version": "v1", "action": "copy_package"}, headers=HEADERS)
    assert target.status_code == 201, target.text
    archive = client.get(f"/api/v1/delivery-targets/{target.json()['id']}/package.zip", headers=HEADERS)
    assert archive.status_code == 200, archive.text
    with zipfile.ZipFile(io.BytesIO(archive.content)) as zipped:
        assert zipped.read("content.md").decode() == review.json()["preview"]["markdown"]
    assert db_session.get(ContentMasterRevision, base["id"]).payload_json == base["payload"]
    assert db_session.get(ContentMasterRevision, master["id"]).payload_json == master["payload"]
