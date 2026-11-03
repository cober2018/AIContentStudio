## ADDED Requirements

### Requirement: Cut deliveries report each shot's source in-point

A 小样 or 成片 delivery MAY carry `shot_sources` listing, per live-picture shot, the shot id, the picture material and the source in-point in milliseconds. The platform SHALL refuse entries naming an unknown shot, a material outside the edit package, or an in-point that is negative or past the material's duration, saying which entry. Edit rules SHALL require the editor to report them.

#### Scenario: Final with in-points
- **WHEN** a final is delivered with shot-6's in-point 3200 ms in material 455
- **THEN** it is accepted and stored with the output

### Requirement: Source brightness comparison uses reported in-points

The final-versus-source brightness check SHALL sample the source at the reported in-point plus the offset of the shot's middle; shots without a reported in-point SHALL use the in-shot offset and be marked as estimated on the review page.

#### Scenario: Compensated cut
- **WHEN** task 42's final is checked with its true in-points
- **THEN** its SDR shots differ from the source by under 2 levels and no warning is shown

### Requirement: The brightness comparison is recomputed from the edit manifest

When an edit manifest passes its check, the platform SHALL recompute the final-versus-source brightness comparison using each shot's manifest trim_start_ms, converting the in-shot offset by speed_percent for speed-changed clips, and SHALL replace the review warnings with the new readings. Manifest in-points take precedence over delivered shot_sources, which take precedence over estimates.

#### Scenario: Task 42 shot-6
- **WHEN** task 42's edit manifest is applied to the comparison
- **THEN** shot-6 samples the source at about 8.55 s reading about 146.8, every shot is within 2 levels and no warning is shown
