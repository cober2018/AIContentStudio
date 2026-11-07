# landscape-cover-four-three

## 需求背景
横版作品多交一张 4:3 横封面（抖音用），16:9 横封面照旧。详见 proposal.md。

## 当前阶段
2026-11-07 已实现、已重启、已归档提交（本地 main，未推送）。

## 代码位置
apps/api/app/services（web_video_handoff、creative_executions、video_chain、video_documents、finished_video、creative_mcp），apps/api/app/routers/edit_agent.py，apps/web/src/product（VideoChainPanel、WorkCovers、FinishedVideoPreview）

## 成果文件
proposal.md、specs/、tasks.md、task_plan.md、progress.md、findings.md

## 下一步
「推送」后推到远端。作品 95 的文案由第三方模型或用户写好后会自动生成新待审版本。
