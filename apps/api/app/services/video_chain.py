"""Video made end to end by the external model over MCP; the platform keeps records and asks the user.

导演稿 (with a material request per shot) → user → materials, voiceover, DaVinci / AE → 小样 → user → 排版 → 成片 → user.
The platform calls no model here. Saves that do not change picture content (materials, voiceover, edit preparation,
duplicate merges) keep the 导演稿 the user approved; any other save is a new 导演稿 that needs approval again.
"""

from __future__ import annotations

import copy
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from ..models import (
    ContentMasterRevision,
    ContentUnit,
    CreativeExecution,
    CreativeExecutionOutput,
    MaterialRevision,
    ProjectMaterialReference,
    SystemSetting,
    User,
)

KEY = "video_chain"
# Returned with the brief so any external model (not only one with the repo's skills) follows the same chain.
RULES = [
    "你主导整条视频；平台不调用自己的模型。三处停下等用户：导演稿、小样、成片。有意见就出下一版再停。",
    "导演稿：完整 video.master.v2；每个镜头 board 含 message/visual/camera/speaker/sound/notes/material_request。material_request 写清画面必须有什么、景别、时长、实拍还是图形、横竖屏。一镜一个意思，景别和运镜要有变化，同一画面不重复用。",
    "导演稿采用后：先用用户新放进库的素材，其余按 素材库 → 图库搜索 → 生图 → AE 模板 补齐；每个镜头用哪条由你定；回执写明哪些是用户给的、哪些是你找的或做的。",
    "小样、排版、成片都在达芬奇（剪辑、调色、声音、导出）和 AE（标题、字幕、包装、特效）里做；ffmpeg 只用于检查和转格式。",
    "剪辑照导演稿：画面内容要变就先存新导演稿；导演稿没写的细节和网络素材署名写进回执。",
]
EXECUTOR = "codex-video-production"
_KEEPS_DRAFT = {"material", "edit_prep"}


def _fail(code: str, message: str, status: int = 409):
    raise HTTPException(status, {"code": code, "message": message})


def _records(db: Session) -> dict:
    row = db.get(SystemSetting, KEY)
    return dict(row.value or {}) if row else {}


def _unit_record(db: Session, unit_id: int) -> dict:
    return copy.deepcopy(_records(db).get(str(unit_id)) or {"decisions": [], "tasks": []})


def _put(db: Session, unit_id: int, record: dict) -> None:
    row = db.get(SystemSetting, KEY)
    if row is None:
        row = SystemSetting(key=KEY, value={})
        db.add(row)
    value = dict(row.value or {})
    value[str(unit_id)] = record
    row.value = value
    flag_modified(row, "value")
    db.flush()


def _latest(db: Session, unit_id: int) -> ContentMasterRevision | None:
    return db.scalar(select(ContentMasterRevision).where(ContentMasterRevision.content_unit_id == unit_id)
                     .order_by(ContentMasterRevision.revision_no.desc()).limit(1))


def _keeps_draft(master: ContentMasterRevision) -> bool:
    summary = master.edit_summary_json or {}
    return summary.get("video_chain") in _KEEPS_DRAFT or bool({"voiceover", "dedupe", "auto_handoff"} & summary.keys())


def draft_root(db: Session, master: ContentMasterRevision | None) -> ContentMasterRevision | None:
    """The 导演稿 the current version stands on: walk back past saves that kept the picture content."""
    while master is not None and _keeps_draft(master) and master.parent_revision_id:
        master = db.get(ContentMasterRevision, master.parent_revision_id)
    return master


def _decision(record: dict, stage: str, target_id: int) -> dict | None:
    return next((item for item in reversed(record["decisions"]) if item["stage"] == stage and item["target_id"] == target_id), None)


def _task(db: Session, record: dict) -> tuple[dict | None, CreativeExecution | None]:
    if not record["tasks"]:
        return None, None
    task = record["tasks"][-1]
    return task, db.get(CreativeExecution, task["execution_id"])


