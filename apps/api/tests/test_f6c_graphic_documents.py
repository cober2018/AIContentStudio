"""Graphic v2 document boundaries and deterministic canonical form."""

import hashlib
import importlib

import pytest

from app.models import (
    ChannelTemplateVersion,
    ContentMasterRevision,
    FactPack,
    FactPackItem,
    Material,
    MaterialRevision,
    ProjectMaterialReference,
)
from app.services.production_modalities import adapter_for, default_payload_schema, supported_payload_schemas


def graphics():
    return importlib.import_module("app.services.graphic_documents")


def text_layer(layer_id: str, order: int, value: str) -> dict:
    return {
        "id": layer_id,
        "order": order,
        "type": "text",
        "x": 10,
        "y": 20,
        "width": 400,
        "height": 80,
        "runs": [{"text": value, "style": {"font_size": 30, "color": "#123456"}}],
    }


def canvas(canvas_id: str, order: int, layers: list[dict], **extra: object) -> dict:
    return {
        "id": canvas_id,
        "order": order,
        "width": 1080,
        "height": 1440,
        "background": {"color": "#ffffff"},
        "layers": layers,
        **extra,
    }


def test_graphic_v2_canonicalizes_order_without_changing_inputs():
    input_payload = {
        "title": "两张卡片",
        "canvases": [
            canvas("second", 1, [text_layer("late", 1, "第二张"), text_layer("early", 0, "先读我")], variant_of_canvas_id="first"),
            canvas("first", 0, [text_layer("intro", 0, "第一张")]),
        ],
    }
    normalized = graphics().canonical_payload(input_payload)
    assert [item["id"] for item in normalized["canvases"]] == ["first", "second"]
    assert [item["id"] for item in normalized["canvases"][1]["layers"]] == ["early", "late"]
    assert normalized["canvases"][1]["variant_of_canvas_id"] == "first"
    assert normalized == graphics().canonical_payload(normalized)
    assert [item["id"] for item in input_payload["canvases"]] == ["second", "first"]
    assert graphics().document_hash(input_payload) == graphics().document_hash(normalized)


def test_canvas_reorder_preserves_variant_lineage_but_rejects_cycles():
    payload = {"canvases": [canvas("variant", 0, [], variant_of_canvas_id="source"), canvas("source", 1, [])]}
    assert graphics().canonical_payload(payload)["canvases"][0]["variant_of_canvas_id"] == "source"
    payload["canvases"][1]["variant_of_canvas_id"] = "variant"
    with pytest.raises(graphics().GraphicDocumentError, match="graphic_variant_source_invalid"):
        graphics().canonical_payload(payload)


@pytest.mark.parametrize("change", ["variant", "layer_type", "media_fit", "shape_kind", "text_align"])
def test_graphic_v2_malformed_json_types_return_domain_errors(change: str):
    base = canvas("a", 0, [text_layer("copy", 0, "正文")])
    if change == "variant":
        base["variant_of_canvas_id"] = ["a"]
    elif change == "layer_type":
        base["layers"][0]["type"] = ["text"]
    elif change == "media_fit":
        base["layers"] = [{"id": "media", "order": 0, "type": "image", "x": 0, "y": 0, "width": 100, "height": 100, "material_revision_id": 7, "fit": ["cover"]}]
    elif change == "shape_kind":
        base["layers"] = [{"id": "shape", "order": 0, "type": "shape", "x": 0, "y": 0, "width": 100, "height": 100, "shape": ["rectangle"]}]
    else:
        base["layers"][0]["runs"][0]["style"]["align"] = ["left"]
    with pytest.raises(graphics().GraphicDocumentError):
        graphics().canonical_payload({"canvases": [base]})


