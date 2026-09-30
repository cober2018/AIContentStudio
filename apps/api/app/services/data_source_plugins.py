"""Typed Data Source Plugin catalog and read-only snapshot adapter."""

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import (
    CapabilityRegistration,
    ConnectorEndpoint,
    ContentUnit,
    DataSnapshot,
    Fact,
    SourceDocument,
    User,
    WorkflowRun,
    utcnow,
)
from . import connector_service
from .capability_integrations import endpoint_config_fingerprint, is_verified_for_scope
from .content_harness.registry import RegistryError, registry
from .project_events import record_project_event
from .workflow_engine import canonical_checksum

_CAPABILITY_REF = re.compile(r"capability:([1-9][0-9]*)@([A-Za-z0-9_.-]{1,50})\Z")


class GenericRestDataConnector:
    """The only loaded external Data Source executor in the first F7 mapping."""


def configured_data_endpoint(db: Session, registration: CapabilityRegistration, plugin_key: str) -> ConnectorEndpoint:
    if (registration.kind != "data_connector" or registration.data_source_plugin_key != plugin_key
            or registration.status != "configured" or registration.endpoint_id is None):
        raise ValueError("Data Source capability 映射不存在或版本不匹配")
    endpoint = db.get(ConnectorEndpoint, registration.endpoint_id)
    if endpoint is None or endpoint_config_fingerprint(endpoint) != registration.config_fingerprint:
        raise ValueError("Data Source capability 配置或凭据版本已变化")
    try:
        loaded = registry.resolve("data_connector", registration.key, registration.version)
    except RegistryError:
        if endpoint.connector.connector_type != "generic_rest":
            raise ValueError("Data Source capability 执行器未加载") from None
        registry.register("data_connector", registration.key, registration.version, GenericRestDataConnector())
        loaded = registry.resolve("data_connector", registration.key, registration.version)
    if not isinstance(loaded, GenericRestDataConnector):
        raise TypeError("Data Source capability 执行器不匹配")
    return endpoint


def verified_data_endpoint(db: Session, registration: CapabilityRegistration, plugin_key: str) -> ConnectorEndpoint:
    endpoint = configured_data_endpoint(db, registration, plugin_key)
    if endpoint.last_pull_status == "failed":
        raise ValueError("Data Source capability 最近拉取失败，须重新探测")
    scope = {"plugin_key": plugin_key, "registration_key": registration.key,
             "registration_version": registration.version, "endpoint_id": endpoint.id}
    if not is_verified_for_scope(db, registration, scope, registration.config_fingerprint, registry):
        raise ValueError("Data Source capability 未验证或已失效")
    return endpoint


def _mapped_endpoint(db: Session, plugin_key: str, source_ref: str, user: User | None, unit_id: int | None) -> tuple[ConnectorEndpoint, CapabilityRegistration]:
    match = _CAPABILITY_REF.fullmatch(source_ref)
    if plugin_key != "api" or match is None:
        raise ValueError("Data Source Plugin 未连接/不可执行")
    registration = db.get(CapabilityRegistration, int(match.group(1)))
    if registration is None or registration.version != match.group(2):
        raise ValueError("Data Source capability 映射不存在或版本不匹配")
    if user is None or unit_id is None:
        raise ValueError("Data Source capability 缺少项目授权上下文")
    unit = db.get(ContentUnit, unit_id)
    if unit is None:
        raise ValueError("Data Source capability 内容单元不存在")
    from .content_masters import owned_unit

    project, unit = owned_unit(db, unit.project_id, unit_id, user)
    if project.status == "archived" or unit.status == "archived":
        raise ValueError("Data Source capability 项目或内容单元已归档")
    return verified_data_endpoint(db, registration, plugin_key), registration

_PLUGINS = [
    ("studio.source", "内部数据 · Studio Source", "internal_data", True, None),
    ("media.data", "媒体数据", "media_data", False, "未连接经过验证的媒体数据源"),
    ("notion", "Notion", "knowledge_base", False, "Notion Connector 未连接"),
    ("obsidian", "Obsidian", "knowledge_base", False, "Obsidian Connector 未连接"),
    ("api", "API", "remote_api", False, "未配置并验证 API Connection"),
    ("sql", "SQL / Database", "database", False, "未配置只读数据库 Connection"),
]


def descriptors() -> list[dict]:
    return [
        {
            "key": key,
            "name": name,
            "category": category,
            "connection_mode": "internal_read_only" if key == "studio.source" else "external_connection",
            "capabilities": {"search": False, "query": False, "snapshot": key == "studio.source"},
            "config_schema": {"type": "object", "properties": {"source_ref": {"type": "string"}}, "required": ["source_ref"]},
            "result_schema": {"type": "object", "properties": {"snapshot_id": {"type": "integer"}, "data_checksum": {"type": "string"}}},
            "available": available,
            "reason": reason,
        }
        for key, name, category, available, reason in _PLUGINS
    ]