def state(db: Session, user: User, project_id: int, unit_id: int) -> dict:
    from .content_masters import owned_unit

    owned_unit(db, project_id, unit_id, user)
    record = _unit_record(db, unit_id)
    root = draft_root(db, _latest(db, unit_id))
    if root is None or (root.edit_summary_json or {}).get("video_chain") != "draft":
        return {"state": "not_started", "label": "待开始", "detail": "在 Claude Code 里说「做这个视频」开始：先写导演稿和素材需求"}
    view = {"draft_master_id": root.id, "draft_revision_no": root.revision_no}
    decided = _decision(record, "draft", root.id)
    if decided is None:
        return {**view, "state": "draft_review", "label": "导演稿待你看", "detail": "看分镜和素材需求；有素材就放进素材库，然后采用或写修改意见"}
    if decided["decision"] == "changes":
        return {**view, "state": "draft_changes", "label": "导演稿按你的意见修改中", "notes": decided["notes"]}
    task, execution = _task(db, record)
    if task is None or task["draft_master_id"] != root.id:
        return {**view, "state": "making", "label": "制作中", "detail": "选素材、配音，准备剪小样"}
    phase = "sample" if task["phase"] == "rough_cut" else "final"
    view.update(execution_id=execution.id, execution_state=execution.state, phase=task["phase"])
    notes = _decision(record, phase, execution.id)
    if execution.state in {"prepared", "claimed", "in_progress"}:
        return {**view, "state": "making" if phase == "sample" else "finishing", "label": "剪小样中" if phase == "sample" else "排版中"}
    if execution.state == "result_ready" and notes and notes["decision"] == "approve":
        return {**view, "state": "finishing" if phase == "sample" else "done", "label": "排版中" if phase == "sample" else "已完成"}
    if execution.state == "result_ready":
        if notes and notes["decision"] == "changes":
            return {**view, "state": f"{phase}_changes", "label": "小样按你的意见修改中" if phase == "sample" else "成片按你的意见修改中", "notes": notes["notes"]}
        return {**view, "state": f"{phase}_review", "label": "小样待你看" if phase == "sample" else "成片待你看"}
    if execution.state == "accepted":
        return {**view, "state": "finishing" if phase == "sample" else "done", "label": "排版中" if phase == "sample" else "已完成"}
    return {**view, "state": "error", "label": "出错", "detail": execution.safe_reason or execution.state}


def cut_location(db: Session, user: User, project_id: int, unit_id: int, output_id: int):
    """The file behind the 小样 / 成片 the page plays: its library place once accepted, else the 导出/小样 copy."""
    from . import materials, project_folders
    from .creative_execution_files import work_root

    current = state(db, user, project_id, unit_id)
    output = db.get(CreativeExecutionOutput, output_id)
    if output is None or output.execution_id != current.get("execution_id") or output.role_id not in {"rough_cut", "final"}:
        _fail("video_chain_cut_not_found", "找不到这条片子", 404)
    if output.material_revision_id:
        revision = db.get(MaterialRevision, output.material_revision_id)
        path = materials.local_file_checked(db, revision) if revision is not None else None
        if path is not None:
            return path
    execution = db.get(CreativeExecution, output.execution_id)
    path = project_folders.sample_copy(db, execution, output)
    if path is None and output.staging_key:
        path = work_root(execution.owner_user_id, execution.id) / output.staging_key
    if path is None or not path.is_file():
        _fail("video_chain_cut_not_found", "片子文件不在了", 404)
    return path


def file_as_common(db: Session, user: User, project_id: int, unit_id: int, revision_id: int) -> dict:
    """The video model judged this material generic; it moves to 通用素材库 on the Mac."""
    from . import project_folders
    from .content_masters import owned_unit

    owned_unit(db, project_id, unit_id, user, mutate=True)
    revision = db.get(MaterialRevision, revision_id)
    used = db.scalar(select(ProjectMaterialReference.id).where(ProjectMaterialReference.project_id == project_id,
                     ProjectMaterialReference.material_revision_id == revision_id, ProjectMaterialReference.status == "active"))
    if revision is None or used is None:
        _fail("video_chain_material_not_in_project", "这条素材不在本项目里", 404)
    if project_folders.is_output(revision):
        _fail("video_chain_output_not_material", "小样 / 成片是成果，不放进通用素材库", 422)
    return project_folders.to_common(db, revision)


