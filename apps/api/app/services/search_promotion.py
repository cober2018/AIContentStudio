"""Search promotion: subjects a person confirms, a question library on each subject, and projects AI produces end to end.

Two human gates only: confirming a subject's base material, and reviewing the platform versions a project produces
(a video keeps its own chain's stops, its 成片 being that review). Everything between is done by AI and recorded here.
"""
from __future__ import annotations

import re
from datetime import UTC, datetime

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import (
    ChannelVariantRevision,
    ContentAsset,
    ContentProject,
    ContentUnit,
    PromotionCategory,
    PromotionSubject,
    PromotionSubjectRevision,
    QuestionLibrary,
    QuestionLibraryRevision,
    Review,
    SearchProject,
    SearchWork,
    User,
)
from .discovery_runtime import digest

TOPS = {"physical": "实体产品", "digital": "数字产品", "service": "服务", "org": "品牌与机构"}
PRESETS = {
    "physical": ["消费品", "工业设备", "原材料与化学品", "零部件"],
    "digital": ["APP", "软件 / SaaS", "数据服务与接口", "网站与平台"],
    "service": ["专业服务", "工程与施工", "培训教育", "本地服务"],
    "org": ["品牌", "公司", "门店"],
}
AUDIENCES = {"individual": "个人", "business": "企业", "government": "政府"}
FORMS = {"text": "文章", "graphic": "图文", "video": "视频"}
WRITERS = {"external": "第三方模型", "platform": "平台模型"}
GENRES = {
    "definition": ("定义科普", "XX 是什么"),
    "buying-guide": ("选购指南", "XX 怎么选"),
    "comparison": ("对比评测", "A 和 B 哪个好"),
    "shortlist": ("推荐清单", "有哪些 XX"),
    "how-to": ("操作教程", "怎么用、怎么做"),
    "price-spec": ("价格与参数说明", "多少钱、参数怎么看"),
    "case-study": ("案例解读", "谁用过、效果如何"),
    "faq": ("问答合集", "一组常见问题"),
}
# Text platforms a search piece can be rewritten for; every one takes its "article" form.
PLATFORMS = {"wechat": "公众号", "zhihu": "知乎", "toutiao": "今日头条", "baijia": "百家号", "penguin": "企鹅号", "netease": "网易号", "bilibili": "B站专栏"}
DEFAULT_PLATFORMS = ["wechat", "zhihu", "toutiao"]
BATCH_LIMIT = 5
DEFAULT_BANNED = ["最好", "最佳", "第一", "首选", "顶级", "唯一", "100%", "绝对", "永久", "国家级", "全网最低"]
# What people in each category tend to ask AI, and what a piece must lean on.
HINTS = {
    "physical": {"common_questions": ["怎么选型/怎么挑", "关键参数怎么看", "哪家厂家/品牌靠谱", "价格大概多少", "和同类比有什么不同"],
                 "writing_focus": ["型号参数", "资质认证", "应用案例", "适用与不适用场景"]},
    "digital": {"common_questions": ["有什么好用的XX", "怎么接入/怎么用", "收费方式和价格", "和同类产品比怎么样", "数据安全吗"],
                "writing_focus": ["核心功能", "价格与套餐", "和同类对比", "上手步骤"]},
    "service": {"common_questions": ["XX服务怎么选", "靠不靠谱", "流程是怎样的", "费用怎么算", "多久能交付"],
                "writing_focus": ["服务流程", "资质与团队", "案例与口碑", "费用构成"]},
    "org": {"common_questions": ["XX公司怎么样", "XX品牌靠谱吗", "主要做什么", "有什么代表产品/案例"],
            "writing_focus": ["机构简介", "资质与荣誉", "代表案例", "统一的品牌说法"]},
}
RULES = [
    "第一段直接给结论，正面回答对应的问题；中间讲判断依据，最后讲适用条件和限制",
    "数据和原话只用 facts 里带出处的事实，写明出处和数据时间（如「截至 2026 年 11 月」）；没有出处的不写",
    "写到竞品时，竞品的信息也要有出处，只摆事实，不贬低",
    "文末带问答段，用用户提问的说法列 3–5 个问题并简短回答",
    "品牌、产品名称和说法与 brand_statement 一致；不用 banned_words 里的词",
    "标题前段放主词，开头一段也要含主词",
    "按 settings.tone 的基调和 settings.reader_level 的读者水平写；按 genre 的体裁结构写",
    "关键词自然出现，不堆砌，不编造参数、案例、评价",
]
VIDEO_RULE = "视频由核心稿改成口播：先用 studio.video.script-review 做口语化评审，再存导演稿"
PACKAGE_NOTICE = "如属付费推广，按规定标明「广告」。"


def _fail(status: int, code: str, message: str):
    raise HTTPException(status, {"code": code, "message": message})


def _now():
    return datetime.now(UTC)


def _iso(value):
    return value.isoformat() if value else None


# ---------- 分类 ----------
def ensure_categories(db: Session, user: User) -> None:
    if db.scalar(select(PromotionCategory.id).where(PromotionCategory.owner_user_id == user.id).limit(1)):
        return
    for top, names in PRESETS.items():
        for index, name in enumerate(names):
            db.add(PromotionCategory(owner_user_id=user.id, top_key=top, name=name, sort_order=index))
    db.flush()


def _category_json(row: PromotionCategory) -> dict:
    return {"id": row.id, "top_key": row.top_key, "top_name": TOPS[row.top_key], "name": row.name, "status": row.status}


def list_categories(db: Session, user: User) -> dict:
    ensure_categories(db, user)
    db.commit()
    rows = db.scalars(select(PromotionCategory).where(PromotionCategory.owner_user_id == user.id)
                      .order_by(PromotionCategory.sort_order, PromotionCategory.id)).all()
    return {"tops": [{"key": key, "name": name, "categories": [_category_json(r) for r in rows if r.top_key == key]}
                     for key, name in TOPS.items()]}


def _clean_name(name: str) -> str:
    name = (name or "").strip()
    if not 0 < len(name) <= 30:
        _fail(422, "promotion_category_name_invalid", "小类名称要 1–30 个字")
    return name


def _owned_category(db: Session, user: User, category_id: int) -> PromotionCategory:
    row = db.get(PromotionCategory, category_id)
    if row is None or row.owner_user_id != user.id:
        _fail(404, "promotion_category_not_found", "小类不存在")
    return row


def _category_named(db: Session, user: User, top: str, name: str) -> PromotionCategory | None:
    return db.scalar(select(PromotionCategory).where(PromotionCategory.owner_user_id == user.id, PromotionCategory.top_key == top,
                                                     PromotionCategory.name == name).limit(1))


def _add_category(db: Session, user: User, top: str, name: str) -> PromotionCategory:
    order = db.scalar(select(func.max(PromotionCategory.sort_order)).where(PromotionCategory.owner_user_id == user.id,
                                                                           PromotionCategory.top_key == top)) or 0
    row = PromotionCategory(owner_user_id=user.id, top_key=top, name=name, sort_order=order + 1)
    db.add(row)
    db.flush()
    return row


def create_category(db: Session, user: User, top: str, name: str) -> dict:
    if top not in TOPS:
        _fail(422, "promotion_category_top_invalid", "大类只能是实体产品、数字产品、服务、品牌与机构")
    ensure_categories(db, user)
    name = _clean_name(name)
    if _category_named(db, user, top, name):
        _fail(409, "promotion_category_exists", "这个大类下已经有同名小类")
    row = _add_category(db, user, top, name)
    db.commit()
    return _category_json(row)


