"""Model capability configuration stays distinct from supplier verification."""

import copy

import pytest

from app.models import SystemSetting


@pytest.fixture(autouse=True)
def isolated_runtime(monkeypatch):
    from app import runtime_config

    monkeypatch.setattr(runtime_config, "_OVERRIDES", {})


def config():
    return {
        "profiles": {
            "writer": {"declared_capabilities": ["chat"], "capability_bindings": {}},
            "illustrator": {
                "declared_capabilities": ["image_generation"],
                "capability_bindings": {"image_generation": {
                    "adapter_key": "google.native", "adapter_version": "1", "model_id": "configured-image-model",
                    "base_url": "https://generativelanguage.googleapis.com", "credential_ref": "AICS_GOOGLE_KEY",
                }},
            },
        },
        "media_plugins": {"cover": {"enabled": True, "capability": "image_generation", "model_profile_id": "illustrator"}},
        "capability_routes": {"image_generation": ["cover"]},
        "policies": {"allow_automatic_fallback": True, "limits": {"image_generation": {"max_items": 1, "max_pixels": 1048576, "timeout_seconds": 25}}},
    }


def test_declared_configuration_never_implies_verification_or_executable(db_session):
    from app.services import model_capability_routing as routing

    result = routing.save_configuration(db_session, config(), expected_revision=0, actor="admin")
    assert result["revision"] == 1
    image = result["profiles"]["illustrator"]["capabilities"]["image_generation"]
    assert image["declared"] and image["configured"]
    assert image["verified"] is False and image["executable"] is False
    assert image["reason"] == "adapter_not_loaded"


def test_atomic_revision_conflict_and_preserve_legacy(db_session):
    from app.services import model_capability_routing as routing

    db_session.add(SystemSetting(key="models", value={"profiles": {"writer": {"provider": "openai_compatible", "api_key": "private-original", "model": "old-model"}}, "routes": {"rewrite": "writer"}}))
    db_session.commit()
    routing.save_configuration(db_session, config(), expected_revision=0, actor="admin")
    with pytest.raises(Exception) as error:
        routing.save_configuration(db_session, config(), expected_revision=0, actor="other")
    assert error.value.status_code == 409
    stored = db_session.get(SystemSetting, "models").value
    assert stored["revision"] == 1
    assert stored["profiles"]["writer"]["api_key"] == "private-original"
    assert stored["routes"] == {"rewrite": "writer"}
    assert "private-original" not in str(routing.configuration_view(db_session))


@pytest.mark.parametrize("mutation", ["unknown_capability", "dangling_plugin", "unknown_adapter", "credential_url", "masked_secret", "unbounded", "false_boolean"])
def test_invalid_configuration_has_no_partial_writes(db_session, mutation):
    from app.services import model_capability_routing as routing

    value = config()
    if mutation == "unknown_capability":
        value["profiles"]["writer"]["declared_capabilities"] = ["image_understanding"]
    elif mutation == "dangling_plugin":
        value["media_plugins"]["cover"]["model_profile_id"] = "missing"
    elif mutation == "unknown_adapter":
        value["profiles"]["illustrator"]["capability_bindings"]["image_generation"]["adapter_key"] = "run.random.script"
    elif mutation == "credential_url":
        value["profiles"]["illustrator"]["capability_bindings"]["image_generation"]["base_url"] = "https://host.test/?token=private"
    elif mutation == "masked_secret":
        value["profiles"]["illustrator"]["capability_bindings"]["image_generation"]["credential_ref"] = "••••"
    elif mutation == "unbounded":
        value["policies"]["limits"] = {}
    else:
        value["policies"]["allow_automatic_fallback"] = "true"
    with pytest.raises(Exception) as error:
        routing.save_configuration(db_session, value, expected_revision=0, actor="admin")
    assert error.value.status_code == 422
    assert db_session.get(SystemSetting, "models") is None


