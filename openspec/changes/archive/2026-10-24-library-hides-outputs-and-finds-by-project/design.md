## 什么算成果

满足任一条即为成果，素材视图不显示：来自剪辑任务且产出角色为 `rough_cut / final / subtitles / resolve_project / ae_project / edit_manifest`；或存放位置在某项目 `导出/` 下。判断集中在 `project_folders.is_output`。

## 快捷方式

- 用符号链接（访达里显示为带箭头的替身，双击打开原文件；达芬奇 / AE 导入时按原文件处理）。
- 何时建：`move_into` 返回 `referenced`（文件在别的项目或通用素材库）时，在本项目对应子文件夹建链接，记到该版本的 `metadata_json.links[project_id] = 相对路径`。重名按现有 `_free_name` 规则加序号。
- 素材库扫描、去重遇到符号链接一律跳过，避免把快捷方式当成新文件。
- 原文件之后被移动（如归入通用素材库）时，同步改链接指向。

## 「项目」页

`tree()` 每条增加 `linked_projects`；浮窗选项目时显示 `project_id` 等于它或 `linked_projects` 含它的素材，后者标来源。
