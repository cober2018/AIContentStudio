"""Project-owned immutable ChannelVariant history and bounded writes."""

import hashlib
import json

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import (
    ChannelTemplateVersion,
    ChannelVariantAssetRef,
    ChannelVariantCheckRun,
    ChannelVariantEvidenceRef,
    ChannelVariantRevision,
    ContentMasterAssetRef,
    ContentMasterEvidenceRef,
    ContentMasterRevision,
    ContentUnit,
    FactPack,
    FactPackItem,
    IdentitySnapshot,
    MaterialRevision,
    ProjectFactBoundaryRevision,
    ProjectMaterialReference,
    ProjectWorkflowOutput,
    User,
    utcnow,
)
from .channel_adapters import AdapterUnavailable, capability_for, executable_adapter_for
from .channel_variant_documents import VariantDocumentError, canonical_payload
from .content_masters import owned_unit
from .materials import read_bytes_checked, sniff_mime
from .project_events import record_project_event


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _serialize(db: Session, row: ChannelVariantRevision) -> dict:
    assets = db.scalars(
        select(ChannelVariantAssetRef)
        .where(ChannelVariantAssetRef.variant_revision_id == row.id)
        .order_by(ChannelVariantAssetRef.sort_order, ChannelVariantAssetRef.id)
    ).all()
    evidence = db.scalars(
        select(ChannelVariantEvidenceRef)
        .where(ChannelVariantEvidenceRef.variant_revision_id == row.id)
        .order_by(ChannelVariantEvidenceRef.sort_order, ChannelVariantEvidenceRef.id)
    ).all()
    checks = db.scalars(
        select(ChannelVariantCheckRun)
        .where(ChannelVariantCheckRun.variant_revision_id == row.id)
        .order_by(ChannelVariantCheckRun.created_at.desc(), ChannelVariantCheckRun.id.desc())
    ).all()
    return {
        "id": row.id,
        "project_id": row.project_id,
        "content_unit_id": row.content_unit_id,
        "variant_key": row.variant_key,
        "revision_no": row.revision_no,
        "parent_revision_id": row.parent_revision_id,
        "source_master_revision_id": row.source_master_revision_id,
        "source_master_payload_hash": row.source_master_payload_hash,
        "source_master_context_hash": row.source_master_context_hash,
        "source_channel_id": row.source_channel_id,
        "source_content_form": row.source_content_form,
        "identity_snapshot_id": row.identity_snapshot_id,
        "channel_id": row.channel_id,
        "content_form": row.content_form,
        "artifact_kind": row.artifact_kind,
        "profile_template_version_id": row.profile_template_version_id,
        "profile_key": row.profile_key,
        "profile_version": row.profile_version,
        "profile_hash": row.profile_hash,
        "adapter_key": row.adapter_key,
        "adapter_version": row.adapter_version,
        "rule_hash": row.rule_hash,
        "payload_schema": row.payload_schema,
        "payload": row.payload_json,
        "payload_hash": row.payload_hash,
        "context_hash": row.context_hash,
        "source_kind": row.source_kind,
        "edit_summary": row.edit_summary_json,
        "llm_provenance": row.llm_provenance_json,
        "idempotency_key": row.idempotency_key,
        "created_by": row.created_by,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "assets": [
            {"id": item.id, "material_revision_id": item.material_revision_id, "role": item.role, "slot_key": item.slot_key, "sort_order": item.sort_order, "placement": item.placement_json, "rights_snapshot": item.rights_snapshot_json, "content_hash": item.content_hash_snapshot}
            for item in assets
        ],
        "evidence": [
            {"id": item.id, "fact_pack_item_id": item.fact_pack_item_id, "role": item.role, "locator": item.content_locator_json, "sort_order": item.sort_order, "snapshot_checksum": item.snapshot_checksum}
            for item in evidence
        ],
        "checks": [
            {"id": item.id, "check_kind": item.check_kind, "input_hash": item.input_hash, "profile_hash": item.profile_hash, "adapter_hash": item.adapter_hash, "rule_hash": item.rule_hash, "status": item.status, "report": item.report_json, "created_at": item.created_at.isoformat() if item.created_at else None}
            for item in checks
        ],
    }


def list_revisions(db: Session, project_id: int, unit_id: int, user: User, *, variant_key: str | None = None, limit: int = 50, offset: int = 0) -> list[dict]:
    owned_unit(db, project_id, unit_id, user)
    statement = select(ChannelVariantRevision).where(ChannelVariantRevision.project_id == project_id, ChannelVariantRevision.content_unit_id == unit_id)
    if variant_key is not None:
        statement = statement.where(ChannelVariantRevision.variant_key == variant_key)
    rows = db.scalars(statement.order_by(ChannelVariantRevision.created_at.desc(), ChannelVariantRevision.id.desc()).offset(offset).limit(limit)).all()
    return [_serialize(db, row) for row in rows]


def current_revision(db: Session, project_id: int, unit_id: int, variant_key: str, user: User) -> dict | None:
    owned_unit(db, project_id, unit_id, user)
    row = db.scalar(
        select(ChannelVariantRevision)
        .where(ChannelVariantRevision.project_id == project_id, ChannelVariantRevision.content_unit_id == unit_id, ChannelVariantRevision.variant_key == variant_key)
        .order_by(ChannelVariantRevision.revision_no.desc())
        .limit(1)
    )
    return _serialize(db, row) if row else None