@pytest.mark.parametrize(
    ("payload", "error"),
    [
        ({"canvases": []}, "graphic_canvas_required"),
        ({"canvases": [canvas("a", 0, []), canvas("a", 1, [])]}, "graphic_canvas_duplicate_id"),
        ({"canvases": [canvas("a", 1, [])]}, "graphic_canvas_order_invalid"),
        ({"canvases": [canvas("a", 0, [], variant_of_canvas_id="missing")]}, "graphic_variant_source_invalid"),
        ({"canvases": [canvas("a", 0, [text_layer("x", 0, "x"), text_layer("x", 1, "y")])]}, "graphic_layer_duplicate_id"),
        ({"canvases": [canvas("a", 0, [{**text_layer("x", 0, "x"), "x": float("nan")}])]}, "graphic_geometry_invalid"),
        ({"canvases": [canvas("a", 0, [{**text_layer("x", 0, "x"), "type": "html"}])]}, "graphic_layer_type_invalid"),
        ({"canvases": [canvas("a", 0, [{**text_layer("x", 0, "x"), "file_path": "/tmp/a.png"}])]}, "graphic_field_unknown"),
        ({"canvases": [canvas("a", 0, [{**text_layer("x", 0, "x"), "runs": [{"text": "x", "style": {"font_size": 30, "font_family": "remote"}}]}])]}, "graphic_style_invalid"),
    ],
)
def test_graphic_v2_rejects_invalid_document(payload: dict, error: str):
    with pytest.raises(graphics().GraphicDocumentError, match=error):
        graphics().canonical_payload(payload)


def test_graphic_v2_requires_exact_media_layer_ids_and_rejects_raw_urls():
    payload = {"canvases": [canvas("a", 0, [{"id": "image-a", "order": 0, "type": "image", "x": 0, "y": 0, "width": 200, "height": 100, "material_revision_id": 7, "fit": "cover"}])]}
    assert graphics().canonical_payload(payload)["canvases"][0]["layers"][0]["material_revision_id"] == 7
    payload["canvases"][0]["layers"][0]["url"] = "https://example.invalid/image.png"
    with pytest.raises(graphics().GraphicDocumentError, match="graphic_field_unknown"):
        graphics().canonical_payload(payload)


def test_graphic_v2_media_reuse_requires_one_exact_placement_ref_per_layer():
    layer = {"type": "image", "x": 0, "y": 0, "width": 200, "height": 100, "material_revision_id": 7, "fit": "cover"}
    payload = {"canvases": [canvas("one", 0, [{**layer, "id": "image-a", "order": 0}]), canvas("two", 1, [{**layer, "id": "image-b", "order": 0}])]}
    refs = [
        {"material_revision_id": 7, "content_hash": "a" * 64, "role": "graphic_layer", "slot_key": layer_id, "placement": {"canvas_id": canvas_id, "layer_id": layer_id}}
        for canvas_id, layer_id in (("one", "image-a"), ("two", "image-b"))
    ]
    assert graphics().validate_references(payload, refs, []) is None
    with pytest.raises(graphics().GraphicDocumentError, match="graphic_asset_placement_mismatch"):
        graphics().validate_references(payload, refs[:1], [])
    with pytest.raises(graphics().GraphicDocumentError, match="graphic_asset_placement_mismatch"):
        graphics().validate_references(payload, [refs[0], {**refs[1], "slot_key": "image-a"}], [])


def test_graphic_v2_text_claim_requires_exact_evidence_locator():
    layer = text_layer("claim", 0, "已验证的表述")
    layer["claims"] = [{"fact_pack_item_id": 9, "snapshot_checksum": "s" * 64, "start": 0, "end": 3}]
    payload = {"canvases": [canvas("cover", 0, [layer])]}
    evidence = [{"fact_pack_item_id": 9, "snapshot_checksum": "s" * 64, "role": "claim", "locator": {"canvas_id": "cover", "layer_id": "claim", "start": 0, "end": 3}}]
    assert graphics().validate_references(payload, [], evidence) is None
    with pytest.raises(graphics().GraphicDocumentError, match="graphic_evidence_locator_mismatch"):
        graphics().validate_references(payload, [], [{**evidence[0], "locator": {**evidence[0]["locator"], "end": 4}}])
    with pytest.raises(graphics().GraphicDocumentError, match="graphic_evidence_locator_mismatch"):
        graphics().validate_references(payload, [], [{**evidence[0], "locator": {**evidence[0]["locator"], "canvas_id": ["cover"]}}])
    with pytest.raises(graphics().GraphicDocumentError, match="graphic_claim_range_invalid"):
        graphics().canonical_payload({"canvases": [canvas("cover", 0, [{**layer, "claims": [{**layer["claims"][0], "end": 1000}]}])]})


