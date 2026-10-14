"""Bounded read-only proposals from current project, identity and channel facts."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import (
    ContentAccount,
    ContentOpportunity,
    ContentPersona,
    ContentSeries,
    ContentUnit,
    OpportunityProjectConversion,
    PerformanceObservation,
    PublishedContentRecord,
    User,
)
from .channel_adapters import FIRST_BATCH, AdapterUnavailable, capability_for
from .project_brief import current_brief

_SOURCE_SCHEMA = {"text": "text.master.v2", "graphic": "graphic.master.v2", "video": "video.master.v2"}


def _history_coverage(db: Session, owner_id: int) -> dict[tuple[str, str | None], dict]:
    records = db.execute(select(PublishedContentRecord.id, PublishedContentRecord.channel,
                                PublishedContentRecord.content_form).where(
        PublishedContentRecord.owner_user_id == owner_id, PublishedContentRecord.status == "active",
    ).order_by(PublishedContentRecord.id.desc()).limit(250)).all()
    by_id = {row.id: (row.channel, row.content_form) for row in records}
    result: dict[tuple[str, str | None], dict] = {}
    for target in by_id.values():
        entry = result.setdefault(target, {"recordCount": 0, "metrics": {}})
        entry["recordCount"] += 1
    if by_id:
        metrics = db.execute(select(PerformanceObservation.published_content_id,
                                    PerformanceObservation.metric_namespace, PerformanceObservation.metric_key).where(
            PerformanceObservation.published_content_id.in_(by_id),
            PerformanceObservation.observation_kind == "metric",
            PerformanceObservation.numeric_value.is_not(None),
            PerformanceObservation.metric_namespace.is_not(None),
            PerformanceObservation.metric_key.is_not(None),
        )).all()
        for content_id, namespace, key in metrics:
            target = by_id[content_id]
            result[target]["metrics"].setdefault((namespace, key), set()).add(content_id)
    return result


def _series_matches(series: ContentSeries, persona: ContentPersona, account: ContentAccount | None) -> bool:
    if series.status != "active":
        return False
    if getattr(series, "scope", "account_legacy") == "persona_editorial":
        return series.persona_id == persona.id and series.account_id is None and account is None
    return account is not None and series.account_id == account.id


def matrix_suggestions(db: Session, project_id: int, user: User, *, limit: int) -> dict:
    brief = current_brief(db, project_id)
    units = db.scalars(select(ContentUnit).where(ContentUnit.project_id == project_id)).all()
    existing = {(unit.persona_id, unit.account_id, unit.series_id, unit.modality, unit.channel_id)
                for unit in units if unit.status != "archived"}
    scoped = brief.identity_scope_json if brief else []
    identities = []
    if scoped:
        for entry in scoped[:20]:
            if not isinstance(entry, dict) or type(entry.get("persona_id")) is not int:
                continue
            persona = db.get(ContentPersona, entry["persona_id"])
            account = db.get(ContentAccount, entry["account_id"]) if type(entry.get("account_id")) is int else None
            series = db.get(ContentSeries, entry["series_id"]) if type(entry.get("series_id")) is int else None
            if (persona is None or persona.owner_user_id != user.id or persona.status != "active"
                    or account is not None and (account.persona_id != persona.id or account.status != "active")
                    or series is not None and not _series_matches(series, persona, account)):
                continue
            identities.append((persona, account, series))
    elif any(unit.status != "archived" for unit in units):
        selected = {(unit.persona_id, unit.account_id, unit.series_id)
                    for unit in units if unit.status != "archived"}
        for persona_id, account_id, series_id in sorted(selected, key=lambda row: tuple(-1 if value is None else value for value in row))[:20]:
            persona = db.get(ContentPersona, persona_id)
            account = db.get(ContentAccount, account_id) if account_id is not None else None
            series = db.get(ContentSeries, series_id) if series_id is not None else None
            if (persona is None or persona.owner_user_id != user.id or persona.status != "active"
                    or account_id is not None and (account is None or account.persona_id != persona.id or account.status != "active")
                    or series_id is not None and (series is None or not _series_matches(series, persona, account))):
                continue
            identities.append((persona, account, series))
    else:
        personas = db.scalars(select(ContentPersona).where(ContentPersona.owner_user_id == user.id,
            ContentPersona.status == "active").order_by(ContentPersona.id).limit(20)).all()
        identities = [(persona, None, None) for persona in personas]
    modalities = ({value for value in brief.modality_scope_json if isinstance(value, str)}
                  if brief and brief.modality_scope_json else set(_SOURCE_SCHEMA))
    channels = ({value for value in brief.channel_scope_json if isinstance(value, str)}
                if brief and brief.channel_scope_json else None)
    conversion = db.scalar(select(OpportunityProjectConversion).where(OpportunityProjectConversion.project_id == project_id))
    opportunity = db.get(ContentOpportunity, conversion.opportunity_id) if conversion else None
    if opportunity is not None and opportunity.owner_user_id != user.id:
        opportunity = None
    history = _history_coverage(db, user.id)
    items = []
    seen = set()
    for persona, account, series in identities:
        for (channel, form), contract in FIRST_BATCH.items():
            modality = next((name for name, schema in _SOURCE_SCHEMA.items() if schema in contract.accepted_master_schemas), None)
            if modality not in modalities or channels is not None and channel not in channels:
                continue
            identity = (persona.id, account.id if account else None, series.id if series else None)
            key = (*identity, modality, channel, form)
            if key in seen or (*identity, modality, channel) in existing:
                continue
            seen.add(key)
            try:
                capability = capability_for(db, _SOURCE_SCHEMA[modality], channel, form)
            except AdapterUnavailable as exc:
                capability = {"configured": False, "supported_source": True, "executable": False,
                              "verified": False, "reason": str(exc)}
            if not capability["configured"]:
                continue
            coverage = history.get((channel, form))
            historical_metrics = ([{"namespace": namespace, "key": metric_key, "sampleCount": len(content_ids)}
                                   for (namespace, metric_key), content_ids in sorted(coverage["metrics"].items())[:10]]
                                  if coverage else [])
            history_state = "known" if historical_metrics else "missing" if coverage else "unknown"
            items.append({"personaId": persona.id, "accountId": identity[1], "seriesId": identity[2],
                          "modality": modality, "channel": channel, "contentForm": form,
                          "reason": "项目简报与当前身份范围匹配" if brief else "当前身份与已发布渠道形态匹配",
                          "briefRevisionId": brief.id if brief else None,
                          "opportunityId": opportunity.id if opportunity else None,
                          "capability": capability, "estimatedCost": "unknown", "estimatedValue": "unknown",
                          "confidence": "unknown", "historyCoverage": history_state,
                          "historicalMetrics": historical_metrics,
                          "historySampleCount": coverage["recordCount"] if coverage else 0,
                          "unknowns": ["历史指标仅作同渠道同形态覆盖参考，不构成价值排序", "实际适配仍需当前Master与素材验证"]})
            if len(items) >= limit:
                return {"persisted": False, "schedule": False, "items": items}
    return {"persisted": False, "schedule": False, "items": items}
