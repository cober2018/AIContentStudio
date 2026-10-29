"""Channel Registry（D3/§6.4）：渠道与内容形态合法性的唯一业务入口。

数据源优先级：
1. published `ChannelTemplateVersion.profile_json`（Channel Profile，新平台接入点）；
2. published 旧模板（legacy 三渠道）；
3. 内置 legacy 兜底集合（保证既有数据可读、既有行为不变）。

已下线渠道由渠道方法插件声明（selectable=False），不进入列表，也不能作为新目标。历史行仍按原值读取。

业务代码禁止再使用 `channel in {c.value for c in Channel}`；`models.Channel` 仅兼容保留。
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from ...models import ArtifactKind, ChannelTemplateVersion

# 历史渠道兜底。新平台不进这里，走 profile。x_thread 已下线，不在此列。
LEGACY_CHANNELS: dict[str, dict] = {
    "douyin": {"label": "抖音口播", "default_content_form": "spoken_script", "artifact_kind": ArtifactKind.script.value},
    "xiaohongshu": {"label": "小红书图文", "default_content_form": "image_note", "artifact_kind": ArtifactKind.text.value},
    "wechat": {"label": "公众号文章", "default_content_form": "article", "artifact_kind": ArtifactKind.text.value},
}

class _RetiredChannels(Mapping):
    """已下线渠道来自渠道方法插件，主注册表不再写死渠道名。"""

    def __getitem__(self, key: str) -> str:
        from .channel_methods import retired_message

        message = retired_message(key)
        if message is None:
            raise KeyError(key)
        return message

    def __iter__(self):
        from .channel_methods import retired_map

        return iter(retired_map())

    def __len__(self) -> int:
        from .channel_methods import retired_map

        return len(retired_map())


RETIRED_CHANNELS = _RetiredChannels()

CHANNEL_LABELS: dict[str, str] = {
    **{k: v["label"] for k, v in LEGACY_CHANNELS.items()},
    "toutiao": "今日头条",
    "baijia": "百家号",
    "zhihu": "知乎",
    "bilibili": "B站专栏",
    "sohu": "搜狐号",
    "penguin": "企鹅号",
    "netease": "网易号",
    "x": "X（Twitter）",
    "weibo": "微博",
    "xueqiu": "雪球",
    "juejin": "掘金",
}

# 平台要接入的渠道目标清单：只登记，不带任何生成、排版或发布能力。某渠道接入那次改动同时删掉这里的条目。
PLANNED_CHANNELS: dict[str, dict] = {
    "douyin": {"label": "抖音", "forms": {"video": ("视频", "video", "抖音视频"), "image_note": ("图文", "image", "抖音图文")}},
    "wechat": {"label": "公众号", "forms": {"image_message": ("图片消息", "image", "公众号图片消息")}},
    "weibo": {"label": "微博", "forms": {"image_note": ("图文", "image", "微博图文"), "video": ("视频", "video", "微博视频")}},
    "wechat_channels": {"label": "视频号", "forms": {"video": ("视频", "video", "视频号")}},
    "kuaishou": {"label": "快手", "forms": {"video": ("视频", "video", "快手")}},
    "bilibili": {"label": "B站", "forms": {"video": ("视频", "video", "B站视频")}},
    "xiaohongshu": {"label": "小红书", "forms": {"video": ("视频", "video", "小红书视频")}},
    "youtube": {"label": "YouTube", "forms": {"video": ("视频", "video", "YouTube")}},
}

FORM_LABELS: dict[str, str] = {
    "article": "文章",
    "answer": "回答",
    "thread": "推串",
    "single": "单推",
    "image_note": "图文笔记",
    "spoken_script": "口播脚本",
    "quant_research": "量化研究",
    "market_recap": "行情复盘",
    "tech_article": "技术文章",
}

VALID_ARTIFACT_KINDS = {ArtifactKind.text.value, ArtifactKind.image.value, ArtifactKind.script.value, ArtifactKind.video.value}


class ChannelRegistryError(ValueError):
    """渠道/内容形态不合法。routers 层映射为 400。"""


@dataclass
class ContentFormSpec:
    channel: str
    content_form: str
    artifact_kind: str
    source: str  # profile / legacy_template / legacy_default
    profile_version_id: int | None = None  # 承载 profile 的 ChannelTemplateVersion.id
    label: str | None = None
    workflow_key: str | None = None
    renderer_key: str | None = None
    rule_sets: list[str] = field(default_factory=list)
    discoverability_profile: str | None = None
    publisher_candidates: list[str] = field(default_factory=list)
    media_requirements: dict = field(default_factory=dict)
    graphic_requirements: dict = field(default_factory=dict)
    video_requirements: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "channel": self.channel,
            "content_form": self.content_form,
            "artifact_kind": self.artifact_kind,
            "source": self.source,
            "profile_version_id": self.profile_version_id,
            "label": self.label or FORM_LABELS.get(self.content_form, self.content_form),
            "workflow_key": self.workflow_key,
            "renderer_key": self.renderer_key,
            "rule_sets": self.rule_sets,
            "discoverability_profile": self.discoverability_profile,
            "publisher_candidates": self.publisher_candidates,
            "media_requirements": self.media_requirements,
            "graphic_requirements": self.graphic_requirements,
            "video_requirements": self.video_requirements,
        }


@dataclass
class ChannelSpec:
    channel: str
    label: str
    content_forms: list[ContentFormSpec]

    def to_dict(self) -> dict:
        return {
            "channel": self.channel,
            "label": self.label,
            "content_forms": [f.to_dict() for f in self.content_forms],
        }


def _published_templates(db: Session) -> dict[str, list[ChannelTemplateVersion]]:
    rows = db.scalars(
        select(ChannelTemplateVersion)
        .where(ChannelTemplateVersion.status == "published")
        .order_by(ChannelTemplateVersion.version.desc())
    ).all()
    by_channel: dict[str, list[ChannelTemplateVersion]] = {}
    for row in rows:
        by_channel.setdefault(row.channel, []).append(row)
    return by_channel


def _form_from_profile(channel: str, form_key: str, conf: dict, template: ChannelTemplateVersion) -> ContentFormSpec:
    artifact_kind = conf.get("artifact_kind") or ArtifactKind.text.value
    if artifact_kind not in VALID_ARTIFACT_KINDS:
        raise ChannelRegistryError(f"渠道 {channel} 内容形态 {form_key} 的 artifact_kind 非法: {artifact_kind}")
    return ContentFormSpec(
        channel=channel,
        content_form=form_key,
        artifact_kind=artifact_kind,
        source="profile",
        profile_version_id=template.id,
        label=conf.get("label") or FORM_LABELS.get(form_key, form_key),
        workflow_key=conf.get("default_workflow_key"),
        renderer_key=conf.get("renderer_key"),
        rule_sets=list(conf.get("rule_sets") or []),
        discoverability_profile=conf.get("discoverability_profile"),
        publisher_candidates=list(conf.get("publisher_candidates") or []),
        media_requirements=dict(conf.get("media_requirements") or {}),
        graphic_requirements=conf.get("graphic_requirements") if conf.get("graphic_requirements") is not None else {},
        video_requirements=conf.get("video_requirements") if conf.get("video_requirements") is not None else {},
    )


def _legacy_form(channel: str, source: str, template: ChannelTemplateVersion | None) -> ContentFormSpec:
    meta = LEGACY_CHANNELS[channel]
    return ContentFormSpec(
        channel=channel,
        content_form=meta["default_content_form"],
        artifact_kind=meta["artifact_kind"],
        source=source,
        profile_version_id=template.id if template else None,
        label=meta["label"],
        rule_sets=[],  # legacy 渠道不注入具体 RuleSet；rules_for_draft 兜底内置规则
    )


def ensure_channel_selectable(channel_key: str | None) -> None:
    """新写入不得再选择已下线渠道。空渠道仍允许。"""
    if channel_key in RETIRED_CHANNELS:
        raise ChannelRegistryError(RETIRED_CHANNELS[channel_key])


def ensure_channel_in_service(channel_key: str | None) -> None:
    """新选择不得使用已拔出的渠道方法。已有稿件的读取不走这里。"""
    ensure_channel_selectable(channel_key)
    from .channel_methods import unplugged_message, unplugged_set

    if channel_key and channel_key in unplugged_set():
        raise ChannelRegistryError(unplugged_message(channel_key))


def resolve_channel(db: Session, channel_key: str) -> ChannelSpec | None:
    """解析渠道；未注册或已下线返回 None（调用方决定报错或忽略）。"""
    if channel_key in RETIRED_CHANNELS:
        return None
    templates = _published_templates(db).get(channel_key, [])
    profile_row = next((t for t in templates if t.profile_json), None)
    forms: list[ContentFormSpec] = []
    if profile_row:
        content_forms = (profile_row.profile_json or {}).get("content_forms") or {}
        for form_key, conf in content_forms.items():
            if isinstance(conf, dict):
                forms.append(_form_from_profile(channel_key, form_key, conf, profile_row))
    if not forms:
        if templates:
            forms = [_legacy_form(channel_key, "legacy_template", templates[0])]
        elif channel_key in LEGACY_CHANNELS:
            forms = [_legacy_form(channel_key, "legacy_default", None)]
        else:
            return None
    return ChannelSpec(channel=channel_key, label=CHANNEL_LABELS.get(channel_key, channel_key), content_forms=forms)


def resolve_content_form(db: Session, channel_key: str, content_form: str | None = None) -> ContentFormSpec:
    ensure_channel_selectable(channel_key)
    spec = resolve_channel(db, channel_key)
    if spec is None:
        raise ChannelRegistryError(f"未知渠道: {channel_key}")
    if content_form is None:
        return spec.content_forms[0]
    for form in spec.content_forms:
        if form.content_form == content_form:
            return form
    known = "/".join(f.content_form for f in spec.content_forms)
    raise ChannelRegistryError(f"渠道 {channel_key} 不支持内容形态 {content_form}（可用: {known}）")


def list_channel_keys(db: Session) -> set[str]:
    from .channel_methods import unplugged_set

    keys = set(LEGACY_CHANNELS)
    keys.update(_published_templates(db).keys())
    keys.difference_update(RETIRED_CHANNELS)
    keys.difference_update(unplugged_set())
    return keys


def list_channels(db: Session) -> list[dict]:
    return [spec.to_dict() for spec in (resolve_channel(db, key) for key in sorted(list_channel_keys(db))) if spec]


def list_channel_catalog(db: Session) -> list[dict]:
    """完整渠道清单：已接入的形态标 ready，目标清单里还没接入的标 planned。"""
    catalog: dict[str, dict] = {}
    for channel in list_channels(db):
        forms = [{"content_form": f["content_form"], "label": f["label"], "artifact_kind": f["artifact_kind"], "status": "ready"} for f in channel["content_forms"]]
        catalog[channel["channel"]] = {"channel": channel["channel"], "label": channel["label"], "status": "ready", "content_forms": forms}
    for key, planned in PLANNED_CHANNELS.items():
        entry = catalog.setdefault(key, {"channel": key, "label": planned["label"], "status": "planned", "content_forms": []})
        built = {form["content_form"] for form in entry["content_forms"]}
        entry["content_forms"] += [{"content_form": form, "label": label, "artifact_kind": kind, "status": "planned", "display": display}
                                   for form, (label, kind, display) in planned["forms"].items() if form not in built]
    return list(catalog.values())


def ensure_work_channel(db: Session, channel_key: str | None) -> None:
    """作品的渠道必须是清单里已接入的；空渠道允许。"""
    ensure_channel_in_service(channel_key)
    if channel_key and channel_key not in list_channel_keys(db):
        raise ChannelRegistryError(f"渠道 {channel_key} 不在平台清单里或还没接入")


def normalize_targets(
    db: Session,
    channels: list[str] | None = None,
    targets: list[dict] | None = None,
) -> list[dict]:
    """校验并归一化交付目标为 [{channel, content_form}]；显式 targets 优先，纯 channels 走默认形态。"""
    raw: list[tuple[str, str | None]] = []
    for t in targets or []:
        if isinstance(t, str):
            raw.append((t, None))
        elif isinstance(t, dict) and t.get("channel"):
            raw.append((str(t["channel"]), t.get("content_form") or None))
        else:
            raise ChannelRegistryError(f"非法 target: {t}")
    for ch in channels or []:
        raw.append((ch, None))

    normalized: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for channel, content_form in raw:
        ensure_channel_in_service(channel)
        spec = resolve_content_form(db, channel, content_form)
        token = (spec.channel, spec.content_form)
        if token not in seen:
            seen.add(token)
            normalized.append({"channel": spec.channel, "content_form": spec.content_form})
    if not normalized:
        raise ChannelRegistryError("至少选择一个交付目标（channel × content_form）")
    return normalized
