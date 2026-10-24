## Why

Materials live in two places today: the user's drive folder (`/Volumes/T1000/自媒体素材`, linked read-only) and the platform media folder inside the code directory (`apps/api/app/media`), where uploads, AI pictures and AE renders are copied. Neither location can be seen or changed in the product. Adding material means clicking upload and picking files one by one.

The user's direction: the material library is the only home for materials. Editing later works on local proxies (separate change). The library opens as a small floating window, like the AI assistant, and items are dragged where they are needed.

## What Changes

- **Two storage settings** on the settings page, section 存储位置, each showing its path and whether it is reachable:
  - **素材库位置**: default `/Volumes/T1000/自媒体素材` (the current linked folder). Can be changed to another folder or drive. Shows 未连接 when the drive is not plugged in.
  - **本地工作位置**: default the current media folder. Holds previews, temporary and execution files, and older materials stored before this change. Changing it copies the files, checks each one, then switches; the old folder is not deleted.
- **The library is the only home for new materials.** Every new material (drag-in, upload, AI picture, AE render, adopted voice) is written into a platform folder inside the library, `<素材库>/AIContentStudio/{视频,图片,音频}/`, and linked like other library files. The user's own folders are never written to.
- **Library not connected:** adding material is blocked with 素材库未连接; AI 补齐素材 marks affected rows as gaps with that reason. Nothing is written elsewhere as a fallback.
- **Floating library window:** a button at the bottom right opens a small, movable, collapsible window with tabs 素材库 / 本作品 and a search box. It lists library files (thumbnails, type, length).
- **Drag into the table:** dragging an item onto a row's 素材 cell in the storyboard table uses it for that shot (same binding as picking it today).
- **Drag in from Finder:** dropping one or many files onto the window adds them to the library in one go.
- Existing materials keep working from where they are; this change does not move them.
- Not in this change: edit proxies and the standard project folder (`导演稿 / 视频 / 图片 / 音频 / 导出`), which come in a later change.

## Impact

- API: storage settings stored in `system_settings` (new key `storage`), read by `material_storage.provider()` and `asset_media`; new write path into the library folder; settings endpoints `GET/PUT /api/v1/settings/storage` and a move job for the local location; batch upload endpoint for drag-in.
- Web: `ProductSettingsPage` (存储位置 section), new floating library window next to `FormAssistancePanel`, drop target on `StoryboardTable` 素材 cells.
- No database migration expected; `material_source` id 1 becomes the library home.
