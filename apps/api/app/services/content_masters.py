"""Append-only Content Master revisions and their frozen context."""

import hashlib
import json
from collections.abc import Callable

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import (
    ChannelTemplateVersion,
    ContentMasterAssetRef,
    ContentMasterCheckRun,
    ContentMasterEvidenceRef,
    ContentMasterRevision,
    ContentProject,
    ContentUnit,
    CreativeBriefRevision,
    DiscoverabilityProfileVersion,
    EvidenceKind,
    FactPack,
    FactPackItem,
    IdentitySnapshot,
    MaterialRevision,
    ProjectFactBoundaryRevision,
    ProjectMaterialReference,
    ProjectWorkflowOutput,
    User,
    WorkflowRun,
    WorkflowStep,
    WorkflowStepAttempt,
    utcnow,
)
from .content_harness.channel_registry import ChannelRegistryError, resolve_content_form
from .creative_intents import CreativeIntentError, canonical_intent
from .materials import read_bytes_checked, sniff_mime, verify_bytes_checked
from .production_modalities import (
    adapter_for,
    default_payload_schema,
    render_input_hash,
    validate_json_bounds,
    validate_master_references,
)
from .project_brief import current_brief
from .project_events import record_project_event
from .project_evidence import current_boundary


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def local_final_use_allowed(db: Session, project_id: int, unit_id: int, owner_id: int, material: MaterialRevision, *, document: dict | None = None) -> bool:
    from .creative_packages import _check_derived_rights, _external_lineage

    if (material.source_kind != "external_execution" or material.mime_type != "video/mp4"
            or material.material.kind != "video" or material.material.status != "active"
            or material.status in {"revoked", "archived"}):
        return False
    try:
        lineage, execution = _external_lineage(db, material)
        if ((execution.owner_user_id, execution.project_id, execution.content_unit_id) != (owner_id, project_id, unit_id)
                or material.source_metadata_json.get("owner_user_id") != owner_id or lineage["role_id"] != "final"):
            return False
        from ..models import CreativeExecutionPackage

        package = db.get(CreativeExecutionPackage, execution.package_id)
        source = package.package_json.get("source", {})
        if source.get("payload_schema") != "video.master.v2" or not isinstance(source.get("content"), dict):
            return False
        latest = db.scalar(select(ContentMasterRevision).where(ContentMasterRevision.content_unit_id == unit_id).order_by(ContentMasterRevision.revision_no.desc()).limit(1))
        if latest is None or latest.project_id != project_id or latest.payload_schema != "video.master.v2":
            return False
        # Binding a render cannot silently adopt a film made for different editorial content.
        source_content = {key: value for key, value in source["content"].items() if key != "render_asset_ref"}
        if any({key: value for key, value in content.items() if key != "render_asset_ref"} != source_content for content in (latest.payload_json, document if document is not None else latest.payload_json)):
            return False
        _check_derived_rights(db, material)
    except (HTTPException, ValueError):
        return False
    return True


def owned_unit(db: Session, project_id: int, unit_id: int, user: User, *, mutate: bool = False) -> tuple[ContentProject, ContentUnit]:
    project = db.get(ContentProject, project_id)
    unit = db.get(ContentUnit, unit_id)
    if project is None or unit is None or project.owner_user_id != user.id or unit.project_id != project_id:
        raise HTTPException(404, "内容单元不存在")
    if mutate:
        from .project_authorization import lock_project_context

        project = lock_project_context(db, project_id, user)
        db.refresh(unit)
        if unit.project_id != project_id:
            raise HTTPException(404, "内容单元不存在")
    if mutate and (project.status == "archived" or unit.lifecycle_readonly):
        raise HTTPException(409, "已归档项目或单元仅可查看历史")
    return project, unit


def _context(db: Session, project: ContentProject, unit: ContentUnit, *, content_form: str | None, tolerate_unavailable_product: bool = False) -> dict:
    snapshot = db.get(IdentitySnapshot, unit.identity_snapshot_id) if unit.identity_snapshot_id else None
    brief = current_brief(db, project.id)
    boundary = current_boundary(db, project.id)
    from .product_context import context_snapshot, is_product
    product_domain = is_product(unit)
    product_context = None
    unavailable = False
    if product_domain:
        try:
            product_context = context_snapshot(db, unit)
        except (ValueError, HTTPException) as exc:
            if not tolerate_unavailable_product or isinstance(exc, HTTPException) and not 400 <= exc.status_code < 500:
                raise
            unavailable = True
    return {
        **({"production_domain": "product", "product_context": product_context} if product_domain else {}),
        **({"product_context_unavailable": True} if unavailable else {}),
        "identity": {"id": snapshot.id, "checksum": snapshot.checksum} if snapshot and not product_domain else None,
        "brief": {"id": brief.id, "checksum": brief.checksum} if brief else None,
        "boundary": {"id": boundary.id, "fact_pack_id": boundary.fact_pack_id, "checksum": boundary.fact_pack_checksum} if boundary else None,
        "channel_id": unit.channel_id,
        "content_form": content_form,
    }


def capture_status(db: Session, row: ContentMasterRevision) -> dict | None:
    from .production_profiles import capture_profile_current, profile_snapshot
    from .video_documents import capture_content_hash

    plan = (row.payload_json or {}).get("capture_plan")
    if row.payload_schema != "video.master.v2" or not plan:
        return None
    profile = profile_snapshot(db, row.content_unit_id)
    status = {"production_profile_revision_id": profile["id"] if profile else None}
    for kind in ("script", "task"):
        digest = capture_content_hash(row.payload_json, kind)
        ref = plan.get(f"{kind}_confirmation")
        current = bool(ref and ref["content_hash"] == digest)
        if kind == "task":
            current = current and capture_profile_current(db, row.content_unit_id, ref["production_profile_revision_id"], profile) and status["script"]["state"] == "confirmed"
        status[kind] = {"state": "confirmed" if current else "needs_review" if ref else "draft", "content_hash": digest}
    status["ready_to_shoot"] = status["task"]["state"] == "confirmed"
    status["adoptions"] = {shot["id"]: ("current" if status["ready_to_shoot"] and _capture_adoption_current(row.payload_json, shot) else "needs_review") for shot in row.payload_json.get("shots", []) if _real_capture_shot(row.payload_json, shot) and shot.get("source_material_revision_id") is not None}
    return status


def _capture_shot_placements(document: dict, shot: dict) -> list[dict]:
    return [{"track_id": track["id"], **item} for track in document.get("timeline", {}).get("tracks", [])
            for item in track["items"] if item.get("shot_id") == shot["id"] and "material_revision_id" in item]


def _capture_adoption_current(document: dict, shot: dict) -> bool:
    from .video_documents import capture_content_hash

    placements = _capture_shot_placements(document, shot)
    return any(take["material_revision_id"] == shot.get("source_material_revision_id")
               and take["state"] == "usable" and take["task_content_hash"] == capture_content_hash(document, "task")
               and all(item["material_revision_id"] == take["material_revision_id"]
                       and "trim_start_ms" in item and "trim_end_ms" in item
                       and take["trim_start_ms"] <= item["trim_start_ms"] < item["trim_end_ms"] <= take["trim_end_ms"]
                       for item in placements)
               for take in shot.get("capture_takes", []))


def _real_capture_shot(document: dict, shot: dict) -> bool:
    route = (document.get("capture_plan") or {}).get("route")
    return route == "real" or (route == "mixed" and (shot.get("production") or {}).get("source_mode", "existing") == "existing")


def _validate_capture_takes(db: Session, unit: ContentUnit, latest: ContentMasterRevision | None, document: dict, context: dict) -> None:
    from .video_documents import capture_content_hash

    previous_shots = {shot["id"]: shot for shot in (latest.payload_json.get("shots", []) if latest else [])}
    previous_takes = {take["id"]: (shot["id"], take) for shot in previous_shots.values() for take in shot.get("capture_takes", [])}
    for shot in document["shots"]:
        for take in shot.get("capture_takes", []):
            old = previous_takes.get(take["id"])
            if context.get("production_domain") != "product" or (not _real_capture_shot(document, shot) and (not old or old[1] != take)):
                raise HTTPException(422, {"code": "capture_take_route_invalid"})
            if old and (old[0] != shot["id"] or any(old[1][key] != take[key] for key in ("source_master_revision_id", "task_content_hash", "material_revision_id", "content_hash"))):
                raise HTTPException(422, {"code": "capture_take_identity_changed"})
            source = db.get(ContentMasterRevision, take["source_master_revision_id"])
            if source is None or source.content_unit_id != unit.id or source.payload_schema != "video.master.v2" or not any(item["id"] == shot["id"] for item in source.payload_json["shots"]):
                raise HTTPException(422, {"code": "capture_take_source_invalid"})
            source_shot = next(item for item in source.payload_json["shots"] if item["id"] == shot["id"])
            if not _real_capture_shot(source.payload_json, source_shot):
                raise HTTPException(422, {"code": "capture_take_source_invalid"})
            plan = source.payload_json.get("capture_plan") or {}
            task_ref = plan.get("task_confirmation") or {}
            script_ref = plan.get("script_confirmation") or {}
            if (take["task_content_hash"] != capture_content_hash(source.payload_json, "task")
                    or task_ref.get("content_hash") != take["task_content_hash"]
                    or script_ref.get("content_hash") != capture_content_hash(source.payload_json, "script")):
                raise HTTPException(409, {"code": "capture_take_task_unconfirmed"})
            material = db.get(MaterialRevision, take["material_revision_id"])
            if material is None or material.content_hash != take["content_hash"]:
                raise HTTPException(422, {"code": "capture_take_material_invalid"})
            if "trim_end_ms" in take and (type(material.duration_ms) is not int or material.duration_ms <= 0 or take["trim_end_ms"] > material.duration_ms):
                raise HTTPException(422, {"code": "capture_take_duration_unverified_or_exceeded"})
        old_shot = previous_shots.get(shot["id"], {})
        placements = _capture_shot_placements(document, shot)
        old_placements = _capture_shot_placements(latest.payload_json, shot) if latest else []
        adoption_changed = (shot.get("source_material_revision_id") is not None
                            and shot.get("source_material_revision_id") != old_shot.get("source_material_revision_id"))
        placements_changed = any(item not in old_placements for item in placements)
        if _real_capture_shot(document, shot) and (adoption_changed or placements_changed):
            from .production_profiles import capture_profile_current
            task_ref = (document.get("capture_plan") or {}).get("task_confirmation") or {}
            if (task_ref.get("content_hash") != capture_content_hash(document, "task")
                    or not capture_profile_current(db, unit.id, task_ref.get("production_profile_revision_id"))
                    or not _capture_adoption_current(document, shot)):
                raise HTTPException(409, {"code": "capture_take_usable_adoption_required"})


