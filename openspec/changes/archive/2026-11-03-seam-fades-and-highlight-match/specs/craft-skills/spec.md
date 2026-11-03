## ADDED Requirements

### Requirement: Dialogue seam fades stay in pauses

The craft-resolve sound techniques SHALL place seam overlaps and fades only in pauses, never over a word; when a cut is less than 3 frames from a word's start or end the fade SHALL be 1 frame; after joining, the whole dialogue SHALL be re-transcribed and each segment's first and last word checked. The two places describing seams SHALL say the same.

#### Scenario: Cut 1 frame before a word
- **WHEN** a segment starts at 7.733 s and its first word starts at 7.76 s
- **THEN** the fade-in is 1 frame and the word is intact in the re-transcription

### Requirement: AE overlays are read at full data level instead of compensating the render

The craft-resolve color techniques SHALL set every transparent RGB overlay (AE qtrle, ProRes 4444, PNG) to Data Level Full before it goes on the timeline, apply no compensation LUT to ordinary SDR live footage, and restore iPhone HLG with `iphone-hlg-apple-sdr.cube`; the old `sdr-render-comp.cube` and `iphone-hlg-apple-sdr-render.cube` SHALL be removed from the repository and the rules SHALL say to delete them from Resolve's MCP folder. color.md SHALL state that AE overlays themselves do not darken, keep "render once and compare" for AI images, and check highlights by source luma band (at least the areas above 200) as well as the average.

#### Scenario: Task 42 selfie shots re-rendered
- **WHEN** shots 0, 1, 2 and 6 of task 42 are rendered with their overlays at Data Level Full and no LUT
- **THEN** each source luma band from 0 to 235 differs from the render by at most 2 levels

### Requirement: AE RGB exports are read at full data level whether or not they have alpha

The craft-resolve rules SHALL set Data Level Full on every RGB file exported from AE (qtrle, ProRes 4444, PNG and similar), with or without an alpha channel, and confirm it with GetClipProperty; the source note SHALL record an Auto-versus-Full render comparison of an opaque qtrle file by luma band.

#### Scenario: Opaque end card
- **WHEN** an AE end card exported as opaque qtrle is imported
- **THEN** the rules require Data Level Full before it goes on the timeline
