# 进度

- 2026-10-28 写好方案，等用户确认。
- 2026-10-28 方案改为统一开关，等用户确认。
- 2026-10-28 用户确认后实施：
  - 后端：开关存在系统设置 `unit_platform_skills`（只记关闭的作品，没记录 = 开）；`GET/PUT /content-projects/{p}/units/{u}/platform-skills`（写需编辑权限，记 `unit.updated` 事件）；写作 skill = 平台内置 `kind=skill`、按作品形态筛、同名取最新版本、去掉 TTS；`get_craft_skill` 必须带 `project_id`、`unit_id`，craft-resolve / craft-ae 不校验，`studio.*` 按开关校验，关闭返回 `platform_skills_disabled`（已加入 MCP 可见错误码）；`get_video_brief`、`get_article_brief` 附 `platform_skills`。
  - 前端：`PlatformSkillsSwitch`（不用 / 可以用），视频制作页导演稿这一步、写稿页选第三方模型时显示。
  - 本地技能：`video-production-handoff`、`article-writing` 写明按 `platform_skills` 用 skill。
- 验证（项目 42 作品 83，经 MCP stdio 实测）：默认 brief 显示 on、可读 22 项；读 craft-resolve choose.md 和 studio.video.product-script@1 都成功。关闭后 brief 显示 off、只剩 craft-resolve / craft-ae；读写作 skill 返回 `platform_skills_disabled`，choose.md 照常。不带作品编号调用被拒。测完已把开关恢复为开。`test_aco_creative_mcp.py` 74 通过；相关后端测试 2607 通过、6 个失败为原有（迁移、模型插件）。ruff 无新增问题；`tsc --noEmit` 通过；开发服务器能编译两个面板。
- 未验证：浏览器里实点开关（Chrome DevTools 报已有浏览器实例占用配置目录，未去关闭用户的浏览器）。
