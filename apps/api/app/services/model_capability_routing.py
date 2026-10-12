"""Versioned capability configuration; planning never performs supplier requests."""

import copy
import hashlib
import hmac
import json
import math
import re
import secrets
from typing import Annotated, Literal
from urllib.parse import unquote, urlsplit

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictBool, ValidationError, field_validator
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError

from .. import runtime_config
from ..models import SystemSetting

Capability = Literal["chat", "image_generation", "video_generation", "tts", "asr"]
CAPABILITIES = ("chat", "image_generation", "video_generation", "tts", "asr")
Identifier = Annotated[str, Field(pattern=r"^[A-Za-z0-9_.-]{1,100}$")]
Positive = Annotated[int, Field(strict=True, ge=1, le=100_000_000)]
_PLAN_SIGNING_KEY = secrets.token_bytes(32)
TTS_APPLIED_SCHEMA = "studio.audio.tts-applied.v1"


def tts_parameters(parameters, *, capability):
    """Normalize only an explicit pair; legacy requests never acquire implicit defaults."""
    if not isinstance(parameters, dict):
        raise TypeError("tts_parameters_invalid")
    fields = {"voice_id", "rate"}.intersection(parameters)
    if not fields:
        return None
    if capability != "tts" or fields != {"voice_id", "rate"}:
        raise ValueError("tts_parameters_invalid")
    voice, rate = parameters["voice_id"], parameters["rate"]
    if (not isinstance(voice, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,149}", voice)
            or type(rate) not in {int, float} or not 0.5 <= rate <= 2 or not math.isfinite(rate)):
        raise ValueError("tts_parameters_invalid")
    return {"voice_id": voice, "rate": float(rate)}


def validate_tts_applied_parameters(value):
    if (not isinstance(value, dict) or set(value) != {"schema", "voice_id", "rate"}
            or value["schema"] != TTS_APPLIED_SCHEMA):
        raise ValueError("tts_applied_parameters_invalid")
    return {"schema": TTS_APPLIED_SCHEMA, **tts_parameters(value, capability="tts")}


def tts_parameters_supported(binding, *, probe=False):
    # A declaration on a model adapter cannot stand in for the actual media executor.
    from .content_harness.registry import RegistryError, registry
    from .minimax_cli_provider import MiniMaxCLITTSProvider

    if binding.get("adapter_key") != "minimax.cli" or binding.get("adapter_version") != "1":
        return False
    try:
        provider = registry.resolve("tts_provider", "minimax.cli", "1")
        return (type(provider) is MiniMaxCLITTSProvider
                and provider.supports_tts_parameters(binding.get("model_id"), probe=probe))
    except RegistryError:
        return False


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Binding(StrictModel):
    adapter_key: Literal["openai.compatible", "google.native", "xai.native", "minimax.native", "minimax.cli"]
    adapter_version: Literal["1"] = "1"
    model_id: Identifier
    base_url: str = Field(max_length=500)
    credential_ref: str = Field(pattern=r"^[A-Z][A-Z0-9_]{0,127}$")

    @field_validator("base_url")
    @classmethod
    def safe_base_url(cls, value):
        try:
            parsed = urlsplit(value)
            path = parsed.path
            for _ in range(8):
                decoded = unquote(path)
                if decoded == path:
                    break
                path = decoded
            if parsed.scheme == "local":
                if parsed.hostname != "mmx" or parsed.username or parsed.password or parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
                    raise ValueError("invalid_connection")
                return value.rstrip("/")
            if parsed.scheme == "http":
                host = parsed.hostname
                if (not host or parsed.username or parsed.password or parsed.query or parsed.fragment
                        or parsed.port is None or host not in {"localhost", "127.0.0.1", "::1"}):
                    raise ValueError("invalid_connection")
                return value.rstrip("/")
            if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
                    or parsed.query or parsed.fragment or parsed.port not in {None, 443}
                    or any(ord(c) <= 32 for c in value) or "\\" in value
                    or "%" in path or any(ord(c) <= 32 for c in path) or "\\" in path
                    or re.search(r"(?:token|secret|password|api[-_]?key|sk-)", path, re.IGNORECASE)):
                raise ValueError("invalid_connection")
        except ValueError as exc:
            raise ValueError("invalid_connection") from exc
        return value.rstrip("/")


