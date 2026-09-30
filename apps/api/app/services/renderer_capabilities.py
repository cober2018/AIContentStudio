"""Exact Production render descriptors and explicit deterministic readback."""

import hashlib
import marshal
import sys
import types
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import select, update

from ..models import (
    AuditLog,
    CapabilityRegistration,
    CapabilityVerification,
    ContentMasterRevision,
    FactPack,
    FactPackItem,
    Material,
    MaterialRevision,
    ProjectFactBoundaryRevision,
    ProjectMaterialReference,
    ProjectWorkflowOutput,
)
from . import capability_integrations, content_masters, production_modalities, text_documents
from .content_harness import channel_registry
from .content_harness.registry import RegistryError, registry


def code_fingerprint():
    parts = [str(sys.version_info[:3]).encode()]
    for module in (sys.modules[__name__], production_modalities, text_documents, channel_registry, content_masters):
        for name, value in sorted(vars(module).items()):
            if isinstance(value, types.FunctionType) and value.__module__ == module.__name__:
                # Reference-tracking marshal versions change when runtime strings are interned.
                parts.extend((name.encode(), marshal.dumps(value.__code__, 2)))
            elif isinstance(value, type) and value.__module__ == module.__name__:
                for method_name, method in sorted(vars(value).items()):
                    if isinstance(method, types.FunctionType):
                        parts.extend((method_name.encode(), marshal.dumps(method.__code__, 2)))
    return hashlib.sha256(b"".join(parts)).hexdigest()


class ProductionRenderer:
    def __init__(self, schema):
        self.schema = schema
        self.modality = schema.split(".")[0]
        self.version = schema[-1]
        self.mode = "deterministic" if self.modality == "text" else "manual"
        self.key = ("text.markdown.v1" if self.version == "1" else "text.studio.document.v1") if self.modality == "text" else f"manual.{schema}"
        self.output_mimes = ("text/markdown",) if self.modality == "text" else ("image/png", "image/jpeg", "image/webp") if self.modality == "graphic" else ("video/mp4",)

    def supports_scope(self, scope):
        return (scope["renderer_key"] == self.key and scope["renderer_version"] == self.version
                and scope["modality"] == self.modality and scope["payload_schema"] == self.schema
                and scope["output_mime"] in self.output_mimes)

    def render_master(self, db, master):
        if self.mode != "deterministic" or master.payload_schema != self.schema:
            raise HTTPException(422, "automatic_renderer_unavailable")
        result = production_modalities.adapter_for(self.modality, self.schema).build_render_snapshot(db, master)
        if result.get("status") != "ready" or result.get("origin") != "deterministic":
            raise HTTPException(409, "renderer_input_not_ready")
        return result


def bootstrap():
    for modality in ("text", "graphic", "video"):
        for version in (1, 2):
            renderer = ProductionRenderer(f"{modality}.master.v{version}")
            if not any(item.key == renderer.key and item.version == renderer.version for item in registry.list("renderer")):
                registry.register("renderer", renderer.key, renderer.version, renderer, label=renderer.key)


def implementation_fingerprint(renderer):
    adapter = production_modalities.adapter_for(renderer.modality, renderer.schema)
    execution = {}
    for owner, names in ((renderer, ("render_master", "supports_scope")), (adapter, ("build_render_snapshot", "validate_payload"))):
        for name in names:
            function = getattr(owner, name, None)
            function = getattr(function, "__func__", function)
            if not isinstance(function, types.FunctionType):
                return None
            try:
                closure = tuple(cell.cell_contents for cell in function.__closure__ or ())
                identity = (function.__code__, function.__defaults__, function.__kwdefaults__, closure)
                execution[f"{type(owner).__module__}.{type(owner).__qualname__}.{name}"] = hashlib.sha256(marshal.dumps(identity, 2)).hexdigest()
            except (ValueError, TypeError):
                return None
    return content_masters._hash({"code": code_fingerprint(), "execution": execution,
        "mode": renderer.mode, "schema": renderer.schema, "output_mimes": renderer.output_mimes})


