# fact-boundary-topic-templates

## 需求背景
事实边界保留，平台内置按题材分的 7 个模板；模型按模板找来源起草，平台打开来源核对，用户确认冻结。详见 proposal.md、design.md。

## 当前阶段
全自动版本 2026-11-03「确认」并实现，本地验证通过（progress.md）；2026-11-03 已重启 api 和 worker，健康检查 200，新接口返回当前事实边界字段，旧草稿接口已不存在（404）。#1–#10 测试事实包已于「上线」删除（有备份）。2026-11-03 已归档、已提交（未推送）。

## 代码位置
apps/api/app/fact_templates/、services/creative_mcp.py、routers/project_evidence.py、services/video_chain.py、services/article_chain.py；apps/web 选题步骤和来源与事实边界页

## 下一步
无（推送等用户说「推送」）。