class Profile(StrictModel):
    enabled: StrictBool | None = None
    declared_capabilities: list[Capability] = Field(default_factory=list, max_length=5)
    capability_bindings: dict[Capability, Binding] = Field(default_factory=dict, max_length=5)


class Plugin(StrictModel):
    enabled: StrictBool = False
    capability: Capability
    model_profile_id: Identifier
    registry_key: Identifier | None = None
    registry_version: Literal["1"] = "1"


class Limits(StrictModel):
    max_items: Positive = 1
    max_pixels: Positive | None = None
    max_seconds: Positive | None = None
    max_tokens: Positive | None = None
    timeout_seconds: Annotated[int, Field(strict=True, ge=1, le=300)] = 25
    max_cost: Annotated[float, Field(strict=True, gt=0, allow_inf_nan=False)] | None = None
    currency: Literal["USD", "CNY"] | None = None


class Policy(StrictModel):
    allow_automatic_fallback: StrictBool = False
    limits: dict[Capability, Limits] = Field(default_factory=dict, max_length=5)


class Configuration(StrictModel):
    profiles: dict[Identifier, Profile] = Field(default_factory=dict, max_length=100)
    media_plugins: dict[Identifier, Plugin] = Field(default_factory=dict, max_length=100)
    capability_routes: dict[Capability, list[Identifier]] = Field(default_factory=dict, max_length=5)
    policies: Policy = Field(default_factory=Policy)
    voice_catalog: list[dict] = Field(default_factory=list, max_length=2000)


def validate_configuration(value, *, trusted_voice_catalog: bool = False):
    try:
        result = Configuration.model_validate(value).model_dump(mode="json")
    except ValidationError as exc:
        # ValidationError includes raw input; API diagnostics must not echo connections.
        raise HTTPException(422, "capability_configuration_invalid") from exc
    for profile in result["profiles"].values():
        declared = profile["declared_capabilities"]
        if len(declared) != len(set(declared)) or set(profile["capability_bindings"]) - set(declared):
            raise HTTPException(422, "capability_declaration_invalid")
    for plugin in result["media_plugins"].values():
        target = result["profiles"].get(plugin["model_profile_id"])
        if target is None or plugin["capability"] not in target["capability_bindings"]:
            raise HTTPException(422, "plugin_binding_missing")
        binding = target["capability_bindings"][plugin["capability"]]
        if plugin["registry_key"] not in {None, binding["adapter_key"]} or plugin["registry_version"] != binding["adapter_version"]:
            raise HTTPException(422, "plugin_executor_mismatch")
        plugin["registry_key"] = binding["adapter_key"]
    for capability, ids in result["capability_routes"].items():
        if len(ids) > 20 or len(ids) != len(set(ids)):
            raise HTTPException(422, "capability_route_invalid")
        if any(key not in result["media_plugins"] or result["media_plugins"][key]["capability"] != capability for key in ids):
            raise HTTPException(422, "capability_route_invalid")
        limit = result["policies"]["limits"].get(capability)
        if ids and result["policies"]["allow_automatic_fallback"] and not _bounded(capability, limit):
            raise HTTPException(422, "capability_limit_required")
    from .multimedia_generation import voice_catalog_projection

    result["voice_catalog"] = voice_catalog_projection(result.get("voice_catalog", []),
                                                       trusted_verified=trusted_voice_catalog)
    return result


def _bounded(capability, limit):
    if not limit:
        return False
    field = {"chat": "max_tokens", "image_generation": "max_pixels", "video_generation": "max_seconds", "tts": "max_seconds", "asr": "max_seconds"}[capability]
    return limit.get(field) is not None


