"""Each video shot as a slot that takes material from any source.

Nothing new is stored here: the slot is read from the current shot list (video draft, or the shot plan before
a draft exists) and from this piece's material-match runs, so it cannot disagree with either.
"""

from __future__ import annotations

import copy
from types import SimpleNamespace

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ContentMasterRevision, MaterialMatchRun, User, WorkflowRun, WorkflowStepAttempt, utcnow
from . import material_matching
from .content_masters import owned_unit

BRIEF_FIELDS = ("query_zh", "queries_en", "keywords_en", "t2v_prompt", "frame_prompt", "prompt", "gen_mode", "footage", "must_show", "brief_version", "brief_edited")
TOP_CANDIDATES = 4


def review_url(project_id: int, unit_id: int) -> str:
    return f"/projects/{project_id}/units/{unit_id}/production?panel=shots"


def _plan(db: Session, user: User, project_id: int, unit_id: int) -> list[dict]:
    from . import agent_review

    attempt = db.scalar(select(WorkflowStepAttempt).join(WorkflowRun, WorkflowRun.id == WorkflowStepAttempt.run_id)
                        .where(WorkflowRun.content_unit_id == unit_id, WorkflowStepAttempt.node_id == "shots",
                               WorkflowStepAttempt.status == "succeeded").order_by(WorkflowStepAttempt.id.desc()))
    candidates = ((attempt.output_json or {}).get("candidates") or []) if attempt else []
    if not candidates:
        return []
    chosen = None
    try:
        stage = next((item for item in agent_review.stages(db, user, project_id, unit_id, attempt.run_id)["stages"] if item["node_id"] == "shots"), None)
        chosen = ((stage or {}).get("accepted") or {}).get("candidate_id")
    except Exception:  # noqa: BLE001 A recipe that cannot be resolved still has a readable plan.
        db.rollback()
    candidate = next((item for item in candidates if item.get("id") == chosen), candidates[0])
    body = candidate.get("payload") or candidate.get("content") or {}
    return [{"id": shot["id"], "order": shot["order"], "label": f"镜头 {shot['order'] + 1}", "narration": shot.get("script") or "",
             "visual": shot.get("visual") or "", "purpose": shot.get("purpose") or "",
             "requirements": shot.get("asset_requirements") or [], "duration_ms": round((shot.get("duration_seconds") or 0) * 1000),
             "bound_revision_id": None, "route": None}
            for shot in sorted(body.get("shots") or [], key=lambda item: item["order"])]


def _shots(db: Session, user: User, project_id: int, unit_id: int) -> tuple[str, list[dict], object]:
    plan = _plan(db, user, project_id, unit_id)
    master = db.scalar(select(ContentMasterRevision).where(ContentMasterRevision.content_unit_id == unit_id)
                       .order_by(ContentMasterRevision.id.desc()))
    shots = (master.payload_json or {}).get("shots") if master else None
    if not shots:
        return "plan", plan, None
    first = db.scalar(select(ContentMasterRevision.created_at).where(ContentMasterRevision.content_unit_id == unit_id)
                      .order_by(ContentMasterRevision.id))
    blocks = {block["id"]: block.get("text") or "" for block in (master.payload_json.get("script") or {}).get("blocks", [])}
    by_order = {item["order"]: item for item in plan}
    items = []
    for shot in sorted(shots, key=lambda item: item["order"]):
        planned = by_order.get(shot["order"], {})
        items.append({"id": shot["id"], "order": shot["order"], "label": f"镜头 {shot['order'] + 1}",
                      "narration": blocks.get(shot.get("script_block_id"), "") or planned.get("narration", ""),
                      "visual": planned.get("visual") or shot.get("label") or "", "purpose": shot.get("purpose") or "",
                      "requirements": planned.get("requirements", []), "duration_ms": shot.get("duration_ms"),
                      "bound_revision_id": shot.get("source_material_revision_id"),
                      "route": (shot.get("production") or {}).get("source_mode")})
    return "draft", items, first


