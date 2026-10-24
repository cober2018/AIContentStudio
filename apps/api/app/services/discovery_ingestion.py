"""Bounded RSS/Atom, structured HTML and public JSON collection."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

import httpx
from sqlalchemy import select, update

from ..models import DiscoveryItem, DiscoverySource, PersonaSourceSubscription, utcnow
from .discovery_runtime import aware, digest
from .discovery_search import canonical_url
from .url_fetch import UnsafeUrlError, safe_fetch


def clean(value, limit=2500):
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]*>", " ", str(value or "")))).strip()[:limit]


def source_date(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        date = datetime.fromisoformat(value.strip())
    except ValueError:
        try:
            date = parsedate_to_datetime(value)
        except (ValueError, TypeError, OverflowError):
            return None
    return aware(date).astimezone(UTC)


def _item(url, title, text, date, base):
    if not isinstance(url, str) or not url.strip():
        return None
    try:
        url = canonical_url(urljoin(base, str(url or "")))
    except ValueError:
        return None
    title = clean(title, 500)
    if not title or not url:
        return None
    return {"url": url, "title": title, "text": clean(text), "published_at": source_date(date)}


def parse_feed(body, base, *, limit=30):
    if b"<!DOCTYPE" in body.upper() or b"<!ENTITY" in body.upper():
        raise ValueError("feed_entities_forbidden")
    root = ET.fromstring(body)
    entries = list(root.findall(".//item")) + list(root.findall(".//{http://www.w3.org/2005/Atom}entry"))
    result = []
    for entry in entries[:limit]:
        fields = {}
        for node in entry:
            key = node.tag.rsplit("}", 1)[-1]
            if key == "link":
                if node.get("rel", "alternate") == "alternate":
                    fields[key] = node.get("href") or node.text
            else:
                fields[key] = "".join(node.itertext())
        item = _item(fields.get("link"), fields.get("title"),
                     fields.get("description") or fields.get("summary") or fields.get("content") or fields.get("encoded"),
                     fields.get("pubDate") or fields.get("published") or fields.get("updated") or fields.get("date"), base)
        if item:
            result.append(item)
    return result


class _Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.feeds, self.structured = [], []
        self.capture = False
        self.script = []

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag == "link" and data.get("type", "").lower() in {"application/rss+xml", "application/atom+xml"} and data.get("href"):
            self.feeds.append(data["href"])
        if tag == "script" and data.get("type", "").lower() == "application/ld+json":
            self.capture, self.script = True, []

    def handle_data(self, data):
        if self.capture:
            self.script.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.capture:
            self.capture = False
            try:
                self.structured.append(json.loads("".join(self.script)))
            except ValueError:
                pass


def parse_html(body, base, *, limit=30):
    parser = _Page()
    parser.feed(body.decode("utf-8", errors="replace"))
    result = []

    def walk(value, depth=0):
        if depth > 8 or len(result) >= limit:
            return
        if isinstance(value, list):
            for child in value[:max(100, limit)]:
                walk(child, depth + 1)
        elif isinstance(value, dict):
            if value.get("datePublished") and (value.get("headline") or value.get("name")):
                item = _item(value.get("url") or value.get("@id"), value.get("headline") or value.get("name"),
                             value.get("description") or value.get("articleBody"), value.get("datePublished"), base)
                if item:
                    result.append(item)
            for key in ("@graph", "itemListElement", "item", "hasPart", "blogPost"):
                if key in value:
                    walk(value[key], depth + 1)
    walk(parser.structured)
    return parser.feeds[:3], result


def parse_json(body, base, config, *, limit=30):
    data = json.loads(body)
    path = config.get("items_path", "")
    if not isinstance(path, str) or len(path.split(".")) > 4:
        raise ValueError("json_mapping_invalid")
    for key in filter(None, path.split(".")):
        data = data.get(key) if isinstance(data, dict) else None
    if not isinstance(data, list):
        raise TypeError("json_list_required")
    mapping = config.get("fields", {"title": "title", "url": "url", "date": "date", "text": "description"})
    if set(mapping) - {"title", "url", "date", "text"} or any(not isinstance(v, str) for v in mapping.values()):
        raise ValueError("json_mapping_invalid")
    rows = []
    for row in data[:limit]:
        if isinstance(row, dict):
            item = _item(row.get(mapping.get("url", "url")), row.get(mapping.get("title", "title")),
                         row.get(mapping.get("text", "description")), row.get(mapping.get("date", "date")), base)
            if item:
                rows.append(item)
    return rows


def probe(url, adapter=None):
    body, mime = safe_fetch(url)
    if "xml" in mime or body.lstrip().startswith((b"<?xml", b"<rss", b"<feed")):
        return {"kind": "rss", "url": canonical_url(url)}, parse_feed(body, url)
    if "json" in mime:
        config = {"kind": "json", "url": canonical_url(url), **(adapter or {})}
        return config, parse_json(body, url, config)
    feeds, rows = parse_html(body, url)
    for feed in feeds:
        try:
            feed_url = canonical_url(urljoin(url, feed))
            feed_body, _ = safe_fetch(feed_url)
            items = parse_feed(feed_body, feed_url)
            if items:
                return {"kind": "rss", "url": feed_url}, items
        except (UnsafeUrlError, httpx.HTTPError, ET.ParseError, ValueError, TypeError):
            continue
    return {"kind": "html", "url": canonical_url(url)}, rows


def persist_items(db, source, rows, *, metadata=None):
    saved = 0
    for item in rows:
        item_hash = digest(item["url"])
        checksum = digest({**item, "published_at": item["published_at"].isoformat() if item["published_at"] else None})
        existing = db.scalar(select(DiscoveryItem.id).where(DiscoveryItem.source_id == source.id,
            DiscoveryItem.item_key == item_hash, DiscoveryItem.checksum == checksum))
        if existing:
            continue
        db.add(DiscoveryItem(source_id=source.id, item_key=item_hash, checksum=checksum,
                            provenance_json={"adapter": source.adapter_json.get("kind"), "scope": "bounded_excerpt", "date_status": "future_date" if item["published_at"] and item["published_at"] > utcnow() else "verified" if item["published_at"] else "unknown"}, **item))
        saved += 1
        db.flush()
    source.cursor_json = {**(source.cursor_json or {}), **{k: v for k, v in (metadata or {}).items() if k in {"etag", "last_modified"} and v}}
    source.last_success_at, source.last_error, source.failures = utcnow(), None, 0
    minutes = 30 if source.kind == "hotlist" else 360 if source.kind in {"blog", "creator"} else 60
    source.next_due_at = utcnow() + timedelta(minutes=minutes)
    return saved


def register_candidate(db, run, candidate, *, activate=True):
    from .discovery_runtime import check_current

    config = check_current(db, run)
    original = canonical_url(candidate["url"])
    from .discovery_sources import find_source, lock_owner, locked_source, management, reconcile_manual_sources

    known = find_source(db, run.owner_user_id, original)
    if known and management(known).get("roles_managed"):
        known = locked_source(db, known.id, run.owner_user_id)
        known.evidence_json = {**known.evidence_json, "run_id": run.id, "search_provider": config["search_provider"]}
        db.flush()
        reconcile_manual_sources(db, owner_id=run.owner_user_id)
        return known
    source = known or db.scalar(select(DiscoverySource).where(DiscoverySource.owner_user_id == run.owner_user_id,
        (DiscoverySource.canonical_url == original) | (DiscoverySource.evidence_json["search_url"].as_string() == original)))
    reuse = source is not None and source.status == "active" and bool(source.adapter_json)
    adapter, items, reason = (source.adapter_json if reuse else {}), [], None
    try:
        adapter, items = probe(original, candidate.get("adapter")) if activate and not reuse else (adapter, [])
    except httpx.HTTPStatusError as exc:
        reason = "credential_required" if exc.response.status_code in {401, 403} else "source_validation_failed"
    except (UnsafeUrlError, httpx.HTTPError, ET.ParseError, ValueError, TypeError):
        reason = "source_validation_failed"
    endpoint = adapter.get("url", original)
    lock_owner(db, run.owner_user_id)
    source = find_source(db, run.owner_user_id, original) or find_source(db, run.owner_user_id, endpoint)
    if source:
        source = locked_source(db, source.id, run.owner_user_id)
    if source and management(source).get("roles_managed"):
        source = locked_source(db, source.id, run.owner_user_id)
        source.evidence_json = {**source.evidence_json, "run_id": run.id, "search_provider": config["search_provider"]}
        db.flush()
        reconcile_manual_sources(db, owner_id=run.owner_user_id)
        return source
    is_new = source is None
    if source is None:
        source = DiscoverySource(owner_user_id=run.owner_user_id, canonical_url=endpoint,
            name=clean(candidate.get("name") or candidate.get("title") or urlsplit(original).hostname, 300),
            actor_key=".".join(urlsplit(original).hostname.lower().split(".")[-2:]),
            kind=candidate.get("kind") if candidate.get("kind") in {"official", "media", "creator", "community", "hotlist", "blog"} else "website",
            language=str(candidate.get("language") or "unknown")[:20],
            evidence_json={"run_id": run.id, "search_url": original, "search_provider": config["search_provider"],
                           "identity": "public_homepage" if items else "unverified", "relevance": str(candidate.get("relevance") or "")[:1500]})
        db.add(source)
        db.flush()
    source.evidence_json = {**(source.evidence_json or {}), "run_id": run.id, "search_url": original,
        "search_provider": config["search_provider"], "relevance": str(candidate.get("relevance") or "")[:1500],
        "identity_evidence": {"public_entry_url": original, "collector_url": endpoint,
            "verified_scope": "public_entry_and_items" if items or reuse else "unverified_entry",
            "item_urls": [item["url"] for item in items[:3]]},
        "identity": "public_homepage" if items or reuse else "unverified"}
    source.language = str(candidate.get("language") or source.language or "unknown")[:20]
    if is_new:
        source.processing_allowed = config["public_processing_allowed"]
    if not source.manually_paused and not reuse:
        source.adapter_json = adapter
        has_date = any(i["published_at"] for i in items)
        source.status = "active" if has_date and source.processing_allowed else "candidate"
        if not items:
            source.last_error = reason or "adapter_unavailable"
        elif not has_date:
            source.last_error = "source_dates_unverified"
        if source.status == "active":
            check_current(db, run)
            persist_items(db, source, items)
    from sqlalchemy import func

    from ..models import ContentPersona

    db.execute(update(ContentPersona).where(ContentPersona.id == run.persona_id).values(status=ContentPersona.status))
    current_count = db.scalar(select(func.count(PersonaSourceSubscription.id)).join(DiscoverySource,
        DiscoverySource.id == PersonaSourceSubscription.source_id).where(
        PersonaSourceSubscription.persona_id == run.persona_id, PersonaSourceSubscription.source_id != source.id,
        PersonaSourceSubscription.profile_hash == run.profile_hash, PersonaSourceSubscription.enabled.is_(True),
        PersonaSourceSubscription.manually_paused.is_(False), DiscoverySource.status == "active",
        DiscoverySource.processing_allowed.is_(True), DiscoverySource.manually_paused.is_(False)))
    activate = activate and current_count < config["active_sources"]
    subscription = db.scalar(select(PersonaSourceSubscription).where(PersonaSourceSubscription.persona_id == run.persona_id,
                                                                    PersonaSourceSubscription.source_id == source.id))
    if subscription is None:
        subscription = PersonaSourceSubscription(persona_id=run.persona_id, source_id=source.id,
            profile_hash=run.profile_hash, relevance=str(candidate.get("relevance") or "")[:2500], enabled=activate)
        db.add(subscription)
    else:
        subscription.profile_hash = run.profile_hash
        subscription.relevance = str(candidate.get("relevance") or subscription.relevance)[:2500]
        if not subscription.manually_paused and activate:
            subscription.enabled = True
    db.flush()
    return source


def collect_source(db, source_id):
    from .discovery_catchup import collect_latest

    return collect_latest(db, source_id)


def article_evidence(url, *, fetcher=None):
    """Keep article text separate from feed summaries and freeze date provenance."""
    from .parsers import HtmlParser

    metadata = {}
    body, mime = (fetcher or safe_fetch)(url, response_metadata=metadata)
    if "html" not in mime:
        raise ValueError("article_html_required")
    html = body.decode("utf-8", errors="replace")
    parser = _Page()
    parser.feed(html)
    structured = []

    def walk(value, depth=0):
        if depth > 8:
            return
        if isinstance(value, list):
            for child in value[:100]:
                walk(child, depth + 1)
        elif isinstance(value, dict):
            structured.append(value)
            for key in ("@graph", "mainEntity", "blogPost"):
                if key in value:
                    walk(value[key], depth + 1)
    walk(parser.structured)
    articles = [v for v in structured if v.get("headline") or v.get("articleBody")]
    bodies = [v["articleBody"] for v in articles if isinstance(v.get("articleBody"), str)]
    region = re.search(r"<(article|main)\b[^>]*>(.*?)</\1>", html, re.IGNORECASE | re.DOTALL)
    publication_label = ""
    if fetcher and not bodies and not region and urlsplit(url).hostname == "www.chinanews.com.cn":
        region = re.search(r"<!--(正文start)-->(.*?)<!--正文end-->", html, re.DOTALL)
        publication = re.search(r'<span\b[^>]*id=["\']pubtime_baidu["\'][^>]*>([^<]+)</span>', html)
        if publication:
            publication_label = "发布时间：" + publication.group(1) + "\n"
    if not bodies and not region:
        raise ValueError("article_region_missing")
    text = clean(max(bodies, key=len), 10000) if bodies else HtmlParser().parse(
        (region.group(2) if region else html).encode()).text[:10000]
    text = publication_label + text
    if len(re.sub(r"\s+", "", text)) < 120:
        raise ValueError("article_body_missing")
    dates = {}
    for field in ("datePublished", "dateModified"):
        value = next((source_date(v.get(field)) for v in articles if source_date(v.get(field))), None)
        if value:
            dates[field] = value.isoformat()
    return {**({"resolved_url": metadata.get("final_url", url)} if fetcher else {}), "body": text, "body_checksum": digest(text), "body_fetched_at": utcnow().isoformat(),
            "page_dates": dates}
