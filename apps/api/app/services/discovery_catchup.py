"""Durable bounded collection receipts and the daily evidence prerequisite."""
from __future__ import annotations

import json
import time
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from itertools import pairwise
from urllib.parse import urljoin

import httpx
from sqlalchemy import or_, select, update

from ..models import (
    DiscoveryCatchupBatch as Batch,
)
from ..models import (
    DiscoveryCatchupSource as Receipt,
)
from ..models import (
    DiscoveryItem,
    DiscoverySource,
    PersonaSourceSubscription,
    SystemSetting,
    utcnow,
)
from .discovery_runtime import aware, digest, profile, settings
from .discovery_sources import lock_owner, selected_role_ids

OPEN = ("pending", "running")
REQUEST_LIMIT, ENTRY_LIMIT, WAIT_SECONDS = 10, 300, 900
SESSION = uuid.uuid4().hex


class CollectionWaiting(RuntimeError):
    pass


def iso(value):
    return aware(value).isoformat() if value else None


def cutoff(value=None):
    return aware(value or utcnow()).replace(second=0, microsecond=0)


def eligibility(db, source):
    if source.status == "merged":
        return [], "source_merged"
    if source.manually_paused:
        return [], "source_paused"
    if not source.processing_allowed:
        return [], "processing_not_allowed"
    if source.status != "active":
        return [], source.last_error or "source_unvalidated"
    retry_until = (source.cursor_json or {}).get("retry_until")
    if retry_until and aware(datetime.fromisoformat(retry_until)) > utcnow():
        return [], "aggregate_retry_wait"
    config = settings(db, source.owner_user_id)
    from .discovery_aggregation import accepts_source
    if not config["enabled"] or not config["public_processing_allowed"]:
        return [], "persona_paused"
    roles = []
    for sub in db.scalars(select(PersonaSourceSubscription).where(
        PersonaSourceSubscription.source_id == source.id,
        PersonaSourceSubscription.enabled.is_(True), PersonaSourceSubscription.manually_paused.is_(False))).all():
        current = profile(db, sub.persona_id)
        if (current and current[0].owner_user_id == source.owner_user_id and current[3] == sub.profile_hash
                and sub.persona_id not in config["paused_persona_ids"]
                and accepts_source(db, source.owner_user_id, sub.persona_id, source.id)):
            roles.append(sub.persona_id)
    return roles, None if roles else "no_eligible_subscription"


def receipt_json(receipt, source=None):
    return {"id": receipt.id, "batch_id": receipt.batch_id, "source_id": receipt.source_id,
            "name": source.name if source else None, "start_at": iso(receipt.start_at), "end_at": iso(receipt.end_at),
            "status": receipt.status, "reason": receipt.reason, "counts": receipt.counts_json,
            "coverage": receipt.coverage_json, "finished_at": iso(receipt.finished_at),
            "persona_ids": receipt.persona_ids_json}


def conclude(db, receipt, state, reason, *, evidence=None):
    receipt.status, receipt.reason, receipt.finished_at = state, reason, utcnow()
    receipt.coverage_json = {"complete": state == "covered", "basis": evidence or {},
        "unconfirmed_interval": None if state == "covered" else {
            "start_at": iso(receipt.start_at), "end_at": iso(receipt.end_at), "missing_count": None}}
    if reason in {"catchup_wait_budget", "catchup_source_budget"}:
        source = db.get(DiscoverySource, receipt.source_id)
        source.next_due_at = utcnow() + timedelta(hours=1)
    db.flush()
    batch = db.get(Batch, receipt.batch_id)
    unfinished = db.scalar(select(Receipt.id).where(Receipt.batch_id == batch.id, Receipt.status.in_(OPEN)).limit(1))
    if unfinished is None:
        states = db.scalars(select(Receipt.status).where(Receipt.batch_id == batch.id)).all()
        batch.status = "covered" if all(v == "covered" for v in states) else "partial"
        batch.finished_at = utcnow()


