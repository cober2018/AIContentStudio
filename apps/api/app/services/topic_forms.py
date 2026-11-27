"""一份本体、四种形态：每个项目一份全文（本体），用户勾长文、图卡、横版视频、竖版视频，各形态从本体派生并记血缘。

- 本体是一条文字作品（form="body"），沿用文字作品的写稿、采用（= 定稿）和版本。
- 新写的本体停在「稿件待你看」等用户定稿；导入的已发表文章在建项目时就算定稿。
- 定稿前勾选的形态作品已建好但不能存稿（等本体定稿）；定稿那一刻按勾选开工。
- 形态作品每存一版都记下它用的本体版本（source_body_revision_id），并检查数字、结论和视频画幅是否与本体一致。
- 本体出新定稿后，派生作品只标「本体已更新」，由用户决定是否重做（重做新开一条同形态作品）。
- 搜索推广的核心稿就是本体：它的派生作品同样记血缘、查画幅，两道人工关卡不变。
"""

from __future__ import annotations

import hashlib
import re
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from ..models import ContentMasterRevision, ContentProject, ContentUnit, SystemSetting, User

FORMS = {"long_article": "长文", "graphic_cards": "图卡", "video_landscape": "横版视频", "video_portrait": "竖版视频"}
# Forms that are their own work; 长文 is the body itself.
UNIT_FORMS = {"graphic_cards": "graphic", "video_landscape": "video", "video_portrait": "video"}
ASPECT = {"video_landscape": [16, 9], "video_portrait": [9, 16]}
SPECS = {
    "long_article": {"take": "本体全文", "spec": "不另写一篇；本体定稿后直接出平台版本", "channels": ["公众号", "知乎", "头条"]},
    "graphic_cards": {"take": "问题、结果表、判断步骤、结论", "spec": "3～6 张，3:4；首张放问题，中间放表，末张揭晓或给可勾选清单",
                      "channels": ["小红书", "B站图文", "公众号图片消息"]},
    "video_landscape": {"take": "完整过程：问题 → 做法 → 结果怎么核 → 结论", "spec": "16:9，3～5 分钟", "aspect_ratio": [16, 9],
                        "channels": ["B站", "YouTube", "公众号", "视频号"]},
    "video_portrait": {"take": "只追一个点", "spec": "9:16，约 1 分钟", "aspect_ratio": [9, 16], "channels": ["视频号", "抖音", "小红书视频"]},
}
SOURCES = {"new": "新写", "published_article": "已发表文章导入"}
WRITERS = {"external", "platform"}
SECTIONS = [("question", "问题", ("问题", "要回答")), ("conclusion", "结论", ("结论",)),
            ("method", "做法与口径", ("做法", "口径", "方法", "样本", "定义")), ("results", "结果表或算例", ("结果", "算例", "表")),
            ("conditions", "适用条件", ("适用", "条件")), ("sources", "出处", ("出处", "来源", "参考"))]
DEFAULTS_KEY = "persona_default_forms"
STANDARD = "craft-writing"

# Saying the sample cannot tell two things apart, and the stronger claims a derived piece must not make then.
_UNDECIDED = ("无法区分", "区分不出", "分不出", "没有显著差异", "无显著差异", "差异不显著", "看不出差别", "说不清谁更好")
_STRONGER = ("明显更好", "更好", "更优", "跑赢", "显著优于", "优于", "完胜", "碾压", "稳赢", "必然")
_NUMBER = re.compile(r"\d+(?:[.,]\d+)*")


def _fail(status: int, code: str, message: str, **extra):
    raise HTTPException(status, {"code": code, "message": message, **extra})


def _now() -> str:
    return datetime.now(UTC).isoformat()


# --- plan -------------------------------------------------------------------------------------------------------------

def plan_of(project: ContentProject | None) -> dict | None:
    return dict(project.form_plan_json) if project is not None and project.form_plan_json else None


def _save_plan(project: ContentProject, plan: dict) -> None:
    project.form_plan_json = plan
    flag_modified(project, "form_plan_json")


def _clean_forms(forms: list[str]) -> list[str]:
    unknown = set(forms) - FORMS.keys()
    if unknown:
        _fail(422, "forms_unknown", "形态只有长文、图卡、横版视频、竖版视频")
    if not forms:
        _fail(422, "forms_empty", "至少勾一种形态")
    return [key for key in FORMS if key in forms]


