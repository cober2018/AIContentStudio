# video-step-pages Specification

## Purpose
TBD - created by archiving change lock-finished-video-and-page-per-step. Update Purpose after archive.
## Requirements
### Requirement: Saving unchanged content does not restart the video

A master revision whose content is identical to its parent SHALL NOT be treated as a new director draft. The page's save button SHALL be disabled when there are no unsaved changes.

#### Scenario: Unchanged save after the final cut
- **WHEN** a master revision is saved with the same content as the previous one
- **THEN** the video progress stays where it was (e.g. 已完成) and the final cut is still shown

### Requirement: A finished video is locked until reopened

After the final cut is approved, the platform SHALL refuse new master revisions for that unit (from the page and over MCP) until the user reopens it from the 成片 page with a confirmation. Earlier steps SHALL be read-only while locked.

#### Scenario: Save attempt while locked
- **WHEN** someone saves a master for a unit whose final cut is approved and not reopened
- **THEN** the save is refused with 「成片已完成，先在成片页点『重新打开』」

#### Scenario: Reopen
- **WHEN** the user clicks 「重新打开」 and confirms
- **THEN** saving is allowed again; the old final cut stays in 导出/成片, and the next new director draft starts the flow again

### Requirement: Persona video shows one step per page

Persona video production SHALL have the steps 选题与资料, 导演稿, 小样, 成片, 交付, each on its own page with 上一步 / 下一步. Opening the unit SHALL land on the step the video is at. Steps not yet reached SHALL show 「还没到这一步」. The storyboard SHALL show one shot at a time with 上一镜 / 下一镜. Master versions, shot material tools, the director package and the save button SHALL sit under 「更多」, collapsed by default.

#### Scenario: Open a finished video
- **WHEN** the user opens 海底光缆's video
- **THEN** the 成片 page shows with the player, and the 导演稿 page is view-only

