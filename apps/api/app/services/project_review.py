"""Project-scoped Candidate freeze and separate content decisions."""

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import (
    ChannelVariantRevision,
    ContentAsset,
    ContentMasterRevision,
    ContentUnit,
    Draft,
    FactPack,
    FactPackItem,
    IdentitySnapshot,
    ProjectWorkflowOutput,
    Review,
    User,
    WorkflowRun,
    utcnow,
)
from .candidates import asset_v2_columns, build_manifest_v2, candidate_hash, readiness_reasons_v2
from .project_authorization import authorize_project_asset
from .project_events import record_project_event
from .project_evidence import current_boundary


def _blocked(code: str, *reasons: str) -> HTTPException:
    return HTTPException(409, {"code": code, "reasons": list(reasons)})


def live_evidence_reasons(db: Session, project_id: int, manifest: dict) -> list[str]:
    evidence = manifest.get("evidence") or {}
    boundary = current_boundary(db, project_id)
    if boundary is None or boundary.id != evidence.get("boundary_id"):
        return ["project_boundary_changed"]
    pack = db.get(FactPack, boundary.fact_pack_id)
    if pack is None or pack.status != "frozen" or pack.version != boundary.fact_pack_version or pack.checksum != boundary.fact_pack_checksum:
        return ["fact_pack_changed"]
    items = db.scalars(select(FactPackItem).where(FactPackItem.fact_pack_id == pack.id)).all()
    return [f"evidence_rights_unready:{item.id}" for item in items if item.public_use_allowed is not True or item.public_use_revoked_at is not None or item.evidence_kind == "legacy_untyped" or not item.snapshot_checksum]


def _mutable_unit(db: Session, project_id: int, unit_id: int, user: User) -> ContentUnit:
    from ..routers.content_projects import mutable_project, owned_unit

    mutable_project(db, project_id, user)
    unit = owned_unit(db, project_id, unit_id, user)
    if unit.status == "archived":
        raise _blocked("archived_unit", "已归档单元只可查看历史")
    return unit


def _candidate(db: Session, project_id: int, unit_id: int, candidate_id: int, user: User, *, mutate: bool) -> ContentAsset:
    asset = db.get(ContentAsset, candidate_id)
    if asset is None or asset.project_id != project_id or asset.content_unit_id != unit_id:
        raise HTTPException(404, "候选内容不存在")
    authorize_project_asset(db, asset, user, mutate=mutate)
    return asset


def _source(db: Session, unit: ContentUnit, project_output_id: int) -> tuple[ProjectWorkflowOutput, WorkflowRun, Draft]:
    output = db.get(ProjectWorkflowOutput, project_output_id)
    if output is None or output.project_id != unit.project_id or output.unit_id != unit.id or output.output_kind != "draft":
        raise _blocked("unsupported_source", "没有可验证的本单元稿件输出")
    run = db.get(WorkflowRun, output.run_id)
    draft = db.get(Draft, output.entity_id)
    if run is None or run.content_unit_id != unit.id or draft is None or draft.content_job.workflow_run_id != run.id:
        raise _blocked("unsupported_source", "输出、运行与内容单元血缘不一致")
    if run.identity_snapshot_id is None or run.identity_snapshot_id != unit.identity_snapshot_id:
        raise _blocked("identity_mismatch", "运行身份快照与单元不一致")
    if unit.channel_id is not None and draft.content_job.channel != unit.channel_id:
        raise _blocked("source_mismatch", "稿件渠道与内容单元不一致")
    latest = db.scalar(select(Draft).where(Draft.content_job_id == draft.content_job_id).order_by(Draft.revision_no.desc()).limit(1))
    if latest is None or latest.id != draft.id:
        raise _blocked("stale_source", "工作流输出所指稿件已有更新修订，需生成新的可追溯输出")
    return output, run, draft


