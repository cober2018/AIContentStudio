# quant-daily-review-column

## 需求背景
量化研究专家每天发一篇复盘文章，数据来自数据中台公开看板服务 public-*（合规过滤后）。详见 proposal.md。

## 当前阶段
2026-11-16 变更四完成：每日复盘改成 MCP 工具 prepare_daily_review，由第三方模型写稿，平台不再自动调度；11-09～11-13 五篇已按以图为主重生成，等用户看稿。

## 代码位置
apps/api/app/services/quant_daily_review.py（取数、出图、prepare）；creative_mcp.py、mcp_settings.py（MCP 工具）；article_chain.py（「每日复盘」标签、存稿查建议用语）；apps/web/src/product/ArticleChainPanel.tsx、DataGuardPanel.tsx

## 成果文件
proposal.md、specs/content-opportunities/spec.md、tasks.md、task_plan.md、findings.md、progress.md

## 下一步
用户看五篇新稿；在 Antigravity 里接上 aicontentstudio-creative MCP，用 Gemini 说「写今天的复盘」试一篇；观察期后通知数据中台吊销 dodk_491192e；验收后归档、提交。
