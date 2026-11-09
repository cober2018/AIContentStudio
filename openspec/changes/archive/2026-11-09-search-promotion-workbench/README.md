# search-promotion-workbench

## 需求背景
做推广是为了让用户搜索和问 AI 时看到并引用我们的内容。单开「搜索推广工作台」，推广对象覆盖品牌、消费品、to B 服务、工业产品；写作、检查、图文、剪辑特效、交付全部复用。详见 proposal.md。

## 当前阶段
2026-11-09 已实现并提交、归档；正式库在 searchpromo0003（备份 backups/content_studio_before_searchpromo3_20261109214435.db），已重启上线。

## 代码位置
apps/api/app/services/search_promotion.py、search_runner.py、app/routers/search_promotion.py、alembic/versions/searchpromo0001~0003、studio_skills/studio.search.genre.*，及生产链少量判断；apps/web/src/product/SearchPromotionWorkbench.tsx

## 成果文件
proposal.md、specs/、tasks.md、task_plan.md、progress.md、findings.md

## 待完成 / TODO
- 真实模型跑一遍（平台模型、第三方模型各一次）
- 图文、视频衍生实测；视频成片通过后自动出复制包
- 另开提案：简化角色内容、商品视频工作台的平台模型路径
