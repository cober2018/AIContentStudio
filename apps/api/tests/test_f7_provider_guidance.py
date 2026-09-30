"""Provider setup guidance is a bounded projection, not a runtime probe."""

import pytest

from app.models import CapabilityRegistration
from app.services.content_harness import providers
from app.services.content_harness.registry import PluginRegistry


@pytest.fixture
def loaded(monkeypatch):
    registry = PluginRegistry()
    class UntrustedProvider:
        def __getattr__(self, key):
            raise AssertionError("inventory cannot inspect or execute provider")
    registry.register("asr_provider", "asr.contract", "7", UntrustedProvider(), label="token=private-label")
    monkeypatch.setattr(providers, "registry", registry)
    return registry


def test_guidance_lists_exact_loaded_versions_without_calling_runtime(client, loaded):
    result = client.get("/api/v1/settings/capabilities")
    assert result.status_code == 200, result.text
    guidance = result.json()["provider_guidance"]
    assert {row["kind"] for row in guidance} == {"search_provider", "image_provider", "video_provider", "tts_provider", "asr_provider"}
    asr = next(row for row in guidance if row["kind"] == "asr_provider")
    assert asr["adapters"] == [{"key": "asr.contract", "version": "7", "saved_configuration": False,
        "configuration_status": "unchecked", "verified": False, "execution_status": "requires_explicit_runtime_check"}]
    assert "private-label" not in result.text
    video = next(row for row in guidance if row["kind"] == "video_provider")
    assert video["execution_status"] == "unavailable" and video["reason"] == "implementation_missing"


def test_saved_provider_registration_cannot_claim_runtime_availability(client, db_session, loaded):
    db_session.add(CapabilityRegistration(kind="asr_provider", key="asr.contract", version="7", status="configured", config_fingerprint="a" * 64))
    db_session.commit()
    guidance = client.get("/api/v1/settings/capabilities").json()["provider_guidance"]
    adapter = next(row for row in guidance if row["kind"] == "asr_provider")["adapters"][0]
    assert adapter["saved_configuration"] and adapter["configuration_status"] == "unchecked"
    assert not adapter["verified"] and adapter["execution_status"] != "verified"


def test_provider_guidance_caps_and_filters_untrusted_descriptor_identity(client, loaded):
    loaded.register("asr_provider", "https://unsafe.example/?token=secret", "1", object())
    for index in range(105):
        loaded.register("tts_provider", f"tts.contract.{index}", "1", object())
    result = client.get("/api/v1/settings/capabilities")
    assert "unsafe.example" not in result.text
    guidance = result.json()["provider_guidance"]
    assert len(next(row for row in guidance if row["kind"] == "tts_provider")["adapters"]) == 100