def runtime_fingerprint(db, renderer, scope):
    if not renderer.supports_scope(scope):
        return None
    try:
        profile = channel_registry.resolve_content_form(db, scope["channel"], scope["content_form"]).to_dict()
    except channel_registry.ChannelRegistryError:
        return None
    implementation = implementation_fingerprint(renderer)
    if implementation is None:
        return None
    return content_masters._hash({"implementation": implementation, "scope": scope, "profile": profile})


def _live_refs(db, project_id, master):
    boundary = db.get(ProjectFactBoundaryRevision, master.fact_boundary_revision_id) if master.fact_boundary_revision_id else None
    if boundary:
        db.execute(update(FactPack).where(FactPack.id == boundary.fact_pack_id).values(status=FactPack.status).execution_options(synchronize_session=False))
        db.scalar(select(FactPack).where(FactPack.id == boundary.fact_pack_id).execution_options(populate_existing=True))
        for item_id in db.scalars(select(FactPackItem.id).where(FactPackItem.fact_pack_id == boundary.fact_pack_id).order_by(FactPackItem.id)).all():
            db.execute(update(FactPackItem).where(FactPackItem.id == item_id).values(public_use_allowed=FactPackItem.public_use_allowed).execution_options(synchronize_session=False))
        db.scalars(select(FactPackItem).where(FactPackItem.fact_pack_id == boundary.fact_pack_id).execution_options(populate_existing=True)).all()
    assets = content_masters._serialize(db, master)["assets"]
    for source_id in sorted({ref["material_revision_id"] for ref in assets}):
        db.execute(update(MaterialRevision).where(MaterialRevision.id == source_id).values(status=MaterialRevision.status).execution_options(synchronize_session=False))
    material_ids = db.scalars(select(MaterialRevision.material_id).where(MaterialRevision.id.in_([ref["material_revision_id"] for ref in assets]))).all()
    for material_id in sorted(set(material_ids)):
        db.execute(update(Material).where(Material.id == material_id).values(status=Material.status).execution_options(synchronize_session=False))
    for ref in assets:
        material = db.scalar(select(MaterialRevision).where(MaterialRevision.id == ref["material_revision_id"]).execution_options(populate_existing=True))
        if material is None:
            raise HTTPException(409, "renderer_source_unavailable")
        db.refresh(material.material)
        visible = db.scalar(select(ProjectMaterialReference.id).where(ProjectMaterialReference.project_id == project_id,
            ProjectMaterialReference.material_revision_id == material.id, ProjectMaterialReference.status == "active"))
        outputs = db.scalars(select(ProjectWorkflowOutput).where(ProjectWorkflowOutput.project_id == project_id,
            ProjectWorkflowOutput.output_kind == "material_revision", ProjectWorkflowOutput.entity_id == material.id)).all()
        if visible is None and not any(content_masters._verified_generated_asset(db, output, material) for output in outputs):
            raise HTTPException(409, "renderer_source_unavailable")
    if content_masters._rights_check(db, {"assets": assets, "edit_summary": master.edit_summary_json or {}})[0] != "pass":
        raise HTTPException(409, "renderer_source_rights_unavailable")
    if content_masters._serialize(db, master)["evidence"] and content_masters._evidence_check(db, master)[0] != "pass":
        raise HTTPException(409, "renderer_evidence_unavailable")


