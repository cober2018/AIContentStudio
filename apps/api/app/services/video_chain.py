"""Video made end to end by the external model over MCP; the platform keeps records and asks the user.

导演稿 (with a material request per shot) → user → materials, voiceover, DaVinci / AE → 小样 → user → 排版 → 成片 → user.
The platform calls no model here. Saves that do not change picture content (materials, voiceover, edit preparation,
duplicate merges) keep the 导演稿 the user approved; any other save is a new 导演稿 that needs approval again.
"""

from __future__ import annotations

import contextvars
import copy
import uuid
from datetime import UTC, datetime
from pathlib import Path

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
    "商品作品：导演稿采用前不生成任何画面（首帧、图生视频、切换手动 / 自动都会被拒绝）；采用后先把用户素材对应到镜头（set_shot_materials），再只给没有用户素材的镜头生成。",
    "导演稿采用后：先用用户新放进库的素材，其余按 素材库 → 图库搜索 → 生图 → AE 模板 补齐；每个镜头用哪条由你定；回执写明哪些是用户给的、哪些是你找的或做的。",
    "小样、排版、成片都在达芬奇（剪辑、调色、声音、导出）和 AE（标题、字幕、包装、特效）里做；ffmpeg 只用于检查和转格式。",
    "配乐只看主稿 music：有 material_revision_id 就铺这首；none 为 true 是用户明确不要配乐；空着就是还没定：按导演稿和用户意见找一首放进来（set_shot_materials 的 music），拿不准就问用户；不能自己当成不用。只有用户能选「不用配乐」。",
    "封面（可选）：竖版 1080×1920 的 jpg / png，实拍画面当背景，上面大字商品名和卖点；导出到开剪结果给的 cover_dir（导出/封面），用 role cover 交付，并且要在剪辑清单之前交（清单的 output_hashes 可以列上 cover）；成片通过后它就是作品封面。同一张可以剪进视频开头当 0.5 秒第一帧。",
    "剪辑照导演稿：画面内容要变就先存新导演稿；导演稿没写的细节和网络素材署名写进回执。",
    "文件都在项目文件夹里：准备素材（materialize_inputs）给每条素材的原始路径，直接导入达芬奇 / AE，只读，不复制；"
    "临时渲染、AE 单镜头、达芬奇 / AE 工程和剪辑清单放 work_dir（<项目>/工作/<作品>/任务N/），小样导出到 导出/小样、成片导出到 导出/成片；"
    "交付结果（submit_output）给文件的绝对路径 path，平台原地检查登记，交付后别再改或移动这个文件。",
    "复刻参考视频：brief.reference 有值或用户给了参考视频，先 analyze_reference_video / get_reference_video 拿本机拆解，按 studio.video.reference-breakdown 写整体分析、时间线和拍摄清单（save_reference_breakdown），再写导演稿："
    "结构和节奏照参考，口播换成本作品的说法，每镜写 board.source_kind；参考里的证书、医院、成分只记成需要品牌真实资料，不照抄、不生成；参考视频的原画面和水印不进成片。",
    "写人物镜头的提示词按 studio.video.prompt-direction：board.attitude 先写人物态度和对谁说，再写一两个关键反应；首帧按 拍摄方式 / 人物 / 动作与镜头 / 场景 四段写；商品图管外观、人物图管长相，提示词不重复描述包装。",
]
EXECUTOR = "codex-video-production"
_KEEPS_DRAFT = {"material", "edit_prep", "cover"}


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
    while master is not None and master.parent_revision_id:
        parent = db.get(ContentMasterRevision, master.parent_revision_id)
        # Re-saving identical content (e.g. clicking save without edits) is not a new 导演稿.
        if parent is None or not (_keeps_draft(master) or master.payload_hash == parent.payload_hash):
            break
        master = parent
    return master


def _decision(record: dict, stage: str, target_id: int) -> dict | None:
    return next((item for item in reversed(record["decisions"]) if item["stage"] == stage and item["target_id"] == target_id), None)


def _task(db: Session, record: dict) -> tuple[dict | None, CreativeExecution | None]:
    if not record["tasks"]:
        return None, None
    task = record["tasks"][-1]
    return task, db.get(CreativeExecution, task["execution_id"])


def _finished(view: dict) -> dict:
    return {**view, "state": "done", "label": "已定稿", "locked": True}


# Accepting the 成片 files already locks the work; the cover written in that same approval must still get through.
_finalizing: contextvars.ContextVar[int | None] = contextvars.ContextVar("video_chain_finalizing", default=None)


def locked(db: Session, unit_id: int) -> bool:
    """An approved 成片 is final for good; changes go into a copy of the unit instead."""
    return _finalizing.get() != unit_id and bool(_state(db, unit_id).get("locked"))


def state(db: Session, user: User, project_id: int, unit_id: int) -> dict:
    from .content_masters import owned_unit

    owned_unit(db, project_id, unit_id, user)
    return _state(db, unit_id)


