"""Product intake converges on the existing project and Creation Recipe execution."""

import hashlib
import uuid
from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy import or_, select, update
from sqlalchemy.exc import IntegrityError

from ..models import (
    ContentProject,
    ContentUnit,
    CreativeBriefRevision,
    MaterialRevision,
    PersonaWorkflowDefault,
    ProductCreationLaunch,
    ProjectMaterialReference,
    ProjectSourceBinding,
    SourceDocument,
    Workflow,
    WorkflowStep,
    WorkflowStepAttempt,
    utcnow,
)
from . import content_identity, creation_recipes, workflow_engine
from .discovery_runtime import digest
from .project_authorization import authorize_project_workflow
from .project_brief import ProductContext, checksum_brief, current_brief, validate_product_context
from .project_events import record_project_event


def launch_json(row):
    return {"launch_id": row.id, "project_id": row.project_id, "unit_id": row.unit_id,
            "run_id": row.run_id, "status": row.status, "reason": row.reason,
            "href": f"/projects/{row.project_id}/units/{row.unit_id}/production"}


def save_launch(db, user, payload):
    from .content_harness.channel_registry import ensure_channel_in_service

    checksum = digest(payload.model_dump(mode="json", exclude={"launch_key"}))
    existing = db.scalar(select(ProductCreationLaunch).where(ProductCreationLaunch.owner_user_id == user.id,
        ProductCreationLaunch.launch_key == payload.launch_key))
    if existing:
        if existing.input_checksum != checksum:
            raise HTTPException(409, "此发起标识已用于另一份商品资料，请继续原项目或重新发起")
        return existing
    identity = content_identity.create_snapshot(db, user, persona_id=payload.persona_id,
            production_stages=payload.production_stages, modality=payload.modality)
    ensure_channel_in_service(payload.channel)
    product = ProductContext.model_validate(payload.product_context).model_dump(mode="json")
    sources = []
    for source_id in dict.fromkeys(payload.source_ids):
        source = db.get(SourceDocument, source_id)
        if source is None or source.is_archived:
            raise HTTPException(404, "商品资料不存在")
        sources.append(source)
    if not product["description"].strip() and product["url"] and not sources:
        from ..routers.sources import _parse_and_store
        from .url_fetch import safe_fetch

        try:
            body, mime = safe_fetch(product["url"])
            source = SourceDocument(title=product["name"], source_type="url", source_url=product["url"],
                                    mime_type=mime, sha256=hashlib.sha256(body).hexdigest())
            db.add(source)
            db.flush()
            _parse_and_store(db, source, body, mime, ".html" if "html" in mime else ".txt")
            if source.parse_status != "done" or not source.raw_text or not source.raw_text.strip():
                raise ValueError("product_source_unreadable")
            sources.append(source)
        except Exception:  # noqa: BLE001 URL errors can contain sensitive URL parameters.
            db.rollback()
            identity = content_identity.create_snapshot(db, user, persona_id=payload.persona_id,
            production_stages=payload.production_stages, modality=payload.modality)
    # A pasted description is an ordinary source, not an automatically confirmed fact.
    if product["description"].strip():
        from ..routers.sources import _parse_and_store

        data = product["description"].encode()
        source = SourceDocument(title=f"{product['name']} · 用户提供商品说明", source_type="text",
                                mime_type="text/plain", sha256=hashlib.sha256(data).hexdigest())
        db.add(source)
        db.flush()
        _parse_and_store(db, source, data, "text/plain", ".txt")
        sources.append(source)
    product["source_refs"] = [{"source_id": s.id, "checksum": s.sha256} for s in sources]
    materials = []
    for revision_id in dict.fromkeys(payload.material_revision_ids):
        revision = db.get(MaterialRevision, revision_id)
        if not revision:
            raise HTTPException(404, "商品素材不存在")
        materials.append(revision)
    product["material_refs"] = [{"material_revision_id": r.id, "content_hash": r.content_hash} for r in materials]
    product = validate_product_context(db, product)
    workflow_id = payload.workflow_id
    if workflow_id is None:
        binding = db.scalar(select(PersonaWorkflowDefault).where(PersonaWorkflowDefault.persona_id == payload.persona_id,
                                                                 PersonaWorkflowDefault.modality == payload.modality))
        workflow_id = binding.workflow_id if binding else None
    if workflow_id:
        workflow = db.get(Workflow, workflow_id)
        if not workflow or not workflow.enabled or workflow.status != "published":
            raise HTTPException(409, "所选创作流程不可运行")
        authorize_project_workflow(db, workflow, user)
        if workflow.scope != "persona_default" or workflow.workflow_key != f"persona.{payload.persona_id}.{payload.modality}":
            raise HTTPException(409, "所选流程与商品角色或内容形态不匹配")
    project = ContentProject(owner_user_id=user.id, title=payload.title or product["name"], objective=payload.objective)
    db.add(project)
    db.flush()
    brief_data = {"objective": payload.objective,
        "primary_audience": payload.primary_audience or "、".join(identity.effective_profile_json.get("target_audience") or []),
        "core_message": "；".join(product["selling_points"]), "angle": None,
        "required_evidence": ["商品事实需沿用来源与证据的确认和冻结规则"],
        "content_constraints": ["不得虚构规格、功效、价格、亲测或用户评价", *product["excluded_claims"]],
        "identity_scope": [{"persona_id": payload.persona_id}], "modality_scope": [payload.modality],
        "channel_scope": [payload.channel], "cta": payload.cta,
        "references": [{"kind": "source_document", "id": s.id} for s in sources], "product_context": product}
    brief = CreativeBriefRevision(project_id=project.id, revision_no=1, created_by=user.email,
        **{k: brief_data[k] for k in ("objective", "primary_audience", "core_message", "angle", "cta")},
        **{k + "_json": brief_data[k] for k in ("required_evidence", "content_constraints", "identity_scope",
            "modality_scope", "channel_scope", "references", "product_context")}, checksum=checksum_brief(brief_data))
    db.add(brief)
    unit = ContentUnit(project_id=project.id, persona_id=payload.persona_id, identity_snapshot_id=identity.id,
                       modality=payload.modality, channel_id=payload.channel, title=payload.title or product["name"],
                       pinned_workflow_id=workflow_id)
    db.add(unit)
    db.flush()
    if payload.production_stages is not None and payload.production_stages != {}:
        from .creative_configuration import freeze_production_stages

        stages = identity.effective_profile_json[f"{payload.modality}_creative_profile"]["production_stages"]
        manifest = freeze_production_stages(db, user, unit, stages, origin="product_task")
        identity.effective_profile_json = {**identity.effective_profile_json,
            "product_production_methods": {payload.modality: manifest},
            "product_production_stages": payload.production_stages}
        identity.checksum = content_identity.checksum({"identity_checksum": identity.checksum,
            "product_production_methods": {payload.modality: manifest},
            "product_production_stages": payload.production_stages})
    for source in sources:
        db.add(ProjectSourceBinding(project_id=project.id, source_document_id=source.id, attached_by=user.email))
    for revision in materials:
        db.add(ProjectMaterialReference(project_id=project.id, material_revision_id=revision.id,
                                        origin="system_reference", attached_by=user.email))
    launch = ProductCreationLaunch(owner_user_id=user.id, launch_key=payload.launch_key, input_checksum=checksum,
        project_id=project.id, unit_id=unit.id, invocation_key=f"product.{uuid.uuid4().hex}")
    db.add(launch)
    record_project_event(db, project_id=project.id, event_type="project.created", actor=user.email,
                         entity_type="content_project", entity_id=project.id, payload={"entry": "product"})
    record_project_event(db, project_id=project.id, event_type="brief.revision_created", actor=user.email,
                         entity_type="creative_brief_revision", entity_id=brief.id,
                         payload={"revision_no": 1, "checksum": brief.checksum})
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(select(ProductCreationLaunch).where(ProductCreationLaunch.owner_user_id == user.id,
            ProductCreationLaunch.launch_key == payload.launch_key))
        if existing and existing.input_checksum == checksum:
            return existing
        raise HTTPException(409, "商品创作已由其他请求更新，请重新读取") from None
    return launch


