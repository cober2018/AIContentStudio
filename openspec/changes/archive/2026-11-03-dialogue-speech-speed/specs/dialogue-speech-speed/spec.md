## ADDED Requirements

### Requirement: Dialogue segments may play at a set speed

A dialogue segment in a video.master.v2 timeline MAY carry `speed_percent`, an integer from 50 to 200, meaning 100 when absent. A segment SHALL be accepted when its trim length differs from its placement length × speed_percent / 100 by at most 34 ms; otherwise it SHALL be rejected with `video_dialogue_length_mismatch`. A segment without `speed_percent` SHALL normalize exactly as before.

#### Scenario: Faster segment saves
- **WHEN** a segment trims 0–11500 ms of its clip, is placed at 0–10000 ms and has speed_percent 115
- **THEN** the 导演稿 is accepted and the segment keeps speed_percent 115

#### Scenario: Missing speed still mismatches
- **WHEN** the same segment has no speed_percent
- **THEN** saving fails with video_dialogue_length_mismatch

### Requirement: Whole-video speech speed from the voice step

For a video work whose master has a dialogue track, the 配音与音乐 step SHALL show a speed slider from 0.8× to 1.5× in steps of 0.05, set to the current speed, with the resulting video length shown as it moves. Saving SHALL store a new master revision as the user's own edit, without a new 导演稿 adoption, in which every dialogue segment has the new speed_percent and its placement recomputed, and every shot length, track placement, subtitle cue, overlay, AE composition length, feedback time and the total length is rescaled by old speed / new speed from the current master. Music SHALL NOT change speed. Works without a dialogue track SHALL NOT show the slider. A finalized work SHALL refuse the change.

#### Scenario: Work 94 at 1.15×
- **WHEN** the user sets the slider to 1.15 on a work whose dialogue segments have no speed_percent
- **THEN** the new master has speed_percent 115 on every segment, its total length is about the old length / 1.15, shots, subtitles and overlays shrink in proportion, and the page shows the new length

#### Scenario: Back to 1.0×
- **WHEN** the user then sets the slider back to 1.0
- **THEN** every time point returns to its original value within 1 ms

### Requirement: Edit rules and storyboard follow the speed

The edit rules given to the third-party model SHALL say that a dialogue segment with speed_percent is played at that speed with pitch correction and that live picture synced to it plays at the same speed. The storyboard SHALL mark a segment whose speed is not 100 with its speed, for example 「1.15 倍速」, read-only.

#### Scenario: Storyboard shows the speed
- **WHEN** a segment has speed_percent 115
- **THEN** its sound line on the storyboard ends with 「1.15 倍速」
