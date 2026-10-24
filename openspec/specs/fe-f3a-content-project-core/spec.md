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

Opportunity conversion MAY create CreativeBrief revision 1 from the selected Assessment and explicit user overrides. When created, it SHALL become a normal immutable Brief revision.

#### Scenario: Prefilled Brief
- **WHEN** conversion creates Brief v1
- **THEN** recommendations are copied as editable project inputs and later Opportunity changes do not rewrite the Brief

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

Conversion MAY attach selected SourceDocument signals through normal ProjectSourceBinding, and the binding SHALL preserve the existing source reference semantics.

#### Scenario: Attach Opportunity source
- **WHEN** a selected signal references SourceDocument
- **THEN** Project gets a Source binding and no raw source body is copied

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

Opportunity conversion MUST NOT create or bind Fact Boundary implicitly.

#### Scenario: Sources but no boundary
- **WHEN** a converted Project has attached Sources
- **THEN** Fact Boundary stays absent until explicit freeze/bind

A FactPack surfaced through System Assets & Knowledge SHALL still require the normal explicit frozen/checksum-valid Fact Boundary bind. KnowledgeCollection membership MUST NOT satisfy or bypass this gate.

#### Scenario: Collection contains frozen FactPack
- **WHEN** a KnowledgeCollection includes a frozen FactPack
- **THEN** the Project has no Fact Boundary until an authorized user explicitly binds that FactPack

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

System Library MaterialRevision and SourceDocument resources SHALL enter a Project through existing reference bindings. System Assets & Knowledge does not replace the project Shared Assets pool or duplicate underlying resource bytes/text.

#### Scenario: Add system Material to Project
- **WHEN** the user selects a MaterialRevision from `/assets`
- **THEN** ProjectMaterialReference is created and the same MaterialRevision remains the underlying resource

#### Scenario: Add system Source to Project
- **WHEN** the user selects a SourceDocument from `/assets`
- **THEN** ProjectSourceBinding is created and the existing Source remains the underlying truth

### Requirement: Append-only project activity

The system SHALL maintain an append-only product event stream per ContentProject. Events SHALL use stable event codes, entity references and structured payloads. Large content bodies, material bytes, secrets and mutable display text MUST NOT be the event contract. Project Candidate freeze, Content Approval, changes requests, Delivery Authorization, execution outcome, reconciliation, and receipt SHALL emit stable ProjectEvent codes in the same transaction as the corresponding local state change. External side-effect attempts SHALL retain their existing prepare/commit boundary and MUST NOT be claimed succeeded before a confirmed result.

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

#### Scenario: Review and delivery events
- **WHEN** a candidate is frozen, approved, authorized, or reconciled through a project-scoped action
- **THEN** Activity records the corresponding stable event and entity reference exactly once with the committed local change

Conversion SHALL record `project.created_from_opportunity` with Opportunity and Assessment revision references.

#### Scenario: Record origin event
- **WHEN** a conversion transaction commits
- **THEN** the project event is committed with the project, Brief, and selected source bindings, and a failed transaction records no event

### Requirement: Historical project deletion safety

Deleting a FE-F3A ContentProject SHALL archive the project and preserve Brief, Source bindings, Fact Boundary, material references, ProjectEvents and FE-F2 history. An archived project SHALL remain readable but SHALL reject project-scoped mutations through both new and legacy APIs. Repeating delete SHALL be idempotent.

#### Scenario: Archive project with history
- **WHEN** an editor deletes a project that has Brief revisions, events or other project records
- **THEN** the project becomes archived, `project.archived` is recorded once, and historical resources remain readable

#### Scenario: Mutate archived project through legacy API
- **WHEN** a user attempts a project-bound Run mutation through a legacy raw-run endpoint after archive
- **THEN** the mutation is rejected and historical Run/Attempt records are unchanged

### Requirement: Aggregated project Versions view

The system SHALL expose a project Versions read model aggregated from actual versioned resources. It MUST NOT introduce a monolithic ProjectVersion persistence table solely for UI presentation. The view SHALL aggregate, when present: CreativeBrief revisions, ProjectFactBoundary revisions, active/archived ContentUnits, relevant Workflow versions, WorkflowRuns with frozen checksums, project MaterialRevisions, workflow-associated Draft/Candidate references, and real IdentitySnapshots linked to project ContentUnits/Runs. It MUST NOT create synthetic snapshots for legacy units. Versions SHALL also aggregate immutable project Candidates, candidate-bound approval decisions, and delivery authorizations/attempts/receipts from real entities, preserving historical versions without fabricating records.

#### Scenario: Historical versions remain visible
- **WHEN** newer Brief, boundary, Workflow or material versions exist
- **THEN** older project-relevant versions remain visible and their IDs/checksums are not rewritten

