"""Renderer byte receipts cannot mutate or attest a Master implicitly."""

import hashlib
import io

import pytest
from PIL import Image

from app.models import ContentMasterRevision, MaterialRevision, ProjectMaterialReference, User
from app.services import asset_media, materials, provider_media
from app.services.content_harness import providers
from app.services.content_harness.registry import PluginRegistry


@pytest.fixture
def setup(client, db_session, monkeypatch, tmp_path):
    monkeypatch.setattr(asset_media, "MEDIA_ROOT", tmp_path)
    db_session.add(User(email="admin@studio.local", role="admin", name="Admin"))
    db_session.commit()
    registry = PluginRegistry()
    monkeypatch.setattr(providers, "registry", registry)
    with provider_media._lock:
        provider_media._cache.clear()
    data = io.BytesIO()
    Image.new("RGB", (32, 32), "blue").save(data, format="PNG")

    class Renderer:
        key = "graphic.contract"
        version = "1"
        modality = "graphic"
        schema = "graphic.master.v2"
        output_mimes = ("image/png",)
        supported_forms = (("xiaohongshu", "image_note"),)
        content = data.getvalue()
        fingerprint = "a" * 64
        calls = 0
        mutate = None
        change = None

        def runtime_fingerprint(self):
            return self.fingerprint

        def render_master(self, request):
            from app.services.content_harness.providers import MediaRenderOutput

            self.calls += 1
            self.source_count = len(request["source_assets"])
            if self.mutate:
                self.mutate()
            result = {"status": "succeeded", "content": self.content, "mime_type": "image/png",
                      "render_input_hash": request["render_input_hash"], "canvas_id": request["canvas_id"],
                      "metadata": {"token": "private-result", "url": "https://secret/?token=private"}}
            if self.change:
                result.update(self.change)
            return MediaRenderOutput(**result)

    renderer = Renderer()
    registry.register("renderer", renderer.key, "1", renderer)
    persona = client.post("/api/v1/content-personas", json={"name": "Renderer 作者"}).json()["id"]
    project = client.post("/api/v1/content-projects", json={"title": "Renderer 接受"}).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project}/units", json={"title": "图卡", "modality": "graphic",
        "persona_id": persona, "channel_id": "xiaohongshu", "content_form": "image_note"}).json()["id"]
    path = f"/api/v1/content-projects/{project}/units/{unit}/master-revisions"
    payload = {"title": "真实字节", "canvases": [{"id": "one", "order": 0, "width": 32, "height": 32,
        "background": {"color": "#0000ff"}, "layers": []}]}
    response = client.post(path, json={"payload_schema": "graphic.master.v2", "payload": payload, "idempotency_key": "initial"})
    assert response.status_code == 200, response.text
    master = response.json()
    return {"path": path, "master": master, "project": project, "renderer": renderer,
        "body": {"renderer_key": renderer.key, "renderer_version": "1", "canvas_id": "one",
                 "expected_payload_hash": master["payload_hash"], "expected_context_hash": master["context_hash"]}}


def stage(client, setup, **change):
    return client.post(f"{setup['path']}/{setup['master']['id']}/media-render-previews", json={**setup["body"], **change})


def decision():
    return {"confirmed": True, "title": "接受成片", "license_code": "owned", "license_evidence_hash": "b" * 64,
            "public_use_allowed": True, "model_use_allowed": False, "commercial_use_allowed": False}


def test_preview_accept_exact_renderer_bytes_without_master_or_attestation_write(client, db_session, setup):
    response = stage(client, setup)
    assert response.status_code == 200, response.text
    assert response.json()["verified"] is False and response.json()["public_ready"] is False
    assert db_session.query(MaterialRevision).count() == 0 and setup["renderer"].calls == 1
    accepted = client.post(f"/api/v1/provider-media/{response.json()['stage_id']}/accept", json=decision())
    assert accepted.status_code == 201, accepted.text
    revision = db_session.get(MaterialRevision, accepted.json()["material_revision_id"])
    assert revision.source_kind == "upstream"
    assert revision.source_metadata_json["renderer_origin"]["master_id"] == setup["master"]["id"]
    assert revision.source_metadata_json["renderer_origin"]["canvas_id"] == "one"
    assert revision.source_metadata_json["renderer_origin"]["render_input_hash"] == response.json()["input_hash"]
    assert revision.content_hash == hashlib.sha256(provider_media.preview_bytes(response.json()["stage_id"],
        db_session.query(User).filter_by(email="admin@studio.local").one())[0]).hexdigest()
    assert "private-result" not in str(revision.source_metadata_json) and "token=" not in str(revision.source_metadata_json)
    assert db_session.query(ProjectMaterialReference).count() == 1
    master = db_session.get(ContentMasterRevision, setup["master"]["id"])
    assert db_session.query(ContentMasterRevision).count() == 1 and "render_attestation" not in master.edit_summary_json
    repeat = client.post(f"/api/v1/provider-media/{response.json()['stage_id']}/accept", json=decision())
    assert repeat.json() == accepted.json() and db_session.query(MaterialRevision).count() == 1


