# progress

- 2026-10-24 提案写好，用户确认。
- 实现（本地，未提交）：
  - `project_folders.is_output` / `output_material_ids`：剪辑成果（rough_cut / final / subtitles / resolve_project / ae_project / edit_manifest）和 `导出/` 下的文件不算素材。
  - `tree()` 排除成果、每条带 `used_by`；`system_library` 列表排除成果；「存放位置 → 项目」包含该项目复用的素材。
  - `move_into`：素材在别的项目文件夹时，在本项目对应子文件夹放快捷方式（符号链接），记录 `links` / `used_by`；通用素材只记 `used_by`；原文件移动时快捷方式跟着改指向（`_relink`）。
  - `shared-assets?exclude_outputs=true`：只给素材库浮窗「本作品」用；绑定主稿仍用完整列表。
  - Web `MaterialLibraryFloat.tsx`：「项目」页显示复用的素材并标「来自 xx / 通用」。
- 验证：
  - 数据库副本 + 临时目录：项目 39 复用 41 的视频 → `ESP32/视频/Broll/船.mp4` 快捷方式指向原文件；归入通用后快捷方式改指向 Mac 本地通用库，原项目再用时只记录。
  - 真实数据：素材库树、素材库列表、浮窗四个页都不再出现成片；海底光缆项目页 49 条。
- 全量测试：2807 通过；8 个失败中 7 个是之前已知的，1 个（system_library 轻量查询）由本次引起，已改为只读需要的列后通过。
