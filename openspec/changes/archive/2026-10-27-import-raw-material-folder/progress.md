# 进度

- 2026-10-27 写好方案，用户确认（归档时搬走，不复制）。
- 2026-10-28 用户补充：文件名不用改，只搬。
- 2026-10-28 实施完成：
  - 后端 `project_folders.import_folder / archive_raw / raw_pending`；接口 `POST /content-projects/{id}/materials/folder-import`、`GET|POST .../materials/folder-archive`；`video_chain.decide` 成片通过后调用归档。
  - 前端 `ProjectAssetsTab.tsx` 加「引入原始素材文件夹」和「重新归档」，来源显示「原始素材文件夹」。
- 验证（用盘上的临时文件夹，测完已删，测试项目 43、44 已归档，测试素材已归档）：
  - 引入：mp4/png/wav 共 3 个新增，docx 计为不支持；再引入同一文件夹 → 新增 0、已有 3；盘外路径、项目文件夹都被拒绝。
  - 归档：3 个文件分别搬到 `视频/其他素材`、`音频/音效`、`图片/图片素材`，原文件夹只剩 docx；平台存储仍能读出这 3 个文件；再归档一次无动作。
  - 页面：资料页填路径点「引入文件夹」显示「新增 1 个」。
  - `tsc --noEmit` 通过；ruff 只有一条既有的未用导入警告（`after_execution` 里的 `ContentUnit`，改动前就有）。
- 未验证：硬盘拔掉时的待归档和重新归档（无法在本机模拟拔盘）；完整走一次导演稿 → 成片通过的真实链路。
- 2026-10-28 用户实测发现：手机拍的 .MP4 实际是 QuickTime 格式，引入时被当成「读不了」跳过 6 个。已修 `material_external._media_type`：视频按文件内容定类型，.mp4 里装 QuickTime 也接受。修后重新引入用户的「益生元无麸饼干」文件夹：新增 6、已有 1、跳过 0。
