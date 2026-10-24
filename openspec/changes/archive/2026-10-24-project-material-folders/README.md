# project-material-folders

**Stage:** applied locally and archived 2026-10-24 (not committed). User checked the floating window: OK.

**What:** the library root (`/Volumes/T1000/自媒体素材/`) holds 外部素材库 (new files), 通用素材库 (kept for reuse, never moved) and one folder per project using the layout of `项目1`. On 准备剪辑, the files the adopted draft uses move into the project folder, and the 导演稿 is written there. A returned rough cut is copied to 导出/小样; when the cut is accepted, its files move in (cut → 导出/成片). Files already in another project are referenced, not copied. The floating library (外部 / 通用 / 项目 / 本作品) and the material page (存放位置 filter) group by library; 「归入通用素材库」 is on hover in the floating window and in the material drawer.

**Code:** API `app/services/project_folders.py` (new), `material_storage.py` (`_path` reads placement), `material_external.py` (`relative_of`, scan), `storage_locations.py` (`library_source_id`), `edit_handoff.py` (`_archive`, `archive_pending`), `voiceover.py`, `creative_mcp.py` + `routers/creative_orchestration.py` (`after_execution`), `routers/materials.py` (`GET /material-folders`, `POST /materials/{id}/to-common`), `routers/system_library.py` + `services/system_library.py` (`place` filter), `main.py` (creates 外部素材库 / 通用素材库). Web `MaterialLibraryFloat.tsx`, `MaterialLibraryPage.tsx`, `MaterialDetailDrawer.tsx`.

**Data:** where a file sits now = `material_revision.metadata_json.placement`; project folder names = `system_settings.project_folders`; files that could not move = `system_settings.project_folders_pending`. No migration.

**Next:** user checks `/Volumes/T1000/自媒体素材/海底光缆/` and the floating window. Archive the change when the user asks.