def persona_defaults(db: Session, persona_id: int) -> list[str]:
    row = db.get(SystemSetting, DEFAULTS_KEY)
    return list(((row.value or {}) if row else {}).get(str(persona_id)) or ["long_article"])


def set_persona_defaults(db: Session, user: User, persona_id: int, forms: list[str]) -> dict:
    from ..models import ContentPersona

    persona = db.get(ContentPersona, persona_id)
    if persona is None or persona.owner_user_id != user.id:
        _fail(404, "persona_not_found", "内容角色不存在")
    forms = _clean_forms(forms)
    row = db.get(SystemSetting, DEFAULTS_KEY)
    if row is None:
        row = SystemSetting(key=DEFAULTS_KEY, value={})
        db.add(row)
    value = dict(row.value or {})
    value[str(persona_id)] = forms
    row.value, row.updated_by = value, user.email
    flag_modified(row, "value")
    db.commit()
    return {"persona_id": persona_id, "forms": forms}


def body_unit(db: Session, project_id: int) -> ContentUnit | None:
    return db.scalar(select(ContentUnit).where(ContentUnit.project_id == project_id, ContentUnit.form == "body",
                                               ContentUnit.lifecycle == "active").order_by(ContentUnit.id).limit(1))


def final_body(db: Session, unit_id: int) -> ContentMasterRevision | None:
    """The body revision the user last made final (采用); a reopened body keeps this one until the next 定稿."""
    from . import article_chain

    for item in reversed(article_chain._record(db, unit_id)["decisions"]):
        if item["decision"] == "approve":
            return db.get(ContentMasterRevision, item["target_id"])
    return None


def _form_units(db: Session, project_id: int) -> list[ContentUnit]:
    return db.scalars(select(ContentUnit).where(ContentUnit.project_id == project_id, ContentUnit.form.in_(UNIT_FORMS),
                                                ContentUnit.lifecycle == "active", ContentUnit.status != "archived")
                      .order_by(ContentUnit.id)).all()


def _started(db: Session, unit_id: int) -> bool:
    return db.scalar(select(ContentMasterRevision.id).where(ContentMasterRevision.content_unit_id == unit_id).limit(1)) is not None


def _new_unit(db: Session, user: User, project: ContentProject, persona_id: int, form: str, title: str) -> ContentUnit:
    from ..routers import content_projects as projects
    from . import article_chain

    modality = "text" if form == "body" else UNIT_FORMS[form]
    created = projects.create_unit(projects.UnitIn(title=title[:300], persona_id=persona_id, modality=modality,
                                                   channel_id="xiaohongshu" if form == "graphic_cards" else None),
                                   project.id, db=db, user=user)
    unit = db.get(ContentUnit, created["id"])
    unit.form = form
    if modality in {"text", "graphic"}:
        # The platform model writes text only; graphic cards (and videos) are the third-party model's.
        writer = (plan_of(project) or {}).get("writer", "external") if form == "body" else "external"
        article_chain._put(db, unit.id, {"writer": writer, "decisions": [], "hidden": []})
    db.flush()
    return unit


def _title(form: str, project: ContentProject) -> str:
    return f"{'本体' if form == 'body' else FORMS[form]}｜{project.title}"


def create(db: Session, user: User, project_id: int, *, persona_id: int, forms: list[str], body_source: str = "new",
           writer: str = "external", article: dict | None = None) -> dict:
    """Set up the body and the ticked forms for a fresh project (选题转项目 / 新建项目 / 空项目页 / MCP create_project)."""
    from ..routers.content_projects import mutable_project
    from .project_events import record_project_event

    project = mutable_project(db, project_id, user)
    if plan_of(project) or body_unit(db, project_id):
        _fail(409, "forms_already_planned", "这个项目已经有本体了，去本体卡片上补勾或取消形态")
    if body_source not in SOURCES:
        _fail(422, "body_source_unknown", "本体来源只有新写和已发表文章导入")
    if writer not in WRITERS:
        _fail(422, "body_writer_unknown", "写作方只有平台模型和第三方模型")
    if body_source == "published_article" and not (article and str(article.get("text") or "").strip()):
        _fail(422, "body_article_required", "用已发表文章做本体，要给出文章正文")
    forms = _clean_forms(forms)
    _save_plan(project, {"forms": forms, "body_source": body_source, "writer": writer, "persona_id": persona_id,
                         "created_at": _now(), "started_at": None, "started_body_revision_id": None})
    db.flush()
    body = _new_unit(db, user, project, persona_id, "body", _title("body", project))
    for form in forms:
        if form in UNIT_FORMS:
            _new_unit(db, user, project, persona_id, form, _title(form, project))
    record_project_event(db, project_id=project_id, event_type="project.forms_planned", actor=user.email, entity_type="content_unit",
                         entity_id=body.id, payload={"forms": forms, "body_source": body_source})
    db.commit()
    if body_source == "published_article":
        _import_article(db, user, project, body, article or {})
    return view(db, user, project_id)


