"""Package-bound external work and explicit, rights-preserving acceptance."""

from __future__ import annotations

import hashlib
import inspect
import io
import re
from functools import wraps

from fastapi import HTTPException
from PIL import Image, UnidentifiedImageError
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import (
    AuditLog,
    CreativeExecution,
    CreativeExecutionOutput,
    CreativeExecutionPackage,
    MaterialRevision,
    ProjectEvent,
    ProjectMaterialReference,
    User,
    utcnow,
)
from . import creative_execution_files as files
from .content_masters import owned_unit
from .creative_contracts import (
    EXECUTOR_DECLARATION_FIELDS,
    MAX_FILE_BYTES,
    MAX_INPUTS,
    MAX_OUTPUT_ROWS,
    bounded_json,
    canonical_hash,
    canonical_output_contract,
    executor_descriptor,
    safe_metadata,
)
from .creative_packages import (
    check_inputs,
    create_package,
    manual_image_configuration,
    owned_package,
    package_projection,
)
from .materials import (
    _EXTERNAL_EXECUTION_ACCEPTANCE,
    EXECUTION_TEXT_MIME,
    create_material,
    create_revision,
    validate_execution_file,
)
from .project_events import record_project_event

TERMINAL = {"accepted", "rejected", "cancelled", "superseded", "failed_before_dispatch"}
MAX_INPUT_BYTES = 100 * 1024 * 1024
MAX_ATTEMPTS = 20
_HASH = re.compile(r"[0-9a-f]{64}\Z")
_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]*\Z")
_PATH = re.compile(r"file://|(?:^|[\s\"'=])/(?:[A-Za-z0-9_.-]+/)+|[A-Za-z]:[\\/]|Traceback \(most recent call", re.IGNORECASE)
_REASONS = {
    "executor_blocked", "needs_output_replacement", "input_unavailable",
    "validation_failed", "preparation_failed", "dispatch_uncertain",
    "reconciliation_needed", "executor_failed", "cancelled_by_user",
    "superseded_by_user", "rejected_by_user",
}
_CERTAINTY = {"not_dispatched": 0, "possibly_dispatched": 1, "confirmed_dispatched": 2}
MANUAL_IMAGE_EXECUTOR = {"executor_kind": "human", "executor_key": "chatgpt-manual-image", "executor_version": "1"}


def _manual_package(db: Session, row: CreativeExecution, user: User, *, current: bool = True) -> CreativeExecutionPackage:
    if any(getattr(row, key) != value for key, value in MANUAL_IMAGE_EXECUTOR.items()):
        raise _error("manual_image_execution_required", 422)
    package = _package(db, row, user, current=current)
    handoff = package.package_json.get("manual_image", {})
    if (handoff.get("schema") != "chatgpt.manual-image.v1" or handoff.get("origin") != "user_declared_chatgpt"
            or handoff.get("runtime_verified") is not False
            or canonical_hash(handoff.get("prompt")) != handoff.get("prompt_hash")
            or canonical_hash(handoff.get("configuration")) != handoff.get("configuration_hash")):
        raise _error("manual_image_package_integrity")
    manual_image_configuration(handoff["configuration"])
    return package


def prepare_manual_image(db: Session, project_id: int, unit_id: int, payload: dict, user: User) -> dict:
    owned_unit(db, project_id, unit_id, user, mutate=True)
    config = manual_image_configuration({key: payload[key] for key in ("brief", "style", "usage", "aspect_ratio", "width", "height", "candidate_count")})
    key = _identifier(payload.get("idempotency_key"), "idempotency_key", 150)
    existing = db.scalar(select(CreativeExecution).where(CreativeExecution.owner_user_id == user.id, CreativeExecution.idempotency_key == key))
    if existing:
        row = _owned(db, project_id, unit_id, existing.id, user, mutate=True)
        package = _manual_package(db, row, user)
        if (package.package_json["manual_image"]["configuration"] != config
                or package.source_master_revision_id != payload.get("source_master_revision_id")
                or package.source_variant_revision_id != payload.get("source_variant_revision_id")):
            raise _error("creative_execution_idempotency_conflict")
    else:
        package_result = create_package(db, project_id=project_id, unit_id=unit_id, user=user, manual_image=config,
            payload={"source_master_revision_id": payload.get("source_master_revision_id"),
                "source_variant_revision_id": payload.get("source_variant_revision_id"), "objective": "ChatGPT 人工生图交接",
                "output_contract": {"roles": [{"role_id": "image", "kind": "image", "required": True,
                    "allowed_mime": ["image/png", "image/jpeg", "image/webp"], "min_count": 1,
                    "max_count": config["candidate_count"], "max_bytes": 10 * 1024 * 1024}]},
                "acceptance_criteria": ["选择至少一个实际图片候选并明确接受；上传不等于入库", "用户声明ChatGPT来源，不验证网站模型或实际Prompt消费"]})
        result = prepare_execution(db, project_id, unit_id, {**MANUAL_IMAGE_EXECUTOR, "package_id": package_result["id"],
            "idempotency_key": key, "metadata": {"summary": "用户手动操作ChatGPT；本系统未操作浏览器或调用模型"}}, user)
        row = _owned(db, project_id, unit_id, result["id"], user, mutate=True)
        package = _manual_package(db, row, user)
    handoff = package.package_json["manual_image"]
    return {"package": package_projection(db, package, user), "execution": _projection(db, row, user),
        "prompt": handoff["prompt"], "prompt_hash": handoff["prompt_hash"]}


def _manual_image_bytes(content: bytes, mime: str, config: dict, maximum: int) -> tuple[int, int]:
    if not content or len(content) > maximum:
        raise _error("manual_image_file_size_invalid", 413)
    if mime not in {"image/png", "image/jpeg", "image/webp"}:
        raise _error("manual_image_mime_invalid", 422)
    validate_execution_file(content, mime, "image")
    try:
        with Image.open(io.BytesIO(content)) as image:
            width, height = image.size
            if (width, height) != (config["width"], config["height"]) or getattr(image, "n_frames", 1) != 1:
                raise _error("manual_image_dimensions_mismatch", 422)
            image.verify()
        with Image.open(io.BytesIO(content)) as image:
            image.load()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise _error("manual_image_decode_failed", 422) from None
    return width, height


def upload_manual_image(db: Session, project_id: int, unit_id: int, execution_id: int, payload: dict,
        content: bytes, mime: str, user: User) -> dict:
    row = _owned(db, project_id, unit_id, execution_id, user, mutate=True)
    package = _manual_package(db, row, user)
    handoff = package.package_json["manual_image"]
    width, height = _manual_image_bytes(content, mime, handoff["configuration"], handoff["max_bytes"])
    index = _id(payload.get("output_index"), name="output_index")
    digest = hashlib.sha256(content).hexdigest()
    previous = _latest(_outputs(db, row)).get(("image", index))
    if previous and previous.state in {"staged", "accepted"} and previous.content_hash == digest and previous.mime_type == mime:
        return _projection(db, row, user)
    _expected(row, payload)
    if index > handoff["configuration"]["candidate_count"]:
        raise _error("creative_execution_output_count_exceeded", 422)
    if previous and previous.state != "rejected":
        raise _error("creative_execution_output_replacement_denied")
    if row.state == "prepared":
        result = transition_execution(db, project_id, unit_id, row.id, {**MANUAL_IMAGE_EXECUTOR,
            "expected_revision": row.revision_no, "action": "claim"}, user)
        row = _owned(db, project_id, unit_id, result["id"], user, mutate=True)
    _writable(db, row, output=True)
    # The selected references are declared external inputs; reserve their live rights before handing off any result.
    if not row.materialized_inputs_json and package.package_json["assets"]:
        result = materialize_inputs(db, project_id, unit_id, row.id, {**MANUAL_IMAGE_EXECUTOR,
            "expected_revision": row.revision_no}, user)
        row = _owned(db, project_id, unit_id, result["id"], user, mutate=True)
    return submit_output(db, project_id, unit_id, row.id, {**MANUAL_IMAGE_EXECUTOR,
        "expected_revision": row.revision_no, "role_id": "image", "output_index": index,
        "mime_type": mime, "content_hash": digest,
        "metadata": {"summary": f"用户声明ChatGPT生成；实际上传图片 {width}×{height}；网站模型与Prompt消费未验证"}}, user, uploaded_content=content)