def get_revision(db: Session, project_id: int, unit_id: int, variant_id: int, user: User) -> dict:
    owned_unit(db, project_id, unit_id, user)
    row = db.get(ChannelVariantRevision, variant_id)
    if row is None or row.project_id != project_id or row.content_unit_id != unit_id:
        raise HTTPException(404, "ChannelVariant版本不存在")
    return _serialize(db, row)


def _current_source_id(db: Session, unit_id: int) -> int | None:
    return db.scalar(
        select(ContentMasterRevision.id)
        .where(ContentMasterRevision.content_unit_id == unit_id)
        .order_by(ContentMasterRevision.revision_no.desc())
        .limit(1)
    )


def _variant_context(master: ContentMasterRevision, unit_identity_id: int | None, identity_checksum: str | None, channel_id: str, content_form: str, capability: dict, rule_hash: str) -> dict:
    return {
        "source_master_revision_id": master.id,
        "source_payload_hash": master.payload_hash,
        "source_context_hash": master.context_hash,
        "identity_snapshot_id": unit_identity_id,
        "identity_checksum": identity_checksum,
        "target": {"channel": channel_id, "content_form": content_form, "artifact_kind": capability["artifact_kind"]},
        "profile_version_id": capability["profile_version_id"],
        "profile_version": capability["profile_version"],
        "profile_hash": capability["profile_hash"],
        "adapter_key": capability["adapter_key"],
        "adapter_version": capability["adapter_version"],
        "rule_hash": rule_hash,
    }


def _validate_evidence_refs(db: Session, master: ContentMasterRevision, refs: list[dict]) -> list[FactPackItem]:
    if not refs:
        return []
    boundary = db.get(ProjectFactBoundaryRevision, master.fact_boundary_revision_id) if master.fact_boundary_revision_id else None
    pack = db.get(FactPack, boundary.fact_pack_id) if boundary else None
    if pack is None or pack.status != "frozen" or pack.version != boundary.fact_pack_version or pack.checksum != boundary.fact_pack_checksum:
        raise HTTPException(422, {"code": "variant_evidence_boundary_unready"})
    items = []
    for ref in refs:
        item = db.get(FactPackItem, ref.get("fact_pack_item_id"))
        if item is None or item.fact_pack_id != pack.id or item.snapshot_checksum != ref.get("snapshot_checksum") or item.evidence_kind == "legacy_untyped" or item.public_use_allowed is not True or item.public_use_revoked_at is not None:
            raise HTTPException(422, {"code": "variant_evidence_ref_invalid"})
        items.append(item)
    return items


def _graphic_source_refs(db: Session, master: ContentMasterRevision) -> list[dict]:
    from .production_modalities import adapter_for

    render = adapter_for("graphic", master.payload_schema).build_render_snapshot(db, master)
    if render["status"] != "ready":
        raise HTTPException(422, {"code": "variant_render_unready", "reasons": render["reasons"]})
    return [
        {"material_revision_id": output["material_revision_id"], "content_hash_snapshot": output["content_hash"],
         "role": "card_image", "slot_key": output["canvas_id"], "sort_order": index,
         "placement": {"canvas_id": output["canvas_id"]}}
        for index, output in enumerate(render["outputs"])
    ]


def _validate_graphic_assets(db: Session, project_id: int, master: ContentMasterRevision, refs: list[dict]) -> list[MaterialRevision]:
    from .content_masters import _verified_generated_asset

    expected = {item["slot_key"]: item for item in _graphic_source_refs(db, master)}
    if len(refs) != len(expected) or {item.get("slot_key") for item in refs} != set(expected):
        raise HTTPException(422, {"code": "variant_asset_set_mismatch"})
    orders = [item.get("sort_order") for item in refs]
    if any(type(order) is not int for order in orders) or set(orders) != set(range(len(refs))):
        raise HTTPException(422, {"code": "variant_asset_order_invalid"})
    materials = []
    for ref in refs:
        source = expected[ref["slot_key"]]
        if (ref.get("material_revision_id") != source["material_revision_id"] or ref.get("content_hash_snapshot") != source["content_hash_snapshot"]
                or ref.get("role") != "card_image" or ref.get("placement") != source["placement"]):
            raise HTTPException(422, {"code": "variant_asset_binding_mismatch"})
        material = db.get(MaterialRevision, source["material_revision_id"])
        visible = db.scalar(select(ProjectMaterialReference.id).where(
            ProjectMaterialReference.project_id == project_id, ProjectMaterialReference.material_revision_id == material.id,
            ProjectMaterialReference.status == "active",
        )) if material else None
        generated = db.scalars(select(ProjectWorkflowOutput).where(
            ProjectWorkflowOutput.project_id == project_id, ProjectWorkflowOutput.output_kind == "material_revision",
            ProjectWorkflowOutput.entity_id == material.id,
        )).all() if material and visible is None else []
        if material is None or (visible is None and not any(_verified_generated_asset(db, output, material) for output in generated)) or material.content_hash != source["content_hash_snapshot"] or material.material.kind != "image" or material.material.status != "active" or material.status in {"revoked", "archived"} or material.public_use_allowed is not True:
            raise HTTPException(422, {"code": "variant_asset_unready"})
        try:
            content = read_bytes_checked(db, material, require_public=True)
        except (HTTPException, OSError) as exc:
            raise HTTPException(422, {"code": "variant_asset_bytes_unverified"}) from exc
        if not material.mime_type or not material.mime_type.startswith("image/") or sniff_mime(content, None) != material.mime_type:
            raise HTTPException(422, {"code": "variant_asset_mime_invalid"})
        materials.append(material)
    return materials


