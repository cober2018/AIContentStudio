## 位置

- `system_settings["storage"]` 增加 `common_root`，默认 `~/自媒体素材/通用素材库`（首次启动创建）。
- `project_folders.location()`：路径在 `common_root` 下 → `library = common`；硬盘上 `<库>/通用素材库/` 仍识别为 common（兼容，目前为空）。
- 读写不受硬盘连接状态影响：`_writable` / 「素材库未连接」只针对硬盘上的文件。

## 归入通用

- `to_common` / `move_into(project_id=None)` 目标改为 `common_root/<子文件夹>`。从硬盘到 Mac 属跨盘移动，沿用现有「复制 + 校验 + 删原文件」流程。
- 已被其他项目以快捷方式引用的文件移走后，同步改快捷方式指向。

## 旧素材清空（替代原「归位」方案）

1. 备份数据库（`apps/api/content_studio.before-cleanup-20261024.db`）。
2. 除 41（海底光缆）外的项目调用平台「删除项目」（归档）。
3. 不被海底光缆使用、也不在海底光缆文件夹的素材：`Material.status = archived`，写审计 `material.retired_old`。
4. 平台旧本地目录 `media/material/` 里，不属于任何在用素材的文件移到 `~/.Trash/AIContentStudio-旧素材-20261024/`。
5. 海底光缆还在 Mac 上的素材用 `move_into` 移进硬盘项目文件夹（逐个核对哈希）。