def _validate_capture_confirmations(db: Session, unit: ContentUnit, latest: ContentMasterRevision | None, document: dict, context: dict) -> None:
    from .production_profiles import profile_snapshot
    from .video_documents import capture_content_hash

    plan = document.get("capture_plan") or {}
    previous = (latest.payload_json.get("capture_plan") or {}) if latest else {}
    if not plan:
        return
    if context.get("production_domain") != "product":
        raise HTTPException(422, {"code": "capture_product_domain_required"})
    profile = profile_snapshot(db, unit.id)
    for kind in ("script", "task"):
        ref = plan.get(f"{kind}_confirmation")
        # Previously recorded approvals survive edits; their status is computed separately.
        if not ref or ref == previous.get(f"{kind}_confirmation"):
            continue
        source = db.get(ContentMasterRevision, ref["source_master_revision_id"])
        if source is None or source.content_unit_id != unit.id or source.payload_schema != "video.master.v2":
            raise HTTPException(422, {"code": "capture_confirmation_source_invalid"})
        digest = capture_content_hash(document, kind)
        if latest is None or source.id != latest.id or ref["content_hash"] != capture_content_hash(source.payload_json, kind) or ref["content_hash"] != digest:
            raise HTTPException(409, {"code": "capture_confirmation_source_conflict"})
        if plan.get("route") not in {"real", "ai", "mixed"}:
            raise HTTPException(422, {"code": "capture_route_required"})
        if not plan.get("script_structure", "").strip():
            raise HTTPException(422, {"code": "capture_script_structure_required"})
        if kind == "task":
            script_ref = plan.get("script_confirmation")
            if not script_ref or script_ref["content_hash"] != capture_content_hash(document, "script"):
                raise HTTPException(409, {"code": "capture_script_confirmation_required"})
            if not profile or profile["id"] != ref["production_profile_revision_id"]:
                raise HTTPException(409, {"code": "capture_profile_confirmation_conflict"})
            if not document.get("shots"):
                raise HTTPException(422, {"code": "capture_shots_required"})
            for shot in document["shots"]:
                real = plan["route"] == "real" or (plan["route"] == "mixed" and (shot.get("production") or {}).get("source_mode", "existing") == "existing")
                if not real:
                    continue
                filming = shot.get("filming") or {}
                if not shot.get("purpose", "").strip() or any(not filming.get(key, "").strip() for key in ("subject", "action", "camera_position", "angle", "focus")) or not filming.get("raw_duration_ms"):
                    raise HTTPException(422, {"code": "capture_shot_incomplete", "shot_id": shot["id"]})


