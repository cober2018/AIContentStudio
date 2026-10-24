## 1. Placement

- [x] 1.1 Placement record per storage key (relative path, library, project id); project folder name saved on the project.
- [x] 1.2 Reads use the placement first: `LocalMaterialStorage._path`, `material_external.open_verified/path_of`; content check unchanged.
- [x] 1.3 Folder scan treats placed paths as linked.

## 2. Moving

- [x] 2.1 Create the project folder from the standard structure; name rules and clash handling.
- [x] 2.2 Subfolder rules (Aroll / Broll / 其他素材, 图片素材 / 包装设计素材, BGM / 音效 / 音频).
- [x] 2.3 Move step: rename, save placement, roll back on failure; 待归档 list and retry.
- [x] 2.4 Hook into 准备剪辑 (`edit_handoff`), voiceover, execution adoption (小样 / 成片, AE renders); 导演稿 markdown.
- [x] 2.5 「归入通用素材库」 endpoint.

## 3. Pages

- [x] 3.1 Library list returns library / project / subfolder.
- [x] 3.2 Floating window and material page group by library and project; 归入通用素材库 button.

## 4. 海底光缆 and verify

- [x] 4.1 Archive 海底光缆 (picks, voiceover, executions #6 #7) and report each file.
- [x] 4.2 Check previews and execution #7 files still open; run related tests; update docs.
