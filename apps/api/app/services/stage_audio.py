"""Read-only Audio Stage preparation over explicit accepted dependencies."""

from fastapi import HTTPException

from ..models import (
    ContentUnit,
    MaterialRevision,
    ProjectWorkflowOutput,
    ProviderGenerationTask,
    User,
    WorkflowStepAttempt,
)
from . import audio_quality, creation_recipes, creative_method_stage, generation_tasks
from .creative_artifacts import validate_artifact
from .stage_contracts import IDENTIFIER, StageContractError, canonical, digest
from .stage_invocations import StageInvocationError

_TTS_SCHEMA = "studio.audio.stage.tts.v1"
_QC_SCHEMA = "studio.audio.stage.qc.v1"
_TTS_FIELDS = {"capability", "method", "selected_profile", "explicit_plugin", "voice", "rate",
               "items", "seconds", "timeout_seconds", "tts_source"}
_QUALITY_REFS = {"studio.quality.audio.explainer@1", "studio.quality.audio.conversational@1"}
_QC_FIELDS = {"method", "quality_profile_ref", "alignment_enabled", "asr_master_revision_id",
              "asr_receipt_id", "asr_output_hash", "srt_mode"}


def _invalid(code):
    raise StageInvocationError(code, status_code=409)


def _blocker(exc):
    code = exc.code if isinstance(exc, StageInvocationError) else exc.detail if isinstance(exc, HTTPException) else None
    return code if isinstance(code, str) and IDENTIFIER.fullmatch(code) else "stage_audio_input_unavailable"


def _dependencies(db, user, unit, node, context):
    run_id = context.get("run_id")
    if (type(run_id) is not int or run_id <= 0 or context.get("unit_id") != unit.id
            or context.get("project_id") != unit.project_id):
        _invalid("stage_audio_run_required")
    _, live_unit, workflow, run = creation_recipes._workflow(db, unit.project_id, unit.id, user, run_id)
    defined = next((item for item in workflow.definition_json["nodes"] if item["id"] == node["id"]), None) if workflow else None
    if (run is None or live_unit.id != unit.id or defined is None
            or defined.get("plugin") != node.get("plugin")
            or str(defined.get("plugin_version")) != str(node.get("plugin_version"))):
        _invalid("stage_audio_node_changed")
    incoming = [edge["from"] for edge in workflow.definition_json["edges"] if edge["to"] == node["id"]]
    if not 1 <= len(incoming) <= 20 or len(set(incoming)) != len(incoming) or node["id"] in incoming:
        _invalid("stage_audio_direct_dependencies_required")
    targets = [creation_recipes.accepted_stage_target(db, run, source) for source in incoming]
    return run, {"id": workflow.id, "version": workflow.version, "checksum": workflow.checksum}, targets


def _creative_input(db, targets, schema):
    matches = [target for target in targets if target and target.get("output_kind") == "creative_attempt"
               and target.get("output_schema") == schema and target.get("decision") == "accepted"]
    if len(matches) != 1:
        _invalid("stage_audio_accepted_spoken_required" if schema == "audio.spoken-adaptation.v1"
                 else "stage_audio_accepted_voice_direction_required")
    selected = creative_method_stage.selected_input(db, matches[0], include_content=True)
    content = validate_artifact(schema, selected["selected_content"])
    attempt = db.get(WorkflowStepAttempt, selected["attempt_id"])
    if attempt is None:
        _invalid("stage_audio_creative_receipt_changed")
    resolved = (attempt.input_snapshot_json or {}).get("resolved_stage") or {}
    if (attempt.input_hash != resolved.get("resolution_hash")
            or selected["output_hash"] != attempt.output_hash
            or resolved.get("config_hash") != digest(resolved.get("effective_config"))):
        _invalid("stage_audio_creative_receipt_changed")
    return content, canonical({"target": matches[0], "attempt_id": attempt.id,
        "attempt_input_hash": attempt.input_hash, "attempt_output_hash": attempt.output_hash,
        "config_hash": resolved["config_hash"], "content_hash": digest(content)})


