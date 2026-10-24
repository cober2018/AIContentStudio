"""Trusted transaction bridge from a sealed proposal to its accepted Master."""

from fastapi import HTTPException
from sqlalchemy import select, update

from ..models import (
    ContentMasterRevision,
    FactPackItem,
    LLMRun,
    MaterialRevision,
    ProjectEvent,
    ProjectWorkflowOutput,
    WorkflowRun,
    WorkflowStep,
    WorkflowStepAttempt,
    utcnow,
)
from . import content_masters, creation_recipes
from .generation.providers import input_hash
from .materials import read_bytes_checked
from .project_events import record_project_event
from .stage_contracts import IDENTIFIER, RESOLVED_STAGE_MAX_BYTES, canonical, digest
from .stage_invocations import StageInvocationError, _assert_access, require_receipt_schema
from .stage_master_proposals import (
    MASTER_SCHEMAS,
    _validate_supplied_refs,
    build_text_request,
    canonical_master_payload,
    master_modality,
)


def _conflict(code="stage_adoption_integrity"):
    raise StageInvocationError(code, status_code=409)


def _context_changed(frozen, current):
    from .creation_recipes import changed_inputs

    raise StageInvocationError("stage_adoption_context_changed", status_code=409,
                               detail={"changed": changed_inputs({"context": frozen}, {"context": current})})


def _sealed_candidate(db, run, step, attempt, request):
    if (attempt is None or attempt.run_id != run.id or attempt.step_id != step.id
            or attempt.node_id != step.node_id or attempt.plugin_key not in {"stage.master.propose", "stage.graphic.compose"}
            or attempt.plugin_version != "1" or attempt.status != "succeeded"):
        _conflict()
    receipt = canonical(attempt.execution_receipt_json or {}, max_bytes=128 * 1024)
    resolved = canonical((attempt.input_snapshot_json or {}).get("resolved_stage") or {}, max_bytes=RESOLVED_STAGE_MAX_BYTES)
    output = canonical(attempt.output_json, max_bytes=128 * 1024)
    resolution_hash = digest({key: value for key, value in resolved.items() if key != "resolution_hash"})
    model = resolved.get("model") or {}
    hashes = {
        "override_hash": digest(resolved.get("override")),
        "model_route_hash": digest({key: model.get(key) for key in ("profile_id", "provider", "model")}),
        "adapter_hash": digest({key: model.get(key) for key in ("adapter_key", "adapter_version")}),
        "runtime_identity_hash": digest({key: model.get(key) for key in ("runtime_hash", "configuration_revision")}),
        "request_fingerprint": digest({"resolution_hash": resolution_hash, "override": resolved.get("override"),
                                       "automatic": receipt.get("request_mode") == "automatic"}),
    }
    if (receipt.get("schema") != "creation_recipe.execution_receipt.v1"
            or receipt.get("outcome_state") != "succeeded"
            or receipt.get("dispatch_certainty") != "confirmed_dispatched"
            or receipt.get("workflow_run_id") != run.id or receipt.get("workflow_id") != run.workflow_id
            or receipt.get("node_id") != step.node_id or receipt.get("plugin_key") != attempt.plugin_key
            or receipt.get("plugin_version") != attempt.plugin_version
            or output.get("schema") != "stage.master.proposal.v1"
            or attempt.output_hash != digest(output) or receipt.get("output_hash") != attempt.output_hash
            or request["expected_output_hash"] != attempt.output_hash
            or receipt.get("resolution_hash") != resolution_hash
            or resolved.get("resolution_hash") != resolution_hash or attempt.input_hash != resolution_hash
            or request["expected_resolution_hash"] != resolution_hash
            or resolved.get("workflow") != {"id": run.workflow_id, "version": run.workflow_version,
                                          "checksum": run.definition_checksum}
            or resolved.get("node", {}).get("id") != step.node_id
            or resolved.get("node", {}).get("plugin") != attempt.plugin_key
            or resolved.get("node", {}).get("plugin_version") != attempt.plugin_version
            or receipt.get("config_hash") != resolved.get("config_hash")
            or receipt.get("prompt_hash") != resolved.get("prompt_hash")
            or receipt.get("method_hash") != digest(resolved.get("method"))
            or receipt.get("upstream_hash") != digest(resolved.get("upstream"))
            or receipt.get("stage_contract_hash") != resolved.get("stage_contract_hash")
            or receipt.get("request_mode") not in {"explicit", "automatic"}
            or any(receipt.get(key) != value for key, value in hashes.items())
            or receipt.get("output_contract") != resolved.get("output_contract")
            or output.get("proposal_hash") != digest({key: value for key, value in output.items() if key != "proposal_hash"})):
        _conflict()
    if attempt.plugin_key == "stage.graphic.compose":
        from .graphic_composition import build_proposal

        try:
            if output != build_proposal(resolved):
                _conflict()
        except (ValueError, KeyError, TypeError):
            _conflict()
    else:
        generation_request = build_text_request(resolved)
        llm = db.get(LLMRun, output.get("llm_run_id"))
        if (llm is None or llm.status != "succeeded" or llm.input_hash != output.get("input_hash")
                or llm.input_hash != input_hash(generation_request)
                or llm.purpose != generation_request.purpose or llm.prompt_version != "stage.master.propose.v1"
                or llm.provider != model.get("provider") or llm.model != model.get("model")):
            _conflict()
    candidates = [item for item in output.get("candidates", []) if item.get("candidate_id") == request["candidate_id"]]
    if len(candidates) != 1:
        _conflict("stage_candidate_not_found")
    candidate = candidates[0]
    modality = master_modality(resolved)
    if (candidate.get("payload_schema") != MASTER_SCHEMAS[modality]
            or candidate.get("payload_hash") != digest(candidate.get("payload"))
            or candidate.get("candidate_hash") != digest({key: value for key, value in candidate.items() if key != "candidate_hash"})
            or candidate["candidate_hash"] != request["candidate_hash"]):
        _conflict()
    try:
        payload = canonical_master_payload(modality, candidate["payload"], candidate["asset_refs"], candidate["evidence_refs"])
        _validate_supplied_refs(candidate, resolved)
    except (ValueError, KeyError, TypeError):
        _conflict()
    if payload != candidate["payload"]:
        _conflict()
    return candidate, resolved, receipt