def accept_manual_image(db: Session, project_id: int, unit_id: int, execution_id: int, output_id: int, payload: dict, user: User) -> dict:
    row = _owned(db, project_id, unit_id, execution_id, user, mutate=True)
    _manual_package(db, row, user)
    if payload.get("decision") != "accept":
        raise _error("creative_execution_output_decision_invalid", 422)
    output = next((item for item in _outputs(db, row) if item.id == output_id), None)
    if output and output.state == "accepted":
        _live_materialized(db, row, _manual_package(db, row, user))
        revision = db.get(MaterialRevision, output.material_revision_id)
        receipt = revision.source_metadata_json if revision else {}
        expected_hash = canonical_hash({key: value for key, value in payload.items() if key != "expected_revision"})
        if (receipt.get("manual_acceptance_hash") != expected_hash or revision.content_hash != output.content_hash
                or hashlib.sha256(files.read_material(revision)).hexdigest() != output.content_hash):
            raise _error("manual_image_acceptance_conflict")
        result = _projection(db, row, user)
    else:
        if row.state in TERMINAL:
            raise _error("creative_execution_terminal")
        result = decide_output(db, project_id, unit_id, execution_id, output_id, payload, user)
    accepted = next(item for item in result["outputs"] if item["id"] == output_id)
    revision = db.get(MaterialRevision, accepted["material_revision_id"])
    result["accepted_material"] = {"material_id": revision.material_id, "material_revision_id": revision.id,
        "content_hash": revision.content_hash}
    return result


def _error(code: str, status: int = 409) -> HTTPException:
    return HTTPException(status, {"code": code})


def _atomic(function):
    signature = inspect.signature(function)

    @wraps(function)
    def call(db, *args, **kwargs):
        try:
            arguments = signature.bind(db, *args, **kwargs).arguments
            user = arguments["user"]
            execution_id = arguments.get("execution_id")
            if execution_id is None:
                execution_id = db.scalar(select(CreativeExecution.id).where(
                    CreativeExecution.owner_user_id == user.id,
                    CreativeExecution.idempotency_key == arguments["payload"].get("idempotency_key"),
                ))
            before = db.scalar(select(CreativeExecution.revision_no).where(
                CreativeExecution.id == execution_id, CreativeExecution.owner_user_id == user.id,
            )) if execution_id is not None else None
            result = function(db, *args, **kwargs)
            if before != result["revision_no"]:
                event_type = "creative_execution.prepared" if before is None else "creative_execution.updated"
                detail = {"execution_id": result["id"], "package_id": result["package_id"],
                    "package_hash": result["package_hash"], "previous_revision": before,
                    "revision_no": result["revision_no"], "state": result["state"],
                    "operation": "materialize_inputs" if function.__name__ == "_reserve_inputs" else function.__name__,
                    "dispatch_certainty": result["dispatch_certainty"]}
                if result["executor_descriptor"]["declaration_status"] == "declared":
                    detail["executor_descriptor"] = result["executor_descriptor"]
                if arguments["payload"].get("action") == "reconcile":
                    detail["recovery"] = result["recovery"]
                    detail["checkpoint_binding"] = result["checkpoint_binding"]
                if "output_id" in arguments:
                    detail["output_id"] = arguments["output_id"]
                    if "decision" in arguments["payload"]:
                        detail["decision"] = arguments["payload"]["decision"]
                record_project_event(db, project_id=result["project_id"], event_type=event_type,
                    actor=user.email, entity_type="creative_execution", entity_id=result["id"], payload=detail)
                db.add(AuditLog(event=event_type, actor=user.email, entity_type="creative_execution",
                    entity_id=str(result["id"]), detail_json=detail))
            db.commit()
            return result
        except IntegrityError:
            db.rollback()
            raise _error("creative_execution_conflict") from None
        except BaseException:
            db.rollback()
            raise
    return call


def _payload(payload: dict, fields: set[str]) -> dict:
    if not isinstance(payload, dict) or set(payload) - fields:
        raise _error("creative_execution_field_invalid", 422)
    return payload


def _id(value, *, name: str = "id", minimum: int = 1) -> int:
    if type(value) is not int or value < minimum:
        raise _error(f"creative_execution_{name}_invalid", 422)
    return value


def _identifier(value, name: str, maximum: int) -> str:
    if not isinstance(value, str) or not 1 <= len(value) <= maximum or not _IDENTIFIER.fullmatch(value):
        raise _error(f"creative_execution_{name}_invalid", 422)
    bounded_json(value, max_bytes=1000)
    return value


def _metadata(value) -> dict:
    if value is not None and not isinstance(value, dict):
        raise _error("creative_execution_metadata_invalid", 422)
    metadata = safe_metadata(value)
    if any(_PATH.search(item) for item in metadata.values() if isinstance(item, str)):
        raise _error("creative_execution_metadata_unsafe", 422)
    for key in ("supports_checkpoint", "supports_recover", "supports_revert"):
        if key in metadata and type(metadata[key]) is not bool:
            raise _error("creative_execution_capability_invalid", 422)
    if "observation_hash" in metadata and not _HASH.fullmatch(str(metadata["observation_hash"])):
        raise _error("creative_execution_observation_invalid", 422)
    return bounded_json(metadata, max_bytes=4000)


def _checkpoint(value) -> dict:
    checkpoint = _metadata(value)
    if checkpoint.get("readback_status") in {"verified", "succeeded"} and not checkpoint.get("observation_hash"):
        raise _error("creative_execution_checkpoint_observation_required", 422)
    return checkpoint


def _read_checkpoint(row: CreativeExecution, package: CreativeExecutionPackage) -> tuple[dict, dict | None]:
    stored = row.checkpoint_json or {}
    if not isinstance(stored, dict):
        raise _error("creative_execution_checkpoint_binding_invalid")
    if "binding" not in stored:
        metadata = _checkpoint(stored)
        if metadata.get("checkpoint_ref"):
            raise _error("creative_execution_checkpoint_binding_invalid")
        return metadata, None
    if set(stored) != {"metadata", "binding"}:
        raise _error("creative_execution_checkpoint_binding_invalid")
    metadata = _checkpoint(stored["metadata"])
    binding = stored["binding"]
    expected = {"execution_id": row.id, "package_id": package.id, "package_hash": package.package_hash,
        "executor_kind": row.executor_kind, "executor_key": row.executor_key, "executor_version": row.executor_version}
    if (not isinstance(binding, dict) or set(binding) != set(expected) | {"revision_no"}
            or any(binding.get(key) != value for key, value in expected.items())
            or type(binding.get("revision_no")) is not int or not 2 <= binding["revision_no"] <= row.revision_no
            or not metadata.get("checkpoint_ref")):
        raise _error("creative_execution_checkpoint_binding_invalid")
    return metadata, binding


def _executor(payload: dict, row: CreativeExecution | None = None) -> dict:
    identity = {key: _identifier(payload.get(key), key, maximum) for key, maximum in (
        ("executor_kind", 30), ("executor_key", 150), ("executor_version", 50)
    )}
    if row and any(identity[key] != getattr(row, key) for key in identity):
        raise _error("creative_execution_executor_mismatch")
    return identity


