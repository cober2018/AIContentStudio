"""AIHOT selected-set synchronization, retaining original evidence and history."""

import copy
import ipaddress
import json
import time
from datetime import timedelta
from urllib.parse import urlencode, urljoin, urlsplit

import httpx
from sqlalchemy import select

from ..models import ContentOpportunity, ContentOpportunitySignal, DiscoveryItem, DiscoverySource, SystemSetting, utcnow
from .discovery_runtime import digest
from .url_fetch import UnsafeUrlError, safe_fetch

HOSTS = {"aitech.kayoyo.top", "wonderlife.kayoyo.top"}


def actor_key(url):
    host = (urlsplit(url).hostname or "").lower()
    parts = host.split(".")
    if host.endswith((".github.io", ".substack.com")):
        return host
    # Publisher subdomains count together; common country-code suffixes retain their publisher label.
    width = 3 if len(parts) >= 3 and len(parts[-1]) == 2 and parts[-2] in {"com", "co", "org", "net", "gov", "edu"} else 2
    return ".".join(parts[-width:])


def source_id_for(db, owner_id, persona_id):
    row = db.get(SystemSetting, f"discovery.aggregate.{owner_id}")
    return (row.value or {}).get("personas", {}).get(str(persona_id)) if row else None


def allowed_source_ids(db, owner_id, persona_id):
    from .radar_discovery import source_id_for as radar_source_id_for

    selected = source_id_for(db, owner_id, persona_id)
    if selected is None:
        return None
    radar = radar_source_id_for(db, owner_id, persona_id)
    return {selected, radar} if radar is not None else {selected}


def accepts_source(db, owner_id, persona_id, source_id):
    from .radar_discovery import is_radar
    from .radar_discovery import source_id_for as radar_source_id_for

    source = db.get(DiscoverySource, source_id)
    if is_radar(source):
        return (source.owner_user_id == owner_id
                and radar_source_id_for(db, owner_id, persona_id) == source_id)
    selected = allowed_source_ids(db, owner_id, persona_id)
    return selected is None or source_id in selected


def is_aggregate(source):
    return (source.adapter_json or {}).get("kind") == "aihot"


def fetch_public(url, **kwargs):
    from .url_fetch import _PinnedBackend, enforce_outbound_host, resolve_addresses, resolved_public_addresses

    try:
        return safe_fetch(url, **kwargs)
    except UnsafeUrlError as exc:
        if str(exc) != "禁止访问内网/保留地址":
            raise
        host = urlsplit(url).hostname
        addresses = resolve_addresses(host, urlsplit(url).port or 443)
        fake = ipaddress.ip_network("198.18.0.0/15")
        if not addresses or any(ipaddress.ip_address(a[4][0]) not in fake for a in addresses):
            raise
    enforce_outbound_host("https://dns.google/resolve")
    transport = httpx.HTTPTransport(retries=0, trust_env=False)
    transport._pool._network_backend = _PinnedBackend("dns.google", 443, "8.8.8.8", time.monotonic() + 10)
    with httpx.Client(transport=transport, follow_redirects=False, timeout=10, trust_env=False) as client:
        response = client.get("https://dns.google/resolve", params={"name": host, "type": "A"})
        response.raise_for_status()
        if len(response.content) > 64000:
            raise ValueError("aggregate_dns_response_too_large")
        data = response.json()
    if data.get("Status") != 0:
        raise ValueError("aggregate_public_dns_failed")
    answers = [a["data"] for a in data.get("Answer", []) if a.get("type") == 1]
    with resolved_public_addresses(host, answers):
        return safe_fetch(url, **kwargs)


def read_json(source, path, params=None):
    base = source.canonical_url
    parsed = urlsplit(base)
    if parsed.scheme != "https" or parsed.hostname not in HOSTS or parsed.port not in {None, 443} or parsed.username or parsed.password:
        raise ValueError("aggregate_host_invalid")
    if path not in {"/api/v1/selected/snapshot", "/api/v1/selected/changes", "/api/v1/hot-topics"}:
        raise ValueError("aggregate_path_invalid")
    url = f"https://{parsed.hostname}{path}?{urlencode(params or {})}"
    metadata = {}
    state = source.cursor_json or {}
    key = digest(url)
    headers = {"If-None-Match": state["etag"]} if state.get("etag_request") == key and state.get("etag") else {}
    body, _ = fetch_public(url, headers=headers, response_metadata=metadata)
    if metadata.get("status") == 304:
        return {"not_modified": True}
    value = json.loads(body)
    if not isinstance(value, dict) or value.get("schemaVersion") != 1:
        raise ValueError("aggregate_schema_invalid")
    return {**value, "_etag": metadata.get("etag"), "_etag_request": key}


