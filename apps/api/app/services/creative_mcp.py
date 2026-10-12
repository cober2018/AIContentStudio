"""Restricted MCP projections and delegation to the existing creative domain."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import threading
import unicodedata
from dataclasses import dataclass, field
from typing import Annotated, Literal
from urllib.parse import unquote

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from ..models import User
from . import capability_memory, channel_variants, content_masters, creative_executions, creative_packages
from .creative_contracts import bounded_json
from .project_brief import current_brief
from .project_evidence import current_boundary

PROTOCOL_VERSION = "2025-11-25"
MAX_REQUEST_BYTES = 256 * 1024
MAX_ARGUMENT_BYTES = 64 * 1024
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_DEPTH = 24
ID = Annotated[int, Field(ge=1, le=2**53 - 1)]
IDENTIFIER = r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$"
HASH = r"^[0-9a-f]{64}$"


class MCPError(Exception):
    def __init__(self, code: str, category: str, *, status: int = 400, rpc_code: int = -32600):
        self.code, self.category, self.status, self.rpc_code = code, category, status, rpc_code


@dataclass(frozen=True)
class Binding:
    owner_id: int
    fingerprint: str
    token: str = field(repr=False)


def authenticate(authorization: str | None) -> Binding:
    token = os.environ.get("AICS_CREATIVE_MCP_TOKEN", "")
    owner = os.environ.get("AICS_CREATIVE_MCP_OWNER_USER_ID", "")
    if (not re.fullmatch(r"[A-Za-z0-9._~+/-]{32,512}", token)
            or not re.fullmatch(r"[1-9][0-9]{0,15}", owner) or int(owner) > 2**53 - 1):
        raise MCPError("creative_mcp_not_configured", "unavailable", status=503, rpc_code=-32000)
    candidate = authorization[7:] if authorization and authorization.startswith("Bearer ") else ""
    # Hash both sides so compare_digest always compares fixed-length values.
    if not hmac.compare_digest(hashlib.sha256(candidate.encode()).digest(), hashlib.sha256(token.encode()).digest()):
        raise MCPError("creative_mcp_unauthorized", "unauthorized", status=401, rpc_code=-32000)
    fingerprint = hashlib.sha256(f"{owner}:{token}".encode()).hexdigest()
    return Binding(int(owner), fingerprint, token)


def resolve_owner(db: Session, binding: Binding) -> User:
    user = db.scalar(select(User).where(User.id == binding.owner_id).execution_options(populate_existing=True))
    if user is None or not user.is_active or user.role not in {"editor", "admin"}:
        raise MCPError("creative_mcp_owner_unavailable", "forbidden", status=403, rpc_code=-32000)
    return user


@dataclass
class Lifecycle:
    """One credential's process readiness; no transport sessions or business state."""

    fingerprint: str | None = None
    phase: int = 0
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def check(self, binding: Binding, method: str) -> None:
        with self.lock:
            if self.fingerprint != binding.fingerprint:
                self.fingerprint, self.phase = binding.fingerprint, 0
            if method == "initialize":
                self.phase = 1
            elif method == "notifications/initialized":
                if self.phase == 0:
                    raise MCPError("creative_mcp_initialize_required", "lifecycle", rpc_code=-32002)
                self.phase = 2
            elif method != "ping" and self.phase != 2:
                raise MCPError("creative_mcp_initialized_required", "lifecycle", rpc_code=-32002)


