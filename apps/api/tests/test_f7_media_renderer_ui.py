import pytest

from app.models import User
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
        "can_probe": can_probe, "reason": "admin_preview_requires_explicit_runtime"}]
    assert "GRAPHIC_RENDER" not in response.text


def test_viewer_cannot_probe_media_renderer(client, inventory_setup):
    response = client.post("/api/v1/content-projects/1/units/1/master-revisions/1/media-render-previews",
        headers={"X-Studio-User": "media-ui-viewer@studio.local"}, json={"renderer_key": "graphic.chromium",
        "renderer_version": "1", "canvas_id": "one", "expected_payload_hash": "a" * 64, "expected_context_hash": "b" * 64})
    assert response.status_code == 403
