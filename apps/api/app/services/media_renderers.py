"""Explicit media renderer probes; accepted bytes never imply a Master attestation."""

import copy
import hashlib
import io
import marshal
import re
import types
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from PIL import Image
from sqlalchemy import select, update

from ..models import (
    AuditLog,
    CapabilityRegistration,
    CapabilityVerification,
    ContentMasterAssetRef,
    ContentMasterRevision,
    MaterialRevision,
)
from . import (
    capability_integrations,
    content_masters,
    materials,
    provider_calls,
    provider_media,
    renderer_capabilities,
)
from .content_harness import channel_registry, providers
from .production_modalities import render_input_hash

_HASH = re.compile(r"[0-9a-f]{64}\Z")


def preview_inventory(user, db=None):
    from .local_graphic_renderer import LocalGraphicRenderer

    items = []
    for descriptor in providers.registry.list("renderer"):
        renderer = providers.registry.resolve("renderer", descriptor.key, descriptor.version)
        if not isinstance(renderer, LocalGraphicRenderer):
            continue
        recorded = []
        registration = db.scalar(select(CapabilityRegistration).where(CapabilityRegistration.kind == "renderer",
            CapabilityRegistration.key == renderer.key, CapabilityRegistration.version == renderer.version)) if db is not None else None
        events = db.scalars(select(CapabilityVerification).where(CapabilityVerification.registration_id == registration.id,
            CapabilityVerification.scope_kind == "renderer_output").order_by(CapabilityVerification.id.desc()).limit(100)).all() if registration else []
        seen = set()
        for event in events:
            try:
                scope = capability_integrations._scope("renderer_output", event.scope_json)
            except ValueError:
                continue
            token = tuple(scope.items())
            if token in seen:
                continue
            seen.add(token)
            if (scope["renderer_key"] != renderer.key or scope["renderer_version"] != renderer.version
                    or scope["payload_schema"] != renderer.schema or scope["modality"] != renderer.modality
                    or scope["output_mime"] not in renderer.output_mimes
                    or (scope["channel"], scope["content_form"]) not in renderer.supported_forms):
                continue
            expiry = event.expires_at.replace(tzinfo=UTC) if event.expires_at and event.expires_at.tzinfo is None else event.expires_at
            recorded.append({"verification_id": event.id, "scope": scope, "result": event.result,
                "expires_at": expiry.isoformat() if expiry else None,
                "requestable": registration.status == "configured" and event.result == "verified" and expiry is not None and expiry > datetime.now(UTC)})
        items.append({"renderer_key": renderer.key, "renderer_version": renderer.version,
            "modality": renderer.modality, "payload_schema": renderer.schema,
            "output_mimes": list(renderer.output_mimes),
            "supported_forms": [{"channel": channel, "content_form": form} for channel, form in renderer.supported_forms],
            "configuration_status": "not_probed", "verified": False, "executable": False,
            "can_probe": user.role == "admin", "recorded_scopes": recorded,
            "can_request_execution": user.role in {"admin", "editor"} and any(row["requestable"] for row in recorded),
            "reason": "admin_preview_requires_explicit_runtime"})
    return items


def _source_budget(db, master):
    ids = db.scalars(select(ContentMasterAssetRef.material_revision_id).where(
        ContentMasterAssetRef.master_revision_id == master.id, ContentMasterAssetRef.role != "render_output")).all()
    total = 0
    from .material_storage import provider as material_storage

    storage = material_storage()
    for source_id in sorted(set(ids)):
        revision = db.get(MaterialRevision, source_id)
        if revision is None:
            raise HTTPException(409, "media_renderer_source_unavailable")
        try:
            size = storage.size(revision.file_path)
        except (FileNotFoundError, OSError, ValueError):
            raise HTTPException(409, "media_renderer_source_unavailable") from None
        if total + size > 30 * 1024 * 1024:
            raise HTTPException(413, "media_renderer_input_too_large")
        try:
            content = materials.read_bytes_checked(db, revision)
        except HTTPException:
            raise HTTPException(409, "media_renderer_source_unavailable") from None
        if len(content) != size:
            raise HTTPException(409, "media_renderer_source_unavailable")
        total += size


