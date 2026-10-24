"""Read new-term-radar exports, with explicitly authorized daily local production.

The caller owns authorization, leases and the transaction for configure/sync_report.
The parser contract was inspected at upstream 2568cdcba5691cd21d03f2c0a86f4461dbcb7234.
"""

from __future__ import annotations

import copy
import ipaddress
import json
import re
import stat
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit

from sqlalchemy import select

from ..models import DiscoveryItem, DiscoverySource, PersonaSourceSubscription, SystemSetting, utcnow
from .discovery_runtime import digest, profile
from .discovery_search import canonical_url
from .opportunity_policy import TECH, persona_policy

PARSER_VERSION = "radar.daily.v1"
MAX_BYTES = 4 * 1024 * 1024
MAX_LEADS = 1000
MAX_SYNC_ITEMS = 300
BLOCKS = ("x", "hf", "breakout", "sitemap", "newsite", "revenue", "ask", "gsc", "review", "summary", "keywords")


def is_radar(source):
    return bool(source and (source.adapter_json or {}).get("kind") == "radar")


def settings(db, owner_id, persona_id):
    row = db.get(SystemSetting, f"discovery.radar.{owner_id}.{persona_id}")
    return copy.deepcopy(row.value or {}) if row else {}


def source_id_for(db, owner_id, persona_id):
    config = settings(db, owner_id, persona_id)
    if (not config.get("enabled") or not config.get("producer_verified")
            or persona_policy(db, owner_id, persona_id) != TECH):
        return None
    source = db.get(DiscoverySource, config.get("source_id")) if config.get("source_id") else None
    if (not is_radar(source) or source.owner_user_id != owner_id
            or (source.adapter_json or {}).get("persona_id") != persona_id):
        return None
    return source.id


def _url(value):
    try:
        result = canonical_url(value)
        host = urlsplit(result).hostname
        if host == "localhost" or host.endswith((".localhost", ".local")):
            return None
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            pass
        else:
            if not address.is_global or address.is_multicast:
                return None
        return result
    except (ValueError, TypeError):
        return None


def _created(value):
    if type(value) not in (int, float) or value <= 0:
        return None
    try:
        return datetime.fromtimestamp(value, UTC).isoformat()
    except (ValueError, OverflowError, OSError):
        return None


def parse_report(data, *, producer_version=None, producer_revision=None):
    """Pure parser: counts use lead rows and distinct URL items, never fabricated dates."""
    if (not isinstance(data, dict) or not isinstance(data.get("leads"), list)
            or len(data["leads"]) > MAX_LEADS
            or any(not isinstance(data.get(key), dict) for key in BLOCKS)):
        raise ValueError("radar_daily_schema_invalid")
    items, unresolved, issues = {}, [], []
    for kind in BLOCKS:
        block = data[kind]
        if block.get("error") or block.get("errors"):
            issues.append(f"{kind}_error")
        if block.get("first_run"):
            issues.append(f"{kind}_first_run")
        if block.get("no_key"):
            issues.append(f"{kind}_unconfigured")
    if data["x"].get("skipped") and data["hf"].get("skipped"):
        # Upstream daily JSON omits recent_sources even when its Markdown includes them.
        issues.append("recent_sources_not_exported")
    sites = data["sitemap"].get("sites", {})
    if not isinstance(sites, dict):
        raise TypeError("radar_daily_schema_invalid")
    for block in sites.values():
        if isinstance(block, dict) and (block.get("error") or block.get("first_run")):
            issues.append("sitemap_partial")
    for key in ("posts_error", "related_errors", "country_errors", "competition_errors", "no_evidence"):
        if data["keywords"].get(key):
            issues.append(f"keywords_{key}")
    ask_rows = data["ask"].get("rows", [])
    if not isinstance(ask_rows, list):
        raise TypeError("radar_daily_schema_invalid")
    unknown_date_leads = 0
    for index, lead in enumerate(data["leads"]):
        if (not isinstance(lead, dict) or not isinstance(lead.get("term"), str) or not lead["term"].strip()
                or not isinstance(lead.get("kinds"), list)
                or any(not isinstance(k, str) for k in lead["kinds"])
                or not isinstance(lead.get("posts", []), list)):
            raise ValueError("radar_lead_invalid")
        references = []
        repo = lead.get("repo")
        if isinstance(repo, str) and re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
            references.append((f"https://github.com/{repo}", None, "breakout"))
        for post in lead.get("posts", []):
            if isinstance(post, dict):
                references.append((post.get("url"), None, "x"))
        about = lead.get("about")
        if isinstance(about, (list, tuple)) and len(about) == 2:
            references.append((about[0], None, "revenue"))
        if "ask" in lead["kinds"]:
            for row in ask_rows:
                if not isinstance(row, dict) or row.get("phrase") != lead["term"]:
                    continue
                if not isinstance(row.get("posts", []), list):
                    raise TypeError("radar_lead_invalid")
                for post in row.get("posts", []):
                    if isinstance(post, dict):
                        references.append((post.get("url"), _created(post.get("created")), "ask"))
        valid = [(url, date, kind) for raw, date, kind in references if (url := _url(raw))]
        if not any(date for _, date, _ in valid):
            unknown_date_leads += 1
        if not valid:
            unresolved.append({"index": index, "term": lead["term"], "reason": "original_url_unresolved",
                               "upstream": copy.deepcopy(lead)})
        for url, published_at, kind in valid:
            key = digest(url)
            item = items.setdefault(key, {
                "upstream_item_id": key, "original_url": url, "title": lead["term"],
                "producer": "new-term-radar", "producer_version": producer_version,
                "producer_revision": producer_revision, "parser_version": PARSER_VERSION,
                "discovered_at": None, "observed_at": None, "published_at": published_at, "event_at": None,
                "signal_kind": [], "terms": [], "upstream": [],
            })
            if kind not in item["signal_kind"]:
                item["signal_kind"].append(kind)
            if lead["term"] not in item["terms"]:
                item["terms"].append(lead["term"])
            if lead not in item["upstream"]:
                item["upstream"].append(copy.deepcopy(lead))
            if published_at:
                item["published_at"] = min(filter(None, (item["published_at"], published_at)))
    for item in items.values():
        item["terms"].sort()
        item["title"] = item["terms"][0]
        item["signal_kind"].sort()
        item["upstream"].sort(key=digest)
        item["payload_hash"] = digest(item)
    counts = {"lead_rows": len(data["leads"]), "resolved_leads": len(data["leads"]) - len(unresolved),
              "unresolved_leads": len(unresolved), "url_items": len(items),
              "unknown_published_at_leads": unknown_date_leads,
              "unknown_published_at_items": sum(i["published_at"] is None for i in items.values()),
              "unknown_discovered_at_leads": len(data["leads"]), "unknown_observed_at_leads": len(data["leads"])}
    return {"items": list(items.values()), "unresolved": unresolved, "counts": counts,
            "issues": sorted(set(issues)), "partial": bool(issues or unresolved), "report_hash": digest(data)}


