"""After a video 导演稿 is adopted: make the master edit-ready without user clicks.

Steps, each reusing an existing service, stopping at the first failure with its name:
place single picks → save the master → create and queue the edit task. The DaVinci / AE split must already be
recorded by the external model (video_chain.prepare_edit); the platform no longer decides it with a model.
"""

from __future__ import annotations

import copy
import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ContentMasterRevision, MaterialRevision, SystemSetting, User
from . import shot_slots

STEPS = {"place": "把素材放进主稿", "decide": "判断哪些镜头要 AE", "save": "保存主稿", "edit": "建剪辑任务"}


class HandoffError(Exception):
    def __init__(self, step: str, reason: str):
        super().__init__(reason)
        self.step, self.reason = step, reason


def _code(exc: Exception) -> str:
    detail = getattr(exc, "detail", None) or getattr(exc, "body", None)
    if isinstance(detail, dict):
        return str(detail.get("message") or detail.get("code") or detail)
    return str(detail or exc) or type(exc).__name__


def _latest_master(db: Session, unit_id: int) -> ContentMasterRevision:
    master = db.scalar(select(ContentMasterRevision).where(ContentMasterRevision.content_unit_id == unit_id)
                       .order_by(ContentMasterRevision.revision_no.desc()).limit(1))
    if master is None or master.payload_schema != "video.master.v2":
        raise HandoffError("place", "还没有已保存的视频主稿")
    return master


def _usable(revision: MaterialRevision | None) -> bool:
    mime = (revision.mime_type or "") if revision else ""
    return bool(revision and mime.split("/")[0] in {"image", "video"}
                and (revision.model_use_allowed or revision.public_use_allowed)
                and revision.status not in {"revoked", "archived"})


def _postproduction(document: dict, ae: dict[str, str]) -> dict:
    width, height = document.get("aspect_ratio") or [9, 16]
    resolution = [1080, 1920] if height >= width else [1920, 1080]
    order = [shot["id"] for shot in sorted(document["shots"], key=lambda item: item["order"]) if shot["id"] in ae]
    durations = {shot["id"]: shot["duration_ms"] for shot in document["shots"]}
    return {"schema": "video.postproduction.v1", "phase": "rough_cut", "fps": 30, "resolution": resolution,
            "ae_shot_ids": order, "feedback": [],
            "ae_compositions": [{"shot_id": shot_id, "role_id": "ae_intermediate" if len(order) == 1 else f"ae_intermediate_{index + 1}",
                                 "duration_ms": durations[shot_id], "resolution": resolution, "fps": 30, "alpha_required": False}
                                for index, shot_id in enumerate(order)]}


def _save(db: Session, user: User, project_id: int, unit_id: int, master: ContentMasterRevision, document: dict, summary: dict,
          edit_summary: dict | None = None) -> int:
    from .content_masters import get_revision, save_revision
    from .video_documents import _expected_media

    current = get_revision(db, project_id, unit_id, master.id, user)
    hashes = {row["material_revision_id"]: row["content_hash"] for row in current["assets"]}
    refs = []
    for ref in _expected_media(document):
        content_hash = hashes.get(ref["material_revision_id"])
        if content_hash is None:
            content_hash = db.get(MaterialRevision, ref["material_revision_id"]).content_hash
        refs.append({**ref, "content_hash": content_hash})
    evidence = [{key: row[key] for key in ("fact_pack_item_id", "snapshot_checksum", "role", "locator", "sort_order")}
                for row in current["evidence"]]
    saved = save_revision(db, project_id=project_id, unit_id=unit_id, user=user, payload={
        "expected_revision": master.revision_no, "expected_context_hash": current["context_hash"],
        "idempotency_key": f"handoff:{uuid.uuid4().hex}", "payload_schema": "video.master.v2", "payload": document,
        "content_form": current.get("content_form"), "parent_revision_id": master.id, "source_kind": "user_edit",
        "edit_summary": edit_summary if edit_summary is not None else {"auto_handoff": summary}, "asset_refs": refs, "evidence_refs": evidence})
    return saved["id"]


def run(db: Session, user: User, project_id: int, unit_id: int) -> dict:
    try:
        return _run(db, user, project_id, unit_id)
    except HandoffError as exc:
        db.rollback()
        raise HTTPException(409, {"code": "edit_handoff_failed", "step": exc.step,
                                  "message": f"{STEPS[exc.step]}没完成：{exc.reason}"}) from None


