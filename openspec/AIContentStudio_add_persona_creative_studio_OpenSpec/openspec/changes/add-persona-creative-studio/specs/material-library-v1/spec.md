## ADDED Requirements

### Requirement: Persona Graphic and Audio results remain MaterialRevision truth

Actual rendered Graphic PNGs and accepted TTS audio SHALL be persisted through existing Material/MaterialRevision contracts with exact bytes/hash/MIME/source/provider/renderer/rights provenance. Creative Skill/Persona configuration SHALL be provenance, not a replacement file truth.

#### Scenario: Audio method changes
- **WHEN** a Persona later changes voice preset
- **THEN** an old accepted audio MaterialRevision remains immutable and traceable to the prior TTS task/configuration

### Requirement: Quality checks do not silently mutate media rights

Graphic/Audio QC MAY block, warn or reference an exact MaterialRevision but MUST NOT upgrade public/model/commercial rights, remove attribution obligations or replace bytes in place.