def _video_source_refs(db: Session, master: ContentMasterRevision) -> list[dict]:
    from .video_documents import canonical_payload as canonical_video_payload

    source = canonical_video_payload(master.payload_json)
    stored = db.scalars(select(ContentMasterAssetRef).where(ContentMasterAssetRef.master_revision_id == master.id)).all()
    if any(ref.role != "shot_source" for ref in stored):
        raise HTTPException(422, {"code": "video_source_media_requires_explicit_mapping"})
    by_shot = {ref.slot_key: ref for ref in stored}
    shots = [shot for shot in source["shots"] if "source_material_revision_id" in shot]
    if len(by_shot) != len(stored) or set(by_shot) != {shot["id"] for shot in shots}:
        raise HTTPException(422, {"code": "video_source_b_roll_mismatch"})
    result = []
    for index, shot in enumerate(shots):
        ref = by_shot[shot["id"]]
        if ref.material_revision_id != shot["source_material_revision_id"] or ref.placement_json != {"shot_id": shot["id"]}:
            raise HTTPException(422, {"code": "video_source_b_roll_mismatch"})
        result.append({"material_revision_id": ref.material_revision_id, "content_hash_snapshot": ref.content_hash_snapshot,
                       "role": "b_roll", "slot_key": shot["id"], "sort_order": index, "placement": {"shot_id": shot["id"]}})
    return result


def _validate_video_assets(db: Session, project_id: int, master: ContentMasterRevision, refs: list[dict]) -> list[MaterialRevision]:
    from .content_masters import _verified_generated_asset

    expected = _video_source_refs(db, master)
    if len(refs) != len(expected) or not all(isinstance(ref, dict) for ref in refs):
        raise HTTPException(422, {"code": "variant_b_roll_set_mismatch"})
    materials = []
    for actual, source in zip(refs, expected, strict=True):
        if any(actual.get(key) != source[key] for key in source):
            raise HTTPException(422, {"code": "variant_b_roll_binding_mismatch"})
        material = db.get(MaterialRevision, source["material_revision_id"])
        if material is None:
            raise HTTPException(422, {"code": "variant_b_roll_unready"})
        visible = db.scalar(select(ProjectMaterialReference.id).where(
            ProjectMaterialReference.project_id == project_id, ProjectMaterialReference.material_revision_id == material.id,
            ProjectMaterialReference.status == "active",
        ))
        generated = db.scalars(select(ProjectWorkflowOutput).where(
            ProjectWorkflowOutput.project_id == project_id, ProjectWorkflowOutput.output_kind == "material_revision",
            ProjectWorkflowOutput.entity_id == material.id,
        )).all() if visible is None else []
        if ((visible is None and not any(_verified_generated_asset(db, output, material) for output in generated))
                or material.content_hash != source["content_hash_snapshot"] or material.material.kind not in {"image", "video"}
                or material.material.status != "active" or material.status in {"revoked", "archived"}
                or material.public_use_allowed is not True):
            raise HTTPException(422, {"code": "variant_b_roll_unready"})
        try:
            content = read_bytes_checked(db, material, require_public=True)
        except (HTTPException, OSError) as exc:
            raise HTTPException(422, {"code": "variant_b_roll_bytes_unverified"}) from exc
        expected_prefix = "image/" if material.material.kind == "image" else "video/"
        if not material.mime_type or not material.mime_type.startswith(expected_prefix) or sniff_mime(content, None) != material.mime_type:
            raise HTTPException(422, {"code": "variant_b_roll_mime_invalid"})
        materials.append(material)
    return materials


def _validate_wechat_assets(db: Session, project_id: int, refs: list[dict]) -> list[MaterialRevision]:
    from .content_masters import _verified_generated_asset

    if not refs:
        return []
    if len(refs) != 1 or any(ref.get(key) != value for key, value in {
        "role": "cover", "slot_key": "cover", "sort_order": 0, "placement": {"usage": "cover"},
    }.items() for ref in refs):
        raise HTTPException(422, {"code": "variant_cover_mapping_invalid"})
    ref = refs[0]
    material = db.get(MaterialRevision, ref.get("material_revision_id"))
    if material is None:
        raise HTTPException(422, {"code": "variant_cover_unready"})
    visible = db.scalar(select(ProjectMaterialReference.id).where(
        ProjectMaterialReference.project_id == project_id, ProjectMaterialReference.material_revision_id == material.id,
        ProjectMaterialReference.status == "active",
    ))
    generated = db.scalars(select(ProjectWorkflowOutput).where(
        ProjectWorkflowOutput.project_id == project_id, ProjectWorkflowOutput.output_kind == "material_revision",
        ProjectWorkflowOutput.entity_id == material.id,
    )).all() if visible is None else []
    if ((visible is None and not any(_verified_generated_asset(db, output, material) for output in generated))
            or material.content_hash != ref.get("content_hash_snapshot") or material.material.kind != "image"
            or material.material.status != "active" or material.status in {"revoked", "archived"}
            or material.public_use_allowed is not True):
        raise HTTPException(422, {"code": "variant_cover_unready"})
    try:
        content = read_bytes_checked(db, material, require_public=True)
    except (HTTPException, OSError) as exc:
        raise HTTPException(422, {"code": "variant_cover_bytes_unverified"}) from exc
    if not material.mime_type or not material.mime_type.startswith("image/") or sniff_mime(content, None) != material.mime_type:
        raise HTTPException(422, {"code": "variant_cover_mime_invalid"})
    return [material]