def test_route_preview_reports_missing_adapter_without_a_request(db_session):
    from app.services import model_capability_routing as routing

    routing.save_configuration(db_session, config(), expected_revision=0, actor="admin")
    result = routing.plan(db_session, capability="image_generation", selected_profile="writer", parameters={"items": 1, "pixels": 1048576})
    assert result["status"] == "blocked"
    assert result["reason"] == "adapter_not_loaded"
    assert result["selected_profile"] == "writer"
    assert result["plugin_id"] == "cover"
    assert result["execution_profile"] == "illustrator"
    assert "AICS_GOOGLE_KEY" not in str(result)


def test_settings_api_roles_and_unknown_extra_fields(client, db_session):
    from app.models import User

    db_session.add(User(email="admin@studio.local", name="Admin", role="admin"))
    db_session.commit()
    saved = client.put("/api/v1/settings/model-capabilities", headers={"X-Studio-User": "admin@studio.local"}, json={"expected_revision": 0, "configuration": config()})
    assert saved.status_code == 200, saved.text

    db_session.add(User(email="viewer-route@test.local", name="Viewer", role="viewer"))
    db_session.commit()
    forbidden = client.put("/api/v1/settings/model-capabilities", headers={"X-Studio-User": "viewer-route@test.local"}, json={"expected_revision": 1, "configuration": config()})
    assert forbidden.status_code == 403
    value = copy.deepcopy(config())
    value["profiles"]["writer"]["api_key"] = "must-not-be-accepted"
    invalid = client.put("/api/v1/settings/model-capabilities", json={"expected_revision": 1, "configuration": value})
    assert invalid.status_code == 422


def test_missing_supplier_credentials_are_not_an_execution_claim(db_session):
    from app.services import model_capability_routing as routing

    routing.save_configuration(db_session, config(), expected_revision=0, actor="admin")
    view = routing.configuration_view(db_session)
    assert all(not state["verified"] for profile in view["profiles"].values() for state in profile["capabilities"].values())


def test_existing_empty_setting_is_upgradable(db_session):
    from app.services import model_capability_routing as routing

    db_session.add(SystemSetting(key="models", value={}))
    db_session.commit()
    assert routing.save_configuration(db_session, config(), expected_revision=0, actor="admin")["revision"] == 1


def test_old_models_writer_cannot_remove_capability_configuration(client, db_session):
    from app.models import User
    from app.services import model_capability_routing as routing

    db_session.add(User(email="admin@studio.local", name="Admin", role="admin"))
    db_session.commit()
    routing.save_configuration(db_session, config(), expected_revision=0, actor="admin")
    response = client.put("/api/v1/settings/models", json={"profiles": [{"name": "writer", "provider": "mock"}], "routes": {}})
    assert response.status_code == 409
    assert db_session.get(SystemSetting, "models").value["revision"] == 1
    assert db_session.get(SystemSetting, "models").value["media_plugins"]["cover"]["enabled"] is True


def test_limit_exceeded_or_unpriced_money_blocks_planning(db_session):
    from app.services import model_capability_routing as routing

    routing.save_configuration(db_session, config(), expected_revision=0, actor="admin")
    result = routing.plan(db_session, capability="image_generation", selected_profile="writer", parameters={"items": 2})
    assert result["reason"] == "capability_limit_exceeded"
    value = config()
    value["policies"]["limits"]["image_generation"].update(max_cost=1.0, currency="USD")
    routing.save_configuration(db_session, value, expected_revision=1, actor="admin")
    result = routing.plan(db_session, capability="image_generation", selected_profile="writer")
    assert result["reason"] == "cost_bound_unverified"


def test_media_only_profile_cannot_enter_legacy_chat_route(db_session):
    from app import runtime_config
    from app.services import model_capability_routing as routing
    from app.services.generation.providers import LLMError, effective_llm_config

    routing.save_configuration(db_session, config(), expected_revision=0, actor="admin")
    value = runtime_config.get_runtime("models")
    value["routes"] = {"generate": "illustrator"}
    runtime_config.set_runtime("models", value)
    with pytest.raises(LLMError, match="chat_capability_unavailable"):
        effective_llm_config("generate")


