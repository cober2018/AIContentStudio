## MODIFIED Requirements

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
