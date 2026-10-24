"""Bounded JSON Streamable HTTP; no SSE, proxy identity, or transport sessions."""

from __future__ import annotations

import asyncio
import ipaddress
import json
import re
import uuid

from fastapi import APIRouter, Depends, Request, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..db import get_db
from ..services import creative_mcp as service

router = APIRouter(tags=["creative-mcp"])
_AUTHORITY = re.compile(r"(localhost|127\.0\.0\.1|\[::1\]):([1-9][0-9]{0,4})\Z")
_SINGLE_HEADERS = ("host", "origin", "authorization", "mcp-protocol-version", "content-type", "content-length", "accept")


def _error(error: service.MCPError, trace_id: str, request_id=None) -> dict:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": error.rpc_code,
            "message": error.category, "data": service.error_data(error.code, error.category, trace_id)}}


def _authority(value: str, ports: set[int]) -> bool:
    match = _AUTHORITY.fullmatch(value)
    return bool(match and 1 <= int(match[2]) <= 65535 and int(match[2]) in ports)


def _guard(request: Request) -> service.Binding:
    try:
        loopback = request.client is not None and ipaddress.ip_address(request.client.host).is_loopback
    except ValueError:
        loopback = False
    if not loopback:
        raise service.MCPError("creative_mcp_loopback_required", "forbidden", status=403)
    if sum(len(key) + len(value) for key, value in request.scope["headers"]) > 8192:
        raise service.MCPError("creative_mcp_header_bounds", "bounds", status=431)
    if (any(len(request.headers.getlist(key)) > 1 for key in _SINGLE_HEADERS)
            or any(key == "forwarded" or key.startswith("x-forwarded-") or key == "x-real-ip" for key in request.headers)):
        raise service.MCPError("creative_mcp_headers_invalid", "forbidden", status=403)
    server = request.scope.get("server")
    port = server[1] if server else None
    if type(port) is not int or not _authority(request.headers.get("host", ""), {port}):
        raise service.MCPError("creative_mcp_host_invalid", "forbidden", status=403)
    origin = request.headers.get("origin")
    if origin is not None:
        match = re.fullmatch(r"https?://([^/\s?#]+)", origin)
        if not match or not _authority(match[1], {port, 5173}):
            raise service.MCPError("creative_mcp_origin_invalid", "forbidden", status=403)
    return service.authenticate(request.headers.get("authorization"))


