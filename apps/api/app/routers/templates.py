"""模板中心 API（STU-050~053）：Brand Voice / Channel Template / Prompt 版本。

历史版本 immutable：只能 clone 出新 draft，publish 后不可改（PRD §7.12）。
"""

import hashlib
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_admin
from ..models import (
    BrandVoiceVersion,
    ChannelTemplateVersion,
    ContentJob,
    PromptVersion,
    TopicBrief,
    User,
)
from ..services.generation import renderers

router = APIRouter(prefix="/api/v1/templates", tags=["templates"])


def _checksum(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def _demote_other_published(db, model, scope: dict, keep_id: int) -> int:
    """发布新版本时自动下线同范围的其他生效版本（同渠道模板/Prompt、同名 Voice）。

    不变量：每个范围内至多一个 published（当前生效）；旧版本降级为 archived，
    ContentJob / TopicBrief 按 id 引用不受影响。
    """
    query = db.query(model).filter(model.status == "published", model.id != keep_id)
    for field, value in scope.items():
        query = query.filter(getattr(model, field) == value)
    return query.update({"status": "archived"}, synchronize_session=False)


def normalize_template_publication(db) -> int:
    """修复历史数据：同渠道存在多个 published 模板时，仅保留最高版本，其余降级 archived。"""
    from ..models import Channel

    demoted = 0
    for channel in {c.value for c in Channel}:
        published = db.scalars(
            select(ChannelTemplateVersion)
            .where(ChannelTemplateVersion.channel == channel, ChannelTemplateVersion.status == "published")
            .order_by(ChannelTemplateVersion.version.desc())
        ).all()
        for old in published[1:]:
            old.status = "archived"
            demoted += 1
    return demoted


class BrandVoiceIn(BaseModel):
    name: str
    description: str | None = None
    tone_rules: list[str] = Field(default_factory=list)
    preferred_words: list[str] = Field(default_factory=list)
    forbidden_words: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)


class TemplateIn(BaseModel):
    channel: str
    name: str
    structure: list[str] = Field(default_factory=list)
    length_guidance: dict = Field(default_factory=dict)
    forbidden_patterns: list[str] = Field(default_factory=list)
    output_schema: dict = Field(default_factory=dict)


class StatusIn(BaseModel):
    status: str  # draft / published / archived


# ---------- Brand Voice ----------


def _bv_serialize(bv: BrandVoiceVersion) -> dict:
    return {
        "id": bv.id,
        "name": bv.name,
        "version": bv.version,
        "description": bv.description,
        "tone_rules": bv.tone_rules or [],
        "preferred_words": bv.preferred_words or [],
        "forbidden_words": bv.forbidden_words or [],
        "examples": bv.examples or [],
        "status": bv.status,
        "checksum": bv.checksum,
    }


