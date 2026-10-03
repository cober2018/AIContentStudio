"""Search is bounded candidate data; only explicit byte/rights acceptance writes."""

import hashlib
import io
import json
import sys
import types

import pytest
from PIL import Image
from sqlalchemy import select

from app.models import AuditLog, MaterialRevision, ProjectMaterialReference
from app.services.content_harness import providers
from app.services.content_harness.contracts import MaterialSearchResult
from app.services.content_harness.registry import PluginRegistry

OWNER = {"X-Studio-User": "search-owner@studio.local"}
OTHER = {"X-Studio-User": "search-other@studio.local"}


def test_commons_runtime_fingerprint_survives_incidental_string_interning():
    from app.services.material_search import WikimediaSearchProvider

    provider = WikimediaSearchProvider()
    original = provider.search.__func__
    value = b"aics-commons-fingerprint-intern-regression-20261001".decode()
    code = original.__code__.replace(co_consts=original.__code__.co_consts + (value,))
    provider.search = types.MethodType(types.FunctionType(code, original.__globals__), provider)
    before = provider.runtime_fingerprint()
    sys.intern(value)
    assert provider.runtime_fingerprint() == before


@pytest.fixture
def search_provider(monkeypatch, tmp_path):
    from app.services import asset_media, material_search, provider_media

    monkeypatch.setattr(asset_media, "MEDIA_ROOT", tmp_path)
    monkeypatch.setattr(provider_media, "_cache", {})
    monkeypatch.setattr(material_search, "_cache", {})
    output = io.BytesIO()
    Image.new("RGB", (2, 2), "green").save(output, format="PNG")

    class Provider:
        key = "search.fixture"
        version = "1"
        fingerprint = "a" * 64
        content = output.getvalue()
        license_code = "CC-BY-4.0"
        downloads = 0

        def runtime_fingerprint(self):
            return self.fingerprint

        def search(self, query, limit=10):
            return MaterialSearchResult(self.key, [{"source_id": "commons.42", "title": "Example picture", "license_code": self.license_code,
                "attribution_text": "Example Author", "source_url": "https://commons.wikimedia.org/wiki/File:Example.png",
                "fetch_url": "https://upload.wikimedia.org/example.png?signature=private-fetch-secret",
                "mime_type": "image/png", "metadata": {"token": "provider-private-token"}}])

        def fetch(self, candidate):
            self.downloads += 1
            return providers.MediaOutput("succeeded", self.content, "image/png")

    loaded = PluginRegistry()
    provider = Provider()
    loaded.register("search_provider", provider.key, provider.version, provider)
    monkeypatch.setattr(providers, "registry", loaded)
    return provider


def search(client, **extra):
    return client.post("/api/v1/provider-search", headers=OWNER, json={"provider_key": "search.fixture", "provider_version": "1", "query": "test", **extra})


def test_search_preview_import_accept_keeps_exact_rights_and_project_ref(client, db_session, search_provider):
    project = client.post("/api/v1/content-projects", headers=OWNER, json={"title": "搜索项目"}).json()
    response = search(client)
    assert response.status_code == 200, response.text
    assert search_provider.downloads == 0
    assert "private-fetch-secret" not in response.text and "provider-private-token" not in response.text
    result = response.json()["items"][0]
    assert result["public_ready"] is False
    assert db_session.scalars(select(MaterialRevision)).all() == []
    stage_path = f"/api/v1/provider-search/{result['candidate_id']}/stage"
    assert client.post(stage_path, headers=OTHER, json={"project_id": project["id"]}).status_code == 404
    staged = client.post(stage_path, headers=OWNER, json={"project_id": project["id"]})
    assert staged.status_code == 200, staged.text
    assert search_provider.downloads == 1
    assert db_session.scalars(select(MaterialRevision)).all() == []
    receipt = staged.json()
    accepted = client.post(f"/api/v1/provider-media/{receipt['stage_id']}/accept", headers=OWNER, json={
        "confirmed": True, "title": "Example", "license_code": result["license_code"], "license_evidence_hash": result["license_evidence_hash"],
        "attribution_text": result["attribution_text"], "public_use_allowed": True, "model_use_allowed": True, "commercial_use_allowed": False,
    })
    assert accepted.status_code == 201, accepted.text
    revision = db_session.get(MaterialRevision, accepted.json()["material_revision_id"])
    assert revision.content_hash == hashlib.sha256(search_provider.content).hexdigest()
    assert revision.source_kind == "web_search" and revision.source_url == result["source_url"]
    assert revision.attribution_text == "Example Author"
    assert len(db_session.scalars(select(ProjectMaterialReference)).all()) == 1
    stored = json.dumps([revision.source_metadata_json, revision.metadata_json, [row.detail_json for row in db_session.scalars(select(AuditLog)).all()]])
    assert "private-fetch-secret" not in stored and "provider-private-token" not in stored


