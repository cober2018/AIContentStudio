"""One live gate for Master freeze, v4 approval, authorization and local delivery."""


from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import (
    ChannelTemplateVersion,
    ChannelVariantAssetRef,
    ChannelVariantCheckRun,
    ChannelVariantRevision,
    ContentAsset,
    ContentMasterAssetRef,
    ContentMasterCheckRun,
    ContentMasterRevision,
    ContentUnit,
    CreativeBriefRevision,
    FactPack,
    FactPackItem,
    IdentitySnapshot,
    Material,
    MaterialRevision,
    ProjectFactBoundaryRevision,
    Review,
)
from .candidates import candidate_hash
from .candidates_v4 import build_manifest_v4, load_manifest_v4_inputs
from .candidates_v5 import build_manifest_v5, load_manifest_v5_inputs
from .channel_variants import (
    _check_inputs,
    _validate_graphic_assets,
    _validate_video_assets,
    source_check_exclusions,
)
from .content_masters import _evidence_check, _hash, _rights_check, _serialize, frozen_context
from .production_modalities import adapter_for


def latest_legacy_candidate_id(db: Session, unit_id: int) -> int | None:
    # V5 has its own channel series and must not supersede the legacy Unit series.
    return db.scalar(select(ContentAsset.id).where(
        ContentAsset.content_unit_id == unit_id,
        ContentAsset.channel_variant_revision_id.is_(None),
    ).order_by(ContentAsset.id.desc()).limit(1))


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
    warnings.extend(row for row in manifest.get("source_master", {}).get("warning_checks", []) if row["status"] == "warning")
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
        current_section = current[key]
        if key == "production" and "external_execution" not in manifest.get(key, {}):
            # Older frozen manifests remain byte-for-byte unchanged.
            current_section = {name: value for name, value in current_section.items() if name != "external_execution"}
        if key not in {"project", "checks"} and manifest.get(key) != current_section:
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
        latest = latest_legacy_candidate_id(db, asset.content_unit_id)
        if latest != asset.id:
            raise _blocked("historical_candidate", "历史候选不能新增审批或授权")
    if require_approved:
        review = db.scalar(select(Review).where(Review.content_asset_id == asset.id, Review.decision == "approved", Review.candidate_hash == asset.candidate_hash).order_by(Review.id.desc()).limit(1))
        if asset.status not in {"approved", "exported"} or asset.approved_candidate_hash != asset.candidate_hash or review is None:
            raise _blocked("candidate_unapproved", "缺少绑定准确候选哈希的审批")
        validate_warning_dispositions(manifest, review.warning_dispositions_json)
    return manifest


def _lock_live_v5_resources(db: Session, variant: ChannelVariantRevision) -> None:
    """Hold mutable source, profile and rights rows through the final decision commit."""
    master = db.get(ContentMasterRevision, variant.source_master_revision_id)
    boundary = db.get(ProjectFactBoundaryRevision, master.fact_boundary_revision_id) if master else None
    material_ids = select(ChannelVariantAssetRef.material_revision_id).where(ChannelVariantAssetRef.variant_revision_id == variant.id)
    parent_ids = select(MaterialRevision.material_id).where(MaterialRevision.id.in_(material_ids))
    queries = [
        select(ContentUnit).where(ContentUnit.id == variant.content_unit_id),
        select(ContentMasterRevision).where(ContentMasterRevision.id == variant.source_master_revision_id),
        select(ChannelVariantRevision).where(ChannelVariantRevision.id == variant.id),
        select(ChannelTemplateVersion).where(ChannelTemplateVersion.id == variant.profile_template_version_id),
        select(Material).where(Material.id.in_(parent_ids)).order_by(Material.id),
        select(MaterialRevision).where(MaterialRevision.id.in_(material_ids)).order_by(MaterialRevision.id),
    ]
    if boundary:
        queries.extend([
            select(FactPack).where(FactPack.id == boundary.fact_pack_id),
            select(FactPackItem).where(FactPackItem.fact_pack_id == boundary.fact_pack_id).order_by(FactPackItem.id),
        ])
    for query in queries:
        db.scalars(query.with_for_update().execution_options(populate_existing=True)).all()