def _stored(db):
    row = db.scalar(select(SystemSetting).where(SystemSetting.key == "models").execution_options(populate_existing=True))
    return copy.deepcopy(row.value) if row else {}


def _binding_state(binding, capability, enabled, *, _for_execution=False):
    if not enabled:
        return {"executable": False, "reason": "profile_disabled", "runtime_hash": None}
    if binding is None:
        return {"executable": False, "reason": "binding_not_configured", "runtime_hash": None}
    from .content_harness.registry import RegistryError, registry

    try:
        adapter = registry.resolve("model_provider", binding["adapter_key"], binding["adapter_version"])
    except RegistryError:
        return {"executable": False, "reason": "adapter_not_loaded", "runtime_hash": None}
    try:
        if adapter.key != binding["adapter_key"] or adapter.version != binding["adapter_version"]:
            raise ValueError("adapter_identity_invalid")
        method = adapter.binding_state
        if _for_execution:
            method = getattr(adapter, "execution_binding_state", method)
        state = method(capability, copy.deepcopy(binding))
        runtime_hash = state.get("runtime_hash")
        valid_runtime = isinstance(runtime_hash, str) and re.fullmatch(r"[0-9a-f]{64}", runtime_hash) is not None
        ready = state.get("reason") is None and valid_runtime
        reason = state.get("reason")
        if reason is not None and reason not in {"credential_not_configured", "credential_continuity_unverified", "adapter_capability_unsupported", "model_operation_unsupported", "connection_unavailable"}:
            reason = "adapter_runtime_unavailable"
        return {"executable": bool(ready), "reason": None if ready else reason,
            "runtime_hash": runtime_hash if valid_runtime and (ready or reason == "credential_continuity_unverified") else None}
    except Exception:  # noqa: BLE001 Adapter diagnostics may contain credentials.
        return {"executable": False, "reason": "adapter_runtime_unavailable", "runtime_hash": None}


def configuration_view(db):
    stored = _stored(db)
    profiles = {}
    for key, profile in (stored.get("profiles") or {}).items():
        declarations = [cap for cap in profile.get("declared_capabilities", ["chat"]) if cap in CAPABILITIES]
        bindings = {}
        for capability, raw in profile.get("capability_bindings", {}).items():
            if capability not in CAPABILITIES:
                continue
            try:
                bindings[capability] = Binding.model_validate(raw).model_dump(mode="json")
            except ValidationError:
                continue
        profiles[key] = {
            "enabled": profile.get("enabled", True) is True,
            "declared_capabilities": declarations,
            "capability_bindings": copy.deepcopy(bindings),
            "capabilities": {cap: {"declared": cap in declarations, "configured": cap in bindings,
                                   "verified": False, **_binding_state(bindings.get(cap) if cap in declarations else None, cap, profile.get("enabled", True) is True)}
                             for cap in CAPABILITIES},
        }
        profiles[key]["multimedia_controls"] = {
            cap: _multimedia_controls(binding, cap) for cap, binding in bindings.items()
            if cap in {"image_generation", "tts"}
        }
    plugins = {}
    for key, raw in stored.get("media_plugins", {}).items():
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", key) or not isinstance(raw, dict):
            continue
        try:
            plugins[key] = Plugin.model_validate({name: raw[name] for name in Plugin.model_fields if name in raw}).model_dump(mode="json")
        except ValidationError:
            continue
    routes = {cap: [key for key in ids if isinstance(key, str) and key in plugins][:20]
              for cap, ids in stored.get("capability_routes", {}).items() if cap in CAPABILITIES and isinstance(ids, list)}
    raw_policy = stored.get("policies", {})
    limits = {}
    for cap, raw in raw_policy.get("limits", {}).items():
        if cap not in CAPABILITIES or not isinstance(raw, dict):
            continue
        try:
            limits[cap] = Limits.model_validate({name: raw[name] for name in Limits.model_fields if name in raw}).model_dump(mode="json")
        except ValidationError:
            continue
    from .multimedia_generation import voice_preset_projection

    voice_catalog = []
    for item in stored.get("voice_catalog", []):
        try:
            voice_catalog.append(voice_preset_projection(item, trusted_verified=True))
        except HTTPException:
            continue
    return {"schema_version": stored.get("schema_version", 1), "revision": stored.get("revision", 0),
            "profiles": profiles, "media_plugins": plugins, "capability_routes": routes,
            "policies": {"allow_automatic_fallback": raw_policy.get("allow_automatic_fallback") is True, "limits": limits},
            "voice_catalog": voice_catalog}


