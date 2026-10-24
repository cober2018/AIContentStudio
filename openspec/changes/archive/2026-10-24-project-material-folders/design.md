## Folder layout

```
<素材库>/                       default /Volumes/T1000/自媒体素材
  外部素材库/                   user adds new files here
  通用素材库/                   kept for reuse, never moved by the platform
  <项目名>/                     created from 项目1's structure on first use
    导演稿/  视频/{Aroll,Broll,其他素材}/  图片/{图片素材,包装设计素材}/
    音频/{BGM,音效}/  导出/{小样,成片}/
  AIContentStudio/              existing platform files; unused ones stay here
```

- Project folder name = the part of the project title before the first ｜ (so 「海底光缆｜你发的消息…」 → 海底光缆), with `/ : \` and control characters removed. If another project already owns that name, ` (#<project id>)` is appended. The folder name is saved on the project, so renaming the project later does not move files.
- File name inside a project = the material title plus the original extension (platform files, which only have a hash name, get their title). A name clash in the same folder adds `-<first 6 chars of hash>`.

## Keeping files findable after a move

- Storage keys stay the same (`material/xx/<hash>.ext`, `external/<source>/<hash>/<relative>`), because execution packages and manifests hash them.
- A new **placement** record per key holds where the file is now (path relative to the library root), the project id and the library (`external` / `common` / `project`). Lookup order: placement → the old location.
- Both read paths use it: `LocalMaterialStorage._path` (platform files) and `material_external.open_verified/path_of` (linked files). The content hash check stays, so a wrong file is still refused.
- Folder scan treats a placed path as already linked, so a moved file never appears as a new one.

## Moving

- Same drive: `rename` (atomic). Different drive is not expected (all libraries share one root); if it happens: copy, sha256 check, then delete the source.
- Order: move the file, then save the placement; if saving fails, move it back. A file that cannot be moved (drive unplugged, permissions) is listed as 待归档 on the project and retried at the next 准备剪辑; the edit task is not blocked.
- Who triggers:
  - 准备剪辑: every material the adopted draft uses (picks in all shots, voiceover, BGM).
  - Voiceover / AE renders / adopted executions after that: written straight into the project folder.
  - Rough cut submitted → `导出/小样`; accepted → `导出/成片`.
  - 「归入通用素材库」 on the material page → `通用素材库/<视频|图片|音频>/`.
- Already in a project or in 通用素材库 → not moved, only referenced.

## The user's own copy wins

Older uploads are platform copies (`material/xx/<hash>`) of files that are also in the user's folders. When such a file moves, the platform first looks for a file with the same bytes outside projects and 通用素材库 (size first, then sha256). If found, the user's file moves (keeping its name) and the byte-identical platform copy is removed. Edit tasks keep their own input copies, so they are not affected.

## Choosing a subfolder

Decided by the platform from facts it already has, no extra model call:
- Video: the shot's `board.speaker` is set (someone on camera talking) → Aroll; AE render or generated video → 其他素材; otherwise Broll.
- Image: material role/tag logo, card, packaging, cover → 包装设计素材; otherwise 图片素材.
- Audio: voiceover → `音频/`; material role BGM → BGM; otherwise 音效.
- A file used by several shots goes by the first shot that uses it.

## 导演稿 file

At 准备剪辑, the adopted storyboard (9 columns) and narration are written as `导演稿/导演稿-v<revision>.md`. Older versions are kept.

## Material pages

- Library list API returns `library` (外部 / 通用 / 项目) and, for projects, project name and subfolder.
- Floating window: tabs 外部 / 通用 / 项目 (project → subfolder), plus the existing 本作品. Material page: same grouping.

## One-off archive of 海底光缆

Run the 准备剪辑 move step for its adopted master and both submitted executions (#6, #7): picks, voiceover, rough cuts → `海底光缆/…`. Reported file by file.
