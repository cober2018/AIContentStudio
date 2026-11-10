"""Versioned content identity, hierarchy authorization and frozen resolution."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Annotated, Any, Literal

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from ..models import (
    BrandVoiceVersion,
    ContentAccount,
    ContentBrand,
    ContentBrandRevision,
    ContentPersona,
    ContentPersonaRevision,
    ContentSeries,
    ContentSeriesRevision,
    IdentitySnapshot,
    MaterialRevision,
    SystemSetting,
    User,
)
from .studio_creative_catalog import validate_creative_profile


class CreativeProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_: Literal["persona.creative.text.v1", "persona.creative.graphic.v1", "persona.creative.video.v1"] = Field(alias="schema")
    mode: Literal["auto", "custom", "composed"]
    skill_ref: str = Field(min_length=3, max_length=150)
    style_preset_ref: str = Field(min_length=3, max_length=150)
    quality_profile_ref: str = Field(min_length=3, max_length=150)
    capability: Literal["chat", "image_generation", "video_generation", "tts", "asr"]
    model_binding: dict[str, str] | None = None
    model_chain: list[dict[str, str]] = Field(default_factory=list, max_length=8)
    capability_memory_revision_ids: list[int] = Field(default_factory=list, max_length=8)
    installed_skill_refs: list[str] = Field(default_factory=list, max_length=8)
    production_stages: dict[str, Any] = Field(default_factory=dict, max_length=10)
    parameters: dict[str, Any] = Field(default_factory=dict, max_length=32)
    stage_instruction: str | None = Field(default=None, max_length=4000)
    provenance: dict[str, Any] = Field(default_factory=dict, max_length=8)

    @model_validator(mode="before")
    @classmethod
    def drop_model_choice(cls, value):
        # 模型只在 设置 → AI 与模型 选；角色里的模型绑定不再保存。
        if isinstance(value, dict) and (value.get("model_binding") or value.get("model_chain") or value.get("mode") == "custom"):
            value = {**value, "model_binding": None, "model_chain": [],
                     "mode": "auto" if value.get("mode") == "custom" else value.get("mode")}
        return value

    @model_validator(mode="after")
    def validate_contract(self):
        validate_creative_profile(self.model_dump(mode="json", by_alias=True))
        return self


class CoverTemplateRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9-]{1,60}$")
    version: str = Field(pattern=r"^v[0-9]{1,3}$")


class IdentityProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    positioning: str | None = None
    target_audience: list[str] | None = None
    content_domains: list[str] | None = None
    expression_style: dict[str, Any] | None = None
    visual_language: dict[str, Any] | None = None
    long_term_views: list[str] | list[dict[str, Any]] | None = None
    value_propositions: list[str] | None = None
    content_boundaries: list[str] | None = None
    risk_boundaries: list[str] | None = None
    public_fact_policy: dict[str, Any] | None = None
    brand_voice_version_id: int | None = None
    # Real photos of the persona; only revision ids are kept, the files live in the common library.
    portrait_material_revision_ids: list[int] | None = Field(default=None, max_length=3)
    # The one portrait the persona's separate covers (3:4, 4:3) carry; it goes public, so it must be cleared for that.
    cover_portrait_material_revision_id: int | None = None
    # A folder in the Obsidian vault with this persona's real spoken transcripts; read fresh for each video brief.
    speech_sample_folder: str | None = Field(default=None, max_length=500)
    # The AE 封面 template every edit task of this persona renders its cover text with.
    cover_template: CoverTemplateRef | None = None
    # Logo animations the 成片 gets at its start / end, one per aspect; a work in the other aspect gets none.
    intro_clip: dict[Literal["16:9", "9:16"], int | None] | None = None
    outro_clip: dict[Literal["16:9", "9:16"], int | None] | None = None
    text_creative_profile: CreativeProfile | None = None
    graphic_creative_profile: CreativeProfile | None = None
    video_creative_profile: CreativeProfile | None = None

    @model_validator(mode="after")
    def validate_creative_modalities(self):
        for modality in ("text", "graphic", "video"):
            profile = getattr(self, f"{modality}_creative_profile")
            if profile is not None and profile.schema_ != f"persona.creative.{modality}.v1":
                raise ValueError("creative_profile_modality_mismatch")
        return self


class BrandProfile(BaseModel):
    """A brand speaks for every persona under it; it is not a persona, so it has none of the persona fields."""
    model_config = ConfigDict(extra="forbid")

    introduction: str | None = Field(default=None, max_length=1000)
    proposition: str | None = Field(default=None, max_length=500)
    offerings: list[Annotated[str, Field(max_length=200)]] | None = Field(default=None, max_length=30)
    tone_rules: list[Annotated[str, Field(max_length=300)]] | None = Field(default=None, max_length=30)
    preferred_words: list[Annotated[str, Field(max_length=50)]] | None = Field(default=None, max_length=100)
    forbidden_words: list[Annotated[str, Field(max_length=50)]] | None = Field(default=None, max_length=200)
    logo_material_revision_ids: list[int] | None = Field(default=None, max_length=3)
    # People write a colour with its name and usage, not just the hex code.
    colors: list[Annotated[str, Field(max_length=200)]] | None = Field(default=None, max_length=20)
    fonts: list[Annotated[str, Field(max_length=100)]] | None = Field(default=None, max_length=10)
    compliance: list[Annotated[str, Field(max_length=300)]] | None = Field(default=None, max_length=30)
    red_lines: list[Annotated[str, Field(max_length=100)]] | None = Field(default=None, max_length=100)


def brand_terms(profile: dict) -> list[str]:
    """Brand words and red lines a draft must not contain, checked literally like the persona's forbidden phrases."""
    brand = profile.get("brand") if isinstance(profile.get("brand"), dict) else {}
    return [term for key in ("forbidden_words", "red_lines") for term in brand.get(key) or [] if isinstance(term, str) and term]


