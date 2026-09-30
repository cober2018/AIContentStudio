"""ASR receipt is a bounded proposal; only explicit Master save accepts it."""

import io
import json
import threading
import wave
from copy import deepcopy

import pytest
from sqlalchemy import select

from app.models import (
    ContentMasterAssetRef,
    ContentMasterRevision,
    MaterialRevision,
    ProjectEvent,
    ProjectMaterialReference,
)
from app.services.content_harness import providers
from app.services.content_harness.registry import PluginRegistry

OWNER = {"X-Studio-User": "asr-owner@studio.local"}
OTHER = {"X-Studio-User": "asr-other@studio.local"}


@pytest.fixture
def asr_setup(client, db_session, monkeypatch, tmp_path):
    from app.services import asr_suggestions, asset_media

    monkeypatch.setattr(asset_media, "MEDIA_ROOT", tmp_path)
    monkeypatch.setattr(asr_suggestions, "_cache", {})
    audio = io.BytesIO()
    with wave.open(audio, "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(16000)
        output.writeframes(b"\x00\x00" * 64000)
    upload = client.post("/api/v1/materials/upload?kind=audio&public_use_allowed=true&model_use_allowed=true&rights_status=cleared", headers=OWNER, files={"file": ("source.wav", audio.getvalue(), "audio/wav")})
    assert upload.status_code == 201, upload.text
    revision = upload.json()["revisions"][0]
    persona = client.post("/api/v1/content-personas", headers=OWNER, json={"name": "ASR 作者"}).json()["id"]
    project = client.post("/api/v1/content-projects", headers=OWNER, json={"title": "ASR 项目"}).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project}/units", headers=OWNER, json={"title": "视频", "modality": "video", "persona_id": persona}).json()["id"]
    db_session.add(ProjectMaterialReference(project_id=project, material_revision_id=revision["id"], origin="system_reference", status="active"))
    db_session.commit()
    payload = {"title": "ASR", "aspect_ratio": [9, 16], "script": {"blocks": []}, "shots": [],
        "timeline": {"duration_ms": 4000, "tracks": []}, "voice": {"mode": "recorded", "material_revision_id": revision["id"]},
        "subtitles": {"cues": []}, "overlays": [], "music": {}, "cover": {}}
    refs = [{"material_revision_id": revision["id"], "content_hash": revision["content_hash"], "role": "voice_audio", "slot_key": "voice", "sort_order": 0, "placement": {"voice": "main"}}]
    base = f"/api/v1/content-projects/{project}/units/{unit}/master-revisions"
    saved = client.post(base, headers=OWNER, json={"payload_schema": "video.master.v2", "idempotency_key": "initial", "payload": payload, "asset_refs": refs})
    assert saved.status_code == 200, saved.text

    class Provider:
        key = "asr.fixture"
        version = "1"
        fingerprint = "a" * 64
        calls = 0
        result = {"status": "succeeded", "transcript": "这是转录", "cues": [{"text": "这是转录", "start_ms": 0, "end_ms": 2000}], "metadata": {"token": "private-response-token"}}

        def runtime_fingerprint(self):
            return self.fingerprint

        def transcribe(self, request):
            self.calls += 1
            assert request["source_bytes"] == audio.getvalue()
            return deepcopy(self.result)

    provider = Provider()
    registry = PluginRegistry()
    registry.register("asr_provider", provider.key, provider.version, provider)
    monkeypatch.setattr(providers, "registry", registry)
    return {"provider": provider, "base": base, "master": saved.json(), "revision": revision, "refs": refs, "payload": payload}


def suggest(client, setup, headers=OWNER):
    return client.post(f"{setup['base']}/{setup['master']['id']}/asr-suggestions", headers=headers, json={
        "provider_key": "asr.fixture", "provider_version": "1", "source_revision_id": setup["revision"]["id"], "base_payload_hash": setup["master"]["payload_hash"]})


def save(client, setup, suggestion, **extra):
    payload = deepcopy(setup["payload"])
    payload["subtitles"]["cues"] = suggestion["cues"]
    return client.post(setup["base"], headers=OWNER, json={"payload_schema": "video.master.v2", "payload": payload, "asset_refs": setup["refs"],
        "expected_revision": 1, "parent_revision_id": setup["master"]["id"], "expected_context_hash": setup["master"]["context_hash"],
        "idempotency_key": "asr-save", "edit_summary": {"asr_receipt_id": suggestion["receipt_id"]}, **extra})