def latest_items(db, source_id):
    rows = db.scalars(select(DiscoveryItem).where(DiscoveryItem.source_id == source_id)
                      .order_by(DiscoveryItem.id.desc())).all()
    latest = {}
    for row in rows:
        latest.setdefault(row.item_key, row)
    return latest


def _upsert(db, source, item):
    from .discovery_ingestion import clean, source_date
    from .discovery_search import canonical_url

    if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
        raise ValueError("aggregate_item_invalid")
    links = item.get("links") or {}
    original = canonical_url(links.get("original") or links.get("aihot"))
    if not item.get("title") or not isinstance(item.get("source"), dict):
        raise ValueError("aggregate_item_invalid")
    payload = {"id": item["id"], "title": item["title"], "summary": item.get("summary"),
               "original": original, "publishedAt": item.get("publishedAt"), "source": item["source"],
               "selected": True, "score": item.get("score"), "category": item.get("category")}
    content_hash, key = digest(payload), digest({"site": source.canonical_url, "id": item["id"]})
    previous = db.scalar(select(DiscoveryItem).where(DiscoveryItem.source_id == source.id,
        DiscoveryItem.item_key == key).order_by(DiscoveryItem.id.desc()).limit(1))
    if previous and previous.provenance_json.get("content_hash") == content_hash and previous.provenance_json.get("selected"):
        return 0
    db.add(DiscoveryItem(source_id=source.id, item_key=key, checksum=digest({"content_hash": content_hash, "parent": previous.id if previous else None}),
        url=original, title=clean(item["title"], 500), text=clean(item.get("summary")),
        published_at=source_date(item.get("publishedAt")), provenance_json={
            "adapter": "aihot", "content_hash": content_hash, "aggregate_id": item["id"], "aggregate_url": links.get("aihot"),
            "upstream": copy.deepcopy(item), "selected": True, "original_actor": actor_key(original),
            "scope": "upstream_summary", "date_status": "upstream_reported"}))
    db.flush()
    return 1


def _withdraw(db, source, item_id, changed_at=None):
    key = digest({"site": source.canonical_url, "id": item_id})
    previous = db.scalar(select(DiscoveryItem).where(DiscoveryItem.source_id == source.id,
        DiscoveryItem.item_key == key).order_by(DiscoveryItem.id.desc()).limit(1))
    if not previous or not previous.provenance_json.get("selected"):
        return 0
    data = {**previous.provenance_json, "parent_item_id": previous.id, "selected": False, "withdrawn_at": changed_at or utcnow().isoformat()}
    db.add(DiscoveryItem(source_id=source.id, item_key=key, checksum=digest(data), url=previous.url,
        title=previous.title, text=previous.text, published_at=previous.published_at, provenance_json=data))
    version_ids = set(db.scalars(select(DiscoveryItem.id).where(DiscoveryItem.source_id == source.id, DiscoveryItem.item_key == key)).all())
    for signal, op in db.execute(select(ContentOpportunitySignal, ContentOpportunity).join(
        ContentOpportunity, ContentOpportunity.id == ContentOpportunitySignal.opportunity_id).where(
        ContentOpportunity.owner_user_id == source.owner_user_id,
        ContentOpportunitySignal.status == "active")):
        annotation = signal.annotation_json or {}
        if annotation.get("item_id") not in version_ids and not any(
                r.get("item_id") in version_ids for r in [*annotation.get("timeline", []), *annotation.get("discovery_paths", [])]):
            continue
        signal.annotation_json = {**annotation, "upstream_withdrawal": {
            "source_id": source.id, "aggregate_id": item_id, "changed_at": data["withdrawn_at"],
            "notice": "上游已撤选，来源需复核；已有项目及冻结证据保留"}}
        if op.status not in {"converted", "archived"}:
            op.status = "watching"
    db.flush()
    return 1


