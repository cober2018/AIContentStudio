"""Graphic v2 Candidate and local package preserve exact canvas order and bytes."""

import io
import json
import zipfile
from copy import deepcopy
from pathlib import Path

from test_f6a_modality_adapters import HEADERS, _render_material, _unit


def _canvas(canvas_id: str, order: int, body: str) -> dict:
    return {
        "id": canvas_id,
        "order": order,
        "width": 1080,
        "height": 1440,
        "background": {"color": "#ffffff"},
        "layers": [{"id": f"text-{canvas_id}", "order": 0, "type": "text", "x": 10, "y": 20, "width": 400, "height": 80, "runs": [{"text": body, "style": {"font_size": 30, "color": "#123456"}}]}],
    }


def test_graphic_v2_two_canvas_candidate_approval_and_exact_local_package(client, db_session, tmp_path):
    project, path = _unit(client, db_session, "graphic", suffix="_f6c_package")
    outputs = [_render_material(db_session, project, tmp_path, "graphic", f"render-{index}") for index in range(2)]
    canvas_ids = ["cover", "second"]
    declarations = [{"canvas_id": canvas_id, "material_revision_id": output.id} for canvas_id, output in zip(canvas_ids, outputs, strict=True)]
    asset_refs = [
        {"material_revision_id": output.id, "content_hash": output.content_hash, "role": "render_output", "slot_key": canvas_id, "sort_order": index, "placement": {"canvas_id": canvas_id}}
        for index, (canvas_id, output) in enumerate(zip(canvas_ids, outputs, strict=True))
    ]
    payload = {"canvases": [_canvas("cover", 0, "封面"), _canvas("second", 1, "正文")], "render_asset_ref": declarations}
    payload["canvases"][1]["layers"].append({"id": "card-image", "order": 1, "type": "image", "x": 0, "y": 120, "width": 300, "height": 300, "material_revision_id": outputs[1].id, "fit": "cover"})
    asset_refs.insert(0, {"material_revision_id": outputs[1].id, "content_hash": outputs[1].content_hash, "role": "graphic_layer", "slot_key": "card-image", "sort_order": 0, "placement": {"canvas_id": "second", "layer_id": "card-image"}})
    request = {"payload_schema": "graphic.master.v2", "payload": payload, "asset_refs": asset_refs, "content_form": "final"}
    saved = client.post(path, json={"idempotency_key": "graphic-draft", **request}, headers=HEADERS)
    assert saved.status_code == 200, saved.text
    readiness = client.get(f"{path}/{saved.json()['id']}/readiness", headers=HEADERS)
    assert readiness.status_code == 200, readiness.text
    unverified = client.post(path, json={"idempotency_key": "graphic-unverified-renderer", "expected_revision": 1, **request, "render_attestation": {"origin": "verified_renderer", "confirmed": True, "render_input_hash": readiness.json()["render_input_hash"]}}, headers=HEADERS)
    assert unverified.status_code == 422, unverified.text
    assert unverified.json()["detail"]["code"] == "renderer_capability_unavailable"
    assert len(client.get(path, headers=HEADERS).json()["items"]) == 1
    confirmed = client.post(path, json={"idempotency_key": "graphic-attested", "expected_revision": 1, **request, "render_attestation": {"confirmed": True, "render_input_hash": readiness.json()["render_input_hash"]}}, headers=HEADERS)
    assert confirmed.status_code == 200, confirmed.text
    master = confirmed.json()
    checked = client.post(f"{path}/{master['id']}/checks", headers=HEADERS)
    assert checked.status_code == 200, checked.text
    current_checks = checked.json()["items"]
    assert {item["check_kind"] for item in current_checks} >= {"graphic_structure", "graphic_fact", "graphic_identity", "graphic_platform"}
    assert not any(item["status"] in {"blocker", "incomplete", "stale"} for item in current_checks)
    frozen = client.post(path.replace("master-revisions", "candidates/freeze"), json={"content_master_revision_id": master["id"], "expected_payload_hash": master["payload_hash"]}, headers=HEADERS)
    assert frozen.status_code == 201, frozen.text
    candidate = frozen.json()
    unit_id = path.split("/")[6]
    review_url = f"/api/v1/review-center/projects/{project}/units/{unit_id}/candidates/{candidate['id']}"
    reviewed = client.get(review_url, headers=HEADERS)
    assert reviewed.status_code == 200, reviewed.text
    assert [item["text"] for item in reviewed.json()["preview"]["canvases"]] == ["封面", "正文"]
    assert reviewed.json()["preview"]["checks"]
    exact_render = client.get(f"{review_url}/renders/{outputs[1].id}", headers=HEADERS)
    assert exact_render.status_code == 200, exact_render.text
    assert exact_render.content == Path(outputs[1].file_path).read_bytes()
    base = f"{path.replace('master-revisions', 'candidates')}/{candidate['id']}"
    disposition = {f"{item['id']}:{item['input_hash']}": "人工确认此覆盖范围限制" for item in current_checks if item["status"] == "warning"}
    approved = client.post(f"{base}/approve", json={"candidate_hash": candidate["candidate_hash"], "warning_dispositions": disposition}, headers=HEADERS)
    assert approved.status_code == 200, approved.text
    authorized = client.post(f"{base}/delivery-authorizations", json={"channel": "fixture_graphic_f6c_package", "content_form": "final", "account_ref": "manual", "authorization_version": "v1", "action": "copy_package"}, headers=HEADERS)
    assert authorized.status_code == 201, authorized.text
    archive_response = client.get(f"/api/v1/delivery-targets/{authorized.json()['id']}/package.zip", headers=HEADERS)
    assert archive_response.status_code == 200, archive_response.text
    with zipfile.ZipFile(io.BytesIO(archive_response.content)) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        assert len(archive.namelist()) == len(set(archive.namelist()))
        assert [name for name in archive.namelist() if name.startswith("render-")] == ["render-1.png", "render-2.png"]
        assert manifest["schema_version"] == 4
        assert manifest["content_master"]["id"] == master["id"]
        assert [output["canvas_id"] for output in manifest["render"]["outputs"]] == canvas_ids
        assert archive.read("render-1.png") == Path(outputs[0].file_path).read_bytes()
        assert archive.read("render-2.png") == Path(outputs[1].file_path).read_bytes()
        assert "content.md" not in archive.namelist()
    changed_payload = deepcopy(payload)
    changed_payload["canvases"][1]["layers"][0]["runs"][0]["text"] = "第二版正文"
    draft = client.post(path, json={"idempotency_key": "graphic-next-draft", "expected_revision": 2, "payload_schema": "graphic.master.v2", "payload": changed_payload, "asset_refs": asset_refs, "content_form": "final"}, headers=HEADERS)
    assert draft.status_code == 200, draft.text
    next_readiness = client.get(f"{path}/{draft.json()['id']}/readiness", headers=HEADERS)
    assert next_readiness.status_code == 200, next_readiness.text
    next_master = client.post(path, json={"idempotency_key": "graphic-next-attested", "expected_revision": 3, "payload_schema": "graphic.master.v2", "payload": changed_payload, "asset_refs": asset_refs, "content_form": "final", "render_attestation": {"confirmed": True, "render_input_hash": next_readiness.json()["render_input_hash"]}}, headers=HEADERS)
    assert next_master.status_code == 200, next_master.text
    next_checks = client.post(f"{path}/{next_master.json()['id']}/checks", headers=HEADERS)
    assert next_checks.status_code == 200, next_checks.text
    next_candidate = client.post(path.replace("master-revisions", "candidates/freeze"), json={"content_master_revision_id": next_master.json()["id"], "expected_payload_hash": next_master.json()["payload_hash"]}, headers=HEADERS)
    assert next_candidate.status_code == 201, next_candidate.text
    old_review = client.get(review_url, headers=HEADERS)
    assert old_review.status_code == 200, old_review.text
    assert [item["text"] for item in old_review.json()["preview"]["canvases"]] == ["封面", "正文"]
    assert {(item["check_kind"], item["input_hash"], item["status"]) for item in old_review.json()["preview"]["checks"]} == {(item["check_kind"], item["input_hash"], item["status"]) for item in current_checks}
    next_review_url = f"/api/v1/review-center/projects/{project}/units/{unit_id}/candidates/{next_candidate.json()['id']}"
    next_review = client.get(next_review_url, headers=HEADERS)
    assert next_review.status_code == 200, next_review.text
    assert [item["text"] for item in next_review.json()["preview"]["canvases"]] == ["封面", "第二版正文"]
    assert {(item["check_kind"], item["input_hash"], item["status"]) for item in next_review.json()["preview"]["checks"]} == {(item["check_kind"], item["input_hash"], item["status"]) for item in next_checks.json()["items"]}
    compared = client.get(f"{next_review_url}/diff", headers=HEADERS)
    assert compared.status_code == 200, compared.text
    assert compared.json()["from_candidate_id"] == candidate["id"]
    assert compared.json()["structured"]
    assert compared.json()["text"] is None
    outputs[1].public_use_allowed = False
    db_session.commit()
    blocked = client.get(f"/api/v1/delivery-targets/{authorized.json()['id']}/package.zip", headers=HEADERS)
    assert blocked.status_code == 409, blocked.text