def probe(db, user, request):
    project_id, unit_id = request["project_id"], request["unit_id"]
    project, unit = content_masters.owned_unit(db, project_id, unit_id, user, mutate=True)
    master = db.get(ContentMasterRevision, request["master_id"])
    if master is None or master.project_id != project_id or master.content_unit_id != unit_id:
        raise HTTPException(404, "renderer_master_unavailable")
    bootstrap()
    try:
        renderer = registry.resolve("renderer", request["renderer_key"], request["renderer_version"])
    except RegistryError:
        raise HTTPException(422, "renderer_unavailable") from None
    if not isinstance(renderer, ProductionRenderer) or renderer.mode != "deterministic" or renderer.schema != master.payload_schema:
        raise HTTPException(422, "automatic_renderer_unavailable")
    if not master.channel_id or not master.content_form:
        raise HTTPException(409, "renderer_channel_form_required")
    scope = capability_integrations._scope("renderer_output", {"renderer_key": renderer.key, "renderer_version": renderer.version,
        "modality": master.modality, "payload_schema": master.payload_schema, "channel": master.channel_id,
        "content_form": master.content_form, "output_mime": "text/markdown"})
    fingerprint = runtime_fingerprint(db, renderer, scope)
    if fingerprint is None:
        raise HTTPException(409, "renderer_scope_unavailable")
    registration = db.scalar(select(CapabilityRegistration).where(CapabilityRegistration.kind == "renderer", CapabilityRegistration.key == renderer.key, CapabilityRegistration.version == renderer.version))
    result = request.get("result", "verified")
    if result == "verified":
        latest = db.scalar(select(ContentMasterRevision.id).where(ContentMasterRevision.content_unit_id == unit_id).order_by(ContentMasterRevision.revision_no.desc()).limit(1))
        if (master.id != latest or master.payload_hash != request["expected_payload_hash"]
                or content_masters._hash(master.payload_json) != master.payload_hash
                or master.context_hash != request["expected_context_hash"]
                or content_masters._hash(content_masters._context(db, project, unit, content_form=master.content_form)) != master.context_hash):
            raise HTTPException(409, "renderer_master_changed")
        _live_refs(db, project_id, master)
        rendered = renderer.render_master(db, master)
        _live_refs(db, project_id, master)
        if runtime_fingerprint(db, renderer, scope) != fingerprint:
            raise HTTPException(409, "renderer_runtime_changed")
        evidence = {"kind": "render_readback", "input_hash": rendered["render_input_hash"], "output_hash": rendered["content_hash"]}
        evidence["reference_hash"] = content_masters._hash(evidence)
        if registration is None:
            registration = CapabilityRegistration(kind="renderer", key=renderer.key, version=renderer.version, status="configured", config_fingerprint=implementation_fingerprint(renderer), created_by=user.email)
            db.add(registration)
            db.flush()
        else:
            registration.status, registration.config_fingerprint = "configured", implementation_fingerprint(renderer)
    elif registration is None:
        raise HTTPException(404, "renderer_verification_unavailable")
    else:
        evidence = {"kind": "revocation"}
    event = capability_integrations.append_verification(db, registration, scope_kind="renderer_output", scope=scope,
        result=result, actor=user.email, evidence=evidence, config_fingerprint=fingerprint,
        expires_at=datetime.now(UTC) + timedelta(hours=24) if result == "verified" else None)
    db.add(AuditLog(event="renderer.verification_recorded", actor=user.email, entity_type="capability_verification", entity_id=str(event.id),
        detail_json={"registration_id": registration.id, "scope": scope, "result": result}))
    db.commit()
    return {"registration_id": registration.id, "verification_id": event.id, "scope": scope, "result": result}


def inventory(db):
    bootstrap()
    result = []
    registrations = db.scalars(select(CapabilityRegistration).where(CapabilityRegistration.kind == "renderer").limit(100)).all()
    for descriptor in registry.list("renderer"):
        renderer = registry.resolve("renderer", descriptor.key, descriptor.version)
        if not isinstance(renderer, ProductionRenderer):
            continue
        registration = next((row for row in registrations if row.key == renderer.key and row.version == renderer.version), None)
        base = {"renderer_key": renderer.key, "renderer_version": renderer.version, "modality": renderer.modality,
            "payload_schema": renderer.schema, "output_mimes": list(renderer.output_mimes), "mode": renderer.mode,
            "configured": registration is not None and registration.status == "configured"}
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
            fingerprint = runtime_fingerprint(db, renderer, scope)
            verified = fingerprint is not None and capability_integrations.is_verified_for_scope(db, registration, scope, fingerprint, registry)
            result.append({**base, "registration_id": registration.id, "scope": scope, "verified": verified, "executable": verified,
                "reason": None if verified else "renderer_scope_unverified", "last_verification": {"id": event.id, "result": event.result,
                "verified_at": event.verified_at.isoformat(), "expires_at": event.expires_at.isoformat() if event.expires_at else None}})
        if not seen:
            result.append({**base, "verified": False, "executable": False,
                "reason": "manual_attestation_only" if renderer.mode == "manual" else "renderer_scope_unverified"})
    return result
