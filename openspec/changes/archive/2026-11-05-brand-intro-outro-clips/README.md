# brand-intro-outro-clips

## 需求背景
品牌上存进门 / 收尾片段（Logo 动画视频），成片任务自动带上，平台检查。详见 proposal.md。

## 当前阶段
2026-11-05 用户确认，已实现、库副本验证和测试通过，2026-11-06 已重启生效；2026-11-06 已归档、已提交（未推送）。

## 代码位置
apps/api/app/services（content_identity、video_chain、web_video_handoff、creative_packages、creative_executions、delivery_checks），apps/api/app/routers/edit_agent.py，apps/web/src/product（BrandProfile、VideoChainPanel）

## 成果文件
proposal.md、specs/、tasks.md、task_plan.md、progress.md、findings.md

## 下一步
用户在品牌页设收尾片段（视频先改成可公开）；用户说「推送」再推送。
