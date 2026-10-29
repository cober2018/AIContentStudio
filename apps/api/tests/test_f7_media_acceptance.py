"""Provider previews never become durable assets without a checked explicit acceptance."""

import hashlib
import io
import json

import pytest
from PIL import Image
from sqlalchemy import select

from app.models import AuditLog, Material, MaterialRevision, ProjectMaterialReference, User
from app.services.content_harness import providers
from app.services.content_harness.registry import PluginRegistry

EDITOR = {"X-Studio-User": "media-owner@studio.local"}
OTHER = {"X-Studio-User": "media-other@studio.local"}


@pytest.mark.parametrize("path", [
    "/api/v1/provider-search",
    "/api/v1/materials/search",
    "/api/v1/materials/generate",
    "/api/v1/provider-media/stage",
    "/api/v1/provider-media/opaque/accept",
    "/api/v1/settings/renderer-probes",
    "/api/v1/settings/media-renderer-verifications",
    "/api/v1/settings/publisher-verifications",
    "/api/v1/data-source-capabilities",
    "/api/v1/data-source-capabilities/private-request-secret/probe",
    "/api/v1/content-projects/private-request-secret/units/1/master-revisions/1/asr-suggestions",
    "/api/v1/content-projects/1/units/1/master-revisions/1/media-render-previews",
])
def test_capability_validation_never_echoes_raw_input(client, db_session, path):
    db_session.add(User(email=EDITOR["X-Studio-User"], name="Validation", role="admin"))
    db_session.commit()
    response = client.post(path, headers=EDITOR, json={"prompt": {"Authorization": "private-request-secret"}})
    assert response.status_code == 422
    assert "private-request-secret" not in response.text
    assert response.json() == {"detail": "capability_input_invalid"}
    assert db_session.query(MaterialRevision).count() == 0
    assert db_session.query(AuditLog).count() == 0


def test_legacy_validation_shape_is_unchanged(client):
    response = client.get("/api/v1/materials/private-request-secret", headers=EDITOR)
    assert response.status_code == 422
    assert isinstance(response.json()["detail"], list)


@pytest.fixture
def media_provider(monkeypatch, tmp_path):
    from app.services import asset_media, provider_media

    monkeypatch.setattr(asset_media, "MEDIA_ROOT", tmp_path)
    monkeypatch.setattr(provider_media, "_cache", {})
    output = io.BytesIO()
    Image.new("RGB", (2, 2), "blue").save(output, format="PNG")

    class Provider:
        key = "image.fixture"
        version = "1"
        fingerprint = "a" * 64
        content = output.getvalue()
        mime = "image/png"
        status = "succeeded"

        def runtime_fingerprint(self):
            return self.fingerprint

        def generate(self, request, out_path=None):
            if out_path is not None:
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_bytes(self.content)
                return True
            return providers.MediaOutput(status=self.status, content=self.content, mime_type=self.mime,
                                         metadata={"token": "provider-secret", "url": "https://cdn.example/file?sig=secret"})

    loaded = PluginRegistry()
    provider = Provider()
    loaded.register("image_provider", provider.key, provider.version, provider)
    monkeypatch.setattr(providers, "registry", loaded)
    return provider


def stage(client, **extra):
    return client.post("/api/v1/provider-media/stage", headers=EDITOR, json={
        "provider_kind": "image_provider", "provider_key": "image.fixture", "provider_version": "1",
        "prompt": "prompt containing private-request-secret", **extra,
    })


def decision(**extra):
    return {"confirmed": True, "title": "人工接受的图片", "license_code": "CC0",
            "license_evidence_hash": "b" * 64, "public_use_allowed": True,
            "model_use_allowed": True, "commercial_use_allowed": False, **extra}


