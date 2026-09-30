"""Private bounded search candidates; explicit downloads reuse media acceptance."""

from __future__ import annotations

import hashlib
import json
import logging
import marshal
import re
import threading
import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import unquote, urlencode, urlsplit

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import User
from . import provider_media
from .content_harness import providers
from .content_harness.contracts import MaterialSearchResult
from .project_authorization import lock_project_context
from .url_fetch import pinned_transport

_lock = threading.RLock()
_cache: dict[str, Candidate] = {}
_TTL = 900
_fetching = ContextVar("commons_fetching", default=False)


class _PrivateFetchLogs(logging.Filter):
    def filter(self, _record):
        return not _fetching.get()


logging.getLogger("httpx").addFilter(_PrivateFetchLogs())


def commons_fetch(url: str, max_bytes: int) -> tuple[bytes, str]:
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname not in {"commons.wikimedia.org", "upload.wikimedia.org"}
            or parsed.port not in {None, 443} or parsed.username or parsed.password or parsed.fragment
            or (parsed.hostname == "upload.wikimedia.org" and parsed.query)
            or (parsed.hostname == "commons.wikimedia.org" and parsed.path != "/w/api.php")):
        raise ValueError("search fetch source forbidden")
    limit = min(max_bytes, 5_000_000)
    deadline = time.monotonic() + 15
    token = _fetching.set(True)
    try:
        current = url
        for _ in range(4):
            with (
                httpx.Client(timeout=10, follow_redirects=False, trust_env=False,
                             transport=pinned_transport(current)) as client,
                client.stream("GET", current, headers={"User-Agent": "AIContentStudio/0.1 (explicit user media search)", "Accept-Encoding": "identity"}) as response,
            ):
                if response.status_code in {301, 302, 303, 307, 308}:
                    redirected = httpx.URL(current).join(response.headers["location"])
                    original = httpx.URL(url)
                    if (redirected.scheme, redirected.host, redirected.port) != (original.scheme, original.host, original.port):
                        raise ValueError("search redirect forbidden")
                    if redirected.username or redirected.password or (redirected.host == "upload.wikimedia.org" and redirected.query):
                        raise ValueError("search redirect forbidden")
                    current = str(redirected)
                    continue
                response.raise_for_status()
                if response.headers.get("content-encoding", "identity").strip().lower() != "identity":
                    raise ValueError("search response compression forbidden")
                if int(response.headers.get("content-length", "0")) > limit:
                    raise ValueError("search response too large")
                chunks, total = [], 0
                for chunk in response.iter_bytes():
                    total += len(chunk)
                    if total > limit or time.monotonic() > deadline:
                        raise ValueError("search fetch bound exceeded")
                    chunks.append(chunk)
                return b"".join(chunks), response.headers.get("content-type", "").split(";")[0].strip()
        raise ValueError("search redirects exceeded")
    finally:
        _fetching.reset(token)


class _PlainText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