def _owned(db: Session, project_id: int, unit_id: int, execution_id: int, user: User, *, mutate: bool = False) -> CreativeExecution:
    owned_unit(db, project_id, unit_id, user, mutate=mutate)
    if mutate:
        db.expire_all()
    row = db.scalar(select(CreativeExecution).where(CreativeExecution.id == execution_id).execution_options(populate_existing=True))
    if row is None or (row.owner_user_id, row.project_id, row.content_unit_id) != (user.id, project_id, unit_id):
        raise _error("creative_execution_not_found", 404)
    return row


def _expected(row: CreativeExecution, payload: dict) -> int:
    expected = _id(payload.get("expected_revision"), name="expected_revision")
    if expected != row.revision_no:
        raise _error("creative_execution_revision_conflict")
    return expected


def _has_claim(db: Session, row: CreativeExecution) -> bool:
    # A pre-dispatch blocker is not proof that the executor ever claimed the task.
    return db.scalar(select(ProjectEvent.id).where(
        ProjectEvent.project_id == row.project_id, ProjectEvent.event_type == "creative_execution.updated",
        ProjectEvent.entity_type == "creative_execution", ProjectEvent.entity_id == str(row.id),
        ProjectEvent.payload_json["state"].as_string() == "claimed",
        ProjectEvent.payload_json["operation"].as_string() == "transition_execution",
        ProjectEvent.payload_json["package_id"].as_integer() == row.package_id,
        ProjectEvent.payload_json["revision_no"].as_integer() <= row.revision_no,
    ).limit(1)) is not None


def _cas(db: Session, row: CreativeExecution, expected: int, **values) -> None:
    changed = db.execute(update(CreativeExecution).where(
        CreativeExecution.id == row.id, CreativeExecution.owner_user_id == row.owner_user_id,
        CreativeExecution.project_id == row.project_id, CreativeExecution.content_unit_id == row.content_unit_id,
        CreativeExecution.revision_no == expected,
    ).values(**values, revision_no=expected + 1, updated_at=utcnow()).execution_options(synchronize_session=False))
    if changed.rowcount != 1:
        raise _error("creative_execution_revision_conflict")
    db.refresh(row)


def _package(db: Session, row: CreativeExecution, user: User, *, current: bool = False) -> CreativeExecutionPackage:
    if current:
        package = owned_package(db, row.project_id, row.content_unit_id, row.package_id, user)
        revision_ids = sorted({ref["material_revision_id"] for ref in package.package_json["assets"]})
        if revision_ids:
            db.scalars(select(MaterialRevision).join(MaterialRevision.material).where(MaterialRevision.id.in_(revision_ids))
                .order_by(MaterialRevision.id).with_for_update().execution_options(populate_existing=True)).all()
    return owned_package(db, row.project_id, row.content_unit_id, row.package_id, user, current=current)


def _guard_unknown(db: Session, package: CreativeExecutionPackage, *, exclude_id: int | None = None) -> None:
    query = select(CreativeExecution.id).where(
        CreativeExecution.owner_user_id == package.owner_user_id, CreativeExecution.project_id == package.project_id,
        CreativeExecution.content_unit_id == package.content_unit_id, CreativeExecution.state == "unknown",
    )
    if exclude_id is not None:
        query = query.where(CreativeExecution.id != exclude_id)
    if db.scalar(query.limit(1)) is not None:
        raise _error("creative_execution_reconciliation_required")


def _roles(package: CreativeExecutionPackage) -> list[dict]:
    return canonical_output_contract(package.package_json["output_contract"])["roles"]


def _outputs(db: Session, row: CreativeExecution) -> list[CreativeExecutionOutput]:
    outputs = list(db.scalars(select(CreativeExecutionOutput).where(CreativeExecutionOutput.execution_id == row.id)
        .order_by(CreativeExecutionOutput.id).limit(MAX_OUTPUT_ROWS + 1).execution_options(populate_existing=True)).all())
    if len(outputs) > MAX_OUTPUT_ROWS:
        raise _error("creative_execution_output_history_limit")
    return outputs


def _latest(outputs: list[CreativeExecutionOutput]) -> dict[tuple[str, int], CreativeExecutionOutput]:
    latest = {}
    for output in outputs:
        key = (output.role_id, output.output_index)
        if key not in latest or output.attempt_no > latest[key].attempt_no:
            latest[key] = output
    return latest


def _counts(package: CreativeExecutionPackage, outputs: list[CreativeExecutionOutput]) -> list[dict]:
    latest = _latest(outputs)
    roles = _roles(package)
    role_ids = {role["role_id"] for role in roles}
    if any(output.role_id not in role_ids for output in outputs):
        raise _error("creative_execution_output_contract_mismatch")
    counts = []
    for role in roles:
        members = [output for (role_id, _), output in latest.items() if role_id == role["role_id"]]
        if len(members) > role["max_count"] or any(
            output.kind != role["kind"] or output.mime_type not in role["allowed_mime"]
            or not 0 < output.size_bytes <= role["max_bytes"]
            or not 1 <= output.output_index <= role["max_count"] for output in members
        ):
            raise _error("creative_execution_output_contract_mismatch")
        counts.append({**role, "staged_count": sum(output.state in {"staged", "accepted"} for output in members),
            "accepted_count": sum(output.state == "accepted" for output in members),
            "rejected_indexes": [output.output_index for output in members if output.state == "rejected"]})
    return counts


def _completion(package: CreativeExecutionPackage, outputs: list[CreativeExecutionOutput]) -> tuple[bool, bool]:
    required = [count for count in _counts(package, outputs) if count["required"]]
    if any(count["rejected_indexes"] for count in required):
        return False, False
    return (bool(required) and all(count["staged_count"] >= count["min_count"] for count in required),
            bool(required) and all(count["accepted_count"] >= count["min_count"] for count in required))


def _needs_replacement(package: CreativeExecutionPackage, outputs: list[CreativeExecutionOutput]) -> bool:
    return any(count["required"] and count["rejected_indexes"]
        for count in _counts(package, outputs))


def _output_json(output: CreativeExecutionOutput) -> dict:
    return {"id": output.id, "execution_id": output.execution_id, "role_id": output.role_id, "kind": output.kind,
        "output_index": output.output_index, "attempt_no": output.attempt_no, "staging_key": output.staging_key,
        "mime_type": output.mime_type, "content_hash": output.content_hash, "size_bytes": output.size_bytes,
        "metadata": _metadata(output.metadata_json), "state": output.state, "material_revision_id": output.material_revision_id,
        "created_by": output.created_by, "created_at": output.created_at.isoformat() if output.created_at else None,
        "decided_by": output.decided_by, "decided_at": output.decided_at.isoformat() if output.decided_at else None}


def _cleanup_query(row: CreativeExecution):
    return select(ProjectEvent).where(
        ProjectEvent.project_id == row.project_id, ProjectEvent.entity_type == "creative_execution",
        ProjectEvent.entity_id == str(row.id), ProjectEvent.event_type == "creative_execution.updated",
        ProjectEvent.payload_json["operation"].as_string() == "cleanup_staging",
    )


def _cleanup_order():
    # Older records already froze revision_no at intent creation; a late result
    # must rank within that intent rather than supersede a newer cleanup.
    intent_revision = func.coalesce(ProjectEvent.payload_json["intent_revision"].as_integer(),
        ProjectEvent.payload_json["revision_no"].as_integer(), 0)
    return intent_revision.desc(), ProjectEvent.id.desc()