def _state(db: Session, unit_id: int) -> dict:
    record = _unit_record(db, unit_id)
    root = draft_root(db, _latest(db, unit_id))
    if root is None or (root.edit_summary_json or {}).get("video_chain") != "draft":
        return {"state": "not_started", "label": "待开始", "detail": "在接了 MCP 的第三方模型里说「做这个视频」开始：先写导演稿和素材需求"}
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
        return {**view, "state": "finishing", "label": "排版中"} if phase == "sample" else _finished(view)
    if execution.state == "result_ready":
        if notes and notes["decision"] == "changes":
            return {**view, "state": f"{phase}_changes", "label": "小样按你的意见修改中" if phase == "sample" else "成片按你的意见修改中", "notes": notes["notes"]}
        return {**view, "state": f"{phase}_review", "label": "小样待你看" if phase == "sample" else "成片待你看"}
    if execution.state == "accepted":
        return {**view, "state": "finishing", "label": "排版中"} if phase == "sample" else _finished(view)
    return {**view, "state": "error", "label": "出错", "detail": execution.safe_reason or execution.state}


def cut_location(db: Session, user: User, project_id: int, unit_id: int, output_id: int):
    """The file behind the 小样 / 成片 the page plays: the library record once accepted, else where the model exported it."""
    from . import creative_executions, materials

    current = state(db, user, project_id, unit_id)
    output = db.get(CreativeExecutionOutput, output_id)
    if output is None or output.execution_id != current.get("execution_id") or output.role_id not in {"rough_cut", "final"}:
        _fail("video_chain_cut_not_found", "找不到这条片子", 404)
    if output.material_revision_id:
        revision = db.get(MaterialRevision, output.material_revision_id)
        path = materials.local_file_checked(db, revision) if revision is not None else None
        if path is not None:
            return path
    if not output.staging_key.startswith("/"):
        _fail("video_chain_cut_not_found", "片子不在项目文件夹里", 404)
    execution = db.get(CreativeExecution, output.execution_id)
    try:
        creative_executions.check_output(execution.owner_user_id, execution.id, output.staging_key, output.size_bytes, output.content_hash)
    except HTTPException as exc:
        if (exc.detail or {}).get("code") == "video_chain_output_changed":
            raise
        _fail("video_chain_cut_not_found", "片子文件不在了", 404)
    return Path(output.staging_key)


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
    # Until the 成片 is final the user may send the 导演稿 back from any later stop.
    back_to_draft = stage == "draft" and decision == "changes" and "draft_master_id" in current and not current.get("locked")
    if current["state"] not in {expected, expected.replace("review", "changes")} and not back_to_draft:
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
    if stage == "final" and accepted:
        token = _finalizing.set(unit_id)
        try:
            _adopt_cover(db, user, project_id, unit_id, target)
        except HTTPException:
            # The cut is approved either way; a cover that cannot be written must not undo that.
            db.rollback()
        finally:
            _finalizing.reset(token)
    record = _unit_record(db, unit_id)
    record["decisions"].append({"stage": stage, "target_id": target, "decision": decision, "outputs_accepted": accepted,
                                "notes": [{"time_ms": item.get("time_ms"), "note": str(item.get("note") or "")[:2000]} for item in notes][:50],
                                "by": user.email, "at": datetime.now(UTC).isoformat()})
    _put(db, unit_id, record)
    db.commit()
    if stage == "final" and decision == "approve":
        from . import project_folders

        try:
            project_folders.archive_raw(db, project_id)
        except Exception:  # noqa: BLE001 Filing the raw folder must never undo the approval; failures stay 待归档.
            db.rollback()
    return state(db, user, project_id, unit_id)