def decide(db: Session, user: User, project_id: int, unit_id: int, stage: str, decision: str, notes: list[dict]) -> dict:
    """The user's answer at one of the three stops. 通过 on 小样 / 成片 accepts that task's outputs."""
    from .content_masters import owned_unit

    owned_unit(db, project_id, unit_id, user, mutate=True)
    current = state(db, user, project_id, unit_id)
    expected = {"draft": "draft_review", "sample": "sample_review", "final": "final_review"}[stage]
    if current["state"] not in {expected, expected.replace("review", "changes")}:
        _fail("video_chain_not_waiting", f"现在不在等你看{ {'draft': '导演稿', 'sample': '小样', 'final': '成片'}[stage] }")
    if decision == "changes" and not any(str(item.get("note") or "").strip() for item in notes):
        _fail("video_chain_notes_required", "写一下要改哪里", 422)
    target = current["draft_master_id"] if stage == "draft" else current["execution_id"]
    accepted = None
    if decision == "approve" and stage != "draft":
        try:
            _accept_outputs(db, user, project_id, unit_id, target)
            accepted = True
        except HTTPException as exc:
            # Voice or timing saved after the 小样 (prep for the 成片) makes its source older than the master;
            # the approval still stands, the 小样 file is already in 导出/小样, and the 成片 is cut from the newest master.
            if stage != "sample" or (exc.detail or {}).get("code") != "creative_source_not_current":
                raise
            db.rollback()
            accepted = False
    record = _unit_record(db, unit_id)
    record["decisions"].append({"stage": stage, "target_id": target, "decision": decision, "outputs_accepted": accepted,
                                "notes": [{"time_ms": item.get("time_ms"), "note": str(item.get("note") or "")[:2000]} for item in notes][:50],
                                "by": user.email, "at": datetime.now(UTC).isoformat()})
    _put(db, unit_id, record)
    db.commit()
    return state(db, user, project_id, unit_id)


def _accept_outputs(db: Session, user: User, project_id: int, unit_id: int, execution_id: int) -> None:
    from . import creative_executions, project_folders

    unit = db.get(ContentUnit, unit_id)
    outputs = db.scalars(select(CreativeExecutionOutput).where(CreativeExecutionOutput.execution_id == execution_id)
                         .order_by(CreativeExecutionOutput.attempt_no)).all()
    latest = {}
    for output in outputs:
        latest[(output.role_id, output.output_index)] = output
    for output in latest.values():
        if output.state != "staged":
            continue
        execution = db.get(CreativeExecution, execution_id)
        db.refresh(execution)
        # Materials are allowed by default; project files (projects, manifests) stay private as the platform requires.
        shareable = output.kind in {"video", "image", "audio"}
        rights = {"rights_status": "cleared", "public_use_allowed": shareable, "model_use_allowed": shareable}
        payload = {"expected_revision": execution.revision_no, "decision": "accept", "rights": rights,
                   "title": f"{unit.title} · {output.role_id}"[:255], "attach_to_project": output.role_id in {"rough_cut", "final"}}
        try:
            creative_executions.decide_output(db, project_id, unit_id, execution_id, output.id, payload, user)
        except HTTPException as exc:
            if (exc.detail or {}).get("code") != "creative_execution_rights_escalation":
                raise
            db.rollback()
            payload["rights"] = {"rights_status": "cleared", "public_use_allowed": False, "model_use_allowed": False}
            creative_executions.decide_output(db, project_id, unit_id, execution_id, output.id, payload, user)
    project_folders.after_execution(db, execution_id)