def test_invalid_stored_binding_is_not_serialized(db_session):
    from app.services import model_capability_routing as routing

    db_session.add(SystemSetting(key="models", value={"profiles": {"legacy": {"capability_bindings": {"image_generation": {"api_key": "secret-in-legacy-field"}}}}}))
    db_session.commit()
    assert "secret-in-legacy-field" not in str(routing.configuration_view(db_session))


@pytest.mark.parametrize("path", ["/%74oken/private", "/%2574oken/private"])
def test_encoded_secret_paths_are_rejected(db_session, path):
    from app.services import model_capability_routing as routing

    value = config()
    value["profiles"]["illustrator"]["capability_bindings"]["image_generation"]["base_url"] = "https://host.test" + path
    with pytest.raises(Exception) as error:
        routing.save_configuration(db_session, value, expected_revision=0, actor="admin")
    assert error.value.status_code == 422


def test_stored_metadata_uses_only_safe_schema_fields(db_session):
    from app.services import model_capability_routing as routing

    value = config()
    value["media_plugins"]["cover"]["raw_output"] = "private-metadata"
    value["policies"]["api_key"] = "private-metadata"
    value["capability_routes"]["unknown"] = ["private-metadata"]
    db_session.add(SystemSetting(key="models", value=value))
    db_session.commit()
    assert "private-metadata" not in str(routing.configuration_view(db_session))


def test_legacy_writer_atomically_rechecks_upgrade_after_read(db_session, monkeypatch):
    from sqlalchemy import update

    from app.services.system_settings import save_models

    db_session.add(SystemSetting(key="models", value={"profiles": {}}))
    db_session.commit()
    original = db_session.scalar

    def upgrade_after_read(statement, *args, **kwargs):
        row = original(statement, *args, **kwargs)
        db_session.connection().execute(update(SystemSetting).where(SystemSetting.key == "models").values(value={"schema_version": 2, "revision": 1}))
        return row

    monkeypatch.setattr(db_session, "scalar", upgrade_after_read)
    with pytest.raises(Exception) as error:
        save_models(db_session, {"profiles": {}}, "admin")
    assert error.value.status_code == 409


def test_legacy_save_advances_head_so_pending_upgrade_conflicts(db_session):
    from app.services import model_capability_routing as routing
    from app.services.system_settings import save_models

    db_session.add(SystemSetting(key="models", value={"profiles": {"writer": {"model": "before"}}}))
    db_session.commit()
    observed_revision = routing.configuration_view(db_session)["revision"]
    save_models(db_session, {"profiles": {"writer": {"model": "new-legacy-value"}}}, "admin")
    db_session.commit()
    with pytest.raises(Exception) as error:
        routing.save_configuration(db_session, config(), expected_revision=observed_revision, actor="admin")
    assert error.value.status_code == 409
    assert db_session.get(SystemSetting, "models").value["profiles"]["writer"]["model"] == "new-legacy-value"


def test_empty_route_can_remove_its_limits(db_session):
    from app.services import model_capability_routing as routing

    value = config()
    value["capability_routes"]["image_generation"] = []
    value["policies"]["limits"] = {}
    saved = routing.save_configuration(db_session, value, expected_revision=0, actor="admin")
    assert saved["capability_routes"]["image_generation"] == []


@pytest.fixture
def loaded_image_adapter(monkeypatch):
    from app.services.content_harness import registry as registry_module

    registry = registry_module.PluginRegistry()

    class ImageAdapter:
        key = "google.native"
        version = "1"

        def binding_state(self, capability, binding):
            return {"reason": None if capability == "image_generation" else "adapter_capability_unsupported",
                    "runtime_hash": "a" * 64 if capability == "image_generation" else None}

    registry.register("model_provider", "google.native", "1", ImageAdapter())
    monkeypatch.setattr(registry_module, "registry", registry)