class Input(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")


class Scope(Input):
    project_id: ID
    unit_id: ID


class ContextInput(Scope):
    variant_key: str | None = Field(default=None, min_length=1, max_length=150, pattern=IDENTIFIER)


class PackageInput(Scope):
    package_id: ID


class ExecutionInput(Scope):
    execution_id: ID


class CapabilityDiscoveryInput(Scope):
    execution_id: ID | None = None
    kind: Literal["prompt_skill", "recipe", "creative_pattern", "preference", "execution_template", "tool"] | None = None
    q: str | None = Field(default=None, max_length=200)
    tag: str | None = Field(default=None, max_length=100)
    limit: int = Field(default=20, ge=1, le=50)
    offset: int = Field(default=0, ge=0, le=10000)


class CapabilityUseInput(Scope):
    execution_id: ID | None = None
    artifact_id: ID
    artifact_revision_id: ID
    arguments: dict = Field(default_factory=dict, max_length=30)


class MutationInput(ExecutionInput):
    expected_revision: ID
    executor_kind: str = Field(min_length=1, max_length=30, pattern=IDENTIFIER)
    executor_key: str = Field(min_length=1, max_length=150, pattern=IDENTIFIER)
    executor_version: str = Field(min_length=1, max_length=50, pattern=IDENTIFIER)


class ClaimInput(MutationInput):
    metadata: dict = Field(default_factory=dict, max_length=20)


class ReportInput(ClaimInput):
    dispatch_certainty: Literal["not_dispatched", "possibly_dispatched", "confirmed_dispatched"] | None = None
    safe_reason: Literal["executor_blocked", "input_unavailable", "validation_failed", "dispatch_uncertain",
                         "reconciliation_needed", "executor_failed"] | None = None


class CheckpointInput(MutationInput):
    checkpoint: dict = Field(max_length=20)


class MaterializeInput(MutationInput):
    material_revision_ids: list[ID] | None = Field(default=None, max_length=100)


class OutputInput(MutationInput):
    role_id: str = Field(min_length=1, max_length=100, pattern=IDENTIFIER)
    output_index: int = Field(ge=1, le=20)
    attempt_no: int | None = Field(default=None, ge=1, le=20)
    relative_path: str = Field(min_length=1, max_length=500,
                               pattern=r"^outputs/[A-Za-z0-9][A-Za-z0-9_.-]{0,149}$")
    mime_type: str = Field(min_length=3, max_length=100, pattern=r"^[a-z0-9.+-]+/[a-z0-9.+-]+$")
    content_hash: str | None = Field(default=None, pattern=HASH)
    metadata: dict = Field(default_factory=dict, max_length=20)


class ReconcileInput(MutationInput):
    observation_hash: str = Field(pattern=HASH)
    summary: str = Field(min_length=1, max_length=2000)
    resolution: Literal["in_progress", "blocked", "result_ready", "failed_before_dispatch"]
    dispatch_certainty: Literal["not_dispatched", "confirmed_dispatched"]
    recovery: dict | None = Field(default=None, max_length=20)


TOOLS = {
    "get_context": (ContextInput, "Read current owned unit context and content metadata.", True),
    "get_package": (PackageInput, "Read an exact frozen package, including its authorized input manifest.", True),
    "get_execution": (ExecutionInput, "Read exact execution state, contract, counts and staged output metadata.", True),
    "find_capabilities": (CapabilityDiscoveryInput, "Read every applicable saved/pinned method with exact scope/revision. Ordering is not automatic selection.", True),
    "use_capability": (CapabilityUseInput, "Explicitly render one exact applicable method and record its use; never execute code or change content.", False),
    "claim_execution": (ClaimInput, "Claim an already prepared current execution with its exact executor and CAS.", False),
    "start_execution": (ClaimInput, "Start a claimed current execution; possible dispatch cannot be auto-retried.", False),
    "materialize_inputs": (MaterializeInput, "Materialize only authorized exact package inputs into the private work root.", False),
    "report_progress": (ReportInput, "Record safe progress metadata through the existing transition/CAS service.", False),
    "report_blocker": (ReportInput, "Record a proven blocker; possible side effects require Unknown reconciliation.", False),
    "report_checkpoint": (CheckpointInput, "Record a bounded checkpoint through the shared execution transition.", False),
    "submit_output": (OutputInput, "Stage one output from outputs/<filename>; never accept or bind it to content.", False),
    "mark_unknown": (ReportInput, "Record dispatch uncertainty without resending or starting another execution.", False),
    "reconcile_unknown": (ReconcileInput, "Reconcile Unknown using an observation hash/summary and explicit certainty.", False),
    "request_human_review": (MutationInput, "Record a human-review request for result_ready; cannot accept outputs.", False),
}
_ACTIONS = {"claim_execution": "claim", "start_execution": "start", "report_progress": "progress",
            "report_blocker": "block", "report_checkpoint": "progress", "mark_unknown": "unknown",
            "reconcile_unknown": "reconcile", "request_human_review": "progress"}
_META_FIELDS = ("id", "project_id", "content_unit_id", "revision_no", "payload_schema", "payload_hash",
                "context_hash", "creative_intent", "creative_intent_hash", "modality", "channel_id",
                "content_form", "variant_key", "source_master_revision_id", "readiness")
_SAFE_CODES = {
    "creative_execution_revision_conflict", "creative_execution_executor_mismatch", "creative_execution_terminal",
    "creative_execution_reconciliation_required", "creative_execution_transition_denied",
    "creative_execution_idempotency_conflict", "creative_execution_not_found", "creative_package_not_found",
    "creative_source_not_current", "creative_package_stale", "creative_input_model_use_denied",
    "creative_input_rights_changed", "creative_execution_required_outputs_missing",
    "creative_execution_output_replacement_required", "creative_execution_output_hash_mismatch",
    "creative_execution_output_replacement_denied", "creative_execution_checkpoint_observation_required",
    "creative_execution_predispatch_not_proven", "execution_path_invalid", "execution_regular_file_required",
    "creative_execution_input_not_in_package", "creative_execution_rights_escalation",
    "creative_execution_checkpoint_binding_invalid", "creative_execution_checkpoint_requires_claim",
    "creative_execution_observation_required", "creative_execution_reconcile_certainty_required",
    "creative_execution_descriptor_conflict", "creative_execution_descriptor_requires_prepare",
    "creative_execution_descriptor_incomplete", "creative_execution_output_kinds_invalid",
    "creative_execution_checkpoint_unsupported", "creative_execution_recovery_unsupported",
    "creative_execution_recovery_observation_required", "creative_execution_recovery_checkpoint_mismatch",
    "creative_execution_recovery_action_invalid",
}
_CATEGORIES = {403: "forbidden", 404: "not_found", 409: "conflict", 413: "bounds", 422: "invalid_arguments"}


def dumps(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def safe_value(value: object, binding: Binding, *, maximum: int) -> object:
    pending = [value]
    seen = 0
    while pending:
        item = pending.pop()
        seen += 1
        if seen > 20_000:
            raise MCPError("creative_mcp_payload_bounds", "bounds")
        if isinstance(item, dict):
            pending.extend(item.keys())
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item)
        elif isinstance(item, str):
            if len(item) > 8192:
                # Bound strings before decoding or scanning credentials.
                raise MCPError("creative_mcp_string_bounds", "bounds")
            scanned = unicodedata.normalize("NFKC", item)
            for _ in range(MAX_DEPTH):
                if binding.token in scanned:
                    raise MCPError("creative_mcp_sensitive_payload", "redaction", rpc_code=-32602)
                decoded = unicodedata.normalize("NFKC", unquote(scanned))
                if decoded == scanned:
                    break
                scanned = decoded
            else:
                # Do not echo a value whose bounded credential scan is incomplete.
                raise MCPError("creative_mcp_encoding_bounds", "bounds", rpc_code=-32602)
    value = bounded_json(value, max_bytes=maximum)
    if binding.token in dumps(value):
        raise MCPError("creative_mcp_sensitive_payload", "redaction", rpc_code=-32602)
    return value


def tools_list() -> dict:
    return {"tools": [{"name": name, "description": description, "inputSchema": model.model_json_schema(),
                      "annotations": {"readOnlyHint": readonly, "destructiveHint": not readonly,
                                      "idempotentHint": readonly, "openWorldHint": False}}
                     for name, (model, description, readonly) in TOOLS.items()]}


def _context(db: Session, args: ContextInput, user: User) -> dict:
    project, unit = content_masters.owned_unit(db, args.project_id, args.unit_id, user)
    masters = content_masters.list_revisions(db, project.id, unit.id, user, limit=1)
    variant = channel_variants.current_revision(db, project.id, unit.id, args.variant_key, user) if args.variant_key else None
    brief = current_brief(db, project.id)
    boundary = current_boundary(db, project.id)
    pointers = content_masters._context(db, project, unit, content_form=masters[0]["content_form"] if masters else None)
    return {"project": {"id": project.id, "status": project.status},
            "unit": {"id": unit.id, "status": unit.status, "channel_id": unit.channel_id},
            "context": pointers,
            "brief": {"id": brief.id, "revision_no": brief.revision_no, "checksum": brief.checksum,
                      "objective": brief.objective, "primary_audience": brief.primary_audience,
                      "core_message": brief.core_message, "angle": brief.angle} if brief else None,
            "fact_boundary": {"id": boundary.id, "revision_no": boundary.revision_no,
                              "fact_pack_id": boundary.fact_pack_id, "fact_pack_version": boundary.fact_pack_version,
                              "checksum": boundary.fact_pack_checksum} if boundary else None,
            "master": {key: masters[0][key] for key in _META_FIELDS if key in masters[0]} if masters else None,
            "variant": {key: variant[key] for key in _META_FIELDS if key in variant} if variant else None}


def _execute(db: Session, name: str, args: Input, user: User) -> dict:
    if name == "get_context":
        return _context(db, args, user)
    if name == "get_package":
        return creative_packages.get_package(db, args.project_id, args.unit_id, args.package_id, user)
    if name == "get_execution":
        return creative_executions.get_execution(db, args.project_id, args.unit_id, args.execution_id, user)
    if name == "find_capabilities":
        return capability_memory.discover(db, user, args.model_dump(exclude_none=True))
    if name == "use_capability":
        return capability_memory.use_artifact(db, user, args.artifact_id,
            args.model_dump(exclude_none=True, exclude={"artifact_id"}))
    payload = args.model_dump(exclude_none=True, exclude={"project_id", "unit_id", "execution_id"})
    if name in _ACTIONS:
        payload["action"] = _ACTIONS[name]
        if name == "request_human_review":
            current = creative_executions.get_execution(db, args.project_id, args.unit_id, args.execution_id, user)
            if current["state"] != "result_ready":
                raise MCPError("creative_mcp_result_not_ready", "conflict", status=409)
            payload["metadata"] = {"summary": "Human review requested"}
        return creative_executions.transition_execution(db, args.project_id, args.unit_id, args.execution_id, payload, user)
    if name == "materialize_inputs":
        return creative_executions.materialize_inputs(db, args.project_id, args.unit_id, args.execution_id, payload, user)
    if name == "submit_output":
        return creative_executions.submit_output(db, args.project_id, args.unit_id, args.execution_id, payload, user)
    raise MCPError("creative_mcp_unknown_tool", "invalid_arguments", rpc_code=-32602)


def error_data(code: str, category: str, trace_id: str, **extra) -> dict:
    return {"code": code, "category": category, "trace_id": trace_id, **extra}


def domain_error(exc: HTTPException, trace_id: str) -> dict:
    category = _CATEGORIES.get(exc.status_code, "unavailable")
    code = exc.detail.get("code") if isinstance(exc.detail, dict) else None
    return error_data(code if code in _SAFE_CODES else f"creative_domain_{category}", category, trace_id,
                      status=exc.status_code if exc.status_code in _CATEGORIES else 503)


def tool_result(data: dict, *, failed: bool = False) -> dict:
    return {"content": [{"type": "text", "text": dumps(data)}], "structuredContent": data, "isError": failed}


def call_tool(db: Session, user: User, binding: Binding, params: dict, trace_id: str) -> dict:
    if set(params) - {"name", "arguments", "_meta"} or not isinstance(params.get("name"), str):
        raise MCPError("creative_mcp_call_invalid", "invalid_arguments", rpc_code=-32602)
    name = params["name"]
    if name not in TOOLS:
        raise MCPError("creative_mcp_unknown_tool", "invalid_arguments", rpc_code=-32602)
    mutated = False
    try:
        raw = safe_value(params.get("arguments", {}), binding, maximum=MAX_ARGUMENT_BYTES)
        args = TOOLS[name][0].model_validate(raw)
        mutated = not TOOLS[name][2]
        data = _execute(db, name, args, user)
        data = safe_value(data, binding, maximum=MAX_RESPONSE_BYTES // 2 - 4096)
        result = tool_result(data)
        if len(dumps(result).encode()) > MAX_RESPONSE_BYTES - 4096:
            raise MCPError("creative_mcp_response_too_large", "bounds")
        result["_meta"] = {"aics/trace_id": trace_id}
        return result
    except ValidationError:
        data = error_data("creative_mcp_arguments_invalid", "invalid_arguments", trace_id, status=422)
    except HTTPException as exc:
        data = domain_error(exc, trace_id)
    except MCPError as exc:
        data = error_data(exc.code, exc.category, trace_id, status=exc.status)
        if exc.code == "creative_capability_unavailable":
            data["required_phase"] = 10
    except Exception:  # noqa: BLE001 MCP must never serialize an internal exception or its inputs.
        data = error_data("creative_mcp_internal_error", "internal", trace_id, status=500)
    db.rollback()
    if mutated:
        data["read_capability_use_before_retry" if name == "use_capability" else "read_execution_before_retry"] = True
    return tool_result(data, failed=True)


RESOURCE_TEMPLATES = {
    "context": ("get_context", "aics://projects/{project_id}/units/{unit_id}/context"),
    "package": ("get_package", "aics://projects/{project_id}/units/{unit_id}/packages/{package_id}"),
    "execution": ("get_execution", "aics://projects/{project_id}/units/{unit_id}/executions/{execution_id}"),
    "capabilities": ("find_capabilities", "aics://projects/{project_id}/units/{unit_id}/capabilities"),
}
STATUS_URI = "aics://creative-mcp/status"


def resources_list() -> dict:
    return {"resources": [{"uri": STATUS_URI, "name": "Creative MCP availability", "mimeType": "application/json"}]}


def resource_templates_list() -> dict:
    return {"resourceTemplates": [{"uriTemplate": uri, "name": name, "mimeType": "application/json"}
                                  for name, (_, uri) in RESOURCE_TEMPLATES.items()]}


def read_resource(db: Session, user: User, binding: Binding, params: dict, trace_id: str) -> dict:
    if set(params) - {"uri", "_meta"} or not isinstance(params.get("uri"), str) or len(params["uri"]) > 500:
        raise MCPError("creative_mcp_resource_invalid", "invalid_arguments", rpc_code=-32602)
    uri = params["uri"]
    if uri == STATUS_URI:
        available = all(inspect(db.get_bind()).has_table(table) for table in (
            "capability_artifact", "capability_artifact_revision", "capability_use"))
        data = {"protocol_version": PROTOCOL_VERSION, "transport_sessions": False,
                "capability_memory": {"available": available, "execution": False,
                    "explicit_selection_required": True,
                    "code": None if available else "capability_memory_unavailable"}}
    else:
        match = re.fullmatch(r"aics://projects/([1-9][0-9]{0,15})/units/([1-9][0-9]{0,15})/"
                             r"(context|capabilities|packages/([1-9][0-9]{0,15})|executions/([1-9][0-9]{0,15}))", uri)
        if match is None:
            raise MCPError("creative_mcp_resource_not_found", "not_found", rpc_code=-32002)
        project, unit, kind, package, execution = match.groups()
        values = {"project_id": int(project), "unit_id": int(unit)}
        resource = "package" if package else "execution" if execution else kind
        if package:
            values["package_id"] = int(package)
        if execution:
            values["execution_id"] = int(execution)
        name = RESOURCE_TEMPLATES[resource][0]
        try:
            args = TOOLS[name][0].model_validate(values)
        except ValidationError:
            raise MCPError("creative_mcp_resource_invalid", "invalid_arguments", rpc_code=-32602) from None
        data = _execute(db, name, args, user)
    data = safe_value(data, binding, maximum=MAX_RESPONSE_BYTES // 2 - 4096)
    return {"contents": [{"uri": uri, "mimeType": "application/json", "text": dumps(data)}],
            "_meta": {"aics/trace_id": trace_id}}
