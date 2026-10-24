## Where files go

| What | Where |
| --- | --- |
| New materials (drag-in, upload, AI picture, AE render, adopted voice) | `<素材库>/AIContentStudio/视频|图片|音频/` |
| The user's own folders in the library | read only, never written |
| Previews, temporary and execution files, older materials | 本地工作位置 |

## Decisions

- The library location is the existing `material_source` record marked as home; new material files are written under its `AIContentStudio/` folder and then linked through the existing link flow, so availability and change checks are reused.
- Changing 素材库位置: the platform checks that linked files exist at the new place with the same size and fingerprint, shows how many match, and switches only after the user confirms. Files that do not match stay pointed at the old place and show as unavailable.
- Changing 本地工作位置: copy → verify each file by hash → switch the setting → keep the old folder. The API reads the setting at start and after a change; `AI_STUDIO_MEDIA_ROOT` still wins when set, and the page says so.
- No fallback write: if the library is not reachable, the action fails with 素材库未连接, so a material never ends up in two places.
- Floating window follows the AI assistant pattern (`FormAssistancePanel`, fixed bottom right). It sits to the left of the assistant button when both are shown.
- Drag uses HTML5 drag-and-drop. From Finder the browser sends file bytes, so files are uploaded to the API, which writes them into the library folder.