def test_accepted_search_revision_is_shared_by_text_and_video_units_with_live_rights(client, db_session, search_provider):
    project = client.post("/api/v1/content-projects", headers=OWNER, json={"title": "跨形态共享"}).json()["id"]
    candidate = search(client).json()["items"][0]
    assert candidate["public_ready"] is False
    staged = client.post(f"/api/v1/provider-search/{candidate['candidate_id']}/stage", headers=OWNER, json={"project_id": project}).json()
    assert db_session.query(MaterialRevision).count() == 0
    accepted = client.post(f"/api/v1/provider-media/{staged['stage_id']}/accept", headers=OWNER, json={
        "confirmed": True, "title": "共享原图", "license_code": candidate["license_code"], "license_evidence_hash": candidate["license_evidence_hash"],
        "attribution_text": candidate["attribution_text"], "public_use_allowed": True, "model_use_allowed": False, "commercial_use_allowed": False})
    assert accepted.status_code == 201, accepted.text
    source = db_session.get(MaterialRevision, accepted.json()["material_revision_id"])
    persona = client.post("/api/v1/content-personas", headers=OWNER, json={"name": "共享素材作者"}).json()["id"]
    saved = []
    for modality in ("text", "video"):
        unit = client.post(f"/api/v1/content-projects/{project}/units", headers=OWNER, json={"title": modality,
            "modality": modality, "persona_id": persona}).json()["id"]
        if modality == "text":
            payload = {"document": {"schema": "studio.text.document.v1", "blocks": [
                {"id": "body", "type": "paragraph", "content": [{"text": "跨形态同一精确版本", "marks": []}]},
                {"id": "shared", "type": "image", "material_revision_id": source.id}], "citations": []}}
            ref = {"role": "inline"}
        else:
            payload = {"aspect_ratio": [9, 16], "script": {"blocks": []}, "shots": [],
                "timeline": {"duration_ms": 4000, "tracks": [{"id": "visual", "order": 0, "kind": "video",
                    "items": [{"id": "shared", "order": 0, "start_ms": 0, "end_ms": 4000, "material_revision_id": source.id}]}]},
                "voice": {"mode": "none"}, "subtitles": {"cues": []}, "overlays": [], "music": {}, "cover": {}}
            ref = {"role": "timeline_media", "slot_key": "shared", "sort_order": 0, "placement": {"track_id": "visual", "item_id": "shared", "start_ms": 0, "end_ms": 4000}}
        path = f"/api/v1/content-projects/{project}/units/{unit}/master-revisions"
        response = client.post(path, headers=OWNER, json={"payload_schema": f"{modality}.master.v2", "payload": payload,
            "idempotency_key": f"shared-{modality}", "asset_refs": [{"material_revision_id": source.id, "content_hash": source.content_hash, **ref}]})
        assert response.status_code == 200, response.text
        master = response.json()
        assert master["assets"][0]["material_revision_id"] == source.id
        saved.append((path, master))
    assert db_session.query(MaterialRevision).count() == 1
    assert db_session.query(ProjectMaterialReference).count() == 1
    assert source.content_hash == hashlib.sha256(search_provider.content).hexdigest()
    source.public_use_allowed = False
    db_session.commit()
    for path, master in saved:
        response = client.post(f"{path}/{master['id']}/checks", headers=OWNER)
        assert response.status_code == 200, response.text
        rights = next(row for row in response.json()["items"] if row["check_kind"] == "rights")
        assert rights["status"] == "blocker"
        readiness = client.get(f"{path}/{master['id']}/readiness", headers=OWNER).json()
        assert readiness["candidate_freeze_available"] is False
        assert len(client.get(path, headers=OWNER).json()["items"]) == 1


