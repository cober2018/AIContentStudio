"""Agent side of the review loop: run stages and read the user's decisions, never decide."""

from __future__ import annotations

import json
import time

from sqlalchemy.orm import Session

from ..models import User
from .stage_contracts import digest

MAX_WAIT_SECONDS = 25
_EXCERPT = 1500


def review_url(project_id: int, unit_id: int, node_id: str | None = None) -> str:
    return f"/projects/{project_id}/units/{unit_id}/production" + (f"?stage={node_id}&open=result" if node_id else "")


def match_review_url(run_id: int) -> str:
    return f"/materials?tab=match&run={run_id}"


def _text(value) -> str:
    """Readable excerpt of a candidate: canvas text for graphics, content otherwise."""
    if isinstance(value, dict) and isinstance(value.get("canvases"), list):
        parts = []
        for canvas in value["canvases"]:
            texts = ["".join(run["text"] for run in layer.get("runs", [])) for layer in canvas.get("layers", []) if layer.get("type") == "text"]
            parts.append(f"[{canvas.get('id')}] " + " / ".join(texts))
        return "\n".join(parts)[:_EXCERPT]
    return json.dumps(value, ensure_ascii=False)[:_EXCERPT]


def _candidates(output: dict) -> list[dict]:
    items = []
    for candidate in output.get("candidates") or []:
        body = candidate.get("payload") if "payload" in candidate else candidate.get("content", candidate)
        items.append({"candidate_id": candidate.get("candidate_id", candidate.get("id")),
                      "candidate_hash": candidate.get("candidate_hash"), "payload_schema": candidate.get("payload_schema"),
                      "canvas_count": len(body["canvases"]) if isinstance(body, dict) and isinstance(body.get("canvases"), list) else None,
                      "excerpt": _text(body)})
    return items


def stages(db: Session, user: User, project_id: int, unit_id: int, run_id: int | None) -> dict:
    from .creation_recipes import recipe_view

    view = recipe_view(db, project_id, unit_id, user, run_id=run_id)
    return {"run_id": view.get("run_id"), "readonly": view.get("readonly"), "review_url": review_url(project_id, unit_id),
            "stages": [{**{key: stage.get(key) for key in ("node_id", "label", "status", "requires_human_acceptance", "dependencies", "blockers")},
                        "last_attempt": {key: (stage.get("last_attempt") or {}).get(key) for key in ("id", "status")} if stage.get("last_attempt") else None,
                        "accepted": {key: stage["accepted_target"].get(key) for key in ("decision", "candidate_id", "entity_id", "output_kind", "summary")}
                        if stage.get("accepted_target") else None}
                       for stage in view.get("stages", [])]}


def start_run(db: Session, user: User, project_id: int, unit_id: int) -> dict:
    from ..routers.content_projects import ProjectRunIn, start_project_run

    run = start_project_run(ProjectRunIn(params={}), project_id, unit_id, db, user)
    return {"run_id": run["id"], "status": run.get("status"), "review_url": review_url(project_id, unit_id)}


def preview(db: Session, user: User, project_id: int, unit_id: int, run_id: int, node_id: str, override: dict) -> dict:
    from .creation_recipes import preview_stage

    result = preview_stage(db, project_id, unit_id, node_id, user, run_id=run_id, stage_override=override)
    stack = (result.get("creative_configuration") or {}).get("method_stack") or []
    return {"node_id": node_id, "run_id": run_id, "ready": result.get("ready"), "blockers": result.get("blockers"),
            "resolution_hash": result.get("resolution_hash"), "model": (result.get("model") or {}).get("model"),
            "methods": [item.get("skill_ref") or item.get("artifact_id") for item in stack]}


def _result(db, user, project_id, unit_id, node_id, run_id, attempt_id=None, invocation_key=None) -> dict:
    from .creation_recipes import stage_result

    return stage_result(db, project_id, unit_id, node_id, user, run_id=run_id, attempt_id=attempt_id, invocation_key=invocation_key)


def project_result(db: Session, project_id: int, unit_id: int, result: dict) -> dict:
    from ..models import WorkflowStepAttempt

    output = result.get("output") or {}
    attempt = db.get(WorkflowStepAttempt, result["attempt_id"])
    quality = output.get("quality") or {}
    return {"run_id": result["run_id"], "node_id": result["node_id"], "attempt_id": result["attempt_id"],
            "status": result["status"], "is_current": result.get("is_current"),
            "error": attempt.error if attempt else None,
            "candidates": _candidates(output),
            "quality": {"status": quality.get("status"), "issues": [item.get("reason") for item in quality.get("issues", [])][:30]} if quality else None,
            "accepted": bool(result.get("accepted_target")),
            "review_url": review_url(project_id, unit_id, result["node_id"])}


def run(db: Session, user: User, project_id: int, unit_id: int, run_id: int, node_id: str, *,
        expected_resolution_hash: str, invocation_key: str, override: dict) -> dict:
    from .stage_invocations import execute_stage

    result = execute_stage(db, project_id, unit_id, node_id, user, run_id=run_id, expected_resolution_hash=expected_resolution_hash,
                           invocation_key=invocation_key, stage_override=override)
    return result_view(db, user, project_id, unit_id, node_id, run_id, attempt_id=result["attempt_id"])


