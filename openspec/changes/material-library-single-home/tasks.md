## 1. Settings

- [x] 1.1 `storage` setting (library source + root) in `system_settings`; first registered folder becomes the default at API start. `GET /api/v1/settings/storage`, reachability shown.
- [x] 1.2 Local location move: copy, sha256 check per file, write `apps/api/storage_location.json`, keep old; effective after API restart. Blocked when `AI_STUDIO_MEDIA_ROOT` is set.
- [x] 1.3 Library location change: count linked files present with the same size, switch only with confirm.
- [x] 1.4 Settings page 存储位置 section.

## 2. Library as home

- [x] 2.1 `LocalMaterialStorage(library=True)`: new `material/xx/<hash>.ext` bytes go to `<素材库>/AIContentStudio/<视频|图片|音频|其他>/xx/`; existing local files keep being read locally; unreachable library → `素材库未连接` (409), nothing written, no folder created under /Volumes.
- [x] 2.2 All material writes (uploads, AI pictures, AE renders, adopted outputs) go through that path; execution readers walk from the library folder (`locate`); autofill gap reason shows 素材库未连接.

## 3. Floating window

- [x] 3.1 `MaterialLibraryFloat` (bottom right, movable, collapsible; tabs 素材库 / 本作品; search; thumbnails).
- [x] 3.2 Drop on a storyboard row's 素材 cell → shot pick (upload-target + attach, same as choosing in the slot).
- [x] 3.3 Finder multi-file drop → uploaded one by one into the library, with progress and per-file errors.

## 4. Verify

- [x] 4.1 Temp folders: write lands in `AIContentStudio/图片/..`, reads back, local untouched; unplugged → `material_library_unavailable`, `/Volumes/NOPE` not created; local move copies, verifies, writes location file, keeps old. Related API tests 117 passed. Web build passes. Settings page and float checked in the browser.
- [ ] 4.2 Live drag onto a U80 row and Finder drop were not run, to avoid writing test data into the user's work and drive.

## 5. Docs

- [x] 5.1 README, task_plan, progress, findings.
