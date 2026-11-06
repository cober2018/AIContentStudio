# persona-intro-outro-clips

## 需求背景
进门 / 收尾片段从品牌搬到角色上配置，品牌那块删掉。详见 proposal.md。

## 当前阶段
2026-11-06 已确认、已实现、已重启、已上线（品牌 6 去掉片段，角色 6 设 618/619），已归档、已提交（未推送）。

## 代码位置
apps/api/app/services（content_identity、video_chain、web_video_handoff、creative_packages、creative_executions、delivery_checks），apps/api/app/routers（content_identities、edit_agent），apps/web/src/product（BrandClips→PersonaClips、BrandProfile、IdentityWorkspace、IdentityProfileView、VideoChainPanel）

## 成果文件
proposal.md、specs/、tasks.md、task_plan.md、progress.md、findings.md

## 下一步
用户说「推送」再推送。