def _validate_frozen_v5_history(db: Session, variant: ChannelVariantRevision, manifest: dict) -> None:
    """Existing authorizations use frozen lineage but still honor live rights and bytes."""
    source = manifest["source_master"]
    frozen_variant = manifest["variant"]
    target = manifest["target"]
    master = db.get(ContentMasterRevision, variant.source_master_revision_id)
    if (master is None or master.id != source["id"] or master.project_id != variant.project_id
            or master.content_unit_id != variant.content_unit_id or master.revision_no != source["revision_no"]
            or master.payload_schema != source["payload_schema"] or master.payload_hash != source["payload_hash"]
            or _hash(master.payload_json) != master.payload_hash or master.context_hash != source["context_hash"]
            or master.channel_id != source.get("channel") or master.content_form != source.get("content_form")
            or master.identity_snapshot_id != manifest["identity"]["id"]):
        raise _blocked("candidate_provenance", "历史候选来源Master血缘不一致")
    from .content_masters import projected_checks

    exclusions = source_check_exclusions(master, variant.payload_schema)
    live_checks = [check for check in projected_checks(db, master) if check["check_kind"] not in exclusions]
    frozen_warning_keys = {(check["id"], check["kind"], check["input_hash"])
                           for check in source.get("warning_checks", [])}
    live_warning_keys = {(check["id"], check["check_kind"], check["input_hash"])
                         for check in live_checks if check["status"] == "warning"}
    for check in source.get("warning_checks", []):
        stored = db.get(ContentMasterCheckRun, check["id"])
        if (stored is None or stored.master_revision_id != master.id
                or check != {"id": stored.id, "kind": stored.check_kind,
                             "profile_key": stored.profile_key, "profile_version": stored.profile_version,
                             "input_hash": stored.input_hash, "status": stored.status, "report": stored.report_json}):
            raise _blocked("checks_unready", "历史来源Master warning血缘不一致")
    if any(getattr(variant, column) != frozen_variant[key] for column, key in (
        ("variant_key", "variant_key"), ("revision_no", "revision_no"),
        ("source_master_revision_id", "source_master_revision_id"), ("identity_snapshot_id", "identity_snapshot_id"),
        ("source_channel_id", "source_channel"), ("source_content_form", "source_content_form"),
        ("payload_schema", "payload_schema"), ("payload_hash", "payload_hash"),
        ("context_hash", "context_hash"), ("source_kind", "source_kind"),
    )) or variant.payload_json != manifest["content"] or variant.channel_id != target["channel"] or variant.content_form != target["content_form"] or variant.artifact_kind != target["artifact_kind"]:
        raise _blocked("candidate_provenance", "历史渠道版本与冻结清单不一致")
    if (variant.source_master_payload_hash != master.payload_hash
            or variant.source_master_context_hash != master.context_hash
            or variant.identity_snapshot_id != master.identity_snapshot_id
            or variant.source_channel_id != master.channel_id
            or variant.source_content_form != master.content_form):
        raise _blocked("candidate_provenance", "历史渠道版本的源Master快照不一致")
    if (variant.profile_template_version_id != target["profile"]["id"] or variant.profile_hash != target["profile"]["hash"]
            or variant.profile_key != target["profile"]["key"] or variant.profile_version != target["profile"]["version"]
            or variant.adapter_key != target["adapter"]["key"] or variant.adapter_version != target["adapter"]["version"]
            or variant.rule_hash != target["rule_hash"]):
        raise _blocked("candidate_provenance", "历史渠道Profile/Adapter血缘不一致")
    profile = db.get(ChannelTemplateVersion, variant.profile_template_version_id)
    form_profile = (profile.profile_json or {}).get("content_forms", {}).get(variant.content_form) if profile else None
    if profile is None or not isinstance(form_profile, dict) or _hash(form_profile) != variant.profile_hash:
        raise _blocked("candidate_provenance", "冻结Profile版本或配置已损坏")
    identity = db.get(IdentitySnapshot, master.identity_snapshot_id)
    brief = db.get(CreativeBriefRevision, master.creative_brief_revision_id)
    boundary = db.get(ProjectFactBoundaryRevision, master.fact_boundary_revision_id)
    pack = db.get(FactPack, boundary.fact_pack_id) if boundary else None
    if (identity is None or identity.checksum != manifest["identity"]["checksum"] or brief is None
            or (brief.id, brief.revision_no, brief.checksum) != (manifest["brief"]["id"], manifest["brief"]["revision_no"], manifest["brief"]["checksum"])
            or boundary is None or (boundary.id, boundary.revision_no) != (manifest["evidence"]["boundary_id"], manifest["evidence"]["revision_no"])
            or pack is None or pack.status != "frozen" or (pack.id, pack.version, pack.checksum) != (
                manifest["evidence"]["fact_pack"]["id"], manifest["evidence"]["fact_pack"]["version"],
                manifest["evidence"]["fact_pack"]["checksum"])
            or (boundary.fact_pack_id, boundary.fact_pack_version, boundary.fact_pack_checksum) != (pack.id, pack.version, pack.checksum)):
        raise _blocked("candidate_provenance", "历史身份、Brief或事实边界血缘不一致")
    _, assets, evidence_refs = _check_inputs(db, variant)
    if assets != manifest["assets"] or evidence_refs != manifest["evidence_refs"]:
        raise _blocked("candidate_provenance", "历史素材或证据引用已变化")
    if master.payload_schema == "graphic.master.v2":
        _validate_graphic_assets(db, variant.project_id, master, assets)
    elif master.payload_schema == "video.master.v2":
        _validate_video_assets(db, variant.project_id, master, assets)
    else:
        from .channel_variants import _validate_text_target_assets

        _validate_text_target_assets(db, variant.project_id, assets, variant.payload_json, variant.payload_schema)
    for ref in assets:
        revision = db.get(MaterialRevision, ref["material_revision_id"])
        if revision is None or revision.content_hash != ref["content_hash_snapshot"]:
            raise _blocked("media_unready", "历史素材版本不一致")
        from .materials import verify_bytes_checked
        verify_bytes_checked(db, revision, require_public=True)
    items = db.scalars(select(FactPackItem).where(FactPackItem.fact_pack_id == pack.id)).all()
    if any(item.public_use_allowed is not True or item.public_use_revoked_at is not None or item.evidence_kind == "legacy_untyped" or not item.snapshot_checksum for item in items):
        raise _blocked("evidence_unready", "历史事实包中有失效证据")
    for ref in evidence_refs:
        item = db.get(FactPackItem, ref["fact_pack_item_id"])
        if item is None or item.fact_pack_id != pack.id or item.snapshot_checksum != ref["snapshot_checksum"]:
            raise _blocked("evidence_unready", "历史精确证据引用不一致")
    if any(check["status"] not in {"pass", "warning"} for check in live_checks):
        raise _blocked("checks_unready", "来源Master最新检查已阻断或失效")
    if "warning_checks" in source and frozen_warning_keys != live_warning_keys:
        raise _blocked("checks_unready", "来源Master warning 已变化，须重新审批")
    if "warning_checks" not in source and live_warning_keys:
        raise _blocked("warning_dispositions_required", "旧v5候选缺少来源Master warning快照")
    production = manifest["production"]
    if "external_execution" in production:
        from .creative_packages import external_material_sources

        if production["external_execution"] != external_material_sources(db, variant.project_id, assets):
            raise _blocked("candidate_provenance", "冻结外部成果血缘不一致")
    if (production["edit_summary"] != variant.edit_summary_json or production["created_by"] != variant.created_by
            or production.get("llm_provenance") != variant.llm_provenance_json):
        raise _blocked("candidate_provenance", "历史生产记录不一致")
    workflow = production.get("workflow")
    output = production.get("output")
    if master.origin_workflow_run_id != (workflow or {}).get("run_id") or master.origin_project_output_id != (output or {}).get("id"):
        raise _blocked("candidate_provenance", "历史Workflow血缘不一致")


