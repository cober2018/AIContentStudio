"""Built-in topic templates for fact boundaries; the model submits sourced claims by template, the platform checks every source and freezes what passes."""

import json
import re
import unicodedata
from datetime import UTC, date, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from ..models import (
    ContentPersonaRevision,
    ContentProject,
    ContentUnit,
    Fact,
    FactPack,
    FactPackItem,
    FactStatus,
    ProjectFactBoundaryRevision,
    SourceDocument,
    SystemSetting,
    User,
)

KEY = "fact_templates"
KINDS = {"fact": "fact", "event": "event", "quote": "third_party_quote", "opinion": "author_opinion"}
# Unreachable or unmatched sources mean the claim was never seen in its source; those go back to the model instead of into the boundary.
BLOCKING = {"unreachable", "quote_missing"}
FLAGS = {"unreachable": "来源打不开", "quote_missing": "原文对不上", "outside_sources": "来源不在常见权威网站", "stale": "来源可能过期"}


@lru_cache(maxsize=1)
def _catalog() -> tuple[dict, ...]:
    path = Path(__file__).resolve().parents[1] / "fact_templates" / "topics.json"
    return tuple(json.loads(path.read_text("utf-8"))["templates"])


def templates() -> list[dict]:
    return [dict(item) for item in _catalog()]


def _by_id() -> dict[str, dict]:
    return {item["id"]: item for item in _catalog()}


def _fail(status: int, code: str, message: str):
    raise HTTPException(status, {"code": code, "message": message})


def _record(db: Session, project_id: int) -> dict:
    row = db.get(SystemSetting, KEY)
    return dict(((row.value or {}) if row else {}).get(str(project_id)) or {})


def _store(db: Session, project_id: int, record: dict, actor: str) -> None:
    row = db.get(SystemSetting, KEY) or SystemSetting(key=KEY)
    value = dict(row.value or {})
    value[str(project_id)] = record
    row.value, row.updated_by = value, actor
    flag_modified(row, "value")
    db.add(row)


def chosen(db: Session, project_id: int) -> list[str]:
    known = _by_id()
    return [item for item in _record(db, project_id).get("templates") or [] if item in known]


def suggest(db: Session, project_id: int) -> list[str]:
    project = db.get(ContentProject, project_id)
    text = " ".join(filter(None, [project.title if project else "", project.objective if project else ""]))
    for persona_id in set(db.scalars(select(ContentUnit.persona_id).where(ContentUnit.project_id == project_id, ContentUnit.persona_id.is_not(None)))):
        revision = db.scalar(select(ContentPersonaRevision).where(ContentPersonaRevision.persona_id == persona_id)
                             .order_by(ContentPersonaRevision.revision_no.desc()).limit(1))
        profile = (revision.profile_json if revision else None) or {}
        for key in ("positioning", "target_audience", "content_domains"):
            value = profile.get(key)
            text += " " + (" ".join(map(str, value)) if isinstance(value, list) else str(value or ""))
    lowered = text.lower()
    return [item["id"] for item in _catalog() if any(word.lower() in lowered for word in item["keywords"])]


def set_chosen(db: Session, user: User, project_id: int, ids: list[str]) -> dict:
    known = _by_id()
    unknown = [item for item in ids if item not in known]
    if unknown:
        _fail(422, "fact_template_unknown", f"没有这个题材模板：{'、'.join(unknown)}")
    record = _record(db, project_id)
    record["templates"] = list(dict.fromkeys(ids))
    _store(db, project_id, record, user.email)
    db.commit()
    return view(db, project_id)


def view(db: Session, project_id: int) -> dict:
    return {"templates": templates(), "chosen": chosen(db, project_id), "suggested": suggest(db, project_id)}


def stale_works(db: Session, project_id: int) -> list[dict]:
    """Persona works whose latest saved master was written against an older (or no) fact boundary."""
    from ..models import ContentMasterRevision
    from .product_context import is_product
    from .project_evidence import current_boundary

    boundary = current_boundary(db, project_id)
    if boundary is None:
        return []
    stale = []
    for unit in db.scalars(select(ContentUnit).where(ContentUnit.project_id == project_id).order_by(ContentUnit.id)):
        master = db.scalar(select(ContentMasterRevision).where(ContentMasterRevision.content_unit_id == unit.id)
                           .order_by(ContentMasterRevision.revision_no.desc()).limit(1))
        if master is not None and not is_product(unit) and master.fact_boundary_revision_id != boundary.id:
            stale.append({"unit_id": unit.id, "title": unit.title, "modality": unit.modality})
    return stale


def brief_rules(db: Session, project_id: int) -> list[dict]:
    """What the writing model must follow for the chosen topics (red lines and opinion-only content)."""
    known = _by_id()
    return [{key: known[item][key] for key in ("id", "name", "need_source", "red_lines", "opinion_only")} for item in chosen(db, project_id)]


