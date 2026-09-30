import hashlib
import io
import os

import pytest
from PIL import Image
from test_f7_media_renderers import setup  # noqa: F401 Imported pytest fixture.


def request(layers=None):
    return {"payload": {"title": "Render", "canvases": [{"id": "one", "order": 0,
        "width": 64, "height": 64, "background": {"color": "#ffffff"}, "layers": layers or []}]},
        "canvas_id": "one", "render_input_hash": "a" * 64, "source_assets": []}


def shape():
    return {"id": "shape", "order": 0, "type": "shape", "x": 8, "y": 8,
        "width": 32, "height": 32, "shape": "rectangle", "fill": "#ff0000"}


def test_no_implicit_developer_runtime(monkeypatch):
    from app.services.local_graphic_renderer import LocalGraphicRenderer

    for key in ("GRAPHIC_RENDER_NODE", "GRAPHIC_RENDER_BROWSER", "GRAPHIC_RENDER_PLAYWRIGHT", "GRAPHIC_RENDER_FONT"):
        monkeypatch.delenv(key, raising=False)
    renderer = LocalGraphicRenderer()
    assert renderer.runtime_fingerprint() is None
    assert renderer.render_master(request()).status == "unavailable"


@pytest.fixture
def renderer():
    from app.services.local_graphic_renderer import LocalGraphicRenderer

    if not all(os.environ.get(key) for key in ("GRAPHIC_RENDER_NODE", "GRAPHIC_RENDER_BROWSER", "GRAPHIC_RENDER_PLAYWRIGHT", "GRAPHIC_RENDER_FONT")):
        pytest.skip("real local browser/font runtime not explicitly configured")
    return LocalGraphicRenderer()


def test_actual_png_pixels_and_determinism(renderer):
    first = renderer.render_master(request([shape()]))
    second = renderer.render_master(request([shape()]))
    assert first.status == second.status == "succeeded"
    assert first.content == second.content
    assert first.render_input_hash == "a" * 64 and first.canvas_id == "one"
    image = Image.open(io.BytesIO(first.content)).convert("RGB")
    assert image.size == (64, 64)
    assert image.getpixel((16, 16)) == (255, 0, 0)
    assert image.getpixel((60, 60)) == (255, 255, 255)


def test_image_crop_uses_exact_bytes(renderer):
    source = Image.new("RGB", (20, 10), "red")
    source.paste("blue", (10, 0, 20, 10))
    stream = io.BytesIO()
    source.save(stream, format="PNG")
    content = stream.getvalue()
    body = request([{**shape(), "type": "image", "material_revision_id": 7,
        "fit": "fill", "crop": {"x": .5, "y": 0, "width": .5, "height": 1}}])
    del body["payload"]["canvases"][0]["layers"][0]["shape"]
    del body["payload"]["canvases"][0]["layers"][0]["fill"]
    body["source_assets"] = [{"revision_id": 7, "content": content,
        "content_hash": hashlib.sha256(content).hexdigest(), "mime_type": "image/png"}]
    result = renderer.render_master(body)
    assert result.status == "succeeded"
    assert Image.open(io.BytesIO(result.content)).convert("RGB").getpixel((16, 16)) == (0, 0, 255)
    body["source_assets"] = []
    assert renderer.render_master(body).status == "failed"


def test_user_html_is_literal_text(renderer):
    body = request([{**shape(), "type": "text", "runs": [{"text": "<script>x</script>",
        "style": {"font_size": 10, "color": "#000000"}}]}])
    layer = body["payload"]["canvases"][0]["layers"][0]
    del layer["shape"]
    del layer["fill"]
    result = renderer.render_master(body)
    assert result.status == "succeeded"
    pixels = Image.open(io.BytesIO(result.content)).convert("RGB")
    assert any(sum(pixels.getpixel((x, y))) < 400 for x in range(pixels.width) for y in range(pixels.height))


def test_unsupported_font_is_not_silently_substituted(renderer):
    body = request([{**shape(), "type": "text", "runs": [{"text": "\U0010ffff",
        "style": {"font_size": 10, "color": "#000000"}}]}])
    layer = body["payload"]["canvases"][0]["layers"][0]
    del layer["shape"]
    del layer["fill"]
    assert renderer.render_master(body).status == "failed"


def test_invalid_canonical_document_fails(renderer):
    body = request([shape()])
    body["payload"]["canvases"][0]["layers"][0]["fill"] = "url(https://remote/)"
    assert renderer.render_master(body).status == "failed"


