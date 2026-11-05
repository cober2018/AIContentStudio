# material-public-use-by-owner

## 需求背景
作品 95 开成片被 `video_asset_kind_or_rights_invalid` 拒：用户自己的 Logo 309 登记时没勾公开，经 AE 渲染 546 传到小样 581，采纳小样时连「给模型用」也一起关了。详见 proposal.md。

## 当前阶段
2026-11-05 用户确认，已实现、库副本验证和测试通过，已重启生效；2026-11-05 已归档、已提交（未推送）。

## 代码位置
apps/api/app/services（materials、video_chain、content_masters、creative_mcp），apps/api/app/routers/materials.py，apps/web/src/product/MaterialDetailDrawer.tsx

## 成果文件
proposal.md、specs/、tasks.md、task_plan.md、progress.md、findings.md

## 下一步
用户在素材详情里把 309 改成可公开（直达 /materials?material=302），第三方模型重渲第 40 镜关注卡、重出小样后开成片；用户说「推送」再推送。
