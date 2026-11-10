"""内容机会数据保障：只盯结果——信息源按时抓到、每个角色每天按时出选题；没达标就补救，补救不了就提醒。"""
from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

from ..models import ContentPersona, DiscoverySource, PersonaResearchRun, PersonaSourceSubscription, SystemSetting, utcnow
from . import discovery_runtime as runtime

TZ = ZoneInfo("Asia/Taipei")
DONE = {"succeeded", "partial"}
ACTIVE = {"queued", "running", "waiting_collection"}
# Failures the guard may resend on its own; a call that may have reached the model ("unknown") is never resent.
RETRY = {"model_unreachable": None, "search_unavailable": None, "research_processing_failed": 1}
REASONS = {
    "model_unreachable": "模型通道断开（连不上模型）",
    "research_processing_failed": "代码报错（详情见后台日志）",
    "provider_outcome_unknown": "模型调用结果未知，需要核对后再重跑",
    "search_unavailable": "搜索服务不可用",
    "model_budget_exhausted": "今天的模型额度用完了",
    "waiting_collection": "等信息源抓取完成",
    "missing_today_run": "到点了还没生成今天的任务",
    "past_deadline": "过了截止时间还没跑完",
    "attempts_exhausted": "自动重试次数用完了",
    "source_processing_revoked": "用到的信息源已停用或已从角色移除",
    "radar_report_unavailable": "科技日报（Radar）今天没生成",
    "persona_paused": "角色已暂停或没开自动选题",
    "persona_profile_changed": "角色定位改过了，按新定位重跑",
    "public_processing_not_allowed": "没开「允许处理公开内容」",
    "missed_historical_day": "错过了当天，不再补跑",
    "no_grounded_candidates": "没有能用原文支撑的选题",
    "aggregate_evidence_withdrawn": "聚合站撤回了用到的文章",
    "candidate_response_invalid": "模型返回的格式不对",
    "model_unavailable": "没配置可用的模型",
    "research_inputs_changed": "跑的过程中信息源有变动",
    "research_lease_lost": "任务被别的进程接走了",
    "search_budget_exhausted": "今天的搜索额度用完了",
    "search_outcome_unknown": "搜索调用结果未知，需要核对",
}


def _aware(value: datetime | None) -> datetime | None:
    return runtime.aware(value) if value else None


def _guard(run: PersonaResearchRun) -> dict:
    return dict((run.output_json or {}).get("guard") or {})


def _requeue(db, run: PersonaResearchRun, now: datetime) -> None:
    guard = _guard(run)
    guard.update(attempts=guard.get("attempts", 0) + 1, last_at=now.isoformat(), last_reason=run.reason)
    run.output_json = {**(run.output_json or {}), "guard": guard}
    flag_modified(run, "output_json")
    run.status, run.reason, run.lease_token, run.lease_until = "queued", None, None, None


def _run_check(db, run: PersonaResearchRun, config: dict, now: datetime, actions: list) -> dict:
    """One research run against its goal; resends it when the failure is safe and the limits allow."""
    local = now.astimezone(TZ)
    view = {"run_id": run.id, "kind": run.kind, "status": run.status, "reason": run.reason}
    if run.status in DONE:
        return {**view, "state": "ok"}
    if run.status in ACTIVE:
        return {**view, "state": "remedying", "detail": REASONS.get(run.reason or "", "正在跑")}
    if run.status == "unknown":
        return {**view, "state": "attention", "detail": REASONS["provider_outcome_unknown"]}
    limit = RETRY.get(run.reason or "", 0)
    guard = _guard(run)
    attempts = guard.get("attempts", 0)
    text = REASONS.get(run.reason or "", run.reason or "失败")
    if run.reason not in RETRY:
        return {**view, "state": "attention", "detail": text}
    if (limit is not None and attempts >= limit) or attempts >= config["guard_max_attempts"]:
        return {**view, "state": "attention", "detail": f"{text}；{REASONS['attempts_exhausted']}"}
    if local.hour >= config["guard_remedy_until_hour"]:
        return {**view, "state": "attention", "detail": f"{text}；已过当天补救时间"}
    last = _aware(datetime.fromisoformat(guard["last_at"])) if guard.get("last_at") else _aware(run.finished_at)
    if last and now - last < timedelta(minutes=config["guard_retry_minutes"]):
        return {**view, "state": "remedying", "detail": f"{text}；稍后自动重试"}
    if run.reason == "model_unreachable" and not runtime.model_reachable():
        # Waiting costs nothing; only a resend counts as an attempt.
        return {**view, "state": "remedying", "detail": f"{REASONS['model_unreachable']}；等通道恢复后自动重跑"}
    _requeue(db, run, now)
    actions.append({"at": now.isoformat(), "target": f"run:{run.id}", "action": "requeue", "reason": view["reason"]})
    return {**view, "status": "queued", "state": "remedying", "detail": f"{text}；已自动重跑"}


