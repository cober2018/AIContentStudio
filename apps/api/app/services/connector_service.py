"""External Connector 拉取服务（EPIC-18）。

量化平台等外部 API 返回结构化 JSON，直接按映射规则生成候选 Fact，
比句子规则抽取准确：statement 由模板渲染，value/unit/as_of 来自字段值。
"""

import hashlib
import json
import os
import re
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from ..models import AuditLog, Connector, ConnectorEndpoint, Fact, ParseStatus, SourceDocument, User
from .fact_extractor import CandidateFact
from .url_fetch import safe_fetch

PLACEHOLDER_TODAY = "{today}"


class ConnectorError(ValueError):
    """配置或映射错误（用户可修复），与网络错误区分。"""


def get_json_path(data: Any, path: str) -> Any:
    """按 a.b.0.c 取 JSON 值。路径不存在时抛 ConnectorError 指明位置。"""
    current = data
    for part in path.split("."):
        if isinstance(current, dict):
            if part not in current:
                raise ConnectorError(f"映射路径不存在：{path}（在 {part} 处断开）")
            current = current[part]
        elif isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                raise ConnectorError(f"映射路径不存在：{path}（数组下标 {part} 无效）") from None
        else:
            raise ConnectorError(f"映射路径不存在：{path}（在 {part} 处类型为标量）")
    return current