def build_manifest_v3(db: Session, unit: ContentUnit, output: ProjectWorkflowOutput, run: WorkflowRun, draft: Draft) -> dict:
    snapshot = db.get(IdentitySnapshot, unit.identity_snapshot_id)
    boundary = current_boundary(db, unit.project_id)
    topic = draft.content_job.topic_brief
    if snapshot is None or boundary is None or topic is None or topic.fact_pack.status != "frozen":
        raise _blocked("readiness_blocked", "缺少真实身份快照或冻结事实边界")
    if (boundary.fact_pack_id, boundary.fact_pack_version, boundary.fact_pack_checksum) != (topic.fact_pack_id, topic.fact_pack_version, topic.fact_pack.checksum):
        raise _blocked("evidence_mismatch", "项目事实边界与稿件证据不一致")
    try:
        manifest = build_manifest_v2(db, draft)
    except (KeyError, ValueError) as exc:
        raise _blocked("unsupported_source", str(exc)) from exc
    reasons = readiness_reasons_v2(db, draft, manifest)
    if not draft.title or not draft.body or reasons:
        raise _blocked("readiness_blocked", *(reasons or ["稿件缺少可发布标题或正文"]))
    execution = manifest.get("execution") or {}
    if execution.get("workflow_run_id") != run.id or execution.get("workflow_checksum") != run.definition_checksum:
        raise _blocked("workflow_mismatch", "稿件执行快照与项目运行不一致")
    manifest.update({
        "schema_version": 3,
        "project": {"id": unit.project_id, "unit_id": unit.id, "modality": unit.modality, "channel": draft.content_job.channel},
        "identity": {"snapshot_id": snapshot.id, "checksum": snapshot.checksum},
        "evidence": {"boundary_id": boundary.id, "fact_pack_id": boundary.fact_pack_id, "version": boundary.fact_pack_version, "checksum": boundary.fact_pack_checksum},
        "production": {"project_output_id": output.id, "run_id": run.id, "workflow_id": run.workflow_id, "workflow_key": run.workflow_key, "workflow_version": run.workflow_version, "definition_checksum": run.definition_checksum, "node_id": output.node_id, "attempt_id": output.attempt_id},
        "source_revision": {"kind": "draft", "draft_id": draft.id, "revision_no": draft.revision_no, "input_hash": draft.input_hash},
    })
    evidence_reasons = live_evidence_reasons(db, unit.project_id, manifest)
    if evidence_reasons:
        raise _blocked("readiness_blocked", *evidence_reasons)
    return manifest


def freeze_candidate(db: Session, project_id: int, unit_id: int, project_output_id: int, user: User) -> ContentAsset:
    unit = _mutable_unit(db, project_id, unit_id, user)
    output, run, draft = _source(db, unit, project_output_id)
    manifest = build_manifest_v3(db, unit, output, run, draft)
    frozen_hash = candidate_hash(manifest)
    existing = db.scalar(select(ContentAsset).where(ContentAsset.project_id == project_id, ContentAsset.content_unit_id == unit_id, ContentAsset.candidate_hash == frozen_hash).limit(1))
    if existing is not None:
        return existing
    topic = draft.content_job.topic_brief
    columns = asset_v2_columns(manifest)
    asset = ContentAsset(
        project_id=project_id, content_unit_id=unit_id, identity_snapshot_id=unit.identity_snapshot_id,
        workflow_run_id=run.id, draft_id=draft.id, topic_brief_id=topic.id,
        channel=draft.content_job.channel, title=draft.title, final_body=draft.body,
        structured_json=draft.structured_json, fact_pack_id=topic.fact_pack_id,
        fact_pack_version=topic.fact_pack_version, fact_pack_checksum=topic.fact_pack.checksum,
        approved_revision=None, status="frozen", candidate_hash=frozen_hash,
        approved_candidate_hash=None, candidate_manifest_json=manifest,
        mother_revision_id=draft.mother_revision_id, **columns,
    )
    db.add(asset)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        concurrent = db.scalar(select(ContentAsset).where(ContentAsset.project_id == project_id, ContentAsset.content_unit_id == unit_id, ContentAsset.candidate_hash == frozen_hash).limit(1))
        if concurrent is not None:
            return concurrent
        raise _blocked("freeze_conflict", "候选冻结并发冲突，请刷新后重试") from None
    record_project_event(db, project_id=project_id, event_type="candidate.frozen", actor=user.email, entity_type="content_asset", entity_id=asset.id, payload={"unit_id": unit_id, "candidate_hash": frozen_hash})
    db.commit()
    db.refresh(asset)
    return asset