def read_report(report_path, *, producer_version=None, producer_revision=None):
    if not isinstance(report_path, str) or not report_path:
        raise ValueError("radar_absolute_json_path_required")
    path = Path(report_path)
    if not path.is_absolute() or path.suffix.lower() != ".json":
        raise ValueError("radar_absolute_json_path_required")
    try:
        if not stat.S_ISREG(path.stat().st_mode):
            raise ValueError("radar_regular_file_required")
        with path.open("rb") as stream:
            raw = stream.read(MAX_BYTES + 1)
    except OSError:
        raise ValueError("radar_report_unavailable") from None
    if len(raw) > MAX_BYTES:
        raise ValueError("radar_report_too_large")
    try:
        def invalid_constant(_):
            raise ValueError("radar_report_invalid_json")

        data = json.loads(raw, parse_constant=invalid_constant)
    except (ValueError, UnicodeError):
        raise ValueError("radar_report_invalid_json") from None
    return parse_report(data, producer_version=producer_version, producer_revision=producer_revision)


def status(db, owner_id, persona_id):
    """A read-model only: no filesystem access, refresh, sync or transaction commit."""
    config = settings(db, owner_id, persona_id)
    source = db.get(DiscoverySource, config.get("source_id")) if config.get("source_id") else None
    if source and (source.owner_user_id != owner_id or not is_radar(source)
                   or source.adapter_json.get("persona_id") != persona_id):
        source = None
    state = source.cursor_json or {} if source else {}
    reason = None
    if not config:
        result = "unconfigured"
    elif not config.get("enabled"):
        result = "disabled"
    elif persona_policy(db, owner_id, persona_id) != TECH:
        result, reason = "unavailable", "radar_technology_only"
    elif not source:
        result, reason = "unavailable", "radar_source_missing"
    elif source.manually_paused or not source.processing_allowed:
        result, reason = "disabled", "radar_processing_paused"
    elif source.last_error == "radar_sync_required":
        result, reason = "ready", "radar_sync_required"
    elif source.last_error:
        result, reason = "unavailable", source.last_error
    elif not state.get("report_hash"):
        result = "ready"
    else:
        result = "partial" if state.get("partial") else "synced"
    from .radar_producer import projection

    return {"status": result, "reason": reason, "persona_id": persona_id, "config": config,
            "generation": projection(db, source.id) if source and config.get("auto_daily") else None,
            "source_id": source.id if source else None, "counts": state.get("counts") if not source or not source.last_error else None,
            "issues": state.get("issues"), "last_imported_at": state.get("imported_at"),
            "report_hash": state.get("report_hash"), "availability_checked": False}