# --- importing a published article ------------------------------------------------------------------------------------

_IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)[^)]*\)")


def article_document(title: str, text: str) -> tuple[dict, list[dict]]:
    """Markdown or plain text → text.master.v2; images become listed sources (原图) instead of blocks."""
    blocks, images, counter = [], [], 0

    def add(kind: str, content: str, **extra):
        nonlocal counter
        counter += 1
        blocks.append({"id": f"b{counter}", "type": kind, "content": [{"text": content}], **extra})

    listing: list[str] = []
    ordered = False

    def flush_list():
        nonlocal counter, listing
        if listing:
            counter += 1
            blocks.append({"id": f"b{counter}", "type": "ordered_list" if ordered else "bullet_list",
                           "items": [{"id": f"b{counter}i{index}", "content": [{"text": item}]} for index, item in enumerate(listing, 1)]})
            listing = []

    for raw in text.replace("\r\n", "\n").split("\n"):
        line = raw.strip()
        for alt, src in _IMAGE.findall(line):
            images.append({"alt": alt, "src": src})
        line = _IMAGE.sub("", line).strip()
        bullet = re.match(r"^([-*+]|\d+[.、)])\s+(.*)$", line)
        if bullet and not line.startswith("|"):
            if listing and ordered != bullet.group(1)[0].isdigit():
                flush_list()
            ordered = bullet.group(1)[0].isdigit()
            listing.append(bullet.group(2))
            continue
        flush_list()
        if not line or re.fullmatch(r"\|?\s*:?-{2,}.*", line):
            continue
        heading = re.match(r"^(#{1,4})\s+(.*)$", line)
        if heading:
            add("heading", heading.group(2).strip(), level=max(2, len(heading.group(1))) if heading.group(2).strip() != title else 1)
        elif line.startswith(">"):
            add("quote", line.lstrip("> ").strip())
        elif line.startswith("|"):
            # Tables have no block of their own; each row stays checkable line by line.
            add("paragraph", " ｜ ".join(cell.strip() for cell in line.strip("|").split("|")))
        else:
            add("paragraph", line)
    flush_list()
    if not blocks:
        _fail(422, "body_article_empty", "文章正文是空的")
    return {"title": title[:500], "document": {"schema": "studio.text.document.v1", "blocks": blocks}}, images


def _import_article(db: Session, user: User, project: ContentProject, body: ContentUnit, article: dict) -> None:
    from . import article_chain
    from .content_masters import save_revision
    from .project_events import record_project_event

    title = str(article.get("title") or project.title).strip()[:500]
    payload, images = article_document(title, str(article["text"]))
    source = {"kind": "published_article", "title": title, "url": (article.get("url") or None),
              "published_record_id": article.get("published_record_id"), "published_at": article.get("published_at"),
              "images": images[:100], "imported_by": user.email, "imported_at": _now()}
    saved = save_revision(db, project_id=project.id, unit_id=body.id, user=user, payload={
        "expected_revision": 0, "idempotency_key": f"body-import:{uuid.uuid4().hex}", "payload_schema": "text.master.v2",
        "payload": payload, "source_kind": "user_edit", "edit_summary": {"body_import": source, "note": "已发表文章导入"},
        "asset_refs": [], "evidence_refs": []})
    # The user picked this article when creating the project, so it is final without another stop.
    record = article_chain._record(db, body.id)
    record["decisions"].append({"target_id": saved["id"], "decision": "approve", "notes": [], "by": user.email, "at": _now(),
                                "imported": True})
    article_chain._put(db, body.id, record)
    plan = plan_of(project)
    plan["import"] = source
    _save_plan(project, plan)
    record_project_event(db, project_id=project.id, event_type="body.imported", actor=user.email, entity_type="content_unit",
                         entity_id=body.id, payload={"url": source["url"], "master_id": saved["id"]})
    db.commit()
    body_finalized(db, user, body)


# --- 定稿 and starting the forms --------------------------------------------------------------------------------------