def _slot_id(run: MaterialMatchRun, segment_id: str, source: str, draft_since, plan_order: dict, draft_by_order: dict) -> str | None:
    # The draft numbers shots from 1 while the plan numbers from 0; runs made before the draft use plan ids.
    if source == "draft" and draft_since is not None and run.created_at is not None and run.created_at < draft_since:
        order = plan_order.get(segment_id)
        return draft_by_order.get(order) if order is not None else None
    return segment_id


def view(db: Session, user: User, project_id: int, unit_id: int) -> dict:
    owned_unit(db, project_id, unit_id, user)
    source, shots, draft_since = _shots(db, user, project_id, unit_id)
    plan_order = {item["id"]: item["order"] for item in _plan(db, user, project_id, unit_id)} if source == "draft" else {}
    draft_by_order = {item["order"]: item["id"] for item in shots}
    runs = db.scalars(select(MaterialMatchRun).where(MaterialMatchRun.owner_user_id == user.id, MaterialMatchRun.unit_id == unit_id,
                                                     MaterialMatchRun.scope == "shots").order_by(MaterialMatchRun.id)).all()
    slots = {item["id"]: {**item, "brief": None, "latest": None, "picks": [], "candidate_count": 0, "autofill": None} for item in shots}
    for run in runs:
        material_matching._settle(db, run)
        for segment in (run.result_json or {}).get("segments", []):
            slot = slots.get(_slot_id(run, segment["id"], source, draft_since, plan_order, draft_by_order))
            if slot is None:
                continue
            if any(segment.get(key) for key in BRIEF_FIELDS):
                slot["brief"] = {key: segment.get(key) for key in BRIEF_FIELDS} | {"run_id": run.id, "segment_id": segment["id"]}
            slot["latest"] = {"run_id": run.id, "segment_id": segment["id"], "status": run.status}
            row = ((run.result_json or {}).get("autofill") or {}).get("rows", {}).get(segment["id"])
            if row:
                slot["autofill"] = row
            slot["candidate_count"] = len(segment.get("candidates") or [])
            for candidate in segment.get("candidates") or []:
                saved = candidate.get("accepted")
                if saved and all(pick["material_revision_id"] != saved["material_revision_id"] for pick in slot["picks"]):
                    slot["picks"].append({"material_revision_id": saved["material_revision_id"], "title": candidate.get("title"),
                                          "provider_label": candidate.get("provider_label"), "media_type": candidate.get("media_type"),
                                          "uploaded": bool(candidate.get("uploaded")), "run_id": run.id,
                                          **({"auto": candidate["auto"]} if candidate.get("auto") else {})})
    items = []
    for slot in slots.values():
        slot["status"] = "chosen" if slot["bound_revision_id"] or slot["picks"] else "candidates" if slot["candidate_count"] else "missing"
        brief = slot["brief"] or {}
        slot["brief_stale"] = not brief.get("brief_edited") and brief.get("brief_version") != material_matching.PROMPT_VERSION
        items.append(slot)
    return {"source": source, "project_id": project_id, "unit_id": unit_id, "review_url": review_url(project_id, unit_id),
            "counts": {key: sum(item["status"] == key for item in items) for key in ("missing", "candidates", "chosen")},
            "shots": items}


def update_brief(db: Session, user: User, project_id: int, unit_id: int, shot_id: str, values: dict) -> dict:
    owned_unit(db, project_id, unit_id, user, mutate=True)
    slot = next((item for item in view(db, user, project_id, unit_id)["shots"] if item["id"] == shot_id), None)
    if slot is None:
        raise HTTPException(404, {"code": "shot_slot_not_found"})
    if not slot["brief"]:
        raise HTTPException(409, {"code": "shot_slot_brief_missing"})
    run = db.get(MaterialMatchRun, slot["brief"]["run_id"])
    result = copy.deepcopy(run.result_json or {})
    for segment in result.get("segments", []):
        if segment["id"] == slot["brief"]["segment_id"]:
            changes = {key: value for key, value in values.items() if value is not None}
            # Switching the generation mode is a choice, not an edit, so later prompt refreshes still apply.
            segment.update(changes, **({"brief_edited": True} if set(changes) - {"gen_mode"} else {}))
    run.result_json = result
    run.updated_at = utcnow()
    db.commit()
    return view(db, user, project_id, unit_id)