def for_model(db: Session, user: User, project_id: int, unit_id: int) -> dict:
    from .content_masters import owned_unit
    from .product_context import is_product
    from .project_brief import current_brief

    project, unit = owned_unit(db, project_id, unit_id, user)
    if is_product(unit):
        _fail(422, "fact_template_product", "商品作品用商品资料，不用事实边界")
    known = _by_id()
    brief = current_brief(db, project_id)
    return {
        "project": {"id": project.id, "title": project.title, "objective": project.objective},
        "brief": {key: getattr(brief, key) for key in ("objective", "primary_audience", "core_message", "angle")} if brief else None,
        "chosen": [known[item] for item in chosen(db, project_id)],
        "suggested": [known[item] for item in suggest(db, project_id)],
        "all": [{"id": item["id"], "name": item["name"]} for item in _catalog()],
        "current": current(db, project_id),
        "rules": [
            "chosen 为空时按选题从 suggested / all 里选模板，交事实时写进 templates；用户可能在页面上改过，以 chosen 为准。",
            "按每个模板的 need_source 列出这条内容要当事实说的全部话，到 sources / domains 认的来源里找，打开原页面核对后再交。",
            "每条交：statement（要说的话）、kind（fact 事实 / event 事件 / quote 引语 / opinion 专家观点）、template（模板 id）、source_url、excerpt（来源页面里的原文，逐字摘）、source_date（来源发布或更新日期 YYYY-MM-DD），引语和观点再写 attribution（谁说的）。",
            "submit_facts 每次交完整一份：平台打开来源核对，打不开、原文对不上的退回（换来源重交，或把这句删掉、改成个人经历的说法）；其余自动冻结成事实边界新一版，替换上一版。",
            "交完事实再存导演稿 / 文章；事实改了要重存稿子。",
        ],
    }


def _item_view(item: FactPackItem, labels: list[str]) -> dict:
    snapshot = item.snapshot_json or {}
    return {
        "id": item.id, "kind": next((key for key, value in KINDS.items() if value == item.evidence_kind), item.evidence_kind),
        "statement": snapshot.get("statement"), "excerpt": snapshot.get("excerpt") or (snapshot.get("source_locator") or {}).get("quote"),
        "attribution": snapshot.get("attribution"), "source_url": snapshot.get("source_url"), "source_date": snapshot.get("as_of"),
        "labels": [FLAGS[flag] for flag in labels if flag in FLAGS],
    }


def current(db: Session, project_id: int) -> dict | None:
    """The frozen boundary as the reviewer sees it: every item, its source and the platform's labels."""
    from .project_evidence import current_boundary

    boundary = current_boundary(db, project_id)
    pack = db.get(FactPack, boundary.fact_pack_id) if boundary else None
    if pack is None:
        return None
    labels = (_record(db, project_id).get("labels") or {})
    items = [_item_view(item, labels.get(str(item.id)) or []) for item in sorted(pack.items, key=lambda row: (row.sort_order, row.id))]
    return {"revision_no": boundary.revision_no, "fact_pack_id": pack.id, "frozen_at": pack.frozen_at.isoformat() if pack.frozen_at else None, "items": items,
            "labelled": sum(1 for item in items if item["labels"])}


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "").lower()
    return re.sub(r"[\s　，。、；：！？“”‘’「」（）()\"',.;:!?\-—…·]+", "", text)


def _fetch(db: Session, url: str, title: str, source_date: str | None) -> SourceDocument:
    import hashlib

    from ..observability import safe_error_category
    from ..routers.sources import _parse_and_store
    from .url_fetch import safe_fetch

    doc = SourceDocument(title=title[:500] or url[:200], source_type="url", source_url=url, as_of=source_date, metadata_json={"final_url": url, "origin": "fact_template_auto"})
    db.add(doc)
    db.flush()
    try:
        content, mime = safe_fetch(url)
    except Exception as exc:  # noqa: BLE001 An unreachable source is a finding to show, not a failed call.
        doc.parse_status, doc.parse_error = "failed", f"fetch: {safe_error_category(exc)}"
        db.flush()
        return doc
    doc.mime_type, doc.sha256 = mime, hashlib.sha256(content).hexdigest()
    _parse_and_store(db, doc, content, mime, ".html" if "html" in (mime or "") else ".txt")
    return doc


def _flags(doc: SourceDocument, excerpt: str, template: dict, source_date: str | None) -> list[str]:
    if doc.parse_status != "done" or not doc.raw_text:
        return ["unreachable"]
    flags = [] if _normalize(excerpt) in _normalize(doc.raw_text) else ["quote_missing"]
    host = (urlparse(doc.source_url or "").hostname or "").lower()
    if not any(host == domain or host.endswith("." + domain) for domain in template["domains"]):
        flags.append("outside_sources")
    if template.get("max_age_days") and (not source_date or date.fromisoformat(source_date) < datetime.now(UTC).date() - timedelta(days=template["max_age_days"])):
        flags.append("stale")
    return flags