def _projection(db: Session, row: CreativeExecution, user: User, *, include_outputs: bool = True) -> dict:
    package = _package(db, row, user)
    checkpoint, checkpoint_binding = _read_checkpoint(row, package)
    outputs = _outputs(db, row)
    result = {key: getattr(row, key) for key in ("id", "project_id", "content_unit_id", "package_id", "idempotency_key",
        "request_fingerprint", "executor_kind", "executor_key", "executor_version", "state", "revision_no", "dispatch_certainty", "safe_reason", "retry_of_id", "created_by")}
    result.update({"package_hash": package.package_hash, "output_contract": package.package_json["output_contract"],
        "executor_descriptor": executor_descriptor({key: getattr(row, key) for key in ("executor_kind", "executor_key", "executor_version")}, checkpoint),
        "output_counts": _counts(package, outputs), "checkpoint": checkpoint, "checkpoint_binding": checkpoint_binding,
        "recovery": _checkpoint(row.recovery_json),
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None})
    if include_outputs:
        result["outputs"] = [_output_json(output) for output in outputs]
        ranked = _cleanup_query(row).with_only_columns(ProjectEvent.id.label("event_id"),
            func.row_number().over(partition_by=ProjectEvent.payload_json["staging_key"].as_string(),
                order_by=_cleanup_order()).label("cleanup_rank")).subquery()
        latest_ids = select(ranked.c.event_id).where(ranked.c.cleanup_rank == 1)
        cleanups = db.scalars(select(ProjectEvent).where(ProjectEvent.id.in_(latest_ids))).all()
        by_output = {}
        for event in cleanups:
            detail = event.payload_json
            for output_id in detail.get("output_ids", []):
                if output_id not in by_output:
                    by_output[output_id] = detail
        for output in result["outputs"]:
            output["staging_cleanup"] = by_output.get(output["id"])
        result["materialized_inputs"] = row.materialized_inputs_json or []
    else:
        result["materialized_input_count"] = len(row.materialized_inputs_json or [])
    return result


@_atomic
def prepare_execution(db: Session, project_id: int, unit_id: int, payload: dict, user: User) -> dict:
    _payload(payload, {"package_id", "idempotency_key", "executor_kind", "executor_key", "executor_version", "retry_of_id", "metadata"})
    owned_unit(db, project_id, unit_id, user, mutate=True)
    package = owned_package(db, project_id, unit_id, _id(payload.get("package_id")), user)
    _roles(package)
    key = _identifier(payload.get("idempotency_key"), "idempotency_key", 150)
    executor = _executor(payload)
    metadata = _checkpoint(payload.get("metadata"))
    if any(key in metadata for key in ("checkpoint_ref", "observation_hash", "observation_ref", "readback_status")):
        raise _error("creative_execution_checkpoint_requires_claim", 422)
    retry_of_id = payload.get("retry_of_id")
    if retry_of_id is not None:
        _id(retry_of_id, name="retry_of_id")
    fingerprint = canonical_hash({"owner_user_id": user.id, "project_id": project_id, "unit_id": unit_id,
        "package_id": package.id, "package_hash": package.package_hash, **executor, "retry_of_id": retry_of_id, "metadata": metadata})
    existing = db.scalar(select(CreativeExecution).where(CreativeExecution.owner_user_id == user.id,
        CreativeExecution.idempotency_key == key).execution_options(populate_existing=True))
    if existing:
        if existing.request_fingerprint != fingerprint:
            raise _error("creative_execution_idempotency_conflict")
        return _projection(db, existing, user)
    descriptor = executor_descriptor(executor, metadata, require_complete=True)
    if descriptor["declaration_status"] == "declared" and any(role["kind"] not in descriptor["output_kinds"] for role in _roles(package)):
        raise _error("creative_execution_output_kinds_contract_mismatch", 422)
    _guard_unknown(db, package)
    owned_package(db, project_id, unit_id, package.id, user, current=True)
    if retry_of_id is not None:
        parent = _owned(db, project_id, unit_id, retry_of_id, user)
        if parent.state != "failed_before_dispatch" or parent.dispatch_certainty != "not_dispatched" or parent.idempotency_key == key:
            raise _error("creative_execution_retry_denied")
        _executor(payload, parent)
        if db.scalar(select(CreativeExecution.id).where(CreativeExecution.retry_of_id == parent.id).limit(1)):
            raise _error("creative_execution_retry_already_prepared")
    row = CreativeExecution(owner_user_id=user.id, project_id=project_id, content_unit_id=unit_id,
        package_id=package.id, idempotency_key=key, request_fingerprint=fingerprint, **executor, state="prepared",
        revision_no=1, dispatch_certainty="not_dispatched", checkpoint_json=metadata, recovery_json={},
        materialized_inputs_json=[], retry_of_id=retry_of_id, created_by=user.email)
    db.add(row)
    db.flush()
    with files.root_fd(user.id, row.id, create=True):
        pass
    return _projection(db, row, user)


def _cleanup_references(db: Session, row: CreativeExecution, output: CreativeExecutionOutput, user: User) -> list[int]:
    if row.state == "unknown" or (row.state == "blocked" and row.safe_reason != "needs_output_replacement"):
        raise _error("creative_execution_cleanup_unresolved")
    if (output.state not in {"rejected", "accepted"}
            and not (output.state == "staged" and row.state in TERMINAL - {"accepted"})):
        raise _error("creative_execution_cleanup_not_discardable")
    if not _HASH.fullmatch(output.content_hash) or output.staging_key != f"staging/{output.content_hash}.bin":
        raise _error("creative_execution_cleanup_target_invalid")
    refs = [item for item in _outputs(db, row) if item.staging_key == output.staging_key]
    package_hash = _package(db, row, user).package_hash if any(ref.state == "accepted" for ref in refs) else None
    for ref in refs:
        if (ref.content_hash, ref.size_bytes) != (output.content_hash, output.size_bytes):
            raise _error("creative_execution_cleanup_reference_invalid")
        # Optional outputs can still be accepted after required outputs complete.
        if ref.state == "staged" and row.state not in TERMINAL - {"accepted"}:
            raise _error("creative_execution_cleanup_shared_pending")
        if ref.state not in {"staged", "accepted", "rejected"}:
            raise _error("creative_execution_cleanup_reference_invalid")
        if ref.state == "accepted":
            revision = db.get(MaterialRevision, ref.material_revision_id)
            provenance = revision.source_metadata_json if revision else None
            expected = {"execution_id": row.id, "output_id": ref.id, "package_id": row.package_id,
                "package_hash": package_hash, "owner_user_id": user.id,
                "project_id": row.project_id, "content_unit_id": row.content_unit_id, "output_hash": ref.content_hash}
            if (revision is None or revision.source_kind != "external_execution"
                    or revision.content_hash != ref.content_hash or revision.mime_type != ref.mime_type
                    or not isinstance(provenance, dict)
                    or any(provenance.get(key) != value for key, value in expected.items())
                    or not isinstance(revision.file_path, str)
                    or not re.fullmatch(r"material/[0-9a-f]{2}/" + ref.content_hash + r"(?:\.[A-Za-z0-9]+)?", revision.file_path)):
                raise _error("creative_execution_cleanup_material_unverified")
            content = files.read_material(revision)
            if len(content) != ref.size_bytes or hashlib.sha256(content).hexdigest() != ref.content_hash:
                raise _error("creative_execution_cleanup_material_unverified")
    return [ref.id for ref in refs]


def _record_cleanup(db: Session, row: CreativeExecution, user: User, detail: dict) -> dict:
    event_type = "creative_execution.updated"
    detail = {**detail, "operation": "cleanup_staging"}
    event = record_project_event(db, project_id=row.project_id, event_type=event_type, actor=user.email,
        entity_type="creative_execution", entity_id=row.id, payload=detail)
    db.add(AuditLog(event=event_type, actor=user.email, entity_type="creative_execution",
        entity_id=str(row.id), detail_json=event.payload_json))
    db.flush()
    return event.payload_json


def _cleanup_response(db: Session, row: CreativeExecution, user: User, output_id: int) -> dict:
    result = _projection(db, row, user)
    result["staging_cleanup"] = next(output["staging_cleanup"] for output in result["outputs"] if output["id"] == output_id)
    return result