ENTITY_MODELS = {"brand": ContentBrand, "persona": ContentPersona, "account": ContentAccount, "series": ContentSeries}
# An account records only the platform account itself; how it speaks comes from its persona.
REVISION_MODELS = {
    "brand": (ContentBrand, ContentBrandRevision, "brand_id"),
    "persona": (ContentPersona, ContentPersonaRevision, "persona_id"),
    "series": (ContentSeries, ContentSeriesRevision, "series_id"),
}


def checksum(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True)
class Hierarchy:
    brand: ContentBrand | None
    persona: ContentPersona
    account: ContentAccount | None
    series: ContentSeries | None

    def members(self) -> tuple[tuple[str, Any], ...]:
        return tuple((name, value) for name, value in (
            ("brand", self.brand), ("persona", self.persona),
            ("account", self.account), ("series", self.series),
        ) if value is not None)


def hierarchy(db: Session, user: User, *, persona_id: int, account_id: int | None = None, series_id: int | None = None, mutable: bool = False) -> Hierarchy:
    persona = db.get(ContentPersona, persona_id)
    if persona is None or persona.owner_user_id != user.id or (mutable and persona.status == "deleted"):
        raise HTTPException(404, "内容角色不存在")
    brand = db.get(ContentBrand, persona.brand_id) if persona.brand_id else None
    if persona.brand_id and (brand is None or brand.owner_user_id != user.id):
        raise HTTPException(404, "品牌不存在")
    account = db.get(ContentAccount, account_id) if account_id is not None else None
    if account_id is not None and (account is None or account.persona_id != persona.id):
        raise HTTPException(404, "账号不存在")
    series = db.get(ContentSeries, series_id) if series_id is not None else None
    if series_id is not None and series is None:
        raise HTTPException(404, "栏目不存在")
    if series is not None and (series.scope != "persona_editorial" or series.persona_id != persona.id or series.account_id is not None):
        raise HTTPException(404, "栏目不存在")
    result = Hierarchy(brand, persona, account, series)
    if mutable and any(value.status == "archived" for _, value in result.members()):
        raise HTTPException(409, "已归档身份只可查看历史")
    return result