def _tts_config(config, *, direction_rate=1.0):
    if not isinstance(config, dict) or set(config) - _TTS_FIELDS:
        _invalid("stage_audio_unconsumed_control")
    if config.get("capability", "tts") != "tts" or config.get("tts_source", "accepted_spoken") != "accepted_spoken":
        _invalid("stage_audio_accepted_spoken_required")
    if not config.get("voice"):
        _invalid("stage_audio_provider_voice_required")
    result = {**config, "capability": "tts", "tts_source": "accepted_spoken",
              "items": config.get("items", 1),
              "seconds": config.get("seconds", 120), "timeout_seconds": config.get("timeout_seconds", 25)}
    if (type(result["items"]) is not int or result["items"] != 1
            or type(result["seconds"]) is not int or not 1 <= result["seconds"] <= 600
            or type(result["timeout_seconds"]) is not int or not 1 <= result["timeout_seconds"] <= 300):
        _invalid("stage_audio_tts_limits_invalid")
    try:
        spoken = generation_tasks.routing.tts_parameters({"voice_id": result["voice"], "rate": result.get("rate", direction_rate)}, capability="tts")
    except (ValueError, TypeError):
        _invalid("stage_audio_voice_rate_invalid")
    if "rate" in result:
        result["rate"] = spoken["rate"]
    return canonical(result), spoken


def _request(config, script, parameters):
    return generation_tasks.workflow_request({"capability": "tts", "selected_profile": config.get("selected_profile"),
        "explicit_plugin": config.get("explicit_plugin"), "prompt": script, "source_revision_ids": [],
        "parameters": {"items": config["items"], "seconds": config["seconds"],
                       "timeout_seconds": config["timeout_seconds"], **parameters}}, allow_tts_long=True)


def prepare_tts(db, user, unit, node, config, context):
    """Return enriched context, effective config and blockers; never edit the accepted script."""
    try:
        with db.no_autoflush:
            if node.get("plugin") != "media.generate" or str(node.get("plugin_version")) != "4":
                _invalid("stage_audio_tts_requires_v4")
            effective, parameters = _tts_config(config)
            run, workflow, targets = _dependencies(db, user, unit, node, context)
            spoken, spoken_proof = _creative_input(db, targets, "audio.spoken-adaptation.v1")
            direction, direction_proof = _creative_input(db, targets, "audio.voice-direction.v1")
            effective, parameters = _tts_config(config, direction_rate=direction["rate"])
            if len(spoken["script"]) > 9999 or not spoken["script"].strip():
                _invalid("stage_audio_spoken_script_limit")
            _request(effective, spoken["script"], parameters)
            snapshot = {"schema": _TTS_SCHEMA, "run_id": run.id, "unit_id": unit.id,
                "project_id": unit.project_id, "node_id": node["id"], "workflow": workflow,
                "tts_source": "accepted_spoken", "config_hash": digest(effective),
                "spoken": spoken_proof, "voice_direction": {**direction_proof, "content": direction},
                "script": spoken["script"], "script_hash": digest(spoken["script"]), "parameters": parameters,
                "rate_difference": {"direction_rate": direction["rate"], "config_rate": parameters["rate"],
                                    "source": "config" if "rate" in effective else "accepted_voice_direction",
                                    "differs": direction["rate"] != parameters["rate"]}}
            snapshot["input_hash"] = digest(snapshot)
            return canonical({**context, "audio_stage": snapshot}), effective, []
    except (StageInvocationError, HTTPException, StageContractError, ValueError, TypeError, KeyError, AttributeError) as exc:
        return context if isinstance(context, dict) else {}, config if isinstance(config, dict) else {}, [_blocker(exc)]


def tts_request(config, context):
    """Project only the frozen accepted script and actual CLI controls into a native request."""
    if not isinstance(context, dict):
        _invalid("stage_audio_tts_snapshot_invalid")
    snapshot = canonical(context.get("audio_stage") or {})
    if not isinstance(snapshot, dict):
        _invalid("stage_audio_tts_snapshot_invalid")
    for name, schema in (("spoken", "audio.spoken-adaptation.v1"), ("voice_direction", "audio.voice-direction.v1")):
        proof = snapshot.get(name)
        target = proof.get("target") if isinstance(proof, dict) else None
        if (not isinstance(target, dict) or target.get("output_kind") != "creative_attempt"
                or target.get("output_schema") != schema or target.get("decision") != "accepted"
                or proof.get("attempt_output_hash") != target.get("output_hash")):
            _invalid("stage_audio_tts_snapshot_invalid")
    direction = snapshot["voice_direction"].get("content")
    if not isinstance(direction, dict) or snapshot["voice_direction"].get("content_hash") != digest(direction):
        _invalid("stage_audio_tts_snapshot_invalid")
    effective, parameters = _tts_config(config, direction_rate=direction.get("rate", 1.0))
    if (snapshot.get("schema") != _TTS_SCHEMA or snapshot.get("tts_source") != "accepted_spoken"
            or snapshot.get("input_hash") != digest({key: value for key, value in snapshot.items() if key != "input_hash"})
            or snapshot.get("config_hash") != digest(effective) or snapshot.get("parameters") != parameters
            or snapshot.get("script_hash") != digest(snapshot.get("script"))
            or any(snapshot.get(key) != context.get(key) for key in ("run_id", "unit_id", "project_id"))):
        _invalid("stage_audio_tts_snapshot_invalid")
    return _request(effective, snapshot["script"], parameters)


