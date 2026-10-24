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

Opportunity Assessment MAY recommend valid stable identity hierarchy entities, but recommendation SHALL NOT mutate identity revisions or create IdentitySnapshot.

#### Scenario: Recommended Persona/Account/Series
- **WHEN** an Assessment saves identity recommendations
- **THEN** hierarchy ownership is validated and identity remains unchanged

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

#### Scenario: Historical Memory tab before F5
- **WHEN** the user opens Content Memory in the pre-F5 FE-F3B baseline
- **THEN** the UI may show truthful linked historical content and explicitly marks automated learning/strategy promotion as not yet implemented

Opportunity relevance/recommendation SHALL NOT be treated as verified learning or written automatically into Content Memory.

#### Scenario: Later performance
- **WHEN** converted content later performs well
- **THEN** F5A makes no automatic Identity/Memory mutation; later LearningCandidate flow owns that decision

Content Memory SHALL be backed by validated, versioned ContentMemory records scoped to owner/Brand/Persona/Account/Series. Memory remains a dynamic learned layer and MUST NOT silently mutate stable Identity revisions.

#### Scenario: Read validated memory
- **WHEN** the user opens an identity's Content Memory tab
- **THEN** applicable validated memory entries and revision provenance are shown with scope origin and limitations

#### Scenario: Promote Identity learning
- **WHEN** an accepted identity-category LearningCandidate is promoted to memory
- **THEN** ContentMemory changes but Brand/Persona/Account/Series revisions remain unchanged until a separate explicit identity save

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

### Requirement: Brand constraints and Persona creative root remain separate

Brand SHALL supply Brand Voice, content boundaries, compliance/risk constraints and common factual policy, while Creative Profile defaults SHALL resolve from Persona → Account → Series only; Brand mutations that attempt `*_creative_profile` SHALL be rejected.

#### Scenario: Two Personas share one Brand but not creative defaults
- **GIVEN** an AI technology Persona and a lifestyle Persona share one Brand
- **WHEN** both create content
- **THEN** applicable brand constraints are respected
- **BUT** neither Persona acquires the other's Skills, Styles, Recipes or creative memories

#### Scenario: No account is required for new editorial Series
- **WHEN** an owner creates a Persona-owned editorial Series for content planning
- **THEN** no Account is required at Series creation or source Master planning
- **AND** legacy Account-Series rules continue to apply only in the legacy context

### Requirement: Explicit origin and destination identity in frozen records

The system SHALL record whether an Account selected for a Unit is an origin creative context or a target delivery account; historical IdentitySnapshot data SHALL remain interpretable under its original semantics.

#### Scenario: Target account differs from origin
- **WHEN** a modern Candidate is adapted for a destination Account different from a Unit's origin Account
- **THEN** provenance includes both source and target contexts
- **AND** the destination Account is not represented as the origin or vice versa

### Requirement: Identity revisions may carry persona-native creative profiles

Persona/Account/Series profile JSON SHALL support bounded Text/Graphic/Audio/Video creative-profile fields without changing stable identity tables. Brand profile JSON MUST reject these creative-profile fields. Creative-profile inheritance/origin applies only across Persona → Account → Series per whole field, while Brand constraints remain separate Effective Context. IdentitySnapshot SHALL freeze the effective creative profile and origin with the existing checksum.

#### Scenario: Persona creative profile advances
- **WHEN** Persona saves a new Text creative profile revision
- **THEN** new explicitly rebound/created production may use it while existing IdentitySnapshots, Units, Runs and Masters remain unchanged

### Requirement: Persona is the normal creative configuration root

Identity UX and resolution SHALL treat Persona as the ordinary scope for creative defaults. Account/Series may explicitly override modality profiles. Owner/User MUST NOT be presented as the automatic writing/visual/audio style source shared across all Personas.

#### Scenario: Persona A learned style does not affect Persona B
- **WHEN** the owner uses two Personas and saves a creative method/profile for Persona A
- **THEN** Persona B's effective identity/ordinary method discovery does not inherit it merely because owner IDs match

### Requirement: Identity Workspace exposes typed creative configuration

Persona/Account/Series SHALL expose a `创作配置` surface with inherited origin, Auto/Custom/Composed mode, exact Studio Skill/Preset/Quality refs, method extensions, model policy, default recipe and readiness. Normal users SHALL NOT need to edit raw workflow/profile JSON to configure supported defaults.

#### Scenario: Account overrides only Graphic behavior
- **WHEN** an Account explicitly overrides the Graphic creative profile and leaves other modality fields absent
- **THEN** Graphic origin is Account while Text/Audio/Video continue inheriting their existing effective fields

#### Scenario: First Starter initialization selects its confirmed Persona
- **WHEN** the user explicitly initializes a Starter Persona from an empty identity tree and has not changed identity selection during the request
- **THEN** the refreshed tree selects that confirmed Persona, opens its typed creative configuration and reports success without a second initialization request

#### Scenario: Late initialization preserves a newer identity selection
- **WHEN** the user changes identity selection while a Starter initialization request is pending
- **THEN** the confirmed record may refresh the tree but its late callback does not replace the newer selection or discard that selection's creative draft

#### Scenario: Two Personas share Brand constraints without sharing creative defaults
- **WHEN** one Brand owns a technical Persona and a lifestyle Persona and defines Brand Voice or boundary constraints
- **THEN** both Personas apply those constraints, but neither Persona inherits a Studio Skill, Style Preset, Quality Profile, Recipe or creative method stack from Brand

### Requirement: Task-oriented identity directories and detail views
The Identity Workspace SHALL provide separate role, owned account, series and brand directories with URL-preserved search, status and pagination. Overview, profile editing, immutable revision history and advanced configuration SHALL be independently addressable. Existing hierarchy, inheritance, revision contracts and persona links SHALL remain available. Independent owned accounts MUST NOT require a Persona.

#### Scenario: Open identity entry
- **WHEN** the user opens the default identity workspace
- **THEN** role selection and next actions are clear without displaying all forms or automatically initializing a role

#### Scenario: Existing persona link
- **WHEN** a production work links to identities with its persona parameter
- **THEN** the correct role opens without selecting an unrelated default identity or changing a snapshot

#### Scenario: Edit and conflict
- **WHEN** an authorized editor explicitly saves a profile revision and receives a conflict
- **THEN** input remains available for explicit comparison with the latest revision, without automatic retry or overwriting inherited data

#### Scenario: Read-only or archived identity
- **WHEN** permission is unknown, read-only or an applicable identity ancestor is archived
- **THEN** the workspace exposes readable data but no permitted mutation path through its UI

#### Scenario: Change selected identity during a read
- **WHEN** an earlier identity read completes after navigation to another identity
- **THEN** that response does not replace the selected identity's values or draft
