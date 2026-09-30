"""External Connector API（EPIC-18）。"""

import re
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_admin, require_editor
from ..models import AuditLog, CapabilityRegistration, CapabilityVerification, Connector, ConnectorEndpoint, Fact, User
from ..services import connector_service, data_source_plugins
from ..services.capability_integrations import append_verification, endpoint_config_fingerprint
from ..services.connector_service import ConnectorError
from ..services.url_fetch import UnsafeUrlError
from . import CapabilityInputRoute

router = APIRouter(prefix="/api/v1", tags=["connectors"], route_class=CapabilityInputRoute)

AUTH_STYLES = {"bearer", "header", "none"}


class ConnectorIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    base_url: str = Field(min_length=1, max_length=500)
    connector_type: str = "generic_rest"
    auth_style: str = "bearer"
    api_key_env: str | None = None
    auth_header_name: str | None = None
    default_headers: dict[str, str] | None = None
    is_active: bool = True


class EndpointIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    path: str = Field(min_length=1, max_length=500)
    method: str = "GET"
    body_template: dict | None = None
    params: dict[str, Any] | None = None  # 值支持 bool/int（local_git）与字符串（query 参数）
    title_template: str = Field(min_length=1, max_length=300)
    as_of_path: str | None = None
    trust_level: float = 0.9
    fact_mapping: dict
    pagination: dict | None = None
    interval_minutes: int | None = Field(default=None, ge=0, le=10080)


class DataSourceCapabilityIn(BaseModel):
    key: str = Field(min_length=1, max_length=150)
    version: str = Field(min_length=1, max_length=50)
    plugin_key: str
    endpoint_id: int = Field(ge=1)


def _validate_connector(payload: ConnectorIn) -> None:
    if payload.connector_type == "local_git":
        # 本地文档数据源：base_url 是仓库目录（绝对路径或 file://）
        if not payload.base_url.startswith(("file://", "/")):
            raise HTTPException(400, "local_git 的 base_url 必须是本地目录绝对路径或 file:// 开头")
    elif not payload.base_url.startswith(("http://", "https://")):
        raise HTTPException(400, "base_url 必须以 http/https 开头")
    if payload.auth_style not in AUTH_STYLES:
        raise HTTPException(400, f"auth_style 只允许 {sorted(AUTH_STYLES)}")
    if payload.auth_style == "header" and not payload.auth_header_name:
        raise HTTPException(400, "auth_style=header 需要提供 auth_header_name")
    if payload.auth_style != "none" and not payload.api_key_env:
        raise HTTPException(400, "需要 api_key_env（鉴权凭据的环境变量名，值不落库）")


def _serialize_connector(c: Connector) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "connector_type": c.connector_type,
        "base_url": c.base_url,
        "api_key_env": c.api_key_env,
        "auth_style": c.auth_style,
        "auth_header_name": c.auth_header_name,
        "default_headers": c.default_headers_json or {},
        "is_active": c.is_active,
        "endpoint_count": len(c.endpoints) if c.endpoints else 0,
        "endpoints": [
            {"id": e.id, "name": e.name, "path": e.path}
            for e in (c.endpoints or [])
        ],
        "created_by": c.created_by,
    }


def _serialize_endpoint(e: ConnectorEndpoint) -> dict:
    return {
        "id": e.id,
        "connector_id": e.connector_id,
        "name": e.name,
        "path": e.path,
        "method": e.method,
        "body_template": e.body_template_json or {},
        "params": e.params_json or {},
        "title_template": e.title_template,
        "as_of_path": e.as_of_path,
        "trust_level": e.trust_level,
        "fact_mapping": e.fact_mapping_json or {},
        "pagination": e.pagination_json or {},
        "interval_minutes": e.interval_minutes,
        "last_pull_at": e.last_pull_at.isoformat() if e.last_pull_at else None,
        "last_pull_status": e.last_pull_status,
        "last_pull_error": e.last_pull_error,
    }