def request_source(db, source, target, *, reason="scheduled"):
    lock_owner(db, source.owner_user_id)
    reusable = db.scalar(select(Receipt).where(Receipt.source_id == source.id, Receipt.end_at >= target)
                         .order_by(Receipt.end_at, Receipt.id).limit(1))
    if reusable:
        roles, excluded = eligibility(db, source)
        if reusable.status == "excluded" and roles and not excluded and not reusable.counts_json.get("requests"):
            reusable.status, reusable.reason, reusable.finished_at = "pending", None, None
            reusable.persona_ids_json, reusable.coverage_json = roles, {}
            batch = db.get(Batch, reusable.batch_id)
            if batch.active_seconds >= WAIT_SECONDS:
                conclude(db, reusable, "partial", "catchup_wait_budget")
            else:
                batch.status, batch.finished_at = "pending", None
        return reusable
    latest = db.scalar(select(Receipt).where(Receipt.source_id == source.id)
                       .order_by(Receipt.end_at.desc(), Receipt.id.desc()).limit(1))
    batch = db.scalar(select(Batch).where(Batch.owner_user_id == source.owner_user_id, Batch.window_key == iso(target)))
    if batch is None:
        batch = Batch(owner_user_id=source.owner_user_id, window_key=iso(target), cutoff_at=target,
                      reason=reason, last_tick_at=utcnow())
        db.add(batch)
        db.flush()
    start = max(filter(None, [aware(source.last_success_at), aware(latest.end_at) if latest else None]), default=None)
    start = min(start, target) if start else None
    known = list(db.scalars(select(DiscoveryItem.item_key).where(DiscoveryItem.source_id == source.id)
                           .order_by(DiscoveryItem.collected_at.desc(), DiscoveryItem.id.desc()).limit(30)).all())
    roles, excluded = eligibility(db, source)
    receipt = Receipt(batch_id=batch.id, source_id=source.id, start_at=start, end_at=target,
        persona_ids_json=roles or selected_role_ids(db, source),
        progress_json={"next_url": (source.adapter_json or {}).get("url") or source.canonical_url,
                       "visited": [], "anchors": list(dict.fromkeys(known)), "seen": [], "ordered": True},
        counts_json={"requests": 0, "pages": 0, "scanned": 0, "new_versions": 0, "duplicates": 0})
    db.add(receipt)
    batch.status, batch.finished_at = "pending", None
    db.flush()
    if excluded:
        conclude(db, receipt, "excluded", excluded)
    elif batch.active_seconds >= WAIT_SECONDS:
        conclude(db, receipt, "partial", "catchup_wait_budget")
    return receipt


def scan(db, now=None):
    now = aware(now or utcnow())
    clock = db.get(SystemSetting, "discovery.catchup_clock")
    previous = (clock.value or {}) if clock else {}
    last = aware(datetime.fromisoformat(previous["last_scan_at"])) if previous.get("last_scan_at") else None
    same_session = previous.get("session") == SESSION
    monotonic_now = time.monotonic()
    active_elapsed = max(0, monotonic_now - previous.get("monotonic", monotonic_now)) if same_session else 0
    recovering = not same_session or last is None or (now - last).total_seconds() - active_elapsed > 180
    target = cutoff(now)
    if clock is None:
        clock = SystemSetting(key="discovery.catchup_clock")
        db.add(clock)
    clock.value = {"last_scan_at": iso(now), "session": SESSION, "monotonic": monotonic_now,
                   "recovery_cutoff_at": iso(target) if recovering else previous.get("recovery_cutoff_at")}
    for batch in db.scalars(select(Batch).where(Batch.status.in_(OPEN))).all():
        elapsed = (now - aware(batch.last_tick_at)).total_seconds()
        if elapsed >= 0 and not recovering:
            batch.active_seconds += min(elapsed, active_elapsed)
        batch.last_tick_at = now
        if batch.active_seconds >= WAIT_SECONDS:
            for receipt in db.scalars(select(Receipt).where(Receipt.batch_id == batch.id, Receipt.status.in_(OPEN))).all():
                conclude(db, receipt, "partial", "catchup_wait_budget")
    for source in db.scalars(select(DiscoverySource).where(DiscoverySource.status != "merged")).all():
        if not selected_role_ids(db, source):
            continue
        roles, _ = eligibility(db, source)
        if recovering or (roles and (source.next_due_at is None or aware(source.next_due_at) <= now)):
            pending = db.scalar(select(Receipt.id).where(Receipt.source_id == source.id, Receipt.status.in_(OPEN)).limit(1))
            if recovering or pending is None:
                request_source(db, source, target, reason="recovery" if recovering else "scheduled")
    db.commit()
    jobs, seen = [], set()
    for receipt in db.scalars(select(Receipt).where(Receipt.status.in_(OPEN)).order_by(Receipt.id)).all():
        source = db.get(DiscoverySource, receipt.source_id)
        if source.id in seen:
            continue
        seen.add(source.id)
        if not source.lease_until or aware(source.lease_until) <= now:
            jobs.append(receipt.id)
    return jobs[:100]