def _serialize(db: Session, row: ContentMasterRevision, *, require_current: bool = True) -> dict:
    context = (_context(db, db.get(ContentProject, row.project_id), db.get(ContentUnit, row.content_unit_id), content_form=row.content_form, tolerate_unavailable_product=True)
               if require_current else frozen_context(db, row))
    stale: list[str] = []
    if (context["identity"] or {}).get("id") != row.identity_snapshot_id:
        stale.append("stale_identity")
    if (context["brief"] or {}).get("id") != row.creative_brief_revision_id:
        stale.append("stale_brief")
    if (context["boundary"] or {}).get("id") != row.fact_boundary_revision_id:
        stale.append("stale_evidence")
    if context["channel_id"] != row.channel_id:
        stale.append("stale_channel")
    if _hash(context) != row.context_hash:
        stale.append("stale_context")
    prerequisites = (("product_context", "product_context_missing"),) if context.get("production_domain") == "product" else (("identity", "identity_missing"),)
    missing = [reason for key, reason in (*prerequisites, ("brief", "brief_missing"), ("boundary", "evidence_missing")) if context.get(key) is None]
    return {
        "id": row.id, "project_id": row.project_id, "content_unit_id": row.content_unit_id,
        "revision_no": row.revision_no, "parent_revision_id": row.parent_revision_id,
        "modality": row.modality, "channel_id": row.channel_id, "content_form": row.content_form,
        "payload_schema": row.payload_schema, "payload": row.payload_json, "payload_hash": row.payload_hash,
        "capture_status": capture_status(db, row),
        "creative_intent": row.creative_intent_json, "creative_intent_hash": row.creative_intent_hash,
        "context_hash": row.context_hash, "identity_snapshot_id": row.identity_snapshot_id,
        "creative_brief_revision_id": row.creative_brief_revision_id, "fact_boundary_revision_id": row.fact_boundary_revision_id,
        "source_kind": row.source_kind, "edit_summary": row.edit_summary_json,
        "origin_workflow_run_id": row.origin_workflow_run_id, "origin_project_output_id": row.origin_project_output_id,
        "readiness": {"state": "blocked" if context.get("product_context_unavailable") else "stale" if stale else "incomplete_context" if missing else "current", "reasons": stale + missing + (["product_context_unavailable"] if context.get("product_context_unavailable") else [])},
        "assets": [{"id": ref.id, "material_revision_id": ref.material_revision_id, "role": ref.role, "slot_key": ref.slot_key, "sort_order": ref.sort_order, "placement": ref.placement_json, "rights_snapshot": ref.rights_snapshot_json, "content_hash": ref.content_hash_snapshot} for ref in db.scalars(select(ContentMasterAssetRef).where(ContentMasterAssetRef.master_revision_id == row.id).order_by(ContentMasterAssetRef.sort_order, ContentMasterAssetRef.id)).all()],
        "evidence": [{"id": ref.id, "fact_pack_item_id": ref.fact_pack_item_id, "role": ref.role, "locator": ref.content_locator_json, "sort_order": ref.sort_order, "snapshot_checksum": ref.snapshot_checksum} for ref in db.scalars(select(ContentMasterEvidenceRef).where(ContentMasterEvidenceRef.master_revision_id == row.id).order_by(ContentMasterEvidenceRef.sort_order, ContentMasterEvidenceRef.id)).all()],
        "created_by": row.created_by, "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def list_revisions(db: Session, project_id: int, unit_id: int, user: User, *, limit: int = 50, offset: int = 0) -> list[dict]:
    owned_unit(db, project_id, unit_id, user)
    rows = db.scalars(select(ContentMasterRevision).where(ContentMasterRevision.content_unit_id == unit_id).order_by(ContentMasterRevision.revision_no.desc()).offset(offset).limit(limit)).all()
    return [_serialize(db, row) for row in rows]


def get_revision(db: Session, project_id: int, unit_id: int, master_id: int, user: User) -> dict:
    owned_unit(db, project_id, unit_id, user)
    row = db.get(ContentMasterRevision, master_id)
    if row is None or row.project_id != project_id or row.content_unit_id != unit_id:
        raise HTTPException(404, "Master版本不存在")
    return _serialize(db, row)


def get_readiness(db: Session, project_id: int, unit_id: int, master_id: int, user: User) -> dict:
    projection = get_revision(db, project_id, unit_id, master_id, user)
    row = db.get(ContentMasterRevision, master_id)
    adapter = adapter_for(row.modality, row.payload_schema)
    checks = current_checks(db, project_id, unit_id, master_id, user)
    available = adapter.freeze_availability(db, row)
    latest = db.scalar(select(ContentMasterRevision.id).where(ContentMasterRevision.content_unit_id == unit_id).order_by(ContentMasterRevision.revision_no.desc()).limit(1))
    project = db.get(ContentProject, project_id)
    unit = db.get(ContentUnit, unit_id)
    return {"master_revision_id": row.id, "payload_schema": adapter.payload_schema, "adapter_version": adapter.version, "render_input_hash": render_input_hash(db, row), "preview": adapter.build_preview(row), "render": adapter.build_render_snapshot(db, row), "adapter_availability": available, "context": projection["readiness"], "checks": checks, "candidate_freeze_available": project.status != "archived" and not unit.lifecycle_readonly and latest == row.id and projection["readiness"]["state"] == "current" and available["available"] and all(check["status"] in {"pass", "warning"} and check["is_current"] for check in checks)}


def frozen_context(db: Session, row: ContentMasterRevision) -> dict:
    identity = db.get(IdentitySnapshot, row.identity_snapshot_id) if row.identity_snapshot_id else None
    brief = db.get(CreativeBriefRevision, row.creative_brief_revision_id) if row.creative_brief_revision_id else None
    boundary = db.get(ProjectFactBoundaryRevision, row.fact_boundary_revision_id) if row.fact_boundary_revision_id else None
    product_context = (row.edit_summary_json or {}).get("product_context_snapshot")
    return {
        **({"production_domain": "product", "product_context": product_context} if product_context is not None else {}),
        "identity": {"id": identity.id, "checksum": identity.checksum} if identity else None,
        "brief": {"id": brief.id, "checksum": brief.checksum} if brief else None,
        "boundary": {"id": boundary.id, "fact_pack_id": boundary.fact_pack_id, "checksum": boundary.fact_pack_checksum} if boundary else None,
        "channel_id": row.channel_id,
        "content_form": row.content_form,
    }


def check_input_hash(db: Session, row: ContentMasterRevision, *, require_current: bool = True) -> str:
    inputs = _serialize(db, row, require_current=require_current)
    assets = []
    for ref in inputs["assets"]:
        material = db.get(MaterialRevision, ref["material_revision_id"])
        assets.append({"ref": ref, "live": _material_live_state(db, material) if material else None})
    evidence = []
    for ref in inputs["evidence"]:
        item = db.get(FactPackItem, ref["fact_pack_item_id"])
        evidence.append({"ref": ref, "live": {"checksum": item.snapshot_checksum, "public_use_allowed": item.public_use_allowed, "revoked": item.public_use_revoked_at is not None, "kind": item.evidence_kind} if item else None})
    project = db.get(ContentProject, row.project_id)
    unit = db.get(ContentUnit, row.content_unit_id)
    adapter = adapter_for(row.modality, row.payload_schema)
    context = _context(db, project, unit, content_form=row.content_form, tolerate_unavailable_product=True) if require_current else frozen_context(db, row)
    return _hash({"payload_hash": row.payload_hash, "context_hash": row.context_hash, "current_context": context, "assets": assets, "evidence": evidence, "boundary_live": _boundary_live_state(db, row), "render": adapter.build_render_snapshot(db, row), "profile_key": adapter.payload_schema, "profile_version": adapter.version})


TEXT_CHECK_VERSIONS = {kind: "1" for kind in ("master_schema", "evidence", "rights", "render", "text_structure", "text_fact", "text_identity", "text_platform", "text_discoverability")}
TEXT_CHECK_VERSIONS["text_identity"] = "3"


def check_requirements(db: Session, row: ContentMasterRevision, *, require_current: bool = True, frozen_checks: list[dict] | None = None) -> dict[str, dict]:
    """Resolve each required check against its own pinned inputs; v1 keeps its original hash."""
    adapter = adapter_for(row.modality, row.payload_schema)
    base_hash = check_input_hash(db, row, require_current=require_current)
    if row.payload_schema == "video.master.v2":
        if frozen_checks is not None:
            frozen = {item.get("kind"): (item.get("report") or {}).get("requirement") for item in frozen_checks if isinstance(item, dict)}
            if len(frozen) != len(frozen_checks) or set(frozen) != set(adapter.required_check_kinds):
                raise ValueError("invalid frozen Video check requirement set")
        else:
            frozen = None
        result = {}
        for kind in adapter.required_check_kinds:
            if frozen is not None:
                metadata = frozen[kind]
                if not isinstance(metadata, dict) or metadata.get("kind") != kind:
                    raise ValueError(f"missing frozen Video check requirement: {kind}")
            else:
                metadata = {"kind": kind, "schema": adapter.payload_schema, "adapter_version": adapter.version, "implementation": "1"}
                if kind == "video_platform":
                    try:
                        form = resolve_content_form(db, row.channel_id, row.content_form)
                        template = db.get(ChannelTemplateVersion, form.profile_version_id) if form.profile_version_id else None
                        metadata["profile"] = {"id": template.id if template else None, "version": template.version if template else None, "checksum": (template.checksum or _hash(template.profile_json or {})) if template else None, "form_hash": _hash(form.to_dict()), "source": form.source, "artifact_kind": form.artifact_kind}
                    except (ChannelRegistryError, TypeError, ValueError):
                        metadata["profile"] = {"unavailable": True, "channel": row.channel_id, "content_form": row.content_form}
                elif kind == "video_identity":
                    from .generation.providers import effective_llm_config

                    config = effective_llm_config("identity_review")
                    metadata["semantic"] = {"profile": config.get("profile"), "provider": config["provider"], "model": config["model"], "configured": bool(config["provider"] == "openai_compatible" and config["model"] and config["api_key"] and config["base_url"])}
            result[kind] = {"kind": kind, "profile_key": adapter.payload_schema, "profile_version": adapter.version, "input_hash": _hash({"base": base_hash, "requirement": metadata}), "profile": metadata.get("profile"), "metadata": metadata}
        return result
    if row.payload_schema == "graphic.master.v2":
        if frozen_checks is not None:
            frozen = {item.get("kind"): (item.get("report") or {}).get("requirement") for item in frozen_checks if isinstance(item, dict)}
            if len(frozen) != len(frozen_checks) or set(frozen) != set(adapter.required_check_kinds):
                raise ValueError("invalid frozen Graphic check requirement set")
        else:
            frozen = None
        result = {}
        for kind in adapter.required_check_kinds:
            if frozen is not None:
                metadata = frozen[kind]
                if not isinstance(metadata, dict) or metadata.get("kind") != kind:
                    raise ValueError(f"missing frozen Graphic check requirement: {kind}")
            else:
                metadata = {"kind": kind, "schema": adapter.payload_schema, "adapter_version": adapter.version, "implementation": "1"}
                if kind == "graphic_platform":
                    try:
                        form = resolve_content_form(db, row.channel_id, row.content_form)
                        template = db.get(ChannelTemplateVersion, form.profile_version_id) if form.profile_version_id else None
                        metadata["profile"] = {"id": template.id if template else None, "version": template.version if template else None, "checksum": (template.checksum or _hash(template.profile_json or {})) if template else None, "form_hash": _hash(form.to_dict()), "source": form.source, "artifact_kind": form.artifact_kind}
                    except (ChannelRegistryError, TypeError, ValueError):
                        metadata["profile"] = {"unavailable": True, "channel": row.channel_id, "content_form": row.content_form}
                elif kind == "graphic_structure":
                    from .graphic_composition import photo_requirement
                    from .studio_creative_catalog import PRESETS, QUALITY, digest

                    snapshot = db.get(IdentitySnapshot, row.identity_snapshot_id) if row.identity_snapshot_id else None
                    creative = (snapshot.effective_profile_json or {}).get("graphic_creative_profile") if snapshot else None
                    if creative:
                        ref = creative.get("quality_profile_ref")
                        effective_preset = creative.get("style_preset_ref")
                        stage = (row.edit_summary_json or {}).get("stage_provenance") or {}
                        configuration = stage.get("creative_configuration") or {}
                        frozen_preset = configuration.get("style_preset") or {}
                        if (stage.get("accepted_payload_hash") == row.payload_hash
                                and configuration.get("identity_snapshot_id") == row.identity_snapshot_id
                                and configuration.get("identity_checksum") == snapshot.checksum):
                            effective_preset = frozen_preset.get("ref")
                        metadata["persona_quality"] = {"ref": ref, "hash": digest(QUALITY[ref]) if ref in QUALITY else None,
                            "style_preset_ref": effective_preset,
                            "style_preset_hash": digest(PRESETS[effective_preset]) if effective_preset in PRESETS else None,
                            "photo_requirement": photo_requirement(PRESETS[effective_preset]["config"]) if effective_preset in PRESETS else None,
                            "implementation": "graphic.geometry.v1"}
                elif kind in {"graphic_fact", "graphic_identity"}:
                    from .generation.providers import effective_llm_config

                    config = effective_llm_config("fact_review" if kind == "graphic_fact" else "identity_review")
                    metadata["semantic"] = {"profile": config.get("profile"), "provider": config["provider"], "model": config["model"], "configured": bool(config["provider"] == "openai_compatible" and config["model"] and config["api_key"] and config["base_url"])}
                    if kind == "graphic_fact":
                        boundary = db.get(ProjectFactBoundaryRevision, row.fact_boundary_revision_id) if row.fact_boundary_revision_id else None
                        items = db.scalars(select(FactPackItem).where(FactPackItem.fact_pack_id == boundary.fact_pack_id).order_by(FactPackItem.id)).all() if boundary else []
                        metadata["model_use"] = [{"id": item.id, "checksum": item.snapshot_checksum, "allowed": item.model_use_allowed, "revoked": item.public_use_revoked_at is not None} for item in items]
            result[kind] = {"kind": kind, "profile_key": adapter.payload_schema, "profile_version": adapter.version, "input_hash": _hash({"base": base_hash, "requirement": metadata}), "profile": metadata.get("profile"), "metadata": metadata}
        return result
    if row.payload_schema != "text.master.v2":
        return {kind: {"kind": kind, "profile_key": adapter.payload_schema, "profile_version": adapter.version, "input_hash": base_hash, "profile": None} for kind in adapter.required_check_kinds}
    profile = None
    if frozen_checks is None:
        if row.channel_id and row.content_form:
            profile = db.scalar(select(DiscoverabilityProfileVersion).where(DiscoverabilityProfileVersion.channel == row.channel_id, DiscoverabilityProfileVersion.content_form == row.content_form, DiscoverabilityProfileVersion.status == "published").order_by(DiscoverabilityProfileVersion.version.desc(), DiscoverabilityProfileVersion.id.desc()).limit(1))
        kinds = (*adapter.required_check_kinds, *(("text_discoverability",) if profile else ()))
        frozen = {}
    else:
        frozen = {item.get("kind"): (item.get("report") or {}).get("requirement") for item in frozen_checks if isinstance(item, dict)}
        kinds = tuple(frozen)
        required = set(adapter.required_check_kinds)
        if len(kinds) != len(frozen_checks) or not required.issubset(kinds) or set(kinds) - required - {"text_discoverability"}:
            raise ValueError("invalid frozen Text check requirement set")
    result = {}
    for kind in kinds:
        if frozen_checks is not None:
            metadata = frozen.get(kind)
            if not isinstance(metadata, dict) or metadata.get("kind") != kind:
                raise ValueError(f"missing frozen check requirement: {kind}")
        else:
            metadata = {"kind": kind, "schema": adapter.payload_schema, "adapter_version": adapter.version, "implementation": TEXT_CHECK_VERSIONS[kind], "renderer": {"key": "text.studio.document.v1", "version": adapter.version}}
            if kind == "text_discoverability":
                metadata["profile"] = {"id": profile.id, "key": profile.profile_key, "version": profile.version, "checksum": profile.checksum or _hash(profile.config_json or {}), "checksum_origin": "stored" if profile.checksum else "computed", "config_hash": _hash(profile.config_json or {})}
            elif kind == "text_platform":
                try:
                    form = resolve_content_form(db, row.channel_id, row.content_form)
                    template = db.get(ChannelTemplateVersion, form.profile_version_id) if form.profile_version_id else None
                    metadata["profile"] = {"id": template.id if template else None, "version": template.version if template else None, "checksum": (template.checksum or _hash(template.profile_json or {})) if template else None, "checksum_origin": "stored" if template and template.checksum else "computed" if template else "legacy_default", "form": form.to_dict()}
                except (ChannelRegistryError, TypeError, ValueError):
                    metadata["profile"] = {"unavailable": True, "channel": row.channel_id, "content_form": row.content_form}
            elif kind in {"text_fact", "text_identity"}:
                from .generation.providers import effective_llm_config

                config = effective_llm_config("fact_review" if kind == "text_fact" else "identity_review")
                metadata["semantic"] = {"profile": config.get("profile"), "provider": config["provider"], "model": config["model"], "configured": bool(config["provider"] == "openai_compatible" and config["model"] and config["api_key"] and config["base_url"])}
                if kind == "text_identity":
                    from .studio_creative_catalog import QUALITY, digest
                    snapshot = db.get(IdentitySnapshot, row.identity_snapshot_id) if row.identity_snapshot_id else None
                    creative = (snapshot.effective_profile_json or {}).get("text_creative_profile") if snapshot else None
                    if creative:
                        ref = creative.get("quality_profile_ref")
                        metadata["persona_quality"] = {"ref": ref, "hash": digest(QUALITY[ref]) if ref in QUALITY else None}
                if kind == "text_fact":
                    boundary = db.get(ProjectFactBoundaryRevision, row.fact_boundary_revision_id) if row.fact_boundary_revision_id else None
                    items = db.scalars(select(FactPackItem).where(FactPackItem.fact_pack_id == boundary.fact_pack_id).order_by(FactPackItem.id)).all() if boundary else []
                    metadata["model_use"] = [{"id": item.id, "checksum": item.snapshot_checksum, "allowed": item.model_use_allowed, "revoked": item.public_use_revoked_at is not None} for item in items]
        result[kind] = {"kind": kind, "profile_key": adapter.payload_schema, "profile_version": adapter.version, "input_hash": _hash({"base": base_hash, "requirement": metadata}), "profile": metadata.get("profile"), "profile_config": profile.config_json if kind == "text_discoverability" and profile is not None and frozen_checks is None else None, "metadata": metadata}
    return result


def _material_live_state(db: Session, material: MaterialRevision) -> dict:
    try:
        verify_bytes_checked(db, material)
        bytes_state = "verified"
    except HTTPException as exc:
        bytes_state = "missing" if exc.status_code == 404 else "invalid"
    return {"hash": material.content_hash, "status": material.status, "material_status": material.material.status, "public_use_allowed": material.public_use_allowed, "commercial_use_allowed": material.commercial_use_allowed, "rights_status": material.rights_status, "attribution_text": material.attribution_text, "bytes": bytes_state}


def _boundary_live_state(db: Session, row: ContentMasterRevision) -> dict | None:
    boundary = db.get(ProjectFactBoundaryRevision, row.fact_boundary_revision_id) if row.fact_boundary_revision_id else None
    pack = db.get(FactPack, boundary.fact_pack_id) if boundary else None
    if pack is None:
        return None
    items = db.scalars(select(FactPackItem).where(FactPackItem.fact_pack_id == pack.id).order_by(FactPackItem.id)).all()
    return {"id": pack.id, "version": pack.version, "checksum": pack.checksum, "status": pack.status, "matches_boundary": pack.version == boundary.fact_pack_version and pack.checksum == boundary.fact_pack_checksum, "items": [{"id": item.id, "checksum": item.snapshot_checksum, "kind": item.evidence_kind, "public_use_allowed": item.public_use_allowed, "revoked": item.public_use_revoked_at is not None} for item in items]}


def _evidence_check(db: Session, row: ContentMasterRevision) -> tuple[str, dict]:
    live = _boundary_live_state(db, row)
    if live is None:
        return "incomplete", {"reasons": ["evidence_missing"]}
    if live["status"] != "frozen" or not live["checksum"] or not live["matches_boundary"]:
        return "blocker", {"reasons": ["fact_pack_changed"]}
    if not live["items"]:
        return "incomplete", {"reasons": ["evidence_empty"]}
    kinds = {kind.value for kind in EvidenceKind if kind.value != "legacy_untyped"}
    reasons = [f"evidence_unready:{item['id']}" for item in live["items"] if not item["checksum"] or item["kind"] not in kinds or item["public_use_allowed"] is not True or item["revoked"]]
    items = {item["id"]: item for item in live["items"]}
    for ref in db.scalars(select(ContentMasterEvidenceRef).where(ContentMasterEvidenceRef.master_revision_id == row.id)).all():
        item = items.get(ref.fact_pack_item_id)
        if item is None or item["checksum"] != ref.snapshot_checksum:
            reasons.append(f"evidence_snapshot_changed:{ref.fact_pack_item_id}")
    if not reasons and (row.edit_summary_json or {}).get("unmapped_claims"):
        return "incomplete", {"reasons": ["draft_claims_unmapped"]}
    return ("blocker" if reasons else "pass"), {"reasons": reasons}


def _rights_check(db: Session, inputs: dict) -> tuple[str, dict]:
    reasons = []
    for ref in inputs["assets"]:
        material = db.get(MaterialRevision, ref["material_revision_id"])
        live = _material_live_state(db, material) if material else None
        if live is None or live["hash"] != ref["content_hash"] or live["status"] in {"revoked", "archived"} or live["material_status"] != "active" or live["public_use_allowed"] is not True or live["bytes"] != "verified":
            reasons.append(f"asset_unready:{ref['material_revision_id']}")
    if not reasons and inputs["edit_summary"].get("unmapped_media_ids"):
        return "incomplete", {"reasons": ["draft_media_unmapped"]}
    return ("blocker" if reasons else "pass"), {"reasons": reasons}


def current_checks(db: Session, project_id: int, unit_id: int, master_id: int, user: User) -> list[dict]:
    get_revision(db, project_id, unit_id, master_id, user)
    row = db.get(ContentMasterRevision, master_id)
    return projected_checks(db, row)


def projected_checks(db: Session, row: ContentMasterRevision) -> list[dict]:
    """Internal read projection; callers authorize the enclosing project/unit."""
    requirements = check_requirements(db, row)
    latest = {}
    for kind in requirements:
        latest[kind] = db.scalar(select(ContentMasterCheckRun).where(ContentMasterCheckRun.master_revision_id == row.id, ContentMasterCheckRun.check_kind == kind).order_by(ContentMasterCheckRun.id.desc()).limit(1))
    result = []
    for kind, check in latest.items():
        requirement = requirements[kind]
        is_current = check is not None and check.input_hash == requirement["input_hash"] and check.profile_key == requirement["profile_key"] and check.profile_version == requirement["profile_version"]
        result.append({"id": check.id if check else None, "check_kind": kind, "input_hash": check.input_hash if check else None, "is_current": is_current, "stored_status": check.status if check else None, "status": check.status if is_current else "stale" if check else "incomplete", "report": check.report_json if check else {"reason": "check_missing"}})
    return result


def master_risks(db: Session, row: ContentMasterRevision) -> list[dict]:
    projection = _serialize(db, row)
    checks = projected_checks(db, row)
    adapter = adapter_for(row.modality, row.payload_schema)
    risks = []
    context = projection["readiness"]
    if context["state"] != "current":
        risks.append({"code": "master_stale" if context["state"] == "stale" else "master_incomplete", "reasons": context["reasons"]})
    if any(item["status"] == "blocker" for item in checks):
        risks.append({"code": "master_check_blocked", "reasons": [item["check_kind"] for item in checks if item["status"] == "blocker"]})
    elif any(item["status"] not in {"pass", "warning"} for item in checks):
        risks.append({"code": "master_incomplete", "reasons": [f"{item['check_kind']}:{item['status']}" for item in checks if item["status"] not in {"pass", "warning"}]})
    render = adapter.build_render_snapshot(db, row)
    if render["status"] != "ready":
        risks.append({"code": "master_render_unready", "reasons": render["reasons"]})
    availability = adapter.freeze_availability(db, row)
    if not availability["available"] and render["status"] == "ready":
        risks.append({"code": "master_incomplete", "reasons": availability["reasons"]})
    return [{**risk, "master_revision_id": row.id, "unit_id": row.content_unit_id} for risk in risks]


def run_checks(db: Session, project_id: int, unit_id: int, master_id: int, user: User) -> list[dict]:
    _, unit = owned_unit(db, project_id, unit_id, user, mutate=True)
    row = db.get(ContentMasterRevision, master_id)
    if row is None or row.project_id != project_id or row.content_unit_id != unit.id:
        raise HTTPException(404, "Master版本不存在")
    inputs = _serialize(db, row)
    if inputs["readiness"]["state"] in {"stale", "blocked"}:
        raise HTTPException(409, {"code": "stale_master", "reasons": inputs["readiness"]["reasons"]})
    requirements = check_requirements(db, row)
    adapter = adapter_for(row.modality, row.payload_schema)
    payload_errors = adapter.validate_payload(row.payload_json)
    render = adapter_for(row.modality, row.payload_schema).build_render_snapshot(db, row)
    results = {
        "master_schema": ("blocker" if payload_errors else "pass", {"reasons": payload_errors}),
        "evidence": _evidence_check(db, row),
        "rights": _rights_check(db, inputs),
        "render": ("pass" if render["status"] == "ready" else "incomplete", render),
    }
    if row.payload_schema == "text.master.v2":
        from .text_master_checks import run_text_checks

        results.update(run_text_checks(db, row, inputs, requirements))
    elif row.payload_schema == "graphic.master.v2":
        from .graphic_master_checks import run_graphic_checks

        results.update(run_graphic_checks(db, row, inputs, requirements))
    elif row.payload_schema == "video.master.v2":
        from .video_master_checks import run_video_checks

        results.update(run_video_checks(db, row, inputs, requirements))
    rows = []
    for kind, requirement in requirements.items():
        status, report = results.get(kind, ("incomplete", {"reasons": ["check_handler_unavailable"]}))
        if inputs["readiness"]["state"] in {"stale", "blocked"}:
            status, report = "stale", {"reasons": inputs["readiness"]["reasons"]}
        if row.payload_schema in {"text.master.v2", "graphic.master.v2", "video.master.v2"}:
            report = {**report, "requirement": requirement["metadata"]}
        semantic = requirement.get("metadata", {}).get("semantic", {}) if (report.get("coverage") or {}).get("semantic") in {"verified", "partial"} else {}
        check = ContentMasterCheckRun(master_revision_id=row.id, check_kind=kind, profile_key=requirement["profile_key"], profile_version=requirement["profile_version"], input_hash=requirement["input_hash"], status=status, report_json=report, provider_key=str(semantic.get("provider") or "")[:100] or None, provider_version=str(semantic.get("model") or "")[:100] or None, created_at=utcnow())
        db.add(check)
        rows.append(check)
    db.commit()
    return [{"id": item.id, "check_kind": item.check_kind, "input_hash": item.input_hash, "status": item.status, "report": item.report_json} for item in rows]


def list_checks(db: Session, project_id: int, unit_id: int, master_id: int, user: User) -> list[dict]:
    owned_unit(db, project_id, unit_id, user)
    row = db.get(ContentMasterRevision, master_id)
    if row is None or row.project_id != project_id or row.content_unit_id != unit_id:
        raise HTTPException(404, "Master版本不存在")
    return [{"id": item.id, "check_kind": item.check_kind, "input_hash": item.input_hash, "status": item.status, "report": item.report_json, "created_at": item.created_at.isoformat() if item.created_at else None} for item in db.scalars(select(ContentMasterCheckRun).where(ContentMasterCheckRun.master_revision_id == master_id).order_by(ContentMasterCheckRun.id)).all()]


def _verified_generated_asset(db: Session, output: ProjectWorkflowOutput, material: MaterialRevision) -> bool:
    from .project_outputs import MEDIA_KINDS

    try:
        verify_bytes_checked(db, material)
    except (HTTPException, OSError):
        return False
    attempt = db.get(WorkflowStepAttempt, output.attempt_id) if output.attempt_id else None
    run = db.get(WorkflowRun, output.run_id)
    producer = db.get(ContentUnit, output.unit_id)
    step = db.get(WorkflowStep, attempt.step_id) if attempt else None
    provenance = output.provenance_json or {}
    # Shared assets keep successful historical attempt lineage, not the consumer's unit.
    return bool(
        attempt and run and producer and step
        and producer.project_id == output.project_id and run.content_unit_id == producer.id
        and attempt.run_id == run.id and step.run_id == run.id
        and attempt.node_id == output.node_id == step.node_id
        and attempt.status == "succeeded" and attempt.output_hash
        and (attempt.output_json or {}).get("generated") is True
        and attempt.output_json.get("material_revision_id") == material.id
        and MEDIA_KINDS.get(step.plugin_key) == material.material.kind
        and provenance.get("plugin_key") == step.plugin_key
        and provenance.get("workflow_id") == run.workflow_id
        and run.definition_checksum and provenance.get("definition_checksum") == run.definition_checksum
        and provenance.get("content_hash") == material.content_hash
    )


def save_revision(db: Session, *, project_id: int, unit_id: int, user: User, payload: dict, workflow_seed: bool = False, upgrade_source: ContentMasterRevision | None = None, derived_source: ContentMasterRevision | None = None, stage_adoption: Callable[[ContentMasterRevision], None] | None = None) -> dict:
    project, unit = owned_unit(db, project_id, unit_id, user, mutate=True)
    if unit.modality == "video":
        from .video_chain import locked

        if locked(db, unit_id):
            raise HTTPException(409, {"code": "video_chain_locked", "message": "成片已定稿，要调整请复制一份"})
    elif unit.modality in {"text", "graphic"}:
        from .article_chain import locked as article_locked

        if article_locked(db, unit_id):
            raise HTTPException(409, {"code": "article_chain_locked", "message": "已定稿，要调整请复制一份"})
    if "creative_intent" in payload:
        try:
            creative_intent, creative_intent_hash = canonical_intent(payload["creative_intent"])
        except CreativeIntentError as exc:
            raise HTTPException(422, {"code": str(exc)}) from None
        payload = {**payload, "creative_intent": creative_intent}
    modality = payload.get("modality") or unit.modality
    if modality != unit.modality:
        raise HTTPException(422, "Master形态必须与内容单元一致")
    payload_schema = payload.get("payload_schema")
    if not payload_schema:
        document = payload["payload"].get("document")
        studio_document = isinstance(document, dict) and document.get("schema") == "studio.text.document.v1"
        legacy_text = modality == "text" and (workflow_seed or "markdown" in payload["payload"] or not studio_document)
        payload_schema = "text.master.v1" if legacy_text else default_payload_schema(modality)
    adapter = adapter_for(modality, payload_schema)
    errors = adapter.validate_payload(payload["payload"])
    errors.extend(validate_json_bounds(payload))
    errors.extend(validate_master_references(payload["payload"], payload.get("asset_refs", []), payload.get("evidence_refs", [])))
    if errors:
        raise HTTPException(422, {"code": "invalid_master_payload", "reasons": errors})
    if payload_schema == "text.master.v2":
        from .text_documents import TextDocumentError, canonical_payload, validate_references

        try:
            payload = {**payload, "payload": canonical_payload(payload["payload"])}
            validate_references(payload["payload"], payload.get("asset_refs", []), payload.get("evidence_refs", []))
        except TextDocumentError as exc:
            raise HTTPException(422, {"code": "invalid_master_document", "reason": str(exc)}) from exc
    elif payload_schema == "graphic.master.v2":
        from .graphic_documents import GraphicDocumentError, canonical_payload, validate_references

        try:
            payload = {**payload, "payload": canonical_payload(payload["payload"])}
            validate_references(payload["payload"], payload.get("asset_refs", []), payload.get("evidence_refs", []))
        except GraphicDocumentError as exc:
            raise HTTPException(422, {"code": "invalid_master_document", "reason": str(exc)}) from exc
    elif payload_schema == "video.master.v2":
        from .video_documents import VideoDocumentError, canonical_payload, validate_references

        try:
            payload = {**payload, "payload": canonical_payload(payload["payload"])}
            validate_references(payload["payload"], payload.get("asset_refs", []), payload.get("evidence_refs", []))
        except VideoDocumentError as exc:
            raise HTTPException(422, {"code": "invalid_master_document", "reason": str(exc)}) from exc
    refs_fingerprint = {"assets": payload.get("asset_refs", []), "evidence": payload.get("evidence_refs", [])}
    trusted_kind = "workflow_stage" if stage_adoption is not None else "derived_video" if derived_source is not None else "explicit_upgrade" if upgrade_source is not None else "workflow_seed" if workflow_seed else "user_edit"
    if payload.get("source_kind", "user_edit") != trusted_kind:
        raise HTTPException(422, "来源血缘必须通过对应的已验证服务创建")
    if stage_adoption is None and "stage_provenance" in payload.get("edit_summary", {}):
        raise HTTPException(422, {"code": "unverified_stage_provenance"})
    if upgrade_source is None and {"upgrade_source", "upgrade_request"} & set(payload.get("edit_summary", {})):
        raise HTTPException(422, {"code": "unverified_upgrade_provenance"})
    if derived_source is None and "derived_video" in payload.get("edit_summary", {}):
        raise HTTPException(422, {"code": "unverified_derived_video_provenance"})
    if "render_attestation" in payload.get("edit_summary", {}):
        raise HTTPException(422, "渲染确认必须使用显式render_attestation输入")
    if "ai_provenance" in payload.get("edit_summary", {}):
        raise HTTPException(422, {"code": "unverified_ai_provenance"})
    if "asr_provenance" in payload.get("edit_summary", {}):
        raise HTTPException(422, {"code": "unverified_asr_provenance"})
    if "asr_receipt_id" in payload.get("edit_summary", {}) and payload_schema != "video.master.v2":
        raise HTTPException(422, {"code": "asr_video_v2_required"})
    if "ai_edits" in payload.get("edit_summary", {}) and (payload_schema != "text.master.v2" or not payload["edit_summary"]["ai_edits"]):
        raise HTTPException(422, {"code": "invalid_ai_edit_history"})
    request_intent = {"modality": modality, "schema": payload_schema, "payload": payload["payload"], "content_form": payload.get("content_form"), "parent_revision_id": payload.get("parent_revision_id"), "expected_revision": payload.get("expected_revision", 0), "edit_summary": payload.get("edit_summary", {}), "refs": refs_fingerprint, "source_kind": payload.get("source_kind", "user_edit"), "origin_project_output_id": payload.get("origin_project_output_id"), "origin_workflow_run_id": payload.get("origin_workflow_run_id")}
    if payload.get("expected_context_hash") is not None:
        request_intent["expected_context_hash"] = payload["expected_context_hash"]
    if payload.get("render_attestation") is not None:
        request_intent["render_attestation"] = payload["render_attestation"]
    if "creative_intent" in payload:
        request_intent["creative_intent"] = creative_intent
    fingerprint = _hash(request_intent)
    key = payload["idempotency_key"]
    existing = db.scalar(select(ContentMasterRevision).where(ContentMasterRevision.content_unit_id == unit_id, ContentMasterRevision.idempotency_key == key))
    if existing:
        if existing.request_fingerprint != fingerprint:
            raise HTTPException(409, "幂等键已用于不同的Master请求")
        return _serialize(db, existing)
    content_form = payload.get("content_form")
    if unit.channel_id:
        try:
            content_form = resolve_content_form(db, unit.channel_id, content_form).content_form
        except ChannelRegistryError as exc:
            raise HTTPException(422, {"code": "invalid_channel_form", "reason": str(exc)}) from exc
    elif content_form is not None:
        raise HTTPException(422, {"code": "channel_required_for_content_form"})
    context = _context(db, project, unit, content_form=content_form)
    latest = db.scalar(select(ContentMasterRevision).where(ContentMasterRevision.content_unit_id == unit_id).order_by(ContentMasterRevision.revision_no.desc()).limit(1))
    upgrade_pair = (upgrade_source.payload_schema, payload_schema) if upgrade_source is not None else None
    if upgrade_source is not None and (latest is None or latest.id != upgrade_source.id or latest.content_unit_id != unit_id or upgrade_pair not in {("text.master.v1", "text.master.v2"), ("graphic.master.v1", "graphic.master.v2"), ("video.master.v1", "video.master.v2")} or latest.payload_hash != payload.get("edit_summary", {}).get("upgrade_source", {}).get("payload_hash") or _hash(latest.payload_json) != latest.payload_hash):
        raise HTTPException(409, {"code": "master_upgrade_source_conflict"})
    if derived_source is not None and (latest is None or latest.id != derived_source.id or latest.content_unit_id != unit_id or latest.payload_schema != "video.master.v2" or payload_schema != "video.master.v2" or latest.payload_hash != payload.get("edit_summary", {}).get("derived_video", {}).get("source_payload_hash") or latest.context_hash != payload.get("edit_summary", {}).get("derived_video", {}).get("source_context_hash") or _hash(latest.payload_json) != latest.payload_hash):
        raise HTTPException(409, {"code": "video_derivation_source_conflict"})
    if latest and latest.payload_schema != payload_schema and upgrade_source is None:
        raise HTTPException(409, {"code": "explicit_master_upgrade_required"})
    expected_context = _context(db, project, unit, content_form=latest.content_form) if latest else context
    if payload.get("expected_context_hash") is not None and payload["expected_context_hash"] != _hash(expected_context):
        db.rollback()
        raise HTTPException(409, {"code": "master_context_conflict"})
    head = latest.revision_no if latest else 0
    expected = payload.get("expected_revision", 0)
    if expected != head:
        raise HTTPException(409, {"code": "master_revision_conflict", "expected_revision": expected, "current_revision": head})
    if payload_schema == "video.master.v2":
        _validate_capture_confirmations(db, unit, latest, payload["payload"], context)
        _validate_capture_takes(db, unit, latest, payload["payload"], context)
    if "creative_intent" not in payload:
        creative_intent = latest.creative_intent_json if latest else None
        creative_intent_hash = latest.creative_intent_hash if latest else None
    if "asr_receipt_id" in payload.get("edit_summary", {}):
        from .asr_suggestions import verify_for_save

        payload["edit_summary"] = {**payload["edit_summary"], "asr_provenance": verify_for_save(
            db, project_id, unit_id, user, latest, payload["payload"], payload["edit_summary"]["asr_receipt_id"])}
    if payload_schema == "text.master.v2" and payload.get("edit_summary", {}).get("ai_edits"):
        from .text_master_ai import verify_ai_edits

        payload["edit_summary"] = {
            **payload.get("edit_summary", {}),
            "ai_provenance": verify_ai_edits(
                db,
                project_id=project_id,
                unit_id=unit_id,
                actor=user.email,
                base=latest,
                document=payload["payload"]["document"],
                ai_edits=payload["edit_summary"]["ai_edits"],
            ),
        }
    parent_id = payload.get("parent_revision_id") or (latest.id if latest else None)
    if parent_id is not None:
        parent = db.get(ContentMasterRevision, parent_id)
        if parent is None or parent.content_unit_id != unit_id:
            raise HTTPException(422, "父Master必须属于当前内容单元")
        if latest is None or parent.id != latest.id:
            raise HTTPException(409, "父Master不是当前版本，请刷新后重试")
    boundary = db.get(ProjectFactBoundaryRevision, context["boundary"]["id"]) if context["boundary"] else None
    asset_inputs = payload.get("asset_refs", [])
    embedded = payload["payload"]["document"]["blocks"] if payload_schema == "text.master.v2" else []
    graphic_embedded = {(canvas["id"], layer["id"]): layer["type"] for canvas in payload["payload"]["canvases"] for layer in canvas["layers"] if layer["type"] in {"image", "chart"}} if payload_schema == "graphic.master.v2" else {}
    video_track_kinds = {track["id"]: track["kind"] for track in payload["payload"]["timeline"]["tracks"]} if payload_schema == "video.master.v2" else {}
    for item in asset_inputs:
        material = db.get(MaterialRevision, item.get("material_revision_id"))
        if material is None or material.content_hash != item.get("content_hash"):
            raise HTTPException(422, "素材版本不存在或内容哈希不匹配")
        if any(block["type"] in {"image", "chart"} and block["material_revision_id"] == material.id and block["type"] != material.material.kind for block in embedded):
            raise HTTPException(422, {"code": "text_asset_kind_mismatch"})
        visible = db.scalar(select(ProjectMaterialReference.id).where(ProjectMaterialReference.project_id == project_id, ProjectMaterialReference.material_revision_id == material.id, ProjectMaterialReference.status == "active"))
        generated = db.scalars(select(ProjectWorkflowOutput).where(ProjectWorkflowOutput.project_id == project_id, ProjectWorkflowOutput.output_kind == "material_revision", ProjectWorkflowOutput.entity_id == material.id)).all()
        if visible is None and not any(_verified_generated_asset(db, output, material) for output in generated):
            raise HTTPException(422, "素材版本尚未被当前项目明确引用")
        if payload_schema == "graphic.master.v2" and item.get("role") == "graphic_layer":
            placement = item["placement"]
            expected_kind = graphic_embedded[(placement["canvas_id"], placement["layer_id"])]
            if material.material.kind != expected_kind or material.material.status != "active" or material.status in {"revoked", "archived"} or material.public_use_allowed is not True:
                raise HTTPException(422, {"code": "graphic_asset_kind_or_rights_invalid"})
            content = read_bytes_checked(db, material, require_public=True)
            if not material.mime_type or not material.mime_type.startswith("image/") or sniff_mime(content, None) != material.mime_type:
                raise HTTPException(422, {"code": "graphic_asset_bytes_or_mime_invalid"})
        if payload_schema == "video.master.v2":
            role = item["role"]
            if role == "timeline_media":
                track_kind = video_track_kinds[item["placement"]["track_id"]]
                allowed_kinds = {"image", "video"} if track_kind == "video" else {"audio"} if track_kind in {"audio", "music"} else set()
            else:
                allowed_kinds = {
                    "shot_source": {"image", "video"}, "voice_audio": {"audio"}, "music_audio": {"audio"},
                    "cover_image": {"image"}, "render_output": {"video"},
                    "shot_reference": {"image"}, "postproduction_parent": {"video"}, "capture_take": {"video"},
                }[role]
            local_render = role == "render_output" and material.public_use_allowed is not True and local_final_use_allowed(
                db, project_id, unit_id, user.id, material, document=payload["payload"])
            # Accepted local renders preserve restricted rights; Candidate still requires public rights.
            if (material.material.kind not in allowed_kinds or material.material.status != "active"
                    or material.status in {"revoked", "archived"}
                    or (not local_render and material.model_use_allowed is not True and material.public_use_allowed is not True)
                    or (role == "render_output" and material.public_use_allowed is not True and not local_render)):
                raise HTTPException(422, {"code": "video_asset_kind_or_rights_invalid"})
            try:
                content = verify_bytes_checked(db, material, require_public=role == "render_output" and not local_render)
            except (HTTPException, OSError) as exc:
                raise HTTPException(422, {"code": "video_asset_bytes_unverified"}) from exc
            expected_prefix = "image/" if material.material.kind == "image" else "audio/" if material.material.kind == "audio" else "video/"
            if not material.mime_type or not material.mime_type.startswith(expected_prefix) or (role == "render_output" and material.mime_type != "video/mp4") or sniff_mime(content, None) != material.mime_type:
                raise HTTPException(422, {"code": "video_asset_bytes_or_mime_invalid"})
    for item in payload.get("evidence_refs", []):
        evidence = db.get(FactPackItem, item.get("fact_pack_item_id"))
        if boundary is None or evidence is None or evidence.fact_pack_id != boundary.fact_pack_id or not evidence.snapshot_checksum or evidence.snapshot_checksum != item.get("snapshot_checksum") or evidence.fact_pack.status != "frozen" or evidence.evidence_kind == "legacy_untyped":
            raise HTTPException(422, "证据必须属于当前冻结事实边界并匹配快照")
    row = ContentMasterRevision(
        project_id=project_id, content_unit_id=unit_id, revision_no=head + 1, parent_revision_id=parent_id,
        modality=modality, channel_id=unit.channel_id, content_form=content_form, payload_schema=payload_schema,
        payload_json=payload["payload"], payload_hash=_hash(payload["payload"]), context_hash=_hash(context),
        creative_intent_json=creative_intent, creative_intent_hash=creative_intent_hash,
        identity_snapshot_id=None if context.get("production_domain") == "product" else unit.identity_snapshot_id, creative_brief_revision_id=context["brief"]["id"] if context["brief"] else None,
        fact_boundary_revision_id=context["boundary"]["id"] if context["boundary"] else None,
        origin_workflow_run_id=payload.get("origin_workflow_run_id"), origin_project_output_id=payload.get("origin_project_output_id"),
        source_kind=payload.get("source_kind", "user_edit"), edit_summary_json={**payload.get("edit_summary", {}), **({"product_context_snapshot": context["product_context"]} if context.get("production_domain") == "product" else {})}, idempotency_key=key,
        request_fingerprint=fingerprint, created_by=user.email, created_at=utcnow(),
    )
    db.add(row)
    try:
        db.flush()
        for item in asset_inputs:
            material = db.get(MaterialRevision, item["material_revision_id"])
            db.add(ContentMasterAssetRef(
                master_revision_id=row.id, material_revision_id=material.id, role=item.get("role", "other"),
                slot_key=item.get("slot_key"), sort_order=item.get("sort_order", 0), placement_json=item.get("placement", {}),
                rights_snapshot_json={"rights_status": material.rights_status, "public_use_allowed": material.public_use_allowed, "model_use_allowed": material.model_use_allowed, "commercial_use_allowed": material.commercial_use_allowed},
                content_hash_snapshot=material.content_hash, created_at=utcnow(),
            ))
        for item in payload.get("evidence_refs", []):
            db.add(ContentMasterEvidenceRef(
                master_revision_id=row.id, fact_pack_item_id=item["fact_pack_item_id"], role=item.get("role", "claim"),
                content_locator_json=item.get("locator", {}), sort_order=item.get("sort_order", 0), snapshot_checksum=item["snapshot_checksum"], created_at=utcnow(),
            ))
        db.flush()
        attestation = payload.get("render_attestation")
        if attestation is not None:
            if isinstance(attestation, dict) and any(key in attestation for key in ("origin", "renderer_key", "renderer_version", "provider", "verified")):
                db.rollback()
                raise HTTPException(422, {"code": "renderer_capability_unavailable"})
            if modality not in {"graphic", "video"} or set(attestation) != {"confirmed", "render_input_hash"} or attestation.get("confirmed") is not True or attestation.get("render_input_hash") != render_input_hash(db, row):
                db.rollback()
                raise HTTPException(422, {"code": "invalid_render_attestation"})
            declaration = row.payload_json.get("render_asset_ref")
            declarations = declaration if isinstance(declaration, list) else [declaration] if isinstance(declaration, dict) else []
            refs = {item.material_revision_id: item.content_hash_snapshot for item in db.scalars(select(ContentMasterAssetRef).where(ContentMasterAssetRef.master_revision_id == row.id, ContentMasterAssetRef.role == "render_output")).all()}
            outputs = [{"material_revision_id": item.get("material_revision_id"), "content_hash": refs.get(item.get("material_revision_id")), "canvas_id": item.get("canvas_id")} for item in declarations if isinstance(item, dict)]
            row.edit_summary_json = {**row.edit_summary_json, "render_attestation": {"origin": "manual", "confirmed": True, "render_input_hash": attestation["render_input_hash"], "attested_by": user.email, "outputs": outputs}}
            rendered = adapter_for(modality, row.payload_schema).build_render_snapshot(db, row)
            if rendered["status"] != "ready":
                db.rollback()
                raise HTTPException(422, {"code": "invalid_render_attestation", "reasons": rendered["reasons"]})
        record_project_event(db, project_id=project_id, event_type="content_master.saved", actor=user.email, entity_type="content_master_revision", entity_id=row.id, payload={"unit_id": unit_id, "revision_no": row.revision_no})
        db.flush()
        db.expire_all()
        project = db.get(ContentProject, project_id)
        unit = db.get(ContentUnit, unit_id)
        if project.owner_user_id != user.id or project.status == "archived" or unit.project_id != project_id or unit.lifecycle_readonly or unit.modality != modality or _hash(_context(db, project, unit, content_form=content_form)) != row.context_hash:
            db.rollback()
            raise HTTPException(409, {"code": "master_context_conflict"})
        if attestation is not None and adapter_for(modality, row.payload_schema).build_render_snapshot(db, row)["status"] != "ready":
            db.rollback()
            raise HTTPException(409, {"code": "render_inputs_changed"})
        if stage_adoption is not None:
            # The trusted bridge owns association and feedback in this same
            # transaction; committing the Master first would orphan acceptance.
            stage_adoption(row)
            db.flush()
        if "asr_receipt_id" in row.edit_summary_json:
            from .asr_suggestions import commit_guard

            try:
                with commit_guard(row.edit_summary_json["asr_receipt_id"], user.id, project_id, unit_id,
                                  row.edit_summary_json["asr_provenance"]):
                    db.commit()
            except HTTPException:
                db.rollback()
                raise
        else:
            db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Master版本并发冲突，请刷新后重试") from exc
    db.refresh(row)
    return _serialize(db, row)


def preview_text_upgrade(db: Session, project_id: int, unit_id: int, master_id: int, user: User) -> dict:
    from .text_documents import TextDocumentError, convert_legacy_text

    project, unit = owned_unit(db, project_id, unit_id, user)
    row = db.get(ContentMasterRevision, master_id)
    if row is None or row.content_unit_id != unit_id or row.project_id != project_id:
        raise HTTPException(404, "Master版本不存在")
    if row.modality != "text" or row.payload_schema != "text.master.v1":
        raise HTTPException(409, {"code": "text_v1_upgrade_source_required"})
    if row.payload_hash != _hash(row.payload_json):
        raise HTTPException(409, {"code": "master_upgrade_source_integrity"})
    saved = _serialize(db, row)
    assets = [{key: ref[key] for key in ("material_revision_id", "content_hash", "role", "slot_key", "sort_order", "placement")} for ref in saved["assets"]]
    evidence = [{key: ref[key] for key in ("fact_pack_item_id", "snapshot_checksum", "role", "locator", "sort_order")} for ref in saved["evidence"]]
    try:
        converted = convert_legacy_text(row.payload_json, asset_refs=assets, evidence_refs=evidence)
    except TextDocumentError as exc:
        raise HTTPException(422, {"code": "legacy_text_conversion_failed", "reason": str(exc)}) from exc
    return {**converted, "source_master_id": row.id, "source_revision_no": row.revision_no, "source_payload_hash": row.payload_hash, "source_schema": row.payload_schema, "current_context_hash": _hash(_context(db, project, unit, content_form=row.content_form))}


def upgrade_text_master(db: Session, *, project_id: int, unit_id: int, master_id: int, user: User, payload: dict) -> dict:
    owned_unit(db, project_id, unit_id, user, mutate=True)
    intent = {"source_master_id": master_id, "actor": user.email, **payload}
    existing = db.scalar(select(ContentMasterRevision).where(ContentMasterRevision.content_unit_id == unit_id, ContentMasterRevision.idempotency_key == payload["idempotency_key"]))
    if existing:
        if existing.source_kind != "explicit_upgrade" or existing.edit_summary_json.get("upgrade_request") != intent:
            raise HTTPException(409, {"code": "master_upgrade_idempotency_conflict"})
        return _serialize(db, existing)
    preview = preview_text_upgrade(db, project_id, unit_id, master_id, user)
    if preview["source_payload_hash"] != payload["expected_payload_hash"] or preview["current_context_hash"] != payload["expected_context_hash"]:
        raise HTTPException(409, {"code": "master_upgrade_source_conflict"})
    source = db.get(ContentMasterRevision, master_id)
    if _serialize(db, source)["readiness"]["state"] == "stale":
        raise HTTPException(409, {"code": "stale_upgrade_source"})
    return save_revision(db, project_id=project_id, unit_id=unit_id, user=user, upgrade_source=source, payload={
        "expected_revision": payload["expected_revision"], "expected_context_hash": payload["expected_context_hash"],
        "idempotency_key": payload["idempotency_key"], "parent_revision_id": source.id, "content_form": source.content_form,
        "payload_schema": "text.master.v2", "payload": preview["payload"], "asset_refs": preview["asset_refs"], "evidence_refs": preview["evidence_refs"], "source_kind": "explicit_upgrade",
        "edit_summary": {"upgrade_request": intent, "upgrade_source": {"master_id": source.id, "revision_no": source.revision_no, "payload_schema": source.payload_schema, "payload_hash": source.payload_hash}, "conversion_warnings": preview["warnings"], "document_hash": preview["document_hash"]},
    })


def preview_graphic_upgrade(db: Session, project_id: int, unit_id: int, master_id: int, user: User) -> dict:
    from .graphic_documents import GraphicDocumentError, convert_legacy_graphic

    project, unit = owned_unit(db, project_id, unit_id, user)
    row = db.get(ContentMasterRevision, master_id)
    if row is None or row.content_unit_id != unit_id or row.project_id != project_id:
        raise HTTPException(404, "Master版本不存在")
    if row.modality != "graphic" or row.payload_schema != "graphic.master.v1":
        raise HTTPException(409, {"code": "graphic_v1_upgrade_source_required"})
    if row.payload_hash != _hash(row.payload_json):
        raise HTTPException(409, {"code": "master_upgrade_source_integrity"})
    saved = _serialize(db, row)
    assets = [{key: ref[key] for key in ("material_revision_id", "content_hash", "role", "slot_key", "sort_order", "placement")} for ref in saved["assets"]]
    evidence = [{key: ref[key] for key in ("fact_pack_item_id", "snapshot_checksum", "role", "locator", "sort_order")} for ref in saved["evidence"]]
    try:
        converted = convert_legacy_graphic(row.payload_json, asset_refs=assets, evidence_refs=evidence)
    except GraphicDocumentError as exc:
        raise HTTPException(422, {"code": "legacy_graphic_conversion_failed", "reason": str(exc)}) from exc
    return {**converted, "source_master_id": row.id, "source_revision_no": row.revision_no, "source_payload_hash": row.payload_hash, "source_schema": row.payload_schema, "current_context_hash": _hash(_context(db, project, unit, content_form=row.content_form))}


def upgrade_graphic_master(db: Session, *, project_id: int, unit_id: int, master_id: int, user: User, payload: dict) -> dict:
    owned_unit(db, project_id, unit_id, user, mutate=True)
    intent = {"source_master_id": master_id, "actor": user.email, **payload}
    existing = db.scalar(select(ContentMasterRevision).where(ContentMasterRevision.content_unit_id == unit_id, ContentMasterRevision.idempotency_key == payload["idempotency_key"]))
    if existing:
        if existing.source_kind != "explicit_upgrade" or existing.edit_summary_json.get("upgrade_request") != intent:
            raise HTTPException(409, {"code": "master_upgrade_idempotency_conflict"})
        return _serialize(db, existing)
    preview = preview_graphic_upgrade(db, project_id, unit_id, master_id, user)
    if preview["source_payload_hash"] != payload["expected_payload_hash"] or preview["current_context_hash"] != payload["expected_context_hash"]:
        raise HTTPException(409, {"code": "master_upgrade_source_conflict"})
    source = db.get(ContentMasterRevision, master_id)
    if _serialize(db, source)["readiness"]["state"] == "stale":
        raise HTTPException(409, {"code": "stale_upgrade_source"})
    return save_revision(db, project_id=project_id, unit_id=unit_id, user=user, upgrade_source=source, payload={
        "expected_revision": payload["expected_revision"], "expected_context_hash": payload["expected_context_hash"],
        "idempotency_key": payload["idempotency_key"], "parent_revision_id": source.id, "content_form": source.content_form,
        "payload_schema": "graphic.master.v2", "payload": preview["payload"], "asset_refs": preview["asset_refs"], "evidence_refs": preview["evidence_refs"], "source_kind": "explicit_upgrade",
        "edit_summary": {"upgrade_request": intent, "upgrade_source": {"master_id": source.id, "revision_no": source.revision_no, "payload_schema": source.payload_schema, "payload_hash": source.payload_hash}, "conversion_warnings": preview["warnings"], "document_hash": preview["document_hash"]},
    })


def preview_video_upgrade(db: Session, project_id: int, unit_id: int, master_id: int, user: User) -> dict:
    from .video_documents import legacy_upgrade_preview

    project, unit = owned_unit(db, project_id, unit_id, user)
    row = db.get(ContentMasterRevision, master_id)
    if row is None or row.content_unit_id != unit_id or row.project_id != project_id:
        raise HTTPException(404, "Master版本不存在")
    if row.modality != "video" or row.payload_schema != "video.master.v1":
        raise HTTPException(409, {"code": "video_v1_upgrade_source_required"})
    if row.payload_hash != _hash(row.payload_json):
        raise HTTPException(409, {"code": "master_upgrade_source_integrity"})
    saved = _serialize(db, row)
    return {
        **legacy_upgrade_preview(row.payload_json, saved["assets"], saved["evidence"]),
        "source_master_id": row.id, "source_revision_no": row.revision_no,
        "source_payload_hash": row.payload_hash, "source_schema": row.payload_schema,
        "current_context_hash": _hash(_context(db, project, unit, content_form=row.content_form)),
    }


def upgrade_video_master(db: Session, *, project_id: int, unit_id: int, master_id: int, user: User, payload: dict) -> dict:
    from .video_documents import VideoDocumentError, canonical_payload

    owned_unit(db, project_id, unit_id, user, mutate=True)
    intent = {"source_master_id": master_id, "actor": user.email, "request_hash": _hash(payload)}
    existing = db.scalar(select(ContentMasterRevision).where(ContentMasterRevision.content_unit_id == unit_id, ContentMasterRevision.idempotency_key == payload["idempotency_key"]))
    if existing:
        if existing.source_kind != "explicit_upgrade" or existing.edit_summary_json.get("upgrade_request") != intent:
            raise HTTPException(409, {"code": "master_upgrade_idempotency_conflict"})
        return _serialize(db, existing)
    preview = preview_video_upgrade(db, project_id, unit_id, master_id, user)
    if preview["source_payload_hash"] != payload["expected_payload_hash"] or preview["current_context_hash"] != payload["expected_context_hash"]:
        raise HTTPException(409, {"code": "master_upgrade_source_conflict"})
    if payload["acknowledged_warnings"] != preview["warnings"]:
        raise HTTPException(422, {"code": "video_upgrade_warnings_not_acknowledged", "warnings": preview["warnings"]})
    try:
        document = canonical_payload(payload["payload"])
    except VideoDocumentError as exc:
        raise HTTPException(422, {"code": "invalid_master_document", "reason": str(exc)}) from exc
    source_fields = preview["source_fields"]
    if source_fields["script"] is not None and "".join(block["text"] for block in document["script"]["blocks"]) != source_fields["script"]:
        raise HTTPException(409, {"code": "legacy_script_changed_during_upgrade"})
    if [{"id": shot["id"], "order": shot["order"]} for shot in document["shots"]] != source_fields["shots"]:
        raise HTTPException(409, {"code": "legacy_shots_changed_during_upgrade"})
    if "render_asset_ref" in document or any(ref.get("role") == "render_output" for ref in payload["asset_refs"]):
        raise HTTPException(422, {"code": "video_upgrade_render_requires_new_attestation"})
    source = db.get(ContentMasterRevision, master_id)
    if _serialize(db, source)["readiness"]["state"] == "stale":
        raise HTTPException(409, {"code": "stale_upgrade_source"})
    return save_revision(db, project_id=project_id, unit_id=unit_id, user=user, upgrade_source=source, payload={
        "expected_revision": payload["expected_revision"], "expected_context_hash": payload["expected_context_hash"],
        "idempotency_key": payload["idempotency_key"], "parent_revision_id": source.id, "content_form": source.content_form,
        "payload_schema": "video.master.v2", "payload": document, "asset_refs": payload["asset_refs"], "evidence_refs": payload["evidence_refs"],
        "source_kind": "explicit_upgrade", "edit_summary": {
            "upgrade_request": intent,
            "upgrade_source": {"master_id": source.id, "revision_no": source.revision_no, "payload_schema": source.payload_schema, "payload_hash": source.payload_hash},
            "conversion_warnings": preview["warnings"],
        },
    })
