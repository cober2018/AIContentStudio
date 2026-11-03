# 进度

- 2026-11-04 写提案，等用户「确认」。
- 2026-11-04 用户「确认」，实施完成（未提交）：
  - 脚本：`make_templates.py`（VERSIONS 登记 v2、示例 4 张、`hostParallel` 4 槽、4 张时竖屏小图 224×156、标签按框宽缩放、`LENS` 让本模板合成 60 秒）、`landscape_layouts.py`、`make_previews.py`（img4）、`check_safe_area.py`（按 VERSIONS 找版本、`--until`）。
  - 搭建：AE 里搭竖屏、横屏两个工程，各 22 层；`templates/host-parallel/v2/manifest.json` 写好两个 SHA256（竖 a8ba8f3f…、横 040bc164…），checks 空。
  - 检查渲染（`output/_平台/模板审片/host-parallel-v2/`）：A（4 张、41 秒、4 组 beats）、B（3 张、7 秒、不填 beats）竖横各一，时长 41.000 / 7.000 秒；每组三帧（A：0.9 / 16.0 / 40.6 秒；B：0.9 / 4.2 / 6.5 秒）；和 v1 预览并排对比视频两段。A 抽 9 帧看过：四张按 beats 依次展开、收回，结尾淡出。aerender 出 41 秒约 28 秒，7 秒约 10 秒。
  - 安全区：A、B、外加 8 字长标签 × 竖横 6 次，全部零越界（A 查到 41 秒）。8 字标签在 4 张时自动缩小，看得清。
  - 预览：v2 `preview-9x16.mp4`、`preview-16x9.mp4` 已出，示例四张依次展开。
  - `SKILL.md` 模板表补 v2 一行。
  - v1 的工程、图片、预览、说明书 SHA256 前后一致；平台列表 v1 ready、v2 draft，两个画幅都有预览。
  - AE 里原来开着的作品 94 `rough-cut.aep`（未改动）在脚本关掉后已重新打开，仍是未改动状态。
- 后端全量测试：2441 通过、28 跳过、5 失败（之前就有的 5 个，与本次无关）。
- 2026-11-04 用户看过对比视频说可以：manifest 写入 4 条 checks（A、B × 竖横），平台状态 v2 ready。
