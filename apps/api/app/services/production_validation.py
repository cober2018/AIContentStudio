"""One live gate for Master freeze, v4 approval, authorization and local delivery."""

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import (
    ContentAsset,
    ContentMasterAssetRef,
    ContentMasterCheckRun,
    ContentMasterRevision,
    ContentUnit,
    FactPack,
    FactPackItem,
    Material,
    MaterialRevision,
    ProjectFactBoundaryRevision,
    Review,
)
from .candidates import candidate_hash
from .candidates_v4 import build_manifest_v4, load_manifest_v4_inputs
from .content_masters import _evidence_check, _hash, _rights_check, _serialize, frozen_context
from .production_modalities import adapter_for


def _blocked(code: str, *reasons: str) -> HTTPException:
    return HTTPException(409, {"code": code, "reasons": list(reasons)})


def lock_live_resources(db: Session, master: ContentMasterRevision) -> None:
    """Keep system-shared rights writers outside the gate-to-commit window."""
    material_ids = select(ContentMasterAssetRef.material_revision_id).where(ContentMasterAssetRef.master_revision_id == master.id)
    parent_ids = select(MaterialRevision.material_id).where(MaterialRevision.id.in_(material_ids))
    boundary = db.get(ProjectFactBoundaryRevision, master.fact_boundary_revision_id) if master.fact_boundary_revision_id else None
    queries = [select(Material).where(Material.id.in_(parent_ids)).order_by(Material.id), select(MaterialRevision).where(MaterialRevision.id.in_(material_ids)).order_by(MaterialRevision.id)]
    if boundary:
        queries.extend([select(FactPack).where(FactPack.id == boundary.fact_pack_id), select(FactPackItem).where(FactPackItem.fact_pack_id == boundary.fact_pack_id).order_by(FactPackItem.id)])
    for query in queries:
        db.scalars(query.with_for_update().execution_options(populate_existing=True)).all()


def validate_live_v4_master(db: Session, master: ContentMasterRevision, *, require_current: bool = True, lock_live: bool = False, frozen_checks: list[dict] | None = None) -> dict:
    if lock_live:
        lock_live_resources(db, master)
    unit = db.get(ContentUnit, master.content_unit_id)
    if unit is None or unit.project_id != master.project_id:
        raise _blocked("master_mismatch", "Master所属内容单元不一致")
    projection = _serialize(db, master)
    if require_current:
        latest = db.scalar(select(ContentMasterRevision.id).where(ContentMasterRevision.content_unit_id == unit.id).order_by(ContentMasterRevision.revision_no.desc()).limit(1))
        if latest != master.id or unit.modality != master.modality or projection["readiness"]["state"] != "current":
            raise _blocked("stale_master", "必须使用当前且上下文有效的Master")
    if _hash(master.payload_json) != master.payload_hash or _hash(frozen_context(db, master)) != master.context_hash:
        raise _blocked("master_integrity", "Master内容或冻结上下文哈希不一致")
    for status, report in (_rights_check(db, projection), _evidence_check(db, master)):
        if status != "pass":
            raise _blocked("readiness_blocked", *report["reasons"])
    adapter = adapter_for(master.modality, master.payload_schema)
    if master.payload_schema != adapter.payload_schema:
        raise _blocked("master_schema", "Master适配器契约不一致")
    availability = adapter.freeze_availability(db, master)
    if not availability["available"]:
        raise _blocked("readiness_blocked", *availability["reasons"])
    try:
        manifest = build_manifest_v4(load_manifest_v4_inputs(db, master, require_current=require_current, frozen_checks=frozen_checks))
    except (TypeError, ValueError) as exc:
        raise _blocked("manifest_unready", str(exc)) from exc
    if any(check["status"] not in {"pass", "warning"} for check in manifest["checks"]):
        raise _blocked("checks_unready", "必需检查尚未全部通过")
    return manifest