@_atomic
def cleanup_output(db: Session, project_id: int, unit_id: int, execution_id: int, output_id: int, payload: dict, user: User) -> dict:
    _payload(payload, {"expected_revision", "confirm_temporary_only"})
    if user.role not in {"admin", "editor"}:
        raise _error("creative_execution_cleanup_editor_required", 403)
    if payload.get("confirm_temporary_only") is not True:
        raise _error("creative_execution_cleanup_confirmation_required", 422)
    requested_revision = _id(payload.get("expected_revision"), name="expected_revision")
    row = _owned(db, project_id, unit_id, execution_id, user, mutate=True)
    output = next((item for item in _outputs(db, row) if item.id == output_id), None)
    if output is None:
        raise _error("creative_execution_output_not_found", 404)
    previous = db.scalar(_cleanup_query(row).where(
        ProjectEvent.payload_json["staging_key"].as_string() == output.staging_key,
    ).order_by(*_cleanup_order()).limit(1))
    if previous and previous.payload_json.get("status") in {"removed", "already_absent"} and output_id in previous.payload_json.get("output_ids", []):
        return _cleanup_response(db, row, user, output_id)
    expected = _expected(row, payload)
    output_ids = _cleanup_references(db, row, output, user)
    _cas(db, row, expected)
    detail = {"execution_id": row.id, "package_id": row.package_id, "output_id": output.id,
        "output_ids": output_ids, "staging_key": output.staging_key, "content_hash": output.content_hash,
        "size_bytes": output.size_bytes, "requested_revision": requested_revision,
        "revision_no": row.revision_no, "intent_revision": row.revision_no,
        "status": "pending", "retryable": True, "code": None}
    _record_cleanup(db, row, user, detail)
    # Preserve intent across a crash; reacquire the writer guard before checking
    # every reference again, since another attempt may have reused this key.
    db.commit()
    row = _owned(db, project_id, unit_id, execution_id, user, mutate=True)
    try:
        _expected(row, {"expected_revision": expected + 1})
        output = next(item for item in _outputs(db, row) if item.id == output_id)
        if _cleanup_references(db, row, output, user) != output_ids:
            raise _error("creative_execution_cleanup_reference_invalid")
        detail = {**detail, "status": files.cleanup_staging(user.id, row.id, output.staging_key,
            content_hash=output.content_hash, size_bytes=output.size_bytes), "retryable": False}
    except (OSError, HTTPException) as exc:
        code = exc.detail.get("code") if isinstance(exc, HTTPException) and isinstance(exc.detail, dict) else "execution_storage_unavailable"
        detail = {**detail, "status": "failed", "retryable": True, "code": code}
    _record_cleanup(db, row, user, detail)
    return _cleanup_response(db, row, user, output_id)


def get_execution(db: Session, project_id: int, unit_id: int, execution_id: int, user: User) -> dict:
    return _projection(db, _owned(db, project_id, unit_id, execution_id, user), user)


def list_executions(db: Session, project_id: int, unit_id: int, user: User, *, limit: int = 50, offset: int = 0) -> dict:
    owned_unit(db, project_id, unit_id, user)
    if type(limit) is not int or not 1 <= limit <= 100 or type(offset) is not int or not 0 <= offset <= 100_000:
        raise _error("creative_execution_pagination_invalid", 422)
    rows = db.scalars(select(CreativeExecution).where(CreativeExecution.owner_user_id == user.id,
        CreativeExecution.project_id == project_id, CreativeExecution.content_unit_id == unit_id)
        .order_by(CreativeExecution.id.desc()).limit(limit).offset(offset)).all()
    return {"items": [_projection(db, row, user, include_outputs=False) for row in rows], "limit": limit, "offset": offset}


