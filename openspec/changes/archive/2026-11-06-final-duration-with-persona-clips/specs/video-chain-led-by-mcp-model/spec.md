## ADDED Requirements

### Requirement: The 成片 length check includes persona clips

When a `final` output is submitted for an edit task whose package carries `director.persona_clips`, the platform SHALL require its container and video-stream length to equal `director.timeline.duration_ms` plus the duration of every persona clip, within one frame plus 1 ms. A 小样 and a 成片 without persona clips SHALL be checked against `director.timeline.duration_ms` as before.

#### Scenario: 成片 with an outro
- **WHEN** the timeline is 217283 ms, the outro is 4200 ms and the delivered 成片 is 221483 ms at 60 fps
- **THEN** the 成片 is accepted for staging

#### Scenario: Off by more than a frame
- **WHEN** the same 成片 is two frames shorter
- **THEN** it is refused with creative_video_duration_mismatch

#### Scenario: 小样 unchanged
- **WHEN** a 小样 of the same work is delivered at 221483 ms
- **THEN** it is refused, because a 小样 carries no clips