@router.get("/brand-voices")
def list_brand_voices(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return [_bv_serialize(bv) for bv in db.scalars(select(BrandVoiceVersion).order_by(BrandVoiceVersion.id))]


@router.post("/brand-voices/clone", status_code=201)
def clone_brand_voice(source_id: int, payload: BrandVoiceIn | None = None,
                      db: Session = Depends(get_db), user: User = Depends(require_admin)):
    source = db.get(BrandVoiceVersion, source_id)
    if not source:
        raise HTTPException(404, "Brand Voice 不存在")
    data = payload or BrandVoiceIn(
        name=source.name,
        description=source.description,
        tone_rules=source.tone_rules or [],
        preferred_words=source.preferred_words or [],
        forbidden_words=source.forbidden_words or [],
        examples=source.examples or [],
    )
    max_version = db.scalars(
        select(BrandVoiceVersion.version).where(BrandVoiceVersion.name == data.name)
        .order_by(BrandVoiceVersion.version.desc()).limit(1)
    ).first() or 0
    bv = BrandVoiceVersion(
        name=data.name,
        version=max_version + 1,
        description=data.description,
        tone_rules=data.tone_rules,
        preferred_words=data.preferred_words,
        forbidden_words=data.forbidden_words,
        examples=data.examples,
        status="draft",
    )
    db.add(bv)
    db.commit()
    db.refresh(bv)
    return _bv_serialize(bv)


@router.post("/brand-voices/{bv_id}/status")
def set_brand_voice_status(bv_id: int, payload: StatusIn, db: Session = Depends(get_db),
                           user: User = Depends(require_admin)):
    bv = db.get(BrandVoiceVersion, bv_id)
    if not bv:
        raise HTTPException(404, "Brand Voice 不存在")
    if bv.status == "published":
        raise HTTPException(409, "已发布版本 immutable，请 clone 新版本")
    bv.status = payload.status
    if payload.status == "published":
        bv.checksum = _checksum({
            "tone_rules": bv.tone_rules, "preferred_words": bv.preferred_words,
            "forbidden_words": bv.forbidden_words,
        })
        # 同名 Voice 仅一个生效版本：新发布自动下线旧版本（选题按 id 绑定，不受影响）
        _demote_other_published(db, BrandVoiceVersion, {"name": bv.name}, keep_id=bv.id)
    db.commit()
    return _bv_serialize(bv)


@router.delete("/brand-voices/{bv_id}")
def delete_brand_voice(bv_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    """删除 Brand Voice 版本。被任何选题引用时禁止（保护历史内容的口径可追溯）。"""
    bv = db.get(BrandVoiceVersion, bv_id)
    if not bv:
        raise HTTPException(404, "Brand Voice 不存在")
    referenced = db.scalars(
        select(TopicBrief.id).where(TopicBrief.brand_voice_version_id == bv_id).limit(1)
    ).first()
    if referenced:
        raise HTTPException(409, "该 Brand Voice 已被选题引用，不能删除（可归档）")
    db.delete(bv)
    db.commit()
    return {"deleted": True, "id": bv_id}


# ---------- Channel Template ----------


def _ct_serialize(ct: ChannelTemplateVersion) -> dict:
    return {
        "id": ct.id,
        "channel": ct.channel,
        "name": ct.name,
        "version": ct.version,
        "structure": ct.structure or [],
        "length_guidance": ct.length_guidance or {},
        "forbidden_patterns": ct.forbidden_patterns or [],
        "output_schema": ct.output_schema or {},
        "status": ct.status,
        "checksum": ct.checksum,
    }


@router.get("/channel-templates")
def list_channel_templates(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return [
        _ct_serialize(ct)
        for ct in db.scalars(
            select(ChannelTemplateVersion).order_by(ChannelTemplateVersion.channel, ChannelTemplateVersion.version)
        )
    ]


@router.post("/channel-templates/clone", status_code=201)
def clone_channel_template(source_id: int, payload: TemplateIn | None = None,
                           db: Session = Depends(get_db), user: User = Depends(require_admin)):
    source = db.get(ChannelTemplateVersion, source_id)
    if not source:
        raise HTTPException(404, "模板不存在")
    data = payload or TemplateIn(
        channel=source.channel,
        name=source.name,
        structure=source.structure or [],
        length_guidance=source.length_guidance or {},
        forbidden_patterns=source.forbidden_patterns or [],
        output_schema=source.output_schema or {},
    )
    max_version = db.scalars(
        select(ChannelTemplateVersion.version).where(ChannelTemplateVersion.channel == data.channel)
        .order_by(ChannelTemplateVersion.version.desc()).limit(1)
    ).first() or 0
    ct = ChannelTemplateVersion(
        channel=data.channel,
        name=data.name,
        version=max_version + 1,
        structure=data.structure,
        length_guidance=data.length_guidance,
        forbidden_patterns=data.forbidden_patterns,
        output_schema=data.output_schema,
        status="draft",
    )
    db.add(ct)
    db.commit()
    db.refresh(ct)
    return _ct_serialize(ct)


@router.post("/channel-templates/{ct_id}/status")
def set_template_status(ct_id: int, payload: StatusIn, db: Session = Depends(get_db),
                        user: User = Depends(require_admin)):
    ct = db.get(ChannelTemplateVersion, ct_id)
    if not ct:
        raise HTTPException(404, "模板不存在")
    if ct.status == "published":
        raise HTTPException(409, "已发布版本 immutable，请 clone 新版本")
    ct.status = payload.status
    if payload.status == "published":
        ct.checksum = _checksum({"structure": ct.structure, "output_schema": ct.output_schema})
        # 同渠道仅一个生效版本：新发布自动下线旧版本（历史任务按 id 引用，不受影响）
        _demote_other_published(db, ChannelTemplateVersion, {"channel": ct.channel}, keep_id=ct.id)
    db.commit()
    return _ct_serialize(ct)


@router.delete("/channel-templates/{ct_id}")
def delete_channel_template(ct_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    """删除渠道模板版本。被任何内容任务引用时禁止（任务记录生成时所用模板）。"""
    ct = db.get(ChannelTemplateVersion, ct_id)
    if not ct:
        raise HTTPException(404, "模板不存在")
    referenced = db.scalars(
        select(ContentJob.id).where(ContentJob.template_version_id == ct_id).limit(1)
    ).first()
    if referenced:
        raise HTTPException(409, "该模板已被内容任务引用，不能删除")
    db.delete(ct)
    db.commit()
    return {"deleted": True, "id": ct_id}


# ---------- Prompt Version ----------


def _pv_serialize(pv: PromptVersion) -> dict:
    return {
        "id": pv.id,
        "channel": pv.channel,
        "name": pv.name,
        "version": pv.version,
        "status": pv.status,
        "checksum": pv.checksum,
        "template_text": pv.template_text,
    }


@router.get("/prompts")
def list_prompts(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return [
        _pv_serialize(pv)
        for pv in db.scalars(select(PromptVersion).order_by(PromptVersion.channel, PromptVersion.version))
    ]


@router.post("/prompts/{pv_id}/status")
def set_prompt_status(pv_id: int, payload: StatusIn, db: Session = Depends(get_db),
                      user: User = Depends(require_admin)):
    pv = db.get(PromptVersion, pv_id)
    if not pv:
        raise HTTPException(404, "Prompt 不存在")
    if pv.status == "published":
        raise HTTPException(409, "已发布版本 immutable")
    pv.status = payload.status
    if payload.status == "published":
        pv.checksum = _checksum({"template_text": pv.template_text})
        _demote_other_published(db, PromptVersion, {"channel": pv.channel}, keep_id=pv.id)
    db.commit()
    return _pv_serialize(pv)


@router.delete("/prompts/{pv_id}")
def delete_prompt(pv_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    """删除 Prompt 版本。已发布版本由 prompts 目录文件同步产生（文件为准），不可删除。"""
    pv = db.get(PromptVersion, pv_id)
    if not pv:
        raise HTTPException(404, "Prompt 不存在")
    if pv.status == "published":
        raise HTTPException(409, "已发布 Prompt 由 prompts 目录同步产生（文件为准），不能删除")
    db.delete(pv)
    db.commit()
    return {"deleted": True, "id": pv_id}


def sync_prompt_versions_from_files(db: Session) -> int:
    """启动时将 prompts 目录同步为 draft 版本（文件为准，checksum 判断变更）。"""
    created = 0
    for channel in ("douyin", "xiaohongshu", "wechat"):
        text = (renderers.PROMPT_DIR / f"{channel}.txt").read_text(encoding="utf-8")
        checksum = _checksum({"template_text": text})
        latest = db.scalars(
            select(PromptVersion).where(PromptVersion.channel == channel)
            .order_by(PromptVersion.version.desc()).limit(1)
        ).first()
        if latest and latest.checksum == checksum:
            continue
        max_version = latest.version if latest else 0
        pv = PromptVersion(
            channel=channel,
            name=f"{channel} 结构化生成 Prompt",
            version=max_version + 1,
            template_text=text,
            status="published",
            checksum=checksum,
        )
        db.add(pv)
        db.flush()
        # 文件为准：新版本生效的同时下线该渠道旧的 published 版本
        _demote_other_published(db, PromptVersion, {"channel": channel}, keep_id=pv.id)
        created += 1
    return created