def validate_live_v5_candidate(db: Session, asset: ContentAsset, *, require_current: bool = True,
                               require_approved: bool = False, lock_live: bool = False) -> dict:
    """Validate the sole Variant source and live safety without v3/v4 fallback."""
    manifest = asset.candidate_manifest_json or {}
    if manifest.get("schema_version") != 5:
        raise _blocked("candidate_schema", "渠道候选必须使用v5清单")
    try:
        intact = candidate_hash(manifest) == asset.candidate_hash
        build_manifest_v5({key: value for key, value in manifest.items() if key != "schema_version"})
    except (KeyError, TypeError, ValueError):
        intact = False
    if not intact:
        raise _blocked("candidate_integrity", "v5冻结清单或哈希不一致")
    legacy_sources = (asset.draft_id, asset.topic_brief_id, asset.mother_revision_id,
                      asset.content_master_revision_id, asset.workflow_run_id)
    variant = db.get(ChannelVariantRevision, asset.channel_variant_revision_id) if asset.channel_variant_revision_id else None
    if (any(value is not None for value in legacy_sources) or variant is None
            or variant.project_id != asset.project_id or variant.content_unit_id != asset.content_unit_id
            or variant.id != manifest["variant"]["id"]):
        raise _blocked("candidate_source_mismatch", "v5候选必须且只能使用本项目准确的渠道版本")
    from .channel_variants import validate_target_account

    account_context = validate_target_account(db, variant)
    if account_context != manifest["target"].get("account"):
        raise _blocked("candidate_target_account", "冻结目标账号与渠道版本不一致")
    if "export_metadata" in manifest:
        from .production_packages import public_export_metadata

        if public_export_metadata(db, manifest["assets"], manifest["evidence_refs"]) != manifest["export_metadata"]:
            raise _blocked("candidate_export_metadata", "冻结的公开来源或署名已变化")
    target = manifest["target"]
    pack = manifest["evidence"]["fact_pack"]
    if (asset.channel != target["channel"] or asset.content_form != target["content_form"]
            or asset.artifact_kind != target["artifact_kind"] or asset.identity_snapshot_id != manifest["identity"]["id"]
            or (asset.fact_pack_id, asset.fact_pack_version, asset.fact_pack_checksum) != (pack["id"], pack["version"], pack["checksum"])):
        raise _blocked("candidate_provenance", "候选投影列与冻结渠道或证据不一致")
    if lock_live:
        _lock_live_v5_resources(db, variant)
    if require_current:
        try:
            current = build_manifest_v5(load_manifest_v5_inputs(db, variant))
        except (KeyError, TypeError, ValueError, HTTPException) as exc:
            raise _blocked("candidate_stale", str(exc)) from exc
    else:
        _validate_frozen_v5_history(db, variant, manifest)
        current = manifest
    for section in ("identity", "brief", "evidence", "source_master", "variant", "target", "content",
                    "assets", "evidence_refs", "render", "production", "citations", "declarations"):
        frozen_section = manifest[section]
        current_section = current[section]
        if section == "production" and "external_execution" not in frozen_section:
            current_section = {key: value for key, value in current_section.items() if key != "external_execution"}
        if section == "source_master" and "warning_checks" not in frozen_section and current_section.get("warning_checks") == []:
            current_section = {key: value for key, value in current_section.items() if key != "warning_checks"}
        if frozen_section != current_section:
            raise _blocked("candidate_provenance", f"v5冻结来源或内容已变化: {section}")
    if any(manifest["project"].get(key) != current["project"][key] for key in ("id", "unit_id", "modality")):
        raise _blocked("candidate_provenance", "v5冻结项目或形态不一致")
    latest_checks = {check["kind"]: check for check in current["checks"]}
    if len(manifest["checks"]) != len(latest_checks):
        raise _blocked("checks_unready", "渠道候选检查不完整")
    for frozen in manifest["checks"]:
        stored = db.get(ChannelVariantCheckRun, frozen["id"])
        latest = latest_checks.get(frozen["kind"])
        if (stored is None or stored.variant_revision_id != variant.id or latest is None
                or frozen != {"id": stored.id, "kind": stored.check_kind, "input_hash": stored.input_hash,
                              "status": stored.status, "profile_hash": stored.profile_hash,
                              "adapter_hash": stored.adapter_hash, "rule_hash": stored.rule_hash,
                              "report": stored.report_json}
                or any(frozen[key] != latest[key] for key in ("kind", "input_hash", "status", "profile_hash", "adapter_hash", "rule_hash"))):
            raise _blocked("checks_unready", "渠道候选检查失效或血缘不一致")
    if require_current:
        latest_id = db.scalar(select(ContentAsset.id).join(
            ChannelVariantRevision, ContentAsset.channel_variant_revision_id == ChannelVariantRevision.id,
        ).where(ContentAsset.content_unit_id == asset.content_unit_id,
                ChannelVariantRevision.variant_key == variant.variant_key).order_by(ContentAsset.id.desc()).limit(1))
        if latest_id != asset.id:
            raise _blocked("historical_candidate", "同一渠道系列已有更新候选")
    if require_approved:
        review = db.scalar(select(Review).where(Review.content_asset_id == asset.id,
                                                 Review.decision == "approved", Review.candidate_hash == asset.candidate_hash)
                           .order_by(Review.id.desc()).limit(1))
        if asset.status not in {"approved", "exported"} or asset.approved_candidate_hash != asset.candidate_hash or review is None:
            raise _blocked("candidate_unapproved", "缺少绑定准确v5候选的内容审批")
        validate_warning_dispositions(manifest, review.warning_dispositions_json)
    return manifest
