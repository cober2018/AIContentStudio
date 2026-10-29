# AE 模板横屏版 + 模板库预览 + 默认由大模型选模板

- 阶段：已完成并归档（2026-10-29）
- 结果：46 个模板各有 16:9 版本（同名同字段、横屏单独排版、16:9 安全区零越界），渲染按画幅选工程、缺画幅明确报错；每个模板竖横各一段库内预览，说明书带类别；设置页新增只读「AE 模板库」（类别分组、竖横切换播放、用法与字段）；「默认大模型自选、用户微调点名必用、画幅跟片子走、beats 按配音逐句时间填」写进 craft-ae SKILL.md 与 MCP 工具说明。
- 代码：`apps/api/craft_skills/craft-ae/scripts/`（make_templates.py --aspect、landscape_layouts.py、make_previews.py、check_safe_area.py --aspect）、`templates/*/v1/manifest.json`；`apps/api/app/services/craft_skills.py`、`creative_mcp.py`、`app/routers/settings.py`；`apps/web/src/product/AeTemplateLibrary.tsx`、`ProductSettingsPage.tsx`。工程与预览在本机 `~/AIContentStudio/ae-templates/`，示例图在 `_samples/`。
- 审片页（本地，未进版本库）：`output/template-preview/index.html`、`output/template-preview-landscape/index.html`。
- 测试产物：项目 41 的素材 182、183（模板渲染验证），可删。
- 下一步：商品工作台的模板（另起需求）。