def _personas(db, owner_id: int, config: dict, now: datetime, actions: list) -> list[dict]:
    local = now.astimezone(TZ)
    today = local.date().isoformat()
    rows = []
    for persona in db.scalars(select(ContentPersona).where(ContentPersona.owner_user_id == owner_id, ContentPersona.status == "active")).all():
        item = {"persona_id": persona.id, "name": persona.name}
        if persona.id in config["paused_persona_ids"]:
            rows.append({**item, "state": "skipped", "detail": "已暂停"})
            continue
        if not runtime.profile(db, persona.id):
            rows.append({**item, "state": "skipped", "detail": "角色定位没填完，暂不跑"})
            continue
        setup = db.scalar(select(PersonaResearchRun).where(PersonaResearchRun.persona_id == persona.id,
            PersonaResearchRun.kind.in_(["bootstrap", "weekly"])).order_by(PersonaResearchRun.id.desc()).limit(1))
        if setup is not None and setup.status not in DONE | ACTIVE:
            item["setup"] = _run_check(db, setup, config, now, actions)
        daily = db.scalar(select(PersonaResearchRun).where(PersonaResearchRun.persona_id == persona.id,
            PersonaResearchRun.kind == "daily", PersonaResearchRun.business_date == today).order_by(PersonaResearchRun.id.desc()).limit(1))
        if daily is None:
            due = local.hour >= config["daily_hour"] + 1
            rows.append({**item, "state": "attention" if due else "waiting",
                         "detail": REASONS["missing_today_run"] if due else f"今天 {config['daily_hour']}:00 开跑"})
            continue
        check = _run_check(db, daily, config, now, actions)
        if check["state"] != "ok" and local.hour >= config["guard_daily_deadline_hour"]:
            check = {**check, "state": "attention", "detail": f"{REASONS['past_deadline']}：{check.get('detail', '')}"}
        rows.append({**item, **check})
    return rows


def _sources(db, owner_id: int, config: dict, now: datetime, actions: list) -> list[dict]:
    limit = timedelta(hours=config["guard_source_hours"])
    ids = select(PersonaSourceSubscription.source_id).join(ContentPersona, ContentPersona.id == PersonaSourceSubscription.persona_id).where(
        PersonaSourceSubscription.enabled.is_(True), PersonaSourceSubscription.manually_paused.is_not(True),
        ContentPersona.status == "active", ContentPersona.owner_user_id == owner_id)
    rows = []
    for source in db.scalars(select(DiscoverySource).where(DiscoverySource.id.in_(ids), DiscoverySource.status == "active",
                                                            DiscoverySource.manually_paused.is_not(True))).all():
        last = _aware(source.last_success_at)
        item = {"source_id": source.id, "name": source.name, "last_success_at": last.isoformat() if last else None}
        if last and now - last <= limit:
            rows.append({**item, "state": "ok"})
            continue
        if (source.failures or 0) >= 3:
            rows.append({**item, "state": "attention", "detail": f"连续 {source.failures} 次抓取失败：{source.last_error or '原因未记录'}"})
            continue
        leased = source.lease_until is not None and _aware(source.lease_until) > now
        if not leased and (source.next_due_at is None or _aware(source.next_due_at) > now):
            source.next_due_at = now
            actions.append({"at": now.isoformat(), "target": f"source:{source.id}", "action": "collect_now"})
        rows.append({**item, "state": "remedying", "detail": f"超过 {config['guard_source_hours']} 小时没抓到，已安排马上重抓"})
    return rows


def sweep(db, now: datetime | None = None) -> dict:
    now = runtime.aware(now or utcnow())
    results = {}
    for row in db.scalars(select(SystemSetting).where(SystemSetting.key.like("discovery.%"))).all():
        owner = row.key.split(".", 1)[1]
        if not owner.isdigit():
            continue
        config = runtime.settings(db, int(owner))
        if not config["enabled"]:
            continue
        actions: list = []
        personas = _personas(db, int(owner), config, now, actions)
        sources = _sources(db, int(owner), config, now, actions)
        key = f"discovery.guard.{owner}"
        stored = db.get(SystemSetting, key) or SystemSetting(key=key, value={})
        db.add(stored)
        today = now.astimezone(TZ).date().isoformat()
        earlier = [item for item in (stored.value or {}).get("actions", []) if item["at"][:10] >= (now - timedelta(days=1)).date().isoformat()]
        log = (earlier + actions)[-200:]
        stored.value = {"checked_at": now.isoformat(), "personas": personas, "sources": sources, "actions": log,
                        "remedies_today": sum(1 for item in log if datetime.fromisoformat(item["at"]).astimezone(TZ).date().isoformat() == today)}
        flag_modified(stored, "value")
        db.commit()
        results[owner] = {"actions": len(actions)}
    return results


def status(db, owner_id: int) -> dict:
    row = db.get(SystemSetting, f"discovery.guard.{owner_id}")
    value = dict(row.value or {}) if row else {}
    items = value.get("personas", []) + value.get("sources", []) + [p["setup"] for p in value.get("personas", []) if p.get("setup")]
    value["attention"] = sum(1 for item in items if item.get("state") == "attention")
    return value