def save_configuration(db, value, *, expected_revision, actor):
    if type(expected_revision) is not int or expected_revision < 0:
        raise HTTPException(422, "configuration_revision_invalid")
    config = validate_configuration(value)
    with runtime_config.configuration_guard():
        stored = _stored(db)
        if stored.get("revision", 0) != expected_revision:
            raise HTTPException(409, "configuration_revision_conflict")
        if "voice_catalog" not in value:
            config.pop("voice_catalog", None)
        else:
            _preserve_voice_evidence(config["voice_catalog"], stored.get("voice_catalog", []))
        profiles = copy.deepcopy(stored.get("profiles", {}))
        for key, profile in config["profiles"].items():
            if profile["enabled"] is None:
                profile.pop("enabled")
            profiles[key] = {**profiles.get(key, {}), **profile}
        merged = {**stored, **config, "profiles": profiles, "schema_version": 2, "revision": expected_revision + 1}
        commit_configuration(db, merged, expected_revision=expected_revision, actor=actor)
        return configuration_view(db)


def save_voice_catalog(db, value, *, expected_revision, actor):
    """Persist a secret-free local voice inventory without contacting a provider."""
    if type(expected_revision) is not int or expected_revision < 0 or not isinstance(value, list) or len(value) > 2000:
        raise HTTPException(422, "voice_catalog_invalid")
    from .multimedia_generation import voice_catalog_projection

    catalog = voice_catalog_projection(value)
    with runtime_config.configuration_guard():
        stored = _stored(db)
        if stored.get("revision", 0) != expected_revision:
            raise HTTPException(409, "configuration_revision_conflict")
        _preserve_voice_evidence(catalog, stored.get("voice_catalog", []))
        merged = {**stored, "voice_catalog": catalog, "schema_version": 2, "revision": expected_revision + 1}
        commit_configuration(db, merged, expected_revision=expected_revision, actor=actor)
        return configuration_view(db)


def refresh_voice_catalog(db, *, actor):
    """Refresh voice metadata only on an explicit admin action.

    This intentionally performs no retry and never runs from configuration reads
    or route planning. Provider failures return the existing local inventory.
    """
    stored = _stored(db)
    existing = []
    from .multimedia_generation import voice_preset_projection

    for item in stored.get("voice_catalog", []):
        try:
            existing.append(voice_preset_projection(item, trusted_verified=True))
        except HTTPException:
            continue
    discovered: list[dict] = []
    try:
        from .content_harness.registry import registry
        from .minimax_cli_provider import MiniMaxCLITTSProvider

        provider = registry.resolve("tts_provider", "minimax.cli", "1")
        if type(provider) is MiniMaxCLITTSProvider:
            seen = {}
            for profile_id, profile in (stored.get("profiles") or {}).items():
                binding = (profile.get("capability_bindings") or {}).get("tts") if isinstance(profile, dict) else None
                model_id = binding.get("model_id") if isinstance(binding, dict) and binding.get("adapter_key") == "minimax.cli" and binding.get("adapter_version") == "1" else None
                if not isinstance(model_id, str) or profile.get("enabled") is False:
                    continue
                if model_id not in seen:
                    seen[model_id] = provider.list_voices(model_id=model_id)
                for item in seen[model_id]:
                    try:
                        discovered.append(voice_preset_projection({**item,
                            "id": f"{profile_id}.{item['voice_id']}", "profile_id": profile_id}, trusted_verified=True))
                    except (HTTPException, KeyError, TypeError):
                        continue
    except Exception:  # noqa: BLE001 Explicit refresh reports a bounded unavailable result.
        discovered = []
    by_key = {(item["provider_key"], item["provider_version"], item["model_id"], item["profile_id"], item["voice_id"]): item
              for item in existing}
    for item in discovered:
        key = (item["provider_key"], item["provider_version"], item["model_id"], item["profile_id"], item["voice_id"])
        previous = by_key.get(key)
        by_key[key] = {**item, **({field: previous[field] for field in ("id", "label", "tags", "favorite", "preview_ref", "rate")}
                                  if previous else {})}
    revision = stored.get("revision", 0)
    if discovered:
        if len(by_key) > 2000:
            raise HTTPException(422, "voice_catalog_invalid")
        merged = {**stored, "voice_catalog": list(by_key.values()), "schema_version": 2, "revision": revision + 1}
        commit_configuration(db, merged, expected_revision=revision, actor=actor)
        result = configuration_view(db)
        result["voice_catalog_refresh"] = {"status": "updated", "count": len(discovered)}
        return result
    result = configuration_view(db)
    result["voice_catalog_refresh"] = {"status": "unchanged", "count": len(existing),
                                        "reason": "voice_catalog_provider_unavailable"}
    return result