@pytest.mark.parametrize("field,value", [("license_code", "CC0"), ("license_evidence_hash", "0" * 64), ("attribution_text", "another author")])
def test_search_accept_cannot_replace_observed_license_or_attribution(client, db_session, search_provider, field, value):
    result = search(client).json()["items"][0]
    receipt = client.post(f"/api/v1/provider-search/{result['candidate_id']}/stage", headers=OWNER, json={}).json()
    decision = {"confirmed": True, "title": "Example", "license_code": result["license_code"], "license_evidence_hash": result["license_evidence_hash"],
                "attribution_text": result["attribution_text"], "public_use_allowed": True, "model_use_allowed": False, "commercial_use_allowed": False, field: value}
    response = client.post(f"/api/v1/provider-media/{receipt['stage_id']}/accept", headers=OWNER, json=decision)
    assert response.status_code == 422
    assert db_session.scalars(select(MaterialRevision)).all() == []


def test_search_runtime_drift_before_download_is_no_write(client, db_session, search_provider):
    result = search(client).json()["items"][0]
    search_provider.fingerprint = "b" * 64
    response = client.post(f"/api/v1/provider-search/{result['candidate_id']}/stage", headers=OWNER, json={})
    assert response.status_code == 409
    assert search_provider.downloads == 0
    assert db_session.scalars(select(MaterialRevision)).all() == []


def test_unsupported_license_cannot_stage_as_reusable_material(client, db_session, search_provider):
    search_provider.license_code = "unknown"
    result = search(client).json()["items"][0]
    response = client.post(f"/api/v1/provider-search/{result['candidate_id']}/stage", headers=OWNER, json={})
    assert response.status_code == 422
    assert search_provider.downloads == 0
    assert db_session.scalars(select(MaterialRevision)).all() == []


def test_commons_adapter_normalizes_license_and_verifies_exact_download(monkeypatch):
    from app.services import material_search

    provider_type = getattr(material_search, "WikimediaSearchProvider", None)
    assert provider_type is not None, "real bounded Commons adapter is missing"
    image = io.BytesIO()
    Image.new("RGB", (2, 2), "green").save(image, format="PNG")
    content = image.getvalue()
    response = {"query": {"pages": [{"pageid": 42, "title": "File:Example.png", "imageinfo": [{"url": "https://upload.wikimedia.org/wikipedia/commons/a/ab/Example.png",
        "descriptionurl": "https://commons.wikimedia.org/wiki/File:Example.png", "mime": "image/png", "size": len(content),
        "sha1": hashlib.sha1(content).hexdigest(), "extmetadata": {"LicenseShortName": {"value": "CC BY 4.0"}, "Artist": {"value": "<b>Author</b>"}}}]}]}}
    calls = []

    def fetch(url, max_bytes):
        calls.append((url, max_bytes))
        return (json.dumps(response).encode(), "application/json") if "api.php" in url else (content, "image/png")

    monkeypatch.setattr(material_search, "commons_fetch", fetch)
    provider = provider_type()
    result = provider.search("example", limit=1)
    assert result.items[0]["license_code"] == "CC-BY-4.0"
    assert result.items[0]["attribution_text"] == "Author"
    assert provider.fetch(result.items[0]).content == content
    assert calls[0][1] == 1_000_000 and calls[1][1] == 5_000_000
    response["query"]["pages"][0]["imageinfo"][0]["extmetadata"]["Artist"]["value"] = "Author " * 200
    assert provider.search("example", limit=1).items == []
    bad = {**result.items[0], "source_sha1": "0" * 40}
    with pytest.raises(ValueError, match="source bytes changed"):
        provider.fetch(bad)