def resolve_renderer(key, version):
    try:
        renderer = providers.registry.resolve("renderer", key, version)
        runtime = renderer.runtime_fingerprint()
        function = getattr(renderer.render_master, "__func__", renderer.render_master)
        if (renderer.key != key or renderer.version != version or renderer.modality not in {"graphic", "video"}
                or renderer.schema != f"{renderer.modality}.master.v2" or not isinstance(runtime, str)
                or not _HASH.fullmatch(runtime) or not isinstance(function, types.FunctionType)
                or not isinstance(renderer.output_mimes, tuple) or not renderer.output_mimes
                or not isinstance(renderer.supported_forms, tuple) or not renderer.supported_forms
                or any(not isinstance(form, tuple) or len(form) != 2 or any(not isinstance(part, str) or len(part) > 100 for part in form) for form in renderer.supported_forms)
                or set(renderer.output_mimes) - ({"image/png", "image/jpeg", "image/webp"} if renderer.modality == "graphic" else {"video/mp4"})):
            raise ValueError("unavailable")
        code = marshal.dumps((function.__code__, function.__defaults__, function.__kwdefaults__,
                              tuple(cell.cell_contents for cell in function.__closure__ or ())), 2)
        fingerprint = content_masters._hash({"runtime": runtime, "code": hashlib.sha256(code).hexdigest(),
            "key": key, "version": version, "schema": renderer.schema, "mimes": renderer.output_mimes,
            "forms": renderer.supported_forms})
        return renderer, fingerprint
    except Exception:  # noqa: BLE001 Never expose renderer configuration/errors.
        raise HTTPException(422, "media_renderer_unavailable") from None


def _current(db, user, origin):
    if user.role != "admin" and not (user.role == "editor" and origin.get("execution_mode") == "verified"):
        raise HTTPException(403, "media_renderer_admin_probe_required")
    project, unit = content_masters.owned_unit(db, origin["project_id"], origin["unit_id"], user, mutate=True)
    master = db.get(ContentMasterRevision, origin["master_id"])
    latest = db.scalar(select(ContentMasterRevision.id).where(ContentMasterRevision.content_unit_id == unit.id)
                       .order_by(ContentMasterRevision.revision_no.desc()).limit(1))
    if master:
        db.refresh(master)
    if (master is None or master.project_id != project.id or master.content_unit_id != unit.id or master.id != latest
            or master.payload_hash != origin["payload_hash"] or content_masters._hash(master.payload_json) != master.payload_hash
            or master.context_hash != origin["context_hash"]
            or content_masters._hash(content_masters._context(db, project, unit, content_form=master.content_form)) != master.context_hash):
        raise HTTPException(409, "media_renderer_master_changed")
    if master.modality not in {"graphic", "video"} or master.payload_schema != f"{master.modality}.master.v2":
        raise HTTPException(422, "media_renderer_schema_unavailable")
    canvas_id = origin["canvas_id"]
    if (master.modality == "graphic" and canvas_id not in [item["id"] for item in master.payload_json["canvases"]]
            or master.modality == "video" and canvas_id is not None):
        raise HTTPException(422, "media_renderer_canvas_invalid")
    try:
        profile = channel_registry.resolve_content_form(db, master.channel_id, master.content_form).to_dict()
    except channel_registry.ChannelRegistryError:
        raise HTTPException(409, "media_renderer_profile_unavailable") from None
    profile_hash = content_masters._hash(profile)
    if origin.get("profile_hash") not in {None, profile_hash}:
        raise HTTPException(409, "media_renderer_profile_changed")
    _source_budget(db, master)
    renderer_capabilities._live_refs(db, project.id, master, exclude_outputs=True)
    input_hash = render_input_hash(db, master)
    if origin.get("render_input_hash") not in {None, input_hash}:
        raise HTTPException(409, "media_renderer_input_changed")
    if origin.get("execution_mode") == "verified":
        _require_verified(db, master, origin["renderer_key"], origin["renderer_version"], origin["output_mime"])
    return master, profile_hash, input_hash