def owned_entity(db: Session, user: User, kind: str, entity_id: int, *, mutable: bool = False):
    model = ENTITY_MODELS[kind]
    entity = db.get(model, entity_id)
    if entity is None:
        raise HTTPException(404, "身份不存在")
    if kind == "brand":
        if entity.owner_user_id != user.id:
            raise HTTPException(404, "身份不存在")
        if mutable and entity.status == "archived":
            raise HTTPException(409, "已归档身份只可查看历史")
    elif kind == "persona":
        hierarchy(db, user, persona_id=entity_id, mutable=mutable)
    elif kind == "account":
        if entity.persona_id is not None:
            hierarchy(db, user, persona_id=entity.persona_id, account_id=entity_id, mutable=mutable)
            if entity.owner_user_id is not None and entity.owner_user_id != user.id:
                raise HTTPException(404, "身份不存在")
        elif entity.owner_user_id != user.id:
            raise HTTPException(404, "账号不存在")
        if mutable and entity.status != "active":
            raise HTTPException(409, "已归档账号只可查看历史")
    else:
        if entity.scope != "persona_editorial":
            raise HTTPException(404, "身份不存在")
        hierarchy(db, user, persona_id=entity.persona_id, series_id=entity_id, mutable=mutable)
    return entity


def current_revision(db: Session, kind: str, entity_id: int):
    _, revision_model, foreign_key = REVISION_MODELS[kind]
    return db.scalar(select(revision_model).where(getattr(revision_model, foreign_key) == entity_id).order_by(revision_model.revision_no.desc()).limit(1))


def _lock_account(db: Session, user: User, account_id: int) -> ContentAccount:
    row = owned_entity(db, user, "account", account_id, mutable=True)
    selected = hierarchy(db, user, persona_id=row.persona_id, account_id=row.id, mutable=True) if row.persona_id is not None else None
    try:
        # Serialize with normal archive UPDATEs, including ancestors, before re-reading authority.
        with db.no_autoflush:
            for model, entity in ((ContentBrand, selected.brand if selected else None), (ContentPersona, selected.persona if selected else None), (ContentAccount, row)):
                if entity is not None:
                    db.execute(update(model).where(model.id == entity.id).values(status=model.status).execution_options(synchronize_session=False))
                    db.refresh(entity)
        owned_entity(db, user, "account", row.id, mutable=True)
    except OperationalError:
        db.rollback()
        raise HTTPException(409, "platform_binding_busy") from None
    except HTTPException:
        db.rollback()
        raise
    return row


_WECHAT_APP_ID = re.compile(r"^wx[0-9a-f]{16}$")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
_TOKEN_LIKE = re.compile(r"^[A-Za-z0-9+/=_-]{32,}$")
_SECRET_MARKERS = ("password", "secret", "token", "appsecret", "bearer", "api_key", "apikey", "credential")


def public_platform_id(channel: str, value: str) -> str:
    """只接受公开账号标识。拒绝密码、密钥和长令牌，且错误信息不回显原值。"""
    if channel == "wechat":
        if _WECHAT_APP_ID.fullmatch(value) is None:
            raise HTTPException(422, "platform_account_public_id_invalid")
        return value
    # Many platforms only show a nickname, which may hold spaces, full-width marks or emoji; only secret-shaped values are refused.
    value = value.strip()
    lowered = value.lower()
    if (not 0 < len(value) <= 64 or _CONTROL.search(value) or "://" in value or lowered.startswith("www.")
            or lowered.startswith("sk-") or any(marker in lowered for marker in _SECRET_MARKERS) or _TOKEN_LIKE.fullmatch(value)):
        raise HTTPException(422, "platform_account_public_id_invalid")
    return value


