"""Grounded Persona angles, independent evaluation and atomic opportunity publication."""

import difflib
import json
import math
import re
import unicodedata
from datetime import datetime, timedelta
from types import SimpleNamespace

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from ..models import (
    ContentOpportunity,
    ContentOpportunityAssessmentRevision,
    ContentOpportunitySignal,
    DiscoveryEvent,
    DiscoveryItem,
    DiscoverySource,
    PersonaResearchRun,
    PersonaSourceSubscription,
    User,
    utcnow,
)
from .discovery_runtime import DiscoveryBlocked, aware, check_current, checkpoint, claim, digest, model_json
from .opportunity_policy import TECH, diagnostic, freeze_policy

WEIGHTS = {"role_fit": .30, "audience_value": .25, "evidence_quality": .20, "angle_novelty": .15, "timeliness": .10}


def _evidence(db, run):
    from sqlalchemy.orm import aliased

    from .discovery_aggregation import allowed_source_ids
    from .radar_discovery import source_id_for as radar_source_id_for

    selected_sources = allowed_source_ids(db, run.owner_user_id, run.persona_id)
    radar_id = radar_source_id_for(db, run.owner_user_id, run.persona_id)
    snapshot_at = datetime.fromisoformat((run.input_json.get("collection_snapshot") or {}).get("frozen_at") or utcnow().isoformat())
    version = aliased(DiscoveryItem)
    latest_id = select(func.max(version.id)).where(version.source_id == DiscoveryItem.source_id,
        version.item_key == DiscoveryItem.item_key, version.collected_at <= snapshot_at).correlate(DiscoveryItem).scalar_subquery()
    stmt = select(DiscoveryItem, DiscoverySource).join(DiscoverySource,
        DiscoverySource.id == DiscoveryItem.source_id).join(PersonaSourceSubscription,
        PersonaSourceSubscription.source_id == DiscoverySource.id).where(
        PersonaSourceSubscription.persona_id == run.persona_id, PersonaSourceSubscription.enabled.is_(True),
        PersonaSourceSubscription.manually_paused.is_(False), PersonaSourceSubscription.profile_hash == run.profile_hash,
        DiscoverySource.owner_user_id == run.owner_user_id, DiscoverySource.status == "active",
        DiscoverySource.processing_allowed.is_(True), DiscoverySource.manually_paused.is_(False),
        (DiscoverySource.adapter_json["kind"].as_string().is_distinct_from("radar")) | DiscoverySource.last_error.is_(None),
        (DiscoverySource.adapter_json["kind"].as_string().is_distinct_from("radar")) | (DiscoverySource.id == radar_id),
        DiscoverySource.id.in_(selected_sources) if selected_sources is not None else True,
        DiscoveryItem.id == latest_id,
        DiscoveryItem.provenance_json["selected"].as_boolean().is_not(False),
        DiscoveryItem.collected_at <= datetime.fromisoformat((run.input_json.get("collection_snapshot") or {}).get("frozen_at") or utcnow().isoformat()),
        (DiscoveryItem.published_at.is_(None)) | (DiscoveryItem.published_at <= utcnow()),
    ).order_by(DiscoveryItem.published_at.desc(), DiscoveryItem.collected_at.desc(), DiscoveryItem.id.desc())
    if selected_sources is None:
        rows = db.execute(stmt.limit(150)).all()
    else:
        rows = [row for source_id in sorted(selected_sources)
                for row in db.execute(stmt.where(DiscoverySource.id == source_id).limit(40)).all()]
    groups = {}
    for row in rows:
        groups.setdefault(row[1].id, []).append(row)
    selected = []
    while any(groups.values()) and len(selected) < 40:
        for group in groups.values():
            if group and len(selected) < 40:
                selected.append(group.pop(0))
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
    return selected, total


def _ref(item, source):
    from .discovery_aggregation import reference

    return {**reference(item, source),"item_id": item.id, "source_id": source.id, "checksum": item.checksum,
            "url": item.url, "title": item.title, "excerpt": item.text[:180], "actor": (item.provenance_json or {}).get("original_actor") or source.actor_key,
            "published_at": aware(item.published_at).isoformat() if item.published_at else None,
            "discovery_paths": [{"item_id": item.id, "source_id": source.id, "checksum": item.checksum}]}



def _article_ref(item, source):
    import httpx

    from .discovery_ingestion import article_evidence
    from .url_fetch import UnsafeUrlError

    try:
        from .discovery_aggregation import article as aggregate_article
        from .discovery_aggregation import is_aggregate

        article = aggregate_article(item, source) if is_aggregate(source) else article_evidence(item.url)
        if not is_aggregate(source):
            from .discovery_aggregation import actor_key

            resolved = article.pop("resolved_url", item.url)
            article = {**article, "url": resolved, "actor": actor_key(resolved)}
    except (UnsafeUrlError, httpx.HTTPError, ValueError, TypeError) as exc:
        return {"item_id": item.id, "article_error": type(exc).__name__}
    return {**_ref(item, source), **article, "body": article["body"][:5000],
            "body_checksum": digest(article["body"][:5000])}


def _quoted(ref, quote):
    return isinstance(quote, str) and len(quote.strip()) >= 12 and quote.strip() in ref.get("body", "")


