"""Allowlisted product inventory; never execute providers or inspect local files."""

import re
from urllib.parse import urlsplit

from sqlalchemy import func, literal, select, union_all
from sqlalchemy.orm import Session

from .. import runtime_config
from ..config import get_settings
from ..models import (
    BrandVoiceVersion,
    CapabilityRegistration,
    CapabilityVerification,
    ChannelTemplateVersion,
    Connector,
    ConnectorEndpoint,
    ContentAccount,
    ContentJob,
    ContentPersona,
    DeliveryTarget,
    DiscoverabilityProfileVersion,
    PromptVersion,
    TopicBrief,
    User,
)
from . import capability_integrations, data_source_plugins, system_settings
from .content_harness import channel_registry, rules
from .content_harness.publishers import bootstrap_publishers
from .content_harness.registry import RegistryKinds, registry
from .generation.providers import effective_llm_config

LABELS = {
    "models": "模型与 AI", "data_sources": "数据源", "channels": "渠道",
    "rules": "规则与模板", "team": "团队与权限", "advanced": "高级运行环境",
}


def _text(value) -> str:
    if not isinstance(value, str):
        return ""
    if any(ord(c) < 32 for c in value) or any(s in value.lower() for s in ("://", "password=", "token=", "api_key=", "authorization:", "/users/", "/private/", "/tmp/", "~/")):
        return ""
    return value[:200]


def _ref(value) -> str | None:
    return value if isinstance(value, str) and re.fullmatch(r"[a-zA-Z0-9_.-]{1,150}", value) else None


def _refs(value) -> list[str]:
    return [item for item in value if _ref(item)] if isinstance(value, list) else []


def _origin(value) -> str:
    # A safe view is not an editable URL snapshot: path/query/userinfo never return.
    if not isinstance(value, str) or any(ord(c) <= 32 for c in value) or any(c in value for c in ("?", "#", "\\")):
        return ""
    try:
        url = urlsplit(value)
        if url.scheme not in {"http", "https"} or not url.hostname or url.username is not None or url.password is not None:
            return ""
        host = url.hostname
        if not re.fullmatch(r"[a-zA-Z0-9.:-]+", host):
            return ""
        host = f"[{host}]" if ":" in host else host
        return f"{url.scheme}://{host}" + (f":{url.port}" if url.port else "")
    except ValueError:
        return ""


def _secret(value) -> dict:
    configured = bool(value.get("configured")) if isinstance(value, dict) else bool(value)
    return {"configured": configured, "masked": "••••" if configured else ""}


def _profile(value: dict) -> dict:
    return {
        "provider": _text(value.get("provider")), "model": _text(value.get("model")),
        "base_url": _origin(value.get("base_url")), "api_key": _secret(value.get("api_key")),
    }


def _section(key: str, data: dict, editability="read_only", reason=None) -> dict:
    result = {"key": key, "label": LABELS[key], "editability": editability, "data": data}
    if reason:
        result["reason"] = reason
    return result


def models_section(user: User) -> dict:
    llm = _profile(effective_llm_config())
    llm["overridden"] = bool(runtime_config.get_runtime(runtime_config.KEY_LLM))
    models = system_settings.models_view()
    profiles = {
        name: {**_profile(profile), "enabled": bool(profile.get("enabled"))}
        for name, profile in models["profiles"].items() if _text(name) == name
    }
    image_raw = system_settings.image_view()
    image = {
        **_profile(image_raw), "enabled": bool(image_raw["enabled"]),
        "size": _text(image_raw["size"]), "providers_available": _refs(image_raw["providers_available"]),
    }
    return _section("models", {
        "llm": llm, "models": {"profiles": profiles, "routes": {k: _text(v) for k, v in models["routes"].items()}},
        "image": image,
    }, "editable" if user.role == "admin" else "read_only")