def _associate_adoption(db, run, step, attempt, master, provenance):
    if (master.source_kind != "workflow_stage" or master.origin_workflow_run_id != run.id
            or master.content_unit_id != run.content_unit_id
            or master.edit_summary_json.get("stage_provenance") != provenance
            or master.payload_hash != provenance["accepted_payload_hash"]
            or attempt.output_hash != provenance["output_hash"]):
        _conflict()
    output = ProjectWorkflowOutput(
        project_id=master.project_id, unit_id=master.content_unit_id, run_id=run.id,
        node_id=step.node_id, attempt_id=attempt.id, output_kind="content_master_revision", entity_id=master.id,
        provenance_json={**provenance, "payload_hash": master.payload_hash, "context_hash": master.context_hash,
                         "revision_no": master.revision_no}, created_at=utcnow(),
    )
    db.add(output)
    db.flush()
    provenance["project_output_id"] = output.id
    output.provenance_json = {**provenance, "payload_hash": master.payload_hash,
                              "context_hash": master.context_hash, "revision_no": master.revision_no}
    master.edit_summary_json = {**master.edit_summary_json, "stage_provenance": provenance}
    master.origin_project_output_id = output.id
    return output


def _record_feedback(db, master, output, provenance, user):
    return record_project_event(
        db, project_id=master.project_id, event_type="creation_recipe.stage_feedback", actor=user.email,
        entity_type="workflow_step_attempt", entity_id=output.attempt_id,
        payload={**provenance, "schema": "creation_recipe.stage_feedback.v1", "unit_id": master.content_unit_id,
                 "result_kind": "content_master_revision", "result_id": master.id,
                 "accepted_hash": master.payload_hash, "project_output_id": output.id},
    )