@_atomic
def transition_execution(db: Session, project_id: int, unit_id: int, execution_id: int, payload: dict, user: User) -> dict:
    _payload(payload, {"expected_revision", "action", "state", "executor_kind", "executor_key", "executor_version",
        "dispatch_certainty", "safe_reason", "metadata", "checkpoint", "recovery", "observation_hash", "summary", "resolution"})
    row = _owned(db, project_id, unit_id, execution_id, user, mutate=True)
    expected = _expected(row, payload)
    if row.state in TERMINAL:
        raise _error("creative_execution_terminal")
    if "action" in payload and "state" in payload:
        raise _error("creative_execution_transition_invalid", 422)
    action = payload.get("action", payload.get("state"))
    if not isinstance(action, str):
        raise _error("creative_execution_transition_invalid", 422)
    action = {"claim": "claimed", "start": "in_progress", "progress": "progress", "block": "blocked",
        "cancel": "cancelled", "supersede": "superseded", "reject": "rejected"}.get(action, action)
    certainty = payload.get("dispatch_certainty", row.dispatch_certainty)
    if not isinstance(certainty, str) or certainty not in _CERTAINTY:
        raise _error("creative_execution_dispatch_invalid", 422)
    reason = payload.get("safe_reason", row.safe_reason)
    if reason is not None and (not isinstance(reason, str) or reason not in _REASONS):
        raise _error("creative_execution_reason_invalid", 422)
    metadata = _metadata(payload.get("metadata"))
    package = _package(db, row, user)
    previous_checkpoint, checkpoint_binding = _read_checkpoint(row, package)
    checkpoint = _metadata(payload["checkpoint"]) if "checkpoint" in payload else previous_checkpoint
    descriptor = executor_descriptor({key: getattr(row, key) for key in ("executor_kind", "executor_key", "executor_version")}, previous_checkpoint)
    incoming_checkpoint = {**(checkpoint if "checkpoint" in payload else {}), **metadata}
    if descriptor["declaration_status"] == "declared":
        if any(key in incoming_checkpoint and incoming_checkpoint[key] != previous_checkpoint[key] for key in EXECUTOR_DECLARATION_FIELDS):
            raise _error("creative_execution_descriptor_conflict")
        checkpoint = {**checkpoint, **{key: previous_checkpoint[key] for key in EXECUTOR_DECLARATION_FIELDS}}
        if incoming_checkpoint.get("checkpoint_ref") and not descriptor["supports_checkpoint"]:
            raise _error("creative_execution_checkpoint_unsupported")
    elif "output_kinds" in incoming_checkpoint:
        raise _error("creative_execution_descriptor_requires_prepare", 422)
    incoming_recovery = _checkpoint(payload["recovery"]) if "recovery" in payload else {}
    recovery = incoming_recovery if "recovery" in payload else _checkpoint(row.recovery_json)
    if action == "reconcile":
        if row.state != "unknown":
            raise _error("creative_execution_reconcile_not_unknown")
        _executor(payload, row)
        observation = _metadata({"observation_hash": payload.get("observation_hash"), "summary": payload.get("summary")})
        if not isinstance(observation["summary"], str) or not observation["summary"].strip():
            raise _error("creative_execution_observation_required", 422)
        target = payload.get("resolution")
        if not isinstance(target, str) or target not in {"in_progress", "blocked", "result_ready", "failed_before_dispatch", "cancelled", "superseded", "rejected"}:
            raise _error("creative_execution_resolution_invalid", 422)
        if certainty == "possibly_dispatched" or "dispatch_certainty" not in payload:
            raise _error("creative_execution_reconcile_certainty_required", 422)
        if target == "failed_before_dispatch" and certainty != "not_dispatched":
            raise _error("creative_execution_retry_denied")
        if target in {"in_progress", "result_ready"}:
            package = _package(db, row, user, current=True)
            if target == "in_progress":
                _guard_unknown(db, package, exclude_id=row.id)
        if target == "result_ready" and not _completion(_package(db, row, user), _outputs(db, row))[0]:
            raise _error("creative_execution_required_outputs_missing")
        recovery_action = incoming_recovery.get("recovery_action", target)
        if recovery_action in {"recover", "revert", "continue"}:
            if (incoming_recovery.get("observation_hash") != observation["observation_hash"]
                    or incoming_recovery.get("readback_status") != "verified"):
                raise _error("creative_execution_recovery_observation_required", 422)
            if recovery_action in {"recover", "revert"}:
                if certainty != "confirmed_dispatched" or target == "failed_before_dispatch":
                    raise _error("creative_execution_predispatch_not_proven")
                if (not checkpoint_binding or not previous_checkpoint.get("checkpoint_ref")
                        or incoming_recovery.get("checkpoint_ref") != previous_checkpoint["checkpoint_ref"]
                        or any(previous_checkpoint.get(key) != value for key, value in incoming_checkpoint.items())):
                    raise _error("creative_execution_recovery_checkpoint_mismatch")
                if descriptor["declaration_status"] == "declared" and not descriptor[f"supports_{recovery_action}"]:
                    raise _error("creative_execution_recovery_unsupported")
                checkpoint = previous_checkpoint
            recovery = _metadata({**incoming_recovery, **observation})
        else:
            if "recovery_action" in incoming_recovery and recovery_action != target:
                raise _error("creative_execution_recovery_action_invalid", 422)
            recovery = _metadata({**recovery, **observation, "recovery_action": target, "readback_status": "observed"})
        reason = reason or ("executor_blocked" if target == "blocked" else None)
    else:
        if row.state == "unknown":
            raise _error("creative_execution_reconciliation_required")
        if _CERTAINTY[certainty] < _CERTAINTY[row.dispatch_certainty]:
            raise _error("creative_execution_dispatch_regression")
        if action == "fail":
            action = "failed_before_dispatch" if certainty == "not_dispatched" else "unknown"
        allowed = {
            "claimed": {"prepared"}, "in_progress": {"claimed", "blocked"},
            "progress": {"claimed", "in_progress", "blocked", "result_ready"},
            "blocked": {"prepared", "claimed", "in_progress", "result_ready", "blocked"},
            "failed_before_dispatch": {"prepared", "claimed", "blocked"},
            "unknown": {"claimed", "in_progress", "blocked", "result_ready"},
            "cancelled": {"prepared", "claimed", "in_progress", "blocked", "result_ready"},
            "superseded": {"prepared", "claimed", "in_progress", "blocked", "result_ready"},
            "rejected": {"prepared", "claimed", "in_progress", "blocked", "result_ready"},
        }
        if action not in allowed or row.state not in allowed[action]:
            raise _error("creative_execution_transition_denied")
        target = row.state if action == "progress" else action
        if action in {"claimed", "in_progress", "progress", "blocked", "failed_before_dispatch", "unknown"}:
            _executor(payload, row)
        if action in {"claimed", "in_progress"}:
            package = _package(db, row, user, current=True)
            _guard_unknown(db, package)
            if action == "in_progress" and _needs_replacement(_package(db, row, user), _outputs(db, row)):
                raise _error("creative_execution_output_replacement_required")
        if target == "in_progress" and certainty == "not_dispatched":
            certainty = "possibly_dispatched"
        if target == "claimed" and certainty != "not_dispatched":
            raise _error("creative_execution_dispatch_invalid", 422)
        if target == "failed_before_dispatch" and certainty != "not_dispatched":
            raise _error("creative_execution_predispatch_not_proven")
        if target == "unknown":
            certainty = "possibly_dispatched"
            reason = reason or "reconciliation_needed"
        elif certainty == "possibly_dispatched" and target in {"blocked", "cancelled", "superseded", "rejected"}:
            raise _error("creative_execution_reconciliation_required")
        if target == "blocked":
            reason = reason or "executor_blocked"
    if incoming_recovery.get("recovery_action") in {"recover", "revert", "continue"} and action != "reconcile":
        raise _error("creative_execution_recovery_observation_required", 422)
    if incoming_checkpoint.get("checkpoint_ref", previous_checkpoint.get("checkpoint_ref")) != previous_checkpoint.get("checkpoint_ref"):
        checkpoint = {key: value for key, value in checkpoint.items()
            if key not in {"observation_hash", "observation_ref", "readback_status"} or key in incoming_checkpoint}
    checkpoint = _checkpoint({**checkpoint, **metadata})
    claimed = action == "claimed" or _has_claim(db, row)
    if (checkpoint.get("checkpoint_ref") or target in {"in_progress", "unknown"} or action == "progress") and not claimed:
        raise _error("creative_execution_checkpoint_requires_claim", 422)
    stored_checkpoint = checkpoint
    if checkpoint.get("checkpoint_ref"):
        if checkpoint != previous_checkpoint or checkpoint_binding is None:
            checkpoint_binding = {"execution_id": row.id, "package_id": package.id, "package_hash": package.package_hash,
                "executor_kind": row.executor_kind, "executor_key": row.executor_key,
                "executor_version": row.executor_version, "revision_no": expected + 1}
        stored_checkpoint = {"metadata": checkpoint, "binding": checkpoint_binding}
    rejected_required = _needs_replacement(_package(db, row, user), _outputs(db, row))
    if rejected_required and target in {"in_progress", "result_ready"}:
        raise _error("creative_execution_output_replacement_required")
    if rejected_required and target == "blocked":
        reason = "needs_output_replacement"
    if target == "failed_before_dispatch" and _outputs(db, row):
        raise _error("creative_execution_predispatch_not_proven")
    _cas(db, row, expected, state=target, dispatch_certainty=certainty, safe_reason=reason,
        checkpoint_json=stored_checkpoint, recovery_json=recovery)
    return _projection(db, row, user)


def _writable(db: Session, row: CreativeExecution, *, output: bool = False) -> None:
    if row.state in TERMINAL:
        raise _error("creative_execution_terminal")
    if row.state == "unknown":
        raise _error("creative_execution_reconciliation_required")
    if not _has_claim(db, row):
        raise _error("creative_execution_checkpoint_requires_claim", 422)
    if output and row.state not in {"claimed", "in_progress", "blocked", "result_ready"}:
        raise _error("creative_execution_output_not_started")


def _input_snapshot(revision: MaterialRevision, package: CreativeExecutionPackage, *, size: int) -> dict:
    refs = [ref for ref in package.package_json["assets"] if ref["material_revision_id"] == revision.id]
    if not refs or any(ref["content_hash"] != revision.content_hash or ref["rights"] != refs[0]["rights"] for ref in refs):
        raise _error("creative_execution_input_not_in_package")
    return bounded_json({"material_revision_id": revision.id, "content_hash": revision.content_hash,
        "mime_type": revision.mime_type, "size_bytes": size, "rights": refs[0]["rights"],
        "package_hash": package.package_hash}, max_bytes=40_000)


@_atomic
def _reserve_inputs(db: Session, project_id: int, unit_id: int, execution_id: int, payload: dict, user: User) -> dict:
    _payload(payload, {"expected_revision", "material_revision_ids", "executor_kind", "executor_key", "executor_version"})
    row = _owned(db, project_id, unit_id, execution_id, user, mutate=True)
    expected = _expected(row, payload)
    _writable(db, row)
    _executor(payload, row)
    package = _package(db, row, user, current=True)
    revisions = {revision.id: revision for revision in check_inputs(db, package)}
    requested = payload.get("material_revision_ids", list(revisions))
    if not isinstance(requested, list) or len(requested) > MAX_INPUTS or len(revisions) > MAX_INPUTS:
        raise _error("creative_execution_input_count_invalid", 422)
    for revision_id in requested:
        _id(revision_id, name="input")
    if len(set(requested)) != len(requested) or set(requested) - revisions.keys():
        raise _error("creative_execution_input_not_in_package", 422)
    previous = row.materialized_inputs_json or []
    snapshots = {item["material_revision_id"]: item for item in previous}
    if set(requested) - snapshots.keys() and any(output.state == "accepted" for output in _outputs(db, row)):
        raise _error("creative_execution_input_boundary_frozen")
    total_bytes = sum(item["size_bytes"] for item in snapshots.values())
    if total_bytes > MAX_INPUT_BYTES:
        raise _error("creative_execution_input_bytes_exceeded", 413)
    for revision_id in requested:
        previous_size = snapshots[revision_id]["size_bytes"] if revision_id in snapshots else 0
        remaining = MAX_INPUT_BYTES - total_bytes + previous_size
        if remaining <= 0:
            raise _error("creative_execution_input_bytes_exceeded", 413)
        content = files.read_material(revisions[revision_id], maximum=min(MAX_FILE_BYTES, remaining))
        snapshot = _input_snapshot(revisions[revision_id], package, size=len(content))
        if revision_id in snapshots and snapshots[revision_id] != snapshot:
            raise _error("creative_execution_materialized_input_changed")
        total_bytes += len(content) - previous_size
        snapshots[revision_id] = snapshot
    if len(snapshots) > MAX_INPUTS or total_bytes > MAX_INPUT_BYTES:
        raise _error("creative_execution_input_bytes_exceeded", 413)
    manifest = [snapshots[key] for key in sorted(snapshots)]
    _cas(db, row, expected, materialized_inputs_json=manifest)
    result = _projection(db, row, user)
    result["files"] = [{"material_revision_id": revision_id,
        "relative_path": f"inputs/{revision_id}-{snapshots[revision_id]['content_hash']}.bin",
        "content_hash": snapshots[revision_id]["content_hash"], "size_bytes": snapshots[revision_id]["size_bytes"]}
        for revision_id in requested]
    return result