def ensure_run(db: Session, user: User, project_id: int, unit_id: int, shot_id: str) -> dict:
    """A slot with no search yet still takes uploads; it gets a finished run holding just this shot."""
    owned_unit(db, project_id, unit_id, user, mutate=True)
    slot = next((item for item in view(db, user, project_id, unit_id)["shots"] if item["id"] == shot_id), None)
    if slot is None:
        raise HTTPException(404, {"code": "shot_slot_not_found"})
    if slot["latest"] and slot["latest"]["status"] not in {"queued", "running"}:
        return {"run_id": slot["latest"]["run_id"], "segment_id": slot["latest"]["segment_id"]}
    text = "；".join(filter(None, [slot["narration"], slot["visual"]]))[:2000] or slot["label"]
    segment = {"id": shot_id, "order": slot["order"], "text": text, "label": slot["label"], "role": "proof", "media_type": "video",
               "status": "gap", "candidates": [], "main_id": None}
    run = MaterialMatchRun(owner_user_id=user.id, project_id=project_id, unit_id=unit_id, scope="shots",
                           title=f"镜头上传 · {slot['label']}", source_json={"shots": [{"id": shot_id, "label": slot["label"], "text": text}]},
                           settings_json={"aspect": "9:16", "min_short_side": 720, "providers": [], "strict_aspect": False},
                           status="completed", cancel_requested=False, progress_json={"stage": "done", "done": 1, "total": 1},
                           result_json={"segments": [segment], "providers": {}})
    db.add(run)
    db.commit()
    return {"run_id": run.id, "segment_id": shot_id}


def shot_text(slot: dict) -> str:
    seconds = round((slot.get("duration_ms") or 0) / 1000, 1)
    return "；".join(filter(None, [slot["narration"] and f"口播：{slot['narration']}", slot["visual"] and f"画面：{slot['visual']}",
                                   slot["purpose"], *slot["requirements"], seconds and f"时长：{seconds:g} 秒"]))[:4000] or slot["label"]


def write_briefs(db: Session, user: User, project_id: int, unit_id: int) -> dict:
    """Briefs written by an older planner get current ones from the planner alone, without searching again; briefs the user edited are kept."""
    owned_unit(db, project_id, unit_id, user, mutate=True)
    lacking = [item for item in view(db, user, project_id, unit_id)["shots"] if not (item["brief"] or {}).get("brief_edited")
               and (item["brief"] or {}).get("brief_version") != material_matching.PROMPT_VERSION]
    if not lacking:
        return view(db, user, project_id, unit_id)
    shots = [{"id": item["id"], "label": item["label"],
              "text": shot_text(item)} for item in lacking]
    try:
        planned, _, _ = material_matching._plan(db, SimpleNamespace(scope="shots", source_json={"shots": shots}))
    except material_matching.MatchError as exc:
        db.commit()
        raise HTTPException(502, {"code": exc.code}) from None
    planned = {item["id"]: item for item in planned}
    for item in lacking:
        values = {key: planned[item["id"]][key] for key in BRIEF_FIELDS if item["id"] in planned and planned[item["id"]].get(key)}
        if not values:
            continue
        if item["brief"]:
            run = db.get(MaterialMatchRun, item["brief"]["run_id"])
            result = copy.deepcopy(run.result_json or {})
            for segment in result.get("segments", []):
                if segment["id"] == item["brief"]["segment_id"]:
                    segment.update({key: value for key, value in values.items() if key in {"t2v_prompt", "frame_prompt", "prompt", "brief_version"} or not segment.get(key)})
            run.result_json = result
            run.updated_at = utcnow()
        else:
            target = ensure_run(db, user, project_id, unit_id, item["id"])
            run = db.get(MaterialMatchRun, target["run_id"])
            result = copy.deepcopy(run.result_json or {})
            for segment in result.get("segments", []):
                if segment["id"] == target["segment_id"]:
                    segment.update(values)
            run.result_json = result
        db.commit()
    return view(db, user, project_id, unit_id)