def test_shared_resolver_selects_real_plugin_and_freezes_hashes(db_session, loaded_image_adapter):
    from app.services import model_capability_routing as routing

    routing.save_configuration(db_session, config(), expected_revision=0, actor="admin")
    first = routing.plan(db_session, capability="image_generation", selected_profile="writer", parameters={"items": 1, "pixels": 1024}, input_hash="b" * 64, source_refs=[{"revision_id": 1, "content_hash": "c" * 64}])
    second = routing.plan(db_session, capability="image_generation", selected_profile="writer", parameters={"items": 1, "pixels": 1024}, input_hash="b" * 64, source_refs=[{"revision_id": 1, "content_hash": "c" * 64}])
    assert first["status"] == "ready"
    assert first["plugin_id"] == "cover" and first["execution_profile"] == "illustrator"
    assert first["plan_hash"] == second["plan_hash"]
    assert first["runtime_hash"] == "a" * 64
    assert "AICS_GOOGLE_KEY" not in str(first)


def test_explicit_binding_never_falls_back(db_session, loaded_image_adapter):
    from app.services import model_capability_routing as routing

    routing.save_configuration(db_session, config(), expected_revision=0, actor="admin")
    result = routing.plan(db_session, capability="image_generation", selected_profile="writer", explicit_profile="writer", parameters={"pixels": 1024})
    assert result["status"] == "blocked"
    assert result["plugin_id"] is None


def test_stale_frozen_plan_rejected_before_execution(db_session, loaded_image_adapter):
    from app.services import model_capability_routing as routing

    routing.save_configuration(db_session, config(), expected_revision=0, actor="admin")
    planned = routing.plan(db_session, capability="image_generation", selected_profile="writer", parameters={"pixels": 1024}, input_hash="b" * 64)
    routing.save_configuration(db_session, config(), expected_revision=1, actor="admin")
    with pytest.raises(Exception) as error:
        routing.revalidate_plan(db_session, planned)
    assert error.value.status_code == 409


def test_disabled_profile_not_executable(db_session, loaded_image_adapter):
    from app.services import model_capability_routing as routing

    value = config()
    value["profiles"]["illustrator"]["enabled"] = False
    routing.save_configuration(db_session, value, expected_revision=0, actor="admin")
    result = routing.plan(db_session, capability="image_generation", selected_profile="writer", parameters={"pixels": 1024})
    assert result["status"] == "blocked"
    assert result["reason"] == "profile_disabled"


def test_viewer_can_read_safe_inventory_but_cannot_edit(client, db_session):
    from app.models import User
    from app.services import model_capability_routing as routing

    db_session.add(User(email="routing-viewer@test.local", name="Viewer", role="viewer"))
    db_session.commit()
    routing.save_configuration(db_session, config(), expected_revision=0, actor="admin")
    headers = {"X-Studio-User": "routing-viewer@test.local"}
    response = client.get("/api/v1/settings/model-capabilities", headers=headers)
    assert response.status_code == 200
    assert "api_key" not in response.text
    assert client.put("/api/v1/settings/model-capabilities", headers=headers, json={"expected_revision": 1, "configuration": config()}).status_code == 403


def test_plan_tampering_and_runtime_rotation_are_rejected(db_session, loaded_image_adapter, monkeypatch):
    from app.services import model_capability_routing as routing
    from app.services.content_harness.registry import registry

    routing.save_configuration(db_session, config(), expected_revision=0, actor="admin")
    planned = routing.plan(db_session, capability="image_generation", selected_profile="writer", parameters={"pixels": 1024}, input_hash="b" * 64)
    tampered = copy.deepcopy(planned)
    tampered["parameters"]["pixels"] += 1
    with pytest.raises(Exception) as error:
        routing.revalidate_plan(db_session, tampered)
    assert error.value.detail == "execution_plan_corrupt"
    adapter = registry.resolve("model_provider", "google.native", "1")
    monkeypatch.setattr(adapter, "binding_state", lambda *_args: {"reason": None, "runtime_hash": "d" * 64})
    with pytest.raises(Exception) as error:
        routing.revalidate_plan(db_session, planned)
    assert error.value.detail == "execution_plan_stale"


@pytest.mark.parametrize("selected", ["missing", "disabled"])
def test_explicit_executable_binding_precedes_selected_profile(db_session, loaded_image_adapter, selected):
    from app.services import model_capability_routing as routing

    value = config()
    value["profiles"]["disabled"] = {"enabled": False, "declared_capabilities": [], "capability_bindings": {}}
    routing.save_configuration(db_session, value, expected_revision=0, actor="admin")
    planned = routing.plan(db_session, capability="image_generation", selected_profile=selected, explicit_profile="illustrator", parameters={"pixels": 1024}, input_hash="b" * 64)
    assert planned["status"] == "ready"
    assert planned["execution_profile"] == "illustrator"


