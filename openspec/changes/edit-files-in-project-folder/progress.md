# 进度

## 2026-10-29 本地实施（未提交）
- 代码：`project_folders`（加 `工作/`、`work_dir` / `export_dir` / `proxy_dir`、清理；删 `export_copy` / `sample_copy` / `sample_name`）、`creative_executions`（`in_project` 分支：开任务建 work_dir、准备素材给原路径、交付收绝对路径原地校验、通过时原地登记）、`creative_media_stream`（`project_file`、`make_proxy`、`budget(private=)`）、`video_chain`（RULES、`cut_location`、`prepare_edit` 返回 work_dir / export_dir）、`web_video_handoff`（剪辑清单素材用 `path`、交接说明）、`creative_mcp`（工具说明、出错日志）、`storage_locations` + `routers/settings`（代理开关）、`routers/creative_orchestration`（播放 / 读取走记录的路径）、前端 `StorageSettings.tsx`（代理开关）、`.codex/skills/video-production-handoff/SKILL.md`（路径约定）。
- 测试：`tests/test_aco_creative_executions.py` 加 2 个用例（目录外 / 快捷方式 / 跳目录 / 交付后被改）。
- 验证：后端 `pytest -q` 2451 通过、5 个已知失败、28 跳过；前端 `tsc` 通过、`node --test` 37/37、`npm run build` 成功。API 重启后 83、84 仍是「小样待你看」，播放接口 200，字节指纹与 `导出/小样` 里的文件一致。
- 旧数据：`/Users/mshengran/.claude/jobs/1765d66a/tmp/old_executions.py`（list / repoint / revert）。已执行 repoint：任务 11、14 共 16 条输出改指项目文件夹（小样两条本来就在 `导出/小样`，指纹核对一致；其余 14 条复制到各自 `工作/<作品>-<作品号>/任务N/` 并核对指纹）；旧键存于 `repoint-revert.json`；`.creative-executions` 未删任何文件。
- 未做：第三方模型实跑一次新流程、删除旧 7.6 GB（等用户确认）、`/opsx:archive`。

## 2026-10-29 清理旧任务文件（用户确认）
- 删前核对：没有素材记录、项目文件夹里的快捷方式指向 `.creative-executions`；任务 11、14 的输出都已改指项目文件夹。
- 已删 `apps/api/app/media/.creative-executions`（7.6 GB）。
- 删后核对：作品 83、84 仍是「小样待你看」，作品 80「已定稿」；三条片子的位置都指向项目文件夹，接口 200。
- 成片通过时的清理改为：已登记的文件一律保留，只删没登记的。后端 `5 failed, 2451 passed`（5 个已知失败）。