# Opening these in the user's own browser reuses its login; the studio never stores platform passwords.
CREATOR_LINKS = {
    "wechat": (("去后台", "https://mp.weixin.qq.com/"),),
    "baijia": (("去写作", "https://baijiahao.baidu.com/builder/rc/edit?type=news"), ("去发布视频", "https://baijiahao.baidu.com/builder/rc/edit?type=videoV2")),
    "toutiao": (("去写作", "https://mp.toutiao.com/profile_v4/graphic/publish"), ("去发布视频", "https://mp.toutiao.com/profile_v4/xigua/upload-video")),
    "zhihu": (("去写作", "https://zhuanlan.zhihu.com/write"),),
    "bilibili": (("去写专栏", "https://member.bilibili.com/platform/upload/text/edit"), ("去发布视频", "https://member.bilibili.com/platform/upload/video/frame"), ("去数据页", "https://member.bilibili.com/platform/data-up/video")),
    "xiaohongshu": (("去发布", "https://creator.xiaohongshu.com/publish/publish"), ("去数据页", "https://creator.xiaohongshu.com/statistics/data-analysis")),
    "douyin": (("去发布", "https://creator.douyin.com/creator-micro/content/upload"), ("去数据页", "https://creator.douyin.com/creator-micro/data-center/content")),
    "wechat_channels": (("去发布", "https://channels.weixin.qq.com/platform/post/create"),),
    "kuaishou": (("去发布", "https://cp.kuaishou.com/article/publish/video"),),
    "weibo": (("去发微博", "https://weibo.com/"),),
    "netease": (("去后台", "https://mp.163.com/"),),
    "penguin": (("去后台", "https://om.qq.com/"),),
    "x": (("去发帖", "https://x.com/compose/post"),),
    "juejin": (("去写作", "https://juejin.cn/editor/drafts/new"),),
    "xueqiu": (("去发帖", "https://xueqiu.com/"),),
    "youtube": (("去发布", "https://studio.youtube.com/"),),
}


def creator_links(channel: str | None) -> list[dict]:
    return [{"label": label, "url": url} for label, url in CREATOR_LINKS.get(channel or "", ())]


def _persona_platform_taken(db: Session, persona_id: int | None, channel: str, *, excluding: int | None = None) -> bool:
    if persona_id is None:
        return False
    query = select(ContentAccount.id).where(ContentAccount.persona_id == persona_id, ContentAccount.platform_channel == channel,
                                            ContentAccount.status == "active")
    if excluding is not None:
        query = query.where(ContentAccount.id != excluding)
    return db.scalar(query.limit(1)) is not None


def _account_in_use(db: Session, account_id: int) -> bool:
    from ..models import ContentMemoryEntry, ContentUnit, DeliveryTarget, SeriesAccountTarget

    return any(db.scalar(select(column).where(column == account_id).limit(1)) is not None for column in (
        ContentUnit.account_id, IdentitySnapshot.account_id, DeliveryTarget.content_account_id,
        SeriesAccountTarget.account_id, ContentMemoryEntry.account_id))


def update_account(db: Session, user: User, account_id: int, *, name: str | None, home_url: str | None, fields: set[str],
                   persona_id: int | None = None) -> ContentAccount:
    row = owned_entity(db, user, "account", account_id, mutable=True)
    if "persona_id" in fields and persona_id != row.persona_id:
        if user.role != "admin":
            raise HTTPException(403, "platform_binding_admin_required")
        if persona_id is not None:
            owned_entity(db, user, "persona", persona_id, mutable=True)
        # Works, snapshots and deliveries froze this account under its old persona; moving it would split their history.
        if _account_in_use(db, row.id):
            raise HTTPException(409, {"code": "account_in_use", "message": "这个账号已经被作品、投放或记忆用过，不能再换角色"})
        if _persona_platform_taken(db, persona_id, row.platform_channel, excluding=row.id):
            raise HTTPException(409, "persona_platform_taken")
        row.persona_id = persona_id
        row.owner_user_id = user.id
    if "name" in fields and name is not None:
        row.name = name
    if "home_url" in fields:
        url = (home_url or "").strip()
        if url and not url.startswith(("https://", "http://")):
            raise HTTPException(422, {"code": "account_home_url_invalid", "message": "主页链接要以 http:// 或 https:// 开头"})
        row.home_url = url or None
    db.commit()
    return row