def _date_proof(ref, value, quote):
    from .discovery_ingestion import source_date

    when = source_date(value)
    if not when or not isinstance(quote, str) or len(quote.strip()) < 8 or quote.strip() not in ref.get("body", ""):
        return None
    # A quoted claim alone cannot establish when it happened.
    y, m, d = when.year, when.month, when.day
    numeric = re.search(rf"{y}[-/.年]0?{m}[-/.月]0?{d}(?:日|\b)", quote)
    month = when.strftime("%B")
    english = re.search(rf"(?:{month}|{month[:3]})\.?\s+{d}(?:st|nd|rd|th)?(?:,|\s)+\s*{y}", quote, re.IGNORECASE)
    reverse = re.search(rf"\b{d}\s+(?:{month}|{month[:3]})\.?\s+{y}\b", quote, re.IGNORECASE)
    return when.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() if numeric or english or reverse else None


def _ground_candidate(candidate, event, at, *, policy="discovery.v2", reasons=None):
    def reject(reason):
        if reasons is not None:
            reasons.append(reason)

    timelines = candidate.get("timeline")
    if not isinstance(timelines, list):
        return reject("timeline_missing")
    by_id = {r["item_id"]: r for r in event.evidence_json}
    verified = []
    for row in timelines[:8]:
        if not isinstance(row, dict):
            continue
        ref = by_id.get(row.get("item_id"))
        if not ref or not ref.get("body_checksum") or not _quoted(ref, row.get("supporting_quote")):
            continue
        dates = {key: _date_proof(ref, row.get(key), row.get(key + "_quote"))
                 for key in ("original_published_at", "republished_at", "event_at")}
        event_quote = row.get("event_at_quote")
        if dates["event_at"] and isinstance(event_quote, str):
            normalized = re.sub(r"\s+", " ", event_quote).strip().casefold()
            publication_quotes = {re.sub(r"\s+", " ", str(row.get(key) or "")).strip().casefold()
                                  for key in ("original_published_at_quote", "republished_at_quote")}
            when = datetime.fromisoformat(dates["event_at"])
            month = when.strftime("%B")
            date_pattern = (rf"{when.year}[-/.年]0?{when.month}[-/.月]0?{when.day}(?:日|\b)"
                            rf"|(?:{month}|{month[:3]})\.?\s+{when.day}(?:st|nd|rd|th)?(?:,|\s)+\s*{when.year}"
                            rf"|\b{when.day}\s+(?:{month}|{month[:3]})\.?\s+{when.year}\b")
            context = re.sub(date_pattern, "", normalized, flags=re.IGNORECASE)
            context = re.sub(r"t\d{2}:\d{2}(?::\d{2})?(?:z|[+-]\d{2}:\d{2})?", "", context)
            # A dated publication label proves reporting time, not a substantive event.
            if (normalized in publication_quotes or not re.search(r"[a-z\u4e00-\u9fff]", context)
                    or re.fullmatch(r"(?:published|posted|updated|modified|datepublished|datemodified|发布时间|发布日期|更新日期|更新时间|发表于)"
                                    r"(?:\s+(?:on|at))?\s*[:：]?\s*(?:" + date_pattern + ")", normalized, re.IGNORECASE)):
                dates["event_at"] = None
        if any(v and aware(datetime.fromisoformat(v)) > at for v in dates.values()):
            continue
        verified.append({"item_id": ref["item_id"], "supporting_quote": row["supporting_quote"], **dates,
                         "date_quotes": {key: row.get(key + "_quote") for key, value in dates.items() if value},
                         "page_dates": ref.get("page_dates", {}), "feed_published_at": ref.get("published_at")})
    if not verified:
        return reject("supporting_evidence_missing")
    classification = candidate.get("classification")
    if not isinstance(classification, str) or classification not in {"hot", "recent_report", "evergreen"}:
        return reject("classification_invalid")
    recent_event = any(v["event_at"] and 0 <= (
        at - aware(datetime.fromisoformat(v["event_at"]))).total_seconds() <= 48 * 3600 for v in verified)
    recent_hours = 30 * 24 if policy == TECH else 48
    recent_original = any(v[key] and 0 <= (
        at - aware(datetime.fromisoformat(v[key]))).total_seconds() <= recent_hours * 3600
        for v in verified for key in (("original_published_at", "event_at") if policy == TECH else ("original_published_at",)))
    if classification == "hot" and not recent_event:
        if not recent_original:
            return reject("recent_date_unverified_or_outside_window")
        classification = "recent_report"
    if classification == "recent_report" and not recent_original:
        return reject("recent_date_unverified_or_outside_window")
    if policy == TECH and classification == "evergreen" and (
            not isinstance(candidate.get("lasting_value"), str) or not candidate["lasting_value"].strip()):
        return reject("lasting_value_missing")
    # Only quoted body-bearing references may support the published opportunity.
    ids = {v["item_id"] for v in verified}
    return {**candidate, "timeline": verified, "classification": classification,
            "evergreen": classification == "evergreen", "verified_item_ids": sorted(ids)}


def _model_refs(refs):
    return [{k: v for k, v in ref.items() if k not in {"body", "body_checksum", "body_fetched_at", "upstream"}}
            for ref in refs]