@pytest.mark.parametrize("style", [{"weight": 700}, {"italic": True}])
def test_missing_font_variant_is_not_synthesized(renderer, style):
    body = request([{**shape(), "type": "text", "runs": [{"text": "Actual text",
        "style": {"font_size": 10, "color": "#000000", **style}}]}])
    layer = body["payload"]["canvases"][0]["layers"][0]
    del layer["shape"]
    del layer["fill"]
    assert renderer.render_master(body).status == "failed"


def test_layer_order_visibility_and_alpha(renderer):
    bottom = shape()
    top = {**shape(), "id": "top", "order": 1, "fill": "#0000ff", "opacity": .5}
    hidden = {**shape(), "id": "hidden", "order": 2, "fill": "#00ff00", "visible": False}
    result = renderer.render_master(request([hidden, top, bottom]))
    assert result.status == "succeeded"
    pixel = Image.open(io.BytesIO(result.content)).convert("RGB").getpixel((16, 16))
    assert pixel[1] == 0 and all(127 <= component <= 128 for component in (pixel[0], pixel[2]))


@pytest.mark.parametrize("patch,point,color", [
    ({"rotation": 90, "height": 16}, (24, 24), (255, 0, 0)),
    ({"rotation": 90, "height": 16}, (10, 10), (255, 255, 255)),
    ({"shape": "ellipse"}, (24, 24), (255, 0, 0)),
    ({"shape": "ellipse"}, (8, 8), (255, 255, 255)),
    ({"shape": "line", "stroke": "#0000ff", "stroke_width": 4}, (16, 25), (0, 0, 255)),
])
def test_actual_rotated_shape_ellipse_and_stroke(renderer, patch, point, color):
    result = renderer.render_master(request([{**shape(), **patch}]))
    assert result.status == "succeeded"
    assert Image.open(io.BytesIO(result.content)).convert("RGB").getpixel(point) == color


def test_mixed_text_alignment_is_explicitly_unsupported(renderer):
    layer = {**shape(), "type": "text", "runs": [{"text": "one", "style": {"font_size": 10,
        "color": "#000000", "align": "left"}}, {"text": "two", "style": {"font_size": 10,
        "color": "#000000", "align": "right"}}]}
    del layer["shape"]
    del layer["fill"]
    assert renderer.render_master(request([layer])).status == "failed"


def test_runtime_font_bytes_drift_invalidates_fingerprint(renderer, monkeypatch, tmp_path):
    original = renderer.runtime_fingerprint()
    font = tmp_path / "font.ttf"
    font.write_bytes(b"different font bytes")
    monkeypatch.setenv("GRAPHIC_RENDER_FONT", str(font))
    assert renderer.runtime_fingerprint() != original
    assert renderer.render_master(request()).status == "failed"


def test_real_renderer_api_stage_accept_and_explicit_manual_bind(client, db_session, setup, renderer):  # noqa: F811 Pytest fixture injection.
    from test_f7_media_renderers import decision

    from app.models import ContentMasterRevision, MaterialRevision
    from app.services.content_harness import providers

    providers.registry.register("renderer", renderer.key, renderer.version, renderer)
    master = setup["master"]
    response = client.post(f"{setup['path']}/{master['id']}/media-render-previews", json={**setup["body"],
        "renderer_key": renderer.key, "renderer_version": renderer.version})
    assert response.status_code == 200, response.text
    assert response.json()["verified"] is False
    accepted = client.post(f"/api/v1/provider-media/{response.json()['stage_id']}/accept", json=decision())
    assert accepted.status_code == 201, accepted.text
    revision = db_session.get(MaterialRevision, accepted.json()["material_revision_id"])
    assert revision.source_metadata_json["renderer_origin"]["render_input_hash"] == response.json()["input_hash"]
    assert db_session.query(ContentMasterRevision).count() == 1
    payload = {**master["payload"], "render_asset_ref": [{"canvas_id": "one", "material_revision_id": revision.id}]}
    saved = client.post(setup["path"], json={"payload_schema": "graphic.master.v2", "payload": payload,
        "expected_revision": 1, "idempotency_key": "explicit-real-render-bind",
        "asset_refs": [{"material_revision_id": revision.id, "content_hash": revision.content_hash,
            "role": "render_output", "slot_key": "one", "placement": {"canvas_id": "one"}}],
        "render_attestation": {"confirmed": True, "render_input_hash": response.json()["input_hash"]}})
    assert saved.status_code == 200, saved.text
    assert db_session.query(ContentMasterRevision).count() == 2
    assert saved.json()["edit_summary"]["render_attestation"]["origin"] == "manual"