def _text_source_cover_refs(db: Session, master: ContentMasterRevision) -> list[dict]:
    refs = db.scalars(select(ContentMasterAssetRef).where(
        ContentMasterAssetRef.master_revision_id == master.id,
    ).order_by(ContentMasterAssetRef.sort_order, ContentMasterAssetRef.id)).all()
    if not refs:
        return []
    if len(refs) != 1 or refs[0].role != "cover" or refs[0].slot_key != "cover" or refs[0].sort_order != 0 or refs[0].placement_json != {"usage": "cover"}:
        raise HTTPException(422, {"code": "source_refs_require_exact_variant_mapping"})
    ref = refs[0]
    return [{"material_revision_id": ref.material_revision_id, "content_hash_snapshot": ref.content_hash_snapshot,
             "role": "cover", "slot_key": "cover", "sort_order": 0, "placement": {"usage": "cover"}}]


def _check_inputs(db: Session, row: ChannelVariantRevision) -> tuple[str, list[dict], list[dict]]:
    assets = db.scalars(select(ChannelVariantAssetRef).where(ChannelVariantAssetRef.variant_revision_id == row.id).order_by(ChannelVariantAssetRef.sort_order, ChannelVariantAssetRef.id)).all()
    evidence = db.scalars(select(ChannelVariantEvidenceRef).where(ChannelVariantEvidenceRef.variant_revision_id == row.id).order_by(ChannelVariantEvidenceRef.sort_order, ChannelVariantEvidenceRef.id)).all()
    asset_refs = [{"material_revision_id": item.material_revision_id, "content_hash_snapshot": item.content_hash_snapshot,
                   "role": item.role, "slot_key": item.slot_key, "sort_order": item.sort_order, "placement": item.placement_json,
                   "rights_snapshot": item.rights_snapshot_json} for item in assets]
    evidence_refs = [{"fact_pack_item_id": item.fact_pack_item_id, "snapshot_checksum": item.snapshot_checksum,
                      "role": item.role, "sort_order": item.sort_order, "content_locator_json": item.content_locator_json} for item in evidence]
    return _hash({"variant_id": row.id, "payload": row.payload_json, "payload_hash": row.payload_hash,
                  "context_hash": row.context_hash, "profile_hash": row.profile_hash, "adapter_key": row.adapter_key,
                  "adapter_version": row.adapter_version, "rule_hash": row.rule_hash, "assets": asset_refs,
                  "evidence": evidence_refs}), asset_refs, evidence_refs


def _drift_reasons(db: Session, row: ChannelVariantRevision) -> list[str]:
    from .content_masters import _serialize as serialize_master

    reasons: list[str] = []
    current_variant_id = db.scalar(select(ChannelVariantRevision.id).where(
        ChannelVariantRevision.content_unit_id == row.content_unit_id,
        ChannelVariantRevision.variant_key == row.variant_key,
    ).order_by(ChannelVariantRevision.revision_no.desc()).limit(1))
    if current_variant_id != row.id:
        reasons.append("variant_revision_not_current")
    master = db.get(ContentMasterRevision, row.source_master_revision_id)
    if (master is None or master.project_id != row.project_id or master.content_unit_id != row.content_unit_id
            or _current_source_id(db, row.content_unit_id) != row.source_master_revision_id):
        return ["source_master_not_current"]
    if (master.payload_hash != row.source_master_payload_hash or master.payload_hash != _hash(master.payload_json)
            or master.context_hash != row.source_master_context_hash
            or serialize_master(db, master)["readiness"]["state"] == "stale"):
        reasons.append("source_master_changed")
    _, asset_refs, evidence_refs = _check_inputs(db, row)
    try:
        _validate_evidence_refs(db, master, evidence_refs)
    except HTTPException:
        reasons.append("evidence_changed")
    try:
        if master.payload_schema == "graphic.master.v2":
            _validate_graphic_assets(db, row.project_id, master, asset_refs)
        elif master.payload_schema == "video.master.v2":
            _validate_video_assets(db, row.project_id, master, asset_refs)
        elif row.payload_schema == "wechat.article.v1":
            _validate_wechat_assets(db, row.project_id, asset_refs)
        elif asset_refs:
            reasons.append("asset_mapping_unavailable")
    except HTTPException:
        reasons.append("assets_or_render_changed")
    unit = db.get(ContentUnit, row.content_unit_id)
    identity = db.get(IdentitySnapshot, unit.identity_snapshot_id) if unit and unit.identity_snapshot_id else None
    if unit is None or unit.identity_snapshot_id != row.identity_snapshot_id:
        reasons.append("identity_changed")
    try:
        capability = capability_for(db, master.payload_schema, row.channel_id, row.content_form)
    except AdapterUnavailable:
        capability = {"executable": False}
    if not capability.get("executable"):
        reasons.append("profile_or_adapter_unavailable")
    else:
        profile = db.get(ChannelTemplateVersion, capability["profile_version_id"])
        form_profile = (profile.profile_json or {}).get("content_forms", {}).get(row.content_form, {}) if profile else {}
        rule_hash = _hash(form_profile.get("rule_sets") or [])
        if (row.profile_template_version_id != capability["profile_version_id"]
                or row.profile_version != str(capability["profile_version"])
                or row.profile_hash != capability["profile_hash"]
                or row.adapter_key != capability["adapter_key"]
                or row.adapter_version != capability["adapter_version"]
                or row.artifact_kind != capability["artifact_kind"]
                or row.payload_schema != capability["payload_schema"]
                or row.rule_hash != rule_hash):
            reasons.append("profile_or_adapter_changed")
        elif _hash(_variant_context(master, unit.identity_snapshot_id if unit else None,
                                    identity.checksum if identity else None, row.channel_id, row.content_form,
                                    capability, rule_hash)) != row.context_hash:
            reasons.append("variant_context_changed")
    return reasons