def update_category(db: Session, user: User, category_id: int, name: str | None, status: str | None) -> dict:
    row = _owned_category(db, user, category_id)
    if name is not None:
        name = _clean_name(name)
        other = _category_named(db, user, row.top_key, name)
        if other is not None and other.id != row.id:
            _fail(409, "promotion_category_exists", "这个大类下已经有同名小类")
        row.name = name
    if status is not None:
        if status not in {"active", "disabled"}:
            _fail(422, "promotion_category_status_invalid", "状态只能是启用或停用")
        row.status = status
    db.commit()
    return _category_json(row)


# ---------- 推广对象 ----------
class Fact(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=500)
    source: str = Field(default="", max_length=500)
    url: str = Field(default="", max_length=1000)
    excerpt: str = Field(default="", max_length=1000)
    status: str = Field(default="", max_length=20)


class ProposedCategory(BaseModel):
    model_config = ConfigDict(extra="forbid")
    top_key: str = Field(pattern="^(physical|digital|service|org)$")
    name: str = Field(min_length=1, max_length=30)


class SubjectIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=200)
    category_id: int | None = Field(default=None, ge=1)
    proposed_category: ProposedCategory | None = None
    audiences: list[str] = Field(default_factory=list, max_length=3)
    brand: str = Field(default="", max_length=200)
    url: str = Field(default="", max_length=1000)
    description: str = Field(default="", max_length=20000)
    facts: list[Fact] = Field(default_factory=list, max_length=60)
    brand_statement: str = Field(default="", max_length=2000)
    banned_words: list[str] | None = Field(default=None, max_length=100)

    @field_validator("audiences")
    @classmethod
    def _audiences(cls, value):
        if set(value) - AUDIENCES.keys():
            raise ValueError("面向谁只能是个人、企业、政府")
        return list(dict.fromkeys(value))

    @field_validator("url")
    @classmethod
    def _url(cls, value):
        value = value.strip()
        if value and not re.match(r"^https?://\S+$", value):
            raise ValueError("链接要以 http:// 或 https:// 开头")
        return value


def _owned_subject(db: Session, user: User, subject_id: int) -> PromotionSubject:
    row = db.get(PromotionSubject, subject_id)
    if row is None or row.owner_user_id != user.id or row.status == "deleted":
        _fail(404, "promotion_subject_not_found", "推广对象不存在")
    return row


def latest_revision(db: Session, subject_id: int) -> PromotionSubjectRevision | None:
    return db.scalar(select(PromotionSubjectRevision).where(PromotionSubjectRevision.subject_id == subject_id)
                     .order_by(PromotionSubjectRevision.revision_no.desc()).limit(1))


def confirmed_revision(db: Session, subject_id: int) -> PromotionSubjectRevision | None:
    return db.scalar(select(PromotionSubjectRevision).where(PromotionSubjectRevision.subject_id == subject_id,
                                                            PromotionSubjectRevision.status == "confirmed")
                     .order_by(PromotionSubjectRevision.revision_no.desc()).limit(1))


def _revision_json(row: PromotionSubjectRevision | None) -> dict | None:
    if row is None:
        return None
    return {"revision_id": row.id, "revision_no": row.revision_no, "status": row.status, "origin": row.origin,
            "checksum": row.checksum, "created_at": _iso(row.created_at), "confirmed_at": _iso(row.confirmed_at), **row.payload_json}


def _subject_json(db: Session, row: PromotionSubject) -> dict:
    latest, confirmed = latest_revision(db, row.id), confirmed_revision(db, row.id)
    payload = (latest.payload_json if latest else {}) or {}
    return {"id": row.id, "status": row.status, "name": payload.get("name"), "category_name": payload.get("category_name"),
            "draft": _revision_json(latest) if latest and latest.status == "draft" else None, "confirmed": _revision_json(confirmed),
            "needs_confirmation": bool(latest and latest.status == "draft")}


def _check_fact_links(db: Session, facts: list[dict]) -> tuple[list[dict], list[dict]]:
    """AI facts must quote their source: the platform opens each link and looks for the excerpt."""
    from .fact_templates import _fetch, _normalize

    kept, rejected, fetched = [], [], {}
    for fact in facts:
        if not fact.get("url") or not fact.get("excerpt"):
            rejected.append({"text": fact["text"], "reason": "AI 起草的事实要附原文链接和摘录"})
            continue
        doc = fetched.get(fact["url"]) or _fetch(db, fact["url"], fact.get("source") or fact["url"], None)
        fetched[fact["url"]] = doc
        if doc.parse_status != "done" or not doc.raw_text:
            kept.append({**fact, "status": "needs_manual"})
        elif _normalize(fact["excerpt"]) in _normalize(doc.raw_text):
            kept.append({**fact, "source": fact.get("source") or doc.title or fact["url"], "status": "sourced"})
        else:
            rejected.append({"text": fact["text"], "url": fact["url"], "reason": "摘录在原文里找不到"})
    return kept, rejected


def _subject_payload(db: Session, user: User, data: SubjectIn, *, origin: str) -> tuple[dict, list[dict]]:
    value = data.model_dump(mode="json")
    value["name"] = value["name"].strip()
    rejected = []
    if origin == "ai":
        value["facts"], rejected = _check_fact_links(db, value["facts"])
    else:
        # A person's own facts need only a stated source; one still marked for a manual check stays so until confirmed.
        value["facts"] = [{**f, "text": f["text"].strip(), "source": f["source"].strip(),
                           "status": "needs_manual" if f.get("status") == "needs_manual" else "sourced" if f["source"].strip() or f.get("url") else "needs_source"}
                          for f in value["facts"]]
    if value["category_id"]:
        category = _owned_category(db, user, value["category_id"])
        if category.status != "active":
            _fail(409, "promotion_category_disabled", "这个小类已停用，请换一个")
        value["category_top"], value["category_name"] = category.top_key, category.name
        value["proposed_category"] = None
    elif value["proposed_category"]:
        proposal = value["proposed_category"]
        existing = _category_named(db, user, proposal["top_key"], proposal["name"].strip())
        if existing is not None and existing.status == "active":
            value["category_id"], value["proposed_category"] = existing.id, None
            value["category_top"], value["category_name"] = existing.top_key, existing.name
        else:
            value["category_top"], value["category_name"] = proposal["top_key"], proposal["name"].strip()
    if value["banned_words"] is None:
        value["banned_words"] = list(DEFAULT_BANNED)
    value["banned_words"] = list(dict.fromkeys(w.strip() for w in value["banned_words"] if w.strip()))[:100]
    return value, rejected


def list_subjects(db: Session, user: User, include_archived: bool = False) -> list[dict]:
    query = select(PromotionSubject).where(PromotionSubject.owner_user_id == user.id, PromotionSubject.status != "deleted")
    if not include_archived:
        query = query.where(PromotionSubject.status == "active")
    return [_subject_json(db, row) for row in db.scalars(query.order_by(PromotionSubject.id.desc()))]


def get_subject(db: Session, user: User, subject_id: int) -> dict:
    row = _owned_subject(db, user, subject_id)
    data = _subject_json(db, row)
    data["library"] = library_json(db, row.id)
    data["projects"] = [_project_row(db, p) for p in db.scalars(select(SearchProject).where(SearchProject.subject_id == row.id)
                                                                .order_by(SearchProject.id.desc()))]
    data["hints"] = HINTS.get(((data["confirmed"] or data["draft"] or {}).get("category_top")) or "physical")
    data["genres"] = [{"key": key, "name": name, "for": use} for key, (name, use) in GENRES.items()]
    return data


