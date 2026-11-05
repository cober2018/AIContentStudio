# progress

- 2026-11-05 写好方案，待用户确认。
- 2026-11-05 用户澄清清理范围：硬盘文件全留，只清达芬奇项目；方案已改，待确认。
- 2026-11-05 用户确认（93、94 也只留最后一个）。实施：
  - `craft_skills.py`：aerender 外加按到达顺序的单线排队（`_one_render`）
  - `creative_executions.py`：领取剪辑任务时 `_edit_slot` 检查，忙就回 `video_edit_queue_busy`（带正在剪的作品、等待数）；`creative_mcp.domain_error` 让这条提示原样给到模型
  - 删掉 `project_folders` 的 `_remove_inside` / `_clean_work` / `after_execution` 和 5 处调用，硬盘工作文件不再被删
  - `video_chain.py` 剪辑说明、`video-production-handoff/SKILL.md`：工作文件全留、排队、每 20 分钟回报、达芬奇每作品留一个项目
- 验证（数据库副本）：4 个渲染按到达顺序 0,1,2,3 依次执行、同时最多 1 个；现有卡住的旧任务都超 30 分钟，不挡领取；把任务 25 设为 5 分钟前有动静，领任务 47 被拒，模型看到「达芬奇正在剪「敏贝贝薯乐酥」，另有 0 部在等」；改回 31 分钟前，能领，任务 25 状态仍是 in_progress。
- 全量测试：2441 通过、28 跳过，5 个失败与改动前相同（aco_schema_lifecycle、3 个 migrations、models_plugins）。
- 达芬奇项目清理清单已列，待用户确认后删除。
- 2026-11-05 用户确认后通过达芬奇脚本删除 91 个项目，失败 0；剩 8 个（每作品最后一个任务）。硬盘 .drp 未动。
- 2026-11-05 已重启 API 和后台，健康检查正常。
