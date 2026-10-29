# import-raw-material-folder

**阶段：** 已本地实施并验证，2026-10-28 归档；未提交 Git。

**做什么：** 项目「资料」页可以一次引入整个原始素材文件夹（原地登记）；成片通过后把这批素材搬进项目标准目录。

**文件：** `proposal.md`、`design.md`、`specs/project-material-folders/spec.md`、`tasks.md`、`task_plan.md`、`progress.md`、`findings.md`。

**代码位置：** `apps/api/app/services/project_folders.py`（引入、归档）、`app/routers/project_assets.py`（接口）、`app/services/video_chain.py`（成片通过后归档）；`apps/web/src/product/project/ProjectAssetsTab.tsx`、`types.ts`。

**下一步：** 用户实际用一次（引入 → 做片 → 成片通过），看归档结果。
