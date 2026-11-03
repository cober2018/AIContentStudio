## MODIFIED Requirements

### Requirement: SDR live footage is compensated for the render offset

Edit rules SHALL remove the davinciYRGB render darkening at its cause: every RGB file exported from AE, with or without alpha, is set to Data Level Full before it goes on the timeline, ordinary SDR live footage gets no compensation LUT, and HLG clips get only `iphone-hlg-apple-sdr.cube`. The rules SHALL tell the editor not to use, and to delete from Resolve's MCP folder, the old `sdr-render-comp.cube` and `iphone-hlg-apple-sdr-render.cube`, and the receipt SHALL say which AE files were set to Full.

#### Scenario: Selfie SDR clip under an AE overlay
- **WHEN** a product video puts an AE overlay over a bt709 HEVC selfie clip
- **THEN** the rules require the overlay at Data Level Full and no LUT on the selfie clip, so the render matches the source brightness

## ADDED Requirements

### Requirement: Final-versus-source comparison checks highlights

For every shot in the source comparison (HLG / PQ sources excluded) the platform SHALL also compare the 90th-percentile luma of the delivered and source frames, warn when the difference exceeds an adjustable highlight threshold (default 5) with both readings and the frame basis, keep the delivered highlight reading in the slim stored form, and redo the highlight comparison when the edit manifest arrives.

#### Scenario: Task 41 final
- **WHEN** task 41's final is checked against its sources
- **THEN** all four selfie shots warn that highlights are about 18–19 levels darker

#### Scenario: Task 42 final
- **WHEN** task 42's final is checked with the edit manifest's in-points
- **THEN** all four selfie shots warn that highlights are about 6–7 levels darker and no average-brightness warning appears

## ADDED Requirements

### Requirement: Shot checks keep every brightness warning when many shots are flagged

The stored shot checks of a 小样 or 成片 SHALL allow up to 8000 characters, with the same allowance wherever output metadata is validated or re-read, so that 20 shots each carrying an average and a highlight warning keep every warning and their per-shot readings and can be recomputed from the edit manifest. When even that does not fit, the brightness comparison warnings SHALL be kept before any other warning is dropped. Records stored in the full, 4-item slim and 6-item slim forms SHALL still display and recompute.

#### Scenario: Twenty darkened shots
- **WHEN** a final has 20 shots each with an average and a highlight warning
- **THEN** all 40 warnings and the per-shot readings are stored, and the edit manifest recompute runs

#### Scenario: Sixty shots that do not fit
- **WHEN** the checks of 60 shots exceed the allowance
- **THEN** the brightness comparison warnings are kept first and only other warnings are dropped before them
