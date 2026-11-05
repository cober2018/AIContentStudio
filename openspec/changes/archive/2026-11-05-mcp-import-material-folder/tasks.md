## 1. 实现
- [x] 1.1 `project_folders.import_folder` 返回值加 `files`（relative_path、material_revision_id）
- [x] 1.2 `creative_mcp`：输入模型、工具表说明、`_VIDEO_TOOLS` 分发（作品归属 + `mutable_project` + `import_folder`）
- [x] 1.3 `mcp_settings`：「做视频」组、`SUMMARIES` 各一行

## 2. 验证（数据库副本）
- [x] 2.1 项目 50 / 作品 95 导入验收文件夹：10 个文件各有 id；已引入文件夹里显示 10 个
- [x] 2.2 再导一次：10 个都算已在项目里，id 相同，不重复登记
- [x] 2.3 已归档项目：被拒
- [x] 2.4 相关已有测试

## 3. 用户实测（重启后）
- [ ] 3.1 第三方模型重连后实际调用一次