def register_public_channel_account(db: Session, user: User, persona_id: int | None, *, name: str, channel: str, platform_account_id: str) -> ContentAccount:
    """在角色下登记一个平台公开身份。不保存密码，也不改已经绑定的账号。"""
    if user.role != "admin":
        raise HTTPException(403, "platform_binding_admin_required")
    if persona_id is not None:
        owned_entity(db, user, "persona", persona_id, mutable=True)
    from .content_harness.channel_registry import PUBLISH_ONLY_CHANNELS, ChannelRegistryError, ensure_channel_in_service, resolve_channel

    try:
        ensure_channel_in_service(channel)
    except ChannelRegistryError as exc:
        raise HTTPException(422, str(exc)) from None
    if resolve_channel(db, channel) is None and channel not in PUBLISH_ONLY_CHANNELS:
        raise HTTPException(422, "未知渠道")
    public_id = public_platform_id(channel, platform_account_id)
    if _persona_platform_taken(db, persona_id, channel):
        raise HTTPException(409, "persona_platform_taken")
    row = ContentAccount(owner_user_id=user.id, persona_id=persona_id, name=name, platform_channel=channel, platform_account_id=public_id)
    try:
        db.add(row)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "platform_identity_conflict") from None
    db.refresh(row)
    return row


def create_editorial_series(db: Session, user: User, persona_id: int, *, name: str) -> ContentSeries:
    """创建 Persona-owned 跨平台栏目。不要求也不接受账号；同名栏目不自动合并。"""
    owned_entity(db, user, "persona", persona_id, mutable=True)
    row = ContentSeries(persona_id=persona_id, account_id=None, scope="persona_editorial", name=name)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def publisher_connection(db: Session, user: User, account_id: int) -> dict:
    account = owned_entity(db, user, "account", account_id)
    ancestry = hierarchy(db, user, persona_id=account.persona_id, account_id=account.id)
    setting = db.get(SystemSetting, f"wechat.official.account.{account_id}", populate_existing=True)
    config = setting.value if setting else {}
    return {
        "content_account_id": account.id,
        "publisher_key": "publisher.wechat.official", "publisher_version": "1",
        "platform_account_id": account.platform_account_id,
        "revision": config.get("revision", 0), "enabled": config.get("enabled", False),
        "credential_ref": f"AICS_WECHAT_ACCOUNT_{account.id}_APPSECRET",
        "credential_version": config.get("credential_version"),
        "configured": bool(setting), "verified": False, "executable": bool(setting) and config.get("enabled") is True,
        "read_only": user.role != "admin" or any(row.status != "active" for _, row in ancestry.members()),
        "unavailable_reason": None if bool(setting) and config.get("enabled") is True else "official_connection_disabled",
    }


def save_publisher_connection(db: Session, user: User, account_id: int, *, expected_revision: int, enabled: bool, credential_version: str) -> dict:
    if user.role != "admin":
        raise HTTPException(403, "platform_binding_admin_required")
    account = _lock_account(db, user, account_id)
    try:
        if account.platform_channel != "wechat" or account.platform_account_id is None:
            raise HTTPException(409, "platform_binding_required")
        key = f"wechat.official.account.{account.id}"
        setting = db.get(SystemSetting, key, populate_existing=True)
        revision = setting.value.get("revision", 0) if setting else 0
        if revision != expected_revision:
            raise HTTPException(409, "publisher_connection_conflict")
        if setting is None:
            setting = SystemSetting(key=key)
            db.add(setting)
        setting.value = {
            "revision": revision + 1, "enabled": enabled,
            "credential_ref": f"AICS_WECHAT_ACCOUNT_{account.id}_APPSECRET",
            "credential_version": credential_version,
            "platform_account_id": account.platform_account_id,
        }
        setting.updated_by = user.email
        db.commit()
    except (IntegrityError, OperationalError):
        db.rollback()
        raise HTTPException(409, "publisher_connection_conflict") from None
    except HTTPException:
        db.rollback()
        raise
    return publisher_connection(db, user, account_id)