def _page(body, url, adapter):
    from .discovery_ingestion import _Page, parse_feed, parse_html, parse_json

    kind, next_url, complete, raw_count = adapter.get("kind"), None, False, None
    if kind == "rss":
        rows = parse_feed(body, url, limit=ENTRY_LIMIT + 1)
        root = ET.fromstring(body)
        raw_count = len(root.findall(".//item")) + len(root.findall(".//{http://www.w3.org/2005/Atom}entry"))
        links = [n for n in root.iter() if n.tag.rsplit("}", 1)[-1] == "link"]
        next_url = next((n.get("href") for n in links if n.get("rel") in {"next", "prev-archive"} and n.get("href")), None)
        complete = any(n.tag == "{http://purl.org/syndication/history/1.0}complete" for n in root.iter())
    elif kind == "json":
        rows = parse_json(body, url, adapter, limit=ENTRY_LIMIT + 1)
        data, path = json.loads(body), adapter.get("next_url_path")
        raw = data
        for key in filter(None, adapter.get("items_path", "").split(".")):
            raw = raw.get(key) if isinstance(raw, dict) else None
        raw_count = len(raw) if isinstance(raw, list) else None
        if isinstance(path, str) and len(path.split(".")) <= 4:
            for key in path.split("."):
                data = data.get(key) if isinstance(data, dict) else None
            next_url = data if isinstance(data, str) else None
    else:
        rows = parse_html(body, url, limit=ENTRY_LIMIT + 1)[1]
        class History(_Page):
            def handle_starttag(self, tag, attrs):
                super().handle_starttag(tag, attrs)
                data = dict(attrs)
                if tag in {"a", "link"} and "next" in data.get("rel", "").split() and data.get("href"):
                    self.next_url = data["href"]
        parser = History()
        parser.feed(body.decode("utf-8", errors="replace"))
        next_url = getattr(parser, "next_url", None)
    from .discovery_search import canonical_url
    return rows, canonical_url(urljoin(url, next_url)) if next_url else None, complete, raw_count if raw_count is not None else len(rows)