def _accepted_audio(db, targets, run, user, unit, *, local_qc=False):
    from .stage_domain_adoptions import accepted_domain_input

    matches = []
    for target in targets:
        if target and target.get("output_kind") == "material_revision" and target.get("decision") == "accepted":
            revision = db.get(MaterialRevision, target["entity_id"])
            if revision is not None and revision.material is not None and revision.material.kind == "audio":
                matches.append((target, revision))
    if len(matches) != 1:
        _invalid("stage_audio_accepted_material_required")
    target, revision = matches[0]
    accepted_domain_input(db, target, require_model_use=False, local_audio_qc=local_qc)
    output = db.get(ProjectWorkflowOutput, target["project_output_id"])
    task = db.get(ProviderGenerationTask, (output.provenance_json or {}).get("task_id"))
    if (task is None or task.state != "accepted" or task.project_id != unit.project_id
            or task.accepted_material_revision_id != revision.id or task.result_hash != revision.content_hash
            or task.workflow_step_attempt_id != target["attempt_id"] or task.provider_kind != "tts_provider"):
        _invalid("stage_audio_accepted_task_required")
    generation_tasks._verify_result_receipt(task)
    attempt = db.get(WorkflowStepAttempt, task.workflow_step_attempt_id)
    if attempt is None or attempt.run_id != run.id or attempt.node_id != target["node_id"]:
        _invalid("stage_audio_task_run_changed")
    resolved = (attempt.input_snapshot_json or {}).get("resolved_stage") or {}
    script = task.request_json.get("prompt")
    audio_stage = (resolved.get("context") or {}).get("audio_stage")
    if str(attempt.plugin_version) == "4":
        current, effective, blockers = prepare_tts(db, user, unit, resolved["node"],
                                                  resolved["effective_config"], resolved["context"])
        if (blockers or audio_stage is None or current["audio_stage"] != audio_stage
                or tts_request(effective, current) != tts_request(resolved["effective_config"], resolved["context"])
                or tts_request(effective, current)["prompt"] != script):
            _invalid("stage_audio_spoken_source_changed")
    if not isinstance(script, str) or not 1 <= len(script) <= 9999:
        _invalid("stage_audio_signed_script_invalid")
    return target, revision, task, script, audio_stage


