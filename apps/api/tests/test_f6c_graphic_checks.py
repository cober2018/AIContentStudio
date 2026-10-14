"""Exact Graphic profile and professional check invariants."""

import importlib
import importlib.util
from types import SimpleNamespace

import pytest

from app.services.content_harness.channel_registry import ContentFormSpec, resolve_content_form
from app.services.graphic_documents import canonical_payload


def profile_reasons(*args):
    assert importlib.util.find_spec("app.services.graphic_master_checks"), "Graphic profile validator missing"
    return importlib.import_module("app.services.graphic_master_checks").profile_reasons(*args)


def _canvas(canvas_id: str, order: int, *, width: int = 1080, height: int = 1440, role: str | None = None) -> dict:
    row = {"id": canvas_id, "order": order, "width": width, "height": height, "background": {"color": "#ffffff"}, "layers": []}
    if role is not None:
        row["role"] = role
    return row


def _pure_cards() -> dict:
    canvases = [_canvas("cover", 0, role="cover"), _canvas("body-1", 1, role="body"), _canvas("body-2", 2, role="body")]
    for canvas in canvases:
        canvas["layers"] = [
            {"id": "accent", "order": 0, "type": "shape", "x": 24, "y": 24, "width": 300,
             "height": 8, "shape": "rectangle", "fill": "#123456"},
            {"id": "copy", "order": 1, "type": "text", "x": 24, "y": 80, "width": 600,
             "height": 80, "runs": [{"text": "明确选择的纯图卡", "style": {"font_size": 30, "color": "#123456"}}]},
        ]
    return canonical_payload({"canvases": canvases})


def test_image_note_inline_requires_a_body_card_without_requiring_an_input_photo():
    form = ContentFormSpec(channel="xiaohongshu", content_form="image_note", artifact_kind="image", source="profile",
                           profile_version_id=29, media_requirements={"cover": "required", "inline": "required"})
    document = _pure_cards()
    assert profile_reasons(form, document) == []
    assert profile_reasons(form, canonical_payload({"canvases": document["canvases"][:1]})) == ["graphic_inline_media_required"]
    document["canvases"][1]["role"] = "cover"
    document["canvases"][2]["role"] = "cover"
    assert profile_reasons(form, document) == ["graphic_inline_media_required"]
    document["canvases"][0]["role"] = "body"
    assert profile_reasons(form, document) == ["graphic_cover_required"]


@pytest.mark.parametrize("kind", ["image", "chart"])
def test_other_graphic_forms_still_require_a_visible_input_image_or_chart(kind):
    form = ContentFormSpec(channel="fixture", content_form="image", artifact_kind="image", source="profile",
                           profile_version_id=42, media_requirements={"inline": "required"})
    document = _pure_cards()
    assert profile_reasons(form, document) == ["graphic_inline_media_required"]
    layer = {"id": "media", "order": 2, "type": kind, "visible": False, "x": 24, "y": 200,
             "width": 600, "height": 400, "material_revision_id": 7}
    document["canvases"][1]["layers"].append(layer)
    document = canonical_payload(document)
    assert profile_reasons(form, document) == ["graphic_inline_media_required"]
    document["canvases"][1]["layers"][-1]["visible"] = True
    assert profile_reasons(form, document) == []


def test_image_note_card_image_role_accepts_output_canvases():
    form = ContentFormSpec(channel="bilibili", content_form="image_note", artifact_kind="image", source="profile",
                           profile_version_id=20, media_requirements={"required_roles": ["card_image"]})
    document = _pure_cards()
    assert profile_reasons(form, document) == []
    assert profile_reasons(form, canonical_payload({"canvases": document["canvases"][:1]})) == []


@pytest.mark.parametrize("roles, reason", [
    (["unknown_role"], "graphic_profile_rule_unavailable"),
    (["card_image", "unknown_role"], "graphic_profile_rule_unavailable"),
    (["card_image", "card_image"], "graphic_profile_rules_invalid"),
    ([7], "graphic_profile_rules_invalid"),
    ([["card_image"]], "graphic_profile_rules_invalid"),
    ("card_image", "graphic_profile_rules_invalid"),
    ({"card_image": "required"}, "graphic_profile_rules_invalid"),
    (None, "graphic_profile_rules_invalid"),
])
def test_image_note_card_image_role_declarations_fail_closed(roles, reason):
    form = ContentFormSpec(channel="bilibili", content_form="image_note", artifact_kind="image", source="profile",
                           profile_version_id=20, media_requirements={"required_roles": roles})
    assert profile_reasons(form, _pure_cards()) == [reason]