def configure(db, owner_id, *, persona_id, report_path=None, enabled=True,
              producer_version=None, producer_revision=None, producer_verified=None, auto_daily=None, actor=None):
    """Explicit admin configuration; flush only. Enabling validates an existing export."""
    if type(enabled) is not bool:
        raise ValueError("radar_enabled_invalid")
    if persona_policy(db, owner_id, persona_id) != TECH:
        raise ValueError("radar_technology_only")
    key = f"discovery.radar.{owner_id}.{persona_id}"
    config = settings(db, owner_id, persona_id)
    auto_daily = config.get("auto_daily", False) if auto_daily is None else auto_daily
    if type(auto_daily) is not bool:
        raise ValueError("radar_auto_daily_invalid")
    path = report_path if report_path is not None else config.get("report_path")
    version = producer_version if producer_version is not None else config.get("producer_version")
    revision = producer_revision if producer_revision is not None else config.get("producer_revision")
    changed = (path, version, revision) != (config.get("report_path"), config.get("producer_version"),
                                           config.get("producer_revision"))
    verified = producer_verified if producer_verified is not None else (False if changed else config.get("producer_verified", False))
    if type(verified) is not bool:
        raise ValueError("radar_producer_verified_invalid")
    if version is not None and (not isinstance(version, str) or not re.fullmatch(r"[A-Za-z0-9_.+-]{1,80}", version)):
        raise ValueError("radar_producer_version_invalid")
    if revision is not None and (not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}", revision)):
        raise ValueError("radar_producer_revision_invalid")
    parsed, current = None, None
    if enabled and auto_daily:
        from .radar_producer import validate_install

        validate_install({"report_path": path, "producer_version": version, "producer_revision": revision})
    if enabled:
        if not version:
            raise ValueError("radar_producer_version_required")
        if not verified:
            raise ValueError("radar_producer_confirmation_required")
        if not isinstance(path, str) or not path:
            raise ValueError("radar_absolute_json_path_required")
        parsed = read_report(path, producer_version=version, producer_revision=revision)
        path = str(Path(path).resolve())
        current = profile(db, persona_id)
        if not current:
            raise ValueError("radar_persona_ineligible")
    source = db.get(DiscoverySource, config.get("source_id")) if config.get("source_id") else None
    if source and (source.owner_user_id != owner_id or not is_radar(source)
                   or source.adapter_json.get("persona_id") != persona_id):
        raise ValueError("radar_source_mismatch")
    if enabled and source is None:
        source = DiscoverySource(owner_user_id=owner_id, canonical_url=f"radar://local/{owner_id}/{persona_id}",
            name="New-term Radar", actor_key="new-term-radar", kind="local_report", status="active",
            processing_allowed=True, adapter_json={"kind": "radar", "persona_id": persona_id})
        db.add(source)
        db.flush()
    if source:
        source.adapter_json = {**source.adapter_json, "report_path": path, "producer_version": version,
                               "producer_revision": revision, "parser_version": PARSER_VERSION}
        source.status = "active" if enabled else "paused"
        if changed:
            source.cursor_json = {}
        if parsed:
            source.evidence_json = {**(source.evidence_json or {}), "validation": {
                "report_hash": parsed["report_hash"], "counts": parsed["counts"], "issues": parsed["issues"]}}
            if parsed["report_hash"] != (source.cursor_json or {}).get("report_hash"):
                source.last_error = "radar_sync_required"
        source.next_due_at = utcnow() if enabled else None
        sub = db.scalar(select(PersonaSourceSubscription).where(
            PersonaSourceSubscription.source_id == source.id, PersonaSourceSubscription.persona_id == persona_id))
        if sub is None and enabled:
            sub = PersonaSourceSubscription(persona_id=persona_id, source_id=source.id, profile_hash=current[3],
                                            relevance="显式科技Radar补充来源")
            db.add(sub)
        if sub:
            sub.enabled = enabled
            if current:
                sub.profile_hash = current[3]
    row = db.get(SystemSetting, key)
    if row is None:
        row = SystemSetting(key=key)
        db.add(row)
    row.value = {"enabled": enabled, "auto_daily": auto_daily, "persona_id": persona_id, "source_id": source.id if source else None,
                 "report_path": path, "producer_version": version, "producer_revision": revision,
                 "producer_verified": verified, "verified_by": actor if producer_verified is True else config.get("verified_by"),
                 "parser_version": PARSER_VERSION}
    row.updated_by = actor
    db.flush()
    return status(db, owner_id, persona_id)


