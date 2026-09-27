# fe-f3a-content-project-core Specification

## Purpose
Define the persistent ContentProject core contract for append-only Brief and Fact Boundary revisions, project assets and events, aggregated Versions, deterministic Overview readiness, and validated content identity scope.
## Requirements
### Requirement: Immutable CreativeBrief revisions

The system SHALL persist CreativeBrief as append-only revisions owned by one ContentProject. Each committed revision SHALL include objective, primary audience, core message, angle, required evidence, content constraints, identity scope, modality scope, channel scope, CTA, references, checksum, author and creation time. Saving a Brief SHALL create a new revision; a prior revision MUST NOT be mutated. New CreativeBrief revisions MAY reference stable Brand/Persona/Account/Series IDs in identity scope. Those typed references SHALL be server-validated against ownership/hierarchy when saved. Historical Brief revisions MUST NOT be rewritten when identity hierarchy changes.

#### Scenario: Save next Brief revision
- **WHEN** an editor saves a valid Brief with `expected_revision` equal to the current revision
- **THEN** the backend creates revision N+1, returns its checksum, keeps revision N readable, and records `brief.revision_created`

#### Scenario: Reject stale Brief save
- **WHEN** another editor has already created a newer Brief revision
- **THEN** the stale save returns 409 and creates neither a new revision nor a project event

#### Scenario: Concurrent Brief saves
- **WHEN** two saves both target the same current revision and race at the database constraint
- **THEN** at most one new revision and its event commit; the other request returns 409 without a partial event

#### Scenario: Reload Brief
- **WHEN** the user reloads the project
- **THEN** the Brief tab shows the latest committed revision and its prior revisions from backend state

#### Scenario: Invalid identity scope
- **WHEN** a Brief revision references an identity outside the user's hierarchy
- **THEN** the save is rejected without changing prior Brief revisions

### Requirement: Project Sources reference existing SourceDocument records

A ContentProject SHALL organize Sources through project bindings to existing SourceDocument rows. Attaching or detaching a Source MUST NOT copy, rewrite, archive, or delete the SourceDocument.

#### Scenario: Attach an existing Source
- **WHEN** an editor attaches a visible SourceDocument to a project
- **THEN** an active project-source binding is persisted and the Source appears in the Evidence tab after reload

#### Scenario: Create then attach Source
- **WHEN** an editor creates a text, URL, or uploaded Source using the existing Source APIs and then attaches the returned Source ID
- **THEN** the project references that Source without copying its raw text or bytes

#### Scenario: Detach Source used by historical evidence
- **WHEN** an editor detaches a Source that contributed to an older frozen FactPack
- **THEN** the Source disappears from the project's active Source list but the historical FactPack snapshot and project Fact Boundary remain unchanged

#### Scenario: Reattach Source
- **WHEN** an editor attaches a previously detached Source already bound to the project
- **THEN** the existing unique binding becomes active again; repeated active attach is idempotent and does not emit a duplicate event

### Requirement: Immutable project Fact Boundary revisions

A ContentProject SHALL represent its factual boundary through immutable ProjectFactBoundaryRevision rows that reference existing frozen FactPack versions. Creating a project boundary revision MUST NOT duplicate FactPack items. Only frozen FactPacks with a checksum MAY become a project boundary.

#### Scenario: Bind initial frozen FactPack
- **WHEN** an editor selects a frozen FactPack for a project with no prior Fact Boundary
- **THEN** boundary revision 1 records the FactPack ID, version and checksum

#### Scenario: Refuse mutable boundary
- **WHEN** an editor attempts to bind a draft FactPack as the current boundary
- **THEN** the request is rejected and the prior boundary remains current

#### Scenario: Clone, edit, freeze and advance boundary
- **WHEN** an editor clones the current boundary, edits the draft using existing FactPack operations, and uses the project freeze-and-bind action
- **THEN** the draft is frozen and a new immutable project boundary revision points to that new frozen FactPack while the old revision remains readable

#### Scenario: Concurrent boundary advancement
- **WHEN** two editors advance the same boundary revision concurrently
- **THEN** at most one new revision and event commit; the other request returns 409 and leaves the current boundary unchanged

### Requirement: Unified Project Shared Assets by reference

Project Shared Assets SHALL combine explicit project references to existing MaterialRevision rows with FE-F2 verified workflow-produced MaterialRevision associations. The system MUST NOT duplicate underlying material bytes merely to add an item to a project.

#### Scenario: Reference system material
- **WHEN** an editor adds an existing MaterialRevision to a project
- **THEN** an explicit project material reference is stored and the unified Shared Assets response returns its original revision/rights/provenance data

#### Scenario: Upload project material
- **WHEN** an editor uploads a material from the project
- **THEN** the existing material service creates Material + immutable MaterialRevision and the project stores only a reference to that revision

#### Scenario: Workflow material appears in same pool
- **WHEN** FE-F2 records a verified workflow-generated MaterialRevision in ProjectWorkflowOutput
- **THEN** the same project Shared Assets API displays it with source type `workflow` without creating a duplicate project material reference

#### Scenario: Detach explicit reference
- **WHEN** an editor detaches a project-upload/system-reference item
- **THEN** the project reference becomes inactive while the global MaterialRevision and workflow histories remain unchanged

