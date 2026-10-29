## ADDED Requirements

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
