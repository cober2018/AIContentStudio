## ADDED Requirements

### Requirement: The 导演稿 can carry a dialogue track separate from the picture

A video 导演稿 MAY contain one timeline track of kind `dialogue` whose segments name a source material, its trimmed span, the placement on the cut and optionally the script line. Segments MAY cross shot boundaries. Saving SHALL refuse a segment whose material is missing or unusable, whose trim exceeds the material's duration, whose placement falls outside the cut, whose trimmed and placed lengths differ, that overlaps another segment on the track, or that names an unknown script line, saying which segment and why. Dialogue-track materials SHALL enter the edit package and the edit-manifest check like music and voice. Without a dialogue track, editing follows each shot's own sound.

#### Scenario: Voice from a clip that is not any shot's picture
- **WHEN** work 93's 导演稿 places material 455 from 0.70–2.97 s at 12.30–14.57 s on a dialogue track
- **THEN** it saves, material 455 is in the edit package, and the 导演稿 page shows that source beside the line

#### Scenario: Overlapping segments
- **WHEN** two dialogue segments overlap in time
- **THEN** the save is refused naming both segments