def test_other_graphic_forms_do_not_gain_card_image_role_support():
    form = ContentFormSpec(channel="fixture", content_form="image", artifact_kind="image", source="profile",
                           profile_version_id=42, media_requirements={"required_roles": ["card_image"]})
    assert profile_reasons(form, _pure_cards()) == ["graphic_profile_rule_unavailable"]


def test_exact_graphic_profile_enforces_only_declared_canvas_rules(db_session):
    from app.models import ChannelTemplateVersion

    db_session.add(ChannelTemplateVersion(channel="graphic_profile_fixture", version=1, name="图像形态", status="published", profile_json={"content_forms": {"cards": {"artifact_kind": "image", "graphic_requirements": {"min_canvases": 2, "max_canvases": 4, "allowed_dimensions": [[1080, 1440]], "cover_required": True, "presets": [{"key": "portrait", "label": "竖图", "width": 1080, "height": 1440}]}}}}))
    db_session.commit()
    form = resolve_content_form(db_session, "graphic_profile_fixture", "cards")
    assert form.graphic_requirements["max_canvases"] == 4
    document = canonical_payload({"canvases": [_canvas("cover", 0, role="cover"), _canvas("card-2", 1, role="body")]})
    assert profile_reasons(form, document) == []
    assert document["canvases"][0]["role"] == "cover"
    assert profile_reasons(form, canonical_payload({"canvases": [_canvas("only", 0, role="body")]})) == ["graphic_canvas_count_below_profile_minimum", "graphic_cover_required"]
    assert profile_reasons(form, canonical_payload({"canvases": [_canvas("cover", 0, role="cover"), _canvas("wide", 1, width=1920, height=1080)]})) == ["graphic_dimensions_not_allowed"]


def test_manual_dimensions_remain_valid_without_exact_profile_restriction():
    form = ContentFormSpec(channel="fixture", content_form="image", artifact_kind="image", source="profile", profile_version_id=42)
    document = canonical_payload({"canvases": [_canvas("square", 0, width=1200, height=1200)]})
    assert profile_reasons(form, document) == []
    assert document["canvases"][0]["width"] == 1200
    legacy = ContentFormSpec(channel="xiaohongshu", content_form="image_note", artifact_kind="text", source="legacy_default")
    assert profile_reasons(legacy, document) == ["graphic_profile_unavailable"]


def test_unknown_profile_media_rule_cannot_pass_and_declared_inline_is_required():
    document = canonical_payload({"canvases": [_canvas("cover", 0, role="cover")]})
    form = ContentFormSpec(channel="fixture", content_form="image", artifact_kind="image", source="profile", profile_version_id=42, media_requirements={"unknown_role": "required"})
    assert profile_reasons(form, document) == ["graphic_profile_rule_unavailable"]
    form.media_requirements = {"inline": "required"}
    assert profile_reasons(form, document) == ["graphic_inline_media_required"]


def test_graphic_v2_readiness_uses_exact_published_profile_rules(client, db_session):
    from app.models import ChannelTemplateVersion

    headers = {"X-Studio-User": "graphic-profile@studio.local"}
    db_session.add(ChannelTemplateVersion(channel="graphic_cards_fixture", version=1, name="图像卡片", status="published", profile_json={"content_forms": {"cards": {"artifact_kind": "image", "graphic_requirements": {"min_canvases": 2, "cover_required": True}}}}))
    db_session.commit()
    persona = client.post("/api/v1/content-personas", json={"name": "设计师"}, headers=headers).json()["id"]
    project = client.post("/api/v1/content-projects", json={"title": "渠道卡片项目"}, headers=headers).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project}/units", json={"title": "卡片", "persona_id": persona, "modality": "graphic", "channel_id": "graphic_cards_fixture"}, headers=headers).json()["id"]
    path = f"/api/v1/content-projects/{project}/units/{unit}/master-revisions"
    saved = client.post(path, json={"idempotency_key": "one-card", "payload_schema": "graphic.master.v2", "payload": {"canvases": [_canvas("one", 0, role="body")]}, "content_form": "cards"}, headers=headers)
    assert saved.status_code == 200, saved.text
    readiness = client.get(f"{path}/{saved.json()['id']}/readiness", headers=headers)
    assert readiness.status_code == 200, readiness.text
    assert {"graphic_canvas_count_below_profile_minimum", "graphic_cover_required"}.issubset(readiness.json()["adapter_availability"]["reasons"])
    checked = client.post(f"{path}/{saved.json()['id']}/checks", headers=headers)
    assert checked.status_code == 200, checked.text
    checks = {item["check_kind"]: item for item in checked.json()["items"]}
    assert {"graphic_structure", "graphic_fact", "graphic_identity", "graphic_platform"}.issubset(checks)
    assert checks["graphic_structure"]["status"] == "incomplete"
    assert checks["graphic_platform"]["status"] == "blocker"
    assert {"graphic_canvas_count_below_profile_minimum", "graphic_cover_required"}.issubset(checks["graphic_platform"]["report"]["reasons"])
    assert checks["graphic_fact"]["status"] != "pass"
    assert checks["graphic_identity"]["status"] != "pass"