def projected_variant_checks(db: Session, row: ChannelVariantRevision) -> dict:
    input_hash, _, _ = _check_inputs(db, row)
    drift_reasons = _drift_reasons(db, row)
    required = ("variant_schema", "variant_evidence", "variant_rights", "variant_profile")
    if row.payload_schema == "xiaohongshu.image_note.v1":
        required = (*required, "variant_render")
    required = (*required, "variant_package")
    adapter_hash = _hash({"key": row.adapter_key, "version": row.adapter_version})
    items = []
    for kind in required:
        latest = db.scalar(select(ChannelVariantCheckRun).where(
            ChannelVariantCheckRun.variant_revision_id == row.id, ChannelVariantCheckRun.check_kind == kind,
        ).order_by(ChannelVariantCheckRun.id.desc()).limit(1))
        is_current = bool(not drift_reasons and latest and latest.input_hash == input_hash and latest.profile_hash == row.profile_hash
                          and latest.adapter_hash == adapter_hash and latest.rule_hash == row.rule_hash)
        items.append({"id": latest.id if latest else None, "check_kind": kind, "input_hash": latest.input_hash if latest else None,
                      "is_current": is_current, "stored_status": latest.status if latest else None,
                      "status": latest.status if is_current else "stale" if latest else "incomplete",
                      "report": {"reasons": drift_reasons} if drift_reasons else latest.report_json if latest else {"reason": "check_missing"}})
    return {"items": items, "ready": not drift_reasons and all(item["status"] == "pass" for item in items), "drift_reasons": drift_reasons}


def _profile_check(db: Session, row: ChannelVariantRevision, assets: list[dict]) -> tuple[str, dict]:
    profile = db.get(ChannelTemplateVersion, row.profile_template_version_id)
    form = (profile.profile_json or {}).get("content_forms", {}).get(row.content_form) if profile else None
    if profile is None or profile.status != "published" or not isinstance(form, dict):
        return "blocker", {"reasons": ["published_profile_missing"]}
    reasons = []
    media = form.get("media_requirements") or {}
    if not isinstance(media, dict):
        return "incomplete", {"reasons": ["media_policy_unavailable"], "coverage": {"profile": "verified", "media": "unknown", "rules": "unknown", "remote_publisher": "unverified"}}
    if media.get("cover") == "required" and not (
        any(ref["role"] == "cover" for ref in assets)
        or row.payload_schema == "xiaohongshu.image_note.v1" and any(ref["role"] == "card_image" for ref in assets)
    ):
        reasons.append("cover_required")
    if media.get("inline") == "required" and not assets:
        reasons.append("inline_media_required")
    rules = form.get("rule_sets") or []
    unsupported_rules = not isinstance(rules, list) or any(
        not isinstance(rule, str) or rule not in {"rule.media.required", "rule.media.public_rights"} for rule in rules
    )
    return ("blocker" if reasons else "incomplete" if unsupported_rules else "pass", {
        "reasons": reasons or (["rule_executor_unavailable"] if unsupported_rules else []),
        "coverage": {"profile": "verified", "media": "deterministic", "rules": "unknown" if unsupported_rules else "deterministic", "remote_publisher": "unverified"},
    })


def _evidence_check(db: Session, row: ChannelVariantRevision, assets: list[dict], evidence: list[dict]) -> tuple[str, dict]:
    master = db.get(ContentMasterRevision, row.source_master_revision_id)
    try:
        _validate_evidence_refs(db, master, evidence)
    except HTTPException as exc:
        return "blocker", {"reasons": [exc.detail.get("code", "evidence_invalid") if isinstance(exc.detail, dict) else "evidence_invalid"]}
    if not evidence:
        try:
            adapter, _ = executable_adapter_for(db, master.payload_schema, row.channel_id, row.content_form)
            source_projection = adapter.adapt(master.payload_json, asset_refs=assets, evidence_refs=[])
        except AdapterUnavailable:
            source_projection = None
        if source_projection != row.payload_json:
            return "incomplete", {"reasons": ["semantic_delta_requires_review"], "coverage": {"exact_refs": "none", "semantic_claims": "unknown"}}
    else:
        return "incomplete", {"reasons": ["citation_semantics_unverified"], "coverage": {"exact_refs": "verified", "semantic_claims": "unknown", "ref_count": len(evidence)}}
    return "pass", {"reasons": [], "coverage": {"exact_refs": "not_applicable", "semantic_claims": "source_equivalent", "ref_count": 0}}


def _rights_check(db: Session, row: ChannelVariantRevision, assets: list[dict]) -> tuple[str, dict]:
    master = db.get(ContentMasterRevision, row.source_master_revision_id)
    try:
        if row.payload_schema == "xiaohongshu.image_note.v1":
            _validate_graphic_assets(db, row.project_id, master, assets)
        elif row.payload_schema == "douyin.spoken_script.v1":
            _validate_video_assets(db, row.project_id, master, assets)
        elif row.payload_schema == "wechat.article.v1":
            _validate_wechat_assets(db, row.project_id, assets)
        elif assets:
            return "blocker", {"reasons": ["asset_mapping_unavailable"]}
    except HTTPException as exc:
        return "blocker", {"reasons": [exc.detail.get("code", "rights_unready") if isinstance(exc.detail, dict) else "rights_unready"]}
    return "pass", {"reasons": [], "coverage": {"exact_media_bytes_and_public_use": "verified" if assets else "not_applicable", "ref_count": len(assets)}}


