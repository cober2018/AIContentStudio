"""Topic Brief API（STU-060~062）。"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_editor
from ..models import AuditLog, FactPack, FactPackStatus, TopicBrief, User, utcnow

router = APIRouter(prefix="/api/v1/topics", tags=["topics"])

VALID_CHANNELS = {"douyin", "xiaohongshu", "wechat"}


class TopicCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    audience: str | None = None
    goal: str | None = None
    angle: str | None = None
    core_thesis: str | None = None
    must_include: list[str] = Field(default_factory=list)
    forbidden: list[str] = Field(default_factory=list)
    cta: str | None = None
    brand_voice_version_id: int | None = None
    fact_pack_id: int
    channels: list[str] = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)


class TopicUpdateIn(BaseModel):
    title: str | None = None
    audience: str | None = None
    goal: str | None = None
    angle: str | None = None
    core_thesis: str | None = None
    must_include: list[str] | None = None
    forbidden: list[str] | None = None
    cta: str | None = None
    channels: list[str] | None = None
    tags: list[str] | None = None
    status: str | None = None


def _serialize(topic: TopicBrief, with_jobs: bool = False) -> dict:
    pack = topic.fact_pack
    data = {
        "id": topic.id,
        "title": topic.title,
        "audience": topic.audience,
        "goal": topic.goal,
        "angle": topic.angle,
        "core_thesis": topic.core_thesis,
        "must_include": topic.must_include_json or [],
        "forbidden": topic.forbidden_json or [],
        "cta": topic.cta,
        "brand_voice_version_id": topic.brand_voice_version_id,
        "fact_pack": {
            "id": pack.id,
            "name": pack.name,
            "version": pack.version,
            "status": pack.status,
            "checksum": pack.checksum,
            "fact_count": len(pack.items),
        },
        "channels": topic.channels or [],
        "status": topic.status,
        "tags": topic.tags or [],
        "created_at": topic.created_at.isoformat() if topic.created_at else None,
        "updated_at": topic.updated_at.isoformat() if topic.updated_at else None,
    }
    if with_jobs:
        data["content_jobs"] = [
            {
                "id": job.id,
                "channel": job.channel,
                "status": job.status,
                "error": job.error,
                "fact_pack_snapshot": job.fact_pack_snapshot,
                "draft_count": len(job.drafts),
                "latest_draft_id": job.drafts[-1].id if job.drafts else None,
            }
            for job in topic.content_jobs
        ]
    return data


@router.post("/suggest")
def suggest_topics(
    fact_pack_id: int,
    count: int = 3,
    db: Session = Depends(get_db),
    user: User = Depends(require_editor),
):
    """AI 选题发现：基于冻结 FactPack 荐题候选（场景路由 topic_discovery），人工采纳后建 Topic。"""
    from ..services.topic_suggest import suggest_for_pack

    pack = db.get(FactPack, fact_pack_id)
    if not pack:
        raise HTTPException(404, "FactPack 不存在")
    try:
        return suggest_for_pack(db, pack, count=count)
    except ValueError as exc:
        raise HTTPException(409 if "frozen" in str(exc) else 422, str(exc))


@router.post("", status_code=201)
def create_topic(
    payload: TopicCreateIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_editor),
):
    invalid = set(payload.channels) - VALID_CHANNELS
    if invalid:
        raise HTTPException(400, f"未知渠道: {sorted(invalid)}")
    pack = db.get(FactPack, payload.fact_pack_id)
    if not pack:
        raise HTTPException(404, "FactPack 不存在")
    if pack.status != FactPackStatus.frozen.value:
        raise HTTPException(409, "Topic 必须绑定 frozen 状态的 FactPack")

    topic = TopicBrief(
        title=payload.title,
        audience=payload.audience,
        goal=payload.goal,
        angle=payload.angle,
        core_thesis=payload.core_thesis,
        must_include_json=payload.must_include,
        forbidden_json=payload.forbidden,
        cta=payload.cta,
        brand_voice_version_id=payload.brand_voice_version_id,
        fact_pack_id=pack.id,
        fact_pack_version=pack.version,
        channels=payload.channels,
        tags=payload.tags,
        created_by=user.email,
    )
    db.add(topic)
    db.add(AuditLog(event="topic.created", actor=user.email, entity_type="topic_brief", entity_id=None,
                    detail_json={"title": payload.title, "fact_pack": f"{pack.name} v{pack.version}"}))
    db.commit()
    db.refresh(topic)
    return _serialize(topic, with_jobs=True)


@router.get("")
def list_topics(
    status: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(TopicBrief).order_by(TopicBrief.created_at.desc())
    if status:
        stmt = stmt.where(TopicBrief.status == status)
    return [_serialize(t) for t in db.scalars(stmt)]


@router.get("/{topic_id}")
def get_topic(topic_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    topic = db.get(TopicBrief, topic_id)
    if not topic:
        raise HTTPException(404, "Topic 不存在")
    return _serialize(topic, with_jobs=True)


@router.patch("/{topic_id}")
def update_topic(
    topic_id: int,
    payload: TopicUpdateIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_editor),
):
    topic = db.get(TopicBrief, topic_id)
    if not topic:
        raise HTTPException(404, "Topic 不存在")
    field_map = {
        "title": "title",
        "audience": "audience",
        "goal": "goal",
        "angle": "angle",
        "core_thesis": "core_thesis",
        "cta": "cta",
        "status": "status",
    }
    for api_field, model_field in field_map.items():
        value = getattr(payload, api_field)
        if value is not None:
            setattr(topic, model_field, value)
    if payload.must_include is not None:
        topic.must_include_json = payload.must_include
    if payload.forbidden is not None:
        topic.forbidden_json = payload.forbidden
    if payload.channels is not None:
        invalid = set(payload.channels) - VALID_CHANNELS
        if invalid:
            raise HTTPException(400, f"未知渠道: {sorted(invalid)}")
        topic.channels = payload.channels
    if payload.tags is not None:
        topic.tags = payload.tags
    topic.updated_at = utcnow()
    db.commit()
    return _serialize(topic, with_jobs=True)
