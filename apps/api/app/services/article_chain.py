"""Who writes a text or graphic piece: the platform's own model (its stages) or a third-party model over MCP.

Either way the user decides on the page, like the video chain: a draft (saved by the third-party model, or adopted from the
platform's creation flow) waits for 采用 or notes; a graphic piece is then rendered and final only once its images are accepted.
Every saved master revision is a version; deleting one hides it, because history and audits still point at it.
"""

from __future__ import annotations

import contextvars
import copy
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from ..models import (
    ChannelVariantRevision,
    ContentAsset,
    ContentMasterRevision,
    ContentUnit,
    CreativeExecutionPackage,
    MaterialRevision,
    SystemSetting,
    User,
)

KEY = "article_chain"
WRITERS = {"platform", "external"}
RULES = [
    "页面开关是「第三方模型」时才由你写；是「平台模型」时由平台阶段写，你不要存稿。",
    "读 get_article_brief：任务书、事实、来源原文、当前稿和格式示例。数字只用事实里有的，并写清来源；不夸大。",
    "当事实说的话（数字、症状、研究结论、政策、参数等）只用 facts（已冻结的事实边界）里有的；角色作品写稿前先用 get_fact_template 看题材模板，把要当事实说的话连出处用 submit_facts 交上去，平台核对后自动冻结；被退回的换来源或不说。事实改了要重存稿子。"
    "fact_templates 里每个模板的 red_lines 必须守，opinion_only 列的内容只能当个人经历或观点说。",
    "事实、身份复核由平台挂起：用 get_review_tasks 领取，逐条对照来源和身份规则判断，再用 submit_review 交回（没有问题就交空 issues）。复核未交回前作品不能定稿。检查若留下提醒，get_review_tasks 的 warning_judgments 会列出，逐条用 submit_warning_judgment 判断能否接受。",
    "写完整一版用 save_article_draft 存，然后停下等用户在页面上采用或写意见；有意见就出下一版再停。文字采用即定稿；图文采用后平台出图，用户验收成图才定稿，验收时写了意见就再出下一版。定稿后不能再存。",
    "文字用 text.master.v2（title + document.blocks：heading / paragraph 等），不写 citations；图文用 graphic.master.v2（canvases → layers），图片层的 material_revision_id 用素材库素材或 generate_video_image 生成的图；图上和发布文案里都不要放「配图为AI生成」之类的标记，用户发布时在平台上自己标。",
    "图文文字层的 claims 可以把一段文字（start/end 字符位置）挂到 facts 里的一条事实（fact_pack_item_id + snapshot_checksum），平台据此登记出处。",
]


def _fail(code: str, message: str, status: int = 409):
    raise HTTPException(status, {"code": code, "message": message})


def _record(db: Session, unit_id: int) -> dict:
    row = db.get(SystemSetting, KEY)
    value = (row.value or {}).get(str(unit_id)) if row else None
    return copy.deepcopy(value or {"writer": "platform", "decisions": [], "hidden": []})


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


def _unit(db: Session, user: User, project_id: int, unit_id: int, *, mutate: bool = False) -> ContentUnit:
    from .content_masters import owned_unit

    _project, unit = owned_unit(db, project_id, unit_id, user, mutate=mutate)
    if unit.modality not in {"text", "graphic"}:
        _fail("article_chain_modality", "只有文字和图文作品有写作方式", 422)
    return unit


def _latest(db: Session, unit_id: int) -> ContentMasterRevision | None:
    return db.scalar(select(ContentMasterRevision).where(ContentMasterRevision.content_unit_id == unit_id)
                     .order_by(ContentMasterRevision.revision_no.desc()).limit(1))


def _renders(db: Session, master: ContentMasterRevision) -> list[dict]:
    rows = []
    for item in (master.payload_json or {}).get("render_asset_ref") or []:
        revision = db.get(MaterialRevision, item["material_revision_id"])
        rows.append({"canvas_id": item["canvas_id"], "material_revision_id": item["material_revision_id"],
                     "material_id": revision.material_id if revision else None})
    return rows