def test_graphic_platform_check_becomes_stale_when_published_profile_changes(client, db_session):
    from app.models import ChannelTemplateVersion

    headers = {"X-Studio-User": "graphic-freshness@studio.local"}
    db_session.add(ChannelTemplateVersion(channel="graphic_freshness_fixture", version=1, name="卡片规则", status="published", profile_json={"content_forms": {"cards": {"artifact_kind": "image"}}}))
    db_session.commit()
    persona = client.post("/api/v1/content-personas", json={"name": "设计师"}, headers=headers).json()["id"]
    project = client.post("/api/v1/content-projects", json={"title": "规则变化", "channels": ["graphic_freshness_fixture"]}, headers=headers).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project}/units", json={"title": "卡片", "persona_id": persona, "modality": "graphic", "channel_id": "graphic_freshness_fixture"}, headers=headers).json()["id"]
    path = f"/api/v1/content-projects/{project}/units/{unit}/master-revisions"
    saved = client.post(path, json={"idempotency_key": "first", "payload_schema": "graphic.master.v2", "payload": {"canvases": [_canvas("one", 0, role="body")]}, "content_form": "cards"}, headers=headers)
    assert saved.status_code == 200, saved.text
    master_id = saved.json()["id"]
    checked = client.post(f"{path}/{master_id}/checks", headers=headers)
    assert checked.status_code == 200, checked.text
    old = next(item for item in checked.json()["items"] if item["check_kind"] == "graphic_platform")
    assert old["status"] == "pass"
    db_session.add(ChannelTemplateVersion(channel="graphic_freshness_fixture", version=2, name="卡片规则二版", status="published", profile_json={"content_forms": {"cards": {"artifact_kind": "image", "graphic_requirements": {"cover_required": True}}}}))
    db_session.commit()
    current = client.get(f"{path}/{master_id}/checks/current", headers=headers)
    assert current.status_code == 200, current.text
    projected = next(item for item in current.json()["items"] if item["check_kind"] == "graphic_platform")
    assert projected["status"] == "stale"
    assert projected["id"] == old["id"]
    rerun = client.post(f"{path}/{master_id}/checks", headers=headers)
    assert rerun.status_code == 200, rerun.text
    newest = next(item for item in rerun.json()["items"] if item["check_kind"] == "graphic_platform")
    assert newest["status"] == "blocker"
    assert newest["id"] != old["id"]


def test_text_identity_review_does_not_verify_visual_identity(monkeypatch):
    checks = importlib.import_module("app.services.graphic_master_checks")
    monkeypatch.setattr(checks, "_semantic_review", lambda *args, **kwargs: ([], {"semantic": "verified"}))
    snapshot = SimpleNamespace(id=7, checksum="i" * 64, effective_profile_json={"expression_style": {"forbidden_phrases": []}})
    db = SimpleNamespace(get=lambda model, key: snapshot)
    layer = {"id": "title", "order": 0, "type": "text", "visible": True, "x": 0, "y": 0, "width": 200, "height": 80, "runs": [{"text": "文字可检查", "style": {"font_size": 30, "color": "#123456"}}]}
    master = SimpleNamespace(identity_snapshot_id=7, payload_json={"canvases": [{**_canvas("one", 0), "layers": [layer]}]})
    status, report = checks._identity(db, master, {"metadata": {"semantic": {"configured": True}}})
    assert status == "warning"
    assert report["coverage"]["semantic"] == "verified"
    assert report["coverage"]["visual_semantics"] == "unavailable"