def data_sources_section(db: Session, user: User, limit=50, offset=0) -> dict:
    plugins = []
    for item in data_source_plugins.descriptors():
        available = bool(item["available"])
        plugins.append({
            "key": _ref(item["key"]), "name": _text(item["name"]),
            "category": _ref(item["category"]), "connection_mode": _ref(item["connection_mode"]),
            "capabilities": {key: bool(item["capabilities"].get(key)) for key in ("search", "query", "snapshot")},
            "available": available, "reason": _text(item.get("reason")) or None,
            "editability": "read_only" if available else "unavailable",
        })
    endpoint_count = select(func.count(ConnectorEndpoint.id)).where(ConnectorEndpoint.connector_id == Connector.id).correlate(Connector).scalar_subquery()
    latest = select(ConnectorEndpoint.last_pull_status).where(ConnectorEndpoint.connector_id == Connector.id, ConnectorEndpoint.last_pull_at.is_not(None)).order_by(ConnectorEndpoint.last_pull_at.desc(), ConnectorEndpoint.id.desc()).limit(1).correlate(Connector).scalar_subquery()
    latest_at = select(func.max(ConnectorEndpoint.last_pull_at)).where(ConnectorEndpoint.connector_id == Connector.id).correlate(Connector).scalar_subquery()
    rows = db.execute(select(Connector.id, Connector.name, Connector.connector_type, Connector.is_active, endpoint_count.label("endpoint_count"), latest.label("last_pull_status"), latest_at.label("last_pull_at")).order_by(Connector.id.desc()).limit(limit).offset(offset))
    connectors = [{
        "id": row.id, "name": _text(row.name), "connector_type": _ref(row.connector_type),
        "is_active": bool(row.is_active), "endpoint_count": row.endpoint_count,
        "last_pull_status": row.last_pull_status if row.last_pull_status in {"ok", "failed"} else "not_recorded",
        "last_pull_at": row.last_pull_at.isoformat() if row.last_pull_at else None,
        "can_configure": user.role == "admin", "can_pull": user.role in {"admin", "editor"},
        "editability": "editable" if user.role == "admin" else "read_only",
        "pull_side_effect": "external_request_and_source_fact_write",
    } for row in rows]
    return _section("data_sources", {
        "plugins": plugins, "connectors": connectors,
        "endpoint_options": [{"id": endpoint.id, "connector_name": _text(endpoint.connector_name), "name": _text(endpoint.name),
                              "method": endpoint.method if endpoint.method in {"GET", "POST"} else "unknown"}
                             for endpoint in db.execute(select(ConnectorEndpoint.id, ConnectorEndpoint.name,
                                                               ConnectorEndpoint.method, Connector.name.label("connector_name")).join(
                                 Connector, ConnectorEndpoint.connector_id == Connector.id,
                             ).where(Connector.is_active.is_(True)).order_by(ConnectorEndpoint.id).limit(200))],
        "total": db.scalar(select(func.count()).select_from(Connector)), "limit": limit, "offset": offset,
        "can_configure": user.role == "admin", "can_pull": user.role in {"admin", "editor"},
    }, "editable" if user.role == "admin" else "read_only")


def channels_section(db: Session, user: User) -> dict:
    try:
        channels = channel_registry.list_channels(db)
    except (channel_registry.ChannelRegistryError, TypeError, ValueError):
        return _section("channels", {}, "unavailable", "Channel registry configuration is invalid")
    items = []
    for channel in channels:
        forms = []
        for form in channel["content_forms"]:
            configured_rules = _refs(form["rule_sets"])
            forms.append({
                "channel": _ref(form["channel"]), "content_form": _ref(form["content_form"]),
                "label": _text(form["label"]), "artifact_kind": _ref(form["artifact_kind"]),
                "source": _ref(form["source"]), "profile_version_id": form["profile_version_id"],
                "workflow_key": _ref(form["workflow_key"]), "renderer_key": _ref(form["renderer_key"]),
                "rule_sets": configured_rules,
                "effective_rule_sets": configured_rules or rules.rules_for_draft(db, None),
                "rule_source": "configured" if configured_rules else "legacy_fallback",
                "discoverability_profile": _ref(form["discoverability_profile"]),
                "publisher_candidates": _refs(form["publisher_candidates"]),
                "capability_state": "configured_not_verified", "verified": False,
                "editability": "read_only",
            })
        items.append({"channel": _ref(channel["channel"]), "label": _text(channel["label"]), "content_forms": forms, "editability": "read_only"})
    return _section("channels", {"items": items})


def _template_query(model, kind, name, channel, can_delete):
    return select(literal(kind).label("type"), model.id.label("id"), name.label("name"), channel.label("channel"), model.version.label("version"), model.status.label("status"), can_delete.label("can_delete"))