def step(db, receipt_id):
    from .discovery_ingestion import persist_items
    from .url_fetch import UnsafeUrlError, safe_fetch

    receipt = db.get(Receipt, receipt_id)
    if not receipt or receipt.status not in OPEN:
        return {"status": "already_concluded"}
    source = db.get(DiscoverySource, receipt.source_id)
    if db.scalar(select(Receipt.id).where(Receipt.source_id == source.id,
                  Receipt.id < receipt.id, Receipt.status.in_(OPEN)).limit(1)):
        return {"status": "waiting_previous_window"}
    roles, excluded = eligibility(db, source)
    if excluded:
        conclude(db, receipt, "excluded", excluded)
        db.commit()
        return {"status": "excluded"}
    now, token = utcnow(), uuid.uuid4().hex
    claimed = db.execute(update(DiscoverySource).where(DiscoverySource.id == source.id,
        or_(DiscoverySource.lease_until.is_(None), DiscoverySource.lease_until < now))
        .values(lease_token=token, lease_until=now + timedelta(minutes=8 if (source.adapter_json or {}).get("kind") == "radar" else 2)).execution_options(synchronize_session=False))
    if not claimed.rowcount:
        db.rollback()
        return {"status": "busy"}
    db.refresh(receipt)
    if receipt.status not in OPEN:
        source.lease_token, source.lease_until = None, None
        db.commit()
        return {"status": "already_concluded"}
    progress, counts = dict(receipt.progress_json), dict(receipt.counts_json)
    from .discovery_aggregation import is_aggregate, sync_page
    from .radar_discovery import is_radar, sync_report

    if counts["requests"] >= REQUEST_LIMIT or (not is_aggregate(source) and counts["scanned"] >= ENTRY_LIMIT):
        conclude(db, receipt, "partial", "catchup_source_budget")
        source.lease_token, source.lease_until = None, None
        db.commit()
        return {"status": "partial"}
    counts["requests"] += 1
    receipt.counts_json, receipt.status = counts, "running"
    db.commit()
    try:
        if is_aggregate(source) or is_radar(source):
            result = sync_report(db, source) if is_radar(source) else sync_page(db, source)
            db.refresh(receipt)
            db.refresh(source, attribute_names=["lease_token", "lease_until", "manually_paused", "processing_allowed"])
            roles, excluded = eligibility(db, source)
            if source.lease_token != token or aware(source.lease_until) <= utcnow() or excluded or receipt.status not in OPEN:
                db.rollback()
                return {"status": "lease_lost"}
            counts.update(pages=counts["pages"] + 1, scanned=counts["scanned"] + result["scanned"],
                          new_versions=counts["new_versions"] + result["saved"])
            receipt.counts_json = counts
            if result["complete"]:
                report_only = is_radar(source)
                conclude(db, receipt, "partial" if result.get("partial") or report_only else "covered",
                    result.get("reason") or ("radar_interval_unverified" if report_only else None),
                    evidence={"scope": result.get("coverage_scope", "upstream_selected_set"),
                              "ledger_cursor": source.cursor_json.get("sync_cursor"),
                              "issues": result.get("issues"), "counts": result.get("counts")})
            elif counts["requests"] >= REQUEST_LIMIT:
                conclude(db, receipt, "partial", "aggregate_sync_incomplete")
                source.next_due_at = utcnow() + timedelta(minutes=15)
            else:
                receipt.status = "pending"
            db.commit()
            return {"status": receipt.status, "receipt_id": receipt.id, "new_versions": result["saved"]}
        url, metadata = progress["next_url"], {}
        # Recovery needs the public list; a conditional response cannot reveal missing historical entries.
        body, _ = safe_fetch(url, response_metadata=metadata)
        db.refresh(receipt)
        db.refresh(source)
        if source.lease_token != token or aware(source.lease_until) <= utcnow() or receipt.status not in OPEN:
            return {"status": "lease_lost"}
        roles, excluded = eligibility(db, source)
        if excluded:
            conclude(db, receipt, "excluded", excluded)
            return {"status": "excluded"}
        if metadata.get("status") == 304:
            conclude(db, receipt, "partial", "catchup_unchanged_unverified")
            return {"status": "partial"}
        rows, next_url, complete, raw_count = _page(body, url, source.adapter_json or {})
        if not rows:
            raise ValueError("source_parse_empty")
        remaining = ENTRY_LIMIT - counts["scanned"]
        parse_incomplete = min(raw_count, ENTRY_LIMIT + 1) != len(rows)
        truncated, rows = raw_count > remaining, rows[:remaining]
        dates = [r["published_at"] for r in rows]
        previous_date = progress.get("last_date")
        ordered = (progress.get("ordered", True) and not parse_incomplete and all(dates)
                   and all(a >= b for a, b in pairwise(dates))
                   and (not previous_date or aware(datetime.fromisoformat(previous_date)) >= dates[0]))
        keys = [digest(r["url"]) for r in rows]
        seen = list(dict.fromkeys([*progress.get("seen", []), *keys]))
        anchors = set(progress.get("anchors", []))
        continuity = (len(anchors) >= 2 and anchors.issubset(set(seen)) and ordered
                      and receipt.start_at is not None and dates[-1] <= aware(receipt.start_at))
        saved = persist_items(db, source, rows, metadata=metadata if counts["pages"] == 0 else None)
        if counts["pages"] == 0:
            source.cursor_json = {**source.cursor_json, "head_keys": keys[:30], "checked_at": iso(now)}
        counts.update(pages=counts["pages"] + 1, scanned=counts["scanned"] + min(raw_count, remaining),
                      new_versions=counts["new_versions"] + saved, duplicates=counts["duplicates"] + len(rows) - saved)
        visited = [*progress.get("visited", []), url]
        progress.update(visited=visited, seen=seen, ordered=bool(ordered), last_date=iso(dates[-1]), next_url=next_url)
        receipt.progress_json, receipt.counts_json, receipt.persona_ids_json = progress, counts, roles
        if continuity and source.kind != "hotlist":
            conclude(db, receipt, "covered", None, evidence={"continuous_anchors": sorted(anchors), "endpoint": url})
        elif truncated:
            conclude(db, receipt, "partial", "catchup_source_budget")
        elif source.kind == "hotlist" and not complete:
            conclude(db, receipt, "partial", "catchup_hotlist_history_unknown")
        elif receipt.start_at is not None and ((complete and ordered) or continuity):
            conclude(db, receipt, "covered", None, evidence={"continuous_anchors": sorted(anchors) if continuity else [],
                     "declared_complete": complete, "endpoint": url})
        elif next_url and next_url not in visited and counts["requests"] < REQUEST_LIMIT and counts["scanned"] < ENTRY_LIMIT:
            receipt.status = "pending"
        else:
            reason = ("catchup_source_budget" if next_url and (counts["requests"] >= REQUEST_LIMIT or counts["scanned"] >= ENTRY_LIMIT)
                      else "catchup_pagination_loop" if next_url in visited
                      else "catchup_initial_history_unknown" if receipt.start_at is None
                      else "catchup_dates_unknown" if not ordered else "catchup_history_unavailable")
            conclude(db, receipt, "partial", reason)
        db.commit()
        return {"status": receipt.status, "receipt_id": receipt.id, "new_versions": saved}
    except (httpx.HTTPError, UnsafeUrlError, ValueError, TypeError, ET.ParseError) as exc:
        db.rollback()
        receipt = db.get(Receipt, receipt_id, populate_existing=True)
        source = db.get(DiscoverySource, receipt.source_id, populate_existing=True)
        if source.lease_token != token or receipt.status not in OPEN:
            return {"status": "lease_lost"}
        reason = ("credential_required" if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code in {401, 403}
                  else "catchup_http_failed" if isinstance(exc, httpx.HTTPStatusError)
                  else "catchup_timeout" if isinstance(exc, httpx.TimeoutException) or isinstance(exc, UnsafeUrlError) and "时限" in str(exc)
                  else "catchup_network_failed" if isinstance(exc, httpx.HTTPError)
                  else "catchup_unsafe_url" if isinstance(exc, UnsafeUrlError) else "catchup_parse_failed")
        if is_radar(source):
            reason = str(exc) if str(exc).startswith("radar_") and len(str(exc)) < 100 else "radar_report_unavailable"
        retry_after = exc.response.headers.get("Retry-After") if isinstance(exc, httpx.HTTPStatusError) else None
        if is_aggregate(source) and isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 429:
            reason = "aggregate_rate_limited"
        transient = isinstance(exc, httpx.TransportError) or (isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code >= 500)
        source.failures += 1
        source.last_error = reason
        if transient and not retry_after and receipt.counts_json["requests"] < 3:
            receipt.status, receipt.reason = "pending", reason
        else:
            conclude(db, receipt, "partial" if receipt.counts_json.get("pages") else "failed", reason,
                     evidence={"http_status": exc.response.status_code} if isinstance(exc, httpx.HTTPStatusError) else None)
            source.next_due_at = utcnow() + timedelta(minutes=min(1440, 15 * 2 ** min(source.failures, 6)))
            if retry_after:
                from .discovery_ingestion import source_date

                try:
                    source.next_due_at = (utcnow() + timedelta(seconds=max(0, int(retry_after)))) if retry_after.isdigit() else source_date(retry_after) or source.next_due_at
                except OverflowError:
                    pass
                source.cursor_json = {**(source.cursor_json or {}), "retry_until": iso(source.next_due_at)}
        db.commit()
        return {"status": receipt.status, "reason": reason}
    finally:
        source = db.get(DiscoverySource, receipt.source_id, populate_existing=True)
        if source.lease_token == token:
            source.lease_token, source.lease_until = None, None
            db.commit()