def _preserve_voice_evidence(catalog, existing):
    fields = ("id", "provider_key", "provider_version", "model_id", "profile_id", "voice_id")
    verified = {tuple(item.get(field) for field in fields) for item in existing
                if isinstance(item, dict) and item.get("verified") is True}
    for item in catalog:
        item["verified"] = tuple(item[field] for field in fields) in verified


def commit_configuration(db, merged, *, expected_revision, actor):
    runtime_config.validate_persisted_configuration(merged)
    with runtime_config.configuration_guard():
        try:
            if db.get(SystemSetting, "models") is not None:
                changed = db.execute(update(SystemSetting).where(
                    SystemSetting.key == "models",
                    func.coalesce(SystemSetting.value["revision"].as_integer(), 0) == expected_revision,
                ).values(value=merged, updated_by=actor).execution_options(synchronize_session=False))
                if changed.rowcount != 1:
                    db.rollback()
                    raise HTTPException(409, "configuration_revision_conflict")
            else:
                db.add(SystemSetting(key="models", value=merged, updated_by=actor))
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(409, "configuration_revision_conflict") from exc
        # Publish only committed configuration, never a transaction that may roll back.
        runtime_config.set_runtime("models", merged)
        from .generation.providers import reset_provider_cache

        reset_provider_cache()


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def _native_batch_supported(capability: str, adapter_key: str, adapter_version: str) -> bool:
    """Read the registered adapter contract without probing the provider."""
    if capability != "image_generation":
        return False
    from .content_harness.providers import registry

    try:
        provider_kind = {"image_generation": "image_provider"}[capability]
        provider = registry.resolve(provider_kind, adapter_key, adapter_version)
    except Exception:  # noqa: BLE001 Registry lookup must not expose provider diagnostics.
        return False
    return callable(getattr(provider, "generate_batch", None))


def _multimedia_controls(binding, capability):
    if capability == "image_generation" and binding["adapter_key"] == "openai.compatible":
        return {"supported_fields": ["items", "pixels", "aspect_ratio", "timeout_seconds"],
                "candidate_counts": [1, 2, 3, 4], "reference_images": False,
                "native_batch": _native_batch_supported(capability, binding["adapter_key"], binding["adapter_version"])}
    if capability == "image_generation" and binding["adapter_key"] == "minimax.cli":
        return {"supported_fields": ["items", "pixels", "aspect_ratio", "timeout_seconds"],
                "candidate_counts": [1, 2, 3, 4], "reference_images": False,
                "native_batch": _native_batch_supported(capability, binding["adapter_key"], binding["adapter_version"])}
    if capability == "tts" and tts_parameters_supported(binding):
        return {"supported_fields": ["items", "seconds", "timeout_seconds", "voice_id", "rate"],
                "candidate_counts": [1], "voice_catalog": True}
    return {"supported_fields": [], "candidate_counts": [1], "reference_images": False}


