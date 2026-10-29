"""Product intake converges on the existing project and Creation Recipe execution."""

import hashlib
import uuid
from datetime import timedelta
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import or_, select, update
from sqlalchemy.exc import IntegrityError

from ..models import (
    ContentPersona,
    ContentProject,
    ContentUnit,
    CreativeBriefRevision,
    MaterialRevision,
    ProductCreationLaunch,
    ProductionProfileRevision,
    ProjectMaterialReference,
    ProjectSourceBinding,
    SourceDocument,
    SystemSetting,
    Workflow,
    WorkflowStep,
    WorkflowStepAttempt,
    utcnow,
)
from . import creation_recipes, product_context, workflow_engine
from .discovery_runtime import digest
from .project_authorization import authorize_project_workflow
from .project_brief import ProductContext, ProductOffer, checksum_brief, current_brief, validate_product_context
from .project_events import record_project_event


def launch_json(row):
    return {"launch_id": row.id, "project_id": row.project_id, "unit_id": row.unit_id,
            "run_id": row.run_id, "status": row.status, "reason": row.reason,
            "href": f"/projects/{row.project_id}/units/{row.unit_id}/production"}


def save_private_costs(db, user, project_id, value):
    # Separate storage keeps internal economics out of versioned creative inputs and exports.
    key = f"product_costs.{user.id}.{project_id}"
    row = db.get(SystemSetting, key)
    if row is None:
        db.add(SystemSetting(key=key, value=value, updated_by=user.email))
    else:
        row.value, row.updated_by = value, user.email


def product_costs_view(db, owner_id, project_id):
    row = db.get(SystemSetting, f"product_costs.{owner_id}.{project_id}")
    costs = row.value if row else None
    contribution = None
    brief = current_brief(db, project_id)
    offer = (brief.product_context_json or {}).get("offer") if brief else None
    fields = ("purchase", "packaging", "shipping", "platform", "promotion", "production", "returns_service")
    if (costs and offer and costs.get("currency") and costs["currency"] == offer.get("currency")
            and offer.get("sale_price") is not None and all(costs.get(key) is not None for key in fields)):
        sale = ProductOffer(currency=offer["currency"], sale_price=offer["sale_price"])
        if {"price_currency_precision_invalid", "currency_required_or_unsupported"}.intersection(sale.promotion_issues):
            return {"costs": costs, "estimated_contribution": None}
        orders = 1 if costs.get("basis") == "per_order" else costs.get("order_count") if costs.get("basis") == "total" else None
        if orders:
            contribution = str(Decimal(str(offer["sale_price"])) * orders - sum(Decimal(str(costs[key])) for key in fields))
    return {"costs": costs, "estimated_contribution": contribution}