def collect_latest(db, source_id):
    source = db.get(DiscoverySource, source_id)
    if not source:
        return {"status": "paused"}
    receipt = request_source(db, source, cutoff())
    db.commit()
    return step(db, receipt.id)


def prerequisite(db, run, *, freeze=False):
    if run.kind not in {"daily", "bootstrap"}:
        return True
    data = dict(run.input_json or {})
    generation_started = any(k in (run.output_json or {}) for k in ("event_groups", "topic_candidates", "scores_a", "scores_b", "angle_comparison", "generation_summary"))
    if generation_started:
        if not data.get("collection_snapshot"):
            run.input_json = {**data, "collection_snapshot": {"status": "legacy_frozen", "sources": [],
                              "notice": "catchup_not_in_frozen_run", "frozen_at": iso(utcnow())}}
            db.commit()
        return True
    clock = db.get(SystemSetting, "discovery.catchup_clock")
    recovery = (clock.value or {}).get("recovery_cutoff_at") if clock else None
    target = max(cutoff(datetime.fromisoformat(data["collection_target_at"])) if data.get("collection_target_at") else cutoff(),
                 aware(datetime.fromisoformat(recovery)) if recovery else cutoff(run.created_at))
    old_snapshot = data.get("collection_snapshot")
    if old_snapshot and old_snapshot.get("target_at") != iso(target):
        for key in ("collection_snapshot", "base_evidence", "evidence", "evaluation_time", "previous_event_ids"):
            data.pop(key, None)
    data["collection_target_at"] = iso(target)
    receipts, waiting = [], False
    for source in db.scalars(select(DiscoverySource).where(DiscoverySource.owner_user_id == run.owner_user_id,
                                                          DiscoverySource.status != "merged")).all():
        from .discovery_aggregation import accepts_source

        if not accepts_source(db, run.owner_user_id, run.persona_id, source.id):
            continue
        if run.persona_id not in selected_role_ids(db, source):
            continue
        receipt = request_source(db, source, target, reason="daily_prerequisite")
        roles, excluded = eligibility(db, source)
        if run.persona_id not in roles:
            excluded = excluded or "no_eligible_subscription"
        view = receipt_json(receipt, source)
        view["persona_ids"] = sorted(set(view["persona_ids"]) | {run.persona_id})
        if excluded:
            view = {**view, "status": "excluded", "reason": excluded}
        gap = db.scalar(select(Receipt).where(Receipt.source_id == source.id, Receipt.id != receipt.id,
            Receipt.status.in_(["partial", "failed"])).order_by(Receipt.id.desc()).limit(1))
        view["earlier_gap"] = receipt_json(gap, source) if gap else None
        receipts.append(view)
        waiting = waiting or (not excluded and receipt.status in OPEN)
        if not excluded and db.scalar(select(Receipt.id).where(Receipt.source_id == source.id, Receipt.end_at < target,
                                              Receipt.status.in_(OPEN)).limit(1)):
            waiting = True
    if old_snapshot and {r["source_id"] for r in old_snapshot.get("sources", [])} != {r["source_id"] for r in receipts}:
        for key in ("collection_snapshot", "base_evidence", "evidence", "evaluation_time", "previous_event_ids"):
            data.pop(key, None)
    run.input_json = data
    if waiting:
        run.status, run.reason = "waiting_collection", "waiting_collection"
    elif freeze:
        run.input_json = {**data, "collection_snapshot": {
            "status": "partial" if any(r["status"] != "covered" or r.get("earlier_gap") for r in receipts) else "covered",
            "target_at": iso(target), "frozen_at": iso(utcnow()), "sources": receipts}}
    db.commit()
    return not waiting