def body_finalized(db: Session, user: User, unit: ContentUnit) -> None:
    """Called after the user makes the body final. The first time, the ticked forms start; later it is a new body revision."""
    from .project_events import record_project_event

    if unit.form != "body" or unit.production_domain != "persona":
        return
    project = db.get(ContentProject, unit.project_id)
    plan = plan_of(project)
    final = final_body(db, unit.id)
    if plan is None or final is None:
        return
    if plan.get("started_at") is None:
        plan["started_at"], plan["started_body_revision_id"] = _now(), final.id
        _save_plan(project, plan)
        record_project_event(db, project_id=project.id, event_type="body.finalized", actor=user.email, entity_type="content_unit",
                             entity_id=unit.id, payload={"master_id": final.id, "forms": plan["forms"]})
        db.commit()
        if "long_article" in plan["forms"]:
            _long_article(db, user, project, unit)
        return
    record_project_event(db, project_id=project.id, event_type="body.updated", actor=user.email, entity_type="content_unit",
                         entity_id=unit.id, payload={"master_id": final.id, "revision_no": final.revision_no})
    db.commit()


def _long_article(db: Session, user: User, project: ContentProject, body: ContentUnit) -> None:
    """长文 is the body itself: put out its 公众号 version mechanically; a failure is recorded, never blocks the rest."""
    from . import channel_variants

    master = final_body(db, body.id)
    result: dict = {"channel_id": "wechat", "content_form": "article", "at": _now()}
    try:
        preview = channel_variants.adapt_preview(db, project_id=project.id, unit_id=body.id, user=user, allow_unmapped=True, payload={
            "source_master_revision_id": master.id, "expected_source_payload_hash": master.payload_hash,
            "expected_source_context_hash": master.context_hash, "channel_id": "wechat", "content_form": "article"})
        # The mechanical 公众号 mapping takes plain paragraphs only; a body with 块 headings and lists is carried over
        # block for block instead (same words, same order), saved as an ordinary edited version.
        mechanical = preview["payload"] is not None
        payload = preview["payload"] if mechanical else _wechat_payload(master, preview["asset_refs"])
        saved = channel_variants.save_revision(db, project_id=project.id, unit_id=body.id, user=user, payload={
            "variant_key": "wechat.article.primary", "expected_revision": 0, "source_master_revision_id": master.id,
            "expected_source_payload_hash": master.payload_hash, "expected_source_context_hash": master.context_hash,
            "expected_profile_hash": preview["profile_hash"], "channel_id": "wechat", "content_form": "article",
            "idempotency_key": f"long-article:{master.id}", "source_kind": "deterministic_adapt" if mechanical else "manual_edit",
            "payload": payload, "asset_refs": preview["asset_refs"], "evidence_refs": preview["evidence_refs"],
            "edit_summary": {} if mechanical else {"long_article": "body blocks carried over"}})
        result.update(state="ready", variant_id=saved["id"])
    except HTTPException as exc:
        db.rollback()
        detail = exc.detail if isinstance(exc.detail, dict) else {"message": str(exc.detail)}
        result.update(state="failed", reason=detail.get("message") or detail.get("reason") or detail.get("code") or "出平台版本失败")
    project = db.get(ContentProject, project.id)
    plan = plan_of(project)
    plan["long_article"] = result
    _save_plan(project, plan)
    db.commit()


def _wechat_payload(master: ContentMasterRevision, asset_refs: list[dict]) -> dict:
    """The body as a 公众号 article: headings, paragraphs, quotes and lists kept; images only where their file is mapped."""
    mapped = {ref.get("slot_key") for ref in asset_refs if ref.get("role") == "inline_image"}
    blocks = []
    for block in ((master.payload_json or {}).get("document") or {}).get("blocks") or []:
        kind, entry = block.get("type"), {"id": block["id"], "order": len(blocks)}
        if kind in {"heading", "paragraph", "quote", "callout"}:
            text = _runs_text(block)
            if text.strip():
                blocks.append({**entry, "kind": kind if kind in {"heading", "quote"} else "paragraph", "text": text})
        elif kind in {"bullet_list", "ordered_list"}:
            items = [_runs_text(item) for item in block.get("items") or []]
            blocks.append({**entry, "kind": "list", "text": "\n".join(
                f"{index}. {item}" if kind == "ordered_list" else f"· {item}" for index, item in enumerate(items, 1))})
        elif kind in {"image", "chart"} and block["id"] in mapped:
            blocks.append({**entry, "kind": "image", "image_ref_key": block["id"], "text": block.get("caption", ""),
                           "alt_text": block.get("alt_text", "")})
    return {"title": (master.payload_json or {}).get("title") or "", "blocks": blocks}