def test_graphic_v1_conversion_keeps_provable_content_and_discards_old_render_attestation():
    source = {"title": "旧版", "canvases": [canvas("first", 0, [text_layer("copy", 0, "原文")])], "render_asset_ref": {"canvas_id": "first", "material_revision_id": 11}}
    converted = graphics().convert_legacy_graphic(source, asset_refs=[{"material_revision_id": 11, "content_hash": "a" * 64, "role": "render_output"}], evidence_refs=[])
    assert converted["payload"] == graphics().canonical_payload({"title": "旧版", "canvases": source["canvases"]})
    assert converted["asset_refs"] == []
    assert converted["warnings"] == [{"code": "legacy_render_requires_new_attestation"}]
    assert source["render_asset_ref"] == {"canvas_id": "first", "material_revision_id": 11}
    with pytest.raises(graphics().GraphicDocumentError, match="graphic_background_invalid"):
        graphics().convert_legacy_graphic({"canvases": [{"id": "first", "order": 0}]}, asset_refs=[], evidence_refs=[])


def test_graphic_v2_adapter_is_registered_without_reinterpreting_unspecified_legacy_payloads():
    assert default_payload_schema("graphic") == "graphic.master.v1"
    assert set(supported_payload_schemas("graphic")) == {"graphic.master.v1", "graphic.master.v2"}
    assert adapter_for("graphic", "graphic.master.v1").payload_schema == "graphic.master.v1"
    payload = {"canvases": [canvas("a", 0, [text_layer("copy", 0, "独立文字")])]}
    assert adapter_for("graphic", "graphic.master.v2").validate_payload(payload) == []
    assert adapter_for("graphic", "graphic.master.v2").validate_payload({"canvases": [canvas("a", 0, [], file_path="/private")]}) == ["graphic_field_unknown"]


def test_graphic_v2_save_persists_canonical_order_without_changing_legacy_default(client, db_session):
    headers = {"X-Studio-User": "graphic-v2@studio.local"}
    db_session.add(ChannelTemplateVersion(channel="graphic_v2_fixture", version=1, name="图像测试", status="published", profile_json={"content_forms": {"final": {"artifact_kind": "image"}}}))
    db_session.commit()
    persona = client.post("/api/v1/content-personas", json={"name": "设计师"}, headers=headers).json()["id"]
    project = client.post("/api/v1/content-projects", json={"title": "视觉项目"}, headers=headers).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project}/units", json={"title": "卡片", "persona_id": persona, "modality": "graphic", "channel_id": "graphic_v2_fixture"}, headers=headers).json()["id"]
    path = f"/api/v1/content-projects/{project}/units/{unit}/master-revisions"
    payload = {"title": "两页", "canvases": [canvas("second", 1, [text_layer("second-text", 0, "第二页")], variant_of_canvas_id="first"), canvas("first", 0, [text_layer("first-text", 0, "第一页")])]}
    response = client.post(path, json={"idempotency_key": "graphic-v2-save", "payload_schema": "graphic.master.v2", "payload": payload}, headers=headers)
    assert response.status_code == 200, response.text
    saved = response.json()
    assert saved["payload_schema"] == "graphic.master.v2"
    assert saved["payload"] == graphics().canonical_payload(payload)
    assert saved["payload_hash"] == graphics().document_hash(payload)
    readback = client.get(f"{path}/{saved['id']}", headers=headers)
    assert readback.status_code == 200, readback.text
    assert readback.json()["payload"] == saved["payload"]
    retry = client.post(path, json={"idempotency_key": "graphic-v2-save", "payload_schema": "graphic.master.v2", "payload": graphics().canonical_payload(payload)}, headers=headers)
    assert retry.status_code == 200, retry.text
    assert retry.json()["id"] == saved["id"]
    invalid = client.post(path, json={"idempotency_key": "graphic-v2-invalid", "expected_revision": 1, "payload_schema": "graphic.master.v2", "payload": {"canvases": [canvas("bad", 0, [{**text_layer("x", 0, "x"), "url": "https://bad.invalid"}])]}}, headers=headers)
    assert invalid.status_code == 422, invalid.text
    assert db_session.query(ContentMasterRevision).filter_by(content_unit_id=unit).count() == 1


