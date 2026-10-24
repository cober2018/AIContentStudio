"""Auto-start of rough-cut edits by a local assistant (Claude Code by default).

The platform only queues tasks and records what the local dispatcher reports; the assistant itself
claims, works and submits through the existing creative MCP, and never accepts its own output.
Only tasks queued here after 准备剪辑 are auto-started; a task is started at most once by itself.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import runtime_config
from ..models import CreativeExecution, CreativeExecutionPackage, SystemSetting, User

SETTINGS = "edit_agent"
RUNS = "edit_agent_runs"
ASSISTANTS = {"claude": "Claude Code", "codex": "Codex"}
EDIT_EXECUTOR = "codex-video-production"
_last_poll: dict = {}


def settings() -> dict:
    value = runtime_config.get_runtime(SETTINGS) or {}
    return {"enabled": value.get("enabled", True), "assistant": value.get("assistant", "claude")}


def _runs(db: Session) -> dict:
    row = db.get(SystemSetting, RUNS)
    return dict(row.value or {}) if row else {}


def _save(db: Session, key: str, value: dict) -> None:
    row = db.get(SystemSetting, key)
    if row is None:
        row = SystemSetting(key=key)
        db.add(row)
    row.value = value
    db.flush()
    if key == SETTINGS:
        runtime_config.set_runtime(key, value)


def save_settings(db: Session, enabled: bool, assistant: str, user: User) -> dict:
    if assistant not in ASSISTANTS:
        raise HTTPException(422, {"code": "edit_agent_assistant_invalid"})
    _save(db, SETTINGS, {"enabled": enabled, "assistant": assistant})
    db.commit()
    return view_settings()


def view_settings() -> dict:
    seen = _last_poll.get("at")
    return {**settings(), "assistants": ASSISTANTS, "dispatcher_seen_at": seen.isoformat() if seen else None}


def queue(db: Session, execution_id: int) -> None:
    runs = _runs(db)
    runs.setdefault(str(execution_id), {"state": "queued", "at": datetime.now(UTC).isoformat()})
    _save(db, RUNS, runs)


def next_task(db: Session, owner: User) -> dict | None:
    _last_poll["at"] = datetime.now(UTC)
    config = settings()
    if not config["enabled"]:
        return None
    runs = _runs(db)
    now = datetime.now(UTC)
    for key, record in runs.items():
        # A dispatcher that died mid-session leaves "launched"; after the session limit it counts as failed.
        if record["state"] == "launched" and (now - datetime.fromisoformat(record["at"])).total_seconds() > 100 * 60:
            runs[key] = {**record, "state": "failed", "reason": "助手没有回报结果，详见日志"}
            _save(db, RUNS, runs)
            db.commit()
    if any(record["state"] == "launched" for record in runs.values()):
        return None
    for key, record in sorted(runs.items(), key=lambda item: int(item[0])):
        if record["state"] != "queued":
            continue
        execution = db.get(CreativeExecution, int(key))
        if execution is None or execution.owner_user_id != owner.id or execution.state != "prepared":
            runs[key] = {**record, "state": "skipped", "reason": "任务已不在待领取状态"}
            _save(db, RUNS, runs)
            db.commit()
            continue
        package = db.get(CreativeExecutionPackage, execution.package_id)
        return {"execution_id": execution.id, "project_id": execution.project_id, "unit_id": execution.content_unit_id,
                "package_hash": package.package_hash if package else None, "assistant": config["assistant"]}
    return None


def report(db: Session, owner: User, execution_id: int, state: str, reason: str = "", log: str = "") -> dict:
    if state not in {"launched", "finished", "failed"}:
        raise HTTPException(422, {"code": "edit_agent_state_invalid"})
    execution = db.get(CreativeExecution, execution_id)
    runs = _runs(db)
    key = str(execution_id)
    if execution is None or execution.owner_user_id != owner.id or key not in runs:
        raise HTTPException(404, {"code": "edit_agent_task_unknown"})
    runs[key] = {**runs[key], "state": state, "reason": reason[:500], "log": log[:500], "at": datetime.now(UTC).isoformat()}
    _save(db, RUNS, runs)
    db.commit()
    return runs[key]


def _latest(db: Session, project_id: int, unit_id: int, user: User) -> CreativeExecution | None:
    return db.scalar(select(CreativeExecution).where(
        CreativeExecution.owner_user_id == user.id, CreativeExecution.project_id == project_id,
        CreativeExecution.content_unit_id == unit_id, CreativeExecution.executor_key == EDIT_EXECUTOR)
        .order_by(CreativeExecution.id.desc()).limit(1))


def status(db: Session, user: User, project_id: int, unit_id: int) -> dict:
    from .content_masters import owned_unit

    owned_unit(db, project_id, unit_id, user)
    execution = _latest(db, project_id, unit_id, user)
    if execution is None:
        return {"label": None}
    record = _runs(db).get(str(execution.id)) or {}
    config = settings()
    name = ASSISTANTS[config["assistant"]]
    labels = {"claimed": "剪辑中", "in_progress": "剪辑中", "result_ready": "粗剪已回传，待你审片", "accepted": "粗剪已接受",
              "rejected": "需修改", "cancelled": "已取消", "superseded": "已替代"}
    if execution.state == "prepared":
        if record.get("state") in {"failed", "finished"}:
            label, detail = "出错", record.get("reason") or "助手结束了，但没有领取任务"
        elif record.get("state") == "launched":
            label, detail = "剪辑中", f"{name} 已启动，正在领取任务"
        elif record.get("state") == "queued":
            label, detail = ("排队中", f"等本机 {name} 开始剪辑") if config["enabled"] else ("等待开始", "自动剪辑已关闭，可在设置里打开，或直接让助手「剪这条」")
        else:
            label, detail = "等待开始", "这个任务需要你让助手开始"
    elif execution.state in {"blocked", "failed_before_dispatch", "unknown"}:
        label, detail = "出错", execution.safe_reason or record.get("reason") or "剪辑没完成"
    else:
        label, detail = labels.get(execution.state, execution.state), ""
    return {"label": label, "detail": detail, "execution_id": execution.id, "state": execution.state,
            "log": record.get("log"), "can_retry": execution.state == "prepared" and record.get("state") in {"failed", "finished"}}


def retry(db: Session, user: User, project_id: int, unit_id: int) -> dict:
    from .content_masters import owned_unit

    owned_unit(db, project_id, unit_id, user, mutate=True)
    execution = _latest(db, project_id, unit_id, user)
    runs = _runs(db)
    record = runs.get(str(execution.id)) if execution else None
    if execution is None or execution.state != "prepared" or not record or record.get("state") not in {"failed", "finished"}:
        raise HTTPException(409, {"code": "edit_agent_retry_unavailable", "message": "这个任务现在不能重试"})
    # Only a start that never claimed the task is retried; the old attempt stays in the log.
    runs[str(execution.id)] = {"state": "queued", "at": datetime.now(UTC).isoformat(), "previous": record}
    _save(db, RUNS, runs)
    db.commit()
    return status(db, user, project_id, unit_id)
