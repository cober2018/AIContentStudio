## ADDED Requirements

### Requirement: Owner-scoped opportunity lifecycle

The system SHALL persist `ContentOpportunity` records owned by one user with title, summary, priority, lifecycle status, created time, and updated time. Supported statuses SHALL be `new`, `watching`, `qualified`, `dismissed`, `converted`, and `archived`. Source categories SHALL be derived from attached `ContentOpportunitySignal.signal_type` values, not a single Opportunity source type. Reads and mutations MUST enforce the same owner boundary as ContentProject. Ordinary PATCH may change triage status only among `new`, `watching`, `qualified`, and `dismissed`; it MUST NOT set `converted` or `archived`. `converted` SHALL be set only by a committed `convert-to-project` transaction, and `archived` only by the archive action. Converted and archived Opportunities SHALL reject triage edits and status rollback.

#### Scenario: Create an opportunity
- **WHEN** an editor submits a valid title and summary
- **THEN** the system creates an owner-scoped opportunity in `new` status and records the lifecycle mutation in the existing AuditLog

#### Scenario: Triage an opportunity
- **WHEN** the owner changes priority or status to `watching`, `qualified`, or `dismissed`
- **THEN** the system persists the new lifecycle state, records the actor and transition in AuditLog, and does not create a project automatically

#### Scenario: Reopen dismissed opportunity
- **WHEN** the owner explicitly changes a `dismissed` Opportunity back to `watching` or `qualified` through ordinary triage PATCH
- **THEN** the transition is audited and no Project is created

#### Scenario: Reject status bypass and rollback
- **WHEN** ordinary PATCH requests `converted` or `archived`, or attempts to change a converted/archived Opportunity back to a triage state
- **THEN** the server rejects the request without changing status or creating an OpportunityProjectConversion

#### Scenario: Cross-owner access
- **WHEN** another user requests, edits, or archives the opportunity
- **THEN** the system returns the existing not-found/forbidden contract and does not disclose its title, signals, or assessments

### Requirement: Immutable opportunity signals

The system SHALL append `ContentOpportunitySignal` records to an opportunity. Each signal SHALL preserve signal type, bounded source reference, optional source version and checksum, observed time, and a bounded annotation snapshot. Adding a signal MUST NOT rewrite an earlier signal or the referenced SourceDocument, DataSnapshot, or DeliveryFeedback.

#### Scenario: Add a source-backed signal
- **WHEN** an owner attaches a visible SourceDocument, DataSnapshot, or authorized DeliveryFeedback reference with its observed version/checksum
- **THEN** the system stores an immutable signal snapshot and returns its lineage

#### Scenario: Add a manual signal
- **WHEN** an owner records a manual observation without an external source ID
- **THEN** the system stores it with `signal_type=manual` and makes the missing external lineage explicit

#### Scenario: Source changes later
- **WHEN** the referenced source receives a newer version or is archived
- **THEN** the historical signal remains readable with its original version/checksum and is not silently refreshed

### Requirement: Append-only opportunity assessments

The system SHALL store opportunity analysis as append-only `ContentOpportunityAssessmentRevision` rows. An assessment SHALL support why-now, relevance, audience fit, suggested identity scope, suggested modalities, suggested channels, evidence references, similar-history references, risks, confidence, author, and creation time. Revisions MUST be owner-scoped and MUST distinguish suggestions from approved project facts. Saving SHALL require `expected_revision` and a unique `(opportunity_id, revision_no)` constraint; stale saves and database uniqueness races MUST return 409 with no partial revision. Assessment revisions are assessment history; they do not require a separate OpportunityEvent table.

#### Scenario: Save an assessment revision
- **WHEN** an owner saves an assessment with `expected_revision=N` matching the current assessment revision
- **THEN** the system creates revision N+1, preserves revision N, and records the assessment checksum and author

#### Scenario: Stale or concurrent assessment save
- **WHEN** another save advances the assessment before or during a save using the previous `expected_revision`
- **THEN** the stale save returns 409 and commits no partial assessment revision or audit record

#### Scenario: Reject an invalid identity suggestion
- **WHEN** an assessment references an identity outside the owner's hierarchy
- **THEN** the save is rejected and no new assessment revision or audit record is committed

#### Scenario: Read assessment history
- **WHEN** an owner opens an opportunity
- **THEN** the latest assessment and prior immutable revisions are available with their confidence, risks, and source references

### Requirement: Explicit opportunity conversion

The system SHALL allow an owner to explicitly convert only a `qualified` opportunity into one ContentProject using the current assessment revision and an idempotency key. Conversion SHALL be idempotent and SHALL preserve the opportunity ID, assessment revision, selected signal references, and suggested-vs-approved distinction. It MUST NOT create a Topic, FactPack, Fact Boundary revision, IdentitySnapshot, Candidate, or Delivery authorization automatically.

#### Scenario: Convert a qualified opportunity
- **WHEN** the owner confirms “创建内容项目” with a qualified opportunity and selected SourceDocument signals
- **THEN** the system creates one ContentProject, a normal first CreativeBriefRevision, and active project-source bindings only for the explicitly selected SourceDocument signals; identity, modality, and channel values remain suggested inputs

#### Scenario: Convert an unqualified opportunity
- **WHEN** the owner attempts conversion while status is `new`, `watching`, or `dismissed`
- **THEN** the system rejects the command without creating a project or changing the opportunity

#### Scenario: Repeat conversion
- **WHEN** the owner repeats conversion with the same idempotency key or opens an already converted opportunity
- **THEN** the system returns the existing project and does not create a second project, Brief revision, or conversion event

#### Scenario: Conversion does not freeze evidence
- **WHEN** conversion includes selected source signals
- **THEN** the new project may show them in its ordinary Source list, but the user must use the existing Evidence/Fact Boundary flow before any fact becomes project evidence

### Requirement: Opportunity lifecycle audit uses existing records

The system SHALL record Opportunity creation, triage, archive, and conversion lifecycle mutations in the existing AuditLog in the same transaction as the state change. It MUST NOT add a parallel ContentOpportunityEvent table. A successful conversion SHALL also create `ProjectEvent(project.created_from_opportunity)` in the same transaction; ProjectEvent MUST NOT be used for pre-project Opportunity history.

#### Scenario: Audit conversion atomically
- **WHEN** conversion commits successfully
- **THEN** the AuditLog transition and new ProjectEvent both reference the committed Opportunity and Project
- **WHEN** conversion rolls back
- **THEN** neither the lifecycle audit record nor ProjectEvent claims success

### Requirement: Optional Opportunity Analysis

The system MAY expose a replaceable `opportunity_analysis` capability, but persisted assessment revisions remain authoritative and manual assessment MUST work without it.

#### Scenario: Analyzer unavailable
- **WHEN** no verified analysis capability is configured
- **THEN** the API reports `capability_unavailable` and creates no fabricated assessment

### Requirement: Opportunity workspace projection

The system SHALL expose an owner-scoped opportunity workspace with lifecycle/priority filtering, latest assessment summary, signal lineage, risks, confidence, and an explicit conversion action. The workspace MUST link to the resulting project and existing source/evidence routes without duplicating their state.

#### Scenario: Filter opportunities
- **WHEN** an owner filters by status or priority
- **THEN** the workspace returns only matching owned opportunities and stable pagination metadata

#### Scenario: Show converted opportunity
- **WHEN** an opportunity is converted
- **THEN** the workspace shows its linked project and disables duplicate conversion while retaining assessment and signal history
