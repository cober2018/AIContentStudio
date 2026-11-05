# progress

- 2026-11-05 写好方案，待用户确认。
- 2026-11-05 用户确认，实施：
  - `import_folder` 返回 `files`，新登记和已在项目里的都列
  - `creative_mcp` 新增 `MaterialFolderInput`、工具说明，`_video` 分发（`owned_unit` → `mutable_project` → `import_folder`）
  - `mcp_settings` 的「做视频」组和 `SUMMARIES` 各加一行
- 副本验证（项目 50 / 作品 95，验收文件夹）：
  - 第一次：added 10，返回 10 个 id（506 起）；已引入文件夹显示该文件夹 10 个文件
  - 第二次：existing 10，id 相同，项目引用数不再增加
  - 项目设为已归档：409「已归档项目仅可查看历史」，MCP 显示 creative_domain_conflict
- `test_aco_creative_mcp.py` 的工具白名单加上新工具名。全量测试 2441 通过，5 个失败与改动前相同。
- 2026-11-05 已重启 API 和后台，健康检查正常。
