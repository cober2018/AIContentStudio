# fe-f3b-content-identity Specification

## Purpose
Define the long-lived Content Identity contract: versioned Brand, Persona, Account, and Series hierarchy; deterministic profile inheritance; immutable production identity snapshots; hierarchical workflow defaults; and honest legacy and archive behavior.
## Requirements
### Requirement: Versioned Brand / Persona / Account / Series hierarchy

The system SHALL persist Brand → Persona → Account → Series as explicit stable entities. Existing ContentPersona SHALL remain the Persona stable entity. Brand, Persona, Account and Series profile changes SHALL be stored as append-only revisions.

#### Scenario: Create hierarchy
- **WHEN** an authorized editor creates Brand, Persona, Account and Series children
- **THEN** every child is persisted under its actual parent and reload returns the same hierarchy

#### Scenario: Reject mismatched hierarchy
- **WHEN** a request combines a Series, Account or Persona that are not in the same persisted hierarchy
- **THEN** the operation is rejected without mutating any identity or project record

#### Scenario: Save next revision
- **WHEN** an editor saves a profile using the current expected revision
- **THEN** revision N+1 is created and all earlier revisions remain immutable and readable

#### Scenario: Stale revision
- **WHEN** another revision has already committed
- **THEN** a stale save returns 409 and does not partially update current identity state

### Requirement: Deterministic identity inheritance

The system SHALL resolve identity fields in Brand → Persona → Account → Series order. Missing fields SHALL inherit, explicit values SHALL override, explicit null SHALL clear, and array/object fields SHALL replace instead of implicit deep merge.

#### Scenario: Inherit missing field
- **WHEN** Persona omits target_audience and Brand defines it
- **THEN** the effective identity uses Brand target_audience and reports Brand as field origin

#### Scenario: Clear inherited field
- **WHEN** Account explicitly sets a supported inherited field to null
- **THEN** that field is empty in the effective identity rather than falling back to Persona or Brand

#### Scenario: Replace structured value
- **WHEN** Series provides an array/object override
- **THEN** the Series value replaces the inherited value as a whole

### Requirement: Reuse versioned Brand Voice

Identity profiles SHALL reference existing BrandVoiceVersion rather than creating a parallel voice system. Effective identity SHALL resolve the nearest explicit BrandVoiceVersion reference.

#### Scenario: Voice override
- **WHEN** Brand provides voice v2 and Account explicitly provides published voice v4
- **THEN** the effective identity and new snapshot use v4

#### Scenario: Invalid voice
- **WHEN** a new identity revision references an unavailable or disallowed BrandVoiceVersion
- **THEN** the revision is rejected without becoming current

#### Scenario: Global published voice
- **WHEN** an editor selects an existing published BrandVoiceVersion
- **THEN** it is eligible for a new snapshot as a global voice resource without a fabricated owner relationship

### Requirement: Immutable IdentitySnapshot

Every new or explicitly rebound project ContentUnit SHALL be able to pin an immutable IdentitySnapshot containing the exact resolved hierarchy revisions, BrandVoiceVersion, effective profile, field origins and checksum used for production.

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

### Requirement: Honest legacy identity state

FE-F3B SHALL NOT synthesize IdentitySnapshot rows for historical ContentUnits, WorkflowRuns, TopicBriefs or ContentAssets that do not prove which new hierarchy revisions were used.

#### Scenario: Legacy unit
- **WHEN** an existing unit has no identity_snapshot_id after migration
- **THEN** APIs/UI report legacy/unknown identity state and do not claim a current snapshot was historical

#### Scenario: Explicit modernization
- **WHEN** an editor explicitly rebinds an eligible legacy active unit
- **THEN** a new real snapshot is created at rebind time under normal history-safety rules

### Requirement: Safe ContentUnit identity rebind

Identity rebind SHALL preserve FE-F2/F3A execution-history safety.

#### Scenario: Rebind before history
- **WHEN** a unit has no Run, DataSnapshot or ProjectWorkflowOutput and the editor changes Persona/Account/Series
- **THEN** the unit MAY update in place, receives a fresh IdentitySnapshot and pins the resolved workflow