def revisions(db: Session, kind: str, entity_id: int) -> list:
    _, revision_model, foreign_key = REVISION_MODELS[kind]
    return db.scalars(select(revision_model).where(getattr(revision_model, foreign_key) == entity_id).order_by(revision_model.revision_no.desc()).limit(100)).all()


def save_revision(db: Session, user: User, kind: str, entity_id: int, *, expected_revision: int, profile: dict):
    owned_entity(db, user, kind, entity_id, mutable=True)
    if kind == "brand":
        # Clips moved to the persona; a page re-saving an older brand revision may still send them.
        profile = {key: value for key, value in profile.items() if key not in ("intro_clip", "outro_clip")}
    try:
        parsed = (BrandProfile if kind == "brand" else IdentityProfile).model_validate(profile)
    except ValidationError as exc:
        raise HTTPException(422, {"code": "identity_profile_invalid", "fields": [".".join(map(str, error["loc"])) for error in exc.errors()]}) from None
    data = parsed.model_dump(exclude_unset=True, by_alias=True)
    if data.get("logo_material_revision_ids") is not None:
        if any(not usable_portrait(db, item, user.email) for item in data["logo_material_revision_ids"]):
            raise HTTPException(422, {"code": "logo_invalid", "message": "Logo 必须是你自己上传、允许模型使用的图片"})
        data["logo_material_revision_ids"] = list(dict.fromkeys(data["logo_material_revision_ids"]))
    voice_id = data.get("brand_voice_version_id")
    if voice_id is not None:
        voice = db.get(BrandVoiceVersion, voice_id)
        if voice is None or voice.status != "published":
            raise HTTPException(422, "品牌语气版本不可用于新身份")
    for slot in ("intro_clip", "outro_clip"):
        if data.get(slot) is not None:
            if kind != "persona":
                raise HTTPException(422, "persona_clip_persona_only")
            data[slot] = {aspect: revision_id for aspect, revision_id in data[slot].items() if revision_id is not None}
            for aspect, revision_id in data[slot].items():
                _persona_clip(db, user, revision_id, f"{'进门' if slot == 'intro_clip' else '收尾'}片段（{aspect}）")
            if not data[slot]:
                data.pop(slot)
    if data.get("portrait_material_revision_ids") is not None:
        if kind != "persona":
            raise HTTPException(422, "portrait_persona_only")
        data["portrait_material_revision_ids"] = _portraits(db, user, data["portrait_material_revision_ids"])
    if data.get("cover_portrait_material_revision_id") is not None:
        cover_portrait = data["cover_portrait_material_revision_id"]
        if kind != "persona":
            raise HTTPException(422, "cover_portrait_persona_only")
        # Removing the portrait itself quietly drops it from the covers rather than blocking the removal.
        if cover_portrait not in (data.get("portrait_material_revision_ids") or []):
            data.pop("cover_portrait_material_revision_id")
        elif not db.get(MaterialRevision, cover_portrait).public_use_allowed:
            raise HTTPException(422, {"code": "cover_portrait_not_public", "message": "这张形象照没允许公开发布，先到素材库把它改成允许公开，再用在封面上"})
    if data.get("cover_template") is not None:
        from .craft_skills import cover_template

        if kind != "persona":
            raise HTTPException(422, "cover_template_persona_only")
        if cover_template(data["cover_template"]["id"], data["cover_template"]["version"]) is None:
            raise HTTPException(422, {"code": "cover_template_invalid", "message": "封面样式只能选 AE 模板库里的封面类模板"})
    if data.get("speech_sample_folder") is not None:
        if kind != "persona":
            raise HTTPException(422, "speech_samples_persona_only")
        before = current_revision(db, kind, entity_id)
        # Other edits carry the folder along; only a changed folder is checked, so an offline vault never blocks them.
        if data["speech_sample_folder"] == ((before.profile_json or {}) if before else {}).get("speech_sample_folder"):
            pass
        elif data["speech_sample_folder"].strip():
            from .obsidian_knowledge import check_speech_folder

            data["speech_sample_folder"] = check_speech_folder(db, data["speech_sample_folder"])
        else:
            data.pop("speech_sample_folder")
    previous = current_revision(db, kind, entity_id)
    current_no = previous.revision_no if previous else 0
    if expected_revision != current_no:
        raise HTTPException(409, "身份版本已更新，请刷新后重试")
    expression = data.get("expression_style")
    if isinstance(expression, dict) and "reference_style" in expression:
        from .capability_memory import freeze_reference_style

        if kind != "persona":
            raise HTTPException(422, "reference_style_persona_required")
        expression["reference_style"] = freeze_reference_style(db, user, entity_id, expression["reference_style"])
    _, revision_model, foreign_key = REVISION_MODELS[kind]
    row = revision_model(**{foreign_key: entity_id}, revision_no=current_no + 1, profile_json=data, checksum=checksum(data), created_by=user.email)
    db.add(row)
    try:
        db.flush()
        if kind == "persona":
            from .discovery_runtime import on_persona_revision

            on_persona_revision(db, entity_id, row)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "身份版本已更新，请刷新后重试") from exc
    db.refresh(row)
    return row