def test_graphic_v2_save_requires_live_kind_and_exact_project_asset_placement(client, db_session, tmp_path):
    headers = {"X-Studio-User": "graphic-asset@studio.local"}
    db_session.add(ChannelTemplateVersion(channel="graphic_asset_fixture", version=1, name="图像素材测试", status="published", profile_json={"content_forms": {"final": {"artifact_kind": "image"}}}))
    db_session.commit()
    persona = client.post("/api/v1/content-personas", json={"name": "设计师"}, headers=headers).json()["id"]
    project = client.post("/api/v1/content-projects", json={"title": "视觉素材项目"}, headers=headers).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project}/units", json={"title": "卡片", "persona_id": persona, "modality": "graphic", "channel_id": "graphic_asset_fixture"}, headers=headers).json()["id"]
    path = f"/api/v1/content-projects/{project}/units/{unit}/master-revisions"
    content = b"\x89PNG\r\n\x1a\nexact image bytes"
    file = tmp_path / "image.png"
    file.write_bytes(content)
    material = Material(title="输入图", kind="video", status="active")
    db_session.add(material)
    db_session.flush()
    revision = MaterialRevision(material_id=material.id, content_hash=hashlib.sha256(content).hexdigest(), file_path=str(file), mime_type="image/png", status="candidate", public_use_allowed=True, rights_status="cleared")
    db_session.add(revision)
    db_session.flush()
    db_session.add(ProjectMaterialReference(project_id=project, material_revision_id=revision.id, origin="system_library", status="active"))
    db_session.commit()
    layer = {"id": "hero", "order": 0, "type": "image", "x": 0, "y": 0, "width": 400, "height": 300, "material_revision_id": revision.id, "fit": "cover"}
    payload = {"canvases": [canvas("cover", 0, [layer])]}
    ref = {"material_revision_id": revision.id, "content_hash": revision.content_hash, "role": "graphic_layer", "slot_key": "hero", "placement": {"canvas_id": "cover", "layer_id": "hero"}}
    wrong_kind = client.post(path, json={"idempotency_key": "wrong-kind", "payload_schema": "graphic.master.v2", "payload": payload, "asset_refs": [ref]}, headers=headers)
    assert wrong_kind.status_code == 422, wrong_kind.text
    material.kind = "image"
    db_session.commit()
    wrong_slot = client.post(path, json={"idempotency_key": "wrong-slot", "payload_schema": "graphic.master.v2", "payload": payload, "asset_refs": [{**ref, "slot_key": "elsewhere"}]}, headers=headers)
    assert wrong_slot.status_code == 422, wrong_slot.text
    accepted = client.post(path, json={"idempotency_key": "valid-media", "payload_schema": "graphic.master.v2", "payload": payload, "asset_refs": [ref]}, headers=headers)
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["assets"][0]["slot_key"] == "hero"
    assert db_session.query(ContentMasterRevision).filter_by(content_unit_id=unit).count() == 1
    reused_layer = {**layer, "id": "reused"}
    reused_ref = {**ref, "slot_key": "reused", "placement": {"canvas_id": "second", "layer_id": "reused"}, "sort_order": 1}
    reused = client.post(path, json={"idempotency_key": "reused-media", "expected_revision": 1, "payload_schema": "graphic.master.v2", "payload": {"canvases": [canvas("cover", 0, [layer]), canvas("second", 1, [reused_layer])]}, "asset_refs": [ref, reused_ref]}, headers=headers)
    assert reused.status_code == 200, reused.text
    assert [asset["material_revision_id"] for asset in reused.json()["assets"]] == [revision.id, revision.id]
    assert [asset["placement"]["canvas_id"] for asset in reused.json()["assets"]] == ["cover", "second"]