#### Scenario: IdentitySnapshot version item
- **WHEN** a project unit pins an IdentitySnapshot
- **THEN** Versions returns the snapshot ID/checksum and unit association as an immutable historical item

#### Scenario: Legacy identity version item
- **WHEN** a unit has no snapshot
- **THEN** Versions reports a legacy/unknown identity state without fabricating Brand/Persona/Account/Series revisions

#### Scenario: Candidate and delivery history
- **WHEN** a project has a frozen Candidate, its approval, and a DeliveryTarget with attempts or receipts
- **THEN** Versions returns their real IDs, hashes, status, and unit association without synthesizing a ProjectVersion row

Project Versions SHALL include real ContentMasterRevision rows with unit/modality, revision number, payload/context hashes, exact Identity/Brief/Fact Boundary refs, origin WorkflowRun/output provenance and creation actor/time. It MUST NOT synthesize Masters for legacy Draft-only history.

#### Scenario: Master version history
- **WHEN** a ContentUnit has multiple ContentMaster revisions
- **THEN** Versions returns each immutable revision and its exact context/provenance

#### Scenario: Legacy Draft-only unit
- **WHEN** historical production predates ContentMasterRevision
- **THEN** Versions keeps existing Draft/Candidate history without fabricating Master rows

### Requirement: Derived project Overview

The backend SHALL derive ContentProject overview stage, counts, readiness, risks, pending decisions and next action from persisted state using deterministic rules. The frontend MUST NOT duplicate an independent stage engine. Active FE-F3B production units lacking a usable IdentitySnapshot SHALL produce a typed identity-readiness risk; archived legacy units SHALL not block current readiness. Overview SHALL derive pending Content Approval, Delivery Authorization, and reconciliation decisions from project candidate/review/delivery facts. Unresolved unknown delivery MUST NOT be flattened into ready, approved, or delivered.

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

#### Scenario: Pending reconciliation
- **WHEN** an active project Candidate has a DeliveryAttempt with unresolved unknown outcome
- **THEN** Overview exposes a typed reconciliation decision ahead of generic ready or approved next actions

Project Overview SHALL derive production attention from the current ContentMaster revision when present, including incomplete_context, stale identity/brief/evidence/channel, blocked Master checks and render-unready state. These remain projections, not a mutable duplicate status table.

#### Scenario: Master context stale
- **WHEN** the current Master references an older Brief or Fact Boundary
- **THEN** Overview exposes a typed production-stale risk and next action back to Production

#### Scenario: Draft-only compatibility
- **WHEN** a unit has no ContentMaster revision
- **THEN** existing FE-F2/F3A/F4 readiness behavior remains valid until the unit adopts the new production core

### Requirement: Project-core authorization and historical safety

All FE-F3A project endpoints SHALL reuse persisted ContentProject ownership checks and existing resource permissions. FE-F3A MUST preserve FE-F2 archived-unit, pinned-workflow, frozen-run and side-effect safety semantics.

#### Scenario: Cross-project read
- **WHEN** a user without access to a project requests its Brief, Sources, boundary, assets, Versions, Activity or Overview
- **THEN** the request returns no protected project data

#### Scenario: Historical run after project-core changes
- **WHEN** Brief, Fact Boundary, Sources or assets advance after a historical Run
- **THEN** the Run still reads its frozen Workflow definition and historical attempts exactly as before FE-F3A

### Requirement: Task-oriented project entry and archive
The project workspace SHALL distinguish project ownership and reference management from the existing content production workspaces. Project lists SHALL support search, status filtering and pagination with URL-preserved state. New project creation SHALL have a separate addressable view with user-scoped draft retention, explicit save, pending-state duplicate prevention and truthful error states.

#### Scenario: Return from a project
- **WHEN** a user opens a project from a filtered page and returns
- **THEN** the list retains its search, status and page without creating or modifying projects

#### Scenario: Read-only user
- **WHEN** the current user lacks editor permissions or permission cannot be verified
- **THEN** project creation and visible project mutation controls are unavailable while readable records remain accessible

### Requirement: Project page responsibility groups
The project workspace SHALL expose overview, works, project resources and history groups while preserving every existing tab deep link and the current backend state. The default overview SHALL explain the current next action and link into existing production workspaces; management and archive actions SHALL be secondary.

#### Scenario: Existing project deep link
- **WHEN** a user opens tab=brief, evidence, assets, matrix, variants, execution, versions or activity
- **THEN** the corresponding existing content remains reachable under its responsibility group and no new workflow action occurs by navigation

#### Scenario: Opportunity-created empty project
- **WHEN** a newly converted project has no content units
- **THEN** the page explains that only the project and initial task brief exist and provides explicit routes to review the brief, sources and create a work without claiming content was generated

#### Scenario: Project switch during read
- **WHEN** a user changes project before previous read requests complete
- **THEN** stale responses do not replace the newly selected project's content