def _state(db: Session, unit_id: int) -> dict:
    record = _record(db, unit_id)
    master = _latest(db, unit_id)
    view = {"writer": record["writer"], "master_id": master.id if master else None, "revision_no": master.revision_no if master else None}
    decided = next((item for item in reversed(record["decisions"]) if master and item["target_id"] == master.id), None)
    kind = decided["decision"] if decided else None
    graphic = bool(master and master.modality == "graphic")
    if kind == "approve" and decided.get("rendered_from"):
        # Older rendered revisions were approved automatically; their images still wait for the user's check.
        kind = "rendered"
    if kind == "accept" or (kind == "approve" and not graphic):
        done = {**view, "state": "done", "label": "已定稿", "locked": True}
        if graphic:
            done["review"] = record.get("review") or {"state": "not_sent"}
        return done
    if kind == "rendered":
        return {**view, "state": "final_review", "label": "成图待你验收", "renders": _renders(db, master)}
    if kind == "approve":
        # The draft is approved and the platform renders it; a failed render shows its reason and a retry.
        return {**view, "state": "rendering", "label": "稿子已采用，出图中", "review": record.get("review") or {"state": "not_sent"}}
    platform = record["writer"] == "platform"
    if master is None:
        if platform:
            return {**view, "state": "platform", "label": "平台模型写作中", "detail": "在下面的创作流程里逐步写稿，采用的稿子会回到这里等你看"}
        return {**view, "state": "not_started", "label": "等第三方模型写稿", "detail": "在接了 MCP 的第三方模型里说「写这篇」"}
    if decided:
        # Platform-written pieces are revised by running the creation flow again; its adopted master comes back here.
        return {**view, "state": "draft_changes", "label": "按你的意见在创作流程里重写" if platform else "第三方模型按你的意见修改中",
                "notes": decided["notes"]}
    return {**view, "state": "draft_review", "label": "稿件待你看"}


# Set only while the platform saves a finalized graphic piece's rendered revision.
finalizing: contextvars.ContextVar[int | None] = contextvars.ContextVar("article_chain_finalizing", default=None)


def locked(db: Session, unit_id: int) -> bool:
    """An approved piece is final; adjustments go into a copy."""
    return finalizing.get() != unit_id and bool(_state(db, unit_id).get("locked"))


def save_blocked(db: Session, unit_id: int) -> str | None:
    """Why a new master cannot be saved now: final, or approved and waiting for its images to be rendered or checked."""
    if finalizing.get() == unit_id:
        return None
    current = _state(db, unit_id)
    if current.get("locked"):
        return "已定稿，要调整请复制一份"
    if current["state"] in {"rendering", "final_review"}:
        return "稿子已采用，成图等你验收；验收时写了意见再出下一版"
    return None


def state(db: Session, user: User, project_id: int, unit_id: int) -> dict:
    _unit(db, user, project_id, unit_id)
    return {**_state(db, unit_id), "decisions": _record(db, unit_id)["decisions"][-10:]}


def set_writer(db: Session, user: User, project_id: int, unit_id: int, writer: str) -> dict:
    _unit(db, user, project_id, unit_id, mutate=True)
    if writer not in WRITERS:
        _fail("article_chain_writer_invalid", "写作方式只有平台模型和第三方模型", 422)
    if locked(db, unit_id):
        _fail("article_chain_locked", "已定稿，要调整请复制一份")
    record = _record(db, unit_id)
    record["writer"] = writer
    _put(db, unit_id, record)
    db.commit()
    return state(db, user, project_id, unit_id)


