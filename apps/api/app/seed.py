"""种子数据：管理员、渠道模板、Brand Voice、V1 平台 Profiles。`make seed` 或 python -m app.seed。"""

from .db import SessionLocal, init_db
from .models import BrandVoiceVersion, ChannelTemplateVersion, User
from .routers.templates import sync_prompt_versions_from_files
from .services.content_harness.channel_methods import length_guidance_for

DOUYIN_STRUCTURE = ["Hook 3-8s", "背景", "核心观点 1", "证据", "核心观点 2", "风险/反面信息", "总结", "CTA"]
XHS_STRUCTURE = ["标题候选", "封面文案", "正文", "小标题", "卡片文案", "图片 Prompt", "Tags"]
WECHAT_STRUCTURE = ["标题", "摘要", "导语", "主体章节", "风险提示", "结尾", "配图建议", "数据来源列表"]


def _form(artifact_kind, family, *, renderer, rules=None, seo=None, publishers=None, media=None, label=None):
    return {
        "artifact_kind": artifact_kind,
        "label": label,
        "default_workflow_key": family,
        "renderer_key": renderer,
        "rule_sets": rules or [],
        "discoverability_profile": seo,
        "publisher_candidates": publishers or ["publisher.copy"],
        "media_requirements": media or {},
    }


def _article(label, family, *, seo=None, media=None, publishers=None):
    return _form("text", family, renderer="renderer.generic.markdown", seo=seo, media=media, publishers=publishers, label=label)


def v1_channel_profile_definitions() -> list[tuple[str, str, dict]]:
    """V1 的 14 个渠道档案。配置存在不等于远端发布已验证。"""
    return [
        ("wechat", "公众号", {"content_forms": {"article": _article(
            "文章", "workflow.article.editorial", seo="seo.wechat.article",
            publishers=["publisher.wechat.wewrite", "publisher.copy"],
            media={"cover": "required", "inline": "optional"},
        )}}),
        ("toutiao", "今日头条", {"content_forms": {"article": _article("文章", "workflow.article.feed")}}),
        ("baijia", "百家号", {"content_forms": {"article": _article("文章", "workflow.article.feed")}}),
        ("zhihu", "知乎", {"content_forms": {
            "article": _article("文章", "workflow.article.editorial", seo="seo.default"),
            "answer": _form("text", "workflow.qa.answer", renderer="renderer.generic.markdown", label="回答"),
        }}),
        ("bilibili", "B站专栏", {"content_forms": {"article": _article("专栏", "workflow.article.editorial")}}),
        ("sohu", "搜狐号", {"content_forms": {"article": _article("文章", "workflow.article.feed")}}),
        ("penguin", "企鹅号", {"content_forms": {"article": _article("文章", "workflow.article.feed")}}),
        ("netease", "网易号", {"content_forms": {"article": _article("文章", "workflow.article.feed")}}),
        ("xiaohongshu", "小红书", {"content_forms": {"image_note": _form(
            "image", "workflow.image.cards", renderer="renderer.xhs.cards",
            rules=["rule.media.required", "rule.media.public_rights"],
            media={"cover": "required", "inline": "required"},
        )}}),
        ("x", "X（Twitter）", {"content_forms": {
            "single": _form("text", "workflow.social.short", renderer="renderer.generic.markdown", label="单推"),
            "thread": _form("text", "workflow.social.thread", renderer="renderer.x.thread", label="推串"),
        }}),
        ("weibo", "微博", {"content_forms": {"single": _form("text", "workflow.social.short", renderer="renderer.generic.markdown", label="帖子")}}),
        ("xueqiu", "雪球", {"content_forms": {
            "quant_research": _form("text", "workflow.finance.article", renderer="renderer.generic.markdown",
                                    rules=["rule.finance.as_of", "rule.finance.no_return_guarantee"], label="量化研究"),
            "market_recap": _form("text", "workflow.finance.article", renderer="renderer.generic.markdown",
                                  rules=["rule.finance.as_of", "rule.finance.no_return_guarantee"], label="行情复盘"),
        }}),
        ("juejin", "掘金", {"content_forms": {"tech_article": _form(
            "text", "workflow.tech.article", renderer="renderer.generic.markdown",
            rules=["rule.tech.code_provenance"],
        )}}),
        ("douyin", "抖音口播", {"content_forms": {"spoken_script": _form(
            "script", "workflow.script.spoken", renderer="renderer.generic.markdown",
        )}}),
    ]


