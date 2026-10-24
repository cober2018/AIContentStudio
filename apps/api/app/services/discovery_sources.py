"""Human source configuration and bounded validation in the shared registry."""

import uuid
import xml.etree.ElementTree as ET
from datetime import timedelta
from urllib.parse import urlsplit

import httpx
from fastapi import HTTPException
from sqlalchemy import func, or_, select, update
from sqlalchemy.exc import IntegrityError

from ..models import AuditLog, ContentPersona, DiscoverySource, PersonaSourceSubscription, User, utcnow
from .discovery_runtime import profile, settings
from .discovery_search import canonical_url


def management(source):
    return (source.evidence_json or {}).get("management", {})


def set_management(source, **values):
    source.evidence_json = {**(source.evidence_json or {}), "management": {**management(source), **values}}


def origin(source):
    evidence = source.evidence_json or {}
    manual = management(source).get("manual", False)
    automatic = bool(evidence.get("run_id") or evidence.get("search_provider"))
    return "both" if manual and automatic else "manual" if manual else "automatic" if automatic else "seed" if evidence.get("seed_id") else "unknown"


def find_source(db, owner_id, url):
    sources = db.scalars(select(DiscoverySource).where(DiscoverySource.owner_user_id == owner_id).order_by(DiscoverySource.id)).all()
    for source in sources:
        m = management(source)
        if url in {source.canonical_url, (source.adapter_json or {}).get("url"),
                   (source.evidence_json or {}).get("search_url"), m.get("input_url"), *m.get("aliases", [])}:
            for _ in range(5):
                target = management(source).get("merged_into")
                if not target:
                    return source
                source = db.get(DiscoverySource, target)
                if not source or source.owner_user_id != owner_id:
                    break
    return None


def lock_owner(db, owner_id):
    db.execute(update(User).where(User.id == owner_id).values(name=User.name))


def locked_source(db, source_id, owner_id):
    lock_owner(db, owner_id)
    result = db.execute(update(DiscoverySource).where(DiscoverySource.id == source_id,
        DiscoverySource.owner_user_id == owner_id).values(name=DiscoverySource.name))
    if not result.rowcount:
        raise HTTPException(404, "来源不存在")
    source = db.get(DiscoverySource, source_id, populate_existing=True)
    if management(source).get("merged_into"):
        raise HTTPException(409, "链接已合并，请配置现有来源")
    return source


def source_audit(db, source, actor, event, detail):
    db.add(AuditLog(event=event, actor=actor, entity_type="discovery_source", entity_id=str(source.id), detail_json=detail))


def owned_roles(db, owner_id, ids):
    if len(ids) != len(set(ids)):
        raise HTTPException(422, "角色不能重复")
    found = set(db.scalars(select(ContentPersona.id).where(ContentPersona.owner_user_id == owner_id,
                                                        ContentPersona.id.in_(ids))).all())
    if found != set(ids):
        raise HTTPException(404, "角色不存在")


def selected_role_ids(db, source):
    m = management(source)
    if m.get("roles_managed"):
        return m.get("persona_ids", [])
    return list(db.scalars(select(PersonaSourceSubscription.persona_id).where(
        PersonaSourceSubscription.source_id == source.id, PersonaSourceSubscription.enabled.is_(True),
        PersonaSourceSubscription.manually_paused.is_(False))).all())


def reconcile_manual_sources(db, *, owner_id=None, persona_id=None):
    sources = db.scalars(select(DiscoverySource).where(DiscoverySource.status != "merged").order_by(DiscoverySource.id)).all()
    for source in sources:
        if not management(source).get("roles_managed") or (owner_id is not None and source.owner_user_id != owner_id):
            continue
        source = locked_source(db, source.id, source.owner_user_id)
        m = management(source)
        ids = set(m.get("persona_ids", []))
        subs = {s.persona_id: s for s in db.scalars(select(PersonaSourceSubscription).where(
            PersonaSourceSubscription.source_id == source.id)).all()}
        states = dict(m.get("persona_states", {}))
        for pid in sorted(ids | set(subs)):
            if persona_id is not None and pid != persona_id:
                continue
            # Persona-row locking serializes capacity decisions across different sources.
            db.execute(update(ContentPersona).where(ContentPersona.id == pid,
                ContentPersona.owner_user_id == source.owner_user_id).values(status=ContentPersona.status))
            current = profile(db, pid)
            sub = subs.get(pid)
            if sub is None:
                sub = PersonaSourceSubscription(persona_id=pid, source_id=source.id, profile_hash="",
                    relevance="用户手动关联", enabled=False)
                db.add(sub)
                db.flush()
            was_active = sub.enabled and current and sub.profile_hash == current[3]
            sub.manually_paused = pid not in ids
            if current:
                sub.profile_hash = current[3]
            config = settings(db, source.owner_user_id)
            reason = "ready"
            if pid not in ids:
                reason = "unlinked"
            elif not current:
                reason = "persona_ineligible"
            elif not config["enabled"] or pid in config["paused_persona_ids"]:
                reason = "persona_paused"
            elif not config["public_processing_allowed"] or not source.processing_allowed:
                reason = "processing_not_allowed"
            elif source.manually_paused:
                reason = "source_paused"
            elif source.status != "active":
                reason = "source_unvalidated"
            elif not was_active:
                count = db.scalar(select(func.count(PersonaSourceSubscription.id)).join(DiscoverySource,
                    DiscoverySource.id == PersonaSourceSubscription.source_id).where(
                    PersonaSourceSubscription.persona_id == pid, PersonaSourceSubscription.id != sub.id,
                    PersonaSourceSubscription.profile_hash == current[3], PersonaSourceSubscription.enabled.is_(True),
                    PersonaSourceSubscription.manually_paused.is_(False), DiscoverySource.status == "active",
                    DiscoverySource.processing_allowed.is_(True), DiscoverySource.manually_paused.is_(False)))
                if count >= config["active_sources"]:
                    reason = "capacity_pending"
            sub.enabled = reason == "ready"
            states[str(pid)] = reason
            db.flush()
        set_management(source, persona_states=states)
    db.flush()