PERSONA_CLIP_MAX_MS = 5000


def _persona_clip(db: Session, user: User, revision_id: int, label: str) -> None:
    """A clip every 成片 of the persona will carry must be publishable and usable by the model, or the 成片 task cannot open."""
    revision = db.get(MaterialRevision, revision_id)
    def refuse(reason: str):
        raise HTTPException(422, {"code": "persona_clip_invalid", "message": f"{label}：{reason}"})
    if revision is None or revision.created_by != user.email:
        refuse("只能选自己素材库里的视频")
    if revision.material.kind != "video" or revision.status in {"revoked", "archived"}:
        refuse("要选一条可用的视频")
    if revision.public_use_allowed is not True or revision.model_use_allowed is not True:
        refuse("这条视频要允许公开使用、也允许给模型用（素材详情里改）")
    if not revision.duration_ms or revision.duration_ms > PERSONA_CLIP_MAX_MS:
        refuse(f"最长 5 秒，这条是 {(revision.duration_ms or 0) / 1000:.1f} 秒")


def usable_portrait(db: Session, revision_id: object, email: str | None = None) -> bool:
    revision = db.get(MaterialRevision, revision_id) if isinstance(revision_id, int) else None
    return bool(revision is not None and revision.material is not None and revision.material.kind == "image"
                and revision.material.status == "active" and revision.status not in {"revoked", "archived"}
                and revision.model_use_allowed and (email is None or revision.created_by == email))


def _portraits(db: Session, user: User, ids: list[int]) -> list[int]:
    ids = list(dict.fromkeys(ids))
    if any(not usable_portrait(db, revision_id, user.email) for revision_id in ids):
        raise HTTPException(422, {"code": "portrait_invalid", "message": "形象照必须是你自己上传、允许模型使用的图片"})
    return ids


