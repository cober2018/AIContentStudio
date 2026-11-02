## ADDED Requirements

### Requirement: HLG footage is restored to its phone appearance before editing

The edit rules sent with every video brief SHALL require checking each live clip's transfer characteristic and applying the stored iPhone HLG-to-SDR LUT only to HLG clips, in a non-color-managed project, leaving SDR stock, generated images and overlays untouched, and verifying brightness on the rendered file against the phone's own display frame. The LUT files SHALL be kept in the repository with install instructions.

#### Scenario: iPhone HLG product footage
- **WHEN** a product video uses iPhone HLG clips and a stock SDR clip
- **THEN** only the HLG clips get the LUT and the rendered brightness matches the phone's display of the same frame

### Requirement: Footage is unified before the sample is exported

Before exporting a 小样, the editor SHALL correct exposure and white balance and match shots of the same scene to a reference shot without stylised grading, level each live dialogue segment to a common loudness, lightly denoise obvious noise and fix one-sided mono, then mix to the existing targets. The delivery receipt SHALL list the color and audio adjustments per shot.

#### Scenario: Clips shot on different days
- **WHEN** a 小样 uses clips from two shooting sessions with different brightness and speech levels
- **THEN** the delivered 小样 shows matched brightness between adjacent shots of the same scene and level speech, and the receipt lists what was changed

### Requirement: Delivery checks flag exposure, brightness jumps and uneven speech

On 小样 and 成片 delivery the platform SHALL sample each shot along the 导演稿 timeline and warn, without blocking, about over-exposed shots, large brightness jumps between adjacent shots and uneven dialogue loudness, naming the shot and the measured difference. Thresholds SHALL be configurable.

#### Scenario: Over-exposed shot
- **WHEN** a delivered 小样 has a shot whose highlights are largely clipped
- **THEN** the review page warns about that shot with its measured brightness
