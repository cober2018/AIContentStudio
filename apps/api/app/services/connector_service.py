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


def _render_values(data: dict, today: str) -> dict:
    return {k: str(v).replace(PLACEHOLDER_TODAY, today) if isinstance(v, str) else v for k, v in data.items()}


DEFAULT_MAX_PAGES = 20


def _fetch_all_pages(endpoint: ConnectorEndpoint, url: str, headers: dict[str, str]) -> tuple[list[dict], str]:
    """带分页拉取全部条目。返回 (items, 最后一页原始响应文本)。

    page 型：page_param 从 page_start 递增，某页 items_path 为空数组即停；
    cursor 型：从响应 cursor_path 取游标写入 cursor_param，游标缺失/为空即停。
    """
    mapping = endpoint.fact_mapping_json or {}
    items_path = mapping.get("items_path")
    pagination = endpoint.pagination_json or {}
    p_type = pagination.get("type")
    max_pages = int(pagination.get("max_pages", DEFAULT_MAX_PAGES))
    method = (endpoint.method or "GET").upper()
    if method not in {"GET", "POST"}:
        raise ConnectorError(f"不支持的 method：{endpoint.method}")

    today = datetime.now(UTC).date().isoformat()
    base_params = _render_params(endpoint.params_json or {}, today)
    body = _render_values(endpoint.body_template_json or {}, today) if method == "POST" else None

    all_items: list[dict] = []
    last_raw = "{}"
    page = int(pagination.get("page_start", 1))
    cursor: str | None = pagination.get("cursor_start")
    # POST 的分页参数在 body 里；GET 在 query 里
    page_target = body if body is not None else None

    def _set_page_param(params: dict, key: str, value: str) -> None:
        if page_target is not None:
            page_target[key] = value
        else:
            params[key] = value

    for _ in range(max_pages if p_type else 1):
        params = dict(base_params)
        if p_type == "page":
            _set_page_param(params, pagination.get("page_param", "page"), str(page))
        elif p_type == "cursor" and cursor:
            _set_page_param(params, pagination.get("cursor_param", "cursor"), cursor)

        page_url = httpx_url_join_urlonly(url, params)
        content, _ = safe_fetch(page_url, headers, method=method, json_body=body)
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ConnectorError(f"响应不是有效 JSON：{exc}") from exc
        last_raw = content.decode("utf-8", errors="replace")

        if items_path:
            items = get_json_path(payload, items_path)
        elif isinstance(payload, list):
            items = payload
        else:
            items = [payload]
        if not isinstance(items, list):
            raise ConnectorError("items_path 指向的不是数组")
        all_items.extend(items)

        if p_type == "page":
            page += 1
            if not items or (pagination.get("stop_path") and not get_json_path(payload, pagination["stop_path"])):
                break
            if pagination.get("has_more_path") and not get_json_path(payload, pagination["has_more_path"]):
                break
        elif p_type == "cursor":
            try:
                cursor = str(get_json_path(payload, pagination.get("cursor_path", "next_cursor")))
            except ConnectorError:
                break
            if not cursor:
                break
        else:
            break

    return all_items, last_raw


def httpx_url_join_urlonly(base_url: str, params: dict) -> str:
    import httpx

    return str(httpx.Request("GET", base_url, params=params).url)



