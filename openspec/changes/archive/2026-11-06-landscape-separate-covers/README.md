# landscape-separate-covers

## 需求背景
横版作品封面单独做，交 16:9 横封面和 3:4 竖封面两张，不再从成片开头截、不再和成片开头比。详见 proposal.md。

## 当前阶段
2026-11-06 已确认、已实现、已重启，已归档、已提交（未推送）。

## 代码位置
apps/api/app/services（video_chain、web_video_handoff、creative_executions、video_documents），apps/api/app/routers（edit_agent、product_skus），apps/web/src/product（VideoChainPanel、ProductPublishCopy、ProductionWorkspace）

## 成果文件
proposal.md、specs/、tasks.md、task_plan.md、progress.md、findings.md

## 下一步
新开的横版成片任务交两张封面后在审片页、交付页核对；用户说「推送」再推送。