def source_projection(db, source):
    receipt = db.scalar(select(Receipt).where(Receipt.source_id == source.id).order_by(Receipt.id.desc()).limit(1))
    gap = db.scalar(select(Receipt).where(Receipt.source_id == source.id, Receipt.status.in_(["partial", "failed"]))
                    .order_by(Receipt.id.desc()).limit(1))
    return {"latest": receipt_json(receipt, source) if receipt else None, "last_gap": receipt_json(gap, source) if gap else None}


def owner_projection(db, owner_id, persona_id=None):
    receipts = db.scalars(select(Receipt).join(DiscoverySource, DiscoverySource.id == Receipt.source_id)
        .where(DiscoverySource.owner_user_id == owner_id).order_by(Receipt.id.desc()).limit(500)).all()
    latest = {}
    for receipt in receipts:
        if persona_id is None or persona_id in receipt.persona_ids_json:
            latest.setdefault(receipt.source_id, receipt)
    result = []
    for r in latest.values():
        source = db.get(DiscoverySource, r.source_id)
        view = receipt_json(r, source)
        view["persona_ids"] = selected_role_ids(db, source)
        gap = db.scalar(select(Receipt).where(Receipt.source_id == r.source_id, Receipt.id != r.id,
            Receipt.status.in_(["partial", "failed"])).order_by(Receipt.id.desc()).limit(1))
        view["earlier_gap"] = receipt_json(gap, source) if gap else None
        result.append(view)
    return result


def later_catchup_notice(db, run):
    snapshot = (run.input_json or {}).get("collection_snapshot")
    if not snapshot:
        return None
    clock = db.get(SystemSetting, "discovery.catchup_clock")
    recovered = (clock.value or {}).get("recovery_cutoff_at") if clock else None
    if recovered and aware(datetime.fromisoformat(recovered)) > aware(datetime.fromisoformat(snapshot["frozen_at"])):
        return "catchup_not_in_frozen_run"
    return snapshot.get("notice")