class WikimediaSearchProvider:
    key = "search.wikimedia.commons"
    version = "1"

    def runtime_fingerprint(self):
        return hashlib.sha256(b"commons.policy.v1.image.5MB.CC0.CCBY4" + marshal.dumps(self.search.__code__)
                              + marshal.dumps(self.fetch.__code__) + marshal.dumps(commons_fetch.__code__)).hexdigest()

    def search(self, query: str, limit: int = 10) -> MaterialSearchResult:
        params = {"action": "query", "format": "json", "formatversion": "2", "generator": "search", "gsrnamespace": "6",
                  "gsrsearch": query, "gsrlimit": limit, "prop": "imageinfo", "iiprop": "url|mime|size|sha1|extmetadata",
                  "iiextmetadatafilter": "LicenseShortName|Artist", "iilimit": "1"}
        content, mime = commons_fetch("https://commons.wikimedia.org/w/api.php?" + urlencode(params), 1_000_000)
        if mime != "application/json":
            raise ValueError("search metadata MIME invalid")
        data = json.loads(content)
        pages = data.get("query", {}).get("pages", [])
        if not isinstance(pages, list) or len(pages) > limit:
            raise ValueError("search metadata bound exceeded")
        items = []
        for page in pages:
            image = page.get("imageinfo", [{}])[0]
            if image.get("mime") not in {"image/png", "image/jpeg", "image/webp"} or type(image.get("size")) is not int or not 0 < image["size"] <= 5_000_000:
                continue
            sha1 = image.get("sha1", "")
            if not isinstance(sha1, str) or not re.fullmatch(r"[0-9a-z]{1,40}", sha1):
                continue
            if not re.fullmatch(r"[0-9a-f]{40}", sha1):
                numeric_hash = int(sha1, 36)
                if numeric_hash >= 2 ** 160:
                    continue
                sha1 = f"{numeric_hash:040x}"
            metadata = image.get("extmetadata", {})
            license_name = metadata.get("LicenseShortName", {}).get("value", "")
            code = {"CC0": "CC0", "CC BY 4.0": "CC-BY-4.0"}.get(license_name, "unknown")
            artist = metadata.get("Artist", {}).get("value", "")
            if not isinstance(artist, str) or len(artist) > 5000:
                continue
            plain = _PlainText()
            plain.feed(artist)
            attribution = "".join(plain.parts).strip() or None
            if attribution and len(attribution) > 1000:
                continue
            title = page.get("title", "")
            if not isinstance(title, str) or not title.startswith("File:") or len(title) > 200:
                continue
            items.append({"source_id": f"commons.{page['pageid']}.{sha1}", "title": title[5:], "license_code": code,
                          "attribution_text": attribution, "source_url": image.get("descriptionurl"), "fetch_url": image.get("url"),
                          "mime_type": image["mime"], "source_sha1": sha1})
        return MaterialSearchResult(self.key, items)

    def fetch(self, candidate: dict) -> providers.MediaOutput:
        content, mime = commons_fetch(candidate["fetch_url"], 5_000_000)
        if hashlib.sha1(content).hexdigest() != candidate.get("source_sha1"):
            raise ValueError("source bytes changed")
        return providers.MediaOutput("succeeded", content, mime)


@dataclass
class Candidate:
    actor_id: int
    key: str
    version: str
    runtime_hash: str
    input_hash: str
    payload: dict
    safe: dict
    expires: float


def safe_citation(value: object) -> str | None:
    if not isinstance(value, str) or len(value) > 1000:
        return None
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return None
    if (parsed.scheme != "https" or parsed.hostname != "commons.wikimedia.org" or port not in {None, 443}
            or parsed.username or parsed.password or parsed.query or parsed.fragment
            or not parsed.path.startswith("/wiki/File:") or any(char in unquote(value) for char in "\r\n\x00")):
        return None
    return value


def _safe_text(value: object, maximum: int) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or re.search(r"https?://|token|secret|signature|authorization", value, re.IGNORECASE):
        raise HTTPException(422, "search_metadata_invalid")
    return value.strip()


def _prune():
    for key in [key for key, candidate in _cache.items() if candidate.expires <= time.monotonic()]:
        del _cache[key]


