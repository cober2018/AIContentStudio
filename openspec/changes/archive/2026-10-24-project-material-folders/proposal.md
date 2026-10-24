## Why

All materials sit loose in the library today: the user's own folders (e.g. `大海/`) and the platform folder `AIContentStudio/视频|图片|音频/xx/<hash>`. Nothing shows which project a file belongs to, and folders are not the standard layout the user archives by.

The user wants the drive organized by library, with each project's materials in its own folder using the standard layout.

## What Changes

- **Three libraries at the library root** (`/Volumes/T1000/自媒体素材/` by default):
  - **外部素材库** `外部素材库/`: where the user keeps adding new material over time. Files wait here until a project uses them.
  - **通用素材库** `通用素材库/`: good material kept for reuse. Files here are never moved; projects only reference them.
  - **项目素材库** `<项目名>/`: one folder per project with exactly the structure of `项目1`:
    `导演稿 / 视频/Aroll,Broll,其他素材 / 图片/图片素材,包装设计素材 / 音频/BGM,音效 / 导出/小样,成片`.
- **Moved when used:** when the user clicks 采用这版 → 准备剪辑, every material the director's draft uses that is not yet in a project or in 通用素材库 is **moved** (not copied) into this project's folder. Files already in another project stay there and are only referenced; no second copy.
- **The platform picks the subfolder**, the user does not:
  - 视频: talking-head or main footage → `Aroll`; cutaways and supporting footage → `Broll`; AE renders and generated clips → `其他素材`.
  - 图片: photos and AI pictures → `图片素材`; logos, cards, packaging graphics → `包装设计素材`.
  - 音频: BGM → `BGM`, sound effects → `音效`, voiceover → `音频/` itself (the layout has no voiceover folder; none is added).
  - 导演稿: the adopted director's draft as a readable file. 导出: the rough cut goes to `小样`, the accepted cut to `成片`.
- **New material made for a project** (voiceover, AI picture, AE render after 准备剪辑) goes straight into that project's folder.
- **Material pages show libraries:** the floating library window and the material page group by 外部素材库 / 通用素材库 / 项目素材库 → project → subfolder. A 「归入通用素材库」 action moves a file into 通用素材库.
- **海底光缆 is archived once:** everything it already uses moves into `/Volumes/T1000/自媒体素材/海底光缆/`.
- Nothing breaks after a move: storyboards, executions and the material page keep finding the file.
- Unchanged: `项目1/` (template) and `大海/` stay as they are, except files 海底光缆 uses, which move out. Edit proxies are still a later change.

## Impact

- API: a placement record per stored file (where it lives now), read by `material_external.open_key/path_of` and `LocalMaterialStorage._path`; folder scan treats placed files as already linked; move step in `edit_handoff` (准备剪辑) and in `voiceover` / execution adoption; project folder naming from the project title.
- Web: `MaterialLibraryFloat.tsx` and the material page group by library and project; 「归入通用素材库」 action.
- One-off archive of 海底光缆.