def test_recomputed_public_hash_cannot_forge_frozen_plan(db_session, loaded_image_adapter):
    from app.services import model_capability_routing as routing

    routing.save_configuration(db_session, config(), expected_revision=0, actor="admin")
    planned = routing.plan(db_session, capability="image_generation", selected_profile="writer", parameters={"pixels": 1024}, input_hash="b" * 64)
    forged = copy.deepcopy(planned)
    forged["input_hash"] = "f" * 64
    forged["plan_hash"] = routing._hash({key: value for key, value in forged.items() if key not in {"plan_hash", "plan_signature"}})
    with pytest.raises(Exception) as error:
        routing.revalidate_plan(db_session, forged)
    assert error.value.status_code == 409


@pytest.fixture
def multimedia_registry(monkeypatch):
    from app.services.content_harness import providers
    from app.services.content_harness import registry as registry_module
    from app.services.content_harness.registry import PluginRegistry
    from app.services.minimax_cli_provider import MiniMaxCLITTSProvider

    loaded = PluginRegistry()

    class ModelAdapter:
        key, version = "minimax.cli", "1"

        def binding_state(self, capability, binding):
            return {"runtime_hash": "a" * 64, "reason": None}

    class NativeImage:
        def generate_batch(self, request):
            pytest.fail("planning must not generate images")

    speech = MiniMaxCLITTSProvider()
    monkeypatch.setattr(speech, "supports_tts_parameters", lambda model, probe=False: model == "speech-2.8-hd")
    monkeypatch.setattr(speech, "list_voices", lambda **kwargs: pytest.fail("reads must not refresh voices"))
    loaded.register("model_provider", "minimax.cli", "1", ModelAdapter())
    loaded.register("image_provider", "minimax.cli", "1", NativeImage())
    loaded.register("tts_provider", "minimax.cli", "1", speech)
    monkeypatch.setattr(registry_module, "registry", loaded)
    monkeypatch.setattr(providers, "registry", loaded)
    return loaded, speech


def multimedia_config():
    value = config()
    value["profiles"]["illustrator"]["capability_bindings"]["image_generation"] = {
        "adapter_key": "minimax.cli", "adapter_version": "1", "model_id": "image-01",
        "base_url": "local://mmx", "credential_ref": "MEDIA_TEST_KEY",
    }
    for profile in ("speaker", "alternate"):
        value["profiles"][profile] = {"declared_capabilities": ["tts"], "capability_bindings": {"tts": {
            "adapter_key": "minimax.cli", "adapter_version": "1", "model_id": "speech-2.8-hd",
            "base_url": "local://mmx", "credential_ref": "MEDIA_TEST_KEY",
        }}}
    value["policies"]["limits"]["image_generation"]["max_items"] = 4
    value["policies"]["limits"]["tts"] = {"max_items": 1, "max_seconds": 360, "timeout_seconds": 120}
    value["voice_catalog"] = [voice_entry()]
    return value


def voice_entry(**overrides):
    return {"id": "speaker.voice-a", "label": "Local voice", "provider_key": "minimax.cli",
            "provider_version": "1", "model_id": "speech-2.8-hd", "profile_id": "speaker",
            "voice_id": "voice-a", "language": "Chinese", "favorite": True,
            "verified": True, "rate": 1.0, **overrides}


@pytest.mark.parametrize("count", [1, 2, 3, 4])
def test_native_image_count_is_frozen_without_dispatch(db_session, multimedia_registry, count):
    from app.services import model_capability_routing as routing

    routing.save_configuration(db_session, multimedia_config(), expected_revision=0, actor="admin")
    planned = routing.plan(db_session, capability="image_generation", selected_profile="illustrator",
                           parameters={"items": count}, input_hash="b" * 64, configuration_mode="custom")
    assert planned["status"] == "ready"
    assert planned["multimedia"]["candidate_count"] == count
    assert planned["multimedia"]["candidate_mode"] == ("native" if count > 1 else "single")
    assert routing.revalidate_plan(db_session, planned) == planned