def _master_freeze_manifest(db: Session, master: ContentMasterRevision, user: User) -> dict:
    from .production_validation import validate_live_v4_master

    return validate_live_v4_master(db, master, lock_live=True)


def freeze_master_candidate(db: Session, project_id: int, unit_id: int, master_revision_id: int, user: User, *, expected_payload_hash: str | None = None) -> ContentAsset:
    """Freeze a current Master as v4 without fabricating legacy Draft lineage."""
    unit = _mutable_unit(db, project_id, unit_id, user)
    master = db.get(ContentMasterRevision, master_revision_id)
    if master is None or master.project_id != project_id or master.content_unit_id != unit_id:
        raise HTTPException(404, "Master版本不存在")
    if expected_payload_hash != master.payload_hash:
        raise _blocked("master_payload_conflict", "Master已变化，请刷新后重试")
    manifest = _master_freeze_manifest(db, master, user)
    frozen_hash = candidate_hash(manifest)
    existing = db.scalar(select(ContentAsset).where(ContentAsset.project_id == project_id, ContentAsset.content_unit_id == unit_id, ContentAsset.candidate_hash == frozen_hash).limit(1))
    if existing:
        return existing
    payload = master.payload_json or {}
    title = payload.get("title") or unit.title
    body = payload.get("markdown") if master.modality == "text" else None
    asset = ContentAsset(
        project_id=project_id, content_unit_id=unit_id, identity_snapshot_id=master.identity_snapshot_id,
        channel=unit.channel_id or "unassigned", title=title, final_body=body, structured_json=payload,
        status="frozen", candidate_hash=frozen_hash, approved_candidate_hash=None, candidate_manifest_json=manifest,
        content_master_revision_id=master.id, artifact_kind=manifest["artifact_kind"], workflow_run_id=master.origin_workflow_run_id,
        fact_pack_id=manifest["evidence"]["fact_pack"]["id"], fact_pack_version=manifest["evidence"]["fact_pack"]["version"], fact_pack_checksum=manifest["evidence"]["fact_pack"]["checksum"],
        content_form=master.content_form,
    )
    db.add(asset)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        concurrent = db.scalar(select(ContentAsset).where(ContentAsset.project_id == project_id, ContentAsset.content_unit_id == unit_id, ContentAsset.candidate_hash == frozen_hash).limit(1))
        if concurrent:
            return concurrent
        raise _blocked("freeze_conflict", "候选冻结并发冲突，请刷新后重试") from None
    record_project_event(db, project_id=project_id, event_type="candidate.frozen", actor=user.email, entity_type="content_asset", entity_id=asset.id, payload={"unit_id": unit_id, "candidate_hash": frozen_hash, "schema_version": 4, "master_revision_id": master.id})
    db.flush()
    db.expire_all()
    try:
        _mutable_unit(db, project_id, unit_id, user)
        if candidate_hash(_master_freeze_manifest(db, master, user)) != frozen_hash:
            raise _blocked("freeze_context_conflict", "冻结输入在提交前已变化")
    except HTTPException:
        db.rollback()
        raise
    db.commit()
    db.refresh(asset)
    return asset


