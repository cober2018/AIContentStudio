## ADDED Requirements

### Requirement: Delivery checks read frames with accurate conversion

Frame readings used by the delivery checks (average, highlight, overexposure, clipping and cover colour) SHALL differ from the standard conversion (Y−16)×255/219 by at most 1 level whether the video is tagged bt709, smpte170m or untagged. Stored checks SHALL record which reader produced them, and a recompute from the edit manifest SHALL read the sources with the same reader as the stored delivered readings. Threshold defaults stay unchanged.

#### Scenario: bt709 solid colour
- **WHEN** a lossless bt709-tagged video with Y=235 is read
- **THEN** the reading is 255 within 1 level

#### Scenario: Task 42 cover
- **WHEN** task 42's cover is compared with its final using accurate conversion
- **THEN** the difference is about 2 levels, below the default threshold 6, and no warning is given

### Requirement: One brightness warning per shot

The final-versus-source comparison SHALL give at most one warning per shot, carrying the average and/or highlight difference that crossed its threshold, so that 30 darkened shots plus a colour-tag, an overexposure and a dialogue warning keep every warning and the per-shot readings and can be recomputed. When the checks still do not fit, brightness and colour-tag warnings SHALL be kept first. Older records with separate average and highlight warnings, and full, 4-item and 6-item slim readings, SHALL still display and recompute.

#### Scenario: Thirty darkened shots
- **WHEN** 30 shots are darker than their sources in average and highlight, with one colour-tag, one overexposure and one dialogue warning
- **THEN** all 33 warnings and the per-shot readings are stored and the edit manifest recompute runs