def plan(db, *, capability, selected_profile, parameters=None, explicit_plugin=None,
         explicit_profile=None, input_hash=None, source_refs=None, configuration_mode="auto",
         _for_execution=False):
    if capability not in CAPABILITIES:
        raise HTTPException(422, "capability_unknown")
    if configuration_mode not in {"auto", "custom"}:
        # Composed stages resolve their declared chain before calling this planner.
        raise HTTPException(422, "multimedia_configuration_mode_invalid")
    view = configuration_view(db)
    params = copy.deepcopy(parameters or {})
    refs = copy.deepcopy(source_refs or [])
    if explicit_profile and explicit_plugin:
        raise HTTPException(422, "explicit_binding_ambiguous")
    if input_hash is not None and (not isinstance(input_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", input_hash)):
        raise HTTPException(422, "plan_input_hash_invalid")
    if (not isinstance(refs, list) or len(refs) > 20 or any(
        not isinstance(ref, dict) or set(ref) != {"revision_id", "content_hash"}
        or type(ref["revision_id"]) is not int or ref["revision_id"] < 1
        or not isinstance(ref["content_hash"], str) or not re.fullmatch(r"[0-9a-f]{64}", ref["content_hash"])
        for ref in refs
    )):
        raise HTTPException(422, "plan_source_refs_invalid")
    if not isinstance(params, dict) or set(params) - {"items", "pixels", "seconds", "tokens", "timeout_seconds", "aspect_ratio", "voice_id", "rate"}:
        raise HTTPException(422, "plan_parameters_invalid")
    if capability == "image_generation":
        from .multimedia_generation import normalize_parameters

        params = normalize_parameters(capability, params)
    elif capability == "tts":
        if set(params) - {"items", "seconds", "timeout_seconds", "voice_id", "rate"}:
            raise HTTPException(422, "multimedia_parameters_unsupported")
        if type(params.get("items", 1)) is not int or params.get("items", 1) != 1:
            raise HTTPException(422, "multimedia_audio_single_output_required")
    try:
        spoken_parameters = tts_parameters(params, capability=capability)
    except (TypeError, ValueError):
        raise HTTPException(422, "plan_tts_parameters_invalid") from None
    if spoken_parameters is not None:
        params.update(spoken_parameters)
    if "aspect_ratio" in params:
        from .media_dimensions import canonical_aspect_ratio

        if capability != "image_generation":
            raise HTTPException(422, "plan_aspect_ratio_unsupported")
        try:
            params["aspect_ratio"] = canonical_aspect_ratio(params["aspect_ratio"])
        except ValueError:
            raise HTTPException(422, "plan_aspect_ratio_unsupported") from None
    result = {"status": "blocked", "reason": "binding_not_configured", "configuration_revision": view["revision"],
              "required_capability": capability, "selected_profile": selected_profile,
              "execution_profile": selected_profile, "plugin_id": None}
    selected = view["profiles"].get(selected_profile)
    unavailable = "selected_profile_missing" if selected is None else "profile_disabled" if not selected["enabled"] else None
    if unavailable and not (explicit_profile or explicit_plugin) and not view["policies"].get("allow_automatic_fallback"):
        result["reason"] = unavailable
        return result
    limits = view["policies"].get("limits", {}).get(capability)
    if not _bounded(capability, limits):
        result["reason"] = "capability_limit_required"
        return result
    for name, ceiling in (("items", "max_items"), ("pixels", "max_pixels"), ("seconds", "max_seconds"), ("tokens", "max_tokens"), ("timeout_seconds", "timeout_seconds")):
        if name in params and (type(params[name]) is not int or params[name] < 1 or limits.get(ceiling) is None or params[name] > limits[ceiling]):
            result["reason"] = "capability_limit_exceeded"
            return result
    if limits.get("max_cost") is not None:
        result["reason"] = "cost_bound_unverified"
        return result
    quantity = {"chat": "tokens", "image_generation": "pixels", "video_generation": "seconds", "tts": "seconds", "asr": "seconds"}[capability]
    params.setdefault("items", 1)
    params.setdefault(quantity, limits[{"tokens": "max_tokens", "pixels": "max_pixels", "seconds": "max_seconds"}[quantity]])
    params.setdefault("timeout_seconds", limits["timeout_seconds"])

    states = {}

    def state_for(profile_id):
        if profile_id not in states:
            target = view["profiles"][profile_id]
            state = target["capabilities"][capability]
            # Only explicit execution checks the requested capability's route,
            # never credentials for unrelated profiles or capability families.
            states[profile_id] = _binding_state(target["capability_bindings"].get(capability), capability,
                target["enabled"], _for_execution=True) if _for_execution and state["declared"] else state
        return states[profile_id]

    def choose(profile_id, plugin_id, route_reason):
        target = view["profiles"].get(profile_id)
        if target is None:
            result["reason"] = "execution_profile_missing"
            return False
        state = state_for(profile_id)
        result.update(execution_profile=profile_id, plugin_id=plugin_id, reason=state["reason"])
        if not state["executable"]:
            return False
        binding = target["capability_bindings"][capability]
        if (capability == "image_generation" and "aspect_ratio" in params
                and "aspect_ratio" not in _multimedia_controls(binding, capability)["supported_fields"]):
            result["reason"] = "multimedia_parameters_unsupported"
            return False
        if capability == "image_generation" and binding["adapter_key"] == "minimax.cli" and refs:
            result["reason"] = "multimedia_reference_images_unsupported"
            return False
        candidate_mode = "single"
        if capability == "image_generation" and params.get("items", 1) > 1:
            candidate_mode = ("native" if _native_batch_supported(capability, binding["adapter_key"],
                                                                   binding["adapter_version"]) else "fan_out")
            if candidate_mode == "fan_out" and configuration_mode == "custom":
                result["reason"] = "multimedia_custom_batch_requires_declared_composition"
                return False
            if candidate_mode == "fan_out":
                from .content_harness.registry import RegistryError, registry

                try:
                    adapter = registry.resolve("image_provider", binding["adapter_key"], binding["adapter_version"])
                except RegistryError:
                    adapter = None
                if getattr(adapter, "supports_candidate_fan_out", False) is not True:
                    result["reason"] = "multimedia_candidate_fan_out_unavailable"
                    return False
        if spoken_parameters is not None and not tts_parameters_supported(binding, probe=_for_execution):
            result["reason"] = "tts_parameters_unsupported"
            return False
        if spoken_parameters is not None and view.get("voice_catalog"):
            voice = spoken_parameters["voice_id"]
            exact = next((item for item in view["voice_catalog"]
                          if item["provider_key"] == binding["adapter_key"]
                          and item["provider_version"] == binding["adapter_version"]
                          and item["model_id"] == binding["model_id"]
                          and item["voice_id"] == voice
                          and item["profile_id"] == profile_id), None)
            if exact is None:
                result["reason"] = "voice_catalog_binding_unavailable"
                return False
        result.update(status="ready", reason=None, route_reason=route_reason,
                      adapter_key=binding["adapter_key"], adapter_version=binding["adapter_version"],
                      model_id=binding["model_id"], runtime_hash=state["runtime_hash"],
                      binding_hash=_hash(binding), parameters=params, limits=copy.deepcopy(limits),
                      input_hash=input_hash, source_refs=refs, explicit_profile=explicit_profile,
                      explicit_plugin=explicit_plugin, configuration_mode=configuration_mode,
                      dispatch_ready=input_hash is not None)
        if capability in {"image_generation", "tts"}:
            from .multimedia_generation import digest

            result["multimedia"] = {
                "schema": "studio.multimedia.request.v1", "capability": capability,
                "parameters": copy.deepcopy(params),
                "candidate_count": params.get("items", 1),
                "candidate_mode": candidate_mode,
                "configuration_mode": configuration_mode,
                "binding": {"adapter_key": binding["adapter_key"], "adapter_version": binding["adapter_version"],
                            "model_id": binding["model_id"], "profile_id": profile_id},
            }
            result["multimedia"]["config_hash"] = digest(result["multimedia"])
        if spoken_parameters is not None:
            result["voice_binding"] = {"voice_id": spoken_parameters["voice_id"], "rate": spoken_parameters["rate"],
                                        "provider_key": binding["adapter_key"], "provider_version": binding["adapter_version"],
                                        "model_id": binding["model_id"], "profile_id": profile_id}
        result["plan_hash"] = _hash(result)
        result["plan_signature"] = hmac.new(_PLAN_SIGNING_KEY, result["plan_hash"].encode(), hashlib.sha256).hexdigest()
        return True

    if explicit_profile:
        choose(explicit_profile, None, "explicit_workflow_binding")
        return result
    if configuration_mode == "custom" and not explicit_plugin:
        choose(selected_profile, None, "selected_model_binding")
        return result
    if explicit_plugin:
        candidates = [explicit_plugin]
    else:
        selected_state = state_for(selected_profile) if unavailable is None else None
        if selected_state is not None and selected_state["executable"]:
            choose(selected_profile, None, "selected_model_binding")
            return result
        if not view["policies"].get("allow_automatic_fallback"):
            result["reason"] = selected_state["reason"] if selected["capabilities"][capability]["configured"] else "automatic_fallback_not_authorized"
            return result
        candidates = view["capability_routes"].get(capability, [])
    for plugin_id in candidates:
        plugin = view["media_plugins"].get(plugin_id)
        if not plugin or not plugin["enabled"] or plugin["capability"] != capability:
            if explicit_plugin:
                result["reason"] = "explicit_plugin_unavailable"
                return result
            continue
        target = view["profiles"].get(plugin["model_profile_id"], {})
        binding = target.get("capability_bindings", {}).get(capability)
        if not binding or plugin.get("registry_key") not in {None, binding["adapter_key"]} or plugin["registry_version"] != binding["adapter_version"]:
            result["reason"] = "plugin_executor_mismatch"
            if explicit_plugin:
                return result
            continue
        if choose(plugin["model_profile_id"], plugin_id, "explicit_plugin_binding" if explicit_plugin else "authorized_plugin_fallback") or explicit_plugin:
            return result
    if result["plugin_id"] is None:
        result["reason"] = "capability_plugin_unavailable"
    return result


def revalidate_plan(db, frozen):
    if not isinstance(frozen, dict) or frozen.get("status") != "ready" or not frozen.get("dispatch_ready"):
        raise HTTPException(409, "execution_plan_unavailable")
    unsigned = {key: value for key, value in frozen.items() if key not in {"plan_hash", "plan_signature"}}
    if _hash(unsigned) != frozen.get("plan_hash"):
        raise HTTPException(409, "execution_plan_corrupt")
    signature = hmac.new(_PLAN_SIGNING_KEY, frozen["plan_hash"].encode(), hashlib.sha256).hexdigest()
    if not isinstance(frozen.get("plan_signature"), str) or not hmac.compare_digest(signature, frozen["plan_signature"]):
        raise HTTPException(409, "execution_plan_signature_invalid")
    current = plan(db, capability=frozen["required_capability"], selected_profile=frozen["selected_profile"],
                   parameters=frozen["parameters"], explicit_profile=frozen["explicit_profile"],
                   explicit_plugin=frozen["explicit_plugin"], input_hash=frozen["input_hash"], source_refs=frozen["source_refs"],
                   configuration_mode=frozen.get("configuration_mode", "auto"), _for_execution=True)
    if current.get("plan_hash") != frozen["plan_hash"]:
        raise HTTPException(409, "execution_plan_stale")
    return current