@pytest.mark.parametrize("url", ["https://commons.wikimedia.org/wiki/File:X.png?token=secret", "https://user:password@commons.wikimedia.org/wiki/File:X.png", "https://evil.example/wiki/File:X.png", "https://commons.wikimedia.org/wiki/File:X.png#secret"])
def test_ambiguous_citation_is_not_returned_or_stored(client, db_session, search_provider, monkeypatch, url):
    original_search = search_provider.search

    def changed(query, limit):
        result = original_search(query, limit)
        result.items[0]["source_url"] = url
        return result

    monkeypatch.setattr(search_provider, "search", changed)
    result = search(client)
    assert result.status_code == 200
    assert result.json()["items"][0]["source_url"] is None
    assert url not in result.text


@pytest.mark.parametrize("url", ["https://commons.wikimedia.org:bad/wiki/File:X.png", "https://[invalid/wiki/File:X.png"])
def test_malformed_citation_is_absent_instead_of_500(url):
    from app.services.material_search import safe_citation

    assert safe_citation(url) is None


@pytest.mark.parametrize("status,headers,content", [(302, {"location": "https://evil.example/file?token=secret"}, b""),
    (302, {"location": "http://upload.wikimedia.org/file"}, b""), (200, {}, b"x" * 101),
    (200, {"content-length": "10000000"}, b"x")])
def test_public_fetch_rejects_bad_redirect_and_streamed_body_bounds(monkeypatch, status, headers, content):
    import httpx

    from app.services import material_search

    calls = []

    def respond(request):
        calls.append(str(request.url))
        return httpx.Response(status, headers=headers, content=content)

    original = httpx.Client
    monkeypatch.setattr(material_search, "pinned_transport", lambda url: None)
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: original(timeout=10, follow_redirects=False, transport=httpx.MockTransport(respond)))
    with pytest.raises(ValueError):
        material_search.commons_fetch("https://upload.wikimedia.org/wikipedia/commons/a/test.png", 100)
    assert len(calls) == 1


@pytest.mark.parametrize("encoding", ["gzip", "br", "deflate"])
def test_commons_refuses_compression_before_body_read(monkeypatch, encoding):
    import httpx

    from app.services import material_search
    read = []
    class Body(httpx.SyncByteStream):
        def __iter__(self):
            read.append(True)
            yield b"private-compressed-body"
    real_client = httpx.Client
    def fixture_client(**kwargs):
        kwargs.pop("transport", None)
        return real_client(transport=httpx.MockTransport(
            lambda request: httpx.Response(200, stream=Body(), headers={"content-encoding": encoding})), **kwargs)
    monkeypatch.setattr(material_search.httpx, "Client", fixture_client)
    monkeypatch.setattr(material_search, "pinned_transport", lambda url: None)
    with pytest.raises(ValueError, match="compression"):
        material_search.commons_fetch("https://upload.wikimedia.org/wikipedia/commons/a/test.png", 100)
    assert not read


def test_provider_error_and_metadata_fail_closed_without_leaking_private_data(client, search_provider, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("Authorization: private-api-key")

    monkeypatch.setattr(search_provider, "search", fail)
    result = search(client)
    assert result.status_code == 502
    assert "private-api-key" not in result.text


def test_oversized_search_field_cannot_enter_cache(client, search_provider, monkeypatch):
    original = search_provider.search

    def invalid(query, limit):
        result = original(query, limit)
        result.items[0]["mime_type"] = {"raw": "x" * 1000000}
        return result

    monkeypatch.setattr(search_provider, "search", invalid)
    response = search(client)
    assert response.status_code == 422


def test_viewer_search_and_oversized_limit_have_no_provider_call(client, db_session, search_provider, monkeypatch):
    from app.models import User

    db_session.add(User(email="viewer-search@studio.local", name="Viewer", role="viewer"))
    db_session.commit()
    calls = []
    original = search_provider.search
    monkeypatch.setattr(search_provider, "search", lambda *args, **kwargs: (calls.append(True), original(*args, **kwargs))[1])
    denied = client.post("/api/v1/provider-search", headers={"X-Studio-User": "viewer-search@studio.local"}, json={"provider_key": "search.fixture", "provider_version": "1", "query": "test"})
    assert denied.status_code == 403
    assert search(client, limit=11).status_code == 422
    assert calls == []