def configure_source(db, source, user, data):
    if "persona_ids" in data:
        owned_roles(db, user.id, data["persona_ids"])
    before = {"name": source.name, "kind": source.kind, "persona_ids": selected_role_ids(db, source),
              "manually_paused": source.manually_paused, "processing_allowed": source.processing_allowed}
    m = management(source)
    updates = {"revision": m.get("revision", 0) + 1, "alias_notice": None}
    if any(k in data for k in ("name", "kind", "persona_ids")):
        updates["manual"] = True
    for key in ("name", "kind", "manually_paused", "processing_allowed"):
        if key in data:
            setattr(source, key, data[key])
    if "persona_ids" in data:
        updates.update(roles_managed=True, persona_ids=sorted(data["persona_ids"]))
    validation = m.get("validation", {})
    if validation.get("state") in {"pending", "running"}:
        updates["validation"] = {"state": "pending", "request_id": uuid.uuid4().hex}
        source.next_due_at = utcnow()
    set_management(source, **updates)
    db.flush()
    reconcile_manual_sources(db, owner_id=user.id)
    source_audit(db, source, user.email, "discovery_source.configured", {"before": before, "changes": data})


def request_validation(db, source, actor):
    state = management(source).get("validation", {}).get("state")
    if state not in {"pending", "running"}:
        set_management(source, validation={"state": "pending", "request_id": uuid.uuid4().hex})
        source.next_due_at = utcnow()
        source_audit(db, source, actor, "discovery_source.validation_requested", {})


def create_source(db, user, data):
    owned_roles(db, user.id, data["persona_ids"])
    try:
        url = canonical_url(data["url"])
    except (ValueError, TypeError):
        raise HTTPException(422, "请输入有效的公开HTTP(S)链接") from None
    lock_owner(db, user.id)
    existing = find_source(db, user.id, url)
    if existing:
        return existing, False
    source = DiscoverySource(owner_user_id=user.id, canonical_url=url,
        name=data.get("name") or urlsplit(url).hostname, kind=data["kind"],
        actor_key=".".join(urlsplit(url).hostname.split(".")[-2:]), status="candidate",
        manually_paused=data["manually_paused"], processing_allowed=data["processing_allowed"],
        last_error="pending_validation", next_due_at=utcnow(), evidence_json={"management": {
            "manual": True, "roles_managed": True, "persona_ids": sorted(data["persona_ids"]),
            "input_url": url, "revision": 1, "validation": {"state": "pending", "request_id": uuid.uuid4().hex}}})
    try:
        with db.begin_nested():
            db.add(source)
            db.flush()
    except IntegrityError:
        source = find_source(db, user.id, url)
        if source is None:
            raise
        return source, False
    reconcile_manual_sources(db, owner_id=user.id)
    source_audit(db, source, user.email, "discovery_source.created", {"url": url, "persona_ids": data["persona_ids"]})
    return source, True


def source_json(db, source):
    from .discovery_aggregation import accepts_source, is_aggregate

    m = management(source)
    ids = selected_role_ids(db, source)
    personas = db.scalars(select(ContentPersona).where(ContentPersona.owner_user_id == source.owner_user_id,
                                                     ContentPersona.id.in_(ids))).all()
    return {"id": source.id, "name": source.name, "url": source.canonical_url, "kind": source.kind,
        "input_url": m.get("input_url") or (source.evidence_json or {}).get("search_url") or source.canonical_url,
        "collector_url": (source.adapter_json or {}).get("url"), "origin": origin(source), "status": source.status,
        "processing_allowed": source.processing_allowed, "manually_paused": source.manually_paused,
        "reason": source.last_error, "last_success_at": source.last_success_at, "next_due_at": source.next_due_at,
        "validation": m.get("validation", {}), "persona_ids": ids, "merged_into": m.get("merged_into"),
        "personas": [{"id": p.id, "name": p.name, "state": m.get("persona_states", {}).get(str(p.id), "selected")} for p in personas],
        "alias_notice": m.get("alias_notice"), "evidence": source.evidence_json,
        "aggregate_sync": source.cursor_json if is_aggregate(source) else None,
        "aggregate_mode_paused_for": [pid for pid in ids if not accepts_source(db, source.owner_user_id, pid, source.id)]}