def freeze_variant_candidate(db: Session, project_id: int, unit_id: int, variant_revision_id: int, user: User, *, expected_payload_hash: str | None = None) -> ContentAsset:
    """Freeze one ready Variant series without turning its Master into the Candidate source."""
    from .candidates_v5 import build_manifest_v5, load_manifest_v5_inputs

    unit = _mutable_unit(db, project_id, unit_id, user)
    variant = db.get(ChannelVariantRevision, variant_revision_id)
    if variant is None or variant.project_id != project_id or variant.content_unit_id != unit_id:
        raise HTTPException(404, "ChannelVariant版本不存在")
    if expected_payload_hash != variant.payload_hash:
        raise _blocked("variant_payload_conflict", "渠道版本已变化，请刷新后重试")
    try:
        manifest = build_manifest_v5(load_manifest_v5_inputs(db, variant))
    except (KeyError, TypeError, ValueError) as exc:
        raise _blocked("variant_freeze_unready", str(exc)) from exc
    frozen_hash = candidate_hash(manifest)
    existing = db.scalar(select(ContentAsset).where(ContentAsset.project_id == project_id, ContentAsset.content_unit_id == unit_id, ContentAsset.candidate_hash == frozen_hash).limit(1))
    if existing:
        return existing
    render = manifest["render"]
    content = manifest["content"]
    title = content.get("title") or unit.title
    body = render.get("body_markdown") if isinstance(render, dict) else None
    asset = ContentAsset(
        project_id=project_id, content_unit_id=unit_id, identity_snapshot_id=variant.identity_snapshot_id,
        channel_variant_revision_id=variant.id, channel=variant.channel_id, content_form=variant.content_form,
        artifact_kind=variant.artifact_kind, title=title, final_body=body, structured_json=content,
        status="frozen", candidate_hash=frozen_hash, approved_candidate_hash=None, candidate_manifest_json=manifest,
        fact_pack_id=manifest["evidence"]["fact_pack"]["id"],
        fact_pack_version=manifest["evidence"]["fact_pack"]["version"],
        fact_pack_checksum=manifest["evidence"]["fact_pack"]["checksum"],
    )
    db.add(asset)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        concurrent = db.scalar(select(ContentAsset).where(ContentAsset.project_id == project_id, ContentAsset.content_unit_id == unit_id, ContentAsset.candidate_hash == frozen_hash).limit(1))
        if concurrent is not None:
            return concurrent
        raise _blocked("freeze_conflict", "候选冻结并发冲突，请刷新后重试") from None
    record_project_event(db, project_id=project_id, event_type="candidate.frozen", actor=user.email,
                         entity_type="content_asset", entity_id=asset.id,
                         payload={"unit_id": unit_id, "candidate_hash": frozen_hash, "schema_version": 5,
                                  "variant_revision_id": variant.id, "variant_key": variant.variant_key})
    db.flush()
    db.expire_all()
    try:
        _mutable_unit(db, project_id, unit_id, user)
        if variant.payload_hash != expected_payload_hash or candidate_hash(build_manifest_v5(load_manifest_v5_inputs(db, variant))) != frozen_hash:
            raise _blocked("freeze_context_conflict", "冻结输入在提交前已变化")
    except (HTTPException, KeyError, TypeError, ValueError) as exc:
        db.rollback()
        if isinstance(exc, HTTPException):
            raise
        raise _blocked("freeze_context_conflict", str(exc)) from exc
    db.commit()
    db.refresh(asset)
    return asset


def _validate_v3_approval(db: Session, asset: ContentAsset) -> None:
    draft = db.get(Draft, asset.draft_id) if asset.draft_id else None
    if draft is None:
        raise _blocked("unsupported_source", "非稿件候选缺少受支持的审批适配器")
    latest = db.scalar(select(Draft.revision_no).where(Draft.content_job_id == draft.content_job_id).order_by(Draft.revision_no.desc()).limit(1))
    if latest != draft.revision_no:
        raise _blocked("stale_candidate", "已有更新稿件修订")
    boundary = current_boundary(db, asset.project_id)
    if boundary is None or boundary.id != (asset.candidate_manifest_json or {}).get("evidence", {}).get("boundary_id"):
        raise _blocked("stale_evidence", "项目事实边界已变化")
    reasons = live_evidence_reasons(db, asset.project_id, asset.candidate_manifest_json or {})
    reasons.extend(readiness_reasons_v2(db, draft, asset.candidate_manifest_json or {}))
    if reasons:
        raise _blocked("readiness_blocked", *reasons)