def _collect_articles(db, run):
    # Keep the shared request bucket available for two independent evaluations.
    rows, total = _evidence(db, run)
    groups = {}
    for row in rows:
        groups.setdefault(row[1].id, []).append(row)
    ordered = []
    while any(groups.values()):
        for group in groups.values():
            if group:
                ordered.append(group.pop(0))
    refs, errors, size, examined, fetched = [], [], 0, 0, 0
    cached = {}
    for row in ordered[:20]:
        examined += 1
        item, source = row
        if item.url in cached:
            cached[item.url]["discovery_paths"].extend(_ref(item, source)["discovery_paths"])
            continue
        ref = _article_ref(*row)
        if ref.get("article_error"):
            errors.append(ref)
            continue
        fetched += 1
        original_url = ref.get("url", item.url)
        if original_url in cached:
            cached[original_url]["discovery_paths"].extend(ref["discovery_paths"])
            continue
        # Retain a bounded literal passage; hash identifies exactly the frozen text.
        ref["body"] = ref["body"].encode()[:1800].decode("utf-8", errors="ignore")
        ref["body_checksum"] = digest(ref["body"])
        ref["excerpt"] = ref["body"]
        nbytes = len(json.dumps(_model_refs([ref]), ensure_ascii=False).encode())
        if size + nbytes > 12000:
            examined -= 1
            break
        refs.append(ref)
        cached[item.url] = ref
        cached[original_url] = ref
        size += nbytes
    run.input_json = {**run.input_json, "article_read_errors": errors}
    db.commit()
    diagnostic(db, run, counts={"eligible_items": total, "body_reads_succeeded": fetched,
                               "body_reads_failed": len(errors),
                               "budget_unexamined_items": total - examined})
    return refs


def _events(db, run, evidence):
    if "previous_event_ids" not in run.input_json:
        old_events = db.scalars(select(DiscoveryEvent).where(DiscoveryEvent.owner_user_id == run.owner_user_id,
            DiscoveryEvent.created_at >= utcnow() - timedelta(days=14)).order_by(DiscoveryEvent.id.desc()).limit(40)).all()
        allowed = {ref["source_id"] for ref in evidence}
        old_events = [e for e in old_events if all(ref["source_id"] in allowed and (not ref.get("published_at") or aware(datetime.fromisoformat(ref["published_at"])) <= utcnow()) for ref in e.evidence_json)
                      and any(difflib.SequenceMatcher(None, old["title"].casefold(), new["title"].casefold()).ratio() >= .35
                              for old in e.evidence_json for new in evidence)][:10]
        run.input_json = {**run.input_json, "previous_event_ids": [e.id for e in old_events],
                         "evidence": list({r["item_id"]: r for r in evidence + [r for e in old_events for r in e.evidence_json]}.values())}
        db.commit()
    else:
        old_events = [db.get(DiscoveryEvent, i) for i in run.input_json["previous_event_ids"]]
    check_current(db, run, provider=True)
    grouped = model_json(db, run, "event_groups", (
        'Return {"events":[{"item_ids":[integer],"same_event_evidence":string,"prior_event_id":integer|null,'
        '"material_progress":boolean,"progress_evidence":string}]}. Group only definitely identical events; '
        'uncertain items stay separate. Match prior events only with concrete evidence. New sources or retitled '
        'copies are NOT material progress. Only substantive new developments justify a new version. '
        'For old or undated evidence do not assert it occurred today. At most ten relevant groups.'),
        {"persona": run.input_json["profile"], "evidence": _model_refs(evidence),
         "previous_events": [{"id": e.id, "evidence": [{"item_id": r["item_id"], "title": r["title"], "url": r["url"]} for r in e.evidence_json]} for e in old_events]}, max_tokens=1800)
    by_id = {r["item_id"]: r for r in evidence}
    old_by_id = {e.id: e for e in old_events}
    result = []
    for group in grouped.get("events", [])[:10]:
        if not isinstance(group, dict) or not isinstance(group.get("item_ids"), list):
            continue
        ids = list(dict.fromkeys(i for i in group["item_ids"] if type(i) is int and i in by_id))[:8]
        if not ids or (len(ids) > 1 and not group.get("same_event_evidence")):
            continue
        refs = [by_id[i] for i in ids]
        previous = old_by_id.get(group.get("prior_event_id"))
        if previous is None:
            previous = next((e for e in old_events if {x["url"] for x in e.evidence_json} & {x["url"] for x in refs}), None)
        event_key = previous.event_key if previous else digest(min(r["url"] for r in refs))
        latest = db.scalar(select(DiscoveryEvent).where(DiscoveryEvent.owner_user_id == run.owner_user_id,
            DiscoveryEvent.event_key == event_key).order_by(DiscoveryEvent.version.desc()).limit(1))
        if latest and not {r["item_id"] for r in latest.evidence_json}.issubset({r["item_id"] for r in run.input_json["evidence"]}):
            continue
        if latest and not (group.get("material_progress") is True and group.get("progress_evidence")
                           and {r["checksum"] for r in refs} - {r["checksum"] for r in latest.evidence_json}):
            result.append(latest)
            continue
        version = latest.version + 1 if latest else 1
        actors = {}
        for ref in refs:
            when = aware(datetime.fromisoformat(ref["published_at"])) if ref["published_at"] else None
            if when:
                age = (utcnow() - when).total_seconds() / 3600
                if 0 <= age <= 48:
                    actors[ref["actor"]] = max(actors.get(ref["actor"], 0), 2 ** (-age / 24))
        event = DiscoveryEvent(owner_user_id=run.owner_user_id, event_key=event_key, version=version,
            evidence_json=refs, actors_json=sorted(actors), heat=sum(actors.values()))
        try:
            with db.begin_nested():
                db.add(event)
                db.flush()
        except IntegrityError:
            event = db.scalar(select(DiscoveryEvent).where(DiscoveryEvent.owner_user_id == run.owner_user_id,
                DiscoveryEvent.event_key == event_key, DiscoveryEvent.version == version))
        result.append(event)
    db.commit()
    return list({event.id: event for event in result}.values())