@pytest.mark.parametrize("change", [{"render_input_hash": "0" * 64}, {"canvas_id": "foreign"},
    {"mime_type": "video/mp4"}, {"content": b""}, {"status": "unknown"}])
def test_wrong_render_output_has_no_write_or_success_preview(client, db_session, setup, change):
    setup["renderer"].change = change
    response = stage(client, setup)
    assert response.status_code in {409, 422}, response.text
    assert "stage_id" not in response.json() and db_session.query(MaterialRevision).count() == 0


@pytest.mark.parametrize("change", [{"expected_payload_hash": "0" * 64}, {"expected_context_hash": "0" * 64},
    {"renderer_version": "99"}, {"canvas_id": "foreign"}, {"output_hash": "0" * 64}])
def test_invalid_renderer_request_does_not_call_executor(client, setup, change):
    assert stage(client, setup, **change).status_code in {409, 422}
    assert setup["renderer"].calls == 0


@pytest.mark.parametrize("drift", ["master", "runtime", "context"])
def test_stale_renderer_preview_cannot_be_accepted(client, db_session, setup, drift):
    response = stage(client, setup)
    assert response.status_code == 200, response.text
    if drift == "runtime":
        setup["renderer"].fingerprint = "c" * 64
    elif drift == "master":
        master = setup["master"]
        result = client.post(setup["path"], json={"expected_revision": 1, "payload_schema": "graphic.master.v2",
            "payload": {**master["payload"], "title": "新稿"}, "idempotency_key": "next"})
        assert result.status_code == 200, result.text
    else:
        result = client.post(f"/api/v1/content-projects/{setup['project']}/brief/revisions",
            json={"expected_revision": 0, "objective": "新上下文"})
        assert result.status_code in {200, 201}, result.text
    accepted = client.post(f"/api/v1/provider-media/{response.json()['stage_id']}/accept", json=decision())
    assert accepted.status_code == 409, accepted.text
    assert db_session.query(MaterialRevision).count() == 0 and db_session.query(ProjectMaterialReference).count() == 0


def test_foreign_and_viewer_cannot_stage_renderer(client, db_session, setup):
    for role, expected in [("admin", 404), ("editor", 403), ("viewer", 403)]:
        email = f"renderer-{role}@studio.local"
        db_session.add(User(email=email, role=role, name=role))
        db_session.commit()
        response = client.post(f"{setup['path']}/{setup['master']['id']}/media-render-previews", headers={"X-Studio-User": email}, json=setup["body"])
        assert response.status_code == expected, response.text
    assert setup["renderer"].calls == 0


def add_source(client, db, setup):
    material = materials.create_material(db, kind="image", title="共享来源", created_by="admin@studio.local")
    revision = materials.create_revision(db, material, content=setup["renderer"].content, suffix=".png", declared_mime="image/png",
        source_kind="upload", public_use_allowed=True, model_use_allowed=False, commercial_use_allowed=False, created_by="admin@studio.local")
    revision.status = "usable"
    db.add(ProjectMaterialReference(project_id=setup["project"], material_revision_id=revision.id, origin="system_reference",
                                    status="active", attached_by="admin@studio.local"))
    db.commit()
    layer = {"id": "source", "order": 0, "type": "image", "x": 0, "y": 0, "width": 32, "height": 32,
             "material_revision_id": revision.id, "fit": "contain"}
    payload = {**setup["master"]["payload"], "canvases": [{**setup["master"]["payload"]["canvases"][0], "layers": [layer]}]}
    response = client.post(setup["path"], json={"payload_schema": "graphic.master.v2", "expected_revision": 1,
        "payload": payload, "asset_refs": [{"material_revision_id": revision.id, "content_hash": revision.content_hash,
            "role": "graphic_layer", "slot_key": "source", "placement": {"canvas_id": "one", "layer_id": "source"}}], "idempotency_key": "with-source"})
    assert response.status_code == 200, response.text
    setup["master"] = response.json()
    setup["body"].update(expected_payload_hash=response.json()["payload_hash"], expected_context_hash=response.json()["context_hash"])
    return revision