def effective(db: Session, user: User, *, persona_id: int, account_id: int | None = None, series_id: int | None = None, mutable: bool = False) -> dict:
    selected = hierarchy(db, user, persona_id=persona_id, account_id=account_id, series_id=series_id, mutable=mutable)
    profile: dict[str, Any] = {}
    origins: dict[str, str] = {}
    creative_keys = {"text_creative_profile", "graphic_creative_profile", "video_creative_profile"}
    creative_profiles: dict[str, Any] = {}
    creative_origins: dict[str, str] = {}
    revision_ids: dict[str, int | None] = {}
    for kind, entity in selected.members():
        if kind not in REVISION_MODELS:
            continue
        revision = current_revision(db, kind, entity.id)
        revision_ids[kind] = revision.id if revision else None
        if kind == "brand":
            # The brand travels as its own block instead of filling in persona fields.
            if revision and revision.profile_json:
                profile["brand"] = {"name": entity.name, **revision.profile_json}
                origins["brand"] = "brand"
            continue
        if revision:
            for key, value in (revision.profile_json or {}).items():
                if key in creative_keys:
                    if kind != "brand":
                        creative_profiles[key] = value
                        creative_origins[key] = kind
                    continue
                profile[key] = value
                origins[key] = kind
    profile.update(creative_profiles)
    origins.update(creative_origins)
    voice_id = profile.get("brand_voice_version_id")
    if mutable and voice_id is not None:
        voice = db.get(BrandVoiceVersion, voice_id)
        if voice is None or voice.status != "published":
            raise HTTPException(409, "当前品牌语气版本不可用于新生产")
    return {
        "brand_id": selected.brand.id if selected.brand else None,
        "persona_id": selected.persona.id,
        "account_id": selected.account.id if selected.account else None,
        "series_id": selected.series.id if selected.series else None,
        "revision_ids": revision_ids,
        "brand_voice_version_id": voice_id,
        "effective_profile": profile,
        "field_origins": origins,
        "creative_profile_origins": creative_origins,
    }


def create_snapshot(db: Session, user: User, *, persona_id: int, account_id: int | None = None, series_id: int | None = None,
                    production_stages: dict | None = None, modality: str | None = None) -> IdentitySnapshot:
    resolved = effective(db, user, persona_id=persona_id, account_id=account_id, series_id=series_id, mutable=True)
    if production_stages is not None and production_stages != {}:
        from copy import deepcopy

        from .studio_creative_catalog import validate_production_stages

        validate_production_stages(production_stages)
        field = f"{modality}_creative_profile"
        profile = deepcopy(resolved["effective_profile"].get(field))
        if profile is None:
            raise HTTPException(409, "creative_profile_missing")
        profile["production_stages"] = {**profile.get("production_stages", {}), **deepcopy(production_stages)}
        validate_creative_profile(profile)
        resolved["effective_profile"] = {**resolved["effective_profile"], field: profile,
            "production_stage_origins": {modality: "product_task"}}
    revisions = resolved["revision_ids"]
    payload = {**resolved, "owner_user_id": user.id}
    row = IdentitySnapshot(
        owner_user_id=user.id,
        brand_id=resolved["brand_id"], brand_revision_id=revisions.get("brand"),
        persona_id=persona_id, persona_revision_id=revisions.get("persona"),
        account_id=account_id,
        series_id=series_id, series_revision_id=revisions.get("series"),
        brand_voice_version_id=resolved["brand_voice_version_id"],
        effective_profile_json=resolved["effective_profile"],
        field_origins_json=resolved["field_origins"], checksum=checksum(payload), created_by=user.email,
    )
    db.add(row)
    db.flush()
    return row


def snapshot_json(row: IdentitySnapshot) -> dict:
    return {
        "id": row.id, "owner_user_id": row.owner_user_id,
        "brand_id": row.brand_id, "brand_revision_id": row.brand_revision_id,
        "persona_id": row.persona_id, "persona_revision_id": row.persona_revision_id,
        "account_id": row.account_id,
        "series_id": row.series_id, "series_revision_id": row.series_revision_id,
        "brand_voice_version_id": row.brand_voice_version_id,
        "effective_profile": row.effective_profile_json,
        "field_origins": row.field_origins_json,
        "readiness": "ready" if row.effective_profile_json else "incomplete",
        "readiness_reason": None if row.effective_profile_json else "empty_profile",
        "checksum": row.checksum,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def owned_product_account(db: Session, user: User, account_id: int, *, mutable: bool = False):
    row = db.get(ContentAccount, account_id)
    if row is None:
        raise HTTPException(404, "账号不存在")
    owner_id = row.owner_user_id
    if owner_id is None and row.persona_id is not None:
        persona = db.get(ContentPersona, row.persona_id)
        owner_id = persona.owner_user_id if persona else None
    if owner_id != user.id:
        raise HTTPException(404, "账号不存在")
    if mutable and row.status != "active":
        raise HTTPException(409, "已归档账号不可使用")
    return row