def validate_source(db, source_id):
    from .discovery_ingestion import persist_items, probe
    from .url_fetch import UnsafeUrlError

    source = db.get(DiscoverySource, source_id)
    if not source:
        return {"status": "not_claimed"}
    validation = management(source).get("validation", {})
    if validation.get("state") not in {"pending", "running"}:
        return {"status": "not_claimed"}
    now, token = utcnow(), uuid.uuid4().hex
    claimed = db.execute(update(DiscoverySource).where(DiscoverySource.id == source_id,
        DiscoverySource.next_due_at <= now,
        or_(DiscoverySource.lease_until.is_(None), DiscoverySource.lease_until < now),
        DiscoverySource.evidence_json["management"]["validation"]["request_id"].as_string() == validation.get("request_id"))
        .values(lease_token=token, lease_until=now + timedelta(minutes=3)).execution_options(synchronize_session=False))
    db.commit()
    if not claimed.rowcount:
        return {"status": "not_claimed"}
    source = locked_source(db, source_id, source.owner_user_id)
    revision = management(source).get("revision", 0)
    request_id = management(source)["validation"]["request_id"]
    set_management(source, validation={"state": "running", "request_id": request_id})
    db.commit()
    reason, adapter, items = None, {}, []
    try:
        from .discovery_aggregation import is_aggregate, read_json

        if is_aggregate(source):
            data = read_json(source, "/api/v1/selected/snapshot", {"limit": 1})
            if not isinstance(data.get("items"), list) or not data.get("cursor"):
                raise ValueError("aggregate_page_invalid")
            adapter, items = source.adapter_json, []
        else:
            adapter, items = probe(management(source).get("input_url") or source.canonical_url)
        if is_aggregate(source):
            pass
        elif not items:
            reason = "adapter_unavailable"
        elif adapter.get("kind") == "html" and len({i["url"] for i in items}) < 2:
            reason = "collection_entry_unverified"
        elif not any(i["published_at"] for i in items):
            reason = "source_dates_unverified"
    except httpx.HTTPStatusError as exc:
        reason = "credential_required" if exc.response.status_code in {401, 403} else "source_validation_failed"
    except (UnsafeUrlError, httpx.HTTPError, ET.ParseError, ValueError, TypeError):
        reason = "source_validation_failed"
    try:
        source = locked_source(db, source_id, source.owner_user_id)
        m = management(source)
        if source.lease_token != token or m.get("revision", 0) != revision or m.get("validation", {}).get("request_id") != request_id:
            return {"status": "stale_configuration"}
        if reason:
            set_management(source, validation={"state": "failed", "request_id": request_id, "reason": reason})
            source.last_error = reason
            return {"status": "failed", "reason": reason}
        endpoint = canonical_url(adapter["url"])
        existing = find_source(db, source.owner_user_id, endpoint)
        if existing and existing.id != source.id:
            existing = locked_source(db, existing.id, source.owner_user_id)
            aliases = list(dict.fromkeys([*management(existing).get("aliases", []), source.canonical_url, endpoint]))
            set_management(existing, manual=True, aliases=aliases, alias_notice={"url": source.canonical_url,
                "persona_ids": m.get("persona_ids", []), "message": "链接采集入口已存在；原设置保留，请打开配置确认关联角色。"})
            set_management(source, merged_into=existing.id, validation={"state": "merged", "request_id": request_id})
            source.status, source.manually_paused = "merged", True
            for sub in db.scalars(select(PersonaSourceSubscription).where(PersonaSourceSubscription.source_id == source.id)):
                sub.enabled, sub.manually_paused = False, True
            source_audit(db, source, "system:source-validation", "discovery_source.alias_merged", {"target_id": existing.id, "requested_persona_ids": m.get("persona_ids", [])})
            return {"status": "merged", "source_id": existing.id}
        source.adapter_json, source.status = adapter, "active"
        source.last_error = None
        set_management(source, validation={"state": "complete", "request_id": request_id})
        # Validation never imports content after a permission revocation or a pause.
        if source.processing_allowed and not source.manually_paused:
            if not is_aggregate(source):
                persist_items(db, source, items)
        else:
            source.next_due_at = utcnow()
        db.flush()
        reconcile_manual_sources(db, owner_id=source.owner_user_id)
        source_audit(db, source, "system:source-validation", "discovery_source.validated", {"collector_url": endpoint, "items": len(items)})
        return {"status": "succeeded", "source_id": source.id}
    finally:
        if source.lease_token == token:
            source.lease_token, source.lease_until = None, None
        db.commit()