def render_template(template: str, values: dict[str, Any]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in values:
            raise ConnectorError(f"模板字段 {{{key}}} 在数据中不存在，可用字段：{sorted(values)}")
        return str(values[key])

    return re.sub(r"\{(\w+)\}", replace, template)


def _field_source(raw: Any) -> tuple[str, str]:
    """字段值来自 item 字段名还是常量：`{xxx}` 视为引用，其余为常量。"""
    text = str(raw)
    if text.startswith("{") and text.endswith("}"):
        return "ref", text[1:-1]
    return "const", text


def map_response_to_facts(
    payload: dict,
    mapping: dict,
    endpoint_as_of: str | None,
) -> list[CandidateFact]:
    """按映射协议把 JSON 响应转为候选事实。

    mapping 协议：
      items_path: 数组在响应中的路径，缺省视为根对象单条
      fields: {value/subject/unit/predicate} → item 字段名（{xxx}）或常量
      statement: 陈述模板，引用 item 字段
      as_of_field: item 内字段名；缺省用 endpoint 层的 as_of_path 解析结果
    """
    items_path = mapping.get("items_path")
    if items_path:
        items = get_json_path(payload, items_path)
        if not isinstance(items, list):
            raise ConnectorError(f"items_path 指向的不是数组：{items_path}")
    else:
        items = [payload]

    fields = mapping.get("fields") or {}
    statement_tpl = mapping.get("statement")
    if not statement_tpl:
        raise ConnectorError("映射缺少 statement 模板")

    value_src, value_key = _field_source(fields.get("value", ""))
    if value_src != "ref":
        raise ConnectorError("fields.value 必须是 {字段名} 引用，事实需要数值")

    candidates = []
    for item in items:
        if not isinstance(item, dict):
            raise ConnectorError("items 数组元素必须是对象")
        if value_key not in item:
            raise ConnectorError(f"字段 {value_key} 在数据条目中不存在，可用字段：{sorted(item)}")

        raw_value = item[value_key]
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            value = str(raw_value)

        subject = None
        if "subject" in fields:
            src, key = _field_source(fields["subject"])
            subject = str(item.get(key, "")) if src == "ref" and key in item else (key if src == "const" else None)

        unit = None
        if "unit" in fields:
            src, key = _field_source(fields["unit"])
            unit = str(item.get(key, "")) if src == "ref" and key in item else key

        predicate = None
        if "predicate" in fields:
            src, key = _field_source(fields["predicate"])
            predicate = str(item.get(key, "")) if src == "ref" and key in item else key

        as_of_field = mapping.get("as_of_field")
        as_of = str(item[as_of_field]) if as_of_field and as_of_field in item else endpoint_as_of

        candidates.append(
            CandidateFact(
                statement=render_template(statement_tpl, item),
                fact_type="metric",
                subject=subject,
                predicate=predicate,
                value=value,
                unit=unit,
                as_of=as_of,
                source_locator={"via": "connector_mapping", "items_path": items_path},
                confidence=0.95,
            )
        )
    return candidates


def _auth_headers(connector: Connector) -> dict[str, str]:
    headers = dict(connector.default_headers_json or {})
    if connector.auth_style == "none":
        return headers
    if not connector.api_key_env:
        raise ConnectorError("Connector 需要 api_key_env（鉴权凭据的环境变量名）")

    api_key = os.environ.get(connector.api_key_env, "")
    if not api_key:
        raise ConnectorError(f"环境变量 {connector.api_key_env} 未设置（该 Connector 的鉴权凭据）")
    if connector.auth_style == "bearer":
        headers["Authorization"] = f"Bearer {api_key}"
    elif connector.auth_style == "header":
        headers[connector.auth_header_name or "X-API-Key"] = api_key
    else:
        raise ConnectorError(f"不支持的 auth_style：{connector.auth_style}")
    return headers


def _render_params(params: dict, today: str) -> dict:
    return {k: str(v).replace(PLACEHOLDER_TODAY, today) for k, v in params.items()}


def pull_endpoint(db: Session, endpoint: ConnectorEndpoint, user: User) -> tuple[SourceDocument, int]:
    """执行一次拉取：GET 外部 API → 存 SourceDocument → 映射生成候选 Fact。"""
    connector = endpoint.connector
    if not connector.is_active:
        raise ConnectorError("Connector 已停用")

    today = datetime.now(UTC).date().isoformat()
    params = _render_params(endpoint.params_json or {}, today)
    url = httpx_url_join(connector.base_url, endpoint.path, params)

    headers = _auth_headers(connector)
    content, mime = safe_fetch(url, headers)

    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ConnectorError(f"响应不是有效 JSON：{exc}") from exc

    endpoint_as_of = str(get_json_path(payload, endpoint.as_of_path)) if endpoint.as_of_path else None
    title = endpoint.title_template.replace(PLACEHOLDER_TODAY, today)

    candidates = map_response_to_facts(payload, endpoint.fact_mapping_json or {}, endpoint_as_of)

    text_lines = [c.statement for c in candidates]
    doc = SourceDocument(
        title=title,
        source_type="connector",
        source_url=url,
        original_uri=f"connector:{connector.id}/endpoint:{endpoint.id}",
        mime_type=mime or "application/json",
        as_of=endpoint_as_of or today,
        trust_level=endpoint.trust_level,
        sha256=hashlib.sha256(content).hexdigest(),
        raw_text=json.dumps(payload, ensure_ascii=False, indent=2),
        parse_status=ParseStatus.done.value,
        parsed_json={
            "blocks": [{"type": "line", "text": line, "locator": {"index": i}} for i, line in enumerate(text_lines)],
            "metadata": {"connector": connector.name, "endpoint": endpoint.name, "item_count": len(candidates)},
        },
        metadata_json={"connector_id": connector.id, "endpoint_id": endpoint.id, "final_url": url},
    )
    db.add(doc)
    db.flush()

    for c in candidates:
        db.add(
            Fact(
                source_document_id=doc.id,
                statement=c.statement,
                fact_type=c.fact_type,
                subject=c.subject,
                predicate=c.predicate,
                value_json={"value": c.value},
                unit=c.unit,
                as_of=c.as_of,
                confidence=min(c.confidence, endpoint.trust_level),
                source_locator_json=c.source_locator,
                created_by=user.email,
            )
        )

    endpoint.last_pull_at = datetime.now(UTC)
    endpoint.last_pull_status = "ok"
    endpoint.last_pull_error = None
    db.add(AuditLog(event="connector.pulled", actor=user.email, entity_type="connector_endpoint",
                    entity_id=str(endpoint.id),
                    detail_json={"source_id": doc.id, "facts": len(candidates)}))
    db.commit()
    return doc, len(candidates)


def record_pull_failure(db: Session, endpoint: ConnectorEndpoint, error: str) -> None:
    """拉取失败也要留痕在 endpoint 上，前端能看到最近一次错误。"""
    endpoint.last_pull_at = datetime.now(UTC)
    endpoint.last_pull_status = "failed"
    endpoint.last_pull_error = error[:500]
    db.commit()


def httpx_url_join(base_url: str, path: str, params: dict) -> str:
    import httpx

    return str(httpx.Request("GET", base_url.rstrip("/") + "/" + path.lstrip("/"), params=params).url)