def rules_section(db: Session, user: User, limit=50, offset=0) -> dict:
    rules.bootstrap_rules()
    descriptors = [{
        "type": "rule", "kind": "rule", "key": _ref(d.key), "version": _text(d.version),
        "label": _text(d.label) or _ref(d.key), "human_gate": bool(d.human_gate),
        "side_effect": bool(d.side_effect), "editability": "read_only", "actions": [],
    } for d in registry.list("rule")]
    voice_unused = ~select(TopicBrief.id).where(TopicBrief.brand_voice_version_id == BrandVoiceVersion.id).exists()
    template_unused = ~select(ContentJob.id).where(ContentJob.template_version_id == ChannelTemplateVersion.id).exists()
    inventory = union_all(
        _template_query(BrandVoiceVersion, "brand_voice", BrandVoiceVersion.name, literal(None), voice_unused),
        _template_query(ChannelTemplateVersion, "channel_template", ChannelTemplateVersion.name, ChannelTemplateVersion.channel, template_unused),
        _template_query(PromptVersion, "prompt", PromptVersion.name, PromptVersion.channel, literal(True)),
        _template_query(DiscoverabilityProfileVersion, "discoverability_profile", DiscoverabilityProfileVersion.profile_key, DiscoverabilityProfileVersion.channel, literal(False)),
    ).subquery()
    items = []
    for row in db.execute(select(inventory).order_by(inventory.c.type, inventory.c.id).limit(limit).offset(offset)):
        actions = []
        if user.role == "admin":
            if row.type in {"brand_voice", "channel_template"}:
                actions.append("clone")
            if row.type != "discoverability_profile" and row.status in {"draft", "archived"}:
                actions.extend(["publish", "archive"] if row.status == "draft" else ["publish", "restore_draft"])
            if row.can_delete and row.type != "discoverability_profile" and not (row.type == "prompt" and row.status == "published"):
                actions.append("delete")
        items.append({
            "type": row.type, "id": row.id, "name": _text(row.name), "channel": _ref(row.channel),
            "version": row.version, "status": row.status if row.status in {"draft", "published", "archived"} else "unknown",
            "actions": actions, "editability": "editable" if actions else "read_only",
        })
    return _section("rules", {
        "rules": descriptors,
        "templates": {"items": items, "total": db.scalar(select(func.count()).select_from(inventory)), "limit": limit, "offset": offset},
    }, "editable" if user.role == "admin" and any(item["actions"] for item in items) else "read_only")


def _user(user) -> dict:
    return {"id": user.id, "email": _text(user.email), "name": _text(user.name), "role": user.role if user.role in {"admin", "editor", "reviewer", "viewer"} else "unknown", "is_active": bool(user.is_active)}


def team_section(db: Session, user: User) -> dict:
    rows = db.execute(select(User.id, User.email, User.name, User.role, User.is_active).order_by(User.id))
    return _section("team", {
        "current_user": _user(user), "users": [_user(row) for row in rows],
        "auth_mode": "development/header",
        "limitations": ["X-Studio-User identity is spoofable development authentication", "No production organizations, invitations, SSO or role management"],
    })


def advanced_section(user: User) -> dict:
    if user.role != "admin":
        return _section("advanced", {}, "unavailable", "Admin-only local runtime configuration")
    settings = get_settings()
    return _section("advanced", {
        "legacy_href": "/legacy/settings", "status": "not_probed",
        "can_manage": True, "runtime_editability": "read_only",
        "management_actions": ["manage_plugins", "manage_dsh"],
        "database": {"status": "not_probed"},
        "queue": {"enabled": bool(settings.task_queue_enabled), "status": "not_probed"},
        "storage": {"enabled": bool(settings.minio_enabled), "secure": bool(settings.minio_secure), "status": "not_probed"},
        "security": {"ssrf_allow_private": bool(settings.ssrf_allow_private), "upload_limit_configured": settings.upload_max_bytes > 0},
        "plugins": {"configured": bool(runtime_config.get_runtime(runtime_config.KEY_PLUGINS)), "status": "not_inspected"},
        "dsh": {"configured": bool(runtime_config.get_runtime(runtime_config.KEY_DSH)), "status": "not_inspected"},
    }, "editable")


def product_view(db: Session, user: User) -> dict:
    return {"sections": [
        models_section(user), data_sources_section(db, user), channels_section(db, user),
        rules_section(db, user), team_section(db, user), advanced_section(user),
    ]}


