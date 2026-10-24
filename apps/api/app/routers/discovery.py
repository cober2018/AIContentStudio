"""Discovery reads and owner/editor-controlled setup; GET never starts research."""

from datetime import datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from ..config import get_settings
from ..db import get_db
from ..deps import get_current_user, require_editor
from ..models import (
    ContentPersona,
    DiscoverySource,
    PersonaResearchRun,
    SystemSetting,
    utcnow,
)
from ..services import discovery_catchup as catchup
from ..services import discovery_runtime as runtime
from ..services import discovery_sources as registry
from ..services.discovery_search import available

router = APIRouter(prefix="/discovery", tags=["persona-discovery"])


class RadarIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    persona_id: int = Field(gt=0)
    enabled: bool
    report_path: str | None = Field(default=None, max_length=2000)
    producer_version: str | None = Field(default=None, max_length=80)
    producer_revision: str | None = Field(default=None, max_length=40)
    producer_verified: bool | None = None
    auto_daily: bool | None = None


@router.get("/radar")
def radar_settings(persona_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    from ..services import radar_discovery

    persona = db.get(ContentPersona, persona_id)
    if not persona or persona.owner_user_id != user.id:
        raise HTTPException(404, "角色不存在")
    return radar_discovery.status(db, user.id, persona_id)


@router.put("/radar")
def configure_radar(payload: RadarIn, db=Depends(get_db), user=Depends(require_editor)):
    from ..services import radar_discovery

    persona = db.get(ContentPersona, payload.persona_id)
    if not persona or persona.owner_user_id != user.id:
        raise HTTPException(404, "角色不存在")
    try:
        result = radar_discovery.configure(db, user.id, actor=user.email, **payload.model_dump(exclude_none=True))
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(422, str(exc)) from None
    return result


class SettingsIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool
    public_processing_allowed: bool
    search_provider: Literal["minimax", "tavily"] = "minimax"
    credential_source: Literal["environment", "codex_mcp"] = "environment"
    daily_hour: int = Field(default=8, ge=0, le=23)
    daily_limit: int = Field(default=5, ge=1, le=5)
    paused_persona_ids: list[int] | None = Field(default=None, max_length=100)


def configuration_json(db, user):
    config = runtime.settings(db, user.id)
    ready = available(config["search_provider"], config["credential_source"])
    heartbeat = db.get(SystemSetting, "discovery.heartbeat")
    last = (heartbeat.value or {}).get("last_scan_at") if heartbeat else None
    try:
        worker = bool(last and 0 <= (utcnow() - runtime.aware(datetime.fromisoformat(last))).total_seconds() < 300)
    except (ValueError, TypeError):
        worker = False
    return {**config, "search_configured": ready, "worker_enabled": worker}


@router.get("/settings")
def read_settings(db=Depends(get_db), user=Depends(get_current_user)):
    return configuration_json(db, user)


@router.put("/settings")
def save_settings(payload: SettingsIn, db=Depends(get_db), user=Depends(require_editor)):
    if payload.credential_source == "codex_mcp" and get_settings().app_env == "production":
        raise HTTPException(422, "生产环境请通过环境变量提供搜索凭据")
    if payload.paused_persona_ids is not None:
        owned = set(db.scalars(select(ContentPersona.id).where(ContentPersona.owner_user_id == user.id)).all())
        if set(payload.paused_persona_ids) - owned:
            raise HTTPException(404, "角色不存在")
    key = f"discovery.{user.id}"
    row = db.get(SystemSetting, key)
    if row is None:
        row = SystemSetting(key=key)
        db.add(row)
    row.value = {**runtime.settings(db, user.id), **payload.model_dump(exclude_none=True)}
    row.updated_by = user.email
    db.flush()
    if payload.enabled:
        from ..services.source_discovery import import_seed_inventory

        import_seed_inventory(db, user.id)
        for persona in db.scalars(select(ContentPersona).where(ContentPersona.owner_user_id == user.id)).all():
            current = runtime.profile(db, persona.id)
            if current:
                runtime.on_persona_revision(db, persona.id, current[1])
        for run in db.scalars(select(PersonaResearchRun).where(PersonaResearchRun.owner_user_id == user.id,
            PersonaResearchRun.status == "blocked", PersonaResearchRun.reason.in_([
                "persona_paused", "search_unavailable", "model_unavailable", "public_processing_not_allowed"]))).all():
            current = runtime.profile(db, run.persona_id)
            unresolved = any(isinstance(v, dict) and v.get("state") in {"pending", "unknown"} for v in (run.output_json or {}).values())
            if current and current[3] == run.profile_hash and run.persona_id not in row.value["paused_persona_ids"] and not unresolved:
                run.status, run.reason, run.lease_token, run.lease_until = "queued", None, None, None
    db.commit()
    return configuration_json(db, user)


@router.get("/sources")
def sources(persona_id: int | None = None, origin: Literal["manual", "automatic", "both", "seed", "unknown"] | None = None,
            limit: int = Query(100, ge=1, le=200), offset: int = Query(0, ge=0), merged_only: bool = False,
            db=Depends(get_db), user=Depends(get_current_user)):
    rows = db.scalars(select(DiscoverySource).where(DiscoverySource.owner_user_id == user.id,
        (DiscoverySource.status == "merged") if merged_only else (DiscoverySource.status != "merged")).order_by(DiscoverySource.id)).all()
    if merged_only:
        rows = [s for s in rows if (target := db.get(DiscoverySource, registry.management(s).get("merged_into")))
                and target.owner_user_id == user.id and registry.management(target).get("alias_notice")]
    rows = [s for s in rows if (origin is None or registry.origin(s) == origin
            or origin in {"manual", "automatic"} and registry.origin(s) == "both")
            and (persona_id is None or persona_id in registry.selected_role_ids(db, s))]
    return [{**registry.source_json(db, s), "catchup": catchup.source_projection(db, s)} for s in rows[offset:offset + limit]]


@router.get("/sources/{source_id}")
def get_source(source_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    source = db.get(DiscoverySource, source_id)
    if not source or source.owner_user_id != user.id:
        raise HTTPException(404, "来源不存在")
    resolved = registry.find_source(db, user.id, source.canonical_url)
    return {**registry.source_json(db, resolved or source), "catchup": catchup.source_projection(db, resolved or source)}


class SourceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url: str = Field(min_length=1, max_length=1000)
    name: str | None = Field(default=None, min_length=1, max_length=300)
    kind: Literal["website", "rss", "creator"] = "website"
    persona_ids: list[int] = Field(default_factory=list, max_length=100)
    manually_paused: bool = False
    processing_allowed: bool | None = None


@router.post("/sources")
def create_source(payload: SourceCreate, db=Depends(get_db), user=Depends(require_editor)):
    data = payload.model_dump()
    if data["processing_allowed"] is None:
        data["processing_allowed"] = runtime.settings(db, user.id)["public_processing_allowed"]
    source, created = registry.create_source(db, user, data)
    db.commit()
    return {"created": created, "source": registry.source_json(db, source)}


class SourcePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=300)
    kind: Literal["website", "rss", "creator"] | None = None
    persona_ids: list[int] | None = Field(default=None, max_length=100)
    manually_paused: bool | None = None
    processing_allowed: bool | None = None


@router.patch("/sources/{source_id}")
def patch_source(source_id: int, payload: SourcePatch, db=Depends(get_db), user=Depends(require_editor)):
    source = registry.locked_source(db, source_id, user.id)
    from ..services.radar_discovery import is_radar

    if is_radar(source):
        raise HTTPException(422, "Radar请使用科技角色的本地日报配置入口")
    registry.configure_source(db, source, user, payload.model_dump(exclude_none=True))
    db.commit()
    return registry.source_json(db, source)


@router.post("/sources/{source_id}/validate")
def revalidate_source(source_id: int, db=Depends(get_db), user=Depends(require_editor)):
    source = registry.locked_source(db, source_id, user.id)
    from ..services.radar_discovery import is_radar

    if is_radar(source):
        raise HTTPException(422, "Radar请在本地日报配置入口核对路径并重新保存")
    registry.request_validation(db, source, user.email)
    db.commit()
    return registry.source_json(db, source)


def run_json(run, db=None):
    from ..services.opportunity_policy import diagnostic_projection

    return {"id": run.id, "persona_id": run.persona_id, "persona_revision_id": run.persona_revision_id,
            "kind": run.kind, "business_date": run.business_date, "origin": (run.input_json or {}).get("origin"),
            "execution_origin": (run.input_json or {}).get("execution_origin"), "task_id": (run.input_json or {}).get("task_id"), "status": run.status, "reason": run.reason,
            "summary": (run.output_json or {}).get("summary"),
            "diagnostics": diagnostic_projection(run),
            "collection_snapshot": (run.input_json or {}).get("collection_snapshot"),
            "collection_notice": catchup.later_catchup_notice(db, run) if db is not None else None,
            "collection_target_at": (run.input_json or {}).get("collection_target_at"), "created_at": run.created_at,
            "finished_at": run.finished_at, "searches": run.searches, "attempt": run.attempt,
            "model_requests": run.model_requests, "reserved_input_tokens": run.input_tokens, "reserved_output_tokens": run.output_tokens}


@router.get("/runs")
def runs(persona_id: int | None = None, limit: int = Query(30, ge=1, le=100),
         db=Depends(get_db), user=Depends(get_current_user)):
    stmt = select(PersonaResearchRun).where(PersonaResearchRun.owner_user_id == user.id,
                                           PersonaResearchRun.kind != "budget")
    if persona_id is not None:
        stmt = stmt.where(PersonaResearchRun.persona_id == persona_id)
    return [run_json(r, db) for r in db.scalars(stmt.order_by(PersonaResearchRun.id.desc()).limit(limit)).all()]


@router.get("/runs/{run_id}")
def read_run(run_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    run = db.get(PersonaResearchRun, run_id)
    if not run or run.owner_user_id != user.id or run.kind == "budget":
        raise HTTPException(404, "研究任务不存在")
    checkpoints = {key: {k: v for k, v in value.items() if k in {"state", "request_id", "llm_run_id", "input_hash", "reason"}}
                   for key, value in (run.output_json or {}).items() if isinstance(value, dict) and "state" in value}
    return {**run_json(run, db), "input_snapshot": run.input_json, "checkpoints": checkpoints}


@router.post("/runs/{run_id}/retry")
def retry(run_id: int, db=Depends(get_db), user=Depends(require_editor)):
    run = db.get(PersonaResearchRun, run_id)
    if not run or run.owner_user_id != user.id or run.kind == "budget":
        raise HTTPException(404, "研究任务不存在")
    if run.status not in {"blocked", "failed", "partial"}:
        raise HTTPException(409, "进行中或结果未知的请求不能重复派发")
    if any(isinstance(value, dict) and value.get("state") in {"pending", "unknown"}
           for value in (run.output_json or {}).values()):
        raise HTTPException(409, "存在结果未知的调用，请先核对供应商回执")
    runtime.check_current(db, run)
    run.status, run.reason, run.lease_token, run.lease_until = "queued", None, None, None
    db.commit()
    return run_json(run, db)


def status_projection(db, user):
    from ..services.opportunity_policy import persona_policy
    from ..services.radar_discovery import status as radar_status

    config = configuration_json(db, user)
    heartbeat = db.get(SystemSetting, "discovery.heartbeat")
    result = []
    for persona in db.scalars(select(ContentPersona).where(ContentPersona.owner_user_id == user.id)).all():
        current = runtime.profile(db, persona.id)
        from ..services.discovery_aggregation import source_id_for

        aggregate = source_id_for(db, user.id, persona.id) is not None
        latest = db.scalar(select(PersonaResearchRun).where(PersonaResearchRun.persona_id == persona.id,
            PersonaResearchRun.kind.in_(["daily", "bootstrap", "weekly"])).order_by(
                (PersonaResearchRun.status == "running").desc(), PersonaResearchRun.id.desc()).limit(1))
        now = utcnow().astimezone(__import__('zoneinfo').ZoneInfo("Asia/Taipei"))
        today = db.scalar(select(PersonaResearchRun).where(PersonaResearchRun.owner_user_id == user.id,
            PersonaResearchRun.persona_id == persona.id, PersonaResearchRun.kind == "daily",
            PersonaResearchRun.business_date == now.date().isoformat()).order_by(PersonaResearchRun.id.desc()).limit(1))
        due = now.replace(hour=config["daily_hour"], minute=0, second=0, microsecond=0)
        if due <= now:
            due += timedelta(days=1)
        reason = "positioning_incomplete" if not current else "paused" if not config["enabled"] or persona.id in config["paused_persona_ids"] else (
            "public_processing_not_allowed" if not config["public_processing_allowed"] else
            "search_unavailable" if not aggregate and not config["search_configured"] else
            "worker_not_enabled" if not config["worker_enabled"] else None)
        result.append({"persona_id": persona.id, "collection_mode": "aggregate" if aggregate else "direct", "name": persona.name,
                       "opportunity_policy": persona_policy(db, user.id, persona.id), "business_date": now.date().isoformat(),
                       "status": reason or (today.status if today else "not_yet_due"),
                       "reason": reason or (today.reason if today else None), "last_run": run_json(latest, db) if latest else None,
                       "today_run": run_json(today, db) if today else None,
                       "radar": radar_status(db, user.id, persona.id),
                       "next_due_at": due.isoformat() if current and config["enabled"] else None})
    return {"settings": config, "personas": result, "scheduler": heartbeat.value if heartbeat else None,
            "catchup": catchup.owner_projection(db, user.id)}


@router.get("/status")
def status(db=Depends(get_db), user=Depends(get_current_user)):
    return status_projection(db, user)