def revalidate_preview(db, user, preview, decision=None):
    master, _, _ = _current(db, user, preview.renderer_origin)
    renderer, fingerprint = resolve_renderer(preview.provider_key, preview.provider_version)
    if (renderer.schema != master.payload_schema or fingerprint != preview.runtime_hash
            or (master.channel_id, master.content_form) not in renderer.supported_forms):
        raise HTTPException(409, "media_renderer_runtime_changed")
    if decision:
        for source_id, _ in preview.sources:
            revision = db.get(MaterialRevision, source_id)
            for field in ("public_use_allowed", "model_use_allowed", "commercial_use_allowed"):
                if decision.get(field) is True and getattr(revision, field) is not True:
                    raise HTTPException(422, "media_renderer_source_rights_escalation")
            if (revision.source_metadata_json or {}).get("license_code") == "CC-BY-4.0":
                attribution = (revision.attribution_text or "").strip()
                if (decision.get("license_code") != "CC-BY-4.0" or not attribution
                        or attribution not in (decision.get("attribution_text") or "")):
                    raise HTTPException(422, "media_renderer_source_license_required")


def stage_render(db, user, project_id, unit_id, master_id, request, *, verified_execution=False):
    origin = {"project_id": project_id, "unit_id": unit_id, "master_id": master_id,
        "payload_hash": request["expected_payload_hash"], "context_hash": request["expected_context_hash"],
        "canvas_id": request["canvas_id"]}
    if verified_execution:
        origin.update({"execution_mode": "verified", "renderer_key": request["renderer_key"],
            "renderer_version": request["renderer_version"], "output_mime": request["output_mime"]})
    try:
        master, profile_hash, input_hash = _current(db, user, origin)
        renderer, fingerprint = resolve_renderer(request["renderer_key"], request["renderer_version"])
        if renderer.schema != master.payload_schema or (master.channel_id, master.content_form) not in renderer.supported_forms:
            raise HTTPException(422, "media_renderer_schema_unavailable")
        origin.update({"modality": master.modality, "profile_hash": profile_hash, "render_input_hash": input_hash})
        refs = content_masters._serialize(db, master)["assets"]
        sources = []
        seen = set()
        total = 0
        for ref in refs:
            if ref["role"] == "render_output" or ref["material_revision_id"] in seen:
                continue
            seen.add(ref["material_revision_id"])
            revision = db.get(MaterialRevision, ref["material_revision_id"])
            content = materials.read_bytes_checked(db, revision, require_public=True)
            total += len(content)
            if total > 30 * 1024 * 1024:
                raise HTTPException(413, "media_renderer_input_too_large")
            sources.append({"revision_id": revision.id, "content_hash": revision.content_hash,
                            "mime_type": revision.mime_type, "content": content})
        render_request = {"payload": copy.deepcopy({key: value for key, value in master.payload_json.items() if key != "render_asset_ref"}),
            "payload_schema": master.payload_schema, "render_input_hash": input_hash,
            "canvas_id": request["canvas_id"], "source_assets": sources, "timeout_seconds": 30,
            "channel": master.channel_id, "content_form": master.content_form, "max_output_bytes": 30 * 1024 * 1024}
        try:
            output = provider_calls.call(renderer.render_master, render_request)
        except provider_calls.ProviderCapacityError:
            raise HTTPException(429, "media_renderer_capacity") from None
        except TimeoutError:
            raise HTTPException(409, "media_renderer_outcome_unknown") from None
        except Exception:  # noqa: BLE001 Output diagnostics may contain secrets.
            raise HTTPException(502, "media_renderer_failed") from None
        if not isinstance(output, providers.MediaRenderOutput) or output.status != "succeeded":
            raise HTTPException(409, "media_renderer_outcome_unknown" if getattr(output, "status", None) == "unknown" else "media_renderer_failed")
        if output.render_input_hash != input_hash or output.canvas_id != request["canvas_id"]:
            raise HTTPException(422, "media_renderer_output_binding_invalid")
        if output.mime_type not in renderer.output_mimes:
            raise HTTPException(422, "media_renderer_output_mime_invalid")
        if verified_execution and output.mime_type != request["output_mime"]:
            raise HTTPException(422, "media_renderer_output_mime_invalid")
        provider_media._decode(output.content, output.mime_type)
        if master.modality == "graphic":
            canvas = next(item for item in master.payload_json["canvases"] if item["id"] == request["canvas_id"])
            with Image.open(io.BytesIO(output.content)) as image:
                if image.size != (canvas["width"], canvas["height"]):
                    raise HTTPException(422, "media_renderer_canvas_dimensions_invalid")
        _current(db, user, origin)
        if resolve_renderer(renderer.key, renderer.version)[1] != fingerprint:
            raise HTTPException(409, "media_renderer_runtime_changed")
        db.rollback()
        result = provider_media.stage_output(user, kind="renderer", key=renderer.key, version=renderer.version,
            runtime_hash=fingerprint, input_hash=input_hash, output=providers.MediaOutput("succeeded", output.content, output.mime_type),
            project_id=project_id, sources=tuple((item["revision_id"], item["content_hash"]) for item in sources), renderer_origin=origin)
        return result
    finally:
        # Probing retains no DB locks while a user is considering a preview.
        db.rollback()