#### Scenario: Rebind after history
- **WHEN** a unit with execution history changes identity
- **THEN** the server creates a replacement unit, archives the old unit, and preserves the old unit snapshot and all runs

#### Scenario: Parent change leaves incompatible child selection
- **WHEN** an editor changes Persona or Account while omitting an existing child selection that no longer belongs to the selected parent
- **THEN** the server rejects the rebind and requires an explicit child replacement or clear rather than silently dropping it

### Requirement: Hierarchical workflow defaults

The system SHALL preserve PersonaWorkflowDefault and add Account × Modality and Series × Modality default bindings. Effective default resolution SHALL be Series > Account > Persona.

#### Scenario: Resolve Series default
- **WHEN** all three scopes define a text workflow default
- **THEN** a new Series-bound text ContentUnit pins the Series workflow version

#### Scenario: Fall back to Persona
- **WHEN** neither Series nor Account defines the modality
- **THEN** the existing Persona default is used

#### Scenario: Save scoped default
- **WHEN** an editor explicitly saves a new Account or Series default
- **THEN** the backend creates an immutable Workflow version using FE-F2 validation/portability rules and advances only that binding revision

#### Scenario: Legacy raw workflow route
- **WHEN** another owner requests or starts an Account/Series-scoped workflow by raw Workflow ID through a legacy API
- **THEN** the shared project-workflow authorization boundary denies disclosure or execution

#### Scenario: No silent unit rebind
- **WHEN** any identity workflow default advances
- **THEN** existing ContentUnits and Runs keep their pinned workflow until explicit rebind

### Requirement: Archive-safe identity lifecycle

Identity entities referenced by snapshots, units or workflow preferences SHALL remain historically readable. Delete operations SHALL archive rather than erase referenced identity state.

#### Scenario: Archive Persona
- **WHEN** a Persona with historical production is deleted
- **THEN** it becomes archived, revisions/snapshots remain readable, and new mutation/children/defaults are rejected

#### Scenario: Archived ancestor cannot start new production
- **WHEN** a selected Brand, Persona, Account or Series is archived and a user creates/rebinds a unit or starts a new run
- **THEN** the mutation is rejected while existing snapshots and runs remain readable

### Requirement: Persistent Identity Workspace

The `/identities` primary workspace SHALL use backend-persisted hierarchy and revisions rather than a placeholder.

#### Scenario: Browse identity tree
- **WHEN** the user opens `/identities`
- **THEN** Brand → Persona → Account → Series hierarchy loads from persisted state with truthful empty/loading/error views

#### Scenario: Inspect effective profile
- **WHEN** the user opens an Account or Series identity
- **THEN** the UI distinguishes inherited, overridden and cleared fields and shows each field origin

#### Scenario: Revision history
- **WHEN** multiple revisions exist
- **THEN** the user can inspect older immutable revisions without changing current production state

### Requirement: Identity and Content Memory remain separate

FE-F3B SHALL NOT automatically convert performance observations into identity or Content Memory mutations.

#### Scenario: Memory tab before F5
- **WHEN** the user opens Content Memory in FE-F3B
- **THEN** the UI may show truthful linked historical content and explicitly marks automated learning/strategy promotion as not yet implemented

### Requirement: Production identity context

Production Workspace SHALL expose the frozen identity used by the selected unit/run.

#### Scenario: Inspect frozen identity
- **WHEN** a run has an IdentitySnapshot
- **THEN** the context header and snapshot inspector show Brand/Persona/Account/Series and frozen effective identity from that snapshot

#### Scenario: Historical legacy run
- **WHEN** a historical run has no snapshot
- **THEN** Production Workspace shows legacy/unknown rather than latest identity

### Requirement: Project-core identity integration

FE-F3A project read models SHALL incorporate identity without fabricating historical data.

#### Scenario: Versions includes snapshot
- **WHEN** a project unit has a real IdentitySnapshot
- **THEN** project Versions includes that immutable snapshot with checksum and unit association

#### Scenario: Versions legacy state
- **WHEN** a unit has no snapshot
- **THEN** Versions reports legacy identity state without creating a synthetic snapshot

#### Scenario: Identity readiness
- **WHEN** an active new-production unit requires identity but lacks a usable snapshot
- **THEN** project Overview returns a typed identity readiness risk through deterministic backend rules