def sync_page(db, source):
    """Caller owns the lease and commits item writes together with the cursor."""
    state = dict(source.cursor_json or {})
    snapshot = not state.get("sync_cursor")
    params = {"limit": 100}
    if snapshot:
        if state.get("snapshot_page"):
            params["page"] = state["snapshot_page"]
        path = "/api/v1/selected/snapshot"
    else:
        params["cursor"] = state["sync_cursor"]
        path = "/api/v1/selected/changes"
    try:
        data = read_json(source, path, params)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 409 and not snapshot and exc.response.json().get("code") == "snapshot_required":
            source.cursor_json = {"reset_reason": "snapshot_required"}
            return {"complete": False, "scanned": 0, "saved": 0, "reason": "aggregate_snapshot_required"}
        raise
    if data.get("not_modified"):
        if snapshot or state.get("has_more"):
            raise ValueError("aggregate_unchanged_unverified")
        source.last_success_at = utcnow()
        source.last_error, source.failures = None, 0
        source.next_due_at = utcnow() + timedelta(minutes=15)
        source.cursor_json = {**state, "synced_at": utcnow().isoformat()}
        return {"complete": True, "scanned": 0, "saved": 0, "reason": None}
    cursor, more = data.get("cursor"), data.get("hasMore")
    values = data.get("items" if snapshot else "changes")
    if (not isinstance(cursor, str) or not cursor or not isinstance(more, bool)
            or not isinstance(values, list) or len(values) > 100 or data.get("fields") != "default"):
        raise ValueError("aggregate_page_invalid")
    saved = 0
    if snapshot:
        if state.get("snapshot_cursor") and state["snapshot_cursor"] != cursor:
            raise ValueError("aggregate_snapshot_watermark_changed")
        seen = set(state.get("snapshot_ids", []))
        for item in values:
            saved += _upsert(db, source, item)
            seen.add(item["id"])
        next_page = data.get("nextPage")
        if more and (not isinstance(next_page, str) or not next_page or next_page == state.get("snapshot_page")):
            raise ValueError("aggregate_pagination_invalid")
        state.update(snapshot_cursor=cursor, snapshot_page=next_page, snapshot_ids=sorted(seen))
        if not more:
            for item in latest_items(db, source.id).values():
                if item.provenance_json.get("selected") and item.provenance_json.get("aggregate_id") not in seen:
                    saved += _withdraw(db, source, item.provenance_json["aggregate_id"])
            state = {"sync_cursor": cursor, "snapshot_completed_at": utcnow().isoformat()}
    else:
        for change in values:
            if not isinstance(change, dict):
                raise TypeError("aggregate_change_invalid")
            if change.get("op") == "upsert":
                saved += _upsert(db, source, change.get("item"))
            elif change.get("op") == "remove" and isinstance(change.get("id"), str):
                saved += _withdraw(db, source, change["id"], change.get("changedAt"))
            else:
                raise ValueError("aggregate_change_invalid")
        if more and cursor == state["sync_cursor"]:
            raise ValueError("aggregate_pagination_invalid")
        state["sync_cursor"] = cursor
    state["phase"] = "snapshot" if snapshot and more else "changes"
    complete = not snapshot and not more
    state["has_more"] = not complete
    state.update(etag=data.get("_etag"), etag_request=data.get("_etag_request"))
    if complete:
        state["synced_at"] = utcnow().isoformat()
    source.cursor_json = state
    source.last_error, source.failures = None, 0
    source.last_success_at = utcnow()
    source.next_due_at = utcnow() + timedelta(minutes=15)
    return {"complete": complete, "scanned": len(values), "saved": saved,
            "reason": None if complete else "aggregate_sync_incomplete"}


def reference(item, source):
    data = item.provenance_json or {}
    return {"actor": data.get("original_actor") or source.actor_key,
            "aggregate_url": data.get("aggregate_url"), "upstream": data.get("upstream")} if is_aggregate(source) else {}


def article(item, source):
    from .discovery_ingestion import article_evidence

    url, hops = item.url, []
    for _ in range(3):
        host = urlsplit(url).hostname
        if host not in HOSTS | {"aihot.news"}:
            result = article_evidence(url, fetcher=fetch_public)
            resolved = result.pop("resolved_url", url)
            if urlsplit(resolved).hostname in HOSTS | {"aihot.news"}:
                raise ValueError("aggregate_original_unresolved")
            return {**result, "url": resolved, "actor": actor_key(resolved),
                    "provenance_hops": [*hops, *([url] if url != resolved else [])]}
        body, mime = fetch_public(url)
        if "html" not in mime:
            raise ValueError("aggregate_article_html_required")
        # Aggregator summaries are leads; only an explicitly linked original establishes evidence.
        import re
        match = re.search(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>\s*(?:阅读原文|查看原文|原文|Read original|Original article)\s*</a>',
                          body.decode("utf-8", errors="replace"), re.IGNORECASE)
        if not match:
            raise ValueError("aggregate_original_unresolved")
        hops.append(url)
        url = urljoin(url, __import__("html").unescape(match.group(1)))
    raise ValueError("aggregate_original_unresolved")
