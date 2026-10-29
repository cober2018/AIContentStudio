# stage-switches-for-third-party-model

**阶段：** 已本地实施并验证（页面开关未能在浏览器里实点，见 progress），2026-10-28 归档；未提交 Git。

**做什么：** 每条作品一个统一开关，由人控制第三方模型能否读平台写作类 skill；剪辑、特效 skill（craft-resolve、craft-ae）一直可读。

**代码位置：** `apps/api/app/services/craft_skills.py`（开关存取、可读清单、`read_skill`）、`creative_mcp.py`（`get_craft_skill` 带作品编号、`platform_skills_disabled`）、`video_chain.py` / `article_chain.py`（brief 附 `platform_skills`）、`app/routers/edit_agent.py`（`GET/PUT .../platform-skills`）；`apps/web/src/product/ArticleChainPanel.tsx`（`PlatformSkillsSwitch`）、`VideoChainPanel.tsx`；`.codex/skills/video-production-handoff`、`article-writing`。

**下一步：** 用户在制作页实际点一次开关；第三方模型做视频时看 brief 里的 `platform_skills`。