def save_subject(db: Session, user: User, subject_id: int | None, data: SubjectIn, *, origin: str, expected_revision: int | None = None) -> dict:
    """Every save is a new draft; only a person confirms one."""
    if subject_id is None:
        row = PromotionSubject(owner_user_id=user.id)
        db.add(row)
        db.flush()
        head = 0
    else:
        row = _owned_subject(db, user, subject_id)
        if row.status != "active":
            _fail(409, "promotion_subject_archived", "已归档的推广对象不能修改")
        latest = latest_revision(db, row.id)
        head = latest.revision_no if latest else 0
        if expected_revision is not None and expected_revision != head:
            _fail(409, "promotion_subject_revision_conflict", "推广对象已在别处修改，请刷新后再改")
    if data.category_id is None and data.proposed_category is None:
        _fail(422, "promotion_subject_category_missing", "要选一个小类，或提议一个新小类")
    payload, rejected = _subject_payload(db, user, data, origin=origin)
    revision = PromotionSubjectRevision(subject_id=row.id, revision_no=head + 1, payload_json=payload, checksum=digest(payload),
                                        status="draft", origin=origin, created_by=user.email)
    db.add(revision)
    db.commit()
    return {**_subject_json(db, row), "rejected_facts": rejected}


def confirm_subject(db: Session, user: User, subject_id: int, revision_no: int) -> dict:
    row = _owned_subject(db, user, subject_id)
    latest = latest_revision(db, row.id)
    if latest is None or latest.status != "draft" or latest.revision_no != revision_no:
        _fail(409, "promotion_subject_revision_conflict", "要确认的资料版本已变化，请刷新")
    payload = dict(latest.payload_json)
    if payload.get("proposed_category"):
        proposal = payload["proposed_category"]
        category = _category_named(db, user, proposal["top_key"], proposal["name"]) or _add_category(db, user, proposal["top_key"], proposal["name"])
        category.status = "active"
        payload.update(category_id=category.id, category_top=category.top_key, category_name=category.name, proposed_category=None)
    # Confirming vouches for the facts the person kept after checking them by hand.
    payload["facts"] = [{**f, "status": "sourced", "checked_by_person": True} if f.get("status") == "needs_manual" else f for f in payload.get("facts", [])]
    latest.payload_json, latest.checksum = payload, digest(payload)
    latest.status, latest.confirmed_by, latest.confirmed_at = "confirmed", user.email, _now()
    db.commit()
    return get_subject(db, user, subject_id)


def set_subject_status(db: Session, user: User, subject_id: int, status: str) -> dict:
    row = _owned_subject(db, user, subject_id)
    if status not in {"active", "archived"}:
        _fail(422, "promotion_subject_status_invalid", "状态只能是使用中或已归档")
    row.status = status
    db.commit()
    return _subject_json(db, row)


def _usable_subject(db: Session, user: User, subject_id: int) -> tuple[PromotionSubject, PromotionSubjectRevision]:
    row = _owned_subject(db, user, subject_id)
    if row.status != "active":
        _fail(409, "promotion_subject_archived", "已归档的推广对象不能再用")
    confirmed = confirmed_revision(db, row.id)
    if confirmed is None:
        _fail(409, "promotion_subject_not_confirmed", "资料还没确认，请先在页面上确认资料")
    return row, confirmed


