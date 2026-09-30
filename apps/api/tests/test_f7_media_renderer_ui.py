from datetime import UTC, datetime, timedelta

import pytest

from app.models import CapabilityRegistration, CapabilityVerification, User
from app.services.content_harness import providers
from app.services.content_harness.registry import PluginRegistry
from app.services.local_graphic_renderer import LocalGraphicRenderer


@pytest.fixture
def inventory_setup(db_session, monkeypatch):
    db_session.add_all([User(email="media-ui-admin@studio.local", name="Admin", role="admin"),
                       User(email="media-ui-viewer@studio.local", name="Viewer", role="viewer")])
    db_session.commit()
    monkeypatch.setattr(providers, "registry", PluginRegistry())
    def forbidden(*args, **kwargs):
        pytest.fail("read-only inventory invoked renderer runtime")
    monkeypatch.setattr(LocalGraphicRenderer, "runtime_fingerprint", forbidden)
    monkeypatch.setattr(LocalGraphicRenderer, "render_master", forbidden)
    monkeypatch.setattr(LocalGraphicRenderer, "_runtime", forbidden)


@pytest.mark.parametrize("role,can_probe", [("admin", True), ("viewer", False)])
def test_media_inventory_is_loaded_not_probed_or_verified(client, inventory_setup, role, can_probe):
    response = client.get("/api/v1/settings/capabilities", headers={"X-Studio-User": f"media-ui-{role}@studio.local"})
    assert response.status_code == 200, response.text
    items = response.json()["media_renderer_previews"]
    assert items == [{"renderer_key": "graphic.chromium", "renderer_version": "1", "modality": "graphic",
        "payload_schema": "graphic.master.v2", "output_mimes": ["image/png"],
        "supported_forms": [{"channel": "xiaohongshu", "content_form": "image_note"}],
        "configuration_status": "not_probed", "verified": False, "executable": False,
        "can_probe": can_probe, "recorded_scopes": [], "can_request_execution": False,
        "reason": "admin_preview_requires_explicit_runtime"}]
    assert "GRAPHIC_RENDER" not in response.text


def test_viewer_cannot_probe_media_renderer(client, inventory_setup):
    response = client.post("/api/v1/content-projects/1/units/1/master-revisions/1/media-render-previews",
        headers={"X-Studio-User": "media-ui-viewer@studio.local"}, json={"renderer_key": "graphic.chromium",
        "renderer_version": "1", "canvas_id": "one", "expected_payload_hash": "a" * 64, "expected_context_hash": "b" * 64})
    assert response.status_code == 403


@pytest.mark.parametrize("role,result,expired,requestable", [("admin", "verified", False, True),
    ("viewer", "verified", False, False), ("admin", "revoked", False, False), ("admin", "verified", True, False)])
def test_recorded_media_scope_inventory_does_not_probe_runtime(client, db_session, inventory_setup, role, result, expired, requestable):
    registration = CapabilityRegistration(kind="renderer", key="graphic.chromium", version="1", status="configured", config_fingerprint="a" * 64)
    db_session.add(registration)
    db_session.flush()
    scope = {"renderer_key": "graphic.chromium", "renderer_version": "1", "modality": "graphic",
        "payload_schema": "graphic.master.v2", "channel": "xiaohongshu", "content_form": "image_note", "output_mime": "image/png"}
    db_session.add(CapabilityVerification(registration_id=registration.id, config_fingerprint="b" * 64,
        scope_kind="renderer_output", scope_json=scope, result=result, verified_by="fixture",
        verified_at=datetime.now(UTC), expires_at=datetime.now(UTC) + timedelta(hours=-1 if expired else 1),
        evidence_json={"kind": "revocation"} if result == "revoked" else {"kind": "render_readback", "reference_hash": "c" * 64, "input_hash": "d" * 64, "output_hash": "e" * 64}))
    db_session.commit()
    response = client.get("/api/v1/settings/capabilities", headers={"X-Studio-User": f"media-ui-{role}@studio.local"})
    assert response.status_code == 200, response.text
    item = response.json()["media_renderer_previews"][0]
    assert item["can_request_execution"] is requestable
    assert item["verified"] is False and item["executable"] is False and item["configuration_status"] == "not_probed"
    assert item["recorded_scopes"][0]["scope"] == scope