def materialize_inputs(db: Session, project_id: int, unit_id: int, execution_id: int, payload: dict, user: User) -> dict:
    # A crash after exposing bytes must never erase their derived-rights boundary.
    result = _reserve_inputs(db, project_id, unit_id, execution_id, payload, user)
    row = _owned(db, project_id, unit_id, execution_id, user, mutate=True)
    if row.revision_no != result["revision_no"]:
        raise _error("creative_execution_revision_conflict")
    _writable(db, row)
    package = _package(db, row, user, current=True)
    revisions = {revision.id: revision for revision in check_inputs(db, package)}
    snapshots = {item["material_revision_id"]: item for item in result["materialized_inputs"]}
    for target in result["files"]:
        revision_id = target["material_revision_id"]
        content = files.read_material(revisions[revision_id], maximum=target["size_bytes"])
        if _input_snapshot(revisions[revision_id], package, size=len(content)) != snapshots[revision_id]:
            raise _error("creative_execution_materialized_input_changed")
        files.write_file(user.id, row.id, target["relative_path"], content)
    if not result["files"]:
        with files.root_fd(user.id, row.id, create=True):
            pass
    result["work_root"] = str(files.work_root(user.id, row.id))
    return result


@_atomic
def submit_output(db: Session, project_id: int, unit_id: int, execution_id: int, payload: dict, user: User, *, uploaded_content: bytes | None = None) -> dict:
    _payload(payload, {"expected_revision", "executor_kind", "executor_key", "executor_version", "role_id", "kind",
        "output_index", "attempt_no", "relative_path", "mime_type", "content_hash", "metadata"})
    row = _owned(db, project_id, unit_id, execution_id, user, mutate=True)
    expected = _expected(row, payload)
    _writable(db, row, output=True)
    _executor(payload, row)
    package = _package(db, row, user, current=True)
    roles = {role["role_id"]: role for role in _roles(package)}
    role_id = payload.get("role_id")
    if not isinstance(role_id, str):
        raise _error("creative_execution_output_role_invalid", 422)
    role = roles.get(role_id)
    if role is None or payload.get("kind", role["kind"]) != role["kind"]:
        raise _error("creative_execution_output_role_invalid", 422)
    index = _id(payload.get("output_index"), name="output_index")
    if index > role["max_count"]:
        raise _error("creative_execution_output_count_exceeded", 422)
    outputs = _outputs(db, row)
    if len(outputs) >= MAX_OUTPUT_ROWS:
        raise _error("creative_execution_output_history_limit")
    previous = _latest(outputs).get((role["role_id"], index))
    if previous and previous.state != "rejected":
        raise _error("creative_execution_output_replacement_denied")
    attempt = previous.attempt_no + 1 if previous else 1
    if attempt > MAX_ATTEMPTS or ("attempt_no" in payload and (type(payload["attempt_no"]) is not int or payload["attempt_no"] != attempt)):
        raise _error("creative_execution_output_attempt_invalid", 422)
    mime = payload.get("mime_type")
    if mime not in role["allowed_mime"]:
        raise _error("creative_execution_output_mime_invalid", 422)
    metadata = _metadata(payload.get("metadata"))
    content = uploaded_content if uploaded_content is not None else files.read_file(user.id, row.id, payload.get("relative_path"), maximum=role["max_bytes"], output=True)
    if not 0 < len(content) <= role["max_bytes"]:
        raise _error("execution_file_size_invalid", 413)
    validate_execution_file(content, mime, role["kind"])
    digest = hashlib.sha256(content).hexdigest()
    if "content_hash" in payload and payload["content_hash"] != digest:
        raise _error("creative_execution_output_hash_mismatch")
    key = f"staging/{digest}.bin"
    files.write_file(user.id, row.id, key, content)
    output = CreativeExecutionOutput(execution_id=row.id, role_id=role["role_id"], kind=role["kind"],
        output_index=index, attempt_no=attempt, staging_key=key, mime_type=mime, content_hash=digest,
        size_bytes=len(content), metadata_json=metadata, state="staged", created_by=user.email)
    db.add(output)
    db.flush()
    outputs.append(output)
    ready, accepted = _completion(package, outputs)
    replacement_missing = _needs_replacement(package, outputs)
    target = "blocked" if replacement_missing else "accepted" if accepted else "result_ready" if ready else "in_progress"
    _cas(db, row, expected, state=target, safe_reason="needs_output_replacement" if replacement_missing else None,
        dispatch_certainty="confirmed_dispatched")
    return _projection(db, row, user)


def _live_materialized(db: Session, row: CreativeExecution, package: CreativeExecutionPackage) -> list[dict]:
    revisions = {revision.id: revision for revision in check_inputs(db, package)}
    snapshots = row.materialized_inputs_json or []
    if revisions and not snapshots:
        raise _error("creative_execution_inputs_not_materialized")
    if not isinstance(snapshots, list) or len(snapshots) > MAX_INPUTS:
        raise _error("creative_execution_materialized_input_invalid")
    if any(not isinstance(snapshot, dict) or type(snapshot.get("material_revision_id")) is not int
           or snapshot["material_revision_id"] < 1 or not isinstance(snapshot.get("content_hash"), str)
           or not _HASH.fullmatch(snapshot["content_hash"]) for snapshot in snapshots):
        raise _error("creative_execution_materialized_input_invalid")
    files.check_input_manifest(row.owner_user_id, row.id, {
        f"{snapshot['material_revision_id']}-{snapshot['content_hash']}.bin" for snapshot in snapshots
    })
    seen = set()
    for snapshot in snapshots:
        revision_id = snapshot.get("material_revision_id")
        if revision_id in seen or revision_id not in revisions:
            raise _error("creative_execution_input_not_in_package")
        seen.add(revision_id)
        content = files.read_material(revisions[revision_id])
        if snapshot != _input_snapshot(revisions[revision_id], package, size=len(content)):
            raise _error("creative_execution_materialized_input_changed")
        transported = files.read_file(row.owner_user_id, row.id, f"inputs/{revision_id}-{snapshot['content_hash']}.bin")
        if hashlib.sha256(transported).hexdigest() != snapshot["content_hash"] or len(transported) != snapshot["size_bytes"]:
            raise _error("creative_execution_materialized_input_changed")
    return snapshots


