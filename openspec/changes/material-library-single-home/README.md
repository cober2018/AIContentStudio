# material-library-single-home

**Stage:** applied locally (not committed). API restarted. User check pending.

**What:** the material library is the only home for new materials (`/Volumes/T1000/自媒体素材/AIContentStudio/视频|图片|音频`). Both locations are settings (设置 → 存储位置), current places are the defaults. A floating 素材库 window (bottom right) drags items onto storyboard rows and takes files dropped from Finder.

**Code:** API `app/services/storage_locations.py` (new), `material_storage.py` (library routing, `locate`), `asset_media.py` (saved local root), `materials.py` (素材库未连接), `material_autofill.py`, `creative_media_stream.py`, `creative_execution_files.py`, `routers/settings.py`, `main.py`. Web `MaterialLibraryFloat.tsx`, `StorageSettings.tsx` (new), `StoryboardTable.tsx`, `ProductSettingsPage.tsx`, `App.tsx`.

**Limits:** uploads keep the existing 30MB limit per file; Finder drops are recorded as 自己拍摄或制作 (public and model use allowed).

**Later (separate change):** edit proxies placed locally in the standard project folder (`导演稿`, `视频/Aroll|Broll|其他素材`, `图片/图片素材|包装设计素材`, `音频/BGM|音效`, `导出/小样|成片`; sample at `/Users/mshengran/Project/new_media/剪辑素材`).

**Next:** user tries a drag onto a row and a Finder drop.