def set_forms(db: Session, user: User, project_id: int, forms: list[str]) -> dict:
    """补勾 / 取消. Before 定稿 the ticks just reshape the not-yet-started works; after it a new tick starts right away."""
    from ..routers.content_projects import mutable_project
    from .project_events import record_project_event

    project = mutable_project(db, project_id, user)
    plan = plan_of(project)
    if plan is None:
        _fail(409, "forms_not_planned", "这个项目还没有本体，先选要做哪几种")
    forms = _clean_forms(forms)
    body = body_unit(db, project_id)
    existing = {unit.form: unit for unit in _form_units(db, project_id)}
    for form, unit in existing.items():
        if form not in forms:
            if _started(db, unit.id):
                _fail(409, "form_already_started", f"{FORMS[form]}已经开始做了，不能取消；不要了就去作品里归档")
            db.delete(unit)
    db.flush()
    for form in forms:
        if form in UNIT_FORMS and form not in existing:
            _new_unit(db, user, project, plan["persona_id"], form, _title(form, project))
    added_long = "long_article" in forms and "long_article" not in plan["forms"]
    plan["forms"] = forms
    _save_plan(project, plan)
    record_project_event(db, project_id=project_id, event_type="project.forms_changed", actor=user.email, entity_type="content_project",
                         entity_id=project_id, payload={"forms": forms})
    db.commit()
    if added_long and plan.get("started_at") and body is not None and not (plan.get("long_article") or {}).get("state") == "ready":
        _long_article(db, user, project, body)
    return view(db, user, project_id)


def redo(db: Session, user: User, project_id: int, unit_id: int) -> dict:
    """The body moved on: start a fresh work of the same form from the current final body; the old one stays as it is."""
    from ..routers.content_projects import mutable_project
    from .project_events import record_project_event

    project = mutable_project(db, project_id, user)
    plan = plan_of(project)
    unit = db.get(ContentUnit, unit_id)
    if plan is None or unit is None or unit.project_id != project_id or unit.form not in UNIT_FORMS:
        _fail(404, "form_unit_not_found", "没有这个形态作品")
    note = stale(db, unit)
    if note is None:
        _fail(409, "form_not_stale", "这个作品用的已经是当前定稿的本体")
    if _unit_view(db, user, unit)["redone_by"]:
        _fail(409, "form_already_redone", "这一条已经按新本体重做过了，去新的那条看")
    fresh = _new_unit(db, user, project, plan["persona_id"], unit.form, f"{_title(unit.form, project)}（按本体第 {note['to_revision_no']} 版重做）")
    record_project_event(db, project_id=project_id, event_type="unit.form_redo", actor=user.email, entity_type="content_unit",
                         entity_id=fresh.id, payload={"replaces_unit_id": unit.id, "body_revision_no": note["to_revision_no"]})
    db.commit()
    return {"unit_id": fresh.id, "replaces_unit_id": unit.id, "form": unit.form}


# --- reading the body ---------------------------------------------------------------------------------------------------

def _runs_text(node) -> str:
    return "".join(run.get("text") or "" for run in node.get("content") or [])


def sections(master: ContentMasterRevision | None) -> list[dict]:
    """Split the body by its level-1/2 headings; each part is matched to a 块 by its heading's words."""
    if master is None:
        return []
    blocks = ((master.payload_json or {}).get("document") or {}).get("blocks") or []
    parts: list[dict] = [{"heading": "", "lines": []}]
    for block in blocks:
        if block.get("type") == "heading" and block.get("level", 2) <= 2:
            parts.append({"heading": _runs_text(block), "lines": []})
            continue
        if block.get("type") in {"bullet_list", "ordered_list"}:
            parts[-1]["lines"] += ["· " + _runs_text(item) for item in block.get("items") or []]
        elif block.get("type") in {"heading", "paragraph", "quote", "callout"}:
            parts[-1]["lines"].append(_runs_text(block))
        elif block.get("type") in {"image", "chart"}:
            parts[-1]["lines"].append(f"[{block['type']}: {block.get('caption') or block.get('alt_text') or block.get('material_revision_id')}]")
    result = []
    for part in parts:
        if not part["heading"] and not part["lines"]:
            continue
        kind = next((key for key, _label, words in SECTIONS if any(word in part["heading"] for word in words)), "other")
        result.append({"kind": kind, "label": dict((key, label) for key, label, _ in SECTIONS).get(kind, "其他"),
                       "heading": part["heading"], "text": "\n".join(line for line in part["lines"] if line)})
    return result


