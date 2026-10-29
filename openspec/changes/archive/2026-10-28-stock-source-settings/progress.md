# 进度

- 2026-10-28 写好方案，等用户确认。
- 2026-10-28 用户确认，完成：
  - 后端：`open_media.py` 各来源读设置（页面保存的 Key 优先，没保存过用 runtime.env），`enabled()` / `configured()`；`visible()` 和 `material_matching._open_candidates` 跳过关闭的来源；新增 `CoverrProvider`（视频，`Authorization: Bearer`，用 `mp4_download`）；`settings_view` / `save_settings` / `test_source`。路由 `GET/PUT /api/v1/settings/open-media`、`POST /api/v1/settings/open-media/{source}/test`（管理员）。
  - 前端：设置新增「素材数据源」分区 `StockSourceSettings.tsx`。
  - 验证：7 个来源列出；Pixabay 显示 env 来的掩码、测试成功（3 条）；Coverr 未配置时提示「未配置 Key」，填假 Key 测试返回「Key 无效或没有权限」，清除后恢复未配置；关掉 Pixabay 后素材搜索来源列表里没有它，打开后恢复；接口响应里没有明文 Key。后端相关测试 72 通过；前端 tsc、37 个测试、build 通过；无头浏览器截图页面正常。