def search(user: User, *, key: str, version: str, query: str, limit: int) -> dict:
    provider, runtime_hash = provider_media._provider("search_provider", key, version)
    with _lock:
        _prune()
        if len(_cache) + limit > 640 or sum(candidate.actor_id == user.id for candidate in _cache.values()) + limit > 40:
            raise HTTPException(429, "search_preview_capacity")
    try:
        result = provider.search(query, limit=limit)
    except Exception:  # noqa: BLE001 Never return provider diagnostics or query URLs.
        raise HTTPException(502, "search_provider_failed") from None
    if not isinstance(result, MaterialSearchResult) or result.provider_key != key or not isinstance(result.items, list) or len(result.items) > limit:
        raise HTTPException(422, "search_result_invalid")
    staged, output = {}, []
    for item in result.items:
        if not isinstance(item, dict):
            raise HTTPException(422, "search_result_invalid")
        source_id = _safe_text(item.get("source_id"), 150)
        title = _safe_text(item.get("title"), 200)
        observed_license = item.get("license_code")
        license_code = observed_license if isinstance(observed_license, str) and observed_license in {"CC0", "CC-BY-4.0"} else "unknown"
        attribution = _safe_text(item.get("attribution_text"), 1000) if item.get("attribution_text") else None
        if license_code == "CC-BY-4.0" and not attribution:
            license_code = "unknown"
        fetch_url = item.get("fetch_url")
        if not isinstance(fetch_url, str) or len(fetch_url) > 2000:
            raise HTTPException(422, "search_result_invalid")
        mime_type, source_sha1 = item.get("mime_type"), item.get("source_sha1")
        if (not isinstance(mime_type, str) or mime_type not in {"image/png", "image/jpeg", "image/webp"}
                or (source_sha1 is not None and (not isinstance(source_sha1, str) or not re.fullmatch(r"[0-9a-f]{40}", source_sha1)))):
            raise HTTPException(422, "search_metadata_invalid")
        url_hash = hashlib.sha256(fetch_url.encode()).hexdigest()
        safe = {"source_id": source_id, "title": title, "source_url": safe_citation(item.get("source_url")),
                "license_code": license_code, "attribution_text": attribution,
                "fetch_url_hash": url_hash, "public_ready": False}
        safe["license_evidence_hash"] = provider_media._hash({field: safe[field] for field in
                                                           ("source_id", "source_url", "license_code", "attribution_text", "fetch_url_hash")})
        input_hash = provider_media._hash({"query_hash": hashlib.sha256(query.encode()).hexdigest(), "source": safe, "provider": key, "version": version})
        token = uuid.uuid4().hex
        payload = {"source_id": source_id, "fetch_url": fetch_url, "mime_type": mime_type, "source_sha1": source_sha1}
        staged[token] = Candidate(user.id, key, version, runtime_hash, input_hash, payload, safe, time.monotonic() + _TTL)
        output.append({**{field: safe[field] for field in ("title", "source_url", "license_code", "attribution_text", "license_evidence_hash", "public_ready")}, "candidate_id": token})
    with _lock:
        _prune()
        if len(_cache) + len(staged) > 640 or sum(candidate.actor_id == user.id for candidate in _cache.values()) + len(staged) > 40:
            raise HTTPException(429, "search_preview_capacity")
        _cache.update(staged)
    return {"items": output, "provider_key": key, "provider_version": version, "verified": False, "expires_in_seconds": _TTL}


def stage(db: Session, user: User, candidate_id: str, project_id: int | None) -> dict:
    with _lock:
        _prune()
        candidate = _cache.get(candidate_id)
        if candidate is None or candidate.actor_id != user.id:
            raise HTTPException(404, "search_candidate_unavailable_or_expired")
    if candidate.safe["license_code"] == "unknown":
        raise HTTPException(422, "search_license_unknown")
    if project_id is not None:
        project = lock_project_context(db, project_id, user)
        if project.status == "archived":
            raise HTTPException(409, "project_archived")
        db.rollback()
    provider, runtime_hash = provider_media._provider("search_provider", candidate.key, candidate.version)
    if runtime_hash != candidate.runtime_hash:
        raise HTTPException(409, "search_runtime_changed")
    try:
        output = provider.fetch(candidate.payload)
    except Exception:  # noqa: BLE001 Fetch errors can contain signed URLs.
        raise HTTPException(502, "search_download_failed") from None
    if not isinstance(output, providers.MediaOutput) or output.status != "succeeded":
        raise HTTPException(422, "search_output_invalid")
    return provider_media.stage_output(user, kind="search_provider", key=candidate.key, version=candidate.version,
                                       runtime_hash=runtime_hash, input_hash=candidate.input_hash, output=output,
                                       project_id=project_id, search_origin=candidate.safe)
