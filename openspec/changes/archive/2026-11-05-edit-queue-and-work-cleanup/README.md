# edit-queue-and-work-cleanup

## 需求背景
用户要多个作品同时推进：AE 模板渲染、达芬奇剪辑各自一次一个、后来的排队；成片通过后自动清掉工作文件夹里的过程文件。详见 proposal.md。

## 当前阶段
2026-11-05 排队部分用户已确认；清理范围按用户澄清改为只清达芬奇项目、硬盘文件全留，用户已确认（93、94 也只留最后一个），代码已改、副本验证和测试通过；达芬奇项目已清理（删 91、留 8）。已重启生效。2026-11-05 已归档、已提交（未推送）。

## 代码位置
apps/api/app/services/{craft_skills,creative_executions,project_folders,video_chain}.py、.codex/skills/video-production-handoff/SKILL.md

## 成果文件
proposal.md、specs/、tasks.md、task_plan.md、progress.md、findings.md

## 下一步
无（推送等用户说「推送」）。