def _render_check(db: Session, row: ChannelVariantRevision, assets: list[dict]) -> tuple[str, dict]:
    master = db.get(ContentMasterRevision, row.source_master_revision_id)
    try:
        _validate_graphic_assets(db, row.project_id, master, assets)
    except HTTPException as exc:
        return "blocker", {"reasons": [exc.detail.get("code", "render_unready") if isinstance(exc.detail, dict) else "render_unready"]}
    return "pass", {"reasons": [], "coverage": {"exact_render_attestation": "verified"}}


def get_variant_checks(db: Session, project_id: int, unit_id: int, variant_id: int, user: User) -> dict:
    owned_unit(db, project_id, unit_id, user)
    row = db.get(ChannelVariantRevision, variant_id)
    if row is None or row.project_id != project_id or row.content_unit_id != unit_id:
        raise HTTPException(404, "ChannelVariant版本不存在")
    return projected_variant_checks(db, row)


def run_variant_checks(db: Session, project_id: int, unit_id: int, variant_id: int, user: User) -> dict:
    owned_unit(db, project_id, unit_id, user, mutate=True)
    row = db.get(ChannelVariantRevision, variant_id)
    if row is None or row.project_id != project_id or row.content_unit_id != unit_id:
        raise HTTPException(404, "ChannelVariant版本不存在")
    current = db.scalar(select(ChannelVariantRevision.id).where(
        ChannelVariantRevision.content_unit_id == unit_id, ChannelVariantRevision.variant_key == row.variant_key,
    ).order_by(ChannelVariantRevision.revision_no.desc()).limit(1))
    if current != row.id or _drift_reasons(db, row):
        raise HTTPException(409, {"code": "variant_not_current"})
    input_hash, assets, evidence = _check_inputs(db, row)
    try:
        canonical = canonical_payload(row.payload_schema, row.payload_json, asset_refs=assets, evidence_refs=evidence)
        reasons = [] if canonical == row.payload_json and _hash(canonical) == row.payload_hash else ["payload_hash_or_canonical_mismatch"]
    except VariantDocumentError as exc:
        reasons = [str(exc)]
    results = {"variant_schema": ("blocker" if reasons else "pass", {"reasons": reasons})}
    results["variant_profile"] = _profile_check(db, row, assets)
    results["variant_evidence"] = _evidence_check(db, row, assets, evidence)
    results["variant_rights"] = _rights_check(db, row, assets)
    if row.payload_schema == "xiaohongshu.image_note.v1":
        results["variant_render"] = _render_check(db, row, assets)
    adapter_hash = _hash({"key": row.adapter_key, "version": row.adapter_version})
    for kind, (status, report) in results.items():
        db.add(ChannelVariantCheckRun(
            variant_revision_id=row.id, check_kind=kind, input_hash=input_hash, profile_hash=row.profile_hash,
            adapter_hash=adapter_hash, rule_hash=row.rule_hash, status=status, report_json=report, created_at=utcnow(),
        ))
    db.commit()
    return projected_variant_checks(db, row)


def adapt_preview(db: Session, *, project_id: int, unit_id: int, user: User, payload: dict) -> dict:
    _, unit = owned_unit(db, project_id, unit_id, user)
    master = db.get(ContentMasterRevision, payload["source_master_revision_id"])
    if master is None or master.project_id != project_id or master.content_unit_id != unit_id:
        raise HTTPException(404, "源 Master 不存在")
    if _current_source_id(db, unit_id) != master.id or master.payload_hash != _hash(master.payload_json):
        raise HTTPException(409, {"code": "variant_source_not_current"})
    if master.payload_hash != payload["expected_source_payload_hash"] or master.context_hash != payload["expected_source_context_hash"]:
        raise HTTPException(409, {"code": "variant_source_conflict"})
    if unit.identity_snapshot_id != master.identity_snapshot_id:
        raise HTTPException(409, {"code": "variant_identity_conflict"})
    from .content_masters import get_revision as get_master_revision

    source_projection = get_master_revision(db, project_id, unit_id, master.id, user)
    if source_projection["readiness"]["state"] == "stale":
        raise HTTPException(409, {"code": "variant_source_context_stale"})
    source_cover = _text_source_cover_refs(db, master) if master.payload_schema == "text.master.v2" and payload["channel_id"] == "wechat" and payload["content_form"] == "article" else []
    if source_projection["evidence"] or (source_projection["assets"] and master.payload_schema not in {"graphic.master.v2", "video.master.v2"} and not source_cover):
        raise HTTPException(422, {"code": "source_refs_require_exact_variant_mapping"})
    try:
        adapter, capability = executable_adapter_for(db, master.payload_schema, payload["channel_id"], payload["content_form"])
    except AdapterUnavailable as exc:
        raise HTTPException(422, {"code": "variant_adapter_unavailable", "reason": str(exc)}) from exc
    asset_refs = _graphic_source_refs(db, master) if master.payload_schema == "graphic.master.v2" else _video_source_refs(db, master) if master.payload_schema == "video.master.v2" else source_cover
    if master.payload_schema == "graphic.master.v2":
        _validate_graphic_assets(db, project_id, master, asset_refs)
    elif master.payload_schema == "video.master.v2":
        _validate_video_assets(db, project_id, master, asset_refs)
    elif capability["payload_schema"] == "wechat.article.v1":
        _validate_wechat_assets(db, project_id, asset_refs)
    try:
        adapted = adapter.adapt(master.payload_json, asset_refs=asset_refs, evidence_refs=[])
    except AdapterUnavailable as exc:
        raise HTTPException(422, {"code": "variant_adaptation_unavailable", "reason": str(exc)}) from exc
    return {
        "source_master_revision_id": master.id, "source_payload_hash": master.payload_hash, "source_context_hash": master.context_hash,
        "channel_id": payload["channel_id"], "content_form": payload["content_form"], "artifact_kind": capability["artifact_kind"],
        "payload_schema": capability["payload_schema"], "payload": adapted, "payload_hash": _hash(adapted),
        "profile_template_version_id": capability["profile_version_id"], "profile_hash": capability["profile_hash"],
        "adapter_key": capability["adapter_key"], "adapter_version": capability["adapter_version"],
        "asset_refs": asset_refs, "verified_remote": False,
    }