def _sync_report(db, source):
    """Read one bounded report; caller commits versions and cursor under its existing lease.

    complete denotes bounded file consumption, not full upstream coverage. Callers must also
    inspect partial/reason before marking a catchup interval covered.
    Daily reports are not inventories and expose no withdrawal operation. Absence
    never withdraws old items; an existing selected=False version stays withdrawn.
    """
    if not is_radar(source):
        raise ValueError("radar_source_required")
    persona_id = (source.adapter_json or {}).get("persona_id")
    config = settings(db, source.owner_user_id, persona_id)
    if (source_id_for(db, source.owner_user_id, persona_id) != source.id or source.status != "active"
            or source.manually_paused or not source.processing_allowed):
        raise ValueError("radar_source_disabled")
    sub = db.scalar(select(PersonaSourceSubscription).where(
        PersonaSourceSubscription.source_id == source.id, PersonaSourceSubscription.persona_id == persona_id))
    current = profile(db, persona_id)
    if not sub or not sub.enabled or sub.manually_paused or not current or current[3] != sub.profile_hash:
        raise ValueError("radar_subscription_ineligible")
    if str(Path(config["report_path"]).resolve()) != config["report_path"]:
        raise ValueError("radar_report_path_changed")
    from .radar_producer import ensure_daily

    ensure_daily(db, source, config)
    parsed = read_report(config["report_path"], producer_version=config.get("producer_version"),
                         producer_revision=config.get("producer_revision"))
    from .discovery_aggregation import actor_key

    saved = 0
    budget_unexamined = max(0, len(parsed["items"]) - MAX_SYNC_ITEMS)
    parsed["counts"]["budget_unexamined_items"] = budget_unexamined
    if budget_unexamined:
        parsed["partial"] = True
        parsed["issues"].append("radar_item_budget")
    for item in parsed["items"][:MAX_SYNC_ITEMS]:
        previous = db.scalar(select(DiscoveryItem).where(DiscoveryItem.source_id == source.id,
            DiscoveryItem.item_key == item["upstream_item_id"]).order_by(DiscoveryItem.id.desc()).limit(1))
        if previous and (previous.provenance_json or {}).get("payload_hash") == item["payload_hash"]:
            continue
        provenance = {**item, "adapter": "radar", "content_hash": item["payload_hash"],
                      "selected": (previous.provenance_json or {}).get("selected", True) if previous else True,
                      "original_actor": actor_key(item["original_url"]), "scope": "upstream_lead",
                      "date_status": "upstream_reported" if item["published_at"] else "unknown",
                      "report_hash": parsed["report_hash"], "report_path": config["report_path"],
                      "parent_item_id": previous.id if previous else None}
        db.add(DiscoveryItem(source_id=source.id, item_key=item["upstream_item_id"],
            checksum=digest({"payload_hash": item["payload_hash"], "parent": previous.id if previous else None}),
            url=item["original_url"], title=item["title"][:500], text="; ".join(item["terms"])[:2500],
            published_at=datetime.fromisoformat(item["published_at"]) if item["published_at"] else None,
            provenance_json=provenance))
        db.flush()
        saved += 1
    source.cursor_json = {"report_hash": parsed["report_hash"], "sync_cursor": parsed["report_hash"],
                          "imported_at": utcnow().isoformat(), "counts": parsed["counts"],
                          "issues": parsed["issues"], "partial": parsed["partial"], "unresolved": parsed["unresolved"],
                          "withdrawal_supported": False}
    source.last_error, source.failures = None, 0
    source.last_success_at = utcnow()
    source.next_due_at = utcnow() + timedelta(minutes=15)
    db.flush()
    return {"complete": True, "scanned": min(len(parsed["items"]), MAX_SYNC_ITEMS), "saved": saved,
            "scanned_unit": "url_items", "withdrawal_supported": False,
            "reason": "radar_item_budget" if budget_unexamined else "radar_partial" if parsed["partial"] else None,
            "partial": parsed["partial"],
            "counts": parsed["counts"], "issues": parsed["issues"], "report_hash": parsed["report_hash"],
            "coverage_scope": "configured_report_only"}


def sync_report(db, source):
    """Return terminal read failures without concealing them behind a previous success."""
    try:
        return _sync_report(db, source)
    except (ValueError, TypeError, KeyError, RecursionError) as exc:
        if not is_radar(source):
            raise ValueError("radar_source_required") from None
        code = str(exc) if re.fullmatch(r"radar_[a-z_]+", str(exc)) else "radar_report_invalid"
        source.last_error = code
        source.failures = (source.failures or 0) + 1
        source.next_due_at = utcnow() + timedelta(minutes=15)
        source.cursor_json = {**(source.cursor_json or {}), "partial": True, "last_attempt_error": code}
        db.flush()
        return {"complete": True, "scanned": 0, "saved": 0, "partial": True, "reason": code,
                "counts": None, "issues": [code], "coverage_scope": "configured_report_only"}


sync_page = sync_report