def _rights(payload: dict, snapshots: list[dict], output: CreativeExecutionOutput) -> dict:
    rights = payload.get("rights")
    fields = {"rights_status", "public_use_allowed", "model_use_allowed", "commercial_use_allowed", "attribution_text", "license"}
    if (not isinstance(rights, dict) or set(rights) - fields or not isinstance(rights.get("rights_status"), str)
            or rights["rights_status"] not in {"cleared", "restricted", "unknown"}):
        raise _error("creative_execution_rights_decision_required", 422)
    permissions = {}
    for key in ("public_use_allowed", "model_use_allowed", "commercial_use_allowed"):
        value = rights.get(key, False)
        if type(value) is not bool:
            raise _error("creative_execution_rights_invalid", 422)
        if value and (rights["rights_status"] != "cleared" or any(
            snapshot["rights"].get(key) is not True or snapshot["rights"].get("rights_status") != "cleared" for snapshot in snapshots
        )):
            raise _error("creative_execution_rights_escalation", 403)
        permissions[key] = value
    # Project documents remain private passive files, even when source media is public.
    if output.kind == "other" and output.mime_type not in EXECUTION_TEXT_MIME and any(permissions.values()):
        raise _error("creative_execution_project_file_rights_restricted", 403)
    attribution = rights.get("attribution_text")
    if attribution is not None and (not isinstance(attribution, str) or len(attribution) > 4000):
        raise _error("creative_execution_attribution_invalid", 422)
    if attribution:
        _metadata({"attribution": attribution})
    license_metadata = _metadata(rights.get("license"))
    if set(license_metadata) - {"license", "license_id", "license_url"}:
        raise _error("creative_execution_license_invalid", 422)
    for snapshot in snapshots:
        inherited_license = snapshot["rights"].get("license", {})
        if inherited_license and any(inherited_license.get(key) != value for key, value in license_metadata.items()):
            raise _error("creative_execution_license_conflict", 403)
    inherited_attribution = [snapshot["rights"].get("attribution_text") for snapshot in snapshots if snapshot["rights"].get("attribution_text")]
    attributions = list(dict.fromkeys(inherited_attribution + ([attribution] if attribution else [])))
    combined = "\n".join(attributions) or None
    bounded_json({"attribution": combined}, max_bytes=40_000)
    inherited = [{"material_revision_id": snapshot["material_revision_id"], "content_hash": snapshot["content_hash"],
        "rights": snapshot["rights"]} for snapshot in snapshots]
    return {"rights_status": rights["rights_status"], **permissions, "attribution_text": combined,
        "license": license_metadata, "inherited_inputs": inherited,
        "license_obligations": [{"material_revision_id": snapshot["material_revision_id"],
            "content_hash": snapshot["content_hash"], "license": snapshot["rights"].get("license", {})}
            for snapshot in snapshots if snapshot["rights"].get("license")]}


@_atomic
def decide_output(db: Session, project_id: int, unit_id: int, execution_id: int, output_id: int, payload: dict, user: User) -> dict:
    _payload(payload, {"expected_revision", "decision", "rights", "title", "attach_to_project"})
    row = _owned(db, project_id, unit_id, execution_id, user, mutate=True)
    expected = _expected(row, payload)
    if row.state != "accepted":
        _writable(db, row, output=True)
    outputs = _outputs(db, row)
    output = next((item for item in outputs if item.id == output_id), None)
    if output is None:
        raise _error("creative_execution_output_not_found", 404)
    if output.state != "staged" or _latest(outputs).get((output.role_id, output.output_index)) is not output:
        raise _error("creative_execution_output_already_decided")
    decision = payload.get("decision")
    if not isinstance(decision, str) or decision not in {"accept", "reject"}:
        raise _error("creative_execution_output_decision_invalid", 422)
    package = _package(db, row, user, current=decision == "accept")
    if row.state == "accepted" and package.package_json.get("manual_image") is not None:
        raise _error("creative_execution_terminal")
    _counts(package, outputs)
    if row.state == "accepted" and decision == "reject" and any(
        role["role_id"] == output.role_id and role["required"] for role in _roles(package)
    ):
        raise _error("creative_execution_terminal")
    if decision == "accept":
        snapshots = _live_materialized(db, row, package)
        rights = _rights(payload, snapshots, output)
        attach = payload.get("attach_to_project", False)
        if type(attach) is not bool:
            raise _error("creative_execution_attach_invalid", 422)
        title = payload.get("title", f"Execution {row.id} / {output.role_id} / {output.output_index}")
        if not isinstance(title, str) or not 1 <= len(title.strip()) <= 255:
            raise _error("creative_execution_title_invalid", 422)
        _metadata({"summary": title})
        content = files.read_file(user.id, row.id, output.staging_key)
        if hashlib.sha256(content).hexdigest() != output.content_hash or len(content) != output.size_bytes:
            raise _error("creative_execution_staged_output_changed")
        validate_execution_file(content, output.mime_type, output.kind)
        from .material_storage import LocalMaterialStorage, provider

        if not isinstance(provider(), LocalMaterialStorage):
            raise _error("creative_execution_local_storage_required")
        provenance = bounded_json({"execution_id": row.id, "output_id": output.id, "package_id": package.id,
            "package_hash": package.package_hash, "owner_user_id": user.id, "project_id": project_id, "content_unit_id": unit_id,
            "role_id": output.role_id, "output_index": output.output_index, "attempt_no": output.attempt_no,
            "executor_kind": row.executor_kind, "executor_key": row.executor_key, "executor_version": row.executor_version,
            "output_hash": output.content_hash, "input_manifest_hash": canonical_hash(snapshots),
            "result_metadata": _metadata(output.metadata_json), "inherited_inputs": rights["inherited_inputs"],
            **rights["license"], "license_obligations": rights["license_obligations"]}, max_bytes=1_000_000)
        if package.package_json.get("manual_image") is not None:
            manual_package = _manual_package(db, row, user)
            handoff = manual_package.package_json["manual_image"]
            _manual_image_bytes(content, output.mime_type, handoff["configuration"], handoff["max_bytes"])
            provenance["manual_image"] = {key: handoff[key] for key in ("schema", "origin", "runtime_verified", "configuration_hash", "prompt_hash")}
            provenance["manual_acceptance_hash"] = canonical_hash({key: value for key, value in payload.items() if key != "expected_revision"})
        material = create_material(db, kind=output.kind, title=title.strip(), created_by=user.email)
        try:
            revision = create_revision(db, material, content=content, suffix=".bin", declared_mime=output.mime_type,
                source_kind="external_execution", source_metadata=provenance,
                _execution_acceptance=_EXTERNAL_EXECUTION_ACCEPTANCE,
                rights_status=rights["rights_status"], public_use_allowed=rights["public_use_allowed"],
                model_use_allowed=rights["model_use_allowed"], commercial_use_allowed=rights["commercial_use_allowed"],
                attribution_text=rights["attribution_text"], metadata={"external_execution": provenance}, created_by=user.email)
        except (OSError, ValueError, RuntimeError):
            raise _error("creative_execution_material_storage_unavailable") from None
        if revision.content_hash != output.content_hash or revision.mime_type != output.mime_type:
            raise _error("creative_execution_accepted_output_mismatch")
        if files.read_material(revision) != content:
            raise _error("creative_execution_accepted_output_mismatch")
        if attach:
            db.add(ProjectMaterialReference(project_id=project_id, material_revision_id=revision.id,
                origin="external_execution", status="active", attached_by=user.email))
        output.material_revision_id = revision.id
        output.state = "accepted"
    else:
        output.state = "rejected"
    output.decided_by = user.email
    output.decided_at = utcnow()
    db.flush()
    if decision == "accept":
        package = _package(db, row, user, current=True)
        _live_materialized(db, row, package)
    ready, accepted = _completion(package, outputs)
    rejected_required = _needs_replacement(package, outputs)
    target = "blocked" if rejected_required else "accepted" if accepted else "result_ready" if ready else "in_progress"
    _cas(db, row, expected, state=target, safe_reason="needs_output_replacement" if rejected_required else None)
    return _projection(db, row, user)
