"""The platform model running a search promotion end to end in the background.

It calls the same platform functions the third-party model calls over MCP, with the model configured for each purpose in
设置 → 模型. People still only confirm the subject and review the platform versions; each step is recorded with the model
used, its result and why it failed, and a failed project can be retried on its own.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from ..models import ContentMasterCheckRun, ContentProject, ContentUnit, SearchProject, SearchRun, SearchWork, User
from . import search_promotion as sp

log = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="search-runner")
_active: set[int] = set()
_active_lock = threading.Lock()
REWRITE_ROUNDS = 2
KINDS = {"draft_subject": "起草资料", "start": "开始", "project": "续做项目", "revise": "按意见重写"}


class StepFailed(Exception):
    pass


def _fail(status: int, code: str, message: str):
    raise HTTPException(status, {"code": code, "message": message})


def _now():
    return datetime.now(UTC)


# ---------- 记录 ----------
def _settle(db: Session, row: SearchRun) -> None:
    """A run the server lost on restart is shown as interrupted instead of running forever."""
    with _active_lock:
        alive = row.id in _active
    if row.status in {"queued", "running"} and not alive:
        row.status, row.error, row.finished_at = "interrupted", "后台重启，这次执行中断了，可以重试", _now()
        db.commit()


def run_json(db: Session, row: SearchRun) -> dict:
    _settle(db, row)
    return {"id": row.id, "kind": row.kind, "kind_name": KINDS.get(row.kind, row.kind), "status": row.status, "subject_id": row.subject_id,
            "project_id": row.project_id, "options": row.options_json, "steps": row.steps_json, "error": row.error,
            "created_at": row.created_at.isoformat() if row.created_at else None, "finished_at": row.finished_at.isoformat() if row.finished_at else None}


def _step(db: Session, run: SearchRun, step: str, status: str, detail: str = "", *, purpose: str | None = None, project_id: int | None = None) -> None:
    model = None
    if purpose:
        from .generation.providers import effective_llm_config, take_fallback_note

        config = effective_llm_config(purpose)
        model = config.get("model") or config.get("provider")
        if note := take_fallback_note(purpose):
            model = note["model"]
            detail = f"{detail}（主模型 {note['from'] or '未配置'} {note['reason']}，这次用了备用模型 {note['model']}）"
    run.steps_json = [*(run.steps_json or []), {"step": step, "status": status, "detail": detail[:500], "model": model,
                                               "project_id": project_id, "at": _now().isoformat()}]
    flag_modified(run, "steps_json")
    db.commit()


def list_runs(db: Session, user: User, *, subject_id: int | None = None, project_id: int | None = None) -> list[dict]:
    query = select(SearchRun).where(SearchRun.owner_user_id == user.id)
    if subject_id is not None:
        query = query.where(SearchRun.subject_id == subject_id)
    if project_id is not None:
        rows = [r for r in db.scalars(query.order_by(SearchRun.id.desc()).limit(50))
                if r.project_id == project_id or any(s.get("project_id") == project_id for s in r.steps_json or [])]
        return [run_json(db, r) for r in rows]
    return [run_json(db, r) for r in db.scalars(query.order_by(SearchRun.id.desc()).limit(20))]


def _enqueue(db: Session, user: User, kind: str, *, subject_id: int | None, project_id: int | None = None, options: dict | None = None) -> dict:
    busy = db.scalar(select(SearchRun.id).where(SearchRun.owner_user_id == user.id, SearchRun.status.in_(("queued", "running")),
                                                (SearchRun.project_id == project_id) if project_id else (SearchRun.subject_id == subject_id)).limit(1))
    if busy is not None:
        existing = db.get(SearchRun, busy)
        _settle(db, existing)
        if existing.status in {"queued", "running"}:
            _fail(409, "search_run_busy", "这里已经有一次执行在跑，等它结束再开始")
    row = SearchRun(owner_user_id=user.id, subject_id=subject_id, project_id=project_id, kind=kind, status="queued",
                    options_json=options or {}, steps_json=[], created_by=user.email)
    db.add(row)
    db.commit()
    with _active_lock:
        _active.add(row.id)
    _executor.submit(_execute, row.id)
    return run_json(db, row)


# ---------- 入口 ----------
def draft_subject(db: Session, user: User, name: str, links: list[str], note: str, subject_id: int | None) -> dict:
    if subject_id is not None:
        sp._owned_subject(db, user, subject_id)
    links = [link.strip() for link in links if link.strip()][:10]
    if any(not re.match(r"^https?://\S+$", link) for link in links):
        _fail(422, "search_run_link_invalid", "链接要以 http:// 或 https:// 开头")
    if not name.strip():
        _fail(422, "search_run_name_missing", "写一下推广对象的名称")
    return _enqueue(db, user, "draft_subject", subject_id=subject_id, options={"name": name.strip()[:200], "links": links, "note": note.strip()[:2000]})


def start(db: Session, user: User, subject_id: int, options: dict) -> dict:
    sp._usable_subject(db, user, subject_id)
    count = int(options.get("count") or 3)
    if not 1 <= count <= sp.BATCH_LIMIT:
        _fail(422, "search_batch_limit", f"一次 1–{sp.BATCH_LIMIT} 个项目")
    item = sp.ProjectItem.model_validate({"question_id": "q0", "genre": "faq", "writer": "platform", "forms": options.get("forms") or ["text"],
                                          "tone": options.get("tone") or "专业中立科普", "reader_level": options.get("reader_level") or "小白",
                                          "platforms": options.get("platforms") or sp.DEFAULT_PLATFORMS})
    return _enqueue(db, user, "start", subject_id=subject_id, options={"count": count, "forms": item.forms, "tone": item.tone,
                                                                       "reader_level": item.reader_level, "platforms": item.platforms})


def retry(db: Session, user: User, run_id: int) -> dict:
    row = db.get(SearchRun, run_id)
    if row is None or row.owner_user_id != user.id:
        _fail(404, "search_run_not_found", "这次执行不存在")
    _settle(db, row)
    if row.status in {"queued", "running"}:
        _fail(409, "search_run_busy", "这次执行还在跑")
    failed = [s["project_id"] for s in row.steps_json or [] if s["status"] == "failed" and s.get("project_id")]
    if row.kind == "start" and failed:
        # Projects already opened continue where they stopped; nothing is opened twice.
        return [_enqueue(db, user, "project", subject_id=row.subject_id, project_id=pid) for pid in dict.fromkeys(failed)][-1]
    return _enqueue(db, user, row.kind, subject_id=row.subject_id, project_id=row.project_id, options=row.options_json)


def continue_project(db: Session, user: User, project_id: int) -> dict:
    _project, row = sp._owned_search_project(db, user, project_id)
    return _enqueue(db, user, "project", subject_id=row.subject_id, project_id=project_id)


def revise_after_review(db: Session, user: User, project_id: int) -> dict | None:
    """When a person writes notes on a platform-written version, the platform rewrites it and sends it back."""
    row = db.scalar(select(SearchProject).where(SearchProject.project_id == project_id))
    if row is None or (row.settings_json or {}).get("writer") != "platform":
        return None
    try:
        return _enqueue(db, user, "revise", subject_id=row.subject_id, project_id=project_id)
    except HTTPException:
        return None


# ---------- 执行 ----------
def _execute(run_id: int) -> None:
    from ..db import SessionLocal

    try:
        with SessionLocal() as db:
            run = db.get(SearchRun, run_id)
            user = db.get(User, run.owner_user_id)
            run.status = "running"
            db.commit()
            try:
                if run.kind == "draft_subject":
                    _run_draft(db, user, run)
                elif run.kind == "start":
                    _run_start(db, user, run)
                elif run.kind in {"project", "revise"}:
                    _run_project(db, user, run, run.project_id)
                failed = any(s["status"] == "failed" for s in run.steps_json or [])
                run.status = "failed" if failed else "done"
                run.error = "有项目没做完，看步骤里的原因，可以重试" if failed else None
            except (StepFailed, HTTPException, ValueError) as exc:
                db.rollback()
                run = db.get(SearchRun, run_id)
                run.status, run.error = "failed", _reason(exc)
            run.finished_at = _now()
            db.commit()
    except Exception:  # noqa: BLE001 A broken run is recorded, never left running.
        log.warning("search run failed: run=%s", run_id, exc_info=True)
        try:
            with SessionLocal() as db:
                run = db.get(SearchRun, run_id)
                run.status, run.error, run.finished_at = "failed", "执行出错，可以重试", _now()
                db.commit()
        except Exception:  # noqa: BLE001
            log.warning("search run state not saved: run=%s", run_id, exc_info=True)
    finally:
        with _active_lock:
            _active.discard(run_id)


def _reason(exc: Exception) -> str:
    if isinstance(exc, HTTPException):
        detail = exc.detail
        return str(detail.get("message") or detail.get("code")) if isinstance(detail, dict) else str(detail)
    return str(exc)[:500]


def _llm(purpose: str, system: str, user_prompt: dict, schema_hint: str) -> dict:
    from .generation.providers import GenerateRequest, get_provider

    # schema_hint only switches the provider to JSON mode; the model sees field names only if the prompt states them.
    system = f"{system}\n严格按这个 JSON 结构输出，字段名和层级不要改，不要加别的字段：{schema_hint}"
    request = GenerateRequest(purpose=purpose, channel=None, system_prompt=system,
                              user_prompt=json.dumps(user_prompt, ensure_ascii=False)[:60000], schema_hint=schema_hint)
    try:
        result = asyncio.run(get_provider(purpose).generate_json(request))
    except Exception as exc:  # noqa: BLE001 Provider failures surface as a step reason, never a secret.
        raise StepFailed("模型调用失败，检查「设置 → 模型」里这个用途的配置") from exc
    if (result.usage or {}).get("mock"):
        raise StepFailed("这个用途还没配置真实模型（现在是模拟模型），先在「设置 → 模型」里配置")
    if not isinstance(result.data, dict):
        raise StepFailed("模型没返回有效结果")
    return result.data


def _search(queries: list[str], limit: int = 5) -> list[dict]:
    from . import discovery_search
    from .model_registration import topic_search_vendor

    provider, results = topic_search_vendor(), []
    for query in queries:
        try:
            rows = discovery_search.search(query, provider=provider, limit=limit)
        except Exception:  # noqa: BLE001 One failed query leaves the others.
            continue
        for row in rows:
            if all(item["url"] != row["url"] for item in results):
                results.append({"url": row["url"], "title": row["title"], "snippet": row.get("snippet", "")[:800]})
    return results[:20]


def _run_draft(db: Session, user: User, run: SearchRun) -> None:
    from .fact_templates import _fetch

    options = run.options_json
    name = options["name"]
    found = _search([name, f"{name} 参数", f"{name} 厂家"])
    _step(db, run, "网页搜索", "done", f"找到 {len(found)} 条结果")
    pages = []
    for url in list(dict.fromkeys(options["links"] + [item["url"] for item in found[:4]]))[:8]:
        doc = _fetch(db, url, url, None)
        if doc.parse_status == "done" and doc.raw_text:
            pages.append({"url": url, "title": doc.title, "text": doc.raw_text[:6000]})
    db.commit()
    if not pages:
        raise StepFailed("给的链接和搜索结果都打不开，没有可依据的资料")
    _step(db, run, "读取原文", "done", f"读到 {len(pages)} 个页面")
    tops = sp.list_categories(db, user)["tops"]
    data = _llm("topic_discovery",
                "你在为搜索推广整理推广对象的基础资料。只依据给你的页面原文，不编造。facts 每条的 excerpt 必须从对应页面原文里逐字复制，url 必须是该页面地址。只输出 JSON。",
                {"name": name, "note": options.get("note"), "pages": pages,
                 "categories": [{"top_key": t["key"], "top_name": t["name"], "names": [c["name"] for c in t["categories"] if c["status"] == "active"]} for t in tops],
                 "audiences": list(sp.AUDIENCES)},
                '{"name":"","category_top":"physical|digital|service|org","category_name":"","audiences":["business"],"brand":"","url":"","description":"",'
                '"brand_statement":"","facts":[{"text":"","url":"","excerpt":"","source":""}]}')
    top = data.get("category_top") if data.get("category_top") in sp.TOPS else "physical"
    category = next((c for t in tops if t["key"] == top for c in t["categories"] if c["name"] == data.get("category_name") and c["status"] == "active"), None)
    subject = sp.SubjectIn.model_validate({
        "name": str(data.get("name") or name)[:200], "category_id": category["id"] if category else None,
        "proposed_category": None if category else {"top_key": top, "name": str(data.get("category_name") or "其他")[:30]},
        "audiences": [a for a in data.get("audiences") or [] if a in sp.AUDIENCES], "brand": str(data.get("brand") or "")[:200],
        "url": str(data.get("url") or (options["links"][0] if options["links"] else ""))[:1000] if re.match(r"^https?://", str(data.get("url") or (options["links"][0] if options["links"] else ""))) else "",
        "description": str(data.get("description") or "")[:20000], "brand_statement": str(data.get("brand_statement") or "")[:2000],
        "facts": [{"text": str(f.get("text") or "")[:500], "url": str(f.get("url") or "")[:1000], "excerpt": str(f.get("excerpt") or "")[:1000],
                   "source": str(f.get("source") or "")[:500]} for f in (data.get("facts") or [])[:40] if str(f.get("text") or "").strip()]})
    saved = sp.save_subject(db, user, run.subject_id, subject, origin="ai")
    run.subject_id = saved["id"]
    db.commit()
    kept = len(saved["draft"]["facts"]) if saved.get("draft") else 0
    _step(db, run, "起草资料", "done", f"草稿第 {saved['draft']['revision_no']} 版：保留 {kept} 条事实，退回 {len(saved['rejected_facts'])} 条；等你确认", purpose="topic_discovery")


def _genre_for(text: str) -> str:
    rules = [("comparison", r"哪个好|对比|区别|还是|vs|VS"), ("price-spec", r"多少钱|价格|费用|报价|参数"), ("buying-guide", r"怎么选|如何选|选购|挑选|选型"),
             ("how-to", r"怎么用|如何使用|怎么做|教程|步骤"), ("shortlist", r"有哪些|推荐|排行|榜单"), ("case-study", r"案例|效果|用过"),
             ("definition", r"是什么|什么是|原理")]
    return next((genre for genre, pattern in rules if re.search(pattern, text)), "faq")


def _run_start(db: Session, user: User, run: SearchRun) -> None:
    options = run.options_json
    subject_id = run.subject_id
    if sp.latest_library(db, subject_id) is None:
        _make_library(db, user, run, subject_id)
    library = sp.library_json(db, subject_id)
    open_ones = sorted([q for q in library["questions"] if q["coverage"] == "none"], key=lambda q: q["priority"])[:options["count"]]
    if not open_ones:
        raise StepFailed("问题库里的问题都已经做过或在做，先补充问题库")
    items = [sp.ProjectItem.model_validate({"question_id": q["id"], "forms": options["forms"], "tone": options["tone"], "reader_level": options["reader_level"],
                                            "genre": _genre_for(q["text"]), "writer": "platform", "platforms": options["platforms"]}) for q in open_ones]
    opened = sp.open_projects(db, user, subject_id, items)
    _step(db, run, "开项目", "done", f"开了 {len(opened['opened'])} 个项目" + (f"，跳过 {len(opened['skipped'])} 个" if opened["skipped"] else ""))
    for project in opened["opened"]:
        _run_project(db, user, run, project["project_id"])


def _make_library(db: Session, user: User, run: SearchRun, subject_id: int) -> None:
    subject = sp.get_subject(db, user, subject_id)
    confirmed = subject["confirmed"]
    name = confirmed["name"]
    found = _search([name, f"{name} 怎么选", f"{name} 哪家好", f"{name} 价格"], limit=5)
    _step(db, run, "网页搜索", "done", f"找到 {len(found)} 条结果")
    data = _llm("discoverability",
                "你在为搜索推广整理问题库：列出用户会在搜索框或问 AI 时提的问题，以及主词、长尾词、品牌词。问题用用户的口吻。"
                "source_url 只能填给你的搜索结果里的地址，说明这个问题从哪里看到；看不出来就留空。只输出 JSON。",
                {"subject": {k: confirmed.get(k) for k in ("name", "category_name", "audiences", "brand", "description", "brand_statement")},
                 "common_questions": subject["hints"]["common_questions"], "search_results": found},
                '{"keywords":{"primary":[""],"long_tail":[""],"brand":[""]},"questions":[{"text":"","intent":"","priority":1,"source_url":""}]}')
    urls = {item["url"] for item in found}
    questions = [{"text": str(q.get("text") or "")[:300], "intent": str(q.get("intent") or "")[:500],
                  "priority": q.get("priority") if q.get("priority") in (1, 2, 3) else 2,
                  "source_url": q.get("source_url") if q.get("source_url") in urls else ""}
                 for q in (data.get("questions") or [])[:30] if str(q.get("text") or "").strip()]
    if not questions:
        raise StepFailed("模型没给出问题")
    keywords = data.get("keywords") or {}
    sp.save_library(db, user, subject_id, sp.LibraryIn.model_validate({"questions": questions, "keywords": {
        key: [str(w)[:60] for w in keywords.get(key) or [] if str(w).strip()][:20] for key in ("primary", "long_tail", "brand")}}), origin="ai")
    _step(db, run, "问题库", "done", f"{len(questions)} 个问题", purpose="discoverability")


def _run_project(db: Session, user: User, run: SearchRun, project_id: int) -> None:
    """Continue one project from wherever it stands; a failure is recorded on the project and the others go on."""
    try:
        _content, row = sp._owned_search_project(db, user, project_id)
        core = db.scalar(select(SearchWork).where(SearchWork.project_id == project_id, SearchWork.role == "core"))
        unit = db.get(ContentUnit, core.unit_id)
        from . import article_chain

        if not article_chain._state(db, unit.id).get("locked"):
            _write_core(db, user, run, project_id, unit)
        for work in db.scalars(select(SearchWork).where(SearchWork.project_id == project_id, SearchWork.role == "derived")):
            derived = db.get(ContentUnit, work.unit_id)
            _step(db, run, f"{sp.FORMS.get(derived.modality, derived.modality)}作品", "skipped", "本期平台模型只做文章，这个作品等第三方模型接手", project_id=project_id)
        if "text" in (row.settings_json or {}).get("forms", []):
            _write_versions(db, user, run, project_id, unit, row.settings_json.get("platforms") or sp.DEFAULT_PLATFORMS)
            result = sp.submit_batch(db, user, project_id)
            blocked = "；".join(f"{b['variant_key']}：{'、'.join(b['reasons'])}" for b in result["blocked"])
            _step(db, run, "整批送审", "failed" if result["blocked"] and not result["sent"] else "done",
                  f"送审 {len(result['sent'])} 个版本" + (f"；没送出：{blocked}" if blocked else ""), project_id=project_id)
    except (StepFailed, HTTPException, ValueError) as exc:
        db.rollback()
        _step(db, run, "项目", "failed", _reason(exc), project_id=project_id)


def _problems(db: Session, master_id: int) -> tuple[list[str], str | None]:
    """What the checks still object to; a missing model configuration stops the run instead of a pointless rewrite."""
    from ..models import CheckWarningJudgment

    latest: dict[str, ContentMasterCheckRun] = {}
    for check in db.scalars(select(ContentMasterCheckRun).where(ContentMasterCheckRun.master_revision_id == master_id).order_by(ContentMasterCheckRun.id)):
        latest[check.check_kind] = check
    problems, fatal = [], None
    for kind, check in latest.items():
        report = check.report_json or {}
        reasons = [str(i.get("reason")) for i in report.get("issues") or []] + [str(r) for r in report.get("reasons") or []]
        if check.status == "incomplete" and (report.get("coverage") or {}).get("reason") == "provider_not_configured":
            fatal = "事实核查用途还没配置模型，先在「设置 → 模型」里配置"
        if check.status in {"blocker", "incomplete"}:
            problems.append(f"{kind}：{'；'.join(reasons) or check.status}")
        elif check.status == "warning":
            judgment = db.scalar(select(CheckWarningJudgment).where(CheckWarningJudgment.check_run_id == check.id,
                                                                    CheckWarningJudgment.input_hash == check.input_hash))
            if judgment is None or judgment.verdict != "accept":
                problems.append(f"{kind}：{'；'.join(reasons) or '提醒'}" + (f"（判断：{judgment.reason}）" if judgment and judgment.reason else ""))
    return problems, fatal


def _to_master(draft: dict) -> dict:
    blocks = []
    for index, raw in enumerate(draft.get("blocks") or []):
        text = str(raw.get("text") or "").strip()
        if not text:
            continue
        kind = raw.get("kind") if raw.get("kind") in {"heading", "paragraph", "quote"} else "paragraph"
        block = {"id": f"b{index + 1}", "type": kind, "content": [{"text": text[:10000]}]}
        if kind == "heading":
            block["level"] = raw.get("level") if isinstance(raw.get("level"), int) and 1 <= raw["level"] <= 4 else 2
        blocks.append(block)
    if not blocks:
        raise StepFailed("模型没写出正文")
    return {"title": str(draft.get("title") or "").strip()[:500], "document": {"schema": "studio.text.document.v1", "blocks": blocks}}


def _write_core(db: Session, user: User, run: SearchRun, project_id: int, unit: ContentUnit) -> None:
    import uuid

    from . import article_chain, content_masters
    from .studio_creative_catalog import load_skill

    brief = article_chain.brief(db, user, project_id, unit.id)
    search = brief["search"]
    genre = load_skill(search["genre"]["skill"])["instruction"]
    issues: list[str] = []
    for attempt in range(REWRITE_ROUNDS + 1):
        data = _llm("generate", "你是搜索推广文章的写作者。严格按体裁结构和写作规则写，只用 facts 里带出处的事实并写明出处。只输出 JSON。",
                    {"task": search, "genre_method": genre, "facts": brief["facts"], "previous_problems": issues,
                     "format": "blocks 按顺序：kind 为 heading / paragraph / quote；heading 写 level（2 或 3）"},
                    '{"title":"","blocks":[{"kind":"paragraph","text":""},{"kind":"heading","level":2,"text":""}]}')
        master = article_chain._latest(db, unit.id)
        saved = content_masters.save_revision(db, project_id=project_id, unit_id=unit.id, user=user, payload={
            "expected_revision": master.revision_no if master else 0, "parent_revision_id": master.id if master else None,
            "idempotency_key": f"search-runner:{uuid.uuid4().hex}", "payload_schema": "text.master.v2", "payload": _to_master(data),
            "source_kind": "user_edit", "edit_summary": {"article_chain": "draft", "search_run": run.id, "attempt": attempt},
            "asset_refs": sp.cover_refs(db, user, unit), "evidence_refs": []})
        db.commit()
        content_masters.run_checks(db, project_id, unit.id, saved["id"], user)
        issues, fatal = _problems(db, saved["id"])
        if fatal:
            raise StepFailed(fatal)
        if not issues:
            sp.adopt_draft(db, user, project_id, unit.id)
            _step(db, run, "核心稿", "done", f"第 {attempt + 1} 稿通过检查并采用", purpose="generate", project_id=project_id)
            return
        _step(db, run, "核心稿", "retry" if attempt < REWRITE_ROUNDS else "failed", "；".join(issues)[:500], purpose="generate", project_id=project_id)
    raise StepFailed(f"重写 {REWRITE_ROUNDS} 轮后检查仍没过：{'；'.join(issues)[:300]}")


def _version_problems(result: dict) -> list[str]:
    return [f"{c['kind']}：{'、'.join(map(str, c.get('reasons') or [])) or c['status']}" for c in result["checks"] if c["status"] != "pass"]


def _write_versions(db: Session, user: User, run: SearchRun, project_id: int, unit: ContentUnit, platforms: list[str], notes: dict[str, str] | None = None) -> None:
    from . import article_chain

    master = article_chain._latest(db, unit.id)
    core_text = article_chain._text_of(master)[:12000]
    snapshot = sp.context_snapshot(db, unit) or {}
    existing = {v["channel"]: v for v in sp._versions(db, unit.id)}
    # Versions the person sent back are rewritten with their comment; approved or waiting ones are left alone.
    feedback = notes if notes is not None else revise_notes(db, project_id)
    for channel in platforms:
        current = existing.get(channel)
        if current and current["candidate"] and channel not in feedback:
            continue
        issues: list[str] = []
        for attempt in range(REWRITE_ROUNDS + 1):
            template = sp.version_template(db, user, project_id, unit.id, channel, "article")
            data = _llm("platform_adaptation", "你把一篇搜索推广文章改写成某个平台的版本：换切入角度和标题句式，保留主词、品牌说法、事实和出处，不新增数字。只输出 JSON。",
                        {"platform": sp.PLATFORMS[channel], "core_article": core_text, "question": (snapshot.get("question") or {}).get("text"),
                         "keywords": snapshot.get("keywords"), "brand_statement": snapshot.get("brand_statement"), "banned_words": snapshot.get("banned_words"),
                         "titles_already_used": template["titles_already_used"], "reviewer_comment": feedback.get(channel), "previous_problems": issues},
                        '{"title":"","summary":"","tags":[""],"blocks":[{"kind":"paragraph","text":""},{"kind":"heading","level":2,"text":""}]}')
            payload = sp.to_version_payload(template["payload_schema"], data)
            try:
                result = sp.save_version(db, user, project_id, unit.id, channel, "article", payload)
            except HTTPException as exc:
                issues = [_reason(exc)]
                db.rollback()
                continue
            issues = _version_problems(result)
            if result["ready"]:
                _step(db, run, f"{sp.PLATFORMS[channel]}版", "done", "改写通过检查" + ("（按意见重写）" if channel in feedback else ""),
                      purpose="platform_adaptation", project_id=project_id)
                break
            _step(db, run, f"{sp.PLATFORMS[channel]}版", "retry", "；".join(issues)[:500], purpose="platform_adaptation", project_id=project_id)
            if any("provider_not_configured" in item for item in issues):
                raise StepFailed("事实核查用途还没配置模型，先在「设置 → 模型」里配置")
        else:
            _step(db, run, f"{sp.PLATFORMS[channel]}版", "failed", "；".join(issues)[:500], purpose="platform_adaptation", project_id=project_id)


def revise_notes(db: Session, project_id: int) -> dict[str, str]:
    notes = {}
    for unit_id in db.scalars(select(SearchWork.unit_id).where(SearchWork.project_id == project_id)):
        for version in sp._versions(db, unit_id):
            if version["review"] and version["review"]["decision"] == "changes_requested" and version["candidate"] and version["candidate"]["status"] == "frozen":
                notes[version["channel"]] = version["review"]["comment"] or ""
    return notes
