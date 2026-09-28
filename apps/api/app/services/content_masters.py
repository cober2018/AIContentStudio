"""Append-only Content Master revisions and their frozen context."""

import hashlib
import json

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import (
    ContentMasterAssetRef,
    ContentMasterCheckRun,
    ContentMasterEvidenceRef,
    ContentMasterRevision,
    ContentProject,
    ContentUnit,
    Draft,
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
from .production_modalities import descriptor, validate_json_bounds, validate_payload
from .project_brief import current_brief
from .project_events import record_project_event
from .project_evidence import current_boundary


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def owned_unit(db: Session, project_id: int, unit_id: int, user: User, *, mutate: bool = False) -> tuple[ContentProject, ContentUnit]:
    project = db.get(ContentProject, project_id)
    unit = db.get(ContentUnit, unit_id)
    if project is None or unit is None or project.owner_user_id != user.id or unit.project_id != project_id:
        raise HTTPException(404, "内容单元不存在")
    if mutate and (project.status == "archived" or unit.status == "archived"):
        raise HTTPException(409, "已归档项目或单元仅可查看历史")
    return project, unit


def _context(db: Session, project: ContentProject, unit: ContentUnit, *, content_form: str | None) -> dict:
    snapshot = db.get(IdentitySnapshot, unit.identity_snapshot_id) if unit.identity_snapshot_id else None
    brief = current_brief(db, project.id)
    boundary = current_boundary(db, project.id)
    return {
        "identity": {"id": snapshot.id, "checksum": snapshot.checksum} if snapshot else None,
        "brief": {"id": brief.id, "checksum": brief.checksum} if brief else None,
        "boundary": {"id": boundary.id, "fact_pack_id": boundary.fact_pack_id, "checksum": boundary.fact_pack_checksum} if boundary else None,
        "channel_id": unit.channel_id,
        "content_form": content_form,
    }


def _serialize(db: Session, row: ContentMasterRevision) -> dict:
    context = _context(db, db.get(ContentProject, row.project_id), db.get(ContentUnit, row.content_unit_id), content_form=row.content_form)
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
    missing = [reason for key, reason in (("identity", "identity_missing"), ("brief", "brief_missing"), ("boundary", "evidence_missing")) if context[key] is None]
    return {
        "id": row.id, "project_id": row.project_id, "content_unit_id": row.content_unit_id,
        "revision_no": row.revision_no, "parent_revision_id": row.parent_revision_id,
        "modality": row.modality, "channel_id": row.channel_id, "content_form": row.content_form,
        "payload_schema": row.payload_schema, "payload": row.payload_json, "payload_hash": row.payload_hash,
        "context_hash": row.context_hash, "identity_snapshot_id": row.identity_snapshot_id,
        "creative_brief_revision_id": row.creative_brief_revision_id, "fact_boundary_revision_id": row.fact_boundary_revision_id,
        "source_kind": row.source_kind, "edit_summary": row.edit_summary_json,
        "origin_workflow_run_id": row.origin_workflow_run_id, "origin_project_output_id": row.origin_project_output_id,
        "readiness": {"state": "stale" if stale else "incomplete_context" if missing else "current", "reasons": stale + missing},
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


def check_input_hash(db: Session, row: ContentMasterRevision) -> str:
    inputs = _serialize(db, row)
    assets = []
    for ref in inputs["assets"]:
        material = db.get(MaterialRevision, ref["material_revision_id"])
        assets.append({"ref": ref, "live": {"hash": material.content_hash, "status": material.status, "public_use_allowed": material.public_use_allowed, "commercial_use_allowed": material.commercial_use_allowed, "rights_status": material.rights_status} if material else None})
    evidence = []
    for ref in inputs["evidence"]:
        item = db.get(FactPackItem, ref["fact_pack_item_id"])
        evidence.append({"ref": ref, "live": {"checksum": item.snapshot_checksum, "public_use_allowed": item.public_use_allowed, "revoked": item.public_use_revoked_at is not None, "kind": item.evidence_kind} if item else None})
    project = db.get(ContentProject, row.project_id)
    unit = db.get(ContentUnit, row.content_unit_id)
    return _hash({"payload_hash": row.payload_hash, "context_hash": row.context_hash, "current_context": _context(db, project, unit, content_form=row.content_form), "assets": assets, "evidence": evidence, "profile_key": descriptor(row.modality).payload_schema, "profile_version": "1"})


def current_checks(db: Session, project_id: int, unit_id: int, master_id: int, user: User) -> list[dict]:
    get_revision(db, project_id, unit_id, master_id, user)
    row = db.get(ContentMasterRevision, master_id)
    input_hash = check_input_hash(db, row)
    latest = {}
    for kind in descriptor(row.modality).required_checks:
        latest[kind] = db.scalar(select(ContentMasterCheckRun).where(ContentMasterCheckRun.master_revision_id == master_id, ContentMasterCheckRun.check_kind == kind).order_by(ContentMasterCheckRun.id.desc()).limit(1))
    result = []
    for kind, check in latest.items():
        is_current = check is not None and check.input_hash == input_hash and check.profile_key == descriptor(row.modality).payload_schema and check.profile_version == "1"
        result.append({"id": check.id if check else None, "check_kind": kind, "input_hash": check.input_hash if check else None, "is_current": is_current, "stored_status": check.status if check else None, "status": check.status if is_current else "stale" if check else "incomplete", "report": check.report_json if check else {"reason": "check_missing"}})
    return result


def run_checks(db: Session, project_id: int, unit_id: int, master_id: int, user: User) -> list[dict]:
    _, unit = owned_unit(db, project_id, unit_id, user, mutate=True)
    row = db.get(ContentMasterRevision, master_id)
    if row is None or row.project_id != project_id or row.content_unit_id != unit.id:
        raise HTTPException(404, "Master版本不存在")
    inputs = _serialize(db, row)
    input_hash = check_input_hash(db, row)
    descriptor_row = descriptor(row.modality)
    payload_errors = validate_payload(row.modality, row.payload_json)
    results = {
        "master_schema": ("blocker" if payload_errors else "pass", {"reasons": payload_errors}),
        "evidence": ("incomplete" if row.fact_boundary_revision_id is None else "pass", {"reason": "evidence_missing" if row.fact_boundary_revision_id is None else None}),
        "rights": ("pass" if not inputs["assets"] else "incomplete", {"reason": "asset_rights_live_check_required" if inputs["assets"] else None}),
        "render": ("incomplete" if validate_payload(row.modality, row.payload_json, for_freeze=True) else "pass", {"reasons": validate_payload(row.modality, row.payload_json, for_freeze=True)}),
    }
    rows = []
    for kind in descriptor_row.required_checks:
        status, report = results[kind]
        if inputs["readiness"]["state"] == "stale":
            status, report = "stale", {"reasons": inputs["readiness"]["reasons"]}
        check = ContentMasterCheckRun(master_revision_id=row.id, check_kind=kind, profile_key=f"{row.modality}.master.v1", profile_version="1", input_hash=input_hash, status=status, report_json=report, created_at=utcnow())
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


def save_revision(db: Session, *, project_id: int, unit_id: int, user: User, payload: dict, workflow_seed: bool = False) -> dict:
    project, unit = owned_unit(db, project_id, unit_id, user, mutate=True)
    modality = payload.get("modality") or unit.modality
    if modality != unit.modality:
        raise HTTPException(422, "Master形态必须与内容单元一致")
    desc = descriptor(modality)
    errors = validate_payload(modality, payload["payload"])
    errors.extend(validate_json_bounds(payload))
    if errors:
        raise HTTPException(422, {"code": "invalid_master_payload", "reasons": errors})
    context = _context(db, project, unit, content_form=payload.get("content_form"))
    refs_fingerprint = {"assets": payload.get("asset_refs", []), "evidence": payload.get("evidence_refs", [])}
    payload_schema = payload.get("payload_schema") or desc.payload_schema
    if payload_schema != desc.payload_schema:
        raise HTTPException(422, "Master schema必须匹配当前形态支持的版本")
    if payload.get("source_kind", "user_edit") != ("workflow_seed" if workflow_seed else "user_edit"):
        raise HTTPException(422, "来源血缘必须通过对应的已验证服务创建")
    fingerprint = _hash({"modality": modality, "schema": payload_schema, "payload": payload["payload"], "content_form": payload.get("content_form"), "parent_revision_id": payload.get("parent_revision_id"), "expected_revision": payload.get("expected_revision", 0), "edit_summary": payload.get("edit_summary", {}), "refs": refs_fingerprint, "source_kind": payload.get("source_kind", "user_edit"), "origin_project_output_id": payload.get("origin_project_output_id"), "origin_workflow_run_id": payload.get("origin_workflow_run_id")})
    key = payload["idempotency_key"]
    existing = db.scalar(select(ContentMasterRevision).where(ContentMasterRevision.content_unit_id == unit_id, ContentMasterRevision.idempotency_key == key))
    if existing:
        if existing.request_fingerprint != fingerprint:
            raise HTTPException(409, "幂等键已用于不同的Master请求")
        return _serialize(db, existing)
    latest = db.scalar(select(ContentMasterRevision).where(ContentMasterRevision.content_unit_id == unit_id).order_by(ContentMasterRevision.revision_no.desc()).limit(1))
    head = latest.revision_no if latest else 0
    expected = payload.get("expected_revision", 0)
    if expected != head:
        raise HTTPException(409, {"code": "master_revision_conflict", "expected_revision": expected, "current_revision": head})
    parent_id = payload.get("parent_revision_id") or (latest.id if latest else None)
    if parent_id is not None:
        parent = db.get(ContentMasterRevision, parent_id)
        if parent is None or parent.content_unit_id != unit_id:
            raise HTTPException(422, "父Master必须属于当前内容单元")
        if latest is None or parent.id != latest.id:
            raise HTTPException(409, "父Master不是当前版本，请刷新后重试")
    boundary = db.get(ProjectFactBoundaryRevision, context["boundary"]["id"]) if context["boundary"] else None
    asset_inputs = payload.get("asset_refs", [])
    for item in asset_inputs:
        material = db.get(MaterialRevision, item.get("material_revision_id"))
        if material is None or material.content_hash != item.get("content_hash"):
            raise HTTPException(422, "素材版本不存在或内容哈希不匹配")
        visible = db.scalar(select(ProjectMaterialReference.id).where(ProjectMaterialReference.project_id == project_id, ProjectMaterialReference.material_revision_id == material.id, ProjectMaterialReference.status == "active"))
        generated = db.scalar(select(ProjectWorkflowOutput.id).where(ProjectWorkflowOutput.project_id == project_id, ProjectWorkflowOutput.unit_id == unit_id, ProjectWorkflowOutput.output_kind == "material_revision", ProjectWorkflowOutput.entity_id == material.id))
        if visible is None and generated is None:
            raise HTTPException(422, "素材版本尚未被当前项目明确引用")
    for item in payload.get("evidence_refs", []):
        evidence = db.get(FactPackItem, item.get("fact_pack_item_id"))
        if boundary is None or evidence is None or evidence.fact_pack_id != boundary.fact_pack_id or not evidence.snapshot_checksum or evidence.snapshot_checksum != item.get("snapshot_checksum") or evidence.fact_pack.status != "frozen" or evidence.evidence_kind == "legacy_untyped":
            raise HTTPException(422, "证据必须属于当前冻结事实边界并匹配快照")
    row = ContentMasterRevision(
        project_id=project_id, content_unit_id=unit_id, revision_no=head + 1, parent_revision_id=parent_id,
        modality=modality, channel_id=unit.channel_id, content_form=payload.get("content_form"), payload_schema=payload_schema,
        payload_json=payload["payload"], payload_hash=_hash(payload["payload"]), context_hash=_hash(context),
        identity_snapshot_id=unit.identity_snapshot_id, creative_brief_revision_id=context["brief"]["id"] if context["brief"] else None,
        fact_boundary_revision_id=context["boundary"]["id"] if context["boundary"] else None,
        origin_workflow_run_id=payload.get("origin_workflow_run_id"), origin_project_output_id=payload.get("origin_project_output_id"),
        source_kind=payload.get("source_kind", "user_edit"), edit_summary_json=payload.get("edit_summary", {}), idempotency_key=key,
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
        record_project_event(db, project_id=project_id, event_type="content_master.saved", actor=user.email, entity_type="content_master_revision", entity_id=row.id, payload={"unit_id": unit_id, "revision_no": row.revision_no})
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Master版本并发冲突，请刷新后重试") from exc
    db.refresh(row)
    return _serialize(db, row)


def seed_from_output(db: Session, *, project_id: int, unit_id: int, user: User, output_id: int, idempotency_key: str, expected_revision: int) -> dict:
    _, unit = owned_unit(db, project_id, unit_id, user, mutate=True)
    if unit.modality != "text":
        raise HTTPException(409, "Draft兼容转换仅支持文字内容单元")
    output = db.get(ProjectWorkflowOutput, output_id)
    if output is None or output.project_id != project_id or output.unit_id != unit_id or output.output_kind != "draft":
        raise HTTPException(409, "没有可验证的本单元稿件输出")
    run = db.get(WorkflowRun, output.run_id)
    draft = db.get(Draft, output.entity_id)
    if run is None or run.content_unit_id != unit.id or run.status != "succeeded" or draft is None or draft.content_job.workflow_run_id != run.id or run.identity_snapshot_id is None or run.identity_snapshot_id != unit.identity_snapshot_id:
        raise HTTPException(409, "工作流输出与内容单元身份血缘不一致")
    step = db.scalar(select(WorkflowStep).where(WorkflowStep.run_id == run.id, WorkflowStep.node_id == output.node_id).order_by(WorkflowStep.id.desc()).limit(1))
    attempt = db.get(WorkflowStepAttempt, output.attempt_id) if output.attempt_id else None
    latest_attempt = db.scalar(select(WorkflowStepAttempt).where(WorkflowStepAttempt.step_id == step.id).order_by(WorkflowStepAttempt.attempt_no.desc(), WorkflowStepAttempt.id.desc()).limit(1)) if step else None
    if step is None or attempt is None or latest_attempt is None or latest_attempt.id != attempt.id or attempt.step_id != step.id or attempt.run_id != run.id or attempt.node_id != output.node_id or attempt.attempt_no != step.attempt_no or step.status != "succeeded" or attempt.status != "succeeded" or not step.output_hash or step.output_hash != attempt.output_hash or step.output_json != attempt.output_json or (step.output_json or {}).get("draft_id") != draft.id:
        raise HTTPException(409, "工作流输出已失败、过期或被新的节点尝试替换")
    latest = db.scalar(select(Draft).where(Draft.content_job_id == draft.content_job_id).order_by(Draft.revision_no.desc()).limit(1))
    if latest is None or latest.id != draft.id:
        raise HTTPException(409, "工作流输出所指稿件已过期")
    if unit.channel_id and draft.content_job.channel != unit.channel_id:
        raise HTTPException(409, "工作流稿件渠道与当前单元不一致")
    return save_revision(db, project_id=project_id, unit_id=unit_id, user=user, workflow_seed=True, payload={
        "expected_revision": expected_revision, "idempotency_key": idempotency_key, "modality": unit.modality,
        "payload": {"title": draft.title, "markdown": draft.body, "structured": draft.structured_json},
        "source_kind": "workflow_seed", "origin_workflow_run_id": run.id, "origin_project_output_id": output.id,
        "content_form": draft.content_job.content_form,
        "edit_summary": {"workflow_source": {"draft_id": draft.id, "draft_revision_no": draft.revision_no, "draft_input_hash": draft.input_hash, "run_id": run.id, "definition_checksum": run.definition_checksum, "node_id": step.node_id, "attempt_id": attempt.id, "attempt_input_hash": attempt.input_hash, "attempt_output_hash": attempt.output_hash}, "unmapped_media_ids": [ref.material_revision_id for ref in draft.media], "unmapped_claims": (draft.structured_json or {}).get("claim_fact_map", [])},
    })