def _body_text(master: ContentMasterRevision) -> str:
    return ((master.payload_json or {}).get("title") or "") + "\n" + "\n".join(
        f"{part['heading']}\n{part['text']}" for part in sections(master))


def standard() -> dict:
    from . import craft_skills

    text = craft_skills.skill_index(STANDARD)
    return {"skill": STANDARD, "version": hashlib.sha256(text.encode()).hexdigest()[:12], "text": text,
            "rule": "四种形态共用这一份写作标准，不分平台；写稿前照它写，平台存稿时会查其中能机械检查的几条"}


def _search_core(db: Session, unit: ContentUnit) -> ContentUnit | None:
    from ..models import SearchWork

    work = db.scalar(select(SearchWork).where(SearchWork.unit_id == unit.id))
    if work is None or work.role != "derived":
        return None
    core = db.scalar(select(SearchWork).where(SearchWork.project_id == work.project_id, SearchWork.role == "core"))
    return db.get(ContentUnit, core.unit_id) if core else None


def current_body_for(db: Session, unit: ContentUnit) -> ContentMasterRevision | None:
    """The body revision a form work should be derived from now: the final body, or the search core's latest version."""
    from . import article_chain

    if unit.production_domain == "search":
        core = _search_core(db, unit)
        return article_chain._latest(db, core.id) if core else None
    body = body_unit(db, unit.project_id)
    return final_body(db, body.id) if body else None


def is_form_work(db: Session, unit: ContentUnit) -> bool:
    if unit.production_domain == "search":
        return _search_core(db, unit) is not None
    return unit.form in UNIT_FORMS and plan_of(db.get(ContentProject, unit.project_id)) is not None


def brief_part(db: Session, unit: ContentUnit) -> dict | None:
    """What a writing brief adds for a body or form work: the form's spec, the body revision's 块 and the writing standard."""
    project = db.get(ContentProject, unit.project_id)
    plan = plan_of(project)
    if unit.form == "body" and plan is not None:
        return {"form": {"key": "body", "label": "本体", "source": plan["body_source"],
                         "sections": [{"kind": key, "label": label} for key, label, _ in SECTIONS],
                         "rule": "本体就是全文：用二级标题按上面的块写，所有数字和结论都从这里来；写完存稿后等用户在页面上定稿"},
                "writing_standard": standard()}
    if not is_form_work(db, unit):
        return None
    form = unit.form or ("graphic_cards" if unit.modality == "graphic" else None)
    master = current_body_for(db, unit)
    return {"form": {"key": form, "label": FORMS.get(form, unit.modality), **SPECS.get(form, {})},
            "body": {"master_id": master.id, "revision_no": master.revision_no, "title": (master.payload_json or {}).get("title"),
                     "sections": sections(master)} if master else None,
            "body_rule": "只从 body.sections 取材：数字、日期、样本区间只用本体或 facts 里有的；结论不能比本体更强；节选和示意要标注",
            "writing_standard": standard()}


# --- checks on save -----------------------------------------------------------------------------------------------------

def _visible_text(schema: str, payload: dict) -> str:
    if schema == "text.master.v2":
        lines = [payload.get("title") or ""]
        for block in (payload.get("document") or {}).get("blocks") or []:
            lines += [_runs_text(item) for item in block.get("items") or []] if "items" in block else [_runs_text(block)]
        return "\n".join(lines)
    if schema == "graphic.master.v2":
        return "\n".join(run.get("text") or "" for canvas in payload.get("canvases") or [] for layer in canvas.get("layers") or []
                         if layer.get("type") == "text" for run in layer.get("runs") or [])
    if schema == "video.master.v2":
        parts = [payload.get("title") or ""]
        parts += [block.get("text") or "" for block in (payload.get("script") or {}).get("blocks") or []]
        parts += [cue.get("text") or "" for cue in (payload.get("subtitles") or {}).get("cues") or []]
        parts += [item.get("text") or "" for item in payload.get("overlays") or []]
        return "\n".join(parts)
    return ""