def _accepted_result(db, master, provenance):
    output = db.scalar(select(ProjectWorkflowOutput).where(
        ProjectWorkflowOutput.entity_id == master.id, ProjectWorkflowOutput.output_kind == "content_master_revision",
        ProjectWorkflowOutput.unit_id == master.content_unit_id, ProjectWorkflowOutput.project_id == master.project_id,
        ProjectWorkflowOutput.id == provenance.get("project_output_id"),
    ))
    feedback = db.scalar(select(ProjectEvent).where(
        ProjectEvent.project_id == master.project_id, ProjectEvent.event_type == "creation_recipe.stage_feedback",
        ProjectEvent.entity_type == "workflow_step_attempt",
        ProjectEvent.entity_id == str(provenance["attempt_id"]),
        ProjectEvent.payload_json["schema"].as_string() == "creation_recipe.stage_feedback.v1",
        ProjectEvent.payload_json["decision"].as_string().in_(("accepted", "accepted_with_edits")),
        ProjectEvent.payload_json["project_output_id"].as_integer() == provenance.get("project_output_id"),
        ProjectEvent.payload_json["adoption_fingerprint"].as_string() == provenance["adoption_fingerprint"],
    ).order_by(ProjectEvent.id.desc()))
    if (master.source_kind != "workflow_stage" or master.payload_hash != digest(master.payload_json)
            or master.payload_hash != provenance["accepted_payload_hash"]
            or provenance.get("decision") not in {"accepted", "accepted_with_edits"}
            or output is None or output.attempt_id != provenance["attempt_id"]
            or output.project_id != master.project_id or output.run_id != provenance["run_id"]
            or output.node_id != provenance["node_id"]
            or master.origin_workflow_run_id != provenance["run_id"]
            or provenance.get("project_output_id") is not None and output.id != provenance["project_output_id"]
            or output.provenance_json.get("adoption_fingerprint") != provenance["adoption_fingerprint"]
            or output.id != master.origin_project_output_id
            or feedback is None or feedback.payload_json.get("adoption_fingerprint") != provenance["adoption_fingerprint"]
            or feedback.payload_json.get("project_output_id") != output.id
            or feedback.payload_json.get("result_id") != master.id
            or feedback.payload_json.get("accepted_hash") != master.payload_hash
            or feedback.payload_json.get("decision") != provenance.get("decision")
            or output.provenance_json != {**provenance, "payload_hash": master.payload_hash,
                                         "context_hash": master.context_hash, "revision_no": master.revision_no}
            or feedback.payload_json.get("schema") != "creation_recipe.stage_feedback.v1"
            or any(feedback.payload_json.get(key) != value for key, value in provenance.items() if key != "schema")):
        _conflict()
    run = db.get(WorkflowRun, provenance["run_id"])
    step = db.scalar(select(WorkflowStep).where(WorkflowStep.run_id == provenance["run_id"],
                                              WorkflowStep.node_id == provenance["node_id"]))
    if run is None or step is None or run.content_unit_id != master.content_unit_id:
        _conflict()
    candidate, resolved, receipt = _sealed_candidate(db, run, step, db.get(WorkflowStepAttempt, provenance["attempt_id"]), {
        "expected_output_hash": provenance["output_hash"], "expected_resolution_hash": provenance["resolution_hash"],
        "candidate_id": provenance["candidate_id"], "candidate_hash": provenance["candidate_hash"],
    })
    if (provenance["config_hash"] != receipt["config_hash"] or provenance["prompt_hash"] != receipt["prompt_hash"]
            or provenance["context_hash"] != resolved["context_hash"]
            or master.modality != master_modality(resolved) or master.payload_schema != candidate["payload_schema"]
            or provenance["model"] != resolved.get("model") or provenance["method"] != resolved.get("method")):
        _conflict()
    if (resolved.get("creative_configuration") is not None
            and provenance.get("creative_configuration") != resolved["creative_configuration"]):
        _conflict()
    return {"schema": "creation_recipe.master_acceptance.v1", "master": content_masters._serialize(db, master),
            "project_output_id": output.id, "feedback_event_id": feedback.id, "decision": provenance["decision"]}


