## ADDED Requirements

### Requirement: Spoken-script variants of a finished video take only shot footage
A spoken-script channel variant of a video master SHALL map only the master's per-shot footage. Voice, music, covers, rough cut and final render attached to the master SHALL be left out of the variant and SHALL NOT block the preview.

#### Scenario: Finished video
- **WHEN** the user requests a 抖音口播 preview for a video whose master carries voice, music, covers and a rough cut
- **THEN** the preview is generated from the script and per-shot footage without a 422

#### Scenario: Footage does not match the shots
- **WHEN** a shot's footage differs from the director draft's shot
- **THEN** the preview is refused with `video_source_b_roll_mismatch` as before

#### Scenario: Shots share a narration line or have none
- **WHEN** several consecutive shots share one script line, or a shot such as an outro card has no line
- **THEN** the preview has one scene per line carrying all of those shots' footage, without repeating or inventing words