def _numbers(text: str) -> set[str]:
    found = set()
    for token in _NUMBER.findall(text):
        value = token.replace(",", "")
        if value.isdigit() and int(value) < 10:
            continue  # 「3 张」「第 2 步」 are wording, not data
        found.add(value.rstrip("0").rstrip(".") if "." in value else value)
    return found


def _allowed_text(db: Session, unit: ContentUnit, body: ContentMasterRevision) -> str:
    from ..models import Fact, FactPackItem
    from .project_brief import current_brief
    from .project_evidence import current_boundary

    parts = [_body_text(body)]
    boundary = current_boundary(db, unit.project_id)
    if boundary is not None:
        for statement, snapshot in db.execute(select(Fact.statement, FactPackItem.snapshot_json).select_from(FactPackItem)
                                              .outerjoin(Fact, FactPackItem.fact_id == Fact.id)
                                              .where(FactPackItem.fact_pack_id == boundary.fact_pack_id)):
            parts.append(statement or str((snapshot or {}).get("statement") or ""))
    brief = current_brief(db, unit.project_id)
    if brief is not None:
        parts += [brief.objective or "", brief.core_message or "", brief.angle or ""]
    project = db.get(ContentProject, unit.project_id)
    parts.append(project.title if project else "")
    return "\n".join(parts)


def consistency_problems(db: Session, unit: ContentUnit, schema: str, payload: dict, body: ContentMasterRevision) -> list[str]:
    text = _visible_text(schema, payload)
    problems = []
    allowed = _numbers(_allowed_text(db, unit, body))
    extra = sorted(_numbers(text) - allowed)
    for value in extra[:10]:
        line = next((row.strip() for row in text.split("\n") if value in row.replace(",", "")), "")
        problems.append(f"「{value}」本体第 {body.revision_no} 版和已冻结事实里都没有（出现在：{line[:60]}）")
    body_text = _body_text(body)
    if any(word in body_text for word in _UNDECIDED):
        scan = text
        for phrase in _UNDECIDED:
            scan = scan.replace(phrase, "")  # 「说不清谁更好」 itself is not a stronger claim
        word = next((word for word in _STRONGER if word in scan and word not in body_text), None)
        if word:
            line = next((row.strip() for row in text.split("\n") if word in row), "")
            problems.append(f"结论比本体强：本体第 {body.revision_no} 版说样本区分不出，这里写了「{word}」（{line[:60]}）")
    return problems


def guard_save(db: Session, unit: ContentUnit, schema: str, payload: dict, latest: ContentMasterRevision | None) -> int | None:
    """Before a master revision is stored: which body revision it derives from, after checking it agrees with that body."""
    if unit.form == "body" or not is_form_work(db, unit):
        return None
    if unit.form in ASPECT and schema == "video.master.v2" and payload.get("aspect_ratio") != ASPECT[unit.form]:
        want = ":".join(map(str, ASPECT[unit.form]))
        _fail(422, "form_aspect_mismatch", f"这是{FORMS[unit.form]}作品，导演稿画幅要写 {want}；要换比例就补勾另一种形态，不从这条裁")
    inherited = db.get(ContentMasterRevision, latest.source_body_revision_id) if latest is not None and latest.source_body_revision_id else None
    body = inherited or current_body_for(db, unit)
    if body is None:
        if unit.production_domain == "search":
            return None
        _fail(409, "body_not_final", "本体还没定稿：等用户在页面上把本体定稿后，这个形态才开始")
    problems = consistency_problems(db, unit, schema, payload, body)
    if problems:
        _fail(422, "form_body_mismatch", "和本体对不上，改了再存：" + "；".join(problems), problems=problems)
    return body.id


def require_started(db: Session, unit: ContentUnit) -> None:
    """Form works wait for the body to be final before a brief is handed out."""
    if unit.production_domain == "persona" and unit.form in UNIT_FORMS and is_form_work(db, unit) and current_body_for(db, unit) is None:
        _fail(409, "body_not_final", "本体还没定稿：等用户在页面上把本体定稿后，这个形态才开始")


# --- staleness and the page view ----------------------------------------------------------------------------------------

def _latest(db: Session, unit_id: int) -> ContentMasterRevision | None:
    return db.scalar(select(ContentMasterRevision).where(ContentMasterRevision.content_unit_id == unit_id)
                     .order_by(ContentMasterRevision.revision_no.desc()).limit(1))