def scope_fingerprint(db, renderer, scope):
    try:
        actual, fingerprint = resolve_renderer(scope["renderer_key"], scope["renderer_version"])
        if (actual is not renderer or scope["modality"] != renderer.modality or scope["payload_schema"] != renderer.schema
                or scope["output_mime"] not in renderer.output_mimes
                or (scope["channel"], scope["content_form"]) not in renderer.supported_forms):
            return None
        profile = channel_registry.resolve_content_form(db, scope["channel"], scope["content_form"]).to_dict()
        return content_masters._hash({"implementation": fingerprint, "scope": scope, "profile": profile})
    except (HTTPException, channel_registry.ChannelRegistryError):
        return None


def _scope(renderer, master, mime):
    return capability_integrations._scope("renderer_output", {"renderer_key": renderer.key,
        "renderer_version": renderer.version, "modality": master.modality, "payload_schema": master.payload_schema,
        "channel": master.channel_id, "content_form": master.content_form, "output_mime": mime})


def _lock_registration(db, registration):
    db.execute(update(CapabilityRegistration).where(CapabilityRegistration.id == registration.id)
        .values(status=CapabilityRegistration.status).execution_options(synchronize_session=False))
    db.refresh(registration)


def _require_verified(db, master, key, version, mime):
    renderer, _ = resolve_renderer(key, version)
    scope = _scope(renderer, master, mime)
    registration = db.scalar(select(CapabilityRegistration).where(CapabilityRegistration.kind == "renderer",
        CapabilityRegistration.key == key, CapabilityRegistration.version == version))
    if registration is not None:
        _lock_registration(db, registration)
    fingerprint = scope_fingerprint(db, renderer, scope)
    if (registration is None or fingerprint is None or not capability_integrations.is_verified_for_scope(
            db, registration, scope, fingerprint, providers.registry)):
        raise HTTPException(409, "media_renderer_scope_unverified")


def _stage_identity(preview):
    return content_masters._hash({"actor": preview.actor_id, "kind": preview.provider_kind,
        "key": preview.provider_key, "version": preview.provider_version, "runtime": preview.runtime_hash,
        "input": preview.input_hash, "hash": preview.content_hash, "actual": hashlib.sha256(preview.content).hexdigest(),
        "mime": preview.mime_type, "sources": preview.sources, "origin": preview.renderer_origin})