def _ensure_references(db: Session, user: User, project_id: int, revision_ids: set[int]) -> None:
    for revision_id in revision_ids:
        row = db.scalar(select(ProjectMaterialReference).where(ProjectMaterialReference.project_id == project_id,
                                                               ProjectMaterialReference.material_revision_id == revision_id))
        if row is None:
            db.add(ProjectMaterialReference(project_id=project_id, material_revision_id=revision_id, origin="system_reference",
                                            status="active", attached_by=user.email, note="视频导演稿使用"))
        elif row.status != "active":
            row.status = "active"
    db.flush()


def _save(db: Session, user: User, project_id: int, unit_id: int, document: dict, summary: dict) -> int:
    from .content_masters import save_revision
    from .edit_handoff import _save as save_on
    from .video_documents import _expected_media

    revisions = {ref["material_revision_id"] for ref in _expected_media(document)}
    for revision_id in revisions:
        if db.get(MaterialRevision, revision_id) is None:
            _fail("video_chain_material_unknown", f"素材版本 {revision_id} 不存在", 422)
    _ensure_references(db, user, project_id, revisions)
    master = _latest(db, unit_id)
    if master is not None:
        return save_on(db, user, project_id, unit_id, master, document, {}, edit_summary=summary)
    refs = [{**ref, "content_hash": db.get(MaterialRevision, ref["material_revision_id"]).content_hash} for ref in _expected_media(document)]
    saved = save_revision(db, project_id=project_id, unit_id=unit_id, user=user, payload={
        "expected_revision": 0, "idempotency_key": f"video-chain:{uuid.uuid4().hex}", "payload_schema": "video.master.v2",
        "payload": document, "source_kind": "user_edit", "edit_summary": summary, "asset_refs": refs, "evidence_refs": []})
    return saved["id"]


def _text_of(master: ContentMasterRevision) -> str:
    def walk(node) -> str:
        if isinstance(node, dict):
            return (node.get("text") or "") + "".join(walk(child) for child in node.get("content") or [])
        return ""

    blocks = ((master.payload_json or {}).get("document") or {}).get("blocks") or []
    return "\n".join(filter(None, (walk(block) for block in blocks)))


def brief(db: Session, user: User, project_id: int, unit_id: int) -> dict:
    from ..models import Fact, FactPackItem
    from . import project_folders, voiceover
    from .content_masters import owned_unit
    from .project_brief import current_brief
    from .project_evidence import current_boundary

    project, unit = owned_unit(db, project_id, unit_id, user)
    row = current_brief(db, project_id)
    boundary = current_boundary(db, project_id)
    facts = []
    if boundary is not None:
        facts = [statement for (statement,) in db.execute(select(Fact.statement).join(FactPackItem, FactPackItem.fact_id == Fact.id)
                                                          .where(FactPackItem.fact_pack_id == boundary.fact_pack_id)
                                                          .order_by(FactPackItem.sort_order).limit(80))]
    siblings = []
    for other in db.scalars(select(ContentUnit).where(ContentUnit.project_id == project_id, ContentUnit.id != unit_id)):
        master = _latest(db, other.id)
        if master is not None and master.payload_schema.startswith("text."):
            siblings.append({"unit": other.title, "text": _text_of(master)[:8000]})
    tree = project_folders.tree(db)
    durations = dict(db.execute(select(MaterialRevision.id, MaterialRevision.duration_ms)
                                .where(MaterialRevision.id.in_([item["material_revision_id"] for item in tree["items"]]))).all())
    materials = [{**{key: item[key] for key in ("material_id", "material_revision_id", "title", "kind", "mime_type", "library", "group", "folder")},
                  "duration_ms": durations.get(item["material_revision_id"])}
                 for item in tree["items"] if item["library"] != "project" or item["project_id"] == project_id]
    master = _latest(db, unit_id)
    return {"project": {"id": project.id, "title": project.title, "objective": project.objective},
            "unit": {"id": unit.id, "title": unit.title, "channel_id": unit.channel_id},
            "brief": {key: getattr(row, key) for key in ("objective", "primary_audience", "core_message", "angle")} if row else None,
            "facts": facts, "source_texts": siblings, "voice_settings": voiceover.settings(),
            "materials": materials, "state": state(db, user, project_id, unit_id),
            "current_master": {"id": master.id, "revision_no": master.revision_no, "payload": master.payload_json} if master else None,
            "review_url": f"/projects/{project_id}/units/{unit_id}/production?workstep=plan", "rules": RULES}