def test_provider_wall_clock_timeout_does_not_retry_or_stage(client, db_session, media_provider, monkeypatch):
    import importlib.util
    import threading

    assert importlib.util.find_spec("app.services.provider_calls"), "bounded provider call is missing"
    from app.services import provider_calls

    release = threading.Event()
    calls = []

    def slow(request):
        calls.append(True)
        release.wait(5)
        return providers.MediaOutput("succeeded", media_provider.content, "image/png")

    monkeypatch.setattr(provider_calls, "TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(media_provider, "generate", slow)
    try:
        result = stage(client)
        assert result.status_code == 409 and result.json()["detail"] == "provider_outcome_unknown"
        assert len(calls) == 1
        assert db_session.scalars(select(Material)).all() == []
    finally:
        release.set()


def test_preview_accept_is_explicit_atomic_and_exact_project_reference(client, db_session, media_provider):
    project = client.post("/api/v1/content-projects", headers=EDITOR, json={"title": "素材项目"}).json()
    response = stage(client, project_id=project["id"])
    assert response.status_code == 200, response.text
    receipt = response.json()
    assert receipt["public_ready"] is False
    assert db_session.scalars(select(MaterialRevision)).all() == []
    assert "private-request-secret" not in response.text and "provider-secret" not in response.text
    assert client.get(f"/api/v1/provider-media/{receipt['stage_id']}/raw", headers=OTHER).status_code == 404
    raw = client.get(f"/api/v1/provider-media/{receipt['stage_id']}/raw", headers=EDITOR)
    assert raw.content == media_provider.content
    accepted = client.post(f"/api/v1/provider-media/{receipt['stage_id']}/accept", headers=EDITOR, json=decision())
    assert accepted.status_code == 201, accepted.text
    revision = db_session.get(MaterialRevision, accepted.json()["material_revision_id"])
    assert revision.content_hash == hashlib.sha256(media_provider.content).hexdigest()
    assert revision.prompt_text is None and revision.source_url is None
    stored = json.dumps([revision.metadata_json, revision.source_metadata_json,
                         [row.detail_json for row in db_session.scalars(select(AuditLog)).all()]])
    assert "provider-secret" not in stored and "private-request-secret" not in stored and "sig=secret" not in stored
    refs = db_session.scalars(select(ProjectMaterialReference)).all()
    assert len(refs) == 1 and refs[0].project_id == project["id"] and refs[0].material_revision_id == revision.id
    shared = client.get(f"/api/v1/content-projects/{project['id']}/shared-assets", headers=EDITOR)
    assert shared.status_code == 200, shared.text
    assert len(shared.json()) == 1
    replay = client.post(f"/api/v1/provider-media/{receipt['stage_id']}/accept", headers=EDITOR, json=decision())
    assert replay.status_code == 201 and replay.json() == accepted.json()
    conflicting = client.post(f"/api/v1/provider-media/{receipt['stage_id']}/accept", headers=EDITOR,
                              json=decision(public_use_allowed=False))
    assert conflicting.status_code == 409
    assert len(db_session.scalars(select(MaterialRevision)).all()) == 1


@pytest.mark.parametrize("change", [{"confirmed": False}, {"license_code": "unknown"}, {"license_evidence_hash": ""}])
def test_incomplete_rights_decision_writes_no_material(client, db_session, media_provider, change):
    response = stage(client)
    assert response.status_code == 200, response.text
    accepted = client.post(f"/api/v1/provider-media/{response.json()['stage_id']}/accept", headers=EDITOR,
                           json=decision(**change))
    assert accepted.status_code == 422
    assert db_session.scalars(select(Material)).all() == []


def test_runtime_rotation_during_accept_rolls_back_all_rows(client, db_session, media_provider, monkeypatch):
    from app.services import materials

    receipt = stage(client).json()
    create = materials.create_revision

    def rotate(*args, **kwargs):
        revision = create(*args, **kwargs)
        media_provider.fingerprint = "c" * 64
        return revision

    monkeypatch.setattr(materials, "create_revision", rotate)
    response = client.post(f"/api/v1/provider-media/{receipt['stage_id']}/accept", headers=EDITOR, json=decision())
    assert response.status_code == 409, response.text
    assert response.json()["detail"] == "provider_runtime_changed"
    assert not db_session.scalars(select(Material)).all()
    assert not db_session.scalars(select(MaterialRevision)).all()
    assert not db_session.scalars(select(AuditLog).where(AuditLog.event == "provider.media_accepted")).all()


def test_accept_holds_runtime_configuration_until_actual_db_commit(client, db_session, media_provider, monkeypatch):
    import threading

    from app import runtime_config

    key = "f7-test-accept-guard"
    runtime_config.set_runtime(key, {"fingerprint": "a" * 64})
    monkeypatch.setattr(media_provider, "runtime_fingerprint",
                        lambda: runtime_config.get_runtime(key)["fingerprint"])
    started, done = threading.Event(), threading.Event()
    def rotate():
        started.set()
        runtime_config.set_runtime(key, {"fingerprint": "b" * 64})
        done.set()
    worker = threading.Thread(target=rotate)
    commit = db_session.commit
    def observed_commit():
        worker.start()
        assert started.wait(2)
        assert not done.wait(0.05), "configuration changed before durable acceptance committed"
        assert runtime_config.get_runtime(key)["fingerprint"] == "a" * 64
        commit()
    try:
        receipt = stage(client).json()
        monkeypatch.setattr(db_session, "commit", observed_commit)
        response = client.post(f"/api/v1/provider-media/{receipt['stage_id']}/accept", headers=EDITOR, json=decision())
        assert response.status_code == 201, response.text
        worker.join(2)
        assert done.is_set()
        revision = db_session.get(MaterialRevision, response.json()["material_revision_id"])
        assert revision.source_metadata_json["runtime_hash"] == "a" * 64
    finally:
        worker.join(2) if worker.ident else None
        runtime_config.clear_runtime(key)


def test_runtime_guard_serializes_config_rotation_through_commit(monkeypatch):
    import threading

    from app import runtime_config

    started, done = threading.Event(), threading.Event()
    def rotate():
        started.set()
        runtime_config.set_runtime("f7-test-guard", {"revision": 2})
        done.set()

    runtime_config.set_runtime("f7-test-guard", {"revision": 1})
    worker = threading.Thread(target=rotate)
    try:
        with runtime_config.configuration_guard():
            worker.start()
            assert started.wait(2)
            assert not done.wait(0.05)
            assert runtime_config.get_runtime("f7-test-guard") == {"revision": 1}
        worker.join(2)
        assert done.is_set()
        assert runtime_config.get_runtime("f7-test-guard") == {"revision": 2}
    finally:
        worker.join(2) if worker.ident else None
        runtime_config.clear_runtime("f7-test-guard")


@pytest.mark.parametrize("content,mime", [(b"", "image/png"), (b"not-media", "image/png"), (b"\x89PNG\r\n\x1a\ninvalid", "image/png")])
def test_provider_success_without_valid_decoded_bytes_creates_no_receipt(client, db_session, media_provider, content, mime):
    media_provider.content, media_provider.mime = content, mime
    response = stage(client)
    assert response.status_code == 422, response.text
    assert db_session.scalars(select(MaterialRevision)).all() == []


def test_runtime_drift_before_acceptance_writes_nothing(client, db_session, media_provider):
    response = stage(client)
    assert response.status_code == 200, response.text
    media_provider.fingerprint = "c" * 64
    accepted = client.post(f"/api/v1/provider-media/{response.json()['stage_id']}/accept", headers=EDITOR, json=decision())
    assert accepted.status_code == 409
    assert db_session.scalars(select(MaterialRevision)).all() == []


def test_attribution_license_requires_credit_before_accept(client, db_session, media_provider):
    receipt = stage(client).json()
    path = f"/api/v1/provider-media/{receipt['stage_id']}/accept"
    denied = client.post(path, headers=EDITOR, json=decision(license_code="CC-BY-4.0"))
    assert denied.status_code == 422
    assert db_session.scalars(select(MaterialRevision)).all() == []
    accepted = client.post(path, headers=EDITOR, json=decision(license_code="CC-BY-4.0", attribution_text="Author · CC BY 4.0"))
    assert accepted.status_code == 201, accepted.text
    assert db_session.get(MaterialRevision, accepted.json()["material_revision_id"]).attribution_text == "Author · CC BY 4.0"


def test_foreign_accept_and_archived_project_write_nothing(client, db_session, media_provider):
    from app.models import ContentProject

    project = client.post("/api/v1/content-projects", headers=EDITOR, json={"title": "将归档的项目"}).json()
    receipt = stage(client, project_id=project["id"]).json()
    path = f"/api/v1/provider-media/{receipt['stage_id']}/accept"
    assert client.post(path, headers=OTHER, json=decision()).status_code == 404
    db_session.get(ContentProject, project["id"]).status = "archived"
    db_session.commit()
    assert client.post(path, headers=EDITOR, json=decision()).status_code == 409
    assert db_session.scalars(select(MaterialRevision)).all() == []


def test_unavailable_provider_is_typed_and_redacted(client, db_session, media_provider):
    media_provider.status = "unavailable"
    response = stage(client)
    assert response.status_code == 422 and response.json()["detail"] == "capability_unavailable"
    assert db_session.scalars(select(MaterialRevision)).all() == []


def test_wewrite_image_without_single_attempt_runtime_is_unavailable(monkeypatch):
    from app import runtime_config

    monkeypatch.setattr(runtime_config, "get_runtime", lambda *args: {"enabled": True, "provider": "openai", "model": "m", "api_key": "secret"})
    monkeypatch.setenv("WEWRITE_IMAGE_CREDENTIAL_VERSION", "test-version")
    provider = providers.WewriteImageProvider()
    assert provider.runtime_fingerprint() is None
    assert provider.generate({"prompt": "test"}).status == "unavailable"


def test_video_metadata_without_successful_decode_cannot_stage(client, db_session, media_provider, monkeypatch):
    import subprocess

    from app.services import provider_media

    media_provider.key = "video.fixture"
    media_provider.content = b"\x00\x00\x00\x18ftypisom" + b"corrupt-video-packets"
    media_provider.mime = "video/mp4"
    providers.registry.register("video_provider", media_provider.key, "1", media_provider)
    calls = []

    def probe_or_decode(command, **kwargs):
        calls.append(command[0])
        if command[0] == "ffprobe":
            return subprocess.CompletedProcess(command, 0, b'{"streams":[{"width":16,"height":16}]}', b"")
        return subprocess.CompletedProcess(command, 183, b"", b"corrupt packet")

    monkeypatch.setattr(provider_media.subprocess, "run", probe_or_decode)
    response = stage(client, provider_kind="video_provider", provider_key="video.fixture")
    assert response.status_code == 422, response.text
    assert calls == ["ffprobe", "ffmpeg"]
    assert db_session.scalars(select(MaterialRevision)).all() == []


def test_source_revocation_committing_during_acceptance_writes_no_derived_asset(media_provider, tmp_path):
    import threading
    from concurrent.futures import ThreadPoolExecutor

    from fastapi import HTTPException
    from sqlalchemy import create_engine, event, update
    from sqlalchemy.orm import Session

    from app.db import Base
    from app.models import User
    from app.services import materials, provider_media

    engine = create_engine(f"sqlite:///{tmp_path / 'race.db'}", connect_args={"check_same_thread": False, "timeout": 3})
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user = User(email=EDITOR["X-Studio-User"], name="media owner", role="editor")
        db.add(user)
        material = materials.create_material(db, kind="image", title="source", created_by=user.email)
        source = materials.create_revision(db, material, content=media_provider.content, suffix=".png", declared_mime="image/png", model_use_allowed=True)
        db.commit()
        actor_id, source_id = user.id, source.id
        receipt = provider_media.stage(db, user, {"provider_kind": "image_provider", "provider_key": "image.fixture",
                                                "provider_version": "1", "prompt": "derived", "source_revision_ids": [source_id]})
    writer_locked, release_writer, acceptance_started = threading.Event(), threading.Event(), threading.Event()
    acceptance_lock_attempted = threading.Event()

    @event.listens_for(engine, "before_cursor_execute")
    def observe_lock(_connection, _cursor, statement, _parameters, _context, _executemany):
        if "SET status=material_revision.status" in statement:
            acceptance_lock_attempted.set()

    def revoke():
        with Session(engine) as db:
            db.execute(update(MaterialRevision).where(MaterialRevision.id == source_id).values(status="revoked"))
            writer_locked.set()
            assert release_writer.wait(3)
            db.commit()

    def accept():
        with Session(engine) as db:
            actor = db.get(User, actor_id)
            acceptance_started.set()
            try:
                return provider_media.accept(db, actor, receipt["stage_id"], decision())
            except HTTPException as error:
                return error.status_code

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            writer = executor.submit(revoke)
            assert writer_locked.wait(3)
            accepting = executor.submit(accept)
            assert acceptance_started.wait(3)
            assert acceptance_lock_attempted.wait(3)
            release_writer.set()
            writer.result(timeout=3)
            assert accepting.result(timeout=3) == 409
        with Session(engine) as db:
            assert len(db.scalars(select(MaterialRevision)).all()) == 1
    finally:
        release_writer.set()
        engine.dispose()


def test_real_small_mp4_is_fully_decoded_before_stage(client, media_provider, tmp_path):
    import subprocess

    video = tmp_path / "valid.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=blue:s=16x16:d=0.1", "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", str(video)], timeout=10, check=True, capture_output=True)
    media_provider.key, media_provider.mime, media_provider.content = "video.fixture", "video/mp4", video.read_bytes()
    providers.registry.register("video_provider", media_provider.key, "1", media_provider)
    response = stage(client, provider_kind="video_provider", provider_key="video.fixture")
    assert response.status_code == 200, response.text
    assert response.json()["content_hash"] == hashlib.sha256(video.read_bytes()).hexdigest()