@pytest.mark.parametrize("count", [0, 5, True, "4", 2.5])
def test_image_candidate_count_rejected_before_execution(db_session, multimedia_registry, count):
    from fastapi import HTTPException

    from app.services import model_capability_routing as routing

    routing.save_configuration(db_session, multimedia_config(), expected_revision=0, actor="admin")
    before = copy.deepcopy(db_session.get(SystemSetting, "models").value)
    with pytest.raises(HTTPException) as exc:
        routing.plan(db_session, capability="image_generation", selected_profile="illustrator",
                     parameters={"items": count}, input_hash="b" * 64)
    assert exc.value.status_code == 422
    assert db_session.get(SystemSetting, "models").value == before


def test_single_image_custom_cannot_fan_out(db_session, multimedia_registry, monkeypatch):
    from app.services import model_capability_routing as routing

    loaded, _speech = multimedia_registry
    image = loaded.resolve("image_provider", "minimax.cli", "1")
    monkeypatch.delattr(type(image), "generate_batch")
    monkeypatch.setattr(image, "supports_candidate_fan_out", True, raising=False)
    routing.save_configuration(db_session, multimedia_config(), expected_revision=0, actor="admin")
    custom = routing.plan(db_session, capability="image_generation", selected_profile="illustrator",
                          parameters={"items": 4}, configuration_mode="custom")
    assert custom["status"] == "blocked"
    assert custom["reason"] == "multimedia_custom_batch_requires_declared_composition"
    auto = routing.plan(db_session, capability="image_generation", selected_profile="illustrator",
                        parameters={"items": 4})
    assert auto["status"] == "ready" and auto["multimedia"]["candidate_mode"] == "fan_out"


@pytest.mark.parametrize("selected", ["missing", "writer", "disabled"])
def test_custom_image_pin_never_uses_available_plugin(db_session, multimedia_registry, selected):
    from app.services import model_capability_routing as routing

    configuration = multimedia_config()
    configuration["profiles"]["disabled"] = {**configuration["profiles"]["illustrator"], "enabled": False}
    routing.save_configuration(db_session, configuration, expected_revision=0, actor="admin")
    planned = routing.plan(db_session, capability="image_generation", selected_profile=selected,
                           parameters={"items": 4}, configuration_mode="custom")
    assert planned["status"] == "blocked" and planned["plugin_id"] is None
    assert planned["execution_profile"] == selected


def test_audio_batch_cannot_reuse_image_candidate_contract(db_session, multimedia_registry):
    from fastapi import HTTPException

    from app.services import model_capability_routing as routing

    routing.save_configuration(db_session, multimedia_config(), expected_revision=0, actor="admin")
    with pytest.raises(HTTPException) as exc:
        routing.plan(db_session, capability="tts", selected_profile="speaker",
                     parameters={"items": 4, "voice_id": "voice-a", "rate": 1.0})
    assert exc.value.status_code == 422 and exc.value.detail == "multimedia_audio_single_output_required"


@pytest.mark.parametrize("field,value", [("profile_id", "alternate"), ("model_id", "speech-02-hd"),
                                         ("provider_version", "2"), ("voice_id", "voice-b")])
def test_voice_catalog_matches_exact_execution_scope(db_session, multimedia_registry, field, value):
    from app.services import model_capability_routing as routing

    configuration = multimedia_config()
    configuration["voice_catalog"][0][field] = value
    routing.save_configuration(db_session, configuration, expected_revision=0, actor="admin")
    result = routing.plan(db_session, capability="tts", selected_profile="speaker",
                          parameters={"voice_id": "voice-a", "rate": 1.0})
    assert result["status"] == "blocked" and result["reason"] == "voice_catalog_binding_unavailable"


