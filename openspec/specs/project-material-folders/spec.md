# project-material-folders Specification

## Purpose
TBD - created by archiving change project-material-folders. Update Purpose after archive.
## Requirements
### Requirement: Three libraries

The library root SHALL hold 外部素材库, 通用素材库 and one folder per project. Each project folder SHALL use exactly the structure of `项目1`.

#### Scenario: First use creates the project folder
- **WHEN** a project's materials are moved for the first time
- **THEN** `<素材库>/<项目名>/` exists with 导演稿, 视频/Aroll|Broll|其他素材, 图片/图片素材|包装设计素材, 音频/BGM|音效, 导出/小样|成片

### Requirement: Materials move into the project when the draft is adopted

On 准备剪辑, every material the adopted draft uses that is not in a project folder or 通用素材库 SHALL be moved into this project's folder, into the subfolder the platform picks. Files in another project or in 通用素材库 SHALL NOT be moved or copied.

#### Scenario: External footage
- **WHEN** a shot uses `外部素材库/海缆船.mp4` and the user clicks 准备剪辑
- **THEN** the file is now at `<项目名>/视频/Broll/海缆船.mp4` and no longer in 外部素材库

#### Scenario: Used by a second project
- **WHEN** a file already in project A is used by project B
- **THEN** it stays in project A's folder and project B references it

#### Scenario: Drive unplugged
- **WHEN** a file cannot be moved
- **THEN** it is listed as 待归档 and retried at the next 准备剪辑; the edit task is still prepared

### Requirement: Moved files stay findable

After a move, the storyboard, edit tasks, previews and the material page SHALL keep using the file, with the same content check as before. A moved file SHALL NOT be found again as a new file by the folder scan.

#### Scenario: Preview after move
- **WHEN** the user opens a shot whose material was moved
- **THEN** the preview plays from the new location

### Requirement: Project outputs are archived

The adopted director's draft SHALL be written to 导演稿, a submitted rough cut to 导出/小样, an accepted cut to 导出/成片, and project voiceover, AI pictures and AE renders straight into the project folder.

#### Scenario: Rough cut
- **WHEN** an edit task returns its rough cut
- **THEN** the file is in `<项目名>/导出/小样/`

### Requirement: Material pages group by library

The floating library window and the material page SHALL group materials by 外部素材库, 通用素材库 and project → subfolder, and SHALL offer 归入通用素材库.

#### Scenario: Browse a project
- **WHEN** the user opens 项目 → 海底光缆 → 视频/Broll
- **THEN** they see that project's Broll files

### Requirement: Import a raw material folder into a project

The project 资料 page SHALL let the user import a folder on the library drive by path; folders off the drive, project folders and 通用素材库 SHALL be refused. Every supported video, image and audio file in it and its subfolders SHALL be linked in place as this project's material, marked as coming from that folder. Unsupported files SHALL be skipped and counted.

#### Scenario: Import a folder
- **WHEN** the user imports `/Volumes/T1000/原始素材/手机评测/` with 30 mp4, 20 jpg and 3 docx files
- **THEN** 50 materials are attached to the project, the files stay where they are, and the result says 3 files were skipped

#### Scenario: Import the same folder again
- **WHEN** the user imports the same folder after adding 5 new photos
- **THEN** only the 5 new photos are added

### Requirement: Raw folder material is filed when the final cut is approved

When the user approves the 成片, every material imported from a raw folder that is still in that folder SHALL be moved into the project folder by type: video → `视频/其他素材`, image → `图片/图片素材`, audio → `音频/音效`. Files already moved on 准备剪辑 SHALL stay where they are.

#### Scenario: Unused footage
- **WHEN** an imported clip was never used and the user approves the 成片
- **THEN** the clip is now at `<项目名>/视频/其他素材/` and no longer in the raw folder

#### Scenario: Drive unplugged
- **WHEN** a file cannot be moved
- **THEN** it is listed as 待归档 with a 重新归档 action on the 资料 page; the approval still stands; file names are kept

### Requirement: Dated project folder names

A content project's material folder SHALL be named `YYYYMMDD_<short name>`, where the date is the project's creation date and the short name follows the existing rule (title before the first ｜, unsafe characters removed, `(#id)` added on a clash). The name SHALL be fixed once created. Existing project folders SHALL be renamed to this form once, with the platform's recorded folder names, material placements and cross-project shortcuts updated to match.

#### Scenario: New project
- **WHEN** a project titled 「儿童麸质饼干｜宝妈测评」 created on 2026-10-29 first gets its material folder
- **THEN** the folder is `20261029_儿童麸质饼干`

#### Scenario: Existing folder renamed
- **WHEN** the one-time migration runs with the material drive connected
- **THEN** the old folder is renamed to its dated name, every material placed in it still resolves to its file, and shortcuts in other projects point to the new location

### Requirement: Local output layout

Local outputs SHALL be organised as `output/YYYYMMDD_<project short name>/` for anything belonging to a content project and `output/_平台/` (模板审片, 规格, 吸收资料, 剪辑技法, 测试) for platform work, and the root README SHALL document this layout.

#### Scenario: Template review pages
- **WHEN** the template review pages are opened from `output/_平台/模板审片/`
- **THEN** all their videos play