#### Scenario: Upload transaction fails
- **WHEN** creating the project material reference or event fails after byte storage
- **THEN** the API does not report success or leave a committed MaterialRevision without its project reference; newly unreferenced bytes are cleaned up or tracked for bounded cleanup without deleting shared content

### Requirement: Append-only project activity

The system SHALL maintain an append-only product event stream per ContentProject. Events SHALL use stable event codes, entity references and structured payloads. Large content bodies, material bytes, secrets and mutable display text MUST NOT be the event contract.

#### Scenario: Business mutation records event
- **WHEN** project, Brief, Source, boundary, ContentUnit, Workflow, DataSnapshot or project-asset state changes through an FE-F3A/FE-F2 project flow
- **THEN** the same transaction records the corresponding ProjectEvent unless the underlying operation is idempotently returning an already-recorded association

#### Scenario: Activity survives display copy changes
- **WHEN** frontend wording changes
- **THEN** historical activity is still renderable from stable `event_type` and structured payload fields

#### Scenario: AuditLog remains separate
- **WHEN** an operation already has a security/operations AuditLog requirement
- **THEN** FE-F3A does not remove that AuditLog merely because a ProjectEvent also exists

#### Scenario: Failed mutation has no event
- **WHEN** a project mutation rolls back
- **THEN** its ProjectEvent also rolls back and the activity timeline does not claim a change that did not commit

### Requirement: Historical project deletion safety

Deleting a FE-F3A ContentProject SHALL archive the project and preserve Brief, Source bindings, Fact Boundary, material references, ProjectEvents and FE-F2 history. An archived project SHALL remain readable but SHALL reject project-scoped mutations through both new and legacy APIs. Repeating delete SHALL be idempotent.

#### Scenario: Archive project with history
- **WHEN** an editor deletes a project that has Brief revisions, events or other project records
- **THEN** the project becomes archived, `project.archived` is recorded once, and historical resources remain readable

#### Scenario: Mutate archived project through legacy API
- **WHEN** a user attempts a project-bound Run mutation through a legacy raw-run endpoint after archive
- **THEN** the mutation is rejected and historical Run/Attempt records are unchanged

### Requirement: Aggregated project Versions view

The system SHALL expose a project Versions read model aggregated from actual versioned resources. It MUST NOT introduce a monolithic ProjectVersion persistence table solely for UI presentation. The view SHALL aggregate, when present: CreativeBrief revisions, ProjectFactBoundary revisions, active/archived ContentUnits, relevant Workflow versions, WorkflowRuns with frozen checksums, project MaterialRevisions, workflow-associated Draft/Candidate references, and real IdentitySnapshots linked to project ContentUnits/Runs. It MUST NOT create synthetic snapshots for legacy units.

#### Scenario: Historical versions remain visible
- **WHEN** newer Brief, boundary, Workflow or material versions exist
- **THEN** older project-relevant versions remain visible and their IDs/checksums are not rewritten

#### Scenario: IdentitySnapshot version item
- **WHEN** a project unit pins an IdentitySnapshot
- **THEN** Versions returns the snapshot ID/checksum and unit association as an immutable historical item

#### Scenario: Legacy identity version item
- **WHEN** a unit has no snapshot
- **THEN** Versions reports a legacy/unknown identity state without fabricating Brand/Persona/Account/Series revisions

### Requirement: Derived project Overview

The backend SHALL derive ContentProject overview stage, counts, readiness, risks, pending decisions and next action from persisted state using deterministic rules. The frontend MUST NOT duplicate an independent stage engine. Active FE-F3B production units lacking a usable IdentitySnapshot SHALL produce a typed identity-readiness risk; archived legacy units SHALL not block current readiness.

#### Scenario: Missing Brief
- **WHEN** a project has no CreativeBrief revision
- **THEN** overview stage is `brief_needed` and next action points to the Brief tab

#### Scenario: Missing Fact Boundary
- **WHEN** a project has a Brief but no frozen project Fact Boundary
- **THEN** overview stage is `evidence_needed`

#### Scenario: Attention state
- **WHEN** active units/runs contain blocked, stale, unknown or failed states
- **THEN** overview returns typed risks and an attention-required stage rather than flattening them into a generic failure

#### Scenario: Waiting human
- **WHEN** no higher-priority blocker exists and an active production run is waiting for human input
- **THEN** overview returns `waiting_human` with a typed pending decision

#### Scenario: Identity not ready
- **WHEN** an active FE-F3B unit lacks a usable identity snapshot
- **THEN** Overview includes an `identity_unready` risk and a deterministic next action

#### Scenario: Empty legacy Persona profile
- **WHEN** a newly bound active unit has a snapshot of a brandless Persona with no authored profile revision
- **THEN** Overview identifies incomplete identity readiness rather than presenting the empty snapshot as a complete identity

### Requirement: Project-core authorization and historical safety

All FE-F3A project endpoints SHALL reuse persisted ContentProject ownership checks and existing resource permissions. FE-F3A MUST preserve FE-F2 archived-unit, pinned-workflow, frozen-run and side-effect safety semantics.

#### Scenario: Cross-project read
- **WHEN** a user without access to a project requests its Brief, Sources, boundary, assets, Versions, Activity or Overview
- **THEN** the request returns no protected project data

#### Scenario: Historical run after project-core changes
- **WHEN** Brief, Fact Boundary, Sources or assets advance after a historical Run
- **THEN** the Run still reads its frozen Workflow definition and historical attempts exactly as before FE-F3A
