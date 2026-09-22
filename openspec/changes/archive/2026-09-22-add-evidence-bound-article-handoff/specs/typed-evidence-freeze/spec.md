## ADDED Requirements

### Requirement: Evidence items are explicitly classified
The system SHALL classify each newly reviewed evidence item as `fact`, `event`, `third_party_quote`, or `author_opinion`; migrated items without a reviewed classification SHALL be marked `legacy_untyped`.

#### Scenario: Author opinion is not promoted to fact
- **WHEN** an imported article passage is confirmed as the author's interpretation or opinion
- **THEN** the system stores the actual passage as `author_opinion`
- **AND** the item cannot be used as an objective Fact solely because it belongs to a frozen pack

#### Scenario: Third-party quotation keeps attribution
- **WHEN** a third-party statement is accepted as evidence
- **THEN** the system requires the verbatim excerpt, speaker or publisher, source reference, and available time or position locator
- **AND** the system treats the quotation as attributed speech rather than verified objective truth

#### Scenario: Event evidence may be non-numeric
- **WHEN** a sourced event contains no numeric value
- **THEN** the system permits the event as evidence when its statement, source locator, and time scope are present

### Requirement: Freeze stores an immutable evidence snapshot
Freezing a FactPack SHALL persist the exact normalized evidence payload and snapshot schema version used by downstream content, including applicable statement, value, unit, excerpt, attribution, source locator/version, time scope, and permission flags.

#### Scenario: Live fact edit does not change frozen evidence
- **WHEN** a Fact referenced by a frozen pack is later edited
- **THEN** the frozen evidence snapshot and checksum remain unchanged
- **AND** historical mother revisions and handoff packages continue to read the frozen value

#### Scenario: Clone produces a new freeze boundary
- **WHEN** a frozen FactPack is cloned and its evidence is revised
- **THEN** the original snapshot remains unchanged
- **AND** the clone receives a new snapshot and checksum when it is frozen

### Requirement: All M1 readers use the frozen snapshot
Generation, rewriting, checking, preview, approval, and package construction for an M1 item MUST read the typed frozen snapshot rather than re-reading mutable evidence values from live Fact rows.

#### Scenario: Preview and package agree after source changes
- **WHEN** an upstream source or Fact changes after an M1 candidate was created
- **THEN** the candidate preview and package continue to show the same frozen evidence
- **AND** the system records the upstream change as a possible new revision rather than mutating history

### Requirement: Legacy evidence does not gain eligibility by migration
The system SHALL keep `legacy_untyped` evidence readable and traceable, but MUST NOT treat migration as evidence review, content approval, or delivery authorization.

#### Scenario: Legacy pack requires review before new handoff
- **WHEN** a user attempts to create a new M1 candidate from a legacy untyped pack
- **THEN** the system blocks new approval and handoff until required items are classified, validated, and frozen into a typed snapshot

### Requirement: Public and model-use permissions remain separate
The frozen snapshot SHALL preserve public-distribution permission separately from permission to send source material to an external model.

#### Scenario: Private source is excluded from handoff package
- **WHEN** evidence may be used internally but lacks public-distribution permission
- **THEN** its private payload and source original are excluded from the public package
- **AND** any public attribution included in the article must have an independently permitted representation
