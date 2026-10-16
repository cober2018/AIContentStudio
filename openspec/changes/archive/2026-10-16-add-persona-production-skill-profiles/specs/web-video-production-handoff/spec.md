## ADDED Requirements

### Requirement: Technology explainer production follows a shared narration timeline
For the technology explainer route, final shot timing SHALL derive from corrected narration and verified word/phrase timing. Cuts SHALL preserve source-to-output mappings and update linked captions, visuals and sound cues together. Estimated timing SHALL be labeled and MUST NOT be represented as verified alignment. The visible workflow SHALL expose research, script, narration, assets, sound edit, visual pacing, captions/color, packaging, export and review, allowing irrelevant stages to be skipped.

#### Scenario: A narration phrase is removed
- **WHEN** the accepted cut changes narration duration
- **THEN** linked visuals, captions and SFX follow the same updated mapping and are checked in the rendered result

### Requirement: Resolve edits and AE packaging preserve editable handoff
Resolve SHALL remain the main timeline for sound, pacing, captions, color, final mix and export. AE SHALL receive bounded packaging shots after rough-cut lock and return render files plus editable project evidence. The workflow SHALL verify returned timing and format against the main timeline and preserve originals and reopenable native projects. The existing manual website generation and platform CLI/MCP operation model SHALL remain unchanged.

#### Scenario: A shot needs explanatory motion graphics
- **WHEN** an approved shot is assigned to AE
- **THEN** its asset references, timing anchors and style parameters accompany the task, and the returned render is verified in Resolve before final export

### Requirement: Creative quality and sound inspection are explicit
Review SHALL inspect the actual final media and assess factual support, explanation quality, reference-style consistency, readable captions, pacing and sound. Objective measurements, transcript checks, AI review and direct listening SHALL be recorded as distinct evidence. Missing listening or style acceptance MUST NOT be described as completed human quality review.

#### Scenario: A mixed soundtrack passes technical measurements
- **WHEN** no direct listening has occurred
- **THEN** the report states the technical results and listening boundary without claiming auditory acceptance