@pytest.mark.parametrize("when", ["before_call", "before_accept"])
def test_source_public_revocation_blocks_renderer_without_new_media(client, db_session, setup, when):
    source = add_source(client, db_session, setup)
    if when == "before_accept":
        response = stage(client, setup)
        assert response.status_code == 200, response.text
    source.public_use_allowed = False
    db_session.commit()
    if when == "before_call":
        assert stage(client, setup).status_code == 409
        assert setup["renderer"].calls == 0
    else:
        assert client.post(f"/api/v1/provider-media/{response.json()['stage_id']}/accept", json=decision()).status_code == 409
    assert db_session.query(MaterialRevision).count() == 1 and db_session.query(ContentMasterRevision).count() == 2


@pytest.mark.parametrize("field", ["model_use_allowed", "commercial_use_allowed"])
def test_renderer_accept_cannot_escalate_source_rights(client, db_session, setup, field):
    add_source(client, db_session, setup)
    response = stage(client, setup)
    assert response.status_code == 200, response.text
    accepted = client.post(f"/api/v1/provider-media/{response.json()['stage_id']}/accept", json={**decision(), field: True})
    assert accepted.status_code == 422, accepted.text
    assert db_session.query(MaterialRevision).count() == 1


def test_renderer_accept_rechecks_rights_before_commit(client, db_session, setup, monkeypatch):
    source = add_source(client, db_session, setup)
    response = stage(client, setup)
    assert response.status_code == 200, response.text
    original = materials.create_revision

    def revoke_after_create(*args, **kwargs):
        row = original(*args, **kwargs)
        source.public_use_allowed = False
        db_session.flush()
        return row

    monkeypatch.setattr(materials, "create_revision", revoke_after_create)
    accepted = client.post(f"/api/v1/provider-media/{response.json()['stage_id']}/accept", json=decision())
    assert accepted.status_code == 409, accepted.text
    assert db_session.query(MaterialRevision).count() == 1 and db_session.query(ProjectMaterialReference).count() == 1


@pytest.mark.parametrize("change", ["expired", "foreign", "restart"])
def test_renderer_preview_lifecycle_blocks_acceptance(client, db_session, setup, change):
    response = stage(client, setup)
    assert response.status_code == 200, response.text
    stage_id = response.json()["stage_id"]
    headers = {}
    if change == "expired":
        provider_media._cache[stage_id].expires = 0
    elif change == "restart":
        provider_media._cache.clear()
    else:
        headers = {"X-Studio-User": "foreign@studio.local"}
    result = client.post(f"/api/v1/provider-media/{stage_id}/accept", json=decision(), headers=headers)
    assert result.status_code == 404 and db_session.query(MaterialRevision).count() == 0


def test_renderer_wrong_canvas_dimensions_cannot_be_staged(client, db_session, setup):
    data = io.BytesIO()
    Image.new("RGB", (2, 2), "red").save(data, format="PNG")
    setup["renderer"].change = {"content": data.getvalue()}
    response = stage(client, setup)
    assert response.status_code == 422, response.text
    assert response.json()["detail"] == "media_renderer_canvas_dimensions_invalid"
    assert db_session.query(MaterialRevision).count() == 0


def test_renderer_profile_change_cannot_accept_old_output(client, db_session, setup, monkeypatch):
    from app.services.content_harness import channel_registry

    response = stage(client, setup)
    assert response.status_code == 200, response.text
    resolver = channel_registry.resolve_content_form

    def changed_profile(*args, **kwargs):
        profile = resolver(*args, **kwargs)
        original = profile.to_dict
        # A real profile revision would produce a different safe projection.
        class Changed:
            def to_dict(self):
                return {**original(), "profile_version_id": -1}
        return Changed()

    monkeypatch.setattr(channel_registry, "resolve_content_form", changed_profile)
    result = client.post(f"/api/v1/provider-media/{response.json()['stage_id']}/accept", json=decision())
    assert result.status_code == 409 and db_session.query(MaterialRevision).count() == 0


def test_renderer_source_revoked_during_render_has_no_receipt(client, db_session, setup):
    source = add_source(client, db_session, setup)

    def revoke():
        source.public_use_allowed = False
        db_session.flush()

    setup["renderer"].mutate = revoke
    response = stage(client, setup)
    assert response.status_code == 409 and "stage_id" not in response.json()
    assert db_session.query(MaterialRevision).count() == 1


def test_renderer_sensitive_exception_is_redacted_without_retry(client, db_session, setup):
    def error():
        raise ValueError("token=private-result https://unsafe/?token=private")

    setup["renderer"].mutate = error
    response = stage(client, setup)
    assert response.status_code == 502 and "private-result" not in response.text
    assert setup["renderer"].calls == 1 and db_session.query(MaterialRevision).count() == 0