def test_asr_suggestion_does_not_write_until_explicit_save(client, db_session, asr_setup):
    response = suggest(client, asr_setup)
    assert response.status_code == 200, response.text
    result = response.json()
    assert "private-response-token" not in response.text
    assert result["cues"][0]["id"].startswith("asr-")
    assert db_session.query(ContentMasterRevision).count() == 1
    accepted = save(client, asr_setup, result)
    assert accepted.status_code == 200, accepted.text
    receipt = accepted.json()["edit_summary"]["asr_provenance"]
    assert receipt["status"] == "verified_output_match"
    assert receipt["source"]["revision_id"] == asr_setup["revision"]["id"]
    assert receipt["source"]["content_hash"] == asr_setup["revision"]["content_hash"]
    assert "private-response-token" not in json.dumps(receipt)
    assert db_session.query(ContentMasterRevision).count() == 2
    replay = save(client, asr_setup, result)
    assert replay.status_code == 200 and replay.json()["id"] == accepted.json()["id"]


@pytest.mark.parametrize("change", [{"cues": [{"text": "bad", "start_ms": 0, "end_ms": 5000}]},
    {"cues": [{"text": "bad", "start_ms": True, "end_ms": 100}]}, {"cues": [{"text": "x" * 501, "start_ms": 0, "end_ms": 100}]},
    {"cues": [{"text": "one", "start_ms": 0, "end_ms": 2000}, {"text": "two", "start_ms": 1000, "end_ms": 3000}]},
    {"transcript": "x" * 100001}, {"status": "unknown"}])
def test_asr_bad_output_is_no_write(client, db_session, asr_setup, change):
    asr_setup["provider"].result.update(change)
    result = suggest(client, asr_setup)
    assert result.status_code in {409, 422}
    assert db_session.query(ContentMasterRevision).count() == 1
    assert len(db_session.scalars(select(MaterialRevision)).all()) == 1


def test_asr_foreign_actor_or_revoked_source_never_calls_provider(client, db_session, asr_setup):
    assert suggest(client, asr_setup, OTHER).status_code == 404
    source = db_session.get(MaterialRevision, asr_setup["revision"]["id"])
    source.model_use_allowed = False
    db_session.commit()
    assert suggest(client, asr_setup).status_code == 409
    assert asr_setup["provider"].calls == 0


@pytest.mark.parametrize("change", ["forged", "runtime", "rights"])
def test_asr_invalid_receipt_save_is_atomic(client, db_session, asr_setup, change):
    response = suggest(client, asr_setup)
    assert response.status_code == 200, response.text
    result = response.json()
    if change == "forged":
        result["receipt_id"] = "0" * 32
    elif change == "runtime":
        asr_setup["provider"].fingerprint = "b" * 64
    else:
        db_session.get(MaterialRevision, asr_setup["revision"]["id"]).model_use_allowed = False
        db_session.commit()
    accepted = save(client, asr_setup, result)
    assert accepted.status_code in {404, 409, 422}
    assert db_session.query(ContentMasterRevision).count() == 1


def test_client_cannot_forge_asr_provenance(client, db_session, asr_setup):
    response = client.post(asr_setup["base"], headers=OWNER, json={"idempotency_key": "forged", "expected_revision": 1,
        "payload_schema": "video.master.v2", "payload": asr_setup["payload"], "asset_refs": asr_setup["refs"], "edit_summary": {"asr_provenance": {"verified": True}}})
    assert response.status_code == 422
    assert db_session.query(ContentMasterRevision).count() == 1


def test_asr_edits_after_accept_are_not_claimed_as_exact_provider_output(client, db_session, asr_setup):
    result = suggest(client, asr_setup).json()
    result["cues"][0]["text"] = "人工调整"
    accepted = save(client, asr_setup, result)
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["edit_summary"]["asr_provenance"]["status"] == "subsequently_modified"


def test_expired_receipt_does_not_save(client, db_session, asr_setup, monkeypatch):
    from app.services import asr_suggestions

    result = suggest(client, asr_setup).json()
    monkeypatch.setattr(asr_suggestions.time, "monotonic", lambda: 10 ** 20)
    assert save(client, asr_setup, result).status_code == 422
    assert db_session.query(ContentMasterRevision).count() == 1


def test_asr_timeout_is_unknown_and_is_not_retried(client, db_session, asr_setup, monkeypatch):
    calls = []

    def timeout(request):
        calls.append(True)
        raise TimeoutError("private-provider-token")

    monkeypatch.setattr(asr_setup["provider"], "transcribe", timeout)
    response = suggest(client, asr_setup)
    assert response.status_code == 409 and response.json()["detail"] == "asr_outcome_unknown"
    assert len(calls) == 1 and "private-provider-token" not in response.text
    assert db_session.query(ContentMasterRevision).count() == 1


