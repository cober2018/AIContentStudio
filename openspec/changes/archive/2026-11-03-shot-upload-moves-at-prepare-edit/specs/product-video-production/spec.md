## ADDED Requirements

### Requirement: A manually uploaded shot video is filed at 准备剪辑

A video the user uploads onto a shot from the supplement panel SHALL be stored and placed on the shot without moving any file on the library drive; it SHALL be moved into the project folder on 准备剪辑 like every other material the adopted draft uses, keeping the user's file name when a byte-identical user file exists. Platform-made files (automatic clips, AI pictures, voiceover) keep going straight into the project folder.

#### Scenario: Upload of a file that sits in 外部素材库
- **WHEN** the user uploads a video whose bytes match a file in 外部素材库
- **THEN** that file stays where it is and the shot uses the upload
- **AND** on 准备剪辑 the file is moved into the project folder under its own name

### Requirement: The supplement panel shows a placed clip clearly

When a shot's clip is an uploaded or generated video placed on the shot, the supplement panel SHALL say so plainly (uploaded / generated and placed on this shot, with the material number) while still allowing a new upload or generation. The panel's missing count SHALL count only shots with no clip at all.

#### Scenario: After an upload
- **WHEN** the user uploads a video onto shot 6 of work 94
- **THEN** the panel says the video is uploaded and placed on this shot, and shot 6 is not counted as missing