def test_manual_voice_registration_cannot_forge_verification(db_session, multimedia_registry):
    from app.services import model_capability_routing as routing

    saved = routing.save_configuration(db_session, multimedia_config(), expected_revision=0, actor="admin")
    assert saved["voice_catalog"][0]["verified"] is False
    new_voice = voice_entry(id="speaker.clone", voice_id="my-clone", verified=True)
    view = routing.save_voice_catalog(db_session, [new_voice], expected_revision=1, actor="admin")
    assert view["voice_catalog"][0]["voice_id"] == "my-clone"
    assert view["voice_catalog"][0]["verified"] is False


def test_catalog_removal_invalidates_frozen_voice_plan(db_session, multimedia_registry):
    from fastapi import HTTPException

    from app.services import model_capability_routing as routing

    configuration = multimedia_config()
    configuration["voice_catalog"].append(voice_entry(id="speaker.voice-b", voice_id="voice-b"))
    routing.save_configuration(db_session, configuration, expected_revision=0, actor="admin")
    planned = routing.plan(db_session, capability="tts", selected_profile="speaker",
                           parameters={"voice_id": "voice-a", "rate": 1.0}, input_hash="b" * 64)
    assert planned["status"] == "ready"
    routing.save_voice_catalog(db_session, [configuration["voice_catalog"][1]], expected_revision=1, actor="admin")
    with pytest.raises(HTTPException) as exc:
        routing.revalidate_plan(db_session, planned)
    assert exc.value.status_code == 409 and exc.value.detail == "execution_plan_stale"


def test_catalog_refresh_preserves_preferences_and_deduplicates_model_reads(db_session, multimedia_registry, monkeypatch):
    from sqlalchemy import func, select

    from app.models import MaterialRevision, ProviderGenerationTask
    from app.services import model_capability_routing as routing

    _loaded, speech = multimedia_registry
    calls = []

    def list_voices(*, model_id):
        calls.append(model_id)
        return [voice_entry(label="Provider label", verified=True)]

    monkeypatch.setattr(speech, "list_voices", list_voices)
    routing.save_configuration(db_session, multimedia_config(), expected_revision=0, actor="admin")
    view = routing.refresh_voice_catalog(db_session, actor="admin")
    assert calls == ["speech-2.8-hd"]
    assert view["revision"] == 2 and view["voice_catalog_refresh"]["status"] == "updated"
    exact = next(item for item in view["voice_catalog"] if item["profile_id"] == "speaker")
    assert exact["favorite"] and exact["label"] == "Local voice" and exact["verified"]
    assert {item["profile_id"] for item in view["voice_catalog"]} == {"speaker", "alternate"}
    assert db_session.scalar(select(func.count()).select_from(ProviderGenerationTask)) == 0
    assert db_session.scalar(select(func.count()).select_from(MaterialRevision)) == 0


def test_failed_catalog_refresh_preserves_inventory_without_secrets(db_session, multimedia_registry, monkeypatch):
    from app.services import model_capability_routing as routing

    _loaded, speech = multimedia_registry

    def unavailable(**kwargs):
        raise RuntimeError("api_key=never-expose-provider-diagnostic")

    monkeypatch.setattr(speech, "list_voices", unavailable)
    routing.save_configuration(db_session, multimedia_config(), expected_revision=0, actor="admin")
    before = copy.deepcopy(db_session.get(SystemSetting, "models").value)
    view = routing.refresh_voice_catalog(db_session, actor="admin")
    assert view["revision"] == 1 and view["voice_catalog_refresh"]["status"] == "unchanged"
    assert db_session.get(SystemSetting, "models").value == before
    assert "never-expose" not in str(view)


def test_voice_catalog_compare_and_swap_keeps_newer_inventory(db_session, multimedia_registry):
    from fastapi import HTTPException

    from app.services import model_capability_routing as routing

    routing.save_configuration(db_session, multimedia_config(), expected_revision=0, actor="admin")
    with pytest.raises(HTTPException) as exc:
        routing.save_voice_catalog(db_session, [], expected_revision=0, actor="admin")
    assert exc.value.status_code == 409 and exc.value.detail == "configuration_revision_conflict"
    assert len(routing.configuration_view(db_session)["voice_catalog"]) == 1