def _live_refs(db, master, *, require_model_use=False):
    from ..models import ContentMasterAssetRef, ContentMasterEvidenceRef
    from .creative_packages import _check_derived_rights

    for ref in db.scalars(select(ContentMasterAssetRef).where(ContentMasterAssetRef.master_revision_id == master.id)):
        material = db.get(MaterialRevision, ref.material_revision_id)
        require_public = ref.role == "render_output" or master.modality == "graphic" and ref.role == "graphic_layer"
        if (material is None or material.content_hash != ref.content_hash_snapshot
                or material.status in {"revoked", "archived"} or material.material.status != "active"
                or require_public and material.public_use_allowed is not True
                or not (material.public_use_allowed is True or material.model_use_allowed is True)):
            _conflict("stage_asset_model_use_blocked" if require_model_use else "stage_asset_rights_changed")
        if require_model_use and material.model_use_allowed is not True:
            _conflict("stage_asset_model_use_blocked")
        try:
            _check_derived_rights(db, material)
        except HTTPException:
            _conflict("stage_asset_model_use_blocked" if require_model_use else "stage_asset_rights_changed")
        try:
            read_bytes_checked(db, material, require_public=require_public)
        except HTTPException:
            _conflict("stage_asset_model_use_blocked" if require_model_use else "stage_asset_bytes_changed")
    for ref in db.scalars(select(ContentMasterEvidenceRef).where(ContentMasterEvidenceRef.master_revision_id == master.id)):
        item = db.get(FactPackItem, ref.fact_pack_item_id)
        if item is None or item.public_use_revoked_at is not None or item.snapshot_checksum != ref.snapshot_checksum:
            _conflict("stage_evidence_model_use_blocked" if require_model_use else "stage_evidence_changed")
        if require_model_use and item.model_use_allowed is not True:
            _conflict("stage_evidence_model_use_blocked")