def save_launch(db, user, payload, project=None):
    """``project``: add the product work to this existing project instead of creating one."""
    from .content_harness.channel_registry import ensure_channel_in_service

    checksum = digest(payload.model_dump(mode="json", exclude={"launch_key"}))
    existing = db.scalar(select(ProductCreationLaunch).where(ProductCreationLaunch.owner_user_id == user.id,
        ProductCreationLaunch.launch_key == payload.launch_key))
    if existing:
        accepted_checksums = {checksum}
        legacy_defaults = {"core_message": None, "angle": None, "creative_profile": None,
            "fetch_product_url": True, "private_costs": None}
        data = payload.model_dump(mode="json", exclude={"launch_key"})
        # Older launch hashes predate these optional fields; only their exact defaults may be omitted.
        if all(data.get(key) == value for key, value in legacy_defaults.items()):
            accepted_checksums.add(digest({key: value for key, value in data.items() if key not in legacy_defaults}))
        if existing.input_checksum not in accepted_checksums:
            raise HTTPException(409, "此发起标识已用于另一份商品资料，请继续原项目或重新发起")
        return existing
    if payload.modality != "video":
        raise HTTPException(422, "商品工作台仅制作视频；文字与图文请使用角色内容工作台，旧商品记录仍可读取")
    ensure_channel_in_service(payload.channel)
    persona = db.get(ContentPersona, payload.persona_id) if payload.persona_id else None
    if payload.persona_id and (persona is None or persona.owner_user_id != user.id or persona.status == "archived"):
        raise HTTPException(404, "角色不存在")
    product = ProductContext.model_validate(payload.product_context).model_dump(mode="json")
    sources = []
    for source_id in dict.fromkeys(payload.source_ids):
        source = db.get(SourceDocument, source_id)
        if source is None or source.is_archived:
            raise HTTPException(404, "商品资料不存在")
        sources.append(source)
    if payload.fetch_product_url and not product["description"].strip() and product["url"] and not sources:
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
        supplied = next((ref for ref in product["material_refs"] if ref["material_revision_id"] == revision_id), None)
        if supplied and supplied["content_hash"] != revision.content_hash:
            raise HTTPException(409, "商品素材版本已变化，请重新读取")
        materials.append(revision)
    categories = {r["material_revision_id"]: r["categories"] for r in product["material_refs"]}
    product["material_refs"] = [{"material_revision_id": r.id, "content_hash": r.content_hash,
                                 "categories": categories.get(r.id, [])} for r in materials]
    product = validate_product_context(db, product, user=user)
    from copy import deepcopy

    from .workflow_templates import ensure_product_workflow

    settings = {}
    if payload.creative_profile is not None:
        settings[f"{payload.modality}_creative_profile"] = deepcopy(payload.creative_profile)
    if payload.production_stages is not None:
        settings["production_stages"] = deepcopy(payload.production_stages)
    workflow = db.get(Workflow, payload.workflow_id) if payload.workflow_id else ensure_product_workflow(db, payload.modality, user)
    if not workflow or not workflow.enabled or workflow.status != "published":
        raise HTTPException(409, "所选创作流程不可运行")
    authorize_project_workflow(db, workflow, user)
    if workflow.scope != "product_default" or workflow.workflow_key != f"product.{user.id}.{payload.modality}":
        raise HTTPException(409, "所选流程与商品生产领域或内容形态不匹配")
    workflow_id = workflow.id
    existing_project = project is not None
    if not existing_project:
        project = ContentProject(owner_user_id=user.id, title=payload.title or product["name"], objective=payload.objective)
        db.add(project)
        db.flush()
    brief_data = {"objective": payload.objective,
        "primary_audience": payload.primary_audience or "",
        "core_message": payload.core_message or "；".join(product["selling_points"]), "angle": payload.angle,
        "required_evidence": ["商品事实需沿用来源与证据的确认和冻结规则"],
        "content_constraints": ["不得虚构规格、功效、价格、亲测或用户评价", *product["excluded_claims"]],
        "identity_scope": [], "modality_scope": [payload.modality],
        "channel_scope": [payload.channel] if payload.channel else [], "cta": payload.cta,
        "references": [{"kind": "source_document", "id": s.id} for s in sources], "product_context": product}
    previous = current_brief(db, project.id) if existing_project else None
    if existing_project and previous is None and (project.objective or "").strip():
        brief_data["objective"] = project.objective
    if previous is not None:
        # What the user already wrote for the project wins; product facts only fill the gaps.
        for key in ("objective", "primary_audience", "core_message", "angle", "cta"):
            if (getattr(previous, key) or "").strip():
                brief_data[key] = getattr(previous, key)
        for key in ("required_evidence", "content_constraints", "identity_scope", "modality_scope", "channel_scope", "references"):
            merged = list(getattr(previous, key + "_json") or [])
            merged += [item for item in brief_data[key] if item not in merged]
            brief_data[key] = merged
    brief = CreativeBriefRevision(project_id=project.id, revision_no=(previous.revision_no + 1) if previous else 1,
        parent_revision_id=previous.id if previous else None, created_by=user.email,
        **{k: brief_data[k] for k in ("objective", "primary_audience", "core_message", "angle", "cta")},
        **{k + "_json": brief_data[k] for k in ("required_evidence", "content_constraints", "identity_scope",
            "modality_scope", "channel_scope", "references", "product_context")}, checksum=checksum_brief(brief_data))
    db.add(brief)
    if payload.private_costs is not None:
        save_private_costs(db, user, project.id, payload.private_costs.model_dump(mode="json"))
    unit = ContentUnit(project_id=project.id, persona_id=payload.persona_id, identity_snapshot_id=None, production_domain="product",
                       modality=payload.modality, channel_id=payload.channel, title=payload.title or product["name"],
                       pinned_workflow_id=workflow_id)
    db.add(unit)
    db.flush()
    settings.setdefault(f"{payload.modality}_creative_profile", product_context.default_creative_profile(payload.modality))
    if payload.production_stages is not None and payload.production_stages != {}:
        from .creative_configuration import freeze_production_stages

        settings[f"{payload.modality}_creative_profile"]["production_stages"] = deepcopy(payload.production_stages)
        manifest = freeze_production_stages(db, user, unit, payload.production_stages, origin="product_task")
        settings["product_production_methods"] = {payload.modality: manifest}
    db.add(ProductionProfileRevision(unit_id=unit.id, revision=1, settings_json=settings,
        settings_hash=digest(settings), created_by=user.email))
    bound = set(db.scalars(select(ProjectSourceBinding.source_document_id).where(ProjectSourceBinding.project_id == project.id)))
    for source in sources:
        if source.id not in bound:
            db.add(ProjectSourceBinding(project_id=project.id, source_document_id=source.id, attached_by=user.email))
    attached = set(db.scalars(select(ProjectMaterialReference.material_revision_id).where(ProjectMaterialReference.project_id == project.id)))
    for revision in materials:
        if revision.id not in attached:
            db.add(ProjectMaterialReference(project_id=project.id, material_revision_id=revision.id,
                                            origin="system_reference", attached_by=user.email))
    launch = ProductCreationLaunch(owner_user_id=user.id, launch_key=payload.launch_key, input_checksum=checksum,
        project_id=project.id, unit_id=unit.id, invocation_key=f"product.{uuid.uuid4().hex}")
    db.add(launch)
    if existing_project:
        record_project_event(db, project_id=project.id, event_type="unit.created", actor=user.email,
                             entity_type="content_unit", entity_id=unit.id, payload={"entry": "product"})
    else:
        record_project_event(db, project_id=project.id, event_type="project.created", actor=user.email,
                             entity_type="content_project", entity_id=project.id, payload={"entry": "product"})
    record_project_event(db, project_id=project.id, event_type="brief.revision_created", actor=user.email,
                         entity_type="creative_brief_revision", entity_id=brief.id,
                         payload={"revision_no": brief.revision_no, "checksum": brief.checksum})
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
    if project.owner_user_id != user.id or project.status == "archived" or unit.lifecycle_readonly:
        raise HTTPException(409, "项目不可继续创作")
    if not product_context.is_product(unit):
        raise HTTPException(409, "作品尚未迁移至商品生产领域")
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
        validate_product_context(db, brief.product_context_json, user=user, project_id=project.id)
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
        if launch.run_id is None and (not workflow or workflow.scope in {"persona_default", "account_default", "series_default"}):
            from .workflow_templates import ensure_product_workflow

            workflow = ensure_product_workflow(db, unit.modality, user)
            unit.pinned_workflow_id = workflow.id
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