def seed_v1_channel_profiles(db) -> int:
    """V1 PRD 2.0 的 14 平台 profile seeding（§9/7.1）。幂等：以 (channel, workflow 标记 version) 判重。

    注意：profile 是「配置存在」，不代表该平台 auto publish 已验证（PRD：不得伪装 verified）。
    """
    created = 0
    for channel, name, profile in v1_channel_profile_definitions():
        exists = (
            db.query(ChannelTemplateVersion)
            .filter(ChannelTemplateVersion.channel == channel, ChannelTemplateVersion.profile_json.is_not(None))
            .first()
        )
        if exists:
            continue
        db.add(
            ChannelTemplateVersion(
                channel=channel,
                name=f"{name} V1 Profile",
                version=100,  # profile 行为该渠道最高版本（发布时自动下线同渠道旧 published）
                structure=[],
                output_schema={"type": "object", "required": ["claim_fact_map"]},
                profile_schema_version=1,
                profile_json=profile,
                status="published",
            )
        )
        created += 1
    db.flush()
    return created


def install_missing_channel_profiles(db) -> list[str]:
    """Publish a V1 profile only where no published profile exists.

    A channel that already has a published profile, including the live WeChat
    official profile and the Xiaohongshu image profile, is not rewritten.
    A published legacy template without profile_json is archived by the new
    published version. This does not verify remote publishing.
    """
    from .routers.templates import _checksum, _demote_other_published, validate_profile_json

    created: list[str] = []
    for channel, name, profile in v1_channel_profile_definitions():
        published = (
            db.query(ChannelTemplateVersion)
            .filter(ChannelTemplateVersion.channel == channel, ChannelTemplateVersion.status == "published")
            .all()
        )
        if any(isinstance(row.profile_json, dict) and row.profile_json.get("content_forms") for row in published):
            continue
        validate_profile_json(profile, channel)
        max_version = (
            db.query(ChannelTemplateVersion.version)
            .filter(ChannelTemplateVersion.channel == channel)
            .order_by(ChannelTemplateVersion.version.desc())
            .limit(1)
            .scalar()
        ) or 0
        row = ChannelTemplateVersion(
            channel=channel,
            name=f"{name} V1 Profile",
            version=int(max_version) + 1,
            structure=[],
            output_schema={"type": "object", "required": ["claim_fact_map"]},
            profile_schema_version=1,
            profile_json=profile,
            status="published",
        )
        row.checksum = _checksum({
            "structure": row.structure,
            "output_schema": row.output_schema,
            "profile_schema_version": row.profile_schema_version,
            "profile_json": row.profile_json,
        })
        db.add(row)
        db.flush()
        _demote_other_published(db, ChannelTemplateVersion, {"channel": channel}, keep_id=row.id)
        created.append(channel)
    return created


def seed() -> None:
    init_db()
    with SessionLocal() as db:
        if not db.query(User).filter(User.email == "admin@studio.local").first():
            db.add(User(email="admin@studio.local", name="Admin", role="admin"))
        if not db.query(User).filter(User.email == "editor@studio.local").first():
            db.add(User(email="editor@studio.local", name="Editor", role="editor"))
        if not db.query(User).filter(User.email == "reviewer@studio.local").first():
            db.add(User(email="reviewer@studio.local", name="Reviewer", role="reviewer"))
        if not db.query(User).filter(User.email == "viewer@studio.local").first():
            db.add(User(email="viewer@studio.local", name="Viewer", role="viewer"))

        if not db.query(BrandVoiceVersion).filter(BrandVoiceVersion.name == "默认客观财经风").first():
            db.add(
                BrandVoiceVersion(
                    name="默认客观财经风",
                    version=1,
                    description="客观、数据驱动、不夸大",
                    tone_rules=["陈述事实优先于观点", "数字必须带时间与来源", "避免情绪化措辞"],
                    preferred_words=["数据显示", "截至", "区间", "结构上"],
                    forbidden_words=["保证收益", "稳赚", "必涨", "暴涨暴跌"],
                    examples=["截至 2026-09-15，该指数上涨 1.2%。"],
                    status="published",
                )
            )

        for channel, name, structure in (
            ("douyin", "抖音口播脚本模板", DOUYIN_STRUCTURE),
            ("xiaohongshu", "小红书图文模板", XHS_STRUCTURE),
            ("wechat", "公众号长文模板", WECHAT_STRUCTURE),
        ):
            exists = (
                db.query(ChannelTemplateVersion)
                .filter(ChannelTemplateVersion.channel == channel, ChannelTemplateVersion.version == 1)
                .first()
            )
            if not exists:
                db.add(
                    ChannelTemplateVersion(
                        channel=channel,
                        name=name,
                        version=1,
                        structure=structure,
                        length_guidance=length_guidance_for(channel),
                        forbidden_patterns=["确定性投资承诺", "夸张收益表述"],
                        output_schema={"type": "object", "required": ["claim_fact_map"]},
                        status="published",
                    )
                )

        sync_prompt_versions_from_files(db)
        seed_v1_channel_profiles(db)
        db.commit()
    print("Seed 完成：4 个内置用户、3 渠道 legacy 模板、默认 Brand Voice、V1 平台 Profiles（14 渠道）")


if __name__ == "__main__":
    seed()
