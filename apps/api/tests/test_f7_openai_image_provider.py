"""Native adapter tests use HTTP transport fixtures, never vendor credentials."""

import base64
import gzip
import hashlib
import io
import json

import httpx
import pytest
from PIL import Image
from sqlalchemy import select

from app import runtime_config
from app.models import MaterialRevision
from app.services.content_harness import providers

EDITOR = {"X-Studio-User": "native-image@studio.local"}


@pytest.fixture
def configured(monkeypatch):
    from app.services import model_registration

    config = {
        "model": "gpt-image-1",
        "size": "1024x1024",
        "base_url": "https://images.example/v1",
        "api_key": "PRIVATE_KEY",
    }
    monkeypatch.setattr(model_registration, "cover_image_config", lambda: dict(config))
    return config


def adapter():
    from app.services.openai_image_provider import OpenAIImageProvider

    return OpenAIImageProvider()


def png():
    stream = io.BytesIO()
    Image.new("RGB", (3, 2), "red").save(stream, "PNG")
    return stream.getvalue()


def transport(monkeypatch, handler):
    from app.services import openai_image_provider as module

    client = httpx.Client
    monkeypatch.setattr(module.socket, "getaddrinfo", lambda *args, **kwargs: [(2, 1, 6, "", ("8.8.8.8", 443))])

    def fixture_client(**kwargs):
        kwargs.pop("transport", None)
        return client(transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr(module.httpx, "Client", fixture_client)


def test_private_dns_cannot_receive_credentials(configured, monkeypatch):
    from app.services import openai_image_provider as module

    transport(monkeypatch, lambda request: pytest.fail("private DNS must not call"))
    monkeypatch.setattr(module.socket, "getaddrinfo", lambda *args, **kwargs: [(2, 1, 6, "", ("127.0.0.1", 443))])
    assert adapter().generate({"prompt": "hello"}).status == "unavailable"


def test_response_cap_stops_before_material(configured, monkeypatch):
    from app.services import openai_image_provider as module

    monkeypatch.setattr(module, "MAX_RESPONSE_BYTES", 20)
    transport(
        monkeypatch,
        lambda request: httpx.Response(200, json={"data": [{"b64_json": base64.b64encode(png()).decode()}]}),
    )
    assert adapter().generate({"prompt": "hello"}).status == "unknown"


def test_compressed_provider_body_is_rejected_before_decode(configured, monkeypatch):
    body = json.dumps({"data": [{"b64_json": base64.b64encode(png()).decode()}]}).encode()
    transport(
        monkeypatch,
        lambda request: httpx.Response(
            200, content=gzip.compress(body), headers={"content-type": "application/json", "content-encoding": "gzip"}
        ),
    )
    assert adapter().generate({"prompt": "hello"}).status == "failed"


def test_response_stream_stops_at_cap(configured, monkeypatch):
    from app.services import openai_image_provider as module

    seen = []

    class Body(httpx.SyncByteStream):
        def __iter__(self):
            for index in range(100):
                seen.append(index)
                yield b"x" * 10

    monkeypatch.setattr(module, "MAX_RESPONSE_BYTES", 20)
    transport(
        monkeypatch, lambda request: httpx.Response(200, stream=Body(), headers={"content-type": "application/json"})
    )
    assert adapter().generate({"prompt": "hello"}).status == "unknown"
    assert seen == [0, 1, 2]


def test_config_change_during_call_discards_output(configured, monkeypatch):
    def response(request):
        configured["api_key"] = "ROTATED"
        return httpx.Response(200, json={"data": [{"b64_json": base64.b64encode(png()).decode()}]})

    transport(monkeypatch, response)
    assert adapter().generate({"prompt": "hello"}).status == "unknown"


def test_loaded_native_provider_is_registered_without_probe(monkeypatch):
    from app.services.content_harness.registry import PluginRegistry

    loaded = PluginRegistry()
    monkeypatch.setattr(providers, "registry", loaded)
    monkeypatch.setattr(runtime_config, "get_runtime", lambda *args: pytest.fail("inventory must not read config"))
    providers.bootstrap_media_providers()
    assert loaded.resolve("image_provider", "image.openai", "1") is not None


def test_legacy_generate_selects_explicit_native_without_fallback(client, configured, monkeypatch):
    from app.services import provider_media

    monkeypatch.setattr(provider_media, "stage", lambda db, user, request: {"selected": request["provider_key"]})
    response = client.post("/api/v1/materials/generate", headers=EDITOR, json={"prompt": "hello"})
    assert response.status_code == 200, response.text
    assert response.json()["selected"] == "image.openai"


def test_connection_uses_prevalidated_ip_but_original_tls_host(configured, monkeypatch):
    from app.services import openai_image_provider as module

    calls = []
    monkeypatch.setattr(
        module.SyncBackend, "connect_tcp", lambda self, host, port, **kwargs: calls.append((host, port))
    )
    backend = module._PinnedBackend("images.example", "8.8.8.8")
    backend.connect_tcp("images.example", 443)
    assert calls == [("8.8.8.8", 443)]
    with pytest.raises(OSError):
        backend.connect_tcp("other.example", 443)


def test_configured_image_one_post_exact_payload_and_private_bytes(configured, monkeypatch):
    calls = []
    content = png()

    def response(request):
        calls.append(request)
        assert request.headers["authorization"] == "Bearer PRIVATE_KEY"
        assert json.loads(request.content) == {
            "model": "gpt-image-1",
            "size": "1024x1024",
            "prompt": "PRIVATE_PROMPT",
            "n": 1,
            "output_format": "png",
        }
        return httpx.Response(
            200,
            json={
                "data": [{"b64_json": base64.b64encode(content).decode(), "revised_prompt": "PRIVATE_PROVIDER"}],
                "token": "PRIVATE_RESPONSE",
            },
        )

    transport(monkeypatch, response)
    instance = adapter()
    output = instance.generate({"prompt": "PRIVATE_PROMPT", "source_bytes": [], "source_revision_ids": []})
    assert len(calls) == 1 and str(calls[0].url) == "https://images.example/v1/images/generations"
    assert output.status == "succeeded" and output.content == content and output.mime_type == "image/png"
    assert output.metadata == {}
    assert "PRIVATE" not in instance.runtime_fingerprint()


@pytest.mark.parametrize(
    "changes",
    [
        {"api_key": ""},
        {"model": ""},
        {"model": "image-01"},
        {"size": "unsupported"},
        {"base_url": "http://images.example/v1"},
        {"base_url": "https://user:secret@images.example/v1"},
        {"base_url": "https://images.example/v1?token=SECRET"},
    ],
)
def test_bad_configuration_never_calls(configured, monkeypatch, changes):
    configured.update(changes)
    transport(monkeypatch, lambda request: pytest.fail("must not call"))
    assert adapter().runtime_fingerprint() is None
    assert adapter().generate({"prompt": "hello"}).status == "unavailable"


@pytest.mark.parametrize(
    "status,body",
    [
        (307, {"data": []}),
        (500, {"secret": "PRIVATE_ERROR"}),
        (200, {"data": [{"url": "https://signed/?token=PRIVATE"}]}),
        (200, {"data": [{"b64_json": "invalid!"}]}),
        (200, {"data": []}),
        (200, {"data": [{"b64_json": "AA=="}, {"b64_json": "AA=="}]}),
    ],
)
def test_unusable_responses_no_retry_no_metadata(configured, monkeypatch, status, body):
    calls = []
    transport(
        monkeypatch,
        lambda request: (
            calls.append(request),
            httpx.Response(status, json=body, headers={"location": "https://other/"}),
        )[1],
    )
    result = adapter().generate({"prompt": "hello"})
    assert len(calls) == 1 and result.status in {"failed", "unknown"}
    assert not result.content and result.metadata == {}


def test_timeout_is_unknown_and_never_retried(configured, monkeypatch):
    calls = []

    def timeout(request):
        calls.append(True)
        raise httpx.ReadTimeout("PRIVATE_ERROR", request=request)

    transport(monkeypatch, timeout)
    assert adapter().generate({"prompt": "hello"}).status == "unknown"
    assert calls == [True]


def test_image_edit_not_silently_dropped(configured, monkeypatch):
    transport(monkeypatch, lambda request: pytest.fail("unsupported edit must not call"))
    assert (
        adapter().generate({"prompt": "hello", "source_bytes": [png()], "source_revision_ids": [1]}).status
        == "unavailable"
    )


def test_config_rotation_changes_runtime_identity(configured):
    instance = adapter()
    original = instance.runtime_fingerprint()
    assert original and len(original) == 64
    configured["api_key"] = "NEW_PRIVATE_KEY"
    assert instance.runtime_fingerprint() != original
    configured["model"] = "gpt-image-1-mini"
    assert instance.runtime_fingerprint() != original


def test_native_stage_accept_and_rotation_block(client, db_session, configured, monkeypatch, tmp_path):
    from app.services import asset_media, provider_media
    from app.services.content_harness.registry import PluginRegistry

    monkeypatch.setattr(asset_media, "MEDIA_ROOT", tmp_path)
    monkeypatch.setattr(provider_media, "_cache", {})
    loaded = PluginRegistry()
    instance = adapter()
    loaded.register("image_provider", instance.key, instance.version, instance)
    monkeypatch.setattr(providers, "registry", loaded)
    content = png()
    transport(
        monkeypatch,
        lambda request: httpx.Response(200, json={"data": [{"b64_json": base64.b64encode(content).decode()}]}),
    )
    request = {
        "provider_kind": "image_provider",
        "provider_key": instance.key,
        "provider_version": "1",
        "prompt": "PRIVATE_PROMPT",
    }
    stage = client.post("/api/v1/provider-media/stage", headers=EDITOR, json=request)
    assert stage.status_code == 200, stage.text
    assert not db_session.scalars(select(MaterialRevision)).all()
    decision = {
        "confirmed": True,
        "title": "Explicit image",
        "license_code": "provider_terms",
        "license_evidence_hash": "c" * 64,
        "public_use_allowed": True,
        "model_use_allowed": False,
        "commercial_use_allowed": False,
    }
    accepted = client.post(f"/api/v1/provider-media/{stage.json()['stage_id']}/accept", headers=EDITOR, json=decision)
    assert accepted.status_code == 201, accepted.text
    revision = db_session.get(MaterialRevision, accepted.json()["material_revision_id"])
    assert revision.content_hash == hashlib.sha256(content).hexdigest()
    assert revision.prompt_text is None and "PRIVATE" not in str(revision.metadata_json)
    next_stage = client.post("/api/v1/provider-media/stage", headers=EDITOR, json=request).json()
    configured["api_key"] = "ROTATED_PRIVATE_KEY"
    denied = client.post(f"/api/v1/provider-media/{next_stage['stage_id']}/accept", headers=EDITOR, json=decision)
    assert denied.status_code == 409
    assert len(db_session.scalars(select(MaterialRevision)).all()) == 1