def assert_executable(db: Session, plugin_key: str, source_ref: str, *, user: User | None = None, unit_id: int | None = None) -> SourceDocument | ConnectorEndpoint:
    item = next((item for item in _PLUGINS if item[0] == plugin_key), None)
    if item is None:
        raise ValueError(f"未注册的 Data Source Plugin：{plugin_key}")
    if plugin_key == "api":
        return _mapped_endpoint(db, plugin_key, source_ref, user, unit_id)[0]
    if not item[3]:
        raise ValueError(f"Data Source Plugin 未连接/不可执行：{item[4]}")
    if plugin_key != "studio.source":
        raise ValueError("Data Source Plugin 未验证执行器")
    try:
        source_id = int(source_ref)
    except (TypeError, ValueError) as exc:
        raise ValueError("Studio Source 引用须为来源 ID") from exc
    source = db.get(SourceDocument, source_id)
    if source is None or source.is_archived:
        raise ValueError("Studio Source 不存在或已归档")
    return source


def snapshot_source(db: Session, run: WorkflowRun, node_id: str, plugin_key: str, source_ref: str, user: User | None = None) -> dict:
    if run.content_unit_id is None:
        raise ValueError("Data Node 只能在项目内容单元中执行")
    mapped = None
    if plugin_key == "api":
        endpoint, mapped = _mapped_endpoint(db, plugin_key, source_ref, user, run.content_unit_id)
        try:
            source, _facts, _created = connector_service.pull_endpoint(db, endpoint, user, dedup_mode="mapped_facts", bounded=True)
        except Exception as exc:  # noqa: BLE001 远端响应或异常可能含凭据，节点只记录安全码。
            connector_service.record_pull_failure(db, endpoint, exc, actor=user.email if user else None)
            raise ValueError("connector_pull_failed") from None
        db.expire_all()
        _mapped_endpoint(db, plugin_key, source_ref, user, run.content_unit_id)
    else:
        source = assert_executable(db, plugin_key, source_ref, user=user, unit_id=run.content_unit_id)
    if mapped is not None:
        blocks = (source.parsed_json or {}).get("blocks", [])
        text = "\n".join(str(block.get("text", "")) for block in blocks if isinstance(block, dict))
    else:
        text = source.raw_text or ""
    normalized = {
        "source_id": source.id,
        "title": source.title,
        "source_type": source.source_type,
        "as_of": source.as_of,
        "text": text[:20000],
        "truncated": len(text) > 20000,
    }
    if mapped is not None:
        facts = db.scalars(select(Fact).where(Fact.source_document_id == source.id).order_by(Fact.id)).all()
        normalized.update({
            "source_version": source.sha256,
            "fact_count": len(facts),
            "facts_truncated": len(facts) > 100,
            "facts": [{"fact_id": fact.id, "statement": fact.statement[:1000],
                       "value": value[:2000] if isinstance(value := (fact.value_json or {}).get("value"), str) else value,
                       "unit": fact.unit, "as_of": fact.as_of} for fact in facts[:100]],
        })
    checksum = canonical_checksum(normalized)
    previous = db.scalar(select(DataSnapshot).where(DataSnapshot.unit_id == run.content_unit_id, DataSnapshot.node_id == node_id).order_by(DataSnapshot.id.desc()).limit(1))
    snapshot = DataSnapshot(
        unit_id=run.content_unit_id,
        run_id=run.id,
        node_id=node_id,
        plugin_key=plugin_key,
        source_ref=source_ref if mapped is not None else str(source.id),
        source_version=source.sha256,
        checksum=checksum,
        normalized_output=normalized,
        lineage_json={"source_document_id": source.id, "source_url": source.source_url, "as_of": source.as_of,
                      **({"connector_endpoint_id": mapped.endpoint_id, "capability_registration_id": mapped.id,
                          "capability_version": mapped.version, "config_fingerprint": mapped.config_fingerprint} if mapped else {})},
        created_at=utcnow(),
    )
    db.add(snapshot)
    db.flush()
    unit = db.get(ContentUnit, run.content_unit_id)
    if unit is not None:
        record_project_event(db, project_id=unit.project_id, event_type="data.snapshot_changed" if previous and previous.checksum != checksum else "data.snapshot_created", actor=None, entity_type="data_snapshot", entity_id=snapshot.id, payload={"unit_id": unit.id, "run_id": run.id, "node_id": node_id, "old_checksum": previous.checksum if previous else None, "new_checksum": checksum, "changed": bool(previous and previous.checksum != checksum)})
    return {"snapshot_id": snapshot.id, "data_checksum": checksum, "source_version": source.sha256}