def validate_warning_dispositions(manifest: dict, dispositions: dict | None) -> None:
    warnings = [row for row in manifest.get("checks", []) if row["status"] == "warning"]
    required = {f"{row['id']}:{row['input_hash']}" for row in warnings}
    supplied = dispositions or {}
    if set(supplied) != required or any(not isinstance(reason, str) or not reason.strip() or len(reason) > 1000 for reason in supplied.values()):
        raise _blocked("warning_dispositions_required", "必须明确处置准确检查ID与输入哈希对应的每条warning")


def validate_live_v4_candidate(db: Session, asset: ContentAsset, *, require_current: bool = True, require_approved: bool = False, lock_live: bool = False) -> dict:
    manifest = asset.candidate_manifest_json or {}
    if manifest.get("schema_version") != 4:
        raise _blocked("candidate_schema", "Master候选必须使用v4清单，禁止旧版本回退")
    try:
        intact = candidate_hash(manifest) == asset.candidate_hash
    except (TypeError, ValueError):
        intact = False
    if not intact:
        raise _blocked("candidate_integrity", "冻结候选哈希不一致")
    master = db.get(ContentMasterRevision, asset.content_master_revision_id) if asset.content_master_revision_id else None
    if master is None or master.project_id != asset.project_id or master.content_unit_id != asset.content_unit_id:
        raise _blocked("master_mismatch", "候选未绑定所属项目的准确Master")
    current = validate_live_v4_master(db, master, require_current=require_current, lock_live=lock_live, frozen_checks=manifest.get("checks") if not require_current else None)
    # Display titles and newer checks may change; frozen business provenance may not.
    for key in current:
        if key not in {"project", "checks"} and manifest.get(key) != current[key]:
            raise _blocked("candidate_provenance", f"冻结候选与Master不一致: {key}")
    frozen_project = manifest.get("project") or {}
    if any(frozen_project.get(key) != current["project"][key] for key in ("id", "unit_id", "modality", "channel", "content_form")):
        raise _blocked("candidate_provenance", "冻结项目/单元/形态不一致")
    if asset.identity_snapshot_id != master.identity_snapshot_id or asset.channel != master.channel_id or asset.content_form != master.content_form or asset.artifact_kind != current["artifact_kind"]:
        raise _blocked("candidate_provenance", "候选字段与冻结血缘不一致")
    frozen_checks = manifest.get("checks")
    if not isinstance(frozen_checks, list) or len(frozen_checks) != len(current["checks"]):
        raise _blocked("checks_unready", "冻结检查不完整")
    latest_checks = {check["kind"]: check for check in current["checks"]}
    seen = set()
    for check in frozen_checks:
        if not isinstance(check, dict):
            raise _blocked("checks_unready", "冻结检查格式无效")
        row = db.get(ContentMasterCheckRun, check.get("id"))
        kind = check.get("kind")
        if row is None or row.master_revision_id != master.id or kind in seen or kind not in latest_checks:
            raise _blocked("checks_unready", "冻结检查血缘无效")
        seen.add(kind)
        stored = {"id": row.id, "kind": row.check_kind, "profile_key": row.profile_key, "profile_version": row.profile_version, "input_hash": row.input_hash, "status": row.status, "report": row.report_json}
        if check != stored or any(check.get(key) != latest_checks[kind][key] for key in ("input_hash", "profile_key", "profile_version", "status")) or (check["status"] == "warning" and check != latest_checks[kind]):
            raise _blocked("checks_unready", "冻结检查已失效或被修改")
    if require_current:
        latest = db.scalar(select(ContentAsset.id).where(ContentAsset.content_unit_id == asset.content_unit_id).order_by(ContentAsset.id.desc()).limit(1))
        if latest != asset.id:
            raise _blocked("historical_candidate", "历史候选不能新增审批或授权")
    if require_approved:
        review = db.scalar(select(Review).where(Review.content_asset_id == asset.id, Review.decision == "approved", Review.candidate_hash == asset.candidate_hash).order_by(Review.id.desc()).limit(1))
        if asset.status not in {"approved", "exported"} or asset.approved_candidate_hash != asset.candidate_hash or review is None:
            raise _blocked("candidate_unapproved", "缺少绑定准确候选哈希的审批")
        validate_warning_dispositions(manifest, review.warning_dispositions_json)
    return manifest
