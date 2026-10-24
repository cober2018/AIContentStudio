# local-common-library

**Stage:** applied locally and archived 2026-10-24 (not committed). API restarted.

**What:** 通用素材库放 Mac 本地；专有素材跟项目放硬盘；旧素材按用户决定清空（只留海底光缆）。

**Related:** `library-hides-outputs-and-finds-by-project`。

**Code:** API `services/storage_locations.py`, `services/project_folders.py`, `services/video_chain.py`, `services/creative_mcp.py`, `services/mcp_settings.py`, `routers/settings.py`; Web `product/StorageSettings.tsx`; skill `.codex/skills/video-production-handoff/SKILL.md`.

**Undo:** 数据库备份 `apps/api/content_studio.before-cleanup-20261024.db`；旧文件在 `~/.Trash/AIContentStudio-旧素材-20261024/`。

**Next:** none.