def _run(db: Session, user: User, project_id: int, unit_id: int) -> dict:
    step = "place"
    try:
        master = _latest_master(db, unit_id)
        document = copy.deepcopy(master.payload_json)
        slots = {slot["id"]: slot for slot in shot_slots.view(db, user, project_id, unit_id)["shots"]}
        placed, waiting, gaps = [], [], []
        for shot in document["shots"]:
            picks = (slots.get(shot["id"]) or {}).get("picks") or []
            if shot.get("source_material_revision_id"):
                continue
            if len(picks) > 1:
                waiting.append(shot["id"])
            elif len(picks) == 1 and _usable(db.get(MaterialRevision, picks[0]["material_revision_id"])):
                shot["source_material_revision_id"] = picks[0]["material_revision_id"]
                placed.append(shot["id"])
            else:
                gaps.append(shot["id"])

        step = "decide"
        ae, note = {}, None
        if not document.get("postproduction"):
            # Video decisions belong to the external model (video_chain.prepare_edit); the platform calls no model here.
            raise HandoffError(step, "哪些镜头用 AE 由 Claude Code 决定，请在 Claude Code 里继续这条视频")
        if not placed:
            existing = master.edit_summary_json or {}
            ae = (existing.get("auto_handoff") or {}).get("ae") or {}

        step = "save"
        summary = {"ae": ae, "note": note, "placed": placed, "waiting": waiting, "gaps": gaps}
        master_id = master.id
        # Save only when something changed, so repeating 准备剪辑 keeps the same master and edit task.
        if placed or not master.payload_json.get("postproduction"):
            master_id = _save(db, user, project_id, unit_id, master, document, summary)

        step = "edit"
        edit = _edit_task(db, user, project_id, unit_id, waiting, gaps)
    except HandoffError:
        raise
    except HTTPException as exc:
        raise HandoffError(step, _code(exc)) from None
    except Exception as exc:  # noqa: BLE001 The page shows which step stopped and why.
        raise HandoffError(step, _code(exc)) from None
    return {"master_id": master_id, **summary, "edit": edit, "archive": _archive(db, project_id, unit_id, slots)}


def _archive(db: Session, project_id: int, unit_id: int, slots: dict) -> dict:
    """The adopted draft's files move into the project folder; anything that cannot move waits for next time."""
    from . import project_folders

    try:
        master = _latest_master(db, unit_id)
        result = project_folders.archive_master(db, project_id, master.payload_json, slots)
        project_folders.write_director_draft(db, project_id, master.revision_no, master.payload_json)
    except Exception as exc:  # noqa: BLE001 Archiving never blocks the edit task.
        db.rollback()
        return {"moved": 0, "referenced": 0, "pending": [{"reason": _code(exc)}]}
    return {"moved": len(result["moved"]), "referenced": len(result["referenced"]), "pending": result["pending"]}


def _edit_task(db: Session, user: User, project_id: int, unit_id: int, waiting: list, gaps: list) -> dict:
    from . import edit_agent
    from .web_video_handoff import prepare_edit

    if waiting or gaps:
        return {"status": "skipped", "reason": "还有镜头没定素材，定好后再点「准备剪辑」"}
    master = _latest_master(db, unit_id)
    # One edit task per saved master: repeating 准备剪辑 on the same master reuses it.
    result = prepare_edit(db, project_id, unit_id, {"source_master_revision_id": master.id,
                                                    "idempotency_key": f"handoff-edit-{master.id}"}, user)
    execution_id = result["execution"]["id"]
    edit_agent.queue(db, execution_id)
    db.commit()
    return {"status": "queued", "execution_id": execution_id}


def status(db: Session, user: User, project_id: int, unit_id: int) -> dict:
    from .content_masters import owned_unit

    owned_unit(db, project_id, unit_id, user)
    master = db.scalar(select(ContentMasterRevision).where(ContentMasterRevision.content_unit_id == unit_id)
                       .order_by(ContentMasterRevision.revision_no.desc()).limit(1))
    summary = ((master.edit_summary_json or {}).get("auto_handoff") if master else None) or {}
    post = ((master.payload_json or {}).get("postproduction") if master else None) or {}
    needs = False
    if master is not None and master.payload_schema == "video.master.v2":
        from ..models import CreativeExecution, CreativeExecutionPackage

        source = master
        # A save that only merged duplicate entries keeps the same files, so the earlier edit task still counts.
        while (source.edit_summary_json or {}).get("dedupe") and source.parent_revision_id:
            source = db.get(ContentMasterRevision, source.parent_revision_id)
        task = db.scalar(select(CreativeExecution.id).join(CreativeExecutionPackage, CreativeExecutionPackage.id == CreativeExecution.package_id)
                         .where(CreativeExecution.owner_user_id == user.id, CreativeExecution.content_unit_id == unit_id,
                                CreativeExecution.executor_key == "codex-video-production",
                                CreativeExecutionPackage.source_master_revision_id == source.id).limit(1))
        needs = not post or task is None or any(not shot.get("source_material_revision_id") for shot in master.payload_json.get("shots", []))
    from .project_folders import PENDING

    archive = db.get(SystemSetting, PENDING)
    return {"master_id": master.id if master else None, "decided": bool(post),
            "archive_pending": len(((archive.value or {}) if archive else {}).get(str(project_id), [])), "needs_handoff": needs, "ae": summary.get("ae") or {},
            "ae_shot_ids": post.get("ae_shot_ids", []), "note": summary.get("note"),
            "waiting": summary.get("waiting", []), "gaps": summary.get("gaps", [])}
