"""Typed Data Source Plugin catalog and read-only snapshot adapter."""

from sqlalchemy.orm import Session

from ..models import DataSnapshot, SourceDocument, WorkflowRun, utcnow
from .workflow_engine import canonical_checksum

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


def assert_executable(db: Session, plugin_key: str, source_ref: str) -> SourceDocument:
    item = next((item for item in _PLUGINS if item[0] == plugin_key), None)
    if item is None:
        raise ValueError(f"未注册的 Data Source Plugin：{plugin_key}")
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


def snapshot_source(db: Session, run: WorkflowRun, node_id: str, plugin_key: str, source_ref: str) -> dict:
    if run.content_unit_id is None:
        raise ValueError("Data Node 只能在项目内容单元中执行")
    source = assert_executable(db, plugin_key, source_ref)
    text = source.raw_text or ""
    normalized = {
        "source_id": source.id,
        "title": source.title,
        "source_type": source.source_type,
        "as_of": source.as_of,
        "text": text[:20000],
        "truncated": len(text) > 20000,
    }
    checksum = canonical_checksum(normalized)
    snapshot = DataSnapshot(
        unit_id=run.content_unit_id,
        run_id=run.id,
        node_id=node_id,
        plugin_key=plugin_key,
        source_ref=str(source.id),
        source_version=source.sha256,
        checksum=checksum,
        normalized_output=normalized,
        lineage_json={"source_document_id": source.id, "source_url": source.source_url, "as_of": source.as_of},
        created_at=utcnow(),
    )
    db.add(snapshot)
    db.flush()
    return {"snapshot_id": snapshot.id, "data_checksum": checksum, "source_version": source.sha256}