def save_draft(db: Session, user: User, project_id: int, unit_id: int, payload: dict, note: str | None) -> dict:
    from . import project_folders
    from .video_documents import VideoDocumentError, canonical_payload

    document = copy.deepcopy(payload)
    document.pop("postproduction", None)
    try:
        canonical_payload(document)
    except VideoDocumentError as exc:
        _fail("video_chain_draft_invalid", f"导演稿格式不对：{exc}", 422)
    master_id = _save(db, user, project_id, unit_id, document, {"video_chain": "draft", "note": (note or "")[:2000]})
    master = db.get(ContentMasterRevision, master_id)
    project_folders.write_director_draft(db, project_id, master.revision_no, master.payload_json)
    db.commit()
    return {"master_id": master_id, "revision_no": master.revision_no, **state(db, user, project_id, unit_id)}


def _approved_master(db: Session, user: User, project_id: int, unit_id: int) -> tuple[ContentMasterRevision, dict]:
    current = state(db, user, project_id, unit_id)
    if current["state"] in {"not_started", "draft_review", "draft_changes"}:
        _fail("video_chain_draft_not_approved", "导演稿还没被采用，先等用户在页面上采用")
    return _latest(db, unit_id), current


def set_materials(db: Session, user: User, project_id: int, unit_id: int, picks: dict[str, int], music: int | None = None,
                  silent_durations: dict[str, int] | None = None) -> dict:
    master, _current = _approved_master(db, user, project_id, unit_id)
    document = copy.deepcopy(master.payload_json)
    shots = {shot["id"]: shot for shot in document["shots"]}
    unknown = sorted(set(picks) - shots.keys())
    if unknown:
        _fail("video_chain_shot_unknown", f"没有这些镜头：{', '.join(unknown)}", 422)
    for shot_id, revision_id in picks.items():
        revision = db.get(MaterialRevision, revision_id)
        if revision is None or revision.material.status != "active":
            _fail("video_chain_material_unknown", f"素材版本 {revision_id} 不可用", 422)
        shots[shot_id]["source_material_revision_id"] = revision_id
    for shot_id, length in (silent_durations or {}).items():
        # Only shots without a line: their length is pacing (how long the ending stays), the voice sets the rest.
        if shot_id not in shots or shots[shot_id].get("script_block_id") or not 1000 <= length <= 15000:
            _fail("video_chain_silent_shot_invalid", f"{shot_id} 不是无人声镜头，或时长不在 1–15 秒", 422)
        shots[shot_id]["duration_ms"] = length
    if music is not None:
        revision = db.get(MaterialRevision, music)
        if revision is None or revision.material.status != "active" or revision.material.kind != "audio":
            _fail("video_chain_material_unknown", f"音乐素材版本 {music} 不可用", 422)
        document["music"] = {"material_revision_id": music}
    master_id = _save(db, user, project_id, unit_id, document, {"video_chain": "material", "picks": picks, "music": music, "silent_durations": silent_durations})
    db.commit()
    missing = [shot["id"] for shot in document["shots"] if not shot.get("source_material_revision_id")]
    return {"master_id": master_id, "missing_shots": missing}


def generate_image(db: Session, user: User, project_id: int, prompt: str, label: str) -> dict:
    from . import project_folders
    from .material_autofill import _Images

    revision_id = _Images(db, user, project_id).make(prompt, label)
    revision = db.get(MaterialRevision, revision_id)
    project_folders.store_new(db, revision, project_id, "图片/图片素材")
    return {"material_id": revision.material_id, "material_revision_id": revision_id, "width": revision.width, "height": revision.height}


def accept_candidate(db: Session, user: User, project_id: int, run_id: int, segment_id: str, candidate_id: str) -> dict:
    from . import material_matching

    return material_matching.accept(db, user, run_id, {"segment_id": segment_id, "candidate_id": candidate_id, "project_id": project_id,
                                                       "public_use_allowed": True, "model_use_allowed": True, "commercial_use_allowed": True})