def _validate_approval(db: Session, asset: ContentAsset, warning_dispositions: dict | None = None) -> None:
    from .production_validation import (
        validate_live_v4_candidate,
        validate_live_v5_candidate,
        validate_warning_dispositions,
    )

    schema = (asset.candidate_manifest_json or {}).get("schema_version")
    if schema == 5:
        validate_live_v5_candidate(db, asset, lock_live=True)
    elif schema == 4 or asset.content_master_revision_id is not None:
        manifest = validate_live_v4_candidate(db, asset, lock_live=True)
        validate_warning_dispositions(manifest, warning_dispositions)
    elif schema == 3:
        _validate_v3_approval(db, asset)
    else:
        raise _blocked("candidate_schema", "不支持的项目候选清单版本")


def decide_candidate(db: Session, project_id: int, unit_id: int, candidate_id: int, expected_hash: str, decision: str, comment: str | None, user: User, warning_dispositions: dict | None = None) -> ContentAsset:
    _mutable_unit(db, project_id, unit_id, user)
    asset = _candidate(db, project_id, unit_id, candidate_id, user, mutate=True)
    schema = (asset.candidate_manifest_json or {}).get("schema_version")
    if schema == 5:
        from .production_validation import validate_live_v5_candidate

        validate_live_v5_candidate(db, asset, lock_live=True)
    else:
        current_candidate_id = db.scalar(select(ContentAsset.id).where(
            ContentAsset.project_id == project_id,
            ContentAsset.content_unit_id == unit_id,
        ).order_by(ContentAsset.id.desc()).limit(1))
        if current_candidate_id != asset.id:
            raise _blocked("historical_candidate", "历史候选只可查看，不能重新审批或退改")
    if expected_hash != asset.candidate_hash or candidate_hash(asset.candidate_manifest_json or {}) != asset.candidate_hash:
        raise _blocked("candidate_mismatch", "冻结候选哈希不一致")
    if decision == "approved":
        _validate_approval(db, asset, warning_dispositions)
        if asset.status == "approved" and asset.approved_candidate_hash == asset.candidate_hash:
            return asset
    elif decision != "changes_requested":
        raise HTTPException(422, "不支持的内容审核决定")
    elif asset.status == "approved":
        raise _blocked("approved_candidate", "已批准候选保持历史不变；修改内容须产生新候选")
    review = Review(
        content_asset_id=asset.id, draft_id=asset.draft_id, revision_no=(asset.candidate_manifest_json or {}).get("variant", {}).get("revision_no") if schema == 5 else (asset.candidate_manifest_json or {}).get("content_master", {}).get("revision_no") if schema == 4 else (asset.candidate_manifest_json or {}).get("revision_no"),
        reviewer_id=user.email, decision=decision, comment=comment, candidate_hash=asset.candidate_hash,
        approved_at=utcnow() if decision == "approved" else None,
        warning_dispositions_json=warning_dispositions,
    )
    db.add(review)
    if decision == "approved":
        asset.status = "approved"
        asset.approved_candidate_hash = asset.candidate_hash
        asset.approved_revision = review.revision_no
        asset.reviewer = user.email
    db.flush()
    record_project_event(db, project_id=project_id, event_type="content.approved" if decision == "approved" else "content.changes_requested", actor=user.email, entity_type="review", entity_id=review.id, payload={"unit_id": unit_id, "candidate_id": asset.id, "candidate_hash": asset.candidate_hash})
    if decision == "approved" and schema in {4, 5}:
        db.flush()
        db.expire_all()
        try:
            _mutable_unit(db, project_id, unit_id, user)
            _validate_approval(db, asset, warning_dispositions)
            if asset.candidate_hash != expected_hash:
                raise _blocked("candidate_mismatch", "审批提交前候选发生变化")
        except HTTPException:
            db.rollback()
            raise
    db.commit()
    db.refresh(asset)
    return asset
