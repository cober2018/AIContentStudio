## MODIFIED Requirements

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