def observed_heat(event, *, at=None):
    at = at or utcnow()
    actors = {}
    for ref in event.evidence_json:
        when = datetime.fromisoformat(ref["published_at"]) if ref.get("published_at") else None
        if when:
            age = (at - aware(when)).total_seconds() / 3600
            if 0 <= age <= 48:
                actors[ref["actor"]] = max(actors.get(ref["actor"], 0), 2 ** (-age / 24))
    return {"tracked_heat": sum(actors.values()), "independent_actors": len(actors)}


def _score(row):
    if not isinstance(row, dict) or row.get("grounded") is not True or not isinstance(row.get("reasons"), str) or not row["reasons"]:
        return None
    total = 0
    for key, weight in WEIGHTS.items():
        value = row.get(key)
        if type(value) not in {int, float} or not math.isfinite(value) or not 0 <= value <= 100:
            return None
        total += value * weight
    return total


def generate_daily(db, run):
    from .discovery_catchup import CollectionWaiting, prerequisite

    if not prerequisite(db, run, freeze=True):
        raise CollectionWaiting()

    from .opportunities import audit, persist_system_assessment

    config = check_current(db, run, provider=True)
    completed = (run.output_json or {}).get("generation_summary")
    if isinstance(completed, dict) and "count" in completed:
        return completed
    policy = freeze_policy(db, run)
    existing_ids = list(db.scalars(select(ContentOpportunity.id).where(ContentOpportunity.research_run_id == run.id)).all())
    if existing_ids:
        return {"count": len(existing_ids), "opportunity_ids": existing_ids, "coverage": "partial",
                "reason": "recovered_committed_outputs"}
    generated_today = db.scalar(select(func.count(ContentOpportunity.id)).where(
        ContentOpportunity.owner_user_id == run.owner_user_id, ContentOpportunity.persona_id == run.persona_id,
        ContentOpportunity.business_date == run.business_date, ContentOpportunity.research_run_id.is_not(None)))
    remaining = max(0, min(5, config["daily_limit"]) - generated_today)
    if not remaining:
        diagnostic(db, run, counts={"persisted_opportunities": 0}, rejections=[
            {"stage": "selection", "reason": "daily_limit_reached"}])
        result = {"count": 0, "opportunity_ids": [], "coverage": "succeeded", "reason": "daily_limit_reached"}
        checkpoint(db, run, "generation_summary", result)
        return result
    refs = (run.input_json or {}).get("base_evidence")
    if refs is None:
        refs = _collect_articles(db, run)
        from .discovery_aggregation import source_id_for

        if not refs and run.kind == "daily" and source_id_for(db, run.owner_user_id, run.persona_id) is None:
            from .discovery_search import available
            from .source_discovery import research_sources

            if available(config["search_provider"], config["credential_source"]):
                research_sources(db, run)
                run.input_json = {k: v for k, v in run.input_json.items() if k != "collection_snapshot"}
                db.commit()
                if not prerequisite(db, run, freeze=True):
                    raise CollectionWaiting()
                refs = _collect_articles(db, run)
    refs = [r for r in refs if r.get("body_checksum") and r.get("body")]
    if not refs:
        diagnostic(db, run, counts={"persisted_opportunities": 0})
        return {"count": 0, "reason": "article_read_incomplete" if run.input_json.get("article_read_errors") else "no_usable_article_body",
                "coverage": "partial" if run.input_json.get("article_read_errors") else "succeeded"}
    run.input_json = {**run.input_json, "base_evidence": refs, "evidence": run.input_json.get("evidence", refs)}
    db.commit()
    if "evaluation_time" not in run.input_json:
        run.input_json = {**run.input_json, "evaluation_time": utcnow().isoformat()}
        db.commit()
    evaluation_now = datetime.fromisoformat(run.input_json["evaluation_time"])
    if "event_ids" in run.input_json:
        events = [db.get(DiscoveryEvent, i) for i in run.input_json["event_ids"]]
    else:
        events = _events(db, run, refs)
        run.input_json = {**run.input_json, "event_ids": [e.id for e in events]}
        db.commit()
    check_current(db, run, provider=True)
    if not events:
        diagnostic(db, run, counts={"persisted_opportunities": 0})
        return {"count": 0, "reason": "no_suitable_events",
                "coverage": "partial" if run.input_json.get("article_read_errors") else "succeeded"}
    current_refs = {r["item_id"]: r for r in refs}
    events = [SimpleNamespace(id=e.id, event_key=e.event_key, version=e.version,
        evidence_json=[current_refs[r["item_id"]] for r in e.evidence_json if r["item_id"] in current_refs]) for e in events]
    events = [e for e in events if e.evidence_json]
    event_map = {e.id: e for e in events}
    policy_instruction = (
        'Technology policy: hot needs a verified substantive event within 48 hours; recent_report permits '
        'verified original reporting or substantive progress within 30 days. Older/undated sources may support '
        'evergreen only with an explicit lasting_value explanation. Do not simply discard non-breaking engineering topics. '
        'Include lasting_value:string for evergreen. Never turn old prices, API versions or availability into current facts: '
        'remove unsupported current claims or defer the topic. Age is not a standalone relevance failure. '
    ) if policy == TECH else ''
    proposed = model_json(db, run, "topic_candidates", (policy_instruction +
        'Return {"candidates":[{"event_id":integer,"title":string,"summary":string,"angle":string,'
        '"why_now":string,"audience_value":string,"role_fit":string,"gaps":[string],'
        '"formats":["text"|"graphic"|"video"],"evergreen":boolean,"expiry_hours":integer,'
        '"classification":"hot"|"recent_report"|"evergreen","timeline":[{"item_id":integer,"supporting_quote":string,'
        '"original_published_at":string|null,"original_published_at_quote":string|null,"republished_at":string|null,'
        '"republished_at_quote":string|null,"event_at":string|null,"event_at_quote":string|null}]}]}. '
        'At most ten grounded Persona-specific opportunities. Use ONLY supplied literal body passages. '
        'Upstream summaries, headlines, link labels and model knowledge are discovery leads, not proof of facts. '
        'Every factual clause in title and summary must be supported by these passages; mark unread details as gaps. '
        'No invented experience, tests, benchmark results or hype. Never infer market trends, demand growth, incident frequency or popularity from publication dates or a single article. Distinguish evergreen from news '
        'using real dates. Quotes MUST be verbatim body passages, dates ISO with absolute date quotes including year. '
        'Unknown dates stay null; page/feed/translation/update dates alone do not prove event dates. '
        'Read bylines and source attribution in the literal passage: if the named publisher differs from the hosting '
        'publication, the current page date proves republication only, not the original publication date. '
        'Leave the original date null unless the passage explicitly dates that original source. '
        'hot requires a recent dated substantive development; recent_report is recent reporting on an older/undated event, '
        'evergreen is a lasting question. Distinguish author opinion, product promotion and independent evidence. '
        'Consolidate equivalent editorial questions across different articles into a single candidate with all evidence. Heat is only observed within tracked sources. Do not fill quotas.'),
        {"persona": run.input_json["profile"], "now": evaluation_now.isoformat(),
         "events": [{"event_id": e.id, "version": e.version, "evidence": _model_refs(e.evidence_json),
                     **observed_heat(e, at=evaluation_now)} for e in events]}, max_tokens=2600)
    candidates, rejections = [], []
    proposed_rows = proposed.get("candidates", [])
    if not isinstance(proposed_rows, list):
        raise DiscoveryBlocked("candidate_response_invalid")
    for candidate_id, candidate in enumerate(proposed_rows[:10]):
        def reject_candidate(reason, candidate=candidate, candidate_id=candidate_id):
            rejections.append({"candidate_id": candidate_id,
                               "title": str(candidate.get("title", ""))[:300] if isinstance(candidate, dict) else "",
                               "stage": "evidence", "reason": reason})
        if not isinstance(candidate, dict) or type(candidate.get("event_id")) is not int or candidate["event_id"] not in event_map:
            reject_candidate("candidate_schema_invalid")
            continue
        if not all(isinstance(candidate.get(k), str) and candidate[k].strip()
                   for k in ("title", "summary", "angle", "why_now", "audience_value", "role_fit")):
            reject_candidate("candidate_schema_invalid")
            continue
        candidate = {**candidate, "candidate_id": candidate_id}
        event = event_map[candidate["event_id"]]
        if any(r.get("published_at") and aware(datetime.fromisoformat(r["published_at"])) > evaluation_now for r in event.evidence_json):
            reject_candidate("future_source_date")
            continue
        reasons = []
        grounded = _ground_candidate(candidate, event, evaluation_now, policy=policy, reasons=reasons)
        if grounded:
            candidates.append(grounded)
        else:
            reject_candidate(reasons[0])
    diagnostic(db, run, counts={"proposed_candidates": min(10, len(proposed_rows)),
                               "pre_score_rejected": len(rejections), "scored_candidates": 0,
                               "persisted_opportunities": 0}, rejections=rejections)
    if not candidates:
        return {"count": 0, "opportunity_ids": [], "reason": "no_grounded_candidates",
                "coverage": "partial" if run.input_json.get("article_read_errors") else "succeeded"}
    scoring_instruction = (policy_instruction + 'Return {"scores":[{"candidate_id":integer,"role_fit":number,"audience_value":number,'
        '"evidence_quality":number,"angle_novelty":number,"timeliness":number,"grounded":boolean,"reasons":string}]}. '
        'Score each dimension 0..100 independently. Reject unsupported claims or invented experience. '
        'Use supplied Persona and frozen literal body passages only; return all candidate IDs. '
        'Check EVERY factual clause in title and summary. A source reputation, headline, link label, '
        'upstream summary or unread remainder cannot prove a claim. '
        'If any material detail lacks support in the supplied passages, set grounded=false and explain the gap. '
        'Evidence quality below 70 rejects a candidate regardless of other scores. Opinion is not verified industry fact; '
        'advertising is not independent review. For evergreen, timeliness measures lasting value, not breaking-news freshness. '
        'Check timeline date roles against the byline and source attribution as well: a syndicating page date '
        'cannot establish original publication. If dates mislabel republication as original, set grounded=false. '
        'For hot use verified event date; republication never refreshes an event. Quotes must support title and summary.')
    score_data = {"evaluation_time": evaluation_now.isoformat(), "persona": run.input_json["profile"], "candidates": candidates,
                  "events": [{"id": e.id, "evidence": _model_refs(e.evidence_json)} for e in events]}
    diagnostic(db, run, counts={"scored_candidates": len(candidates)})
    first = model_json(db, run, "scores_a", scoring_instruction, score_data)
    second = model_json(db, run, "scores_b", scoring_instruction, score_data)
    a = {r.get("candidate_id"): r for r in first.get("scores", []) if isinstance(r, dict)}
    b = {r.get("candidate_id"): r for r in second.get("scores", []) if isinstance(r, dict)}
    prior = db.execute(select(ContentOpportunity, ContentOpportunityAssessmentRevision).join(
        ContentOpportunityAssessmentRevision, ContentOpportunityAssessmentRevision.opportunity_id == ContentOpportunity.id
    ).where(ContentOpportunity.owner_user_id == run.owner_user_id, ContentOpportunity.persona_id == run.persona_id,
            ContentOpportunity.event_key.in_([f"{e.event_key}:{e.version}" for e in events]))) .all()
    comparison = model_json(db, run, "angle_comparison", (
        'Return {"duplicates":[{"candidate_id":integer,"opportunity_id":integer}],'
        '"batch_duplicates":[{"candidate_id":integer,"keep_candidate_id":integer}]}. '
        'Identify equivalent editorial questions even across different article/event IDs. '
        'Prior dismissed/archived/converted topics remain duplicates for the same event. '
        'Consolidate current batch same-question candidates into the earlier candidate ID; '
        'distinct questions such as deterministic tooling versus Eval stay separate.'),
        {"candidates": candidates, "prior": [{"id": p.id, "event_key": p.event_key,
            "angle": v.assessment_json.get("suggested_angle")} for p, v in prior]})
    duplicates = {v["candidate_id"] for v in comparison.get("duplicates", []) if isinstance(v, dict)
                  and v.get("opportunity_id") in {p.id for p, _ in prior} and type(v.get("candidate_id")) is int}
    by_id = {c["candidate_id"]: c for c in candidates}
    passing = {c["candidate_id"] for c in candidates
               if (x := _score(a.get(c["candidate_id"]))) is not None
               and (y := _score(b.get(c["candidate_id"]))) is not None
               and (x + y) / 2 >= 70 and a[c["candidate_id"]]["evidence_quality"] >= 70
               and b[c["candidate_id"]]["evidence_quality"] >= 70}
    merge_parent = {}
    for row in comparison.get("batch_duplicates", []):
        if not isinstance(row, dict):
            continue
        drop, keep = row.get("candidate_id"), row.get("keep_candidate_id")
        if type(drop) is int and type(keep) is int and drop in passing and keep in passing and keep < drop:
            duplicates.add(drop)
            merge_parent[drop] = keep
    for drop, keep in merge_parent.items():
        while keep in merge_parent:
            keep = merge_parent[keep]
        by_id[keep].setdefault("merged_candidate_ids", []).append(drop)
    approved = []
    for candidate in candidates:
        i = candidate["candidate_id"]
        x, y = _score(a.get(i)), _score(b.get(i))
        if i not in duplicates and x is not None and y is not None and (x + y) / 2 >= 70 and a[i]["evidence_quality"] >= 70 and b[i]["evidence_quality"] >= 70:
            approved.append(((x + y) / 2, candidate))
    approved.sort(key=lambda r: (-r[0], r[1]["candidate_id"]))
    for c in candidates:
        reason = "score_below_threshold_or_ungrounded" if c["candidate_id"] not in passing else (
            "duplicate_topic" if c["candidate_id"] in duplicates else None)
        if reason:
            rejections.append({"candidate_id": c["candidate_id"], "title": c["title"][:300],
                               "stage": "score" if c["candidate_id"] not in passing else "selection", "reason": reason})
    diagnostic(db, run, counts={"score_rejected": len(candidates) - len(passing),
                               "deduplicated_candidates": len(passing & duplicates)}, rejections=rejections)
    check_current(db, run, provider=True)
    user = db.get(User, run.owner_user_id)
    created = []
    actor_counts = {}
    today = db.scalars(select(ContentOpportunity).where(ContentOpportunity.owner_user_id == run.owner_user_id,
        ContentOpportunity.persona_id == run.persona_id, ContentOpportunity.business_date == run.business_date,
        ContentOpportunity.research_run_id.is_not(None))).all()
    for old in today:
        signal = db.scalar(select(ContentOpportunitySignal).where(ContentOpportunitySignal.opportunity_id == old.id,
            ContentOpportunitySignal.status == "active").order_by(ContentOpportunitySignal.id).limit(1))
        if signal:
            source = db.get(DiscoverySource, (signal.annotation_json or {}).get("source_id"))
            if source:
                primary = (signal.annotation_json or {}).get("primary_actor") or source.actor_key
                actor_counts[primary] = actor_counts.get(primary, 0) + 1
    source_cap, daily_cap, exact_duplicates = 0, 0, 0
    for score, candidate in approved:
        if len(created) >= remaining:
            daily_cap += 1
            rejections.append({"candidate_id": candidate["candidate_id"], "title": candidate["title"][:300],
                               "stage": "selection", "reason": "daily_limit_reached"})
            continue
        event = event_map[candidate["event_id"]]
        selected_refs = [{**r, "event_id": event.id, "event_version": event.version, "candidate_id": candidate["candidate_id"]} for r in event.evidence_json if r["item_id"] in candidate["verified_item_ids"]]
        actor = selected_refs[0]["actor"]
        if actor_counts.get(actor, 0) >= 2:
            source_cap += 1
            rejections.append({"candidate_id": candidate["candidate_id"], "title": candidate["title"][:300],
                               "stage": "selection", "reason": "source_actor_limit"})
            continue
        # Merge source references without changing immutable source/event versions.
        for merged_id in candidate.get("merged_candidate_ids", []):
            merged = by_id[merged_id]
            merged_event = event_map[merged["event_id"]]
            selected_refs.extend({**r, "event_id": merged_event.id, "event_version": merged_event.version, "candidate_id": merged_id}
                                 for r in merged_event.evidence_json if r["item_id"] in merged["verified_item_ids"])
            candidate["timeline"].extend(merged["timeline"])
        selected_refs = list({r["item_id"]: r for r in selected_refs}.values())
        event_key = f"{event.event_key}:{event.version}"
        angle = re.sub(r"[\W_]+", "", unicodedata.normalize("NFKC", candidate["angle"]).casefold())
        angle_key = digest(angle)
        if db.scalar(select(ContentOpportunity.id).where(ContentOpportunity.owner_user_id == user.id,
            ContentOpportunity.persona_id == run.persona_id, ContentOpportunity.event_key == event_key,
            ContentOpportunity.angle_key == angle_key)):
            exact_duplicates += 1
            rejections.append({"candidate_id": candidate["candidate_id"], "title": candidate["title"][:300],
                               "stage": "selection", "reason": "duplicate_topic"})
            continue
        hours = candidate.get("expiry_hours", 72)
        hours = min(168 if candidate.get("evergreen") else 48, max(1, hours if type(hours) is int else 48))
        if policy == TECH:
            hours = {"hot": 48, "recent_report": 168, "evergreen": 720}[candidate["classification"]]
        opportunity = ContentOpportunity(owner_user_id=user.id, title=candidate["title"][:300],
            summary=candidate["summary"][:5000], persona_id=run.persona_id, persona_revision_id=run.persona_revision_id,
            research_run_id=run.id, business_date=run.business_date, event_key=event_key, angle_key=angle_key,
            relevant_until=utcnow() + timedelta(hours=hours), created_by="system:daily-discovery")
        db.add(opportunity)
        db.flush()
        signal_ids = []
        for ref in selected_refs:
            signal = ContentOpportunitySignal(opportunity_id=opportunity.id, signal_type="external_ref",
                external_ref=ref["url"], label=ref["title"][:300], annotation_json={
                    "source_id": ref["source_id"], "item_id": ref["item_id"], "checksum": ref["checksum"],
                    "published_at": ref["published_at"], "event_id": ref["event_id"], "event_version": ref["event_version"],
                    "rule_version": policy, "classification": candidate["classification"],
                    "primary_actor": actor, "body_checksum": ref["body_checksum"],
                    "discovery_paths": ref.get("discovery_paths", []),
                    "timeline": [v for v in candidate["timeline"] if v["item_id"] == ref["item_id"]], "merged_candidate_ids": candidate.get("merged_candidate_ids", []), "evaluation": {key: {field: (value[:1000] if isinstance(value, str) else value) for field, value in evaluation.items() if field in {*WEIGHTS, "grounded", "reasons"}} for key, evaluation in (("a", a[ref["candidate_id"]]), ("b", b[ref["candidate_id"]]))},
                    **observed_heat(event_map[ref["event_id"]], at=evaluation_now)}, attached_by="system:daily-discovery")
            db.add(signal)
            db.flush()
            signal_ids.append(signal.id)
        labels = {"hot": "热点：已核对近期事件日期。", "recent_report": "近期报道：事件时间不等于报道时间，不代表刚发生。",
                  "evergreen": "常青参考：不称为今日新事件。"}
        if policy == TECH:
            labels = {"hot": "最新动态：已核对48小时内事件日期。", "recent_report": "近期进展：30天内报道或技术进展，不代表刚发生。",
                      "evergreen": "深度常青：" + str(candidate.get("lasting_value", ""))[:500] + "；不称为今日新事件。"}
        why_now = labels[candidate["classification"]] + " 来源发布时间不代表全网热度。"
        for timeline in candidate["timeline"]:
            why_now += " 原文：" + (timeline["original_published_at"] or "未知") + "；转载/更新：" + (
                timeline["republished_at"] or "未知") + "；事件：" + (timeline["event_at"] or "未知") + "。"
        persist_system_assessment(db, user, opportunity, assessment={
            "what_happened": candidate["summary"][:5000], "why_now": why_now,
            "brand_relevance": candidate["role_fit"][:5000], "audience_fit": candidate["audience_value"][:5000],
            "suggested_angle": candidate["angle"][:5000], "time_sensitivity": "timeless" if candidate.get("evergreen") else "high",
            "recommended_identity_refs": [{"persona_id": run.persona_id}],
            "recommended_modalities": [v for v in candidate.get("formats", []) if v in {"text", "graphic", "video"}][:3],
            "evidence_signal_ids": signal_ids, "evidence_summary": [r["title"][:500] for r in selected_refs],
            "risk_flags": [str(v)[:300] for v in candidate.get("gaps", [])[:10]], "confidence": score / 100,
        }, provider_key="daily-discovery", provider_version=policy)
        audit(db, user=user, event="content_opportunity.generated", opportunity_id=opportunity.id,
              detail={"run_id": run.id, "actor": "system", "event_version": event.version})
        created.append(opportunity.id)
        actor_counts[actor] = actor_counts.get(actor, 0) + 1
    check_current(db, run, provider=True)
    from .discovery_aggregation import allowed_source_ids

    allowed = allowed_source_ids(db, run.owner_user_id, run.persona_id)
    failed_sources = db.scalar(select(DiscoverySource.id).join(PersonaSourceSubscription,
        PersonaSourceSubscription.source_id == DiscoverySource.id).where(
        PersonaSourceSubscription.persona_id == run.persona_id, PersonaSourceSubscription.enabled.is_(True),
        DiscoverySource.id.in_(allowed) if allowed is not None else True,
        DiscoverySource.last_error.is_not(None)).limit(1))
    result = {"count": len(created), "opportunity_ids": created,
              "reason": "fewer_qualifying_topics" if len(created) < remaining else None,
              "coverage": "partial" if failed_sources or run.input_json.get("article_read_errors") else "succeeded"}
    run.output_json = {**(run.output_json or {}), "generation_summary": result}
    current_diag = (run.output_json or {}).get("diagnostics") or {}
    run.output_json = {**run.output_json, "diagnostics": {**current_diag,
        "counts": {**current_diag.get("counts", {}), "source_cap_excluded": source_cap,
                   "daily_cap_excluded": daily_cap, "persisted_opportunities": len(created),
                   "deduplicated_candidates": len(passing & duplicates) + exact_duplicates},
        "rejections": rejections}}
    db.commit()
    return result


