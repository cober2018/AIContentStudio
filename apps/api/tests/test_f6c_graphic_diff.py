"""Graphic v2 diff identifies stable canvas and layer changes without text similarity."""

import importlib

import pytest
from fastapi import HTTPException
from test_f6c_graphic_documents import canvas, text_layer

from app.models import ChannelTemplateVersion, ContentAsset
from app.services.candidates import candidate_hash
from app.services.project_review_projection import candidate_diff, candidate_preview


def test_graphic_diff_reports_canvas_move_resize_add_and_text_modify():
    diff = importlib.import_module("app.services.graphic_master_diff").diff_graphic_documents
    before = {"canvases": [canvas("first", 0, [text_layer("title", 0, "原文")]), canvas("second", 1, [text_layer("body", 0, "旧正文")])]}
    after = {"canvases": [canvas("second", 0, [text_layer("body", 0, "新正文")]), canvas("first", 1, [text_layer("title", 0, "原文")], width=1200), canvas("third", 2, [text_layer("new", 0, "新卡")])]}
    result = diff(before, after)
    changes = {item["canvas_id"]: item for item in result["canvases"]}
    assert {"move", "resize"}.issubset(changes["first"]["changes"])
    assert "move" in changes["second"]["changes"]
    assert changes["third"]["kind"] == "add"
    layers = {(item["canvas_id"], item["layer_id"]): item for item in result["layers"]}
    assert "text" in layers[("second", "body")]["changes"]
    assert "similarity" not in str(result)


def test_graphic_diff_identifies_layer_moved_between_canvases():
    diff = importlib.import_module("app.services.graphic_master_diff").diff_graphic_documents
    layer = text_layer("shared", 0, "同一层")
    before = {"canvases": [canvas("one", 0, [layer]), canvas("two", 1, [])]}
    after = {"canvases": [canvas("one", 0, []), canvas("two", 1, [layer])]}
    result = diff(before, after)
    changes = [item for item in result["layers"] if item["layer_id"] == "shared"]
    assert len(changes) == 1
    assert changes[0]["kind"] == "move"
    assert changes[0]["from_canvas_id"] == "one"
    assert changes[0]["to_canvas_id"] == "two"


def test_graphic_master_diff_route_reads_exact_two_revisions(client, db_session):
    headers = {"X-Studio-User": "graphic-diff@studio.local"}
    db_session.add(ChannelTemplateVersion(channel="graphic_diff_fixture", version=1, name="图像差异", status="published", profile_json={"content_forms": {"final": {"artifact_kind": "image"}}}))
    db_session.commit()
    persona = client.post("/api/v1/content-personas", json={"name": "设计师"}, headers=headers).json()["id"]
    project = client.post("/api/v1/content-projects", json={"title": "差异项目"}, headers=headers).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project}/units", json={"title": "卡片", "persona_id": persona, "modality": "graphic", "channel_id": "graphic_diff_fixture"}, headers=headers).json()["id"]
    path = f"/api/v1/content-projects/{project}/units/{unit}/master-revisions"
    first = client.post(path, json={"idempotency_key": "diff-first", "payload_schema": "graphic.master.v2", "payload": {"canvases": [canvas("one", 0, [text_layer("copy", 0, "旧文")])]}}, headers=headers)
    assert first.status_code == 200, first.text
    second = client.post(path, json={"idempotency_key": "diff-second", "expected_revision": 1, "payload_schema": "graphic.master.v2", "payload": {"canvases": [canvas("one", 0, [text_layer("copy", 0, "新文")])]}}, headers=headers)
    assert second.status_code == 200, second.text
    response = client.get(f"{path}/{second.json()['id']}/diff", params={"compare_to_id": first.json()["id"]}, headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["from_schema"] == response.json()["to_schema"] == "graphic.master.v2"
    assert "text" in response.json()["layers"][0]["changes"]
    assert "similarity" not in str(response.json())


def test_candidate_review_uses_frozen_graphic_v2_content_and_structured_diff():
    before = {"canvases": [canvas("cover", 0, [text_layer("title", 0, "旧标题")])]}
    after = {"canvases": [canvas("cover", 0, [text_layer("title", 0, "新标题")]), canvas("card", 1, [text_layer("copy", 0, "第二张")])]}

    def asset(asset_id: int, payload: dict):
        outputs = [{"canvas_id": item["id"], "material_revision_id": index + 10, "content_hash": "a" * 64, "mime_type": "image/png"} for index, item in enumerate(payload["canvases"])]
        manifest = {"schema_version": 4, "project": {"modality": "graphic"}, "content_master": {"payload_schema": "graphic.master.v2"}, "content": payload, "render": {"status": "ready", "origin": "manual", "outputs": outputs}, "checks": [{"check_kind": "graphic_platform", "status": "pass"}]}
        return ContentAsset(id=asset_id, title="图文成品", candidate_manifest_json=manifest, candidate_hash=candidate_hash(manifest))

    prior, current = asset(1, before), asset(2, after)
    preview = candidate_preview(current)
    assert preview["canvases"][0]["text"] == "新标题"
    assert preview["canvases"][1]["render_output"]["material_revision_id"] == 11
    assert preview["checks"][0]["check_kind"] == "graphic_platform"
    result = candidate_diff(prior, current)
    assert result["text"] is None
    assert result["structured"]["canvases"][0]["kind"] == "add"
    assert "text" in result["structured"]["layers"][0]["changes"]
    current.candidate_manifest_json["content"]["canvases"][0]["layers"][0]["runs"][0]["text"] = "篡改"
    with pytest.raises(HTTPException) as exc:
        candidate_preview(current)
    assert exc.value.status_code == 409
