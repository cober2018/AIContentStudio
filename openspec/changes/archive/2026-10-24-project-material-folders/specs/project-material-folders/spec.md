## ADDED Requirements

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
