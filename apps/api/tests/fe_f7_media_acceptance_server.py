"""Explicit isolated browser fixture, never loaded by the production application."""

import io
import os
import re

assert os.environ.get("F7_ISOLATED_ACCEPTANCE") == "yes"
assert re.fullmatch(r"sqlite:////tmp/aicontent-f7-media\.[^/]+/studio\.db", os.environ.get("DATABASE_URL", ""))
assert re.fullmatch(r"/tmp/aicontent-f7-media\.[^/]+/media", os.environ.get("AI_STUDIO_MEDIA_ROOT", ""))

from PIL import Image

from app import runtime_config
from app.main import app  # noqa: F401 Uvicorn loads this module's app export.
from app.services.content_harness import providers
from app.services.content_harness.contracts import MaterialSearchResult

output = io.BytesIO()
Image.new("RGB", (32, 32), "blue").save(output, format="PNG")


class FixtureProvider:
    key = "asset_provider.wewrite_image"
    version = "1"

    def runtime_fingerprint(self):
        return "a" * 64

    def generate(self, request):
        return providers.MediaOutput("succeeded", output.getvalue(), "image/png", {"token": "fixture-secret"})


class SearchFixture:
    key = "search.wikimedia.commons"
    version = "1"

    def runtime_fingerprint(self):
        return "b" * 64

    def search(self, query, limit=10):
        return MaterialSearchResult(self.key, [{"source_id": "commons.fixture", "title": "F7 搜索候选",
            "license_code": "CC-BY-4.0", "attribution_text": "Fixture Author",
            "source_url": "https://commons.wikimedia.org/wiki/File:Fixture.png",
            "fetch_url": "https://upload.wikimedia.org/fixture.png", "mime_type": "image/png"}])

    def fetch(self, candidate):
        return providers.MediaOutput("succeeded", output.getvalue(), "image/png")


class AsrFixture:
    key = "asr.fixture"
    version = "1"

    def runtime_fingerprint(self):
        return "c" * 64

    def transcribe(self, request):
        assert request["source_bytes"].startswith(b"RIFF")
        return {"status": "succeeded", "transcript": "隔离转录字幕", "cues": [
            {"text": "隔离转录字幕", "start_ms": 0, "end_ms": 2000}], "metadata": {"token": "fixture-secret"}}


original_config = runtime_config.get_runtime


def isolated_config(key, *args, **kwargs):
    if key == runtime_config.KEY_IMAGE:
        return {"enabled": True, "provider": "isolated_fixture_not_real_provider"}
    return original_config(key, *args, **kwargs)


original_bootstrap = providers.bootstrap_media_providers


def isolated_bootstrap():
    if not providers.registry.list("image_provider"):
        providers.registry.register("image_provider", FixtureProvider.key, "1", FixtureProvider())
    if not providers.registry.list("search_provider"):
        providers.registry.register("search_provider", SearchFixture.key, "1", SearchFixture())
    if not providers.registry.list("asr_provider"):
        providers.registry.register("asr_provider", AsrFixture.key, "1", AsrFixture())
    original_bootstrap()


runtime_config.get_runtime = isolated_config
providers.bootstrap_media_providers = isolated_bootstrap