def submit(db: Session, user: User, project_id: int, unit_id: int, items: list[dict], chosen_ids: list[str] | None = None) -> dict:
    from . import factpack_service
    from .content_masters import owned_unit
    from .product_context import is_product
    from .project_events import record_project_event
    from .project_evidence import current_boundary

    project, unit = owned_unit(db, project_id, unit_id, user, mutate=True)
    if is_product(unit):
        _fail(422, "fact_template_product", "商品作品用商品资料，不用事实边界")
    if chosen_ids and not chosen(db, project_id):
        set_chosen(db, user, project_id, chosen_ids)
    picked = {item: _by_id()[item] for item in chosen(db, project_id)}
    if not picked:
        _fail(409, "fact_template_missing", "这个项目还没选题材模板；按选题从 suggested 里选，写进 templates 一起交")
    for index, item in enumerate(items, 1):
        if item["template"] not in picked:
            _fail(422, "fact_template_item_invalid", f"第 {index} 条的 template「{item['template']}」不在这个项目选的模板里（{'、'.join(picked)}）")
        if item["kind"] in {"quote", "opinion"} and not item.get("attribution"):
            _fail(422, "fact_template_item_invalid", f"第 {index} 条是引语或观点，要写 attribution（谁说的）")
    fetched: dict[str, SourceDocument] = {}
    kept, returned = [], []
    for index, item in enumerate(items, 1):
        url = item["source_url"]
        doc = fetched.get(url) or _fetch(db, url, item.get("source_title") or url, item.get("source_date"))
        fetched[url] = doc
        flags = _flags(doc, item["excerpt"], picked[item["template"]], item.get("source_date"))
        blocking = [flag for flag in flags if flag in BLOCKING]
        if blocking:
            returned.append({"index": index, "statement": item["statement"], "reasons": [FLAGS[flag] for flag in blocking]})
        else:
            kept.append((item, doc, flags))
    if not kept:
        db.commit()
        return {"kept": 0, "returned": returned, "current": current(db, project_id),
                "next": "一条都没收下，事实边界没变；换能打开、原文对得上的来源重交"}
    boundary = current_boundary(db, project_id)
    name = f"{project.title}｜事实边界"[:300]
    version = (db.scalar(select(FactPack.version).where(FactPack.name == name).order_by(FactPack.version.desc()).limit(1)) or 0) + 1
    pack = FactPack(name=name, description="按题材模板自动核对：" + "、".join(item["name"] for item in picked.values()), version=version,
                    parent_id=boundary.fact_pack_id if boundary else None, created_by=user.email)
    db.add(pack)
    db.flush()
    labels: dict[str, list[str]] = {}
    for order, (item, doc, flags) in enumerate(kept):
        url, kind = item["source_url"], KINDS[item["kind"]]
        fact = None
        if kind in {"fact", "event"}:
            fact = Fact(source_document_id=doc.id, statement=item["statement"], fact_type="event" if kind == "event" else "statement", as_of=item.get("source_date"),
                        status=FactStatus.confirmed.value, source_locator_json={"url": url, "quote": item["excerpt"]}, note=item["template"], created_by=user.email)
            db.add(fact)
            db.flush()
        # Facts keep their source on the Fact row; quotes and opinions need it in the snapshot, and the reviewer view reads both from there.
        row = FactPackItem(fact_pack_id=pack.id, fact=fact, sort_order=order, evidence_kind=kind, public_use_allowed=True, model_use_allowed=True,
                           snapshot_json=None if fact else {"statement": item["statement"], "excerpt": item["excerpt"], "attribution": item["attribution"],
                                                             "source_title": doc.title, "source_url": url, "source_locator": {"url": url, "quote": item["excerpt"]},
                                                             "as_of": item.get("source_date")})
        db.add(row)
        db.flush()
        labels[str(row.id)] = flags
    db.refresh(pack)
    try:
        factpack_service.freeze_pack(pack)
    except ValueError as exc:
        _fail(422, "fact_boundary_invalid", str(exc))
    revision = ProjectFactBoundaryRevision(project_id=project_id, revision_no=(boundary.revision_no if boundary else 0) + 1, parent_revision_id=boundary.id if boundary else None,
                                           fact_pack_id=pack.id, fact_pack_version=pack.version, fact_pack_checksum=pack.checksum, created_by=user.email)
    db.add(revision)
    db.flush()
    record_project_event(db, project_id=project_id, event_type="fact_boundary.frozen_bound", actor=user.email, entity_type="fact_pack", entity_id=pack.id,
                         payload={"revision_no": revision.revision_no, "checksum": pack.checksum, "origin": "fact_template_auto"})
    record = _record(db, project_id)
    record["labels"] = labels
    _store(db, project_id, record, user.email)
    db.commit()
    return {"kept": len(kept), "returned": returned, "current": current(db, project_id),
            "next": "事实边界已更新；现在按它存导演稿 / 文章（之前存的稿子要重存）" + ("；退回的条目换来源重交，或从稿子里删掉、改成个人经历的说法" if returned else "")}