def test_legacy_generate_is_preview_only_not_automatic_public_asset(client, db_session, media_provider, monkeypatch):
    from app.services import model_registration

    monkeypatch.setattr(model_registration, "cover_image_config", lambda: {
        "vendor_id": "minimax", "model": "image-01", "size": "1344x768", "base_url": "https://images.example/v1", "api_key": "PRIVATE"})
    monkeypatch.setattr(providers, "resolve_asset_provider", lambda: media_provider)
    monkeypatch.setattr(providers, "bootstrap_media_providers", lambda: None)
    response = client.post("/api/v1/materials/generate", headers=EDITOR, json={"prompt": "private prompt"})
    assert response.status_code == 200, response.text
    assert response.json()["public_ready"] is False
    assert db_session.scalars(select(MaterialRevision)).all() == []


def test_tts_accepts_exact_audio_but_never_edits_video_master(client, db_session, media_provider):
    import wave

    from app.models import ContentMasterRevision

    output = io.BytesIO()
    with wave.open(output, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(16000)
        audio.writeframes(b"\x00\x00" * 160)
    media_provider.key, media_provider.content, media_provider.mime = "tts.fixture", output.getvalue(), "audio/wav"
    providers.registry.register("tts_provider", "tts.fixture", "1", media_provider)
    staged = stage(client, provider_kind="tts_provider", provider_key="tts.fixture")
    assert staged.status_code == 200, staged.text
    saved = client.post(f"/api/v1/provider-media/{staged.json()['stage_id']}/accept", headers=EDITOR,
                        json=decision(public_use_allowed=False, model_use_allowed=False))
    assert saved.status_code == 201
    revision = db_session.get(MaterialRevision, saved.json()["material_revision_id"])
    assert revision.mime_type == "audio/wav" and revision.public_use_allowed is False
    assert db_session.scalars(select(ContentMasterRevision)).all() == []


def test_unknown_outcome_exposes_no_raw_provider_error(client, db_session, media_provider, monkeypatch):
    def timeout(request):
        raise TimeoutError("Authorization: provider-secret")
    monkeypatch.setattr(media_provider, "generate", timeout)
    response = stage(client)
    assert response.status_code == 409 and "provider_outcome_unknown" in response.text
    assert "provider-secret" not in response.text
    assert db_session.scalars(select(MaterialRevision)).all() == []


def test_source_revoked_after_preview_blocks_accept(client, db_session, media_provider):
    first = stage(client).json()
    accepted = client.post(f"/api/v1/provider-media/{first['stage_id']}/accept", headers=EDITOR, json=decision()).json()
    source_id = accepted["material_revision_id"]
    second = stage(client, source_revision_ids=[source_id])
    assert second.status_code == 200, second.text
    source = db_session.get(MaterialRevision, source_id)
    source.status = "revoked"
    db_session.commit()
    denied = client.post(f"/api/v1/provider-media/{second.json()['stage_id']}/accept", headers=EDITOR, json=decision())
    assert denied.status_code == 409
    assert len(db_session.scalars(select(MaterialRevision)).all()) == 1


def test_generation_keeps_source_authorization_transaction_through_dispatch(client, db_session, media_provider, monkeypatch):
    from app.services import provider_calls, provider_media

    first = stage(client).json()
    accepted = client.post(f"/api/v1/provider-media/{first['stage_id']}/accept", headers=EDITOR, json=decision()).json()
    project = client.post("/api/v1/content-projects", headers=EDITOR, json={"title": "Dispatch authorization"}).json()
    observed = []
    original_sources, original_call = provider_media._sources, provider_calls.call

    def sources(*args, **kwargs):
        observed.append(kwargs.get("lock", False))
        return original_sources(*args, **kwargs)

    def dispatch(*args, **kwargs):
        assert observed == [True]
        assert db_session.in_transaction()
        return original_call(*args, **kwargs)

    monkeypatch.setattr(provider_media, "_sources", sources)
    monkeypatch.setattr(provider_calls, "call", dispatch)
    response = stage(client, project_id=project["id"], source_revision_ids=[accepted["material_revision_id"]])
    assert response.status_code == 200, response.text
    assert len(db_session.scalars(select(MaterialRevision)).all()) == 1


def test_revocation_winning_generation_dispatch_lock_sends_no_source_bytes(media_provider, tmp_path, monkeypatch):
    import threading
    from concurrent.futures import ThreadPoolExecutor

    from fastapi import HTTPException
    from sqlalchemy import create_engine, event, update
    from sqlalchemy.orm import Session

    from app.db import Base
    from app.models import User
    from app.services import materials, provider_media

    engine = create_engine(f"sqlite:///{tmp_path / 'dispatch.db'}", connect_args={"check_same_thread": False, "timeout": 3})
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user = User(email=EDITOR["X-Studio-User"], name="media owner", role="editor")
        db.add(user)
        material = materials.create_material(db, kind="image", title="source", created_by=user.email)
        source = materials.create_revision(db, material, content=media_provider.content, suffix=".png", declared_mime="image/png", model_use_allowed=True)
        db.commit()
        actor_id, source_id = user.id, source.id
    writer_locked, release_writer, boundary_attempted = threading.Event(), threading.Event(), threading.Event()
    dispatched = []
    original_generate = media_provider.generate

    def generate(request):
        dispatched.append(request["source_bytes"])
        boundary_attempted.set()
        return original_generate(request)

    monkeypatch.setattr(media_provider, "generate", generate)

    @event.listens_for(engine, "before_cursor_execute")
    def observe_lock(_connection, _cursor, statement, _parameters, _context, _executemany):
        if "SET status=material_revision.status" in statement:
            boundary_attempted.set()

    def revoke():
        with Session(engine) as db:
            db.execute(update(MaterialRevision).where(MaterialRevision.id == source_id).values(model_use_allowed=False))
            writer_locked.set()
            assert release_writer.wait(3)
            db.commit()

    def generate_preview():
        with Session(engine) as db:
            try:
                return provider_media.stage(db, db.get(User, actor_id), {"provider_kind": "image_provider", "provider_key": "image.fixture",
                    "provider_version": "1", "prompt": "derived", "source_revision_ids": [source_id]})
            except HTTPException as error:
                return error.status_code

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            writer = executor.submit(revoke)
            assert writer_locked.wait(3)
            generating = executor.submit(generate_preview)
            assert boundary_attempted.wait(3)
            release_writer.set()
            writer.result(timeout=3)
            assert generating.result(timeout=3) == 409
        assert dispatched == []
        assert provider_media._cache == {}
        with Session(engine) as db:
            assert len(db.scalars(select(MaterialRevision)).all()) == 1
    finally:
        release_writer.set()
        engine.dispose()


def test_expired_preview_requires_explicit_new_generation(client, db_session, media_provider, monkeypatch):
    from app.services import provider_media

    monkeypatch.setattr(provider_media, "_TTL", 0)
    staged = stage(client)
    assert staged.status_code == 200
    denied = client.post(f"/api/v1/provider-media/{staged.json()['stage_id']}/accept", headers=EDITOR, json=decision())
    assert denied.status_code == 404
    assert db_session.scalars(select(MaterialRevision)).all() == []