def test_graphic_v2_render_attestation_requires_canonical_canvas_order(client, db_session, tmp_path):
    headers = {"X-Studio-User": "graphic-order@studio.local"}
    db_session.add(ChannelTemplateVersion(channel="graphic_order_fixture", version=1, name="图像顺序测试", status="published", profile_json={"content_forms": {"final": {"artifact_kind": "image"}}}))
    db_session.commit()
    persona = client.post("/api/v1/content-personas", json={"name": "设计师"}, headers=headers).json()["id"]
    project = client.post("/api/v1/content-projects", json={"title": "多画布项目"}, headers=headers).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project}/units", json={"title": "双卡", "persona_id": persona, "modality": "graphic", "channel_id": "graphic_order_fixture"}, headers=headers).json()["id"]
    path = f"/api/v1/content-projects/{project}/units/{unit}/master-revisions"
    revisions = []
    for index in range(2):
        content = b"\x89PNG\r\n\x1a\nexact image bytes" + bytes([index])
        file = tmp_path / f"render-{index}.png"
        file.write_bytes(content)
        material = Material(title=f"成品{index}", kind="image", status="active")
        db_session.add(material)
        db_session.flush()
        revision = MaterialRevision(material_id=material.id, content_hash=hashlib.sha256(content).hexdigest(), file_path=str(file), mime_type="image/png", status="active", public_use_allowed=True, rights_status="cleared")
        db_session.add(revision)
        db_session.flush()
        db_session.add(ProjectMaterialReference(project_id=project, material_revision_id=revision.id, origin="system_library", status="active"))
        revisions.append(revision)
    db_session.commit()
    declarations = [{"canvas_id": canvas_id, "material_revision_id": revision.id} for canvas_id, revision in zip(("first", "second"), revisions, strict=True)]
    asset_refs = [{"material_revision_id": revision.id, "content_hash": revision.content_hash, "role": "render_output", "slot_key": canvas_id, "sort_order": index, "placement": {"canvas_id": canvas_id}} for index, (canvas_id, revision) in enumerate(zip(("first", "second"), revisions, strict=True))]
    payload = {"canvases": [canvas("first", 0, [text_layer("a", 0, "第一页")]), canvas("second", 1, [text_layer("b", 0, "第二页")])], "render_asset_ref": list(reversed(declarations))}
    saved = client.post(path, json={"idempotency_key": "draft-order", "payload_schema": "graphic.master.v2", "payload": payload, "asset_refs": asset_refs}, headers=headers)
    assert saved.status_code == 200, saved.text
    readiness = client.get(f"{path}/{saved.json()['id']}/readiness", headers=headers).json()
    bad = client.post(path, json={"idempotency_key": "wrong-order", "expected_revision": 1, "payload_schema": "graphic.master.v2", "payload": payload, "asset_refs": asset_refs, "render_attestation": {"confirmed": True, "render_input_hash": readiness["render_input_hash"]}}, headers=headers)
    assert bad.status_code == 422, bad.text
    assert db_session.query(ContentMasterRevision).filter_by(content_unit_id=unit).count() == 1
    wrong_binding_refs = [{**asset_refs[0], "slot_key": "second", "placement": {"canvas_id": "second"}}, asset_refs[1]]
    wrong_binding = client.post(path, json={"idempotency_key": "wrong-binding", "expected_revision": 1, "payload_schema": "graphic.master.v2", "payload": {**payload, "render_asset_ref": declarations}, "asset_refs": wrong_binding_refs, "render_attestation": {"confirmed": True, "render_input_hash": readiness["render_input_hash"]}}, headers=headers)
    assert wrong_binding.status_code == 422, wrong_binding.text
    for case, declared, refs in (
        ("missing-output", declarations[:1], asset_refs[:1]),
        ("duplicate-output", [declarations[0], declarations[0]], asset_refs),
        ("mismatched-hash", declarations, [{**asset_refs[0], "content_hash": "f" * 64}, asset_refs[1]]),
    ):
        rejected = client.post(path, json={"idempotency_key": case, "expected_revision": 1, "payload_schema": "graphic.master.v2", "payload": {**payload, "render_asset_ref": declared}, "asset_refs": refs, "render_attestation": {"confirmed": True, "render_input_hash": readiness["render_input_hash"]}}, headers=headers)
        assert rejected.status_code == 422, (case, rejected.text)
        assert db_session.query(ContentMasterRevision).filter_by(content_unit_id=unit).count() == 1
    revisions[1].material.kind = "chart"
    db_session.flush()
    wrong_kind = client.post(path, json={"idempotency_key": "wrong-kind-output", "expected_revision": 1, "payload_schema": "graphic.master.v2", "payload": {**payload, "render_asset_ref": declarations}, "asset_refs": asset_refs, "render_attestation": {"confirmed": True, "render_input_hash": readiness["render_input_hash"]}}, headers=headers)
    assert wrong_kind.status_code == 422, wrong_kind.text
    revisions[1].material.kind = "image"
    db_session.flush()
    good = client.post(path, json={"idempotency_key": "right-order", "expected_revision": 1, "payload_schema": "graphic.master.v2", "payload": {**payload, "render_asset_ref": declarations}, "asset_refs": asset_refs, "render_attestation": {"confirmed": True, "render_input_hash": readiness["render_input_hash"]}}, headers=headers)
    assert good.status_code == 200, good.text
    render = client.get(f"{path}/{good.json()['id']}/readiness", headers=headers).json()["render"]
    assert render["status"] == "ready"
    assert [output["canvas_id"] for output in render["outputs"]] == ["first", "second"]
    package = adapter_for("graphic", "graphic.master.v2").build_package_projection(db_session, db_session.get(ContentMasterRevision, good.json()["id"]))
    assert [item["material_revision_id"] for item in package["material_outputs"]] == [revision.id for revision in revisions]
    changed_canvas = canvas("first", 0, [text_layer("a", 0, "新第一页")])
    changed = client.post(path, json={"idempotency_key": "stale-render", "expected_revision": 2, "payload_schema": "graphic.master.v2", "payload": {"canvases": [changed_canvas, payload["canvases"][1]], "render_asset_ref": declarations}, "asset_refs": asset_refs, "render_attestation": {"confirmed": True, "render_input_hash": readiness["render_input_hash"]}}, headers=headers)
    assert changed.status_code == 422, changed.text
    revisions[0].public_use_allowed = False
    db_session.commit()
    live = client.get(f"{path}/{good.json()['id']}/readiness", headers=headers).json()["render"]
    assert live["status"] == "incomplete"


