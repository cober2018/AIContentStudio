## MODIFIED Requirements

### Requirement: Immutable IdentitySnapshot

Every new or explicitly rebound project ContentUnit SHALL be able to pin an immutable IdentitySnapshot containing the exact resolved hierarchy revisions, BrandVoiceVersion, effective profile, field origins and checksum used for production. A Project Candidate manifest SHALL freeze the exact IdentitySnapshot ID and checksum pinned to the producing ContentUnit and, for workflow-backed sources, WorkflowRun. Approval and delivery MUST use that frozen reference, not resolve latest identity revisions in place of it.

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

Every new ContentMasterRevision SHALL pin the exact IdentitySnapshot used for that production revision. Historical Master revisions MUST retain that snapshot even if Brand/Persona/Account/Series changes later. Candidate v4 SHALL freeze the same Master-pinned IdentitySnapshot ID/checksum rather than resolving current identity.

#### Scenario: Identity changes after Master save
- **WHEN** the identity hierarchy advances after a Master revision is saved
- **THEN** the old Master remains bound to the unit-pinned snapshot; hierarchy drift is advisory, and only an explicit authorized change of pinned production context creates identity staleness

#### Scenario: V4 Candidate identity
- **WHEN** a v4 Candidate freezes a current Master
- **THEN** the Candidate identity section exactly matches the Master revision's pinned IdentitySnapshot
