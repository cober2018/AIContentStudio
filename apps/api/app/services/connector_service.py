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

from sqlalchemy import select
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


def _render_value(value: Any) -> str:
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        # 上游 Float32 常带精度噪声（1.059999942779541），统一降噪到 6 位
        return str(round(value, 6))
    if isinstance(value, (list, tuple)):
        return "、".join(_render_value(v) for v in value) if value else "无"
    return str(value)


def render_template(template: str, values: dict[str, Any]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in values:
            raise ConnectorError(f"模板字段 {{{key}}} 在数据中不存在，可用字段：{sorted(values)}")
        return _render_value(values[key])

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


# ---------------------------------------------------------------------------
# 映射协议 v2：stages（一张宽表 → 一组精选事实，服务 DreamO 数据服务等宽表 API）
# ---------------------------------------------------------------------------

def _field_missing(value: Any) -> bool:
    """when_present 口径：None / 缺失 / 空串视为不存在（API 约定空串表示空值）。"""
    return value is None or value == ""


def _match_filter(item: dict, cond: dict) -> bool:
    """filter/when 精确匹配：期望 None 表示字段缺失或为 None；其他值按 str 相等比较。"""
    for key, expected in cond.items():
        actual = item.get(key)
        if expected is None:
            if actual is not None:
                return False
        elif _field_missing(actual) or str(actual) != str(expected):
            return False
    return True


def _sort_items(items: list[dict], sort_by: str | None) -> list[dict]:
    if not sort_by:
        return items
    desc = sort_by.startswith("-")
    key = sort_by.lstrip("+-")

    def sort_value(item: dict):
        v = item.get(key)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return (0, v)
        if v is None or v == "":
            return (2, 0)
        return (1, str(v))

    return sorted(items, key=sort_value, reverse=desc)


def _apply_derived(items: list[dict], derived: dict | None) -> list[dict]:
    """derived: {新字段: [源字段, 倍数]}——纯数值乘法，源值非数值时新字段缺省。"""
    if not derived:
        return items
    out = []
    for item in items:
        enriched = dict(item)
        for new_field, spec in derived.items():
            src, multiplier = spec
            v = item.get(src)
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                enriched[new_field] = round(v * multiplier, 2)
        out.append(enriched)
    return out


def _expand_items(item: dict, stage: dict) -> list[dict]:
    """把 *_json 字符串列二次解析为子条目：dict → [{key_into: k, **v}]；list → 原样。"""
    raw = item.get(stage["expand_field"])
    if _field_missing(raw):
        return []
    try:
        parsed = json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        return []
    key_into = stage.get("key_into")
    if isinstance(parsed, dict):
        if key_into:
            return [{key_into: k, **(v if isinstance(v, dict) else {"value": v})} for k, v in parsed.items()]
        return [parsed]
    if isinstance(parsed, list):
        return [el for el in parsed if isinstance(el, dict)]
    return []


def _facts_from_specs(items: list[dict], specs: list[dict], endpoint_as_of: str | None,
                      as_of_field: str | None, stage_label: str) -> list[CandidateFact]:
    candidates: list[CandidateFact] = []
    for item in items:
        ctx = dict(item)
        for spec in specs:
            statement_tpl = spec.get("statement")
            if not statement_tpl:
                raise ConnectorError(f"stage[{stage_label}] 的 fact 缺少 statement 模板")
            if any(_field_missing(ctx.get(f)) for f in spec.get("when_present", [])):
                continue
            if not _match_filter(ctx, spec.get("when") or {}):
                continue
            candidates.append(_build_fact(ctx, spec, statement_tpl, endpoint_as_of, as_of_field, stage_label))
    return candidates


def _build_fact(ctx: dict, spec: dict, statement_tpl: str, endpoint_as_of: str | None,
                as_of_field: str | None, stage_label: str) -> CandidateFact:
    statement = render_template(statement_tpl, ctx)

    value_src, value_key = _field_source(spec.get("value", ""))
    value: float | str | None
    if value_src == "ref":
        raw = ctx.get(value_key)
        if _field_missing(raw):
            raise ConnectorError(f"stage[{stage_label}] value 字段 {value_key} 缺失（when_present 应覆盖）")
        try:
            value = float(raw)
        except (TypeError, ValueError):
            value = str(raw)
        else:
            if isinstance(value, float):
                value = round(value, 6)
    else:
        value = spec.get("value")

    def resolve(field: str) -> str | None:
        if field not in spec:
            return None
        src, key = _field_source(spec[field])
        if src == "const":
            return key
        raw = ctx.get(key)
        return None if _field_missing(raw) else str(raw)

    as_of = None
    if as_of_field and not _field_missing(ctx.get(as_of_field)):
        as_of = str(ctx[as_of_field])

    return CandidateFact(
        statement=statement,
        fact_type=spec.get("fact_type", "metric"),
        subject=resolve("subject"),
        predicate=resolve("predicate"),
        value=value,
        unit=resolve("unit"),
        as_of=as_of or endpoint_as_of,
        source_locator={"via": "connector_mapping_v2", "stage": stage_label},
        confidence=float(spec.get("confidence", 0.95)),
    )


def _facts_from_stage(items: list[dict], stage: dict, endpoint_as_of: str | None,
                      as_of_field: str | None) -> list[CandidateFact]:
    mode = stage.get("mode", "item")
    filtered = [it for it in items if _match_filter(it, stage.get("filter") or {})]
    if not filtered:
        return []
    filtered = _sort_items(filtered, stage.get("sort_by"))
    if stage.get("limit"):
        filtered = filtered[: int(stage["limit"])]

    if mode == "aggregate":
        work_items = [filtered[0]]
    elif mode == "expand":
        work_items = _expand_items(filtered[0], stage)
        work_items = _apply_derived(work_items, stage.get("derived"))
        work_items = _sort_items(work_items, stage.get("sort_by"))
        if stage.get("limit"):
            work_items = work_items[: int(stage["limit"])]
        return _facts_from_specs(work_items, stage["facts"], endpoint_as_of, as_of_field, mode)
    elif mode == "join":
        work_items = _apply_derived(filtered, stage.get("derived"))
        ctx: dict[str, Any] = dict(work_items[0])
        ctx["__count__"] = len(work_items)
        if stage.get("count_by"):
            counts: dict[str, int] = {}
            for it in work_items:
                k = str(it.get(stage["count_by"]))
                counts[k] = counts.get(k, 0) + 1
            ctx["__counts__"] = " ".join(f"{k}={v}" for k, v in sorted(counts.items(), key=lambda kv: -kv[1]))
        if stage.get("join_field"):
            names = [str(it.get(stage["join_field"])) for it in work_items if not _field_missing(it.get(stage["join_field"]))]
            ctx["__joined__"] = "、".join(names)
        return _facts_from_specs([ctx], stage["facts"], endpoint_as_of, as_of_field, mode)
    else:
        work_items = _apply_derived(filtered, stage.get("derived"))

    return _facts_from_specs(work_items, stage["facts"], endpoint_as_of, as_of_field, mode)


def map_response_to_facts_v2(payload_items: list[dict], mapping: dict,
                             endpoint_as_of: str | None) -> list[CandidateFact]:
    """v2 映射：stages 按序作用在 items 上，各自产出候选事实。"""
    stages = mapping.get("stages") or []
    if not stages:
        raise ConnectorError("v2 映射需要非空 stages 列表")
    as_of_field = mapping.get("as_of_field")
    candidates: list[CandidateFact] = []
    for stage in stages:
        if not stage.get("facts"):
            raise ConnectorError("v2 stage 缺少 facts 列表")
        candidates.extend(_facts_from_stage(payload_items, stage, endpoint_as_of, as_of_field))
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
    """带分页拉取全部条目。返回 (items, 最后一个有数据页的原始响应文本)。

    page 型：page_param 从 page_start 递增，某页 items_path 为空数组即停；
    cursor 型：从响应 cursor_path 取游标写入 cursor_param，游标缺失/为空即停；
    offset 型：limit/offset 下推（DreamO 数据服务约定），取回行数 < page_size 即停。
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
    offset = int(pagination.get("offset_start", 0))
    page_size = int(pagination.get("page_size", 500))
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
        elif p_type == "offset":
            _set_page_param(params, pagination.get("limit_param", "limit"), str(page_size))
            _set_page_param(params, pagination.get("offset_param", "offset"), str(offset))

        page_url = httpx_url_join_urlonly(url, params)
        content, _ = safe_fetch(page_url, headers, method=method, json_body=body)
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ConnectorError(f"响应不是有效 JSON：{exc}") from exc

        if items_path:
            items = get_json_path(payload, items_path)
        elif isinstance(payload, list):
            items = payload
        else:
            items = [payload]
        if not isinstance(items, list):
            raise ConnectorError("items_path 指向的不是数组")
        all_items.extend(items)
        if items:
            # 空页不覆盖 last_raw，保证 as_of_path 从最后一个有数据的响应解析
            last_raw = content.decode("utf-8", errors="replace")

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
        elif p_type == "offset":
            offset += page_size
            if len(items) < page_size:
                break
        else:
            break

    return all_items, last_raw


def httpx_url_join_urlonly(base_url: str, params: dict) -> str:
    import httpx

    return str(httpx.Request("GET", base_url, params=params).url)



def pull_endpoint(db: Session, endpoint: ConnectorEndpoint, user: User) -> tuple[SourceDocument, int, bool]:
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

    if mapping.get("stages"):
        # v2 宽表协议：stages 从 items 里精选聚合事实（见 map_response_to_facts_v2）
        candidates = map_response_to_facts_v2(all_items, mapping, endpoint_as_of)
    else:
        candidates = []
        for item in all_items:
            candidates.extend(map_response_to_facts({"item": [item]}, {**mapping, "items_path": "item"}, endpoint_as_of))

    raw_keep = mapping.get("raw_keep_fields")
    if raw_keep:
        # 宽表原始响应瘦身：只保留关注列，避免 190 列 × 千行 JSON 打爆 SQLite raw_text
        trimmed = [{k: it.get(k) for k in raw_keep} for it in all_items]
        raw_text = json.dumps({"row_count": len(trimmed), "rows": trimmed}, ensure_ascii=False)
    else:
        raw_text = last_raw

    # 去重：同一端点拉到的响应与上次完全一致（sha256 相同）→ 不新建 Source，只刷新状态
    prev = db.scalars(
        select(SourceDocument.id).where(SourceDocument.original_uri == f"connector:{connector.id}/endpoint:{endpoint.id}")
        .order_by(SourceDocument.id.desc()).limit(1)
    ).first()
    prev_sha = db.scalars(
        select(SourceDocument.sha256).where(SourceDocument.id == prev).limit(1)
    ).first() if prev else None
    # 指纹用候选事实集合（statement 排序哈希）：响应内嵌时间戳会导致整包 sha 每次不同
    new_sha = hashlib.sha256(
        json.dumps(sorted(c.statement for c in candidates), ensure_ascii=False).encode()
    ).hexdigest()
    endpoint.last_pull_at = datetime.now(UTC)
    if prev and prev_sha == new_sha:
        endpoint.last_pull_status = "ok"
        endpoint.last_pull_error = None
        db.commit()
        return db.get(SourceDocument, prev), 0, False

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
        sha256=new_sha,
        raw_text=raw_text,
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
    return doc, len(candidates), True


def _pull_local_git(db: Session, connector: Connector, endpoint: ConnectorEndpoint, user: User) -> tuple[SourceDocument, int, bool]:
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
    # 去重：文件与 git log 都没变化则不新建
    prev = db.scalars(
        select(SourceDocument.id).where(SourceDocument.original_uri == f"connector:{connector.id}/endpoint:{endpoint.id}")
        .order_by(SourceDocument.id.desc()).limit(1)
    ).first()
    prev_sha = db.scalars(
        select(SourceDocument.sha256).where(SourceDocument.id == prev).limit(1)
    ).first() if prev else None
    new_sha = hashlib.sha256(raw_text.encode()).hexdigest()
    endpoint.last_pull_at = datetime.now(UTC)
    if prev and prev_sha == new_sha:
        endpoint.last_pull_status = "ok"
        endpoint.last_pull_error = None
        db.commit()
        return db.get(SourceDocument, prev), 0, False
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
    return doc, 0, True


def record_pull_failure(db: Session, endpoint: ConnectorEndpoint, error: str) -> None:
    """拉取失败也要留痕在 endpoint 上，前端能看到最近一次错误。"""
    endpoint.last_pull_at = datetime.now(UTC)
    endpoint.last_pull_status = "failed"
    endpoint.last_pull_error = error[:500]
    db.commit()
