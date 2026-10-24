## ADDED Requirements

### Requirement: Every shot carries a brief

Each shot in the shot plan and the video draft SHALL carry its narration, on-screen visual, search words (Chinese and English), a first-frame image prompt, an image-to-video prompt based on that frame, and a suggested route (find, generate, platform-drawn). All fields SHALL be editable by the user.

#### Scenario: New shot plan
- **WHEN** the shot-plan step produces shots
- **THEN** each shot includes search words, a generation prompt and a route

#### Scenario: Older draft without a brief
- **WHEN** the user opens a shot slot whose shot has no brief
- **THEN** the platform proposes one, and it is stored only when the user saves the draft

### Requirement: A shot slot takes material from any source

The video production page SHALL show each shot as a slot with its brief, a status (缺素材 / 有候选 / 已选定) and its candidates. Candidates SHALL include picks and uploads from this unit's match runs with the same shot id, platform search results, uploads made on the slot, and generated outputs. A shot MAY keep several candidates. Binding SHALL happen only by the user choosing a candidate and saving the draft.

#### Scenario: Pick made in the material library
- **WHEN** the user picked a material for shot-8 in a match run of this unit
- **THEN** shot-8's slot shows it as a candidate and the status is 有候选

#### Scenario: Upload on the slot
- **WHEN** the user uploads a clip on a shot with rights fields
- **THEN** it becomes a material revision, a candidate of that shot, and is referenced by the project with the shot as note

#### Scenario: Web-video route
- **WHEN** the user chooses the web-video route for a shot
- **THEN** the prompt is pre-filled with the brief's video prompt and stays editable

#### Scenario: First frame then video
- **WHEN** the user opens a shot's brief
- **THEN** it shows a first-frame image prompt and a video prompt that only describes motion and camera movement from that frame, each with a copy button
- **AND** the API-image route shows that shot's frame prompt to copy into the image generator

### Requirement: Missing material does not block work

Empty slots MUST NOT block drafting, narration, subtitles or editing. Steps that need every shot (web-video handoff, final render) SHALL name the missing shots.

#### Scenario: Handoff with gaps
- **WHEN** the user starts a handoff while shots 3 and 14 have no source
- **THEN** it is refused with a message naming shots 3 and 14

### Requirement: Agents read slots but cannot bind

The MCP tool `get_shot_slots` SHALL return each shot's brief, status, candidates, the user's choice and a review link, and SHALL be read-only. No MCP tool SHALL bind a shot source.

#### Scenario: Agent checks progress
- **WHEN** an agent calls `get_shot_slots` for U80
- **THEN** it sees which shots are 缺素材 and can start a material match for them, while binding remains on the platform

### Requirement: Each shot chooses how to generate

Each shot brief SHALL carry a direct text-to-video prompt, a first-frame image prompt, and an image-to-video prompt based on that frame, plus a generation mode (`text` or `frame`) suggested by the planner. The user SHALL switch the mode per shot on the page. Switching MUST NOT count as editing the prompts. Every prompt SHALL state the aspect ratio and exclude text, watermarks and audio, and video prompts SHALL state the shot's duration. The shot keeps one material slot whatever the mode.

#### Scenario: Switch mode
- **WHEN** the user switches shot 2 from 直接生成视频 to 先生成首帧
- **THEN** the page shows the first-frame and image-to-video prompts, the choice is saved, and a later prompt refresh still updates the prompts

### Requirement: Upload windows close only on purpose

Windows used to upload files MUST NOT close when the user clicks outside them. They SHALL close only through their close or cancel controls or the Escape key.

#### Scenario: Drag a file and click beside the window
- **WHEN** the user drags a file and the click lands outside the upload window
- **THEN** the window stays open with its contents

### Requirement: An upload can be withdrawn from its segment

Each material the user uploaded to a segment or shot SHALL have a ✕ control that, after confirmation, removes it from that segment's candidates and picks. The material MUST stay in the material library. The project's reference to it SHALL be detached unless another segment of the same project still uses the same file.

#### Scenario: Withdraw the only upload
- **WHEN** the user withdraws the only upload on shot 1
- **THEN** shot 1 has no pick, its status updates, and the project's reference to that file is detached while the file remains in the library
