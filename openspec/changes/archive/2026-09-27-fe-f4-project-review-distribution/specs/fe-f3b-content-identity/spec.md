## MODIFIED Requirements

### Requirement: Immutable IdentitySnapshot

Every new or explicitly rebound project ContentUnit SHALL be able to pin an immutable IdentitySnapshot containing the exact resolved hierarchy revisions, BrandVoiceVersion, effective profile, field origins and checksum used for production. A Project Candidate manifest SHALL freeze the exact IdentitySnapshot ID and checksum pinned to the producing ContentUnit and WorkflowRun. Approval and delivery MUST use that frozen reference, not resolve latest identity revisions in place of it.

#### Scenario: Create unit snapshot
- **WHEN** an editor creates a new ContentUnit with a valid Persona/Account/Series selection
- **THEN** the server resolves current identity revisions, creates an immutable IdentitySnapshot and pins it to the unit

#### Scenario: Brandless legacy Persona used for new production
- **WHEN** an editor explicitly creates a new unit from an existing brandless Persona with no authored profile revision
- **THEN** the snapshot records that Persona and null absent revision IDs with an empty effective profile, and readiness labels the identity incomplete rather than inventing a Brand or positioning

#### Scenario: Run pins unit snapshot
- **WHEN** a WorkflowRun starts for a unit with an IdentitySnapshot
- **THEN** the run stores that exact snapshot ID and never resolves latest identity in place of it

#### Scenario: Identity advances
- **WHEN** Persona receives revision N+1 after a unit/run pinned revision N
- **THEN** the old unit/run continue to read their original snapshot unchanged

#### Scenario: Candidate preserves production identity
- **WHEN** a Candidate is frozen after its producing Run pinned an IdentitySnapshot
- **THEN** the Candidate records that same snapshot ID/checksum and later identity revisions do not alter it

### Requirement: Production identity context

Production Workspace SHALL expose the frozen identity used by the selected unit/run. Project Review SHALL display the Candidate's frozen identity context. A legacy Candidate without a proven IdentitySnapshot SHALL be explicitly labeled legacy/unknown rather than assigned the current identity.

#### Scenario: Inspect frozen identity
- **WHEN** a run has an IdentitySnapshot
- **THEN** the context header and snapshot inspector show Brand/Persona/Account/Series and frozen effective identity from that snapshot

#### Scenario: Historical legacy run
- **WHEN** a historical run has no snapshot
- **THEN** Production Workspace shows legacy/unknown rather than latest identity

#### Scenario: Review legacy candidate identity
- **WHEN** an authorized reviewer opens a historical Candidate without an IdentitySnapshot
- **THEN** Review shows legacy/unknown identity and does not present current Brand/Persona/Account/Series data as historical provenance