def decide(db: Session, user: User, project_id: int, unit_id: int, decision: str, notes: list[dict]) -> dict:
    """采用 / 按意见修改 on a draft; 验收通过 (accept) / 按意见修改 on a graphic piece's rendered images."""
    unit = _unit(db, user, project_id, unit_id, mutate=True)
    current = _state(db, unit_id)
    allowed = {"draft_review": {"approve", "changes"}, "draft_changes": {"approve", "changes"}, "final_review": {"accept", "changes"}}
    if current["state"] not in allowed:
        _fail("article_chain_not_waiting", "现在没有等你看的稿")
    if decision not in allowed[current["state"]]:
        _fail("article_chain_decision_invalid", "成图请验收或写意见" if current["state"] == "final_review" else "稿子请采用或写意见", 422)
    if decision == "changes" and not any(str(item.get("note") or "").strip() for item in notes):
        _fail("article_chain_notes_required", "写一下要改哪里", 422)
    record = _record(db, unit_id)
    record["decisions"].append({"target_id": current["master_id"], "decision": decision,
                                "notes": [{"note": str(item.get("note") or "")[:2000]} for item in notes][:50],
                                "by": user.email, "at": datetime.now(UTC).isoformat()})
    if decision == "changes":
        record.pop("review", None)
    _put(db, unit_id, record)
    db.commit()
    if decision in {"approve", "accept"} and unit.modality == "graphic":
        from . import graphic_review

        graphic_review.run(db, user, project_id, unit_id)
    return state(db, user, project_id, unit_id)


def send_to_review(db: Session, user: User, project_id: int, unit_id: int) -> dict:
    """Retry: render an approved draft again, or freeze an accepted piece whose sending failed."""
    from . import graphic_review

    unit = _unit(db, user, project_id, unit_id, mutate=True)
    if unit.modality != "graphic" or _state(db, unit_id)["state"] not in {"rendering", "done"}:
        _fail("article_chain_not_final", "只有已采用的图文作品可以重新出图或送审")
    graphic_review.run(db, user, project_id, unit_id)
    return state(db, user, project_id, unit_id)


def _text_of(master: ContentMasterRevision) -> str:
    from .video_chain import _text_of as text

    return text(master)


def brief(db: Session, user: User, project_id: int, unit_id: int) -> dict:
    from ..models import Fact, FactPackItem
    from . import craft_skills, fact_templates
    from .persona_brief import persona_brief
    from .project_brief import current_brief
    from .project_evidence import current_boundary

    from ..models import ContentProject

    unit = _unit(db, user, project_id, unit_id)
    project = db.get(ContentProject, project_id)
    row = current_brief(db, project_id)
    boundary = current_boundary(db, project_id)
    facts = []
    if boundary is not None:
        # Quotes and expert opinions have no Fact row; they carry who said it in the frozen snapshot.
        facts = [{"fact_pack_item_id": item_id, "snapshot_checksum": checksum,
                  "statement": statement or f"{(snapshot or {}).get('attribution')}：{(snapshot or {}).get('statement')}"}
                 for item_id, checksum, statement, snapshot in db.execute(
                     select(FactPackItem.id, FactPackItem.snapshot_checksum, Fact.statement, FactPackItem.snapshot_json).outerjoin(Fact, FactPackItem.fact_id == Fact.id)
                     .where(FactPackItem.fact_pack_id == boundary.fact_pack_id).order_by(FactPackItem.sort_order).limit(80))]
    siblings = []
    for other in db.scalars(select(ContentUnit).where(ContentUnit.project_id == project_id, ContentUnit.id != unit_id)):
        master = _latest(db, other.id)
        if master is not None and master.payload_schema.startswith("text."):
            siblings.append({"unit": other.title, "text": _text_of(master)[:8000]})
    master = _latest(db, unit_id)
    schema = "text.master.v2" if unit.modality == "text" else "graphic.master.v2"
    return {"project": {"id": project.id, "title": project.title, "objective": project.objective},
            "unit": {"id": unit.id, "title": unit.title, "modality": unit.modality, "channel_id": unit.channel_id},
            "brief": {key: getattr(row, key) for key in ("objective", "primary_audience", "core_message", "angle")} if row else None,
            "facts": facts, "fact_templates": fact_templates.brief_rules(db, project_id), "source_texts": siblings, "payload_schema": schema,
            "platform_skills": craft_skills.platform_skills(db, unit),
            # Who the piece speaks as; null when it belongs to no persona.
            "persona": persona_brief(db, user, unit),
            # Search works: the question this piece answers, its keywords, the sourced facts it may cite and the search writing rules.
            "search": __import__("app.services.search_promotion", fromlist=["writing_brief"]).writing_brief(db, unit),
            "state": state(db, user, project_id, unit_id),
            # The current version doubles as the format example the model fills in.
            "current_master": {"id": master.id, "revision_no": master.revision_no, "payload_schema": master.payload_schema,
                               "payload": master.payload_json} if master else None,
            "review_url": f"/projects/{project_id}/units/{unit_id}/production?workstep=plan", "rules": RULES}