def save_revision(db: Session, *, project_id: int, unit_id: int, user: User, payload: dict) -> dict:
    project, unit = owned_unit(db, project_id, unit_id, user, mutate=True)
    key = payload["variant_key"]
    idempotency_key = payload["idempotency_key"]
    fingerprint = _hash(payload)
    existing = db.scalar(select(ChannelVariantRevision).where(
        ChannelVariantRevision.content_unit_id == unit_id,
        ChannelVariantRevision.variant_key == key,
        ChannelVariantRevision.idempotency_key == idempotency_key,
    ))
    if existing is not None:
        if existing.request_fingerprint != fingerprint:
            raise HTTPException(409, {"code": "variant_idempotency_conflict"})
        return _serialize(db, existing)
    if payload.get("llm_provenance"):
        raise HTTPException(422, {"code": "variant_refs_or_ai_not_yet_supported"})
    master = db.get(ContentMasterRevision, payload["source_master_revision_id"])
    if master is None or master.project_id != project_id or master.content_unit_id != unit_id:
        raise HTTPException(404, "源 Master 不存在")
    if _current_source_id(db, unit_id) != master.id or master.payload_hash != _hash(master.payload_json):
        raise HTTPException(409, {"code": "variant_source_not_current"})
    if master.payload_hash != payload["expected_source_payload_hash"] or master.context_hash != payload["expected_source_context_hash"]:
        raise HTTPException(409, {"code": "variant_source_conflict"})
    if unit.identity_snapshot_id != master.identity_snapshot_id:
        raise HTTPException(409, {"code": "variant_identity_conflict"})
    from .content_masters import get_revision as get_master_revision

    source_projection = get_master_revision(db, project_id, unit_id, master.id, user)
    if source_projection["readiness"]["state"] == "stale":
        raise HTTPException(409, {"code": "variant_source_context_stale"})
    source_cover = _text_source_cover_refs(db, master) if master.payload_schema == "text.master.v2" and payload["channel_id"] == "wechat" and payload["content_form"] == "article" else []
    if (master.payload_schema not in {"graphic.master.v2", "video.master.v2"} and db.scalar(select(ContentMasterAssetRef.id).where(ContentMasterAssetRef.master_revision_id == master.id).limit(1)) is not None and not source_cover) or db.scalar(select(ContentMasterEvidenceRef.id).where(ContentMasterEvidenceRef.master_revision_id == master.id).limit(1)) is not None:
        raise HTTPException(422, {"code": "source_refs_require_exact_variant_mapping"})
    evidence_refs = payload.get("evidence_refs", [])
    asset_refs = payload.get("asset_refs", [])
    if source_cover and asset_refs != source_cover:
        raise HTTPException(422, {"code": "source_cover_mapping_mismatch"})
    try:
        adapter, capability = executable_adapter_for(db, master.payload_schema, payload["channel_id"], payload["content_form"])
    except AdapterUnavailable as exc:
        raise HTTPException(422, {"code": "variant_adapter_unavailable", "reason": str(exc)}) from exc
    if payload.get("source_kind", "manual_edit") == "deterministic_adapt":
        try:
            expected_adapted = adapter.adapt(master.payload_json, asset_refs=asset_refs, evidence_refs=[])
        except AdapterUnavailable as exc:
            raise HTTPException(422, {"code": "variant_adaptation_unavailable", "reason": str(exc)}) from exc
    else:
        expected_adapted = None
    try:
        canonical = canonical_payload(capability["payload_schema"], payload["payload"], asset_refs=asset_refs, evidence_refs=evidence_refs)
    except VariantDocumentError as exc:
        raise HTTPException(422, {"code": "variant_payload_invalid", "reason": str(exc)}) from exc
    materials = _validate_graphic_assets(db, project_id, master, asset_refs) if master.payload_schema == "graphic.master.v2" else _validate_video_assets(db, project_id, master, asset_refs) if master.payload_schema == "video.master.v2" else _validate_wechat_assets(db, project_id, asset_refs) if capability["payload_schema"] == "wechat.article.v1" else []
    if master.payload_schema == "graphic.master.v2" and [card["image_ref_key"] for card in canonical["cards"]] != [ref["slot_key"] for ref in sorted(asset_refs, key=lambda item: item["sort_order"])]:
        raise HTTPException(422, {"code": "variant_asset_order_mismatch"})
    if master.payload_schema not in {"graphic.master.v2", "video.master.v2"} and capability["payload_schema"] != "wechat.article.v1" and asset_refs:
        raise HTTPException(422, {"code": "variant_asset_mapping_unavailable"})
    _validate_evidence_refs(db, master, evidence_refs)
    if expected_adapted is not None and canonical != expected_adapted:
        raise HTTPException(422, {"code": "variant_adapted_output_mismatch"})
    head = db.scalar(select(ChannelVariantRevision).where(
        ChannelVariantRevision.content_unit_id == unit_id,
        ChannelVariantRevision.variant_key == key,
    ).order_by(ChannelVariantRevision.revision_no.desc()).limit(1))
    if (head.revision_no if head else 0) != payload["expected_revision"]:
        raise HTTPException(409, {"code": "variant_revision_conflict"})
    if head is not None and (head.channel_id != payload["channel_id"] or head.content_form != payload["content_form"]):
        raise HTTPException(409, {"code": "variant_series_target_conflict"})
    profile = db.get(ChannelTemplateVersion, capability["profile_version_id"])
    form_profile = (profile.profile_json or {}).get("content_forms", {}).get(payload["content_form"], {})
    rule_hash = _hash(form_profile.get("rule_sets") or [])
    identity = db.get(IdentitySnapshot, unit.identity_snapshot_id) if unit.identity_snapshot_id else None
    context = _variant_context(master, unit.identity_snapshot_id, identity.checksum if identity else None, payload["channel_id"], payload["content_form"], capability, rule_hash)
    row = ChannelVariantRevision(
        project_id=project.id, content_unit_id=unit_id, variant_key=key, revision_no=payload["expected_revision"] + 1,
        parent_revision_id=head.id if head else None, source_master_revision_id=master.id,
        source_master_payload_hash=master.payload_hash, source_master_context_hash=master.context_hash,
        source_channel_id=master.channel_id, source_content_form=master.content_form,
        identity_snapshot_id=unit.identity_snapshot_id, channel_id=payload["channel_id"], content_form=payload["content_form"],
        artifact_kind=capability["artifact_kind"], profile_template_version_id=profile.id,
        profile_key=f"{payload['channel_id']}/{payload['content_form']}", profile_version=str(profile.version), profile_hash=capability["profile_hash"],
        adapter_key=capability["adapter_key"], adapter_version=capability["adapter_version"], rule_hash=rule_hash,
        payload_schema=capability["payload_schema"], payload_json=canonical, payload_hash=_hash(canonical), context_hash=_hash(context),
        source_kind=payload.get("source_kind", "manual_edit"), edit_summary_json=payload.get("edit_summary", {}),
        idempotency_key=idempotency_key, request_fingerprint=fingerprint, created_by=user.email, created_at=utcnow(),
    )
    db.add(row)
    try:
        db.flush()
        for ref, material in zip(asset_refs, materials, strict=True):
            db.add(ChannelVariantAssetRef(
                variant_revision_id=row.id, material_revision_id=material.id, role=ref["role"], slot_key=ref["slot_key"],
                sort_order=ref["sort_order"], placement_json=ref["placement"],
                rights_snapshot_json={"rights_status": material.rights_status, "public_use_allowed": material.public_use_allowed,
                                      "model_use_allowed": material.model_use_allowed, "commercial_use_allowed": material.commercial_use_allowed},
                content_hash_snapshot=material.content_hash, created_at=utcnow(),
            ))
        for ref in evidence_refs:
            db.add(ChannelVariantEvidenceRef(
                variant_revision_id=row.id, fact_pack_item_id=ref["fact_pack_item_id"], role=ref.get("role", "claim"),
                content_locator_json=ref["content_locator_json"], sort_order=ref.get("sort_order", 0),
                snapshot_checksum=ref["snapshot_checksum"], created_at=utcnow(),
            ))
        record_project_event(db, project_id=project_id, event_type="channel_variant.saved", actor=user.email, entity_type="channel_variant_revision", entity_id=row.id, payload={"unit_id": unit_id, "variant_key": key, "revision_no": row.revision_no})
        db.flush()
        db.expire_all()
        project, unit = owned_unit(db, project_id, unit_id, user)
        master = db.get(ContentMasterRevision, row.source_master_revision_id)
        identity = db.get(IdentitySnapshot, unit.identity_snapshot_id) if unit.identity_snapshot_id else None
        try:
            latest_capability = capability_for(db, master.payload_schema, row.channel_id, row.content_form)
        except AdapterUnavailable as exc:
            db.rollback()
            raise HTTPException(409, {"code": "variant_profile_changed"}) from exc
        if not latest_capability.get("executable"):
            db.rollback()
            raise HTTPException(409, {"code": "variant_profile_changed"})
        latest_context = _variant_context(master, unit.identity_snapshot_id, identity.checksum if identity else None, row.channel_id, row.content_form, latest_capability, rule_hash)
        current_master = get_master_revision(db, project_id, unit_id, master.id, user)
        try:
            _validate_evidence_refs(db, master, evidence_refs)
            if master.payload_schema == "graphic.master.v2":
                _validate_graphic_assets(db, project_id, master, asset_refs)
            elif master.payload_schema == "video.master.v2":
                _validate_video_assets(db, project_id, master, asset_refs)
            elif row.payload_schema == "wechat.article.v1":
                _validate_wechat_assets(db, project_id, asset_refs)
        except HTTPException:
            db.rollback()
            raise HTTPException(409, {"code": "variant_refs_changed"}) from None
        if project.status == "archived" or unit.status == "archived" or unit.identity_snapshot_id != master.identity_snapshot_id or current_master["readiness"]["state"] == "stale" or _current_source_id(db, unit_id) != master.id or master.payload_hash != _hash(master.payload_json) or _hash(latest_context) != row.context_hash:
            db.rollback()
            raise HTTPException(409, {"code": "variant_context_conflict"})
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, {"code": "variant_concurrent_conflict"}) from exc
    db.refresh(row)
    return _serialize(db, row)