def _pairs(items: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def _constant(_value: str):
    raise ValueError("non_finite_json")


def _parse(raw: bytes, binding: service.Binding) -> dict:
    try:
        text = raw.decode("utf-8")
        depth, quoted, escaped = 0, False, False
        for char in text:
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
            elif char == '"':
                quoted = True
            elif char in "[{":
                depth += 1
                if depth > service.MAX_DEPTH:
                    raise service.MCPError("creative_mcp_depth_bounds", "bounds")
            elif char in "]}":
                depth -= 1
        value = json.loads(text, object_pairs_hook=_pairs, parse_constant=_constant)
    except (ValueError, UnicodeError, RecursionError):
        raise service.MCPError("creative_mcp_parse_error", "parse_error", rpc_code=-32700) from None
    if (not isinstance(value, dict) or set(value) - {"jsonrpc", "id", "method", "params"}
            or value.get("jsonrpc") != "2.0" or not isinstance(value.get("method"), str)
            or not 1 <= len(value["method"]) <= 80 or not isinstance(value.get("params", {}), dict)):
        raise service.MCPError("creative_mcp_request_invalid", "invalid_request")
    request_id = value.get("id")
    if "id" in value and not (type(request_id) is int and abs(request_id) < 2**53
                              or isinstance(request_id, str) and re.fullmatch(r"[\x21-\x7e]{1,100}", request_id)):
        raise service.MCPError("creative_mcp_id_invalid", "invalid_request")
    try:
        return service.safe_value(value, binding, maximum=service.MAX_REQUEST_BYTES)
    except service.HTTPException:
        raise service.MCPError("creative_mcp_payload_invalid", "invalid_request") from None


async def _body(request: Request) -> bytes:
    media_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if media_type != "application/json":
        raise service.MCPError("creative_mcp_content_type_invalid", "transport", status=415)
    accepted = {piece.split(";", 1)[0].strip().lower() for piece in request.headers.get("accept", "").split(",")
                if not re.search(r";\s*q=0(?:\.0*)?(?:\s*;|$)", piece)}
    if not {"application/json", "text/event-stream"} <= accepted:
        raise service.MCPError("creative_mcp_accept_invalid", "transport", status=406)
    length = request.headers.get("content-length")
    if length is not None and (not re.fullmatch(r"[0-9]{1,9}", length) or int(length) > service.MAX_REQUEST_BYTES):
        raise service.MCPError("creative_mcp_body_bounds", "bounds", status=413)
    chunks, size = [], 0
    try:
        async with asyncio.timeout(10):
            async for chunk in request.stream():
                size += len(chunk)
                if size > service.MAX_REQUEST_BYTES:
                    raise service.MCPError("creative_mcp_body_bounds", "bounds", status=413)
                chunks.append(chunk)
    except TimeoutError:
        raise service.MCPError("creative_mcp_body_timeout", "transport", status=408) from None
    if length is not None and int(length) != size:
        raise service.MCPError("creative_mcp_body_invalid", "transport")
    return b"".join(chunks)


def _params(params: dict, allowed: set[str]) -> None:
    if set(params) - allowed - {"_meta"}:
        raise service.MCPError("creative_mcp_params_invalid", "invalid_arguments", rpc_code=-32602)


def _dispatch(request: Request, db: Session, binding: service.Binding, message: dict, trace_id: str):
    user = service.resolve_owner(db, binding)
    method, params = message["method"], message.get("params", {})
    version = request.headers.get("mcp-protocol-version")
    if version not in {None, service.PROTOCOL_VERSION} or (version is None and method not in {"initialize", "ping"}):
        raise service.MCPError("creative_mcp_protocol_unsupported", "protocol", rpc_code=-32602)
    notification = "id" not in message
    if notification:
        if method not in {"notifications/initialized", "notifications/cancelled"}:
            raise service.MCPError("creative_mcp_notification_invalid", "invalid_request")
        _params(params, set() if method == "notifications/initialized" else {"requestId", "reason"})
        if method == "notifications/cancelled":
            cancelled_id, reason = params.get("requestId"), params.get("reason")
            if (not (type(cancelled_id) is int and abs(cancelled_id) < 2**53
                     or isinstance(cancelled_id, str) and re.fullmatch(r"[\x21-\x7e]{1,100}", cancelled_id))
                    or reason is not None and (not isinstance(reason, str) or len(reason) > 1000)):
                raise service.MCPError("creative_mcp_notification_invalid", "invalid_request")
    elif method.startswith("notifications/"):
        raise service.MCPError("creative_mcp_notification_invalid", "invalid_request")
    if method == "initialize":
        _params(params, {"protocolVersion", "capabilities", "clientInfo"})
        client = params.get("clientInfo")
        if (not isinstance(params.get("protocolVersion"), str)
                or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", params["protocolVersion"])
                or not isinstance(params.get("capabilities"), dict) or not isinstance(client, dict)
                or any(not isinstance(client.get(key), str) or not 1 <= len(client[key]) <= 150 for key in ("name", "version"))):
            raise service.MCPError("creative_mcp_initialize_invalid", "invalid_arguments", rpc_code=-32602)
    request.app.state.creative_mcp_lifecycle.check(binding, method)
    if notification:
        return None
    if method == "initialize":
        return {"protocolVersion": service.PROTOCOL_VERSION, "serverInfo": {"name": "aics-creative", "version": "1.0"},
                "capabilities": {"tools": {"listChanged": False}, "resources": {"subscribe": False, "listChanged": False}},
                "instructions": ("Use prepared executions only. Results require human acceptance and a separate content save. "
                                 "Production stages: get_stages -> preview_stage -> run_stage -> send the user review_url -> "
                                 "get_stage_decision (wait_seconds<=25, call again while waiting_for_you) -> continue only on accepted; "
                                 "on rejected or rerun_requested use the note. Footage: start_material_match -> review_url -> get_material_match. "
                                 "Never accept, reject, bind or publish for the user, and never use the REST API to do so.")}
    if method == "ping":
        _params(params, set())
        return {}
    if method in {"tools/list", "resources/list", "resources/templates/list"}:
        _params(params, {"cursor"})
        if params.get("cursor") is not None:
            raise service.MCPError("creative_mcp_cursor_invalid", "invalid_arguments", rpc_code=-32602)
        return {"tools/list": service.tools_list, "resources/list": service.resources_list,
                "resources/templates/list": service.resource_templates_list}[method]()
    if method == "tools/call":
        return service.call_tool(db, user, binding, params, trace_id)
    if method == "resources/read":
        return service.read_resource(db, user, binding, params, trace_id)
    raise service.MCPError("creative_mcp_method_not_found", "method_not_found", rpc_code=-32601)


@router.api_route("/api/v1/creative-mcp", methods=["POST", "GET", "DELETE", "HEAD", "OPTIONS"])
async def creative_mcp(request: Request, db: Session = Depends(get_db)) -> Response:
    trace_id, request_id = uuid.uuid4().hex, None
    headers = {"X-Creative-MCP-Trace": trace_id, "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"}
    try:
        binding = _guard(request)
        if request.method != "POST":
            headers["Allow"] = "POST"
            raise service.MCPError("creative_mcp_method_not_allowed", "transport", status=405)
        message = await run_in_threadpool(_parse, await _body(request), binding)
        request_id = message.get("id")
        if not hasattr(request.app.state, "creative_mcp_lifecycle"):
            request.app.state.creative_mcp_lifecycle = service.Lifecycle()
        result = await run_in_threadpool(_dispatch, request, db, binding, message, trace_id)
        if result is None:
            return Response(status_code=202, headers=headers)
        response = {"jsonrpc": "2.0", "id": request_id, "result": result}
        if len(service.dumps(response).encode()) > service.MAX_RESPONSE_BYTES:
            raise service.MCPError("creative_mcp_response_too_large", "bounds", status=500, rpc_code=-32000)
        return JSONResponse(response, headers=headers)
    except service.MCPError as exc:
        status = exc.status if request_id is None or exc.category in {"protocol", "forbidden", "unavailable"} else 200
        if exc.status == 401:
            headers["WWW-Authenticate"] = 'Bearer realm="aics-creative-mcp"'
        return JSONResponse(_error(exc, trace_id, request_id), status_code=status, headers=headers)
    except service.HTTPException as exc:
        data = service.domain_error(exc, trace_id)
        error = service.MCPError(data["code"], data["category"], status=data["status"], rpc_code=-32000)
        return JSONResponse(_error(error, trace_id, request_id), status_code=200 if request_id is not None else error.status, headers=headers)
    except Exception:  # noqa: BLE001 The transport boundary returns only a fixed safe error.
        error = service.MCPError("creative_mcp_internal_error", "internal", status=500, rpc_code=-32603)
        return JSONResponse(_error(error, trace_id, request_id), status_code=500, headers=headers)