def _asset_refs(db: Session, modality: str, payload: dict) -> list[dict]:
    """Declare every image the draft uses, so the model only names material revisions."""
    refs = []

    def declare(revision_id, **extra):
        revision = db.get(MaterialRevision, revision_id) if type(revision_id) is int else None
        if revision is None or revision.material.status != "active":
            _fail("article_chain_material_unknown", f"素材版本 {revision_id} 不可用", 422)
        refs.append({"material_revision_id": revision_id, "content_hash": revision.content_hash, "sort_order": len(refs), **extra})

    if modality == "graphic":
        for canvas in payload.get("canvases") or []:
            for layer in canvas.get("layers") or []:
                if layer.get("type") in {"image", "chart"}:
                    declare(layer.get("material_revision_id"), role="graphic_layer", slot_key=layer.get("id"),
                            placement={"canvas_id": canvas.get("id"), "layer_id": layer.get("id")})
    else:
        seen = set()
        for block in (payload.get("document") or {}).get("blocks") or []:
            revision_id = block.get("material_revision_id")
            if revision_id is not None and revision_id not in seen:
                seen.add(revision_id)
                declare(revision_id, role="document_media")
    return refs


def _with_cover(db: Session, user: User, unit, refs: list[dict]) -> list[dict]:
    """Search pieces published to 公众号 carry their generated cover first; other works are unchanged."""
    from .search_promotion import cover_refs

    cover = cover_refs(db, user, unit)
    if not cover:
        return refs
    rest = [ref for ref in refs if ref["material_revision_id"] != cover[0]["material_revision_id"]]
    return cover + [{**ref, "sort_order": index + 1} for index, ref in enumerate(rest)]


def _evidence_refs(modality: str, payload: dict) -> list[dict]:
    """A graphic text layer's claims become the evidence the platform checks against the fact boundary."""
    if modality != "graphic":
        return []
    refs = []
    for canvas in payload.get("canvases") or []:
        for layer in canvas.get("layers") or []:
            if layer.get("type") == "text":
                for claim in layer.get("claims") or []:
                    refs.append({"fact_pack_item_id": claim.get("fact_pack_item_id"), "snapshot_checksum": claim.get("snapshot_checksum"),
                                 "role": "claim", "sort_order": len(refs),
                                 "locator": {"canvas_id": canvas.get("id"), "layer_id": layer.get("id"), "start": claim.get("start"), "end": claim.get("end")}})
    return refs


def save_draft(db: Session, user: User, project_id: int, unit_id: int, payload: dict, note: str | None) -> dict:
    from .content_masters import save_revision

    unit = _unit(db, user, project_id, unit_id, mutate=True)
    current = _state(db, unit_id)
    if current["writer"] != "external":
        _fail("article_chain_platform_writer", "页面上的写作方式是「平台模型」，先在内容方案页切到「第三方模型」")
    if current.get("locked"):
        _fail("article_chain_locked", "已定稿，要调整请复制一份")
    if current["state"] in {"rendering", "final_review"}:
        _fail("article_chain_waiting_render_check", "稿子已采用，成图等用户验收；用户写了意见再出下一版")
    master = _latest(db, unit_id)
    saved = save_revision(db, project_id=project_id, unit_id=unit_id, user=user, payload={
        "expected_revision": master.revision_no if master else 0, "parent_revision_id": master.id if master else None,
        "idempotency_key": f"article-chain:{uuid.uuid4().hex}",
        "payload_schema": "text.master.v2" if unit.modality == "text" else "graphic.master.v2", "payload": payload,
        "source_kind": "user_edit", "edit_summary": {"article_chain": "draft", "note": (note or "")[:500]},
        "asset_refs": _with_cover(db, user, unit, _asset_refs(db, unit.modality, payload)), "evidence_refs": _evidence_refs(unit.modality, payload)})
    db.commit()
    return {"master_id": saved["id"], "revision_no": saved["revision_no"], "state": _state(db, unit_id)}


