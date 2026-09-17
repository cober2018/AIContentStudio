"""External Connector API（EPIC-18）。"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_admin, require_editor
from ..models import Connector, ConnectorEndpoint, User
from ..services import connector_service
from ..services.connector_service import ConnectorError
from ..services.url_fetch import UnsafeUrlError

router = APIRouter(prefix="/api/v1", tags=["connectors"])

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
    params: dict[str, str] | None = None
    title_template: str = Field(min_length=1, max_length=300)
    as_of_path: str | None = None
    trust_level: float = 0.9
    fact_mapping: dict
    pagination: dict | None = None
    interval_minutes: int | None = Field(default=None, ge=0, le=10080)


def _validate_connector(payload: ConnectorIn) -> None:
    if not payload.base_url.startswith(("http://", "https://")):
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
    if "statement" not in payload.fact_mapping or "value" not in payload.fact_mapping.get("fields", {}):
        raise HTTPException(400, "fact_mapping 需要包含 statement 模板和 fields.value 字段引用")
    if payload.method.upper() not in {"GET", "POST"}:
        raise HTTPException(400, "method 只允许 GET/POST")
    if payload.method.upper() == "POST" and not payload.body_template:
        raise HTTPException(400, "POST 请求需要提供 body_template")
    p_type = (payload.pagination or {}).get("type")
    if p_type not in {None, "page", "cursor"}:
        raise HTTPException(400, "pagination.type 只允许 page/cursor")
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
        doc, count = connector_service.pull_endpoint(db, endpoint, user)
    except ConnectorError as exc:
        connector_service.record_pull_failure(db, endpoint, str(exc))
        raise HTTPException(400, str(exc)) from exc
    except UnsafeUrlError as exc:
        connector_service.record_pull_failure(db, endpoint, f"SSRF 拦截：{exc}")
        raise HTTPException(400, f"目标被安全策略拒绝：{exc}") from exc
    except Exception as exc:
        connector_service.record_pull_failure(db, endpoint, str(exc))
        raise HTTPException(502, f"拉取失败：{exc}") from exc
    return {
        "source_id": doc.id,
        "source_title": doc.title,
        "facts": count,
        "endpoint": _serialize_endpoint(endpoint),
    }