def prepare_qc(db, user, unit, node, config, context):
    """Prepare a local report; it remains Attempt output, not a ContentMasterCheckRun."""
    try:
        with db.no_autoflush:
            if node.get("plugin") != "stage.audio.qc" or str(node.get("plugin_version")) != "1":
                _invalid("stage_audio_qc_node_invalid")
            config = canonical(config)
            if not isinstance(config, dict) or set(config) - _QC_FIELDS or config.get("quality_profile_ref") not in _QUALITY_REFS:
                _invalid("stage_audio_quality_profile_required")
            options = {"enabled": config.get("alignment_enabled", False), "srt_mode": config.get("srt_mode", "none")}
            for field in ("master_revision_id", "receipt_id", "output_hash"):
                if "asr_" + field in config:
                    options[field] = config["asr_" + field]
            run, workflow, targets = _dependencies(db, user, unit, node, context)
            target, revision, task, script, source = _accepted_audio(db, targets, run, user, unit, local_qc=True)
            proof = None
            stage_asr = [item for item in targets if item and item.get("domain") == "audio_asr"]
            if stage_asr and options["enabled"] is True:
                from .stage_audio_asr import accepted_alignment

                if set(options) != {"enabled", "srt_mode"} or options["srt_mode"] not in {"none", "asr", "estimated"}:
                    _invalid("stage_audio_alignment_source_ambiguous")
                enabled, mode = True, options["srt_mode"]
                proof = accepted_alignment(db, targets, run, user, unit, revision, task, script)
            else:
                try:
                    enabled, mode = audio_quality.alignment_options(options)
                except ValueError as exc:
                    _invalid(str(exc))
            report = audio_quality.check_audio(db, revision, task=task, quality_profile_ref=config["quality_profile_ref"],
                                               script=script, alignment=options if enabled or mode != "none" else None,
                                               accepted_stage_asr=proof)
            snapshot = {"schema": _QC_SCHEMA, "kind": "checks", "audio_quality": True,
                "actor_id": user.id, "project_id": unit.project_id, "unit_id": unit.id, "run_id": run.id,
                "node": {key: node[key] for key in ("id", "plugin", "plugin_version")}, "workflow": workflow,
                "config": config, "config_hash": digest(config), "accepted_target": target,
                "material_revision_id": revision.id, "content_hash": revision.content_hash, "task_id": task.id,
                "task_request_hash": task.request_hash, "task_plan_hash": task.plan_hash,
                "task_input_hash": task.input_hash, "task_result_signature_hash": digest(task.result_signature),
                "task_acceptance_hash": task.acceptance_hash, "script": script, "script_hash": digest(script),
                "tts_source_hash": digest(source), "quality_profile_ref": config["quality_profile_ref"],
                "preset": {"ref": report["quality_profile_ref"], "hash": report["quality_profile_hash"]},
                "qc_report": report, "expected_revision": 0}
            snapshot["input_hash"] = digest(snapshot)
            return canonical({**context, "domain": snapshot}), config, []
    except (StageInvocationError, HTTPException, StageContractError, ValueError, TypeError, KeyError, AttributeError) as exc:
        return context if isinstance(context, dict) else {}, config if isinstance(config, dict) else {}, [_blocker(exc)]


def _qc_snapshot(snapshot):
    snapshot = canonical(snapshot)
    if (not isinstance(snapshot, dict) or snapshot.get("schema") != _QC_SCHEMA or snapshot.get("audio_quality") is not True
            or snapshot.get("kind") != "checks"
            or snapshot.get("input_hash") != digest({key: value for key, value in snapshot.items() if key != "input_hash"})
            or snapshot.get("config_hash") != digest(snapshot.get("config"))
            or snapshot.get("script_hash") != digest(snapshot.get("script"))):
        _invalid("stage_audio_qc_snapshot_invalid")
    return snapshot


def qc_result(db, snapshot):
    """Return the standard checks projection with currentness only on current_checks."""
    snapshot = _qc_snapshot(snapshot)
    with db.no_autoflush:
        user = db.get(User, snapshot["actor_id"])
        unit = db.get(ContentUnit, snapshot["unit_id"])
        if user is None or user.is_active is not True or unit is None or unit.project_id != snapshot["project_id"]:
            _invalid("stage_audio_qc_scope_changed")
        context, _, blockers = prepare_qc(db, user, unit, snapshot["node"], snapshot["config"],
            {key: snapshot[key] for key in ("project_id", "unit_id", "run_id")})
        if blockers:
            _invalid(blockers[0])
        current = context["domain"]
        def item(value):
            return {"id": value["material_revision_id"], "check_kind": "audio_quality", "input_hash": value["input_hash"],
                    "status": value["qc_report"]["status"], "report": value["qc_report"]}
        is_current = current["input_hash"] == snapshot["input_hash"]
        return canonical({"audio_quality": True, "audio_snapshot": snapshot,
            "material_revision_id": snapshot["material_revision_id"], "content_hash": snapshot["content_hash"],
            "task_id": snapshot["task_id"], "quality_profile_ref": snapshot["quality_profile_ref"],
            "input_hash": snapshot["input_hash"], "checks": [item(snapshot)],
            "current_checks": [{**item(current), "is_current": is_current}], "expected_revision": 0,
            "checks_pass": is_current and current["qc_report"]["status"] == "pass",
            "checks_reviewable": is_current and current["qc_report"]["status"] in {"pass", "warning"},
            "blockers": [] if is_current and current["qc_report"]["status"] in {"pass", "warning"} else ["audio_quality"]})


def validate_qc_result(db, result):
    """Fail closed on changed accepted inputs, bytes, rights, task receipt or QC rules."""
    result = canonical(result)
    if not isinstance(result, dict) or result.get("audio_quality") is not True:
        _invalid("stage_audio_qc_proof_invalid")
    current = qc_result(db, result.get("audio_snapshot") or {})
    if current != result or any(item["is_current"] is not True for item in current["current_checks"]):
        _invalid("stage_audio_qc_inputs_changed")
    return current["current_checks"]