def _referenced(db: Session, master_ids: list[int]) -> set[int]:
    used = set()
    for column in (ChannelVariantRevision.source_master_revision_id, CreativeExecutionPackage.source_master_revision_id,
                   ContentAsset.content_master_revision_id):
        used.update(value for (value,) in db.execute(select(column).where(column.in_(master_ids))) if value)
    return used


def versions(db: Session, user: User, project_id: int, unit_id: int) -> dict:
    _unit(db, user, project_id, unit_id)
    record = _record(db, unit_id)
    current = _state(db, unit_id)
    rows = db.scalars(select(ContentMasterRevision).where(ContentMasterRevision.content_unit_id == unit_id)
                      .order_by(ContentMasterRevision.revision_no.desc())).all()
    rows = [row for row in rows if row.id not in set(record["hidden"])]
    used = _referenced(db, [row.id for row in rows])
    final = current["master_id"] if current.get("locked") else None
    items = []
    for row in rows:
        summary = row.edit_summary_json or {}
        source = ("第三方模型" if summary.get("article_chain") == "draft" else "平台模型" if row.source_kind == "workflow_stage"
                  else "复制" if summary.get("copied_from") else "恢复的版本" if summary.get("restored_from") else "手动")
        items.append({"id": row.id, "revision_no": row.revision_no, "source": source, "note": summary.get("note") or "",
                      "created_at": row.created_at.isoformat() if row.created_at else None,
                      "current": row.id == current["master_id"], "final": row.id == final, "referenced": row.id in used,
                      "deletable": row.id not in {current["master_id"], final} and row.id not in used})
    return {"items": items, "locked": bool(current.get("locked"))}


def restore(db: Session, user: User, project_id: int, unit_id: int, master_id: int) -> dict:
    """Make an older version current by saving it again; nothing is overwritten."""
    from .content_masters import _serialize, save_revision

    _unit(db, user, project_id, unit_id, mutate=True)
    if locked(db, unit_id):
        _fail("article_chain_locked", "已定稿，要调整请复制一份")
    source = db.get(ContentMasterRevision, master_id)
    if source is None or source.content_unit_id != unit_id or master_id in _record(db, unit_id)["hidden"]:
        _fail("article_chain_version_unknown", "没有这个版本", 404)
    latest = _latest(db, unit_id)
    view = _serialize(db, source, require_current=False)
    summary = {"restored_from": master_id, **({"article_chain": "draft"} if (source.edit_summary_json or {}).get("article_chain") else {})}
    saved = save_revision(db, project_id=project_id, unit_id=unit_id, user=user, payload={
        "expected_revision": latest.revision_no, "parent_revision_id": latest.id, "idempotency_key": f"article-restore:{uuid.uuid4().hex}",
        "payload_schema": source.payload_schema, "payload": source.payload_json, "content_form": source.content_form,
        "source_kind": "user_edit", "edit_summary": summary,
        "asset_refs": [{key: ref[key] for key in ("material_revision_id", "content_hash", "role", "slot_key", "sort_order", "placement")} for ref in view["assets"]],
        "evidence_refs": [{key: ref[key] for key in ("fact_pack_item_id", "snapshot_checksum", "role", "locator", "sort_order")} for ref in view["evidence"]]})
    db.commit()
    return {"master_id": saved["id"], "revision_no": saved["revision_no"]}


def delete_version(db: Session, user: User, project_id: int, unit_id: int, master_id: int) -> dict:
    _unit(db, user, project_id, unit_id, mutate=True)
    item = next((row for row in versions(db, user, project_id, unit_id)["items"] if row["id"] == master_id), None)
    if item is None:
        _fail("article_chain_version_unknown", "没有这个版本", 404)
    if not item["deletable"]:
        _fail("article_chain_version_in_use", "当前版本、定稿版本和渠道版本用到的版本不能删")
    record = _record(db, unit_id)
    record["hidden"].append(master_id)
    _put(db, unit_id, record)
    db.commit()
    return {"deleted": master_id}
