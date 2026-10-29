# 项目文件夹日期前缀 + 本地输出目录规范

- 阶段：已完成并归档（2026-10-29）
- 结果：项目素材文件夹统一 `YYYYMMDD_项目名称`；已有 `20261022_海底光缆`、`20261027_儿童麸质饼干` 改名并同步素材位置；`output/` 按项目 / `_平台` 归位，规则写进根 README。
- 代码：`apps/api/app/services/project_folders.py`（_dated_name、folder_name、date_existing_folders）；附带修复 `minimax_cli_provider.py` 启动注册与 `main.py`、`routers/settings.py` 的注册时机。