def test_graphic_v1_to_v2_upgrade_is_explicit_append_only_and_cas_guarded(client, db_session):
    headers = {"X-Studio-User": "graphic-upgrade@studio.local"}
    db_session.add(ChannelTemplateVersion(channel="graphic_upgrade_fixture", version=1, name="图像升级测试", status="published", profile_json={"content_forms": {"final": {"artifact_kind": "image"}}}))
    db_session.commit()
    persona = client.post("/api/v1/content-personas", json={"name": "设计师"}, headers=headers).json()["id"]
    project = client.post("/api/v1/content-projects", json={"title": "升级项目"}, headers=headers).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project}/units", json={"title": "旧卡", "persona_id": persona, "modality": "graphic", "channel_id": "graphic_upgrade_fixture"}, headers=headers).json()["id"]
    path = f"/api/v1/content-projects/{project}/units/{unit}/master-revisions"
    legacy = {"title": "旧稿", "canvases": [canvas("old", 0, [text_layer("copy", 0, "旧正文")])]}
    saved = client.post(path, json={"idempotency_key": "legacy", "payload_schema": "graphic.master.v1", "payload": legacy}, headers=headers)
    assert saved.status_code == 200, saved.text
    source = saved.json()
    direct = client.post(path, json={"idempotency_key": "not-upgrade", "expected_revision": 1, "payload_schema": "graphic.master.v2", "payload": legacy}, headers=headers)
    assert direct.status_code == 409, direct.text
    preview = client.get(f"{path}/{source['id']}/graphic-v2-upgrade-preview", headers=headers)
    assert preview.status_code == 200, preview.text
    assert preview.json()["payload"] == graphics().canonical_payload(legacy)
    intent = {"idempotency_key": "explicit-fork", "expected_revision": 1, "expected_payload_hash": source["payload_hash"], "expected_context_hash": preview.json()["current_context_hash"]}
    stale = client.post(f"{path}/{source['id']}/graphic-v2-upgrade", json={**intent, "expected_payload_hash": "0" * 64}, headers=headers)
    assert stale.status_code == 409, stale.text
    upgraded = client.post(f"{path}/{source['id']}/graphic-v2-upgrade", json=intent, headers=headers)
    assert upgraded.status_code == 200, upgraded.text
    child = upgraded.json()
    assert child["payload_schema"] == "graphic.master.v2"
    assert child["parent_revision_id"] == source["id"]
    assert child["payload"] == preview.json()["payload"]
    assert client.post(f"{path}/{source['id']}/graphic-v2-upgrade", json=intent, headers=headers).json()["id"] == child["id"]
    assert client.get(f"{path}/{source['id']}", headers=headers).json()["payload_schema"] == "graphic.master.v1"
    compared = client.get(f"{path}/{child['id']}/diff", params={"compare_to_id": source["id"]}, headers=headers)
    assert compared.status_code == 200, compared.text
    assert compared.json()["from_schema"] == "graphic.master.v1"
    assert compared.json()["to_schema"] == "graphic.master.v2"
    assert "similarity" not in str(compared.json())
    assert db_session.query(ContentMasterRevision).filter_by(content_unit_id=unit).count() == 2


