## ADDED Requirements

### Requirement: Loudness-mastered narration is a derived MaterialRevision
The audio chain SHALL offer a deterministic loudness-mastering step for accepted narration that produces a new MaterialRevision with parent lineage, unchanged rights flags, identical duration, and recorded target integrated loudness, true-peak ceiling and measured results (defaults −16 LUFS and −1.5 dBTP). The original narration and its transcript alignment SHALL remain unchanged and reusable.

#### Scenario: Narration has a high peak-to-loudness ratio
- **WHEN** accepted narration measures −23 LUFS with −0.1 dBTP peaks and mastering runs with defaults
- **THEN** a derived revision near −16 LUFS with peaks at or below −1.5 dBTP is stored with its lineage, and the original is untouched
