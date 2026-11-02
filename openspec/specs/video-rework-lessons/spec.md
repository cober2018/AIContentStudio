# video-rework-lessons Specification

## Purpose
TBD - created by archiving change video-unify-footage-and-learn-from-rework. Update Purpose after archive.
## Requirements
### Requirement: Rework notes are kept as rework records

Every note given when a 小样 or 成片 is sent back SHALL be stored as a rework record with the work, stage, time point, text and time, in addition to being passed to the current editor.

#### Scenario: Sending back a sample
- **WHEN** the user sends back a 小样 with the note 「画面过曝」
- **THEN** a rework record for that work and stage is kept and listed in the lessons library

### Requirement: Editors propose lessons that the user approves

MCP SHALL offer `propose_lesson` with cause, rule, scope and source rework records. A proposal describing an existing lesson SHALL attach to it and increase its count instead of creating a duplicate. Settings SHALL show pending lessons to approve, edit or reject, and active lessons with count and sources that can be retired; causes seen twice or more SHALL be highlighted.

#### Scenario: Same cause again
- **WHEN** a second video is sent back for over-exposure and the editor proposes the same lesson
- **THEN** the existing lesson's count becomes 2 and it is highlighted

### Requirement: Active lessons reach every new video

Active lessons SHALL be included in the video brief given to the editor with a rule to follow them, and the delivery receipt SHALL name the lessons applied.

#### Scenario: Next product video
- **WHEN** the HLG over-exposure lesson is active and a new product video brief is read
- **THEN** the brief lists that lesson and the receipt states it was applied

