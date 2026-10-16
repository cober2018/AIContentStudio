## ADDED Requirements

### Requirement: Background music supports editable scene-based metadata
Existing music assets SHALL support editable multi-label scene, mood, energy, instrumentation/vocal, tempo when known, looping suitability and source/license metadata. Metadata corrections SHALL preserve prior execution references. Music selection SHALL depend on current scene needs rather than exclusive Persona ownership, and no-BGM SHALL be an explicit valid choice.

#### Scenario: A track was tagged with the wrong mood
- **WHEN** the user corrects its tags
- **THEN** future searches and suggestions use the correction while previously frozen selections remain explainable

#### Scenario: A scene needs unobstructed narration
- **WHEN** the selected audio plan omits background music
- **THEN** production completes without requiring a replacement track

### Requirement: Selected music has traceable assets and a mixing plan
The video handoff SHALL record selected music revision, source interval, target scene and mix intent including fades/ducking where used. Existing rights checks SHALL apply to each track rather than inheriting a code repository's license. Initial curated tracks SHALL have individual source evidence before production adoption.

#### Scenario: A Skill bundles an unidentified music file
- **WHEN** the file has no recoverable track-level provenance
- **THEN** it is not declared cleared for public delivery merely because the Skill repository has a permissive code license