def pull_endpoint(db: Session, endpoint: ConnectorEndpoint, user: User) -> tuple[SourceDocument, int]:
    """执行一次拉取：请求外部 API（支持 POST/分页）→ 存 SourceDocument → 映射生成候选 Fact。"""
    connector = endpoint.connector
    if not connector.is_active:
        raise ConnectorError("Connector 已停用")
    if connector.connector_type == "local_git":
        return _pull_local_git(db, connector, endpoint, user)

    today = datetime.now(UTC).date().isoformat()
    url = connector.base_url.rstrip("/") + "/" + endpoint.path.lstrip("/")

    headers = _auth_headers(connector)
    all_items, last_raw = _fetch_all_pages(endpoint, url, headers)

    # as_of 优先从最后一页响应取；分页 items 模式下响应结构被收集，退化为 endpoint 级配置
    endpoint_as_of = None
    if endpoint.as_of_path:
        try:
            endpoint_as_of = str(get_json_path(json.loads(last_raw), endpoint.as_of_path))
        except (ConnectorError, json.JSONDecodeError):
            endpoint_as_of = None

    title = endpoint.title_template.replace(PLACEHOLDER_TODAY, today)
    mapping = endpoint.fact_mapping_json or {}

    candidates = []
    for item in all_items:
        candidates.extend(map_response_to_facts({"item": [item]}, {**mapping, "items_path": "item"}, endpoint_as_of))

    mime = "application/json"
    text_lines = [c.statement for c in candidates]
    doc = SourceDocument(
        title=title,
        source_type="connector",
        source_url=url,
        original_uri=f"connector:{connector.id}/endpoint:{endpoint.id}",
        mime_type=mime,
        as_of=endpoint_as_of or today,
        trust_level=endpoint.trust_level,
        sha256=hashlib.sha256(last_raw.encode()).hexdigest(),
        raw_text=last_raw,
        parse_status=ParseStatus.done.value,
        parsed_json={
            "blocks": [{"type": "line", "text": line, "locator": {"index": i}} for i, line in enumerate(text_lines)],
            "metadata": {
                "connector": connector.name,
                "endpoint": endpoint.name,
                "item_count": len(candidates),
                "pages_items": len(all_items),
            },
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


def _pull_local_git(db: Session, connector: Connector, endpoint: ConnectorEndpoint, user: User) -> tuple[SourceDocument, int]:
    """本地开发文档数据源（connector_type=local_git）。

    connector.base_url = 仓库根目录；endpoint.path = 相对 glob（如 docs/**/*.md、CHANGELOG.md）；
    params: {max_files, max_bytes_per_file, git_log, max_commits}。
    只读文本（md/txt）与 git log，不执行任何仓库代码；目录必须在 LOCAL_DOCS_ALLOWLIST 前缀内。
    """
    import subprocess
    from pathlib import Path

    from ..config import get_settings

    today = datetime.now(UTC).date().isoformat()
    allowlist = get_settings().local_docs_allowlist_dirs
    if not allowlist:
        raise ConnectorError("未启用本地文档数据源：需设置 LOCAL_DOCS_ALLOWLIST（允许读取的目录前缀）")
    root = Path(connector.base_url.replace("file://", "")).expanduser().resolve()
    if not root.is_dir():
        raise ConnectorError(f"仓库目录不存在: {root}")
    if not any(str(root).startswith(prefix) for prefix in allowlist):
        raise ConnectorError(f"目录不在 LOCAL_DOCS_ALLOWLIST 内: {root}")

    params = endpoint.params_json or {}
    max_files = int(params.get("max_files", 20))
    max_bytes = int(params.get("max_bytes_per_file", 200_000))
    pattern = endpoint.path or "*.md"
    files = sorted(p for p in root.glob(pattern) if p.is_file())[:max_files]
    if not files:
        raise ConnectorError(f"未匹配到文档文件: {pattern}（相对 {root.name}）")

    sections: list[str] = []
    blocks: list[dict] = []
    for f in files:
        rel = f.relative_to(root).as_posix()
        text = f.read_text(encoding="utf-8", errors="replace")[:max_bytes]
        sections.append(f"## 文件：{rel}\n\n{text}")
        blocks.append({"type": "doc", "text": text, "locator": {"file": rel}})

    git_log = ""
    if params.get("git_log"):
        max_commits = str(params.get("max_commits", 50))
        try:
            proc = subprocess.run(
                ["git", "-C", str(root), "log", f"--max-count={max_commits}", "--no-decorate", "--oneline"],
                capture_output=True, text=True, timeout=10, check=True,
            )
            git_log = proc.stdout
            sections.append(f"## 近期提交（修复/变更日志）\n\n{git_log}")
            blocks.append({"type": "git_log", "text": git_log, "locator": {"source": "git log"}})
        except (subprocess.SubprocessError, OSError):
            pass  # 非 git 目录 / git 不可用：best-effort 跳过

    as_of = today
    if git_log:
        try:
            proc = subprocess.run(
                ["git", "-C", str(root), "log", "-1", "--format=%cs"],
                capture_output=True, text=True, timeout=5, check=True,
            )
            as_of = proc.stdout.strip() or today
        except (subprocess.SubprocessError, OSError):
            pass

    raw_text = "\n\n".join(sections)
    doc = SourceDocument(
        title=endpoint.title_template.replace(PLACEHOLDER_TODAY, today),
        source_type="local_git",
        source_url=str(root),
        original_uri=f"connector:{connector.id}/endpoint:{endpoint.id}",
        mime_type="text/markdown",
        as_of=as_of,
        trust_level=endpoint.trust_level,
        sha256=hashlib.sha256(raw_text.encode()).hexdigest(),
        raw_text=raw_text,
        parse_status=ParseStatus.done.value,
        parsed_json={
            "blocks": blocks,
            "metadata": {
                "connector": connector.name,
                "endpoint": endpoint.name,
                "files": [f.relative_to(root).as_posix() for f in files],
                "git_log_commits": len(git_log.splitlines()) if git_log else 0,
            },
        },
        metadata_json={"connector_id": connector.id, "endpoint_id": endpoint.id, "root": str(root)},
    )
    db.add(doc)
    db.flush()

    endpoint.last_pull_at = datetime.now(UTC)
    endpoint.last_pull_status = "ok"
    endpoint.last_pull_error = None
    db.add(AuditLog(event="connector.pulled", actor=user.email, entity_type="connector_endpoint",
                    entity_id=str(endpoint.id),
                    detail_json={"source_id": doc.id, "files": len(files), "facts": 0}))
    db.commit()
    return doc, 0


def record_pull_failure(db: Session, endpoint: ConnectorEndpoint, error: str) -> None:
    """拉取失败也要留痕在 endpoint 上，前端能看到最近一次错误。"""
    endpoint.last_pull_at = datetime.now(UTC)
    endpoint.last_pull_status = "failed"
    endpoint.last_pull_error = error[:500]
    db.commit()