def result_view(db: Session, user: User, project_id: int, unit_id: int, node_id: str, run_id: int, *,
                attempt_id: int | None = None, invocation_key: str | None = None) -> dict:
    return project_result(db, project_id, unit_id, _result(db, user, project_id, unit_id, node_id, run_id, attempt_id, invocation_key))


def _decision(db, user, project_id, unit_id, node_id, run_id, attempt_id, invocation_key) -> dict:
    from .stage_feedback import feedback_events

    result = _result(db, user, project_id, unit_id, node_id, run_id, attempt_id, invocation_key)
    events = [event.payload_json or {} for event in feedback_events(db, project_id, result["attempt_id"])]
    decided = next((event for event in reversed(events) if event.get("decision") != "commented"), None)
    notes = [event.get("note") for event in events if event.get("note")]
    accepted = result.get("accepted_target")
    if decided:
        state = decided["decision"]
    elif accepted:
        state = "accepted"
    elif result["status"] == "waiting_input":
        state = "waiting_for_you"
    else:
        # Not a user decision: the stage itself is running, failed, stale or blocked.
        state = f"stage_{result['status']}"
    if state == "waiting_for_you" and notes:
        state = "commented"
    continuation = []
    if state in {"accepted", "accepted_with_edits"}:
        view = stages(db, user, project_id, unit_id, run_id)
        continuation = [{"node_id": item["node_id"], "status": item["status"]} for item in view["stages"]
                        if node_id in (item.get("dependencies") or []) and item["status"] != "not_started"]
    return {"run_id": run_id, "node_id": node_id, "attempt_id": result["attempt_id"], "state": state,
            "note": notes[-1] if notes else None, "notes": notes[-5:],
            "candidate_id": (decided or {}).get("candidate_id"),
            "accepted": {key: accepted.get(key) for key in ("output_kind", "entity_id", "accepted_hash") if key in accepted} if accepted else None,
            "continuation": continuation, "review_url": review_url(project_id, unit_id, node_id)}


def decision(db: Session, user: User, project_id: int, unit_id: int, node_id: str, run_id: int, *,
             attempt_id: int | None, invocation_key: str | None, wait_seconds: int) -> dict:
    """Bounded wait: the transport has no push, so the agent polls again while it is still the user's turn."""
    deadline = time.monotonic() + min(max(wait_seconds, 0), MAX_WAIT_SECONDS)
    while True:
        value = _decision(db, user, project_id, unit_id, node_id, run_id, attempt_id, invocation_key)
        if value["state"] not in {"waiting_for_you", "stage_running"} or time.monotonic() >= deadline:
            return value
        db.rollback()
        time.sleep(1)


def _match_view(run: dict) -> dict:
    segments = []
    for segment in run.get("segments", []):
        candidates = segment.get("candidates", [])
        segments.append({"id": segment["id"], "label": segment.get("label"), "text": (segment.get("text") or "")[:300],
                         "status": segment.get("status"), "main_id": segment.get("main_id"),
                         "chosen_id": segment.get("chosen_id"),
                         "chosen": next((item.get("accepted") for item in candidates if item["id"] == segment.get("chosen_id")), None),
                         "chosen_uploaded": next((bool(item.get("uploaded")) for item in candidates if item["id"] == segment.get("chosen_id")), False),
                         # Every accepted candidate is a pick; runs accepted before picked_ids existed only recorded `accepted`.
                         "picks": [{"candidate_id": item["id"], "uploaded": bool(item.get("uploaded")), **item["accepted"]}
                                   for item in candidates if item.get("accepted")],
                         "rejected": segment.get("rejected"), "request": segment.get("request"),
                         "candidates": [{"id": item["id"], "provider": item.get("provider"), "title": (item.get("title") or "")[:120],
                                         "media_type": item.get("media_type"), "score": item.get("score"),
                                         "eligible_main": item.get("eligible_main"), "reason": (item.get("reason") or "")[:300],
                                         "license": (item.get("license") or {}).get("accept_code")} for item in candidates[:6]]})
    return {"id": run["id"], "status": run["status"], "title": run.get("title"), "project_id": run.get("project_id"),
            "unit_id": run.get("unit_id"), "project": run.get("project"), "unit": run.get("unit"), "progress": run.get("progress"), "error_code": run.get("error_code"),
            "segments": segments, "review_url": match_review_url(run["id"])}


def _match_state(view: dict) -> str:
    return digest({"status": view["status"], "segments": [[item["id"], item["chosen_id"], item["rejected"]] for item in view["segments"]]})


def start_match(db: Session, user: User, payload: dict) -> dict:
    from . import material_matching

    return _match_view(material_matching.start(db, user, payload))


def read_match(db: Session, user: User, run_id: int, wait_seconds: int) -> dict:
    """Returns once the run finishes or the user picks or rejects something, or when the wait ends."""
    from . import material_matching

    deadline = time.monotonic() + min(max(wait_seconds, 0), MAX_WAIT_SECONDS)
    first = _match_view(material_matching.read(db, user, run_id))
    before = _match_state(first)
    while time.monotonic() < deadline:
        db.rollback()
        time.sleep(1)
        current = _match_view(material_matching.read(db, user, run_id))
        if _match_state(current) != before:
            return current
    return first
