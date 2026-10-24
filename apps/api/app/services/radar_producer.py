"""Run the approved free Radar CLI inside the existing collection lease."""

from __future__ import annotations

import fcntl
import json
import os
import subprocess
from pathlib import Path
from zoneinfo import ZoneInfo

from ..models import SystemSetting, utcnow

ROOT = Path(__file__).resolve().parents[4].parent / "new-term-radar"
REVISION = "2568cdcba5691cd21d03f2c0a86f4461dbcb7234"
TIMEOUT = 300
SKIP = "x,sitemaps,newsites,revenue,asks,gsc,review,judge,usecases,tutorials"


def receipt_key(source_id, day):
    return f"discovery.radar_generation.{source_id}.{day}"


def validate_install(config):
    if (config.get("producer_version") != "0.4.0" or config.get("producer_revision") != REVISION
            or Path(config.get("report_path") or "").resolve() != ROOT / "report.json"):
        raise ValueError("radar_producer_binding_invalid")
    if not (ROOT / ".venv/bin/python3.12").is_file():
        raise ValueError("radar_producer_not_installed")
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, timeout=10, stderr=subprocess.DEVNULL)
        dirty = subprocess.check_output(["git", "diff", "HEAD", "--", "radar", "pyproject.toml"],
                                        cwd=ROOT, timeout=10, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        raise ValueError("radar_producer_not_installed") from None
    if head.decode().strip() != REVISION or dirty:
        raise ValueError("radar_producer_version_changed")


def projection(db, source_id):
    day = utcnow().astimezone(ZoneInfo("Asia/Taipei")).date().isoformat()
    row = db.get(SystemSetting, receipt_key(source_id, day)) if source_id else None
    return dict(row.value) if row else None


def ensure_daily(db, source, config, now=None):
    """One invocation per local day; an interrupted invocation is not dispatched again."""
    from .discovery_runtime import settings
    from .radar_discovery import MAX_BYTES, read_report

    if not config.get("auto_daily"):
        return
    now = (now or utcnow()).astimezone(ZoneInfo("Asia/Taipei"))
    if now.hour < settings(db, source.owner_user_id)["daily_hour"]:
        return
    day = now.date().isoformat()
    validate_install(config)
    work = ROOT / ".aics-daily"
    work.mkdir(exist_ok=True)
    with (work / "producer.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("radar_generation_busy") from None
        key = receipt_key(source.id, day)
        row = db.get(SystemSetting, key, populate_existing=True)
        if row:
            state = dict(row.value)
            if state.get("status") == "running":
                state.update(status="unknown", reason="radar_generation_interrupted")
                row.value = state
                db.commit()
            if state.get("status") != "succeeded":
                raise ValueError(state.get("reason") or "radar_generation_unknown")
            parsed = read_report(config["report_path"], producer_version="0.4.0", producer_revision=REVISION)
            if parsed["report_hash"] != state.get("report_hash"):
                raise ValueError("radar_generated_report_changed")
            return
        state = {"business_date": day, "status": "running", "started_at": utcnow().isoformat(),
                 "source_id": source.id, "producer_revision": REVISION, "attempts": 1,
                 "mode": "free_github_hf", "origin": "existing_discovery_catchup"}
        row = SystemSetting(key=key, value=state)
        db.add(row)
        # Commit before launching: a crash must not erase the dispatch receipt.
        db.commit()
        state = dict(state)
        try:
            output = work / day
            output.mkdir(exist_ok=True)
            cfg = output / "free-config.json"
            cfg.write_text(json.dumps({"lang": "zh", "x_accounts": {"labs": [], "bloggers": []},
                                      "sitemaps": {}, "gsc": {}, "usecases": {"per_day": 0},
                                      "tutorials": {"max_leads": 0}}))
            env = {key: value for key, value in os.environ.items()
                   if key in {"PATH", "HOME", "LANG", "SSL_CERT_FILE", "SSL_CERT_DIR",
                              "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY",
                              "http_proxy", "https_proxy", "all_proxy", "no_proxy"}}
            env.update(TZ="Asia/Taipei", PYTHONNOUSERSITE="1")
            result = subprocess.run([str(ROOT / ".venv/bin/python3.12"), "-m", "radar", "daily",
                                     "--config", str(cfg), "--state", str(ROOT / "state"),
                                     "--skip", SKIP, "--out", str(output / "report.md")],
                                    cwd=ROOT, env=env, timeout=TIMEOUT, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL, check=False)
            if result.returncode:
                raise ValueError("radar_generation_failed")
            report = output / "report.json"
            parsed = read_report(str(report), producer_version="0.4.0", producer_revision=REVISION)
            if {"hf_error", "breakout_error"}.issubset(parsed["issues"]):
                raise ValueError("radar_generation_sources_failed")
            # Keep the dated output as evidence; consumers only see a complete validated file.
            with report.open("rb") as stream:
                raw = stream.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise ValueError("radar_report_too_large")
            staged = work / "publish.json"
            staged.write_bytes(raw)
            os.replace(staged, config["report_path"])
            state.update(status="succeeded", report_hash=parsed["report_hash"], counts=parsed["counts"],
                         issues=parsed["issues"], output_path=str(report))
        except subprocess.TimeoutExpired:
            state.update(status="unknown", reason="radar_generation_timeout")
        except (OSError, ValueError, TypeError, KeyError) as exc:
            code = str(exc)
            state.update(status="failed", reason=code if code.startswith("radar_") and len(code) < 100
                         else "radar_generation_failed")
        state["finished_at"] = utcnow().isoformat()
        row.value = state
        db.commit()
        if state["status"] != "succeeded":
            raise ValueError(state["reason"])