def accept_master(db, project_id, unit_id, node_id, user, request):
    require_receipt_schema(db)
    request = canonical(request, max_bytes=128 * 1024)
    if not IDENTIFIER.fullmatch(request.get("adoption_key", "")):
        raise StageInvocationError("stage_adoption_key_invalid", status_code=422)
    project, unit, workflow, run = creation_recipes._workflow(db, project_id, unit_id, user, request["run_id"])
    _assert_access(db, run, user, mutate=False)
    project, unit = content_masters.owned_unit(db, project_id, unit_id, user, mutate=True)
    step = db.scalar(select(WorkflowStep).where(WorkflowStep.run_id == run.id, WorkflowStep.node_id == node_id))
    if step is None:
        raise StageInvocationError("stage_not_found", status_code=404)
    try:
        # Use the same project -> Step lock order as execution and Master writers.
        db.execute(update(WorkflowStep).where(WorkflowStep.id == step.id)
                   .values(attempt_no=WorkflowStep.attempt_no).execution_options(synchronize_session=False))
        db.refresh(step)
        db.refresh(run)
        attempt = db.get(WorkflowStepAttempt, request["attempt_id"])
        candidate, resolved, receipt = _sealed_candidate(db, run, step, attempt, request)
        modality = master_modality(resolved)
        assets, evidence = request["asset_refs"], request["evidence_refs"]
        try:
            payload = canonical_master_payload(modality, request["payload"], assets, evidence)
        except (ValueError, KeyError, TypeError) as exc:
            raise StageInvocationError("stage_adoption_payload_invalid", status_code=422) from exc
        if request.get("payload_schema", candidate["payload_schema"]) != candidate["payload_schema"]:
            raise StageInvocationError("stage_adoption_schema_invalid", status_code=422)
        intent = {**request, "payload": payload, "project_id": project_id, "unit_id": unit_id,
                  "node_id": node_id, "actor_id": user.id}
        fingerprint = digest(intent)
        key = "stage-adopt:" + digest({"run_id": run.id, "node_id": node_id, "key": request["adoption_key"]})
        existing = db.scalar(select(ContentMasterRevision).where(
            ContentMasterRevision.content_unit_id == unit_id, ContentMasterRevision.idempotency_key == key,
        ))
        if existing is not None:
            old = existing.edit_summary_json.get("stage_provenance") or {}
            if old.get("adoption_fingerprint") != fingerprint:
                _conflict("stage_adoption_key_conflict")
            result = _accepted_result(db, existing, old)
            db.commit()
            from .stage_continuation import continue_after_acceptance

            result["continuation"] = continue_after_acceptance(
                db, run_id=old["run_id"], accepted_node_id=old["node_id"],
                accepted_hash=old["accepted_payload_hash"], user=user,
                accepted_output_id=old.get("project_output_id"), accepted_attempt_id=old.get("attempt_id"),
                accepted_decision=old.get("decision"),
            )
            return result
        _assert_access(db, run, user)
        if unit.modality != modality or run.workflow_id != unit.pinned_workflow_id or run.identity_snapshot_id != (None if unit.production_domain == "product" else unit.identity_snapshot_id):
            _conflict("stage_adoption_context_changed")
        if (step.attempt_no != attempt.attempt_no or step.status != "waiting_input"
                or step.output_hash != attempt.output_hash or step.output_json != attempt.output_json):
            _conflict("stage_attempt_not_current")
        if db.scalar(select(ProjectWorkflowOutput.id).where(ProjectWorkflowOutput.attempt_id == attempt.id,
                                                           ProjectWorkflowOutput.output_kind == "content_master_revision")):
            _conflict("stage_already_accepted")
        current, blockers = creation_recipes._context(db, project, unit, run, node=resolved["node"], config=resolved["effective_config"])
        if blockers or digest(resolved["context"]) != request["expected_context_hash"]:
            _conflict("stage_adoption_context_changed")
        if creation_recipes.context_basis(current) != creation_recipes.context_basis(resolved["context"]):
            _context_changed(resolved["context"], current)
        expected_revision = (current.get("master") or {}).get("revision_no", 0)
        if request["expected_revision"] != expected_revision:
            _conflict("stage_master_revision_conflict")
        edited = (payload != candidate["payload"] or assets != candidate["asset_refs"] or evidence != candidate["evidence_refs"])
        if request["decision"] != ("accepted_with_edits" if edited else "accepted"):
            raise StageInvocationError("stage_acceptance_decision_mismatch", status_code=422)
        provenance = canonical({
            "schema": "creation_recipe.stage_provenance.v1", "workflow_id": workflow.id,
            "workflow_version": run.workflow_version, "definition_checksum": run.definition_checksum,
            "run_id": run.id, "node_id": node_id, "attempt_id": attempt.id, "attempt_no": attempt.attempt_no,
            "plugin_key": attempt.plugin_key, "plugin_version": attempt.plugin_version,
            "output_hash": attempt.output_hash, "proposal_hash": attempt.output_json["proposal_hash"],
            "candidate_id": candidate["candidate_id"], "candidate_hash": candidate["candidate_hash"],
            "modality": modality, "payload_schema": candidate["payload_schema"],
            "proposal_payload_hash": candidate["payload_hash"], "accepted_payload_hash": digest(payload),
            "resolution_hash": receipt["resolution_hash"], "config_hash": receipt["config_hash"],
            "base_config_hash": resolved.get("base_config_hash"),
            "prompt_hash": receipt["prompt_hash"], "context_hash": request["expected_context_hash"],
            "model": resolved.get("model"), "method": resolved.get("method"),
            "llm_run_id": attempt.output_json["llm_run_id"], "decision": request["decision"],
            "note": request.get("note", ""), "adoption_fingerprint": fingerprint,
            "edit_summary": {"payload_changed": payload != candidate["payload"],
                             "asset_refs_changed": assets != candidate["asset_refs"],
                             "evidence_refs_changed": evidence != candidate["evidence_refs"]},
        })
        if resolved.get("creative_configuration") is not None:
            provenance["creative_configuration"] = canonical(resolved["creative_configuration"])
        accepted_ids = {}

        def persist_acceptance(master):
            db.refresh(step)
            db.refresh(run)
            _assert_access(db, run, user)
            if (unit.modality != modality or run.workflow_id != unit.pinned_workflow_id
                    or run.identity_snapshot_id != (None if unit.production_domain == "product" else unit.identity_snapshot_id)):
                _conflict("stage_adoption_context_changed")
            if (step.attempt_no != attempt.attempt_no or step.status != "waiting_input"
                    or step.output_hash != attempt.output_hash or step.output_json != attempt.output_json):
                _conflict("stage_attempt_not_current")
            _sealed_candidate(db, run, step, attempt, request)
            context, live_blockers = creation_recipes._context(db, project, unit, run, node=resolved["node"], config=resolved["effective_config"], rework_current=False)
            # The save replaces the Master and its derived ref projections;
            # compare the frozen source while validating actual live refs below.
            context["master"] = resolved["context"].get("master")
            context["asset_refs"] = resolved["context"].get("asset_refs", [])
            context["evidence_refs"] = resolved["context"].get("evidence_refs", [])
            if live_blockers:
                _conflict("stage_adoption_context_changed")
            if creation_recipes.context_basis(context) != creation_recipes.context_basis(resolved["context"]):
                _context_changed(resolved["context"], context)
            _live_refs(db, master)
            output = _associate_adoption(db, run, step, attempt, master, provenance)
            feedback = _record_feedback(db, master, output, provenance, user)
            from .stage_feedback import invalidate_downstream

            invalidate_downstream(db, run, step, master.payload_hash)
            db.flush()
            accepted_ids.update(project_output_id=output.id, feedback_event_id=feedback.id)
            step.status = "succeeded"
            db.flush()
            statuses = db.scalars(select(WorkflowStep.status).where(WorkflowStep.run_id == run.id)).all()
            run.status = "succeeded" if all(status == "succeeded" for status in statuses) else "running"
            run.finished_at = utcnow() if run.status == "succeeded" else None

        saved = content_masters.save_revision(
            db, project_id=project_id, unit_id=unit_id, user=user, stage_adoption=persist_acceptance,
            payload={"modality": modality, "payload_schema": candidate["payload_schema"], "payload": payload,
                     "asset_refs": assets, "evidence_refs": evidence, "idempotency_key": key,
                     "expected_revision": request["expected_revision"], "source_kind": "workflow_stage",
                     "content_form": (current.get("master") or {}).get("content_form"),
                     "origin_workflow_run_id": run.id, "edit_summary": {"stage_provenance": provenance}},
        )
        from .stage_continuation import continue_after_acceptance

        continuation = continue_after_acceptance(
            db, run_id=run.id, accepted_node_id=node_id,
            accepted_hash=provenance["accepted_payload_hash"], user=user,
            accepted_output_id=accepted_ids.get("project_output_id"), accepted_attempt_id=attempt.id,
            accepted_decision=provenance["decision"],
        )
        return {"schema": "creation_recipe.master_acceptance.v1", "master": saved,
                **accepted_ids, "decision": request["decision"], "continuation": continuation}
    except Exception:
        db.rollback()
        raise