def _adopt_cover(db: Session, user: User, project_id: int, unit_id: int, execution_id: int) -> None:
    """The 成片's cover becomes the work's cover; no cover leaves the old one."""
    cover = db.scalar(select(CreativeExecutionOutput).where(CreativeExecutionOutput.execution_id == execution_id,
                                                            CreativeExecutionOutput.role_id == "cover", CreativeExecutionOutput.state == "accepted")
                      .order_by(CreativeExecutionOutput.attempt_no.desc()).limit(1))
    master = _latest(db, unit_id)
    if cover is None or cover.material_revision_id is None or master is None:
        return
    document = copy.deepcopy(master.payload_json)
    if document.get("cover") == {"material_revision_id": cover.material_revision_id}:
        return
    document["cover"] = {"material_revision_id": cover.material_revision_id}
    _save(db, user, project_id, unit_id, document, {"video_chain": "cover", "output_id": cover.id})


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
                   "title": f"{unit.title} · {output.role_id}"[:255], "attach_to_project": output.role_id in {"rough_cut", "final", "cover"}}
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
    from . import craft_skills, product_video, project_folders, reference_video, voiceover
    from .persona_brief import persona_brief
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
            "facts": facts, "source_texts": siblings, "voice_settings": voiceover.settings_for(db, unit),
            "materials": materials, "state": state(db, user, project_id, unit_id),
            "current_master": {"id": master.id, "revision_no": master.revision_no, "payload": master.payload_json} if master else None,
            "review_url": f"/projects/{project_id}/units/{unit_id}/production?workstep=plan", "rules": RULES,
            "platform_skills": craft_skills.platform_skills(db, unit),
            # Product works add their category, style, material mode and image-to-video route; persona works get null.
            "product": product_video.direction(db, unit_id),
            # Who the work speaks as; null when it belongs to no persona.
            "persona": persona_brief(db, user, unit),
            # The reference video being cloned, when the user attached one; null otherwise.
            "reference": reference_video.brief_view(db, unit_id)}


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
                  silent_durations: dict[str, int] | None = None, no_music: bool = False) -> dict:
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
    elif no_music:
        document["music"] = {"none": True}
    master_id = _save(db, user, project_id, unit_id, document, {"video_chain": "material", "picks": picks, "music": music, "no_music": no_music, "silent_durations": silent_durations})
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
    # A 成片 sent back (final_changes) is redone as a new task on top of the same approved 小样.
    if phase == "final" and current["state"] not in {"finishing", "final_changes"}:
        _fail("video_chain_sample_not_approved", "小样还没通过，等用户在页面上通过小样")
    document = copy.deepcopy(master.payload_json)
    if not document.get("music"):
        _fail("video_chain_music_undecided", "配乐还没定：先选一首放进主稿（set_shot_materials 的 music），或请用户在「配音与音乐」里点「不用配乐」，再开剪")
    shots = {shot["id"] for shot in document["shots"]}
    if set(ae_shot_ids) - shots or set(alpha_shot_ids) - set(ae_shot_ids):
        _fail("video_chain_shot_unknown", "AE 镜头必须是导演稿里的镜头", 422)
    post = _postproduction(document, dict.fromkeys(ae_shot_ids, "ae"))
    for comp in post["ae_compositions"]:
        comp["alpha_required"] = comp["shot_id"] in alpha_shot_ids
    if phase == "final":
        post["phase"] = "final"
        record = _unit_record(db, unit_id)
        sample = next((cut for task in reversed(record["tasks"]) if task["phase"] == "rough_cut"
                       for cut in [_accepted_cut(db, task["execution_id"])] if cut is not None), None)
        if sample is not None:
            post.update(parent_output_id=sample.id, parent_output_hash=sample.content_hash, parent_material_revision_id=sample.material_revision_id)
    if document.get("postproduction") != post:
        document["postproduction"] = post
        _save(db, user, project_id, unit_id, document, {"video_chain": "edit_prep", "phase": phase, "notes": (notes or "")[:2000]})
    master = _latest(db, unit_id)
    record = _unit_record(db, unit_id)
    # After the user sends a 小样 / 成片 back, an unchanged master would hand back that same task; the latest
    # send-back of this phase makes the key new, and stays the same on retries so a retry reuses the new task.
    stage = "sample" if phase == "rough_cut" else "final"
    sent_back = next((item["target_id"] for item in reversed(record["decisions"]) if item["stage"] == stage and item["decision"] == "changes"), None)
    key = f"chain-{master.id}-{phase}" + (f"-after-{sent_back}" if sent_back else "")
    result = open_task(db, project_id, unit_id, {"source_master_revision_id": master.id, "idempotency_key": key}, user)
    execution_id = result["execution"]["id"]
    if not record["tasks"] or record["tasks"][-1]["execution_id"] != execution_id:
        record["tasks"].append({"phase": phase, "execution_id": execution_id, "draft_master_id": current["draft_master_id"],
                                "master_id": master.id, "at": datetime.now(UTC).isoformat()})
        _put(db, unit_id, record)
    db.commit()
    archive = project_folders.archive_master(db, project_id, master.payload_json) if phase == "rough_cut" else None
    work = project_folders.work_dir(db, project_id, unit_id, execution_id)
    export = project_folders.export_dir(db, project_id, phase)
    cover = project_folders.export_dir(db, project_id, "cover")
    cover.mkdir(parents=True, exist_ok=True)
    db.commit()
    return {"execution_id": execution_id, "master_id": master.id, "phase": phase,
            "archive": {"moved": len(archive["moved"]), "pending": archive["pending"]} if archive else None,
            "work_dir": str(work), "export_dir": str(export), "cover_dir": str(cover),
            "files": f"素材用 materialize_inputs 给的原始路径（只读）；{'小样' if phase == 'rough_cut' else '成片'}导出到 {export}/，"
                     f"可选的封面图（role cover，jpg / png）导出到 {cover}/；"
                     f"其他交付文件和临时渲染放 {work}/；submit_output 传文件的绝对路径 path。"}


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