# ---------- 问题库 ----------
class Question(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(default="", max_length=40)
    text: str = Field(min_length=1, max_length=300)
    intent: str = Field(default="", max_length=500)
    priority: int = Field(default=2, ge=1, le=3)
    source_url: str = Field(default="", max_length=1000)


class Keywords(BaseModel):
    model_config = ConfigDict(extra="forbid")
    primary: list[str] = Field(default_factory=list, max_length=20)
    long_tail: list[str] = Field(default_factory=list, max_length=60)
    brand: list[str] = Field(default_factory=list, max_length=20)


class LibraryIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    questions: list[Question] = Field(default_factory=list, max_length=100)
    keywords: Keywords = Field(default_factory=Keywords)


def _library(db: Session, subject_id: int) -> QuestionLibrary | None:
    return db.scalar(select(QuestionLibrary).where(QuestionLibrary.subject_id == subject_id))


def latest_library(db: Session, subject_id: int) -> QuestionLibraryRevision | None:
    library = _library(db, subject_id)
    if library is None:
        return None
    return db.scalar(select(QuestionLibraryRevision).where(QuestionLibraryRevision.library_id == library.id)
                     .order_by(QuestionLibraryRevision.revision_no.desc()).limit(1))


def _library_payload(data: LibraryIn, previous: dict | None) -> dict:
    value = data.model_dump(mode="json")
    used = {q["id"] for q in (previous or {}).get("questions", [])}
    taken = {q["id"] for q in value["questions"] if q["id"]}
    counter = max([int(i[1:]) for i in used | taken if re.fullmatch(r"q\d+", i)] or [0])
    seen = set()
    for question in value["questions"]:
        question["text"] = question["text"].strip()
        question["source_kind"] = "search" if question["source_url"].strip() else "inferred"
        # Ids stay stable across revisions so projects keep pointing at the same question.
        if not question["id"] or question["id"] in seen:
            counter += 1
            question["id"] = f"q{counter}"
        seen.add(question["id"])
    for key, words in value["keywords"].items():
        value["keywords"][key] = list(dict.fromkeys(w.strip() for w in words if w.strip() and len(w.strip()) <= 60))
    return value


def save_library(db: Session, user: User, subject_id: int, data: LibraryIn, *, origin: str) -> dict:
    row, confirmed = _usable_subject(db, user, subject_id)
    library = _library(db, row.id)
    if library is None:
        library = QuestionLibrary(subject_id=row.id)
        db.add(library)
        db.flush()
    latest = latest_library(db, row.id)
    payload = _library_payload(data, latest.payload_json if latest else None)
    db.add(QuestionLibraryRevision(library_id=library.id, revision_no=(latest.revision_no if latest else 0) + 1,
                                   subject_revision_id=confirmed.id, payload_json=payload, checksum=digest(payload),
                                   origin=origin, created_by=user.email))
    db.commit()
    return library_json(db, row.id)


def _project_state(db: Session, search_project: SearchProject) -> str:
    """在做 / 已有成稿: a project counts as having a finished piece once any of its versions is approved."""
    units = [w.unit_id for w in db.scalars(select(SearchWork).where(SearchWork.project_id == search_project.project_id))]
    if units and db.scalar(select(ContentAsset.id).where(ContentAsset.content_unit_id.in_(units), ContentAsset.status.in_(("approved", "exported"))).limit(1)):
        return "done"
    return "in_progress"


def library_json(db: Session, subject_id: int) -> dict | None:
    latest = latest_library(db, subject_id)
    if latest is None:
        return None
    states: dict[str, list[str]] = {}
    for project in db.scalars(select(SearchProject).where(SearchProject.subject_id == subject_id)):
        content = db.get(ContentProject, project.project_id)
        if content is None or content.status in {"deleted", "archived"}:
            continue
        states.setdefault(project.question_id, []).append(_project_state(db, project))
    questions = []
    for question in latest.payload_json.get("questions", []):
        found = states.get(question["id"], [])
        questions.append({**question, "coverage": "done" if "done" in found else "in_progress" if found else "none"})
    return {"revision_id": latest.id, "revision_no": latest.revision_no, "origin": latest.origin, "created_at": _iso(latest.created_at),
            "keywords": latest.payload_json.get("keywords", {}), "questions": questions}


# ---------- 推广项目 ----------
class ProjectItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question_id: str = Field(min_length=1, max_length=40)
    forms: list[str] = Field(min_length=1, max_length=3)
    tone: str = Field(default="专业中立科普", max_length=100)
    reader_level: str = Field(default="小白", max_length=50)
    genre: str
    writer: str = "external"
    platforms: list[str] = Field(default_factory=lambda: list(DEFAULT_PLATFORMS), min_length=1, max_length=7)
    title: str = Field(default="", max_length=300)

    @field_validator("platforms")
    @classmethod
    def _platforms(cls, value):
        if set(value) - PLATFORMS.keys():
            raise ValueError("发布平台只能是：" + "、".join(PLATFORMS.values()))
        return list(dict.fromkeys(value))

    @field_validator("forms")
    @classmethod
    def _forms(cls, value):
        if set(value) - FORMS.keys():
            raise ValueError("形式只能是文章、图文、视频")
        return [key for key in FORMS if key in value]

    @field_validator("genre")
    @classmethod
    def _genre(cls, value):
        if value not in GENRES:
            raise ValueError("体裁不在体裁库里")
        return value

    @field_validator("writer")
    @classmethod
    def _writer(cls, value):
        if value not in WRITERS:
            raise ValueError("写作方式只能是第三方模型或平台模型")
        return value


def _bind_fact_boundary(db: Session, user: User, project: ContentProject, subject_revision: PromotionSubjectRevision) -> None:
    """The subject's sourced facts become the project's frozen fact boundary, so evidence and fact checks work as for any piece."""
    from ..models import FactPack, FactPackItem, ProjectFactBoundaryRevision
    from . import factpack_service
    from .project_events import record_project_event

    facts = [f for f in (subject_revision.payload_json or {}).get("facts", []) if f.get("status") == "sourced"]
    name = f"{project.title}｜推广对象事实"[:300]
    version = (db.scalar(select(FactPack.version).where(FactPack.name == name).order_by(FactPack.version.desc()).limit(1)) or 0) + 1
    pack = FactPack(name=name, description=f"promotion_subject_revision:{subject_revision.id}", version=version, created_by=user.email)
    db.add(pack)
    db.flush()
    for order, fact in enumerate(facts):
        source = fact.get("source") or fact.get("url") or ""
        locator = {"promotion_subject_revision_id": subject_revision.id, "source": source, "url": fact.get("url") or None}
        db.add(FactPackItem(fact_pack_id=pack.id, sort_order=order, evidence_kind="third_party_quote", public_use_allowed=True, model_use_allowed=True,
                            snapshot_json={"statement": f"{fact['text']}（出处：{source}）", "excerpt": fact.get("excerpt") or fact["text"],
                                           "attribution": source, "source_title": source, "source_url": fact.get("url") or None, "source_locator": locator}))
    db.flush()
    db.refresh(pack)
    factpack_service.freeze_pack(pack)
    revision = ProjectFactBoundaryRevision(project_id=project.id, revision_no=1, fact_pack_id=pack.id, fact_pack_version=pack.version,
                                           fact_pack_checksum=pack.checksum, created_by=user.email)
    db.add(revision)
    db.flush()
    record_project_event(db, project_id=project.id, event_type="fact_boundary.frozen_bound", actor=user.email, entity_type="fact_pack",
                         entity_id=pack.id, payload={"revision_no": 1, "checksum": pack.checksum, "origin": "promotion_subject"})


def _open_one(db: Session, user: User, subject: PromotionSubject, confirmed: PromotionSubjectRevision, library: QuestionLibraryRevision,
              item: ProjectItem, question: dict) -> dict:
    from ..routers import content_projects as projects
    from . import article_chain
    from .project_events import record_project_event

    payload = confirmed.payload_json or {}
    title = (item.title.strip() or question["text"])[:300]
    project = projects.create_project(projects.ProjectIn(title=title, objective=f"回答「{question['text']}」，让用户在搜索和问 AI 时看到并引用"), db=db, user=user)
    projects.save_project_brief(projects.BriefRevisionIn(expected_revision=0, objective=f"回答「{question['text']}」",
        core_message=payload.get("brand_statement") or payload.get("name") or "", angle=GENRES[item.genre][0],
        content_constraints=["只引用推广对象里带出处的事实", "不用禁用词，不堆关键词，不编造"]), project["id"], db=db, user=user)
    content = db.get(ContentProject, project["id"])
    _bind_fact_boundary(db, user, content, confirmed)
    settings = {"forms": item.forms, "tone": item.tone.strip(), "reader_level": item.reader_level.strip(), "genre": item.genre, "writer": item.writer,
                "platforms": item.platforms}
    db.add(SearchProject(project_id=content.id, subject_id=subject.id, subject_revision_id=confirmed.id, library_revision_id=library.id,
                         question_id=question["id"], settings_json=settings, created_by=user.email))
    # The core piece is always text; graphic and video are derived from it. Graphic cards are drawn for 小红书 first.
    plan = [("core", "text", None)] + [("derived", form, "xiaohongshu" if form == "graphic" else None) for form in item.forms if form != "text"]
    units = []
    for role, modality, channel in plan:
        label = "核心稿" if role == "core" else FORMS[modality]
        unit = ContentUnit(project_id=content.id, persona_id=None, identity_snapshot_id=None, production_domain="search",
                           modality=modality, channel_id=channel, title=f"{label}｜{title}"[:300])
        db.add(unit)
        db.flush()
        db.add(SearchWork(unit_id=unit.id, project_id=content.id, role=role))
        if modality in {"text", "graphic"}:
            # The platform model writes text only for now, so a derived graphic piece goes to the third-party model like video.
            writer = item.writer if modality == "text" else "external"
            article_chain._put(db, unit.id, {"writer": writer, "decisions": [], "hidden": []})
        record_project_event(db, project_id=content.id, event_type="unit.created", actor=user.email, entity_type="content_unit",
                             entity_id=unit.id, payload={"entry": "search", "role": role})
        units.append({"unit_id": unit.id, "role": role, "modality": modality})
    db.commit()
    return {"project_id": content.id, "title": title, "question_id": question["id"], "units": units}


def open_projects(db: Session, user: User, subject_id: int, items: list[ProjectItem], *, force: bool = False) -> dict:
    if not items:
        _fail(422, "search_projects_empty", "至少开一个项目")
    if len(items) > BATCH_LIMIT:
        _fail(422, "search_batch_limit", f"一次最多开 {BATCH_LIMIT} 个项目")
    subject, confirmed = _usable_subject(db, user, subject_id)
    if not any(f.get("status") == "sourced" for f in (confirmed.payload_json or {}).get("facts", [])):
        _fail(409, "search_subject_facts_missing", "确认过的资料里没有带出处的事实，写作无据可依")
    library = latest_library(db, subject.id)
    if library is None:
        _fail(409, "search_library_missing", "还没有问题库，先生成问题库")
    coverage = {q["id"]: q for q in library_json(db, subject.id)["questions"]}
    opened, skipped = [], []
    for item in items:
        question = coverage.get(item.question_id)
        if question is None:
            skipped.append({"question_id": item.question_id, "reason": "问题不在问题库里"})
            continue
        # A question already in progress or done would only produce a duplicate source.
        if question["coverage"] != "none" and not force:
            skipped.append({"question_id": item.question_id, "reason": "这个问题已有项目在做或已有成稿"})
            continue
        opened.append(_open_one(db, user, subject, confirmed, library, item, question))
        coverage[item.question_id] = {**question, "coverage": "in_progress"}
    return {"opened": opened, "skipped": skipped}


def _owned_search_project(db: Session, user: User, project_id: int) -> tuple[ContentProject, SearchProject]:
    project = db.get(ContentProject, project_id)
    row = db.scalar(select(SearchProject).where(SearchProject.project_id == project_id))
    if project is None or project.owner_user_id != user.id or row is None or project.status == "deleted":
        _fail(404, "search_project_not_found", "推广项目不存在")
    return project, row


def _question_of(db: Session, row: SearchProject) -> dict:
    library = db.get(QuestionLibraryRevision, row.library_revision_id)
    return next((q for q in (library.payload_json or {}).get("questions", []) if q["id"] == row.question_id), {"id": row.question_id, "text": ""})


def _project_row(db: Session, row: SearchProject) -> dict:
    project = db.get(ContentProject, row.project_id)
    return {"id": row.project_id, "title": project.title if project else "", "status": project.status if project else "deleted",
            "question": _question_of(db, row).get("text"), "settings": row.settings_json, "state": _project_state(db, row),
            "pending_review": len(_pending_candidates(db, row.project_id)), "href": f"/search-promotion/projects/{row.project_id}"}


def _unit_state(db: Session, unit: ContentUnit) -> dict:
    from . import article_chain

    if unit.modality in {"text", "graphic"}:
        state = article_chain._state(db, unit.id)
        return {"state": state["state"], "label": state["label"], "writer": state["writer"]}
    return {"state": "video", "label": "视频链条（导演稿、小样、成片在作品页由你看）", "writer": "external"}


def _versions(db: Session, unit_id: int) -> list[dict]:
    rows = db.scalars(select(ChannelVariantRevision).where(ChannelVariantRevision.content_unit_id == unit_id)
                      .order_by(ChannelVariantRevision.variant_key, ChannelVariantRevision.revision_no.desc())).all()
    latest = {}
    for row in rows:
        latest.setdefault(row.variant_key, row)
    result = []
    for row in latest.values():
        asset = db.scalar(select(ContentAsset).where(ContentAsset.channel_variant_revision_id == row.id).order_by(ContentAsset.id.desc()).limit(1))
        review = db.scalar(select(Review).where(Review.content_asset_id == asset.id).order_by(Review.id.desc()).limit(1)) if asset else None
        result.append({"variant_id": row.id, "variant_key": row.variant_key, "channel": row.channel_id, "content_form": row.content_form,
                       "revision_no": row.revision_no, "title": (row.payload_json or {}).get("title"),
                       "candidate": {"id": asset.id, "status": asset.status, "candidate_hash": asset.candidate_hash} if asset else None,
                       "review": {"decision": review.decision, "comment": review.comment, "at": _iso(review.created_at)} if review else None})
    return result


def get_project(db: Session, user: User, project_id: int) -> dict:
    _project, row = _owned_search_project(db, user, project_id)
    subject = db.get(PromotionSubject, row.subject_id)
    revision = db.get(PromotionSubjectRevision, row.subject_revision_id)
    units = []
    for work, unit in db.execute(select(SearchWork, ContentUnit).join(ContentUnit, ContentUnit.id == SearchWork.unit_id)
                                 .where(SearchWork.project_id == project_id, ContentUnit.lifecycle != "deleted").order_by(SearchWork.id)).all():
        units.append({"unit_id": unit.id, "title": unit.title, "role": work.role, "modality": unit.modality, **_unit_state(db, unit),
                      "versions": _versions(db, unit.id), "href": f"/projects/{project_id}/units/{unit.id}/production"})
    return {**_project_row(db, row), "subject": {"id": subject.id, "name": (revision.payload_json or {}).get("name"), "revision_no": revision.revision_no},
            "genre_name": GENRES[row.settings_json["genre"]][0], "units": units}


# ---------- 作品读取 ----------
def is_search(unit) -> bool:
    return getattr(unit, "production_domain", "persona") == "search"


def _work(db: Session, unit) -> tuple[SearchWork | None, SearchProject | None]:
    work = db.scalar(select(SearchWork).where(SearchWork.unit_id == unit.id))
    row = db.scalar(select(SearchProject).where(SearchProject.project_id == work.project_id)) if work else None
    return work, row


def context_snapshot(db: Session, unit) -> dict | None:
    """What a search work is written from, frozen at the subject and library versions its project was opened with."""
    if not is_search(unit):
        return None
    work, row = _work(db, unit)
    if work is None or row is None:
        return None
    subject_revision = db.get(PromotionSubjectRevision, row.subject_revision_id)
    library = db.get(QuestionLibraryRevision, row.library_revision_id)
    subject = subject_revision.payload_json or {}
    question = next((q for q in (library.payload_json or {}).get("questions", []) if q["id"] == row.question_id), None)
    settings = row.settings_json or {}
    value = {
        "production_domain": "search", "role": work.role,
        "subject_revision": {"id": subject_revision.id, "revision_no": subject_revision.revision_no, "checksum": subject_revision.checksum},
        "library_revision": {"id": library.id, "revision_no": library.revision_no, "checksum": library.checksum},
        "question": question,
        "settings": {key: settings.get(key) for key in ("forms", "tone", "reader_level", "genre", "platforms")},
        "subject": {"name": subject.get("name"), "category": f"{TOPS.get(subject.get('category_top'), '')} / {subject.get('category_name', '')}",
                    "audiences": [AUDIENCES[a] for a in subject.get("audiences", [])], "brand": subject.get("brand"),
                    "url": subject.get("url"), "description": subject.get("description")},
        "brand_statement": subject.get("brand_statement", ""), "banned_words": subject.get("banned_words", []),
        # Only sourced facts may be cited; the rest are listed so the writer knows to leave them out.
        "facts": [{"text": f["text"], "source": f.get("source"), "url": f.get("url") or None} for f in subject.get("facts", []) if f.get("status") == "sourced"],
        "unsourced_facts": [f["text"] for f in subject.get("facts", []) if f.get("status") != "sourced"],
        "keywords": (library.payload_json or {}).get("keywords", {}),
    }
    return {**value, "checksum": digest(value)}


def _core_text(db: Session, project_id: int) -> str | None:
    from .article_chain import _latest, _text_of

    core = db.scalar(select(SearchWork).where(SearchWork.project_id == project_id, SearchWork.role == "core"))
    master = _latest(db, core.unit_id) if core else None
    return _text_of(master)[:12000] if master else None


def writing_brief(db: Session, unit) -> dict | None:
    snapshot = context_snapshot(db, unit)
    if snapshot is None:
        return None
    work, row = _work(db, unit)
    genre = snapshot["settings"]["genre"]
    brief = {key: value for key, value in snapshot.items() if key not in {"checksum", "subject_revision", "library_revision"}}
    rules = list(RULES) + ([VIDEO_RULE] if unit.modality == "video" else [])
    if work.role == "core" and "text" not in (snapshot["settings"]["forms"] or []):
        rules.append("这个项目不发文章：核心稿只作图文、视频的底稿，不出平台版本")
    top = (db.get(PromotionSubjectRevision, row.subject_revision_id).payload_json or {}).get("category_top")
    brief["platforms"] = [{"channel_id": key, "content_form": "article", "name": PLATFORMS[key]} for key in snapshot["settings"].get("platforms") or DEFAULT_PLATFORMS]
    return {**brief, "genre": {"key": genre, "name": GENRES[genre][0], "for": GENRES[genre][1], "skill": f"studio.search.genre.{genre}@1"},
            "writing_focus": HINTS.get(top, {}).get("writing_focus", []),
            "core_text": _core_text(db, row.project_id) if work.role == "derived" else None, "rules": rules,
            "next": ("视频按视频链条走（get_video_brief 起），导演稿、小样、成片由用户在页面上看" if unit.modality == "video" else
                     "写完存稿后用 adopt_search_draft 自己采用；图文出图后再用一次 adopt_search_draft 验收成图；"
                     "然后用 get_search_version_template / save_search_version 出各平台版本，最后 submit_search_batch 整批送审")}


def work_info(db: Session, user: User, unit_id: int) -> dict:
    unit = db.get(ContentUnit, unit_id)
    project = db.get(ContentProject, unit.project_id) if unit else None
    if unit is None or project is None or project.owner_user_id != user.id or not is_search(unit):
        _fail(404, "search_work_not_found", "搜索推广作品不存在")
    snapshot = context_snapshot(db, unit) or {}
    settings = snapshot.get("settings") or {}
    return {"unit_id": unit.id, "project_id": project.id, "project_title": project.title, "role": snapshot.get("role"),
            "subject": (snapshot.get("subject") or {}).get("name"), "category": (snapshot.get("subject") or {}).get("category"),
            "question": (snapshot.get("question") or {}).get("text"), "genre": GENRES.get(settings.get("genre"), ("",))[0],
            "tone": settings.get("tone"), "keywords": snapshot.get("keywords") or {}, "href": f"/search-promotion/projects/{project.id}"}


# ---------- AI 采用与平台版本 ----------
def _search_unit(db: Session, user: User, project_id: int, unit_id: int) -> ContentUnit:
    from .content_masters import owned_unit

    _project, unit = owned_unit(db, project_id, unit_id, user, mutate=True)
    if not is_search(unit):
        _fail(422, "search_work_required", "只有搜索推广作品走这一步")
    return unit


def adopt_draft(db: Session, user: User, project_id: int, unit_id: int) -> dict:
    """The writing model adopts its own checked draft (and, for graphic, its rendered images); people review only the platform versions."""
    from . import article_chain

    unit = _search_unit(db, user, project_id, unit_id)
    if unit.modality not in {"text", "graphic"}:
        _fail(422, "search_adopt_modality", "视频走视频链条，在页面上由人看导演稿、小样和成片")
    state = article_chain._state(db, unit_id)["state"]
    decision = {"draft_review": "approve", "draft_changes": "approve", "final_review": "accept"}.get(state)
    if decision is None:
        _fail(409, "search_adopt_not_waiting", "现在没有可以采用的稿")
    article_chain.decide(db, user, project_id, unit_id, decision, [])
    record = article_chain._record(db, unit_id)
    if record["decisions"]:
        record["decisions"][-1]["by_model"] = True
        article_chain._put(db, unit_id, record)
        db.commit()
    return article_chain.state(db, user, project_id, unit_id)


def _project_titles(db: Session, project_id: int, exclude_key: tuple[int, str] | None) -> dict[str, str]:
    titles = {}
    for unit_id in db.scalars(select(SearchWork.unit_id).where(SearchWork.project_id == project_id)):
        for version in _versions(db, unit_id):
            if (unit_id, version["variant_key"]) != exclude_key and version["title"]:
                titles[version["title"].strip()] = version["channel"]
    return titles


def _version_source(db: Session, user: User, project_id: int, unit_id: int):
    from . import article_chain

    unit = _search_unit(db, user, project_id, unit_id)
    master = article_chain._latest(db, unit_id) if unit.modality in {"text", "graphic"} else None
    if master is None or not article_chain._state(db, unit_id).get("locked"):
        _fail(409, "search_version_source_unready", "稿子还没采用；先用 adopt_search_draft 采用再出平台版本")
    work, row = _work(db, unit)
    if work.role == "core" and "text" not in (row.settings_json or {}).get("forms", []):
        _fail(409, "search_version_not_published", "这个项目不发文章，核心稿不出平台版本")
    return unit, master


def version_template(db: Session, user: User, project_id: int, unit_id: int, channel_id: str, content_form: str) -> dict:
    """The platform's mechanical adaptation, as the format the writing model rewrites from."""
    from . import channel_variants

    _unit, master = _version_source(db, user, project_id, unit_id)
    preview = channel_variants.adapt_preview(db, project_id=project_id, unit_id=unit_id, user=user, allow_unmapped=True, payload={
        "source_master_revision_id": master.id, "expected_source_payload_hash": master.payload_hash,
        "expected_source_context_hash": master.context_hash, "channel_id": channel_id, "content_form": content_form})
    return {"channel_id": channel_id, "content_form": content_form, "payload_schema": preview["payload_schema"],
            "payload": preview["payload"] if preview["payload"] is not None else payload_skeleton(preview["payload_schema"]),
            "mechanical": preview["payload"] is not None,
            "titles_already_used": list(_project_titles(db, project_id, None)),
            "rule": "按这个平台的读者换切入角度和标题句式，保留主词、品牌说法和事实出处，不新增数字；标题不能和其他版本一样"}


def save_version(db: Session, user: User, project_id: int, unit_id: int, channel_id: str, content_form: str, payload: dict) -> dict:
    from . import channel_variants

    _unit, master = _version_source(db, user, project_id, unit_id)
    key = f"search.{channel_id}.{content_form}"
    title = str((payload or {}).get("title") or "").strip()
    other = _project_titles(db, project_id, (unit_id, key)).get(title)
    # Versions of one piece must not share a title, or they read as one copied article.
    if title and other:
        _fail(409, "search_version_title_duplicate", f"标题和 {other} 版一样，换一个说法")
    preview = channel_variants.adapt_preview(db, project_id=project_id, unit_id=unit_id, user=user, allow_unmapped=True, payload={
        "source_master_revision_id": master.id, "expected_source_payload_hash": master.payload_hash,
        "expected_source_context_hash": master.context_hash, "channel_id": channel_id, "content_form": content_form})
    head = db.scalar(select(ChannelVariantRevision).where(ChannelVariantRevision.content_unit_id == unit_id, ChannelVariantRevision.variant_key == key)
                     .order_by(ChannelVariantRevision.revision_no.desc()).limit(1))
    saved = channel_variants.save_revision(db, project_id=project_id, unit_id=unit_id, user=user, payload={
        "source_master_revision_id": master.id, "expected_source_payload_hash": master.payload_hash,
        "expected_source_context_hash": master.context_hash, "channel_id": channel_id, "content_form": content_form,
        "variant_key": key, "expected_revision": head.revision_no if head else 0, "idempotency_key": f"search-version:{master.id}:{key}:{head.revision_no if head else 0}:{digest(payload)[:16]}",
        "source_kind": "manual_edit", "expected_profile_hash": preview["profile_hash"], "payload": payload,
        "asset_refs": preview["asset_refs"], "evidence_refs": preview["evidence_refs"]})
    checks = channel_variants.run_variant_checks(db, project_id, unit_id, saved["id"], user)
    return {"variant_id": saved["id"], "variant_key": key, "revision_no": saved["revision_no"], "ready": checks.get("ready"),
            "checks": [{"kind": item["check_kind"], "status": item["status"], "reasons": (item.get("report") or {}).get("reasons")} for item in checks["items"]],
            "source_gate": checks.get("source_gate")}


def payload_skeleton(schema: str) -> dict:
    """The shape a model fills when no mechanical adaptation exists (for example a 公众号 piece the mapper refuses)."""
    block = {"id": "b1", "order": 0, "kind": "paragraph", "text": "第一段：直接给结论"}
    if schema == "wechat.article.v1":
        # A 公众号 digest needs the official HTML projection, so a rewritten piece carries only title and blocks.
        return {"title": "标题", "blocks": [block, {"id": "b2", "order": 1, "kind": "heading", "text": "小标题"}]}
    return {"title": "标题", "summary": "摘要", "tags": [], "blocks": [block, {"id": "b2", "order": 1, "kind": "heading", "text": "小标题", "level": 2}]}


def to_version_payload(schema: str, draft: dict) -> dict:
    """Turn a model's plain {title, summary, blocks, tags} into the platform schema."""
    blocks = []
    for index, raw in enumerate(draft.get("blocks") or []):
        text = str(raw.get("text") or "").strip()
        if not text:
            continue
        kind = raw.get("kind") if raw.get("kind") in {"heading", "paragraph", "quote"} else "paragraph"
        block = {"id": f"b{index + 1}", "order": len(blocks), "kind": kind, "text": text[:10000]}
        if kind == "heading" and schema != "wechat.article.v1":
            block["level"] = raw.get("level") if isinstance(raw.get("level"), int) and 1 <= raw["level"] <= 6 else 2
        blocks.append(block)
    title = str(draft.get("title") or "").strip()[:200]
    summary = str(draft.get("summary") or "").strip()
    if schema == "wechat.article.v1":
        return {"title": title, "blocks": blocks}
    return {"title": title, "summary": summary[:300], "tags": [str(t).strip()[:30] for t in draft.get("tags") or [] if str(t).strip()][:10], "blocks": blocks}


def _pending_candidates(db: Session, project_id: int) -> list[ContentAsset]:
    units = list(db.scalars(select(SearchWork.unit_id).where(SearchWork.project_id == project_id)))
    if not units:
        return []
    frozen = db.scalars(select(ContentAsset).where(ContentAsset.content_unit_id.in_(units), ContentAsset.status == "frozen",
                                                  ContentAsset.channel_variant_revision_id.is_not(None)).order_by(ContentAsset.id)).all()
    # A version sent back with notes waits for AI, not for the person.
    return [asset for asset in frozen if not db.scalar(select(Review.id).where(Review.content_asset_id == asset.id,
                                                                              Review.decision == "changes_requested").limit(1))]


def submit_batch(db: Session, user: User, project_id: int) -> dict:
    """Freeze every current platform version of the project so a person reviews them on one page."""
    from . import channel_variants
    from .project_review import freeze_variant_candidate

    _owned_search_project(db, user, project_id)
    sent, blocked = [], []
    for unit_id in db.scalars(select(SearchWork.unit_id).where(SearchWork.project_id == project_id)):
        unit = db.get(ContentUnit, unit_id)
        if unit.modality == "video" or unit.lifecycle == "deleted":
            continue
        for version in _versions(db, unit_id):
            if version["candidate"] is not None:
                continue
            # Re-running would ask the fact model again and may flip a version that already passed; only unfinished ones run again.
            checks = channel_variants.projected_variant_checks(db, db.get(ChannelVariantRevision, version["variant_id"]))
            if not checks.get("ready"):
                checks = channel_variants.run_variant_checks(db, project_id, unit_id, version["variant_id"], user)
            if not checks.get("ready"):
                reasons = [f"{item['check_kind']}：{'、'.join(map(str, (item.get('report') or {}).get('reasons') or [])) or item['status']}"
                           for item in checks["items"] if item["status"] != "pass"]
                if (checks.get("source_gate") or {}).get("status") != "pass":
                    reasons.append("稿件检查没过")
                blocked.append({"unit_id": unit_id, "variant_key": version["variant_key"], "reasons": reasons + checks.get("drift_reasons", [])})
                continue
            variant = db.get(ChannelVariantRevision, version["variant_id"])
            asset = freeze_variant_candidate(db, project_id, unit_id, variant.id, user, expected_payload_hash=variant.payload_hash)
            sent.append({"unit_id": unit_id, "variant_key": version["variant_key"], "candidate_id": asset.id})
    if not sent and not blocked and not _pending_candidates(db, project_id):
        _fail(409, "search_batch_empty", "这个项目没有新的平台版本可送审")
    return {"sent": sent, "blocked": blocked, "review_url": "/search-promotion?tab=review"}


def review_feedback(db: Session, user: User, project_id: int) -> dict:
    """What the person decided on each platform version, so the writing model knows what to revise."""
    project = get_project(db, user, project_id)
    return {"project_id": project_id, "versions": [{"unit_id": unit["unit_id"], "modality": unit["modality"], **version}
                                                    for unit in project["units"] for version in unit["versions"]],
            "rule": "changes_requested 的版本按 comment 改后重新 save_search_version，再 submit_search_batch"}


# ---------- 第 2 关：成稿 ----------
def review_queue(db: Session, user: User) -> list[dict]:
    rows = db.execute(select(SearchProject, ContentProject).join(ContentProject, ContentProject.id == SearchProject.project_id)
                      .where(ContentProject.owner_user_id == user.id, ContentProject.status != "deleted").order_by(SearchProject.id.desc())).all()
    result = []
    for row, project in rows:
        items = []
        for asset in _pending_candidates(db, project.id):
            variant = db.get(ChannelVariantRevision, asset.channel_variant_revision_id)
            items.append({"candidate_id": asset.id, "candidate_hash": asset.candidate_hash, "unit_id": asset.content_unit_id,
                          "channel": asset.channel, "content_form": asset.content_form, "title": asset.title,
                          "body": asset.final_body, "payload": variant.payload_json if variant else None})
        if items:
            result.append({"project_id": project.id, "title": project.title, "question": _question_of(db, row).get("text"), "items": items})
    return result


def _candidate_in_search(db: Session, user: User, candidate_id: int) -> ContentAsset:
    asset = db.get(ContentAsset, candidate_id)
    unit = db.get(ContentUnit, asset.content_unit_id) if asset and asset.content_unit_id else None
    project = db.get(ContentProject, asset.project_id) if asset and asset.project_id else None
    if asset is None or unit is None or project is None or project.owner_user_id != user.id or not is_search(unit):
        _fail(404, "search_candidate_not_found", "这个平台版本不存在")
    return asset


def approve_version(db: Session, user: User, candidate_id: int, candidate_hash: str) -> dict:
    """Approving a version hands it off at once: a copy package, no further authorization step."""
    from ..routers.delivery import GenericTargetIn
    from .delivery import authorize_target
    from .project_review import decide_candidate

    asset = _candidate_in_search(db, user, candidate_id)
    decide_candidate(db, asset.project_id, asset.content_unit_id, asset.id, candidate_hash, "approved", None, user)
    asset = db.get(ContentAsset, asset.id)
    target = authorize_target(db, asset, GenericTargetIn(channel=asset.channel, content_form=asset.content_form, account_ref="搜索推广稿件",
                                                         content_account_id=None, authorization_version="v1", action="copy_package"), user)
    return {"candidate_id": asset.id, "status": "approved", "delivery_target_id": target.id,
            "package_url": f"/api/v1/delivery-targets/{target.id}/package.zip"}


def request_changes(db: Session, user: User, candidate_id: int, candidate_hash: str, comment: str) -> dict:
    from .project_review import decide_candidate

    if not comment.strip():
        _fail(422, "search_review_comment_required", "写一下要改哪里")
    asset = _candidate_in_search(db, user, candidate_id)
    decide_candidate(db, asset.project_id, asset.content_unit_id, asset.id, candidate_hash, "changes_requested", comment.strip()[:2000], user)
    from .search_runner import revise_after_review

    # A platform-written project is rewritten in the background; a third-party one waits for that model to read the notes.
    run = revise_after_review(db, user, asset.project_id)
    return {"candidate_id": asset.id, "status": "changes_requested", "revise_run_id": run["id"] if run else None}


def delivered(db: Session, user: User) -> list[dict]:
    """Approved versions and their packages, newest first."""
    from ..models import DeliveryTarget

    rows = db.execute(select(DeliveryTarget, ContentAsset, ContentUnit).join(ContentAsset, ContentAsset.id == DeliveryTarget.content_asset_id)
                      .join(ContentUnit, ContentUnit.id == ContentAsset.content_unit_id)
                      .where(ContentUnit.production_domain == "search", DeliveryTarget.action == "copy_package")
                      .order_by(DeliveryTarget.id.desc()).limit(200)).all()
    result = []
    for target, asset, unit in rows:
        project = db.get(ContentProject, unit.project_id)
        if project is None or project.owner_user_id != user.id:
            continue
        result.append({"delivery_target_id": target.id, "project_id": project.id, "project_title": project.title, "channel": asset.channel,
                       "content_form": asset.content_form, "title": asset.title, "body": asset.final_body,
                       "package_url": f"/api/v1/delivery-targets/{target.id}/package.zip"})
    return result


# ---------- 检查 ----------
FAQ_MARKERS = ("问答", "常见问题", "FAQ", "Q&A", "答疑")


def master_context(master) -> dict | None:
    return ((getattr(master, "edit_summary_json", None) or {}).get("search_context_snapshot")) or None


def no_persona_report() -> tuple[str, dict]:
    return "pass", {"reasons": [], "production_domain": "search", "coverage": {"semantic": "not_applicable", "reason": "search_work_has_no_persona"}}


def discoverability(title: str, blocks: list[dict], body: str, snapshot: dict, config: dict) -> tuple[str, dict]:
    """Deterministic search rules; whether the piece really answers its question is left to the writing model."""
    keywords = snapshot.get("keywords") or {}
    primary = [w for w in keywords.get("primary") or [] if w]
    brand = [w for w in keywords.get("brand") or [] if w]
    window = int(config.get("title_keyword_window") or 15)
    issues = []
    if primary and not any(w in title[:window] for w in primary):
        issues.append({"code": "title_front_missing_primary", "reason": f"标题前 {window} 字没有主词（{'、'.join(primary)}）"})
    paragraphs = [b for b in blocks if b["block_type"] in {"paragraph", "callout", "quote"} and b["text"].strip()]
    lead = paragraphs[0]["text"] if paragraphs else ""
    if not lead:
        issues.append({"code": "lead_missing", "reason": "没有开头段落，无法给出结论和摘要"})
    elif primary and not any(w in lead for w in primary + brand):
        issues.append({"code": "lead_missing_primary", "reason": "开头一段（摘要位置）没有主词或品牌词"})
    headings = [b["text"] for b in blocks if b["block_type"] == "heading"]
    questions = [b["text"] for b in blocks if b["text"].strip().endswith(("？", "?"))]
    if not any(any(m.lower() in h.lower() for m in FAQ_MARKERS) for h in headings) and len(questions) < 2:
        issues.append({"code": "faq_missing", "reason": "没有问答段（问答小标题或至少两个问句）"})
    limit = float(config.get("max_keyword_per_1000") or 8)
    length = max(len(body), 1)
    # Short pieces naturally repeat the main word a few times, so only frequent repeats count.
    stuffed = [w for w in primary + list(keywords.get("long_tail") or []) if w and body.count(w) >= 6 and body.count(w) * 1000 / length > limit]
    if stuffed:
        issues.append({"code": "keyword_stuffing", "reason": f"关键词出现太密（{'、'.join(stuffed)}），读起来像堆词"})
    banned = [w for w in snapshot.get("banned_words") or [] if w and w in f"{title}\n{body}"]
    if banned:
        issues.append({"code": "banned_words", "reason": f"用了禁用词：{'、'.join(banned)}"})
    question = (snapshot.get("question") or {}).get("text") or ""
    statement = snapshot.get("brand_statement") or ""
    judgment = f"请判断：这篇是否正面回答了「{question}」，第一段是否直接给出结论"
    if statement:
        judgment += f"，品牌说法是否与「{statement}」一致"
    report = {"reasons": [issue["code"] for issue in issues], "issues": issues, "production_domain": "search", "question": question,
              "needs_judgment": judgment + "。", "coverage": {"deterministic": "complete", "semantic": "writing_model_judgment"}}
    # Always a warning: the writing model must confirm the answer even when every mechanical rule passes.
    return "warning", report


def version_fact_check(db: Session, master, text: str) -> tuple[str, dict]:
    """A search version is rewritten per platform, so it is fact-checked like the core piece instead of compared word for word."""
    from ..models import FactPackItem, ProjectFactBoundaryRevision
    from .factchecker import run_deterministic_check
    from .generation.providers import effective_llm_config
    from .text_master_checks import _semantic_review

    boundary = db.get(ProjectFactBoundaryRevision, master.fact_boundary_revision_id) if master.fact_boundary_revision_id else None
    if boundary is None:
        return "incomplete", {"reasons": ["fact_boundary_missing"]}
    items = db.scalars(select(FactPackItem).where(FactPackItem.fact_pack_id == boundary.fact_pack_id).order_by(FactPackItem.id)).all()
    facts = [{"id": item.id, "statement": str((item.snapshot_json or {}).get("statement") or "")[:400], "value": None, "as_of": ""} for item in items]
    deterministic = run_deterministic_check(text, facts, "", [])
    issues = [{"severity": issue.severity, "span": issue.span[:160], "reason": issue.reason[:500], "source": "deterministic"} for issue in deterministic.issues[:50]]
    config = effective_llm_config("fact_review")
    configured = bool(config["provider"] == "openai_compatible" and config["model"] and config["api_key"] and config["base_url"])
    semantic, coverage = _semantic_review("fact_review", text=text, context={"facts": [{"id": f["id"], "statement": f["statement"]} for f in facts[:50]],
                                                                             "rule": "这是同一篇稿子按平台改写的版本：只核对事实、数字、出处是否与 facts 一致，措辞和角度可以不同"},
                                          configured=configured, review=(db, master))
    issues += semantic
    report = {"reasons": [], "issues": issues, "coverage": {**coverage, "deterministic": "complete", "semantic_claims": "fact_reviewed"}}
    if deterministic.result == "blocker" or any(issue["severity"] == "blocker" for issue in semantic):
        return "blocker", {**report, "reasons": ["version_fact_issue"]}
    if coverage.get("semantic") != "verified":
        return "incomplete", {**report, "reasons": [coverage.get("reason") or "version_fact_review_unavailable"]}
    if issues:
        return "warning", {**report, "reasons": ["version_fact_warning"]}
    return "pass", report


def cover_refs(db: Session, user: User, unit) -> list[dict]:
    """A 公众号 version needs a cover, so the core piece of a project publishing there gets one generated image, made once."""
    from sqlalchemy.orm.attributes import flag_modified

    from ..models import MaterialRevision

    if not is_search(unit) or unit.modality != "text":
        return []
    work, row = _work(db, unit)
    settings = dict(row.settings_json or {}) if row else {}
    if work is None or work.role != "core" or "wechat" not in (settings.get("platforms") or []) or "text" not in (settings.get("forms") or []):
        return []
    revision = db.get(MaterialRevision, (settings.get("cover") or {}).get("material_revision_id")) if settings.get("cover") else None
    if revision is None:
        from .video_chain import generate_image

        snapshot = context_snapshot(db, unit) or {}
        subject = snapshot.get("subject") or {}
        question = (snapshot.get("question") or {}).get("text") or ""
        prompt = (f"为一篇回答「{question}」的文章生成公众号封面配图，主题是{subject.get('category', '')}「{subject.get('name', '')}」。"
                  "真实质感的场景或产品意象，画面简洁、专业、留白充足，横版构图；画面里不要出现任何文字、logo、水印。")
        try:
            made = generate_image(db, user, row.project_id, unit.id, prompt[:1500], f"封面｜{question}"[:80], aspect_ratio="16:9")
        except HTTPException as exc:
            # The draft is still saved; the 公众号 version reports the missing cover and the next save tries again.
            detail = exc.detail if isinstance(exc.detail, dict) else {"code": str(exc.detail)}
            settings["cover_error"] = str(detail.get("message") or detail.get("code"))[:300]
            row.settings_json = settings
            flag_modified(row, "settings_json")
            db.commit()
            return []
        settings["cover"] = {"material_revision_id": made["material_revision_id"], "model": made.get("model_id")}
        settings.pop("cover_error", None)
        row.settings_json = settings
        flag_modified(row, "settings_json")
        db.commit()
        revision = db.get(MaterialRevision, made["material_revision_id"])
    return [{"material_revision_id": revision.id, "content_hash": revision.content_hash, "sort_order": 0,
             "role": "cover", "slot_key": "cover", "placement": {"usage": "cover"}}]