def voiceover(db: Session, user: User, project_id: int, unit_id: int) -> dict:
    from . import voiceover as voice

    _approved_master(db, user, project_id, unit_id)
    result = voice.generate(db, user, project_id, unit_id)
    revision = db.get(MaterialRevision, result["material_revision_id"])
    return {**{key: result[key] for key in ("material_revision_id", "master_id", "duration_ms", "has_timing")},
            "lines": (revision.metadata_json or {}).get("subtitles_srt")}


def prepare_edit(db: Session, user: User, project_id: int, unit_id: int, phase: str, ae_shot_ids: list[str],
                 alpha_shot_ids: list[str], notes: str | None) -> dict:
    """Records the DaVinci / AE split and opens the edit task: 小样 (rough_cut) first, 成片 (final) after 小样 is approved."""
    from . import project_folders
    from .edit_handoff import _postproduction
    from .web_video_handoff import prepare_edit as open_task

    master, current = _approved_master(db, user, project_id, unit_id)
    if phase == "final" and current["state"] != "finishing":
        _fail("video_chain_sample_not_approved", "小样还没通过，等用户在页面上通过小样")
    document = copy.deepcopy(master.payload_json)
    shots = {shot["id"] for shot in document["shots"]}
    if set(ae_shot_ids) - shots or set(alpha_shot_ids) - set(ae_shot_ids):
        _fail("video_chain_shot_unknown", "AE 镜头必须是导演稿里的镜头", 422)
    post = _postproduction(document, dict.fromkeys(ae_shot_ids, "ae"))
    for comp in post["ae_compositions"]:
        comp["alpha_required"] = comp["shot_id"] in alpha_shot_ids
    if phase == "final":
        post["phase"] = "final"
        sample = _accepted_cut(db, current["execution_id"])
        if sample is not None:
            post.update(parent_output_id=sample.id, parent_output_hash=sample.content_hash, parent_material_revision_id=sample.material_revision_id)
    if document.get("postproduction") != post:
        document["postproduction"] = post
        _save(db, user, project_id, unit_id, document, {"video_chain": "edit_prep", "phase": phase, "notes": (notes or "")[:2000]})
    master = _latest(db, unit_id)
    record = _unit_record(db, unit_id)
    result = open_task(db, project_id, unit_id, {"source_master_revision_id": master.id,
                                                 "idempotency_key": f"chain-{master.id}-{phase}"}, user)
    execution_id = result["execution"]["id"]
    if not record["tasks"] or record["tasks"][-1]["execution_id"] != execution_id:
        record["tasks"].append({"phase": phase, "execution_id": execution_id, "draft_master_id": current["draft_master_id"],
                                "master_id": master.id, "at": datetime.now(UTC).isoformat()})
        _put(db, unit_id, record)
    db.commit()
    archive = project_folders.archive_master(db, project_id, master.payload_json) if phase == "rough_cut" else None
    return {"execution_id": execution_id, "master_id": master.id, "phase": phase,
            "archive": {"moved": len(archive["moved"]), "pending": archive["pending"]} if archive else None}


def _accepted_cut(db: Session, execution_id: int) -> CreativeExecutionOutput | None:
    output = db.scalar(select(CreativeExecutionOutput).where(CreativeExecutionOutput.execution_id == execution_id,
                                                             CreativeExecutionOutput.role_id == "rough_cut",
                                                             CreativeExecutionOutput.state == "accepted")
                       .order_by(CreativeExecutionOutput.attempt_no.desc()).limit(1))
    # None when the 小样 was approved without accepting its files (the master moved on after it).
    return output if output is not None and output.material_revision_id is not None else None


def decisions(db: Session, user: User, project_id: int, unit_id: int) -> dict:
    from .content_masters import owned_unit

    owned_unit(db, project_id, unit_id, user)
    record = _unit_record(db, unit_id)
    return {**state(db, user, project_id, unit_id), "decisions": record["decisions"][-10:], "tasks": record["tasks"][-5:]}