def stale(db: Session, unit: ContentUnit) -> dict | None:
    """「本体已更新到第 N 版」 and which 块 changed, when the work was derived from an older final body."""
    master = _latest(db, unit.id)
    if master is None or master.source_body_revision_id is None:
        return None
    current = current_body_for(db, unit)
    if current is None or current.id == master.source_body_revision_id:
        return None
    used = db.get(ContentMasterRevision, master.source_body_revision_id)
    before = {(part["heading"], part["kind"]): part["text"] for part in sections(used)}
    after = {(part["heading"], part["kind"]): part["text"] for part in sections(current)}
    changed = [heading or "开头" for (heading, _kind) in dict.fromkeys([*before, *after]) if before.get((heading, _kind)) != after.get((heading, _kind))]
    return {"from_revision_no": used.revision_no if used else None, "to_revision_no": current.revision_no, "changed_sections": changed}


def _unit_view(db: Session, user: User, unit: ContentUnit) -> dict:
    from . import article_chain, video_chain

    master = _latest(db, unit.id)
    used = db.get(ContentMasterRevision, master.source_body_revision_id) if master and master.source_body_revision_id else None
    if unit.modality == "video":
        state = video_chain._state(db, unit.id)
    else:
        state = article_chain._state(db, unit.id)
    from ..models import ProjectEvent

    redone = next((event.entity_id for event in db.scalars(select(ProjectEvent).where(
        ProjectEvent.project_id == unit.project_id, ProjectEvent.event_type == "unit.form_redo"))
        if (event.payload_json or {}).get("replaces_unit_id") == unit.id), None)
    return {"unit_id": unit.id, "title": unit.title, "form": unit.form, "state": state.get("state"), "label": state.get("label"),
            "started": master is not None, "body_revision_no": used.revision_no if used else None,
            "body_master_id": used.id if used else None, "stale": stale(db, unit),
            # Already redone from a newer body: the page points at the new work instead of offering another redo.
            "redone_by": int(redone) if redone else None}


def view(db: Session, user: User, project_id: int) -> dict:
    from ..routers.content_projects import owned_project
    from . import article_chain

    project = owned_project(db, project_id, user)
    plan = plan_of(project)
    if plan is None:
        return {"planned": False, "forms": [], "labels": FORMS}
    body = body_unit(db, project_id)
    final = final_body(db, body.id) if body else None
    state = article_chain._state(db, body.id) if body else {}
    units = _form_units(db, project_id)
    return {"planned": True, "labels": FORMS, "forms": plan["forms"], "body_source": plan["body_source"], "writer": plan.get("writer"),
            "persona_id": plan["persona_id"], "started": bool(plan.get("started_at")), "import": plan.get("import"),
            "long_article": plan.get("long_article"),
            "body": {"unit_id": body.id, "title": body.title, "state": state.get("state"), "label": state.get("label"),
                     "final_master_id": final.id if final else None, "final_revision_no": final.revision_no if final else None,
                     "review_url": f"/projects/{project_id}/units/{body.id}/production?workstep=plan"} if body else None,
            "works": [_unit_view(db, user, unit) for unit in units],
            "specs": SPECS}


def pending(db: Session, user: User) -> dict:
    """Form works waiting for the third-party model: the body is final and the work has no draft yet or was sent back."""
    from . import article_chain, video_chain

    items = []
    projects = db.scalars(select(ContentProject).where(ContentProject.owner_user_id == user.id, ContentProject.form_plan_json.is_not(None),
                                                       ContentProject.status != "archived")).all()
    for project in projects:
        plan = plan_of(project)
        if not plan or not plan.get("started_at"):
            continue
        for unit in _form_units(db, project.id):
            state = (video_chain._state if unit.modality == "video" else article_chain._state)(db, unit.id)
            if state.get("state") not in {"not_started", "draft_changes"}:
                continue
            body = current_body_for(db, unit)
            items.append({"project_id": project.id, "project_title": project.title, "unit_id": unit.id, "title": unit.title,
                          "form": unit.form, "label": FORMS[unit.form], "spec": SPECS[unit.form], "state": state.get("state"),
                          "notes": state.get("notes"),
                          "body": {"master_id": body.id, "revision_no": body.revision_no, "sections": sections(body)} if body else None,
                          "next": "get_video_brief → save_director_draft" if unit.modality == "video" else "get_article_brief → save_article_draft"})
    return {"items": items, "writing_standard": {key: value for key, value in standard().items() if key != "text"},
            "rule": "逐条做：先读 brief 里的 body 和 writing_standard，按形态规格取材；存稿时平台自动记下用的是本体哪一版"}