def execute_research(db, run_id, *, execution_origin="explicit", task_id=None):
    from .discovery_catchup import CollectionWaiting

    token = claim(db, run_id)
    if not token:
        return {"status": "not_claimed"}
    run = db.get(PersonaResearchRun, run_id, populate_existing=True)
    run.input_json = {**run.input_json, "execution_origin": execution_origin, "task_id": task_id}
    db.commit()
    try:
        today = utcnow().astimezone(__import__("zoneinfo").ZoneInfo("Asia/Taipei")).date().isoformat()
        if (run.kind == "bootstrap" and run.business_date != today
                and not any(k in run.output_json for k in ("event_groups", "topic_candidates", "scores_a", "generation_summary"))):
            run.business_date = today
            run.input_json = {k: v for k, v in run.input_json.items() if k not in {
                "collection_snapshot", "base_evidence", "evidence", "evaluation_time", "previous_event_ids"}}
            db.commit()
        config = check_current(db, run)
        if run.kind in {"bootstrap", "weekly"}:
            from .discovery_aggregation import source_id_for
            from .discovery_search import available

            if source_id_for(db, run.owner_user_id, run.persona_id) is None and not available(config["search_provider"], config["credential_source"]):
                raise DiscoveryBlocked("search_unavailable")
            from .source_discovery import research_sources

            research = research_sources(db, run)
            checkpoint(db, run, "research_summary", research)
        if run.kind in {"bootstrap", "daily"}:
            if run.kind == "bootstrap" and "base_evidence" not in run.input_json:
                run.business_date = utcnow().astimezone(__import__("zoneinfo").ZoneInfo("Asia/Taipei")).date().isoformat()
                db.commit()
            result = generate_daily(db, run)
            if (run.input_json.get("collection_snapshot") or {}).get("status") == "partial":
                result = {**result, "coverage": "partial", "collection_reason": "catchup_coverage_incomplete"}
        else:
            result = {"coverage": "partial" if research["unavailable"] else "succeeded", **research}
        checkpoint(db, run, "summary", result)
        run.status = result["coverage"]
        run.reason = result.get("reason")
    except CollectionWaiting:
        run.status, run.reason = "waiting_collection", "waiting_collection"
    except DiscoveryBlocked as exc:
        db.rollback()
        run = db.get(PersonaResearchRun, run_id, populate_existing=True)
        run.status = "unknown" if "unknown" in str(exc) else "blocked"
        run.reason = str(exc)[:100]
    except Exception:  # noqa: BLE001 Worker boundary records failure without leaking provider payloads.
        db.rollback()
        run = db.get(PersonaResearchRun, run_id, populate_existing=True)
        run.status, run.reason = "failed", "research_processing_failed"
    finally:
        if run.lease_token == token:
            run.lease_token, run.lease_until, run.finished_at = None, None, None if run.status == "waiting_collection" else utcnow()
            db.commit()
    return {"run_id": run.id, "status": run.status, "reason": run.reason}