def verify_stage(db, user, request):
    if user.role != "admin":
        raise HTTPException(403, "media_renderer_admin_probe_required")
    if not request["confirmed"]:
        raise HTTPException(422, "media_renderer_readback_required")
    with provider_media._lock:
        preview = provider_media._get(request["stage_id"], user)
    with preview.operation_lock:
        with provider_media._lock:
            if provider_media._get(request["stage_id"], user) is not preview:
                raise HTTPException(409, "provider_preview_changed")
            identity = _stage_identity(preview)
        if (preview.provider_kind != "renderer" or not preview.renderer_origin
                or preview.input_hash != request["expected_input_hash"]
                or preview.content_hash != request["expected_output_hash"]
                or hashlib.sha256(preview.content).hexdigest() != preview.content_hash):
            raise HTTPException(409, "media_renderer_readback_mismatch")
        master, _, _ = _current(db, user, preview.renderer_origin)
        revalidate_preview(db, user, preview)
        provider_media._decode(preview.content, preview.mime_type)
        renderer, fingerprint = resolve_renderer(preview.provider_key, preview.provider_version)
        scope = _scope(renderer, master, preview.mime_type)
        scoped = scope_fingerprint(db, renderer, scope)
        if scoped is None:
            raise HTTPException(409, "media_renderer_scope_unavailable")
        registration = db.scalar(select(CapabilityRegistration).where(CapabilityRegistration.kind == "renderer",
            CapabilityRegistration.key == renderer.key, CapabilityRegistration.version == renderer.version))
        if registration is None:
            registration = CapabilityRegistration(kind="renderer", key=renderer.key, version=renderer.version,
                status="configured", config_fingerprint=fingerprint, created_by=user.email)
            db.add(registration)
            db.flush()
        else:
            _lock_registration(db, registration)
            registration.config_fingerprint, registration.status = fingerprint, "configured"
        evidence = {"kind": "render_readback", "input_hash": preview.input_hash, "output_hash": preview.content_hash}
        evidence["reference_hash"] = content_masters._hash(evidence)
        event = capability_integrations.append_verification(db, registration, scope_kind="renderer_output", scope=scope,
            result="verified", actor=user.email, evidence=evidence, config_fingerprint=scoped,
            expires_at=datetime.now(UTC) + timedelta(hours=24))
        revalidate_preview(db, user, preview)
        with provider_media._lock:
            if provider_media._get(request["stage_id"], user) is not preview or _stage_identity(preview) != identity:
                raise HTTPException(409, "provider_preview_changed")
            db.add(AuditLog(event="renderer.verification_recorded", actor=user.email, entity_type="capability_verification",
                entity_id=str(event.id), detail_json={"registration_id": registration.id, "scope": scope, "result": "verified"}))
            db.commit()
        return {"registration_id": registration.id, "verification_id": event.id, "scope": scope, "result": "verified"}


def revoke(db, user, verification_id):
    event = db.get(CapabilityVerification, verification_id)
    if event is None or event.scope_kind != "renderer_output":
        raise HTTPException(404, "renderer_verification_unavailable")
    registration = db.get(CapabilityRegistration, event.registration_id)
    _lock_registration(db, registration)
    revoked = capability_integrations.append_verification(db, registration, scope_kind="renderer_output", scope=event.scope_json,
        result="revoked", actor=user.email, evidence={"kind": "revocation"}, config_fingerprint=event.config_fingerprint)
    db.add(AuditLog(event="renderer.verification_recorded", actor=user.email, entity_type="capability_verification",
        entity_id=str(revoked.id), detail_json={"registration_id": registration.id, "scope": event.scope_json, "result": "revoked"}))
    db.commit()
    return {"registration_id": registration.id, "verification_id": revoked.id, "result": "revoked", "scope": event.scope_json}
