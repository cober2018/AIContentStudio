# progress

- 2026-10-24 提案写好；用户确认，并决定旧素材直接清空、只保留海底光缆。
- 实现（本地，未提交）：
  - `storage_locations`：`common_root()`（默认 `~/自媒体素材/通用素材库`）、`set_common`、`view()` 增加 common；`_save` 改为合并写入，换素材库位置不会丢通用库设置。
  - `project_folders`：通用库在 Mac 本地（placement 带 `root: common`）；`ensure_library_dirs` 建通用库子文件夹；`to_common` 按类型放子文件夹。
  - `routers/settings.py`：`PUT /settings/storage/common`；Web `StorageSettings.tsx` 增加「通用素材库位置」。
  - MCP：`file_as_common`（`video_chain.file_as_common`），`mcp_settings` 和视频 skill 同步。
- 清理：
  - 数据库备份 `apps/api/content_studio.before-cleanup-20261024.db`（另一份在会话临时目录）。
  - 40 个项目归档（11–33 属测试账号 goalprobe@studio.local，用该账号归档）；现在只有 41 海底光缆在用。
  - 76 条旧素材标为归档（审计 `material.retired_old`）；平台旧本地目录 258 个文件（253MB）移到 `~/.Trash/AIContentStudio-旧素材-20261024/`。
  - 海底光缆还在 Mac 上的 13 张图片移进 `海底光缆/图片/图片素材`、`图片/包装设计素材`；旧本地目录现已清空。
- 验证：设置页显示通用素材库 `/Users/mshengran/自媒体素材/通用素材库` 可用；浮窗 外部 0、通用 0、项目 49、本作品 33，均无成片。
- 全量测试：2807 通过；8 个失败中 7 个是之前已知的，1 个（system_library 轻量查询）由本次引起，已改为只读需要的列后通过。