def test_graphic_v2_claim_evidence_must_match_frozen_project_boundary(client, db_session):
    headers = {"X-Studio-User": "graphic-evidence@studio.local"}
    db_session.add(ChannelTemplateVersion(channel="graphic_evidence_fixture", version=1, name="图像证据测试", status="published", profile_json={"content_forms": {"final": {"artifact_kind": "image"}}}))
    db_session.commit()
    persona = client.post("/api/v1/content-personas", json={"name": "设计师"}, headers=headers).json()["id"]
    project = client.post("/api/v1/content-projects", json={"title": "证据项目"}, headers=headers).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project}/units", json={"title": "论证卡片", "persona_id": persona, "modality": "graphic", "channel_id": "graphic_evidence_fixture"}, headers=headers).json()["id"]
    pack = FactPack(name="事实包", version=1, status="frozen", checksum="p" * 64)
    db_session.add(pack)
    db_session.flush()
    item = FactPackItem(fact_pack_id=pack.id, evidence_kind="author_opinion", snapshot_json={"statement": "可核对"}, snapshot_checksum="s" * 64, public_use_allowed=True)
    db_session.add(item)
    db_session.commit()
    boundary = client.post(f"/api/v1/content-projects/{project}/fact-boundary", json={"fact_pack_id": pack.id, "expected_revision": 0}, headers=headers)
    assert boundary.status_code == 201, boundary.text
    layer = text_layer("claim", 0, "证据在这里")
    layer["claims"] = [{"fact_pack_item_id": item.id, "snapshot_checksum": item.snapshot_checksum, "start": 0, "end": 2}]
    payload = {"canvases": [canvas("cover", 0, [layer])]}
    evidence = {"fact_pack_item_id": item.id, "snapshot_checksum": item.snapshot_checksum, "role": "claim", "locator": {"canvas_id": "cover", "layer_id": "claim", "start": 0, "end": 2}}
    path = f"/api/v1/content-projects/{project}/units/{unit}/master-revisions"
    wrong = client.post(path, json={"idempotency_key": "wrong-evidence", "payload_schema": "graphic.master.v2", "payload": payload, "evidence_refs": [{**evidence, "snapshot_checksum": "x" * 64}]}, headers=headers)
    assert wrong.status_code == 422, wrong.text
    accepted = client.post(path, json={"idempotency_key": "valid-evidence", "payload_schema": "graphic.master.v2", "payload": payload, "evidence_refs": [evidence]}, headers=headers)
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["evidence"][0]["locator"] == evidence["locator"]
    item.snapshot_json = ["legacy-format"]
    item.model_use_allowed = True
    db_session.commit()
    checked = client.post(f"{path}/{accepted.json()['id']}/checks", headers=headers)
    assert checked.status_code == 200, checked.text
    fact = next(row for row in checked.json()["items"] if row["check_kind"] == "graphic_fact")
    assert fact["status"] != "pass"
