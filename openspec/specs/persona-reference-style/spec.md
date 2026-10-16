# persona-reference-style Specification

## Purpose
TBD - created by archiving change add-persona-production-skill-profiles. Update Purpose after archive.
## Requirements
### Requirement: Reference style observations preserve modality and evidence
The system SHALL support separate text, image and video reference observations linked to existing material/source revisions. Each observation SHALL distinguish directly observed expression, inferred creative intent and unknown details, and carry a text passage, image region or video time reference as applicable. Reference identity, personal experiences and historical claims MUST NOT become Persona facts by style extraction.

#### Scenario: A reference video informs the technology Persona
- **WHEN** an Agent analyzes the user's video reference
- **THEN** the resulting draft preserves evidence for narrative, screen demonstrations, graphical treatment, pacing and inspected sound, while unsupported or uninspected sound characteristics remain unknown

### Requirement: Style drafts become Persona assets only through explicit adoption
The system SHALL expose editable style drafts and save accepted drafts as versioned existing style/method assets linked to the Persona. Updating a style SHALL preserve historical snapshots and other Personas. No fixed sample count SHALL prevent producing a provisional draft, and provisional findings SHALL remain labeled until accepted.

#### Scenario: User changes an inferred visual preference
- **WHEN** the user edits and adopts the draft
- **THEN** the accepted rules and supporting references form a new Persona-scoped revision while the original observation remains inspectable

### Requirement: Style transfer validation uses a new subject
Before promoting a trial production Skill combination as the technology Persona default, the workflow SHALL compare baseline and selected method outputs and evaluate a complete work on a subject not used to derive the reference style. Technical validation, AI creative review and user style acceptance SHALL be recorded separately.

#### Scenario: Engineering passes but style is not accepted
- **WHEN** an output renders correctly but has no user style acceptance
- **THEN** it remains a trial and is not reported as the finalized Persona standard