def resume_launch(db, user, launch):
    from .project_evidence import current_boundary
    from .stage_invocations import StageInvocationError, execute_stage

    project = db.get(ContentProject, launch.project_id)
    unit = db.get(ContentUnit, launch.unit_id)
    if project.owner_user_id != user.id or project.status == "archived" or unit.status == "archived":
        raise HTTPException(409, "项目不可继续创作")
    content_identity.hierarchy(db, user, persona_id=unit.persona_id, mutable=True)
    if launch.status in {"started", "unknown"}:
        return launch_json(launch)
    token, now = uuid.uuid4().hex, utcnow()
    claimed = db.execute(update(ProductCreationLaunch).where(ProductCreationLaunch.id == launch.id,
        ProductCreationLaunch.status.not_in(["started", "unknown"]),
        or_(ProductCreationLaunch.lease_until.is_(None), ProductCreationLaunch.lease_until < now))
        .values(lease_token=token, lease_until=now + timedelta(minutes=15)))
    db.commit()
    if not claimed.rowcount:
        db.refresh(launch)
        return launch_json(launch)
    db.refresh(launch)
    try:
        brief = current_brief(db, project.id)
        if not brief.product_context_json or (not brief.product_context_json.get("description", "").strip()
                and not brief.product_context_json.get("source_refs")):
            launch.status, launch.reason = "blocked", "product_information_required"
            return launch_json(launch)
        validate_product_context(db, brief.product_context_json)
        if not brief.product_context_json.get("description", "").strip():
            source_refs = brief.product_context_json.get("source_refs", [])
            if any((not db.get(SourceDocument, r["source_id"]).raw_text
                    or db.get(SourceDocument, r["source_id"]).parse_status != "done") for r in source_refs):
                launch.status, launch.reason = "blocked", "product_source_unreadable"
                return launch_json(launch)
            if current_boundary(db, project.id) is None:
                launch.status, launch.reason = "blocked", "product_evidence_confirmation_required"
                return launch_json(launch)

        workflow = db.get(Workflow, unit.pinned_workflow_id) if unit.pinned_workflow_id else None
        if not workflow or not workflow.enabled or workflow.status != "published":
            launch.status, launch.reason = "blocked", "workflow_required"
            return launch_json(launch)
        authorize_project_workflow(db, workflow, user)
        if launch.run_id is None:
            run = workflow_engine.start_run(db, workflow, {}, user, content_unit_id=unit.id,
                                            advance_now=False, stage_run=True, commit=False)
            launch.run_id = run.id
            db.commit()
        view = creation_recipes.recipe_view(db, project.id, unit.id, user, run_id=launch.run_id)
        stage = next((s for s in view["stages"] if s["mode"] == "stage"), None)
        if not stage:
            launch.status, launch.reason = "blocked", "creation_stage_required"
            return launch_json(launch)
        attempts = db.scalars(select(WorkflowStepAttempt).join(WorkflowStep, WorkflowStep.id == WorkflowStepAttempt.step_id)
            .where(WorkflowStep.run_id == launch.run_id, WorkflowStep.node_id == stage["node_id"])
            .order_by(WorkflowStepAttempt.attempt_no.desc())).all()
        previous = next((a for a in attempts if (a.execution_receipt_json or {}).get("invocation_key") == launch.invocation_key), None)
        if previous:
            receipt = previous.execution_receipt_json or {}
            if previous.status == "running":
                launch.status, launch.reason = "dispatching", "stage_invocation_in_progress"
                return launch_json(launch)
            if previous.status == "unknown" or receipt.get("dispatch_certainty") == "possibly_dispatched":
                launch.status, launch.reason = "unknown", "stage_dispatch_unknown"
                return launch_json(launch)
            if previous.status == "succeeded":
                execute_stage(db, project.id, unit.id, stage["node_id"], user, run_id=launch.run_id,
                    expected_resolution_hash=previous.input_hash, invocation_key=launch.invocation_key, stage_override={})
                launch.status, launch.reason = "started", None
                return launch_json(launch)
            if receipt.get("dispatch_certainty") != "not_dispatched":
                launch.status, launch.reason = "blocked", "stage_failed_review_required"
                return launch_json(launch)
            launch.invocation_key = f"product.{uuid.uuid4().hex}"
            db.commit()
        preview = creation_recipes.preview_stage(db, project.id, unit.id, stage["node_id"], user, run_id=launch.run_id)
        if not preview.get("ready"):
            launch.status = "blocked"
            launch.reason = str((preview.get("blockers") or ["creation_inputs_required"])[0])[:100]
            return {**launch_json(launch), "blockers": preview.get("blockers", [])}
        launch.status, launch.reason = "dispatching", None
        db.commit()
        result = execute_stage(db, project.id, unit.id, stage["node_id"], user, run_id=launch.run_id,
            expected_resolution_hash=preview["resolution_hash"], invocation_key=launch.invocation_key, stage_override={})
        result_status = result.get("status")
        launch.status = "unknown" if result_status == "unknown" else "started" if result_status in {"succeeded", "waiting_input", "waiting_human"} else "blocked"
        if launch.status == "blocked":
            launch.reason = "stage_failed_review_required"
        return {**launch_json(launch), "stage_result": result}
    except StageInvocationError as exc:
        db.rollback()
        launch = db.get(ProductCreationLaunch, launch.id)
        launch.status = "unknown" if "unknown" in exc.code else "blocked"
        launch.reason = exc.code
        return launch_json(launch)
    except (ValueError, HTTPException) as exc:
        db.rollback()
        launch = db.get(ProductCreationLaunch, launch.id)
        launch.status, launch.reason = "blocked", "creation_inputs_required"
        return {**launch_json(launch), "detail": exc.detail if isinstance(exc, HTTPException) else str(exc)[:200]}
    finally:
        if launch.lease_token == token:
            launch.lease_token, launch.lease_until = None, None
        db.commit()
