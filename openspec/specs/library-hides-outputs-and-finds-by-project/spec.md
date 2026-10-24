# library-hides-outputs-and-finds-by-project Specification

## Purpose
TBD - created by archiving change library-hides-outputs-and-finds-by-project. Update Purpose after archive.
## Requirements
### Requirement: Outputs are not materials

The material library views and material search SHALL NOT list edit-task outputs (小样, 成片, their subtitles, Resolve / AE projects, edit manifest) or files under a project's `导出/` folder. The files SHALL stay where they are.

#### Scenario: Final cut hidden
- **WHEN** the user opens 素材库 → 项目 → 海底光缆
- **THEN** 「海底光缆｜竖屏视频 · final」 is not listed, and the file is still in `海底光缆/导出/成片/`

#### Scenario: AE shot renders stay
- **WHEN** the user opens 海底光缆 → 视频/其他素材
- **THEN** the AE-rendered shot clips are listed

### Requirement: Reused material appears in the project folder as a shortcut

When a project uses a material stored in another project's folder or in 通用素材库, the platform SHALL leave the file in place and put a shortcut to it in the using project's matching subfolder.

#### Scenario: Second project reuses a clip
- **WHEN** project B's adopted 导演稿 uses a clip stored in `海底光缆/视频/Broll/`
- **THEN** the clip stays there and `B/视频/Broll/` holds a shortcut with the same name pointing to it

### Requirement: Project view follows the project folder

The 项目 view SHALL list the materials in that project's folder, including those reached through shortcuts, marking where shortcut targets come from. Outputs SHALL NOT be listed.

#### Scenario: Shortcut listed
- **WHEN** the user opens 素材库 → 项目 → B
- **THEN** the reused clip is listed with 「来自 海底光缆」