def test_old_receipt_does_not_attach_to_new_master(client, db_session, asr_setup):
    result = suggest(client, asr_setup).json()
    manual = client.post(asr_setup["base"], headers=OWNER, json={"idempotency_key": "manual", "expected_revision": 1,
        "payload_schema": "video.master.v2", "payload": asr_setup["payload"], "asset_refs": asr_setup["refs"]})
    assert manual.status_code == 200, manual.text
    response = save(client, asr_setup, result, expected_revision=2, parent_revision_id=manual.json()["id"])
    assert response.status_code == 409
    assert db_session.query(ContentMasterRevision).count() == 2


@pytest.mark.parametrize("after_suggestion", [False, True])
def test_detached_source_cannot_be_transcribed_or_accepted(client, db_session, asr_setup, after_suggestion):
    result = suggest(client, asr_setup).json() if after_suggestion else None
    reference = db_session.scalar(select(ProjectMaterialReference).where(
        ProjectMaterialReference.material_revision_id == asr_setup["revision"]["id"]))
    reference.status = "detached"
    db_session.commit()
    response = save(client, asr_setup, result) if after_suggestion else suggest(client, asr_setup)
    assert response.status_code == 422
    assert db_session.query(ContentMasterRevision).count() == 1
    assert asr_setup["provider"].calls == int(after_suggestion)


def test_source_authorization_transaction_is_held_through_provider_dispatch(client, db_session, asr_setup, monkeypatch):
    from app.services import provider_calls, provider_media

    observed = []
    original_sources = provider_media._sources
    original_call = provider_calls.call

    def sources(*args, **kwargs):
        observed.append(kwargs.get("lock", False))
        return original_sources(*args, **kwargs)

    def dispatch(*args, **kwargs):
        assert observed == [True]
        assert db_session.in_transaction()
        return original_call(*args, **kwargs)

    monkeypatch.setattr(provider_media, "_sources", sources)
    monkeypatch.setattr(provider_calls, "call", dispatch)
    assert suggest(client, asr_setup).status_code == 200


def test_provider_http_exception_is_redacted(client, db_session, asr_setup, monkeypatch):
    from fastapi import HTTPException

    def failed(_request):
        raise HTTPException(502, "Authorization synthetic-secret https://host/?signature=secret")

    monkeypatch.setattr(asr_setup["provider"], "transcribe", failed)
    result = suggest(client, asr_setup)
    assert result.status_code == 502
    assert result.json()["detail"] == "asr_execution_failed"
    assert "synthetic-secret" not in result.text
    assert db_session.query(ContentMasterRevision).count() == 1


def test_asr_runtime_rotation_at_commit_rolls_back_master(client, db_session, asr_setup, monkeypatch):
    from app.services import content_masters

    result = suggest(client, asr_setup).json()
    original = content_masters.record_project_event
    events = db_session.query(ProjectEvent).count()
    refs = db_session.query(ContentMasterAssetRef).count()

    def rotate_after_writes(*args, **kwargs):
        original(*args, **kwargs)
        asr_setup["provider"].fingerprint = "b" * 64

    monkeypatch.setattr(content_masters, "record_project_event", rotate_after_writes)
    response = save(client, asr_setup, result)
    assert response.status_code == 409, response.text
    assert response.json()["detail"] == "asr_runtime_changed"
    assert db_session.query(ContentMasterRevision).count() == 1
    assert db_session.query(ContentMasterAssetRef).count() == refs
    assert db_session.query(ProjectEvent).count() == events


def test_asr_configuration_update_waits_for_actual_commit(client, db_session, asr_setup, monkeypatch):
    from app import runtime_config

    result = suggest(client, asr_setup).json()
    started, finished = threading.Event(), threading.Event()
    original = db_session.commit
    workers = []

    def rotate():
        started.set()
        runtime_config.set_runtime("asr-commit-test", {"version": "rotated"})
        finished.set()

    def commit():
        worker = threading.Thread(target=rotate)
        workers.append(worker)
        worker.start()
        assert started.wait(1)
        assert not finished.wait(0.05)
        return original()

    monkeypatch.setattr(db_session, "commit", commit)
    try:
        response = save(client, asr_setup, result)
        assert response.status_code == 200, response.text
        assert finished.wait(1)
        assert db_session.query(ContentMasterRevision).count() == 2
    finally:
        for worker in workers:
            worker.join(timeout=1)
        runtime_config.clear_runtime("asr-commit-test")