def test_media_renderer_must_declare_exact_channel_form(client, setup):
    setup["renderer"].supported_forms = (("wechat", "article"),)
    assert stage(client, setup).status_code == 422
    assert setup["renderer"].calls == 0


def test_renderer_cannot_remove_source_cc_by_license_and_attribution(client, db_session, setup):
    source = add_source(client, db_session, setup)
    source.source_metadata_json = {"license_code": "CC-BY-4.0"}
    source.attribution_text = "Original Author"
    db_session.commit()
    response = stage(client, setup)
    assert response.status_code == 200, response.text
    accepted = client.post(f"/api/v1/provider-media/{response.json()['stage_id']}/accept", json=decision())
    assert accepted.status_code == 422, accepted.text
    valid = client.post(f"/api/v1/provider-media/{response.json()['stage_id']}/accept",
        json={**decision(), "license_code": "CC-BY-4.0", "attribution_text": "Original Author"})
    assert valid.status_code == 201, valid.text
    assert db_session.query(MaterialRevision).count() == 2


def test_actual_mp4_bytes_accept_without_implicit_video_attestation(client, db_session, setup, tmp_path):
    import subprocess

    from test_f6d_video_documents import _document

    renderer = setup["renderer"]
    renderer.modality, renderer.schema = "video", "video.master.v2"
    renderer.output_mimes = ("video/mp4",)
    renderer.supported_forms = (("douyin", "spoken_script"),)
    persona = client.post("/api/v1/content-personas", json={"name": "视频作者"}).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{setup['project']}/units", json={"title": "视频", "modality": "video",
        "persona_id": persona, "channel_id": "douyin", "content_form": "spoken_script"}).json()["id"]
    setup["path"] = f"/api/v1/content-projects/{setup['project']}/units/{unit}/master-revisions"
    response = client.post(setup["path"], json={"payload_schema": "video.master.v2", "payload": _document(), "idempotency_key": "video"})
    assert response.status_code == 200, response.text
    setup["master"] = response.json()
    setup["body"].update(canvas_id=None, expected_payload_hash=response.json()["payload_hash"], expected_context_hash=response.json()["context_hash"])
    video = tmp_path / "render.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=blue:s=16x16:d=0.1", "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", str(video)], timeout=10, check=True, capture_output=True)
    renderer.change = {"content": video.read_bytes(), "mime_type": "video/mp4"}
    staged = stage(client, setup)
    assert staged.status_code == 200, staged.text
    assert staged.json()["content_hash"] == hashlib.sha256(video.read_bytes()).hexdigest()
    accepted = client.post(f"/api/v1/provider-media/{staged.json()['stage_id']}/accept", json=decision())
    assert accepted.status_code == 201, accepted.text
    revision = db_session.get(MaterialRevision, accepted.json()["material_revision_id"])
    assert revision.material.kind == "video" and revision.mime_type == "video/mp4"
    assert "render_attestation" not in db_session.get(ContentMasterRevision, setup["master"]["id"]).edit_summary_json


def test_oversized_renderer_source_is_rejected_before_any_byte_read(client, db_session, setup, monkeypatch):
    source = add_source(client, db_session, setup)
    path = asset_media.MEDIA_ROOT / source.file_path
    with path.open("wb") as stream:
        stream.truncate(31 * 1024 * 1024)

    def forbidden(*args, **kwargs):
        raise AssertionError("oversized input must be rejected before read")

    monkeypatch.setattr(materials, "read_bytes_checked", forbidden)
    result = stage(client, setup)
    assert result.status_code == 413, result.text
    assert setup["renderer"].calls == 0


def test_repeated_layers_pass_one_source_byte_set_to_renderer(client, db_session, setup):
    source = add_source(client, db_session, setup)
    payload = setup["master"]["payload"]
    first = payload["canvases"][0]["layers"][0]
    payload = {**payload, "canvases": [{**payload["canvases"][0], "layers": [first, {**first, "id": "second", "order": 1}]}]}
    refs = [{"material_revision_id": source.id, "content_hash": source.content_hash, "role": "graphic_layer",
        "slot_key": layer_id, "sort_order": order, "placement": {"canvas_id": "one", "layer_id": layer_id}}
        for order, layer_id in enumerate(["source", "second"])]
    response = client.post(setup["path"], json={"expected_revision": 2, "payload_schema": "graphic.master.v2",
        "payload": payload, "asset_refs": refs, "idempotency_key": "shared-source"})
    assert response.status_code == 200, response.text
    setup["master"] = response.json()
    setup["body"].update(expected_payload_hash=response.json()["payload_hash"], expected_context_hash=response.json()["context_hash"])
    staged = stage(client, setup)
    assert staged.status_code == 200, staged.text
    assert setup["renderer"].source_count == 1
