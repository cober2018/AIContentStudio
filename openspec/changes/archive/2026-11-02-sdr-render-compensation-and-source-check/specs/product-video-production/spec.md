## ADDED Requirements

### Requirement: SDR live footage is compensated for the render offset

Edit rules SHALL require compensating ordinary SDR live footage for the davinciYRGB render darkening (about 20/255), by applying the stored `sdr-render-comp.cube` or by fixing the cause in project settings for the whole cut, stating which in the receipt; HLG clips SHALL keep only their render LUT. The LUT SHALL be kept in the repository with install instructions.

#### Scenario: Selfie SDR clip in a product video
- **WHEN** a product video uses a bt709 HEVC selfie clip without a LUT
- **THEN** the rules require the compensation so the render matches the source brightness

### Requirement: Delivery compares final and source brightness for live shots

On 成片 and 小样 delivery the platform SHALL, for each shot whose picture is an SDR video material, compare the mean luma of the delivered frame at the shot's middle with the source frame at the matching time, and warn when they differ by more than a configurable threshold (default 8). HLG sources and unreadable sources SHALL be skipped. Warnings SHALL NOT block delivery.

#### Scenario: Task 41
- **WHEN** task 41's final of work 93 is checked
- **THEN** its SDR selfie shots are flagged as about 20 levels darker than the source