def capability_inventory(db: Session, user: User) -> dict:
    from . import media_renderers, renderer_capabilities
    from .content_harness import providers

    renderer_capabilities.bootstrap()
    providers.bootstrap_media_providers()
    bootstrap_publishers()
    rows = db.scalars(select(CapabilityRegistration).order_by(CapabilityRegistration.id.desc()).limit(100)).all()
    registrations = {(row.kind, row.key, row.version): row for row in rows}
    descriptors = []
    for kind in RegistryKinds:
        for descriptor in registry.list(kind):
            registration = registrations.get((kind, descriptor.key, descriptor.version))
            descriptors.append({"kind": kind, "key": _ref(descriptor.key), "version": _ref(descriptor.version),
                                "discovered": True, "configured": bool(registration and registration.status == "configured"),
                                "verified": False, "executable": False,
                                "reason": "scope_verification_required" if kind in {"publisher", "data_connector"} else "configuration_required"})
    owned_accounts = set(db.scalars(select(ContentAccount.id).join(
        ContentPersona, ContentAccount.persona_id == ContentPersona.id,
    ).where(ContentPersona.owner_user_id == user.id)).all())
    publisher_rows = [row for row in rows if row.kind == "publisher"]
    publishers = []
    for registration in publisher_rows:
        events = db.scalars(select(CapabilityVerification).where(
            CapabilityVerification.registration_id == registration.id,
            CapabilityVerification.scope_kind == "publisher_action",
        ).order_by(CapabilityVerification.id.desc()).limit(200)).all()
        seen = set()
        for event in events:
            try:
                scope = capability_integrations._scope("publisher_action", event.scope_json)
            except ValueError:
                continue
            token = tuple(scope.items())
            if scope["content_account_id"] not in owned_accounts or token in seen:
                continue
            seen.add(token)
            target = DeliveryTarget(**scope)
            verified = capability_integrations.publisher_target_verified(db, target, registry)
            publishers.append({"registration_id": registration.id, "scope": scope,
                               "configured": registration.status == "configured", "verified": verified,
                               "executable": verified, "reason": None if verified else "publisher_scope_unverified",
                               "last_verification": {"id": event.id, "result": event.result,
                                                     "verified_at": event.verified_at.isoformat(),
                                                     "expires_at": event.expires_at.isoformat() if event.expires_at else None}})
    from .capability_integrations import publisher_runtime_fingerprint

    return {"descriptors": descriptors, "publishers": publishers, "renderers": renderer_capabilities.inventory(db),
            "media_renderer_previews": media_renderers.preview_inventory(user),
            "provider_guidance": provider_guidance(registrations), "can_verify": user.role == "admin",
            "publisher_verification_available": publisher_runtime_fingerprint("publisher.wechat.wewrite", "1") is not None}


def provider_guidance(registrations: dict) -> list[dict]:
    from .content_harness import providers

    instructions = (
        ("search_provider", "公共素材搜索", "公共 Commons 无需账号密钥；需实际网络与来源校验，接受前核对许可和完整署名。"),
        ("image_provider", "图片生成", "沿用管理员模型与图片配置工具；现有 WeWrite CLI 不满足单次调用及安全配置契约，保存 CLI 配置不等于 typed Provider 可用。"),
        ("video_provider", "视频生成", "需要已加载的精确 video_provider key/version 与受控单次真实调用；当前没有独立持久配置 API，不提供保存按钮。"),
        ("tts_provider", "语音合成", "需要已加载的精确 tts_provider key/version、已配置且可核验的 runtime；接受前核对音频许可和使用权。"),
        ("asr_provider", "字幕转录", "需要已加载的精确 asr_provider key/version；在 Video Studio 对已保存、允许模型使用的精确音视频版本明确请求。"),
    )
    result = []
    for kind, label, setup in instructions:
        adapters = []
        for descriptor in providers.registry.list(kind)[:100]:
            key, version = _ref(descriptor.key), _ref(descriptor.version)
            if key is None or version is None:
                continue
            registration = registrations.get((kind, key, version))
            adapters.append({"key": key, "version": version,
                "saved_configuration": bool(registration and registration.status == "configured"),
                "configuration_status": "unchecked", "verified": False,
                "execution_status": "requires_explicit_runtime_check"})
        result.append({"kind": kind, "label": label, "setup": setup, "adapters": adapters,
            "execution_status": "requires_explicit_runtime_check" if adapters else "unavailable",
            "reason": "runtime_not_inspected" if adapters else "implementation_missing"})
    return result
