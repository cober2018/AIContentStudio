## ADDED Requirements

### Requirement: The cover is taken from the rendered final cut

The edit rules SHALL require the cover design to be rendered as the opening of the final cut and the cover image to be extracted from the rendered file within its first 0.5 s, never composited separately from source footage; the final cut SHALL be tagged sRGB (BT.709 primaries, sRGB transfer, BT.709 matrix) by retagging without re-encoding, and the cover saved as sRGB.

#### Scenario: Cover made in AE from source footage
- **WHEN** the editor composites a cover in AE from the original clip
- **THEN** this breaks the rule; the cover must be a frame of the rendered final cut

### Requirement: Delivery warns about cover mismatch and non-sRGB tags

When both a cover and a final cut of one task are delivered, the platform SHALL compare the cover with frames from the first 0.5 s of the final cut, take the closest, and warn 「封面与成片颜色不一致」 when the average per-channel difference exceeds a configurable threshold (default 6 of 255), naming the difference and time. A final cut whose color tags are not sRGB SHALL be warned about. Warnings SHALL NOT block delivery.

#### Scenario: Cover from a different grade
- **WHEN** a final cut is delivered with a cover composited from the source footage
- **THEN** the review page shows 「封面与成片颜色不一致」 with the measured difference
