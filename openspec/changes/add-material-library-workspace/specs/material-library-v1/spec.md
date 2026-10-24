## ADDED Requirements

### Requirement: Materials are browsable visually

The material library SHALL show every material with a preview (image thumbnail, video poster, audio waveform), its type, rights summary, source and availability, and SHALL filter by those properties.

#### Scenario: Find usable footage
- **WHEN** the user filters video materials with model use allowed from the T1000 folder
- **THEN** only matching footage appears with poster frames, and unavailable drive files are marked as such

### Requirement: Preview derivatives never change material truth

Thumbnails, posters and waveforms SHALL be cached derivatives keyed by content hash and MUST NOT create material revisions or modify original files.

#### Scenario: Drive file thumbnail
- **WHEN** a linked drive video is listed
- **THEN** its poster comes from the cache and the drive file is only read
