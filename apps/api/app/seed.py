"""种子数据：管理员、渠道模板、Brand Voice。`make seed` 或 python -m app.seed。"""

from .db import SessionLocal, init_db
from .models import BrandVoiceVersion, ChannelTemplateVersion, User
from .routers.templates import sync_prompt_versions_from_files

DOUYIN_STRUCTURE = ["Hook 3-8s", "背景", "核心观点 1", "证据", "核心观点 2", "风险/反面信息", "总结", "CTA"]
XHS_STRUCTURE = ["标题候选", "封面文案", "正文", "小标题", "卡片文案", "图片 Prompt", "Tags"]
WECHAT_STRUCTURE = ["标题", "摘要", "导语", "主体章节", "风险提示", "结尾", "配图建议", "数据来源列表"]


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
                        length_guidance=(
                            {"seconds": "45-90", "chars": "300-600"} if channel == "douyin"
                            else {"body_chars": "300-800"} if channel == "xiaohongshu"
                            else {"body_chars": "1500-3000"}
                        ),
                        forbidden_patterns=["确定性投资承诺", "夸张收益表述"],
                        output_schema={"type": "object", "required": ["claim_fact_map"]},
                        status="published",
                    )
                )

        sync_prompt_versions_from_files(db)
        db.commit()
    print("Seed 完成：4 个内置用户（admin/editor/reviewer/viewer @studio.local）、3 渠道模板、默认 Brand Voice")


if __name__ == "__main__":
    seed()
