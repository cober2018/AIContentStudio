# start-work-from-project

**阶段：** 已本地实施并验证，2026-10-28 归档；未提交 Git。

**做什么：** 在内容项目里直接开始角色内容或商品视频，不用跳到工作台重新建项目。

**文件：** `proposal.md`、`design.md`、`specs/project-work-entry/spec.md`、`tasks.md`、`task_plan.md`、`progress.md`、`findings.md`。

**代码位置：** `apps/api/app/routers/product_skus.py`（`WorkIn.project_id`）、`app/services/product_creation.py`（`save_launch(project=...)`）；`apps/web/src/product/PersistentProjectPage.tsx`（引导卡片）、`project/ProjectMatrixTab.tsx`（加商品视频）、`ProductWorkbench.tsx`（`?project=` 带入项目）。

**下一步：** 用户在项目 42 点「商品视频」选商品，接着交给第三方模型做视频。
