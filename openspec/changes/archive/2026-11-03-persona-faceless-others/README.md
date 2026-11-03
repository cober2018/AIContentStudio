# persona-faceless-others

## 需求背景
没有形象照的角色作品，导演稿标明的镜头可以出现不露脸的其他人物（如宝宝的手脚、身体局部）。用户 2026-11-03 选的做法。详见 proposal.md。

## 当前阶段
用户 2026-11-03「确认」；本地开发完成、本地验证通过（progress.md）。2026-11-03 已重启 API 和 worker；已归档，和 persona-shot-generation 一次提交。

## 依赖
在 persona-shot-generation（未提交）的代码上继续；两个变更最后一起归档、一次提交。

## 成果文件
| 文件 | 内容 |
| --- | --- |
| proposal.md | 改什么、不做什么、验收 |
| specs/product-video-production/spec.md | 规范增量 |
| tasks.md | 开发清单 |
| task_plan.md / progress.md / findings.md | 计划、进展、发现 |

## 代码位置
- apps/api/app/services/video_documents.py、product_video.py、shot_image.py、video_chain.py、creative_mcp.py
- apps/api/app/studio_skills/studio.video.prompt-direction/v1/SKILL.md
- apps/web/src/product/ShotWork.tsx、StoryboardGridDialog.tsx

## 下一步
无（已提交；推送等用户说「推送」）。
- 审计：review.md（2026-11-03 通过，代码复核和线上实测都过；新发现一条建议修：角色作品提示词总带「运镜强度：中」，和「镜头固定」矛盾）