@router.post("/connectors", status_code=201)
def create_connector(payload: ConnectorIn, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    _validate_connector(payload)
    connector = Connector(
        name=payload.name,
        connector_type=payload.connector_type,
        base_url=payload.base_url.rstrip("/"),
        api_key_env=payload.api_key_env,
        auth_style=payload.auth_style,
        auth_header_name=payload.auth_header_name,
        default_headers_json=payload.default_headers,
        is_active=payload.is_active,
        created_by=user.email,
    )
    db.add(connector)
    db.commit()
    return _serialize_connector(connector)


@router.get("/connectors")
def list_connectors(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    connectors = list(db.scalars(select(Connector).order_by(Connector.id.desc())))
    return [_serialize_connector(c) for c in connectors]


@router.get("/connectors/{connector_id}")
def get_connector(connector_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    connector = db.get(Connector, connector_id)
    if not connector:
        raise HTTPException(404, "Connector 不存在")
    data = _serialize_connector(connector)
    data["endpoints"] = [_serialize_endpoint(e) for e in connector.endpoints]
    return data


@router.patch("/connectors/{connector_id}")
def update_connector(
    connector_id: int,
    payload: ConnectorIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    connector = db.get(Connector, connector_id)
    if not connector:
        raise HTTPException(404, "Connector 不存在")
    _validate_connector(payload)
    connector.name = payload.name
    connector.connector_type = payload.connector_type
    connector.base_url = payload.base_url.rstrip("/")
    connector.api_key_env = payload.api_key_env
    connector.auth_style = payload.auth_style
    connector.auth_header_name = payload.auth_header_name
    connector.default_headers_json = payload.default_headers
    connector.is_active = payload.is_active
    db.commit()
    return _serialize_connector(connector)


@router.delete("/connectors/{connector_id}", status_code=204)
def delete_connector(connector_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    connector = db.get(Connector, connector_id)
    if not connector:
        raise HTTPException(404, "Connector 不存在")
    db.delete(connector)
    db.commit()


@router.post("/connectors/{connector_id}/endpoints", status_code=201)
def create_endpoint(
    connector_id: int,
    payload: EndpointIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    connector = db.get(Connector, connector_id)
    if not connector:
        raise HTTPException(404, "Connector 不存在")
    mapping = payload.fact_mapping or {}
    is_v1 = "statement" in mapping and "value" in mapping.get("fields", {})
    is_v2 = bool(mapping.get("stages"))
    if not is_v1 and not is_v2:
        raise HTTPException(
            400,
            "fact_mapping 需要 v1（statement 模板 + fields.value 字段引用）或 v2（非空 stages 列表）协议之一",
        )
    if payload.method.upper() not in {"GET", "POST"}:
        raise HTTPException(400, "method 只允许 GET/POST")
    if payload.method.upper() == "POST" and not payload.body_template:
        raise HTTPException(400, "POST 请求需要提供 body_template")
    p_type = (payload.pagination or {}).get("type")
    if p_type not in {None, "page", "cursor", "offset"}:
        raise HTTPException(400, "pagination.type 只允许 page/cursor/offset")
    endpoint = ConnectorEndpoint(
        connector_id=connector.id,
        name=payload.name,
        path=payload.path,
        method=payload.method.upper(),
        body_template_json=payload.body_template,
        params_json=payload.params,
        title_template=payload.title_template,
        as_of_path=payload.as_of_path,
        trust_level=payload.trust_level,
        fact_mapping_json=payload.fact_mapping,
        pagination_json=payload.pagination,
        interval_minutes=payload.interval_minutes,
    )
    db.add(endpoint)
    db.commit()
    return _serialize_endpoint(endpoint)


@router.patch("/endpoints/{endpoint_id}")
def update_endpoint(
    endpoint_id: int,
    payload: EndpointIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    """编辑端点（补缺口 #13）：可改路径/参数/映射/周期等，interval_minutes=0 表示仅手动拉取。"""
    endpoint = db.get(ConnectorEndpoint, endpoint_id)
    if not endpoint:
        raise HTTPException(404, "端点不存在")
    endpoint.name = payload.name
    endpoint.path = payload.path
    endpoint.method = payload.method
    endpoint.body_template_json = payload.body_template
    endpoint.params_json = payload.params
    endpoint.title_template = payload.title_template
    endpoint.as_of_path = payload.as_of_path
    endpoint.trust_level = payload.trust_level
    endpoint.fact_mapping_json = payload.fact_mapping
    endpoint.pagination_json = payload.pagination
    endpoint.interval_minutes = payload.interval_minutes or None
    db.commit()
    return _serialize_endpoint(endpoint)


@router.delete("/endpoints/{endpoint_id}", status_code=204)
def delete_endpoint(endpoint_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    endpoint = db.get(ConnectorEndpoint, endpoint_id)
    if not endpoint:
        raise HTTPException(404, "Endpoint 不存在")
    db.delete(endpoint)
    db.commit()


@router.post("/endpoints/{endpoint_id}/pull")
def pull(endpoint_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    """立即拉取一次：外部 API → SourceDocument + 候选 Fact（去 Sources 页确认）。"""
    endpoint = db.get(ConnectorEndpoint, endpoint_id)
    if not endpoint:
        raise HTTPException(404, "Endpoint 不存在")
    try:
        doc, count, created = connector_service.pull_endpoint(db, endpoint, user)
    except ConnectorError as exc:
        connector_service.record_pull_failure(db, endpoint, str(exc), actor=user.email)
        raise HTTPException(400, connector_service.safe_pull_failure_code(exc)) from exc
    except UnsafeUrlError as exc:
        connector_service.record_pull_failure(db, endpoint, str(exc), actor=user.email)
        raise HTTPException(400, "目标被安全策略拒绝") from exc
    except Exception as exc:
        connector_service.record_pull_failure(db, endpoint, str(exc), actor=user.email)
        raise HTTPException(502, "连接器拉取失败") from exc
    return {
        "unchanged": not created,
        "source_id": doc.id,
        "source_title": doc.title,
        "facts": count,
        "endpoint": _serialize_endpoint(endpoint),
    }


@router.post("/data-source-capabilities/{registration_id}/pull")
def pull_verified_data_capability(
    registration_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_editor),
):
    registration = db.get(CapabilityRegistration, registration_id)
    if registration is None or registration.kind != "data_connector":
        raise HTTPException(404, "Data Source capability 不存在")
    try:
        endpoint = data_source_plugins.verified_data_endpoint(db, registration, "api")
    except (ValueError, TypeError) as exc:
        raise HTTPException(409, "data_source_capability_unavailable") from exc
    try:
        source, facts, created = connector_service.pull_endpoint(db, endpoint, user, dedup_mode="mapped_facts", bounded=True)
    except Exception as exc:  # noqa: BLE001 第三方响应/异常不可信，只回显固定错误码。
        connector_service.record_pull_failure(db, endpoint, exc, actor=user.email)
        raise HTTPException(502, "connector_pull_failed") from None
    db.expire_all()
    try:
        data_source_plugins.verified_data_endpoint(db, registration, "api")
    except (ValueError, TypeError) as exc:
        raise HTTPException(409, "data_source_capability_changed") from exc
    return {"source_id": source.id, "facts": facts, "unchanged": not created,
            "registration_id": registration.id, "registration_version": registration.version}


@router.post("/data-source-capabilities", status_code=201)
def create_data_source_capability(
    payload: DataSourceCapabilityIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    if (payload.plugin_key != "api" or not re.fullmatch(r"[1-9][0-9]{0,49}", payload.version)
            or not re.fullmatch(r"[A-Za-z0-9_.-]+", payload.key)):
        raise HTTPException(422, "data_source_capability_unsupported")
    endpoint = db.get(ConnectorEndpoint, payload.endpoint_id)
    fingerprint = endpoint_config_fingerprint(endpoint) if endpoint else None
    if fingerprint is None:
        raise HTTPException(409, "data_source_endpoint_unavailable")
    existing = db.scalar(select(CapabilityRegistration).where(
        CapabilityRegistration.kind == "data_connector", CapabilityRegistration.key == payload.key,
        CapabilityRegistration.version == payload.version,
    ))
    if existing is not None:
        raise HTTPException(409, "data_source_capability_exists")
    registration = CapabilityRegistration(
        kind="data_connector", key=payload.key, version=payload.version, status="configured",
        config_fingerprint=fingerprint, data_source_plugin_key=payload.plugin_key,
        endpoint_id=endpoint.id, created_by=user.email,
    )
    db.add(registration)
    try:
        db.flush()
        db.add(AuditLog(event="data_source_capability.configured", actor=user.email,
                        entity_type="capability_registration", entity_id=str(registration.id),
                        detail_json={"key": registration.key, "version": registration.version,
                                     "endpoint_id": endpoint.id}))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "data_source_capability_exists") from exc
    return {"id": registration.id, "key": registration.key, "version": registration.version,
            "plugin_key": registration.data_source_plugin_key, "endpoint_id": endpoint.id, "verified": False}


@router.get("/data-source-capabilities")
def list_data_source_capabilities(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    registrations = db.scalars(select(CapabilityRegistration).where(
        CapabilityRegistration.kind == "data_connector",
    ).order_by(CapabilityRegistration.id.desc()).limit(100)).all()
    result = []
    for registration in registrations:
        executable = False
        try:
            data_source_plugins.verified_data_endpoint(db, registration, registration.data_source_plugin_key or "")
            executable = True
        except (ValueError, TypeError):
            pass
        last = db.scalar(select(CapabilityVerification).where(
            CapabilityVerification.registration_id == registration.id,
            CapabilityVerification.scope_kind == "data_source_endpoint",
        ).order_by(CapabilityVerification.id.desc()).limit(1))
        result.append({
            "id": registration.id, "key": registration.key, "version": registration.version,
            "plugin_key": registration.data_source_plugin_key,
            "endpoint_id": registration.endpoint_id,
            "source_ref": f"capability:{registration.id}@{registration.version}",
            "configured": registration.status == "configured",
            "executable": executable, "verified": executable,
            "last_verification": {"result": last.result, "verified_at": last.verified_at.isoformat(),
                                  "expires_at": last.expires_at.isoformat() if last.expires_at else None} if last else None,
        })
    return result


@router.post("/data-source-capabilities/{registration_id}/probe")
def probe_data_source_capability(
    registration_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    registration = db.get(CapabilityRegistration, registration_id)
    if registration is None or registration.kind != "data_connector":
        raise HTTPException(404, "Data Source capability 不存在")
    try:
        endpoint = data_source_plugins.configured_data_endpoint(db, registration, "api")
    except (ValueError, TypeError) as exc:
        raise HTTPException(409, "data_source_capability_unavailable") from exc
    try:
        source, _facts, _created = connector_service.pull_endpoint(db, endpoint, user, dedup_mode="mapped_facts", bounded=True)
    except Exception as exc:  # noqa: BLE001 不回传远端异常原文。
        connector_service.record_pull_failure(db, endpoint, exc, actor=user.email)
        append_verification(db, registration, scope_kind="data_source_endpoint", scope={
            "plugin_key": "api", "registration_key": registration.key,
            "registration_version": registration.version, "endpoint_id": endpoint.id,
        }, result="failed", actor=user.email,
            evidence={"kind": "probe_failure", "reason_code": "connector_pull_failed"})
        db.add(AuditLog(event="data_source_capability.probed", actor=user.email,
                        entity_type="capability_registration", entity_id=str(registration.id),
                        detail_json={"result": "failed", "reason_code": "connector_pull_failed"}))
        db.commit()
        raise HTTPException(502, "connector_pull_failed") from None
    db.expire_all()
    try:
        data_source_plugins.configured_data_endpoint(db, registration, "api")
    except (ValueError, TypeError) as exc:
        raise HTTPException(409, "data_source_capability_changed") from exc
    mapped_facts = db.scalar(select(func.count(Fact.id)).where(Fact.source_document_id == source.id)) or 0
    if mapped_facts < 1 or not source.sha256 or not re.fullmatch(r"[0-9a-f]{64}", source.sha256):
        append_verification(db, registration, scope_kind="data_source_endpoint", scope={
            "plugin_key": "api", "registration_key": registration.key,
            "registration_version": registration.version, "endpoint_id": endpoint.id,
        }, result="failed", actor=user.email,
            evidence={"kind": "probe_failure", "reason_code": "no_mapped_facts"})
        db.add(AuditLog(event="data_source_capability.probed", actor=user.email,
                        entity_type="capability_registration", entity_id=str(registration.id),
                        detail_json={"result": "failed", "reason_code": "no_mapped_facts"}))
        db.commit()
        raise HTTPException(422, "data_source_probe_no_mapped_facts")
    verification = append_verification(db, registration, scope_kind="data_source_endpoint", scope={
        "plugin_key": "api", "registration_key": registration.key,
        "registration_version": registration.version, "endpoint_id": endpoint.id,
    }, result="verified", actor=user.email,
        evidence={"kind": "platform_readback", "reference_hash": source.sha256})
    db.add(AuditLog(event="data_source_capability.probed", actor=user.email,
                    entity_type="capability_registration", entity_id=str(registration.id),
                    detail_json={"result": "verified", "verification_id": verification.id}))
    db.commit()
    return {"verified": True, "registration_id": registration.id,
            "verification_id": verification.id, "source_id": source.id, "facts": mapped_facts}
