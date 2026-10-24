## ADDED Requirements

### Requirement: Scripts are matched segment by segment

The platform SHALL split a given script into segments, record for each segment its visual role, subject constraints, media type and search queries, and SHALL search the user's own library before open libraries.

#### Scenario: Script about two countries' economies
- **WHEN** a segment compares China and the United States
- **THEN** its constraints name both countries and the comparison, and candidates showing another country score low with that reason

#### Scenario: Own footage exists
- **WHEN** a linked drive file's metadata matches a segment and its rights allow model use
- **THEN** it appears as a candidate before open-library results with an own-library match score

### Requirement: Only licensed candidates are shown

Open-library candidates SHALL carry a license code, license URL and attribution text, and candidates with unknown or disallowed licenses MUST NOT be shown.

#### Scenario: Unknown license
- **WHEN** a provider returns an item without a recognisable license
- **THEN** the item is dropped and counted in the run's skipped totals

### Requirement: Main picks require a seen picture

Each candidate SHALL have a score breakdown with reasons. A candidate MUST NOT become a segment's main pick unless a vision-capable model actually read its image or video poster. Video candidates SHALL be marked for full-clip human review.

#### Scenario: No vision model configured
- **WHEN** no registered chat model accepts images
- **THEN** the run completes with text scores only, no automatic main picks, and a notice explaining why

### Requirement: Matching never downloads or fills gaps on its own

A match run SHALL only store links, previews and metadata. Files SHALL be downloaded only when the user or an agent explicitly accepts a candidate, which creates a Material revision with source URL, license, attribution and rights. Segments without a good candidate SHALL be listed as gaps and MUST NOT be filled with generated or unrelated material automatically.

#### Scenario: Accept a candidate into a project
- **WHEN** the user accepts a Pexels clip for segment 3 of a project's script
- **THEN** a Material revision is created with the Pexels license and attribution and referenced by the project with the segment as note

#### Scenario: Segment with no fit
- **WHEN** no candidate passes the threshold for a segment
- **THEN** the plan shows it as a material request with what the shot must show, and nothing is substituted

### Requirement: Match plans are saved and reviewable

Each run SHALL be saved with its source text or source revision hash, settings, progress, results and the model and provider versions used, and SHALL be reopenable, cancellable and resumable after a restart.

#### Scenario: API restart during a run
- **WHEN** the API restarts while a run is in progress
- **THEN** the run is shown as interrupted with completed segments kept, and the user can resume it

### Requirement: Shots in the storyboard can find their own material

On the video 分镜 step, the AI 创作助手 SHALL offer a search for the focused shot, or for every shot without material, built from that shot's narration, visual, purpose and requirements. A picked candidate SHALL be accepted into the material library, referenced by the project with the shot as note, and set as the shot's source material in the unsaved draft; the shot binding MUST only persist when the user saves the draft.

#### Scenario: Find footage for one shot
- **WHEN** the user focuses shot 4 and asks the assistant to find material
- **THEN** the assistant shows ranked candidates for shot 4 with previews, reasons and licenses, own-library matches first

#### Scenario: Pick a candidate
- **WHEN** the user picks a candidate for shot 4
- **THEN** a Material revision is created with its license and attribution, the project references it with note "镜头 4", and shot 4's source material changes in the draft only

#### Scenario: Nothing fits
- **WHEN** no candidate passes the threshold for a shot
- **THEN** the assistant shows a material request for that shot and binds nothing

### Requirement: Match runs are shown under their project and piece
A match run linked to a project or unit SHALL show that project and piece, with a link back. 素材库 history SHALL list runs of every scope, labelled with project and piece. Each piece's production page SHALL offer a 「找素材」 entry listing that piece's runs.

#### Scenario: Card photo search
- **WHEN** a shots-scope run is started for project 41, graphic unit 79
- **THEN** it appears in 素材库 history labelled 「海底光缆 · 图文」, its page links back to the piece, and the graphic piece's 「找素材」 entry lists it

### Requirement: Users can upload their own material for a segment
Each matched segment or shot SHALL offer 「上传自己的」. The upload SHALL use the existing material upload, with the user stating source and rights. It SHALL then be recorded as that segment's choice, attached to the run's project with the segment as the note, and clear an earlier rejection.

#### Scenario: Upload for a gap
- **WHEN** the user uploads a press photo of a cable ship for card-2, states its source and licence, and confirms
- **THEN** a Material revision is created with those rights, card-2 shows it as chosen, the project references it, and `get_material_match` returns it as card-2's choice
